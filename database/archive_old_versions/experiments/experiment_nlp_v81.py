#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MOL-54: Experimento NLP v8.1 vs v8.0
====================================
Compara extraccion de skills en prosa entre v8.0 y v8.1
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
METRICS_DIR = Path(__file__).parent / 'metrics'

def parse_nested_json(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [parsed] if parsed else []
        except:
            return [value] if value else []
    return []

def get_baseline_v80():
    """Guarda baseline de v8.0 antes de reprocesar"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            v.id_oferta,
            v.resultado_capa1_verificado,
            m.score_final_ponderado,
            m.match_confirmado,
            m.requiere_revision
        FROM validacion_v7 v
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0'
    """)

    baseline = {}
    total = 0
    con_skills_tec = 0
    total_skills = 0
    scores = []
    confirmados = 0
    revision = 0
    rechazados = 0

    for row in cursor.fetchall():
        id_oferta, nlp_json, score, confirmed, needs_rev = row
        total += 1

        skills_tec = []
        if nlp_json:
            try:
                data = json.loads(nlp_json)
                skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
            except:
                pass

        if skills_tec:
            con_skills_tec += 1
            total_skills += len(skills_tec)

        if score:
            scores.append(float(score))
            if confirmed:
                confirmados += 1
            elif needs_rev:
                revision += 1
            else:
                rechazados += 1

        baseline[str(id_oferta)] = {
            'skills_tec': skills_tec,
            'score': float(score) if score else None
        }

    conn.close()

    stats = {
        'total': total,
        'con_skills_tec': con_skills_tec,
        'pct_con_skills': con_skills_tec / total * 100 if total > 0 else 0,
        'avg_skills_when_present': total_skills / con_skills_tec if con_skills_tec > 0 else 0,
        'avg_score': sum(scores) / len(scores) if scores else 0,
        'min_score': min(scores) if scores else 0,
        'max_score': max(scores) if scores else 0,
        'confirmados': confirmados,
        'revision': revision,
        'rechazados': rechazados
    }

    return baseline, stats

