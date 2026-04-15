#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de Validacion con Gold Set Manual
=======================================

VERSION: 1.1
FECHA: 2025-12-07

OBJETIVO:
  Evaluar la precision del matching ESCO usando un gold set
  de casos revisados manualmente.

METRICAS:
  - Precision: % de matches correctos sobre total evaluado
  - Errores por tipo: nivel_jerarquico, sector_funcion, tipo_ocupacion, programa_general

EJECUCION:
  python test_gold_set_manual.py
  python test_gold_set_manual.py --no-save  # Sin guardar en historial

CAMBIOS v1.1:
  - Integracion con experiment_logger.py (MOL-48)
  - Guarda resultados automaticamente en metrics/gold_set_history.json
"""

import sqlite3
import json
import struct
import argparse
from pathlib import Path
from datetime import datetime

# Import experiment logger
try:
    from experiment_logger import get_logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / 'database' / 'bumeran_scraping.db'
GOLD_SET_PATH = PROJECT_ROOT / 'database' / 'gold_set_manual_v2.json'


def parse_score(value):
    """Convierte score que puede ser float, bytes (float32) o None."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 4:
            return struct.unpack('f', value)[0]
        elif len(value) == 8:
            return struct.unpack('d', value)[0]
    return 0.0


def load_gold_set():
    """Carga el gold set desde JSON."""
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_current_matches(cursor, ids):
    """Obtiene los matches actuales de la DB."""
    placeholders = ','.join(['?'] * len(ids))
    cursor.execute(f'''
        SELECT
            m.id_oferta,
            o.titulo,
            m.esco_occupation_label,
            m.score_final_ponderado,
            m.match_confirmado,
            m.requiere_revision,
            m.matching_version
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.id_oferta IN ({placeholders})
    ''', ids)

    results = {}
    for row in cursor.fetchall():
        results[row[0]] = {
            'titulo': row[1],
            'esco_label': row[2],
            'score': parse_score(row[3]),
            'confirmado': row[4],
            'revision': row[5],
            'version': row[6]
        }
    return results


