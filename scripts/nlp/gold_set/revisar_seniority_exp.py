# -*- coding: utf-8 -*-
"""Revision completa de seniority y experiencia en Gold Set 100"""
import sqlite3
import json
from pathlib import Path

DB = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
GOLD = Path(__file__).parent.parent / "database" / "gold_set_nlp_100_ids.json"

with open(GOLD, 'r', encoding='utf-8') as f:
    ids = json.load(f)

conn = sqlite3.connect(DB)
c = conn.cursor()

placeholders = ','.join(['?' for _ in ids])
c.execute(f"""
    SELECT id_oferta, nivel_seniority, experiencia_min_anios, titulo_limpio
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
    ORDER BY
        CASE WHEN experiencia_min_anios IS NULL THEN 1 ELSE 0 END,
        experiencia_min_anios DESC
""", ids)

print("=" * 100)
print("REVISION SENIORITY + EXPERIENCIA - Gold Set 100")
print("=" * 100)
print(f"{'ID':<12} {'Seniority':<12} {'Exp':<6} {'Titulo':<65}")
print("-" * 100)

anomalias = []
todos = []
for row in c.fetchall():
    id_oferta, seniority, exp_min, titulo = row
    todos.append(row)
    titulo_corto = (titulo[:62] + "...") if titulo and len(titulo) > 65 else (titulo or "-")
    exp_str = str(int(exp_min)) if exp_min else "-"
    seniority_str = seniority or "-"

    # Detectar anomalias
    flag = ""
    if exp_min and exp_min >= 15:
        flag = " [EXP ALTA?]"
        anomalias.append((id_oferta, f"exp={int(exp_min)} muy alta", titulo_corto))
    elif exp_min and exp_min == 0 and seniority and seniority not in ["trainee"]:
        flag = " [EXP=0?]"
        anomalias.append((id_oferta, f"exp=0 pero seniority={seniority}", titulo_corto))
    elif not seniority and not exp_min:
        flag = " [SIN DATOS]"
        anomalias.append((id_oferta, "sin seniority ni experiencia", titulo_corto))

    print(f"{id_oferta:<12} {seniority_str:<12} {exp_str:<6} {titulo_corto}{flag}")

print()
print("=" * 100)
print("RESUMEN")
print("=" * 100)

# Stats
c.execute(f"""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN nivel_seniority IS NOT NULL THEN 1 ELSE 0 END) as con_seniority,
        SUM(CASE WHEN experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END) as con_exp,
        SUM(CASE WHEN nivel_seniority IS NULL AND experiencia_min_anios IS NULL THEN 1 ELSE 0 END) as sin_ambos
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
""", ids)
stats = c.fetchone()
print(f"Total: {stats[0]}")
print(f"Con seniority: {stats[1]} ({stats[1]*100//stats[0]}%)")
print(f"Con experiencia: {stats[2]} ({stats[2]*100//stats[0]}%)")
print(f"Sin ambos: {stats[3]}")

# Distribucion seniority
print()
print("Distribucion seniority:")
c.execute(f"""
    SELECT nivel_seniority, COUNT(*)
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
    GROUP BY nivel_seniority
    ORDER BY COUNT(*) DESC
""", ids)
for row in c.fetchall():
    print(f"  {row[0] or 'NULL':<15} {row[1]}")

# Distribucion experiencia
print()
print("Distribucion experiencia:")
c.execute(f"""
    SELECT
        CASE
            WHEN experiencia_min_anios IS NULL THEN 'NULL'
            WHEN experiencia_min_anios = 0 THEN '0'
            WHEN experiencia_min_anios = 1 THEN '1'
            WHEN experiencia_min_anios BETWEEN 2 AND 4 THEN '2-4'
            WHEN experiencia_min_anios BETWEEN 5 AND 10 THEN '5-10'
            ELSE '10+'
        END as rango,
        COUNT(*)
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
    GROUP BY rango
    ORDER BY
        CASE rango
            WHEN 'NULL' THEN 0
            WHEN '0' THEN 1
            WHEN '1' THEN 2
            WHEN '2-4' THEN 3
            WHEN '5-10' THEN 4
            ELSE 5
        END
""", ids)
for row in c.fetchall():
    print(f"  {row[0]:<15} {row[1]}")

if anomalias:
    print()
    print("=" * 100)
    print("POSIBLES ANOMALIAS A REVISAR:")
    print("=" * 100)
    for id_o, msg, titulo in anomalias:
        print(f"  {id_o}: {msg}")
        print(f"      -> {titulo}")

conn.close()
