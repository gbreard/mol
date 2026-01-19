"""
Diagnóstico: Por qué Matching v2 tiene 75% de No Match

Este script analiza:
1. Scores de ofertas que no pasaron el threshold
2. Estructura de datos ESCO (tasks/skills disponibles?)
3. Comparación con enfoque v8.3
"""

import sqlite3
import json
import sys
from pathlib import Path
from rapidfuzz import fuzz

DB_PATH = Path(__file__).parent / "bumeran_scraping.db"
GOLD_SET_PATH = Path(__file__).parent / "gold_set_manual_v1.json"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "matching_config.json"

def conectar_db():
    return sqlite3.connect(DB_PATH)

def cargar_gold_set():
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # El gold set puede ser lista directa o dict con 'casos'
        if isinstance(data, list):
            return data
        return data.get('casos', data)

def cargar_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def preprocesar_titulo(titulo):
    """Limpia el título para matching"""
    if not titulo:
        return ""
    import re
    # Remover sufijos comunes
    titulo = re.sub(r'\s*-\s*(zona\s+\w+|caba|gba|remoto|híbrido|presencial)\s*$', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'\s*\(\w+\)\s*$', '', titulo)
    titulo = re.sub(r'\s*(sr|ssr|jr|semi sr)\b', '', titulo, flags=re.IGNORECASE)
    return titulo.strip().lower()

def calcular_similitud_titulo(titulo_oferta, label_esco):
    """Calcula similitud entre título de oferta y label ESCO"""
    if not titulo_oferta or not label_esco:
        return 0.0
    return fuzz.ratio(titulo_oferta.lower(), label_esco.lower()) / 100.0

def calcular_similitud_descripcion(desc_oferta, desc_esco):
    """Calcula similitud entre descripciones"""
    if not desc_oferta or not desc_esco:
        return 0.0
    # TF-IDF simplificado usando partial ratio
    return fuzz.partial_ratio(desc_oferta[:500].lower(), desc_esco[:500].lower()) / 100.0

def cargar_ocupaciones_esco(conn):
    """Carga ocupaciones ESCO con campos disponibles"""
    cursor = conn.cursor()

    # Ver qué columnas existen
    cursor.execute("PRAGMA table_info(esco_occupations)")
    columnas = [col[1] for col in cursor.fetchall()]

    # Construir query con columnas existentes
    cols = ["isco_code"]
    if "occupation_uri" in columnas:
        cols.append("occupation_uri as esco_uri")
    if "preferred_label_es" in columnas:
        cols.append("preferred_label_es as label")
    if "description_es" in columnas:
        cols.append("description_es as description")

    query = f"SELECT {', '.join(cols)} FROM esco_occupations WHERE isco_code IS NOT NULL"
    cursor.execute(query)

    ocupaciones = []
    for row in cursor.fetchall():
        ocu = {'isco_code': row[0]}
        for i, col_name in enumerate(cols[1:], 1):
            key = col_name.split(' as ')[-1] if ' as ' in col_name else col_name
            ocu[key] = row[i] if i < len(row) else None
        ocupaciones.append(ocu)

    return ocupaciones

