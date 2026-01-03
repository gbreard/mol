#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validar precision REAL de Matching v2.1 BGE-M3.

Compara el ESCO que asigna BGE-M3 vs el ESCO esperado del Gold Set.
NO solo el score, sino el LABEL/URI correcto.

Ejecutar: python validar_precision_real_v21.py
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
GOLD_CANDIDATES_PATH = Path(__file__).parent / "gold_set_candidates_validated.json"
EMBEDDINGS_DIR = Path(__file__).parent / "embeddings"


class SemanticMatcher:
    """Matcher semantico BGE-M3."""
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
        for meta, sim in zip(self.esco_metadata, similarities):
            results.append({
                'esco_code': meta.get('esco_code', ''),
                'preferred_label': meta.get('preferred_label', ''),
                'score': float(sim)
            })
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]


def cargar_gold_sets():
    """Carga ambos gold sets y los combina."""
    # Gold set v2 tiene esco_ok actualizado
    with open(GOLD_SET_V2_PATH, 'r', encoding='utf-8') as f:
        gold_v2 = {item['id_oferta']: item for item in json.load(f)}

    # Gold candidates tiene los labels originales
    with open(GOLD_CANDIDATES_PATH, 'r', encoding='utf-8') as f:
        gold_candidates = {item['id_oferta']: item for item in json.load(f)}

    return gold_v2, gold_candidates


