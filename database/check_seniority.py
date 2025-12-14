import sqlite3
conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

# Verificar datos NLP del caso con error
cursor.execute("""
    SELECT id_oferta, titulo_normalizado, nivel_seniority, tiene_gente_cargo, area_funcional
    FROM ofertas_nlp
    WHERE id_oferta = '1117984105'
""")
row = cursor.fetchone()
print("=" * 60)
print("DATOS NLP PARA OFERTA 1117984105 (Gerente de Ventas)")
print("=" * 60)
if row:
    print(f"  id_oferta: {row[0]}")
    print(f"  titulo_normalizado: {row[1]}")
    print(f"  nivel_seniority: {row[2]}")
    print(f"  tiene_gente_cargo: {row[3]}")
    print(f"  area_funcional: {row[4]}")
else:
    print("  NO ENCONTRADO")

# Verificar el match actual en DB
cursor.execute("""
    SELECT esco_occupation_label, isco_code, occupation_match_score
    FROM ofertas_esco_matching
    WHERE id_oferta = '1117984105'
""")
row = cursor.fetchone()
print()
print("MATCH ACTUAL EN DB:")
if row:
    print(f"  esco_label: {row[0]}")
    print(f"  isco_code: {row[1]}")
    print(f"  score: {row[2]}")
else:
    print("  NO ENCONTRADO")

# Verificar mapeo de seniority
print()
print("ANALISIS DEL ERROR:")
print("  - Si nivel_seniority = 'gerente' o 'manager'")
print("  - Deberia matchear a ISCO 1xxx (directivos)")
print("  - Pero matcheo a ISCO 3xxx (tecnicos/representantes)")

conn.close()
