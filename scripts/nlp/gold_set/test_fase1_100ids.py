#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test FASE 1 - Medir impacto de mejoras en 100 IDs
=================================================

Ejecuta las mejoras de FASE 1 en los 100 IDs de test:
1. Limpia títulos con regex v2.2
2. Aplica matching v3.2.1 con penalización sector
3. Exporta resultados para comparación

FASE 1 mejoras:
- limpiar_titulos.py v2.2: códigos, modalidad, ubicación, edad
- sector_isco_compatibilidad.json v2.0: 20 sectores con penalización
- match_ofertas_v3.py v3.2.1: usa sector_empresa para penalizar

Ejecutar desde /database/:
    python ../scripts/nlp/gold_set/test_fase1_100ids.py
"""

import sqlite3
import json
import sys
import io
from pathlib import Path
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "database"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Imports locales
from limpiar_titulos import limpiar_titulo, cargar_config

DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "bumeran_scraping.db"


def get_100_ids():
    """Obtiene los 100 IDs de test."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute('''
        SELECT DISTINCT n.id_oferta
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.titulo_limpio IS NOT NULL
        ORDER BY n.id_oferta DESC
        LIMIT 100
    ''')
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids


def test_titulo_cleaning(verbose=True):
    """Prueba limpieza de títulos en 100 IDs."""
    conn = sqlite3.connect(str(DB_PATH))
    config = cargar_config()

    # Obtener títulos originales de scraping
    cur = conn.execute('''
        SELECT o.id_oferta, o.titulo as titulo_scraping, n.titulo_limpio as titulo_nlp
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE n.titulo_limpio IS NOT NULL
        ORDER BY o.id_oferta DESC
        LIMIT 100
    ''')

    cleaned_count = 0
    same_count = 0
    results = []

    print("=" * 70)
    print("PRUEBA LIMPIEZA TÍTULOS v2.2")
    print("=" * 70)

    for row in cur.fetchall():
        id_oferta, titulo_scraping, titulo_nlp = row

        # Aplicar limpieza al título original de scraping
        titulo_limpio_nuevo = limpiar_titulo(titulo_scraping or "", config)

        # Comparar con el título NLP actual
        if titulo_limpio_nuevo != titulo_nlp:
            cleaned_count += 1
            if verbose and cleaned_count <= 15:
                print(f"\n[{id_oferta}] CAMBIO:")
                print(f"  Scraping:  {titulo_scraping[:70]}...")
                print(f"  NLP actual: {titulo_nlp[:70]}...")
                print(f"  Nuevo:     {titulo_limpio_nuevo[:70]}...")
        else:
            same_count += 1

        results.append({
            "id_oferta": id_oferta,
            "titulo_scraping": titulo_scraping,
            "titulo_nlp_actual": titulo_nlp,
            "titulo_limpio_nuevo": titulo_limpio_nuevo,
            "cambio": titulo_limpio_nuevo != titulo_nlp
        })

    conn.close()

    print(f"\n{'=' * 70}")
    print(f"RESUMEN LIMPIEZA:")
    print(f"  Títulos mejorados: {cleaned_count} ({cleaned_count}%)")
    print(f"  Sin cambio: {same_count} ({same_count}%)")
    print(f"{'=' * 70}")

    return results


def test_sector_coverage():
    """Verifica cobertura de sector_empresa en los 100 IDs."""
    conn = sqlite3.connect(str(DB_PATH))

    cur = conn.execute('''
        SELECT id_oferta, sector_empresa
        FROM ofertas_nlp
        WHERE id_oferta IN (
            SELECT DISTINCT n.id_oferta
            FROM ofertas_nlp n
            JOIN ofertas o ON n.id_oferta = o.id_oferta
            WHERE n.titulo_limpio IS NOT NULL
            ORDER BY n.id_oferta DESC
            LIMIT 100
        )
    ''')

    sectores = {}
    sin_sector = 0

    for row in cur.fetchall():
        sector = row[1]
        if sector:
            sectores[sector] = sectores.get(sector, 0) + 1
        else:
            sin_sector += 1

    conn.close()

    print(f"\n{'=' * 70}")
    print("COBERTURA SECTOR_EMPRESA:")
    print(f"{'=' * 70}")
    print(f"  Con sector: {100 - sin_sector} ({100 - sin_sector}%)")
    print(f"  Sin sector: {sin_sector} ({sin_sector}%)")
    print(f"\nDistribución:")
    for sector, count in sorted(sectores.items(), key=lambda x: -x[1])[:15]:
        print(f"  {sector}: {count}")

    return sectores


def get_current_matching_results():
    """Obtiene resultados actuales del matching."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    cur = conn.execute('''
        SELECT m.id_oferta, m.isco_code, m.esco_occupation_label,
               m.occupation_match_score, m.occupation_match_method,
               n.titulo_limpio, n.sector_empresa, n.area_funcional, n.nivel_seniority
        FROM ofertas_esco_matching m
        JOIN ofertas_nlp n ON m.id_oferta = n.id_oferta
        WHERE m.id_oferta IN (
            SELECT DISTINCT n2.id_oferta
            FROM ofertas_nlp n2
            JOIN ofertas o ON n2.id_oferta = o.id_oferta
            WHERE n2.titulo_limpio IS NOT NULL
            ORDER BY n2.id_oferta DESC
            LIMIT 100
        )
    ''')

    results = [dict(row) for row in cur.fetchall()]
    conn.close()

    return results


def main():
    """Ejecuta todas las pruebas de FASE 1."""
    print("=" * 70)
    print("TEST FASE 1 - 100 IDs")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    # 1. Test limpieza títulos
    titulo_results = test_titulo_cleaning(verbose=True)

    # 2. Cobertura sector
    test_sector_coverage()

    # 3. Resultados matching actuales
    matching_results = get_current_matching_results()
    print(f"\n{'=' * 70}")
    print(f"MATCHING ACTUAL:")
    print(f"  IDs con matching: {len(matching_results)}")
    if matching_results:
        methods = {}
        for r in matching_results:
            m = r.get("occupation_match_method", "?")
            methods[m] = methods.get(m, 0) + 1
        print(f"  Métodos: {methods}")
    print(f"{'=' * 70}")

    # 4. Identificar casos problemáticos (sector incompatible con ISCO actual)
    print(f"\n{'=' * 70}")
    print("CASOS POTENCIALMENTE AFECTADOS POR PENALIZACIÓN SECTOR:")
    print(f"{'=' * 70}")

    # Cargar config sector
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "sector_isco_compatibilidad.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        sector_config = json.load(f)

    sectores_cfg = sector_config.get("sectores", {})
    aliases = sector_config.get("aliases", {})

    affected = 0
    for r in matching_results:
        sector = r.get("sector_empresa", "")
        isco = r.get("isco_code", "")

        if not sector or not isco:
            continue

        # Normalizar sector
        sector_norm = aliases.get(sector, sector)
        sector_cfg = sectores_cfg.get(sector_norm, {})

        if not sector_cfg:
            continue

        compatibles = sector_cfg.get("isco_compatibles", [])
        is_compatible = any(isco.startswith(c) for c in compatibles)

        if not is_compatible:
            affected += 1
            if affected <= 10:
                print(f"  [{r['id_oferta']}] {r['titulo_limpio'][:40]}...")
                print(f"     Sector: {sector} | ISCO: {isco} | {r['esco_occupation_label'][:40]}...")

    print(f"\nTotal afectados por penalización: {affected} ({affected}%)")

    return {
        "titulo_changes": sum(1 for t in titulo_results if t["cambio"]),
        "matching_count": len(matching_results),
        "sector_affected": affected
    }


if __name__ == "__main__":
    results = main()
    print(f"\n{'=' * 70}")
    print("RESUMEN FASE 1:")
    print(f"  Títulos mejorados: {results['titulo_changes']}")
    print(f"  IDs con matching: {results['matching_count']}")
    print(f"  Afectados por sector: {results['sector_affected']}")
    print(f"{'=' * 70}")
