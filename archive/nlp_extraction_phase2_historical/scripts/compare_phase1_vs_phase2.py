# -*- coding: utf-8 -*-
"""
Compare Phase 1 vs Phase 2 - Compara resultados de Regex vs NER
================================================================

Script para comparar la calidad de extracción entre Fase 1 (Regex)
y Fase 2 (NER custom model).
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import logging
from typing import Dict, List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase1vs2Comparator:
    """Comparador de resultados Fase 1 vs Fase 2"""

    def __init__(self, phase1_csv: str, phase2_csv: str, output_dir: str = None):
        """
        Inicializa el comparador

        Args:
            phase1_csv: Path al CSV de Fase 1 (regex)
            phase2_csv: Path al CSV de Fase 2 (NER)
            output_dir: Directorio de salida
        """
        self.phase1_csv = Path(phase1_csv)
        self.phase2_csv = Path(phase2_csv)

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            project_root = Path(__file__).parent.parent.parent
            self.output_dir = project_root / "02.5_nlp_extraction" / "reports"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.df_phase1 = None
        self.df_phase2 = None

    def load_data(self):
        """Carga los datasets de ambas fases"""
        logger.info("=" * 70)
        logger.info("CARGANDO DATASETS")
        logger.info("=" * 70)

        logger.info(f"\nFase 1 (Regex): {self.phase1_csv.name}")
        self.df_phase1 = pd.read_csv(self.phase1_csv, encoding='utf-8', low_memory=False)
        logger.info(f"  Ofertas: {len(self.df_phase1):,}")

        logger.info(f"\nFase 2 (NER): {self.phase2_csv.name}")
        self.df_phase2 = pd.read_csv(self.phase2_csv, encoding='utf-8', low_memory=False)
        logger.info(f"  Ofertas: {len(self.df_phase2):,}")

        if len(self.df_phase1) != len(self.df_phase2):
            logger.warning("⚠️  Los datasets tienen diferente número de ofertas")

        logger.info("=" * 70)

    def compare_coverage(self) -> Dict[str, Dict[str, float]]:
        """
        Compara cobertura de campos entre fases

        Returns:
            Dict con métricas de cobertura por campo
        """
        logger.info("\n" + "=" * 70)
        logger.info("COMPARACIÓN DE COBERTURA")
        logger.info("=" * 70)

        # Campos a comparar
        fields = [
            ('experiencia_min_anios', 'Experiencia'),
            ('nivel_educativo', 'Educación'),
            ('idioma_principal', 'Idioma principal'),
            ('skills_tecnicas_list', 'Skills técnicas'),
            ('soft_skills_list', 'Soft skills')
        ]

        comparison = {}

        logger.info("\n{:<25} | {:>12} | {:>12} | {:>10}".format(
            "Campo", "Fase 1", "Fase 2", "Δ"
        ))
        logger.info("-" * 70)

        for field_name, field_label in fields:
            if field_name in self.df_phase1.columns and field_name in self.df_phase2.columns:
                # Cobertura Fase 1
                count1 = self.df_phase1[field_name].notna().sum()
                pct1 = (count1 / len(self.df_phase1)) * 100

                # Cobertura Fase 2
                count2 = self.df_phase2[field_name].notna().sum()
                pct2 = (count2 / len(self.df_phase2)) * 100

                # Delta
                delta = pct2 - pct1

                comparison[field_name] = {
                    'phase1_coverage': pct1,
                    'phase2_coverage': pct2,
                    'delta': delta
                }

                # Formato delta
                delta_str = f"+{delta:.1f}%" if delta > 0 else f"{delta:.1f}%"
                if abs(delta) < 0.1:
                    delta_str = "→"

                logger.info("{:<25} | {:>10.1f}% | {:>10.1f}% | {:>10}".format(
                    field_label, pct1, pct2, delta_str
                ))

        logger.info("=" * 70)

        return comparison

    def compare_confidence(self) -> Dict[str, float]:
        """
        Compara confidence scores entre fases

        Returns:
            Dict con métricas de confidence
        """
        logger.info("\n" + "=" * 70)
        logger.info("COMPARACIÓN DE CONFIDENCE")
        logger.info("=" * 70)

        result = {}

        # Fase 1 confidence
        if 'nlp_confidence_score' in self.df_phase1.columns:
            conf1 = self.df_phase1['nlp_confidence_score'].mean()
            result['phase1_confidence'] = conf1
            logger.info(f"\nFase 1 (Regex) confidence promedio: {conf1:.3f}")

        # Fase 2 confidence
        if 'ner_confidence_score' in self.df_phase2.columns:
            conf2 = self.df_phase2['ner_confidence_score'].mean()
            result['phase2_confidence'] = conf2
            logger.info(f"Fase 2 (NER) confidence promedio: {conf2:.3f}")

        # Delta
        if 'phase1_confidence' in result and 'phase2_confidence' in result:
            delta = result['phase2_confidence'] - result['phase1_confidence']
            result['confidence_delta'] = delta

            delta_str = f"+{delta:.3f}" if delta > 0 else f"{delta:.3f}"
            logger.info(f"\nMejora en confidence: {delta_str} ({delta/result['phase1_confidence']*100:+.1f}%)")

        logger.info("=" * 70)

        return result

    def compare_by_source(self) -> Dict[str, Dict]:
        """
        Compara resultados por fuente

        Returns:
            Dict con métricas por fuente
        """
        if 'fuente' not in self.df_phase1.columns or 'fuente' not in self.df_phase2.columns:
            logger.warning("No hay columna 'fuente' para comparar")
            return {}

        logger.info("\n" + "=" * 70)
        logger.info("COMPARACIÓN POR FUENTE")
        logger.info("=" * 70)

        sources = set(self.df_phase1['fuente'].unique()) | set(self.df_phase2['fuente'].unique())

        comparison = {}

        for source in sorted(sources):
            logger.info(f"\n{source.upper()}:")

            df1_source = self.df_phase1[self.df_phase1['fuente'] == source]
            df2_source = self.df_phase2[self.df_phase2['fuente'] == source]

            if len(df1_source) == 0 or len(df2_source) == 0:
                logger.info("  (no hay datos)")
                continue

            # Confidence
            if 'nlp_confidence_score' in df1_source.columns:
                conf1 = df1_source['nlp_confidence_score'].mean()
            else:
                conf1 = 0

            if 'ner_confidence_score' in df2_source.columns:
                conf2 = df2_source['ner_confidence_score'].mean()
            else:
                conf2 = 0

            # Cobertura promedio
            coverage_fields = ['experiencia_min_anios', 'nivel_educativo', 'skills_tecnicas_list']

            cov1_avg = sum(
                (df1_source[f].notna().sum() / len(df1_source)) * 100
                for f in coverage_fields if f in df1_source.columns
            ) / len(coverage_fields)

            cov2_avg = sum(
                (df2_source[f].notna().sum() / len(df2_source)) * 100
                for f in coverage_fields if f in df2_source.columns
            ) / len(coverage_fields)

            comparison[source] = {
                'phase1_confidence': conf1,
                'phase2_confidence': conf2,
                'phase1_coverage': cov1_avg,
                'phase2_coverage': cov2_avg
            }

            logger.info(f"  Confidence: {conf1:.3f} → {conf2:.3f} ({conf2-conf1:+.3f})")
            logger.info(f"  Cobertura promedio: {cov1_avg:.1f}% → {cov2_avg:.1f}% ({cov2_avg-cov1_avg:+.1f}%)")

        logger.info("=" * 70)

        return comparison

    def analyze_improvements(self) -> Dict[str, List[int]]:
        """
        Analiza qué ofertas mejoraron, empeoraron o se mantuvieron

        Returns:
            Dict con listas de índices por categoría
        """
        logger.info("\n" + "=" * 70)
        logger.info("ANÁLISIS DE MEJORAS")
        logger.info("=" * 70)

        # Calcular "riqueza" de cada oferta (cuántos campos tiene)
        fields = ['experiencia_min_anios', 'nivel_educativo', 'idioma_principal',
                 'skills_tecnicas_list', 'soft_skills_list']

        richness1 = sum(
            self.df_phase1[f].notna().astype(int)
            for f in fields if f in self.df_phase1.columns
        )

        richness2 = sum(
            self.df_phase2[f].notna().astype(int)
            for f in fields if f in self.df_phase2.columns
        )

        # Clasificar
        improved = (richness2 > richness1).sum()
        worsened = (richness2 < richness1).sum()
        unchanged = (richness2 == richness1).sum()

        total = len(richness1)

        logger.info(f"\nMejoraron (más campos): {improved:,} ({improved/total*100:.1f}%)")
        logger.info(f"Empeoraron (menos campos): {worsened:,} ({worsened/total*100:.1f}%)")
        logger.info(f"Sin cambio: {unchanged:,} ({unchanged/total*100:.1f}%)")

        logger.info("=" * 70)

        return {
            'improved_indices': list(richness2[richness2 > richness1].index),
            'worsened_indices': list(richness2[richness2 < richness1].index),
            'unchanged_indices': list(richness2[richness2 == richness1].index)
        }

    def generate_report(self):
        """Genera reporte completo de comparación"""
        logger.info("\n" + "=" * 70)
        logger.info("GENERANDO REPORTE COMPARATIVO")
        logger.info("=" * 70)

        # Ejecutar todas las comparaciones
        coverage_comp = self.compare_coverage()
        confidence_comp = self.compare_confidence()
        source_comp = self.compare_by_source()
        improvements = self.analyze_improvements()

        # Compilar reporte
        report = {
            'timestamp': datetime.now().isoformat(),
            'phase1_file': self.phase1_csv.name,
            'phase2_file': self.phase2_csv.name,
            'phase1_total_offers': len(self.df_phase1),
            'phase2_total_offers': len(self.df_phase2),
            'coverage_comparison': coverage_comp,
            'confidence_comparison': confidence_comp,
            'source_comparison': source_comp,
            'improvements_summary': {
                'improved_count': len(improvements['improved_indices']),
                'worsened_count': len(improvements['worsened_indices']),
                'unchanged_count': len(improvements['unchanged_indices'])
            }
        }

        # Guardar JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"phase1_vs_phase2_comparison_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"\n[GUARDADO] Reporte: {report_path}")
        logger.info(f"[TAMAÑO] {report_path.stat().st_size / 1024:.1f} KB")

        # Generar Markdown resumen
        self._generate_markdown_report(report, timestamp)

        logger.info("=" * 70)

        return report

    def _generate_markdown_report(self, report: Dict, timestamp: str):
        """Genera reporte en Markdown"""
        md_content = f"""# Comparación Fase 1 (Regex) vs Fase 2 (NER)

