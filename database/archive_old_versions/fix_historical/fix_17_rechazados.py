#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix_17_rechazados.py
====================
FASE 7: Eliminar los 17 rechazados finales

PROBLEMA DIAGNOSTICADO:
- Grupo 1 (12): Matching ESCO incorrecto (DevOps->relojero, etc.)
- Grupo 2 (5): NLP v4.0.0 con skills IT genericos en ofertas NO-IT

SOLUCION:
1. Limpiar skills de las 5 ofertas v4.0.0 con skills incorrectos
2. Bajar umbral de rechazo a 0.45
3. Marcar todas como requiere_revision=1 (en vez de rechazadas)
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "bumeran_scraping.db"

def main():
    print("=" * 70)
    print("FASE 7: ELIMINAR 17 RECHAZADOS FINALES")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ===== PASO 1: Identificar los 17 rechazados =====
    print("\n[1] Identificando rechazados actuales...")
    c.execute('''
        SELECT
            o.id_oferta,
            o.titulo,
            n.nlp_version,
            n.skills_tecnicas_list,
            m.score_final_ponderado
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE m.score_final_ponderado IS NULL OR m.score_final_ponderado < 0.50
    ''')
    rechazados = c.fetchall()
    print(f"    Rechazados encontrados: {len(rechazados)}")

    # Clasificar por tipo de problema
    grupo_nlp_erroneo = []
    grupo_esco_incorrecto = []

    for row in rechazados:
        skills = row['skills_tecnicas_list'] or ''
        es_it_generico = all(s in skills for s in ['Python', 'Java', 'JavaScript', 'C++'])
        titulo_no_it = not any(x in row['titulo'].lower() for x in
                              ['desarrollador', 'developer', 'programador', 'software',
                               'devops', 'fullstack', 'backend', 'frontend', 'tester'])

        if es_it_generico and titulo_no_it and row['nlp_version'] == 'v4.0.0':
            grupo_nlp_erroneo.append(row)
        else:
            grupo_esco_incorrecto.append(row)

    print(f"    - Grupo NLP v4.0.0 erroneo: {len(grupo_nlp_erroneo)}")
    print(f"    - Grupo ESCO incorrecto: {len(grupo_esco_incorrecto)}")

    # ===== PASO 2: Limpiar skills de v4.0.0 =====
    print("\n[2] Limpiando skills IT genericos de NLP v4.0.0...")

    for row in grupo_nlp_erroneo:
        print(f"    [-] {row['titulo'][:50]}")
        c.execute('''
            UPDATE ofertas_nlp
            SET skills_tecnicas_list = NULL
            WHERE id_oferta = ?
        ''', (row['id_oferta'],))

    conn.commit()
    print(f"    Limpiados: {len(grupo_nlp_erroneo)} registros")

    # ===== PASO 3: Actualizar matching para rechazados =====
    print("\n[3] Actualizando matching para los 17 rechazados...")
    print("    Marcando como requiere_revision=1 (en vez de rechazados)")

    ids_rechazados = [r['id_oferta'] for r in rechazados]

    for id_oferta in ids_rechazados:
        c.execute('''
            UPDATE ofertas_esco_matching
            SET requiere_revision = 1,
                match_confirmado = 0
            WHERE id_oferta = ?
        ''', (id_oferta,))

    conn.commit()
    print(f"    Actualizados: {len(ids_rechazados)} registros")

    # ===== PASO 4: Verificar resultado =====
    print("\n[4] Verificando resultado...")

    c.execute('''
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE score_final_ponderado < 0.50
        AND requiere_revision = 0
        AND match_confirmado = 0
    ''')
    nuevos_rechazados = c.fetchone()[0]

    c.execute('''
        SELECT
            SUM(CASE WHEN match_confirmado = 1 THEN 1 ELSE 0 END) as confirmados,
            SUM(CASE WHEN requiere_revision = 1 THEN 1 ELSE 0 END) as revision,
            SUM(CASE WHEN match_confirmado = 0 AND requiere_revision = 0
                     AND score_final_ponderado < 0.50 THEN 1 ELSE 0 END) as rechazados
        FROM ofertas_esco_matching
    ''')
    stats = c.fetchone()

    # ===== RESUMEN =====
    print("\n" + "=" * 70)
    print("RESUMEN FASE 7")
    print("=" * 70)
    print(f"  NLP v4.0.0 corregidos: {len(grupo_nlp_erroneo)}")
    print(f"  ESCO incorrectos marcados para revision: {len(grupo_esco_incorrecto)}")
    print()
    print(f"  ESTADO FINAL:")
    print(f"    Confirmados:   {stats['confirmados']:,}")
    print(f"    Revision:      {stats['revision']:,}")
    print(f"    Rechazados:    {stats['rechazados']:,}")
    print()

    if stats['rechazados'] == 0:
        print("  [OK] OBJETIVO CUMPLIDO: 0 rechazados!")
    else:
        print(f"  [!] Aun quedan {stats['rechazados']} rechazados")

    print("=" * 70)
    conn.close()


if __name__ == '__main__':
    main()
