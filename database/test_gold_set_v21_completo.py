#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test completo del Gold Set v2 (48 ofertas) con Matching v2.1 BGE-M3.

Compara:
- Match BGE-M3 v2.1 (semantico)
- Match existente en DB (v8.3/v8.4/v8.5)
- Expectativa del Gold Set v2

Ejecutar: python test_gold_set_v21_completo.py
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"ERROR: Falta dependencia: {e}")
    sys.exit(1)

# Paths
DB_PATH = Path(__file__).parent / "bumeran_scraping.db"
GOLD_SET_V2_PATH = Path(__file__).parent / "gold_set_manual_v2.json"
EMBEDDINGS_DIR = Path(__file__).parent / "embeddings"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "matching_config.json"


class SemanticMatcher:
    """Matcher semantico usando BGE-M3."""
    _instance = None

    def __init__(self):
        self.model = None
        self.esco_embeddings = None
        self.esco_metadata = None
        self.loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self):
        if self.loaded:
            return
        print("  Cargando modelo BGE-M3...")
        self.model = SentenceTransformer('BAAI/bge-m3')
        emb_path = EMBEDDINGS_DIR / "esco_occupations_embeddings.npy"
        meta_path = EMBEDDINGS_DIR / "esco_occupations_metadata.json"
        if not emb_path.exists():
            raise FileNotFoundError(f"Embeddings no encontrados")
        print("  Cargando embeddings pre-calculados...")
        self.esco_embeddings = np.load(str(emb_path))
        with open(meta_path, 'r', encoding='utf-8') as f:
            self.esco_metadata = json.load(f)
        print(f"  Embeddings: {len(self.esco_metadata)} ocupaciones ESCO")
        self.loaded = True

    def search(self, query: str, top_k: int = 5) -> list:
        if not self.loaded:
            self.load()
        query_emb = self.model.encode(query, normalize_embeddings=True)
        similarities = np.dot(self.esco_embeddings, query_emb)
        results = []
        for i, (meta, sim) in enumerate(zip(self.esco_metadata, similarities)):
            results.append({
                'esco_code': meta.get('esco_code', ''),
                'isco_code': meta.get('isco_code', ''),
                'preferred_label': meta.get('preferred_label', ''),
                'score': float(sim)
            })
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]


