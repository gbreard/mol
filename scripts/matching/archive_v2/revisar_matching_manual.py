#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revision manual de resultados del matching.
Genera un reporte detallado para analisis humano.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'D:/OEDE/Webscrapping/database')
sys.path.insert(0, 'D:/OEDE/Webscrapping')

import sqlite3
from pathlib import Path

from match_ofertas_v2 import (
    load_all_configs,
    get_semantic_matcher,
    match_oferta_v2_bge,
    obtener_ofertas_nlp
)

DB_PATH = Path("D:/OEDE/Webscrapping/database/bumeran_scraping.db")


def revisar_matching(limit: int = 50):
    """Revisa cada caso de matching."""

    conn = sqlite3.connect(str(DB_PATH))

    print("Cargando modelo...")
    matcher = get_semantic_matcher()
    matcher.load()

    config = load_all_configs()
    ofertas = obtener_ofertas_nlp(conn, limit=limit)

    print(f"\n{'='*100}")
    print(f"REVISION MANUAL DE MATCHING - {len(ofertas)} OFERTAS")
    print(f"{'='*100}\n")

    for i, oferta in enumerate(ofertas, 1):
        result = match_oferta_v2_bge(oferta, conn, config)

        # Extraer codigo ESCO del URI
        esco_code = ""
        if result.esco_uri and "/" in result.esco_uri:
            esco_code = result.esco_uri.split("/")[-1]

        print(f"{'='*100}")
        print(f"[{i:02d}/50] ID: {oferta['id_oferta']}")
        print(f"{'='*100}")
        print(f"TITULO ORIGINAL: {oferta.get('titulo', '')}")
        print(f"TITULO LIMPIO:   {oferta.get('titulo_limpio', '')}")
        print(f"")
        print(f"NLP DATA:")
        print(f"  - Area funcional: {oferta.get('area_funcional')}")
        print(f"  - Seniority:      {oferta.get('nivel_seniority')}")
        print(f"  - Sector:         {oferta.get('sector_empresa')}")
        print(f"  - NLP version:    {oferta.get('nlp_version')}")
        print(f"")
        print(f"RESULTADO MATCHING:")
        print(f"  - Status:     {result.status}")
        print(f"  - Metodo:     {result.metodo}")
        print(f"  - ESCO Label: {result.esco_label}")
        print(f"  - ESCO Code:  {esco_code}")
        print(f"  - ISCO Code:  {result.isco_code}")
        print(f"  - Score:      {result.score:.4f}" if result.score else "  - Score:      N/A")
        print(f"")

        if result.alternativas:
            print(f"ALTERNATIVAS:")
            for j, alt in enumerate(result.alternativas[:3], 1):
                alt_esco = alt.get('esco_uri', '').split('/')[-1] if alt.get('esco_uri') else ''
                print(f"  Alt{j}: {alt.get('label', '')[:60]}")
                print(f"         ESCO: {alt_esco} | ISCO: {alt.get('isco_code')} | Score: {alt.get('score', 0):.3f}")

        print(f"\n")

    conn.close()


if __name__ == "__main__":
    revisar_matching(50)
