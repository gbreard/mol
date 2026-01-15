#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
match_ofertas_multicriteria.py
==============================
Matching multicriteria ESCO según PLAN_TECNICO_MOL_v2.0 Sección 5.6

VERSION: v8.4 (2025-12-09)
- PENALIZACION NIVEL JERARQUICO: Detecta nivel en título (Gerente/Ejecutivo/etc)
  y penaliza candidatos ESCO con nivel incompatible
- BYPASS DICCIONARIO ARGENTINO: Si hay match exacto en diccionario_arg_esco,
  usar directamente sin búsqueda semántica (resuelve caso Repositor->Reponedor)
- Integración de diccionario argentino (normalizacion_arg.py)
- BUSQUEDA HIBRIDA: titulo + esco_preferred_label del diccionario
- Boost/Penalty ISCO basado en términos locales (Mozo->5131, etc)
- Usa titulo_limpio de ofertas_nlp cuando está disponible
- Reglas v8.4 con penalizaciones por sector/función incorrectos

v8.1 (2025-11-28):
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
import argparse
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

# Importar reglas de validación v8.4
try:
    from matching_rules_v84 import (
        calcular_ajustes_v84 as calcular_ajustes_v83,  # Alias para compatibilidad
        es_oferta_programa_pasantia
    )
    RULES_AVAILABLE = True
    RULES_VERSION = "v8.4"
except ImportError:
    try:
        # Fallback a v8.3
        from matching_rules_v83 import (
            calcular_ajustes_v83,
            es_oferta_programa_pasantia
        )
        RULES_AVAILABLE = True
        RULES_VERSION = "v8.3"
    except ImportError:
        print("WARNING: matching_rules no disponible. Reglas deshabilitadas.")
        RULES_AVAILABLE = False
        RULES_VERSION = None

# NOTA: ESCO-XLM Reranker eliminado en limpieza de código zombi (2025-12-09)
# Spike MOL-49 demostró que sin reranker hay +31.6% mejor precisión y 4.4x más rápido
# Ver: metrics/spike_reranker_summary.json
RERANKER_AVAILABLE = False

# Experiment logger para timing (MOL-48)
try:
    from experiment_logger import get_logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False

# Normalizacion argentina (diccionario arg -> ESCO)
try:
    from normalizacion_arg import (
        obtener_boost_isco,
        normalizar_termino_argentino,
        buscar_match_diccionario_directo  # v8.3: bypass semántico
    )
    NORMALIZACION_ARG_AVAILABLE = True
except ImportError:
    print("WARNING: normalizacion_arg no disponible. Boost argentino deshabilitado.")
    NORMALIZACION_ARG_AVAILABLE = False

# Config loader para configuración externalizada
try:
    from config_loader import (
        get_config,
        get_pesos,
        get_thresholds,
        get_isco_keywords
    )
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    print("WARNING: config_loader no disponible. Usando valores hardcodeados.")
    CONFIG_LOADER_AVAILABLE = False

# Deteccion de nivel jerarquico v8.4
try:
    from nivel_jerarquico import (
        aplicar_penalizacion_nivel_candidatos,
        detectar_nivel_jerarquico,
        calcular_penalizacion_nivel
    )
    NIVEL_JERARQUICO_AVAILABLE = True
except ImportError:
    print("WARNING: nivel_jerarquico no disponible. Penalización nivel deshabilitada.")
    NIVEL_JERARQUICO_AVAILABLE = False

# Configuración
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
EMBEDDINGS_DIR = Path(__file__).parent / 'embeddings'