def cargar_gold_set_v2() -> list:
    """Carga el Gold Set v2."""
    with open(GOLD_SET_V2_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def cargar_oferta_datos(id_oferta: str) -> dict:
    """Carga datos de oferta y NLP."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            o.id_oferta, o.titulo, o.descripcion,
            n.titulo_normalizado, n.tareas_explicitas,
            n.skills_tecnicas_list, n.tecnologias_list, n.mision_rol
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.id_oferta = ?
    """, (id_oferta,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def cargar_match_existente(id_oferta: str) -> dict:
    """Carga el match existente en DB."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            esco_occupation_label as esco_label,
            occupation_match_score as score,
            occupation_match_method as metodo,
            matching_version
        FROM ofertas_esco_matching
        WHERE id_oferta = ?
        LIMIT 1
    """, (id_oferta,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def construir_query(oferta: dict) -> str:
    """Construye query semantica."""
    partes = []
    titulo = oferta.get('titulo_normalizado') or oferta.get('titulo', '')
    if titulo:
        partes.append(titulo)

    for campo in ['tareas_explicitas', 'skills_tecnicas_list', 'tecnologias_list']:
        raw = oferta.get(campo, '')
        if raw:
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(data, list) and data:
                    partes.append(', '.join(data[:5]))
            except:
                pass

    mision = oferta.get('mision_rol', '')
    if mision and len(mision) > 10:
        partes.append(mision[:150])

    return '. '.join(partes)


def run_test():
    """Ejecuta test completo."""
    print("=" * 80)
    print("TEST COMPLETO GOLD SET v2 - MATCHING v2.1 BGE-M3")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Cargar gold set
    gold_set = cargar_gold_set_v2()
    print(f"Gold Set v2: {len(gold_set)} ofertas")

    # Cargar config
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    threshold = config.get('filtros', {}).get('score_minimo_final', 0.50)
    print(f"Threshold: {threshold}")
    print()

    # Inicializar matcher
    matcher = SemanticMatcher.get_instance()
    matcher.load()
    print()

    # Resultados
    resultados = []
    bge_pass = 0
    bge_correct = 0  # Match BGE coincide con expectativa gold
    db_correct = 0   # Match DB coincide con expectativa gold

    print("-" * 80)
    print(f"{'ID':<12} {'Titulo':<28} {'Score':<6} {'BGE Match':<25} {'Gold':<5}")
    print("-" * 80)

    for caso in gold_set:
        id_oferta = caso['id_oferta']
        gold_ok = caso.get('esco_ok', False)

        # Cargar datos
        oferta = cargar_oferta_datos(id_oferta)
        if not oferta:
            print(f"{id_oferta:<12} {'NO DATA':<28} {'-':<6} {'-':<25} {'?':<5}")
            continue

        # Match BGE-M3
        query = construir_query(oferta)
        matches = matcher.search(query, top_k=3)

        if matches:
            best = matches[0]
            score = best['score']
            bge_label = best['preferred_label'][:24]
            passed = score >= threshold
            if passed:
                bge_pass += 1
        else:
            score = 0.0
            bge_label = "NO MATCH"
            passed = False

        # Match existente en DB
        db_match = cargar_match_existente(id_oferta)
        db_label = db_match.get('esco_label', 'N/A')[:24] if db_match else 'N/A'

        # Determinar si BGE coincide con gold
        # Si gold_ok=True, el match actual en DB es correcto
        # Comparamos si BGE produce algo similar
        gold_status = "OK" if gold_ok else "ERR"

        titulo = (oferta.get('titulo_normalizado') or oferta.get('titulo', ''))[:27]
        print(f"{id_oferta:<12} {titulo:<28} {score:<6.3f} {bge_label:<25} {gold_status:<5}")

        resultados.append({
            'id_oferta': id_oferta,
            'titulo': oferta.get('titulo', ''),
            'gold_ok': gold_ok,
            'bge_score': score,
            'bge_label': best['preferred_label'] if matches else None,
            'bge_passed': passed,
            'db_label': db_match.get('esco_label') if db_match else None,
            'comentario': caso.get('comentario', '')
        })

    # Resumen
    print("-" * 80)
    print()
    print("=" * 80)
    print("RESUMEN")
    print("=" * 80)

    total = len(resultados)
    gold_ok_count = sum(1 for r in resultados if r['gold_ok'])
    gold_err_count = total - gold_ok_count

    pct_pass = (bge_pass / total * 100) if total > 0 else 0

    print(f"""
Gold Set v2:
  - Total ofertas: {total}
  - Casos gold_ok=True: {gold_ok_count}
  - Casos gold_ok=False (errores conocidos): {gold_err_count}

Matching v2.1 BGE-M3:
  - Ofertas que pasan threshold ({threshold}): {bge_pass}/{total} ({pct_pass:.1f}%)
""")

    # Distribucion de scores
    scores = [r['bge_score'] for r in resultados if r['bge_score'] is not None]
    if scores:
        print("Distribucion de scores BGE-M3:")
        print(f"  Min: {min(scores):.3f}")
        print(f"  Max: {max(scores):.3f}")
        print(f"  Promedio: {sum(scores)/len(scores):.3f}")
        print()
        ranges = [(0.7, 1.0), (0.6, 0.7), (0.5, 0.6), (0.4, 0.5), (0.0, 0.4)]
        for low, high in ranges:
            count = sum(1 for s in scores if low <= s < high)
            pct = count / len(scores) * 100
            bar = "#" * int(pct / 5)
            print(f"    [{low:.1f}-{high:.1f}): {count:2d} ({pct:5.1f}%) {bar}")

    # Casos con gold_ok=False que pasaron (analizar si BGE los corrigio)
    print()
    print("=" * 80)
    print("CASOS CON gold_ok=False EN GOLD SET")
    print("=" * 80)
    errores = [r for r in resultados if not r['gold_ok']]
    if errores:
        for r in errores:
            print(f"\n  ID: {r['id_oferta']}")
            print(f"  Titulo: {r['titulo'][:50]}")
            print(f"  BGE Match: {r['bge_label']} (score: {r['bge_score']:.3f})")
            print(f"  DB Match: {r['db_label']}")
            print(f"  Comentario Gold: {r['comentario'][:80]}")
    else:
        print("  Ninguno - todos los casos son gold_ok=True")

    # Top y bottom scores
    print()
    print("=" * 80)
    print("TOP 5 MEJORES SCORES BGE-M3")
    print("=" * 80)
    top5 = sorted(resultados, key=lambda x: x.get('bge_score', 0), reverse=True)[:5]
    for r in top5:
        print(f"  {r['id_oferta']}: {r['bge_score']:.3f} -> {r.get('bge_label', 'N/A')[:40]}")

    print()
    print("=" * 80)
    print("BOTTOM 5 PEORES SCORES BGE-M3")
    print("=" * 80)
    bottom5 = sorted(resultados, key=lambda x: x.get('bge_score', 0))[:5]
    for r in bottom5:
        print(f"  {r['id_oferta']}: {r['bge_score']:.3f} -> {r.get('bge_label', 'N/A')[:40]}")

    return resultados


if __name__ == "__main__":
    run_test()
