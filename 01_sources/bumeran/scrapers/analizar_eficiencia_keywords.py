"""
Analizador de Eficiencia de Keywords - Bumeran
===============================================

Calcula métricas de eficiencia para cada keyword:
- Ofertas únicas (que solo esta keyword captura)
- Ofertas compartidas (overlap con otras keywords)
- Productividad
- Redundancia

Identifica:
- Keywords CRÍTICAS (tienen ofertas únicas > 0)
- Keywords REDUNDANTES (100% overlap, se pueden eliminar)

Uso:
    python analizar_eficiencia_keywords.py bumeran_multi_20251030.json
"""

import pandas as pd
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime


class KeywordMetrics:
    """Métricas de eficiencia de una keyword"""

    def __init__(self, keyword: str):
        self.keyword = keyword
        self.ofertas_totales = 0
        self.ofertas_unicas = 0
        self.ofertas_compartidas = 0
        self.tiempo_scraping = 0.0
        self.ofertas_ids = set()
        self.overlap_keywords = {}  # {keyword: count}
        self.productividad = 0.0
        self.redundancia = 0.0

    def calcular_metricas(self, todas_ofertas_dict):
        """Calcula métricas basadas en todas las keywords"""

        # Ofertas de OTRAS keywords
        ofertas_otras = set()
        for kw, ids in todas_ofertas_dict.items():
            if kw != self.keyword:
                ofertas_otras.update(ids)

        # Ofertas ÚNICAS: solo esta keyword las captura
        self.ofertas_unicas = len(self.ofertas_ids - ofertas_otras)

        # Ofertas COMPARTIDAS: otras keywords también las capturan
        self.ofertas_compartidas = len(self.ofertas_ids & ofertas_otras)

        # Productividad: ofertas únicas por segundo
        if self.tiempo_scraping > 0:
            self.productividad = self.ofertas_unicas / self.tiempo_scraping

        # Redundancia: % de ofertas que otras keywords también capturan
        if len(self.ofertas_ids) > 0:
            self.redundancia = (self.ofertas_compartidas / len(self.ofertas_ids)) * 100

        # Overlap con cada keyword
        for kw, ids in todas_ofertas_dict.items():
            if kw != self.keyword:
                overlap_count = len(self.ofertas_ids & ids)
                if overlap_count > 0:
                    self.overlap_keywords[kw] = overlap_count

    def es_critica(self):
        """Una keyword es crítica si tiene ofertas únicas > 0"""
        return self.ofertas_unicas > 0

    def es_redundante(self):
        """Una keyword es redundante si 100% de sus ofertas las capturan otras"""
        return self.redundancia >= 100.0 and self.ofertas_totales > 0

    def to_dict(self):
        """Convierte a diccionario"""
        return {
            'keyword': self.keyword,
            'ofertas_totales': self.ofertas_totales,
            'ofertas_unicas': self.ofertas_unicas,
            'ofertas_compartidas': self.ofertas_compartidas,
            'productividad': round(self.productividad, 2),
            'redundancia': round(self.redundancia, 2),
            'es_critica': self.es_critica(),
            'es_redundante': self.es_redundante(),
            'top_5_overlap': dict(sorted(self.overlap_keywords.items(), key=lambda x: x[1], reverse=True)[:5])
        }