# Pesos del algoritmo (PLAN_TECNICO Sección 5.6)
# Carga desde config_loader si disponible, sino usa valores hardcodeados
if CONFIG_LOADER_AVAILABLE:
    _pesos_base = get_pesos('alta')
    PESO_TITULO = _pesos_base['titulo']
    PESO_SKILLS = _pesos_base['skills']
    PESO_DESCRIPCION = _pesos_base['descripcion']

    _thresholds = get_thresholds()
    THRESHOLD_CONFIRMADO_SCORE = _thresholds.get('confirmado_score', 0.60)
    THRESHOLD_CONFIRMADO_COVERAGE = _thresholds.get('confirmado_coverage', 0.40)
    THRESHOLD_REVISION = _thresholds.get('revision', 0.50)

    _pesos_alta = get_pesos('alta')
    _pesos_media = get_pesos('media')
    COVERAGE_ALTA = get_config('pesos_dinamicos.coverage_alta.umbral', 0.8)
    COVERAGE_MEDIA = get_config('pesos_dinamicos.coverage_media.umbral', 0.4)
else:
    # Fallback a valores hardcodeados
    PESO_TITULO = 0.50
    PESO_SKILLS = 0.40
    PESO_DESCRIPCION = 0.10
    THRESHOLD_CONFIRMADO_SCORE = 0.60
    THRESHOLD_CONFIRMADO_COVERAGE = 0.40
    THRESHOLD_REVISION = 0.50
    COVERAGE_ALTA = 0.8
    COVERAGE_MEDIA = 0.4

# Diccionario de keywords -> grupos ISCO permitidos
# Evita matches absurdos (ej: "Gerente de Restaurante" -> vendedor)
# Se carga desde config si disponible, sino usa valores hardcodeados
if CONFIG_LOADER_AVAILABLE:
    _isco_keywords_config = get_isco_keywords()
    ISCO_KEYWORDS = {}
    for grupo_name, grupo_data in _isco_keywords_config.items():
        keywords = tuple(grupo_data.get('keywords', []))
        isco_permitidos = grupo_data.get('isco_permitidos', [])
        if keywords and isco_permitidos:
            ISCO_KEYWORDS[keywords] = isco_permitidos
