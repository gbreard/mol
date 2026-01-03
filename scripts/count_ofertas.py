import sqlite3
from datetime import datetime
from collections import defaultdict

conn = sqlite3.connect('database/bumeran_scraping.db')
cursor = conn.cursor()

# Obtener todas las ofertas con fecha
query = """
SELECT fecha_publicacion_original
FROM ofertas
WHERE fecha_publicacion_original IS NOT NULL
"""

# Agrupar por mes y semana
meses = defaultdict(lambda: defaultdict(int))
for row in cursor.execute(query):
    fecha_str = row[0]  # formato: DD-MM-YYYY
    try:
        dia = int(fecha_str[:2])
        mes = int(fecha_str[3:5])
        ano = int(fecha_str[6:10])
        semana = (dia - 1) // 7 + 1
        mes_key = f"{ano}-{mes:02d}"
        meses[mes_key][semana] += 1
    except:
        continue

meses_nombre = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# Tabla por semana
print("=" * 70)
print("OFERTAS POR SEMANA DE CADA MES")
print("=" * 70)
print(f"{'Mes':<10} {'Sem1':>8} {'Sem2':>8} {'Sem3':>8} {'Sem4':>8} {'Sem5':>8} {'Total':>8}")
print("-" * 70)

total_general = 0
for mes_key in sorted(meses.keys()):
    semanas = meses[mes_key]
    s1, s2, s3, s4, s5 = [semanas.get(i, 0) for i in range(1,6)]
    total_mes = s1 + s2 + s3 + s4 + s5
    total_general += total_mes
    ano, mes = mes_key.split('-')
    mes_nombre = f"{meses_nombre[int(mes)]} {ano}"
    print(f"{mes_nombre:<10} {s1:>8} {s2:>8} {s3:>8} {s4:>8} {s5:>8} {total_mes:>8}")

print("-" * 70)
print(f"{'TOTAL':<10} {'':>8} {'':>8} {'':>8} {'':>8} {'':>8} {total_general:>8}")

# Analisis comparativo
print("\n" + "=" * 70)
print("ANALISIS: CAYO O SE MANTUVO?")
print("=" * 70)

hoy = datetime.now()
dia_actual = hoy.day

# Noviembre completo
nov = meses.get("2025-11", {})
nov_total = sum(nov.values())
nov_dias = 30
nov_diario = nov_total / nov_dias

# Diciembre parcial
dic = meses.get("2025-12", {})
dic_total = sum(dic.values())
dic_dias = dia_actual
dic_diario = dic_total / dic_dias if dic_dias > 0 else 0

print(f"\nNOVIEMBRE 2025 (completo):")
print(f"  Total: {nov_total} ofertas en {nov_dias} dias")
print(f"  Promedio: {nov_diario:.1f} ofertas/dia")

print(f"\nDICIEMBRE 2025 (hasta dia {dia_actual}):")
print(f"  Total: {dic_total} ofertas en {dic_dias} dias")
print(f"  Promedio: {dic_diario:.1f} ofertas/dia")

# Comparacion
var_pct = ((dic_diario - nov_diario) / nov_diario) * 100 if nov_diario > 0 else 0
print(f"\n" + "-" * 40)
print(f"VARIACION RITMO DIARIO: {var_pct:+.1f}%")
print("-" * 40)

# Proyeccion
proyeccion = int(dic_diario * 31)
print(f"Proyeccion Dic completo: ~{proyeccion} ofertas")

# Comparar semanas equivalentes (sem 1-3 de cada mes)
print("\n" + "=" * 70)
print("COMPARACION SEMANAS EQUIVALENTES")
print("=" * 70)

nov_sem123 = nov.get(1,0) + nov.get(2,0) + nov.get(3,0)
dic_sem123 = dic.get(1,0) + dic.get(2,0) + dic.get(3,0)
var_sem = ((dic_sem123 - nov_sem123) / nov_sem123) * 100 if nov_sem123 > 0 else 0

print(f"Nov semanas 1-3: {nov_sem123} ofertas")
print(f"Dic semanas 1-3: {dic_sem123} ofertas")
print(f"Variacion: {var_sem:+.1f}%")

# Conclusion
print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

if var_pct < -15:
    print("[!] CAIDA SIGNIFICATIVA en el ritmo de publicacion")
elif var_pct < -5:
    print("[-] Leve caida en el ritmo (puede ser estacional)")
elif var_pct < 5:
    print("[=] Ritmo ESTABLE, sin cambios significativos")
else:
    print("[+] AUMENTO en el ritmo de publicacion")

# Detalle por semana reciente
print("\n" + "=" * 70)
print("DETALLE ULTIMAS SEMANAS")
print("=" * 70)
for mes_key in sorted(meses.keys())[-2:]:
    ano, mes = mes_key.split('-')
    for sem in sorted(meses[mes_key].keys()):
        count = meses[mes_key][sem]
        # Dias en esa semana
        if mes_key == "2025-12" and sem == 4:
            dias = dia_actual - 21  # dia 22-28
            nota = f" (parcial, {dias} dias)"
        elif sem == 5:
            dias = 2 if mes_key == "2025-11" else 0
            nota = f" (solo {dias} dias)" if dias else ""
        else:
            nota = ""
        print(f"  {meses_nombre[int(mes)]} Sem{sem}: {count}{nota}")

conn.close()
