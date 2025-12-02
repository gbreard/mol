#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
match_ofertas_multicriteria.py
==============================
Matching multicriteria ESCO según PLAN_TECNICO_MOL_v2.0 Sección 5.6

VERSION: v8.1 (2025-11-28)
- Integración de reglas de validación basadas en gold set de 19 casos
- Ajustes por nivel jerárquico, familia funcional, casos especiales
- Revisión forzada para programas de pasantías/trainee

Algoritmo de 4 pasos:
- PASO 1: Título (50% del score) - BGE-M3 + ESCO-XLM re-ranking
- PASO 2: Skills (40% del score) - SQL lookup en esco_associations
- PASO 3: Descripción (10% del score) - BGE-M3 embeddings
- PASO 4: Score ponderado con thresholds + ajustes v8.1

Requiere:
    pip install sentence-transformers numpy transformers tqdm
"""

import sqlite3
import json
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from tqdm import tqdm
except ImportError as e:
    print(f"ERROR: Falta librería: {e}")
    print("Instalar con: pip install sentence-transformers numpy tqdm")
    sys.exit(1)

# Importar reglas de validación v8.1
try:
    from matching_rules_v81 import (
        calcular_ajustes_v81,
        requiere_revision_forzada
    )
    RULES_V81_AVAILABLE = True
except ImportError:
    print("WARNING: matching_rules_v81 no disponible. Reglas v8.1 deshabilitadas.")
    RULES_V81_AVAILABLE = False

try:
    import torch
    from transformers import AutoModel, AutoTokenizer
    RERANKER_AVAILABLE = True
except ImportError:
    print("WARNING: transformers/torch no disponible. Re-ranking deshabilitado.")
    RERANKER_AVAILABLE = False

# Configuración
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
EMBEDDINGS_DIR = Path(__file__).parent / 'embeddings'

# Pesos del algoritmo (PLAN_TECNICO Sección 5.6)
# Pesos BASE - se ajustan dinámicamente según coverage_score
PESO_TITULO = 0.50
PESO_SKILLS = 0.40
PESO_DESCRIPCION = 0.10

# Thresholds v8.0 - PROVISORIOS para calibración
THRESHOLD_CONFIRMADO_SCORE = 0.60
THRESHOLD_CONFIRMADO_COVERAGE = 0.40
THRESHOLD_REVISION = 0.50

# Umbrales de coverage para ajuste dinámico de pesos
COVERAGE_ALTA = 0.8    # >= 80%: pesos normales
COVERAGE_MEDIA = 0.4   # >= 40%: pesos reducidos para skills
# < 40%: fallback sin skills

# Diccionario de keywords -> grupos ISCO permitidos
# Evita matches absurdos (ej: "Gerente de Restaurante" -> vendedor)
ISCO_KEYWORDS = {
    # Directivos/Gerentes -> ISCO 1xxx
    ("gerente", "director", "jefe", "coordinador", "supervisor", "líder", "lider"): ["1"],
    # Profesionales -> ISCO 2xxx
    ("ingeniero", "contador", "abogado", "analista", "bioquímico", "bioquimico",
     "médico", "medico", "arquitecto", "químico", "quimico", "farmacéutico", "farmaceutico",
     "psicólogo", "psicologo", "profesor", "docente", "programador", "developer",
     "científico", "cientifico", "economista", "auditor"): ["2"],
    # Técnicos -> ISCO 3xxx (también pueden ser operarios 7xxx)
    ("técnico", "tecnico", "mecánico", "mecanico", "electricista"): ["3", "7"],
    # Empleados de oficina -> ISCO 4xxx
    ("administrativo", "secretario", "secretaria", "recepcionista", "asistente"): ["4"],
    # Comercio/Servicios -> ISCO 5xxx
    ("vendedor", "repositor", "cajero", "cajera", "mozo", "moza", "mesero", "mesera",
     "cocinero", "cocinera", "chef", "encargado", "asesor comercial"): ["5"],
    # Trabajadores agropecuarios -> ISCO 6xxx
    ("agricultor", "tractorista", "peón rural", "peon rural"): ["6"],
    # Operarios calificados -> ISCO 7xxx
    ("operario", "soldador", "tornero", "fresador", "matricero", "calderero"): ["7"],
    # Operadores de maquinaria -> ISCO 8xxx
    ("operador", "chofer", "conductor", "maquinista"): ["8"],
    # Ocupaciones elementales -> ISCO 9xxx
    ("limpieza", "peón", "peon", "ayudante"): ["9"],
}


def obtener_grupos_isco_permitidos(titulo):
    """
    Determina qué grupos ISCO son válidos según el título de la oferta.
    Retorna None si no hay restricción (título no matchea ningún keyword).
    """
    titulo_lower = titulo.lower()
    for keywords, grupos in ISCO_KEYWORDS.items():
        if any(kw in titulo_lower for kw in keywords):
            return grupos
    return None  # Sin restricción


def normalizar_embeddings(embeddings):
    """Normaliza embeddings a norma L2 unitaria"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return embeddings / norms


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
        return True

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


