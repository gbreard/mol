# -*- coding: utf-8 -*-
"""
Comparación Fuzzy/LLM vs Embeddings Semánticos
===============================================

Compara los resultados de matching ESCO usando diferentes métodos:
- Fuzzy + LLM (método original)
- Embeddings semánticos (nuevo)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

# Rutas
INPUT_FILE = r"D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\ofertas_esco_isco_llm_20251027_191809_semantic_20251028_191855.csv"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\02.5_nlp_extraction\docs")


def categorize_confidence(score, method='embeddings'):
    """Categoriza score en niveles de confianza"""
    if method == 'embeddings':
        if score >= 0.8:
            return 'alta'
        elif score >= 0.6:
            return 'media'
        else:
            return 'baja'
    else:  # fuzzy
        if score >= 80:
            return 'alta'
        elif score >= 70:
            return 'media'
        else:
            return 'baja'


def main():
    print("=" * 100)
    print("COMPARACIÓN: FUZZY/LLM vs EMBEDDINGS SEMÁNTICOS")
    print("=" * 100)

    # Cargar datos
    print(f"\n[1] Cargando datos: {Path(INPUT_FILE).name}")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8', low_memory=False)
    print(f"    OK: {len(df):,} ofertas cargadas")

    # Verificar columnas necesarias
    required_cols = [
        'titulo',
        'esco_occupation_label',  # Fuzzy/LLM
        'esco_codigo_isco',       # Fuzzy/LLM
        'esco_match_score',       # Fuzzy/LLM
        'esco_confianza',         # Fuzzy/LLM
        'semantic_esco_label',    # Embeddings
        'semantic_isco_code',     # Embeddings
        'semantic_similarity'     # Embeddings
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"\n❌ ERROR: Faltan columnas: {missing}")
        return

    # Análisis general
    print("\n" + "=" * 100)
    print("[2] ANÁLISIS GENERAL")
    print("=" * 100)

    # Fuzzy/LLM
    fuzzy_matched = df['esco_occupation_label'].notna().sum()
    fuzzy_pct = (fuzzy_matched / len(df)) * 100

    # Embeddings
    semantic_matched = df['semantic_esco_label'].notna().sum()
    semantic_pct = (semantic_matched / len(df)) * 100

    print(f"\nFuzzy/LLM:")
    print(f"  Matched:        {fuzzy_matched:>5,} ({fuzzy_pct:>5.1f}%)")
    print(f"  Sin match:      {len(df) - fuzzy_matched:>5,} ({100-fuzzy_pct:>5.1f}%)")
    print(f"  Score promedio: {df['esco_match_score'].mean():>5.1f}")

    print(f"\nEmbeddings Semánticos:")
    print(f"  Matched:           {semantic_matched:>5,} ({semantic_pct:>5.1f}%)")
    print(f"  Sin match:         {len(df) - semantic_matched:>5,} ({100-semantic_pct:>5.1f}%)")
    print(f"  Similitud promedio: {df['semantic_similarity'].mean():>5.3f}")

    # Distribución por confianza
    print("\n" + "=" * 100)
    print("[3] DISTRIBUCIÓN POR CONFIANZA")
    print("=" * 100)

    # Fuzzy/LLM
    print("\nFuzzy/LLM:")
    fuzzy_conf = df['esco_confianza'].value_counts().sort_index()
    for conf, count in fuzzy_conf.items():
        pct = (count / len(df)) * 100
        print(f"  {conf:>10s}: {count:>4,} ({pct:>5.1f}%)")

    # Embeddings
    print("\nEmbeddings:")
    df['semantic_confianza'] = df['semantic_similarity'].apply(
        lambda x: categorize_confidence(x, 'embeddings')
    )
    semantic_conf = df['semantic_confianza'].value_counts().sort_index()
    for conf, count in semantic_conf.items():
        pct = (count / len(df)) * 100
        print(f"  {conf:>10s}: {count:>4,} ({pct:>5.1f}%)")

    # Casos donde coinciden/difieren
    print("\n" + "=" * 100)
    print("[4] COINCIDENCIA ENTRE MÉTODOS")
    print("=" * 100)

    # Solo casos donde ambos hicieron match
    both_matched = df[
        df['esco_occupation_label'].notna() &
        df['semantic_esco_label'].notna()
    ].copy()

    print(f"\nCasos con match en AMBOS métodos: {len(both_matched):,}")

    # Coincidencia exacta en ESCO label
    both_matched['labels_coinciden'] = (
        both_matched['esco_occupation_label'] == both_matched['semantic_esco_label']
    )
    coinciden_label = both_matched['labels_coinciden'].sum()
    pct_coinciden = (coinciden_label / len(both_matched)) * 100

    print(f"  Misma ocupación ESCO:     {coinciden_label:>4,} ({pct_coinciden:>5.1f}%)")
    print(f"  Diferente ocupación ESCO: {len(both_matched) - coinciden_label:>4,} ({100-pct_coinciden:>5.1f}%)")

    # Coincidencia en ISCO (más flexible)
    both_matched['isco_coincide'] = (
        both_matched['esco_codigo_isco'] == both_matched['semantic_isco_code']
    )
    coinciden_isco = both_matched['isco_coincide'].sum()
    pct_isco = (coinciden_isco / len(both_matched)) * 100

    print(f"\n  Mismo ISCO code:          {coinciden_isco:>4,} ({pct_isco:>5.1f}%)")
    print(f"  Diferente ISCO code:      {len(both_matched) - coinciden_isco:>4,} ({100-pct_isco:>5.1f}%)")

    # Casos donde difieren (interesantes)
    print("\n" + "=" * 100)
    print("[5] CASOS DONDE DIFIEREN (Top 20)")
    print("=" * 100)

    difieren = both_matched[~both_matched['labels_coinciden']].copy()

    if len(difieren) > 0:
        print(f"\n{len(difieren):,} casos con diferente ocupación ESCO:\n")

        # Mostrar ejemplos
        for idx, row in difieren.head(20).iterrows():
            print(f"Título: {row['titulo']}")
            print(f"  Fuzzy/LLM:  {row['esco_occupation_label']} (ISCO: {row['esco_codigo_isco']}, score: {row['esco_match_score']:.0f})")
            print(f"  Embeddings: {row['semantic_esco_label']} (ISCO: {row['semantic_isco_code']}, sim: {row['semantic_similarity']:.3f})")
            print()

    # Casos mejorados por embeddings
    print("=" * 100)
    print("[6] MEJORAS CON EMBEDDINGS")
    print("=" * 100)

    # Casos con baja confianza en fuzzy, alta en embeddings
    mejorados = df[
        (df['esco_confianza'] == 'baja') &
        (df['semantic_confianza'] == 'alta')
    ]

    print(f"\nCasos con BAJA confianza en Fuzzy/LLM -> ALTA en Embeddings: {len(mejorados):,}\n")

    if len(mejorados) > 0:
        for idx, row in mejorados.head(10).iterrows():
            print(f"Título: {row['titulo']}")
            print(f"  Fuzzy/LLM:  {row['esco_occupation_label']} (score: {row['esco_match_score']:.0f}) [BAJA]")
            print(f"  Embeddings: {row['semantic_esco_label']} (sim: {row['semantic_similarity']:.3f}) [ALTA]")
            print()

    # Casos empeorados
    empeorados = df[
        (df['esco_confianza'] == 'alta') &
        (df['semantic_confianza'] == 'baja')
    ]

    print(f"\nCasos con ALTA confianza en Fuzzy/LLM -> BAJA en Embeddings: {len(empeorados):,}\n")

    if len(empeorados) > 0:
        for idx, row in empeorados.head(5).iterrows():
            print(f"Título: {row['titulo']}")
            print(f"  Fuzzy/LLM:  {row['esco_occupation_label']} (score: {row['esco_match_score']:.0f}) [ALTA]")
            print(f"  Embeddings: {row['semantic_esco_label']} (sim: {row['semantic_similarity']:.3f}) [BAJA]")
            print()

    # Estadísticas por ISCO
    print("=" * 100)
    print("[7] TOP 15 OCUPACIONES ISCO")
    print("=" * 100)

    print("\nFuzzy/LLM:")
    fuzzy_isco = df['esco_codigo_isco'].value_counts().head(15)
    for isco, count in fuzzy_isco.items():
        pct = (count / len(df)) * 100
        print(f"  {isco:>15s}: {count:>4,} ({pct:>5.1f}%)")

    print("\nEmbeddings:")
    semantic_isco = df['semantic_isco_code'].value_counts().head(15)
    for isco, count in semantic_isco.items():
        pct = (count / len(df)) * 100
        isco_str = str(isco) if pd.notna(isco) else 'N/A'
        print(f"  {isco_str:>15s}: {count:>4,} ({pct:>5.1f}%)")

    # Guardar reporte
    print("\n" + "=" * 100)
    print("[8] GUARDANDO REPORTE")
    print("=" * 100)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = OUTPUT_DIR / f"comparison_fuzzy_vs_embeddings_{timestamp}.json"

    report = {
        'timestamp': timestamp,
        'total_ofertas': len(df),
        'fuzzy_llm': {
            'matched': int(fuzzy_matched),
            'matched_pct': float(fuzzy_pct),
            'avg_score': float(df['esco_match_score'].mean()),
            'confianza': {
                conf: int(count)
                for conf, count in fuzzy_conf.items()
            }
        },
        'embeddings': {
            'matched': int(semantic_matched),
            'matched_pct': float(semantic_pct),
            'avg_similarity': float(df['semantic_similarity'].mean()),
            'confianza': {
                conf: int(count)
                for conf, count in semantic_conf.items()
            }
        },
        'coincidencias': {
            'ambos_matched': len(both_matched),
            'labels_coinciden': int(coinciden_label),
            'labels_coinciden_pct': float(pct_coinciden),
            'isco_coincide': int(coinciden_isco),
            'isco_coincide_pct': float(pct_isco)
        },
        'mejoras': {
            'baja_a_alta': len(mejorados),
            'alta_a_baja': len(empeorados)
        }
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nOK: Reporte guardado: {report_path}")

    print("\n" + "=" * 100)
    print("ANALISIS COMPLETADO")
    print("=" * 100)


if __name__ == "__main__":
    main()