def get_ids_v80():
    """Obtiene IDs con NLP v8.0"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.0.0'")
    ids = [str(row[0]) for row in cursor.fetchall()]
    conn.close()
    return ids

def delete_v80_records(ids):
    """Elimina registros de validacion_v7 para forzar reprocesamiento"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    placeholders = ','.join(['?'] * len(ids))
    cursor.execute(f"""
        DELETE FROM validacion_v7
        WHERE CAST(id_oferta AS TEXT) IN ({placeholders})
        AND nlp_version = '8.0.0'
    """, ids)

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def get_results_v81(ids):
    """Obtiene resultados despues de procesar con v8.1"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    placeholders = ','.join(['?'] * len(ids))
    cursor.execute(f"""
        SELECT
            v.id_oferta,
            v.nlp_version,
            v.resultado_capa1_verificado,
            m.score_final_ponderado,
            m.match_confirmado,
            m.requiere_revision
        FROM validacion_v7 v
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE CAST(v.id_oferta AS TEXT) IN ({placeholders})
    """, ids)

    results = {}
    total = 0
    con_skills_tec = 0
    total_skills = 0
    scores = []
    confirmados = 0
    revision = 0
    rechazados = 0

    for row in cursor.fetchall():
        id_oferta, version, nlp_json, score, confirmed, needs_rev = row
        total += 1

        skills_tec = []
        if nlp_json:
            try:
                data = json.loads(nlp_json)
                skills_tec = parse_nested_json(data.get('skills_tecnicas_list'))
            except:
                pass

        if skills_tec:
            con_skills_tec += 1
            total_skills += len(skills_tec)

        if score:
            scores.append(float(score))
            if confirmed:
                confirmados += 1
            elif needs_rev:
                revision += 1
            else:
                rechazados += 1

        results[str(id_oferta)] = {
            'version': version,
            'skills_tec': skills_tec,
            'score': float(score) if score else None
        }

    conn.close()

    stats = {
        'total': total,
        'con_skills_tec': con_skills_tec,
        'pct_con_skills': con_skills_tec / total * 100 if total > 0 else 0,
        'avg_skills_when_present': total_skills / con_skills_tec if con_skills_tec > 0 else 0,
        'avg_score': sum(scores) / len(scores) if scores else 0,
        'min_score': min(scores) if scores else 0,
        'max_score': max(scores) if scores else 0,
        'confirmados': confirmados,
        'revision': revision,
        'rechazados': rechazados
    }

    return results, stats

def compare_results(baseline, baseline_stats, results_v81, stats_v81):
    """Compara v8.0 vs v8.1"""

    # Ofertas que ganaron skills
    gained_skills = []
    for id_oferta, v81_data in results_v81.items():
        v80_data = baseline.get(id_oferta, {})
        v80_skills = v80_data.get('skills_tec', [])
        v81_skills = v81_data.get('skills_tec', [])

        if not v80_skills and v81_skills:
            gained_skills.append({
                'id': id_oferta,
                'new_skills': v81_skills
            })
        elif v81_skills and len(v81_skills) > len(v80_skills):
            gained_skills.append({
                'id': id_oferta,
                'old_skills': v80_skills,
                'new_skills': v81_skills,
                'gained': len(v81_skills) - len(v80_skills)
            })

    comparison = {
        'timestamp': datetime.now().isoformat(),
        'experiment': 'MOL-54: NLP v8.1 vs v8.0 - Skills en prosa',
        'baseline_v80': baseline_stats,
        'results_v81': stats_v81,
        'improvements': {
            'pct_con_skills_delta': stats_v81['pct_con_skills'] - baseline_stats['pct_con_skills'],
            'avg_score_delta': stats_v81['avg_score'] - baseline_stats['avg_score'],
            'confirmados_delta': stats_v81['confirmados'] - baseline_stats['confirmados'],
            'ofertas_gained_skills': len(gained_skills)
        },
        'ofertas_que_ganaron_skills': gained_skills[:20]  # Primeros 20 ejemplos
    }

    return comparison

def main():
    print("=" * 80)
    print("MOL-54: EXPERIMENTO NLP v8.1 vs v8.0")
    print("=" * 80)

    # 1. Guardar baseline v8.0
    print("\n[1] GUARDANDO BASELINE v8.0")
    print("-" * 40)
    baseline, baseline_stats = get_baseline_v80()
    ids = list(baseline.keys())

    print(f"Total ofertas v8.0: {baseline_stats['total']}")
    print(f"Con skills tecnicos: {baseline_stats['con_skills_tec']} ({baseline_stats['pct_con_skills']:.1f}%)")
    print(f"Score promedio: {baseline_stats['avg_score']:.3f}")
    print(f"Distribucion: {baseline_stats['confirmados']} conf / {baseline_stats['revision']} rev / {baseline_stats['rechazados']} rech")

    # Guardar baseline
    METRICS_DIR.mkdir(exist_ok=True)
    baseline_file = METRICS_DIR / 'baseline_v80_before_v81.json'
    with open(baseline_file, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': baseline_stats,
            'details': baseline
        }, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Baseline guardado en: {baseline_file}")

    # 2. Eliminar registros v8.0 para forzar reprocesamiento
    print("\n[2] ELIMINANDO REGISTROS v8.0 PARA FORZAR REPROCESO")
    print("-" * 40)
    deleted = delete_v80_records(ids)
    print(f"Registros eliminados: {deleted}")

    # 3. Procesar con v8.1
    print("\n[3] PROCESANDO CON NLP v8.1")
    print("-" * 40)
    print(f"Ofertas a procesar: {len(ids)}")
    print("\nEjecutando NLP v8.1...")

    # Importar y ejecutar
    from process_nlp_from_db_v7 import NLPExtractorV7

    extractor = NLPExtractorV7(str(DB_PATH), verbose=False)

    # Obtener datos de ofertas
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(ids))
    cursor.execute(f"""
        SELECT id_oferta, titulo, COALESCE(descripcion_utf8, descripcion) as desc, empresa
        FROM ofertas
        WHERE CAST(id_oferta AS TEXT) IN ({placeholders})
    """, ids)
    ofertas_data = {str(row[0]): {'titulo': row[1], 'desc': row[2], 'empresa': row[3]} for row in cursor.fetchall()}
    conn.close()

    # Procesar en batches
    batch_size = 20
    processed = 0
    errors = 0

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        for id_oferta in batch_ids:
            try:
                oferta = ofertas_data.get(id_oferta, {})
                desc = oferta.get('desc', '')
                titulo = oferta.get('titulo', '')
                empresa = oferta.get('empresa', '')

                if not desc:
                    errors += 1
                    continue

                result = extractor.process_oferta(id_oferta, desc, titulo, empresa)
                if result and result.get("error_message") is None:
                    extractor.save_to_validacion_v7(result, titulo=titulo, empresa=empresa)
                    processed += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1

        print(f"  Progreso: {min(i + batch_size, len(ids))}/{len(ids)}")

    print(f"\n[OK] Procesadas: {processed}, Errores: {errors}")

    # 4. Ejecutar matching
    print("\n[4] EJECUTANDO MATCHING")
    print("-" * 40)

    from run_matching_nlp_v8_only import main as run_matching
    # El matching ya procesa las ofertas sin matching o actualiza las existentes

    # Necesitamos re-ejecutar matching para las 121 ofertas
    # Usamos el script existente pero adaptado
    from match_ofertas_multicriteria import MultiCriteriaMatcher
    import numpy as np

    matcher = MultiCriteriaMatcher()
    matcher.conectar()
    matcher.cargar_modelos()
    matcher.cargar_embeddings_esco()

    cursor = matcher.conn.cursor()
    placeholders = ','.join(['?'] * len(ids))

    cursor.execute(f'''
        SELECT
            o.id_oferta, o.titulo, COALESCE(o.descripcion_utf8, o.descripcion) as desc,
            n.skills_tecnicas_list, n.soft_skills_list, n.coverage_score
        FROM ofertas o
        LEFT JOIN ofertas_nlp_latest n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
        WHERE CAST(o.id_oferta AS TEXT) IN ({placeholders})
    ''', ids)

    ofertas = cursor.fetchall()
    print(f"Ofertas para matching: {len(ofertas)}")

    for row in ofertas:
        id_oferta = row[0]
        titulo = row[1]
        descripcion = row[2] or ''
        coverage = row[5] or 1.0

        skills_tecnicas = []
        if row[3]:
            try:
                skills_tecnicas = json.loads(row[3])
                if not isinstance(skills_tecnicas, list):
                    skills_tecnicas = [skills_tecnicas]
            except:
                pass

        if row[4]:
            try:
                soft = json.loads(row[4])
                if isinstance(soft, list):
                    skills_tecnicas.extend(soft)
            except:
                pass

        oferta = {
            'id_oferta': id_oferta,
            'titulo': titulo,
            'descripcion': descripcion,
            'skills_tecnicas': skills_tecnicas
        }

        try:
            texto_oferta = f"{titulo}. {' '.join(descripcion.split()[:200])}"
            oferta_embedding = matcher.embedding_model.encode([texto_oferta])[0]
            oferta_embedding = oferta_embedding / np.linalg.norm(oferta_embedding)

            similarities = np.dot(matcher.esco_embeddings, oferta_embedding)
            top_indices = np.argsort(similarities)[-10:][::-1]

            candidatos = []
            for idx in top_indices:
                candidatos.append({
                    'uri': matcher.esco_metadata[idx]['uri'],
                    'label': matcher.esco_metadata[idx]['label'],
                    'similarity_score': float(similarities[idx]),
                    'isco_code': matcher.esco_metadata[idx].get('isco_code')
                })

            candidatos = candidatos[:3]
            resultado = matcher.procesar_oferta(oferta, candidatos, coverage_score=coverage)

            cursor.execute("""
                INSERT OR REPLACE INTO ofertas_esco_matching (
                    id_oferta, esco_occupation_uri, esco_occupation_label,
                    occupation_match_score, rerank_score,
                    score_titulo, score_skills, score_descripcion, score_final_ponderado,
                    skills_oferta_json, skills_matched_essential, skills_matched_optional,
                    skills_cobertura, match_confirmado, requiere_revision,
                    isco_code, isco_nivel1, isco_nivel2,
                    occupation_match_method, matching_version, matching_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                          'v8.1_experiment', 'v8.1_experiment', datetime('now'))
            """, (
                str(id_oferta),
                resultado['esco_occupation_uri'],
                resultado['esco_occupation_label'],
                resultado['occupation_match_score'],
                resultado['rerank_score'],
                resultado['score_titulo'],
                resultado['score_skills'],
                resultado['score_descripcion'],
                resultado['score_final_ponderado'],
                resultado['skills_oferta_json'],
                resultado['skills_matched_essential'],
                resultado['skills_matched_optional'],
                resultado['skills_cobertura'],
                resultado['match_confirmado'],
                resultado['requiere_revision'],
                resultado['isco_code'],
                resultado['isco_nivel1'],
                resultado['isco_nivel2']
            ))
        except Exception as e:
            print(f"  Error matching {id_oferta}: {e}")

    matcher.conn.commit()
    matcher.conn.close()
    print("[OK] Matching completado")

    # 5. Obtener resultados v8.1 y comparar
    print("\n[5] COMPARANDO RESULTADOS")
    print("-" * 40)

    results_v81, stats_v81 = get_results_v81(ids)

    print(f"\nv8.1 Resultados:")
    print(f"Con skills tecnicos: {stats_v81['con_skills_tec']} ({stats_v81['pct_con_skills']:.1f}%)")
    print(f"Score promedio: {stats_v81['avg_score']:.3f}")
    print(f"Distribucion: {stats_v81['confirmados']} conf / {stats_v81['revision']} rev / {stats_v81['rechazados']} rech")

    comparison = compare_results(baseline, baseline_stats, results_v81, stats_v81)

    # Guardar experimento
    experiment_file = METRICS_DIR / 'experiment_nlp_v81_vs_v80.json'
    with open(experiment_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("RESUMEN EXPERIMENTO")
    print("=" * 80)

    print(f"\n{'Metrica':<30} {'v8.0':>12} {'v8.1':>12} {'Delta':>12}")
    print("-" * 66)
    print(f"{'% con skills tecnicos':<30} {baseline_stats['pct_con_skills']:>11.1f}% {stats_v81['pct_con_skills']:>11.1f}% {comparison['improvements']['pct_con_skills_delta']:>+11.1f}%")
    print(f"{'Score promedio':<30} {baseline_stats['avg_score']:>12.3f} {stats_v81['avg_score']:>12.3f} {comparison['improvements']['avg_score_delta']:>+12.3f}")
    print(f"{'Confirmados':<30} {baseline_stats['confirmados']:>12} {stats_v81['confirmados']:>12} {comparison['improvements']['confirmados_delta']:>+12}")
    print(f"{'Revision':<30} {baseline_stats['revision']:>12} {stats_v81['revision']:>12}")
    print(f"{'Rechazados':<30} {baseline_stats['rechazados']:>12} {stats_v81['rechazados']:>12}")

    print(f"\nOfertas que GANARON skills: {comparison['improvements']['ofertas_gained_skills']}")

    if comparison['ofertas_que_ganaron_skills']:
        print("\nEjemplos de ofertas que ganaron skills:")
        for item in comparison['ofertas_que_ganaron_skills'][:5]:
            print(f"  ID {item['id']}: {item['new_skills']}")

    print(f"\n[OK] Experimento guardado en: {experiment_file}")
    print("=" * 80)

    return comparison

if __name__ == "__main__":
    main()