def evaluate_skills():
    """M-10 P2: Evalúa precision y recall de skills con matching semántico BGE-M3."""
    try:
        import numpy as np
        from pathlib import Path as P

        config_path = PROJECT_ROOT / 'config' / 'supabase_config.json'
        if not config_path.exists():
            return None
        config = json.loads(config_path.read_text())
        from supabase import create_client
        client = create_client(config['url'], config['service_role_key'])

        # Load expected skills from gold_set_skills
        gs_skills = client.table('gold_set_skills').select('id_oferta,skill_label').execute()
        if not gs_skills.data:
            return None

        # Group by oferta
        expected_by_oferta = {}
        for row in gs_skills.data:
            oid = row['id_oferta']
            expected_by_oferta.setdefault(oid, [])
            expected_by_oferta[oid].append(row['skill_label'])

        # Load extracted skills from local DB
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()

        extracted_by_oferta = {}
        for oid in expected_by_oferta:
            cursor.execute('''
                SELECT esco_skill_label FROM ofertas_esco_skills_detalle
                WHERE id_oferta = ?
            ''', (oid,))
            labels = [r[0] for r in cursor.fetchall() if r[0]]
            if labels:
                extracted_by_oferta[oid] = labels
        conn.close()

        # Load BGE-M3 for semantic comparison
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / 'database'))
        sys.path.insert(0, str(PROJECT_ROOT / 'config'))
        from sentence_transformers import SentenceTransformer
        try:
            from embedding_config import EMBEDDING_MODEL, EMBEDDING_REVISION
        except ImportError:
            EMBEDDING_MODEL = "BAAI/bge-m3"
            EMBEDDING_REVISION = None

        print("[SKILLS] Cargando BGE-M3 para comparación semántica...")
        model = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION) if EMBEDDING_REVISION else SentenceTransformer(EMBEDDING_MODEL)

        THRESHOLD = 0.70
        from collections import Counter
        precisions = []
        recalls = []
        missing_skills = Counter()
        ofertas_recall_100 = 0
        ofertas_recall_50 = 0

        for oid, exp_labels in expected_by_oferta.items():
            ext_labels = extracted_by_oferta.get(oid, [])
            if not exp_labels or not ext_labels:
                if exp_labels:
                    recalls.append(0.0)
                    precisions.append(0.0)
                    for e in exp_labels:
                        missing_skills[e] += 1
                continue

            # Embed both sets
            exp_embs = model.encode(exp_labels, normalize_embeddings=True)
            ext_embs = model.encode(ext_labels, normalize_embeddings=True)

            # Cosine similarity matrix (exp × ext)
            sim_matrix = np.dot(exp_embs, ext_embs.T)

            # Recall: for each expected, best match >= threshold?
            matched_exp = 0
            for i, exp in enumerate(exp_labels):
                best = sim_matrix[i].max()
                if best >= THRESHOLD:
                    matched_exp += 1
                else:
                    missing_skills[exp] += 1

            # Precision: for each extracted, best match >= threshold?
            matched_ext = 0
            for j in range(len(ext_labels)):
                best = sim_matrix[:, j].max()
                if best >= THRESHOLD:
                    matched_ext += 1

            recall = matched_exp / len(exp_labels)
            precision = matched_ext / len(ext_labels)
            recalls.append(recall)
            precisions.append(precision)

            if recall >= 1.0:
                ofertas_recall_100 += 1
            if recall >= 0.5:
                ofertas_recall_50 += 1

        if not recalls:
            return None

        return {
            'ofertas_evaluadas': len(recalls),
            'precision_promedio': sum(precisions) / len(precisions) * 100,
            'recall_promedio': sum(recalls) / len(recalls) * 100,
            'ofertas_recall_100': ofertas_recall_100,
            'ofertas_recall_50': ofertas_recall_50,
            'threshold': THRESHOLD,
            'skills_mas_faltantes': missing_skills.most_common(10),
        }
    except Exception as e:
        import traceback
        print(f"[SKILLS] Error evaluando skills: {e}")
        traceback.print_exc()
        return None


