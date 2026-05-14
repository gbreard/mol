#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ordenamiento de Ofertas por Prioridad - Criterios Múltiples

Calcula una prioridad compuesta para ofertas pendientes de procesar
y devuelve lotes ordenados por prioridad.

Criterios de scoring (configurables):
- Fecha publicación (frescura): 40%
- Cantidad vacantes (impacto): 30%
- Permanencia (señal mercado): 30%

Uso:
    python scripts/get_priority_batch.py                    # Próximo lote de 100
    python scripts/get_priority_batch.py --size 50          # Lote de 50
    python scripts/get_priority_batch.py --offset 100       # Segundo lote
    python scripts/get_priority_batch.py --stats            # Ver estadísticas
    python scripts/get_priority_batch.py --export           # Exportar IDs para pipeline
    python scripts/get_priority_batch.py --criteria         # Ver criterios usados
"""

import argparse
import io
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Paths
DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "priority_criteria.json"

# Default weights (can be overridden by config)
DEFAULT_WEIGHTS = {
    "fecha_publicacion": 0.40,   # Frescura
    "cantidad_vacantes": 0.30,   # Impacto laboral
    "permanencia": 0.30          # Señal de mercado
}

# Scoring parameters
SCORING_PARAMS = {
    "fecha": {
        "max_dias": 90,          # Ofertas > 90 días = score 0
        "decay": "linear"        # linear o exponential
    },
    "vacantes": {
        "max_vacantes": 20,      # Más de 20 = score 1.0
        "boost_multiple": True   # Boost extra para múltiples vacantes
    },
    "permanencia": {
        "baja": 1.0,             # Permanencia baja = máxima prioridad
        "media": 0.6,
        "alta": 0.2,
        "null": 0.1
    }
}


def get_connection():
    """Conexión a BD."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_config():
    """Carga configuración de criterios si existe."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"weights": DEFAULT_WEIGHTS, "params": SCORING_PARAMS}


def save_config(config):
    """Guarda configuración de criterios."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def calculate_fecha_score(fecha_pub_iso: str, params: dict) -> float:
    """
    Score basado en frescura de la oferta.
    Más reciente = mayor score.
    """
    if not fecha_pub_iso:
        return 0.0

    try:
        fecha_pub = datetime.fromisoformat(fecha_pub_iso.replace('Z', '+00:00'))
        if fecha_pub.tzinfo:
            fecha_pub = fecha_pub.replace(tzinfo=None)
    except:
        return 0.0

    dias = (datetime.now() - fecha_pub).days
    max_dias = params.get("max_dias", 90)

    if dias <= 0:
        return 1.0
    if dias >= max_dias:
        return 0.0

    # Linear decay
    return 1.0 - (dias / max_dias)


def calculate_vacantes_score(cantidad: int, params: dict) -> float:
    """
    Score basado en cantidad de vacantes.
    Más vacantes = mayor impacto = mayor score.
    """
    if not cantidad or cantidad <= 0:
        return 0.1  # Mínimo para ofertas sin dato

    max_vac = params.get("max_vacantes", 20)

    if cantidad >= max_vac:
        return 1.0

    # Score base
    score = cantidad / max_vac

    # Boost para múltiples vacantes (>1)
    if params.get("boost_multiple", True) and cantidad > 1:
        score = min(1.0, score * 1.2)

    return score


def calculate_permanencia_score(categoria: str, params: dict) -> float:
    """
    Score basado en permanencia.
    Baja permanencia = se llenan rápido = alta demanda = mayor score.
    """
    if not categoria:
        return params.get("null", 0.1)

    return params.get(categoria.lower(), 0.1)


