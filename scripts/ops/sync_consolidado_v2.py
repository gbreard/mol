#!/usr/bin/env python3
"""
[FRENTE L] SYNC CONSOLIDADO v2 — un solo evento que publica al dashboard el
re-matching masivo + el backlog NLP nuevo, dirigido SOLO a lo cambiado.

Contexto (2026-08-22): el P4-sync del frente L quedo POSPUESTO por presupuesto
de I/O de Supabase agotado (aviso formal). Cuando el backlog NLP termine, este
script publica TODO junto en un unico evento rate-limited.

Dos modos:

  PRE-REPORTE (default, NO toca Supabase — es el punto de control de Gerardo):
      python scripts/ops/sync_consolidado_v2.py
    Calcula contra el snapshot pre-rematching que viaja y cuanto:
      A. CAMBIADAS: destino/campos dashboard distintos al snapshot
      B. NUEVAS: no estaban en el snapshot (backlog NLP posterior)
      C. SKILLS-CAMBIADAS: el set (uri, mencionado) difiere del snapshot
    Emite exports/reportes/SYNC_consolidado_prereporte_<fecha>.md con filas,
    requests estimados y duracion al rate configurado. NADA se ejecuta sin
    el OK de Gerardo sobre ese pre-reporte.

  EJECUTAR (solo tras el OK explicito):
      python scripts/ops/sync_consolidado_v2.py --ejecutar --aprobado-por-gerardo
    Requiere ambos flags. Aborta en horario pico (09-21 ART) salvo
    --fuera-de-valle. Sube por tandas con pausas (RATE_SLEEP entre batches de
    ofertas; pausa por oferta en skills) para no pasar ~8 req/s sostenido
    (free tier tolera ~15; margen 2x). Reusa extraccion/transform/upsert del
    canonico scripts/exports/sync_to_supabase.py — NO reimplementa mapeos.

El proceso del backlog NLP corre por su lado (otra sesion): este script no lo
toca; solo exige BD en disco (no symlink tmpfs) para leer consistente.
"""
import argparse
import gzip
import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts' / 'exports'))

DB = ROOT / 'database' / 'bumeran_scraping.db'
SNAP_M = ROOT / 'exports/cohorts/snapshot_pre_rematching_2026-08-19_matching.jsonl.gz'
SNAP_S = ROOT / 'exports/cohorts/snapshot_pre_rematching_2026-08-19_skills.jsonl.gz'
ESTADOS_DASHBOARD = ("'validado_claude'", "'validado_humano'", "'validado'",
                     "'validado_claude_subfaseD'", "'validado_claude_C1'")

BATCH = 100          # upsert de ofertas por request (igual que el sync canonico)
RATE_SLEEP = 1.0     # pausa entre batches de ofertas (seg)
SKILL_SLEEP = 0.25   # pausa entre ofertas en la fase skills (delete+insert = 2 req)
VALLE = range(9, 21) # horas ART consideradas pico: 09..20 → abortar sin --fuera-de-valle

# Campos del dashboard que disparan re-upsert si difieren del snapshot
CAMPOS_DIFF = ['esco_occupation_label', 'esco_occupation_uri', 'titulo_esco_code',
               'isco_code', 'isco_label', 'occupation_match_method',
               'estado_validacion', 'matching_version']


def cargar_snapshot_matching():
    snap = {}
    with gzip.open(SNAP_M, 'rt') as f:
        for line in f:
            d = json.loads(line)
            snap[str(d['id_oferta'])] = tuple(d.get(c) for c in CAMPOS_DIFF)
    return snap


def cargar_snapshot_skills():
    snap = {}
    with gzip.open(SNAP_S, 'rt') as f:
        for line in f:
            d = json.loads(line)
            snap.setdefault(str(d['id_oferta']), set()).add(
                (d.get('esco_skill_uri'), d.get('skill_mencionado')))
    return snap