class MultiCriteriaMatcher:
    """Matcher multicriteria según PLAN_TECNICO Sección 5.6"""

    def __init__(self):
        self.conn = None
        self.embedding_model = None
        self.reranker = None
        self.esco_embeddings = None
        self.esco_metadata = None
        self.esco_desc_embeddings = None

        self.stats = {
            'ofertas_procesadas': 0,
            'ofertas_con_nlp': 0,
            'matches_confirmados': 0,
            'matches_revision': 0,
            'matches_rechazados': 0,
            'con_fallback': 0,  # Ofertas que usaron pesos fallback
            'errores': []
        }

    def conectar(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        print(f"[OK] Conectado a: {DB_PATH}")

    def cargar_modelos(self):
        print("\n[1] CARGANDO MODELOS")
        print("=" * 60)

        # BGE-M3
        print("  -> Cargando BGE-M3...")
        self.embedding_model = SentenceTransformer('BAAI/bge-m3')
        print("  [OK] BGE-M3 cargado")

        # ESCO-XLM (opcional)
        if RERANKER_AVAILABLE:
            self.reranker = ESCOReranker()
            try:
                self.reranker.cargar()
            except Exception as e:
                print(f"  [!] Error cargando reranker: {e}")
                self.reranker = None

    def cargar_embeddings_esco(self):
        print("\n[2] CARGANDO EMBEDDINGS ESCO")
        print("=" * 60)

        # Ocupaciones
        occ_emb_path = EMBEDDINGS_DIR / "esco_occupations_embeddings.npy"
        occ_meta_path = EMBEDDINGS_DIR / "esco_occupations_metadata.json"

        if occ_emb_path.exists():
            self.esco_embeddings = np.load(occ_emb_path)
            with open(occ_meta_path, 'r', encoding='utf-8') as f:
                self.esco_metadata = json.load(f)
            print(f"  [OK] {len(self.esco_embeddings):,} embeddings ocupaciones cargados")
        else:
            print("  [!] No se encontraron embeddings de ocupaciones")
            print("  -> Ejecutar primero: python match_ofertas_to_esco.py")
            return False

        # Generar embeddings de descripciones ESCO (si no existen)
        desc_emb_path = EMBEDDINGS_DIR / "esco_descriptions_embeddings.npy"
        if desc_emb_path.exists():
            self.esco_desc_embeddings = np.load(desc_emb_path)
            print(f"  [OK] {len(self.esco_desc_embeddings):,} embeddings descripciones cargados")
        else:
            print("  -> Generando embeddings de descripciones ESCO...")
            self._generar_embeddings_descripciones()

        return True

    def _generar_embeddings_descripciones(self):
        """Genera embeddings de las descripciones ESCO para PASO 3"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT occupation_uri, description_es
            FROM esco_occupations
            ORDER BY occupation_uri
        """)
        ocupaciones = cursor.fetchall()

        textos = []
        for row in ocupaciones:
            desc = row['description_es'] or ''
            # Truncar a 300 palabras
            desc_short = ' '.join(desc.split()[:300])
            textos.append(desc_short if desc_short else "Sin descripción")

        print(f"  -> Generando embeddings de {len(textos)} descripciones...")
        embeddings = self.embedding_model.encode(textos, show_progress_bar=True, batch_size=32)
        embeddings = normalizar_embeddings(embeddings)

        # Guardar
        desc_emb_path = EMBEDDINGS_DIR / "esco_descriptions_embeddings.npy"
        np.save(desc_emb_path, embeddings)
        self.esco_desc_embeddings = embeddings
        print(f"  [OK] Embeddings descripciones guardados")

    def obtener_skills_ocupacion(self, occupation_uri):
        """Obtiene skills esenciales y opcionales de una ocupación ESCO"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.preferred_label_es, a.relation_type
            FROM esco_associations a
            JOIN esco_skills s ON a.skill_uri = s.skill_uri
            WHERE a.occupation_uri = ?
        """, (occupation_uri,))

        skills = {'essential': set(), 'optional': set()}
        for row in cursor.fetchall():
            label = (row['preferred_label_es'] or '').lower().strip()
            rel = row['relation_type'] or 'optional'
            if label and rel in skills:
                skills[rel].add(label)

        return skills

    def calcular_score_skills(self, skills_oferta, skills_esco):
        """
        Calcula score de matching por skills usando SIMILARIDAD SEMÁNTICA.

        En lugar de matching exacto, usa embeddings para encontrar
        el mejor skill ESCO para cada skill de la oferta.

        Threshold de match: 0.50 (similaridad coseno - ajustado para capturar más matches)
        """
        if not skills_oferta:
            return 0.0, [], []

        # Threshold para considerar un match semántico válido
        # NOTA: Reducido de 0.65 a 0.50 para capturar más similaridades semánticas
        SIMILARITY_THRESHOLD = 0.50

        # Normalizar skills de la oferta
        skills_oferta_list = [s.lower().strip() for s in skills_oferta if s and s.strip()]
        if not skills_oferta_list:
            return 0.0, [], []

        # Combinar essential + optional para matching semántico
        all_esco_skills = list(skills_esco['essential']) + list(skills_esco['optional'])
        if not all_esco_skills:
            return 0.0, [], []

        # Generar embeddings
        try:
            oferta_embeddings = self.embedding_model.encode(skills_oferta_list, show_progress_bar=False)
            esco_embeddings = self.embedding_model.encode(all_esco_skills, show_progress_bar=False)

            # Normalizar
            oferta_embeddings = oferta_embeddings / np.linalg.norm(oferta_embeddings, axis=1, keepdims=True)
            esco_embeddings = esco_embeddings / np.linalg.norm(esco_embeddings, axis=1, keepdims=True)

            # Calcular similaridades (matriz NxM)
            similarities = np.dot(oferta_embeddings, esco_embeddings.T)

            # Para cada skill de oferta, encontrar el mejor match ESCO
            match_essential = []
            match_optional = []
            total_score = 0.0
            num_matches = 0

            n_essential = len(skills_esco['essential'])

            for i, skill_oferta in enumerate(skills_oferta_list):
                best_match_idx = np.argmax(similarities[i])
                best_score = similarities[i][best_match_idx]

                if best_score >= SIMILARITY_THRESHOLD:
                    matched_skill = all_esco_skills[best_match_idx]
                    total_score += best_score
                    num_matches += 1

                    # Determinar si es essential u optional
                    if best_match_idx < n_essential:
                        match_essential.append(f"{skill_oferta}→{matched_skill}")
                    else:
                        match_optional.append(f"{skill_oferta}→{matched_skill}")

            # Calcular score final
            if num_matches == 0:
                return 0.0, match_essential, match_optional

            # Score basado en:
            # 1. Proporción de skills de oferta que matchearon
            # 2. Calidad promedio de los matches (similarity)
            # 3. Bonus por essential (1.5x)

            coverage = num_matches / len(skills_oferta_list)
            avg_quality = total_score / num_matches
            essential_bonus = 1.0 + (len(match_essential) * 0.5 / max(1, n_essential))

            score = min(1.0, coverage * avg_quality * essential_bonus)

            return score, match_essential, match_optional

        except Exception as e:
            # Fallback a matching exacto si hay error
            skills_oferta_norm = {s.lower().strip() for s in skills_oferta if s}
            match_essential = list(skills_oferta_norm & skills_esco['essential'])
            match_optional = list(skills_oferta_norm & skills_esco['optional'])
            total = len(skills_esco['essential']) + len(skills_esco['optional'])
            score = len(match_essential + match_optional) / max(1, total)
            return score, match_essential, match_optional

    def procesar_oferta(self, oferta, esco_candidatos, coverage_score=1.0):
        """
        Procesa una oferta con algoritmo multicriteria y pesos dinámicos

        Args:
            oferta: Dict con datos de la oferta
            esco_candidatos: Lista de candidatos ESCO del PASO 1
            coverage_score: Coverage del NLP (0-1), determina pesos dinámicos

        Returns:
            Dict con resultado del matching
        """
        # PASO 1: Score de título (ya calculado en candidatos)
        # Combinar similarity BGE-M3 con rerank ESCO-XLM
        mejor_candidato = esco_candidatos[0]
        score_titulo = mejor_candidato['similarity_score']
        if 'rerank_score' in mejor_candidato:
            # Promediar similarity y rerank
            score_titulo = (mejor_candidato['similarity_score'] * 0.7 +
                          mejor_candidato['rerank_score'] * 0.3)

        # PASO 2: Score de skills
        skills_esco = self.obtener_skills_ocupacion(mejor_candidato['uri'])
        score_skills, matched_essential, matched_optional = self.calcular_score_skills(
            oferta.get('skills_tecnicas', []),
            skills_esco
        )

        # PASO 3: Score de descripción
        score_descripcion = 0.0
        if oferta.get('descripcion') and self.esco_desc_embeddings is not None:
            # Encontrar índice del candidato en metadata
            candidato_idx = None
            for i, m in enumerate(self.esco_metadata):
                if m['uri'] == mejor_candidato['uri']:
                    candidato_idx = i
                    break

            if candidato_idx is not None:
                # Generar embedding de descripción de la oferta
                desc_oferta = ' '.join(oferta['descripcion'].split()[:300])
                desc_embedding = self.embedding_model.encode([desc_oferta])[0]
                desc_embedding = desc_embedding / np.linalg.norm(desc_embedding)

                # Calcular similaridad con descripción ESCO
                score_descripcion = float(np.dot(
                    desc_embedding,
                    self.esco_desc_embeddings[candidato_idx]
                ))

        # PASO 4: Score ponderado final CON PESOS DINÁMICOS según coverage_score
        # coverage_score indica la calidad de la extracción NLP
        # Alta cobertura -> confiar más en skills
        # Baja cobertura -> reducir peso de skills

        if coverage_score >= COVERAGE_ALTA:
            # Alta confianza en NLP: pesos normales (50/40/10)
            peso_titulo = PESO_TITULO
            peso_skills = PESO_SKILLS
            peso_desc = PESO_DESCRIPCION
            peso_usado = "normal"
        elif coverage_score >= COVERAGE_MEDIA:
            # Confianza media: reducir peso de skills (60/30/10)
            peso_titulo = 0.60
            peso_skills = 0.30
            peso_desc = 0.10
            peso_usado = "medium"
        else:
            # Baja confianza: fallback sin skills (85/0/15)
            peso_titulo = 0.85
            peso_skills = 0.0
            peso_desc = 0.15
            peso_usado = "fallback"

        score_final = (
            score_titulo * peso_titulo +
            score_skills * peso_skills +
            score_descripcion * peso_desc
        )

        # PASO 4b: Aplicar ajustes v8.1 (reglas de validación)
        ajustes_v81 = {}
        if RULES_V81_AVAILABLE:
            titulo = oferta.get('titulo', '')
            descripcion = oferta.get('descripcion', '')
            ajuste_total, ajustes_v81 = calcular_ajustes_v81(
                titulo, descripcion, mejor_candidato['label']
            )
            # Aplicar ajuste (clamped a 0-1)
            score_final = max(0.0, min(1.0, score_final + ajuste_total))

        # Determinar estado del match (v8.1: score + coverage + reglas)
        # CONFIRMADO: score >= 0.60 AND coverage >= 0.40 (y no es pasantía/trainee)
        # REVISION: 0.50 <= score < 0.60, O es pasantía/trainee
        # RECHAZADO: score < 0.50 OR coverage < 0.40

        # v8.1: Revisión forzada para programas de pasantías/trainee
        forzar_revision = False
        if RULES_V81_AVAILABLE:
            titulo = oferta.get('titulo', '')
            forzar_revision = requiere_revision_forzada(titulo)

        if forzar_revision:
            # Nunca auto-confirmar programas de pasantías/trainee
            match_confirmado = 0
            requiere_revision = 1
        elif score_final >= THRESHOLD_CONFIRMADO_SCORE and coverage_score >= THRESHOLD_CONFIRMADO_COVERAGE:
            match_confirmado = 1
            requiere_revision = 0
        elif THRESHOLD_REVISION <= score_final < THRESHOLD_CONFIRMADO_SCORE:
            match_confirmado = 0
            requiere_revision = 1
        else:
            match_confirmado = 0
            requiere_revision = 0

        # Obtener ISCO
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT isco_code FROM esco_occupations
            WHERE occupation_uri = ?
        """, (mejor_candidato['uri'],))
        isco_row = cursor.fetchone()
        isco_code = isco_row['isco_code'] if isco_row else None

        # Asegurar que todos los valores sean float nativos de Python (no numpy.float64)
        return {
            'esco_occupation_uri': mejor_candidato['uri'],
            'esco_occupation_label': mejor_candidato['label'],
            'occupation_match_score': float(mejor_candidato['similarity_score']),
            'rerank_score': float(mejor_candidato['rerank_score']) if mejor_candidato.get('rerank_score') else None,
            'score_titulo': float(score_titulo),
            'score_skills': float(score_skills),
            'score_descripcion': float(score_descripcion),
            'score_final_ponderado': float(score_final),
            'skills_oferta_json': json.dumps(oferta.get('skills_tecnicas', []), ensure_ascii=False),
            'skills_matched_essential': json.dumps(matched_essential, ensure_ascii=False),
            'skills_matched_optional': json.dumps(matched_optional, ensure_ascii=False),
            'skills_cobertura': float(score_skills),
            'match_confirmado': match_confirmado,
            'requiere_revision': requiere_revision,
            'isco_code': isco_code,
            'isco_nivel1': isco_code[1] if isco_code and len(isco_code) > 1 else None,
            'isco_nivel2': isco_code[1:3] if isco_code and len(isco_code) > 2 else None,
            'peso_usado': peso_usado,  # 'normal' o 'fallback'
            'coverage_score': float(coverage_score),  # v8.0: guardar para análisis
        }

    def ejecutar(self):
        """Ejecuta matching multicriteria en todas las ofertas"""
        print("\n" + "=" * 70)
        print("MATCHING MULTICRITERIA ESCO")
        print("Algoritmo: Título (50%) + Skills (40%) + Descripción (10%)")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        self.conectar()
        self.cargar_modelos()

        if not self.cargar_embeddings_esco():
            return False

        # Obtener ofertas
        print("\n[3] PROCESANDO OFERTAS")
        print("=" * 60)

        cursor = self.conn.cursor()
        # Usar ofertas_nlp_latest que prioriza validacion_v7 > ofertas_nlp
        # Incluye coverage_score para ajuste dinámico de pesos
        cursor.execute("""
            SELECT
                o.id_oferta, o.titulo, o.descripcion_utf8,
                n.skills_tecnicas_list, n.soft_skills_list,
                n.source_table, n.nlp_version, n.coverage_score
            FROM ofertas o
            LEFT JOIN ofertas_nlp_latest n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
            WHERE o.titulo IS NOT NULL
            ORDER BY o.id_oferta
        """)
        ofertas = cursor.fetchall()
        print(f"  -> {len(ofertas):,} ofertas a procesar")

        # Procesar ofertas
        batch_size = 20
        for i in tqdm(range(0, len(ofertas), batch_size), desc="  Matching"):
            batch = ofertas[i:i + batch_size]

            for row in batch:
                id_oferta = row['id_oferta']
                titulo = row['titulo']
                descripcion = row['descripcion_utf8'] or ''
                coverage = row['coverage_score'] or 1.0  # Default a 1.0 si no hay

                # Parsear skills de NLP
                skills_tecnicas = []
                if row['skills_tecnicas_list']:
                    try:
                        skills_tecnicas = json.loads(row['skills_tecnicas_list'])
                        if not isinstance(skills_tecnicas, list):
                            skills_tecnicas = [skills_tecnicas]
                    except:
                        pass

                if row['soft_skills_list']:
                    try:
                        soft = json.loads(row['soft_skills_list'])
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
                    self.stats['ofertas_con_nlp'] += 1

                try:
                    # PASO 1: Obtener candidatos por título (BGE-M3)
                    texto_oferta = f"{titulo}. {' '.join(descripcion.split()[:200])}"
                    oferta_embedding = self.embedding_model.encode([texto_oferta])[0]
                    oferta_embedding = oferta_embedding / np.linalg.norm(oferta_embedding)

                    similarities = np.dot(self.esco_embeddings, oferta_embedding)
                    top_indices = np.argsort(similarities)[-10:][::-1]

                    candidatos = []
                    for idx in top_indices:
                        candidatos.append({
                            'uri': self.esco_metadata[idx]['uri'],
                            'label': self.esco_metadata[idx]['label'],
                            'similarity_score': float(similarities[idx]),
                            'isco_code': self.esco_metadata[idx].get('isco_code')
                        })

                    # FILTRO ISCO: Restringir candidatos según keywords del título
                    grupos_permitidos = obtener_grupos_isco_permitidos(titulo)
                    if grupos_permitidos:
                        # Filtrar candidatos que no cumplan con el grupo ISCO
                        candidatos_filtrados = [
                            c for c in candidatos
                            if c.get('isco_code') and c['isco_code'][0] in grupos_permitidos
                        ]
                        # Solo usar filtro si quedan candidatos
                        if candidatos_filtrados:
                            candidatos = candidatos_filtrados

                    # Re-ranking con ESCO-XLM (si disponible)
                    if self.reranker:
                        try:
                            candidatos = self.reranker.rerank(texto_oferta, candidatos, top_k=3)
                        except:
                            pass

                    # Procesar con algoritmo multicriteria (con pesos dinámicos según coverage)
                    resultado = self.procesar_oferta(oferta, candidatos, coverage_score=coverage)

                    # Actualizar base de datos
                    cursor.execute("""
                        UPDATE ofertas_esco_matching SET
                            esco_occupation_uri = ?,
                            esco_occupation_label = ?,
                            occupation_match_score = ?,
                            rerank_score = ?,
                            score_titulo = ?,
                            score_skills = ?,
                            score_descripcion = ?,
                            score_final_ponderado = ?,
                            skills_oferta_json = ?,
                            skills_matched_essential = ?,
                            skills_matched_optional = ?,
                            skills_cobertura = ?,
                            match_confirmado = ?,
                            requiere_revision = ?,
                            isco_code = ?,
                            isco_nivel1 = ?,
                            isco_nivel2 = ?,
                            occupation_match_method = 'v8.1_multicriterio_validado',
                            matching_version = 'v8.1_esco_multicriterio_validado',
                            matching_timestamp = datetime('now')
                        WHERE id_oferta = ?
                    """, (
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
                        resultado['isco_nivel2'],
                        str(id_oferta)
                    ))

                    self.stats['ofertas_procesadas'] += 1
                    if resultado['peso_usado'] in ('fallback', 'medium'):
                        self.stats['con_fallback'] += 1
                    if resultado['match_confirmado']:
                        self.stats['matches_confirmados'] += 1
                    elif resultado['requiere_revision']:
                        self.stats['matches_revision'] += 1
                    else:
                        self.stats['matches_rechazados'] += 1

                except Exception as e:
                    if len(self.stats['errores']) < 10:
                        self.stats['errores'].append(f"{id_oferta}: {e}")

            self.conn.commit()

        # Reporte final
        print("\n" + "=" * 70)
        print("RESUMEN MATCHING MULTICRITERIA (con fallback dinámico)")
        print("=" * 70)
        print(f"  Ofertas procesadas:     {self.stats['ofertas_procesadas']:,}")
        print(f"  Ofertas con NLP skills: {self.stats['ofertas_con_nlp']:,}")
        print(f"  Ofertas con FALLBACK:   {self.stats['con_fallback']:,} (score_skills < 0.35)")
        print(f"\n  Resultados:")
        print(f"    CONFIRMADOS (>75%):   {self.stats['matches_confirmados']:,}")
        print(f"    REVISIÓN (50-75%):    {self.stats['matches_revision']:,}")
        print(f"    RECHAZADOS (<50%):    {self.stats['matches_rechazados']:,}")

        if self.stats['errores']:
            print(f"\n  Errores: {len(self.stats['errores'])}")
            for e in self.stats['errores'][:5]:
                print(f"    - {e}")

        # Estadísticas de scores
        cursor.execute("""
            SELECT
                AVG(score_titulo) as avg_titulo,
                AVG(score_skills) as avg_skills,
                AVG(score_descripcion) as avg_desc,
                AVG(score_final_ponderado) as avg_final
            FROM ofertas_esco_matching
            WHERE score_final_ponderado IS NOT NULL
        """)
        avg_row = cursor.fetchone()
        if avg_row and avg_row['avg_final']:
            print(f"\n  Scores promedio:")
            print(f"    Título (50%):      {avg_row['avg_titulo']:.4f}")
            print(f"    Skills (40%):      {avg_row['avg_skills']:.4f}")
            print(f"    Descripción (10%): {avg_row['avg_desc']:.4f}")
            print(f"    FINAL PONDERADO:   {avg_row['avg_final']:.4f}")

        print("=" * 70)
        self.conn.close()
        return True


if __name__ == '__main__':
    matcher = MultiCriteriaMatcher()
    matcher.ejecutar()