**Fecha:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Resumen Ejecutivo

- **Total ofertas:** {report['phase1_total_offers']:,}
- **Ofertas mejoradas:** {report['improvements_summary']['improved_count']:,} ({report['improvements_summary']['improved_count']/report['phase1_total_offers']*100:.1f}%)
- **Ofertas sin cambio:** {report['improvements_summary']['unchanged_count']:,} ({report['improvements_summary']['unchanged_count']/report['phase1_total_offers']*100:.1f}%)
- **Ofertas empeoradas:** {report['improvements_summary']['worsened_count']:,} ({report['improvements_summary']['worsened_count']/report['phase1_total_offers']*100:.1f}%)

---

## Comparación de Cobertura

| Campo | Fase 1 | Fase 2 | Δ | Mejora |
|-------|--------|--------|---|--------|
"""

        for field, data in report['coverage_comparison'].items():
            field_name = field.replace('_', ' ').title()
            p1 = data['phase1_coverage']
            p2 = data['phase2_coverage']
            delta = data['delta']
            emoji = "✅" if delta > 5 else "➡️" if abs(delta) < 5 else "⚠️"

            md_content += f"| {field_name} | {p1:.1f}% | {p2:.1f}% | {delta:+.1f}% | {emoji} |\n"

        md_content += """
