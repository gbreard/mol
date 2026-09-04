#!/usr/bin/env python3
"""
Pipeline Command Poller — Gateway local para la fábrica de procesamiento.
Mismo patrón que el scraping command poller del VPS.

Lee comandos pendientes de Supabase (pipeline_commands) y los ejecuta localmente.
Diseñado para correr como cron cada 1 minuto o como servicio systemd.

Uso:
    python scripts/pipeline_command_poller.py          # Ejecuta un comando pendiente
    python scripts/pipeline_command_poller.py --daemon  # Loop continuo (cada 60s)
    python scripts/pipeline_command_poller.py --dry-run # Muestra qué haría sin ejecutar
"""

import json
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime, timedelta

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DB_DIR = PROJECT_DIR / "database"

# --- Reintento diferido de Indeed (bloqueo Cloudflare) -----------------------
# Indeed corre LOCAL; la corrida pesada (~1900s+, 480 kw) a veces deja la IP
# flagueada en Cloudflare y la siguiente aborta en ~22s con 5x403. Cuando eso
# pasa, re-encolamos la corrida unas horas después (otra ventana de tráfico)
# por si el bloqueo era transitorio. Es barato: una corrida bloqueada dura ~22s.
# El estado vive en un archivo LOCAL (no toca el schema de pipeline_commands).
INDEED_RETRY_STATE = PROJECT_DIR / "data" / "indeed_retry.json"
INDEED_BLOCK_MAX_DUR = 600        # una corrida limpia dura ~1900s+; <600s = bloqueo
INDEED_RETRY_OFFSETS_MIN = [180, 480]  # reintentos: +3h, luego +8h (2 máx)

# Add project to path
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(DB_DIR))


def get_supabase_client():
    """Crea cliente Supabase con service_role_key."""
    config_path = PROJECT_DIR / "config" / "supabase_config.json"
    if not config_path.exists():
        print("[POLLER] ERROR: config/supabase_config.json no encontrado")
        return None

    config = json.loads(config_path.read_text())
    try:
        from supabase import create_client
        return create_client(config['url'], config['service_role_key'])
    except Exception as e:
        print(f"[POLLER] ERROR: No se pudo conectar a Supabase: {e}")
        return None


# Command → script mapping
#
# NLP SUSPENDIDO 2026-09-04 por Gerardo — reactivar cuando scraping estable +
# mejora de procesamiento. El cron semanal (sabado 09:05) quedo comentado, pero
# este poller es un SEGUNDO camino: cualquier comando encolado desde el dashboard
# dispararia NLP igual. Los comandos que invocan NLP quedan deshabilitados aca;
# el resto del poller (scrape_indeed, sync, export) sigue funcionando.
COMANDOS_NLP_SUSPENDIDOS = {
    'run_pipeline', 'run_nlp', 'reprocess_errors', 'revalidate_nlp',
}