def cargar_oferta_datos(id_oferta: str) -> dict:
    """Carga datos de oferta y NLP."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id_oferta, o.titulo, o.descripcion,
               n.titulo_normalizado, n.tareas_explicitas,
               n.skills_tecnicas_list, n.tecnologias_list, n.mision_rol
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.id_oferta = ?
    """, (id_oferta,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def cargar_match_db(id_oferta: str) -> dict:
    """Carga match existente en DB (v8.3/v8.4/v8.5)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT esco_occupation_label, occupation_match_score, matching_version
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


def normalizar_label(label: str) -> str:
    """Normaliza label para comparacion."""
    if not label:
        return ""
    # Quitar acentos y lowercase
    import unicodedata
    label = unicodedata.normalize('NFD', label.lower())
    label = ''.join(c for c in label if unicodedata.category(c) != 'Mn')
    # Quitar genero (vendedor/vendedora -> vendedor)
    label = label.replace('/vendedora', '').replace('/cajera', '').replace('/operaria', '')
    label = label.replace('/', ' ')
    return label.strip()


def labels_similares(label1: str, label2: str) -> bool:
    """Compara si dos labels son semanticamente similares."""
    n1 = normalizar_label(label1)
    n2 = normalizar_label(label2)

    # Match exacto
    if n1 == n2:
        return True

    # Uno contiene al otro
    if n1 in n2 or n2 in n1:
        return True

    # Palabras clave en comun (al menos 2)
    words1 = set(n1.split())
    words2 = set(n2.split())
    common = words1 & words2
    # Excluir palabras comunes
    stopwords = {'de', 'del', 'la', 'el', 'los', 'las', 'y', 'o', 'en', 'para', 'con', 'a'}
    common = common - stopwords
    if len(common) >= 2:
        return True

    return False


def run_validacion():
    """Ejecuta validacion de precision real."""
    print("=" * 90)
    print("VALIDACION PRECISION REAL - MATCHING v2.1 BGE-M3")
    print("=" * 90)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Cargar gold sets
    gold_v2, gold_candidates = cargar_gold_sets()
    all_ids = set(gold_v2.keys()) | set(gold_candidates.keys())
    print(f"Total ofertas en Gold Sets: {len(all_ids)}")

    # Inicializar matcher
    matcher = SemanticMatcher.get_instance()
    matcher.load()
    print()

    # Resultados
    resultados = []
    bge_correctos = 0
    db_correctos = 0
    total = 0

    print("-" * 90)
    print(f"{'ID':<12} {'Titulo':<22} {'BGE Match':<22} {'DB Match':<22} {'OK?':<5}")
    print("-" * 90)

    for id_oferta in sorted(all_ids):
        gold_info = gold_v2.get(id_oferta, gold_candidates.get(id_oferta, {}))
        gold_ok = gold_info.get('esco_ok', False)
        gold_comment = gold_info.get('comentario', '')

        # El ESCO esperado es el que esta en gold_candidates (lo que asigno v8.3)
        expected_label = gold_candidates.get(id_oferta, {}).get('esco_label', '')

        # Cargar datos oferta
        oferta = cargar_oferta_datos(id_oferta)
        if not oferta:
            continue

        total += 1

        # Match BGE-M3
        query = construir_query(oferta)
        matches = matcher.search(query, top_k=3)
        bge_label = matches[0]['preferred_label'] if matches else "NO MATCH"
        bge_score = matches[0]['score'] if matches else 0

        # Match DB actual
        db_match = cargar_match_db(id_oferta)
        db_label = db_match.get('esco_occupation_label', 'N/A') if db_match else 'N/A'

        # Comparar BGE vs DB (ambos deberian coincidir si BGE es correcto)
        bge_similar_db = labels_similares(bge_label, db_label)

        # Determinar si BGE es correcto segun Gold Set
        # Si gold_ok=True, el match de DB es correcto
        # Entonces BGE es correcto si coincide con DB
        if gold_ok:
            bge_correcto = bge_similar_db
            db_correcto = True
        else:
            # Si gold_ok=False, DB esta mal
            # No podemos saber si BGE es correcto sin saber el ESCO correcto
            bge_correcto = False  # Asumimos que BGE tambien falla
            db_correcto = False

        if bge_correcto:
            bge_correctos += 1
        if db_correcto:
            db_correctos += 1

        status = "OK" if bge_correcto else ("ERR-G" if not gold_ok else "ERR-B")

        titulo = (oferta.get('titulo_normalizado') or oferta.get('titulo', ''))[:21]
        print(f"{id_oferta:<12} {titulo:<22} {bge_label[:21]:<22} {db_label[:21]:<22} {status:<5}")

        resultados.append({
            'id_oferta': id_oferta,
            'titulo': oferta.get('titulo', ''),
            'bge_label': bge_label,
            'bge_score': bge_score,
            'db_label': db_label,
            'gold_ok': gold_ok,
            'bge_correcto': bge_correcto,
            'similar': bge_similar_db,
            'comentario': gold_comment
        })

    # Resumen
    print("-" * 90)
    print()
    print("=" * 90)
    print("RESUMEN DE PRECISION")
    print("=" * 90)

    pct_bge = (bge_correctos / total * 100) if total > 0 else 0
    pct_db = (db_correctos / total * 100) if total > 0 else 0

    print(f"""
Total ofertas procesadas: {total}

Matching v2.1 BGE-M3:
  - Matches correctos: {bge_correctos}/{total}
  - Precision: {pct_bge:.1f}%

Matching DB (v8.3-v8.5):
  - Matches correctos (segun Gold Set): {db_correctos}/{total}
  - Precision: {pct_db:.1f}%

Comparacion BGE vs DB:
  - Casos donde BGE coincide con DB: {sum(1 for r in resultados if r['similar'])}/{total}
""")

    # Casos donde BGE difiere de DB
    print("=" * 90)
    print("CASOS DONDE BGE-M3 DIFIERE DE DB")
    print("=" * 90)
    diferentes = [r for r in resultados if not r['similar']]
    if diferentes:
        for r in diferentes:
            print(f"\n  ID: {r['id_oferta']}")
            print(f"  Titulo: {r['titulo'][:50]}")
            print(f"  BGE asigna: {r['bge_label']} (score: {r['bge_score']:.3f})")
            print(f"  DB tiene: {r['db_label']}")
            print(f"  Gold OK: {'Si' if r['gold_ok'] else 'No'}")
            print(f"  Comentario: {r['comentario'][:80]}")
    else:
        print("  BGE-M3 coincide con DB en todos los casos")

    # Errores conocidos del Gold Set
    print()
    print("=" * 90)
    print("ERRORES CONOCIDOS (gold_ok=False)")
    print("=" * 90)
    errores = [r for r in resultados if not r['gold_ok']]
    if errores:
        for r in errores:
            print(f"\n  ID: {r['id_oferta']}")
            print(f"  Titulo: {r['titulo'][:50]}")
            print(f"  BGE asigna: {r['bge_label']}")
            print(f"  DB tiene: {r['db_label']}")
            print(f"  Comentario: {r['comentario'][:100]}")
    else:
        print("  Ningun error conocido")

    return resultados


if __name__ == "__main__":
    run_validacion()