def analizar_scores_fallidos():
    """Parte 1: Mostrar scores de todas las ofertas fallidas"""
    print("=" * 80)
    print("PARTE 1: SCORES DE OFERTAS QUE NO ALCANZARON THRESHOLD")
    print("=" * 80)

    conn = conectar_db()
    gold_set = cargar_gold_set()
    config = cargar_config()
    ocupaciones = cargar_ocupaciones_esco(conn)

    # Obtener ofertas gold set
    cursor = conn.cursor()
    ids = [str(caso['id_oferta']) for caso in gold_set]
    placeholders = ','.join(['?' for _ in ids])

    cursor.execute(f"""
        SELECT
            o.id_oferta,
            o.titulo,
            o.descripcion,
            n.area_funcional,
            n.nivel_seniority,
            n.tareas_explicitas,
            n.skills_tecnicas_list,
            n.tecnologias_list
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.id_oferta IN ({placeholders})
    """, ids)

    ofertas = cursor.fetchall()
    threshold = config['filtros']['score_minimo_final']

    print(f"\nThreshold configurado: {threshold}")
    print(f"Pesos base: {config['pesos_base']}")
    print(f"Total ofertas gold set: {len(ofertas)}")
    print(f"Total ocupaciones ESCO cargadas: {len(ocupaciones)}")

    resultados = []

    for oferta in ofertas:
        id_aviso, titulo, descripcion, area, seniority, tareas, skills, tecnologias = oferta

        # Preprocesar título
        titulo_limpio = preprocesar_titulo(titulo)

        # Calcular mejor score
        mejor_score = 0
        mejor_ocupacion = None
        scores_componentes = {}

        for ocu in ocupaciones:
            label = ocu.get('label', '')
            desc_esco = ocu.get('description', '')

            # Score título
            score_titulo = calcular_similitud_titulo(titulo_limpio, label)

            # Score descripción
            score_desc = calcular_similitud_descripcion(descripcion or '', desc_esco)

            # Calcular score total con pesos base
            pesos = config['pesos_base']
            score_total = (
                pesos['titulo'] * score_titulo +
                pesos['descripcion'] * score_desc
                # tareas y skills son 0 porque no hay datos en ESCO
            )

            if score_total > mejor_score:
                mejor_score = score_total
                mejor_ocupacion = label
                scores_componentes = {
                    'titulo': score_titulo,
                    'descripcion': score_desc,
                    'tareas': 0.0,
                    'skills': 0.0
                }

        resultados.append({
            'id': id_aviso,
            'titulo_oferta': titulo[:50] if titulo else 'N/A',
            'mejor_score': mejor_score,
            'mejor_match': mejor_ocupacion[:40] if mejor_ocupacion else 'N/A',
            'componentes': scores_componentes,
            'pasa_threshold': mejor_score >= threshold
        })

    # Ordenar por score
    resultados.sort(key=lambda x: x['mejor_score'], reverse=True)

    # Mostrar tabla
    print(f"\n{'ID':<12} {'Score':>6} {'Pass':>5} {'Título Oferta':<40} {'Mejor Match ESCO':<35}")
    print("-" * 100)

    pasaron = 0
    fallaron = 0

    for r in resultados:
        status = "Y" if r['pasa_threshold'] else "X"
        if r['pasa_threshold']:
            pasaron += 1
        else:
            fallaron += 1
        print(f"{r['id']:<12} {r['mejor_score']:>6.3f} {status:>5} {r['titulo_oferta']:<40} {r['mejor_match']:<35}")

    print("-" * 100)
    print(f"\nRESUMEN: {pasaron} pasaron threshold ({pasaron/len(resultados)*100:.1f}%), {fallaron} fallaron ({fallaron/len(resultados)*100:.1f}%)")

    # Mostrar distribución de scores
    print("\n" + "=" * 60)
    print("DISTRIBUCION DE SCORES")
    print("=" * 60)

    rangos = [(0, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.45), (0.45, 0.5), (0.5, 0.6), (0.6, 1.0)]
    for low, high in rangos:
        count = len([r for r in resultados if low <= r['mejor_score'] < high])
        bar = "#" * count
        marker = " <- THRESHOLD" if low == 0.45 else ""
        print(f"{low:.2f}-{high:.2f}: {count:>3} {bar}{marker}")

    conn.close()
    return resultados

