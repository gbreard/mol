#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Fallback para Matching ESCO/ISCO
Re-clasifica ofertas con baja confianza usando Ollama llama3
"""

import pandas as pd
import json
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESCOLLMFallback:
    """LLM fallback para mejorar matching ESCO/ISCO"""

    def __init__(self,
                 matched_csv: str,
                 esco_data_dir: str = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data",
                 threshold: float = 70.0,
                 ollama_url: str = "http://localhost:11434/api/generate",
                 model: str = "llama3"):
        """
        Inicializa el fallback LLM

        Args:
            matched_csv: Ruta al CSV con matching actual
            esco_data_dir: Directorio con datos ESCO
            threshold: Threshold de score para considerar baja confianza
            ollama_url: URL de Ollama API
            model: Modelo a usar
        """
        self.matched_csv = matched_csv
        self.esco_data_dir = Path(esco_data_dir)
        self.threshold = threshold
        self.ollama_url = ollama_url
        self.model = model

        # Cargar datos
        logger.info("Cargando datos...")
        self.df = pd.read_csv(matched_csv, low_memory=False)
        logger.info(f"  Cargadas {len(self.df):,} ofertas")

        # Cargar datos ESCO
        self.ocupaciones = self._load_json('esco_ocupaciones_con_isco_completo.json')
        logger.info(f"  Ocupaciones ESCO: {len(self.ocupaciones):,}")

        # Crear índice de ocupaciones por ID
        self.ocupaciones_by_label = {}
        for occ_id, occ_data in self.ocupaciones.items():
            label_es = occ_data.get('label_es')
            if label_es:
                label = label_es.lower()
                self.ocupaciones_by_label[label] = occ_id

    def _load_json(self, filename: str) -> dict:
        """Carga archivo JSON"""
        filepath = self.esco_data_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Llama a Ollama API

        Args:
            prompt: Prompt para el LLM

        Returns:
            Respuesta del LLM o None si falla
        """
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Baja temperatura para respuestas consistentes
                        "top_p": 0.9
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Error de Ollama: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error llamando a Ollama: {e}")
            return None

    def _get_top_candidates(self, row: pd.Series, top_n: int = 15) -> List[Dict]:
        """
        Obtiene top candidatos ESCO para una oferta usando fuzzy matching

        Args:
            row: Fila del DataFrame
            top_n: Número de candidatos a devolver

        Returns:
            Lista de candidatos con label_es, codigo_isco, score
        """
        from fuzzywuzzy import fuzz
        import unidecode

        titulo = str(row.get('titulo', '')).strip()
        if not titulo:
            # Si no hay título, usar candidatos genéricos
            import random
            sample_ids = random.sample(list(self.ocupaciones.keys()), min(top_n, len(self.ocupaciones)))
            candidates = []
            for occ_id in sample_ids:
                occ_data = self.ocupaciones[occ_id]
                candidates.append({
                    'id': occ_id,
                    'label_es': occ_data['label_es'],
                    'codigo_isco': occ_data.get('codigo_isco', 'N/A'),
                    'score': 0
                })
            return candidates

        # Normalizar título
        titulo_norm = unidecode.unidecode(titulo.lower())
        titulo_norm = re.sub(r'[^\w\s]', ' ', titulo_norm)
        titulo_norm = ' '.join(titulo_norm.split())

        # Calcular scores fuzzy para todas las ocupaciones
        scores = []
        for occ_id, occ_data in self.ocupaciones.items():
            label_es = occ_data.get('label_es')
            if not label_es:
                continue  # Skip if no label

            label_norm = unidecode.unidecode(label_es.lower())
            label_norm = re.sub(r'[^\w\s]', ' ', label_norm)
            label_norm = ' '.join(label_norm.split())

            score = fuzz.token_sort_ratio(titulo_norm, label_norm)
            scores.append((occ_id, occ_data, score))

        # Ordenar por score descendente
        scores.sort(key=lambda x: x[2], reverse=True)

        # Tomar top N
        candidates = []
        for occ_id, occ_data, score in scores[:top_n]:
            candidates.append({
                'id': occ_id,
                'label_es': occ_data['label_es'],
                'codigo_isco': occ_data.get('codigo_isco', 'N/A'),
                'score': score
            })

        return candidates

    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """
        Extrae JSON de la respuesta del LLM

        Args:
            response: Respuesta del LLM

        Returns:
            Diccionario con datos parseados o None
        """
        # Intentar encontrar JSON en la respuesta
        # Buscar entre { y }
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError:
                pass

        # Intentar parsear directamente
        try:
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            logger.warning(f"No se pudo parsear JSON de respuesta: {response[:200]}")
            return None

    def _classify_with_llm(self, row: pd.Series) -> Tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Clasifica una oferta usando LLM

        Args:
            row: Fila del DataFrame

        Returns:
            (esco_id, codigo_isco, confianza) o (None, None, None) si falla
        """
        # Obtener candidatos
        candidates = self._get_top_candidates(row, top_n=15)

        # Preparar información de la oferta
        titulo = str(row.get('titulo', ''))
        descripcion = str(row.get('descripcion', ''))[:500]  # Limitar descripción
        soft_skills = str(row.get('soft_skills', '')) if pd.notna(row.get('soft_skills')) else 'N/A'
        skills_tecnicas = str(row.get('skills_tecnicas', '')) if pd.notna(row.get('skills_tecnicas')) else 'N/A'

        # Construir prompt
        candidates_str = "\n".join([
            f"- Label: {c['label_es']}, ISCO: {c['codigo_isco']}, Score Fuzzy: {c.get('score', 0)}"
            for c in candidates
        ])

        prompt = f"""Eres un experto en clasificacion ocupacional segun la taxonomia ESCO (European Skills, Competences, Qualifications and Occupations).