else:
    ISCO_KEYWORDS = {
        ("gerente", "director", "jefe", "coordinador", "supervisor", "líder", "lider"): ["1"],
        ("ingeniero", "contador", "abogado", "analista", "bioquímico", "bioquimico",
         "médico", "medico", "arquitecto", "químico", "quimico", "farmacéutico", "farmaceutico",
         "psicólogo", "psicologo", "profesor", "docente", "programador", "developer",
         "científico", "cientifico", "economista", "auditor"): ["2"],
        ("técnico", "tecnico", "mecánico", "mecanico", "electricista"): ["3", "7"],
        ("administrativo", "secretario", "secretaria", "recepcionista", "asistente"): ["4"],
        ("vendedor", "repositor", "cajero", "cajera", "mozo", "moza", "mesero", "mesera",
         "cocinero", "cocinera", "chef", "encargado", "asesor comercial"): ["5"],
        ("agricultor", "tractorista", "peón rural", "peon rural"): ["6"],
        ("operario", "soldador", "tornero", "fresador", "matricero", "calderero"): ["7"],
        ("operador", "chofer", "conductor", "maquinista"): ["8"],
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


# NOTA: Clase ESCOReranker eliminada en limpieza de código zombi (2025-12-09)
# Código archivado en: database/archive_old_versions/evaluadores_old/spike_reranker_eval.py


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
        # NOTA: ESCO-XLM reranker eliminado (ver spike MOL-49)

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
        # v8.4: Evaluar top-K candidatos y elegir el mejor que pase las reglas
        TOP_K_CANDIDATOS = 10  # Evaluar los primeros 10 candidatos
        titulo_oferta = oferta.get('titulo', '')
        descripcion_oferta = oferta.get('descripcion', '')

        mejor_candidato = None
        mejor_score_titulo = 0.0
        mejor_ajustes = {}
        mejor_never_confirm = True  # Asumir el peor caso

        # Evaluar top-K candidatos con reglas
        for candidato in esco_candidatos[:TOP_K_CANDIDATOS]:
            # Calcular score de título
            score_titulo_cand = candidato['similarity_score']
            if 'rerank_score' in candidato:
                score_titulo_cand = (candidato['similarity_score'] * 0.7 +
                                    candidato['rerank_score'] * 0.3)

            # Aplicar reglas v8.3 a este candidato
            if RULES_AVAILABLE:
                ajuste_total, ajustes_detalle, never_confirm_cand = calcular_ajustes_v83(
                    titulo_oferta, descripcion_oferta, candidato['label']
                )
            else:
                ajuste_total, ajustes_detalle, never_confirm_cand = 0.0, {}, False

            # Si este candidato NO activa never_confirm, preferirlo
            if not never_confirm_cand:
                # Encontramos un candidato válido
                mejor_candidato = candidato
                mejor_score_titulo = score_titulo_cand
                mejor_ajustes = ajustes_detalle
                mejor_never_confirm = False
                break  # Usar el primer candidato que pase las reglas

            # Si todos activan never_confirm, guardar el de mejor score ajustado
            score_ajustado = score_titulo_cand + ajuste_total
            if mejor_candidato is None or score_ajustado > (mejor_score_titulo + sum(mejor_ajustes.values() if mejor_ajustes else [0])):
                mejor_candidato = candidato
                mejor_score_titulo = score_titulo_cand
                mejor_ajustes = ajustes_detalle
                mejor_never_confirm = never_confirm_cand

        # Fallback: si no hay candidato seleccionado, usar el primero
        if mejor_candidato is None:
            mejor_candidato = esco_candidatos[0]
            mejor_score_titulo = mejor_candidato['similarity_score']
            if 'rerank_score' in mejor_candidato:
                mejor_score_titulo = (mejor_candidato['similarity_score'] * 0.7 +
                                     mejor_candidato['rerank_score'] * 0.3)
            mejor_ajustes = {}
            mejor_never_confirm = False

        # Usar el candidato seleccionado
        score_titulo = mejor_score_titulo

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

        # PASO 4b: Usar ajustes v8.3 calculados en la selección de candidatos
        # (ya calculados durante la evaluación top-K)
        ajustes_reglas = mejor_ajustes
        never_confirm = mejor_never_confirm

        # Aplicar ajuste al score final si hay penalización
        if ajustes_reglas:
            ajuste_total = sum(ajustes_reglas.values())
            score_final = max(0.0, min(1.0, score_final + ajuste_total))

        # Determinar estado del match (v8.3: score + coverage + reglas + never_confirm)
        # CONFIRMADO: score >= 0.60 AND coverage >= 0.40 (y no es pasantía/never_confirm)
        # REVISION: 0.50 <= score < 0.60, O es pasantía/trainee, O never_confirm
        # RECHAZADO: score < 0.50 OR coverage < 0.40

        # v8.3: Revisión forzada para programas de pasantías/trainee O never_confirm
        forzar_revision = never_confirm  # never_confirm de las reglas v8.3
        if RULES_AVAILABLE:
            titulo = oferta.get('titulo', '')
            if es_oferta_programa_pasantia(titulo, ''):
                forzar_revision = True

        if forzar_revision:
            # Nunca auto-confirmar si hay flag never_confirm o es pasantía
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

        # Obtener ISCO code y label
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT isco_code FROM esco_occupations
            WHERE occupation_uri = ?
        """, (mejor_candidato['uri'],))
        isco_row = cursor.fetchone()
        isco_code_raw = isco_row['isco_code'] if isco_row else None
        # Limpiar prefijo "C" del código ISCO (C5223 -> 5223)
        isco_code = isco_code_raw.lstrip('C') if isco_code_raw else None

        # Obtener ISCO label desde hierarchy (usa código con prefijo C)
        isco_label = None
        if isco_code_raw:
            cursor.execute("""
                SELECT preferred_label_es FROM esco_isco_hierarchy
                WHERE isco_code = ?
            """, (isco_code_raw,))
            label_row = cursor.fetchone()
            isco_label = label_row['preferred_label_es'] if label_row else None
            # Capitalizar primera letra
            if isco_label:
                isco_label = isco_label[0].upper() + isco_label[1:]

        # Asegurar que todos los valores sean float nativos de Python (no numpy.float64)
        # Capitalizar label ESCO (primera letra mayúscula)
        esco_label = mejor_candidato['label']
        esco_label = esco_label[0].upper() + esco_label[1:] if esco_label else esco_label

        return {
            'esco_occupation_uri': mejor_candidato['uri'],
            'esco_occupation_label': esco_label,
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
            'isco_nivel1': isco_code[0] if isco_code and len(isco_code) > 0 else None,
            'isco_nivel2': isco_code[0:2] if isco_code and len(isco_code) > 1 else None,
            'isco_label': isco_label,
            'peso_usado': peso_usado,  # 'normal' o 'fallback'
            'coverage_score': float(coverage_score),  # v8.0: guardar para análisis
        }

    def ejecutar(self, filter_ids=None):
        """Ejecuta matching multicriteria en todas las ofertas

        Args:
            filter_ids: Lista de IDs a procesar (opcional). Si None, procesa todas.
        """
        print("\n" + "=" * 70)
        print("MATCHING MULTICRITERIA ESCO")
        print("Algoritmo: Título (50%) + Skills (40%) + Descripción (10%)")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if filter_ids:
            print(f"FILTRO: Solo {len(filter_ids)} IDs específicos")
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

        # Query base - v8.2: incluye titulo_limpio de ofertas_nlp
        query = """
            SELECT
                o.id_oferta, o.titulo,
                COALESCE(o.descripcion_utf8, o.descripcion) as descripcion_utf8,
                n.skills_tecnicas_list, n.soft_skills_list,
                n.source_table, n.nlp_version, n.coverage_score,
                nlp.titulo_limpio
            FROM ofertas o
            LEFT JOIN ofertas_nlp_latest n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
            LEFT JOIN ofertas_nlp nlp ON CAST(o.id_oferta AS TEXT) = nlp.id_oferta
            WHERE o.titulo IS NOT NULL
        """

        # Agregar filtro de IDs si se especifica
        if filter_ids:
            placeholders = ','.join(['?' for _ in filter_ids])
            query += f" AND CAST(o.id_oferta AS TEXT) IN ({placeholders})"
            query += " ORDER BY o.id_oferta"
            cursor.execute(query, filter_ids)
        else:
            query += " ORDER BY o.id_oferta"
            cursor.execute(query)

        ofertas = cursor.fetchall()
        print(f"  -> {len(ofertas):,} ofertas a procesar")

        # Procesar ofertas
        batch_size = 20
        for i in tqdm(range(0, len(ofertas), batch_size), desc="  Matching"):
            batch = ofertas[i:i + batch_size]

            for row in batch:
                id_oferta = row['id_oferta']
                titulo_original = row['titulo']
                titulo_limpio = row['titulo_limpio'] or titulo_original  # v8.2: usar titulo_limpio si existe
                titulo = titulo_limpio
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
                    # v8.3: BYPASS DICCIONARIO ARGENTINO (prioridad absoluta)
                    # Si hay match exacto en diccionario, usar directamente sin búsqueda semántica
                    match_diccionario = None
                    if NORMALIZACION_ARG_AVAILABLE:
                        match_diccionario = buscar_match_diccionario_directo(titulo, self.conn)

                    if match_diccionario:
                        # BYPASS: Usar resultado del diccionario directamente
                        # Crear candidato "fake" con score alto
                        candidatos = [{
                            'uri': match_diccionario['occupation_uri'],
                            'label': match_diccionario['occupation_label'],
                            'similarity_score': 0.95,  # Score alto por match curado
                            'isco_code': match_diccionario['isco_code'],
                            'search_source': 'diccionario_argentino',
                            'termino_argentino': match_diccionario['termino_argentino']
                        }]
                        match_method = 'v8.3_diccionario_argentino'

                    else:
                        # PASO 1: Obtener candidatos por título (BGE-M3)
                        import time
                        bge_start = time.perf_counter()

                        texto_oferta = f"{titulo}. {' '.join(descripcion.split()[:200])}"
                        oferta_embedding = self.embedding_model.encode([texto_oferta])[0]
                        oferta_embedding = oferta_embedding / np.linalg.norm(oferta_embedding)

                        similarities = np.dot(self.esco_embeddings, oferta_embedding)
                        top_indices = np.argsort(similarities)[-10:][::-1]

                        # Log timing BGE-M3 (MOL-48)
                        if LOGGER_AVAILABLE:
                            bge_duration = (time.perf_counter() - bge_start) * 1000
                            get_logger().log_timing("bge_m3_retrieval", bge_duration)

                        candidatos = []
                        for idx in top_indices:
                            candidatos.append({
                                'uri': self.esco_metadata[idx]['uri'],
                                'label': self.esco_metadata[idx]['label'],
                                'similarity_score': float(similarities[idx]),
                                'isco_code': self.esco_metadata[idx].get('isco_code'),
                                'search_source': 'titulo'  # v8.2: marcar origen
                            })

                        # v8.2: BUSQUEDA HIBRIDA con diccionario argentino
                        # Si hay match en diccionario, hacer segunda búsqueda con esco_preferred_label
                        if NORMALIZACION_ARG_AVAILABLE:
                            termino, isco_target, esco_label, _ = normalizar_termino_argentino(titulo, self.conn)
                            if esco_label:
                                # Segunda búsqueda con el label ESCO del diccionario
                                texto_esco = esco_label
                                esco_embedding = self.embedding_model.encode([texto_esco])[0]
                                esco_embedding = esco_embedding / np.linalg.norm(esco_embedding)

                                similarities_esco = np.dot(self.esco_embeddings, esco_embedding)
                                top_indices_esco = np.argsort(similarities_esco)[-10:][::-1]

                                # Agregar candidatos de búsqueda ESCO (evitar duplicados)
                                uris_existentes = {c['uri'] for c in candidatos}
                                for idx in top_indices_esco:
                                    uri = self.esco_metadata[idx]['uri']
                                    if uri not in uris_existentes:
                                        candidatos.append({
                                            'uri': uri,
                                            'label': self.esco_metadata[idx]['label'],
                                            'similarity_score': float(similarities_esco[idx]),
                                            'isco_code': self.esco_metadata[idx].get('isco_code'),
                                            'search_source': 'diccionario_esco'  # v8.2: marcar origen
                                        })
                                        uris_existentes.add(uri)

                                # Reordenar candidatos combinados por score
                                candidatos.sort(key=lambda x: x['similarity_score'], reverse=True)
                                candidatos = candidatos[:15]  # Mantener top-15 combinados

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

                        # BOOST ARGENTINO: Aplicar boost basado en diccionario arg->ESCO
                        if NORMALIZACION_ARG_AVAILABLE:
                            candidatos = obtener_boost_isco(titulo, candidatos, self.conn)

                        # v8.4: PENALIZACION NIVEL JERARQUICO
                        # Penaliza candidatos con nivel jerárquico incompatible
                        # Ej: "Ejecutivo Comercial" -> NO debe ser "Director"
                        if NIVEL_JERARQUICO_AVAILABLE:
                            candidatos = aplicar_penalizacion_nivel_candidatos(titulo, candidatos)

                        # Top 3 candidatos de BGE-M3 (ESCO-XLM reranker eliminado - MOL-49)
                        candidatos = candidatos[:3]
                        match_method = 'v8.4_multicriterio_nivel'

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
                            isco_label = ?,
                            occupation_match_method = ?,
                            matching_version = ?,
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
                        resultado['isco_label'],
                        match_method,  # v8.3: diccionario_argentino o multicriterio_semantico
                        f'{match_method}_validated',  # matching_version
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
    parser = argparse.ArgumentParser(description='Matching multicriteria ESCO')
    parser.add_argument('--ids', nargs='+', type=str,
                        help='IDs específicos a procesar')
    parser.add_argument('--ids-file', type=str,
                        help='Archivo con IDs a procesar (uno por línea)')
    args = parser.parse_args()

    # Cargar IDs si se especifica archivo
    filter_ids = None
    if args.ids:
        filter_ids = args.ids
    elif args.ids_file:
        with open(args.ids_file, 'r') as f:
            filter_ids = [line.strip() for line in f if line.strip()]

    matcher = MultiCriteriaMatcher()
    matcher.ejecutar(filter_ids=filter_ids)
