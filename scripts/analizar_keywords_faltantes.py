"""
Analizador de Keywords Faltantes - Bumeran
===========================================

Analiza las ofertas scrapeadas para identificar términos frecuentes
que NO están en el diccionario de keywords actual.

Objetivo: Descubrir nuevas keywords basadas en datos reales para mejorar cobertura.

Uso:
    python analizar_keywords_faltantes.py
    python analizar_keywords_faltantes.py --min-freq 5 --top-n 200
"""

import pandas as pd
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime
import argparse


# Stopwords en español (palabras a ignorar)
STOPWORDS_ES = {
    'de', 'la', 'el', 'en', 'y', 'a', 'los', 'las', 'del', 'al', 'por', 'para',
    'con', 'sin', 'sobre', 'entre', 'hasta', 'desde', 'un', 'una', 'unos', 'unas',
    'su', 'sus', 'se', 'le', 'lo', 'que', 'como', 'mas', 'pero', 'si', 'no',
    'o', 'u', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas',
    'aquel', 'aquella', 'aquellos', 'aquellas', 'mi', 'tu', 'su', 'nuestro',
    'vuestro', 'me', 'te', 'nos', 'os', 'les', 'muy', 'tanto', 'tan', 'todo',
    'toda', 'todos', 'todas', 'otro', 'otra', 'otros', 'otras', 'mismo', 'misma',
    'he', 'ha', 'han', 'hemos', 'habeis', 'ser', 'estar', 'tener', 'hacer',
    'empresa', 'trabajo', 'puesto', 'cargo', 'area', 'zona', 'local', 'ambiente',
    'laboral', 'profesional', 'oportunidad', 'busca', 'solicita', 'requiere',
    'incorporar', 'sumar', 'excluyente', 'deseable', 'experiencia', 'años', 'año'
}


def normalizar_texto(texto):
    """Normaliza texto: lowercase, sin acentos, limpio"""
    if not isinstance(texto, str):
        return ""

    # Lowercase
    texto = texto.lower()

    # Remover acentos
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

    return texto


def tokenizar(texto):
    """
    Tokeniza texto en palabras individuales
    Separa por espacios, guiones, barras, paréntesis
    """
    if not texto:
        return []

    # Reemplazar separadores por espacios
    texto = re.sub(r'[/\-_\(\)\[\]{}|,;:.]', ' ', texto)

    # Separar en tokens
    tokens = texto.split()

    # Filtrar tokens válidos
    tokens_validos = []
    for token in tokens:
        # Remover números puros
        if token.isdigit():
            continue

        # Remover tokens muy cortos (excepto si son tecnologías conocidas)
        if len(token) < 2:
            continue

        # Remover stopwords
        if token in STOPWORDS_ES:
            continue

        tokens_validos.append(token)

    return tokens_validos


def extraer_bigramas(tokens):
    """Extrae bigramas (pares de palabras consecutivas)"""
    return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens)-1)]


def extraer_trigramas(tokens):
    """Extrae trigramas (trios de palabras consecutivas)"""
    return [f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}" for i in range(len(tokens)-2)]