COMMAND_MAP = {
    'run_pipeline': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--limit', str(p.get('limit', 100))] if p.get('limit') else ['--ids', p.get('ids', '')],
    },
    'run_nlp': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--skip-matching', '--limit', str(p.get('limit', 100))] if p.get('limit') else ['--skip-matching', '--ids', p.get('ids', '')],
    },
    'run_matching': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--skip-nlp'] + (['--ids', p.get('ids', '')] if p.get('ids') else ['--limit', str(p.get('limit', 100))]),
    },
    'reprocess_errors': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--only-pending', '--limit', str(p.get('limit', 200))],
    },
    'revalidate_nlp': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--skip-matching'] + (['--ids', p.get('ids', '')] if p.get('ids') else []),
    },
    'revalidate_matching': {
        'script': 'scripts/run_validated_pipeline.py',
        'build_args': lambda p: ['--skip-nlp'] + (['--ids', p.get('ids', '')] if p.get('ids') else []),
    },
    'reapply_rules': {
        'script': 'scripts/reapply_rules_to_validated.py',
        'build_args': lambda p: [],
    },
    'export_excel': {
        'script': 'scripts/exports/export_validation_excel.py',
        'build_args': lambda p: ['--etapa', 'completo'] + (['--ids', p.get('ids', '')] if p.get('ids') else []),
    },
    'sync_supabase': {
        'script': 'scripts/exports/sync_to_supabase.py',
        'build_args': lambda p: [],
    },
    'sync_supabase_full': {
        'script': 'scripts/exports/sync_to_supabase.py',
        'build_args': lambda p: ['--full'],
    },
    'generate_training': {
        'script': 'scripts/exports/generate_training_pairs.py',
        'build_args': lambda p: [],
    },
    'recluster_preview': {
        'script': 'scripts/generate_skill_equivalences.py',
        'build_args': lambda p: ['--partial', '--preview'] + (['--threshold', str(p['threshold'])] if p.get('threshold') else []),
    },
    'recluster_apply': {
        'script': 'scripts/generate_skill_equivalences.py',
        'build_args': lambda p: ['--partial'] + (['--threshold', str(p['threshold'])] if p.get('threshold') else []),
    },
    # Indeed motor HEADED (solo local): corre un chromium real bajo xvfb.
    # Ver 01_sources/indeed/scrapers/indeed_scraper_headed.py y CLAUDE.md.
    # Por defecto: tramo de 90 kw desde proximo_offset y avanza el offset.
    'scrape_indeed': {
        'script': 'scripts/scraping/run_indeed_headed.py',
        'wrap': ['xvfb-run', '-a'],   # display virtual (Indeed detecta headless)
        'build_args': lambda p: (
            (['--offset', str(p['offset'])] if p.get('offset') is not None else [])
            + ['--max-keywords', str(p.get('max_keywords', 90))]
            + (['--no-advance'] if p.get('no_advance') else [])
            + (['--prototipo'] if p.get('prototipo') else [])
        ),
    },
    # SPEC S1C-PUENTE (mesa de Cyn): escritura git-first de candidatas confirmadas
    # al diccionario argentino. El payload viaja como JSON (lista de candidatas +
    # sesion); aplicar_candidata valida contra el catalogo, respeta longest-match,
    # escribe el JSON local que el matcher lee y hace UN commit (squash por sesion).
    'aplicar_candidata': {
        'script': 'scripts/puente/aplicar_candidata.py',
        'build_args': lambda p: ['--payload-json', json.dumps(p, ensure_ascii=False)],
    },
}


def fetch_pending_command(client):
    """Lee el comando pendiente más antiguo."""
    result = client.table('pipeline_commands') \
        .select('*') \
        .eq('estado', 'pendiente') \
        .order('created_at') \
        .limit(1) \
        .execute()

    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def update_command(client, cmd_id, **kwargs):
    """Actualiza un comando en Supabase."""
    try:
        client.table('pipeline_commands').update(kwargs).eq('id', cmd_id).execute()
    except Exception as e:
        print(f"[POLLER] WARN: No se pudo actualizar comando {cmd_id}: {e}")


def _sync_scraping_stats_after_indeed(client):
    """Merge Indeed stats into scraping_live_stats without overwriting VPS portals."""
    try:
        import sqlite3
        db_path = PROJECT_DIR / "database" / "bumeran_scraping.db"
        conn = sqlite3.connect(str(db_path))

        # Get local Indeed stats only. Mismas 4 métricas que sync_scraping_stats.py
        # (total, ultimo, ultimos_7d, hoy) para que el entry sea schema-consistente
        # con los portales del VPS; si no, sync_scraping_stats.py crashea con KeyError.
        row = conn.execute(
            """SELECT MAX(scrapeado_en), COUNT(*),
                      SUM(CASE WHEN scrapeado_en >= datetime('now','-7 days') THEN 1 ELSE 0 END),
                      SUM(CASE WHEN scrapeado_en >= datetime('now','-1 day')  THEN 1 ELSE 0 END)
               FROM ofertas WHERE portal = 'indeed'"""
        ).fetchone()
        conn.close()

        if not row or not row[0]:
            return

        indeed_ultimo = row[0]
        indeed_total = row[1]
        indeed_7d = row[2] or 0
        indeed_hoy = row[3] or 0

        # Read current stats from Supabase (includes VPS portals)
        existing = client.table('scraping_live_stats').select('portales,ultimo_scraping').eq('id', 'current').execute()
        portales = {}
        if existing.data:
            portales = existing.data[0].get('portales', {}) or {}
            if isinstance(portales, str):
                portales = json.loads(portales)

        # Only update Indeed, keep VPS portals as-is
        portales['indeed'] = {
            'ultimo_scraping': indeed_ultimo,
            'total': indeed_total,
            'ultimos_7d': indeed_7d,
            'hoy': indeed_hoy,
        }

        # Global ultimo = max across all portals
        ultimo_global = max(
            (v.get('ultimo_scraping', '') for v in portales.values()),
            default=indeed_ultimo
        )

        from datetime import timezone
        client.table('scraping_live_stats').upsert({
            'id': 'current',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'portales': portales,
            'ultimo_scraping': ultimo_global,
        }).execute()
        print(f"[POLLER] scraping_live_stats: Indeed actualizado ({indeed_ultimo[:19]}, {indeed_total} ofertas)")
    except Exception as e:
        print(f"[POLLER] WARN: No se pudo sync stats post-Indeed: {e}")


