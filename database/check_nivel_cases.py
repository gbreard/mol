# -*- coding: utf-8 -*-
"""Verificar casos de nivel jerárquico en detalle."""
import sqlite3

db_path = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'
conn = sqlite3.connect(db_path)

casos = [
    ('1118028038', 'Ejecutivo Comercial de Cuentas', 'ejecutivo'),
    ('1118022146', 'Community Manager', 'especialista'),
    ('1117984105', 'Gerente de Ventas', 'gerente'),
]

print("=" * 70)
print("ANALISIS DE CASOS NIVEL JERARQUICO")
print("=" * 70)

for id_oferta, titulo, nivel_esperado in casos:
    print(f"\n[{id_oferta}] {titulo}")
    print(f"    Nivel esperado: {nivel_esperado}")

    # Ver resultado actual
    sql = """SELECT esco_occupation_label, isco_code, occupation_match_method,
                    score_final_ponderado
             FROM ofertas_esco_matching WHERE id_oferta = ?"""
    row = conn.execute(sql, (id_oferta,)).fetchone()

    if row:
        print(f"    ESCO actual:    {row[0]}")
        print(f"    ISCO actual:    {row[1]}")
        print(f"    Metodo:         {row[2]}")
        print(f"    Score:          {row[3]:.3f}")

    # Buscar ocupaciones ESCO que podrían ser correctas
    print(f"\n    --- BUSCAR ESCO CORRECTAS ---")

    if 'Ejecutivo' in titulo:
        # Buscar ocupaciones de nivel ejecutivo en ventas/cuentas
        sql2 = """SELECT preferred_label_es, isco_code
                  FROM esco_occupations
                  WHERE LOWER(preferred_label_es) LIKE '%ejecutivo%'
                     OR LOWER(preferred_label_es) LIKE '%vendedor%'
                     OR LOWER(preferred_label_es) LIKE '%comercial%'
                  LIMIT 10"""
    elif 'Community' in titulo:
        # Buscar ocupaciones de redes sociales/marketing
        sql2 = """SELECT preferred_label_es, isco_code
                  FROM esco_occupations
                  WHERE LOWER(preferred_label_es) LIKE '%social%'
                     OR LOWER(preferred_label_es) LIKE '%marketing%'
                     OR LOWER(preferred_label_es) LIKE '%medios%'
                     OR LOWER(preferred_label_es) LIKE '%comunicaci%'
                  LIMIT 10"""
    elif 'Gerente' in titulo:
        # Buscar gerentes de ventas
        sql2 = """SELECT preferred_label_es, isco_code
                  FROM esco_occupations
                  WHERE LOWER(preferred_label_es) LIKE '%gerente%'
                     OR LOWER(preferred_label_es) LIKE '%director%comercial%'
                     OR LOWER(preferred_label_es) LIKE '%director%ventas%'
                  LIMIT 10"""

    rows = conn.execute(sql2).fetchall()
    for r in rows:
        print(f"    - {r[0]} (ISCO: {r[1]})")

conn.close()
