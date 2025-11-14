# -*- coding: utf-8 -*-
"""
Integración ESCO Mejorada con:
- Traducción automática de títulos en inglés
- Limpieza avanzada de títulos
- Threshold adaptativo (0.3 para segundos intentos)
- Análisis geográfico y por empresa
"""

import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import re
from difflib import SequenceMatcher
import unicodedata
import sys

# Importar el integrador base
sys.path.append(str(Path(__file__).parent))
from integracion_esco_semantica import IntegradorESCOSemantico, NormalizadorTextoES

# Paths
ZONAJOBS_DATA_DIR = Path(r"D:\OEDE\Webscrapping\data\raw")
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\data\processed")


class TraductorSimpleEN_ES:
    """Traductor simple de términos laborales comunes EN->ES"""

    DICCIONARIO = {
        # Roles
        'account executive': 'ejecutivo de cuentas',
        'business development': 'desarrollo de negocios',
        'sales representative': 'representante de ventas',
        'product architect': 'arquitecto de producto',
        'product manager': 'gerente de producto',
        'project manager': 'gerente de proyecto',
        'data analyst': 'analista de datos',
        'software engineer': 'ingeniero de software',
        'full stack developer': 'desarrollador full stack',
        'frontend developer': 'desarrollador frontend',
        'backend developer': 'desarrollador backend',
        'devops engineer': 'ingeniero devops',
        'qa engineer': 'ingeniero de calidad',
        'ux designer': 'diseñador de experiencia',
        'ui designer': 'diseñador de interfaz',
        'marketing manager': 'gerente de marketing',
        'human resources': 'recursos humanos',
        'customer success': 'éxito del cliente',
        'customer support': 'soporte al cliente',
        'technical support': 'soporte técnico',
        'sales manager': 'gerente de ventas',
        'operations manager': 'gerente de operaciones',
        'financial analyst': 'analista financiero',
        'business analyst': 'analista de negocios',
        'scrum master': 'maestro scrum',
        'team leader': 'líder de equipo',
        'tech lead': 'líder técnico',
        'hiring': 'contratación',
        'recruiter': 'reclutador',
        'talent': 'talento',
        'farmer': 'cultivador',  # En contexto laboral, mantenimiento clientes

        # Términos específicos
        'senior': 'senior',
        'semi senior': 'semi senior',
        'junior': 'junior',
        'trainee': 'practicante',
        'intern': 'pasante',
        'coordinator': 'coordinador',
        'assistant': 'asistente',
        'specialist': 'especialista',
        'consultant': 'consultor',
        'advisor': 'asesor',
        'representative': 'representante',
        'agent': 'agente',
        'officer': 'oficial',
        'analyst': 'analista',
        'engineer': 'ingeniero',
        'developer': 'desarrollador',
        'designer': 'diseñador',
        'architect': 'arquitecto',
        'manager': 'gerente',
        'director': 'director',
        'supervisor': 'supervisor',
        'leader': 'líder',
        'head': 'jefe',
        'chief': 'jefe',
        'executive': 'ejecutivo',

        # Modalidades
        'remote': 'remoto',
        'hybrid': 'híbrido',
        'on-site': 'presencial',
        'full-time': 'tiempo completo',
        'part-time': 'medio tiempo',

        # Sectores
        'logistics': 'logística',
        'services': 'servicios',
        'infrastructure': 'infraestructura',
        'technology': 'tecnología',
        'finance': 'finanzas',
        'healthcare': 'salud',
        'education': 'educación',
        'retail': 'ventas minoristas',
        'manufacturing': 'manufactura',
        'construction': 'construcción',
    }

    @staticmethod
    def traducir_titulo(titulo):
        """Traduce título de inglés a español usando diccionario"""
        if pd.isna(titulo):
            return ""

        titulo_lower = titulo.lower()
        titulo_traducido = titulo_lower

        # Traducir cada término del diccionario
        for en_term, es_term in TraductorSimpleEN_ES.DICCIONARIO.items():
            # Buscar el término en inglés (con límites de palabra)
            pattern = r'\b' + re.escape(en_term) + r'\b'
            titulo_traducido = re.sub(pattern, es_term, titulo_traducido, flags=re.IGNORECASE)

        return titulo_traducido


