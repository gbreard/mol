#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplica reglas v8.2 (Familias Funcionales) a un batch de ofertas.
Genera estadisticas y muestra muestra de CONFIRMADOS para revision.

Uso:
    python apply_v82_rules_batch.py               # Solo simular (no aplica)
    python apply_v82_rules_batch.py --apply       # Aplicar cambios
    python apply_v82_rules_batch.py --limit 200   # Limitar a N ofertas
"""

import sqlite3
import struct
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

from matching_rules_v83 import calcular_ajustes_v83

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Thresholds v8.2
THRESHOLD_CONFIRMADO_SCORE = 0.60
THRESHOLD_REVISION = 0.50


def parse_score(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 8:
            return struct.unpack('d', value)[0]
        elif len(value) == 4:
            return struct.unpack('f', value)[0]
    return 0.0


def get_percentiles(values: List[float]) -> dict:
    """Calcula estadisticas de una lista de valores."""
    if not values:
        return {"min": 0, "p25": 0, "p50": 0, "p75": 0, "max": 0}

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def percentile(p):
        k = (n - 1) * p / 100
        f = int(k)
        c = f + 1 if f < n - 1 else f
        return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)

    return {
        "min": sorted_vals[0],
        "p25": percentile(25),
        "p50": percentile(50),
        "p75": percentile(75),
        "max": sorted_vals[-1],
        "count": n
    }


def main():
    parser = argparse.ArgumentParser(description='Aplicar reglas v8.2 a batch de ofertas')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios a la DB')
    parser.add_argument('--limit', type=int, default=200, help='Limite de ofertas a procesar')
    parser.add_argument('--sample', type=int, default=20, help='Muestra de CONFIRMADOS a mostrar')
    args = parser.parse_args()

    print("=" * 90)
    print(f"APLICANDO REGLAS v8.2 (FAMILIAS FUNCIONALES) - BATCH {args.limit}")
    print("=" * 90)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Obtener ofertas (excluyendo Gold Set 19 para no duplicar)
    GOLD_SET_IDS = [
        "1118026700", "1118026729", "1118027188", "1118027243", "1118027261",
        "1118027276", "1118027662", "1118027834", "1118027941", "1118028027",
        "1118028038", "1118028201", "1118028376", "1118028657", "1118028681",
        "1118028828", "1118028833", "1118028887", "1118028891"
    ]

    placeholders_exclude = ','.join(['?'] * len(GOLD_SET_IDS))

    cursor.execute(f'''
        SELECT
            m.id_oferta,
            o.titulo,
            o.descripcion,
            m.esco_occupation_label,
            m.score_final_ponderado,
            m.match_confirmado,
            m.requiere_revision
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.id_oferta NOT IN ({placeholders_exclude})
        LIMIT ?
    ''', GOLD_SET_IDS + [args.limit])

    rows = cursor.fetchall()
    print(f"\nOfertas a procesar: {len(rows)}")

    updates = []
    scores_antes = []
    scores_despues = []
    never_confirm_count = 0
    conf_to_rev = 0
    rev_to_rech = 0
    confirmados_sample = []

    for row in rows:
        id_oferta = row['id_oferta']
        titulo = row['titulo'] or ''
        descripcion = row['descripcion'] or ''
        esco_label = row['esco_occupation_label'] or ''
        score_original = parse_score(row['score_final_ponderado'])
        match_confirmado_ant = row['match_confirmado']
        requiere_revision_ant = row['requiere_revision']

        scores_antes.append(score_original)

        # Aplicar ajustes v8.3
        ajuste_total, ajustes_detalle, never_confirm = calcular_ajustes_v83(titulo, descripcion, esco_label)
        score_nuevo = max(0.0, min(1.0, score_original + ajuste_total))
        scores_despues.append(score_nuevo)

        if never_confirm:
            never_confirm_count += 1

        # Determinar nuevo estado
        if never_confirm:
            if score_nuevo >= THRESHOLD_REVISION:
                match_confirmado = 0
                requiere_revision = 1
            else:
                match_confirmado = 0
                requiere_revision = 0
        elif score_nuevo >= THRESHOLD_CONFIRMADO_SCORE:
            match_confirmado = 1
            requiere_revision = 0
        elif score_nuevo >= THRESHOLD_REVISION:
            match_confirmado = 0
            requiere_revision = 1
        else:
            match_confirmado = 0
            requiere_revision = 0

        # Contar transiciones
        if match_confirmado_ant and not match_confirmado:
            conf_to_rev += 1
        if requiere_revision_ant and not requiere_revision and not match_confirmado:
            rev_to_rech += 1

        # Guardar muestra de CONFIRMADOS para revision
        if match_confirmado and len(confirmados_sample) < args.sample:
            confirmados_sample.append({
                'id': id_oferta,
                'titulo': titulo[:50],
                'esco': esco_label[:50],
                'score': score_nuevo,
                'ajuste': ajuste_total
            })

        updates.append((score_nuevo, match_confirmado, requiere_revision, id_oferta))

    # Estadisticas
    stats_antes = get_percentiles(scores_antes)
    stats_despues = get_percentiles(scores_despues)

    print("\n" + "=" * 90)
    print("ESTADISTICAS DE SCORES:")
    print("-" * 90)
    print(f"{'':15} | {'MIN':>6} | {'P25':>6} | {'P50':>6} | {'P75':>6} | {'MAX':>6} | {'N':>5}")
    print("-" * 90)
    print(f"{'ANTES v8.2':15} | {stats_antes['min']:>6.3f} | {stats_antes['p25']:>6.3f} | {stats_antes['p50']:>6.3f} | {stats_antes['p75']:>6.3f} | {stats_antes['max']:>6.3f} | {stats_antes['count']:>5}")
    print(f"{'DESPUES v8.2':15} | {stats_despues['min']:>6.3f} | {stats_despues['p25']:>6.3f} | {stats_despues['p50']:>6.3f} | {stats_despues['p75']:>6.3f} | {stats_despues['max']:>6.3f} | {stats_despues['count']:>5}")
    print("-" * 90)

    # Conteo de estados finales
    final_conf = sum(1 for u in updates if u[1] == 1)
    final_rev = sum(1 for u in updates if u[1] == 0 and u[2] == 1)
    final_rech = sum(1 for u in updates if u[1] == 0 and u[2] == 0)

    print(f"\nESTADOS FINALES:")
    print(f"  CONFIRMADOS:  {final_conf:>5} ({100*final_conf/len(updates):.1f}%)")
    print(f"  REVISION:     {final_rev:>5} ({100*final_rev/len(updates):.1f}%)")
    print(f"  RECHAZADOS:   {final_rech:>5} ({100*final_rech/len(updates):.1f}%)")

    print(f"\nTRANSICIONES:")
    print(f"  never_confirm activado:  {never_confirm_count}")
    print(f"  CONF -> REV/RECH:        {conf_to_rev}")
    print(f"  REV -> RECH:             {rev_to_rech}")

    # Muestra de CONFIRMADOS para revision manual
    print("\n" + "=" * 90)
    print(f"MUESTRA DE {len(confirmados_sample)} CONFIRMADOS PARA REVISION MANUAL:")
    print("-" * 90)
    print(f"{'ID':<12} | {'TITULO':<50} | {'SCORE':>6}")
    print("-" * 90)
    for c in confirmados_sample:
        print(f"{c['id']:<12} | {c['titulo']:<50} | {c['score']:>6.3f}")
        print(f"             | ESCO: {c['esco']}")
    print("=" * 90)

    # Aplicar cambios
    if args.apply:
        print("\n[!] Aplicando cambios a la base de datos...")
        for score, conf, rev, id_oferta in updates:
            cursor.execute('''
                UPDATE ofertas_esco_matching
                SET score_final_ponderado = ?,
                    match_confirmado = ?,
                    requiere_revision = ?,
                    matching_version = 'v8.3_esco_familias_funcionales',
                    matching_timestamp = datetime('now')
                WHERE id_oferta = ?
            ''', (score, conf, rev, id_oferta))
        conn.commit()
        print(f"[OK] {len(updates)} ofertas actualizadas")
    else:
        print("\n[!] Modo simulacion - cambios NO aplicados")
        print("    Use --apply para aplicar los cambios")

    conn.close()
    print("=" * 90)


if __name__ == '__main__':
    main()