def _sync_scraping_daily_after_indeed():
    """Run sync_scraping_daily.py to update the daily chart with local Indeed data."""
    try:
        script = PROJECT_DIR / "scripts" / "sync_scraping_daily.py"
        if not script.exists():
            print("[POLLER] WARN: sync_scraping_daily.py no encontrado")
            return
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script), '--days', '7'],
            capture_output=True, text=True, timeout=60,
            cwd=str(PROJECT_DIR),
        )
        if result.returncode == 0:
            print("[POLLER] scraping_daily actualizado post-Indeed")
        else:
            print(f"[POLLER] WARN: sync_scraping_daily falló: {result.stderr[-200:]}")
    except Exception as e:
        print(f"[POLLER] WARN: No se pudo sync daily post-Indeed: {e}")


def _indeed_fue_bloqueado(duration, log_output):
    """True si una corrida de Indeed fue abortada por bloqueo Cloudflare.

    Señal principal: duración anómalamente corta (una corrida limpia procesa
    480 keywords a 4s → mínimo ~1900s; un bloqueo aborta a los 5x403 en ~22s).
    """
    if duration is not None and duration < INDEED_BLOCK_MAX_DUR:
        return True
    marcadores = ('blocks consecutivos', 'No se obtuvieron ofertas', 'Cloudflare block')
    return any(m in (log_output or '') for m in marcadores)


def _load_retry_state():
    try:
        if INDEED_RETRY_STATE.exists():
            return json.loads(INDEED_RETRY_STATE.read_text())
    except Exception as e:
        print(f"[POLLER] WARN: no se pudo leer estado de reintento Indeed: {e}")
    return None


def _clear_retry_state(motivo=""):
    try:
        if INDEED_RETRY_STATE.exists():
            INDEED_RETRY_STATE.unlink()
            if motivo:
                print(f"[POLLER] reintento Indeed: estado limpiado ({motivo})")
    except Exception as e:
        print(f"[POLLER] WARN: no se pudo limpiar estado de reintento Indeed: {e}")


def _programar_reintento_indeed():
    """Tras un bloqueo, agenda el próximo reintento (o desiste si se agotaron)."""
    prev = _load_retry_state()
    intento = (prev.get('intento', 0) if prev else 0) + 1
    if intento > len(INDEED_RETRY_OFFSETS_MIN):
        _clear_retry_state(f"agotados {len(INDEED_RETRY_OFFSETS_MIN)} reintentos; espera al próximo cron")
        return
    offset_min = INDEED_RETRY_OFFSETS_MIN[intento - 1]
    not_before = datetime.utcnow() + timedelta(minutes=offset_min)
    try:
        INDEED_RETRY_STATE.parent.mkdir(parents=True, exist_ok=True)
        INDEED_RETRY_STATE.write_text(json.dumps({
            'intento': intento,
            'not_before': not_before.isoformat(),
            'programado_en': datetime.utcnow().isoformat(),
        }))
        print(f"[POLLER] Indeed bloqueado → reintento #{intento} agendado "
              f"para {not_before.isoformat()[:16]} UTC (+{offset_min}min)")
    except Exception as e:
        print(f"[POLLER] WARN: no se pudo agendar reintento Indeed: {e}")


