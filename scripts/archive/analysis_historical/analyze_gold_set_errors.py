# -*- coding: utf-8 -*-
"""Analizar los 13 errores del Gold Set en detalle."""
import json
import sqlite3
from collections import Counter

db_path = r'D:\OEDE\Webscrapping\database\bumeran_scraping.db'
gold_set_path = r'D:\OEDE\Webscrapping\database\gold_set_manual_v2.json'

# Cargar gold set
with open(gold_set_path, 'r', encoding='utf-8') as f:
    gold_set = json.load(f)

# Filtrar solo errores
errores = [g for g in gold_set if not g.get('esco_ok', True)]

print("=" * 80)
print("ANALISIS DETALLADO DE 13 ERRORES - GOLD SET v2")
print("=" * 80)

conn = sqlite3.connect(db_path)

# Primero ver el schema de ofertas_esco_matching
print("\n[DEBUG] Schema de ofertas_esco_matching:")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(ofertas_esco_matching)")
cols = {row[1]: row[0] for row in cursor.fetchall()}
print(f"Columnas: {list(cols.keys())[:10]}...")

# Analisis por error
print(f"\n{'='*80}")
print("1. LISTADO DETALLADO DE ERRORES")
print("=" * 80)

errores_detalle = []
for i, err in enumerate(errores, 1):
    id_oferta = err['id_oferta']
    tipo_error = err.get('tipo_error', 'desconocido')
    comentario = err.get('comentario', '')

    # Buscar en ofertas_esco_matching - usar SELECT * y acceder por indice
    sql = "SELECT * FROM ofertas_esco_matching WHERE id_oferta = ?"
    row = conn.execute(sql, (id_oferta,)).fetchone()

    if row:
        # Obtener nombres de columnas
        cursor.execute("PRAGMA table_info(ofertas_esco_matching)")
        col_names = [c[1] for c in cursor.fetchall()]
        row_dict = dict(zip(col_names, row))

        titulo = (row_dict.get('titulo_oferta') or row_dict.get('titulo') or 'N/A')[:60]
        esco_label = (row_dict.get('esco_occupation_label') or 'N/A')[:50]
        isco = row_dict.get('isco_code') or 'N/A'
        metodo = row_dict.get('occupation_match_method') or 'N/A'
        score = row_dict.get('score_final_ponderado') or 0

        errores_detalle.append({
            'id': id_oferta,
            'titulo': titulo,
            'esco': esco_label,
            'isco': isco,
            'tipo_error': tipo_error,
            'metodo': metodo,
            'score': score,
            'comentario': comentario
        })

        print(f"\n[{i}] ID: {id_oferta}")
        print(f"    Titulo:     {titulo}...")
        print(f"    ESCO:       {esco_label}...")
        print(f"    ISCO:       {isco}")
        print(f"    Tipo Error: {tipo_error}")
        print(f"    Metodo:     {metodo}")
        score_str = f"{score:.3f}" if isinstance(score, (int, float)) else str(score)
        print(f"    Score:      {score_str}")
        print(f"    Problema:   {comentario[:70]}...")
    else:
        print(f"\n[{i}] ID: {id_oferta} - NO ENCONTRADO EN DB")

if not errores_detalle:
    print("\nNo se encontraron detalles en DB")
    conn.close()
    exit(1)

# Agrupar por tipo de error
print(f"\n{'='*80}")
print("2. AGRUPACION POR TIPO DE ERROR")
print("=" * 80)

tipos = Counter([e['tipo_error'] for e in errores_detalle])

print(f"\n| {'Tipo Error':<20} | {'Cantidad':>8} | {'%':>6} |")
print(f"|{'-'*22}|{'-'*10}|{'-'*8}|")
for tipo, cant in tipos.most_common():
    pct = (cant / len(errores_detalle)) * 100
    print(f"| {tipo:<20} | {cant:>8} | {pct:>5.1f}% |")
