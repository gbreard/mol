#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
normalizacion_arg.py
====================
Normaliza terminos argentinos usando diccionario_arg_esco.

VERSION: v1.1 (2025-12-09) - Integración con config_loader

Integracion con match_ofertas_multicriteria.py:
- Busca terminos argentinos en el titulo de la oferta
- Retorna el ISCO target y label ESCO preferido
- Usado para dar hint/boost a candidatos correctos
- Carga valores de boost desde config/normalizacion_boost.json
"""

import re
import sqlite3
from pathlib import Path
from functools import lru_cache

# Intentar cargar configuración externalizada
try:
    from config_loader import get_boost_config, get_boost_isco
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    CONFIG_LOADER_AVAILABLE = False

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Cargar valores de boost desde config o usar defaults
if CONFIG_LOADER_AVAILABLE:
    BOOST_EXACT_ISCO = get_boost_isco('exact_isco')
    BOOST_ISCO_GROUP = get_boost_isco('isco_group')
    PENALTY_WRONG_ISCO = get_boost_isco('wrong_isco')
else:
    # Fallback a valores hardcodeados
    BOOST_EXACT_ISCO = 0.20
    BOOST_ISCO_GROUP = 0.12
    PENALTY_WRONG_ISCO = -0.15

# Cache del diccionario en memoria
_DICCIONARIO_CACHE = None


def _cargar_diccionario(conn=None):
    """Carga diccionario de normalizacion argentino desde DB"""
    global _DICCIONARIO_CACHE

    if _DICCIONARIO_CACHE is not None:
        return _DICCIONARIO_CACHE

    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
        SELECT termino_argentino, isco_target, esco_preferred_label, esco_terms_json
        FROM diccionario_arg_esco
        WHERE termino_argentino IS NOT NULL AND isco_target IS NOT NULL
    """)

    diccionario = {}
    for row in cursor.fetchall():
        # Use index-based access for compatibility with connections without row_factory
        termino = row[0].lower().strip()
        diccionario[termino] = {
            'isco_target': row[1],
            'esco_label': row[2],
            'esco_terms': row[3]
        }

    if close_conn:
        conn.close()

    _DICCIONARIO_CACHE = diccionario
    return diccionario


def normalizar_termino_argentino(titulo: str, conn=None) -> tuple:
    """
    Busca en diccionario_arg_esco si el titulo tiene termino argentino.

    Args:
        titulo: Titulo de la oferta laboral
        conn: Conexion a DB (opcional, crea nueva si no se provee)

    Returns:
        tuple: (termino_encontrado, isco_target, esco_label, titulo_normalizado)
               Si no encuentra match, retorna (None, None, None, titulo)

    Ejemplos:
        "Mozo/Moza para restaurant" -> ("mozo", "5131", "Mozo/Camarero", "Camarero/Camarera para restaurant")
        "Repositor Externo" -> ("repositor", "5223", "Reponedor de tienda", "Reponedor de tienda Externo")
        "Analista de sistemas" -> (None, None, None, "Analista de sistemas")
    """
    diccionario = _cargar_diccionario(conn)

    if not titulo:
        return None, None, None, titulo

    titulo_lower = titulo.lower().strip()
    titulo_normalizado = titulo

    # Buscar matches en el diccionario
    # Ordenar por longitud descendente para matchear primero terminos mas largos
    terminos_ordenados = sorted(diccionario.keys(), key=len, reverse=True)

    for termino in terminos_ordenados:
        # Buscar como palabra completa (con word boundaries)
        pattern = r'\b' + re.escape(termino) + r'\b'
        if re.search(pattern, titulo_lower):
            data = diccionario[termino]

            # Crear titulo normalizado reemplazando termino argentino por ESCO
            esco_label = data['esco_label'] or ''
            if esco_label:
                # Mantener la capitalizacion original del titulo
                titulo_normalizado = re.sub(
                    pattern,
                    esco_label,
                    titulo_lower,
                    flags=re.IGNORECASE
                )
                # Capitalizar primera letra
                titulo_normalizado = titulo_normalizado.capitalize()

            return termino, data['isco_target'], data['esco_label'], titulo_normalizado

    return None, None, None, titulo


