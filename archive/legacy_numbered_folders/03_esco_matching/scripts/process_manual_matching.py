# -*- coding: utf-8 -*-
"""
Procesador de Matching Manual - Claude
=======================================

Procesa las 268 ofertas con razonamiento inteligente.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from manual_matcher_claude import ManualMatcher, TextNormalizer


class ClaudeMatchingProcessor:
    """Procesa matching con razonamiento de Claude"""

    def __init__(self):
        self.matcher = ManualMatcher()
        self.reglas_normalizacion = self._build_normalization_rules()
        self.patrones_identificados = []

    def _build_normalization_rules(self):
        """Diccionario de normalización jerga argentina → ESCO"""
        return {
            # Vendedores/Promotores
            'promovendedor': {'keywords': ['promotor', 'ventas', 'demostrador'], 'isco_prefix': '5'},
            'promovendedora': {'keywords': ['promotor', 'ventas', 'demostrador'], 'isco_prefix': '5'},
            'vendedor': {'keywords': ['vendedor', 'comercial'], 'isco_prefix': '5'},

            # Conductores
            'chofer': {'keywords': ['conductor', 'vehiculo'], 'isco_prefix': '8'},
            'conductor': {'keywords': ['conductor', 'vehiculo'], 'isco_prefix': '8'},

            # Operarios
            'operario': {'keywords': ['operario', 'operador'], 'isco_prefix': '8'},
            'operador': {'keywords': ['operador'], 'isco_prefix': '8'},

            # Administrativos
            'administrativo': {'keywords': ['administrativo', 'oficina'], 'isco_prefix': '4'},
            'asistente administrativo': {'keywords': ['asistente', 'administrativo'], 'isco_prefix': '4'},

            # Profesionales
            'analista': {'keywords': ['analista'], 'isco_prefix': '2'},
            'asesor': {'keywords': ['asesor', 'consultor'], 'isco_prefix': '2'},

            # Técnicos
            'tecnico': {'keywords': ['tecnico'], 'isco_prefix': '3'},

            # Mantenimiento
            'mantenimiento': {'keywords': ['mantenimiento'], 'isco_prefix': '7'},

            # Coordinador/Responsable
            'coordinador': {'keywords': ['coordinador', 'supervisor'], 'isco_prefix': '1'},
            'responsable': {'keywords': ['responsable', 'encargado'], 'isco_prefix': '1'},
        }

    def analizar_titulo(self, titulo):
        """
        Analiza título y retorna keywords + ISCO sugerido

        Returns:
            dict con análisis
        """
        titulo_norm = TextNormalizer.normalize(titulo)

        # Identificar palabras clave
        keywords = []
        isco_prefix = None

        # Buscar en reglas de normalización
        for term, config in self.reglas_normalizacion.items():
            if term in titulo_norm:
                keywords.extend(config['keywords'])
                if not isco_prefix:
                    isco_prefix = config['isco_prefix']

        # Si no encontró en reglas, usar heurística
        if not isco_prefix:
            isco_prefix = self.matcher.get_isco_level(titulo_norm)

        # Extraer keywords adicionales del título
        palabras = titulo_norm.split()
        keywords_extra = [p for p in palabras if len(p) > 3]

        return {
            'titulo_norm': titulo_norm,
            'keywords': list(set(keywords + keywords_extra[:3])),
            'isco_prefix': isco_prefix
        }

    def match_oferta(self, oferta):
        """
        Hace matching de una oferta con razonamiento

        Returns:
            dict con match y justificación
        """
        titulo = oferta.get('titulo', '')
        descripcion = oferta.get('descripcion', '')

        # Analizar título
        analisis = self.analizar_titulo(titulo)

        # Buscar en ESCO
        candidatos = self.matcher.search_esco(
            analisis['keywords'],
            isco_prefix=analisis['isco_prefix']
        )

        if not candidatos:
            # Sin candidatos, ampliar búsqueda
            candidatos = self.matcher.search_esco(analisis['keywords'])

        # Seleccionar mejor candidato con razonamiento
        if candidatos:
            mejor = candidatos[0]

            # Determinar confianza
            if mejor['score'] >= 3:
                confidence = 'alta'
                reasoning = f"Match fuerte: {mejor['score']} keywords coinciden"
            elif mejor['score'] >= 2:
                confidence = 'media'
                reasoning = f"Match parcial: {mejor['score']} keywords coinciden"
            else:
                confidence = 'baja'
                reasoning = f"Match débil: solo {mejor['score']} keyword coincide"

            # Identificar patrón
            pattern = self._identify_pattern(titulo, mejor['label'])

            return {
                'esco_id': mejor['esco_id'],
                'label': mejor['label'],
                'isco_code': mejor['isco_code'],
                'confidence': confidence,
                'reasoning': reasoning,
                'pattern': pattern,
                'candidatos_alternativos': candidatos[1:4]
            }
        else:
            return {
                'esco_id': None,
                'label': None,
                'isco_code': None,
                'confidence': 'sin_match',
                'reasoning': 'No se encontraron candidatos en ESCO',
                'pattern': 'no_match',
                'candidatos_alternativos': []
            }

    def _identify_pattern(self, titulo, esco_label):
        """Identifica patrón de matching"""
        titulo_norm = TextNormalizer.normalize(titulo)
        label_norm = TextNormalizer.normalize(esco_label)

        # Patrones comunes
        if any(w in titulo_norm for w in ['vendedor', 'promotor', 'comercial']):
            return 'ventas_comercial'
        elif any(w in titulo_norm for w in ['operario', 'operador']):
            return 'operario_produccion'
        elif any(w in titulo_norm for w in ['analista', 'especialista']):
            return 'profesional_especializado'
        elif any(w in titulo_norm for w in ['tecnico', 'asistente']):
            return 'tecnico_apoyo'
        elif any(w in titulo_norm for w in ['coordinador', 'responsable', 'jefe']):
            return 'supervision_coordinacion'
        elif any(w in titulo_norm for w in ['chofer', 'conductor']):
            return 'transporte'
        elif any(w in titulo_norm for w in ['administrativo', 'oficina']):
            return 'administrativo_oficina'
        else:
            return 'otro'

    def process_all(self):
        """Procesa todas las ofertas"""
        print("\n" + "=" * 100)
        print("PROCESAMIENTO DE MATCHING MANUAL")
        print("=" * 100)
        print(f"Total ofertas: {len(self.matcher.ofertas)}")

        resultados = []
        patrones_count = {}

        for i, oferta in enumerate(self.matcher.ofertas, 1):
            # Hacer matching Claude
            claude_match = self.match_oferta(oferta)

            # Comparar con fuzzy original
            fuzzy_original = {
                'label': oferta.get('esco_occupation_label', ''),
                'isco_code': oferta.get('esco_codigo_isco', ''),
                'score': oferta.get('esco_match_score', 0),
                'confidence': oferta.get('esco_confianza', '')
            }

            # Guardar resultado
            resultado = {
                'titulo': oferta.get('titulo', ''),
                'descripcion': oferta.get('descripcion', ''),
                'claude_match': claude_match,
                'fuzzy_original': fuzzy_original
            }
            resultados.append(resultado)

            # Contar patrones
            pattern = claude_match.get('pattern', 'otro')
            patrones_count[pattern] = patrones_count.get(pattern, 0) + 1

            # Progreso cada 50
            if i % 50 == 0:
                print(f"  Procesadas: {i}/{len(self.matcher.ofertas)}")

        print(f"\n  Procesadas: {len(resultados)}/{len(self.matcher.ofertas)}")

        # Guardar resultados
        self.matcher.resultados = resultados

        # Análisis de patrones
        self.patrones_identificados = [
            {'pattern': k, 'count': v}
            for k, v in patrones_count.items()
        ]
        self.matcher.patrones = self.patrones_identificados

        # Guardar
        json_path = self.matcher.save_progress()
        csv_path = self.matcher.export_to_csv()

        # Estadísticas
        print("\n" + "=" * 100)
        print("ESTADISTICAS")
        print("=" * 100)

        matched = sum(1 for r in resultados if r['claude_match']['esco_id'])
        print(f"\nMatched: {matched}/{len(resultados)} ({matched/len(resultados)*100:.1f}%)")

        # Confianza
        conf_dist = {}
        for r in resultados:
            conf = r['claude_match']['confidence']
            conf_dist[conf] = conf_dist.get(conf, 0) + 1

        print("\nDistribucion confianza:")
        for conf, count in sorted(conf_dist.items()):
            pct = (count / len(resultados)) * 100
            print(f"  {conf:>15s}: {count:>4} ({pct:>5.1f}%)")

        # Patrones
        print("\nPatrones identificados:")
        for p in sorted(self.patrones_identificados, key=lambda x: x['count'], reverse=True):
            pct = (p['count'] / len(resultados)) * 100
            print(f"  {p['pattern']:>30s}: {p['count']:>4} ({pct:>5.1f}%)")

        # Coincidencia con fuzzy
        coinciden = sum(1 for r in resultados
                       if r['claude_match']['isco_code'] == r['fuzzy_original']['isco_code']
                       and r['claude_match']['isco_code'] is not None)

        print(f"\nCoincidencia ISCO con Fuzzy/LLM: {coinciden}/{matched} ({coinciden/matched*100:.1f}%)")

        print("\n" + "=" * 100)
        print("[COMPLETADO]")
        print("=" * 100)
        print(f"\nArchivos generados:")
        print(f"  JSON: {json_path}")
        print(f"  CSV:  {csv_path}")

        return resultados


def main():
    processor = ClaudeMatchingProcessor()
    processor.process_all()


if __name__ == "__main__":
    main()
