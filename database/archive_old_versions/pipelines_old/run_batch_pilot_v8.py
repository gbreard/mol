#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch Piloto v8.0 - ESCO Multicriterio Calibrado
================================================

VERSION: 8.0
FECHA: 2025-11-28

OBJETIVO:
  Procesar un lote piloto de ofertas (200) con el algoritmo multicriterio v8.0
  y generar estadísticas de distribución para calibración de umbrales.

EJECUCIÓN:
  python run_batch_pilot_v8.py [--limit N]

OUTPUT:
  - Estadísticas: min, max, p25, p50, p75 de score_final_ponderado
  - Conteo por categoría: CONFIRMADO, REVISION, RECHAZADO
  - 10 ejemplos de cada categoría
"""

import sqlite3
import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Configuración
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
EMBEDDINGS_DIR = Path(__file__).parent / 'embeddings'

# Pesos del algoritmo
PESO_TITULO = 0.50
PESO_SKILLS = 0.40
PESO_DESCRIPCION = 0.10

# Thresholds v8.0 - PROVISORIOS para calibración
THRESHOLD_CONFIRMADO_SCORE = 0.60
THRESHOLD_CONFIRMADO_COVERAGE = 0.40
THRESHOLD_REVISION = 0.50
THRESHOLD_SKILLS_MINIMO = 0.35

# Configuración por defecto
DEFAULT_LIMIT = 200


def parse_skills(skills_raw):
    """Parsea skills del formato JSON a lista de strings."""
    if not skills_raw:
        return []

    try:
        # Manejar doble serialización
        if isinstance(skills_raw, str) and skills_raw.startswith('"') and skills_raw.endswith('"'):
            skills_raw = json.loads(skills_raw)

        skills_list = json.loads(skills_raw) if isinstance(skills_raw, str) else skills_raw

        result = []
        if isinstance(skills_list, list):
            for s in skills_list:
                if isinstance(s, dict) and 'valor' in s:
                    result.append(s['valor'])
                elif isinstance(s, str):
                    result.append(s)
        return result
    except Exception:
        return []


def classify_match(score_final, coverage_score):
    """Clasifica el match según umbrales v8.0."""
    if score_final >= THRESHOLD_CONFIRMADO_SCORE and coverage_score >= THRESHOLD_CONFIRMADO_COVERAGE:
        return 'CONFIRMADO'
    elif THRESHOLD_REVISION <= score_final < THRESHOLD_CONFIRMADO_SCORE:
        return 'REVISION'
    else:
        return 'RECHAZADO'


def get_isco_group(cursor, occupation_uri):
    """Obtiene el grupo ISCO (primer dígito) de una ocupación."""
    if not occupation_uri:
        return 'N/A'

    cursor.execute('''
        SELECT isco_code FROM esco_occupations WHERE occupation_uri = ?
    ''', (occupation_uri,))
    row = cursor.fetchone()

    if row and row[0]:
        isco_code = row[0]
        if isco_code.startswith('C'):
            return isco_code[1] if len(isco_code) > 1 else 'N/A'
        return isco_code[0] if isco_code else 'N/A'
    return 'N/A'


def run_batch_pilot(limit=DEFAULT_LIMIT):
    """Ejecuta el batch piloto y genera estadísticas."""
    print("=" * 80)
    print("BATCH PILOTO v8.0 - ESCO MULTICRITERIO CALIBRADO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Límite de ofertas: {limit}")
    print("=" * 80)

    # Umbrales actuales
    print(f"\nUmbrales v8.0:")
    print(f"  - CONFIRMADO: score >= {THRESHOLD_CONFIRMADO_SCORE} AND coverage >= {THRESHOLD_CONFIRMADO_COVERAGE}")
    print(f"  - REVISION:   {THRESHOLD_REVISION} <= score < {THRESHOLD_CONFIRMADO_SCORE}")
    print(f"  - RECHAZADO:  score < {THRESHOLD_REVISION} OR coverage < {THRESHOLD_CONFIRMADO_COVERAGE}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Cargar modelo BGE-M3
    print(f"\n[1] Cargando BGE-M3...")
    model = SentenceTransformer('BAAI/bge-m3')

    # Cargar embeddings ESCO
    print('[2] Cargando embeddings ESCO...')
    esco_embeddings = np.load(EMBEDDINGS_DIR / 'esco_occupations_embeddings.npy')
    with open(EMBEDDINGS_DIR / 'esco_occupations_metadata.json', 'r', encoding='utf-8') as f:
        esco_metadata = json.load(f)
    print(f'    -> {len(esco_embeddings)} ocupaciones ESCO')

    # Cargar descripciones si existen
    desc_embeddings = None
    desc_path = EMBEDDINGS_DIR / 'esco_descriptions_embeddings.npy'
    if desc_path.exists():
        desc_embeddings = np.load(desc_path)
        print(f'    -> Embeddings de descripciones cargados')

    # Obtener ofertas con NLP
    print(f'\n[3] Obteniendo ofertas con NLP...')
    cursor.execute('''
        SELECT DISTINCT
            o.id_oferta,
            o.titulo,
            o.descripcion_utf8,
            n.skills_tecnicas_list,
            n.soft_skills_list,
            n.source_table,
            n.nlp_version
        FROM ofertas o
        INNER JOIN ofertas_nlp_latest n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
        WHERE o.titulo IS NOT NULL
          AND o.titulo != ''
          AND n.skills_tecnicas_list IS NOT NULL
        ORDER BY o.id_oferta DESC
        LIMIT ?
    ''', (limit,))
    ofertas = cursor.fetchall()
    print(f'    -> {len(ofertas)} ofertas encontradas')

    if len(ofertas) == 0:
        print("\n[!] No hay ofertas con datos NLP. Ejecute primero el pipeline NLP.")
        conn.close()
        return

    # Resultados por categoría
    results = {
        'CONFIRMADO': [],
        'REVISION': [],
        'RECHAZADO': []
    }

    # Estadísticas
    all_scores = []
    all_coverages = []
    errores = 0

    print(f'\n[4] Procesando {len(ofertas)} ofertas con algoritmo multicriterio v8.0...')

    for i, row in enumerate(ofertas):
        id_oferta = str(row['id_oferta'])
        titulo = row['titulo'] or ''
        descripcion = row['descripcion_utf8'] or ''

        # Parsear skills
        skills_tecnicas = parse_skills(row['skills_tecnicas_list'])
        soft_skills = parse_skills(row['soft_skills_list'])
        all_skills = skills_tecnicas + soft_skills

        # Progreso cada 50 ofertas
        if (i + 1) % 50 == 0:
            print(f"    -> Procesadas {i + 1}/{len(ofertas)} ofertas...")

        try:
            # PASO 1: Embedding del título + descripción corta
            texto_oferta = f'{titulo}. {" ".join(descripcion.split()[:200])}'
            oferta_embedding = model.encode([texto_oferta])[0]
            oferta_embedding = oferta_embedding / np.linalg.norm(oferta_embedding)

            # Similaridad con ESCO
            similarities = np.dot(esco_embeddings, oferta_embedding)
            top_indices = np.argsort(similarities)[-5:][::-1]

            mejor_idx = top_indices[0]
            mejor_uri = esco_metadata[mejor_idx]['uri']
            mejor_label = esco_metadata[mejor_idx]['label']
            score_titulo = float(similarities[mejor_idx])

            # PASO 2: Score de skills
            cursor.execute('''
                SELECT s.preferred_label_es, a.relation_type
                FROM esco_associations a
                JOIN esco_skills s ON a.skill_uri = s.skill_uri
                WHERE a.occupation_uri = ?
            ''', (mejor_uri,))
            esco_skills = {'essential': set(), 'optional': set()}
            for skill_row in cursor.fetchall():
                label = (skill_row['preferred_label_es'] or '').lower().strip()
                rel = skill_row['relation_type'] or 'optional'
                if label and rel in esco_skills:
                    esco_skills[rel].add(label)

            # Calcular score semántico de skills
            score_skills = 0.0
            if all_skills and (esco_skills['essential'] or esco_skills['optional']):
                all_esco_skills = list(esco_skills['essential']) + list(esco_skills['optional'])
                try:
                    oferta_skill_emb = model.encode(all_skills, show_progress_bar=False)
                    esco_skill_emb = model.encode(all_esco_skills, show_progress_bar=False)

                    oferta_skill_emb = oferta_skill_emb / np.linalg.norm(oferta_skill_emb, axis=1, keepdims=True)
                    esco_skill_emb = esco_skill_emb / np.linalg.norm(esco_skill_emb, axis=1, keepdims=True)

                    sim_matrix = np.dot(oferta_skill_emb, esco_skill_emb.T)

                    # Para cada skill de oferta, tomar mejor match
                    THRESHOLD = 0.50
                    matches = 0
                    total_score = 0.0
                    for j in range(len(all_skills)):
                        best_score = np.max(sim_matrix[j])
                        if best_score >= THRESHOLD:
                            matches += 1
                            total_score += best_score

                    if matches > 0:
                        coverage = matches / len(all_skills)
                        avg_quality = total_score / matches
                        score_skills = min(1.0, coverage * avg_quality * 1.2)
                except Exception:
                    pass

            # PASO 3: Score de descripción
            score_descripcion = 0.0
            if desc_embeddings is not None and descripcion:
                desc_short = ' '.join(descripcion.split()[:300])
                desc_emb = model.encode([desc_short])[0]
                desc_emb = desc_emb / np.linalg.norm(desc_emb)
                score_descripcion = float(np.dot(desc_emb, desc_embeddings[mejor_idx]))

            # PASO 4: Coverage score (basado en skills extraídos)
            # Coverage = proporción de skills que matchean bien
            coverage_score = 0.5  # default
            if all_skills:
                coverage_score = min(1.0, len(all_skills) / 10.0)  # Normalizar a 10 skills

            # PASO 5: Score final con fallback
            if score_skills >= THRESHOLD_SKILLS_MINIMO:
                score_final = (score_titulo * PESO_TITULO +
                              score_skills * PESO_SKILLS +
                              score_descripcion * PESO_DESCRIPCION)
            else:
                score_final = (score_titulo * 0.85 + score_descripcion * 0.15)

            # Clasificar según v8.0
            categoria = classify_match(score_final, coverage_score)

            # Obtener ISCO group
            isco_group = get_isco_group(cursor, mejor_uri)

            # Guardar resultado
            entry = {
                'id_oferta': id_oferta,
                'titulo': titulo[:60],
                'esco_label': mejor_label,
                'score_final': score_final,
                'coverage_score': coverage_score,
                'isco_group': isco_group,
                'score_titulo': score_titulo,
                'score_skills': score_skills,
                'score_descripcion': score_descripcion
            }

            results[categoria].append(entry)
            all_scores.append(score_final)
            all_coverages.append(coverage_score)

            # Actualizar DB
            cursor.execute('''
                INSERT OR REPLACE INTO ofertas_esco_matching (
                    id_oferta,
                    esco_occupation_uri,
                    esco_occupation_label,
                    score_titulo,
                    score_skills,
                    score_descripcion,
                    score_final_ponderado,
                    skills_oferta_json,
                    match_confirmado,
                    requiere_revision,
                    occupation_match_method,
                    matching_version,
                    matching_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (
                id_oferta,
                mejor_uri,
                mejor_label,
                score_titulo,
                score_skills,
                score_descripcion,
                score_final,
                json.dumps(all_skills, ensure_ascii=False),
                1 if categoria == 'CONFIRMADO' else 0,
                1 if categoria == 'REVISION' else 0,
                'v8.0_multicriterio_calibrado',
                'v8.0_esco_multicriterio_calibrado'
            ))

        except Exception as e:
            errores += 1
            if errores <= 5:
                print(f"    [!] Error en oferta {id_oferta}: {e}")

    conn.commit()

    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS DE DISTRIBUCIÓN")
    print("=" * 80)

    total_procesadas = len(all_scores)
    if total_procesadas == 0:
        print("\n[!] No se procesaron ofertas exitosamente.")
        conn.close()
        return

    scores_np = np.array(all_scores)
    coverages_np = np.array(all_coverages)

    print(f"\nOfertas procesadas: {total_procesadas}")
    print(f"Errores: {errores}")

    print(f"\n--- score_final_ponderado ---")
    print(f"  min:  {np.min(scores_np):.4f}")
    print(f"  p25:  {np.percentile(scores_np, 25):.4f}")
    print(f"  p50:  {np.percentile(scores_np, 50):.4f}")
    print(f"  p75:  {np.percentile(scores_np, 75):.4f}")
    print(f"  max:  {np.max(scores_np):.4f}")
    print(f"  mean: {np.mean(scores_np):.4f}")
    print(f"  std:  {np.std(scores_np):.4f}")

    print(f"\n--- coverage_score ---")
    print(f"  min:  {np.min(coverages_np):.4f}")
    print(f"  p25:  {np.percentile(coverages_np, 25):.4f}")
    print(f"  p50:  {np.percentile(coverages_np, 50):.4f}")
    print(f"  p75:  {np.percentile(coverages_np, 75):.4f}")
    print(f"  max:  {np.max(coverages_np):.4f}")

    # =========================================================================
    # CONTEO POR CATEGORÍA
    # =========================================================================
    print("\n" + "-" * 80)
    print("CONTEO POR CATEGORÍA")
    print("-" * 80)

    for cat in ['CONFIRMADO', 'REVISION', 'RECHAZADO']:
        count = len(results[cat])
        pct = (count / total_procesadas * 100) if total_procesadas > 0 else 0
        print(f"  {cat:12}: {count:4} ({pct:5.1f}%)")

    # =========================================================================
    # EJEMPLOS POR CATEGORÍA
    # =========================================================================
    print("\n" + "=" * 80)
    print("EJEMPLOS POR CATEGORÍA (10 cada una)")
    print("=" * 80)

    for cat in ['CONFIRMADO', 'REVISION', 'RECHAZADO']:
        print(f"\n{'='*40}")
        print(f"CATEGORÍA: {cat}")
        print(f"{'='*40}")

        # Tomar hasta 10 ejemplos
        ejemplos = results[cat][:10]

        if not ejemplos:
            print("  (sin ejemplos)")
            continue

        for j, ej in enumerate(ejemplos, 1):
            print(f"\n  [{j}] ID: {ej['id_oferta']}")
            print(f"      Título: {ej['titulo']}...")
            print(f"      ESCO:   {ej['esco_label']}")
            print(f"      Score:  {ej['score_final']:.4f} | Coverage: {ej['coverage_score']:.4f} | ISCO: {ej['isco_group']}")
            print(f"      Desglose: T={ej['score_titulo']:.3f} S={ej['score_skills']:.3f} D={ej['score_descripcion']:.3f}")

    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)
    print(f"""
Batch Piloto v8.0 completado.

Procesadas: {total_procesadas} ofertas
Errores:    {errores}

Distribución por categoría:
  - CONFIRMADO: {len(results['CONFIRMADO'])} ({len(results['CONFIRMADO'])/total_procesadas*100:.1f}%)
  - REVISION:   {len(results['REVISION'])} ({len(results['REVISION'])/total_procesadas*100:.1f}%)
  - RECHAZADO:  {len(results['RECHAZADO'])} ({len(results['RECHAZADO'])/total_procesadas*100:.1f}%)

score_final_ponderado:
  - Media:   {np.mean(scores_np):.4f}
  - Mediana: {np.percentile(scores_np, 50):.4f}
  - Rango:   [{np.min(scores_np):.4f}, {np.max(scores_np):.4f}]

Versión: v8.0_esco_multicriterio_calibrado
""")

    conn.close()
    return results


if __name__ == '__main__':
    # Parsear argumentos
    limit = DEFAULT_LIMIT

    if '--limit' in sys.argv:
        try:
            idx = sys.argv.index('--limit')
            limit = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Uso: python run_batch_pilot_v8.py [--limit N]")
            sys.exit(1)

    run_batch_pilot(limit=limit)
