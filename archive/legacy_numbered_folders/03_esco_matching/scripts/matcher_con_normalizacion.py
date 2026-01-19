# -*- coding: utf-8 -*-
"""
Matcher ESCO con Normalización Argentina
==========================================

Matcher mejorado que usa diccionario de normalización ARG → ESCO
antes de hacer fuzzy matching.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import unicodedata
import re
from difflib import SequenceMatcher
from tqdm import tqdm

# Rutas
OFERTAS_PATH = r"D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\ofertas_esco_isco_llm_20251027_191809.csv"
ESCO_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json"
DICT_PATH = r"D:\OEDE\Webscrapping\03_esco_matching\data\diccionario_normalizacion_arg_esco_expandido.json"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\03_esco_matching\data")


class TextNormalizer:
    """Normalizador de texto"""

    @staticmethod
    def normalize(text):
        if pd.isna(text) or not text:
            return ""
        text = text.lower().strip()
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


class MatcherConNormalizacion:
    """Matcher con diccionario de normalización"""

    def __init__(self):
        self.esco_data = {}
        self.esco_list = []
        self.dict_normalizacion = {}

        self._load_data()

    def _load_data(self):
        """Carga ESCO y diccionario"""
        print("=" * 100)
        print("MATCHER CON NORMALIZACION ARGENTINA")
        print("=" * 100)

        # Cargar ESCO
        print(f"\n[1/3] Cargando ESCO...")
        with open(ESCO_PATH, 'r', encoding='utf-8') as f:
            self.esco_data = json.load(f)

        self.esco_list = [
            {
                'esco_id': k,
                'label_es': v.get('label_es', '') or '',
                'label_en': v.get('label_en', '') or '',
                'isco_code': v.get('codigo_isco_4d', v.get('codigo_isco', '')),
                'alt_labels': v.get('alt_labels_es', []) or [],
                'uri': v.get('uri', '')
            }
            for k, v in self.esco_data.items()
            if v is not None
        ]

        print(f"  OK: {len(self.esco_list)} ocupaciones")

        # Cargar diccionario
        print(f"\n[2/3] Cargando diccionario de normalizacion...")
        with open(DICT_PATH, 'r', encoding='utf-8') as f:
            self.dict_normalizacion = json.load(f)

        print(f"  OK: {len(self.dict_normalizacion)} terminos")

        print(f"\n[3/3] Listo para matching")

    def normalizar_titulo_argentino(self, titulo):
        """
        Normaliza título argentino usando diccionario

        Returns:
            dict con título normalizado y metadata
        """
        titulo_norm = TextNormalizer.normalize(titulo)

        # Buscar en diccionario (exacto y parcial)
        terminos_encontrados = []
        isco_sugerido = None

        # Buscar coincidencias en diccionario
        for term_arg, config in self.dict_normalizacion.items():
            term_arg_norm = TextNormalizer.normalize(term_arg)

            # Match exacto
            if term_arg_norm in titulo_norm:
                terminos_encontrados.append({
                    'termino_arg': term_arg,
                    'esco_terms': config.get('esco_terms', []),
                    'isco_target': config.get('isco_target'),
                    'notes': config.get('notes', '')
                })

                if not isco_sugerido and config.get('isco_target'):
                    isco_sugerido = config.get('isco_target')

        # Si encontró términos, construir búsqueda normalizada
        if terminos_encontrados:
            # Recopilar todos los términos ESCO sugeridos
            esco_terms_combinados = []
            for t in terminos_encontrados:
                esco_terms_combinados.extend(t['esco_terms'])

            return {
                'titulo_original': titulo,
                'titulo_norm': titulo_norm,
                'terminos_encontrados': terminos_encontrados,
                'esco_terms_para_busqueda': list(set(esco_terms_combinados)),
                'isco_sugerido': isco_sugerido,
                'normalizado': True
            }
        else:
            # No encontró en diccionario, extraer keywords del título
            palabras = titulo_norm.split()
            # Filtrar stopwords y palabras cortas
            stopwords = {'de', 'y', 'para', 'con', 'en', 'el', 'la', 'los', 'las', 'un', 'una', 'del', 'al', 'por', 'a'}
            keywords = [p for p in palabras if len(p) > 3 and p not in stopwords]

            return {
                'titulo_original': titulo,
                'titulo_norm': titulo_norm,
                'terminos_encontrados': [],
                'esco_terms_para_busqueda': keywords,
                'isco_sugerido': None,
                'normalizado': False
            }

    def fuzzy_match(self, titulo_info, threshold=0.2):
        """
        Matching fuzzy con normalización

        Args:
            titulo_info: dict con info de normalización
            threshold: umbral mínimo

        Returns:
            dict con match o None
        """
        esco_terms = titulo_info['esco_terms_para_busqueda']
        isco_filtro = titulo_info['isco_sugerido']

        best_match = None
        best_score = 0.0

        for ocu in self.esco_list:
            # Filtrar por ISCO si aplica (más flexible)
            if isco_filtro:
                isco_ocu = str(ocu['isco_code'])
                isco_filtro_str = str(isco_filtro)

                # Si ISCO target es nivel (1 dígito), filtrar por nivel
                # Si es código específico, filtrar por inicio
                if len(isco_filtro_str) <= 2:
                    # Nivel amplio
                    if not isco_ocu.startswith(isco_filtro_str[0]):
                        continue
                else:
                    # Código específico
                    if not isco_ocu.startswith(isco_filtro_str):
                        continue

            # Preparar texto ESCO
            label = ocu['label_es'] or ocu['label_en']
            label_norm = TextNormalizer.normalize(label)

            # Incluir alt_labels
            alt_labels_text = ' '.join([TextNormalizer.normalize(a) for a in ocu['alt_labels'][:3]])
            texto_esco = f"{label_norm} {alt_labels_text}"

            # Calcular score por keywords (más importante)
            keywords_busqueda = set([TextNormalizer.normalize(k) for k in esco_terms if k])
            keywords_esco = set(texto_esco.split())

            # Score principal: Jaccard de keywords
            if keywords_busqueda and keywords_esco:
                keywords_match = len(keywords_busqueda & keywords_esco)
                jaccard = keywords_match / len(keywords_busqueda | keywords_esco)

                # Bonus si matchean muchos keywords
                if keywords_match >= 2:
                    score = jaccard * 1.2  # Boost
                else:
                    score = jaccard
            else:
                score = 0.0

            # Bonus adicional por substring match
            for kw in keywords_busqueda:
                if kw in label_norm:
                    score += 0.1

            if score > best_score:
                best_score = score
                best_match = ocu

        if best_score >= threshold and best_match:
            # Determinar confianza
            if best_score >= 0.7:
                confidence = 'alta'
            elif best_score >= 0.4:
                confidence = 'media'
            else:
                confidence = 'baja'

            return {
                'esco_id': best_match['esco_id'],
                'esco_label': best_match['label_es'],
                'isco_code': best_match['isco_code'],
                'score': round(min(best_score, 1.0), 4),  # Cap at 1.0
                'confidence': confidence,
                'method': 'fuzzy_normalizado' if titulo_info['normalizado'] else 'fuzzy_directo',
                'terminos_usados': titulo_info['terminos_encontrados']
            }

        return None

    def process_ofertas(self, df):
        """Procesa todas las ofertas"""
        print("\n" + "=" * 100)
        print("PROCESAMIENTO CON NORMALIZACION")
        print("=" * 100)
        print(f"Total ofertas: {len(df)}")

        resultados = []
        stats = {
            'con_normalizacion': 0,
            'sin_normalizacion': 0,
            'matched': 0,
            'sin_match': 0,
            'por_confianza': {'alta': 0, 'media': 0, 'baja': 0}
        }

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Procesando"):
            titulo = row.get('titulo', '')

            # Normalizar
            titulo_info = self.normalizar_titulo_argentino(titulo)

            if titulo_info['normalizado']:
                stats['con_normalizacion'] += 1
            else:
                stats['sin_normalizacion'] += 1

            # Matching
            match = self.fuzzy_match(titulo_info, threshold=0.5)

            if match:
                stats['matched'] += 1
                stats['por_confianza'][match['confidence']] += 1

                resultado = {
                    'titulo': titulo,
                    'norm_esco_id': match['esco_id'],
                    'norm_esco_label': match['esco_label'],
                    'norm_isco_code': match['isco_code'],
                    'norm_score': match['score'],
                    'norm_confidence': match['confidence'],
                    'norm_method': match['method'],
                    'norm_usó_diccionario': titulo_info['normalizado'],
                    'norm_terminos_arg': [t['termino_arg'] for t in titulo_info['terminos_encontrados']],
                    # Comparación con fuzzy original
                    'fuzzy_esco_label': row.get('esco_occupation_label', ''),
                    'fuzzy_isco_code': row.get('esco_codigo_isco', ''),
                    'fuzzy_score': row.get('esco_match_score', 0),
                    'fuzzy_confidence': row.get('esco_confianza', '')
                }
            else:
                stats['sin_match'] += 1
                resultado = {
                    'titulo': titulo,
                    'norm_esco_id': None,
                    'norm_esco_label': None,
                    'norm_isco_code': None,
                    'norm_score': 0.0,
                    'norm_confidence': 'sin_match',
                    'norm_method': 'no_match',
                    'norm_usó_diccionario': titulo_info['normalizado'],
                    'norm_terminos_arg': [t['termino_arg'] for t in titulo_info['terminos_encontrados']],
                    'fuzzy_esco_label': row.get('esco_occupation_label', ''),
                    'fuzzy_isco_code': row.get('esco_codigo_isco', ''),
                    'fuzzy_score': row.get('esco_match_score', 0),
                    'fuzzy_confidence': row.get('esco_confianza', '')
                }

            resultados.append(resultado)

        # Estadísticas
        print("\n" + "=" * 100)
        print("RESULTADOS")
        print("=" * 100)

        print(f"\nNormalizacion:")
        print(f"  Con diccionario:    {stats['con_normalizacion']:>4} ({stats['con_normalizacion']/len(df)*100:>5.1f}%)")
        print(f"  Sin diccionario:    {stats['sin_normalizacion']:>4} ({stats['sin_normalizacion']/len(df)*100:>5.1f}%)")

        print(f"\nMatching:")
        print(f"  Matched:            {stats['matched']:>4} ({stats['matched']/len(df)*100:>5.1f}%)")
        print(f"  Sin match:          {stats['sin_match']:>4} ({stats['sin_match']/len(df)*100:>5.1f}%)")

        print(f"\nConfianza:")
        for conf, count in stats['por_confianza'].items():
            pct = (count / len(df)) * 100
            print(f"  {conf:>10}: {count:>4} ({pct:>5.1f}%)")

        # Coincidencia con fuzzy original
        df_results = pd.DataFrame(resultados)
        coinciden_isco = (df_results['norm_isco_code'] == df_results['fuzzy_isco_code']).sum()
        pct_coincide = (coinciden_isco / len(df)) * 100

        print(f"\nCoincidencia ISCO con Fuzzy/LLM original:")
        print(f"  Coinciden:          {coinciden_isco:>4} ({pct_coincide:>5.1f}%)")

        # Guardar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"matching_con_normalizacion_{timestamp}.csv"

        df_results.to_csv(output_path, index=False, encoding='utf-8')

        print(f"\n[GUARDADO] {output_path}")
        print("=" * 100)

        return df_results


def main():
    """Función principal"""
    matcher = MatcherConNormalizacion()

    # Cargar ofertas
    print(f"\nCargando ofertas: {Path(OFERTAS_PATH).name}")
    df = pd.read_csv(OFERTAS_PATH, encoding='utf-8', low_memory=False)
    print(f"  OK: {len(df)} ofertas")

    # Procesar
    resultados = matcher.process_ofertas(df)

    print("\n[COMPLETADO]")


if __name__ == "__main__":
    main()
