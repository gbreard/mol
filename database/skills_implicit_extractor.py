#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skills Implicit Extractor v2.0 - Extrae skills ESCO desde título y tareas
============================================================================

VERSION: 2.0.0
FECHA: 2026-01-04
MODELO: BGE-M3 (BAAI/bge-m3)

OBJETIVO:
Extraer skills ESCO implícitas a partir del TÍTULO y las tareas de una oferta.
Basado en la metodología del Excel Gold Set pestaña 17_Skills_Completas_ESCO.

CAMBIO v2.0:
- Ahora usa título_limpio + tareas_explicitas (antes solo tareas)
- Nuevo método extract_skills() para el pipeline v3

FLUJO:
1. Recibe titulo_limpio + tareas_explicitas
2. Para cada texto, genera embedding con BGE-M3
3. Busca skills ESCO más similares (cosine similarity)
4. Retorna skills con score > umbral, indicando origen (titulo/tarea)

Uso:
    from skills_implicit_extractor import SkillsImplicitExtractor

    extractor = SkillsImplicitExtractor()

    # v2.0 - Nuevo método con título + tareas
    skills = extractor.extract_skills(
        titulo_limpio="Responsable de Depósito",
        tareas_explicitas="Control de inventarios; Gestión de equipo"
    )
    # [
    #     {"skill_esco": "gestionar inventario", "score": 0.83, "origen": "tarea"},
    #     {"skill_esco": "liderar equipos", "score": 0.75, "origen": "titulo"},
    #     ...
    # ]
