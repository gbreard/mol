#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Gold Set para Matching v2.1 con BGE-M3.

Compara resultados de:
- v2.0 (fuzzy - FALLIDO: 0% success)
- v2.1 BGE-M3 (semantic)
- v8.3 (baseline de referencia)

Ejecutar: python test_gold_set_v21_bge.py
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent))

# Verificar dependencias
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"ERROR: Falta dependencia: {e}")
    print("Instalar: pip install sentence-transformers numpy")
    sys.exit(1)

# Paths
DB_PATH = Path(__file__).parent / "bumeran_scraping.db"
GOLD_SET_PATH = Path(__file__).parent / "gold_set_manual_v1.json"
EMBEDDINGS_DIR = Path(__file__).parent / "embeddings"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "matching_config.json"


class SemanticMatcherTest:
    """Matcher semántico para test con BGE-M3."""

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
        """Carga modelo y embeddings pre-calculados."""
        if self.loaded:
            return

        print("  Cargando modelo BGE-M3...")
        self.model = SentenceTransformer('BAAI/bge-m3')

        # Cargar embeddings pre-calculados de ESCO
        emb_path = EMBEDDINGS_DIR / "esco_occupations_embeddings.npy"
        meta_path = EMBEDDINGS_DIR / "esco_occupations_metadata.json"

        if not emb_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"Embeddings no encontrados en {EMBEDDINGS_DIR}")

        print("  Cargando embeddings ESCO pre-calculados...")
        self.esco_embeddings = np.load(str(emb_path))
        with open(meta_path, 'r', encoding='utf-8') as f:
            self.esco_metadata = json.load(f)

        print(f"  Embeddings cargados: {len(self.esco_metadata)} ocupaciones")
        self.loaded = True

    def encode(self, text: str) -> np.ndarray:
        """Genera embedding para texto."""
        return self.model.encode(text, normalize_embeddings=True)

    def search(self, query: str, top_k: int = 5, isco_filter: list = None) -> list:
        """Búsqueda semántica en ocupaciones ESCO."""
        if not self.loaded:
            self.load()

        # Generar embedding de la query
        query_emb = self.encode(query)

        # Calcular similitud coseno con todas las ocupaciones
        similarities = np.dot(self.esco_embeddings, query_emb)

        # Crear lista de resultados con scores
        results = []
        for i, (meta, sim) in enumerate(zip(self.esco_metadata, similarities)):
            # Aplicar filtro ISCO si se especifica
            if isco_filter:
                isco_code = meta.get('isco_code', '')
                if not any(isco_code.startswith(f) for f in isco_filter):
                    continue

            results.append({
                'esco_code': meta.get('esco_code', ''),
                'isco_code': meta.get('isco_code', ''),
                'preferred_label': meta.get('preferred_label', ''),
                'score': float(sim),
                'source': 'bge_m3_semantic'
            })

        # Ordenar por score descendente
        results.sort(key=lambda x: x['score'], reverse=True)

        return results[:top_k]