print(f"|{'-'*22}|{'-'*10}|{'-'*8}|")
print(f"| {'TOTAL':<20} | {len(errores_detalle):>8} | {100:>5.1f}% |")

# Analisis de metodos usados
print(f"\n{'='*80}")
print("3. METODOS DE MATCHING EN ERRORES")
print("=" * 80)

metodos = Counter([e['metodo'] for e in errores_detalle])
print(f"\n| {'Metodo':<40} | {'Cantidad':>8} |")
print(f"|{'-'*42}|{'-'*10}|")
for met, cant in metodos.most_common():
    print(f"| {met:<40} | {cant:>8} |")

# Analisis de posibles soluciones
print(f"\n{'='*80}")
print("4. ANALISIS DE SOLUCIONES POTENCIALES")
print("=" * 80)

# Errores por solucion potencial
diccionario_solucionable = []
reglas_nivel = []
sector_funcion = []
otros = []

for e in errores_detalle:
    tipo = e['tipo_error']
    if tipo in ['termino_similar']:
        diccionario_solucionable.append(e)
    elif tipo in ['nivel_jerarquico', 'nivel_profesional']:
        reglas_nivel.append(e)
    elif tipo in ['sector_funcion', 'sector_especifico', 'tipo_funcion']:
        sector_funcion.append(e)
    else:
        otros.append(e)

print(f"\n[A] SOLUCIONABLES CON DICCIONARIO: {len(diccionario_solucionable)}")
for e in diccionario_solucionable:
    print(f"   - {e['id']}: {e['titulo'][:40]}...")

print(f"\n[B] PROBLEMAS DE NIVEL JERARQUICO: {len(reglas_nivel)}")
for e in reglas_nivel:
    print(f"   - {e['id']}: {e['titulo'][:40]}...")
    print(f"     -> {e['esco'][:40]}... (Error: {e['tipo_error']})")

print(f"\n[C] PROBLEMAS DE SECTOR/FUNCION: {len(sector_funcion)}")
for e in sector_funcion:
    print(f"   - {e['id']}: {e['titulo'][:40]}...")
    print(f"     -> {e['esco'][:40]}... (Error: {e['tipo_error']})")

print(f"\n[D] OTROS: {len(otros)}")
for e in otros:
    print(f"   - {e['id']}: {e['titulo'][:40]}...")
    print(f"     Error: {e['tipo_error']}")

# Recomendacion
print(f"\n{'='*80}")
print("5. RECOMENDACION DE ACCION")
print("=" * 80)

total = len(errores_detalle)
print(f"""
DISTRIBUCION DE ERRORES:
  Nivel jerarquico/profesional: {len(reglas_nivel):>2} ({len(reglas_nivel)/total*100:.0f}%)
  Sector/funcion incorrecta:    {len(sector_funcion):>2} ({len(sector_funcion)/total*100:.0f}%)
  Solucionables con diccionario:{len(diccionario_solucionable):>2} ({len(diccionario_solucionable)/total*100:.0f}%)
  Otros:                        {len(otros):>2} ({len(otros)/total*100:.0f}%)

PRIORIDAD SUGERIDA:
  1. Atacar 'nivel_jerarquico' ({len([e for e in errores_detalle if e['tipo_error']=='nivel_jerarquico'])} casos)
     - Reglas de penalizacion por nivel excesivo
     - Detectar Gerente/Director vs Ejecutivo/Representante

  2. Atacar 'tipo_funcion' ({len([e for e in errores_detalle if e['tipo_error']=='tipo_funcion'])} casos)
     - Mejorar contexto de skills/funciones
     - Picking vs Embalaje, Cultivo vs Alimentos

  3. Revisar 'sector' ({len([e for e in errores_detalle if 'sector' in e['tipo_error']])} casos)
     - sector_funcion: sector laboral incorrecto
     - sector_especifico: demasiado especifico
""")

conn.close()
print("\n" + "=" * 80)
