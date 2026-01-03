#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug: Why Mozo boost is not working"""

import sqlite3
from pathlib import Path
from normalizacion_arg import normalizar_termino_argentino, obtener_boost_isco

base = Path(__file__).parent
conn = sqlite3.connect(base / 'bumeran_scraping.db')
conn.row_factory = sqlite3.Row

# Get Mozo offer
c = conn.cursor()
c.execute("""
    SELECT o.titulo, o.descripcion, m.esco_occupation_label, m.isco_code, m.occupation_match_score
    FROM ofertas o
    JOIN ofertas_esco_matching m ON CAST(o.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
    WHERE o.id_oferta = '2164100'
""")
row = c.fetchone()

if row:
    titulo = row['titulo']
    esco_label = row['esco_occupation_label']
    isco = row['isco_code']
    score = row['occupation_match_score']

    print("=" * 60)
    print("CASO MOZO (id: 2164100)")
    print("=" * 60)
    print(f"Titulo: {titulo}")
    print(f"ESCO actual: {esco_label}")
    print(f"ISCO actual: {isco}")
    print(f"Score: {score}")

    print("\n" + "-" * 60)
    print("NORMALIZACION:")
    print("-" * 60)
    termino, isco_target, esco_label_dict, titulo_norm = normalizar_termino_argentino(titulo, conn)
    print(f"Termino encontrado: {termino}")
    print(f"ISCO target del diccionario: {isco_target}")
    print(f"ESCO label del diccionario: {esco_label_dict}")
    print(f"Titulo normalizado: {titulo_norm}")

    print("\n" + "-" * 60)
    print("SIMULACION DE BOOST:")
    print("-" * 60)

    # Simular candidatos
    candidatos_fake = [
        {'label': 'Supervisor de vinedos', 'isco_code': '6130', 'similarity_score': 0.65},
        {'label': 'Camarero', 'isco_code': '5131', 'similarity_score': 0.55},
        {'label': 'Mozo de almacen', 'isco_code': '9321', 'similarity_score': 0.52}
    ]

    print("Candidatos ANTES del boost:")
    for c in candidatos_fake:
        print(f"  {c['label']}: score={c['similarity_score']:.3f}, ISCO={c['isco_code']}")

    candidatos_boosted = obtener_boost_isco(titulo, candidatos_fake, conn)

    print("\nCandidatos DESPUES del boost:")
    for c in candidatos_boosted:
        boost = c.get('arg_boost', 0)
        reason = c.get('arg_boost_reason', '-')
        print(f"  {c['label']}: score={c['similarity_score']:.3f}, ISCO={c['isco_code']}, boost={boost:.2f}, reason={reason}")

    print("\n" + "-" * 60)
    print("RESULTADO:")
    print("-" * 60)
    if candidatos_boosted[0]['isco_code'] == '5131':
        print("OK: Con boost+penalizacion, el candidato correcto (Camarero 5131) gana")
    else:
        print(f"PENDIENTE: Aun gana {candidatos_boosted[0]['label']} ({candidatos_boosted[0]['isco_code']})")

conn.close()