def analizar_eficiencia_keywords(df):
    """
    Analiza eficiencia de keywords desde DataFrame

    Args:
        df: DataFrame con columnas 'id' y 'keyword_busqueda'

    Returns:
        dict: Métricas por keyword
    """
    print("="*70)
    print("ANALIZADOR DE EFICIENCIA DE KEYWORDS")
    print("="*70)
    print()

    # Validar columnas
    if 'keyword_busqueda' not in df.columns:
        print("ERROR: DataFrame no tiene columna 'keyword_busqueda'")
        return None

    id_col = 'id' if 'id' in df.columns else 'id_oferta'
    if id_col not in df.columns:
        print("ERROR: DataFrame no tiene columna de ID")
        return None

    # 1. Crear diccionario de ofertas por keyword
    print("1. Analizando ofertas por keyword...")
    ofertas_por_keyword = defaultdict(set)

    for _, row in df.iterrows():
        keyword = row['keyword_busqueda']
        oferta_id = str(row[id_col])
        ofertas_por_keyword[keyword].add(oferta_id)

    total_keywords = len(ofertas_por_keyword)
    print(f"   Keywords encontradas: {total_keywords}")
    print()

    # 2. Calcular métricas para cada keyword
    print("2. Calculando métricas de eficiencia...")
    metricas = {}

    for keyword, ids in ofertas_por_keyword.items():
        metrics = KeywordMetrics(keyword)
        metrics.ofertas_totales = len(ids)
        metrics.ofertas_ids = ids
        metrics.calcular_metricas(ofertas_por_keyword)

        metricas[keyword] = metrics

    print(f"   Métricas calculadas para {len(metricas)} keywords")
    print()

    # 3. Clasificar keywords
    keywords_criticas = [m for m in metricas.values() if m.es_critica()]
    keywords_redundantes = [m for m in metricas.values() if m.es_redundante()]

    print("="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    print(f"Total keywords analizadas:  {total_keywords}")
    print(f"Keywords CRÍTICAS:          {len(keywords_criticas)} (tienen ofertas únicas)")
    print(f"Keywords REDUNDANTES:       {len(keywords_redundantes)} (100% overlap)")
    print()

    # 4. Top keywords críticas
    print("="*70)
    print("TOP 15 KEYWORDS CRÍTICAS (más ofertas únicas)")
    print("="*70)
    keywords_criticas_sorted = sorted(keywords_criticas, key=lambda x: x.ofertas_unicas, reverse=True)

    for i, m in enumerate(keywords_criticas_sorted[:15], 1):
        pct_unicas = (m.ofertas_unicas / m.ofertas_totales * 100) if m.ofertas_totales > 0 else 0
        print(f"{i:2d}. '{m.keyword}'")
        print(f"    Ofertas totales: {m.ofertas_totales:3d} | Únicas: {m.ofertas_unicas:3d} ({pct_unicas:.1f}%) | Redundancia: {m.redundancia:.1f}%")

    print()

    # 5. Keywords redundantes
    if keywords_redundantes:
        print("="*70)
        print(f"KEYWORDS REDUNDANTES (se pueden eliminar sin perder cobertura)")
        print("="*70)

        for i, m in enumerate(keywords_redundantes[:20], 1):
            # Encontrar qué keyword(s) cubren esta
            top_overlap = sorted(m.overlap_keywords.items(), key=lambda x: x[1], reverse=True)
            cubierta_por = top_overlap[0][0] if top_overlap else "N/A"
            print(f"{i:2d}. '{m.keyword}' - {m.ofertas_totales} ofertas (cubierta 100% por '{cubierta_por}')")

        print()

    # 6. Estadísticas generales
    total_ofertas = len(set(df[id_col]))
    ofertas_con_criticas = sum(m.ofertas_unicas for m in keywords_criticas)

    print("="*70)
    print("ESTADÍSTICAS GENERALES")
    print("="*70)
    print(f"Total ofertas únicas:            {total_ofertas:,}")
    print(f"Ofertas capturadas por críticas: {ofertas_con_criticas:,}")
    print(f"Promedio ofertas por keyword:    {total_ofertas / total_keywords:.1f}")
    print(f"Promedio redundancia:            {sum(m.redundancia for m in metricas.values()) / len(metricas):.1f}%")
    print()

    # 7. Recomendaciones
    print("="*70)
    print("RECOMENDACIONES")
    print("="*70)
    if len(keywords_redundantes) > 0:
        ahorro_pct = (len(keywords_redundantes) / total_keywords * 100)
        print(f"[OK] Eliminar {len(keywords_redundantes)} keywords redundantes (ahorra {ahorro_pct:.1f}% del tiempo)")
        print(f"[OK] Usar solo {len(keywords_criticas)} keywords críticas para próximas ejecuciones")
    else:
        print("[OK] Todas las keywords aportan valor - Ninguna es 100% redundante")

    print()
    print("="*70)

    return metricas


def guardar_resultados(metricas, output_path=None):
    """Guarda resultados en JSON"""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(__file__).parent.parent / "data" / "metrics" / f"eficiencia_keywords_{timestamp}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    resultados = {
        'timestamp': datetime.now().isoformat(),
        'total_keywords': len(metricas),
        'keywords_criticas': len([m for m in metricas.values() if m.es_critica()]),
        'keywords_redundantes': len([m for m in metricas.values() if m.es_redundante()]),
        'metricas': {kw: m.to_dict() for kw, m in metricas.items()}
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"Resultados guardados: {output_path}")
    return output_path


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python analizar_eficiencia_keywords.py <archivo.json|csv>")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"ERROR: Archivo no encontrado: {input_file}")
        sys.exit(1)

    # Cargar datos
    print(f"Cargando datos desde: {input_file}")
    print()

    if input_file.suffix == '.json':
        df = pd.read_json(input_file)
    elif input_file.suffix == '.csv':
        df = pd.read_csv(input_file)
    else:
        print(f"ERROR: Formato no soportado: {input_file.suffix}")
        sys.exit(1)

    print(f"Datos cargados: {len(df)} ofertas")
    print()

    # Analizar
    metricas = analizar_eficiencia_keywords(df)

    if metricas:
        # Guardar resultados
        guardar_resultados(metricas)


if __name__ == "__main__":
    main()
