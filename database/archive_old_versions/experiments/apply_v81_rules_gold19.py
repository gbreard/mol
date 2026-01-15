#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplica reglas v8.1 a las 19 ofertas del gold set.
Re-calcula score_final y flags de confirmación/revisión.

Uso:
    python apply_v81_rules_gold19.py          # Interactivo
    python apply_v81_rules_gold19.py --apply  # Aplicar sin confirmación
"""

import sqlite3
import struct
import sys
from pathlib import Path

from matching_rules_v81 import (
    calcular_ajustes_v81,
    requiere_revision_forzada
)

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# IDs del gold set 19
GOLD_SET_IDS = [
    "1118026700", "1118026729", "1118027188", "1118027243", "1118027261",
    "1118027276", "1118027662", "1118027834", "1118027941", "1118028027",
    "1118028038", "1118028201", "1118028376", "1118028657", "1118028681",
    "1118028828", "1118028833", "1118028887", "1118028891"
]

# Thresholds (mismos que v8.0)
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


def main():
    print("=" * 70)
    print("APLICANDO REGLAS v8.1 AL GOLD SET 19")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Obtener datos actuales
    placeholders = ','.join(['?'] * len(GOLD_SET_IDS))
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
        WHERE m.id_oferta IN ({placeholders})
    ''', GOLD_SET_IDS)

    rows = cursor.fetchall()
    print(f"\nOfertas encontradas: {len(rows)}")

    updates = []

    print("\n" + "-" * 70)
    print(f"{'ID':<12} | {'TITULO':<25} | {'SC_ANT':>6} | {'SC_NVO':>6} | {'AJUSTE':>6} | {'ANT':>4} | {'NVO':>4}")
    print("-" * 70)

    for row in rows:
        id_oferta = row['id_oferta']
        titulo = row['titulo'] or ''
        descripcion = row['descripcion'] or ''
        esco_label = row['esco_occupation_label'] or ''
        score_original = parse_score(row['score_final_ponderado'])
        conf_anterior = 'CONF' if row['match_confirmado'] else ('REV' if row['requiere_revision'] else 'RECH')

        # Aplicar ajustes v8.1
        ajuste_total, ajustes_detalle = calcular_ajustes_v81(titulo, descripcion, esco_label)
        score_nuevo = max(0.0, min(1.0, score_original + ajuste_total))

        # Verificar revisión forzada
        forzar_revision = requiere_revision_forzada(titulo)

        # Determinar nuevo estado (usamos score como proxy ya que no tenemos coverage_score)
        if forzar_revision:
            match_confirmado = 0
            requiere_revision = 1
        elif score_nuevo >= THRESHOLD_CONFIRMADO_SCORE:
            match_confirmado = 1
            requiere_revision = 0
        elif score_nuevo >= THRESHOLD_REVISION:
            match_confirmado = 0
            requiere_revision = 1
        else:
            match_confirmado = 0
            requiere_revision = 0

        conf_nuevo = 'CONF' if match_confirmado else ('REV' if requiere_revision else 'RECH')

        # Mostrar cambio
        ajuste_str = f"{ajuste_total:+.2f}" if ajuste_total != 0 else "0.00"
        cambio = " *" if conf_anterior != conf_nuevo or ajuste_total != 0 else ""
        print(f"{id_oferta:<12} | {titulo[:25]:<25} | {score_original:>6.3f} | {score_nuevo:>6.3f} | {ajuste_str:>6} | {conf_anterior:>4} | {conf_nuevo:>4}{cambio}")

        if ajustes_detalle:
            print(f"             | Ajustes: {ajustes_detalle}")

        updates.append((score_nuevo, match_confirmado, requiere_revision, id_oferta))

    # Confirmar actualización
    print("\n" + "=" * 70)
    cambios = sum(1 for u in updates if u[0] != parse_score(rows[updates.index(u)]['score_final_ponderado']) or u[1] != rows[updates.index(u)]['match_confirmado'])
    print(f"Cambios detectados: {len([u for u in updates if u[1] == 0 and u[2] == 1])} -> REVISION")

    # Verificar si se pasó --apply
    auto_apply = '--apply' in sys.argv
    if auto_apply:
        respuesta = 's'
    else:
        respuesta = input("\n¿Aplicar cambios a la DB? [s/N]: ").strip().lower()

    if respuesta == 's':
        for score, conf, rev, id_oferta in updates:
            cursor.execute('''
                UPDATE ofertas_esco_matching
                SET score_final_ponderado = ?,
                    match_confirmado = ?,
                    requiere_revision = ?,
                    matching_version = 'v8.1_esco_multicriterio_validado',
                    matching_timestamp = datetime('now')
                WHERE id_oferta = ?
            ''', (score, conf, rev, id_oferta))

        conn.commit()
        print("\n[OK] Cambios aplicados exitosamente")
    else:
        print("\n[!] Cambios NO aplicados")

    conn.close()
    print("=" * 70)


if __name__ == '__main__':
    main()
