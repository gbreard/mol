#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Match Ofertas v3.3.0 - Skills-First Matching Pipeline con Diccionario Argentino
================================================================================

VERSION: 3.4.1
FECHA: 2026-01-20
MODELO: BGE-M3 (BAAI/bge-m3)

CAMBIO ARQUITECTONICO:
- v2.x: Titulo -> Match ISCO -> Skills (post-hoc)
- v3.0: Titulo+Tareas -> Skills -> Match ISCO (skills-first)
- v3.1: Skills con pesos por origen (tarea=1.2x, titulo=0.9x)
- v3.2: PERSISTENCIA AUTOMATICA a BD (ofertas_esco_matching + ofertas_esco_skills_detalle)
- v3.2.1: PENALIZACION SECTOR - usa sector_empresa para penalizar matches cross-sector
- v3.2.2: PENALIZACION SENIORITY - usa nivel_seniority para penalizar ISCO incompatibles
- v3.2.3: AND logic entre condiciones multiples en reglas de negocio
- v3.2.4: INTEGRACION RUN TRACKING - versionado de corridas con snapshot de configs
- v3.3.0: DICCIONARIO ARGENTINO - vocabulario local ANTES de semantico
- v3.4.0: DUAL MATCHING - ejecuta reglas Y semantico, guarda ambos resultados

FLUJO v3.4.0 (DUAL MATCHING):
1. Extraer skills desde titulo_limpio + tareas_explicitas (con origen)
2. SIEMPRE ejecutar matching semantico completo (skills + titulo + penalizaciones)
3. SIEMPRE evaluar reglas de negocio (sin bypass, solo evaluacion)
4. GUARDAR AMBOS resultados en BD:
   - isco_semantico, score_semantico
   - isco_regla, regla_aplicada (si aplica)
   - dual_coinciden (1=mismo ISCO, 0=difieren, NULL=solo semantico)
5. El auto_corrector decide el ISCO final via regla V23_dual_decision

METODOS DE PERSISTENCIA:
- match_and_persist(id, oferta): Match + guarda matching + skills
- save_matching_result(id, result): Guarda solo matching (incluye dual)
- save_skills_detalle(id, skills): Guarda solo skills

FUNCION DE PIPELINE (produccion):
- run_matching_pipeline(offer_ids, limit, only_pending): Procesa lote con persistencia