def _hay_indeed_en_curso(client):
    """True si ya hay un scrape_indeed pendiente o ejecutando (evita duplicados)."""
    try:
        r = client.table('pipeline_commands').select('id') \
            .eq('comando', 'scrape_indeed') \
            .in_('estado', ['pendiente', 'ejecutando']).limit(1).execute()
        return bool(r.data)
    except Exception as e:
        print(f"[POLLER] WARN: no se pudo verificar Indeed en curso: {e}")
        return True  # ante la duda, no encolar


def _check_indeed_retry(client):
    """Cada ciclo: si vence un reintento agendado y no hay Indeed en curso,
    encola una nueva corrida scrape_indeed por el camino normal."""
    state = _load_retry_state()
    if not state:
        return
    try:
        not_before = datetime.fromisoformat(state['not_before'])
    except Exception:
        _clear_retry_state("estado corrupto")
        return
    if datetime.utcnow() < not_before:
        return  # todavía no vence
    if _hay_indeed_en_curso(client):
        return  # ya hay uno; esperar a que termine (re-agenda o limpia solo)
    try:
        client.table('pipeline_commands').insert({
            'comando': 'scrape_indeed',
            'estado': 'pendiente',
            'params': {'reintento': state.get('intento', 1)},
            'creado_por': 'poller-retry',
        }).execute()
        print(f"[POLLER] reintento Indeed #{state.get('intento')} encolado "
              f"(bloqueo Cloudflare previo)")
    except Exception as e:
        print(f"[POLLER] WARN: no se pudo encolar reintento Indeed: {e}")


def execute_command(client, cmd, dry_run=False):
    """Ejecuta un comando del pipeline."""
    cmd_id = cmd['id']
    comando = cmd['comando']
    params = cmd.get('params', {}) or {}

    print(f"\n[POLLER] === Ejecutando: {comando} ===")
    print(f"[POLLER] ID: {cmd_id}")
    print(f"[POLLER] Params: {json.dumps(params)}")
    print(f"[POLLER] Creado por: {cmd.get('creado_por', '?')}")

    if comando in COMANDOS_NLP_SUSPENDIDOS:
        motivo = ("NLP suspendido 2026-09-04 por Gerardo — reactivar cuando el "
                  "scraping este estable y el procesamiento mejorado")
        update_command(client, cmd_id,
            estado='error',
            error_message=motivo,
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] RECHAZADO: {comando} — {motivo}")
        return False

    if comando not in COMMAND_MAP:
        update_command(client, cmd_id,
            estado='error',
            error_message=f"Comando desconocido: {comando}",
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] ERROR: Comando desconocido: {comando}")
        return False

    mapping = COMMAND_MAP[comando]
    script_path = PROJECT_DIR / mapping['script']

    if not script_path.exists():
        update_command(client, cmd_id,
            estado='error',
            error_message=f"Script no encontrado: {mapping['script']}",
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] ERROR: Script no encontrado: {script_path}")
        return False

    args = mapping['build_args'](params)
    wrap = mapping.get('wrap', [])   # p.ej. ['xvfb-run','-a'] para el motor headed
    full_cmd = wrap + [sys.executable, str(script_path)] + [str(a) for a in args if a]

    print(f"[POLLER] Comando: {' '.join(full_cmd)}")

    if dry_run:
        print(f"[POLLER] DRY RUN — no se ejecuta")
        return True

    # Mark as executing
    update_command(client, cmd_id,
        estado='ejecutando',
        started_at=datetime.utcnow().isoformat()
    )

    # Execute
    start_time = time.time()
    try:
        # Set OLLAMA_HOST for WSL if needed
        env = os.environ.copy()
        if 'OLLAMA_HOST' not in env:
            env['OLLAMA_HOST'] = '172.17.0.1'
        # SPEC S1C-F0.3: el acta de corrida registra quién la invocó.
        env['MOL_INVOCADOR'] = 'poller'

        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=28800,  # 8 hours max
            cwd=str(PROJECT_DIR),
            env=env,
        )

        duration = round(time.time() - start_time, 1)
        log_output = result.stdout[-5000:] if result.stdout else ''  # Last 5K chars
        if result.stderr:
            log_output += f"\n--- STDERR ---\n{result.stderr[-2000:]}"

        if result.returncode == 0:
            # M-08c: Intentar parsear JSON estructurado de la última línea
            resultado = {'exit_code': 0, 'duracion_seg': duration}
            try:
                stdout_lines = (result.stdout or '').strip().split('\n')
                if stdout_lines:
                    last_line = stdout_lines[-1].strip()
                    parsed = json.loads(last_line)
                    if isinstance(parsed, dict) and 'tipo' in parsed:
                        resultado.update(parsed)
                        resultado['duracion_seg'] = duration
            except (json.JSONDecodeError, IndexError):
                pass

            update_command(client, cmd_id,
                estado='completado',
                log=log_output,
                resultado=resultado,
                completed_at=datetime.utcnow().isoformat()
            )
            print(f"[POLLER] OK — {duration}s")

            # Post-scraping: sync stats + daily to Supabase so dashboard updates
            if comando == 'scrape_indeed':
                _sync_scraping_stats_after_indeed(client)
                _sync_scraping_daily_after_indeed()
                # Reintento diferido: si Cloudflare bloqueó (corrida ~22s), agendar
                # otra corrida en unas horas; si fue limpia, limpiar cualquier estado.
                if _indeed_fue_bloqueado(duration, log_output):
                    _programar_reintento_indeed()
                else:
                    _clear_retry_state("corrida limpia")

            return True
        else:
            update_command(client, cmd_id,
                estado='error',
                log=log_output,
                error_message=f"Exit code {result.returncode}",
                resultado={
                    'exit_code': result.returncode,
                    'duracion_seg': duration,
                },
                completed_at=datetime.utcnow().isoformat()
            )
            print(f"[POLLER] ERROR — exit code {result.returncode} — {duration}s")
            return False

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 1)
        update_command(client, cmd_id,
            estado='error',
            error_message=f"Timeout ({duration}s)",
            resultado={'duracion_seg': duration},
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] TIMEOUT — {duration}s")
        return False

    except Exception as e:
        update_command(client, cmd_id,
            estado='error',
            error_message=str(e),
            completed_at=datetime.utcnow().isoformat()
        )
        print(f"[POLLER] EXCEPTION: {e}")
        return False