class LimpiadorTitulosAvanzado:
    """Limpiador avanzado de títulos de ofertas"""

    # Patrones a remover
    PATRONES_REMOVER = [
        r'\([^)]*\)',  # Texto entre paréntesis
        r'\[[^\]]*\]',  # Texto entre corchetes
        r'–.*$',  # Todo después de guión largo
        r'-\s*zona\s+\w+',  # "- Zona X"
        r'-\s*importante\s+\w+',  # "- Importante X"
        r'para\s+\w+\s*$',  # "para X" al final
        r'en\s+\w+\s*$',  # "en X" al final (cuando es lugar)
        r'\s*-\s*hiring\s+room',  # "- Hiring Room"
        r'oportunidad\s+laboral\s+(en|para)',  # "Oportunidad laboral en/para"
        r'estudio\s+\w+\s+de\s+\w+',  # "Estudio X de Y"
    ]

    # Palabras genéricas a remover
    PALABRAS_GENERICAS = {
        'oportunidad', 'laboral', 'importante', 'confidencial',
        'excluyente', 'preferentemente', 'zona', 'partido',
        'urgent', 'urgente', 'inmediato', 'immediate',
    }

    @staticmethod
    def limpiar_titulo(titulo):
        """Limpia título removiendo contexto extra"""
        if pd.isna(titulo):
            return ""

        titulo_limpio = titulo

        # Aplicar patrones de remoción
        for patron in LimpiadorTitulosAvanzado.PATRONES_REMOVER:
            titulo_limpio = re.sub(patron, '', titulo_limpio, flags=re.IGNORECASE)

        # Remover palabras genéricas
        palabras = titulo_limpio.split()
        palabras_filtradas = [
            p for p in palabras
            if p.lower() not in LimpiadorTitulosAvanzado.PALABRAS_GENERICAS
        ]
        titulo_limpio = ' '.join(palabras_filtradas)

        # Limpiar espacios múltiples
        titulo_limpio = re.sub(r'\s+', ' ', titulo_limpio).strip()

        return titulo_limpio


