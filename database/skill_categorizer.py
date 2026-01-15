#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Categorizer v2.0 - Clasificación basada en datos ESCO oficiales
=====================================================================

VERSION: 2.0.0
FECHA: 2026-01-14

CAMBIO PRINCIPAL vs v1:
- Elimina 100+ mapeos hardcodeados (ESCO_GROUP_TO_L1)
- Usa datos extraídos directamente del RDF ESCO v1.2.0
- L1/L2 vienen pre-calculados en esco_skills_full.json
- Lookup directo por URI (O(1)) en lugar de caminar jerarquía

ARCHIVOS REQUERIDOS (generados por extract_esco_complete.py):
- database/embeddings/esco_skills_full.json (14,257 skills con L1/L2)
- database/embeddings/esco_skill_hierarchy.json (889 categorías)

COBERTURA:
- 97.7% de skills tienen L1/L2 desde el RDF
- 2.3% (327 skills) son top-level sin broader → fallback a heurísticas

Categorías L1 (códigos oficiales ESCO):
- S1-S8: Skills específicas por área
- K: Knowledge (conocimientos)
- T1-T6: Transversales
- A: Attitudes (actitudes)
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, List

# Nombres display para categorías L1 (para dashboards)
L1_DISPLAY_NAMES = {
    "S1": "Comunicación y colaboración",
    "S2": "Gestión de información",
    "S3": "Asistencia y cuidado",
    "S4": "Gestión y administración",
    "S5": "Trabajar con ordenadores",
    "S6": "Manejo de equipos y maquinaria",
    "S7": "Construcción y mantenimiento",
    "S8": "Trabajar con seres vivos",
    "K": "Conocimientos",
    "T1": "Idiomas",
    "T2": "Pensamiento",
    "T3": "Autogestión",
    "T4": "Trabajo con otros",
    "T5": "Actitudes y valores",
    "T6": "Aplicación de conocimientos",
    "A": "Actitudes",
}

# Skills digitales por código L1 (para flag es_digital)
DIGITAL_L1_CODES = {"S5"}  # Trabajar con ordenadores es digital