def _leer_observabilidad_local(conn):
    """Lee la última acta y las alertas recientes del SQLite local (SPEC S1C-F0.3).

    Devuelve (ultima_acta: dict|None, alertas_recientes: list). Tolerante a que las
    tablas no existan (migración 025 no aplicada) → devuelve (None, []).
    """
    ultima_acta = None
    alertas = []
    try:
        cur = conn.execute(
            "SELECT acta_id, started_at, finished_at, invocador, args, "
            "alcance_entrada, alcance_procesado, resultado, fallos, matching_run_id "
            "FROM pipeline_run_actas ORDER BY started_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            cols = [d[0] for d in cur.description]
            ultima_acta = dict(zip(cols, row))
            if ultima_acta.get("fallos"):
                try:
                    ultima_acta["fallos"] = json.loads(ultima_acta["fallos"])
                except (json.JSONDecodeError, TypeError):
                    ultima_acta["fallos"] = []
    except Exception:
        pass

    try:
        cur = conn.execute(
            "SELECT timestamp, severidad, tipo, mensaje, acta_id, contexto "
            "FROM pipeline_alertas ORDER BY id DESC LIMIT 10"
        )
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
            a = dict(zip(cols, row))
            if a.get("contexto"):
                try:
                    a["contexto"] = json.loads(a["contexto"])
                except (json.JSONDecodeError, TypeError):
                    pass
            alertas.append(a)
    except Exception:
        pass

    return ultima_acta, alertas


def sync_local_status(client):
    """Sube el estado real de SQLite a Supabase para que la Fábrica lo muestre."""
    db_path = PROJECT_DIR / "database" / "bumeran_scraping.db"
    sync_log_path = PROJECT_DIR / "config" / "supabase_sync_log.json"

    if not db_path.exists():
        return

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))

        total = conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]
        con_nlp = conn.execute("SELECT COUNT(*) FROM ofertas_nlp").fetchone()[0]

        try:
            aprobados = conn.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_gate_status = 'aprobado'").fetchone()[0]
            bloqueados = conn.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_gate_status = 'bloqueado'").fetchone()[0]
        except Exception:
            aprobados = con_nlp
            bloqueados = 0

        try:
            con_matching = conn.execute("SELECT COUNT(*) FROM ofertas_esco_matching").fetchone()[0]
        except Exception:
            con_matching = 0

        try:
            validadas = conn.execute(
                "SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion IN ('validado','validado_claude','validado_humano')"
            ).fetchone()[0]
        except Exception:
            validadas = 0

        try:
            errores = conn.execute("SELECT COUNT(*) FROM validation_errors WHERE resuelto = 0").fetchone()[0]
        except Exception:
            errores = 0

        # Observabilidad (SPEC S1C-F0.3): leer acta + alertas con la misma conexión.
        ultima_acta, alertas_recientes = _leer_observabilidad_local(conn)

        conn.close()

        # Sync log + count real from Supabase
        try:
            sync_log = json.loads(sync_log_path.read_text()) if sync_log_path.exists() else {}
            ultimo_sync = sync_log.get("last_sync_timestamp", sync_log.get("ultimo_sync"))
        except Exception:
            sync_log = {}
            ultimo_sync = None

        try:
            count_result = client.table('ofertas_dashboard').select('id_oferta', count='exact', head=True).execute()
            en_supabase = count_result.count or 0
        except Exception:
            en_supabase = sync_log.get("ofertas_synced", sync_log.get("total_synced", 0))

        gate_total = aprobados + bloqueados
        gate_pct = round(aprobados / gate_total * 100, 1) if gate_total > 0 else 100

        client.table('pipeline_local_status').upsert({
            'id': 'current',
            'timestamp': datetime.utcnow().isoformat(),
            'total_ofertas': total,
            'nlp_procesadas': con_nlp,
            'nlp_pendientes': total - con_nlp,
            'nlp_aprobados': aprobados,
            'nlp_bloqueados': bloqueados,
            'nlp_gate_aprobado_pct': gate_pct,
            'matching_con': con_matching,
            'matching_sin': max(aprobados - con_matching, 0),
            'validadas': validadas,
            'errores_pendientes': errores,
            'en_supabase': en_supabase,
            'pendientes_sync': max(validadas - en_supabase, 0),
            'ultimo_sync': ultimo_sync,
        }).execute()

        # Espejo de observabilidad en columnas JSONB aparte. Separado del upsert
        # principal para que, si la migración 066 (columnas) aún no se aplicó en
        # Supabase, el fallo no rompa el sync de estado.
        try:
            client.table('pipeline_local_status').update({
                'ultima_acta': ultima_acta,
                'alertas_recientes': alertas_recientes,
            }).eq('id', 'current').execute()
        except Exception as e:
            print(f"[POLLER] WARN: no se pudo espejar observabilidad (¿migración 066?): {e}")

    except Exception as e:
        print(f"[POLLER] WARN: No se pudo sync status local: {e}")