OFERTA LABORAL:
Titulo: {titulo}
Descripcion: {descripcion}
Soft Skills: {soft_skills}
Skills Tecnicas: {skills_tecnicas}

OCUPACIONES ESCO CANDIDATAS:
{candidates_str}

TAREA:
Identifica cual ocupacion ESCO corresponde MEJOR a esta oferta laboral.
Considera el titulo, descripcion y skills para hacer tu eleccion.

Responde SOLO con un objeto JSON en este formato exacto (sin texto adicional):
{{
    "esco_label": "nombre de la ocupacion ESCO elegida",
    "confianza": 85
}}

JSON:"""

        # Llamar a Ollama
        response = self._call_ollama(prompt)
        if not response:
            return None, None, None

        # Parsear respuesta
        data = self._extract_json_from_response(response)
        if not data:
            return None, None, None

        # Extraer datos
        esco_label = data.get('esco_label', '').lower()
        confianza = float(data.get('confianza', 0))

        # Buscar ID de ocupación por label
        esco_id = None
        codigo_isco = None

        # Buscar coincidencia exacta
        if esco_label in self.ocupaciones_by_label:
            esco_id = self.ocupaciones_by_label[esco_label]
            codigo_isco = self.ocupaciones[esco_id].get('codigo_isco')
        else:
            # Buscar coincidencia parcial
            for label, occ_id in self.ocupaciones_by_label.items():
                if esco_label in label or label in esco_label:
                    esco_id = occ_id
                    codigo_isco = self.ocupaciones[esco_id].get('codigo_isco')
                    break

        if esco_id:
            return esco_id, codigo_isco, confianza
        else:
            logger.warning(f"No se encontro ocupacion ESCO para label: {esco_label}")
            return None, None, None

    def run_fallback(self, batch_size: int = 50) -> pd.DataFrame:
        """
        Ejecuta LLM fallback en ofertas de baja confianza

        Args:
            batch_size: Procesar en lotes (para guardar progreso)

        Returns:
            DataFrame actualizado
        """
        # Identificar ofertas de baja confianza
        mask_baja = self.df['esco_match_score'] < self.threshold
        ofertas_baja = self.df[mask_baja].copy()

        logger.info("")
        logger.info("=" * 70)
        logger.info("LLM FALLBACK - MEJORA DE MATCHING")
        logger.info("=" * 70)
        logger.info(f"Total ofertas: {len(self.df):,}")
        logger.info(f"Ofertas baja confianza (score < {self.threshold}): {len(ofertas_baja):,} ({len(ofertas_baja)/len(self.df)*100:.1f}%)")
        logger.info("")

        if len(ofertas_baja) == 0:
            logger.info("No hay ofertas de baja confianza para procesar")
            return self.df

        # Estadísticas pre-fallback
        score_promedio_antes = ofertas_baja['esco_match_score'].mean()
        logger.info(f"Score promedio ANTES del fallback: {score_promedio_antes:.1f}")
        logger.info("")

        # Procesar con LLM
        mejoras = 0
        sin_mejora = 0
        fallidos = 0

        logger.info("Procesando con LLM...")
        for idx in tqdm(ofertas_baja.index, desc="LLM Fallback"):
            row = self.df.loc[idx]

            # Clasificar con LLM
            esco_id, codigo_isco, confianza_llm = self._classify_with_llm(row)

            if esco_id and codigo_isco:
                # Actualizar en DataFrame
                self.df.at[idx, 'esco_occupation_id'] = esco_id
                self.df.at[idx, 'esco_occupation_label'] = self.ocupaciones[esco_id]['label_es']
                self.df.at[idx, 'esco_codigo_isco'] = codigo_isco
                self.df.at[idx, 'esco_match_score'] = confianza_llm
                self.df.at[idx, 'esco_match_method'] = 'llm'

                # Actualizar confianza
                if confianza_llm >= 80:
                    self.df.at[idx, 'esco_confianza'] = 'alta'
                elif confianza_llm >= 70:
                    self.df.at[idx, 'esco_confianza'] = 'media'
                else:
                    self.df.at[idx, 'esco_confianza'] = 'baja'

                mejoras += 1
            else:
                fallidos += 1

        # Estadísticas post-fallback
        logger.info("")
        logger.info("=" * 70)
        logger.info("RESULTADOS")
        logger.info("=" * 70)
        logger.info(f"Ofertas procesadas: {len(ofertas_baja):,}")
        logger.info(f"Mejoras exitosas: {mejoras:,} ({mejoras/len(ofertas_baja)*100:.1f}%)")
        logger.info(f"Fallidos: {fallidos:,} ({fallidos/len(ofertas_baja)*100:.1f}%)")
        logger.info("")

        # Estadísticas de confianza después
        dist_confianza = self.df['esco_confianza'].value_counts()
        logger.info("DISTRIBUCION DE CONFIANZA (DESPUES):")
        for conf, count in dist_confianza.items():
            logger.info(f"  {conf}: {count:,} ({count/len(self.df)*100:.1f}%)")

        logger.info("")
        logger.info("SCORES PROMEDIO:")
        for method in ['fuzzy', 'llm']:
            mask_method = self.df['esco_match_method'] == method
            if mask_method.sum() > 0:
                avg_score = self.df[mask_method]['esco_match_score'].mean()
                logger.info(f"  {method}: {avg_score:.1f}")

        return self.df

    def save_results(self, output_path: Optional[str] = None) -> str:
        """
        Guarda resultados con fallback aplicado

        Args:
            output_path: Ruta de salida (opcional)

        Returns:
            Ruta del archivo guardado
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(self.matched_csv).parent
            output_path = output_dir / f'ofertas_esco_isco_llm_{timestamp}.csv'

        self.df.to_csv(output_path, index=False)

        # Tamaño del archivo
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)

        logger.info("")
        logger.info(f"Guardando: {output_path}")
        logger.info(f"Tamano: {size_mb:.1f} MB")
        logger.info("")
        logger.info("Matching con LLM fallback completado!")

        return str(output_path)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='LLM Fallback para ESCO/ISCO Matching')
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Archivo CSV con matching actual'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=70.0,
        help='Threshold de score para baja confianza (default: 70.0)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='llama3',
        help='Modelo Ollama a usar (default: llama3)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Tamano de lote (default: 50)'
    )

    args = parser.parse_args()

    # Crear fallback
    fallback = ESCOLLMFallback(
        matched_csv=args.input,
        threshold=args.threshold,
        model=args.model
    )

    # Ejecutar fallback
    df_updated = fallback.run_fallback(batch_size=args.batch_size)

    # Guardar resultados
    fallback.save_results()


if __name__ == '__main__':
    main()
