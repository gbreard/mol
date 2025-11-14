"""
Dashboard de Keywords - Bumeran
================================

Genera un reporte visual de eficiencia de keywords con recomendaciones.

Muestra:
- Resumen general de cobertura
- Top keywords críticas
- Keywords redundantes (se pueden eliminar)
- Matriz de overlap
- Recomendaciones de optimización

Uso:
    python dashboard_keywords.py <archivo_metricas.json>
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def cargar_metricas(filepath):
    """Carga métricas desde JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generar_dashboard(metricas_data):
    """Genera dashboard visual de keywords"""

    metricas = metricas_data['metricas']
    total_keywords = metricas_data['total_keywords']
    keywords_criticas = metricas_data['keywords_criticas']
    keywords_redundantes = metricas_data['keywords_redundantes']

    print("="*80)
    print(" "*25 + "DASHBOARD DE KEYWORDS - BUMERAN")
    print("="*80)
    print()

    # 1. RESUMEN GENERAL
    print("="*80)
    print("RESUMEN GENERAL")
    print("="*80)

    total_ofertas_unicas = len(set(
        oferta_id
        for m in metricas.values()
        for oferta_id in range(m['ofertas_unicas'])
    ))

    total_ofertas_brutas = sum(m['ofertas_totales'] for m in metricas.values())

    eficiencia_global = (keywords_criticas / total_keywords * 100) if total_keywords > 0 else 0

    print(f"Total keywords analizadas:     {total_keywords}")
    print(f"Keywords CRÍTICAS:             {keywords_criticas} ({eficiencia_global:.1f}% del total)")
    print(f"Keywords REDUNDANTES:          {keywords_redundantes}")
    print(f"Total ofertas (con duplicados): {total_ofertas_brutas:,}")
    print()

    # 2. KEYWORDS CRÍTICAS
    print("="*80)
    print("TOP 20 KEYWORDS CRÍTICAS (Ordenadas por ofertas únicas)")
    print("="*80)
    print()
    print(f"{'#':<4} {'Keyword':<25} {'Ofertas':<10} {'Únicas':<10} {'%Única':<10} {'Redund%':<10}")
    print("-"*80)

    criticas = [(kw, m) for kw, m in metricas.items() if m['es_critica']]
    criticas_sorted = sorted(criticas, key=lambda x: x[1]['ofertas_unicas'], reverse=True)

    for i, (kw, m) in enumerate(criticas_sorted[:20], 1):
        pct_unicas = (m['ofertas_unicas'] / m['ofertas_totales'] * 100) if m['ofertas_totales'] > 0 else 0
        print(f"{i:<4} {kw[:24]:<25} {m['ofertas_totales']:<10} {m['ofertas_unicas']:<10} {pct_unicas:<9.1f}% {m['redundancia']:<9.1f}%")

    print()

    # 3. KEYWORDS REDUNDANTES
    if keywords_redundantes > 0:
        print("="*80)
        print(f"KEYWORDS REDUNDANTES ({keywords_redundantes} total)")
        print("="*80)
        print("Estas keywords NO aportan valor - Todas sus ofertas las capturan otras keywords")
        print()
        print(f"{'#':<4} {'Keyword':<25} {'Ofertas':<10} {'Cubierta por':<30}")
        print("-"*80)

        redundantes = [(kw, m) for kw, m in metricas.items() if m['es_redundante']]
        redundantes_sorted = sorted(redundantes, key=lambda x: x[1]['ofertas_totales'], reverse=True)

        for i, (kw, m) in enumerate(redundantes_sorted[:30], 1):
            # Encontrar keyword que más overlap tiene
            if m['top_5_overlap']:
                top_overlap_kw = max(m['top_5_overlap'].items(), key=lambda x: x[1])[0]
            else:
                top_overlap_kw = "N/A"

            print(f"{i:<4} {kw[:24]:<25} {m['ofertas_totales']:<10} {top_overlap_kw[:29]:<30}")

        print()

    # 4. ANÁLISIS DE OVERLAP
    print("="*80)
    print("ANÁLISIS DE OVERLAP (Top 15 keywords)")
    print("="*80)
    print()

    # Calcular pares con mayor overlap
    overlap_pairs = []
    keywords_list = list(metricas.keys())

    for i, kw1 in enumerate(keywords_list):
        m1 = metricas[kw1]
        if m1['top_5_overlap']:
            for kw2, count in m1['top_5_overlap'].items():
                if kw1 < kw2:  # Evitar duplicados (A-B y B-A)
                    overlap_pairs.append((kw1, kw2, count))

    overlap_pairs_sorted = sorted(overlap_pairs, key=lambda x: x[2], reverse=True)

    print(f"{'Keyword 1':<25} {'Keyword 2':<25} {'Ofertas compartidas':<20}")
    print("-"*80)

    for kw1, kw2, count in overlap_pairs_sorted[:15]:
        print(f"{kw1[:24]:<25} {kw2[:24]:<25} {count:<20}")

    print()

    # 5. PRODUCTIVIDAD
    print("="*80)
    print("TOP 10 KEYWORDS MÁS PRODUCTIVAS (Ofertas únicas / segundo)")
    print("="*80)
    print()

    productivas = [(kw, m) for kw, m in metricas.items() if m['productividad'] > 0]
    productivas_sorted = sorted(productivas, key=lambda x: x[1]['productividad'], reverse=True)

    print(f"{'Keyword':<25} {'Productividad':<15} {'Ofertas únicas':<15}")
    print("-"*80)

    for kw, m in productivas_sorted[:10]:
        print(f"{kw[:24]:<25} {m['productividad']:<14.2f}  {m['ofertas_unicas']:<15}")

    print()

    # 6. RECOMENDACIONES
    print("="*80)
    print("RECOMENDACIONES DE OPTIMIZACIÓN")
    print("="*80)
    print()

    if keywords_redundantes > 0:
        ahorro_tiempo = (keywords_redundantes / total_keywords * 100)
        print(f"[1] ELIMINAR {keywords_redundantes} keywords redundantes")
        print(f"    Ahorro: {ahorro_tiempo:.1f}% del tiempo de scraping")
        print(f"    Pérdida de cobertura: 0%")
        print()

    if keywords_criticas < total_keywords:
        print(f"[2] USAR SOLO {keywords_criticas} keywords críticas")
        print(f"    Mantiene cobertura completa")
        print(f"    Tiempo estimado: {keywords_criticas * 2:.0f}s vs {total_keywords * 2:.0f}s actual")
        print()

    # Identificar keywords de baja productividad
    baja_prod = [m for m in metricas.values() if m['ofertas_unicas'] == 1 and m['ofertas_totales'] < 5]
    if len(baja_prod) > 5:
        print(f"[3] REVISAR {len(baja_prod)} keywords de baja productividad")
        print(f"    Traen solo 1 oferta única cada una")
        print(f"    Considerar si vale la pena mantenerlas")
        print()

    # Keywords con alta redundancia pero que aportan valor
    alta_red_valor = [
        (kw, m) for kw, m in metricas.items()
        if m['redundancia'] > 70 and m['ofertas_unicas'] > 0 and m['ofertas_unicas'] < 5
    ]
    if alta_red_valor:
        print(f"[4] EVALUAR {len(alta_red_valor)} keywords con alta redundancia")
        print(f"    Tienen >70% overlap pero aportan algunas ofertas únicas")
        print(f"    Ejemplos:")
        for kw, m in sorted(alta_red_valor, key=lambda x: x[1]['redundancia'], reverse=True)[:5]:
            print(f"    - '{kw}': {m['ofertas_unicas']} únicas, {m['redundancia']:.1f}% redundancia")
        print()

    # 7. CONFIGURACIÓN OPTIMIZADA
    print("="*80)
    print("CONFIGURACIÓN OPTIMIZADA SUGERIDA")
    print("="*80)
    print()

    print("Usar solo keywords críticas:")
    print()
    print("KEYWORDS_OPTIMIZADAS = [")

    for i, (kw, m) in enumerate(criticas_sorted[:20], 1):
        print(f"    '{kw}',  # {m['ofertas_unicas']} únicas")

    print("    ...")
    print("]")
    print()

    print(f"Total: {keywords_criticas} keywords (vs {total_keywords} actuales)")
    print(f"Tiempo estimado: ~{keywords_criticas * 2:.0f}s (~{keywords_criticas * 2 / 60:.1f} min)")
    print()

    print("="*80)


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python dashboard_keywords.py <eficiencia_keywords.json>")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"ERROR: Archivo no encontrado: {filepath}")
        sys.exit(1)

    print(f"Cargando métricas desde: {filepath}")
    print()

    metricas_data = cargar_metricas(filepath)

    generar_dashboard(metricas_data)


if __name__ == "__main__":
    main()
