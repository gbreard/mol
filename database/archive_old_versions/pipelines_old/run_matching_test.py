#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para ejecutar matching multicriteria sobre las 7 ofertas de prueba.
Usa ofertas_nlp_latest que prioriza validacion_v7 > ofertas_nlp
"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
EMBEDDINGS_DIR = Path(__file__).parent / 'embeddings'

# IDs de las ofertas con NLP reciente
TARGET_IDS = ['2154549', '2163782', '2167866', '2168250', '2168254', '2168263', '2168264']

# Pesos
PESO_TITULO = 0.50
PESO_SKILLS = 0.40
PESO_DESCRIPCION = 0.10
THRESHOLD_SKILLS_MINIMO = 0.35
THRESHOLD_CONFIRMADO = 0.75
THRESHOLD_REVISION = 0.50

def main():
    print('=' * 70)
    print('MATCHING MULTICRITERIA - 7 OFERTAS DE PRUEBA')
    print('Usando vista ofertas_nlp_latest (validacion_v7 > ofertas_nlp)')
    print('=' * 70)

    # Conectar DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Cargar modelo
    print('\n[1] Cargando BGE-M3...')
    model = SentenceTransformer('BAAI/bge-m3')

    # Cargar embeddings ESCO
    print('[2] Cargando embeddings ESCO...')
    esco_embeddings = np.load(EMBEDDINGS_DIR / 'esco_occupations_embeddings.npy')
    with open(EMBEDDINGS_DIR / 'esco_occupations_metadata.json', 'r', encoding='utf-8') as f:
        esco_metadata = json.load(f)
    print(f'   -> {len(esco_embeddings)} ocupaciones ESCO')

    # Cargar descripciones si existen
    desc_embeddings = None
    desc_path = EMBEDDINGS_DIR / 'esco_descriptions_embeddings.npy'
    if desc_path.exists():
        desc_embeddings = np.load(desc_path)

    # Obtener ofertas de la vista ofertas_nlp_latest
    print('\n[3] Procesando ofertas con NLP reciente...')
    ids_str = ','.join([f"'{x}'" for x in TARGET_IDS])
    cursor.execute(f'''
        SELECT
            o.id_oferta, o.titulo, o.descripcion_utf8,
            n.skills_tecnicas_list, n.soft_skills_list,
            n.source_table, n.nlp_version
        FROM ofertas o
        LEFT JOIN ofertas_nlp_latest n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
        WHERE CAST(o.id_oferta AS TEXT) IN ({ids_str})
    ''')
    ofertas = cursor.fetchall()
    print(f'   -> {len(ofertas)} ofertas encontradas')

    for row in ofertas:
        id_oferta = row['id_oferta']
        titulo = row['titulo'] or ''
        descripcion = row['descripcion_utf8'] or ''
        source_table = row['source_table'] or 'N/A'
        nlp_version = row['nlp_version'] or 'N/A'

        # Parsear skills
        skills_tecnicas = []
        if row['skills_tecnicas_list']:
            try:
                skills_raw = row['skills_tecnicas_list']
                # Manejar doble serializacion si existe
                if isinstance(skills_raw, str) and skills_raw.startswith('"') and skills_raw.endswith('"'):
                    skills_raw = json.loads(skills_raw)
                skills_list = json.loads(skills_raw) if isinstance(skills_raw, str) else skills_raw
                if isinstance(skills_list, list):
                    for s in skills_list:
                        if isinstance(s, dict) and 'valor' in s:
                            skills_tecnicas.append(s['valor'])
                        elif isinstance(s, str):
                            skills_tecnicas.append(s)
            except Exception as e:
                print(f'   [!] Error parsing skills for {id_oferta}: {e}')

        # Soft skills tambien
        if row['soft_skills_list']:
            try:
                soft_raw = row['soft_skills_list']
                if isinstance(soft_raw, str) and soft_raw.startswith('"') and soft_raw.endswith('"'):
                    soft_raw = json.loads(soft_raw)
                soft_list = json.loads(soft_raw) if isinstance(soft_raw, str) else soft_raw
                if isinstance(soft_list, list):
                    for s in soft_list:
                        if isinstance(s, dict) and 'valor' in s:
                            skills_tecnicas.append(s['valor'])
                        elif isinstance(s, str):
                            skills_tecnicas.append(s)
            except Exception as e:
                print(f'   [!] Error parsing soft_skills for {id_oferta}: {e}')

        print(f'\n--- Oferta {id_oferta} (v{nlp_version}, source: {source_table}) ---')
        print(f'   Titulo: {titulo[:60]}...')
        print(f'   Skills extraidos: {len(skills_tecnicas)} -> {skills_tecnicas[:5]}')

        # PASO 1: Embedding del titulo
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

        print(f'   TOP 3 candidatos:')
        for i, idx in enumerate(top_indices[:3]):
            print(f'      {i+1}. {esco_metadata[idx]["label"]} (score: {similarities[idx]:.4f})')

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

        # Calcular score semantico de skills
        score_skills = 0.0
        if skills_tecnicas and (esco_skills['essential'] or esco_skills['optional']):
            all_esco_skills = list(esco_skills['essential']) + list(esco_skills['optional'])
            try:
                oferta_skill_emb = model.encode(skills_tecnicas, show_progress_bar=False)
                esco_skill_emb = model.encode(all_esco_skills, show_progress_bar=False)

                oferta_skill_emb = oferta_skill_emb / np.linalg.norm(oferta_skill_emb, axis=1, keepdims=True)
                esco_skill_emb = esco_skill_emb / np.linalg.norm(esco_skill_emb, axis=1, keepdims=True)

                sim_matrix = np.dot(oferta_skill_emb, esco_skill_emb.T)

                # Para cada skill de oferta, tomar mejor match
                THRESHOLD = 0.50
                matches = 0
                total_score = 0.0
                for i in range(len(skills_tecnicas)):
                    best_score = np.max(sim_matrix[i])
                    if best_score >= THRESHOLD:
                        matches += 1
                        total_score += best_score

                if matches > 0:
                    coverage = matches / len(skills_tecnicas)
                    avg_quality = total_score / matches
                    score_skills = min(1.0, coverage * avg_quality * 1.2)
            except Exception as e:
                print(f'   [!] Error calculando skills: {e}')

        print(f'   Score Skills: {score_skills:.4f}')

        # PASO 3: Score de descripcion
        score_descripcion = 0.0
        if desc_embeddings is not None and descripcion:
            desc_short = ' '.join(descripcion.split()[:300])
            desc_emb = model.encode([desc_short])[0]
            desc_emb = desc_emb / np.linalg.norm(desc_emb)
            score_descripcion = float(np.dot(desc_emb, desc_embeddings[mejor_idx]))

        # PASO 4: Score final con fallback
        if score_skills >= THRESHOLD_SKILLS_MINIMO:
            score_final = (score_titulo * PESO_TITULO +
                          score_skills * PESO_SKILLS +
                          score_descripcion * PESO_DESCRIPCION)
            peso_usado = 'normal'
        else:
            score_final = (score_titulo * 0.85 + score_descripcion * 0.15)
            peso_usado = 'fallback'

        # Estado
        match_confirmado = 1 if score_final > THRESHOLD_CONFIRMADO else 0
        requiere_revision = 1 if THRESHOLD_REVISION < score_final <= THRESHOLD_CONFIRMADO else 0

        print(f'   RESULTADO:')
        print(f'      ESCO: {mejor_label}')
        print(f'      Score Titulo: {score_titulo:.4f}')
        print(f'      Score Skills: {score_skills:.4f}')
        print(f'      Score Desc:   {score_descripcion:.4f}')
        print(f'      SCORE FINAL:  {score_final:.4f} ({peso_usado})')
        print(f'      Estado: {"CONFIRMADO" if match_confirmado else ("REVISION" if requiere_revision else "RECHAZADO")}')

        # Actualizar DB
        cursor.execute('''
            UPDATE ofertas_esco_matching SET
                esco_occupation_uri = ?,
                esco_occupation_label = ?,
                score_titulo = ?,
                score_skills = ?,
                score_descripcion = ?,
                score_final_ponderado = ?,
                skills_oferta_json = ?,
                match_confirmado = ?,
                requiere_revision = ?,
                occupation_match_method = 'multicriteria_v3_nlp_latest',
                matching_version = 'multicriteria_v3',
                matching_timestamp = datetime('now')
            WHERE id_oferta = ?
        ''', (
            mejor_uri,
            mejor_label,
            score_titulo,
            score_skills,
            score_descripcion,
            score_final,
            json.dumps(skills_tecnicas, ensure_ascii=False),
            match_confirmado,
            requiere_revision,
            str(id_oferta)
        ))

    conn.commit()
    print('\n' + '=' * 70)
    print('MATCHING COMPLETADO')
    print('=' * 70)
    conn.close()


if __name__ == '__main__':
    main()