def analizar_caso_especifico(titulo_buscar="vendedor"):
    """Parte 2: Análisis paso a paso de un caso específico"""
    print("\n" + "=" * 80)
    print(f"PARTE 2: ANALISIS PASO A PASO - Caso: '{titulo_buscar}'")
    print("=" * 80)

    conn = conectar_db()
    config = cargar_config()
    ocupaciones = cargar_ocupaciones_esco(conn)

    # Buscar oferta que contenga el término
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id_oferta, o.titulo, o.descripcion, n.area_funcional, n.nivel_seniority,
               n.tareas_explicitas, n.skills_tecnicas_list, n.tecnologias_list
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE LOWER(o.titulo) LIKE ?
        LIMIT 1
    """, (f'%{titulo_buscar.lower()}%',))

    oferta = cursor.fetchone()
    if not oferta:
        print(f"No se encontro oferta con '{titulo_buscar}' en titulo")
        return

    id_aviso, titulo, descripcion, area, seniority, tareas, skills, tecnologias = oferta

    print(f"\nOFERTA ENCONTRADA:")
    print(f"   ID: {id_aviso}")
    print(f"   Titulo: {titulo}")
    print(f"   Area funcional: {area}")
    print(f"   Seniority: {seniority}")
    print(f"   Descripcion: {descripcion[:200] if descripcion else 'N/A'}...")

    titulo_limpio = preprocesar_titulo(titulo)
    print(f"\n   Titulo preprocesado: '{titulo_limpio}'")

    # Buscar top 10 matches
    print(f"\nTOP 10 CANDIDATOS ESCO:")
    print(f"{'#':>3} {'Score':>7} {'Tit':>5} {'Desc':>5} {'Label ESCO':<50}")
    print("-" * 75)

    candidatos = []
    for ocu in ocupaciones:
        label = ocu.get('label', '')
        desc_esco = ocu.get('description', '')

        score_titulo = calcular_similitud_titulo(titulo_limpio, label)
        score_desc = calcular_similitud_descripcion(descripcion or '', desc_esco)

        pesos = config['pesos_base']
        score_total = pesos['titulo'] * score_titulo + pesos['descripcion'] * score_desc

        candidatos.append({
            'label': label,
            'score_total': score_total,
            'score_titulo': score_titulo,
            'score_desc': score_desc
        })

    candidatos.sort(key=lambda x: x['score_total'], reverse=True)

    for i, c in enumerate(candidatos[:10], 1):
        print(f"{i:>3} {c['score_total']:>7.3f} {c['score_titulo']:>5.2f} {c['score_desc']:>5.2f} {c['label'][:50]:<50}")

    threshold = config['filtros']['score_minimo_final']
    mejor = candidatos[0]

    print(f"\nANALISIS:")
    print(f"   Mejor score: {mejor['score_total']:.3f}")
    print(f"   Threshold: {threshold}")
    print(f"   Diferencia: {mejor['score_total'] - threshold:+.3f}")
    print(f"   Pasa?: {'SI' if mejor['score_total'] >= threshold else 'NO'}")

    print(f"\n!!! PROBLEMA IDENTIFICADO:")
    print(f"   - Score maximo teorico con pesos actuales: {config['pesos_base']['titulo'] + config['pesos_base']['descripcion']:.2f}")
    print(f"   - Pesos titulo ({config['pesos_base']['titulo']}) + descripcion ({config['pesos_base']['descripcion']}) = {config['pesos_base']['titulo'] + config['pesos_base']['descripcion']}")
    print(f"   - Pesos tareas ({config['pesos_base']['tareas']}) + skills ({config['pesos_base']['skills']}) = {config['pesos_base']['tareas'] + config['pesos_base']['skills']} -> SIEMPRE 0 (no hay datos)")
    print(f"   - Para alcanzar threshold {threshold}, necesita score titulo+desc >= {threshold / (config['pesos_base']['titulo'] + config['pesos_base']['descripcion']):.2f}")

    conn.close()

def verificar_datos_esco():
    """Parte 3: Verificar qué datos tiene ESCO (tasks, skills, etc.)"""
    print("\n" + "=" * 80)
    print("PARTE 3: VERIFICACION DE DATOS ESCO EN BASE DE DATOS")
    print("=" * 80)

    conn = conectar_db()
    cursor = conn.cursor()

    # Verificar estructura de esco_occupations
    print("\nESTRUCTURA DE esco_occupations:")
    cursor.execute("PRAGMA table_info(esco_occupations)")
    columnas = cursor.fetchall()
    for col in columnas:
        print(f"   {col[1]:<30} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL OK'}")

    # Contar registros y verificar campos
    print("\nESTADISTICAS DE DATOS:")
    cursor.execute("SELECT COUNT(*) FROM esco_occupations")
    total = cursor.fetchone()[0]
    print(f"   Total ocupaciones: {total}")

    # Verificar si hay columnas de tasks/skills
    nombres_columnas = [col[1] for col in columnas]

    for campo in ['tasks', 'skills', 'alternative_labels', 'description_es']:
        if campo in nombres_columnas:
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN {campo} IS NOT NULL AND {campo} != '' THEN 1 ELSE 0 END) as con_datos
                FROM esco_occupations
            """)
            total, con_datos = cursor.fetchone()
            print(f"   {campo}: {con_datos}/{total} tienen datos ({con_datos/total*100:.1f}%)")
        else:
            print(f"   {campo}: !!! COLUMNA NO EXISTE")

    # Verificar tablas relacionadas
    print("\nTABLAS RELACIONADAS CON ESCO:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%esco%'")
    tablas_esco = cursor.fetchall()
    for tabla in tablas_esco:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla[0]}")
        count = cursor.fetchone()[0]
        print(f"   {tabla[0]}: {count} registros")

    # Verificar esco_skills si existe
    skill_tables = [t[0] for t in tablas_esco if 'skill' in t[0].lower()]
    if skill_tables:
        print("\nESTRUCTURA DE TABLAS DE SKILLS:")
        for tabla in skill_tables:
            cursor.execute(f"PRAGMA table_info({tabla})")
            cols = cursor.fetchall()
            print(f"\n   {tabla}:")
            for col in cols:
                print(f"      {col[1]:<30} {col[2]}")

    conn.close()