class SkillCategorizer:
    """
    Categorizador v2.0 basado en datos ESCO oficiales.

    Lookup directo por URI → L1/L2 (sin hardcoding).
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        skills_path: str = None,
        hierarchy_path: str = None,
        fallback_config_path: str = None,
        verbose: bool = False
    ):
        """
        Inicializa el categorizador.

        Args:
            skills_path: Path a esco_skills_full.json
            hierarchy_path: Path a esco_skill_hierarchy.json
            fallback_config_path: Path a config para heurísticas (2.3% sin L1)
            verbose: Mostrar mensajes de debug
        """
        base_path = Path(__file__).parent
        embeddings_path = base_path / "embeddings"
        config_path = base_path.parent / "config"

        self.skills_path = Path(skills_path) if skills_path else embeddings_path / "esco_skills_full.json"
        self.hierarchy_path = Path(hierarchy_path) if hierarchy_path else embeddings_path / "esco_skill_hierarchy.json"
        self.fallback_config_path = Path(fallback_config_path) if fallback_config_path else config_path / "skill_categories.json"

        self.verbose = verbose

        # Datos cargados
        self.skills_by_uri = {}
        self.skills_by_label = {}
        self.hierarchy = {}
        self.fallback_patterns = {}

        self._load_data()

    def _load_data(self):
        """Carga datos ESCO extraídos del RDF."""
        # 1. Cargar skills con L1/L2
        if self.skills_path.exists():
            with open(self.skills_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            skills = data.get('skills', {})

            # Indexar por URI y por label (para búsqueda flexible)
            for uri, skill_data in skills.items():
                self.skills_by_uri[uri] = skill_data
                label = skill_data.get('label', '').lower().strip()
                if label:
                    self.skills_by_label[label] = skill_data

            if self.verbose:
                print(f"[CategorizerV2] Skills cargados: {len(self.skills_by_uri):,}")
        else:
            print(f"[CategorizerV2] WARN: No existe {self.skills_path}")

        # 2. Cargar jerarquía (para nombres de categorías)
        if self.hierarchy_path.exists():
            with open(self.hierarchy_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.hierarchy = data.get('categories', {})

            if self.verbose:
                print(f"[CategorizerV2] Categorías cargadas: {len(self.hierarchy):,}")

        # 3. Cargar config de fallback (para el 2.3% sin L1)
        if self.fallback_config_path.exists():
            try:
                with open(self.fallback_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self._compile_fallback_patterns(config.get('heuristicas', {}))
            except Exception as e:
                if self.verbose:
                    print(f"[CategorizerV2] WARN: Error cargando fallback config: {e}")

    def _compile_fallback_patterns(self, heuristicas: Dict):
        """Pre-compila regex patterns para fallback."""
        for categoria, data in heuristicas.items():
            keywords = data.get('keywords', [])
            if keywords:
                pattern = '|'.join(re.escape(kw) for kw in keywords)
                self.fallback_patterns[categoria] = {
                    'pattern': re.compile(pattern, re.IGNORECASE),
                    'L1': data.get('L1'),
                    'es_digital': data.get('es_digital', False)
                }

    def categorize(self, skill_uri: str, skill_label: str = None) -> Dict:
        """
        Categoriza una skill ESCO.

        Estrategia:
        1. Lookup por URI en skills_by_uri (97.7% de casos)
        2. Si no hay URI, lookup por label normalizado
        3. Fallback a heurísticas por keywords (2.3% restante)

        Args:
            skill_uri: URI ESCO de la skill
            skill_label: Label en español (opcional, para fallback)

        Returns:
            Dict con L1, L1_nombre, L2, L2_nombre, es_digital, metodo
        """
        # 1. Lookup directo por URI
        if skill_uri and skill_uri in self.skills_by_uri:
            skill_data = self.skills_by_uri[skill_uri]
            L1 = skill_data.get('L1')
            L2 = skill_data.get('L2')

            if L1:
                return self._build_result(
                    L1=L1,
                    L2=L2,
                    es_digital=self._is_digital(L1),
                    metodo="esco_rdf"
                )

        # 2. Lookup por label normalizado
        if skill_label:
            label_norm = skill_label.lower().strip()
            if label_norm in self.skills_by_label:
                skill_data = self.skills_by_label[label_norm]
                L1 = skill_data.get('L1')
                L2 = skill_data.get('L2')

                if L1:
                    return self._build_result(
                        L1=L1,
                        L2=L2,
                        es_digital=self._is_digital(L1),
                        metodo="esco_label"
                    )

        # 3. Fallback a heurísticas (2.3% sin L1)
        if skill_label:
            for categoria, data in self.fallback_patterns.items():
                if data['pattern'].search(skill_label):
                    return self._build_result(
                        L1=data['L1'],
                        L2=None,
                        es_digital=data['es_digital'],
                        metodo="heuristica"
                    )

        # 4. Default: Transversal
        return self._build_result(
            L1="T",
            L2=None,
            es_digital=False,
            metodo="default"
        )

    def _is_digital(self, L1: str) -> bool:
        """Determina si una categoría L1 es digital."""
        if not L1:
            return False
        # S5 es "Trabajar con ordenadores" = digital
        return L1 in DIGITAL_L1_CODES or L1.startswith("S5")

    def _build_result(self, L1: str, L2: str, es_digital: bool, metodo: str) -> Dict:
        """Construye resultado con nombres de categoría."""
        L1_nombre = L1_DISPLAY_NAMES.get(L1, self._get_category_name(L1))
        L2_nombre = self._get_category_name(L2) if L2 else None

        return {
            "L1": L1,
            "L1_nombre": L1_nombre,
            "L2": L2,
            "L2_nombre": L2_nombre,
            "es_digital": es_digital,
            "metodo": metodo
        }

    def _get_category_name(self, code: str) -> Optional[str]:
        """Obtiene nombre de categoría desde la jerarquía."""
        if not code:
            return None

        # Buscar en jerarquía por código
        for uri, cat_data in self.hierarchy.items():
            if cat_data.get('code') == code:
                return cat_data.get('label', code)

        return L1_DISPLAY_NAMES.get(code, code)

    def categorize_batch(self, skills: List[Dict]) -> List[Dict]:
        """
        Categoriza un lote de skills.

        Args:
            skills: Lista de dicts con 'skill_uri' y/o 'skill_esco'

        Returns:
            Lista de skills con categorías agregadas
        """
        for skill in skills:
            categoria = self.categorize(
                skill_uri=skill.get('skill_uri', ''),
                skill_label=skill.get('skill_esco', skill.get('label', ''))
            )
            skill.update(categoria)

        return skills

    def get_summary(self, skills: List[Dict]) -> Dict:
        """Genera resumen de categorías para un conjunto de skills."""
        summary = {
            "por_L1": {},
            "por_L2": {},
            "digitales_count": 0,
            "por_metodo": {},
            "total": len(skills)
        }

        for skill in skills:
            L1 = skill.get("L1", "T")
            L2 = skill.get("L2")
            es_digital = skill.get("es_digital", False)
            metodo = skill.get("metodo", "unknown")

            summary["por_L1"][L1] = summary["por_L1"].get(L1, 0) + 1

            if L2:
                summary["por_L2"][L2] = summary["por_L2"].get(L2, 0) + 1

            if es_digital:
                summary["digitales_count"] += 1

            summary["por_metodo"][metodo] = summary["por_metodo"].get(metodo, 0) + 1

        return summary

    def get_stats(self) -> Dict:
        """Retorna estadísticas del categorizador."""
        return {
            "version": self.VERSION,
            "skills_loaded": len(self.skills_by_uri),
            "categories_loaded": len(self.hierarchy),
            "fallback_patterns": len(self.fallback_patterns)
        }


# Singleton para evitar recargar datos múltiples veces
_categorizer_instance = None

def get_categorizer() -> SkillCategorizer:
    """Obtiene instancia singleton del categorizador v2."""
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = SkillCategorizer()
    return _categorizer_instance


def clear_categorizer_cache():
    """Limpia el cache del singleton."""
    global _categorizer_instance
    _categorizer_instance = None


if __name__ == "__main__":
    # Test básico
    print("=" * 70)
    print("TEST: Skill Categorizer v2.0 (sin hardcoding)")
    print("=" * 70)

    categorizer = SkillCategorizer(verbose=True)
    stats = categorizer.get_stats()
    print(f"\nEstadísticas: {stats}")

    # Test con skills reales
    test_cases = [
        # URI conocido
        ("http://data.europa.eu/esco/skill/f82b05a7-128b-4a72-a815-044ff6062f62", None),
        # Label conocido
        (None, "gestionar inventario"),
        (None, "utilizar lenguajes de programación"),
        (None, "trabajo en equipo"),
        (None, "instalación eléctrica"),
        (None, "atención al cliente"),
        # Fallback
        (None, "skill_desconocida_xyz"),
    ]

    print("\n" + "-" * 70)
    print("Resultados de categorización:")
    print("-" * 70)

    for uri, label in test_cases:
        result = categorizer.categorize(uri, label)
        display = label or uri[:50] + "..."
        print(f"\n'{display}'")
        print(f"  L1: {result['L1']} - {result['L1_nombre']}")
        print(f"  L2: {result['L2']} - {result['L2_nombre']}")
        print(f"  Digital: {result['es_digital']}")
        print(f"  Método: {result['metodo']}")