VENTAJAS:
- Skills de tareas pesan más que del título (tareas son más confiables)
- Resuelve casos ambiguos ("Consultor" -> segun skills, no solo titulo)
- Skills y ocupacion quedan coherentes
- Mejor precision en casos con tareas ricas
- DATOS SIEMPRE PERSISTIDOS en BD
- DUAL MATCHING: permite auditar discrepancias regla vs semantico
"""

import sqlite3
import logging
import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from enum import Enum

# Imports locales
from skills_implicit_extractor import SkillsImplicitExtractor
from match_by_skills import SkillsBasedMatcher

logger = logging.getLogger(__name__)


class MatchStatus(Enum):
    """Estados posibles del matching."""
    MATCHED = "matched"
    SKILLS_FIRST = "skills_first"
    SEMANTIC = "semantic"
    BYPASS = "bypass"
    BUSINESS_RULE = "business_rule"
    FALLBACK = "fallback"
    FILTERED = "filtered"
    ERROR = "error"


@dataclass
class MatchResult:
    """Resultado estructurado del matching v3."""
    status: str
    esco_uri: Optional[str]
    esco_label: Optional[str]
    isco_code: Optional[str]
    score: float
    metodo: str
    skills_extracted: List[Dict]
    skills_matched: List[str]
    alternativas: List[Dict]
    metadata: Dict

    def to_dict(self) -> Dict:
        return asdict(self)


class MatcherV3:
    """
    Pipeline de matching v3.4.0 - Dual Matching (reglas + semantico).
    """

    VERSION = "3.5.2"  # v3.5.2: Fix exclusiones titulo_original, R87 ecommerce

    # Pesos para combinacion de scores
    ALPHA_SKILLS = 0.6  # Peso para match por skills
    BETA_TITLE = 0.4    # Peso para match semantico titulo

    def __init__(
        self,
        db_conn: sqlite3.Connection = None,
        db_path: str = None,
        config_path: str = None,
        verbose: bool = False
    ):
        """
        Inicializa el matcher v3.

        Args:
            db_conn: Conexion SQLite existente
            db_path: Path a BD
            config_path: Path a config de reglas de negocio
            verbose: Modo debug
        """
        base_path = Path(__file__).parent

        if db_conn:
            self.conn = db_conn
            self._owns_connection = False
        else:
            db_path = db_path or str(base_path / "bumeran_scraping.db")
            self.conn = sqlite3.connect(db_path)
            self._owns_connection = True

        self.verbose = verbose
        self.config_path = config_path or str(base_path.parent / "config" / "matching_rules_business.json")

        # Inicializar componentes
        self.skills_extractor = SkillsImplicitExtractor(verbose=verbose)
        self.skills_matcher = SkillsBasedMatcher(db_conn=self.conn, verbose=verbose)

        # Cargar embeddings de ocupaciones para match semantico
        self._load_occupation_embeddings()

        # Cargar reglas de negocio
        self._load_business_rules()

    def _load_occupation_embeddings(self):
        """Carga embeddings pre-calculados de ocupaciones ESCO."""
        base_path = Path(__file__).parent
        emb_path = base_path / "embeddings" / "esco_occupations_embeddings.npy"
        meta_path = base_path / "embeddings" / "esco_occupations_metadata.json"

        if emb_path.exists() and meta_path.exists():
            self.occ_embeddings = np.load(str(emb_path))
            with open(meta_path, 'r', encoding='utf-8') as f:
                self.occ_metadata = json.load(f)
            if self.verbose:
                print(f"[V3] Cargados {len(self.occ_metadata)} embeddings de ocupaciones")
        else:
            self.occ_embeddings = None
            self.occ_metadata = []
            if self.verbose:
                print("[V3] WARN: Embeddings de ocupaciones no encontrados")

    def _load_business_rules(self):
        """Carga reglas de negocio desde JSON."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.business_rules = json.load(f)
            if self.verbose:
                print(f"[V3] Cargadas reglas de negocio desde {self.config_path}")
        except Exception as e:
            self.business_rules = {}
            if self.verbose:
                print(f"[V3] WARN: No se pudieron cargar reglas: {e}")

        # Cargar config sector-ISCO compatibilidad (v3.2.1)
        self._load_sector_isco_config()

    def _load_sector_isco_config(self):
        """Carga configuracion de compatibilidad sector-ISCO para penalizaciones."""
        base_path = Path(__file__).parent
        config_path = base_path.parent / "config" / "sector_isco_compatibilidad.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.sector_isco_config = json.load(f)
            if self.verbose:
                sectores = len(self.sector_isco_config.get("sectores", {}))
                print(f"[V3] Cargado config sector-ISCO: {sectores} sectores")
        except Exception as e:
            self.sector_isco_config = {}
            if self.verbose:
                print(f"[V3] WARN: No se pudo cargar sector_isco_config: {e}")

        # v3.3.0: Cargar diccionario de sinonimos argentinos
        self._load_sinonimos_argentinos()

    def _load_sinonimos_argentinos(self):
        """Carga diccionario de sinonimos argentinos -> ESCO."""
        base_path = Path(__file__).parent
        config_path = base_path.parent / "config" / "sinonimos_argentinos_esco.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.sinonimos_arg = json.load(f)
            if self.verbose:
                ocups = len(self.sinonimos_arg.get("ocupaciones_titulo", {}))
                print(f"[V3.3] Cargado diccionario argentino: {ocups} ocupaciones")
        except Exception as e:
            self.sinonimos_arg = {}
            if self.verbose:
                print(f"[V3.3] WARN: No se pudo cargar sinonimos_argentinos: {e}")

    def _match_by_argentino_dict(self, oferta_nlp: Dict) -> Optional[Dict]:
        """
        v3.3.0: Busca match directo en diccionario argentino.

        Si el titulo contiene un termino con mapeo directo, retorna el ISCO.
        Considera contexto (sector, palabras clave) para elegir el mapeo correcto.

        Returns:
            Dict con isco_code, esco_label, score, metodo si hay match
            None si no hay match en el diccionario
        """
        if not self.sinonimos_arg:
            return None

        titulo = (oferta_nlp.get("titulo_limpio") or "").lower()
        sector = (oferta_nlp.get("sector_empresa") or "").lower()
        ocupaciones = self.sinonimos_arg.get("ocupaciones_titulo", {})

        for termino, config in ocupaciones.items():
            if termino.startswith("_"):
                continue

            # Verificar si el titulo contiene el termino
            variantes = config.get("variantes", [termino])
            match_found = any(v.lower() in titulo for v in variantes)

            if not match_found:
                continue

            # Hay match con el termino, ahora verificar contexto
            contextos = config.get("contextos", {})
            isco = None
            esco_label = config.get("esco_label", "")

            if contextos:
                # Buscar contexto que matchee con titulo o sector
                for patron, isco_ctx in contextos.items():
                    if "|" in patron:
                        keywords = patron.split("|")
                        if any(kw in titulo or kw in sector for kw in keywords):
                            isco = isco_ctx
                            if self.verbose:
                                print(f"[V3.3] Dict argentino: '{termino}' + contexto '{patron}' -> ISCO {isco}")
                            break

            # Si no hay contexto o no matcheo ninguno, usar ISCO primario
            if not isco:
                isco = config.get("isco_primario") or config.get("isco_familia")
                if isco and self.verbose:
                    print(f"[V3.3] Dict argentino: '{termino}' -> ISCO {isco} (primario)")

            if isco:
                # v3.3.1: Solo retornar si tenemos ISCO de 4 digitos
                # Si solo tenemos familia (1-2 digitos), dejar que el semantico resuelva
                if len(str(isco)) < 4:
                    if self.verbose:
                        print(f"[V3.3] Dict argentino: '{termino}' -> ISCO familia {isco}, delegando a semantico")
                    continue  # No retornar, seguir buscando o dejar al semantico

                # Buscar label ESCO si no viene en config
                if not esco_label:
                    esco_label = self._get_esco_label_for_isco(isco)

                return {
                    "isco_code": isco,
                    "esco_label": esco_label,
                    "score": 0.90,  # Score alto por match de diccionario
                    "metodo": f"diccionario_argentino_{termino.replace(' ', '_')}",
                    "termino_matched": termino
                }

        return None

    def _get_esco_label_for_isco(self, isco_code: str) -> str:
        """Obtiene el label ESCO para un codigo ISCO."""
        cur = self.conn.execute('''
            SELECT preferred_label_es FROM esco_occupations
            WHERE isco_code LIKE ? LIMIT 1
        ''', (f"%{isco_code}%",))
        row = cur.fetchone()
        return row[0] if row else ""

    def _apply_sector_penalty(
        self,
        candidates: List[Dict],
        sector_empresa: str
    ) -> List[Dict]:
        """
        Aplica penalizacion a candidatos con ISCO incompatible con el sector.

        v3.2.1: Si el sector_empresa no es compatible con el ISCO del candidato,
        aplica penalizacion al score (-30% por defecto).

        Args:
            candidates: Lista de candidatos con combined_score
            sector_empresa: Sector de la empresa (ej: "Gastronomia", "Tecnologia")

        Returns:
            Lista de candidatos con scores ajustados y reordenados
        """
        if not sector_empresa or not self.sector_isco_config:
            return candidates

        sectores = self.sector_isco_config.get("sectores", {})
        aliases = self.sector_isco_config.get("aliases", {})
        isco_genericos = self.sector_isco_config.get("isco_genericos", {}).get("lista", [])

        # Normalizar sector (buscar en aliases si no existe directo)
        sector_norm = sector_empresa.strip()
        if sector_norm not in sectores:
            sector_norm = aliases.get(sector_empresa, sector_empresa)
        if sector_norm not in sectores:
            # Buscar match parcial (ej: "Tecnología" -> "Tecnologia")
            for key in sectores:
                if key.lower() == sector_norm.lower():
                    sector_norm = key
                    break

        sector_config = sectores.get(sector_norm, {})
        if not sector_config:
            # Sector no encontrado en config, no aplicar penalizacion
            return candidates

        isco_compatibles = sector_config.get("isco_compatibles", [])
        penalizacion = sector_config.get("penalizacion_cruzado", -0.30)

        for candidate in candidates:
            isco_code = candidate.get("isco_code", "").lstrip("C")
            if not isco_code:
                continue

            # Verificar si el ISCO es generico (compatible con cualquier sector)
            is_generico = any(isco_code.startswith(g) for g in isco_genericos)
            if is_generico:
                continue

            # Verificar compatibilidad con sector
            is_compatible = any(isco_code.startswith(ic) for ic in isco_compatibles)

            if not is_compatible:
                # Aplicar penalizacion
                original_score = candidate.get("combined_score", 0)
                candidate["combined_score"] = max(0, original_score + penalizacion)
                candidate["sector_penalty"] = penalizacion
                candidate["sector_incompatible"] = True
                if self.verbose:
                    print(f"[V3] Penalizacion sector: ISCO {isco_code} no compatible con {sector_norm} (-{abs(penalizacion)*100:.0f}%)")

        # Reordenar por score ajustado
        candidates.sort(key=lambda x: x.get("combined_score", x.get("score", 0)), reverse=True)
        return candidates

    def _apply_seniority_penalty(
        self,
        candidates: List[Dict],
        nivel_seniority: str
    ) -> List[Dict]:
        """
        Aplica penalizacion a candidatos con ISCO incompatible con el nivel_seniority.

        v3.2.2 FASE 3:
        - trainee/junior → penalizar ISCO 1xxx (directores/gerentes)
        - manager/director → penalizar ISCO 9xxx (no calificados)

        Args:
            candidates: Lista de candidatos con combined_score
            nivel_seniority: Nivel de seniority (trainee, junior, semisenior, senior, lead, manager, director)

        Returns:
            Lista de candidatos con scores ajustados
        """
        if not nivel_seniority:
            return candidates

        seniority = nivel_seniority.lower().strip()
        penalizacion = -0.25

        # Reglas de incompatibilidad
        if seniority in ["trainee", "junior"]:
            # Juniors no deberían ser directores/gerentes (ISCO 1xxx)
            isco_incompatibles = ["1"]
        elif seniority in ["manager", "director", "lead"]:
            # Managers no deberían ser trabajadores no calificados (ISCO 9xxx)
            isco_incompatibles = ["9"]
        else:
            # semisenior, senior - sin restricciones fuertes
            return candidates

        for candidate in candidates:
            isco_code = candidate.get("isco_code", "").lstrip("C")
            if not isco_code:
                continue

            is_incompatible = any(isco_code.startswith(ic) for ic in isco_incompatibles)

            if is_incompatible:
                original_score = candidate.get("combined_score", 0)
                candidate["combined_score"] = max(0, original_score + penalizacion)
                candidate["seniority_penalty"] = penalizacion
                candidate["seniority_incompatible"] = True
                if self.verbose:
                    print(f"[V3] Penalizacion seniority: ISCO {isco_code} incompatible con {seniority} (-{abs(penalizacion)*100:.0f}%)")

        # Reordenar por score ajustado
        candidates.sort(key=lambda x: x.get("combined_score", x.get("score", 0)), reverse=True)
        return candidates

    def match(self, oferta_nlp: Dict) -> MatchResult:
        """
        Pipeline principal de matching v3.4.0 - DUAL MATCHING.

        v3.4.0: CAMBIO ESTRUCTURAL - Ejecuta AMBOS (semántico Y reglas), guarda ambos.

        Flujo v3.4.0:
          1. SIEMPRE ejecutar matching semántico completo (diccionario/skills/titulo)
          2. SIEMPRE evaluar reglas de negocio (sin bypass)
          3. Guardar AMBOS resultados en metadata:
             - isco_semantico, score_semantico
             - isco_regla, regla_aplicada (si hay regla que aplique)
             - dual_coinciden: 1 si mismo ISCO, 0 si difieren, None si solo semántico
          4. El isco_code retornado es el semántico (auto_corrector decide el final)

        Args:
            oferta_nlp: Dict con campos NLP de la oferta

        Returns:
            MatchResult con ocupacion, skills, score, y metadata con dual match info.
        """
        titulo = oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo", "")
        tareas = oferta_nlp.get("tareas_explicitas", "")

        if self.verbose:
            print(f"\n[V3.4] === DUAL Matching: {titulo[:50]}... ===")

        # PASO 1: Extraer skills desde titulo + tareas + skills_nlp
        skills_nlp = oferta_nlp.get("skills_tecnicas_list", [])
        if isinstance(skills_nlp, str):
            try:
                skills_nlp = json.loads(skills_nlp) if skills_nlp else []
            except (json.JSONDecodeError, TypeError):
                skills_nlp = []

        soft_skills_nlp = oferta_nlp.get("soft_skills_list", [])
        if isinstance(soft_skills_nlp, str):
            try:
                soft_skills_nlp = json.loads(soft_skills_nlp) if soft_skills_nlp else []
            except (json.JSONDecodeError, TypeError):
                soft_skills_nlp = []

        # v2.3: Extraccion DUAL de skills (regla + semantico)
        skills_dual_result = self.skills_extractor.extract_skills_dual(
            titulo_limpio=titulo,
            tareas_explicitas=tareas,
            oferta_nlp=oferta_nlp,
            skills_nlp=skills_nlp,
            soft_skills_nlp=soft_skills_nlp,
            sector_empresa=oferta_nlp.get("sector_empresa"),
            nivel_seniority=oferta_nlp.get("nivel_seniority"),
            area_funcional=oferta_nlp.get("area_funcional")
        )

        # Usar skills_final para el matching (merge de regla + semantico)
        skills_extracted = skills_dual_result["skills_final"]

        # Guardar info dual para persistencia
        skills_regla = skills_dual_result.get("skills_regla")
        skills_semantico = skills_dual_result.get("skills_semantico")
        skills_regla_aplicada = skills_dual_result.get("regla_aplicada")
        dual_coinciden_skills = skills_dual_result.get("dual_coinciden_skills")
        metodo_skills = skills_dual_result.get("metodo_primario", "semantico")

        if self.verbose:
            print(f"[V3.4] Skills extraidas: {len(skills_extracted)} (metodo: {metodo_skills})")
            if skills_regla_aplicada:
                print(f"[V3.4] Regla skills: {skills_regla_aplicada}")

        # =====================================================================
        # PASO 2: MATCHING SEMÁNTICO COMPLETO (sin bypass de reglas)
        # =====================================================================

        # 2a: Intentar match por diccionario argentino
        dict_match = self._match_by_argentino_dict(oferta_nlp)

        # Variables para resultado semántico
        semantic_isco = None
        semantic_score = 0.0
        semantic_label = ""
        semantic_metodo = ""
        semantic_uri = ""
        semantic_skills_matched = []

        if dict_match:
            # Diccionario argentino matcheó
            semantic_isco = dict_match["isco_code"]
            semantic_label = dict_match["esco_label"]
            semantic_score = dict_match["score"]
            semantic_metodo = dict_match["metodo"]
            if self.verbose:
                print(f"[V3.4] Semántico (diccionario): {dict_match['termino_matched']} -> ISCO {semantic_isco}")
        else:
            # 2b: Match por skills + titulo (embedding)
            candidates_by_skills = []
            if skills_extracted:
                candidates_by_skills = self.skills_matcher.match(skills_extracted, top_n=10)
                if self.verbose:
                    print(f"[V3.4] Candidatos por skills: {len(candidates_by_skills)}")

            candidates_by_title = self._semantic_match_title(titulo)
            if self.verbose:
                print(f"[V3.4] Candidatos por titulo: {len(candidates_by_title)}")

            # Combinar scores
            if candidates_by_skills:
                final_candidates = self._combine_candidates(candidates_by_skills, candidates_by_title)
                semantic_metodo = "skills_first_v3"
            elif candidates_by_title:
                final_candidates = candidates_by_title
                semantic_metodo = "semantic_fallback_v3"
            else:
                # Sin candidatos semánticos - caso especial
                semantic_isco = None
                semantic_score = 0.0
                semantic_metodo = "no_match"
                final_candidates = []

            if final_candidates:
                # Aplicar penalizaciones
                sector_empresa = oferta_nlp.get("sector_empresa", "")
                if sector_empresa:
                    final_candidates = self._apply_sector_penalty(final_candidates, sector_empresa)

                nivel_seniority = oferta_nlp.get("nivel_seniority", "")
                if nivel_seniority:
                    final_candidates = self._apply_seniority_penalty(final_candidates, nivel_seniority)

                # Seleccionar mejor candidato
                best = final_candidates[0]
                semantic_isco = best.get("isco_code", "")
                if semantic_isco and semantic_isco.startswith("C"):
                    semantic_isco = semantic_isco[1:]
                semantic_score = best.get("combined_score", best.get("score", 0))
                semantic_label = best.get("esco_label", "")
                semantic_uri = best.get("occupation_uri", "")
                semantic_skills_matched = best.get("skills_matched", [])

                if self.verbose:
                    print(f"[V3.4] Semántico (embedding): ISCO {semantic_isco} score={semantic_score:.2f}")

        # =====================================================================
        # PASO 3: EVALUAR REGLAS DE NEGOCIO (sin bypass, solo evaluación)
        # =====================================================================
        rule_info = self._evaluate_rule_only(oferta_nlp)

        regla_isco = None
        regla_aplicada = None
        if rule_info:
            regla_isco = rule_info["isco_code"]
            regla_aplicada = rule_info["rule_id"]
            if self.verbose:
                print(f"[V3.4] Regla aplicable: {regla_aplicada} -> ISCO {regla_isco}")

        # =====================================================================
        # PASO 4: DETERMINAR dual_coinciden
        # =====================================================================
        if regla_isco is not None and semantic_isco is not None:
            # Comparar los primeros 4 dígitos (nivel ISCO-4)
            dual_coinciden = 1 if regla_isco[:4] == semantic_isco[:4] else 0
            if self.verbose:
                if dual_coinciden:
                    print(f"[V3.4] DUAL: Coinciden (ISCO {semantic_isco})")
                else:
                    print(f"[V3.4] DUAL: DIFIEREN - Semántico={semantic_isco}, Regla={regla_isco}")
        else:
            # Solo semántico disponible (no hay regla que aplique)
            dual_coinciden = None
            if self.verbose:
                print(f"[V3.4] DUAL: Solo semántico (sin regla aplicable)")

        # =====================================================================
        # PASO 5: DECISIÓN INTELIGENTE - v3.5.1
        # =====================================================================

        # v3.5.1: Usar lógica de decisión inteligente
        isco_final, decision_metodo, decision_razon = self._decide_dual_match(
            regla_isco=regla_isco,
            semantic_isco=semantic_isco,
            semantic_score=semantic_score,
            regla_id=regla_aplicada
        )

        if self.verbose:
            print(f"[V3.5.1] Decisión: {decision_metodo} - {decision_razon}")

        # Si no hay ISCO final, retornar error
        if isco_final is None:
            return MatchResult(
                status=MatchStatus.ERROR.value,
                esco_uri=None,
                esco_label=None,
                isco_code=None,
                score=0.0,
                metodo="no_match",
                skills_extracted=skills_extracted,
                skills_matched=[],
                alternativas=[],
                metadata={
                    "razon": decision_razon,
                    "isco_semantico": semantic_isco,
                    "isco_regla": regla_isco,
                    "regla_aplicada": regla_aplicada,
                    "dual_coinciden": dual_coinciden,
                    "decision_metodo": decision_metodo,
                    "decision_razon": decision_razon,
                    # Campos dual matching SKILLS (v2.3)
                    "skills_regla_json": json.dumps(skills_regla) if skills_regla else None,
                    "skills_semantico_json": json.dumps(skills_semantico) if skills_semantico else None,
                    "skills_regla_aplicada": skills_regla_aplicada,
                    "dual_coinciden_skills": dual_coinciden_skills,
                    "metodo_skills": metodo_skills
                }
            )

        # Determinar qué datos de ocupación usar según la decisión
        if "regla" in decision_metodo and rule_info:
            # La decisión es usar la regla
            rule_occupation = self._find_occupation_by_esco_label(rule_info.get("esco_label", ""))
            if rule_occupation:
                return MatchResult(
                    status=MatchStatus.BUSINESS_RULE.value,
                    esco_uri=rule_occupation['uri'],
                    esco_label=rule_occupation['label'],
                    isco_code=rule_occupation['isco_code'].lstrip("C"),
                    score=0.98,
                    metodo=f"regla_negocio_{regla_aplicada}",
                    skills_extracted=skills_extracted,
                    skills_matched=semantic_skills_matched,
                    alternativas=[],
                    metadata={
                        "skills_count": len(skills_extracted),
                        "skills_matched_count": len(semantic_skills_matched),
                        "isco_semantico": semantic_isco.lstrip("C") if semantic_isco else None,
                        "score_semantico": semantic_score,
                        "isco_regla": rule_occupation['isco_code'].lstrip("C"),
                        "regla_aplicada": regla_aplicada,
                        "dual_coinciden": dual_coinciden,
                        "decision_metodo": decision_metodo,
                        "decision_razon": decision_razon,
                        "skills_regla_json": json.dumps(skills_regla) if skills_regla else None,
                        "skills_semantico_json": json.dumps(skills_semantico) if skills_semantico else None,
                        "skills_regla_aplicada": skills_regla_aplicada,
                        "dual_coinciden_skills": dual_coinciden_skills,
                        "metodo_skills": metodo_skills
                    }
                )

        # La decisión es usar el semántico (o dual_coinciden donde ambos dan igual)
        if "skills" in semantic_metodo:
            status = MatchStatus.SKILLS_FIRST.value
        elif "diccionario" in semantic_metodo:
            status = MatchStatus.MATCHED.value
        else:
            status = MatchStatus.SEMANTIC.value

        return MatchResult(
            status=status,
            esco_uri=semantic_uri,
            esco_label=semantic_label,
            isco_code=semantic_isco,
            score=semantic_score,
            metodo=semantic_metodo,
            skills_extracted=skills_extracted,
            skills_matched=semantic_skills_matched,
            alternativas=[],
            metadata={
                "skills_count": len(skills_extracted),
                "skills_matched_count": len(semantic_skills_matched),
                "isco_semantico": semantic_isco,
                "score_semantico": semantic_score,
                "isco_regla": regla_isco,
                "regla_aplicada": regla_aplicada,
                "dual_coinciden": dual_coinciden,
                "decision_metodo": decision_metodo,
                "decision_razon": decision_razon,
                "skills_regla_json": json.dumps(skills_regla) if skills_regla else None,
                "skills_semantico_json": json.dumps(skills_semantico) if skills_semantico else None,
                "skills_regla_aplicada": skills_regla_aplicada,
                "dual_coinciden_skills": dual_coinciden_skills,
                "metodo_skills": metodo_skills
            }
        )

    def _check_business_rules(self, oferta_nlp: Dict, mode: str = "correccion") -> Optional[MatchResult]:
        """Verifica si alguna regla de negocio aplica.

        v3.3.2: Modos disponibles:
        - mode="bypass": Aplica reglas ANTES de semantico/diccionario (prioridad maxima)
        - mode="correccion": Aplica todas las reglas activas (para score bajo)
        - mode="critica_only": Solo aplica reglas con "correccion_critica": true

        Solo aplica reglas que tienen forzar_isco o forzar_isco_familia.
        Las reglas de priorizacion/penalizacion se aplican despues.
        """
        if not self.business_rules:
            return None

        titulo = (oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo", "")).lower()
        # v3.3.4: Para exclusiones, usar título ORIGINAL (no limpio) para no perder contexto
        # Ej: "Gerente de Operaciones – Grupo Gastronómico" limpio queda "Gerente de Operaciones"
        # pero la exclusión debe ver "gastronómico" del título original
        # v3.5.2: Usar titulo_limpio si titulo no existe (ofertas_nlp no tiene titulo)
        titulo_original = (oferta_nlp.get("titulo") or oferta_nlp.get("titulo_limpio", "")).lower()
        tareas = (oferta_nlp.get("tareas_explicitas") or "").lower()
        reglas = self.business_rules.get("reglas_forzar_isco", {})

        # v3.4.1: Ordenar reglas por prioridad (menor = mayor prioridad)
        reglas_ordenadas = sorted(
            reglas.items(),
            key=lambda x: x[1].get("prioridad", 99) if isinstance(x[1], dict) else 99
        )

        for rule_id, rule in reglas_ordenadas:
            # Saltar items que no son reglas (ej: "descripcion")
            if not isinstance(rule, dict):
                continue
            if not rule.get("activa", False):
                continue

            # v3.3.0: En modo "critica_only", solo aplicar reglas criticas
            if mode == "critica_only":
                if not rule.get("correccion_critica", False):
                    continue

            accion = rule.get("accion", {})

            # Solo aplicar bypass si hay forzar_isco
            isco = accion.get("forzar_isco") or accion.get("forzar_isco_familia", "")
            if not isco:
                # Esta regla es de priorizacion, no bypass
                continue

            condicion = rule.get("condicion", {})

            # v3.2.3: Usar AND entre condiciones múltiples
            # Cada condición que existe debe cumplirse (AND)
            # Dentro de cada condición se usa OR (alguno de los términos)
            condiciones_evaluadas = []

            # Verificar titulo_contiene_alguno (case-insensitive)
            terminos = condicion.get("titulo_contiene_alguno", [])
            if terminos:
                condiciones_evaluadas.append(any(t.lower() in titulo.lower() for t in terminos))

            # Verificar titulo_contiene_alguno_2 (segundo grupo de OR, case-insensitive)
            terminos_2 = condicion.get("titulo_contiene_alguno_2", [])
            if terminos_2:
                condiciones_evaluadas.append(any(t.lower() in titulo.lower() for t in terminos_2))

            # Verificar titulo_contiene_todos (AND de todos los términos, case-insensitive)
            terminos_todos = condicion.get("titulo_contiene_todos", [])
            if terminos_todos:
                condiciones_evaluadas.append(all(t.lower() in titulo.lower() for t in terminos_todos))

            # Verificar titulo_o_tareas_contiene_alguno (case-insensitive)
            terminos_ot = condicion.get("titulo_o_tareas_contiene_alguno", [])
            if terminos_ot:
                condiciones_evaluadas.append(any(t.lower() in titulo.lower() or t.lower() in tareas.lower() for t in terminos_ot))

            # Verificar skills_contiene_alguno (se procesa en skills extractor)
            terminos_skills = condicion.get("skills_contiene_alguno", [])
            if terminos_skills:
                # Buscar en titulo y tareas
                texto_completo = f"{titulo} {tareas}"
                condiciones_evaluadas.append(any(t.lower() in texto_completo for t in terminos_skills))

            # ALL condiciones deben cumplirse (AND entre condiciones)
            condicion_texto_cumplida = len(condiciones_evaluadas) > 0 and all(condiciones_evaluadas)

            # Verificar area_funcional_es como filtro adicional (AND con otras condiciones)
            area_requerida = condicion.get("area_funcional_es")
            if condicion_texto_cumplida and area_requerida:
                # Si hay condición de área, verificarla
                condicion_cumplida = oferta_nlp.get("area_funcional", "").lower() == area_requerida.lower()
            else:
                condicion_cumplida = condicion_texto_cumplida

            # Verificar sector_es como filtro adicional (AND con otras condiciones)
            sector_requerido = condicion.get("sector_es")
            if condicion_cumplida and sector_requerido:
                sector_actual = oferta_nlp.get("sector_empresa", "").lower()
                condicion_cumplida = sector_actual == sector_requerido.lower()

            # Verificar sector_empresa_es_alguno (lista de sectores válidos)
            sectores_validos = condicion.get("sector_empresa_es_alguno", [])
            if condicion_cumplida and sectores_validos:
                sector_actual = oferta_nlp.get("sector_empresa", "").lower()
                condicion_cumplida = any(s.lower() == sector_actual for s in sectores_validos)

            # Verificar EXCLUSIONES (si alguna se cumple, la regla NO aplica)
            if condicion_cumplida:
                # titulo_no_contiene_alguno: excluir si el título contiene alguno de estos
                # v3.3.4: Usar titulo_original para exclusiones (no titulo_limpio)
                excluir_titulo = condicion.get("titulo_no_contiene_alguno", [])
                if excluir_titulo and any(t.lower() in titulo_original for t in excluir_titulo):
                    condicion_cumplida = False

                # sector_no_es: excluir si el sector es alguno de estos
                excluir_sector = condicion.get("sector_no_es", [])
                sector_actual = oferta_nlp.get("sector_empresa", "").lower()
                if excluir_sector and any(s.lower() == sector_actual for s in excluir_sector):
                    condicion_cumplida = False

                # area_funcional_no_es: excluir si el área es alguna de estas
                excluir_area = condicion.get("area_funcional_no_es", [])
                area_actual = oferta_nlp.get("area_funcional", "").lower()
                if excluir_area and any(a.lower() == area_actual for a in excluir_area):
                    condicion_cumplida = False

            if condicion_cumplida:
                # v3.4.2: ESCO es el target primario, ISCO se deriva
                esco_label = accion.get("esco_label", "")

                # Buscar ocupación ESCO por label exacto
                occupation = self._find_occupation_by_esco_label(esco_label)

                if not occupation:
                    if self.verbose:
                        print(f"[V3.4.2] WARN: Regla {rule_id} - ESCO label no encontrado: '{esco_label}'")
                    continue  # Skip esta regla, probar siguiente

                if self.verbose:
                    modo_str = "correccion" if mode == "correccion" else "critica"
                    print(f"[V3.4.2] Regla {rule_id} ({modo_str}): {rule.get('nombre', '')} -> {occupation['label']}")

                return MatchResult(
                    status=MatchStatus.BUSINESS_RULE.value,
                    esco_uri=occupation['uri'],
                    esco_label=occupation['label'],  # Label exacto de ESCO
                    isco_code=occupation['isco_code'].lstrip("C"),  # ISCO derivado, sin prefijo C
                    score=0.98,
                    metodo=f"regla_negocio_{rule_id}",
                    skills_extracted=[],
                    skills_matched=[],
                    alternativas=[],
                    metadata={"regla": rule_id, "nombre_regla": rule.get("nombre", "")}
                )

        return None

    def _evaluate_rule_only(self, oferta_nlp: Dict) -> Optional[Dict]:
        """
        Evalúa si alguna regla de negocio aplica, sin hacer bypass.

        v3.4.0: Usado para dual matching. Solo retorna info de la regla,
        NO un MatchResult. El match() usa esto para guardar ambos resultados.

        Returns:
            Dict con {rule_id, isco_code, esco_label} si aplica alguna regla, None si no.
        """
        if not self.business_rules:
            return None

        titulo = (oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo", "")).lower()
        # v3.5.2: Usar titulo_limpio si titulo no existe
        titulo_original = (oferta_nlp.get("titulo") or oferta_nlp.get("titulo_limpio", "")).lower()
        tareas = (oferta_nlp.get("tareas_explicitas") or "").lower()
        reglas = self.business_rules.get("reglas_forzar_isco", {})

        # v3.4.1: Ordenar reglas por prioridad (menor = mayor prioridad)
        reglas_ordenadas = sorted(
            reglas.items(),
            key=lambda x: x[1].get("prioridad", 99) if isinstance(x[1], dict) else 99
        )

        for rule_id, rule in reglas_ordenadas:
            if not isinstance(rule, dict):
                continue
            if not rule.get("activa", False):
                continue

            accion = rule.get("accion", {})
            isco = accion.get("forzar_isco") or accion.get("forzar_isco_familia", "")
            if not isco:
                continue

            condicion = rule.get("condicion", {})
            condiciones_evaluadas = []

            # titulo_contiene_alguno
            terminos = condicion.get("titulo_contiene_alguno", [])
            if terminos:
                condiciones_evaluadas.append(any(t.lower() in titulo.lower() for t in terminos))

            # titulo_contiene_alguno_2
            terminos_2 = condicion.get("titulo_contiene_alguno_2", [])
            if terminos_2:
                condiciones_evaluadas.append(any(t.lower() in titulo.lower() for t in terminos_2))

            # titulo_contiene_todos
            terminos_todos = condicion.get("titulo_contiene_todos", [])
            if terminos_todos:
                condiciones_evaluadas.append(all(t.lower() in titulo.lower() for t in terminos_todos))

            # titulo_o_tareas_contiene_alguno
            terminos_ot = condicion.get("titulo_o_tareas_contiene_alguno", [])
            if terminos_ot:
                condiciones_evaluadas.append(any(t.lower() in titulo.lower() or t.lower() in tareas.lower() for t in terminos_ot))

            # skills_contiene_alguno
            terminos_skills = condicion.get("skills_contiene_alguno", [])
            if terminos_skills:
                texto_completo = f"{titulo} {tareas}"
                condiciones_evaluadas.append(any(t.lower() in texto_completo for t in terminos_skills))

            condicion_texto_cumplida = len(condiciones_evaluadas) > 0 and all(condiciones_evaluadas)

            # area_funcional_es
            area_requerida = condicion.get("area_funcional_es")
            if condicion_texto_cumplida and area_requerida:
                condicion_cumplida = oferta_nlp.get("area_funcional", "").lower() == area_requerida.lower()
            else:
                condicion_cumplida = condicion_texto_cumplida

            # sector_es
            sector_requerido = condicion.get("sector_es")
            if condicion_cumplida and sector_requerido:
                sector_actual = oferta_nlp.get("sector_empresa", "").lower()
                condicion_cumplida = sector_actual == sector_requerido.lower()

            # sector_empresa_es_alguno
            sectores_validos = condicion.get("sector_empresa_es_alguno", [])
            if condicion_cumplida and sectores_validos:
                sector_actual = oferta_nlp.get("sector_empresa", "").lower()
                condicion_cumplida = any(s.lower() == sector_actual for s in sectores_validos)

            # EXCLUSIONES
            if condicion_cumplida:
                excluir_titulo = condicion.get("titulo_no_contiene_alguno", [])
                if excluir_titulo and any(t.lower() in titulo_original for t in excluir_titulo):
                    condicion_cumplida = False

                excluir_sector = condicion.get("sector_no_es", [])
                sector_actual = oferta_nlp.get("sector_empresa", "").lower()
                if excluir_sector and any(s.lower() == sector_actual for s in excluir_sector):
                    condicion_cumplida = False

                excluir_area = condicion.get("area_funcional_no_es", [])
                area_actual = oferta_nlp.get("area_funcional", "").lower()
                if excluir_area and any(a.lower() == area_actual for a in excluir_area):
                    condicion_cumplida = False

            if condicion_cumplida:
                # v3.4.2: ESCO es el target, ISCO se deriva
                esco_label = accion.get("esco_label", "")
                occupation = self._find_occupation_by_esco_label(esco_label)

                if occupation:
                    return {
                        "rule_id": rule_id,
                        "isco_code": occupation['isco_code'].lstrip("C"),  # ISCO derivado, sin prefijo C
                        "esco_label": occupation['label'],  # Label exacto de ESCO
                        "nombre_regla": rule.get("nombre", "")
                    }
                else:
                    # Si no se encuentra ESCO, continuar con siguiente regla
                    continue

        return None

    def _decide_dual_match(
        self,
        regla_isco: Optional[str],
        semantic_isco: Optional[str],
        semantic_score: float,
        regla_id: Optional[str]
    ) -> Tuple[str, str, str]:
        """
        Decide cuál ISCO usar basado en confianza de cada método.

        v3.5.1: Lógica de decisión inteligente para matching dual.

        Args:
            regla_isco: ISCO de la regla de negocio (None si no aplica ninguna)
            semantic_isco: ISCO del matching semántico
            semantic_score: Score del matching semántico (0-1)
            regla_id: ID de la regla aplicada (None si no aplica ninguna)

        Returns:
            Tuple de (isco_final, decision_metodo, decision_razon)
        """
        # Caso 1: Solo semántico disponible (sin regla que aplique)
        if regla_isco is None:
            if semantic_isco is None:
                return (None, "error", "sin match disponible")
            return (semantic_isco, "semantico_unico", "sin regla aplicable")

        # Caso 2: Sin semántico pero hay regla
        if semantic_isco is None:
            return (regla_isco, "regla_unica", "sin match semantico")

        # Caso 3: Ambos disponibles - comparar primeros 4 dígitos (ISCO-4)
        regla_isco_4 = str(regla_isco)[:4]
        semantic_isco_4 = str(semantic_isco)[:4]

        if regla_isco_4 == semantic_isco_4:
            # Coinciden → alta confianza
            return (regla_isco, "dual_coinciden",
                    f"regla {regla_id} y semantico coinciden (ISCO {regla_isco_4})")

        # Caso 4: Divergen → decidir según score
        if semantic_score < 0.55:
            # Semántico poco confiable → usar regla
            return (regla_isco, "regla_por_score_bajo",
                    f"score semantico {semantic_score:.2f} < 0.55, regla {regla_id} prioridad")

        if semantic_score >= 0.80:
            # Semántico muy confiable → usar regla pero marcar WARNING
            return (regla_isco, "regla_override_semantico_alto",
                    f"REVISAR: regla {regla_id} override semantico {semantic_isco} (score {semantic_score:.2f})")

        # Caso 5: Score medio (0.55-0.80) → usar regla pero marcar para revisión
        return (regla_isco, "regla_revisar",
                f"score semantico medio {semantic_score:.2f}, regla {regla_id} aplicada, verificar")

    def _find_occupation_by_esco_label(self, esco_label: str) -> Optional[Dict]:
        """
        Busca ocupación ESCO por label exacto.

        v3.4.2: ESCO es el target primario, ISCO se deriva.

        Args:
            esco_label: Label ESCO a buscar (ej: "vendedor de tienda/vendedora de tienda")

        Returns:
            Dict con {uri, label, isco_code} o None si no se encuentra
        """
        if not esco_label:
            return None

        # 1. Búsqueda exacta (case-insensitive)
        cur = self.conn.execute('''
            SELECT occupation_uri, preferred_label_es, isco_code
            FROM esco_occupations
            WHERE LOWER(preferred_label_es) = LOWER(?)
        ''', (esco_label,))

        row = cur.fetchone()
        if row:
            return {
                'uri': row[0],
                'label': row[1],
                'isco_code': row[2]
            }

        # 2. Fallback: búsqueda parcial por primera parte del label
        # "vendedor de tienda" matchea "vendedor de tienda/vendedora de tienda"
        label_base = esco_label.split('/')[0].strip()
        cur = self.conn.execute('''
            SELECT occupation_uri, preferred_label_es, isco_code
            FROM esco_occupations
            WHERE LOWER(preferred_label_es) LIKE LOWER(?)
            ORDER BY LENGTH(preferred_label_es)
            LIMIT 1
        ''', (f"{label_base}%",))

        row = cur.fetchone()
        if row:
            if self.verbose:
                print(f"[V3.4.2] ESCO fallback: '{esco_label}' -> '{row[1]}'")
            return {
                'uri': row[0],
                'label': row[1],
                'isco_code': row[2]
            }

        return None

    def _find_occupation_uri(self, isco_code: str, label: str) -> str:
        """
        DEPRECATED: Usar _find_occupation_by_esco_label() en su lugar.
        Mantenido por compatibilidad.
        """
        # Intentar con el nuevo método primero
        result = self._find_occupation_by_esco_label(label)
        if result:
            return result['uri']

        # Fallback al método antiguo
        cur = self.conn.execute('''
            SELECT occupation_uri FROM esco_occupations
            WHERE isco_code LIKE ? OR preferred_label_es LIKE ?
            LIMIT 1
        ''', (f"%{isco_code}%", f"%{label}%"))

        row = cur.fetchone()
        return row[0] if row else ""

    def _semantic_match_title(self, titulo: str, top_n: int = 10) -> List[Dict]:
        """Match semantico del titulo usando embeddings."""
        if self.occ_embeddings is None or not titulo:
            return []

        # Usar el modelo de skills para encoding (mismo BGE-M3)
        titulo_emb = self.skills_extractor.model.encode(titulo, normalize_embeddings=True)

        # Calcular similitudes
        similarities = np.dot(self.occ_embeddings, titulo_emb)

        # Top N
        top_indices = np.argsort(similarities)[-top_n:][::-1]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            meta = self.occ_metadata[idx]
            results.append({
                "occupation_uri": meta.get("uri", ""),
                "esco_label": meta.get("label", ""),
                "isco_code": meta.get("isco_code", "").lstrip("C"),  # Sin prefijo C
                "score": score,
                "source": "semantic_title"
            })

        return results

    def _combine_candidates(
        self,
        skills_candidates: List[Dict],
        title_candidates: List[Dict]
    ) -> List[Dict]:
        """
        Combina candidatos de skills y titulo con pesos.

        Score final = ALPHA * skills_score + BETA * title_score
        """
        # Normalizar scores de skills (pueden ser muy altos por suma)
        if skills_candidates:
            max_skill_score = max(c.get("score", 0) for c in skills_candidates)
            if max_skill_score > 0:
                for c in skills_candidates:
                    c["norm_score"] = c.get("score", 0) / max_skill_score
            else:
                for c in skills_candidates:
                    c["norm_score"] = 0

        # Crear lookup por URI
        title_by_uri = {c["occupation_uri"]: c for c in title_candidates}
        skills_by_uri = {c["occupation_uri"]: c for c in skills_candidates}

        # Combinar
        all_uris = set(skills_by_uri.keys()) | set(title_by_uri.keys())
        combined = []

        for uri in all_uris:
            skill_c = skills_by_uri.get(uri, {})
            title_c = title_by_uri.get(uri, {})

            skill_score = skill_c.get("norm_score", 0)
            title_score = title_c.get("score", 0)

            combined_score = self.ALPHA_SKILLS * skill_score + self.BETA_TITLE * title_score

            # Usar metadata del que exista
            base = skill_c if skill_c else title_c

            combined.append({
                "occupation_uri": uri,
                "esco_label": base.get("esco_label", ""),
                "isco_code": base.get("isco_code", "").lstrip("C"),  # Sin prefijo C
                "combined_score": combined_score,
                "skill_score": skill_score,
                "title_score": title_score,
                "skills_matched": skill_c.get("skills_matched", []),
                "match_count": skill_c.get("match_count", 0)
            })

        # Ordenar por score combinado
        combined.sort(key=lambda x: x["combined_score"], reverse=True)

        return combined

    def close(self):
        """Cierra conexiones."""
        if self._owns_connection and self.conn:
            self.conn.close()
        self.skills_matcher.close()

    def save_matching_result(self, id_oferta: str, result: MatchResult, run_id: str = None) -> bool:
        """
        Persiste el resultado del matching en ofertas_esco_matching.

        v3.4.0: Incluye campos de dual matching (isco_regla, isco_semantico, etc.)

        Args:
            id_oferta: ID de la oferta
            result: MatchResult del matching
            run_id: ID de la corrida (opcional, para run tracking v3.2.4)

        Returns:
            True si se guardó correctamente
        """
        from datetime import datetime

        try:
            # Extraer campos de dual matching de metadata
            meta = result.metadata or {}
            isco_regla = meta.get("isco_regla")
            isco_semantico = meta.get("isco_semantico")
            score_semantico = meta.get("score_semantico")
            regla_aplicada = meta.get("regla_aplicada")
            dual_coinciden = meta.get("dual_coinciden")
            # v3.5.0: Campos dual skills
            skills_regla_json = meta.get("skills_regla_json")
            skills_semantico_json = meta.get("skills_semantico_json")
            skills_regla_aplicada = meta.get("skills_regla_aplicada")
            dual_coinciden_skills = meta.get("dual_coinciden_skills")
            # v3.5.1: Decision inteligente
            decision_metodo = meta.get("decision_metodo")
            decision_razon = meta.get("decision_razon")

            self.conn.execute('''
                INSERT OR REPLACE INTO ofertas_esco_matching (
                    id_oferta, esco_occupation_uri, esco_occupation_label,
                    occupation_match_score, occupation_match_method,
                    isco_code, isco_label,
                    skills_oferta_json, skills_matched_essential,
                    skills_demandados_total, skills_matcheados_esco,
                    matching_timestamp, matching_version, run_id,
                    estado_validacion,
                    isco_regla, isco_semantico, score_semantico,
                    regla_aplicada, dual_coinciden, decision_metodo,
                    skills_regla_json, skills_semantico_json,
                    skills_regla_aplicada, dual_coinciden_skills,
                    decision_razon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(id_oferta),
                result.esco_uri,
                result.esco_label,
                result.score,
                result.metodo,
                result.isco_code,
                result.esco_label,  # isco_label = esco_label por ahora
                json.dumps([s.get('skill_esco', '') for s in result.skills_extracted], ensure_ascii=False),
                json.dumps(result.skills_matched, ensure_ascii=False),
                len(result.skills_extracted),
                len(result.skills_matched),
                datetime.now().isoformat(),
                self.VERSION,
                run_id,  # v3.2.4: Run tracking
                'pendiente',  # v3.2.5: Estado validación inicial
                # v3.4.0: Campos dual matching ISCO
                isco_regla,
                isco_semantico,
                score_semantico,
                regla_aplicada,
                dual_coinciden,
                decision_metodo,  # v3.5.1: Decision inteligente
                # v3.5.0: Campos dual skills
                skills_regla_json,
                skills_semantico_json,
                skills_regla_aplicada,
                dual_coinciden_skills,
                decision_razon  # v3.5.1: Razon de la decision
            ))
            # v3.3.3: Tracking histórico
            # Guardar en ofertas_matching_history (no sobrescribe)
            self.conn.execute('''
                INSERT INTO ofertas_matching_history
                (id_oferta, run_id, isco_code, isco_label, match_method, score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(id_oferta),
                run_id,
                result.isco_code,
                result.esco_label,
                result.metodo,
                result.score
            ))

            # Guardar relación run <-> oferta
            if run_id:
                self.conn.execute('''
                    INSERT OR IGNORE INTO run_ofertas (run_id, id_oferta)
                    VALUES (?, ?)
                ''', (run_id, str(id_oferta)))

            self.conn.commit()

            if self.verbose:
                dual_info = ""
                if dual_coinciden is not None:
                    dual_info = f" [DUAL: {'COINCIDEN' if dual_coinciden else 'DIFIEREN'}]"
                print(f"[V3.4] Matching guardado para {id_oferta}{dual_info}" + (f" (run: {run_id})" if run_id else ""))
            return True

        except Exception as e:
            logger.error(f"Error guardando matching para {id_oferta}: {e}")
            if self.verbose:
                print(f"[V3.4] ERROR guardando matching: {e}")
            return False

    def save_skills_detalle(self, id_oferta: str, skills: List[Dict]) -> int:
        """
        Persiste las skills extraídas en ofertas_esco_skills_detalle.

        Args:
            id_oferta: ID de la oferta
            skills: Lista de skills extraídas (del SkillsImplicitExtractor + Categorizer)

        Returns:
            Número de skills guardadas
        """
        try:
            # Primero eliminar skills anteriores de esta oferta
            self.conn.execute(
                'DELETE FROM ofertas_esco_skills_detalle WHERE id_oferta = ?',
                (str(id_oferta),)
            )

            count = 0
            for skill in skills:
                self.conn.execute('''
                    INSERT INTO ofertas_esco_skills_detalle (
                        id_oferta, skill_mencionado, skill_tipo_fuente,
                        esco_skill_label, match_score, match_method,
                        esco_skill_type, source_classification
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(id_oferta),
                    skill.get('skill_esco', skill.get('skill', '')),
                    skill.get('origen', 'unknown'),
                    skill.get('skill_esco', ''),
                    skill.get('score', 0),
                    'implicit_bge_m3',
                    skill.get('L1', 'T'),  # Categoría L1
                    json.dumps({
                        'L1': skill.get('L1', ''),
                        'L1_nombre': skill.get('L1_nombre', ''),
                        'L2': skill.get('L2', ''),
                        'L2_nombre': skill.get('L2_nombre', ''),
                        'es_digital': skill.get('es_digital', False)
                    }, ensure_ascii=False)
                ))
                count += 1

            self.conn.commit()

            if self.verbose:
                print(f"[V3] {count} skills guardadas para {id_oferta}")
            return count

        except Exception as e:
            logger.error(f"Error guardando skills para {id_oferta}: {e}")
            if self.verbose:
                print(f"[V3] ERROR guardando skills: {e}")
            return 0

    def match_and_persist(self, id_oferta: str, oferta_nlp: Dict,
                          categorize_skills: bool = True, run_id: str = None,
                          _allow_no_run: bool = False) -> MatchResult:
        """
        Ejecuta matching completo Y persiste resultados en BD.

        Este es el método recomendado para usar en pipelines de producción,
        ya que garantiza que tanto el matching como las skills se guarden.

        IMPORTANTE: Siempre extrae skills primero, incluso si una regla de
        negocio hace bypass del matching normal. Esto garantiza que las skills
        siempre se persistan.

        ⚠️ ADVERTENCIA (v3.3.2): Se recomienda SIEMPRE usar run_matching_pipeline()
        en lugar de llamar match_and_persist() directamente. Esto garantiza que
        cada corrida quede registrada con su run_id para tracking y comparación.

        Args:
            id_oferta: ID de la oferta
            oferta_nlp: Dict con campos NLP de la oferta
            categorize_skills: Si True, categoriza skills con L1/L2
            run_id: ID de la corrida (RECOMENDADO para run tracking v3.2.4)
            _allow_no_run: Si True, suprime el warning de run_id faltante (uso interno)

        Returns:
            MatchResult con el resultado del matching
        """
        # v3.3.2: Advertir si se llama sin run_id (indica uso incorrecto)
        if run_id is None and not _allow_no_run:
            import warnings
            warnings.warn(
                "[match_ofertas_v3] WARN: match_and_persist() llamado sin run_id. "
                "Para tracking correcto, usar run_matching_pipeline() en lugar de llamar "
                "match_and_persist() directamente. Las ofertas procesadas sin run_id "
                "no quedarán vinculadas a ninguna corrida.",
                UserWarning,
                stacklevel=2
            )
        titulo = oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo", "")
        tareas = oferta_nlp.get("tareas_explicitas", "")

        # 1. SIEMPRE extraer skills primero (antes del matching)
        # Esto garantiza que tengamos skills incluso si una regla hace bypass
        # v3.2.7: Incluir skills_nlp, soft_skills_nlp y contexto para ponderación
        skills_nlp = oferta_nlp.get("skills_tecnicas_list", [])
        if isinstance(skills_nlp, str):
            try:
                skills_nlp = json.loads(skills_nlp) if skills_nlp else []
            except (json.JSONDecodeError, TypeError):
                skills_nlp = []

        soft_skills_nlp = oferta_nlp.get("soft_skills_list", [])
        if isinstance(soft_skills_nlp, str):
            try:
                soft_skills_nlp = json.loads(soft_skills_nlp) if soft_skills_nlp else []
            except (json.JSONDecodeError, TypeError):
                soft_skills_nlp = []

        # v3.5.0: Usar extraccion dual de skills
        skills_dual_result = self.skills_extractor.extract_skills_dual(
            titulo_limpio=titulo,
            tareas_explicitas=tareas,
            oferta_nlp=oferta_nlp,
            skills_nlp=skills_nlp,
            soft_skills_nlp=soft_skills_nlp,
            sector_empresa=oferta_nlp.get("sector_empresa"),
            nivel_seniority=oferta_nlp.get("nivel_seniority"),
            area_funcional=oferta_nlp.get("area_funcional")
        )
        skills_extracted = skills_dual_result["skills_final"]

        if self.verbose:
            metodo_skills = skills_dual_result.get("metodo_primario", "semantico")
            print(f"[V3] Skills extraídas: {len(skills_extracted)} (metodo: {metodo_skills})")

        # 2. Ejecutar matching
        result = self.match(oferta_nlp)

        # 3. Si el matching vino de una regla de negocio, puede no tener skills
        # En ese caso, usar las que extrajimos arriba
        if not result.skills_extracted and skills_extracted:
            # Crear nuevo result con las skills extraídas
            result = MatchResult(
                status=result.status,
                esco_uri=result.esco_uri,
                esco_label=result.esco_label,
                isco_code=result.isco_code,
                score=result.score,
                metodo=result.metodo,
                skills_extracted=skills_extracted,  # <-- Agregar skills
                skills_matched=result.skills_matched,
                alternativas=result.alternativas,
                metadata={**result.metadata, "skills_count": len(skills_extracted)}
            )

        # 4. Categorizar skills si se solicita
        skills_to_save = result.skills_extracted
        if categorize_skills and skills_to_save:
            try:
                from skill_categorizer import SkillCategorizer
                categorizer = SkillCategorizer()
                skills_to_save = categorizer.categorize_batch(skills_to_save)
            except Exception as e:
                if self.verbose:
                    print(f"[V3] WARN: No se pudo categorizar skills: {e}")

        # 5. Persistir matching (con run_id si está disponible)
        self.save_matching_result(id_oferta, result, run_id=run_id)

        # 6. Persistir skills
        self.save_skills_detalle(id_oferta, skills_to_save)

        if self.verbose:
            print(f"[V3] Pipeline completo persistido para {id_oferta}")

        return result


def match_oferta_v3(oferta_nlp: Dict, db_conn: sqlite3.Connection = None) -> MatchResult:
    """
    Funcion de conveniencia para matching v3.

    Args:
        oferta_nlp: Dict con campos NLP
        db_conn: Conexion SQLite (opcional)

    Returns:
        MatchResult
    """
    matcher = MatcherV3(db_conn=db_conn, verbose=False)
    result = matcher.match(oferta_nlp)
    if not db_conn:
        matcher.close()
    return result


def test_v3():
    """Test del pipeline v3 con casos problematicos."""
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("=" * 70)
    print("TEST: Matching v3.0 - Skills First")
    print("=" * 70)

    casos_test = [
        {
            "titulo_limpio": "Consultor Junior de Liquidacion de Sueldos",
            "tareas_explicitas": "Calculo de aportes; Gestion de nominas; Liquidacion mensual",
            "esperado_isco": "4313"
        },
        {
            "titulo_limpio": "Asistente Compliance",
            "tareas_explicitas": "Revision de contratos; Cumplimiento normativo; Analisis de riesgos",
            "esperado_isco": "2611"
        },
        {
            "titulo_limpio": "Project Manager IT",
            "tareas_explicitas": "Gestion de proyectos; Coordinacion de equipos; Seguimiento Jira",
            "esperado_isco": "1213"
        },
        {
            "titulo_limpio": "Responsable de Deposito",
            "tareas_explicitas": "Control de inventarios; Gestion de stock; Coordinacion equipo",
            "esperado_isco": "1324"
        }
    ]

    matcher = MatcherV3(verbose=True)

    for caso in casos_test:
        print(f"\n{'='*60}")
        print(f"Caso: {caso['titulo_limpio']}")
        print(f"Esperado: ISCO {caso['esperado_isco']}")
        print("=" * 60)

        result = matcher.match(caso)

        print(f"\nResultado:")
        print(f"  ISCO: {result.isco_code}")
        print(f"  Label: {result.esco_label}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Metodo: {result.metodo}")
        print(f"  Skills matched: {result.skills_matched[:3]}...")

        if result.isco_code == caso["esperado_isco"]:
            print("  >>> CORRECTO!")
        else:
            print(f"  >>> INCORRECTO (esperado {caso['esperado_isco']})")

    matcher.close()


def run_matching_pipeline(
    offer_ids: List[str] = None,
    limit: int = None,
    only_pending: bool = True,
    verbose: bool = False,
    source: str = "manual",
    description: str = "",
    track_run: bool = True,
    force: bool = False
) -> Dict:
    """
    Ejecuta el pipeline completo de matching con persistencia automática.

    Esta función es el PUNTO DE ENTRADA recomendado para producción.
    Procesa ofertas desde ofertas_nlp y guarda en ofertas_esco_matching + ofertas_esco_skills_detalle.

    v3.2.4: Integración con Run Tracking para versionado de corridas.

    Args:
        offer_ids: Lista de IDs específicos a procesar (None = todas)
        limit: Límite de ofertas a procesar
        only_pending: Si True, solo procesa ofertas sin matching previo
        verbose: Mostrar progreso
        source: Origen de los IDs (gold_set_100, manual, etc.) - para run tracking
        description: Descripción de la corrida - para run tracking
        track_run: Si True, crea un run y guarda métricas (default True)
        force: Si True, permite reprocesar ofertas validadas (default False)

    Returns:
        Dict con estadísticas del procesamiento (incluye run_id si track_run=True)
    """
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

    db_path = Path(__file__).parent / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # PROTECCIÓN: Solo ofertas con validado_humano son inmutables (a menos que force=True)
    # v3.4.3: validado_claude es reprocesable, validado_humano NO
    if offer_ids and not force:
        cur = conn.execute('''
            SELECT id_oferta FROM ofertas_esco_matching
            WHERE id_oferta IN ({})
            AND estado_validacion = 'validado_humano'
        '''.format(','.join(['?'] * len(offer_ids))), offer_ids)
        validated = [row[0] for row in cur.fetchall()]
        if validated:
            conn.close()
            raise ValueError(
                f"[ERROR] No se pueden reprocesar ofertas validadas por humano: {validated[:10]}... "
                f"({len(validated)} total). Use force=True para forzar."
            )

    # PROTECCIÓN v3.4.3: Solo excluir validado_humano (validado_claude es reprocesable)
    exclude_validated_clause = ""
    if not force and not offer_ids:
        exclude_validated_clause = """
            AND n.id_oferta NOT IN (
                SELECT id_oferta FROM ofertas_esco_matching
                WHERE estado_validacion = 'validado_humano'
            )
        """

    # Construir query
    # v3.3.5: Agregar JOIN con ofertas para obtener titulo_original (necesario para exclusiones)
    if offer_ids:
        placeholders = ','.join(['?'] * len(offer_ids))
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa,
                   o.titulo as titulo_original
            FROM ofertas_nlp n
            LEFT JOIN ofertas o ON CAST(n.id_oferta AS INTEGER) = o.id_oferta
            WHERE n.id_oferta IN ({placeholders})
        '''
        params = offer_ids
    elif only_pending:
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa,
                   o.titulo as titulo_original
            FROM ofertas_nlp n
            LEFT JOIN ofertas o ON CAST(n.id_oferta AS INTEGER) = o.id_oferta
            LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
            WHERE m.id_oferta IS NULL
            {exclude_validated_clause}
        '''
        params = []
    else:
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa,
                   o.titulo as titulo_original
            FROM ofertas_nlp n
            LEFT JOIN ofertas o ON CAST(n.id_oferta AS INTEGER) = o.id_oferta
            WHERE 1=1
            {exclude_validated_clause}
        '''
        params = []

    if limit:
        query += f' LIMIT {limit}'

    cur = conn.execute(query, params)
    ofertas = cur.fetchall()

    # Obtener IDs procesados
    processed_ids = [str(o['id_oferta']) for o in ofertas]

    # Crear run si está habilitado
    run_id = None
    tracker = None
    if track_run:
        try:
            from run_tracking import RunTracker
            tracker = RunTracker()
            run_id = tracker.create_run(
                offer_ids=processed_ids,
                source=source,
                description=description
            )
        except ImportError:
            if verbose:
                print("[PIPELINE] WARN: run_tracking no disponible, continuando sin tracking")
        except Exception as e:
            if verbose:
                print(f"[PIPELINE] WARN: No se pudo crear run: {e}")

    if verbose:
        print(f"\n[PIPELINE] Procesando {len(ofertas)} ofertas...")
        if run_id:
            print(f"[PIPELINE] Run ID: {run_id}")

    # Inicializar matcher
    matcher = MatcherV3(db_conn=conn, verbose=verbose)

    stats = {
        'total': len(ofertas),
        'procesadas': 0,
        'errores': 0,
        'skills_totales': 0,
        'run_id': run_id
    }

    for i, oferta in enumerate(ofertas, 1):
        try:
            id_oferta = str(oferta['id_oferta'])
            # v3.3.5: Incluir titulo_original para exclusiones en reglas de negocio
            titulo_original = oferta['titulo_original'] if 'titulo_original' in oferta.keys() else None
            oferta_nlp = {
                'titulo_limpio': oferta['titulo_limpio'] or '',
                'titulo': titulo_original or oferta['titulo_limpio'] or '',  # titulo_original para exclusiones
                'tareas_explicitas': oferta['tareas_explicitas'] or '',
                'area_funcional': oferta['area_funcional'] or '',
                'nivel_seniority': oferta['nivel_seniority'] or '',
                'sector_empresa': oferta['sector_empresa'] or ''
            }

            result = matcher.match_and_persist(id_oferta, oferta_nlp, run_id=run_id)
            stats['procesadas'] += 1
            stats['skills_totales'] += len(result.skills_extracted)

            if verbose and i % 10 == 0:
                print(f"[PIPELINE] {i}/{len(ofertas)} procesadas...")

        except Exception as e:
            stats['errores'] += 1
            if verbose:
                print(f"[PIPELINE] ERROR en {oferta['id_oferta']}: {e}")

    matcher.close()
    conn.close()

    # Guardar resultados del run
    if tracker and run_id:
        try:
            metricas = {
                'total': stats['total'],
                'procesadas': stats['procesadas'],
                'errores': stats['errores'],
                'skills_totales': stats['skills_totales'],
                'precision': stats['procesadas'] / stats['total'] if stats['total'] > 0 else 0
            }
            tracker.save_results(run_id, metricas)
        except Exception as e:
            if verbose:
                print(f"[PIPELINE] WARN: No se pudieron guardar resultados del run: {e}")

    if verbose:
        print(f"\n[PIPELINE] Completado:")
        print(f"  Procesadas: {stats['procesadas']}/{stats['total']}")
        print(f"  Errores: {stats['errores']}")
        print(f"  Skills totales: {stats['skills_totales']}")
        if run_id:
            print(f"  Run ID: {run_id}")

    return stats


if __name__ == "__main__":
    test_v3()
