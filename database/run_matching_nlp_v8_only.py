#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ejecutar matching SOLO para ofertas con NLP v8.0 sin matching
Optimizado: usa el matcher existente pero filtra ofertas
"""

import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Importar el matcher
from match_ofertas_multicriteria import (
    MultiCriteriaMatcher,
    PESO_TITULO, PESO_SKILLS, PESO_DESCRIPCION,
    THRESHOLD_CONFIRMADO_SCORE, THRESHOLD_REVISION
)
from tqdm import tqdm
import numpy as np

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def get_nlp_v8_ids_without_matching():
    """Obtiene IDs con NLP v8.0 pero sin matching"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT v.id_oferta
        FROM validacion_v7 v
        LEFT JOIN ofertas_esco_matching m ON CAST(v.id_oferta AS TEXT) = CAST(m.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0' AND (m.id_oferta IS NULL OR m.esco_occupation_uri IS NULL)
    ''')

    ids = [str(row[0]) for row in cursor.fetchall()]
    conn.close()
    return ids

def main():
    print("=" * 70)
    print("MATCHING SOLO PARA OFERTAS CON NLP v8.0")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Get IDs sin matching
    ids_sin_matching = get_nlp_v8_ids_without_matching()
    print(f"\nOfertas con NLP v8.0 sin matching: {len(ids_sin_matching)}")

    if not ids_sin_matching:
        print("No hay ofertas pendientes.")
        return

    # Inicializar matcher
    print("\nInicializando matcher...")
    matcher = MultiCriteriaMatcher()
    matcher.conectar()
    matcher.cargar_modelos()

    if not matcher.cargar_embeddings_esco():
        print("[ERROR] No se pudieron cargar embeddings ESCO")
        return

    # Obtener ofertas para estos IDs especificos
    print(f"\n[3] PROCESANDO {len(ids_sin_matching)} OFERTAS")
    print("=" * 60)

    cursor = matcher.conn.cursor()

    # Query solo para los IDs especificos
    placeholders = ','.join(['?'] * len(ids_sin_matching))
    cursor.execute(f'''
        SELECT
            o.id_oferta, o.titulo, o.descripcion_utf8,
            n.skills_tecnicas_list, n.soft_skills_list,
            n.source_table, n.nlp_version, n.coverage_score
        FROM ofertas o
        LEFT JOIN ofertas_nlp_latest n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
        WHERE CAST(o.id_oferta AS TEXT) IN ({placeholders})
    ''', ids_sin_matching)

    ofertas = cursor.fetchall()
    print(f"  -> {len(ofertas)} ofertas encontradas")

    # Procesar ofertas (copiado de match_ofertas_multicriteria.ejecutar)
    batch_size = 20
    for i in tqdm(range(0, len(ofertas), batch_size), desc="  Matching"):
        batch = ofertas[i:i + batch_size]

        for row in batch:
            id_oferta = row[0]  # id_oferta
            titulo = row[1]     # titulo
            descripcion = row[2] or ''  # descripcion_utf8
            coverage = row[7] or 1.0    # coverage_score

            # Parsear skills de NLP
            skills_tecnicas = []
            if row[3]:  # skills_tecnicas_list
                try:
                    skills_tecnicas = json.loads(row[3])
                    if not isinstance(skills_tecnicas, list):
                        skills_tecnicas = [skills_tecnicas]
                except:
                    pass

            if row[4]:  # soft_skills_list
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

            if skills_tecnicas:
                matcher.stats['ofertas_con_nlp'] += 1

            try:
                # PASO 1: Obtener candidatos por titulo (BGE-M3)
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

                # Tomar top 3 (sin reranker)
                candidatos = candidatos[:3]

                # Procesar con algoritmo multicriteria
                resultado = matcher.procesar_oferta(oferta, candidatos, coverage_score=coverage)

                # Insertar o actualizar base de datos
                cursor.execute("""
                    INSERT OR REPLACE INTO ofertas_esco_matching (
                        id_oferta,
                        esco_occupation_uri,
                        esco_occupation_label,
                        occupation_match_score,
                        rerank_score,
                        score_titulo,
                        score_skills,
                        score_descripcion,
                        score_final_ponderado,
                        skills_oferta_json,
                        skills_matched_essential,
                        skills_matched_optional,
                        skills_cobertura,
                        match_confirmado,
                        requiere_revision,
                        isco_code,
                        isco_nivel1,
                        isco_nivel2,
                        occupation_match_method,
                        matching_version,
                        matching_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              'v8.1_multicriterio_validado',
                              'v8.1_esco_multicriterio_validado',
                              datetime('now'))
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

                matcher.stats['ofertas_procesadas'] += 1
                if resultado['match_confirmado']:
                    matcher.stats['matches_confirmados'] += 1
                elif resultado['requiere_revision']:
                    matcher.stats['matches_revision'] += 1
                else:
                    matcher.stats['matches_rechazados'] += 1

            except Exception as e:
                if len(matcher.stats['errores']) < 10:
                    matcher.stats['errores'].append(f"{id_oferta}: {e}")

        matcher.conn.commit()

    # Reporte final
    print("\n" + "=" * 70)
    print("RESUMEN MATCHING NLP v8.0")
    print("=" * 70)
    print(f"  Ofertas procesadas:     {matcher.stats['ofertas_procesadas']:,}")
    print(f"  Ofertas con NLP skills: {matcher.stats['ofertas_con_nlp']:,}")
    print(f"\n  Resultados:")
    print(f"    CONFIRMADOS (>60%):   {matcher.stats['matches_confirmados']:,}")
    print(f"    REVISION (50-60%):    {matcher.stats['matches_revision']:,}")
    print(f"    RECHAZADOS (<50%):    {matcher.stats['matches_rechazados']:,}")

    if matcher.stats['errores']:
        print(f"\n  Errores: {len(matcher.stats['errores'])}")
        for e in matcher.stats['errores'][:5]:
            print(f"    - {e}")

    print("\n[OK] Matching completado")
    matcher.conn.close()

if __name__ == "__main__":
    main()