def poll_once(dry_run=False):
    """Ejecuta un ciclo de polling."""
    client = get_supabase_client()
    if not client:
        return False

    # Siempre sincronizar status local
    sync_local_status(client)

    # Reintento diferido de Indeed: encola una corrida si venció un bloqueo previo
    _check_indeed_retry(client)

    cmd = fetch_pending_command(client)
    if not cmd:
        return False

    return execute_command(client, cmd, dry_run=dry_run)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Pipeline Command Poller')
    parser.add_argument('--daemon', action='store_true', help='Loop continuo cada 60s')
    parser.add_argument('--dry-run', action='store_true', help='No ejecutar, solo mostrar')
    parser.add_argument('--interval', type=int, default=60, help='Intervalo en segundos (default: 60)')
    args = parser.parse_args()

    print(f"[POLLER] Pipeline Command Poller v1.0")
    print(f"[POLLER] Proyecto: {PROJECT_DIR}")
    print(f"[POLLER] Modo: {'daemon' if args.daemon else 'single'}")

    if args.daemon:
        print(f"[POLLER] Intervalo: {args.interval}s")
        while True:
            try:
                poll_once(dry_run=args.dry_run)
            except Exception as e:
                print(f"[POLLER] ERROR en ciclo: {e}")
            time.sleep(args.interval)
    else:
        executed = poll_once(dry_run=args.dry_run)
        if not executed:
            print("[POLLER] Sin comandos pendientes")


if __name__ == '__main__':
    main()
