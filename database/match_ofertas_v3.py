#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Match Ofertas v3.3.0 - Skills-First Matching Pipeline con Diccionario Argentino
================================================================================

VERSION: 3.5.8
FECHA: 2026-02-19
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
from typing import Any, List, Dict, Optional, Tuple
from pathlib import Path
from enum import Enum

# Imports locales
from skills_implicit_extractor import SkillsImplicitExtractor
from match_by_skills import SkillsBasedMatcher
from config_loader import load_config

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


def _read_matcher_version() -> str:
    from pathlib import Path
    try:
        return (Path(__file__).parent / "MATCHER_VERSION").read_text().strip()
    except Exception:
        return "unknown"


class MatcherV3:
    """
    Pipeline de matching v3.4.0 - Dual Matching (reglas + semantico).
    """

    VERSION = _read_matcher_version()

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

        # SPEC J: index esco_code → ocupación, para resolución autoritativa
        self.code_to_occupation = {}
        for o in (self.occ_metadata or []):
            code = o.get('esco_code')
            if code and code not in self.code_to_occupation:
                # Derivar isco_4dig si no está presente
                isco = o.get('isco_4dig') or (code.split('.')[0] if '.' in code else code[:4])
                self.code_to_occupation[code] = {
                    'uri': o.get('uri', ''),
                    'label': o.get('label') or o.get('esco_label') or '',
                    'esco_code': code,
                    'isco_code': isco,
                }

        # SPEC U-1 v3.1 C2: index isco_4dig → ocupación canónica, fallback para
        # contextos del diccionario sin URI explícita. Prioriza esco_code == isco_4dig
        # (padre genérico) por sobre versiones con sufijo (.1.7 etc).
        self.isco_to_canonical_occupation = {}
        for o in (self.occ_metadata or []):
            isco = o.get('isco_4dig') or ''
            if not isco:
                continue
            esco_code = o.get('esco_code') or ''
            uri = o.get('uri', '')
            label = o.get('label') or o.get('esco_label') or ''
            if not uri:
                continue
            existing = self.isco_to_canonical_occupation.get(isco)
            # Preferir la entrada cuyo esco_code coincide con isco (más genérica)
            if existing is None or (esco_code == isco and existing.get('esco_code') != isco):
                self.isco_to_canonical_occupation[isco] = {
                    'uri': uri,
                    'label': label,
                    'esco_code': esco_code,
                }

    def _load_business_rules(self):
        """Carga reglas de negocio — override de Supabase o JSON local."""
        try:
            self.business_rules = load_config('matching_rules_business')
            if self.verbose:
                print(f"[V3] Cargadas reglas de negocio (via load_config)")
        except Exception as e:
            self.business_rules = {}
            if self.verbose:
                print(f"[V3] WARN: No se pudieron cargar reglas: {e}")

        # v3.6.0 [FRENTE H P4]: flag de activacion del traductor (piloto Eje 4).
        # Con flag ON el orden es: diccionario -> reglas L3 (preceden, laudo L3)
        # -> traductor (decide-cuando-decide) -> resto de reglas (subordinacion
        # L4 estructural: solo corren si el traductor no decidio) -> semantico.
        # Con flag OFF: flujo v3.5.x identico.
        try:
            _mc = json.load(open(Path(__file__).parent.parent / 'config' / 'matching_config.json'))
            self.traductor_activo = bool(_mc.get('traductor_activo'))
        except Exception:
            self.traductor_activo = False
        self._traductor = None  # lazy (solo se construye si el flag esta ON)
        if self.verbose and self.traductor_activo:
            print("[V3.6] Traductor de contexto ACTIVO (piloto 7 hubs)")

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

        # v3.4.3: Cargar mapeo ISCO -> label ESCO preferido
        self._load_isco_preferred_labels()

    def _load_sinonimos_argentinos(self):
        """Carga diccionario de sinonimos argentinos — override de Supabase o JSON local."""
        try:
            self.sinonimos_arg = load_config('sinonimos_argentinos_esco')
            if self.verbose:
                ocups = len(self.sinonimos_arg.get("ocupaciones_titulo", {}))
                print(f"[V3.3] Cargado diccionario argentino: {ocups} ocupaciones (via load_config)")
        except Exception as e:
            self.sinonimos_arg = {}
            if self.verbose:
                print(f"[V3.3] WARN: No se pudo cargar sinonimos_argentinos: {e}")

    def _load_isco_preferred_labels(self):
        """Carga mapeo ISCO -> label ESCO preferido desde JSON."""
        base_path = Path(__file__).parent
        config_path = base_path.parent / "config" / "isco_preferred_labels.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.isco_preferred_labels = data.get("mapeo", {})
            if self.verbose:
                print(f"[V3.4.3] Cargado mapeo ISCO preferred labels: {len(self.isco_preferred_labels)} ISCOs")
        except Exception as e:
            self.isco_preferred_labels = {}
            if self.verbose:
                print(f"[V3.4.3] WARN: No se pudo cargar isco_preferred_labels: {e}")

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

        # SPEC S1C-G3: ordenar los matches por la variante MÁS LARGA que matchea
        # (la más específica gana). Evita que una denominación genérica
        # ("vigilador/a", "sales") tape a una más específica que la contiene como
        # substring ("vigilador/a de personal" -> supervisor; "sales executive"
        # -> representante comercial). Antes ganaba la primera en orden de inserción.
        # SPEC U-1 v3.1 C2: la KEY del JSON siempre es una variante implícita
        # (ej: "jefe de mantenimiento" matchea aunque "variantes" no lo liste).
        candidatos = []
        for termino, config in ocupaciones.items():
            if termino.startswith("_"):
                continue
            variantes = list(config.get("variantes", []) or [])
            if termino not in variantes:
                variantes.append(termino)
            matched = [v for v in variantes if v.lower() in titulo]
            if matched:
                candidatos.append((max(len(v) for v in matched), termino, config))
        candidatos.sort(key=lambda x: x[0], reverse=True)

        for _mlen, termino, config in candidatos:
            # Hay match con el termino, ahora verificar contexto
            contextos = config.get("contextos", {})
            isco = None
            esco_label = config.get("esco_label", "")
            # SPEC U-1 v3.1 C2: URI raíz del JSON v2 (entradas con isco_primario)
            esco_uri_root = config.get("esco_uri", "")
            ctx_uri_override = ""
            ctx_label_override = ""
            ctx_code_override = ""

            if contextos:
                # Buscar contexto que matchee con titulo o sector
                for patron, ctx_value in contextos.items():
                    # SPEC U-1 v3.1 C2: contextos sin "|" (ej: "marketing") también
                    # se evalúan como una sola keyword. Antes se ignoraban.
                    keywords = patron.split("|") if "|" in patron else [patron]
                    if any(kw in titulo or kw in sector for kw in keywords):
                        # SPEC U-1 v3.1 C2: ctx_value puede ser dict (gerente/operador
                        # tras JSON v2) o string (legacy isco_primario+contextos).
                        if isinstance(ctx_value, dict):
                            isco = ctx_value.get("isco")
                            ctx_uri_override = ctx_value.get("esco_uri", "") or ""
                            ctx_label_override = ctx_value.get("esco_label", "") or ""
                            ctx_code_override = ctx_value.get("esco_code", "") or ""
                        else:
                            isco = ctx_value
                        # v3.4.3: Si el contexto cambió el ISCO, invalidar esco_label del padre
                        # para que se resuelva contra el nuevo ISCO
                        if esco_label and isco != config.get("isco_primario"):
                            esco_label = ctx_label_override
                        if self.verbose:
                            print(f"[V3.3] Dict argentino: '{termino}' + contexto '{patron}' -> ISCO {isco}")
                        break

            # SPEC S1C-G3 (3.a): resolución autoritativa por esco_code.
            # Si la entrada (o su contexto) trae un esco_code — el código exacto que
            # Cyn citó — resolverlo vía code_to_occupation, igual que las reglas en
            # _resolve_rule_target. El código es un token inequívoco: evita la
            # adivinanza de label sobre ISCO-4 (ambigua: 13 preferred + 602 alt
            # mapean a >1 URI) y el fallback silencioso (muerto tras Paso 0).
            # Gana sobre el camino isco→label heredado.
            matched_code = (ctx_code_override or config.get("esco_code", "") or "").strip()
            if matched_code:
                occ_by_code = self._find_occupation_by_esco_code(matched_code)
                if occ_by_code and occ_by_code.get("uri"):
                    if self.verbose:
                        print(f"[S1C-G3] Dict argentino: '{termino}' -> esco_code "
                              f"{matched_code} -> {occ_by_code.get('label')}")
                    return {
                        "isco_code": occ_by_code.get("isco_code"),
                        "esco_label": occ_by_code.get("label", ""),
                        "esco_uri": occ_by_code.get("uri", ""),
                        "score": 0.92,
                        "metodo": f"diccionario_argentino_{termino.replace(' ', '_')}",
                        "termino_matched": termino,
                        "via_resolucion": "esco_code",
                    }
                elif self.verbose:
                    print(f"[S1C-G3] esco_code '{matched_code}' no resuelve en "
                          f"metadata, fallback a isco/label")

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

                # SPEC U-1 v3.1 C2: resolver esco_uri en orden de prioridad
                #   1. Override de contexto dict (gerente/operador en JSON v2)
                #   2. URI raíz del JSON v2 si ISCO == isco_primario de la entrada
                #   3. Lookup canónico en isco_to_canonical_occupation por isco_4dig
                #   4. "" si nada de lo anterior aplica
                final_uri = ""
                if ctx_uri_override:
                    final_uri = ctx_uri_override
                elif esco_uri_root and isco == config.get("isco_primario"):
                    final_uri = esco_uri_root
                else:
                    canonical = self.isco_to_canonical_occupation.get(str(isco))
                    if canonical:
                        final_uri = canonical.get("uri", "")
                        if not esco_label:
                            esco_label = canonical.get("label", "")

                # Buscar label ESCO si no viene en config
                if not esco_label:
                    esco_label = self._get_esco_label_for_isco(isco)

                return {
                    "isco_code": isco,
                    "esco_label": esco_label,
                    "esco_uri": final_uri,  # SPEC U-1 v3.1 C2: URI ahora se propaga
                    "score": 0.90,  # Score alto por match de diccionario
                    "metodo": f"diccionario_argentino_{termino.replace(' ', '_')}",
                    "termino_matched": termino
                }

        return None

    def _get_esco_label_for_isco(self, isco_code: str) -> str:
        """Obtiene label ESCO para un código ISCO, vía mapeo explícito.

        SPEC S1C-G3 (Paso 0.b): la antigua rama de fallback a BD
        (`SELECT ... WHERE isco_code LIKE ? LIMIT 1` sin ORDER BY) devolvía un
        label ARBITRARIO del ISCO (ej 'café verde', 'vendedor de piezas de
        repuesto') cuando el ISCO no estaba mapeado. P.3 midió 0/3839 ofertas
        alcanzándola hoy → enterrarla es seguro. Ahora, en vez de inventar un
        label, falla de forma RUIDOSA: loguea y devuelve "" (sin label).

        El camino correcto para resolver el target del diccionario es por
        `esco_code` (token inequívoco de Cyn) vía `_find_occupation_by_esco_code`,
        no por adivinanza de label sobre el ISCO-4.
        """
        # Mapeo explícito (autoritativo)
        if isco_code in self.isco_preferred_labels:
            return self.isco_preferred_labels[isco_code]

        # Fallo ruidoso: NO inventar un label arbitrario para un ISCO no mapeado.
        logger.warning(
            "[S1C-G3/0.b] _get_esco_label_for_isco sin mapeo explícito para ISCO "
            "'%s' — se devuelve label vacío (antes se devolvía un label arbitrario "
            "vía LIMIT 1). Resolver el target por esco_code, no por ISCO.",
            isco_code,
        )
        return ""

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

    def _apply_supervision_penalty(
        self,
        candidates: List[Dict],
        tiene_gente_cargo: Any
    ) -> List[Dict]:
        """
        Penaliza/bonifica candidatos según coherencia con tiene_gente_cargo.

        v3.5.0: Reincorporado desde v2.
        - tiene_gente=False + ISCO 1xxx (directivos) → penalty -10%
        - tiene_gente=True + ISCO 1xxx → bonus +5%
        """
        if tiene_gente_cargo is None:
            return candidates

        tiene_gente = bool(tiene_gente_cargo)

        for candidate in candidates:
            isco_code = candidate.get("isco_code", "").lstrip("C")
            if not isco_code:
                continue

            is_directivo = isco_code.startswith("1")

            if not tiene_gente and is_directivo:
                original = candidate.get("combined_score", 0)
                candidate["combined_score"] = max(0, original - 0.10)
                candidate["supervision_penalty"] = -0.10
                if self.verbose:
                    print(f"[V3] Penalizacion supervision: ISCO {isco_code} directivo sin gente a cargo (-10%)")

            elif tiene_gente and is_directivo:
                original = candidate.get("combined_score", 0)
                candidate["combined_score"] = original + 0.05
                candidate["supervision_bonus"] = 0.05
                if self.verbose:
                    print(f"[V3] Bonus supervision: ISCO {isco_code} directivo con gente a cargo (+5%)")

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
            # SPEC U-1 v3.1 C2: bug fix — antes esta rama no asignaba semantic_uri,
            # quedaba con el default "" y persistía esco_occupation_uri vacía.
            semantic_uri = dict_match.get("esco_uri", "")
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
                # v3.5.5: Solo aplicar penalización de sector cuando confianza=alta.
                # 84% de los sectores vienen del LLM con confianza=media (10,180 de 12,098).
                # El LLM frecuentemente copia area_funcional como sector_empresa,
                # generando penalizaciones incorrectas.
                sector_empresa = oferta_nlp.get("sector_empresa", "")
                sector_confianza = oferta_nlp.get("sector_confianza", "")
                if sector_empresa and sector_confianza == "alta":
                    final_candidates = self._apply_sector_penalty(final_candidates, sector_empresa)

                nivel_seniority = oferta_nlp.get("nivel_seniority", "")
                if nivel_seniority:
                    final_candidates = self._apply_seniority_penalty(final_candidates, nivel_seniority)

                # v3.5.0: Penalización/bonus por tiene_gente_cargo
                tiene_gente = oferta_nlp.get("tiene_gente_cargo")
                if tiene_gente is not None:
                    final_candidates = self._apply_supervision_penalty(final_candidates, tiene_gente)

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
        # v3.6.0 [FRENTE H P4] con traductor_activo el orden es:
        #   diccionario -> reglas L3 (preceden) -> TRADUCTOR (decide-cuando-
        #   decide) -> resto de reglas (subordinacion L4) -> semantico
        # =====================================================================
        decision_piloto = None  # razon extra cuando el flag esta ON
        if self.traductor_activo:
            if dict_match:
                # el diccionario decide primero en el piloto: no se evaluan reglas
                rule_info = None
                decision_piloto = 'diccionario_prioridad_piloto'
            else:
                rule_info = self._evaluate_rule_only(oferta_nlp, solo_l3=True)
                if rule_info:
                    decision_piloto = 'L3_precede_traductor'
                else:
                    tr = self._evaluar_traductor(oferta_nlp)
                    if tr and tr.get('decide'):
                        occ = self.code_to_occupation.get(tr['codigo_esco'])
                        if occ:
                            tele_tags = {
                                'satelite': tr.get('satelite') or tr['traza'].get('satelite_exacto'),
                                'tag_guard_1a0': tr['traza'].get('tag_guard_1a0'),
                            }
                            return MatchResult(
                                status=MatchStatus.MATCHED.value,
                                esco_uri=occ.get('uri', ''),
                                esco_label=occ.get('esco_label') or occ.get('label', ''),
                                isco_code=str(occ.get('isco_code', '')).lstrip("C"),
                                score=0.97,
                                metodo="arbol_contexto",
                                skills_extracted=skills_extracted,
                                skills_matched=semantic_skills_matched,
                                alternativas=[],
                                metadata={
                                    "razon": f"traductor: hub {tr.get('hub_id')} regla {tr.get('regla_id')} ({tr.get('camino')})",
                                    "isco_semantico": semantic_isco,
                                    "score_semantico": semantic_score,
                                    "isco_regla": None,
                                    "regla_aplicada": None,
                                    "dual_coinciden": None,
                                    "decision_metodo": "arbol_contexto",
                                    "decision_razon": f"piloto Eje 4: {tr.get('regla_id')}@hub{tr.get('hub_id')} camino={tr.get('camino')}",
                                    "arbol_hub_id": tr.get('hub_id'),
                                    "arbol_regla_id": tr.get('regla_id'),
                                    "arbol_camino": tr.get('camino'),
                                    "arbol_traza_json": json.dumps({**tr.get('traza', {}), **tele_tags}, ensure_ascii=False),
                                    "skills_regla_json": json.dumps(skills_regla) if skills_regla else None,
                                    "skills_semantico_json": json.dumps(skills_semantico) if skills_semantico else None,
                                    "skills_regla_aplicada": skills_regla_aplicada,
                                    "dual_coinciden_skills": dual_coinciden_skills,
                                    "metodo_skills": metodo_skills,
                                }
                            )
                    # el traductor no decidio (o destino fuera de catalogo):
                    # resto de reglas = subordinacion estructural (L4)
                    rule_info = self._evaluate_rule_only(oferta_nlp, solo_l3=False)
                    if tr and tr.get('telemetria') == 'satelite_exacto_abstencion':
                        decision_piloto = f"satelite_exacto_abstencion:{tr.get('satelite')}"
                    elif tr and tr.get('traza', {}).get('tag_guard_1a0'):
                        decision_piloto = 'guard_1a0_bloqueo'
        else:
            rule_info = self._evaluate_rule_only(oferta_nlp)

        regla_isco = None
        regla_aplicada = None
        regla_critica = False
        override_semantico = False
        if rule_info:
            regla_isco = rule_info["isco_code"]
            regla_aplicada = rule_info["rule_id"]
            regla_critica = rule_info.get("correccion_critica", False)
            override_semantico = rule_info.get("override_semantico", False)
            if self.verbose:
                flags = []
                if regla_critica: flags.append("CRITICA")
                if override_semantico: flags.append("OVERRIDE_SEM")
                flag_str = f" ({', '.join(flags)})" if flags else ""
                print(f"[V3.4] Regla aplicable: {regla_aplicada} -> ISCO {regla_isco}{flag_str}")

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
            regla_id=regla_aplicada,
            regla_critica=regla_critica,
            override_semantico=override_semantico
        )
        # v3.6.0: telemetria del piloto (dict-prioridad / L3 / abstenciones con tag)
        if decision_piloto:
            decision_razon = f"{decision_razon} | piloto: {decision_piloto}"

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
        # v3.5.3 FIX: También usar regla cuando dual_coinciden=1 (mismo ISCO pero
        # el label de la regla es más específico, ej: "software developer" vs "blockchain")
        use_rule_label = ("regla" in decision_metodo or decision_metodo == "dual_coinciden") and rule_info
        if use_rule_label:
            # La decisión es usar la regla — SPEC J: usar esco_code si está disponible
            rule_occupation = self._resolve_rule_target(rule_info)
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

            # v3.5.4: Verificar titulo_original_contiene_alguno (busca en título SIN limpiar)
            # Útil cuando NLP elimina siglas/códigos del título (ej: "619BE | HRBP | ROSARIO" -> "Rosario")
            terminos_orig = condicion.get("titulo_original_contiene_alguno", [])
            if terminos_orig:
                condiciones_evaluadas.append(any(t.lower() in titulo_original for t in terminos_orig))

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
                condicion_cumplida = (oferta_nlp.get("area_funcional") or "").lower() == area_requerida.lower()
            else:
                condicion_cumplida = condicion_texto_cumplida

            # Verificar sector_es como filtro adicional (AND con otras condiciones)
            sector_requerido = condicion.get("sector_es")
            if condicion_cumplida and sector_requerido:
                sector_actual = (oferta_nlp.get("sector_empresa") or "").lower()
                condicion_cumplida = sector_actual == sector_requerido.lower()

            # Verificar sector_empresa_es_alguno (lista de sectores válidos)
            sectores_validos = condicion.get("sector_empresa_es_alguno", [])
            if condicion_cumplida and sectores_validos:
                sector_actual = (oferta_nlp.get("sector_empresa") or "").lower()
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
                sector_actual = (oferta_nlp.get("sector_empresa") or "").lower()
                if excluir_sector and any(s.lower() == sector_actual for s in excluir_sector):
                    condicion_cumplida = False

                # area_funcional_no_es: excluir si el área es alguna de estas
                excluir_area = condicion.get("area_funcional_no_es", [])
                area_actual = (oferta_nlp.get("area_funcional") or "").lower()
                if excluir_area and any(a.lower() == area_actual for a in excluir_area):
                    condicion_cumplida = False

            if condicion_cumplida:
                # v3.4.2: ESCO es el target primario, ISCO se deriva
                # SPEC J: usar esco_code (autoritativo) con fallback a esco_label
                occupation = self._resolve_rule_target(accion)

                if not occupation:
                    if self.verbose:
                        target = accion.get('esco_code') or accion.get('esco_label', '?')
                        print(f"[V3.4.2] WARN: Regla {rule_id} - ESCO target no encontrado: '{target}'")
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

    def _get_traductor(self):
        """v3.6.0: instancia lazy del evaluador de reglas de contexto (Eje 4).

        Fuentes de runtime: hubs_activos.json (7 activos), lexico_traductor.json
        (v0.3.4), traductor_exclusiones_trigger.json, y el piso de satelites
        COMPILADO en config/traductor_piso_satelites.json (el grafo de exports/
        es artefacto de analisis, no precondicion de runtime).
        """
        if self._traductor is None:
            from traductor_contexto import TraductorContexto
            base = Path(__file__).parent.parent / 'config'
            excl = json.load(open(base / 'traductor_exclusiones_trigger.json'))['exclusiones']
            piso = json.load(open(base / 'traductor_piso_satelites.json'))['triggers']
            sats = {}
            for t in piso:
                sats.setdefault(t['trigger'], t['satelite'])
            tc = TraductorContexto(exclusiones_trigger=excl, satelites=sats)
            ya = {t for t, _ in tc._triggers}
            tc._triggers += [(t['trigger'], t['hub']) for t in piso if t['trigger'] not in ya]
            self._traductor = tc
        return self._traductor

    def _evaluar_traductor(self, oferta_nlp: Dict) -> Optional[Dict]:
        """v3.6.0: evalua el traductor sobre la oferta. Devuelve el dict del
        evaluador (decide/telemetria/traza) o None si no aplica/no decide."""
        def _txt(campo):
            v = oferta_nlp.get(campo)
            if isinstance(v, list):
                return ' '.join(str(x) for x in v)
            return str(v or '')
        titulo = oferta_nlp.get('titulo_limpio') or oferta_nlp.get('titulo', '')
        contenidos = {
            'tareas_explicitas': _txt('tareas_explicitas'),
            'skills_habilidades': f"{_txt('skills_tecnicas_list')} {_txt('soft_skills_list')}",
            'conocimientos': _txt('conocimientos_especificos_list'),
            'tecnologias': _txt('tecnologias_list'),
            'sistemas_herramientas': f"{_txt('sistemas_list')} {_txt('herramientas_list')}",
        }
        try:
            return self._get_traductor().evaluar(titulo, contenidos)
        except Exception as e:
            if self.verbose:
                print(f"[V3.6] WARN traductor: {e}")
            return None

    def _evaluate_rule_only(self, oferta_nlp: Dict, solo_l3: Optional[bool] = None) -> Optional[Dict]:
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
            # v3.6.0 (laudos L3/L4): pasada L3-solo (las especializadas preceden
            # al traductor) o pasada resto (subordinacion estructural: corren
            # solo cuando el traductor no decidio)
            if solo_l3 is True and '_traductor_L3' not in rule:
                continue
            if solo_l3 is False and '_traductor_L3' in rule:
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

            # v3.5.4: titulo_original_contiene_alguno (busca en título SIN limpiar)
            terminos_orig = condicion.get("titulo_original_contiene_alguno", [])
            if terminos_orig:
                condiciones_evaluadas.append(any(t.lower() in titulo_original for t in terminos_orig))

            # skills_contiene_alguno
            terminos_skills = condicion.get("skills_contiene_alguno", [])
            if terminos_skills:
                texto_completo = f"{titulo} {tareas}"
                condiciones_evaluadas.append(any(t.lower() in texto_completo for t in terminos_skills))

            condicion_texto_cumplida = len(condiciones_evaluadas) > 0 and all(condiciones_evaluadas)

            # area_funcional_es
            area_requerida = condicion.get("area_funcional_es")
            if condicion_texto_cumplida and area_requerida:
                condicion_cumplida = (oferta_nlp.get("area_funcional") or "").lower() == area_requerida.lower()
            else:
                condicion_cumplida = condicion_texto_cumplida

            # sector_es
            sector_requerido = condicion.get("sector_es")
            if condicion_cumplida and sector_requerido:
                sector_actual = (oferta_nlp.get("sector_empresa") or "").lower()
                condicion_cumplida = sector_actual == sector_requerido.lower()

            # sector_empresa_es_alguno
            sectores_validos = condicion.get("sector_empresa_es_alguno", [])
            if condicion_cumplida and sectores_validos:
                sector_actual = (oferta_nlp.get("sector_empresa") or "").lower()
                condicion_cumplida = any(s.lower() == sector_actual for s in sectores_validos)

            # EXCLUSIONES
            if condicion_cumplida:
                excluir_titulo = condicion.get("titulo_no_contiene_alguno", [])
                if excluir_titulo and any(t.lower() in titulo_original for t in excluir_titulo):
                    condicion_cumplida = False

                excluir_sector = condicion.get("sector_no_es", [])
                sector_actual = (oferta_nlp.get("sector_empresa") or "").lower()
                if excluir_sector and any(s.lower() == sector_actual for s in excluir_sector):
                    condicion_cumplida = False

                excluir_area = condicion.get("area_funcional_no_es", [])
                area_actual = (oferta_nlp.get("area_funcional") or "").lower()
                if excluir_area and any(a.lower() == area_actual for a in excluir_area):
                    condicion_cumplida = False

            if condicion_cumplida:
                # v3.4.2: ESCO es el target, ISCO se deriva
                # SPEC J: usar esco_code (autoritativo) con fallback a esco_label
                occupation = self._resolve_rule_target(accion)

                if occupation:
                    return {
                        "rule_id": rule_id,
                        "isco_code": occupation['isco_code'].lstrip("C"),  # ISCO derivado, sin prefijo C
                        "esco_code": occupation.get('esco_code', ''),  # SPEC J: pasar el código completo
                        "esco_label": occupation['label'],  # Label exacto de ESCO
                        "nombre_regla": rule.get("nombre", ""),
                        "correccion_critica": rule.get("correccion_critica", False),
                    # override_semantico: true — usar solo cuando el término del título
                    # es inequívoco y el semántico puede confundirse.
                    # Ej: enfermero, soldador, electricista.
                    "override_semantico": rule.get("override_semantico", False)
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
        regla_id: Optional[str],
        regla_critica: bool = False,
        override_semantico: bool = False
    ) -> Tuple[str, str, str]:
        """
        Decide cuál ISCO usar basado en confianza de cada método.

        v3.5.2: Semántico alta confianza (>=0.80) ahora gana sobre regla cuando divergen.
        v3.5.3: Reglas con correccion_critica=True SIEMPRE ganan (no se overridean).
        v3.5.4: Threshold subido a >=0.95. Con 0.80 overrideaba 860 reglas correctas.
        v3.5.5: override_semantico ignora el threshold de alta confianza para reglas
                 con términos de título inequívocos (enfermero, soldador, etc.)

        Args:
            regla_isco: ISCO de la regla de negocio (None si no aplica ninguna)
            semantic_isco: ISCO del matching semántico
            semantic_score: Score del matching semántico (0-1)
            regla_id: ID de la regla aplicada (None si no aplica ninguna)
            regla_critica: Si True, la regla no puede ser overrideada por semántico
            override_semantico: Si True, la regla gana incluso si score >= 0.95

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

        # Caso 2b: Regla crítica → SIEMPRE gana, sin override posible
        if regla_critica:
            return (regla_isco, "regla_critica",
                    f"regla {regla_id} (correccion_critica) fuerza ISCO {regla_isco}, semantico={semantic_isco} score={semantic_score:.2f}")

        # Caso 2c: override_semantico → regla gana incluso si semántico >= 0.95
        # Usar solo cuando el término del título es inequívoco y el semántico
        # puede confundirse. Ej: enfermero, soldador, electricista.
        if override_semantico:
            return (regla_isco, "regla_override_semantico",
                    f"regla {regla_id} (override_semantico) fuerza ISCO {regla_isco}, semantico={semantic_isco} score={semantic_score:.2f}")

        # Caso 3: Ambos disponibles - comparar primeros 4 dígitos (ISCO-4)
        # zfill(4) evita false negatives con ISCOs de 3 dígitos (ej: "332" vs "3322")
        regla_isco_4 = str(regla_isco).zfill(4)[:4]
        semantic_isco_4 = str(semantic_isco).zfill(4)[:4]

        if regla_isco_4 == semantic_isco_4:
            # Coinciden → alta confianza
            return (regla_isco, "dual_coinciden",
                    f"regla {regla_id} y semantico coinciden (ISCO {regla_isco_4})")

        # Caso 4: Divergen → decidir según score
        if semantic_score < 0.55:
            # Semántico poco confiable → usar regla
            return (regla_isco, "regla_por_score_bajo",
                    f"score semantico {semantic_score:.2f} < 0.55, regla {regla_id} prioridad")

        if semantic_score >= 0.95:
            # Semántico extremadamente confiable → gana sobre la regla
            # v3.5.4: subido de 0.80 a 0.95. Con 0.80 el semántico overrideaba 860 reglas
            # correctas (Community Manager→Director TIC, Ejecutivo Ventas→Vendedor, etc.)
            # porque scores 0.85-0.90 son comunes pero no indican match correcto.
            return (semantic_isco, "semantico_alta_confianza",
                    f"score {semantic_score:.2f} >= 0.95 override regla {regla_id} (isco_regla={regla_isco})")

        # Caso 5: Score < 0.95 con regla disponible → regla gana
        # v3.5.4: ampliada zona (antes 0.55-0.80, ahora 0.55-0.95)
        return (regla_isco, "regla_prioridad",
                f"regla {regla_id} prioridad (score semantico {semantic_score:.2f} < 0.95, semantico={semantic_isco})")

    def _find_occupation_by_esco_code(self, esco_code: str) -> Optional[Dict]:
        """
        SPEC J — Busca ocupación ESCO por código específico (autoritativo).

        El esco_code (ej "7214.3.1") es identificador único en el catálogo ESCO.
        Más confiable que esco_label (texto libre).

        Returns: dict con {uri, label, isco_code, esco_code} o None.
        """
        if not esco_code:
            return None
        return self.code_to_occupation.get(esco_code)

    def _resolve_rule_target(self, accion: Dict) -> Optional[Dict]:
        """
        SPEC J — Resuelve la ocupación target de una regla.

        Prioriza esco_code sobre esco_label (más preciso). Mantiene fallback
        para reglas que aún no tengan esco_code.
        """
        esco_code = accion.get('esco_code')
        if esco_code:
            occ = self._find_occupation_by_esco_code(esco_code)
            if occ:
                return occ
            # Si esco_code declarado no existe en metadata, fallback al label
            if self.verbose:
                print(f"[V3/SPEC-J] esco_code '{esco_code}' no encontrado en metadata, fallback a esco_label")
        return self._find_occupation_by_esco_label(accion.get('esco_label', ''))

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

    def _persist_skill_failures(self, oferta_id: str, run_id: str, failures: list) -> None:
        """
        M-06: Persiste intentos fallidos de extracción de skills.
        Fallo silencioso — no interrumpe el pipeline.
        """
        if not failures:
            return
        try:
            for f in failures:
                self.conn.execute('''
                    INSERT INTO skills_extraction_failures
                    (oferta_id, run_id, tarea_texto, tarea_origen,
                     mejor_skill_uri, mejor_skill_label, mejor_score,
                     threshold_usado, gap_al_umbral)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    oferta_id, run_id,
                    f.get("tarea_texto"), f.get("tarea_origen", "matching"),
                    f.get("mejor_skill_uri"), f.get("mejor_skill_label"),
                    f.get("mejor_score", 0.0),
                    f.get("threshold_usado", 0.40),
                    f.get("gap_al_umbral")
                ))
            self.conn.commit()
        except Exception as e:
            import logging
            logging.warning(f"[M-06] No se pudieron registrar {len(failures)} failures para {oferta_id}: {e}")

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
            # v3.5.9: Observabilidad del traductor (metodo arbol_contexto, FRENTE H)
            arbol_hub_id = meta.get("arbol_hub_id")
            arbol_regla_id = meta.get("arbol_regla_id")
            arbol_camino = meta.get("arbol_camino")
            arbol_traza_json = meta.get("arbol_traza_json")

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
                    decision_razon,
                    arbol_hub_id, arbol_regla_id, arbol_camino, arbol_traza_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                decision_razon,  # v3.5.1: Razon de la decision
                # v3.5.9: Observabilidad arbol_contexto (NULL salvo traductor)
                arbol_hub_id,
                arbol_regla_id,
                arbol_camino,
                arbol_traza_json
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

            # Dedup: filtrar skills sin URI + deduplicar por URI (mayor score gana)
            seen_uris = {}
            skipped_no_uri = 0
            for skill in skills:
                uri = (skill.get('skill_uri') or '').strip()
                if not uri:
                    skipped_no_uri += 1
                    continue
                if uri in seen_uris:
                    if (skill.get('score') or 0) > (seen_uris[uri].get('score') or 0):
                        seen_uris[uri] = skill
                else:
                    seen_uris[uri] = skill

            if skipped_no_uri and self.verbose:
                print(f"[V3] {skipped_no_uri} skills sin URI filtradas para {id_oferta}")

            deduped = len(skills) - skipped_no_uri - len(seen_uris)
            if deduped > 0 and self.verbose:
                print(f"[V3] {deduped} skills duplicadas por URI eliminadas para {id_oferta}")

            count = 0
            for skill in seen_uris.values():
                # M-08b: texto_original — texto fuente antes del match ESCO
                texto_orig = skill.get('texto_fuente') or skill.get('tarea') or None
                if texto_orig and len(texto_orig) > 200:
                    texto_orig = texto_orig[:200]

                self.conn.execute('''
                    INSERT INTO ofertas_esco_skills_detalle (
                        id_oferta, skill_mencionado, skill_tipo_fuente,
                        esco_skill_uri, esco_skill_label, match_score, match_method,
                        esco_skill_type, source_classification, texto_original
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(id_oferta),
                    skill.get('skill_esco', skill.get('skill', '')),
                    skill.get('origen', 'unknown'),
                    skill.get('skill_uri', ''),
                    skill.get('skill_esco', ''),
                    skill.get('score', 0),
                    'implicit_bge_m3',
                    skill.get('L1', 'T'),
                    json.dumps({
                        'L1': skill.get('L1', ''),
                        'L1_nombre': skill.get('L1_nombre', ''),
                        'L2': skill.get('L2', ''),
                        'L2_nombre': skill.get('L2_nombre', ''),
                        'es_digital': skill.get('es_digital', False)
                    }, ensure_ascii=False),
                    texto_orig
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
            area_funcional=oferta_nlp.get("area_funcional"),
            track_failures=True
        )
        skills_extracted = skills_dual_result["skills_final"]

        # M-06: Persistir tareas fallidas (fallo silencioso)
        failures = skills_dual_result.get("failures", [])
        if failures:
            self._persist_skill_failures(id_oferta, run_id, failures)

        if self.verbose:
            metodo_skills = skills_dual_result.get("metodo_primario", "semantico")
            print(f"[V3] Skills extraídas: {len(skills_extracted)} (metodo: {metodo_skills})")
            if failures:
                print(f"[V3] Tareas fallidas registradas: {len(failures)}")

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

        # 3b. M-08: Extraer skills de fuentes declaradas
        declared_skills, declared_failures = self.skills_extractor.extract_declared_skills(
            oferta_nlp, track_failures=True
        )

        # M-06: Persistir failures de declaradas
        if declared_failures:
            self._persist_skill_failures(id_oferta, run_id, declared_failures)

        # M-08: Merge declaradas con skills de tareas (dedup por equiv_group)
        if declared_skills:
            existing_keys = set()
            for s in skills_extracted:
                uri = s.get("skill_uri", "")
                group = self.skills_extractor.equiv_lookup.get(uri, uri)
                existing_keys.add(group)

            added = 0
            for s in declared_skills:
                uri = s.get("skill_uri", "")
                group = self.skills_extractor.equiv_lookup.get(uri, uri)
                if group not in existing_keys:
                    existing_keys.add(group)
                    skills_extracted.append(s)
                    added += 1

            if self.verbose and added > 0:
                print(f"[M-08] +{added} skills declaradas (de {len(declared_skills)} candidatas, {len(declared_skills) - added} dedup)")

            # Actualizar result con skills mergeadas
            if added > 0:
                result = MatchResult(
                    status=result.status,
                    esco_uri=result.esco_uri,
                    esco_label=result.esco_label,
                    isco_code=result.isco_code,
                    score=result.score,
                    metodo=result.metodo,
                    skills_extracted=skills_extracted,
                    skills_matched=result.skills_matched,
                    alternativas=result.alternativas,
                    metadata={**result.metadata, "skills_count": len(skills_extracted)}
                )

        # 3c. E2.2: Boost de skills con perfil argentino
        occupation_uri = result.esco_uri
        if occupation_uri and skills_extracted:
            skills_extracted = self.skills_extractor.rerank_with_argentino_boost(
                skills_extracted, occupation_uri
            )
            boosted_count = sum(1 for s in skills_extracted if s.get("boost_applied"))
            if boosted_count > 0:
                result = MatchResult(
                    status=result.status,
                    esco_uri=result.esco_uri,
                    esco_label=result.esco_label,
                    isco_code=result.isco_code,
                    score=result.score,
                    metodo=result.metodo,
                    skills_extracted=skills_extracted,
                    skills_matched=result.skills_matched,
                    alternativas=result.alternativas,
                    metadata={**result.metadata, "argentino_boost_count": boosted_count}
                )
                if self.verbose:
                    print(f"[E2.2] Boost argentino aplicado a {boosted_count}/{len(skills_extracted)} skills")

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

    # NLP Gate v1.0: Excluir ofertas bloqueadas por NLP validator
    nlp_gate_clause = " AND (n.nlp_gate_status IS NULL OR n.nlp_gate_status != 'bloqueado')"

    # Construir query
    # v3.3.5: Agregar JOIN con ofertas para obtener titulo_original (necesario para exclusiones)
    if offer_ids:
        placeholders = ','.join(['?'] * len(offer_ids))
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa,
                   o.titulo as titulo_original,
                   n.skills_tecnicas_list, n.tecnologias_list,
                   n.herramientas_list, n.soft_skills_list
            FROM ofertas_nlp n
            LEFT JOIN ofertas o ON CAST(n.id_oferta AS INTEGER) = o.id_oferta
            WHERE n.id_oferta IN ({placeholders})
            {nlp_gate_clause}
        '''
        params = offer_ids
    elif only_pending:
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa,
                   o.titulo as titulo_original,
                   n.skills_tecnicas_list, n.tecnologias_list,
                   n.herramientas_list, n.soft_skills_list
            FROM ofertas_nlp n
            LEFT JOIN ofertas o ON CAST(n.id_oferta AS INTEGER) = o.id_oferta
            LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
            WHERE m.id_oferta IS NULL
            {exclude_validated_clause}
            {nlp_gate_clause}
        '''
        params = []
    else:
        query = f'''
            SELECT n.id_oferta, n.titulo_limpio, n.tareas_explicitas,
                   n.area_funcional, n.nivel_seniority, n.sector_empresa,
                   o.titulo as titulo_original,
                   n.skills_tecnicas_list, n.tecnologias_list,
                   n.herramientas_list, n.soft_skills_list
            FROM ofertas_nlp n
            LEFT JOIN ofertas o ON CAST(n.id_oferta AS INTEGER) = o.id_oferta
            WHERE 1=1
            {exclude_validated_clause}
            {nlp_gate_clause}
        '''
        params = []

    # Solo aplicar LIMIT cuando NO se pasaron offer_ids explícitos.
    # Caller que pasa offer_ids ya decidió cuántas; aplicar LIMIT recortaba IDs
    # silenciosamente cuando len(offer_ids) > limit (p.ej. lote+sub-ofertas).
    if limit and not offer_ids:
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

    # EQUIV-UI: Verificar si equiv_lookup está desactualizado
    try:
        _config_path = Path(__file__).parent.parent / "config" / "supabase_config.json"
        if _config_path.exists():
            import json as _json
            _sb_config = _json.load(open(_config_path))
            if _sb_config.get('url') and _sb_config.get('anon_key'):
                from supabase import create_client as _create_client
                _sb = _create_client(_sb_config['url'], _sb_config['anon_key'])
                _latest = _sb.rpc('get_latest_equiv_update').execute()
                if _latest.data:
                    from datetime import datetime, timezone
                    _latest_str = str(_latest.data)
                    _latest_update = datetime.fromisoformat(_latest_str.replace('Z', '+00:00'))
                    _loaded_at = getattr(SkillsImplicitExtractor, '_equiv_loaded_at', None)
                    if _loaded_at and _latest_update > _loaded_at:
                        SkillsImplicitExtractor._equiv_lookup = None
                        SkillsImplicitExtractor._equiv_groups = None
                        SkillsImplicitExtractor._initialized = False
                        matcher = MatcherV3(db_conn=conn, verbose=verbose)
                        if verbose:
                            print(f"[EQUIV] Lookup recargado (último cambio: {_latest_str})")
                    elif verbose:
                        print(f"[EQUIV] Lookup vigente (sin cambios desde última carga)")
    except Exception as _e:
        if verbose:
            print(f"[EQUIV] WARN: No se pudo verificar staleness: {_e}")

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
                'sector_empresa': oferta['sector_empresa'] or '',
                # M-08: Fuentes declaradas para extract_declared_skills()
                'skills_tecnicas_list': oferta['skills_tecnicas_list'] or '',
                'tecnologias_list': oferta['tecnologias_list'] or '',
                'herramientas_list': oferta['herramientas_list'] or '',
                'soft_skills_list': oferta['soft_skills_list'] or '',
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
