# -*- coding: utf-8 -*-
"""
ESCO/ISCO Matcher - Asigna códigos ISCO a ofertas laborales
===========================================================

Estrategia:
1. Fuzzy matching: titulo → ocupación ESCO
2. Validación: skills overlap
3. Output: código ISCO + score + metadata
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import logging
from datetime import datetime
from tqdm import tqdm

# Fuzzy matching
try:
    from fuzzywuzzy import fuzz
except ImportError:
    print("Installing fuzzywuzzy...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fuzzywuzzy', 'python-Levenshtein'])
    from fuzzywuzzy import fuzz

# Normalización
try:
    import unidecode
except ImportError:
    print("Installing unidecode...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'unidecode'])
    import unidecode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ESCOISCOMatcher:
    """Matcher de ofertas laborales a ESCO/ISCO"""

    def __init__(self, esco_data_path: str):
        """
        Args:
            esco_data_path: Ruta a carpeta con datos ESCO
        """
        self.esco_path = Path(esco_data_path)

        # Cargar datos ESCO
        logger.info("Cargando datos ESCO...")
        self.ocupaciones = self._load_json('esco_ocupaciones_con_isco_completo.json')  # Cambiado para tener 100% ISCO
        self.relaciones = self._load_json('esco_ocupaciones_skills_relaciones.json')
        self.skills_info = self._load_json('esco_skills_info.json')

        logger.info(f"  Ocupaciones ESCO: {len(self.ocupaciones):,}")
        logger.info(f"  Relaciones skills: {len(self.relaciones):,}")
        logger.info(f"  Skills totales: {len(self.skills_info):,}")

        # Crear índice de búsqueda
        logger.info("\nCreando índice de búsqueda...")
        self.indice = self._crear_indice()
        logger.info(f"  Índice creado con {len(self.indice)} entradas")

    def _load_json(self, filename: str) -> dict:
        """Carga archivo JSON"""
        filepath = self.esco_path / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto para matching

        Ejemplos:
        "Analista de Datos" -> "analista de datos"
        "Técnico/a" -> "tecnico"
        """
        # Manejar NaN, None, o vacío
        if pd.isna(texto) or not texto:
            return ""

        # Convertir a string por si es otro tipo
        texto = str(texto).strip()

        if not texto:
            return ""

        # Quitar acentos
        texto = unidecode.unidecode(texto)

        # Minúsculas
        texto = texto.lower()

        # Remover caracteres especiales (mantener espacios)
        texto = re.sub(r'[^\w\s]', ' ', texto)

        # Normalizar espacios
        texto = ' '.join(texto.split())

        return texto

    def _crear_indice(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Crea índice de búsqueda optimizado

        Returns:
            Dict de {palabra_clave: [(occ_id, label), ...]}
        """
        indice = {}

        for occ_id, occ_data in self.ocupaciones.items():
            # Normalizar label principal
            label_norm = self._normalizar_texto(occ_data['label_es'])

            # Agregar al índice por palabras
            palabras = label_norm.split()
            for palabra in palabras:
                if len(palabra) >= 3:  # Palabras de 3+ caracteres
                    if palabra not in indice:
                        indice[palabra] = []
                    indice[palabra].append((occ_id, occ_data['label_es']))

            # También agregar label completo
            if label_norm not in indice:
                indice[label_norm] = []
            indice[label_norm].append((occ_id, occ_data['label_es']))

            # Agregar labels alternativos
            for alt_label in occ_data.get('alt_labels_es', []):
                alt_norm = self._normalizar_texto(alt_label)
                if alt_norm and alt_norm not in indice:
                    indice[alt_norm] = []
                    indice[alt_norm].append((occ_id, occ_data['label_es']))

        return indice

    def _get_candidatos_rapidos(self, titulo: str, top_n: int = 20) -> List[str]:
        """
        Obtiene candidatos rápidos usando el índice

        Returns:
            Lista de occupation_ids candidatos
        """
        titulo_norm = self._normalizar_texto(titulo)
        palabras = titulo_norm.split()

        candidatos_score = {}

        # Buscar por palabras individuales
        for palabra in palabras:
            if palabra in self.indice:
                for occ_id, label in self.indice[palabra]:
                    if occ_id not in candidatos_score:
                        candidatos_score[occ_id] = 0
                    candidatos_score[occ_id] += 1

        # Buscar por frase completa
        if titulo_norm in self.indice:
            for occ_id, label in self.indice[titulo_norm]:
                if occ_id not in candidatos_score:
                    candidatos_score[occ_id] = 0
                candidatos_score[occ_id] += 10  # Bonus por match completo

        # Ordenar por score y retornar top_n
        candidatos_ordenados = sorted(
            candidatos_score.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [occ_id for occ_id, score in candidatos_ordenados[:top_n]]

    def _fuzzy_match_titulo(self, titulo: str) -> Tuple[Optional[str], int, Optional[str]]:
        """
        Fuzzy matching de título a ocupación ESCO

        Returns:
            (occupation_id, score, label_es)
        """
        titulo_norm = self._normalizar_texto(titulo)

        # Obtener candidatos rápidos
        candidatos = self._get_candidatos_rapidos(titulo, top_n=50)

        # Si no hay candidatos del índice, buscar en todos (más lento)
        if not candidatos:
            candidatos = list(self.ocupaciones.keys())

        best_match = None
        best_score = 0
        best_label = None

        for occ_id in candidatos:
            occ_data = self.ocupaciones[occ_id]

            # Comparar con label principal
            label_norm = self._normalizar_texto(occ_data['label_es'])
            score = fuzz.token_sort_ratio(titulo_norm, label_norm)

            if score > best_score:
                best_score = score
                best_match = occ_id
                best_label = occ_data['label_es']

            # Comparar con labels alternativos
            for alt_label in occ_data.get('alt_labels_es', []):
                alt_norm = self._normalizar_texto(alt_label)
                alt_score = fuzz.token_sort_ratio(titulo_norm, alt_norm)

                if alt_score > best_score:
                    best_score = alt_score
                    best_match = occ_id
                    best_label = occ_data['label_es']

        return best_match, best_score, best_label

    def _calcular_skill_overlap(
        self,
        oferta_skills: List[str],
        esco_occupation_id: str
    ) -> Dict:
        """
        Calcula overlap entre skills de oferta y ESCO

        Returns:
            {
                'overlap_score': 0-100,
                'skills_matched': [...],
                'skills_esco_total': int,
                'skills_oferta_total': int
            }
        """
        # Verificar si hay relaciones de skills para esta ocupación
        if esco_occupation_id not in self.relaciones:
            return {
                'overlap_score': 0,
                'skills_matched': [],
                'skills_esco_total': 0,
                'skills_oferta_total': len(oferta_skills)
            }

        # Obtener skills esenciales de ESCO
        esco_skill_ids = self.relaciones[esco_occupation_id].get('skills_esenciales', [])

        if not esco_skill_ids:
            return {
                'overlap_score': 0,
                'skills_matched': [],
                'skills_esco_total': 0,
                'skills_oferta_total': len(oferta_skills)
            }

        # Convertir IDs a labels en español
        esco_skills_labels = []
        for sid in esco_skill_ids:
            if sid in self.skills_info:
                label = self.skills_info[sid].get('label_es', '')
                if label:
                    esco_skills_labels.append(self._normalizar_texto(label))

        # Normalizar skills de oferta
        oferta_skills_norm = [self._normalizar_texto(s) for s in oferta_skills if s]

        # Calcular matches (fuzzy con umbral 80)
        matches = []
        for oferta_skill in oferta_skills_norm:
            best_match = None
            best_score = 0

            for esco_skill in esco_skills_labels:
                score = fuzz.token_sort_ratio(oferta_skill, esco_skill)
                if score >= 80 and score > best_score:
                    best_score = score
                    best_match = (oferta_skill, esco_skill)

            if best_match:
                matches.append(best_match)

        # Calcular score de overlap
        if esco_skills_labels:
            overlap_score = (len(matches) / len(esco_skills_labels)) * 100
        else:
            overlap_score = 0

        return {
            'overlap_score': round(overlap_score, 1),
            'skills_matched': matches,
            'skills_esco_total': len(esco_skills_labels),
            'skills_oferta_total': len(oferta_skills_norm)
        }

    def match_oferta(self, row: pd.Series) -> Dict:
        """
        Hace matching de una oferta a ESCO/ISCO

        Args:
            row: Fila del DataFrame con columnas:
                - titulo
                - soft_skills
                - skills_tecnicas
                - descripcion (opcional)

        Returns:
            Dict con:
                - esco_occupation_id
                - esco_occupation_label
                - esco_codigo_isco
                - esco_match_score (fuzzy)
                - esco_skills_overlap
                - esco_match_method
                - esco_confianza (final)
        """
        titulo = row.get('titulo', '')

        # FASE 1: Fuzzy matching de título
        occ_id, fuzzy_score, occ_label = self._fuzzy_match_titulo(titulo)

        if not occ_id:
            return {
                'esco_occupation_id': None,
                'esco_occupation_label': None,
                'esco_codigo_isco': None,
                'esco_match_score': 0,
                'esco_skills_overlap': 0,
                'esco_match_method': 'no_match',
                'esco_confianza': 'baja'
            }

        # FASE 2: Validación por skills
        oferta_skills = []

        # Agregar soft skills
        soft_skills_str = row.get('soft_skills', '')
        if pd.notna(soft_skills_str) and soft_skills_str:
            oferta_skills.extend([s.strip() for s in str(soft_skills_str).split(',') if s.strip()])

        # Agregar skills técnicas
        tech_skills_str = row.get('skills_tecnicas', '')
        if pd.notna(tech_skills_str) and tech_skills_str:
            oferta_skills.extend([s.strip() for s in str(tech_skills_str).split(',') if s.strip()])

        # Calcular overlap
        if oferta_skills:
            overlap_result = self._calcular_skill_overlap(oferta_skills, occ_id)
            overlap_score = overlap_result['overlap_score']
        else:
            overlap_score = 0

        # Determinar confianza final
        if fuzzy_score >= 90 and overlap_score >= 60:
            confianza = 'alta'
        elif fuzzy_score >= 70 and overlap_score >= 30:
            confianza = 'media'
        elif fuzzy_score >= 70:
            confianza = 'media'
        else:
            confianza = 'baja'

        # Obtener código ISCO
        codigo_isco = self.ocupaciones[occ_id].get('codigo_isco')

        return {
            'esco_occupation_id': occ_id,
            'esco_occupation_label': occ_label,
            'esco_codigo_isco': codigo_isco,
            'esco_match_score': fuzzy_score,
            'esco_skills_overlap': overlap_score,
            'esco_match_method': 'fuzzy',
            'esco_confianza': confianza
        }

    def process_dataframe(
        self,
        df: pd.DataFrame,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Procesa DataFrame completo

        Args:
            df: DataFrame con ofertas
            limit: Límite de ofertas (para testing)

        Returns:
            DataFrame con columnas ESCO/ISCO agregadas
        """
        logger.info("\n" + "=" * 70)
        logger.info("MATCHING ESCO/ISCO")
        logger.info("=" * 70)

        if limit:
            df = df.head(limit)
            logger.info(f"Procesando {limit} ofertas (modo test)")

        logger.info(f"Total ofertas: {len(df):,}\n")

        results = []

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Matching ESCO/ISCO"):
            match_result = self.match_oferta(row)
            results.append(match_result)

        # Agregar resultados al DataFrame
        df_esco = pd.DataFrame(results)
        df_enriched = pd.concat([df, df_esco], axis=1)

        # Estadísticas
        logger.info("\n" + "=" * 70)
        logger.info("RESULTADOS")
        logger.info("=" * 70)

        total = len(df_enriched)
        matched = df_enriched['esco_occupation_id'].notna().sum()

        logger.info(f"Ofertas procesadas: {total:,}")
        logger.info(f"Ofertas matcheadas: {matched:,} ({100*matched/total:.1f}%)")
        logger.info(f"Sin match: {total - matched:,} ({100*(total-matched)/total:.1f}%)")

        # Confianza
        logger.info("\nDISTRIBUCIÓN DE CONFIANZA:")
        confianza_counts = df_enriched['esco_confianza'].value_counts()
        for nivel, count in confianza_counts.items():
            pct = 100 * count / total
            logger.info(f"  {nivel}: {count:,} ({pct:.1f}%)")

        # Scores promedio
        logger.info("\nSCORES PROMEDIO:")
        avg_fuzzy = df_enriched['esco_match_score'].mean()
        avg_overlap = df_enriched['esco_skills_overlap'].mean()
        logger.info(f"  Match fuzzy: {avg_fuzzy:.1f}")
        logger.info(f"  Skills overlap: {avg_overlap:.1f}")

        # Top 10 ocupaciones
        logger.info("\nTOP 10 OCUPACIONES ESCO:")
        top_ocupaciones = df_enriched['esco_occupation_label'].value_counts().head(10)
        for ocupacion, count in top_ocupaciones.items():
            pct = 100 * count / total
            logger.info(f"  {ocupacion}: {count:,} ({pct:.1f}%)")

        # Top 10 códigos ISCO
        logger.info("\nTOP 10 CÓDIGOS ISCO:")
        top_isco = df_enriched['esco_codigo_isco'].value_counts().head(10)
        for codigo, count in top_isco.items():
            pct = 100 * count / total
            logger.info(f"  {codigo}: {count:,} ({pct:.1f}%)")

        logger.info("=" * 70)

        return df_enriched


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Matcher ESCO/ISCO para ofertas laborales')
    parser.add_argument(
        '--input',
        type=str,
        default=r'D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\all_sources_fixed_20251027_170535.csv',
        help='CSV de entrada con ofertas'
    )
    parser.add_argument(
        '--esco-data',
        type=str,
        default=r'D:\Trabajos en PY\EPH-ESCO\07_esco_data',
        help='Carpeta con datos ESCO'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='CSV de salida (opcional)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Límite de ofertas para testing'
    )

    args = parser.parse_args()

    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'../data/processed/ofertas_esco_isco_{timestamp}.csv'

    try:
        # Cargar ofertas
        logger.info("Cargando ofertas laborales...")
        df = pd.read_csv(args.input, low_memory=False)
        logger.info(f"  Cargadas {len(df):,} ofertas\n")

        # Crear matcher
        matcher = ESCOISCOMatcher(esco_data_path=args.esco_data)

        # Procesar
        df_enriched = matcher.process_dataframe(df, limit=args.limit)

        # Guardar
        logger.info(f"\nGuardando: {args.output}")
        df_enriched.to_csv(args.output, index=False)

        file_size = Path(args.output).stat().st_size / 1024 / 1024
        logger.info(f"Tamaño: {file_size:.1f} MB")

        logger.info("\n¡Matching ESCO/ISCO completado!")

    except Exception as e:
        logger.error(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