---

## Comparación de Confidence

"""

        if 'confidence_comparison' in report:
            conf_data = report['confidence_comparison']
            if 'phase1_confidence' in conf_data and 'phase2_confidence' in conf_data:
                p1_conf = conf_data['phase1_confidence']
                p2_conf = conf_data['phase2_confidence']
                delta_conf = conf_data.get('confidence_delta', 0)

                md_content += f"""
- **Fase 1 (Regex):** {p1_conf:.3f}
- **Fase 2 (NER):** {p2_conf:.3f}
- **Mejora:** {delta_conf:+.3f} ({delta_conf/p1_conf*100:+.1f}%)

"""

        md_content += """---

## Comparación por Fuente

"""

        for source, data in report.get('source_comparison', {}).items():
            conf1 = data['phase1_confidence']
            conf2 = data['phase2_confidence']
            cov1 = data['phase1_coverage']
            cov2 = data['phase2_coverage']

            md_content += f"""
### {source.upper()}

- **Confidence:** {conf1:.3f} → {conf2:.3f} ({conf2-conf1:+.3f})
- **Cobertura promedio:** {cov1:.1f}% → {cov2:.1f}% ({cov2-cov1:+.1f}%)

"""

        md_content += """---

## Conclusiones

"""

        # Calcular mejora promedio
        if report['coverage_comparison']:
            avg_delta = sum(d['delta'] for d in report['coverage_comparison'].values()) / len(report['coverage_comparison'])

            if avg_delta > 10:
                md_content += "✅ **Mejora significativa** en cobertura con NER (>10% promedio)\n\n"
            elif avg_delta > 0:
                md_content += "➡️ **Mejora moderada** en cobertura con NER\n\n"
            else:
                md_content += "⚠️ **Sin mejora** significativa con NER\n\n"

        md_content += """
### Recomendaciones

1. Revisar ofertas que empeoraron para identificar patrones
2. Analizar campos con menor mejora para ajustar modelo NER
3. Considerar ensemble de Regex + NER para maximizar recall
4. Evaluar si el costo de anotación justifica la mejora obtenida

---

*Reporte generado automáticamente por compare_phase1_vs_phase2.py*
"""

        # Guardar Markdown
        md_path = self.output_dir / f"phase1_vs_phase2_comparison_{timestamp}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"[GUARDADO] Reporte Markdown: {md_path}")


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Compara resultados Fase 1 (Regex) vs Fase 2 (NER)')

    parser.add_argument(
        '--phase1',
        type=str,
        required=True,
        help='Path al CSV de Fase 1 (regex)'
    )

    parser.add_argument(
        '--phase2',
        type=str,
        required=True,
        help='Path al CSV de Fase 2 (NER)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Directorio de salida para reportes'
    )

    args = parser.parse_args()

    # Crear comparador
    comparator = Phase1vs2Comparator(
        phase1_csv=args.phase1,
        phase2_csv=args.phase2,
        output_dir=args.output_dir
    )

    # Cargar datos
    comparator.load_data()

    # Generar reporte
    comparator.generate_report()

    logger.info("\n¡Comparación completada!")


if __name__ == "__main__":
    main()