def cargar_gold_set() -> list:
    """Carga el gold set."""
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def cargar_oferta_nlp(id_oferta: str) -> dict:
    """Carga datos NLP de una oferta."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            o.id_oferta,
            o.titulo,
            o.descripcion,
            n.titulo_normalizado,
            n.area_funcional,
            n.nivel_seniority,
            n.tipo_contrato,
            n.tareas_explicitas,
            n.skills_tecnicas_list,
            n.tecnologias_list,
            n.mision_rol
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.id_oferta = ?
    """, (id_oferta,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def construir_query_semantica(oferta_nlp: dict) -> str:
    """Construye query semántica rica a partir de datos NLP."""
    partes = []

    # Título (siempre presente)
    titulo = oferta_nlp.get('titulo_normalizado') or oferta_nlp.get('titulo', '')
    if titulo:
        partes.append(titulo)

    # Tareas explícitas
    tareas_raw = oferta_nlp.get('tareas_explicitas', '')
    if tareas_raw:
        try:
            tareas = json.loads(tareas_raw) if isinstance(tareas_raw, str) else tareas_raw
            if isinstance(tareas, list) and tareas:
                partes.append('. '.join(tareas[:5]))  # Max 5 tareas
        except:
            pass

    # Skills técnicas
    skills_raw = oferta_nlp.get('skills_tecnicas_list', '')
    if skills_raw:
        try:
            skills = json.loads(skills_raw) if isinstance(skills_raw, str) else skills_raw
            if isinstance(skills, list) and skills:
                partes.append(', '.join(skills[:10]))  # Max 10 skills
        except:
            pass

    # Tecnologías
    tecno_raw = oferta_nlp.get('tecnologias_list', '')
    if tecno_raw:
        try:
            tecno = json.loads(tecno_raw) if isinstance(tecno_raw, str) else tecno_raw
            if isinstance(tecno, list) and tecno:
                partes.append(', '.join(tecno[:10]))
        except:
            pass

    # Misión del rol
    mision = oferta_nlp.get('mision_rol', '')
    if mision and len(mision) > 10:
        partes.append(mision[:200])  # Truncar misión

    return '. '.join(partes)


def cargar_match_v83(id_oferta: str) -> dict:
    """Carga el match existente de v8.3 (baseline)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            esco_occupation_uri as esco_code,
            esco_occupation_label as esco_label,
            occupation_match_score as score,
            occupation_match_method as metodo,
            matching_version
        FROM ofertas_esco_matching
        WHERE id_oferta = ?
        ORDER BY occupation_match_score DESC
        LIMIT 1
    """, (id_oferta,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def run_test():
    """Ejecuta test completo del Gold Set con v2.1 BGE-M3."""
    print("=" * 70)
    print("TEST GOLD SET - MATCHING v2.1 BGE-M3")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Cargar gold set
    gold_set = cargar_gold_set()
    print(f"Gold Set: {len(gold_set)} casos")

    # Cargar config
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"Config version: {config.get('version', 'unknown')}")

    threshold = config.get('filtros', {}).get('score_minimo_final', 0.50)
    print(f"Threshold: {threshold}")
    print()

    # Inicializar matcher
    matcher = SemanticMatcherTest.get_instance()
    matcher.load()
    print()

    # Resultados
    resultados = []
    v21_success = 0
    v21_total = 0
    v83_success = 0

    print("-" * 70)
    print(f"{'ID':<12} {'Titulo':<25} {'v2.1 Score':<10} {'v2.1 Match':<20} {'Status'}")
    print("-" * 70)

    for caso in gold_set:
        id_oferta = caso['id_oferta']
        esco_ok = caso.get('esco_ok', False)

        # Cargar datos NLP
        oferta = cargar_oferta_nlp(id_oferta)
        if not oferta:
            print(f"{id_oferta:<12} {'NO NLP DATA':<25} {'-':<10} {'-':<20} SKIP")
            continue

        v21_total += 1

        # Construir query semántica
        query = construir_query_semantica(oferta)

        # Búsqueda BGE-M3
        matches = matcher.search(query, top_k=3)

        if matches:
            best = matches[0]
            score = best['score']
            label = best['preferred_label'][:20]

            # Determinar status
            passed = score >= threshold
            if passed:
                v21_success += 1
                status = "[OK] PASS" if esco_ok else "[!] PASS (gold=F)"
            else:
                status = "[X] FAIL" if esco_ok else "[X] FAIL (gold=F)"
        else:
            score = 0.0
            label = "NO MATCH"
            status = "[X] NO MATCH"

        # Cargar v8.3 para comparación
        v83 = cargar_match_v83(id_oferta)
        if v83 and v83.get('score', 0) > 0:
            v83_success += 1

        titulo = (oferta.get('titulo_normalizado') or oferta.get('titulo', ''))[:25]
        print(f"{id_oferta:<12} {titulo:<25} {score:<10.3f} {label:<20} {status}")

        resultados.append({
            'id_oferta': id_oferta,
            'titulo': oferta.get('titulo', ''),
            'gold_esco_ok': esco_ok,
            'v21_score': score,
            'v21_match': best['preferred_label'] if matches else None,
            'v21_passed': score >= threshold,
            'v83_score': v83.get('score') if v83 else None,
            'v83_match': v83.get('esco_label') if v83 else None
        })

    # Resumen
    print("-" * 70)
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)

    pct_v21 = (v21_success / v21_total * 100) if v21_total > 0 else 0
    pct_v83 = (v83_success / v21_total * 100) if v21_total > 0 else 0

    print(f"""
Matching v2.1 BGE-M3:
  - Total procesados: {v21_total}
  - Pasaron threshold ({threshold}): {v21_success}
  - Precisión: {pct_v21:.1f}%

Comparación con v8.3 (baseline):
  - Con match existente: {v83_success}/{v21_total}
  - Precisión v8.3: {pct_v83:.1f}%

Mejora v2.1 vs v2.0 fuzzy:
  - v2.0 fuzzy: 0% (todos fallaron por ESCO sin tasks/skills)
  - v2.1 BGE-M3: {pct_v21:.1f}%
  - Mejora: +{pct_v21:.1f} puntos porcentuales
""")

    # Detalle de scores
    print("=" * 70)
    print("DISTRIBUCIÓN DE SCORES v2.1")
    print("=" * 70)

    scores = [r['v21_score'] for r in resultados if r['v21_score'] is not None]
    if scores:
        print(f"  Min score: {min(scores):.3f}")
        print(f"  Max score: {max(scores):.3f}")
        print(f"  Promedio: {sum(scores)/len(scores):.3f}")

        # Distribución por rangos
        ranges = [(0.7, 1.0), (0.6, 0.7), (0.5, 0.6), (0.4, 0.5), (0.0, 0.4)]
        print("\n  Distribución por rango:")
        for low, high in ranges:
            count = sum(1 for s in scores if low <= s < high)
            pct = count / len(scores) * 100
            bar = "█" * int(pct / 5)
            print(f"    [{low:.1f}-{high:.1f}): {count:2d} ({pct:5.1f}%) {bar}")

    # Top matches
    print()
    print("=" * 70)
    print("TOP 5 MEJORES MATCHES v2.1")
    print("=" * 70)
    top5 = sorted(resultados, key=lambda x: x.get('v21_score', 0), reverse=True)[:5]
    for r in top5:
        print(f"  {r['id_oferta']}: {r['v21_score']:.3f} -> {r.get('v21_match', 'N/A')[:40]}")

    # Casos problemáticos
    print()
    print("=" * 70)
    print("CASOS QUE NECESITAN REVISIÓN")
    print("=" * 70)
    problemas = [r for r in resultados if r.get('v21_score', 0) < threshold and r.get('gold_esco_ok', False)]
    if problemas:
        for r in problemas:
            print(f"  {r['id_oferta']}: score={r['v21_score']:.3f}, gold=OK pero no pasó threshold")
    else:
        print("  Ninguno - todos los gold=OK pasaron el threshold")

    return resultados


if __name__ == "__main__":
    run_test()
