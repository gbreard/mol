# -*- coding: utf-8 -*-
"""
Comparación Fuzzy/LLM vs Híbrido (Fuzzy + LLM + Embeddings)
============================================================

Compara los resultados de matching ESCO entre:
- Método original: Fuzzy + LLM
- Método nuevo: Híbrido (Fuzzy + LLM + Embeddings)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

# Archivo con AMBOS resultados
INPUT_FILE = r"D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\ofertas_esco_isco_llm_20251027_191809_hybrid_20251028_193022.csv"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\02.5_nlp_extraction\docs")


def main():
    print("=" * 100)
    print("COMPARACION: FUZZY/LLM vs HIBRIDO")
    print("=" * 100)

    # Cargar datos
    print(f"\n[1] Cargando datos: {Path(INPUT_FILE).name}")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8', low_memory=False)
    print(f"    OK: {len(df):,} ofertas cargadas")

    # Verificar columnas
    required_cols_fuzzy = ['titulo', 'esco_occupation_label', 'esco_codigo_isco', 'esco_match_score', 'esco_confianza']
    required_cols_hybrid = ['hybrid_esco_label', 'hybrid_isco_code', 'hybrid_score', 'hybrid_confidence', 'hybrid_strategy']

    missing = [c for c in required_cols_fuzzy + required_cols_hybrid if c not in df.columns]
    if missing:
        print(f"\nERROR: Faltan columnas: {missing}")
        return

    # Análisis general
    print("\n" + "=" * 100)
    print("[2] ANALISIS GENERAL")
    print("=" * 100)

    # Fuzzy/LLM
    fuzzy_matched = df['esco_occupation_label'].notna().sum()
    fuzzy_pct = (fuzzy_matched / len(df)) * 100
    fuzzy_avg = df['esco_match_score'].mean()

    # Híbrido
    hybrid_matched = df['hybrid_esco_label'].notna().sum()
    hybrid_pct = (hybrid_matched / len(df)) * 100
    hybrid_avg = df['hybrid_score'].mean()

    print(f"\nFuzzy/LLM (original):")
    print(f"  Matched:        {fuzzy_matched:>5,} ({fuzzy_pct:>5.1f}%)")
    print(f"  Sin match:      {len(df) - fuzzy_matched:>5,} ({100-fuzzy_pct:>5.1f}%)")
    print(f"  Score promedio: {fuzzy_avg:>5.1f}")

    print(f"\nHibrido (nuevo):")
    print(f"  Matched:        {hybrid_matched:>5,} ({hybrid_pct:>5.1f}%)")
    print(f"  Sin match:      {len(df) - hybrid_matched:>5,} ({100-hybrid_pct:>5.1f}%)")
    print(f"  Score promedio: {hybrid_avg:>5.3f}")

    print(f"\nMejora:")
    diff_matched = hybrid_matched - fuzzy_matched
    diff_pct = hybrid_pct - fuzzy_pct
    print(f"  Matching:       {diff_matched:+5,} ({diff_pct:+5.1f} pp)")

    # Distribución por confianza
    print("\n" + "=" * 100)
    print("[3] DISTRIBUCION POR CONFIANZA")
    print("=" * 100)

    print("\nFuzzy/LLM:")
    fuzzy_conf = df['esco_confianza'].value_counts().sort_index()
    for conf, count in fuzzy_conf.items():
        pct = (count / len(df)) * 100
        print(f"  {conf:>10s}: {count:>4,} ({pct:>5.1f}%)")

    print("\nHibrido:")
    hybrid_conf = df['hybrid_confidence'].value_counts().sort_index()
    for conf, count in hybrid_conf.items():
        pct = (count / len(df)) * 100
        print(f"  {conf:>10s}: {count:>4,} ({pct:>5.1f}%)")

    # Estrategias híbridas
    print("\n" + "=" * 100)
    print("[4] ESTRATEGIAS UTILIZADAS (Hibrido)")
    print("=" * 100)

    strategies = df['hybrid_strategy'].value_counts()
    for strategy, count in strategies.items():
        pct = (count / len(df)) * 100
        print(f"  {strategy:>30s}: {count:>4,} ({pct:>5.1f}%)")

    # Coincidencia entre métodos
    print("\n" + "=" * 100)
    print("[5] COINCIDENCIA ENTRE METODOS")
    print("=" * 100)

    # Solo casos donde ambos hicieron match
    both_matched = df[
        df['esco_occupation_label'].notna() &
        df['hybrid_esco_label'].notna()
    ].copy()

    print(f"\nCasos con match en AMBOS metodos: {len(both_matched):,}")

    # Coincidencia exacta en ESCO label
    both_matched['labels_coinciden'] = (
        both_matched['esco_occupation_label'] == both_matched['hybrid_esco_label']
    )
    coinciden_label = both_matched['labels_coinciden'].sum()
    pct_coinciden = (coinciden_label / len(both_matched)) * 100

    print(f"  Misma ocupacion ESCO:     {coinciden_label:>4,} ({pct_coinciden:>5.1f}%)")
    print(f"  Diferente ocupacion ESCO: {len(both_matched) - coinciden_label:>4,} ({100-pct_coinciden:>5.1f}%)")

    # Coincidencia en ISCO (más flexible)
    both_matched['isco_coincide'] = (
        both_matched['esco_codigo_isco'] == both_matched['hybrid_isco_code']
    )
    coinciden_isco = both_matched['isco_coincide'].sum()
    pct_isco = (coinciden_isco / len(both_matched)) * 100

    print(f"\n  Mismo ISCO code:          {coinciden_isco:>4,} ({pct_isco:>5.1f}%)")
    print(f"  Diferente ISCO code:      {len(both_matched) - coinciden_isco:>4,} ({100-pct_isco:>5.1f}%)")

    # Casos donde difieren
    print("\n" + "=" * 100)
    print("[6] CASOS DONDE DIFIEREN (Top 20)")
    print("=" * 100)

    difieren = both_matched[~both_matched['labels_coinciden']].copy()

    if len(difieren) > 0:
        print(f"\n{len(difieren):,} casos con diferente ocupacion ESCO:\n")

        for idx, row in difieren.head(20).iterrows():
            print(f"Titulo: {row['titulo']}")
            print(f"  Fuzzy/LLM:  {row['esco_occupation_label']} (ISCO: {row['esco_codigo_isco']}, score: {row['esco_match_score']:.0f}, conf: {row['esco_confianza']})")
            print(f"  Hibrido:    {row['hybrid_esco_label']} (ISCO: {row['hybrid_isco_code']}, score: {row['hybrid_score']:.3f}, conf: {row['hybrid_confidence']}, estrategia: {row['hybrid_strategy']})")
            print()

    # Mejoras con híbrido
    print("=" * 100)
    print("[7] MEJORAS CON HIBRIDO")
    print("=" * 100)

    # Casos con baja confianza en fuzzy -> alta en híbrido
    mejorados = df[
        (df['esco_confianza'] == 'baja') &
        (df['hybrid_confidence'] == 'alta')
    ]

    print(f"\nCasos BAJA confianza (Fuzzy/LLM) -> ALTA (Hibrido): {len(mejorados):,}\n")

    if len(mejorados) > 0:
        for idx, row in mejorados.head(10).iterrows():
            print(f"Titulo: {row['titulo']}")
            print(f"  Fuzzy/LLM:  {row['esco_occupation_label']} (score: {row['esco_match_score']:.0f}) [BAJA]")
            print(f"  Hibrido:    {row['hybrid_esco_label']} (score: {row['hybrid_score']:.3f}) [ALTA] - {row['hybrid_strategy']}")
            print()

    # Casos empeorados
    empeorados = df[
        (df['esco_confianza'] == 'alta') &
        (df['hybrid_confidence'] == 'baja')
    ]

    print(f"\nCasos ALTA confianza (Fuzzy/LLM) -> BAJA (Hibrido): {len(empeorados):,}\n")

    if len(empeorados) > 0:
        for idx, row in empeorados.head(5).iterrows():
            print(f"Titulo: {row['titulo']}")
            print(f"  Fuzzy/LLM:  {row['esco_occupation_label']} (score: {row['esco_match_score']:.0f}) [ALTA]")
            print(f"  Hibrido:    {row['hybrid_esco_label']} (score: {row['hybrid_score']:.3f}) [BAJA] - {row['hybrid_strategy']}")
            print()

    # Casos nuevos (híbrido matcheó, fuzzy no)
    nuevos = df[
        df['esco_occupation_label'].isna() &
        df['hybrid_esco_label'].notna()
    ]

    print(f"\nCasos SIN MATCH (Fuzzy/LLM) -> CON MATCH (Hibrido): {len(nuevos):,}\n")

    if len(nuevos) > 0:
        for idx, row in nuevos.head(10).iterrows():
            print(f"Titulo: {row['titulo']}")
            print(f"  Fuzzy/LLM:  [SIN MATCH]")
            print(f"  Hibrido:    {row['hybrid_esco_label']} (ISCO: {row['hybrid_isco_code']}, score: {row['hybrid_score']:.3f}) - {row['hybrid_strategy']}")
            print()

    # Top ISCO codes
    print("=" * 100)
    print("[8] TOP 15 OCUPACIONES ISCO")
    print("=" * 100)

    print("\nFuzzy/LLM:")
    fuzzy_isco = df['esco_codigo_isco'].value_counts().head(15)
    for isco, count in fuzzy_isco.items():
        pct = (count / len(df)) * 100
        isco_str = str(isco) if pd.notna(isco) else 'N/A'
        print(f"  {isco_str:>15s}: {count:>4,} ({pct:>5.1f}%)")

    print("\nHibrido:")
    hybrid_isco = df['hybrid_isco_code'].value_counts().head(15)
    for isco, count in hybrid_isco.items():
        pct = (count / len(df)) * 100
        isco_str = str(isco) if pd.notna(isco) else 'N/A'
        print(f"  {isco_str:>15s}: {count:>4,} ({pct:>5.1f}%)")

    # Guardar reporte
    print("\n" + "=" * 100)
    print("[9] GUARDANDO REPORTE")
    print("=" * 100)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = OUTPUT_DIR / f"comparison_fuzzy_vs_hybrid_{timestamp}.json"

    report = {
        'timestamp': timestamp,
        'total_ofertas': len(df),
        'fuzzy_llm': {
            'matched': int(fuzzy_matched),
            'matched_pct': float(fuzzy_pct),
            'avg_score': float(fuzzy_avg),
            'confianza': {
                str(conf): int(count)
                for conf, count in fuzzy_conf.items()
            }
        },
        'hibrido': {
            'matched': int(hybrid_matched),
            'matched_pct': float(hybrid_pct),
            'avg_score': float(hybrid_avg),
            'confianza': {
                str(conf): int(count)
                for conf, count in hybrid_conf.items()
            },
            'estrategias': {
                str(strategy): int(count)
                for strategy, count in strategies.items()
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
            'alta_a_baja': len(empeorados),
            'nuevos_matches': len(nuevos)
        }
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nOK: Reporte guardado: {report_path}")

    # Conclusiones
    print("\n" + "=" * 100)
    print("[10] CONCLUSIONES")
    print("=" * 100)

    print("\nRESUMEN:")
    if hybrid_matched > fuzzy_matched:
        print(f"  [+] El metodo hibrido matcheo {diff_matched} ofertas MAS que fuzzy/LLM")
    elif hybrid_matched < fuzzy_matched:
        print(f"  [-] El metodo hibrido matcheo {abs(diff_matched)} ofertas MENOS que fuzzy/LLM")
    else:
        print(f"  [=] Ambos metodos matchearon la misma cantidad de ofertas")

    if len(mejorados) > 0:
        print(f"  [+] {len(mejorados)} casos mejoraron de baja a alta confianza")

    if len(empeorados) > 0:
        print(f"  [-] {len(empeorados)} casos empeoraron de alta a baja confianza")

    if len(nuevos) > 0:
        print(f"  [+] {len(nuevos)} ofertas nuevas matcheadas por hibrido")

    print(f"\n  Coincidencia en ISCO codes: {pct_isco:.1f}%")
    print(f"  Coincidencia en ESCO labels: {pct_coinciden:.1f}%")

    print("\n" + "=" * 100)
    print("ANALISIS COMPLETADO")
    print("=" * 100)


if __name__ == "__main__":
    main()
