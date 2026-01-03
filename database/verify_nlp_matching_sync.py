#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificar sincronizacion entre NLP v8.0 y Matching
"""

import sqlite3
import json
import struct
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def parse_score(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 4:
            return struct.unpack('f', value)[0]
        elif len(value) == 8:
            return struct.unpack('d', value)[0]
    return 0.0

def parse_nested_json(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except:
            return []
    return []

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("VERIFICACION SINCRONIZACION NLP v8.0 vs MATCHING")
    print("=" * 80)

    # 1. Confirmar total con nlp_version = '8.0.0'
    print("\n1. TOTAL CON NLP v8.0.0")
    print("-" * 40)
    cursor.execute("SELECT COUNT(*) FROM validacion_v7 WHERE nlp_version = '8.0.0'")
    total_nlp = cursor.fetchone()[0]
    print(f"   Total ofertas con nlp_version='8.0.0': {total_nlp}")

    # 2. De esas, cuantas tienen matching
    print("\n2. ESTADO DE MATCHING EN LAS {0}".format(total_nlp))
    print("-" * 40)

    # IDs con NLP v8.0
    cursor.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.0.0'")
    nlp_ids = [str(row[0]) for row in cursor.fetchall()]

    # Cuantas tienen esco_codigo
    placeholders = ','.join(['?'] * len(nlp_ids))
    cursor.execute(f"""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE id_oferta IN ({placeholders}) AND esco_occupation_uri IS NOT NULL
    """, nlp_ids)
    con_esco = cursor.fetchone()[0]
    print(f"   Con esco_uri asignado: {con_esco}/{total_nlp}")

    # Cuantas tienen score > 0
    cursor.execute(f"""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE id_oferta IN ({placeholders}) AND score_final_ponderado > 0
    """, nlp_ids)
    con_score = cursor.fetchone()[0]
    print(f"   Con matching_score > 0: {con_score}/{total_nlp}")

    # Cuantas tienen skills_tecnicas no vacio en NLP
    cursor.execute("SELECT resultado_capa1_verificado FROM validacion_v7 WHERE nlp_version = '8.0.0'")
    con_skills_tec = 0
    for row in cursor.fetchall():
        if row[0]:
            try:
                data = json.loads(row[0])
                skills = parse_nested_json(data.get('skills_tecnicas_list'))
                if skills:
                    con_skills_tec += 1
            except:
                pass
    print(f"   Con skills_tecnicas no vacio: {con_skills_tec}/{total_nlp}")

    # 3. Ejemplos con todos los campos
    print("\n3. EJEMPLOS DETALLADOS (3 ofertas)")
    print("-" * 40)

    cursor.execute(f"""
        SELECT
            v.id_oferta,
            v.nlp_version,
            v.timestamp as nlp_timestamp,
            v.resultado_capa1_verificado,
            m.esco_occupation_uri,
            m.esco_occupation_label,
            m.score_final_ponderado,
            m.matching_version,
            m.matching_timestamp
        FROM validacion_v7 v
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0'
        LIMIT 3
    """)

    for i, row in enumerate(cursor.fetchall(), 1):
        (id_oferta, nlp_ver, nlp_ts, nlp_json,
         esco_code, esco_label, score, match_ver, match_ts) = row

        skills_tec = []
        skills_soft = []
        if nlp_json:
            try:
                data = json.loads(nlp_json)
                skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
                skills_soft = parse_nested_json(data.get('soft_skills_list'))
            except:
                pass

        score = parse_score(score)

        print(f"\n[{i}] ID: {id_oferta}")
        print(f"    NLP:")
        print(f"      - nlp_version: {nlp_ver}")
        print(f"      - timestamp: {nlp_ts}")
        print(f"      - skills_tecnicas: {skills_tec if skills_tec else '[VACIO]'}")
        print(f"      - skills_blandas: {skills_soft[:3] if skills_soft else '[VACIO]'}")
        print(f"    MATCHING:")
        print(f"      - esco_codigo: {esco_code if esco_code else '[SIN MATCH]'}")
        print(f"      - esco_label: {esco_label[:50] if esco_label else '[SIN MATCH]'}...")
        print(f"      - score: {score:.3f}")
        print(f"      - matching_version: {match_ver}")
        print(f"      - timestamp: {match_ts}")

        # Comparar fechas
        if nlp_ts and match_ts:
            try:
                nlp_dt = datetime.fromisoformat(nlp_ts.replace('Z', '+00:00').split('.')[0])
                match_dt = datetime.fromisoformat(match_ts.replace('Z', '+00:00').split('.')[0])
                if match_dt > nlp_dt:
                    print(f"    [OK] Matching POSTERIOR al NLP")
                else:
                    print(f"    [!] Matching ANTERIOR al NLP - NECESITA RE-CORRER")
            except:
                print(f"    [?] No se pudo comparar fechas")

    # 4. Verificar si hay que re-correr matching
    print("\n" + "=" * 80)
    print("4. DIAGNOSTICO")
    print("=" * 80)

    cursor.execute(f"""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE id_oferta IN ({placeholders})
    """, nlp_ids)
    total_con_match = cursor.fetchone()[0]

    sin_match = total_nlp - total_con_match

    print(f"\n   Ofertas con NLP v8.0: {total_nlp}")
    print(f"   Ofertas con matching: {total_con_match}")
    print(f"   Ofertas SIN matching: {sin_match}")

    if sin_match > 0:
        print(f"\n   [!] HAY {sin_match} OFERTAS CON NLP v8.0 SIN MATCHING")
        print(f"   [!] NECESITAN RE-CORRER match_ofertas_multicriteria.py")

    # Verificar fechas
    cursor.execute(f"""
        SELECT v.id_oferta, v.timestamp, m.matching_timestamp
        FROM validacion_v7 v
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0' AND m.matching_timestamp IS NOT NULL
    """)

    matching_anterior = 0
    for row in cursor.fetchall():
        nlp_ts, match_ts = row[1], row[2]
        if nlp_ts and match_ts:
            try:
                nlp_dt = datetime.fromisoformat(nlp_ts.split('.')[0])
                match_dt = datetime.fromisoformat(match_ts.split('.')[0])
                if match_dt < nlp_dt:
                    matching_anterior += 1
            except:
                pass

    if matching_anterior > 0:
        print(f"\n   [!] {matching_anterior} ofertas tienen MATCHING ANTERIOR al NLP")
        print(f"   [!] El matching NO uso los datos del NLP v8.0")

    if sin_match == 0 and matching_anterior == 0:
        print(f"\n   [OK] Matching esta sincronizado con NLP v8.0")

    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