def cargar_diccionario_keywords(dict_path):
    """Carga keywords del diccionario maestro (estrategia exhaustiva)"""
    with open(dict_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Obtener keywords de estrategia exhaustiva
    keywords_raw = data['estrategias']['exhaustiva']['keywords']

    # Normalizar keywords
    keywords_normalizadas = set()
    for kw in keywords_raw:
        # Normalizar
        kw_norm = normalizar_texto(kw)
        keywords_normalizadas.add(kw_norm)

        # También agregar variantes (con guion medio, bajo, espacio)
        if '-' in kw_norm:
            keywords_normalizadas.add(kw_norm.replace('-', ' '))
            keywords_normalizadas.add(kw_norm.replace('-', '_'))
        if '_' in kw_norm:
            keywords_normalizadas.add(kw_norm.replace('_', ' '))
            keywords_normalizadas.add(kw_norm.replace('_', '-'))
        if ' ' in kw_norm:
            keywords_normalizadas.add(kw_norm.replace(' ', '-'))
            keywords_normalizadas.add(kw_norm.replace(' ', '_'))

    return keywords_normalizadas


def categorizar_termino(termino):
    """
    Intenta categorizar un término basado en patrones

    Returns:
        str: categoria detectada o 'otro'
    """
    termino_lower = termino.lower()

    # Niveles de senioridad
    if any(x in termino_lower for x in ['senior', 'ssr', 'sr', 'semi', 'avanzado']):
        return 'nivel_senioridad'
    if any(x in termino_lower for x in ['junior', 'jr', 'trainee', 'pasante', 'becario']):
        return 'nivel_senioridad'

    # Modalidades
    if any(x in termino_lower for x in ['remoto', 'remote', 'hibrido', 'hybrid', 'presencial', 'oficina']):
        return 'modalidad'
    if any(x in termino_lower for x in ['freelance', 'contractor', 'part', 'time', 'temporal']):
        return 'modalidad'

    # Ubicaciones (CABA, GBA, provincias)
    if any(x in termino_lower for x in ['caba', 'capital', 'federal', 'gba', 'buenos', 'aires']):
        return 'ubicacion'
    if any(x in termino_lower for x in ['cordoba', 'rosario', 'mendoza', 'tucuman', 'zona']):
        return 'ubicacion'

    # Roles/Títulos
    if any(x in termino_lower for x in ['desarrollador', 'developer', 'programador', 'engineer', 'ingeniero']):
        return 'rol_tech'
    if any(x in termino_lower for x in ['analista', 'analyst', 'consultor', 'consultant', 'especialista']):
        return 'rol_general'
    if any(x in termino_lower for x in ['gerente', 'manager', 'director', 'jefe', 'coordinador', 'lider']):
        return 'jerarquia'

    # Tecnologías web
    if any(x in termino_lower for x in ['html', 'css', 'web', 'api', 'rest', 'http', 'json', 'xml']):
        return 'tecnologia_web'

    # Frameworks y librerías
    if any(x in termino_lower for x in ['framework', 'library', 'lib', 'cms', 'erp', 'crm']):
        return 'tecnologia_framework'

    # Bases de datos
    if any(x in termino_lower for x in ['sql', 'database', 'db', 'mysql', 'postgres', 'mongo', 'oracle']):
        return 'tecnologia_database'

    # Soft skills / Características
    if any(x in termino_lower for x in ['bilingue', 'ingles', 'idioma', 'comunicacion', 'equipo']):
        return 'soft_skill'

    # Industrias
    if any(x in termino_lower for x in ['fintech', 'healthtech', 'edtech', 'ecommerce', 'retail', 'startup']):
        return 'industria'

    return 'otro'


def analizar_ofertas(ofertas_path, dict_path, min_freq=3, top_n=100, incluir_descripciones=False):
    """
    Analiza ofertas y descubre términos faltantes

    Args:
        ofertas_path: Path al CSV/JSON de ofertas
        dict_path: Path al diccionario maestro JSON
        min_freq: Frecuencia mínima para considerar un término
        top_n: Cantidad de términos top a reportar
        incluir_descripciones: Si True, analiza también descripciones (más lento)
    """
    print("="*70)
    print("ANALIZADOR DE KEYWORDS FALTANTES - BUMERAN")
    print("="*70)
    print()

    # 1. Cargar datos
    print("1. Cargando datos...")

    if ofertas_path.suffix == '.csv':
        df = pd.read_csv(ofertas_path)
    else:
        df = pd.read_json(ofertas_path)

    print(f"   Ofertas cargadas: {len(df):,}")

    # Cargar diccionario
    keywords_diccionario = cargar_diccionario_keywords(dict_path)
    print(f"   Keywords en diccionario: {len(keywords_diccionario):,}")
    print()

    # 2. Extraer y procesar términos
    print("2. Extrayendo términos de títulos...")

    todos_tokens = []
    todos_bigramas = []
    todos_trigramas = []

    # Procesar títulos
    for titulo in df['titulo']:
        if pd.isna(titulo):
            continue

        # Normalizar y tokenizar
        titulo_norm = normalizar_texto(titulo)
        tokens = tokenizar(titulo_norm)

        todos_tokens.extend(tokens)

        # Bigramas y trigramas
        if len(tokens) >= 2:
            todos_bigramas.extend(extraer_bigramas(tokens))
        if len(tokens) >= 3:
            todos_trigramas.extend(extraer_trigramas(tokens))

    print(f"   Tokens extraídos: {len(todos_tokens):,}")
    print(f"   Tokens únicos: {len(set(todos_tokens)):,}")
    print()

    # Opcionalmente procesar descripciones
    if incluir_descripciones and 'descripcion' in df.columns:
        print("3. Extrayendo términos de descripciones...")
        for desc in df['descripcion']:
            if pd.isna(desc):
                continue
            desc_norm = normalizar_texto(desc)
            tokens = tokenizar(desc_norm)
            todos_tokens.extend(tokens)
        print(f"   Total tokens con descripciones: {len(todos_tokens):,}")
        print()

    # 3. Contar frecuencias
    print(f"3. Calculando frecuencias...")

    contador_tokens = Counter(todos_tokens)
    contador_bigramas = Counter(todos_bigramas)
    contador_trigramas = Counter(todos_trigramas)

    print(f"   Términos únicos totales: {len(contador_tokens):,}")
    print()

    # 4. Identificar términos NO en diccionario
    print("4. Identificando términos faltantes...")

    terminos_faltantes = {}

    for termino, freq in contador_tokens.items():
        # Filtrar por frecuencia mínima
        if freq < min_freq:
            continue

        # Verificar si NO está en diccionario
        if termino not in keywords_diccionario:
            terminos_faltantes[termino] = freq

    print(f"   Términos NO en diccionario (freq >= {min_freq}): {len(terminos_faltantes):,}")
    print()

    # Bigramas faltantes
    bigramas_faltantes = {}
    for bigrama, freq in contador_bigramas.items():
        if freq < min_freq:
            continue
        if bigrama not in keywords_diccionario:
            bigramas_faltantes[bigrama] = freq

    # Trigramas faltantes
    trigramas_faltantes = {}
    for trigrama, freq in contador_trigramas.items():
        if freq < min_freq:
            continue
        if trigrama not in keywords_diccionario:
            trigramas_faltantes[trigrama] = freq

    # 5. Ordenar por frecuencia
    top_terminos = sorted(terminos_faltantes.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_bigramas = sorted(bigramas_faltantes.items(), key=lambda x: x[1], reverse=True)[:50]
    top_trigramas = sorted(trigramas_faltantes.items(), key=lambda x: x[1], reverse=True)[:30]

    # 6. Categorizar términos
    print("5. Categorizando términos...")
    terminos_por_categoria = defaultdict(list)

    for termino, freq in top_terminos:
        categoria = categorizar_termino(termino)
        pct = (freq / len(df)) * 100
        terminos_por_categoria[categoria].append({
            'termino': termino,
            'frecuencia': freq,
            'porcentaje': pct
        })

    print(f"   Categorías identificadas: {len(terminos_por_categoria)}")
    print()

    # 7. Generar reporte
    print("="*70)
    print("RESULTADOS DEL ANÁLISIS")
    print("="*70)
    print()

    print(f"Total ofertas analizadas:        {len(df):,}")
    print(f"Keywords en diccionario actual:  {len(keywords_diccionario):,}")
    print(f"Términos únicos encontrados:     {len(contador_tokens):,}")
    print(f"Términos NO en diccionario:      {len(terminos_faltantes):,}")
    print()

    # Top términos faltantes
    print("="*70)
    print(f"TOP {len(top_terminos)} TÉRMINOS FALTANTES")
    print("="*70)
    print(f"{'#':<4} {'Término':<30} {'Frecuencia':<12} {'% Ofertas':<12}")
    print("-"*70)

    for i, (termino, freq) in enumerate(top_terminos, 1):
        pct = (freq / len(df)) * 100
        print(f"{i:<4} {termino:<30} {freq:<12} {pct:>10.1f}%")

    print()

    # Top bigramas
    if top_bigramas:
        print("="*70)
        print(f"TOP {len(top_bigramas)} BIGRAMAS FALTANTES")
        print("="*70)
        print(f"{'#':<4} {'Bigrama':<40} {'Frecuencia':<12}")
        print("-"*70)

        for i, (bigrama, freq) in enumerate(top_bigramas[:20], 1):
            print(f"{i:<4} {bigrama:<40} {freq:<12}")

        print()

    # Sugerencias por categoría
    print("="*70)
    print("SUGERENCIAS POR CATEGORÍA")
    print("="*70)
    print()

    for categoria in sorted(terminos_por_categoria.keys()):
        items = terminos_por_categoria[categoria]
        if not items:
            continue

        print(f"{categoria.upper().replace('_', ' ')} ({len(items)} términos):")
        for item in items[:10]:  # Primeros 10 de cada categoría
            print(f"  - '{item['termino']}': {item['frecuencia']} ofertas ({item['porcentaje']:.1f}%)")

        if len(items) > 10:
            print(f"  ... y {len(items) - 10} más")
        print()

    # Estimación de impacto
    print("="*70)
    print("ESTIMACIÓN DE IMPACTO")
    print("="*70)

    # Calcular cuántas ofertas mencionan al menos uno de los top 50 términos
    ofertas_con_terminos_faltantes = set()
    top_50_terminos = [t for t, _ in top_terminos[:50]]

    for idx, titulo in enumerate(df['titulo']):
        if pd.isna(titulo):
            continue
        titulo_norm = normalizar_texto(titulo)
        for termino in top_50_terminos:
            if termino in titulo_norm:
                ofertas_con_terminos_faltantes.add(idx)

    pct_ofertas_con_faltantes = (len(ofertas_con_terminos_faltantes) / len(df)) * 100

    print(f"Ofertas que mencionan top 50 términos faltantes: {len(ofertas_con_terminos_faltantes):,} ({pct_ofertas_con_faltantes:.1f}%)")
    print(f"Potencial cobertura adicional estimada: {pct_ofertas_con_faltantes:.1f}% - {pct_ofertas_con_faltantes * 0.7:.1f}%")
    print()

    # 8. Guardar resultados
    output_dir = Path(__file__).parent.parent / "data" / "analysis" / "keywords"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV Top términos
    df_top = pd.DataFrame([
        {'termino': t, 'frecuencia': f, 'porcentaje': (f/len(df))*100, 'categoria': categorizar_termino(t)}
        for t, f in top_terminos
    ])
    csv_path = output_dir / f"terminos_faltantes_top{top_n}_{timestamp}.csv"
    df_top.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Resultados guardados: {csv_path}")

    # CSV Top bigramas
    if top_bigramas:
        df_bigramas = pd.DataFrame([
            {'bigrama': b, 'frecuencia': f}
            for b, f in top_bigramas
        ])
        bigramas_path = output_dir / f"bigramas_faltantes_top50_{timestamp}.csv"
        df_bigramas.to_csv(bigramas_path, index=False, encoding='utf-8')
        print(f"Bigramas guardados: {bigramas_path}")

    # JSON completo
    resultados = {
        'timestamp': datetime.now().isoformat(),
        'ofertas_analizadas': len(df),
        'keywords_diccionario': len(keywords_diccionario),
        'terminos_unicos': len(contador_tokens),
        'terminos_faltantes': len(terminos_faltantes),
        'top_terminos': [
            {'termino': t, 'frecuencia': f, 'porcentaje': (f/len(df))*100}
            for t, f in top_terminos
        ],
        'top_bigramas': [
            {'bigrama': b, 'frecuencia': f}
            for b, f in top_bigramas
        ],
        'por_categoria': {
            cat: items
            for cat, items in terminos_por_categoria.items()
        },
        'impacto_estimado': {
            'ofertas_con_terminos_faltantes': len(ofertas_con_terminos_faltantes),
            'porcentaje': pct_ofertas_con_faltantes
        }
    }

    json_path = output_dir / f"analisis_completo_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"Análisis completo: {json_path}")
    print()
    print("="*70)

    return resultados


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Analiza ofertas para descubrir keywords faltantes')
    parser.add_argument('--ofertas', type=str,
                       default='D:/OEDE/Webscrapping/01_sources/bumeran/data/raw/bumeran_exhaustiva_v3.csv',
                       help='Path al archivo de ofertas (CSV o JSON)')
    parser.add_argument('--diccionario', type=str,
                       default='D:/OEDE/Webscrapping/data/config/master_keywords.json',
                       help='Path al diccionario maestro')
    parser.add_argument('--min-freq', type=int, default=3,
                       help='Frecuencia mínima para considerar un término')
    parser.add_argument('--top-n', type=int, default=100,
                       help='Cantidad de términos top a reportar')
    parser.add_argument('--incluir-descripciones', action='store_true',
                       help='Incluir descripciones en el análisis (más lento)')

    args = parser.parse_args()

    ofertas_path = Path(args.ofertas)
    dict_path = Path(args.diccionario)

    if not ofertas_path.exists():
        print(f"ERROR: Archivo de ofertas no encontrado: {ofertas_path}")
        return

    if not dict_path.exists():
        print(f"ERROR: Diccionario no encontrado: {dict_path}")
        return

    # Ejecutar análisis
    analizar_ofertas(
        ofertas_path=ofertas_path,
        dict_path=dict_path,
        min_freq=args.min_freq,
        top_n=args.top_n,
        incluir_descripciones=args.incluir_descripciones
    )


if __name__ == "__main__":
    main()