def comparar_con_v83():
    """Parte 4: Comparar con el método de scoring de v8.3"""
    print("\n" + "=" * 80)
    print("PARTE 4: COMPARACION CON MATCHING v8.3")
    print("=" * 80)

    # Leer archivo archivado de v8.3
    v83_path = Path(__file__).parent / "archive_old_versions" / "matching_old" / "matching_rules_v83.py"
    multicriteria_path = Path(__file__).parent / "archive_old_versions" / "matching_old" / "match_ofertas_multicriteria.py"

    print("\nENFOQUE v8.3 (archivado):")

    if v83_path.exists():
        with open(v83_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
            # Extraer información clave
            if 'BGE-M3' in contenido or 'bge-m3' in contenido:
                print("   [OK] Usaba embeddings BGE-M3")
            if 'chromadb' in contenido.lower():
                print("   [OK] Usaba ChromaDB para busqueda semantica")
            if 'semantic' in contenido.lower():
                print("   [OK] Tenia busqueda semantica")

            # Buscar thresholds
            import re
            thresholds = re.findall(r'threshold["\']?\s*[:=]\s*([0-9.]+)', contenido, re.IGNORECASE)
            if thresholds:
                print(f"   Thresholds encontrados: {thresholds}")
    else:
        print(f"   !!! No se encontro {v83_path}")

    if multicriteria_path.exists():
        print(f"\n   Analizando {multicriteria_path.name}...")
        with open(multicriteria_path, 'r', encoding='utf-8') as f:
            contenido = f.read()

            # Buscar cómo calculaba scores
            if 'chromadb' in contenido.lower():
                print("   [OK] Usaba ChromaDB")
            if 'embedding' in contenido.lower():
                print("   [OK] Usaba embeddings")
            if 'bge' in contenido.lower():
                print("   [OK] Modelo BGE")
            if 'cosine' in contenido.lower():
                print("   [OK] Similitud coseno")

            # Extraer función de scoring si existe
            if 'def calcular_score' in contenido or 'def score' in contenido:
                print("   [OK] Tenia funcion de scoring personalizada")
    else:
        print(f"   !!! No se encontro {multicriteria_path}")

    print("\nDIFERENCIAS CLAVE:")
    print("   v8.3 (anterior):")
    print("      - Usaba ChromaDB + embeddings BGE-M3 para busqueda semantica")
    print("      - Comparaba SIGNIFICADO, no solo texto")
    print("      - 'Vendedor' encontraba 'Agente de ventas' por semantica")
    print("")
    print("   v2.0 (actual):")
    print("      - Usa fuzzy matching (rapidfuzz) - solo compara TEXTO")
    print("      - 'Vendedor' vs 'Agente de ventas' = score bajo (palabras diferentes)")
    print("      - Sin datos de tasks/skills, score maximo teorico = 0.50")

def proponer_solucion():
    """Parte 5: Proponer solución"""
    print("\n" + "=" * 80)
    print("PARTE 5: PROPUESTA DE SOLUCION")
    print("=" * 80)

    print("""
DIAGNOSTICO:
   El 75% de "No Match" se debe a DOS problemas:

   1. DATOS FALTANTES EN ESCO:
      - La tabla esco_occupations NO tiene columnas de tasks ni skills
      - Los pesos para tareas (0.30) y skills (0.20) siempre dan 0
      - Score maximo posible = 0.50 (titulo 0.40 + descripcion 0.10)
      - Threshold actual = 0.45 -> margen de solo 0.05

   2. MATCHING TEXTUAL vs SEMANTICO:
      - v2.0 usa fuzzy ratio (compara caracteres)
      - "Vendedor" vs "Agente de ventas" = bajo score (palabras distintas)
      - v8.3 usaba embeddings -> entendia que son sinonimos

SOLUCIONES PROPUESTAS:

   OPCION A - Ajustar threshold (rapido, impacto bajo):
      - Bajar threshold de 0.45 a 0.35
      - Pro: Mas matches
      - Contra: Mas falsos positivos

   OPCION B - Recalcular pesos (rapido, mejor):
      - Como no hay tasks/skills, redistribuir pesos:
        {
          "titulo": 0.80,
          "tareas": 0.00,
          "skills": 0.00,
          "descripcion": 0.20
        }
      - Pro: Score maximo = 1.0, threshold 0.45 tiene sentido
      - Contra: Solo considera titulo y descripcion

   OPCION C - Agregar embeddings hibrido (medio, mejor calidad):
      - Usar sentence-transformers para similitud semantica del titulo
      - Mezclar: score = 0.5*fuzzy + 0.5*embedding_cosine
      - Pro: Captura sinonimos (Vendedor ~ Agente de ventas)
      - Contra: Requiere modelo ML, mas lento

   OPCION D - Restaurar ChromaDB (complejo, maxima calidad):
      - Volver a usar ChromaDB + BGE-M3 como v8.3
      - Pro: Mejor precision semantica
      - Contra: Mas dependencias, mas complejo

RECOMENDACION:
   Implementar OPCION B inmediatamente (5 min) +
   Evaluar OPCION C si precision no mejora suficiente

   Cambios en config/matching_config.json:

   "pesos_base": {
     "titulo": 0.80,
     "tareas": 0.00,
     "skills": 0.00,
     "descripcion": 0.20
   },
   "filtros": {
     "score_minimo_final": 0.40
   }
""")

if __name__ == "__main__":
    print("=" * 80)
    print("DIAGNOSTICO: Por que Matching v2 tiene 75% de No Match?")
    print("=" * 80)

    # Ejecutar las 5 partes del diagnóstico
    analizar_scores_fallidos()
    analizar_caso_especifico("vendedor")
    verificar_datos_esco()
    comparar_con_v83()
    proponer_solucion()