"""

import json
import sys
import os
import warnings
import numpy as np
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer

# Configuración centralizada del modelo de embeddings (E1.1)
sys.path.insert(0, str(Path(__file__).parent.parent / "config"))
try:
    from embedding_config import (
        EMBEDDING_MODEL, EMBEDDING_REVISION,
        EQUIVALENCES_CACHE_TTL_HOURS, EQUIVALENCES_CACHE_PATH,
    )
except ImportError:
    EMBEDDING_MODEL = "BAAI/bge-m3"
    EMBEDDING_REVISION = None
    EQUIVALENCES_CACHE_TTL_HOURS = 24
    EQUIVALENCES_CACHE_PATH = "config/skill_equivalences_lookup.json"

# Categorización jerárquica L1/L2 para dashboards
# v2.0: Usa datos ESCO directos del RDF (sin hardcoding)
from skill_categorizer import get_categorizer

# v2.3: Sistema dual de skills (reglas + semántico)
from skills_rules_matcher import SkillsRulesMatcher, SkillsRuleResult


class SkillsImplicitExtractor:
    """
    Extrae skills ESCO implícitas desde tareas usando embeddings BGE-M3.

    Usa cache a nivel de clase para evitar recargar modelo y embeddings.
    """

    VERSION = "2.7.0"  # v2.7: Trust-source filter (SPEC B v2)

    # Configuración por defecto (E1.1: usa config centralizada)
    # LoRA fine-tuned tiene prioridad si existe en disco
    _PROJECT_ROOT = str(Path(__file__).parent.parent)
    _LORA_PATH = Path(_PROJECT_ROOT) / "data" / "finetuning" / "matching" / "model_lora"
    DEFAULT_MODEL = str(_LORA_PATH) if _LORA_PATH.exists() else EMBEDDING_MODEL
    DEFAULT_MODEL_REVISION = None if _LORA_PATH.exists() else EMBEDDING_REVISION
    DEFAULT_THRESHOLD = 0.40  # Umbral para BGE-M3 base (sin LoRA fine-tuned los scores son más bajos)
    DEFAULT_TOP_K = 3  # Top K skills por tarea

    # Cache a nivel de clase
    _model = None
    _skills_embeddings = None
    _skills_metadata = None
    _skills_weights_config = None  # v2.2: Config de pesos
    _terminology_config = None  # v2.4: Terminología argentina
    _initialized = False

    def __init__(
        self,
        embeddings_path: str = None,
        metadata_path: str = None,
        db_path: str = None,
        threshold: float = None,
        top_k: int = None,
        verbose: bool = False,
        filtrar_por_trust: bool = False
    ):
        """
        Inicializa el extractor.

        Args:
            embeddings_path: Path a embeddings .npy (default: database/embeddings/esco_skills_embeddings_full.npy)
            metadata_path: Path a metadata .json (default: database/embeddings/esco_skills_metadata_full.json)
            db_path: Path a BD (para regenerar embeddings si no existen)
            threshold: Umbral de similitud mínima (default: 0.55)
            top_k: Número máximo de skills por tarea (default: 3)
            verbose: Mostrar mensajes de debug
            filtrar_por_trust: v2.7/SPEC B v2 - si True, descarta skills con trust bajo.
                               Default False: solo anota trust_motivo (telemetría).
        """
        base_path = Path(__file__).parent

        self.embeddings_path = Path(embeddings_path) if embeddings_path else base_path / "embeddings" / "esco_skills_embeddings_full.npy"
        self.metadata_path = Path(metadata_path) if metadata_path else base_path / "embeddings" / "esco_skills_metadata_full.json"
        self.db_path = Path(db_path) if db_path else base_path / "bumeran_scraping.db"

        self.threshold = threshold or self.DEFAULT_THRESHOLD
        self.top_k = top_k or self.DEFAULT_TOP_K
        self.verbose = verbose
        self.filtrar_por_trust = filtrar_por_trust

        # Inicializar (usa cache de clase)
        self._initialize()

    def _initialize(self):
        """Carga modelo y embeddings (usa cache si ya están cargados)."""
        # Cargar modelo (una sola vez)
        if SkillsImplicitExtractor._model is None:
            revision = self.DEFAULT_MODEL_REVISION
            if self.verbose:
                rev_str = f" @ {revision[:12]}" if revision else ""
                print(f"[SKILLS] Cargando modelo {self.DEFAULT_MODEL}{rev_str}...")
            if revision:
                SkillsImplicitExtractor._model = SentenceTransformer(
                    self.DEFAULT_MODEL, revision=revision
                )
            else:
                SkillsImplicitExtractor._model = SentenceTransformer(self.DEFAULT_MODEL)

        self.model = SkillsImplicitExtractor._model

        # Cargar embeddings y metadata
        if SkillsImplicitExtractor._skills_embeddings is None:
            if self.embeddings_path.exists() and self.metadata_path.exists():
                if self.verbose:
                    print(f"[SKILLS] Cargando embeddings desde {self.embeddings_path}...")
                SkillsImplicitExtractor._skills_embeddings = np.load(str(self.embeddings_path))
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    SkillsImplicitExtractor._skills_metadata = json.load(f)
            else:
                if self.verbose:
                    print(f"[SKILLS] Embeddings no encontrados, se requiere generación previa")
                SkillsImplicitExtractor._skills_embeddings = np.array([])
                SkillsImplicitExtractor._skills_metadata = []

        self.embeddings = SkillsImplicitExtractor._skills_embeddings
        self.metadata = SkillsImplicitExtractor._skills_metadata

        # E1.3: Verificar compatibilidad modelo ↔ corpus
        if self.embeddings.size > 0:
            self._verify_corpus_compatibility()

        # v2.2: Cargar config de pesos para skills genéricas
        if SkillsImplicitExtractor._skills_weights_config is None:
            weights_path = Path(__file__).parent.parent / "config" / "skills_weights.json"
            if weights_path.exists():
                with open(weights_path, 'r', encoding='utf-8') as f:
                    SkillsImplicitExtractor._skills_weights_config = json.load(f)
                if self.verbose:
                    print(f"[SKILLS] Config pesos cargado: {len(SkillsImplicitExtractor._skills_weights_config.get('skills_genericas', {}).get('lista', []))} skills genéricas")
            else:
                SkillsImplicitExtractor._skills_weights_config = {}

        self.weights_config = SkillsImplicitExtractor._skills_weights_config

        # v2.4: Cargar terminología argentina
        if SkillsImplicitExtractor._terminology_config is None:
            terminology_path = Path(__file__).parent.parent / "config" / "terminologia_argentina_skills.json"
            if terminology_path.exists():
                with open(terminology_path, 'r', encoding='utf-8') as f:
                    SkillsImplicitExtractor._terminology_config = json.load(f)
                if self.verbose:
                    terminos = SkillsImplicitExtractor._terminology_config.get('terminos', {})
                    print(f"[SKILLS] Terminología argentina cargada: {len(terminos)} términos")
            else:
                SkillsImplicitExtractor._terminology_config = {"terminos": {}}

        self.terminology_config = SkillsImplicitExtractor._terminology_config

        # v2.6+cache: Cargar tabla de equivalencias (URI → grupo) con cache local
        if not hasattr(SkillsImplicitExtractor, '_equiv_lookup') or SkillsImplicitExtractor._equiv_lookup is None:
            SkillsImplicitExtractor._equiv_lookup = {}
            SkillsImplicitExtractor._equiv_groups = {}
            force_refresh = getattr(SkillsImplicitExtractor, '_force_refresh_cache', False)
            try:
                self._load_equivalences_cached(force_refresh=force_refresh)
            except Exception as e:
                if self.verbose:
                    print(f"[SKILLS] WARN: Error cargando equivalencias: {e}")

        self.equiv_lookup = getattr(SkillsImplicitExtractor, '_equiv_lookup', {}) or {}
        self.equiv_groups = getattr(SkillsImplicitExtractor, '_equiv_groups', {}) or {}

        # v2.5: Cargar sinónimos argentinos para skills (mapeo directo)
        if not hasattr(SkillsImplicitExtractor, '_sinonimos_skills') or SkillsImplicitExtractor._sinonimos_skills is None:
            sinonimos_path = Path(__file__).parent.parent / "config" / "sinonimos_skills_argentinos.json"
            if sinonimos_path.exists():
                with open(sinonimos_path, 'r', encoding='utf-8') as f:
                    SkillsImplicitExtractor._sinonimos_skills = json.load(f)
                if self.verbose:
                    tareas = len(SkillsImplicitExtractor._sinonimos_skills.get('tareas_a_skills', {}))
                    soft = len(SkillsImplicitExtractor._sinonimos_skills.get('soft_skills_argentinas', {}))
                    print(f"[SKILLS] Sinónimos argentinos cargados: {tareas} tareas + {soft} soft skills")
            else:
                SkillsImplicitExtractor._sinonimos_skills = {"tareas_a_skills": {}, "soft_skills_argentinas": {}}

        self.sinonimos_skills = SkillsImplicitExtractor._sinonimos_skills

        SkillsImplicitExtractor._initialized = True

        # Registrar timestamp de carga de equivalencias (para staleness check)
        from datetime import datetime, timezone
        SkillsImplicitExtractor._equiv_loaded_at = datetime.now(timezone.utc)

        if self.verbose:
            print(f"[SKILLS] Inicializado: {len(self.metadata)} skills, umbral={self.threshold}")

    def _extract_terminology_skills(
        self,
        texto: str,
        area_funcional: str = None
    ) -> List[Dict]:
        """
        v2.4: Extrae skills basadas en terminología argentina.

        Busca términos locales (picking, zorra, RF, etc.) y retorna
        las skills ESCO asociadas con alta confianza.

        Args:
            texto: Texto a analizar (título o tareas)
            area_funcional: Área funcional para filtrar por contexto

        Returns:
            Lista de skills con origen='terminologia'
        """
        if not texto:
            return []

        terminos = self.terminology_config.get('terminos', {})
        if not terminos:
            return []

        texto_lower = texto.lower()
        skills_encontradas = []
        skills_vistas = set()

        for termino, config in terminos.items():
            # Verificar si el término o sus aliases están en el texto
            terminos_a_buscar = [termino.lower()]
            aliases = config.get('aliases', [])
            terminos_a_buscar.extend([a.lower() for a in aliases])

            encontrado = any(t in texto_lower for t in terminos_a_buscar)

            if not encontrado:
                continue

            # Verificar contexto de área si está definido
            contexto_areas = config.get('contexto_area', [])
            if contexto_areas and area_funcional:
                area_lower = area_funcional.lower()
                if not any(ctx.lower() in area_lower or area_lower in ctx.lower()
                          for ctx in contexto_areas):
                    continue

            # Agregar skills asociadas
            for skill_data in config.get('skills_esco', []):
                skill_label = skill_data.get('skill', '')
                skill_uri = skill_data.get('uri', '')

                skill_key = skill_label.lower()
                if skill_key in skills_vistas:
                    continue

                skills_vistas.add(skill_key)

                skills_encontradas.append({
                    "skill_esco": skill_label,
                    "skill_uri": skill_uri,
                    "score": 0.95,  # Alta confianza para terminología
                    "score_ponderado": 0.95,
                    "peso": 1.0,
                    "origen": "terminologia",
                    "termino_fuente": termino,
                    "texto_fuente": texto[:100]
                })

                if self.verbose:
                    print(f"[TERM-ARG] '{termino}' -> '{skill_label}' (score=0.95)")

        return skills_encontradas

    def extract_from_tasks(
        self,
        tareas_explicitas: str,
        top_k: int = None,
        threshold: float = None,
        track_failures: bool = False
    ):
        """
        Extrae skills ESCO implícitas desde las tareas de una oferta.

        Args:
            tareas_explicitas: String con tareas separadas por punto y coma
            top_k: Override del número máximo de skills por tarea
            threshold: Override del umbral de similitud
            track_failures: Si True, retorna tupla (matcheadas, fallidas)

        Returns:
            Si track_failures=False: Lista de dicts con: tarea, skill_esco, skill_uri, score, origen
            Si track_failures=True: Tupla (matcheadas, fallidas)
        """
        empty = ([], []) if track_failures else []
        if not tareas_explicitas or not self.embeddings.size:
            return empty

        top_k = top_k or self.top_k
        threshold = threshold or self.threshold

        # Separar tareas
        tareas = [t.strip() for t in tareas_explicitas.split(';') if t.strip()]

        if not tareas:
            return empty

        skills_implicitas = []
        tareas_fallidas = []
        skills_vistas = set()  # Para evitar duplicados

        # v2.5: Lookup sinónimos argentinos (prioridad sobre BGE-M3)
        sinonimos_tareas = self.sinonimos_skills.get('tareas_a_skills', {})
        sinonimos_soft = self.sinonimos_skills.get('soft_skills_argentinas', {})
        sinonimos_all = {**sinonimos_tareas, **sinonimos_soft}

        for tarea in tareas:
            # Primero: buscar match directo en sinónimos argentinos
            tarea_lower = tarea.lower().strip()
            match_sinonimo = sinonimos_all.get(tarea_lower)
            if match_sinonimo and match_sinonimo.lower() not in skills_vistas:
                skills_vistas.add(match_sinonimo.lower())
                skills_implicitas.append({
                    'tarea': tarea,
                    'skill_esco': match_sinonimo,
                    'skill_uri': None,
                    'score': 0.99,
                    'origen': 'sinonimo_argentino'
                })
                if self.verbose:
                    print(f"[SKILLS] '{tarea}' -> '{match_sinonimo}' (sinónimo argentino)")
                continue

            # Fallback: Generar embedding de la tarea
            tarea_emb = self.model.encode(tarea, normalize_embeddings=True)

            # Calcular similitud coseno con todas las skills
            similarities = np.dot(self.embeddings, tarea_emb)

            # Obtener top K indices ordenados por similitud
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # M-06: Verificar si algún candidato supera el umbral
            tarea_matcheo = False

            for idx in top_indices:
                score = round(float(similarities[idx]), 4)

                if score < threshold:
                    continue

                tarea_matcheo = True
                skill_meta = self.metadata[idx]
                skill_label = skill_meta.get('label', skill_meta.get('preferred_label_es', ''))

                # Evitar duplicados
                if skill_label.lower() in skills_vistas:
                    continue

                skills_vistas.add(skill_label.lower())

                skills_implicitas.append({
                    "tarea": tarea[:100],  # Truncar para BD
                    "skill_esco": skill_label,
                    "skill_uri": skill_meta.get('uri', skill_meta.get('skill_uri', '')),
                    "score": score,
                    "origen": "IMPLICITA"
                })

                if self.verbose:
                    print(f"[SKILLS] '{tarea[:50]}...' -> '{skill_label}' (score={score:.3f})")

            # M-06: Registrar tarea fallida si ningún candidato superó el umbral
            if track_failures and not tarea_matcheo:
                best_idx = top_indices[0] if len(top_indices) > 0 else None
                if best_idx is not None:
                    best_score = float(similarities[best_idx])
                    best_meta = self.metadata[best_idx]
                    tareas_fallidas.append({
                        "tarea_texto": tarea[:200],
                        "mejor_skill_uri": best_meta.get('uri', best_meta.get('skill_uri', '')),
                        "mejor_skill_label": best_meta.get('label', best_meta.get('preferred_label_es', '')),
                        "mejor_score": round(best_score, 4),
                        "threshold_usado": threshold,
                        "gap_al_umbral": round(threshold - best_score, 4)
                    })
                else:
                    tareas_fallidas.append({
                        "tarea_texto": tarea[:200],
                        "mejor_skill_uri": None,
                        "mejor_skill_label": None,
                        "mejor_score": 0.0,
                        "threshold_usado": threshold,
                        "gap_al_umbral": round(threshold, 4)
                    })

        if track_failures:
            return (skills_implicitas, tareas_fallidas)
        return skills_implicitas

    def _get_skill_weight(
        self,
        skill_label: str,
        sector_empresa: str = None,
        nivel_seniority: str = None,
        area_funcional: str = None
    ) -> float:
        """
        v2.2: Calcula el peso de una skill según si es genérica o específica.

        Skills genéricas (trabajo en equipo, comunicación, etc.) tienen peso reducido.
        Skills contextuales dependen del sector/seniority/área.

        Returns:
            Peso entre 0.0 y 1.0
        """
        if not self.weights_config:
            return 1.0

        skill_lower = skill_label.lower().strip()

        # 1. Verificar si es skill genérica
        skills_genericas = self.weights_config.get("skills_genericas", {})
        lista_genericas = [s.lower() for s in skills_genericas.get("lista", [])]
        peso_generico = skills_genericas.get("peso", 0.5)

        if skill_lower in lista_genericas:
            return peso_generico

        # 2. Verificar reglas contextuales
        for regla in self.weights_config.get("skills_contextuales", {}).get("reglas", []):
            skill_regla = regla.get("skill", "").lower()
            if skill_lower == skill_regla or skill_regla in skill_lower:
                # Verificar condición sector
                if "si_sector_es" in regla and sector_empresa:
                    if sector_empresa in regla["si_sector_es"]:
                        return regla.get("entonces_peso", 1.0)
                    else:
                        return regla.get("sino_peso", 0.5)

                # Verificar condición seniority
                if "si_seniority_es" in regla and nivel_seniority:
                    if nivel_seniority.lower() in [s.lower() for s in regla["si_seniority_es"]]:
                        return regla.get("entonces_peso", 1.0)
                    else:
                        return regla.get("sino_peso", 0.5)

                # Verificar condición área
                if "si_area_es" in regla and area_funcional:
                    if area_funcional in regla["si_area_es"]:
                        return regla.get("entonces_peso", 1.0)
                    else:
                        return regla.get("sino_peso", 0.5)

        # Por defecto, peso 1.0 (skill específica)
        return 1.0

    def _classify_skill_trust(
        self,
        skill: Dict,
        oferta_context: Dict
    ) -> Tuple[bool, str]:
        """
        v2.7 / SPEC B v2 — Clasifica la confianza de una skill según su origen.

        No consulta ESCO oficial ni depende del ISCO: evalúa solo el `origen`
        de la skill y la calidad del `texto_fuente` que la generó.

        Args:
            skill: dict con al menos origen, score, texto_fuente
            oferta_context: dict con titulo_limpio, tareas_explicitas, skills_tecnicas_list

        Returns:
            (trust, motivo). trust=True mantiene la skill; False la descarta
            cuando filtrar_por_trust está activo.
        """
        origen = skill.get('origen', 'desconocido')
        texto_fuente = skill.get('texto_fuente', '') or ''
        score = skill.get('score', 0) or 0

        # 1. Origen "regla" / "terminologia_argentina" → siempre confianza alta
        if origen in ('regla', 'terminologia_argentina', 'terminologia',
                      'sinonimo_argentino', 'regla_cynthia', 'regla_issue'):
            return True, 'origen_reglas'

        # 2. Origen "skills_nlp" o "soft_skills_nlp" → LLM las identificó
        if origen in ('skills_nlp', 'soft_skills_nlp'):
            return True, 'origen_llm_detectado'

        # 3. Origen "tarea" con tarea sustantiva (≥20 chars)
        if origen == 'tarea':
            tarea_clean = texto_fuente.strip()
            if len(tarea_clean) >= 20:
                return True, 'origen_tarea_real'
            if score >= 0.75:
                return True, 'origen_tarea_corta_score_alto'
            return False, 'origen_tarea_corta_score_bajo'

        # 4. Origen "titulo" → depende del contexto
        if origen == 'titulo':
            titulo_len = len((oferta_context.get('titulo_limpio') or '').strip())
            tiene_tareas = bool((oferta_context.get('tareas_explicitas') or '').strip())
            tiene_skills_nlp = bool(oferta_context.get('skills_tecnicas_list'))

            # Si ya hay tareas o skills_nlp, las de título son secundarias → exigir score alto
            if (tiene_tareas or tiene_skills_nlp) and score < 0.80:
                return False, 'titulo_redundante_score_bajo'

            # Sin otras fuentes, el título es lo único
            if titulo_len >= 30:
                if score >= 0.70:
                    return True, 'titulo_solo_fuente_score_ok'
                return False, 'titulo_solo_fuente_score_bajo'
            else:
                if score >= 0.85:
                    return True, 'titulo_corto_score_muy_alto'
                return False, 'titulo_corto_score_medio'

        # Fallback: score alto o descartar
        if score >= 0.80:
            return True, 'fallback_score_alto'
        return False, 'fallback_origen_desconocido'

    def extract_skills(
        self,
        titulo_limpio: str,
        tareas_explicitas: str = None,
        skills_nlp: List[str] = None,
        soft_skills_nlp: List[str] = None,
        sector_empresa: str = None,
        nivel_seniority: str = None,
        area_funcional: str = None,
        top_k: int = None,
        threshold: float = None,
        track_failures: bool = False
    ):
        """
        v2.2: Extrae skills ESCO con ponderación de skills genéricas.

        El título aporta contexto general del rol.
        Las tareas aportan detalle específico.
        Las skills_nlp y soft_skills_nlp (si existen) enriquecen con lo que el LLM detectó.

        v2.1 (2026-01-14): Agregado skills_nlp para usar skills_tecnicas_list del NLP.
        v2.2 (2026-01-14): Agregado ponderación de skills genéricas vs específicas.
                          Skills como "trabajo en equipo" tienen peso 0.5x.
                          Agregado soft_skills_nlp para usar soft_skills_list del NLP.

        Args:
            titulo_limpio: Título limpio de la oferta (requerido)
            tareas_explicitas: String con tareas separadas por ; (opcional)
            skills_nlp: Lista de skills técnicas extraídas por NLP (skills_tecnicas_list)
            soft_skills_nlp: Lista de soft skills extraídas por NLP (soft_skills_list)
            sector_empresa: Sector de la empresa (para ponderación contextual)
            nivel_seniority: Nivel de seniority (para ponderación contextual)
            area_funcional: Área funcional (para ponderación contextual)
            top_k: Override del número máximo de skills por texto
            threshold: Override del umbral de similitud
            track_failures: Si True, retorna tupla (matcheadas, fallidas)

        Returns:
            Si track_failures=False: Lista de dicts con: skill_esco, skill_uri, score, score_ponderado, peso, origen
            Si track_failures=True: Tupla (matcheadas, fallidas)
        """
        if not self.embeddings.size:
            return ([], []) if track_failures else []

        top_k = top_k or self.top_k
        threshold = threshold or self.threshold

        # v2.4: PASO 0 - Extraer skills por terminología argentina PRIMERO
        # Estas tienen prioridad sobre semántico
        skills_terminologia = []
        skills_term_vistas = set()

        # Buscar en título
        if titulo_limpio:
            term_skills = self._extract_terminology_skills(titulo_limpio, area_funcional)
            for s in term_skills:
                if s['skill_esco'].lower() not in skills_term_vistas:
                    skills_terminologia.append(s)
                    skills_term_vistas.add(s['skill_esco'].lower())

        # Buscar en tareas
        if tareas_explicitas:
            term_skills = self._extract_terminology_skills(tareas_explicitas, area_funcional)
            for s in term_skills:
                if s['skill_esco'].lower() not in skills_term_vistas:
                    skills_terminologia.append(s)
                    skills_term_vistas.add(s['skill_esco'].lower())

        # Preparar textos a procesar (para semántico)
        textos = []

        # 1. Título siempre presente (si existe)
        if titulo_limpio and titulo_limpio.strip():
            textos.append(("titulo", titulo_limpio.strip()))

        # 2. Tareas si existen
        if tareas_explicitas:
            for tarea in tareas_explicitas.split(';'):
                tarea = tarea.strip()
                if tarea:
                    textos.append(("tarea", tarea))

        # 3. Skills NLP (v2.1): usar skills extraídas por LLM como contexto adicional
        # Esto es CRÍTICO cuando tareas_explicitas es NULL pero el LLM detectó skills
        if skills_nlp:
            for skill in skills_nlp:
                skill = skill.strip() if isinstance(skill, str) else str(skill)
                if skill and skill.lower() not in ['null', 'none', '']:
                    textos.append(("skills_nlp", skill))

        # 4. Soft Skills NLP (v2.2): usar soft skills extraídas por LLM
        # Las soft skills ayudan a identificar mejor roles de gestión/liderazgo
        if soft_skills_nlp:
            for skill in soft_skills_nlp:
                skill = skill.strip() if isinstance(skill, str) else str(skill)
                if skill and skill.lower() not in ['null', 'none', '']:
                    textos.append(("soft_skills_nlp", skill))

        if not textos and not skills_terminologia:
            return ([], []) if track_failures else []

        # v2.4: Iniciar con skills de terminología (ya encontradas)
        skills_extraidas = list(skills_terminologia)
        textos_fallidos = []
        skills_vistas = set(skills_term_vistas)  # Para evitar duplicados con semántico

        for origen, texto in textos:
            # Generar embedding del texto
            texto_emb = self.model.encode(texto, normalize_embeddings=True)

            # Calcular similitud coseno con todas las skills
            similarities = np.dot(self.embeddings, texto_emb)

            # Obtener top K indices ordenados por similitud
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # M-06: Verificar si algún candidato supera el umbral
            texto_matcheo = False

            for idx in top_indices:
                score = round(float(similarities[idx]), 4)

                if score < threshold:
                    continue

                texto_matcheo = True
                skill_meta = self.metadata[idx]
                skill_label = skill_meta.get('label', skill_meta.get('preferred_label_es', ''))
                skill_uri = skill_meta.get('uri', skill_meta.get('skill_uri', ''))

                # v2.6: Dedup por grupo de equivalencia (si existe)
                equiv_group = self.equiv_lookup.get(skill_uri)
                skill_key = equiv_group if equiv_group else skill_label.lower()
                if skill_key in skills_vistas:
                    continue

                skills_vistas.add(skill_key)

                # v2.6: Si tiene equivalencia, usar label representante
                if equiv_group and equiv_group in self.equiv_groups:
                    group_info = self.equiv_groups[equiv_group]
                    skill_label = group_info['label']  # label argentino o representante

                # v2.2: Calcular peso según si es skill genérica o específica
                peso = self._get_skill_weight(
                    skill_label,
                    sector_empresa=sector_empresa,
                    nivel_seniority=nivel_seniority,
                    area_funcional=area_funcional
                )
                score_ponderado = score * peso

                skills_extraidas.append({
                    "skill_esco": skill_label,
                    "skill_uri": skill_uri,
                    "score": score,
                    "score_ponderado": round(score_ponderado, 4),  # v2.2
                    "peso": peso,  # v2.2
                    "origen": origen,  # "titulo" o "tarea"
                    "texto_fuente": texto[:100]  # Truncar para debugging
                })

                if self.verbose:
                    peso_tag = " [GEN]" if peso < 1.0 else ""
                    print(f"[SKILLS] [{origen}] '{texto[:40]}...' -> '{skill_label}' (score={score:.3f}, peso={peso}){peso_tag}")

            # M-06: Registrar texto fallido si ningún candidato superó el umbral
            if track_failures and not texto_matcheo:
                best_idx = top_indices[0] if len(top_indices) > 0 else None
                if best_idx is not None:
                    best_score = float(similarities[best_idx])
                    best_meta = self.metadata[best_idx]
                    textos_fallidos.append({
                        "tarea_texto": texto[:200],
                        "tarea_origen": origen,
                        "mejor_skill_uri": best_meta.get('uri', best_meta.get('skill_uri', '')),
                        "mejor_skill_label": best_meta.get('label', best_meta.get('preferred_label_es', '')),
                        "mejor_score": round(best_score, 4),
                        "threshold_usado": threshold,
                        "gap_al_umbral": round(threshold - best_score, 4)
                    })
                else:
                    textos_fallidos.append({
                        "tarea_texto": texto[:200],
                        "tarea_origen": origen,
                        "mejor_skill_uri": None,
                        "mejor_skill_label": None,
                        "mejor_score": 0.0,
                        "threshold_usado": threshold,
                        "gap_al_umbral": round(threshold, 4)
                    })

        # v2.2: Ordenar por score_ponderado descendente (skills genéricas bajan en el ranking)
        skills_extraidas.sort(key=lambda x: x['score_ponderado'], reverse=True)

        # v2.7 / SPEC B v2: Clasificar trust-source para cada skill
        oferta_context = {
            'titulo_limpio': titulo_limpio or '',
            'tareas_explicitas': tareas_explicitas or '',
            'skills_tecnicas_list': skills_nlp or [],
        }

        skills_filtradas = []
        descartadas = 0
        for s in skills_extraidas:
            trust, motivo = self._classify_skill_trust(s, oferta_context)
            s['trust'] = bool(trust)
            s['trust_motivo'] = motivo
            if self.filtrar_por_trust and not trust:
                descartadas += 1
                continue
            skills_filtradas.append(s)

        if self.filtrar_por_trust:
            if self.verbose and descartadas:
                print(f"[TRUST] Descartadas {descartadas}/{len(skills_extraidas)} skills por baja confianza")
            skills_extraidas = skills_filtradas

        # Agregar categorías L1/L2 para dashboards
        try:
            categorizer = get_categorizer()
            for skill in skills_extraidas:
                categoria = categorizer.categorize(
                    skill_uri=skill.get("skill_uri", ""),
                    skill_label=skill.get("skill_esco", "")
                )
                skill.update(categoria)
        except Exception as e:
            if self.verbose:
                print(f"[WARN] Error en categorización: {e}")

        if track_failures:
            return (skills_extraidas, textos_fallidos)
        return skills_extraidas

    def get_skills_for_offer(
        self,
        skills_declaradas: List[str],
        tareas_explicitas: str,
        merge: bool = True
    ) -> Tuple[List[str], List[Dict]]:
        """
        Combina skills declaradas con skills implícitas extraídas de tareas.

        Args:
            skills_declaradas: Lista de skills ya declaradas en la oferta
            tareas_explicitas: String con tareas separadas por ;
            merge: Si True, retorna lista unificada; si False, retorna separadas

        Returns:
            (skills_all, skills_implicitas_detalle)
        """
        # Normalizar skills declaradas
        declaradas_norm = {s.lower().strip() for s in skills_declaradas if s}

        # Extraer implícitas
        implicitas = self.extract_from_tasks(tareas_explicitas)

        # Filtrar implícitas que ya están declaradas
        implicitas_nuevas = [
            s for s in implicitas
            if s['skill_esco'].lower() not in declaradas_norm
        ]

        if merge:
            # Retornar lista unificada
            all_skills = list(skills_declaradas) + [s['skill_esco'] for s in implicitas_nuevas]
            return all_skills, implicitas_nuevas
        else:
            return skills_declaradas, implicitas_nuevas

    @classmethod
    def clear_cache(cls):
        """Limpia el cache (útil para tests)."""
        cls._model = None
        cls._skills_embeddings = None
        cls._skills_metadata = None
        cls._initialized = False

    def _verify_corpus_compatibility(self):
        """
        E1.3: Verifica que el modelo BGE-M3 cargado coincide con el que generó los embeddings.
        Lee el SHA esperado desde corpus_manifest.json y lo compara con el modelo en cache.
        Si no coinciden → RuntimeError. Si SHA desconocido → warning.
        """
        manifest_path = Path(__file__).parent / "embeddings" / "corpus_manifest.json"
        if not manifest_path.exists():
            return  # Sin manifiesto, no se puede verificar

        try:
            manifest = json.load(open(manifest_path))
            expected_revision = manifest.get('esco_skills', {}).get('model_revision', '')
        except (json.JSONDecodeError, KeyError):
            return  # Manifiesto corrupto, no bloquear

        if not expected_revision:
            return

        # Leer SHA del modelo desde cache de HuggingFace
        actual_revision = None
        hf_ref = Path(os.path.expanduser(
            "~/.cache/huggingface/hub/models--BAAI--bge-m3/refs/main"
        ))
        try:
            if hf_ref.exists():
                actual_revision = hf_ref.read_text().strip()
        except Exception:
            pass

        # Fallback: huggingface_hub si disponible
        if not actual_revision:
            try:
                from huggingface_hub import model_info
                info = model_info("BAAI/bge-m3")
                actual_revision = info.sha
            except Exception:
                pass

        if not actual_revision:
            warnings.warn(
                "[SKILLS] No se pudo determinar la revisión del modelo BGE-M3 cargado. "
                "No se puede verificar compatibilidad con embeddings.",
                UserWarning
            )
            return

        if actual_revision != expected_revision:
            raise RuntimeError(
                f"INCOMPATIBILIDAD DE EMBEDDINGS: "
                f"Modelo cargado ({actual_revision[:8]}) difiere del que generó el corpus ({expected_revision[:8]}). "
                f"Regenerar con: python scripts/db/regenerate_all_embeddings.py"
            )

        if self.verbose:
            print(f"[SKILLS] Compatibilidad verificada: modelo y corpus usan {actual_revision[:12]}")

    # ============================================================
    # Cache local de equivalencias con TTL
    # ============================================================

    def _load_equivalences_cached(self, force_refresh: bool = False):
        """
        Carga equivalencias con cache local (TTL configurable).

        Orden:
        1. Si cache local existe y tiene < EQUIVALENCES_CACHE_TTL_HOURS → cargar local
        2. Si no → cargar desde Supabase → guardar cache local
        3. Si Supabase falla → cargar cache local aunque esté vencido (stale)
        """
        from datetime import datetime, timezone

        cache_path = Path(__file__).parent.parent / EQUIVALENCES_CACHE_PATH

        # Check if local cache is valid
        if not force_refresh and cache_path.exists():
            try:
                cache_data = json.loads(cache_path.read_text(encoding='utf-8'))
                cache_ts = cache_data.get('_cache_timestamp', '')
                if cache_ts:
                    cache_time = datetime.fromisoformat(cache_ts)
                    age_hours = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600
                    if age_hours < EQUIVALENCES_CACHE_TTL_HOURS:
                        # Cache is fresh — use it
                        self._apply_cache_data(cache_data)
                        if self.verbose:
                            print(f"[SKILLS] Equivalencias desde cache local ({age_hours:.1f}h, {len(SkillsImplicitExtractor._equiv_lookup)} URIs)")
                        return
                    elif self.verbose:
                        print(f"[SKILLS] Cache vencido ({age_hours:.1f}h > {EQUIVALENCES_CACHE_TTL_HOURS}h), recargando...")
            except Exception as e:
                if self.verbose:
                    print(f"[SKILLS] WARN: Cache corrupto, recargando: {e}")

        # Load from Supabase
        loaded = self._load_equivalences_from_supabase()

        if loaded:
            # Save cache
            self._save_equivalences_cache(cache_path)
            if self.verbose:
                print(f"[SKILLS] Equivalencias desde Supabase: {len(SkillsImplicitExtractor._equiv_lookup)} URIs, {len(SkillsImplicitExtractor._equiv_groups)} grupos (cache guardado)")
        elif cache_path.exists():
            # Supabase failed but stale cache exists — use it
            try:
                cache_data = json.loads(cache_path.read_text(encoding='utf-8'))
                self._apply_cache_data(cache_data)
                if self.verbose:
                    print(f"[SKILLS] WARN: Supabase no disponible, usando cache stale ({len(SkillsImplicitExtractor._equiv_lookup)} URIs)")
            except Exception:
                pass

    def _load_equivalences_from_supabase(self) -> bool:
        """Load equivalences from Supabase. Returns True on success."""
        try:
            config_path = Path(__file__).parent.parent / "config" / "supabase_config.json"
            if not config_path.exists():
                return False

            supabase_config = json.loads(config_path.read_text())
            from supabase import create_client
            client = create_client(supabase_config['url'], supabase_config['service_role_key'])

            # Paginate lookups
            all_lookups = []
            offset = 0
            while True:
                batch = client.table('skill_equivalence_lookup').select(
                    'skill_uri,equivalence_id'
                ).range(offset, offset + 999).execute()
                all_lookups.extend(batch.data or [])
                if len(batch.data or []) < 1000:
                    break
                offset += 1000

            for row in all_lookups:
                SkillsImplicitExtractor._equiv_lookup[row['skill_uri']] = row['equivalence_id']

            # Load group labels
            groups = client.table('skill_equivalences').select(
                'id,label_representante,label_argentino'
            ).execute()
            for row in (groups.data or []):
                SkillsImplicitExtractor._equiv_groups[row['id']] = {
                    'label': row.get('label_argentino') or row['label_representante'],
                    'label_original': row['label_representante'],
                }

            return len(SkillsImplicitExtractor._equiv_lookup) > 0
        except Exception as e:
            if self.verbose:
                print(f"[SKILLS] WARN: No se pudieron cargar equivalencias desde Supabase: {e}")
            return False

    def _save_equivalences_cache(self, cache_path: Path):
        """Save current equivalences to local JSON cache."""
        from datetime import datetime, timezone
        import hashlib

        lookups = [
            {'skill_uri': uri, 'equivalence_id': eid}
            for uri, eid in SkillsImplicitExtractor._equiv_lookup.items()
        ]
        groups = [
            {'id': gid, 'label': info.get('label', ''), 'label_original': info.get('label_original', '')}
            for gid, info in SkillsImplicitExtractor._equiv_groups.items()
        ]

        cache_data = {
            '_cache_timestamp': datetime.now(timezone.utc).isoformat(),
            '_cache_version': hashlib.md5(json.dumps(len(lookups)).encode()).hexdigest()[:8],
            '_cache_uris': len(lookups),
            '_cache_groups': len(groups),
            'lookups': lookups,
            'groups': groups,
        }

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
        except Exception as e:
            if self.verbose:
                print(f"[SKILLS] WARN: No se pudo guardar cache: {e}")

    def _apply_cache_data(self, cache_data: dict):
        """Apply cached equivalences data to class-level attributes."""
        for entry in cache_data.get('lookups', []):
            SkillsImplicitExtractor._equiv_lookup[entry['skill_uri']] = entry.get('equivalence_id')
        for entry in cache_data.get('groups', []):
            SkillsImplicitExtractor._equiv_groups[entry['id']] = {
                'label': entry.get('label', ''),
                'label_original': entry.get('label_original', ''),
            }

    # ============================================================
    # E2.2: Argentino boost — rerank skills post-matching
    # ============================================================

    _argentino_cache: Dict[str, Dict] = None  # occupation_uri → {skills: {esco_uri: frequency}, max_freq: int}

    @classmethod
    def _load_argentino_cache(cls, verbose: bool = False) -> Dict[str, Dict]:
        """
        Carga esco_argentino desde Supabase y construye cache de boost por ocupación.

        Cache format:
            {occupation_uri: {"skills": {esco_uri: frequency, ...}, "max_freq": int}}

        Degrada sin error si Supabase no está disponible.
        """
        if cls._argentino_cache is not None:
            return cls._argentino_cache

        cls._argentino_cache = {}
        try:
            config_path = Path(__file__).parent.parent / "config" / "supabase_config.json"
            if not config_path.exists():
                if verbose:
                    print("[BOOST] WARN: supabase_config.json no encontrado, boost deshabilitado")
                return cls._argentino_cache

            supabase_config = json.loads(config_path.read_text())
            from supabase import create_client
            client = create_client(supabase_config['url'], supabase_config['service_role_key'])

            result = client.table('esco_argentino').select(
                'esco_occupation_uri,skills_consolidadas'
            ).execute()

            for row in (result.data or []):
                uri = row.get('esco_occupation_uri')
                skills_raw = row.get('skills_consolidadas') or []
                if not uri or not skills_raw:
                    continue

                skill_map = {}
                for s in skills_raw:
                    esco_uri = s.get('esco_uri')
                    freq = s.get('frequency', 1)
                    if esco_uri:
                        skill_map[esco_uri] = freq

                max_freq = max(skill_map.values()) if skill_map else 1
                cls._argentino_cache[uri] = {
                    "skills": skill_map,
                    "max_freq": max_freq,
                }

            if verbose:
                print(f"[BOOST] Cache argentino cargado: {len(cls._argentino_cache)} ocupaciones")

        except Exception as e:
            if verbose:
                print(f"[BOOST] WARN: No se pudo cargar esco_argentino: {e}")
            # Graceful degradation — cache queda vacío pero no None
            cls._argentino_cache = {}

        return cls._argentino_cache

    def rerank_with_argentino_boost(
        self,
        skills: List[Dict],
        occupation_uri: str,
    ) -> List[Dict]:
        """
        E2.2: Re-rankea skills aplicando boost del perfil argentino.

        Para skills que están en el perfil esco_argentino de la ocupación,
        incrementa el score proporcionalmente a la frecuencia observada.

        boost_factor = 0.05 * (frequency / max_frequency)

        Args:
            skills: Lista de skills extraídas (cada una con skill_uri, score, etc.)
            occupation_uri: URI de la ocupación ESCO matcheada

        Returns:
            Skills re-ordenadas por score descendente, con boost_applied=True donde aplica.
            Si no hay perfil argentino → retorna skills sin cambios.
        """
        cache = self._load_argentino_cache(verbose=self.verbose)

        perfil = cache.get(occupation_uri)
        if not perfil:
            return skills

        skill_map = perfil["skills"]
        max_freq = perfil["max_freq"]

        boosted = []
        for s in skills:
            s_copy = dict(s)
            uri = s_copy.get("skill_uri", "")
            if uri in skill_map:
                freq = skill_map[uri]
                boost_factor = 0.05 * (freq / max_freq)
                original_score = s_copy.get("score", 0.0)
                s_copy["score"] = min(1.0, original_score + boost_factor)
                # Also boost score_ponderado if present
                if "score_ponderado" in s_copy:
                    s_copy["score_ponderado"] = min(1.0, s_copy["score_ponderado"] + boost_factor)
                s_copy["boost_applied"] = True
                s_copy["boost_factor"] = round(boost_factor, 4)
            else:
                s_copy["boost_applied"] = False
            boosted.append(s_copy)

        # Re-sort by score descending
        boosted.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return boosted

    def is_ready(self) -> bool:
        """Verifica si el extractor está listo (tiene embeddings cargados)."""
        return self.embeddings.size > 0 and len(self.metadata) > 0

    def extract_skills_dual(
        self,
        titulo_limpio: str,
        tareas_explicitas: str = None,
        oferta_nlp: Dict = None,
        skills_nlp: List[str] = None,
        soft_skills_nlp: List[str] = None,
        sector_empresa: str = None,
        nivel_seniority: str = None,
        area_funcional: str = None,
        top_k: int = None,
        threshold: float = None,
        track_failures: bool = False
    ) -> Dict:
        """
        v2.3: Extracción DUAL de skills: reglas + semántico.

        Patrón idéntico al matching ISCO:
        1. Evaluar reglas primero (prioridad)
        2. Extraer semántico (siempre, para comparación)
        3. Guardar AMBOS resultados
        4. Determinar si coinciden (dual_coinciden_skills)
        5. Merge final (regla tiene prioridad, semántico complementa)

        Args:
            titulo_limpio: Título limpio de la oferta
            tareas_explicitas: Tareas separadas por ;
            oferta_nlp: Dict con campos NLP (para evaluación de reglas)
            skills_nlp: Skills técnicas del NLP
            soft_skills_nlp: Soft skills del NLP
            sector_empresa: Sector de la empresa
            nivel_seniority: Nivel de seniority
            area_funcional: Área funcional
            top_k: Override top K
            threshold: Override threshold

        Returns:
            {
                "skills_regla": [...] o None si no hay regla,
                "skills_semantico": [...],
                "regla_aplicada": "RS01..." o None,
                "nombre_regla": "Desarrollador Python" o None,
                "dual_coinciden_skills": 1/0/None,
                "skills_final": [...] (merged),
                "metodo_primario": "regla" o "semantico"
            }
        """
        if oferta_nlp is None:
            oferta_nlp = {}

        # Construir contexto NLP si no está completo
        if not sector_empresa:
            sector_empresa = oferta_nlp.get("sector_empresa", "")
        if not nivel_seniority:
            nivel_seniority = oferta_nlp.get("nivel_seniority", "")
        if not area_funcional:
            area_funcional = oferta_nlp.get("area_funcional", "")

        # ============================================
        # PASO 1: Evaluar reglas de skills
        # ============================================
        rules_matcher = SkillsRulesMatcher(verbose=self.verbose)
        regla_result = rules_matcher.evaluate(
            titulo=titulo_limpio,
            oferta_nlp=oferta_nlp,
            tareas=tareas_explicitas or ""
        )

        skills_regla = None
        regla_aplicada = None
        nombre_regla = None

        if regla_result:
            # Convertir formato de regla a formato de skills extraídas
            skills_regla = []
            for skill in regla_result.skills_forzadas:
                skills_regla.append({
                    "skill_esco": skill.get("skill_esco", ""),
                    "skill_uri": skill.get("skill_uri", ""),
                    "score": 0.99,  # Alta confianza por ser regla
                    "score_ponderado": 0.99,
                    "peso": 1.0,
                    "origen": "regla"
                })

            # v2.4: Agregar categorías L1/L2 a skills de regla (igual que semántico)
            try:
                categorizer = get_categorizer()
                for skill in skills_regla:
                    categoria = categorizer.categorize(
                        skill_uri=skill.get("skill_uri", ""),
                        skill_label=skill.get("skill_esco", "")
                    )
                    skill.update(categoria)
            except Exception as e:
                if self.verbose:
                    print(f"[DUAL] WARN: Error categorizando skills regla: {e}")

            regla_aplicada = regla_result.regla_aplicada
            nombre_regla = regla_result.nombre_regla

            if self.verbose:
                print(f"[DUAL] Regla {regla_aplicada} aplicada: {nombre_regla}")
                print(f"[DUAL] Skills forzadas: {[s['skill_esco'] for s in skills_regla]}")

        # ============================================
        # PASO 2: Extraer semántico (SIEMPRE)
        # ============================================
        _extract_result = self.extract_skills(
            titulo_limpio=titulo_limpio,
            tareas_explicitas=tareas_explicitas,
            skills_nlp=skills_nlp,
            soft_skills_nlp=soft_skills_nlp,
            sector_empresa=sector_empresa,
            nivel_seniority=nivel_seniority,
            area_funcional=area_funcional,
            top_k=top_k,
            threshold=threshold,
            track_failures=track_failures
        )
        if track_failures:
            skills_semantico, failures_semantico = _extract_result
        else:
            skills_semantico = _extract_result
            failures_semantico = []

        if self.verbose:
            print(f"[DUAL] Skills semántico: {len(skills_semantico)} extraídas")
            if track_failures and failures_semantico:
                print(f"[DUAL] Textos fallidos: {len(failures_semantico)}")

        # ============================================
        # PASO 3: Determinar dual_coinciden_skills
        # ============================================
        dual_coinciden_skills = None

        if skills_regla:
            # Comparar skills de regla vs semántico
            # Coinciden si al menos 1 skill de regla está en semántico
            regla_labels = {s["skill_esco"].lower() for s in skills_regla}
            semantico_labels = {s["skill_esco"].lower() for s in skills_semantico}

            # Intersección: skills que aparecen en ambos
            overlap = regla_labels & semantico_labels
            overlap_ratio = len(overlap) / len(regla_labels) if regla_labels else 0

            # Consideramos que coinciden si hay al menos 50% de overlap
            # o si al menos 1 skill coincide (para reglas con pocas skills)
            dual_coinciden_skills = 1 if (overlap_ratio >= 0.5 or len(overlap) >= 1) else 0

            if self.verbose:
                print(f"[DUAL] Overlap: {len(overlap)}/{len(regla_labels)} ({overlap_ratio:.0%})")
                print(f"[DUAL] dual_coinciden_skills = {dual_coinciden_skills}")

        # ============================================
        # PASO 4: Merge final (regla prioridad)
        # ============================================
        if skills_regla:
            # Regla tiene prioridad, agregar semántico que no esté en regla
            skills_final = list(skills_regla)  # Copiar skills de regla
            regla_labels = {s["skill_esco"].lower() for s in skills_regla}

            for skill_sem in skills_semantico:
                if skill_sem["skill_esco"].lower() not in regla_labels:
                    # Marcar como origen "semantico" para tracking
                    skill_copy = dict(skill_sem)
                    skill_copy["origen"] = "semantico"
                    skills_final.append(skill_copy)

            metodo_primario = "regla"
        else:
            # Sin regla, usar solo semántico
            skills_final = skills_semantico
            metodo_primario = "semantico"

        # ============================================
        # PASO 5: Retornar resultado dual
        # ============================================
        return {
            "skills_regla": skills_regla,
            "skills_semantico": skills_semantico,
            "regla_aplicada": regla_aplicada,
            "nombre_regla": nombre_regla,
            "dual_coinciden_skills": dual_coinciden_skills,
            "skills_final": skills_final,
            "metodo_primario": metodo_primario,
            "failures": failures_semantico
        }

    # ================================================================
    # M-08: Fuentes declaradas
    # ================================================================

    def _parse_declared_source(self, campo: str, texto) -> List[str]:
        """
        M-08: Parsea una fuente declarada a lista de strings limpia.
        Maneja JSON array, semicolon, comma, y texto libre.
        """
        if not texto or texto in ('', '[]', 'null', 'None'):
            return []

        if isinstance(texto, list):
            items = []
            for item in texto:
                if isinstance(item, dict):
                    v = item.get("valor") or item.get("texto_original") or ""
                    if v:
                        items.append(v)
                elif isinstance(item, str) and item.strip():
                    items.append(item.strip())
            texto_str = "; ".join(items) if items else ""
        else:
            texto_str = str(texto).strip()

        if not texto_str:
            return []

        items = []

        # JSON array
        if texto_str.startswith('['):
            try:
                import json as _json
                parsed = _json.loads(texto_str)
                for item in parsed:
                    if isinstance(item, dict):
                        v = item.get("valor") or item.get("texto_original") or ""
                        if v:
                            items.append(v.strip())
                    elif isinstance(item, str) and item.strip():
                        items.append(item.strip())
            except (ValueError, TypeError):
                # JSON inválido — fallback a split
                cleaned = texto_str.strip('[]')
                items = [s.strip().strip('"').strip("'") for s in cleaned.split(',') if s.strip()]

        # Soft skills: comma-separated + split por ' y '
        elif campo == 'soft_skills_list':
            for part in texto_str.split(','):
                part = part.strip()
                if not part:
                    continue
                # Split por ' y ' para frases compuestas
                if ' y ' in part and len(part) > 20:
                    subparts = part.split(' y ')
                    items.extend(s.strip() for s in subparts if s.strip())
                else:
                    items.append(part)

        # Semicolon (tecnologias, herramientas, skills_tecnicas con ;)
        elif ';' in texto_str:
            items = [s.strip() for s in texto_str.split(';') if s.strip()]

        # Comma fallback
        elif ',' in texto_str:
            items = [s.strip() for s in texto_str.split(',') if s.strip()]

        # Texto libre sin separador
        else:
            items = [texto_str.strip()] if texto_str.strip() else []

        # Filtrar vacíos y muy cortos
        items = [s for s in items if s and len(s) > 1]

        # Deduplicar preservando orden
        seen = set()
        deduped = []
        for item in items:
            key = item.lower().strip()
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        items = deduped

        # Normalizar case según campo
        if campo in ('soft_skills_list', 'skills_tecnicas_list'):
            items = [s.lower().strip() for s in items]
        else:
            items = [s.strip() for s in items]  # preservar case para nombres propios

        # Limitar cantidad
        max_items = 20 if campo == 'soft_skills_list' else 15
        return items[:max_items]

    def extract_declared_skills(
        self,
        oferta_nlp: Dict,
        track_failures: bool = False
    ):
        """
        M-08: Extrae skills ESCO de las 4 fuentes declaradas.

        Para cada fuente: parsear → embeddear → coseno top 1 → equivalencias.
        Retorna tupla (declared_skills, declared_failures).
        """
        if not self.embeddings.size:
            return ([], [])

        threshold = self.threshold
        declared_skills = []
        declared_failures = []

        sources = [
            ('skills_tecnicas_list', 'skills_nlp_declarada'),
            ('tecnologias_list', 'tecnologia_declarada'),
            ('herramientas_list', 'herramienta_declarada'),
            ('soft_skills_list', 'soft_skill_declarada'),
        ]

        for campo, tipo_fuente in sources:
            texto = oferta_nlp.get(campo, '')
            items = self._parse_declared_source(campo, texto)

            if not items:
                continue

            for item in items:
                # Embeddear
                item_emb = self.model.encode(item, normalize_embeddings=True)

                # Coseno contra todas las skills ESCO
                similarities = np.dot(self.embeddings, item_emb)

                # Top 1
                best_idx = np.argmax(similarities)
                score = round(float(similarities[best_idx]), 4)

                if score >= threshold:
                    skill_meta = self.metadata[best_idx]
                    skill_label = skill_meta.get('label', skill_meta.get('preferred_label_es', ''))
                    skill_uri = skill_meta.get('uri', skill_meta.get('skill_uri', ''))

                    # Aplicar equivalencias
                    equiv_group = self.equiv_lookup.get(skill_uri)
                    if equiv_group and equiv_group in self.equiv_groups:
                        group_info = self.equiv_groups[equiv_group]
                        skill_label = group_info['label']

                    declared_skills.append({
                        "skill_esco": skill_label,
                        "skill_uri": skill_uri,
                        "score": score,
                        "score_ponderado": score,
                        "peso": 1.0,
                        "origen": tipo_fuente,
                        "texto_fuente": item[:100]
                    })

                    if self.verbose:
                        print(f"[M-08] [{tipo_fuente}] '{item[:40]}' -> '{skill_label}' (score={score:.3f})")

                elif track_failures:
                    best_meta = self.metadata[best_idx]
                    declared_failures.append({
                        "tarea_texto": item[:200],
                        "tarea_origen": tipo_fuente,
                        "mejor_skill_uri": best_meta.get('uri', best_meta.get('skill_uri', '')),
                        "mejor_skill_label": best_meta.get('label', best_meta.get('preferred_label_es', '')),
                        "mejor_score": score,
                        "threshold_usado": threshold,
                        "gap_al_umbral": round(threshold - score, 4)
                    })

        return (declared_skills, declared_failures)

    def compare_skills_with_occupation(
        self,
        skills_extraidas: List[Dict],
        isco_code: str,
        db_path: str = None
    ) -> Dict:
        """
        v2.3: Calcula coherencia entre skills extraídas y skills esperadas para un ISCO.

        Args:
            skills_extraidas: Lista de skills extraídas (formato extract_skills())
            isco_code: Código ISCO asignado (ej: "2514")
            db_path: Path a BD (opcional)

        Returns:
            {
                "coherence_ratio": 0.0-1.0,
                "essential_skills_matched": int,
                "essential_skills_total": int,
                "optional_skills_matched": int
            }
        """
        if not skills_extraidas or not isco_code:
            return {
                "coherence_ratio": None,
                "essential_skills_matched": 0,
                "essential_skills_total": 0,
                "optional_skills_matched": 0
            }

        if db_path is None:
            db_path = self.db_path

        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()

            # Obtener skills esenciales y opcionales para este ISCO
            # (desde esco_associations o similar)
            cur.execute('''
                SELECT DISTINCT s.preferred_label_es, a.relation_type
                FROM esco_associations a
                JOIN esco_skills s ON a.skill_uri = s.skill_uri
                JOIN esco_occupations o ON a.occupation_uri = o.occupation_uri
                WHERE o.isco_code LIKE ?
                AND a.relation_type IN ('essential', 'optional')
            ''', (isco_code + '%',))

            essential_skills = set()
            optional_skills = set()

            for row in cur.fetchall():
                label, rel_type = row
                if label:
                    label_lower = label.lower()
                    if rel_type == 'essential':
                        essential_skills.add(label_lower)
                    else:
                        optional_skills.add(label_lower)

            conn.close()

            # Comparar con skills extraídas
            extracted_labels = {s["skill_esco"].lower() for s in skills_extraidas}

            essential_matched = len(essential_skills & extracted_labels)
            optional_matched = len(optional_skills & extracted_labels)
            total_essential = len(essential_skills)

            # Coherence ratio: proporción de skills esenciales matcheadas
            if total_essential > 0:
                coherence_ratio = essential_matched / total_essential
            else:
                # Sin skills esenciales definidas, usar proporción de optional
                coherence_ratio = optional_matched / len(optional_skills) if optional_skills else 1.0

            return {
                "coherence_ratio": round(coherence_ratio, 4),
                "essential_skills_matched": essential_matched,
                "essential_skills_total": total_essential,
                "optional_skills_matched": optional_matched
            }

        except Exception as e:
            if self.verbose:
                print(f"[WARN] Error calculando coherencia: {e}")
            return {
                "coherence_ratio": None,
                "essential_skills_matched": 0,
                "essential_skills_total": 0,
                "optional_skills_matched": 0
            }


def generate_skills_embeddings(
    db_path: str = None,
    output_dir: str = None,
    model_name: str = "BAAI/bge-m3",
    batch_size: int = 32,
    verbose: bool = True
) -> Tuple[int, str]:
    """
    Genera embeddings para todas las skills ESCO de la BD.

    Args:
        db_path: Path a la BD SQLite
        output_dir: Directorio de salida para embeddings
        model_name: Nombre del modelo de embeddings
        batch_size: Tamaño del batch para encoding
        verbose: Mostrar progreso

    Returns:
        (num_skills, output_path)
    """
    base_path = Path(__file__).parent
    db_path = Path(db_path) if db_path else base_path / "bumeran_scraping.db"
    output_dir = Path(output_dir) if output_dir else base_path / "embeddings"

    output_dir.mkdir(exist_ok=True)

    if verbose:
        print(f"[GEN] Generando embeddings para skills ESCO...")
        print(f"[GEN] BD: {db_path}")
        print(f"[GEN] Modelo: {model_name}")

    # Cargar skills de la BD
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute('''
        SELECT skill_uri, preferred_label_es, description_es
        FROM esco_skills
        WHERE preferred_label_es IS NOT NULL
        ORDER BY skill_uri
    ''')

    skills = []
    texts = []

    for row in cur:
        uri, label, description = row
        if label:
            skills.append({
                'uri': uri,
                'label': label,
                'description': description or ''
            })
            # Usar label + descripción para embedding más rico
            text = label
            if description:
                text = f"{label}: {description[:200]}"
            texts.append(text)

    conn.close()

    if verbose:
        print(f"[GEN] Skills a procesar: {len(skills)}")

    if not skills:
        print("[GEN] ERROR: No se encontraron skills en la BD")
        return 0, ""

    # Cargar modelo
    if verbose:
        print(f"[GEN] Cargando modelo...")
    model = SentenceTransformer(model_name)

    # Generar embeddings en batches
    if verbose:
        print(f"[GEN] Generando embeddings (batch_size={batch_size})...")

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=verbose,
        normalize_embeddings=True
    )

    # Guardar
    embeddings_path = output_dir / "esco_skills_embeddings_full.npy"
    metadata_path = output_dir / "esco_skills_metadata_full.json"

    np.save(str(embeddings_path), embeddings)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"[GEN] Embeddings guardados: {embeddings_path}")
        print(f"[GEN] Metadata guardados: {metadata_path}")
        print(f"[GEN] Shape: {embeddings.shape}")

    return len(skills), str(embeddings_path)


def main():
    """CLI para testing y generación de embeddings."""
    import argparse

    parser = argparse.ArgumentParser(description="Skills Implicit Extractor v1.0")
    parser.add_argument("--generate", action="store_true", help="Generar embeddings para todas las skills")
    parser.add_argument("--test", action="store_true", help="Ejecutar test con tareas de ejemplo")
    parser.add_argument("--tareas", type=str, help="Tareas a procesar (separadas por ;)")
    parser.add_argument("--threshold", type=float, default=0.55, help="Umbral de similitud")
    parser.add_argument("--top-k", type=int, default=3, help="Top K skills por tarea")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.generate:
        print("=" * 60)
        print("GENERACION DE EMBEDDINGS ESCO SKILLS")
        print("=" * 60)
        num_skills, path = generate_skills_embeddings(verbose=True)
        print(f"\nCompletado: {num_skills} skills procesadas")
        return

    if args.test or args.tareas:
        print("=" * 60)
        print("TEST: Skills Implicit Extractor")
        print("=" * 60)

        extractor = SkillsImplicitExtractor(
            threshold=args.threshold,
            top_k=args.top_k,
            verbose=args.verbose
        )

        if not extractor.is_ready():
            print("\n[ERROR] Embeddings no disponibles. Ejecutar primero:")
            print("  python skills_implicit_extractor.py --generate")
            return

        tareas = args.tareas or "Organización integral del depósito; Control de inventarios; Atención al cliente"

        print(f"\nTareas: {tareas}")
        print(f"Umbral: {args.threshold}")
        print(f"Top K: {args.top_k}")
        print()

        skills = extractor.extract_from_tasks(tareas)

        print(f"Skills implícitas encontradas: {len(skills)}")
        for i, skill in enumerate(skills, 1):
            print(f"\n{i}. {skill['skill_esco']}")
            print(f"   Tarea: {skill['tarea']}")
            print(f"   Score: {skill['score']}")
            print(f"   URI: {skill['skill_uri'][:50]}...")


if __name__ == "__main__":
    main()
