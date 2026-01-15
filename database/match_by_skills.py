#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Match By Skills v1.2 - Matchea ocupaciones ESCO usando skills extraídas
========================================================================

VERSION: 1.2.0
FECHA: 2026-01-13

CAMBIOS v1.2.0:
- Añade pesos para skills genéricas (comunicación, trabajo en equipo, etc.)
- Skills genéricas tienen peso 0.5x para no dominar sobre skills específicas
- Config en config/skills_weights.json

OBJETIVO:
Encontrar ocupaciones ESCO que mejor coinciden con las skills extraídas
de una oferta, usando la tabla esco_associations (134,805 registros).

FLUJO:
1. Recibe lista de skills extraídas (con URIs)
2. Busca en esco_associations qué ocupaciones tienen esas skills
3. Rankea ocupaciones por cantidad/peso de skills matcheadas
4. Retorna top N ocupaciones candidatas

Uso:
    from match_by_skills import SkillsBasedMatcher

    matcher = SkillsBasedMatcher(db_conn)
    candidates = matcher.match(extracted_skills)
    # [
    #     {"occupation_uri": "...", "esco_label": "...", "isco_code": "4313",
    #      "score": 5.2, "skills_matched": ["gestionar nóminas", ...]},
    #     ...
    # ]
"""

import sqlite3
import logging
import json
from collections import defaultdict
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default origin weights (can be overridden by config)
DEFAULT_ORIGIN_WEIGHTS = {
    "tarea": 1.2,   # Skills from tasks are more reliable
    "titulo": 0.9   # Skills from title can be misleading
}


class SkillsBasedMatcher:
    """
    Matchea ocupaciones ESCO usando skills extraídas.

    Usa la tabla esco_associations para encontrar ocupaciones
    que tienen las skills como essential u optional.

    v1.1.0: Añade pesos por origen (tarea vs titulo) - tareas valen 1.2x
    v1.2.0: Añade pesos para skills genéricas (comunicación, etc.) - valen 0.5x
    """

    VERSION = "1.2.0"

    # Cache a nivel de clase
    _associations_loaded = False
    _skill_to_occupations = None
    _occupation_metadata = None

    def __init__(
        self,
        db_conn: sqlite3.Connection = None,
        db_path: str = None,
        essential_weight: float = 2.0,
        optional_weight: float = 1.0,
        top_n: int = 10,
        verbose: bool = False,
        config_path: str = None
    ):
        """
        Inicializa el matcher.

        Args:
            db_conn: Conexión SQLite existente
            db_path: Path a BD (si no se proporciona conexión)
            essential_weight: Peso para skills marcadas como essential
            optional_weight: Peso para skills opcionales
            top_n: Número de candidatos a retornar
            verbose: Mostrar mensajes de debug
            config_path: Path a matching_config.json (para origin weights)
        """
        if db_conn:
            self.conn = db_conn
            self._owns_connection = False
        else:
            db_path = db_path or str(Path(__file__).parent / "bumeran_scraping.db")
            self.conn = sqlite3.connect(db_path)
            self._owns_connection = True

        self.essential_weight = essential_weight
        self.optional_weight = optional_weight
        self.top_n = top_n
        self.verbose = verbose

        # Load origin weights from config
        self.origin_weights = self._load_origin_weights(config_path)

        # v1.2: Load generic skills weights
        self.generic_skills = self._load_generic_skills()

        self._load_associations()

    def _load_origin_weights(self, config_path: str = None) -> Dict[str, float]:
        """Load skill origin weights from config."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "matching_config.json"
        else:
            config_path = Path(config_path)

        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                weights = config.get("skill_origin_weights", {})
                if weights:
                    result = {
                        "tarea": weights.get("tarea", DEFAULT_ORIGIN_WEIGHTS["tarea"]),
                        "titulo": weights.get("titulo", DEFAULT_ORIGIN_WEIGHTS["titulo"])
                    }
                    if self.verbose:
                        logger.info(f"[MATCHER] Origin weights: tarea={result['tarea']}, titulo={result['titulo']}")
                    return result
        except Exception as e:
            logger.warning(f"[MATCHER] Could not load config: {e}")

        return DEFAULT_ORIGIN_WEIGHTS.copy()

    def _load_generic_skills(self) -> Dict:
        """Load generic skills config for reduced weighting. v1.2.0"""
        config_path = Path(__file__).parent.parent / "config" / "skills_weights.json"
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                generic_config = config.get("skills_genericas", {})
                skills_list = [s.lower() for s in generic_config.get("lista", [])]
                peso = generic_config.get("peso", 0.5)
                if self.verbose and skills_list:
                    logger.info(f"[MATCHER] Loaded {len(skills_list)} generic skills (weight={peso})")
                return {
                    "skills": set(skills_list),
                    "peso": peso
                }
        except Exception as e:
            logger.warning(f"[MATCHER] Could not load skills_weights.json: {e}")
        return {"skills": set(), "peso": 1.0}

    def _get_generic_weight(self, skill_label: str) -> float:
        """Returns weight for a skill: 0.5 if generic, 1.0 otherwise. v1.2.0"""
        if not skill_label:
            return 1.0
        skill_lower = skill_label.lower()
        # Check if any generic skill is contained in the label
        for generic in self.generic_skills.get("skills", set()):
            if generic in skill_lower or skill_lower in generic:
                return self.generic_skills.get("peso", 0.5)
        return 1.0

    def _load_associations(self):
        """Carga mapa skill_uri → [(occupation_uri, weight)]"""
        if SkillsBasedMatcher._associations_loaded:
            self.skill_to_occupations = SkillsBasedMatcher._skill_to_occupations
            self.occupation_metadata = SkillsBasedMatcher._occupation_metadata
            if self.verbose:
                print(f"[MATCHER] Usando cache: {len(self.skill_to_occupations)} skills mapeadas")
            return

        if self.verbose:
            print("[MATCHER] Cargando asociaciones skill -> occupation...")

        self.skill_to_occupations = defaultdict(list)
        self.occupation_metadata = {}

        # Cargar asociaciones
        cur = self.conn.execute('''
            SELECT skill_uri, occupation_uri, relation_type
            FROM esco_associations
        ''')

        count = 0
        for skill_uri, occ_uri, rel_type in cur:
            weight = self.essential_weight if rel_type == 'essential' else self.optional_weight
            self.skill_to_occupations[skill_uri].append((occ_uri, weight))
            count += 1

        if self.verbose:
            print(f"[MATCHER] Cargadas {count} asociaciones")

        # Cargar metadata de ocupaciones
        cur = self.conn.execute('''
            SELECT occupation_uri, preferred_label_es, isco_code
            FROM esco_occupations
        ''')

        for occ_uri, label, isco in cur:
            self.occupation_metadata[occ_uri] = {
                'label': label,
                'isco_code': isco
            }

        if self.verbose:
            print(f"[MATCHER] Cargadas {len(self.occupation_metadata)} ocupaciones")

        # Guardar en cache de clase
        SkillsBasedMatcher._skill_to_occupations = self.skill_to_occupations
        SkillsBasedMatcher._occupation_metadata = self.occupation_metadata
        SkillsBasedMatcher._associations_loaded = True

    def match(
        self,
        extracted_skills: List[Dict],
        top_n: int = None
    ) -> List[Dict]:
        """
        Encuentra ocupaciones que mejor matchean las skills extraídas.

        Args:
            extracted_skills: Lista de skills con skill_uri y score
            top_n: Override del número de candidatos

        Returns:
            Lista ordenada de candidatos con:
            - occupation_uri, esco_label, isco_code
            - score (suma ponderada)
            - skills_matched (lista de skills que matchearon)
            - match_count (cantidad de skills)
        """
        if not extracted_skills:
            return []

        top_n = top_n or self.top_n

        occupation_scores = defaultdict(float)
        occupation_skills = defaultdict(list)

        for skill in extracted_skills:
            skill_uri = skill.get("skill_uri", "")
            skill_score = skill.get("score", 0.5)
            skill_label = skill.get("skill_esco", "")
            skill_origen = skill.get("origen", "titulo")  # v1.1: Get origin

            if not skill_uri:
                continue

            # v1.1: Apply origin weight (tarea=1.2, titulo=0.9)
            origin_weight = self.origin_weights.get(skill_origen, 1.0)

            # v1.2: Apply generic skill weight (comunicacion=0.5, etc.)
            generic_weight = self._get_generic_weight(skill_label)

            # Buscar ocupaciones que tienen esta skill
            for occ_uri, weight in self.skill_to_occupations.get(skill_uri, []):
                # Score = skill_score * weight * origin_weight * generic_weight
                occupation_scores[occ_uri] += skill_score * weight * origin_weight * generic_weight
                occupation_skills[occ_uri].append(skill_label)

        if not occupation_scores:
            if self.verbose:
                print("[MATCHER] No se encontraron ocupaciones con las skills dadas")
            return []

        # Ordenar por score
        ranked = sorted(
            occupation_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        # Construir resultado con metadata
        results = []
        for occ_uri, score in ranked:
            meta = self.occupation_metadata.get(occ_uri, {})
            results.append({
                "occupation_uri": occ_uri,
                "esco_label": meta.get('label', ''),
                "isco_code": meta.get('isco_code', ''),
                "score": round(score, 4),
                "skills_matched": occupation_skills[occ_uri],
                "match_count": len(occupation_skills[occ_uri])
            })

            if self.verbose:
                print(f"[MATCHER] {meta.get('label', '')[:40]} (ISCO {meta.get('isco_code', '')}) "
                      f"score={score:.2f}, skills={len(occupation_skills[occ_uri])}")

        return results

    def get_occupation_skills(self, occupation_uri: str) -> List[Dict]:
        """
        Obtiene todas las skills asociadas a una ocupación.

        Args:
            occupation_uri: URI de la ocupación ESCO

        Returns:
            Lista de skills con relation_type
        """
        cur = self.conn.execute('''
            SELECT s.skill_uri, s.preferred_label_es, a.relation_type
            FROM esco_associations a
            JOIN esco_skills s ON a.skill_uri = s.skill_uri
            WHERE a.occupation_uri = ?
        ''', (occupation_uri,))

        skills = []
        for uri, label, rel_type in cur:
            skills.append({
                'skill_uri': uri,
                'label': label,
                'relation_type': rel_type
            })

        return skills

    @classmethod
    def clear_cache(cls):
        """Limpia el cache de asociaciones."""
        cls._associations_loaded = False
        cls._skill_to_occupations = None
        cls._occupation_metadata = None

    def close(self):
        """Cierra la conexión si es propia."""
        if self._owns_connection and self.conn:
            self.conn.close()


def test_matcher():
    """Test rápido del matcher."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from skills_implicit_extractor import SkillsImplicitExtractor

    print("=" * 60)
    print("TEST: SkillsBasedMatcher")
    print("=" * 60)

    # Extraer skills de un caso problemático
    extractor = SkillsImplicitExtractor(verbose=False)

    print("\nCaso: Consultor Junior de Liquidación de Sueldos")
    skills = extractor.extract_skills(
        titulo_limpio="Consultor Junior de Liquidacion de Sueldos",
        tareas_explicitas="Calculo de aportes; Gestion de nominas"
    )

    print(f"Skills extraídas: {len(skills)}")
    for s in skills[:5]:
        print(f"  - {s['skill_esco']} (score={s['score']:.2f})")

    # Matchear ocupaciones
    matcher = SkillsBasedMatcher(verbose=True)
    candidates = matcher.match(skills, top_n=5)

    print(f"\nOcupaciones candidatas: {len(candidates)}")
    for i, c in enumerate(candidates, 1):
        print(f"\n{i}. {c['esco_label']}")
        print(f"   ISCO: {c['isco_code']}")
        print(f"   Score: {c['score']:.2f}")
        print(f"   Skills: {c['skills_matched'][:3]}...")

    matcher.close()


if __name__ == "__main__":
    test_matcher()