def calcular_cambios(con):
    """Devuelve (cambiadas, nuevas, skills_cambiadas, n_skills_filas)."""
    estados = ','.join(ESTADOS_DASHBOARD)
    print('cargando estado actual (solo estados que ve el dashboard)...', flush=True)
    actual = {}
    for row in con.execute(
            f"SELECT id_oferta, {','.join(CAMPOS_DIFF)} FROM ofertas_esco_matching "
            f"WHERE estado_validacion IN ({estados})"):
        actual[str(row[0])] = tuple(row[1:])

    print('comparando contra snapshot matching...', flush=True)
    snap = cargar_snapshot_matching()
    cambiadas = [oid for oid, v in actual.items() if oid in snap and snap[oid] != v]
    nuevas = [oid for oid in actual if oid not in snap]
    del snap

    print('comparando skills contra snapshot...', flush=True)
    snap_s = cargar_snapshot_skills()
    actual_s = {}
    for oid, uri, menc in con.execute(
            'SELECT id_oferta, esco_skill_uri, skill_mencionado FROM ofertas_esco_skills_detalle'):
        oid = str(oid)
        if oid in actual:
            actual_s.setdefault(oid, set()).add((uri, menc))
    skills_cambiadas = [oid for oid, s in actual_s.items()
                        if oid in snap_s and snap_s[oid] != s]
    n_skills_filas = sum(len(actual_s.get(o, ())) for o in
                         set(skills_cambiadas) | set(nuevas))
    return cambiadas, nuevas, skills_cambiadas, n_skills_filas


