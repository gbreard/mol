# -*- coding: utf-8 -*-
"""
Auto-Expansión de Diccionario de Normalización
===============================================

Analiza casos sin match y genera entradas de diccionario automáticamente
basándose en el fuzzy/LLM original como referencia.
"""

import pandas as pd
import json
from pathlib import Path
from collections import Counter
import unicodedata
import re

# Rutas
MATCHING_PATH = r"D:\OEDE\Webscrapping\03_esco_matching\data\matching_con_normalizacion_20251028_200305.csv"
ESCO_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json"
DICT_PATH = r"D:\OEDE\Webscrapping\03_esco_matching\data\diccionario_normalizacion_arg_esco.json"


def normalizar_texto(text):
    """Normaliza texto"""
    if pd.isna(text) or not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extraer_keywords_titulo(titulo):
    """Extrae keywords relevantes de un título"""
    titulo_norm = normalizar_texto(titulo)

    # Stopwords
    stopwords = {
        'de', 'y', 'para', 'con', 'en', 'el', 'la', 'los', 'las', 'un', 'una',
        'del', 'al', 'por', 'a', 'zona', 'req', 'eventual', 'sr', 'ssr', 'jr',
        'p', 'rubro', 'empresa', 'importante', 'caba', 'gba', 'norte', 'sur',
        'este', 'oeste', 'buenos', 'aires', 'req199724', 'tortuguitas', 'villa',
        'zona', 'ciudadela', 'soldati', 'lugano', 'pilar', 'san', 'martin',
        'beccar', 'garin', 'hard', 'medio', 'oficial'
    }

    palabras = titulo_norm.split()
    keywords = [p for p in palabras if len(p) > 3 and p not in stopwords]

    return keywords


def main():
    """Función principal"""
    print("=" * 100)
    print("AUTO-EXPANSION DE DICCIONARIO")
    print("=" * 100)

    # Cargar resultados actuales
    print(f"\n[1/5] Cargando resultados...")
    df = pd.read_csv(MATCHING_PATH, encoding='utf-8')
    print(f"  OK: {len(df)} ofertas")

    # Filtrar casos sin match
    sin_match = df[df['norm_esco_label'].isna()].copy()
    print(f"\n[2/5] Casos sin match: {len(sin_match)}")

    # Cargar ESCO
    print(f"\n[3/5] Cargando ESCO...")
    with open(ESCO_PATH, 'r', encoding='utf-8') as f:
        esco_data = json.load(f)
    print(f"  OK: {len(esco_data)} ocupaciones")

    # Crear mapeo ISCO → Label para referencia rápida
    isco_to_label = {}
    for k, v in esco_data.items():
        if v:
            label = v.get('label_es', '') or v.get('label_en', '')
            isco = v.get('codigo_isco_4d', v.get('codigo_isco', ''))
            if isco and label:
                if isco not in isco_to_label:
                    isco_to_label[isco] = label

    # Analizar títulos sin match
    print(f"\n[4/5] Analizando patrones...")

    # Extraer keywords de todos los títulos sin match
    todos_keywords = []
    for titulo in sin_match['titulo']:
        keywords = extraer_keywords_titulo(titulo)
        todos_keywords.extend(keywords)

    # Contar frecuencia
    keyword_freq = Counter(todos_keywords)

    print(f"\n  Keywords más frecuentes en casos sin match:")
    for kw, count in keyword_freq.most_common(30):
        print(f"    {kw:<25}: {count:>3} veces")

    # Cargar diccionario actual
    with open(DICT_PATH, 'r', encoding='utf-8') as f:
        dict_actual = json.load(f)

    print(f"\n  Diccionario actual: {len(dict_actual)} entradas")

    # Generar nuevas entradas basadas en fuzzy/LLM original
    print(f"\n[5/5] Generando nuevas entradas...")

    nuevas_entradas = {}

    # Agrupar casos sin match por patrón
    for idx, row in sin_match.iterrows():
        titulo = row['titulo']
        fuzzy_label = row['fuzzy_esco_label']
        fuzzy_isco = str(row['fuzzy_isco_code'])

        # Extraer keywords del título
        keywords = extraer_keywords_titulo(titulo)

        # Crear claves potenciales (1-grams, 2-grams)
        claves_potenciales = []

        # 1-grams
        claves_potenciales.extend(keywords)

        # 2-grams
        for i in range(len(keywords) - 1):
            bigram = f"{keywords[i]} {keywords[i+1]}"
            claves_potenciales.append(bigram)

        # Para cada clave potencial, verificar si ya existe
        for clave in claves_potenciales:
            clave_norm = normalizar_texto(clave)

            # Si ya existe en diccionario actual, skip
            if clave_norm in dict_actual:
                continue

            # Si ya fue agregada a nuevas_entradas, skip
            if clave_norm in nuevas_entradas:
                continue

            # Generar entrada basada en fuzzy/LLM
            # Extraer keywords del label ESCO
            if pd.isna(fuzzy_label):
                continue

            label_keywords = [
                p for p in normalizar_texto(fuzzy_label).split()
                if len(p) > 3
            ]

            # Crear entrada
            entrada = {
                'esco_terms': label_keywords[:4],  # Top 4 keywords del label
                'isco_target': fuzzy_isco.split('.')[0] if '.' in fuzzy_isco else fuzzy_isco[:4],  # Nivel o código 4 dig
                'notes': f"Auto-generado de: {fuzzy_label}",
                'ejemplos_titulos': [titulo]
            }

            nuevas_entradas[clave_norm] = entrada

    print(f"\n  Nuevas entradas generadas: {len(nuevas_entradas)}")

    # Mostrar muestra
    print(f"\n  Muestra de nuevas entradas:")
    for i, (clave, config) in enumerate(list(nuevas_entradas.items())[:15], 1):
        print(f"    {i:>2}. '{clave}' -> ISCO {config['isco_target']} ({config['notes']})")

    # Combinar con diccionario actual
    diccionario_expandido = {**dict_actual, **nuevas_entradas}

    # Guardar
    output_path = Path(DICT_PATH).parent / "diccionario_normalizacion_arg_esco_expandido.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(diccionario_expandido, f, indent=2, ensure_ascii=False)

    print(f"\n" + "=" * 100)
    print("RESUMEN")
    print("=" * 100)
    print(f"\n  Entradas originales:   {len(dict_actual)}")
    print(f"  Entradas nuevas:       {len(nuevas_entradas)}")
    print(f"  Total expandido:       {len(diccionario_expandido)}")
    print(f"\n  Guardado en: {output_path}")
    print("=" * 100)


if __name__ == "__main__":
    main()
