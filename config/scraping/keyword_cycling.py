"""
Keyword Cycling — Rotación semanal de keywords
===============================================

Divide un pool de keywords en N chunks y selecciona el chunk
correspondiente a la semana actual (ISO week number % N).

Cada corrida usa solo una fracción de las keywords, reduciendo
el volumen de requests y el riesgo de bloqueo por anti-bot.

Uso:
    from keyword_cycling import get_weekly_chunk, load_keywords_with_cycling

    # Desde lista
    chunk = get_weekly_chunk(all_keywords, num_chunks=4)

    # Desde master_keywords.json
    chunk = load_keywords_with_cycling(
        'config/scraping/master_keywords.json',
        estrategia='exhaustiva',
        num_chunks=4
    )
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def get_weekly_chunk(keywords: List[str], num_chunks: int = 4,
                     force_chunk: Optional[int] = None) -> List[str]:
    """
    Devuelve el chunk de keywords correspondiente a esta semana.

    Args:
        keywords: Lista completa de keywords
        num_chunks: En cuántos chunks dividir (default: 4 = ciclo mensual)
        force_chunk: Forzar un chunk específico (0-based, para testing)

    Returns:
        Sublista de keywords para esta semana
    """
    if not keywords or num_chunks <= 1:
        return keywords

    week_number = datetime.now().isocalendar()[1]
    chunk_index = force_chunk if force_chunk is not None else (week_number % num_chunks)

    chunk_size = len(keywords) // num_chunks
    remainder = len(keywords) % num_chunks

    start = chunk_index * chunk_size + min(chunk_index, remainder)
    end = start + chunk_size + (1 if chunk_index < remainder else 0)

    chunk = keywords[start:end]

    logger.info(f"Keyword cycling: semana ISO {week_number}, "
                f"chunk {chunk_index+1}/{num_chunks} "
                f"({len(chunk)} de {len(keywords)} keywords)")

    return chunk


def get_cycling_info(keywords: List[str], num_chunks: int = 4) -> Dict:
    """Info del estado actual del cycling."""
    week_number = datetime.now().isocalendar()[1]
    chunk_index = week_number % num_chunks
    chunk = get_weekly_chunk(keywords, num_chunks)

    return {
        'week_number': week_number,
        'chunk_index': chunk_index,
        'num_chunks': num_chunks,
        'chunk_size': len(chunk),
        'total_keywords': len(keywords),
    }


def load_keywords_with_cycling(json_path: str, estrategia: str = "exhaustiva",
                                num_chunks: int = 4,
                                force_chunk: Optional[int] = None) -> List[str]:
    """
    Carga keywords desde master_keywords.json y aplica cycling.

    Args:
        json_path: Ruta al archivo de keywords
        estrategia: Nombre de la estrategia
        num_chunks: Chunks de cycling (default 4)
        force_chunk: Forzar chunk específico (0-based)

    Returns:
        Sublista de keywords para esta semana
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_keywords = data.get('estrategias', {}).get(estrategia, {}).get('keywords', [])
    all_keywords = [k for k in all_keywords if k.strip()]

    if not all_keywords:
        logger.error(f"No se encontraron keywords en estrategia '{estrategia}'")
        return []

    return get_weekly_chunk(all_keywords, num_chunks, force_chunk)