def get_pending_offers_with_scores(conn, weights: dict, params: dict, limit: int = None, offset: int = 0, from_db: bool = False):
    """
    Obtiene ofertas pendientes con scores calculados.

    Args:
        from_db: Si True, lee desde tabla ofertas_prioridad (más rápido)
                 Si False, calcula scores en memoria (más preciso)

    Returns:
        List of dicts with offer data and scores
    """
    # Si from_db, leer directamente de la tabla de prioridad
    if from_db:
        query = """
            SELECT
                p.id_oferta,
                o.titulo,
                o.empresa,
                o.portal,
                o.fecha_publicacion_iso,
                o.cantidad_vacantes,
                o.categoria_permanencia,
                p.score_total,
                p.score_fecha,
                p.score_vacantes,
                p.score_permanencia,
                p.estado,
                p.lote_asignado
            FROM ofertas_prioridad p
            JOIN ofertas o ON p.id_oferta = o.id_oferta
            WHERE p.estado = 'pendiente'
            ORDER BY p.score_total DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"

        cur = conn.execute(query)
        rows = cur.fetchall()

        return [{
            "id_oferta": row['id_oferta'],
            "titulo": row['titulo'],
            "empresa": row['empresa'],
            "portal": row['portal'],
            "fecha_pub": row['fecha_publicacion_iso'][:10] if row['fecha_publicacion_iso'] else None,
            "vacantes": row['cantidad_vacantes'] or 1,
            "permanencia": row['categoria_permanencia'],
            "score_fecha": row['score_fecha'],
            "score_vacantes": row['score_vacantes'],
            "score_permanencia": row['score_permanencia'],
            "score_total": row['score_total'],
            "estado": row['estado'],
            "lote_asignado": row['lote_asignado']
        } for row in rows]

    # Query ofertas pendientes (sin NLP) - cálculo en memoria
    # NLP requiere descripción no vacía y >100 chars (mismo filtro que process_batch).
    # Sin este filtro, ofertas crudas sin descripción (típico de listados de
    # ComputRabajo/Indeed que no scrapearon el detalle) entran al sistema de
    # prioridad pero NLP las descarta — quedan ciclando como pendientes para
    # siempre y bloquean el avance del loop.
    query = """
        SELECT
            o.id_oferta,
            o.titulo,
            o.empresa,
            o.portal,
            o.fecha_publicacion_iso,
            o.cantidad_vacantes,
            o.categoria_permanencia,
            o.dias_publicada,
            o.tipo_aviso,
            o.plan_publicacion_nombre,
            o.provincia_normalizada
        FROM ofertas o
        WHERE NOT EXISTS (
            SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = o.id_oferta
        )
          AND o.descripcion IS NOT NULL
          AND LENGTH(o.descripcion) > 100
    """

    cur = conn.execute(query)
    rows = cur.fetchall()

    # Calcular scores
    offers_with_scores = []
    fecha_params = params.get("fecha", {})
    vacantes_params = params.get("vacantes", {})
    permanencia_params = params.get("permanencia", {})

    for row in rows:
        # Calcular scores individuales
        score_fecha = calculate_fecha_score(row['fecha_publicacion_iso'], fecha_params)
        score_vacantes = calculate_vacantes_score(row['cantidad_vacantes'], vacantes_params)
        score_permanencia = calculate_permanencia_score(row['categoria_permanencia'], permanencia_params)

        # Score compuesto
        score_total = (
            weights.get("fecha_publicacion", 0.4) * score_fecha +
            weights.get("cantidad_vacantes", 0.3) * score_vacantes +
            weights.get("permanencia", 0.3) * score_permanencia
        )

        offers_with_scores.append({
            "id_oferta": row['id_oferta'],
            "titulo": row['titulo'],
            "empresa": row['empresa'],
            "portal": row['portal'],
            "fecha_pub": row['fecha_publicacion_iso'][:10] if row['fecha_publicacion_iso'] else None,
            "vacantes": row['cantidad_vacantes'] or 1,
            "permanencia": row['categoria_permanencia'],
            "dias_pub": row['dias_publicada'],
            "tipo_aviso": row['tipo_aviso'],
            "provincia": row['provincia_normalizada'],
            "score_fecha": score_fecha,
            "score_vacantes": score_vacantes,
            "score_permanencia": score_permanencia,
            "score_total": score_total
        })

    # Ordenar por score total descendente
    offers_with_scores.sort(key=lambda x: x['score_total'], reverse=True)

    # Aplicar offset y limit
    if offset:
        offers_with_scores = offers_with_scores[offset:]
    if limit:
        offers_with_scores = offers_with_scores[:limit]

    return offers_with_scores


def show_stats(conn, weights: dict, params: dict):
    """Muestra estadísticas de las ofertas pendientes."""
    offers = get_pending_offers_with_scores(conn, weights, params)

    if not offers:
        print("No hay ofertas pendientes de procesar.")
        return

    print(f"\n{'='*60}")
    print(f"  ESTADISTICAS DE OFERTAS PENDIENTES")
    print(f"{'='*60}")
    print(f"\nTotal ofertas pendientes: {len(offers)}")

    # Distribución de scores
    print(f"\n--- DISTRIBUCION DE SCORES ---")
    high = sum(1 for o in offers if o['score_total'] >= 0.7)
    medium = sum(1 for o in offers if 0.4 <= o['score_total'] < 0.7)
    low = sum(1 for o in offers if o['score_total'] < 0.4)

    print(f"  Alta prioridad (>=0.7):  {high:,} ({100*high/len(offers):.1f}%)")
    print(f"  Media prioridad (0.4-0.7): {medium:,} ({100*medium/len(offers):.1f}%)")
    print(f"  Baja prioridad (<0.4):   {low:,} ({100*low/len(offers):.1f}%)")

    # Top 10
    print(f"\n--- TOP 10 OFERTAS POR PRIORIDAD ---")
    print(f"{'ID':<12} {'Score':>6} {'Vac':>4} {'Perm':>6} {'Fecha':>12} Titulo")
    print("-" * 80)
    for o in offers[:10]:
        perm = (o['permanencia'] or '-')[:5]
        fecha = o['fecha_pub'] or '-'
        titulo = (o['titulo'] or '-')[:35]
        print(f"{o['id_oferta']:<12} {o['score_total']:>6.3f} {o['vacantes']:>4} {perm:>6} {fecha:>12} {titulo}")

    # Por portal
    print(f"\n--- POR PORTAL ---")
    by_portal = {}
    for o in offers:
        p = o['portal']
        if p not in by_portal:
            by_portal[p] = {'count': 0, 'avg_score': 0}
        by_portal[p]['count'] += 1
        by_portal[p]['avg_score'] += o['score_total']

    for p, data in sorted(by_portal.items(), key=lambda x: x[1]['count'], reverse=True):
        avg = data['avg_score'] / data['count']
        print(f"  {p}: {data['count']:,} ofertas (score promedio: {avg:.3f})")

    # Lotes estimados
    print(f"\n--- LOTES DE 100 ---")
    total_lotes = (len(offers) + 99) // 100
    print(f"  Total lotes: {total_lotes}")
    print(f"  Lote 1 (prioridad alta): IDs {offers[0]['id_oferta']} - {offers[min(99, len(offers)-1)]['id_oferta']}")
    if len(offers) > 100:
        print(f"  Lote 2: IDs {offers[100]['id_oferta']} - {offers[min(199, len(offers)-1)]['id_oferta']}")


def show_criteria(weights: dict, params: dict):
    """Muestra los criterios de priorización actuales."""
    print(f"\n{'='*60}")
    print(f"  CRITERIOS DE PRIORIZACION")
    print(f"{'='*60}")

    print(f"\n--- PESOS ---")
    for k, v in weights.items():
        print(f"  {k}: {v*100:.0f}%")

    print(f"\n--- PARAMETROS ---")
    print(f"\n  Fecha (frescura):")
    print(f"    Max dias para score 0: {params['fecha']['max_dias']}")

    print(f"\n  Vacantes (impacto):")
    print(f"    Max vacantes para score 1: {params['vacantes']['max_vacantes']}")
    print(f"    Boost multiples: {params['vacantes']['boost_multiple']}")

    print(f"\n  Permanencia (senal mercado):")
    for k, v in params['permanencia'].items():
        print(f"    {k}: {v}")


def get_batch(conn, weights: dict, params: dict, size: int = 100, offset: int = 0, export_format: str = None):
    """Obtiene un lote de ofertas ordenadas por prioridad."""
    offers = get_pending_offers_with_scores(conn, weights, params, limit=size, offset=offset)

    if not offers:
        print("No hay mas ofertas pendientes.")
        return []

    lote_num = (offset // size) + 1

    if export_format == 'ids':
        # Solo IDs para usar con pipeline
        ids = [str(o['id_oferta']) for o in offers]
        print(','.join(ids))
        return ids

    if export_format == 'json':
        print(json.dumps(offers, indent=2, ensure_ascii=False))
        return offers

    # Formato tabla
    print(f"\n{'='*60}")
    print(f"  LOTE {lote_num} - {len(offers)} OFERTAS (offset {offset})")
    print(f"{'='*60}")

    print(f"\n{'ID':<12} {'Score':>6} {'Vac':>4} {'Perm':>6} {'Portal':>10} Titulo")
    print("-" * 90)

    for o in offers:
        perm = (o['permanencia'] or '-')[:5]
        portal = (o['portal'] or '-')[:10]
        titulo = (o['titulo'] or '-')[:40]
        print(f"{o['id_oferta']:<12} {o['score_total']:>6.3f} {o['vacantes']:>4} {perm:>6} {portal:>10} {titulo}")

    # Resumen
    avg_score = sum(o['score_total'] for o in offers) / len(offers)
    total_vacantes = sum(o['vacantes'] for o in offers)

    print(f"\n--- RESUMEN LOTE ---")
    print(f"  Score promedio: {avg_score:.3f}")
    print(f"  Total vacantes: {total_vacantes}")
    print(f"  Rango fechas: {offers[-1]['fecha_pub']} a {offers[0]['fecha_pub']}")

    # Comando para procesar
    ids = ','.join(str(o['id_oferta']) for o in offers)
    print(f"\n--- COMANDO PARA PROCESAR ---")
    print(f"python scripts/run_validated_pipeline.py --ids {ids[:200]}...")

    return offers


# ============================================
# FUNCIONES DE PERSISTENCIA EN BD
# ============================================

def cleanup_stuck_processing(conn):
    """
    Sanea ofertas con estado inconsistente entre `ofertas_prioridad` y `ofertas_nlp`.

    Casos a corregir (lotes interrumpidos sin cierre limpio):
    - `en_proceso` + tiene NLP → marcar `procesado` (lote viejo se cortó después de NLP)
    - `en_proceso` + sin NLP → resetear a `pendiente` (lote se cortó antes de NLP)

    Las ofertas sin descripción procesable NO se purgan: el filtro en
    `get_pending_offers_with_scores` evita que entren a la cola, y existe
    `scripts/backfill_ct_descripciones.py` (y equivalentes) que completan
    descripciones faltantes visitando la URL del aviso. Una vez completas,
    el siguiente refresh las inserta al sistema con su score nuevo.

    Returns:
        dict con {'cerradas_completas': int, 'reseteadas_incompletas': int}
    """
    now = datetime.now().isoformat()

    cur = conn.execute('''
        UPDATE ofertas_prioridad
        SET estado = 'procesado', fecha_procesado = ?
        WHERE estado = 'en_proceso'
          AND EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = ofertas_prioridad.id_oferta)
    ''', (now,))
    cerradas = cur.rowcount

    cur = conn.execute('''
        UPDATE ofertas_prioridad
        SET estado = 'pendiente', lote_asignado = NULL,
            fecha_asignado = NULL, fecha_procesado = NULL
        WHERE estado = 'en_proceso'
          AND NOT EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = ofertas_prioridad.id_oferta)
    ''')
    reseteadas = cur.rowcount

    conn.commit()
    return {'cerradas_completas': cerradas, 'reseteadas_incompletas': reseteadas}


def refresh_priorities(conn, weights: dict = None, params: dict = None):
    """
    Recalcula y persiste prioridades para ofertas pendientes.

    Como `get_pending_offers_with_scores(from_db=False)` SOLO devuelve ofertas
    sin NLP, cualquier oferta que aparezca acá pero esté marcada como
    `procesado` o `en_proceso` en `ofertas_prioridad` es una "zombi": un lote
    se interrumpió antes de terminar y dejó la oferta marcada como completa
    sin que NLP la haya procesado. La reseteamos a `pendiente`.

    Antes del recálculo se ejecuta `cleanup_stuck_processing` para sanear
    lotes que quedaron a medio cerrar (en_proceso con NLP completo).

    1. Saneamiento previo de lotes interrumpidos
    2. Inserta ofertas nuevas (sin NLP y sin entrada en ofertas_prioridad)
    3. Actualiza scores de ofertas que ya están en `pendiente`
    4. Resetea zombi: ofertas en `procesado`/`en_proceso` que aún no tienen NLP

    Returns:
        dict con estadísticas: {'nuevas', 'actualizadas', 'reseteadas',
                                'cerradas_completas', 'reseteadas_incompletas'}
    """
    if weights is None:
        config = load_config()
        weights = config.get("weights", DEFAULT_WEIGHTS)
    if params is None:
        config = load_config()
        params = config.get("params", SCORING_PARAMS)

    # Saneamiento previo de lotes que quedaron a medio cerrar
    cleanup = cleanup_stuck_processing(conn)

    # Obtener ofertas pendientes calculando scores
    offers = get_pending_offers_with_scores(conn, weights, params, from_db=False)

    nuevas = 0
    actualizadas = 0
    reseteadas = 0
    now = datetime.now().isoformat()

    for o in offers:
        # Verificar si ya existe
        cur = conn.execute(
            'SELECT estado FROM ofertas_prioridad WHERE id_oferta = ?',
            (str(o['id_oferta']),)
        )
        row = cur.fetchone()

        if row is None:
            # Insertar nueva
            conn.execute('''
                INSERT INTO ofertas_prioridad
                (id_oferta, score_total, score_fecha, score_vacantes, score_permanencia,
                 estado, fecha_calculo)
                VALUES (?, ?, ?, ?, ?, 'pendiente', ?)
            ''', (str(o['id_oferta']), o['score_total'], o['score_fecha'],
                  o['score_vacantes'], o['score_permanencia'], now))
            nuevas += 1
        elif row['estado'] == 'pendiente':
            # Actualizar score (cambia con el tiempo)
            conn.execute('''
                UPDATE ofertas_prioridad
                SET score_total = ?, score_fecha = ?, score_vacantes = ?,
                    score_permanencia = ?, fecha_calculo = ?
                WHERE id_oferta = ?
            ''', (o['score_total'], o['score_fecha'], o['score_vacantes'],
                  o['score_permanencia'], now, str(o['id_oferta'])))
            actualizadas += 1
        elif row['estado'] in ('procesado', 'en_proceso'):
            # Zombi: marcado como completo pero sin NLP → resetear a pendiente
            conn.execute('''
                UPDATE ofertas_prioridad
                SET estado = 'pendiente',
                    score_total = ?, score_fecha = ?, score_vacantes = ?,
                    score_permanencia = ?, fecha_calculo = ?,
                    lote_asignado = NULL, fecha_asignado = NULL,
                    fecha_procesado = NULL
                WHERE id_oferta = ?
            ''', (o['score_total'], o['score_fecha'], o['score_vacantes'],
                  o['score_permanencia'], now, str(o['id_oferta'])))
            reseteadas += 1

    conn.commit()
    return {
        'nuevas': nuevas,
        'actualizadas': actualizadas,
        'reseteadas': reseteadas,
        'cerradas_completas': cleanup['cerradas_completas'],
        'reseteadas_incompletas': cleanup['reseteadas_incompletas'],
    }


def get_next_batch_from_db(conn, size: int = 100) -> list:
    """
    Obtiene el siguiente lote de ofertas desde BD (ya ordenado por prioridad).

    Returns:
        Lista de dicts con datos de oferta y scores
    """
    cur = conn.execute('''
        SELECT
            p.id_oferta,
            p.score_total,
            p.score_fecha,
            p.score_vacantes,
            p.score_permanencia,
            o.titulo,
            o.empresa,
            o.portal,
            o.cantidad_vacantes,
            o.categoria_permanencia
        FROM ofertas_prioridad p
        JOIN ofertas o ON p.id_oferta = o.id_oferta
        WHERE p.estado = 'pendiente'
        ORDER BY p.score_total DESC
        LIMIT ?
    ''', (size,))

    return [{
        'id_oferta': row['id_oferta'],
        'score_total': row['score_total'],
        'score_fecha': row['score_fecha'],
        'score_vacantes': row['score_vacantes'],
        'score_permanencia': row['score_permanencia'],
        'titulo': row['titulo'],
        'empresa': row['empresa'],
        'portal': row['portal'],
        'vacantes': row['cantidad_vacantes'] or 1,
        'permanencia': row['categoria_permanencia']
    } for row in cur.fetchall()]


def mark_batch_as_processing(conn, offer_ids: list, lote_id: str):
    """
    Marca ofertas como 'en_proceso' y asigna ID de lote.

    Args:
        offer_ids: Lista de IDs de ofertas
        lote_id: Identificador del lote (ej: "lote_20260120_1530")
    """
    now = datetime.now().isoformat()
    for oid in offer_ids:
        conn.execute('''
            UPDATE ofertas_prioridad
            SET estado = 'en_proceso',
                lote_asignado = ?,
                fecha_asignado = ?
            WHERE id_oferta = ?
        ''', (lote_id, now, str(oid)))
    conn.commit()


def mark_batch_as_completed(conn, offer_ids: list, run_id: str = None) -> dict:
    """
    Marca el final de un lote: solo cierra como 'procesado' las ofertas que
    efectivamente quedaron persistidas; las que faltan vuelven a 'pendiente'
    para reintentar en el próximo lote.

    Si `run_id` se proporciona: el criterio es tener entry en
    `ofertas_esco_matching` para ese run_id (cubre zombies post-matching).
    Si no se proporciona: criterio legacy = tener NLP en BD (cubre zombies
    post-NLP, que es lo único que se puede chequear si skip_matching=True).

    Args:
        offer_ids: Lista de IDs de ofertas asignadas al lote
        run_id: Si se pasa, verifica matching del run específico en lugar de NLP

    Returns:
        dict con {'cerradas': int, 'reseteadas': int}
    """
    if not offer_ids:
        return {'cerradas': 0, 'reseteadas': 0}

    now = datetime.now().isoformat()
    ids_str = [str(oid) for oid in offer_ids]
    placeholders = ','.join('?' for _ in ids_str)

    if run_id:
        cur = conn.execute(
            f'''
            UPDATE ofertas_prioridad
            SET estado = 'procesado', fecha_procesado = ?
            WHERE id_oferta IN ({placeholders})
              AND EXISTS (
                  SELECT 1 FROM ofertas_esco_matching m
                  WHERE m.id_oferta = ofertas_prioridad.id_oferta
                    AND m.run_id = ?
              )
            ''',
            [now, *ids_str, run_id],
        )
        cerradas = cur.rowcount

        cur = conn.execute(
            f'''
            UPDATE ofertas_prioridad
            SET estado = 'pendiente',
                lote_asignado = NULL,
                fecha_asignado = NULL,
                fecha_procesado = NULL
            WHERE id_oferta IN ({placeholders})
              AND NOT EXISTS (
                  SELECT 1 FROM ofertas_esco_matching m
                  WHERE m.id_oferta = ofertas_prioridad.id_oferta
                    AND m.run_id = ?
              )
            ''',
            [*ids_str, run_id],
        )
        reseteadas = cur.rowcount
    else:
        cur = conn.execute(
            f'''
            UPDATE ofertas_prioridad
            SET estado = 'procesado', fecha_procesado = ?
            WHERE id_oferta IN ({placeholders})
              AND EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = ofertas_prioridad.id_oferta)
            ''',
            [now, *ids_str],
        )
        cerradas = cur.rowcount

        cur = conn.execute(
            f'''
            UPDATE ofertas_prioridad
            SET estado = 'pendiente',
                lote_asignado = NULL,
                fecha_asignado = NULL,
                fecha_procesado = NULL
            WHERE id_oferta IN ({placeholders})
              AND NOT EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = ofertas_prioridad.id_oferta)
            ''',
            ids_str,
        )
        reseteadas = cur.rowcount

    conn.commit()
    return {'cerradas': cerradas, 'reseteadas': reseteadas}


def check_pending_errors_block(conn) -> dict:
    """
    Verifica si hay errores pendientes que bloquean nuevo procesamiento.

    Returns:
        {'blocked': bool, 'lote': str, 'errores': int, 'ids': list}
    """
    cur = conn.execute('''
        SELECT
            p.lote_asignado,
            COUNT(DISTINCT e.id_oferta) as errores,
            GROUP_CONCAT(DISTINCT p.id_oferta) as ids
        FROM ofertas_prioridad p
        JOIN validation_errors e ON p.id_oferta = e.id_oferta
        WHERE p.estado = 'procesado'
          AND e.resuelto = 0
          AND e.escalado_claude = 1
        GROUP BY p.lote_asignado
        ORDER BY p.lote_asignado DESC
        LIMIT 1
    ''')
    row = cur.fetchone()

    if row and row['errores'] > 0:
        ids_str = row['ids'] or ''
        return {
            'blocked': True,
            'lote': row['lote_asignado'],
            'errores': row['errores'],
            'ids': ids_str.split(',')[:10] if ids_str else []
        }
    return {'blocked': False, 'lote': None, 'errores': 0, 'ids': []}


def get_queue_status(conn) -> dict:
    """
    Obtiene estado actual de la cola de procesamiento.

    Returns:
        dict con métricas de la cola
    """
    cur = conn.execute('''
        SELECT
            SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
            SUM(CASE WHEN estado = 'en_proceso' THEN 1 ELSE 0 END) as en_proceso,
            SUM(CASE WHEN estado = 'procesado' THEN 1 ELSE 0 END) as procesados,
            COUNT(DISTINCT lote_asignado) as lotes_creados,
            ROUND(AVG(CASE WHEN estado = 'pendiente' THEN score_total END), 3) as score_promedio,
            MAX(CASE WHEN estado = 'pendiente' THEN score_total END) as score_max,
            MIN(CASE WHEN estado = 'pendiente' THEN score_total END) as score_min
        FROM ofertas_prioridad
    ''')
    row = cur.fetchone()

    # Verificar bloqueo
    block_info = check_pending_errors_block(conn)

    return {
        'pendientes': row['pendientes'] or 0,
        'en_proceso': row['en_proceso'] or 0,
        'procesados': row['procesados'] or 0,
        'lotes_creados': row['lotes_creados'] or 0,
        'score_promedio': row['score_promedio'] or 0,
        'score_max': row['score_max'] or 0,
        'score_min': row['score_min'] or 0,
        'bloqueado': block_info['blocked'],
        'lote_bloqueado': block_info['lote'],
        'errores_bloqueo': block_info['errores'],
        'ids_bloqueo': block_info['ids']
    }


# ============================================
# CLI
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description='Obtener lotes de ofertas ordenados por prioridad',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--size', type=int, default=100, help='Tamano del lote (default: 100)')
    parser.add_argument('--offset', type=int, default=0, help='Offset para siguiente lote')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadisticas')
    parser.add_argument('--criteria', action='store_true', help='Mostrar criterios actuales')
    parser.add_argument('--export', choices=['ids', 'json'], help='Exportar en formato especifico')
    parser.add_argument('--save-config', action='store_true', help='Guardar configuracion default')

    # Nuevos comandos para persistencia
    parser.add_argument('--refresh', action='store_true', help='Recalcular y persistir prioridades en BD')
    parser.add_argument('--queue-status', action='store_true', help='Mostrar estado de la cola de procesamiento')
    parser.add_argument('--from-db', action='store_true', help='Leer desde BD en vez de calcular (mas rapido)')

    # Opciones para ajustar pesos
    parser.add_argument('--peso-fecha', type=float, help='Peso para fecha (0-1)')
    parser.add_argument('--peso-vacantes', type=float, help='Peso para vacantes (0-1)')
    parser.add_argument('--peso-permanencia', type=float, help='Peso para permanencia (0-1)')

    args = parser.parse_args()

    # Cargar o crear config
    config = load_config()
    weights = config.get("weights", DEFAULT_WEIGHTS).copy()
    params = config.get("params", SCORING_PARAMS)

    # Ajustar pesos si se especifican
    if args.peso_fecha is not None:
        weights["fecha_publicacion"] = args.peso_fecha
    if args.peso_vacantes is not None:
        weights["cantidad_vacantes"] = args.peso_vacantes
    if args.peso_permanencia is not None:
        weights["permanencia"] = args.peso_permanencia

    # Normalizar pesos
    total_peso = sum(weights.values())
    if total_peso != 1.0:
        for k in weights:
            weights[k] /= total_peso

    # Guardar config si se pide
    if args.save_config:
        save_config({"weights": weights, "params": params})
        print(f"Configuracion guardada en {CONFIG_PATH}")
        return 0

    conn = get_connection()

    if args.criteria:
        show_criteria(weights, params)
    elif args.stats:
        show_stats(conn, weights, params)
    elif args.refresh:
        # Recalcular y persistir prioridades
        print("Recalculando prioridades...")
        result = refresh_priorities(conn, weights, params)
        print(f"  Nuevas: {result['nuevas']}")
        print(f"  Actualizadas: {result['actualizadas']}")
        print(f"  Zombi reseteadas (sin NLP marcadas como procesado): {result['reseteadas']}")
        print(f"  Lotes huérfanos cerrados (en_proceso con NLP completo): {result['cerradas_completas']}")
        print(f"  Lotes huérfanos reseteados (en_proceso sin NLP): {result['reseteadas_incompletas']}")
        print(f"Prioridades persistidas en ofertas_prioridad")
    elif args.queue_status:
        # Mostrar estado de la cola
        status = get_queue_status(conn)
        print(f"\n{'='*60}")
        print(f"  ESTADO DE LA COLA DE PROCESAMIENTO")
        print(f"{'='*60}")
        print(f"\n  Pendientes:  {status['pendientes']:,}")
        print(f"  En proceso:  {status['en_proceso']:,}")
        print(f"  Procesados:  {status['procesados']:,}")
        print(f"  Lotes:       {status['lotes_creados']}")
        if status['score_promedio']:
            print(f"\n  Score promedio pendientes: {status['score_promedio']:.3f}")
            print(f"  Score rango: {status['score_min']:.3f} - {status['score_max']:.3f}")

        if status['bloqueado']:
            print(f"\n  [BLOQUEADO] Lote {status['lote_bloqueado']} tiene {status['errores_bloqueo']} errores")
            print(f"  IDs: {','.join(status['ids_bloqueo'][:5])}{'...' if len(status['ids_bloqueo']) > 5 else ''}")
            print(f"\n  Para desbloquear:")
            print(f"    python scripts/run_validated_pipeline.py --ids {','.join(status['ids_bloqueo'])}")
        else:
            print(f"\n  Estado: LISTO para procesar")
            print(f"\n  Para procesar siguiente lote:")
            print(f"    python scripts/run_validated_pipeline.py --limit 100")
    else:
        get_batch(conn, weights, params, size=args.size, offset=args.offset, export_format=args.export)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