class IntegradorESCOMejorado(IntegradorESCOSemantico):
    """Integrador mejorado con traducción, limpieza y threshold adaptativo"""

    def clasificar_ofertas_mejorado(self, threshold_inicial=0.4, threshold_segundo_intento=0.3):
        """
        Clasificación mejorada en dos pasadas:
        1. Primera pasada: threshold normal con títulos originales
        2. Segunda pasada: threshold bajo con títulos traducidos y limpios
        """
        print("\n[PASO 4] CLASIFICACIÓN MEJORADA CON MÚLTIPLES ESTRATEGIAS")
        print("=" * 80)

        if self.zonajobs_df is None or len(self.zonajobs_df) == 0:
            print("[ERROR] No hay datos de ZonaJobs")
            return False

        if not self.esco_ocupaciones:
            print("[ERROR] No hay datos de ESCO")
            return False

        total_ofertas = len(self.zonajobs_df)
        print(f"\n[CONFIG] Estrategia multi-nivel:")
        print(f"  1. Threshold inicial: {threshold_inicial} (título original)")
        print(f"  2. Traducción EN->ES para títulos en inglés")
        print(f"  3. Limpieza de contexto geográfico y palabras extra")
        print(f"  4. Threshold permisivo: {threshold_segundo_intento} (segundo intento)")

        resultados = []
        stats = {
            'pasada_1': 0,
            'pasada_2_traduccion': 0,
            'pasada_3_limpieza': 0,
            'pasada_4_threshold_bajo': 0,
            'sin_clasificar': 0
        }

        for idx, oferta in self.zonajobs_df.iterrows():
            titulo_original = oferta['titulo']
            match = None
            estrategia_usada = None

            # PASADA 1: Título original con threshold normal
            matches = self.encontrar_mejor_match(titulo_original, threshold=threshold_inicial, top_n=3)
            if matches:
                match = matches[0]
                estrategia_usada = 'original'
                stats['pasada_1'] += 1
            else:
                # PASADA 2: Traducir si tiene términos en inglés
                titulo_traducido = TraductorSimpleEN_ES.traducir_titulo(titulo_original)
                if titulo_traducido != titulo_original.lower():
                    matches = self.encontrar_mejor_match(titulo_traducido, threshold=threshold_inicial, top_n=3)
                    if matches:
                        match = matches[0]
                        estrategia_usada = 'traduccion'
                        stats['pasada_2_traduccion'] += 1

            if not match:
                # PASADA 3: Limpiar título
                titulo_limpio = LimpiadorTitulosAvanzado.limpiar_titulo(titulo_original)
                if titulo_limpio and titulo_limpio != titulo_original:
                    matches = self.encontrar_mejor_match(titulo_limpio, threshold=threshold_inicial, top_n=3)
                    if matches:
                        match = matches[0]
                        estrategia_usada = 'limpieza'
                        stats['pasada_3_limpieza'] += 1

            if not match:
                # PASADA 4: Threshold más bajo con título limpio y traducido
                titulo_procesado = LimpiadorTitulosAvanzado.limpiar_titulo(
                    TraductorSimpleEN_ES.traducir_titulo(titulo_original)
                )
                if titulo_procesado:
                    matches = self.encontrar_mejor_match(
                        titulo_procesado,
                        threshold=threshold_segundo_intento,
                        top_n=3
                    )
                    if matches:
                        match = matches[0]
                        estrategia_usada = 'threshold_bajo'
                        stats['pasada_4_threshold_bajo'] += 1

            # Construir resultado
            if match:
                skills = self.obtener_skills_para_ocupacion(match['esco_id'])

                resultado = {
                    'id_oferta': oferta.get('id_oferta'),
                    'titulo_original': titulo_original,
                    'empresa': oferta.get('empresa'),
                    'localizacion': oferta.get('localizacion'),
                    'modalidad_trabajo': oferta.get('modalidad_trabajo'),
                    'tipo_trabajo': oferta.get('tipo_trabajo'),
                    'fecha_publicacion': oferta.get('fecha_publicacion'),
                    'url_oferta': oferta.get('url_oferta'),

                    'esco_match_1_id': match['esco_id'],
                    'esco_match_1_label': match['esco_label_es'],
                    'esco_match_1_isco_4d': match['codigo_isco_4d'],
                    'esco_match_1_isco_2d': match['codigo_isco_2d'],
                    'esco_match_1_similitud': match['similitud'],

                    'skills_esenciales_top5': '; '.join([s['label'] for s in skills['esenciales'][:5]]),
                    'skills_esenciales_count': len(skills['esenciales']),
                    'skills_opcionales_top5': '; '.join([s['label'] for s in skills['opcionales'][:5]]),
                    'skills_opcionales_count': len(skills['opcionales']),

                    'esco_match_2_label': matches[1]['esco_label_es'] if len(matches) > 1 else None,
                    'esco_match_2_similitud': matches[1]['similitud'] if len(matches) > 1 else None,
                    'esco_match_3_label': matches[2]['esco_label_es'] if len(matches) > 2 else None,
                    'esco_match_3_similitud': matches[2]['similitud'] if len(matches) > 2 else None,

                    'estrategia_matching': estrategia_usada,
                    'fecha_clasificacion': datetime.now().isoformat(),
                    'clasificada': True
                }
            else:
                # Sin match después de todas las estrategias
                resultado = {
                    'id_oferta': oferta.get('id_oferta'),
                    'titulo_original': titulo_original,
                    'empresa': oferta.get('empresa'),
                    'localizacion': oferta.get('localizacion'),
                    'modalidad_trabajo': oferta.get('modalidad_trabajo'),
                    'tipo_trabajo': oferta.get('tipo_trabajo'),
                    'fecha_publicacion': oferta.get('fecha_publicacion'),
                    'url_oferta': oferta.get('url_oferta'),
                    'esco_match_1_id': None,
                    'esco_match_1_label': None,
                    'esco_match_1_isco_4d': None,
                    'esco_match_1_isco_2d': None,
                    'esco_match_1_similitud': 0.0,
                    'skills_esenciales_top5': None,
                    'skills_esenciales_count': 0,
                    'skills_opcionales_top5': None,
                    'skills_opcionales_count': 0,
                    'esco_match_2_label': None,
                    'esco_match_2_similitud': None,
                    'esco_match_3_label': None,
                    'esco_match_3_similitud': None,
                    'estrategia_matching': None,
                    'fecha_clasificacion': datetime.now().isoformat(),
                    'clasificada': False
                }
                stats['sin_clasificar'] += 1

            resultados.append(resultado)

            if (idx + 1) % 10 == 0:
                clasificadas = sum(1 for r in resultados if r['clasificada'])
                print(f"  Progreso: {idx + 1}/{total_ofertas} ({clasificadas} clasificadas)")

        self.resultados = pd.DataFrame(resultados)

        # Mostrar estadísticas de estrategias
        print(f"\n[OK] CLASIFICACIÓN COMPLETADA")
        print(f"=" * 80)
        print(f"\n  📊 RESULTADOS POR ESTRATEGIA:")
        print(f"  1. Título original (threshold {threshold_inicial}): {stats['pasada_1']}")
        print(f"  2. Con traducción EN->ES: {stats['pasada_2_traduccion']}")
        print(f"  3. Con limpieza de título: {stats['pasada_3_limpieza']}")
        print(f"  4. Threshold permisivo ({threshold_segundo_intento}): {stats['pasada_4_threshold_bajo']}")
        print(f"  ❌ Sin clasificar: {stats['sin_clasificar']}")

        total_clasificadas = total_ofertas - stats['sin_clasificar']
        print(f"\n  ✅ TOTAL CLASIFICADAS: {total_clasificadas}/{total_ofertas} ({total_clasificadas/total_ofertas*100:.1f}%)")

        return True

    def ejecutar_pipeline_mejorado(self):
        """Pipeline mejorado completo"""
        print("\n" + "🚀 " * 20)
        print("PIPELINE MEJORADO - ZONAJOBS + ESCO")
        print("Con traducción, limpieza y threshold adaptativo")
        print("🚀 " * 20)

        if not self.cargar_zonajobs():
            return False

        if not self.cargar_esco_consolidado():
            return False

        if not self.cargar_esco_skills():
            return False

        if not self.clasificar_ofertas_mejorado():
            return False

        if not self.guardar_resultados():
            return False

        print("\n" + "✅ " * 20)
        print("INTEGRACIÓN MEJORADA COMPLETADA")
        print("✅ " * 20)

        return True


def main():
    """Función principal"""
    integrador = IntegradorESCOMejorado()
    integrador.ejecutar_pipeline_mejorado()


if __name__ == "__main__":
    main()