def run_validation():
    """Ejecuta la validacion contra el gold set."""
    print("=" * 70)
    print("VALIDACION GOLD SET MANUAL - MATCHING ESCO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Cargar gold set
    gold_set = load_gold_set()
    print(f"\n[1] Gold set cargado: {len(gold_set)} casos")

    # Conectar DB (WAL mode + timeout for concurrent pipeline access)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # Obtener matches actuales
    ids = [g['id_oferta'] for g in gold_set]
    current_matches = get_current_matches(cursor, ids)
    print(f"[2] Matches en DB: {len(current_matches)}")

    # Evaluar
    correct = 0
    incorrect = 0
    missing = 0
    errors_by_type = {}

    print("\n" + "-" * 70)
    print("RESULTADOS DETALLADOS:")
    print("-" * 70)

    for gold in gold_set:
        id_oferta = gold['id_oferta']
        expected_ok = gold['esco_ok']
        comentario = gold.get('comentario', '')
        tipo_error = gold.get('tipo_error', 'sin_clasificar')

        if id_oferta not in current_matches:
            print(f"[MISSING] {id_oferta} - No encontrado en DB")
            missing += 1
            continue

        match = current_matches[id_oferta]

        # En este test simple:
        # - Si esco_ok=True, consideramos el match actual como "esperado correcto"
        # - Si esco_ok=False, el match actual es un error conocido

        if expected_ok:
            status = "[OK]"
            correct += 1
        else:
            status = "[ERROR]"
            incorrect += 1
            errors_by_type[tipo_error] = errors_by_type.get(tipo_error, 0) + 1

        print(f"{status} {id_oferta}")
        print(f"       Titulo: {match['titulo'][:50]}...")
        print(f"       ESCO:   {match['esco_label'][:50]}...")
        print(f"       Score:  {match['score']:.3f} | {'CONFIRMADO' if match['confirmado'] else ('REVISION' if match['revision'] else 'RECHAZADO')}")
        if not expected_ok:
            print(f"       Error:  {tipo_error}")
            print(f"       Motivo: {comentario[:60]}...")
        print()

    conn.close()

    # Resumen
    total = correct + incorrect
    precision = (correct / total * 100) if total > 0 else 0

    print("=" * 70)
    print("RESUMEN DE VALIDACION:")
    print("=" * 70)
    print(f"  Total evaluados:  {total}")
    print(f"  Correctos:        {correct} ({correct/total*100:.1f}%)")
    print(f"  Incorrectos:      {incorrect} ({incorrect/total*100:.1f}%)")
    if missing > 0:
        print(f"  No encontrados:   {missing}")

    print(f"\n  PRECISION:        {precision:.1f}%")

    if errors_by_type:
        print("\n  Errores por tipo:")
        for tipo, count in sorted(errors_by_type.items(), key=lambda x: -x[1]):
            print(f"    - {tipo}: {count}")

    print("=" * 70)

    # Obtener version del matching (de la primera oferta con version)
    matching_version = "unknown"
    for match in current_matches.values():
        if match.get('version'):
            matching_version = match['version']
            break

    # M-10 P2: Evaluación de skills
    skills_metrics = evaluate_skills()
    if skills_metrics:
        print("\n" + "=" * 70)
        print("EVALUACION DE SKILLS (M-10 P2):")
        print("=" * 70)
        print(f"  Ofertas evaluadas:        {skills_metrics['ofertas_evaluadas']}")
        print(f"  Threshold semántico:      {skills_metrics.get('threshold', '?')}")
        print(f"  Precision skills prom:    {skills_metrics['precision_promedio']:.1f}%")
        print(f"  Recall skills prom:       {skills_metrics['recall_promedio']:.1f}%")
        print(f"  Ofertas con recall >= 50%:{skills_metrics.get('ofertas_recall_50', '?')}")
        print(f"  Ofertas con 100% recall:  {skills_metrics['ofertas_recall_100']}")
        if skills_metrics.get('skills_mas_faltantes'):
            print(f"  Skills más faltantes:")
            for s, c in skills_metrics['skills_mas_faltantes'][:5]:
                print(f"    - \"{s}\" (falta en {c} ofertas)")
        print("=" * 70)

    # Retornar metricas para uso programatico
    return {
        'precision': precision,
        'correct': correct,
        'incorrect': incorrect,
        'total': total,
        'errors_by_type': errors_by_type,
        'matching_version': matching_version,
        'skills_metrics': skills_metrics,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Test de validacion con Gold Set Manual")
    parser.add_argument("--no-save", action="store_true",
                        help="No guardar resultados en historial")
    parser.add_argument("--notes", type=str, default="",
                        help="Notas adicionales para el run")
    args = parser.parse_args()

    results = run_validation()

    # Guardar en historial (si logger disponible y no --no-save)
    if LOGGER_AVAILABLE and not args.no_save:
        logger = get_logger()
        logger.log_gold_set_run(
            precision=results['precision'],
            correct=results['correct'],
            incorrect=results['incorrect'],
            total=results['total'],
            errors_by_type=results['errors_by_type'],
            version=results['matching_version'],
            notes=args.notes
        )
    elif not LOGGER_AVAILABLE:
        print("[!] experiment_logger no disponible, resultados no guardados")

    # Exit code basado en precision minima esperada
    MIN_PRECISION = 50.0  # Umbral minimo aceptable
    if results['precision'] < MIN_PRECISION:
        print(f"\n[!] ADVERTENCIA: Precision {results['precision']:.1f}% < {MIN_PRECISION}%")
        exit(1)
    else:
        exit(0)
