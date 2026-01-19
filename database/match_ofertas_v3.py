#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Match Ofertas v3.3.0 - Skills-First Matching Pipeline con Diccionario Argentino
================================================================================

VERSION: 3.3.0
FECHA: 2026-01-14
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

FLUJO v3.3.0:
1. Extraer skills desde titulo_limpio + tareas_explicitas (con origen)
1b. Diccionario argentino - si matchea, retornar directo (score 0.90)
2. Buscar ocupaciones por skills (esco_associations) con pesos por origen
3. Match semantico del titulo (como respaldo)
4. Combinar scores (60% skills + 40% titulo)
5. Penalizaciones (sector + seniority)
6. Reglas de negocio como CORRECCION (no bypass)
7. PERSISTIR resultados en BD

METODOS DE PERSISTENCIA:
- match_and_persist(id, oferta): Match + guarda matching + skills
- save_matching_result(id, result): Guarda solo matching
- save_skills_detalle(id, skills): Guarda solo skills

FUNCION DE PIPELINE (produccion):
- run_matching_pipeline(offer_ids, limit, only_pending): Procesa lote con persistencia

VENTAJAS:
- Skills de tareas pesan más que del título (tareas son más confiables)
- Resuelve casos ambiguos ("Consultor" -> segun skills, no solo titulo)
- Skills y ocupacion quedan coherentes
- Mejor precision en casos con tareas ricas
- DATOS SIEMPRE PERSISTIDOS en BD
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
    Pipeline de matching v3.2.2 - Skills First con penalizaciones sector + seniority.
    """

    VERSION = "3.3.3"  # v3.3.3: Tracking histórico (ofertas_matching_history + run_ofertas)

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
        Pipeline principal de matching v3.

        v3.3.0: CAMBIO ESTRUCTURAL - Matching semantico PRIMERO, reglas como correccion.

        Flujo anterior (v3.2.x):
          1. Reglas de negocio (bypass) -> si aplica, retorna inmediato
          2. Matching semantico (solo si no hay regla)

        Flujo nuevo (v3.3.0):
          1. SIEMPRE matching semantico primero
          2. Reglas de negocio SOLO como correccion si:
             - Score semantico es bajo (<0.6)
             - O regla tiene flag "correccion_critica": true

        Args:
            oferta_nlp: Dict con campos NLP de la oferta

        Returns:
            MatchResult con ocupacion, skills, score, etc.
        """
        titulo = oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo", "")
        tareas = oferta_nlp.get("tareas_explicitas", "")

        if self.verbose:
            print(f"\n[V3.3] === Matching: {titulo[:50]}... ===")

        # PASO 1: Extraer skills desde titulo + tareas + skills_nlp (v3.2.6)
        # v3.2.6: Agregamos skills_tecnicas_list del NLP como fuente adicional
        # Esto es CRÍTICO cuando tareas_explicitas es NULL pero el LLM detectó skills
        skills_nlp = oferta_nlp.get("skills_tecnicas_list", [])
        if isinstance(skills_nlp, str):
            # Si viene como string JSON, parsearlo
            try:
                import json
                skills_nlp = json.loads(skills_nlp) if skills_nlp else []
            except:
                skills_nlp = []

        # v3.2.7: Pasar contexto para ponderación de skills genéricas
        # v3.2.7: Agregar soft_skills_list también
        soft_skills_nlp = oferta_nlp.get("soft_skills_list", [])
        if isinstance(soft_skills_nlp, str):
            try:
                soft_skills_nlp = json.loads(soft_skills_nlp) if soft_skills_nlp else []
            except:
                soft_skills_nlp = []

        skills_extracted = self.skills_extractor.extract_skills(
            titulo_limpio=titulo,
            tareas_explicitas=tareas,
            skills_nlp=skills_nlp,
            soft_skills_nlp=soft_skills_nlp,
            sector_empresa=oferta_nlp.get("sector_empresa"),
            nivel_seniority=oferta_nlp.get("nivel_seniority"),
            area_funcional=oferta_nlp.get("area_funcional")
        )

        if self.verbose:
            print(f"[V3] Skills extraidas: {len(skills_extracted)}")

        # PASO 1b: PRIMERO verificar reglas de negocio especificas (v3.3.2)
        # Las reglas de negocio tienen prioridad sobre el diccionario argentino
        # porque son correcciones especificas para casos puntuales
        rule_result = self._check_business_rules(oferta_nlp, mode="bypass")
        if rule_result:
            if self.verbose:
                print(f"[V3.3.2] Bypass por regla de negocio: ISCO {rule_result.isco_code}")
            rule_result.skills_extracted = skills_extracted
            return rule_result

        # PASO 1c: Intentar match por diccionario argentino (v3.3.0)
        # Solo si no hay regla de negocio especifica
        dict_match = self._match_by_argentino_dict(oferta_nlp)
        if dict_match:
            isco = dict_match["isco_code"]
            label = dict_match["esco_label"]
            if self.verbose:
                print(f"[V3.3] Match diccionario argentino: {dict_match['termino_matched']} -> ISCO {isco}")

            return MatchResult(
                status=MatchStatus.MATCHED.value,
                esco_uri="",
                esco_label=label,
                isco_code=isco,
                score=dict_match["score"],
                metodo=dict_match["metodo"],
                skills_extracted=skills_extracted,
                skills_matched=[],
                alternativas=[],
                metadata={
                    "diccionario_argentino": True,
                    "termino_matched": dict_match["termino_matched"]
                }
            )

        # PASO 2: Match por skills
        candidates_by_skills = []
        if skills_extracted:
            candidates_by_skills = self.skills_matcher.match(skills_extracted, top_n=10)
            if self.verbose:
                print(f"[V3] Candidatos por skills: {len(candidates_by_skills)}")

        # PASO 3: Match semantico del titulo
        candidates_by_title = self._semantic_match_title(titulo)
        if self.verbose:
            print(f"[V3] Candidatos por titulo: {len(candidates_by_title)}")

        # PASO 4: Combinar scores
        if candidates_by_skills:
            # Tenemos resultados por skills - usar combinacion
            final_candidates = self._combine_candidates(
                candidates_by_skills,
                candidates_by_title
            )
            metodo = "skills_first_v3"
        elif candidates_by_title:
            # Solo tenemos semantico - fallback
            final_candidates = candidates_by_title
            metodo = "semantic_fallback_v3"
        else:
            # Sin candidatos
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
                metadata={"razon": "Sin candidatos"}
            )

        # PASO 5: Aplicar penalizacion por sector incompatible (v3.2.1)
        sector_empresa = oferta_nlp.get("sector_empresa", "")
        if sector_empresa:
            final_candidates = self._apply_sector_penalty(final_candidates, sector_empresa)
            if self.verbose:
                print(f"[V3] Sector empresa: {sector_empresa}")

        # PASO 6: Aplicar penalizacion por nivel_seniority incompatible (v3.2.2 - FASE 3)
        nivel_seniority = oferta_nlp.get("nivel_seniority", "")
        if nivel_seniority:
            final_candidates = self._apply_seniority_penalty(final_candidates, nivel_seniority)
            if self.verbose:
                print(f"[V3] Nivel seniority: {nivel_seniority}")

        # Seleccionar mejor candidato del matching semantico
        best = final_candidates[0]
        semantic_score = best.get("combined_score", best.get("score", 0))
        alternativas = final_candidates[1:4]  # Top 3 alternativas

        # v3.3.0: PASO 7 - Aplicar reglas como CORRECCION (no bypass)
        # Solo si: score bajo (<0.75) O regla tiene "correccion_critica": true
        # v3.3.1: Subido umbral de 0.60 a 0.75 porque el semantico aun no es confiable
        UMBRAL_SCORE_BAJO = 0.75
        rule_result = None

        if semantic_score < UMBRAL_SCORE_BAJO:
            # Score bajo - verificar si hay regla que corrija
            rule_result = self._check_business_rules(oferta_nlp, mode="correccion")
            if rule_result and self.verbose:
                print(f"[V3.3] Score bajo ({semantic_score:.2f}), aplicando correccion por regla")
        else:
            # Score alto - solo verificar reglas criticas
            rule_result = self._check_business_rules(oferta_nlp, mode="critica_only")
            if rule_result and self.verbose:
                print(f"[V3.3] Regla critica aplicada sobre score semantico {semantic_score:.2f}")

        # Si hay correccion por regla, usarla; sino mantener semantico
        if rule_result:
            # Agregar skills extraidas al resultado de regla
            rule_result.skills_extracted = skills_extracted
            rule_result.metadata["semantic_score_original"] = semantic_score
            rule_result.metadata["semantic_isco_original"] = best.get("isco_code", "").lstrip("C")
            return rule_result

        # Limpiar codigo ISCO (quitar 'C' prefix si existe)
        isco_code = best.get("isco_code", "")
        if isco_code and isco_code.startswith("C"):
            isco_code = isco_code[1:]

        return MatchResult(
            status=MatchStatus.SKILLS_FIRST.value if "skills" in metodo else MatchStatus.SEMANTIC.value,
            esco_uri=best.get("occupation_uri", ""),
            esco_label=best.get("esco_label", ""),
            isco_code=isco_code,
            score=semantic_score,
            metodo=metodo,
            skills_extracted=skills_extracted,
            skills_matched=best.get("skills_matched", []),
            alternativas=[
                {
                    "esco_uri": a.get("occupation_uri", ""),
                    "esco_label": a.get("esco_label", ""),
                    "isco_code": a.get("isco_code", "").lstrip("C"),
                    "score": a.get("combined_score", a.get("score", 0))
                }
                for a in alternativas
            ],
            metadata={
                "skills_count": len(skills_extracted),
                "skills_matched_count": len(best.get("skills_matched", []))
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
        tareas = (oferta_nlp.get("tareas_explicitas") or "").lower()
        reglas = self.business_rules.get("reglas_forzar_isco", {})

        for rule_id, rule in reglas.items():
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
                excluir_titulo = condicion.get("titulo_no_contiene_alguno", [])
                if excluir_titulo and any(t.lower() in titulo for t in excluir_titulo):
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
                label = accion.get("esco_label", "")

                if self.verbose:
                    modo_str = "correccion" if mode == "correccion" else "critica"
                    print(f"[V3.3] Regla {rule_id} ({modo_str}): {rule.get('nombre', '')}")

                # Buscar URI de la ocupacion
                esco_uri = self._find_occupation_uri(isco, label)

                return MatchResult(
                    status=MatchStatus.BUSINESS_RULE.value,
                    esco_uri=esco_uri,
                    esco_label=label,
                    isco_code=isco,
                    score=0.98,
                    metodo=f"regla_negocio_{rule_id}",
                    skills_extracted=[],
                    skills_matched=[],
                    alternativas=[],
                    metadata={"regla": rule_id, "nombre_regla": rule.get("nombre", "")}
                )

        return None

    def _find_occupation_uri(self, isco_code: str, label: str) -> str:
        """Busca el URI de una ocupacion por ISCO y label."""
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
                "isco_code": meta.get("isco_code", ""),
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
                "isco_code": base.get("isco_code", ""),
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

        Args:
            id_oferta: ID de la oferta
            result: MatchResult del matching
            run_id: ID de la corrida (opcional, para run tracking v3.2.4)

        Returns:
            True si se guardó correctamente
        """
        from datetime import datetime

        try:
            # Preparar alternativas como JSON
            alt1 = result.alternativas[0] if len(result.alternativas) > 0 else {}
            alt2 = result.alternativas[1] if len(result.alternativas) > 1 else {}
            alt3 = result.alternativas[2] if len(result.alternativas) > 2 else {}

            self.conn.execute('''
                INSERT OR REPLACE INTO ofertas_esco_matching (
                    id_oferta, esco_occupation_uri, esco_occupation_label,
                    occupation_match_score, occupation_match_method,
                    isco_code, isco_label,
                    skills_oferta_json, skills_matched_essential,
                    skills_demandados_total, skills_matcheados_esco,
                    matching_timestamp, matching_version, run_id,
                    estado_validacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                'pendiente'  # v3.2.5: Estado validación inicial
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
                print(f"[V3] Matching guardado para {id_oferta}" + (f" (run: {run_id})" if run_id else ""))
            return True

        except Exception as e:
            logger.error(f"Error guardando matching para {id_oferta}: {e}")
            if self.verbose:
                print(f"[V3] ERROR guardando matching: {e}")
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
                import json
                skills_nlp = json.loads(skills_nlp) if skills_nlp else []
            except:
                skills_nlp = []

        soft_skills_nlp = oferta_nlp.get("soft_skills_list", [])
        if isinstance(soft_skills_nlp, str):
            try:
                import json
                soft_skills_nlp = json.loads(soft_skills_nlp) if soft_skills_nlp else []
            except:
                soft_skills_nlp = []

        skills_extracted = self.skills_extractor.extract_skills(
            titulo_limpio=titulo,
            tareas_explicitas=tareas,
            skills_nlp=skills_nlp,
            soft_skills_nlp=soft_skills_nlp,
            sector_empresa=oferta_nlp.get("sector_empresa"),
            nivel_seniority=oferta_nlp.get("nivel_seniority"),
            area_funcional=oferta_nlp.get("area_funcional")
        )

        if self.verbose:
            print(f"[V3] Skills extraídas: {len(skills_extracted)}")

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

    # PROTECCIÓN: Verificar que no haya ofertas validadas (a menos que force=True)
    if offer_ids and not force:
        cur = conn.execute('''
            SELECT id_oferta FROM ofertas_esco_matching
            WHERE id_oferta IN ({})
            AND estado_validacion = 'validado'
        '''.format(','.join(['?'] * len(offer_ids))), offer_ids)
        validated = [row[0] for row in cur.fetchall()]
        if validated:
            conn.close()
            raise ValueError(
                f"[ERROR] No se pueden reprocesar ofertas validadas: {validated[:10]}... "
                f"({len(validated)} total). Use force=True para forzar o cambie el estado primero."
            )

    # PROTECCIÓN v3.3.4: Excluir ofertas validadas cuando se usa limit sin offer_ids
    exclude_validated_clause = ""
    if not force and not offer_ids:
        exclude_validated_clause = """
            AND n.id_oferta NOT IN (
                SELECT id_oferta FROM ofertas_esco_matching
                WHERE estado_validacion = 'validado'
            )
        """

    # Construir query
    if offer_ids:
        placeholders = ','.join(['?'] * len(offer_ids))
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa
            FROM ofertas_nlp n
            WHERE n.id_oferta IN ({placeholders})
        '''
        params = offer_ids
    elif only_pending:
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa
            FROM ofertas_nlp n
            LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
            WHERE m.id_oferta IS NULL
            {exclude_validated_clause}
        '''
        params = []
    else:
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa
            FROM ofertas_nlp n
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
            oferta_nlp = {
                'titulo_limpio': oferta['titulo_limpio'] or '',
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
