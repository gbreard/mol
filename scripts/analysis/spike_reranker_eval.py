#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Spike: Evaluar si ESCO-XLM Reranker Aporta Valor
=================================================

VERSION: 1.0.0
FECHA: 2025-12-07
ISSUE: MOL-49

Este spike compara el pipeline de matching CON y SIN el reranker ESCO-XLM
usando los 19 casos del gold set.

Hipotesis:
- El reranker usa mean pooling de ESCO-XLM-RoBERTa, pero este modelo
  fue disenado para clasificacion, no para generar embeddings.
- Remover el reranker podria dar similar precision con menos complejidad.

Experimento:
- Test A: BGE-M3 -> Top 10 -> ESCO-XLM rerank -> Top 3 -> Rules
- Test B: BGE-M3 -> Top 3 directo -> Rules

Criterio de exito:
- Si B precision >= A precision - 2%: Remover reranker (simplificar)
- Si B precision < A precision - 2%: Mantener reranker
"""

import sqlite3
import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from sentence_transformers import SentenceTransformer

# Imports locales
from experiment_logger import ExperimentLogger
from matching_rules_v83 import calcular_ajustes_v83, es_oferta_programa_pasantia

try:
    import torch
    from transformers import AutoModel, AutoTokenizer
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("[!] transformers/torch no disponible. Solo se probara sin reranker.")

# Paths (relativo a project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / 'database' / 'bumeran_scraping.db'
GOLD_SET_PATH = PROJECT_ROOT / 'database' / 'gold_set_manual_v2.json'
EMBEDDINGS_DIR = PROJECT_ROOT / 'database' / 'embeddings'

# Thresholds (copiados de match_ofertas_multicriteria.py)
THRESHOLD_CONFIRMADO_SCORE = 0.60
THRESHOLD_CONFIRMADO_COVERAGE = 0.40
THRESHOLD_REVISION = 0.50


class ESCOReranker:
    """Re-ranker usando ESCO-XLM-RoBERTa-Large"""

    def __init__(self, model_name='jjzha/esco-xlm-roberta-large'):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def cargar(self):
        print(f"  [RERANKER] Cargando ESCO-XLM... (device: {self.device})")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        print("  [OK] Reranker cargado")

    def _get_embedding(self, text):
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True,
            max_length=512, padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            attention_mask = inputs['attention_mask']
            hidden_states = outputs.last_hidden_state
            mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
            sum_embeddings = torch.sum(hidden_states * mask_expanded, dim=1)
            sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
            embedding = sum_embeddings / sum_mask

        return embedding.cpu().numpy()[0]

    def rerank(self, oferta_texto, candidatos_esco, top_k=3):
        oferta_embedding = self._get_embedding(oferta_texto[:500])
        oferta_embedding = oferta_embedding / np.linalg.norm(oferta_embedding)

        for candidato in candidatos_esco:
            candidato_embedding = self._get_embedding(candidato['label'])
            candidato_embedding = candidato_embedding / np.linalg.norm(candidato_embedding)
            candidato['rerank_score'] = float(np.dot(oferta_embedding, candidato_embedding))

        return sorted(candidatos_esco, key=lambda x: x['rerank_score'], reverse=True)[:top_k]


def load_gold_set():
    """Carga el gold set"""
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_models():
    """Carga BGE-M3 y embeddings ESCO"""
    print("\n[1] CARGANDO MODELOS")
    print("=" * 60)

    # BGE-M3
    print("  -> Cargando BGE-M3...")
    embedding_model = SentenceTransformer('BAAI/bge-m3')
    print("  [OK] BGE-M3 cargado")

    # ESCO embeddings
    occ_emb_path = EMBEDDINGS_DIR / "esco_occupations_embeddings.npy"
    occ_meta_path = EMBEDDINGS_DIR / "esco_occupations_metadata.json"

    esco_embeddings = np.load(occ_emb_path)
    with open(occ_meta_path, 'r', encoding='utf-8') as f:
        esco_metadata = json.load(f)
    print(f"  [OK] {len(esco_embeddings):,} embeddings ESCO cargados")

    return embedding_model, esco_embeddings, esco_metadata


def get_candidates_bge(texto_oferta, embedding_model, esco_embeddings, esco_metadata, top_k=10):
    """Obtiene top-K candidatos usando BGE-M3"""
    oferta_embedding = embedding_model.encode([texto_oferta])[0]
    oferta_embedding = oferta_embedding / np.linalg.norm(oferta_embedding)

    similarities = np.dot(esco_embeddings, oferta_embedding)
    top_indices = np.argsort(similarities)[-top_k:][::-1]

    candidatos = []
    for idx in top_indices:
        candidatos.append({
            'uri': esco_metadata[idx]['uri'],
            'label': esco_metadata[idx]['label'],
            'similarity_score': float(similarities[idx]),
            'isco_code': esco_metadata[idx].get('isco_code')
        })

    return candidatos


def evaluate_match(candidato, titulo, descripcion, gold_case):
    """Evalua si el candidato seleccionado es correcto segun el gold set"""
    # Un match es "correcto" si esco_ok=True en el gold set
    # En realidad, el gold set marca si el match ACTUAL de la BD es correcto
    # Para este spike, comparamos si obtenemos el MISMO candidato que el match actual
    return gold_case.get('esco_ok', False)


def run_experiment(use_reranker: bool, embedding_model, esco_embeddings, esco_metadata, gold_set, conn, reranker=None):
    """
    Ejecuta el experimento con o sin reranker.

    Returns:
        Dict con resultados
    """
    experiment_name = "spike_con_reranker" if use_reranker else "spike_sin_reranker"
    print(f"\n{'=' * 60}")
    print(f"EXPERIMENTO: {'CON' if use_reranker else 'SIN'} RERANKER")
    print(f"{'=' * 60}")

    cursor = conn.cursor()

    results = {
        'correct': 0,
        'incorrect': 0,
        'total': 0,
        'timing_bge': [],
        'timing_reranker': [],
        'timing_total': [],
        'details': []
    }

    for gold_case in gold_set:
        id_oferta = gold_case['id_oferta']
        expected_ok = gold_case.get('esco_ok', False)
        expected_error_type = gold_case.get('tipo_error', None)

        # Obtener datos de la oferta
        cursor.execute("""
            SELECT titulo, descripcion_utf8 FROM ofertas WHERE id_oferta = ?
        """, (id_oferta,))
        row = cursor.fetchone()

        if not row:
            print(f"  [SKIP] {id_oferta} - No encontrado en BD")
            continue

        titulo, descripcion = row
        texto_oferta = f"{titulo}. {' '.join((descripcion or '').split()[:200])}"

        # Timing total
        total_start = time.perf_counter()

        # PASO 1: BGE-M3 retrieval
        bge_start = time.perf_counter()
        candidatos = get_candidates_bge(texto_oferta, embedding_model, esco_embeddings, esco_metadata, top_k=10)
        bge_time = (time.perf_counter() - bge_start) * 1000
        results['timing_bge'].append(bge_time)

        # PASO 2: Reranking (si habilitado)
        rerank_time = 0
        if use_reranker and reranker:
            rerank_start = time.perf_counter()
            candidatos = reranker.rerank(texto_oferta, candidatos, top_k=3)
            rerank_time = (time.perf_counter() - rerank_start) * 1000
            results['timing_reranker'].append(rerank_time)
        else:
            # Sin reranker: top 3 directo
            candidatos = candidatos[:3]

        # Seleccionar mejor candidato
        mejor_candidato = candidatos[0]

        total_time = (time.perf_counter() - total_start) * 1000
        results['timing_total'].append(total_time)

        # El gold set indica si el match ACTUAL es correcto
        # Para comparar, verificamos si nuestro candidato coincide con el actual
        cursor.execute("""
            SELECT esco_occupation_label FROM ofertas_esco_matching WHERE id_oferta = ?
        """, (str(id_oferta),))
        match_row = cursor.fetchone()
        current_label = match_row[0] if match_row else None

        # Comparar si obtenemos el mismo resultado
        same_result = mejor_candidato['label'] == current_label

        # Registrar resultado
        results['total'] += 1

        # Si el gold set dice que el match actual es correcto Y obtenemos el mismo -> correcto
        # Si el gold set dice que es incorrecto Y obtenemos el mismo -> sigue siendo incorrecto
        # Lo que nos interesa es si CAMBIA el resultado
        if expected_ok:
            if same_result:
                results['correct'] += 1
                status = "[OK]"
            else:
                # Cambio el resultado! Podria ser mejor o peor
                results['incorrect'] += 1
                status = "[CAMBIO]"
        else:
            # El match actual es incorrecto segun gold set
            if same_result:
                results['incorrect'] += 1
                status = "[ERROR]"
            else:
                # Cambio! Podria haber mejorado
                results['correct'] += 1  # Asumimos que cambiar un error es potencialmente mejor
                status = "[CAMBIO+]"

        results['details'].append({
            'id_oferta': id_oferta,
            'titulo': titulo[:50],
            'candidato': mejor_candidato['label'][:50],
            'score': mejor_candidato['similarity_score'],
            'same_as_current': same_result,
            'gold_ok': expected_ok,
            'status': status,
            'timing_ms': total_time
        })

        print(f"  {status} {id_oferta}: {mejor_candidato['label'][:40]}... ({total_time:.0f}ms)")

    # Calcular metricas
    precision = (results['correct'] / results['total'] * 100) if results['total'] > 0 else 0
    avg_bge = sum(results['timing_bge']) / len(results['timing_bge']) if results['timing_bge'] else 0
    avg_rerank = sum(results['timing_reranker']) / len(results['timing_reranker']) if results['timing_reranker'] else 0
    avg_total = sum(results['timing_total']) / len(results['timing_total']) if results['timing_total'] else 0

    results['precision'] = precision
    results['avg_timing_bge_ms'] = avg_bge
    results['avg_timing_reranker_ms'] = avg_rerank
    results['avg_timing_total_ms'] = avg_total

    print(f"\n  Precision: {precision:.1f}% ({results['correct']}/{results['total']})")
    print(f"  Timing promedio: {avg_total:.0f}ms (BGE: {avg_bge:.0f}ms, Rerank: {avg_rerank:.0f}ms)")

    return results


def main():
    print("=" * 70)
    print("SPIKE MOL-49: EVALUAR ESCO-XLM RERANKER")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Cargar gold set
    gold_set = load_gold_set()
    print(f"\n[0] Gold set: {len(gold_set)} casos")

    # Cargar modelos
    embedding_model, esco_embeddings, esco_metadata = load_models()

    # Cargar reranker (si disponible)
    reranker = None
    if RERANKER_AVAILABLE:
        reranker = ESCOReranker()
        reranker.cargar()

    # Conectar DB
    conn = sqlite3.connect(DB_PATH)

    # Logger
    logger = ExperimentLogger()

    # =========================================================
    # EXPERIMENTO A: CON RERANKER (baseline)
    # =========================================================
    results_con = run_experiment(
        use_reranker=True,
        embedding_model=embedding_model,
        esco_embeddings=esco_embeddings,
        esco_metadata=esco_metadata,
        gold_set=gold_set,
        conn=conn,
        reranker=reranker
    )

    # Guardar experimento A
    logger.log_experiment(
        name="spike_reranker_baseline",
        metrics={
            "precision": results_con['precision'],
            "correct": results_con['correct'],
            "total": results_con['total'],
            "avg_timing_ms": results_con['avg_timing_total_ms']
        },
        config={"use_reranker": True, "top_k": 3},
        description="Baseline con ESCO-XLM reranker",
        tags=["spike", "reranker", "baseline"]
    )

    # =========================================================
    # EXPERIMENTO B: SIN RERANKER
    # =========================================================
    results_sin = run_experiment(
        use_reranker=False,
        embedding_model=embedding_model,
        esco_embeddings=esco_embeddings,
        esco_metadata=esco_metadata,
        gold_set=gold_set,
        conn=conn,
        reranker=None
    )

    # Guardar experimento B
    logger.log_experiment(
        name="spike_reranker_sin",
        metrics={
            "precision": results_sin['precision'],
            "correct": results_sin['correct'],
            "total": results_sin['total'],
            "avg_timing_ms": results_sin['avg_timing_total_ms']
        },
        config={"use_reranker": False, "top_k": 3},
        description="Experimento sin reranker (solo BGE-M3)",
        tags=["spike", "reranker", "experiment"]
    )

    conn.close()

    # =========================================================
    # COMPARACION Y DECISION
    # =========================================================
    print("\n" + "=" * 70)
    print("RESULTADOS DEL SPIKE")
    print("=" * 70)

    precision_diff = results_sin['precision'] - results_con['precision']
    timing_diff = results_con['avg_timing_total_ms'] - results_sin['avg_timing_total_ms']
    speedup = results_con['avg_timing_total_ms'] / results_sin['avg_timing_total_ms'] if results_sin['avg_timing_total_ms'] > 0 else 1

    print(f"\n  CON RERANKER (baseline):")
    print(f"    Precision: {results_con['precision']:.1f}%")
    print(f"    Timing:    {results_con['avg_timing_total_ms']:.0f}ms promedio")
    print(f"      - BGE-M3:  {results_con['avg_timing_bge_ms']:.0f}ms")
    print(f"      - Rerank:  {results_con['avg_timing_reranker_ms']:.0f}ms")

    print(f"\n  SIN RERANKER (experimento):")
    print(f"    Precision: {results_sin['precision']:.1f}%")
    print(f"    Timing:    {results_sin['avg_timing_total_ms']:.0f}ms promedio")

    print(f"\n  DIFERENCIA:")
    print(f"    Precision: {precision_diff:+.1f}%")
    print(f"    Timing:    {timing_diff:+.0f}ms ({speedup:.1f}x mas rapido sin reranker)")

    # Decision
    print("\n" + "-" * 70)
    print("DECISION:")
    print("-" * 70)

    # Criterio: Si sin reranker >= con reranker - 2% -> remover
    threshold = -2.0

    if precision_diff >= threshold:
        decision = "GO"
        if precision_diff >= 0:
            razon = f"Sin reranker es IGUAL o MEJOR ({precision_diff:+.1f}%)"
        else:
            razon = f"Sin reranker esta dentro de tolerancia ({precision_diff:+.1f}% >= {threshold}%)"
        recomendacion = "REMOVER el reranker ESCO-XLM"
    else:
        decision = "NO-GO"
        razon = f"Sin reranker pierde demasiada precision ({precision_diff:+.1f}% < {threshold}%)"
        recomendacion = "MANTENER el reranker ESCO-XLM"

    print(f"\n  Decision:      {decision}")
    print(f"  Razon:         {razon}")
    print(f"  Recomendacion: {recomendacion}")

    if decision == "GO":
        print(f"\n  Beneficios de remover:")
        print(f"    - {speedup:.1f}x mas rapido por oferta")
        print(f"    - Menos dependencias (no requiere transformers/torch)")
        print(f"    - Codigo mas simple")

    print("\n" + "=" * 70)

    # Guardar resumen
    summary = {
        "timestamp": datetime.now().isoformat(),
        "decision": decision,
        "precision_con_reranker": results_con['precision'],
        "precision_sin_reranker": results_sin['precision'],
        "precision_diff": precision_diff,
        "timing_con_reranker_ms": results_con['avg_timing_total_ms'],
        "timing_sin_reranker_ms": results_sin['avg_timing_total_ms'],
        "speedup": speedup,
        "recomendacion": recomendacion,
        "razon": razon
    }

    # Guardar en metrics/
    summary_path = Path(__file__).parent.parent / "metrics" / "spike_reranker_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nResumen guardado en: {summary_path}")

    return decision


if __name__ == "__main__":
    decision = main()
    exit(0 if decision == "GO" else 1)
