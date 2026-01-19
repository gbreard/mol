#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Reporte de Calidad - ESCO/ISCO Matching
Analiza los resultados del matching y genera un reporte detallado
"""

import pandas as pd
import json
from pathlib import Path
from collections import Counter
from datetime import datetime
import sys

class ESCOQualityReporter:
    """Genera reportes de calidad para matching ESCO/ISCO"""

    def __init__(self, matched_csv_path: str):
        """
        Inicializa el reporter

        Args:
            matched_csv_path: Ruta al CSV con resultados de matching
        """
        print(f"[*] Cargando datos de matching...")
        self.df = pd.read_csv(matched_csv_path, low_memory=False)
        print(f"[OK] Cargadas {len(self.df):,} ofertas\n")

    def generar_reporte_completo(self) -> dict:
        """Genera reporte completo de calidad"""

        print("=" * 80)
        print("REPORTE DE CALIDAD - MATCHING ESCO/ISCO")
        print("=" * 80)
        print()

        reporte = {}

        # 1. Estadísticas Generales
        print("[1] ESTADISTICAS GENERALES")
        print("-" * 80)
        reporte['general'] = self._estadisticas_generales()
        print()

        # 2. Distribución por Confianza
        print("[2] DISTRIBUCION POR NIVEL DE CONFIANZA")
        print("-" * 80)
        reporte['confianza'] = self._distribucion_confianza()
        print()

        # 3. Top Ocupaciones ESCO
        print("[3] TOP 20 OCUPACIONES ESCO MAS FRECUENTES")
        print("-" * 80)
        reporte['top_ocupaciones'] = self._top_ocupaciones_esco()
        print()

        # 4. Distribución ISCO
        print("[4] DISTRIBUCION POR CODIGO ISCO")
        print("-" * 80)
        reporte['isco'] = self._distribucion_isco()
        print()

        # 5. Análisis de Skills Overlap
        print("[5] ANALISIS DE SKILLS OVERLAP")
        print("-" * 80)
        reporte['skills'] = self._analisis_skills()
        print()

        # 6. Ejemplos de Alta Confianza
        print("[6] EJEMPLOS DE MATCHES DE ALTA CONFIANZA (Top 10)")
        print("-" * 80)
        reporte['ejemplos_alta'] = self._ejemplos_alta_confianza()
        print()

        # 7. Ejemplos de Baja Confianza
        print("[7] CASOS DE BAJA CONFIANZA PARA REVISION (Top 15)")
        print("-" * 80)
        reporte['ejemplos_baja'] = self._ejemplos_baja_confianza()
        print()

        # 8. Análisis por Fuente
        print("[8] DISTRIBUCION POR FUENTE DE DATOS")
        print("-" * 80)
        reporte['fuentes'] = self._analisis_por_fuente()
        print()

        # 9. Recomendaciones
        print("[9] RECOMENDACIONES Y PROXIMOS PASOS")
        print("-" * 80)
        self._generar_recomendaciones()
        print()

        return reporte

    def _estadisticas_generales(self) -> dict:
        """Calcula estadísticas generales del matching"""
        stats = {
            'total_ofertas': len(self.df),
            'con_esco_id': self.df['esco_occupation_id'].notna().sum(),
            'con_isco_code': self.df['esco_codigo_isco'].notna().sum(),
            'score_promedio': self.df['esco_match_score'].mean(),
            'score_mediana': self.df['esco_match_score'].median(),
            'score_min': self.df['esco_match_score'].min(),
            'score_max': self.df['esco_match_score'].max(),
            'overlap_promedio': self.df['esco_skills_overlap'].mean(),
        }

        print(f"  Total ofertas procesadas:       {stats['total_ofertas']:>8,}")
        print(f"  Con ESCO Occupation ID:         {stats['con_esco_id']:>8,} ({stats['con_esco_id']/stats['total_ofertas']*100:>5.1f}%)")
        print(f"  Con código ISCO:                {stats['con_isco_code']:>8,} ({stats['con_isco_code']/stats['total_ofertas']*100:>5.1f}%)")
        print()
        print(f"  Score fuzzy matching:")
        print(f"    - Promedio:                   {stats['score_promedio']:>8.1f}")
        print(f"    - Mediana:                    {stats['score_mediana']:>8.1f}")
        print(f"    - Mínimo:                     {stats['score_min']:>8.1f}")
        print(f"    - Máximo:                     {stats['score_max']:>8.1f}")
        print()
        print(f"  Skills overlap promedio:        {stats['overlap_promedio']:>8.1f}%")

        return stats

    def _distribucion_confianza(self) -> dict:
        """Analiza distribución por nivel de confianza"""
        dist = self.df['esco_confianza'].value_counts()

        resultado = {}
        for confianza, count in dist.items():
            pct = count / len(self.df) * 100
            resultado[confianza] = {'count': int(count), 'pct': pct}
            print(f"  {confianza:>15}: {count:>6,} ({pct:>5.1f}%)")

        # Análisis de scores por confianza
        print()
        print("  Scores por nivel de confianza:")
        for confianza in dist.index:
            subset = self.df[self.df['esco_confianza'] == confianza]['esco_match_score']
            print(f"    {confianza:>12}: avg={subset.mean():.1f}, min={subset.min():.1f}, max={subset.max():.1f}")

        return resultado

    def _top_ocupaciones_esco(self) -> list:
        """Lista las top ocupaciones ESCO"""
        top = self.df['esco_occupation_label'].value_counts().head(20)

        resultado = []
        for i, (ocupacion, count) in enumerate(top.items(), 1):
            pct = count / len(self.df) * 100
            resultado.append({
                'ocupacion': ocupacion,
                'count': int(count),
                'pct': pct
            })

            # Obtener código ISCO de esta ocupación
            isco = self.df[self.df['esco_occupation_label'] == ocupacion]['esco_codigo_isco'].iloc[0]
            print(f"  {i:>2}. {ocupacion:<50} | {count:>4} ({pct:>4.1f}%) | ISCO: {isco}")

        return resultado

    def _distribucion_isco(self) -> dict:
        """Analiza distribución por códigos ISCO"""

        # Análisis por nivel de dígitos
        resultado = {}

        # ISCO 1 dígito (grandes grupos)
        print("  Por grandes grupos (1 dígito):")
        self.df['isco_1digit'] = self.df['esco_codigo_isco'].apply(
            lambda x: str(x)[0] if pd.notna(x) else None
        )
        isco_1 = self.df['isco_1digit'].value_counts().head(10)
        resultado['isco_1digit'] = {}

        isco_labels = {
            '1': 'Directores y gerentes',
            '2': 'Profesionales científicos e intelectuales',
            '3': 'Técnicos y profesionales de nivel medio',
            '4': 'Personal de apoyo administrativo',
            '5': 'Trabajadores de servicios y vendedores',
            '6': 'Agricultores y trabajadores agropecuarios',
            '7': 'Oficiales, operarios y artesanos',
            '8': 'Operadores de instalaciones y máquinas',
            '9': 'Ocupaciones elementales',
            '0': 'Ocupaciones militares'
        }

        for digit, count in isco_1.items():
            if digit:
                pct = count / len(self.df) * 100
                label = isco_labels.get(digit, 'Desconocido')
                resultado['isco_1digit'][digit] = {
                    'label': label,
                    'count': int(count),
                    'pct': pct
                }
                print(f"    {digit} - {label:<45} | {count:>4} ({pct:>4.1f}%)")

        print()

        # Top códigos ISCO completos
        print("  Top 15 códigos ISCO completos más frecuentes:")
        top_isco = self.df['esco_codigo_isco'].value_counts().head(15)
        resultado['top_isco'] = []

        for i, (codigo, count) in enumerate(top_isco.items(), 1):
            pct = count / len(self.df) * 100
            resultado['top_isco'].append({
                'codigo': codigo,
                'count': int(count),
                'pct': pct
            })

            # Obtener una ocupación ejemplo
            ejemplo = self.df[self.df['esco_codigo_isco'] == codigo]['esco_occupation_label'].iloc[0]
            print(f"    {i:>2}. {codigo:<12} | {count:>4} ({pct:>4.1f}%) | Ej: {ejemplo[:45]}")

        return resultado

    def _analisis_skills(self) -> dict:
        """Analiza el overlap de skills"""

        stats = {
            'promedio': float(self.df['esco_skills_overlap'].mean()),
            'mediana': float(self.df['esco_skills_overlap'].median()),
            'max': float(self.df['esco_skills_overlap'].max()),
        }

        # Distribución
        no_overlap = (self.df['esco_skills_overlap'] == 0).sum()
        bajo_overlap = ((self.df['esco_skills_overlap'] > 0) & (self.df['esco_skills_overlap'] < 30)).sum()
        medio_overlap = ((self.df['esco_skills_overlap'] >= 30) & (self.df['esco_skills_overlap'] < 60)).sum()
        alto_overlap = (self.df['esco_skills_overlap'] >= 60).sum()

        print(f"  Overlap promedio:           {stats['promedio']:>6.1f}%")
        print(f"  Overlap mediana:            {stats['mediana']:>6.1f}%")
        print(f"  Overlap maximo:             {stats['max']:>6.1f}%")
        print()
        print("  Distribucion:")
        print(f"    Sin overlap (0%):         {no_overlap:>6,} ({no_overlap/len(self.df)*100:>5.1f}%)")
        print(f"    Bajo (<30%):              {bajo_overlap:>6,} ({bajo_overlap/len(self.df)*100:>5.1f}%)")
        print(f"    Medio (30-59%):           {medio_overlap:>6,} ({medio_overlap/len(self.df)*100:>5.1f}%)")
        print(f"    Alto (>=60%):             {alto_overlap:>6,} ({alto_overlap/len(self.df)*100:>5.1f}%)")

        stats['distribucion'] = {
            'sin_overlap': int(no_overlap),
            'bajo': int(bajo_overlap),
            'medio': int(medio_overlap),
            'alto': int(alto_overlap)
        }

        if stats['promedio'] == 0:
            print()
            print("  [!] NOTA: El overlap de skills es 0% en todos los casos.")
            print("      Esto puede indicar:")
            print("      - Las ocupaciones matcheadas no tienen relaciones de skills en ESCO")
            print("      - Hay desajuste entre los labels de skills extraídas y ESCO")
            print("      - El fuzzy matching de skills necesita ajuste de umbral")

        return stats

    def _ejemplos_alta_confianza(self) -> list:
        """Muestra ejemplos de matches de alta confianza"""

        # Obtener top scores
        alta = self.df.nlargest(10, 'esco_match_score')

        ejemplos = []
        for i, (_, row) in enumerate(alta.iterrows(), 1):
            # Handle NaN values
            titulo = str(row['titulo']) if pd.notna(row['titulo']) else '[Sin titulo]'
            isco = str(row['esco_codigo_isco']) if pd.notna(row['esco_codigo_isco']) else '[Sin ISCO]'

            ejemplo = {
                'titulo': titulo,
                'esco_label': row['esco_occupation_label'],
                'isco': isco,
                'score': float(row['esco_match_score']),
                'confianza': row['esco_confianza']
            }
            ejemplos.append(ejemplo)

            print(f"  {i:>2}. Score: {ejemplo['score']:.1f} | Confianza: {ejemplo['confianza']}")
            print(f"      Titulo:         {ejemplo['titulo'][:60]}")
            print(f"      ESCO:           {ejemplo['esco_label']}")
            print(f"      ISCO:           {ejemplo['isco']}")
            print()

        return ejemplos

    def _ejemplos_baja_confianza(self) -> list:
        """Muestra casos de baja confianza para revisión"""

        # Obtener casos de baja confianza con scores más bajos
        baja = self.df[self.df['esco_confianza'] == 'baja'].nsmallest(15, 'esco_match_score')

        if len(baja) == 0:
            print("  [OK] No hay casos de baja confianza")
            return []

        ejemplos = []
        for i, (_, row) in enumerate(baja.iterrows(), 1):
            # Handle NaN values
            titulo = str(row['titulo']) if pd.notna(row['titulo']) else '[Sin titulo]'
            isco = str(row['esco_codigo_isco']) if pd.notna(row['esco_codigo_isco']) else '[Sin ISCO]'

            ejemplo = {
                'titulo': titulo,
                'esco_label': row['esco_occupation_label'],
                'isco': isco,
                'score': float(row['esco_match_score']),
                'soft_skills': row.get('soft_skills', ''),
                'skills_tecnicas': row.get('skills_tecnicas', '')
            }
            ejemplos.append(ejemplo)

            print(f"  {i:>2}. Score: {ejemplo['score']:.1f} (REVISAR)")
            print(f"      Titulo:         {ejemplo['titulo'][:60]}")
            print(f"      ESCO asignado:  {ejemplo['esco_label']}")
            print(f"      ISCO:           {ejemplo['isco']}")

            # Mostrar skills si existen
            if pd.notna(ejemplo['soft_skills']) or pd.notna(ejemplo['skills_tecnicas']):
                skills = []
                if pd.notna(ejemplo['soft_skills']):
                    skills.extend(str(ejemplo['soft_skills']).split(',')[:3])
                if pd.notna(ejemplo['skills_tecnicas']):
                    skills.extend(str(ejemplo['skills_tecnicas']).split(',')[:2])
                if skills:
                    print(f"      Skills:         {', '.join(skills)[:60]}...")
            print()

        return ejemplos

    def _analisis_por_fuente(self) -> dict:
        """Analiza distribución por fuente de datos"""

        if 'fuente' not in self.df.columns:
            print("  [!] Columna 'fuente' no disponible")
            return {}

        fuentes = self.df['fuente'].value_counts()

        resultado = {}
        for fuente, count in fuentes.items():
            pct = count / len(self.df) * 100

            # Score promedio por fuente
            avg_score = self.df[self.df['fuente'] == fuente]['esco_match_score'].mean()

            resultado[fuente] = {
                'count': int(count),
                'pct': pct,
                'avg_score': float(avg_score)
            }

            print(f"  {fuente:<20} | {count:>5,} ({pct:>5.1f}%) | Score avg: {avg_score:.1f}")

        return resultado

    def _generar_recomendaciones(self):
        """Genera recomendaciones basadas en el análisis"""

        # Calcular métricas clave
        baja_confianza_pct = (self.df['esco_confianza'] == 'baja').sum() / len(self.df) * 100
        score_promedio = self.df['esco_match_score'].mean()
        overlap_promedio = self.df['esco_skills_overlap'].mean()

        print()

        # Recomendación 1: Fuzzy matching
        if score_promedio >= 90:
            print("  [OK] 1. FUZZY MATCHING: Excelente (score promedio >= 90)")
            print("       - El matching basado en titulos funciona muy bien")
            print("       - La mayoria de titulos tienen correspondencia directa con ESCO")
        elif score_promedio >= 80:
            print("  [OK] 1. FUZZY MATCHING: Bueno (score promedio >= 80)")
            print("       - El matching funciona bien en general")
            print("       - Considerar revisar manualmente casos con score < 75")
        else:
            print("  [!] 1. FUZZY MATCHING: Mejorable (score promedio < 80)")
            print("       - Considerar implementar matching semantico con LLM")
            print("       - Revisar normalizacion de titulos")

        print()

        # Recomendación 2: Confianza
        if baja_confianza_pct <= 10:
            print("  [OK] 2. CONFIANZA: Excelente (<= 10% baja confianza)")
            print("       - Solo casos puntuales requieren revision")
        elif baja_confianza_pct <= 20:
            print("  [OK] 2. CONFIANZA: Aceptable (10-20% baja confianza)")
            print(f"       - Revisar manualmente {int(self.df['esco_confianza'].value_counts().get('baja', 0))} casos de baja confianza")
        else:
            print("  [!] 2. CONFIANZA: Mejorable (> 20% baja confianza)")
            print("       - Implementar matching con LLM para casos de score < 70")
            print("       - Considerar usar descripcion ademas de titulo")

        print()

        # Recomendación 3: Skills
        if overlap_promedio == 0:
            print("  [!] 3. SKILLS OVERLAP: Sin validacion")
            print("       - El overlap de skills no esta funcionando")
            print("       - PROXIMOS PASOS:")
            print("         a) Verificar que ocupaciones matcheadas tengan relaciones en ESCO")
            print("         b) Revisar normalizacion de skills extraidas vs ESCO")
            print("         c) Ajustar umbral de fuzzy matching de skills (actual: 80)")
            print("         d) Considerar matching semantico para skills (embeddings)")
        elif overlap_promedio < 30:
            print("  [!] 3. SKILLS OVERLAP: Bajo (< 30%)")
            print("       - Las skills extraidas no coinciden bien con ESCO")
            print("       - Revisar calidad de extraccion de skills")
        else:
            print("  [OK] 3. SKILLS OVERLAP: Funcional")
            print("       - Las skills validan correctamente los matches")

        print()

        # Recomendación 4: Próximos pasos
        print("  [*] 4. PROXIMOS PASOS SUGERIDOS:")
        print()

        if baja_confianza_pct > 15:
            print("     a) Implementar LLM fallback para casos score < 70")
            print("        - Usar Ollama llama3 con prompt estructurado")
            print("        - Incluir descripción + skills en el prompt")
            print()

        if overlap_promedio == 0:
            print("     b) Investigar y corregir skills overlap:")
            print("        - Ejecutar script de diagnóstico de relaciones ESCO")
            print("        - Verificar cobertura de ocupaciones en esco_ocupaciones_skills_relaciones.json")
            print()

        print("     c) Validación manual de muestra:")
        print(f"        - Revisar {min(50, int(self.df['esco_confianza'].value_counts().get('baja', 0)))} casos de baja confianza")
        print("        - Verificar 20-30 casos de alta confianza aleatoriamente")
        print()

        print("     d) Enriquecimiento de ofertas:")
        print("        - Agregar skills esenciales ESCO a ofertas con pocas skills")
        print("        - Usar el código ISCO para análisis agregados")
        print()

        print("     e) Integración con datos SIPA:")
        print("        - Cruzar códigos ISCO con clasificaciones de empleo registrado")
        print("        - Comparar demanda (ofertas) vs oferta (trabajadores SIPA)")
        print()

    def guardar_reporte_json(self, reporte: dict, output_path: str):
        """Guarda el reporte en formato JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n[FILE] Reporte JSON guardado: {output_path}")


def main():
    """Función principal"""

    # Ruta al archivo de matching
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        # Buscar el más reciente
        data_dir = Path(__file__).parent.parent / 'data' / 'processed'
        csv_files = list(data_dir.glob('ofertas_esco_isco_*.csv'))
        if not csv_files:
            print("[ERROR] No se encontraron archivos ofertas_esco_isco_*.csv")
            return
        csv_path = max(csv_files, key=lambda p: p.stat().st_mtime)

    print(f"[FILE] Archivo: {csv_path}")
    print()

    # Generar reporte
    reporter = ESCOQualityReporter(str(csv_path))
    reporte = reporter.generar_reporte_completo()

    # Guardar JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = Path(csv_path).parent / f'esco_quality_report_{timestamp}.json'
    reporter.guardar_reporte_json(reporte, str(output_path))

    print()
    print("=" * 80)
    print("[OK] REPORTE COMPLETADO")
    print("=" * 80)


if __name__ == '__main__':
    main()