def pre_reporte(cambiadas, nuevas, skills_cambiadas, n_skills_filas):
    ofertas_viajan = sorted(set(cambiadas) | set(nuevas))
    ofertas_skills = sorted(set(skills_cambiadas) | set(nuevas))
    req_ofertas = -(-len(ofertas_viajan) // BATCH)
    req_skills = len(ofertas_skills) * 2          # delete + insert por oferta
    dur_min = (req_ofertas * RATE_SLEEP + len(ofertas_skills) * SKILL_SLEEP) / 60
    hoy = datetime.now().strftime('%Y-%m-%d')
    md = f"""# SYNC CONSOLIDADO v2 — PRE-REPORTE de volumen ({hoy})

**PUNTO DE CONTROL: nada de esto se ejecuto.** Numeros contra el snapshot
pre-rematching (2026-08-19) con la BD local de hoy.

| Poblacion | Ofertas |
|---|---|
| A. Cambiadas (re-matching: destino/campos dashboard distintos) | {len(cambiadas):,} |
| B. Nuevas (backlog NLP posterior al snapshot) | {len(nuevas):,} |
| C. Skills cambiadas (set difiere) | {len(skills_cambiadas):,} |
| **Upserts ofertas_dashboard (A∪B)** | **{len(ofertas_viajan):,}** |
| **Ofertas con reemplazo de skills (C∪B)** | **{len(ofertas_skills):,}** ({n_skills_filas:,} filas) |

**Requests estimados:** {req_ofertas:,} batches de ofertas (x{BATCH}) + {req_skills:,}
requests de skills (delete+insert por oferta) ≈ **{req_ofertas + req_skills:,} requests**.
**Duracion estimada** al rate configurado (sleep {RATE_SLEEP}s/batch, {SKILL_SLEEP}s/oferta-skills):
**~{dur_min:.0f} min** — multiplicar x2-3 para presupuestar (historial de estimaciones cortas).

Ejecucion SOLO tras OK de Gerardo, en horario valle (fuera de 09-21 ART):
`python scripts/ops/sync_consolidado_v2.py --ejecutar --aprobado-por-gerardo`
"""
    out = ROOT / f'exports/reportes/SYNC_consolidado_prereporte_{hoy}.md'
    out.write_text(md)
    (ROOT / f'exports/reportes/SYNC_consolidado_prereporte_{hoy}.json').write_text(
        json.dumps({'cambiadas': len(cambiadas), 'nuevas': len(nuevas),
                    'skills_cambiadas': len(skills_cambiadas),
                    'ofertas_viajan': ofertas_viajan, 'ofertas_skills': ofertas_skills},
                   ensure_ascii=False))
    print(md)
    print(f'pre-reporte -> {out}')


def esperar_valle(fuera_de_valle):
    """Guarda de pico como PAUSA-Y-RETOMA (instruccion de Gerardo 2026-08-23):
    si estamos en horario pico (09-21 ART) NO se aborta — se duerme hasta las
    21:00 y se retoma. Se chequea al inicio y entre batches, asi una corrida
    que cruza las 09:00 pausa sola y termina la noche siguiente."""
    if fuera_de_valle:
        return
    now = datetime.now()
    if now.hour in VALLE:
        objetivo = now.replace(hour=21, minute=0, second=30, microsecond=0)
        segs = (objetivo - now).total_seconds()
        print(f'[{now:%F %T}] PAUSA por horario pico — retomo 21:00 '
              f'({segs/3600:.1f} h)', flush=True)
        time.sleep(max(segs, 0))


def ejecutar(con, cambiadas, nuevas, skills_cambiadas, fuera_de_valle):
    esperar_valle(fuera_de_valle)
    import sync_to_supabase as sts
    client = sts.get_supabase_client()
    conn = sts.get_sqlite_connection()
    ofertas_viajan = sorted(set(cambiadas) | set(nuevas))
    ofertas_skills = sorted(set(skills_cambiadas) | set(nuevas))
    print(f'EJECUTANDO: {len(ofertas_viajan):,} upserts de ofertas + '
          f'{len(ofertas_skills):,} reemplazos de skills', flush=True)

    subidas = 0
    for i in range(0, len(ofertas_viajan), BATCH):
        esperar_valle(fuera_de_valle)
        chunk = ofertas_viajan[i:i + BATCH]
        ofertas = sts.extraer_ofertas_validadas(conn, ids=chunk)
        subidas += sts.upsert_ofertas(client, ofertas)
        time.sleep(RATE_SLEEP)
        if (i // BATCH) % 50 == 0:
            print(f'[{datetime.now():%F %T}]  ofertas {i + len(chunk):,}/{len(ofertas_viajan):,}', flush=True)
    print(f'ofertas subidas: {subidas:,}', flush=True)

    for j, oid in enumerate(ofertas_skills):
        if j % 50 == 0:
            esperar_valle(fuera_de_valle)
        skills = sts.extraer_skills_detalle(conn, [oid])
        sts.upsert_skills(client, skills)
        time.sleep(SKILL_SLEEP)
        if j % 500 == 0:
            print(f'[{datetime.now():%F %T}]  skills {j:,}/{len(ofertas_skills):,}', flush=True)
    print('SYNC CONSOLIDADO COMPLETO. Actualizar supabase_sync_log.json y '
          'hacer el spot 10 en el dashboard.', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ejecutar', action='store_true')
    ap.add_argument('--aprobado-por-gerardo', action='store_true',
                    help='OBLIGATORIO junto a --ejecutar: confirma el OK sobre el pre-reporte')
    ap.add_argument('--fuera-de-valle', action='store_true')
    args = ap.parse_args()

    if DB.is_symlink():
        sys.exit('ABORT: la BD es symlink (sesion tmpfs activa de otro frente). Reintentar despues.')
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    cambiadas, nuevas, skills_cambiadas, n_filas = calcular_cambios(con)

    if not args.ejecutar:
        pre_reporte(cambiadas, nuevas, skills_cambiadas, n_filas)
        return
    if not args.aprobado_por_gerardo:
        sys.exit('ABORT: --ejecutar requiere --aprobado-por-gerardo (el pre-reporte es el punto de control).')
    ejecutar(con, cambiadas, nuevas, skills_cambiadas, args.fuera_de_valle)


if __name__ == '__main__':
    main()