def obtener_boost_isco(titulo: str, candidatos: list, conn=None) -> list:
    """
    Aplica boost/penalizacion a candidatos ESCO basado en diccionario argentino.

    Si el titulo tiene un termino argentino mapeado a un ISCO:
    - Candidatos con ISCO correcto reciben BOOST
    - Candidatos con ISCO incorrecto reciben PENALIZACION

    Args:
        titulo: Titulo de la oferta
        candidatos: Lista de candidatos ESCO del PASO 1
        conn: Conexion DB opcional

    Returns:
        Lista de candidatos reordenados con boost/penalizacion aplicado
    """
    termino, isco_target, esco_label, _ = normalizar_termino_argentino(titulo, conn)

    if not isco_target:
        return candidatos  # Sin cambios

    # Usar constantes del módulo (cargadas desde config o hardcodeadas)
    candidatos_boosted = []
    for cand in candidatos:
        cand_copy = cand.copy()
        isco_cand = cand.get('isco_code', '')

        boost = 0.0
        boost_reason = None

        if isco_cand:
            # Boost exacto: si el ISCO coincide completamente o empieza igual
            if isco_cand.startswith(isco_target) or isco_target.startswith(isco_cand):
                boost = BOOST_EXACT_ISCO
                boost_reason = f"isco_exact:{termino}->{isco_target}"
            # Boost de grupo: si el primer digito coincide
            elif isco_cand[0] == isco_target[0]:
                boost = BOOST_ISCO_GROUP
                boost_reason = f"isco_group:{termino}->{isco_target[0]}xxx"
            # Penalizacion: ISCO diferente al esperado
            else:
                boost = PENALTY_WRONG_ISCO
                boost_reason = f"isco_mismatch:{termino}->expected_{isco_target}_got_{isco_cand}"

        if boost != 0:
            cand_copy['similarity_score'] = cand_copy.get('similarity_score', 0) + boost
            cand_copy['arg_boost'] = boost
            cand_copy['arg_boost_reason'] = boost_reason

        candidatos_boosted.append(cand_copy)

    # Reordenar por score boosted
    candidatos_boosted.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)

    return candidatos_boosted


def buscar_match_diccionario_directo(titulo: str, conn=None) -> dict | None:
    """
    Busca match DIRECTO en diccionario argentino y retorna ocupación ESCO completa.

    BYPASS SEMANTICO: Si hay match exacto en diccionario, retorna el resultado
    directamente sin pasar por la búsqueda semántica BGE-M3.

    Args:
        titulo: Título de la oferta laboral
        conn: Conexión a DB (opcional)

    Returns:
        dict con datos ESCO si hay match, None si no hay match
        {
            'occupation_uri': '...',
            'occupation_label': '...',
            'isco_code': '...',
            'termino_argentino': '...',
            'match_method': 'diccionario_argentino'
        }
    """
    termino, isco_target, esco_label_dict, _ = normalizar_termino_argentino(titulo, conn)

    if not isco_target or not esco_label_dict:
        return None

    # Buscar ocupación ESCO que coincida con el label del diccionario
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        close_conn = True

    cursor = conn.cursor()

    # Buscar por preferred_label_es (match exacto)
    cursor.execute("""
        SELECT occupation_uri, preferred_label_es, isco_code
        FROM esco_occupations
        WHERE LOWER(preferred_label_es) = LOWER(?)
    """, (esco_label_dict,))

    row = cursor.fetchone()

    if not row:
        # Fallback: buscar ocupación con ISCO target que contenga el label
        cursor.execute("""
            SELECT occupation_uri, preferred_label_es, isco_code
            FROM esco_occupations
            WHERE isco_code LIKE ?
            AND LOWER(preferred_label_es) LIKE ?
            LIMIT 1
        """, (f'%{isco_target}%', f'%{esco_label_dict.split("/")[0].lower()}%'))
        row = cursor.fetchone()

    if close_conn:
        conn.close()

    if not row:
        return None

    # Limpiar ISCO code (quitar prefijo C)
    isco_clean = row[2].lstrip('C') if row[2] else isco_target

    return {
        'occupation_uri': row[0],
        'occupation_label': row[1],
        'isco_code': isco_clean,
        'termino_argentino': termino,
        'esco_label_dict': esco_label_dict,
        'match_method': 'diccionario_argentino'
    }


def get_stats():
    """Retorna estadisticas del diccionario"""
    diccionario = _cargar_diccionario()

    isco_groups = {}
    for termino, data in diccionario.items():
        isco = data['isco_target']
        grupo = isco[0] if isco else '?'
        isco_groups[grupo] = isco_groups.get(grupo, 0) + 1

    return {
        'config_loader_activo': CONFIG_LOADER_AVAILABLE,
        'total_terminos': len(diccionario),
        'por_grupo_isco': dict(sorted(isco_groups.items())),
        'boost_exact_isco': BOOST_EXACT_ISCO,
        'boost_isco_group': BOOST_ISCO_GROUP,
        'penalty_wrong_isco': PENALTY_WRONG_ISCO
    }


# Test standalone
if __name__ == '__main__':
    print("=" * 60)
    print("TEST: normalizacion_arg.py")
    print("=" * 60)

    stats = get_stats()
    print(f"\nDiccionario cargado: {stats['total_terminos']} terminos")
    print(f"Por grupo ISCO: {stats['por_grupo_isco']}")

    # Test cases
    test_titulos = [
        "Mozo/Moza para restaurant",
        "Repositor Externo Zona Norte",
        "Camarero para hotel",
        "Analista de sistemas",
        "Chofer de camion",
        "Fletero con vehiculo propio",
        "Vendedor de mostrador",
        "Promovendedora para supermercado"
    ]

    print("\n" + "-" * 60)
    print("TESTS DE NORMALIZACION:")
    print("-" * 60)

    for titulo in test_titulos:
        termino, isco, esco_label, titulo_norm = normalizar_termino_argentino(titulo)
        if termino:
            print(f"\n  '{titulo}'")
            print(f"    -> Termino:    {termino}")
            print(f"    -> ISCO:       {isco}")
            print(f"    -> ESCO Label: {esco_label}")
            print(f"    -> Normalizado:{titulo_norm}")
        else:
            print(f"\n  '{titulo}' -> Sin match en diccionario")
