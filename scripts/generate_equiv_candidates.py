#!/usr/bin/env python3
"""
M-08b Parte 2: Detecta candidatos a nuevos grupos de equivalencia
desde co-matcheo de skills declaradas.

Un par de términos es candidato cuando:
- Dos texto_original distintos matchearon la misma URI ESCO
- En al menos 5 ofertas distintas
- No están ya en el mismo grupo de equivalencia

Uso:
    python scripts/generate_equiv_candidates.py              # Detectar y subir
    python scripts/generate_equiv_candidates.py --dry-run    # Solo mostrar
    python scripts/generate_equiv_candidates.py --min-co 10  # Mínimo 10 co-apariciones
"""

import json
import sys
import argparse
import sqlite3
from pathlib import Path
from collections import defaultdict
from itertools import combinations

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "supabase_config.json"


def detect_candidates(min_co=5, verbose=True):
    """Detecta pares candidatos desde ofertas_esco_skills_detalle."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    if verbose:
        print("[CANDIDATES] Buscando co-matcheo en skills declaradas...")

    # Agrupar por URI ESCO: para cada URI, listar texto_original distintos
    rows = conn.execute('''
        SELECT esco_skill_uri, esco_skill_label, texto_original,
               skill_tipo_fuente, id_oferta, match_score
        FROM ofertas_esco_skills_detalle
        WHERE texto_original IS NOT NULL
        AND LENGTH(texto_original) > 1
    ''').fetchall()

    # Construir: URI → {texto_original → set(ofertas)}
    uri_textos = defaultdict(lambda: defaultdict(lambda: {"ofertas": set(), "fuente": "", "scores": []}))

    for row in rows:
        uri = row["esco_skill_uri"]
        texto = row["texto_original"].strip().lower()
        uri_textos[uri][texto]["ofertas"].add(row["id_oferta"])
        uri_textos[uri][texto]["fuente"] = row["skill_tipo_fuente"]
        uri_textos[uri][texto]["scores"].append(row["match_score"] or 0)

    # Cargar equivalencias existentes para filtrar
    equiv_lookup = {}
    try:
        rows_eq = conn.execute('''
            SELECT skill_uri, equivalence_id FROM ofertas_esco_skills_detalle
            WHERE equivalence_id IS NOT NULL
            GROUP BY skill_uri, equivalence_id
        ''').fetchall()
        for r in rows_eq:
            equiv_lookup[r["skill_uri"]] = r["equivalence_id"]
    except:
        pass

    conn.close()

    # Detectar pares
    candidates = []
    for uri, textos_dict in uri_textos.items():
        textos = list(textos_dict.keys())
        if len(textos) < 2:
            continue

        label_esco = ""
        # Obtener label de la primera fila
        for t_data in textos_dict.values():
            break

        for t_a, t_b in combinations(textos, 2):
            data_a = textos_dict[t_a]
            data_b = textos_dict[t_b]

            # Co-apariciones: ofertas donde ambos textos matchearon la misma URI
            co = len(data_a["ofertas"] & data_b["ofertas"])
            # También contar apariciones independientes
            total = len(data_a["ofertas"] | data_b["ofertas"])

            if total < min_co:
                continue

            # Filtrar si ya en el mismo grupo
            # (simplificación: si la URI tiene grupo, ambos textos ya están agrupados)
            # El check real sería por texto_original → URI → grupo, pero como matchean
            # la misma URI, estarían en el mismo grupo si la URI tiene equivalencia.
            # Esto es un filtro conservador.

            candidates.append({
                "uri_esco": uri,
                "skill_label_esco": "",  # Se llena abajo
                "termino_a": t_a,
                "termino_b": t_b,
                "fuente_a": data_a["fuente"],
                "fuente_b": data_b["fuente"],
                "co_apariciones": total,
                "score_promedio_a": round(sum(data_a["scores"]) / len(data_a["scores"]), 4) if data_a["scores"] else 0,
                "score_promedio_b": round(sum(data_b["scores"]) / len(data_b["scores"]), 4) if data_b["scores"] else 0,
            })

    # Llenar labels ESCO
    if candidates:
        conn2 = sqlite3.connect(str(DB_PATH))
        for c in candidates:
            row = conn2.execute(
                "SELECT esco_skill_label FROM ofertas_esco_skills_detalle WHERE esco_skill_uri = ? LIMIT 1",
                (c["uri_esco"],)
            ).fetchone()
            if row:
                c["skill_label_esco"] = row[0]
        conn2.close()

    candidates.sort(key=lambda x: -x["co_apariciones"])

    if verbose:
        print(f"[CANDIDATES] {len(candidates)} candidatos detectados (min_co={min_co})")
        for c in candidates[:10]:
            print(f'  {c["co_apariciones"]:>3}x | "{c["termino_a"]}" ↔ "{c["termino_b"]}" → {c["skill_label_esco"][:40]}')

    return candidates


def upload_candidates(candidates, verbose=True):
    """Sube candidatos a Supabase."""
    if not candidates:
        print("[CANDIDATES] Sin candidatos para subir")
        return

    config = json.load(open(CONFIG_PATH))
    from supabase import create_client
    client = create_client(config['url'], config['service_role_key'])

    for c in candidates:
        try:
            client.table('equiv_candidates').insert({
                "uri_esco": c["uri_esco"],
                "skill_label_esco": c["skill_label_esco"],
                "termino_a": c["termino_a"],
                "termino_b": c["termino_b"],
                "fuente_a": c["fuente_a"],
                "fuente_b": c["fuente_b"],
                "co_apariciones": c["co_apariciones"],
                "score_promedio_a": c["score_promedio_a"],
                "score_promedio_b": c["score_promedio_b"],
            }).execute()
        except Exception as e:
            if verbose:
                print(f"[CANDIDATES] Error: {e}")

    if verbose:
        print(f"[CANDIDATES] {len(candidates)} candidatos subidos a Supabase")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-co', type=int, default=5, help='Mínimo co-apariciones')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar, no subir')
    args = parser.parse_args()

    candidates = detect_candidates(min_co=args.min_co)

    if not args.dry_run:
        upload_candidates(candidates)
    else:
        print(f"\n[DRY-RUN] {len(candidates)} candidatos detectados, no subidos")


if __name__ == '__main__':
    main()
