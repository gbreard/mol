#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
esco_skills_extractor.py
========================
Extrae conocimientos y competencias ESCO para una ocupación dada.

Estructura ESCO:
- Skills: Competencias/habilidades (hacer algo)
- Knowledge: Conocimientos (saber algo)
- Attitudes: Actitudes (ser de cierta manera) - poco usados

Relaciones:
- Essential: Requeridos para la ocupación
- Optional: Deseables pero no obligatorios

Uso:
    from esco_skills_extractor import ESCOSkillsExtractor

    extractor = ESCOSkillsExtractor()
    result = extractor.get_skills_for_occupation(
        'http://data.europa.eu/esco/occupation/abc123'
    )
    print(result)
    # {
    #     'essential_skills': [...],
    #     'optional_skills': [...],
    #     'essential_knowledge': [...],
    #     'optional_knowledge': [...]
    # }

CLI:
    python esco_skills_extractor.py <esco_uri>
    python esco_skills_extractor.py --label "vendedor"
"""

import sqlite3
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Patrones para detectar si un skill es realmente "knowledge" basado en el label
# ESCO no siempre marca correctamente el tipo, así que usamos heurísticas
KNOWLEDGE_PATTERNS = [
    # Idiomas
    r'^(inglés|español|francés|alemán|portugués|italiano|chino|japonés|árabe|ruso)',
    r'^idioma',
    # Conocimientos técnicos/teóricos
    r'^(matemáticas|física|química|biología|estadística|economía)',
    r'^(derecho|legislación|normativa|reglamento)',
    r'^(contabilidad|finanzas|presupuesto)',
    r'^(informática|programación|software|hardware)',
    r'^(medicina|farmacología|anatomía|fisiología)',
    r'^(psicología|sociología|antropología)',
    r'^(historia|geografía|filosofía)',
    r'^(ingeniería|arquitectura|diseño)',
    # Patrones de conocimiento
    r'^conocimiento(s)? de',
    r'^principios de',
    r'^teoría de',
    r'^fundamentos de',
    r'^metodología(s)? de',
    r'^técnica(s)? de',  # A veces son knowledge
    r'^norma(s)? ',
    r'^ley(es)? ',
    r'^regulación',
    r'^estándar(es)?',
]

# Patrones para confirmar que es un SKILL (acción)
SKILL_PATTERNS = [
    r'^(gestionar|administrar|coordinar|supervisar|dirigir)',
    r'^(comunicar|negociar|persuadir|presentar)',
    r'^(analizar|evaluar|investigar|diagnosticar)',
    r'^(crear|diseñar|desarrollar|implementar)',
    r'^(operar|utilizar|manejar|manipular)',
    r'^(enseñar|capacitar|formar|entrenar)',
    r'^(vender|comercializar|promocionar)',
    r'^(atender|asistir|ayudar|apoyar)',
    r'^(resolver|solucionar|reparar|mantener)',
    r'^(planificar|organizar|programar)',
    r'^(trabajar|colaborar|cooperar)',
    r'^(aplicar|ejecutar|realizar|efectuar)',
]


@dataclass
class SkillInfo:
    """Información de un skill/knowledge"""
    uri: str
    label_es: str
    description_es: Optional[str]
    skill_type: str  # 'skill' o 'knowledge'
    relation_type: str  # 'essential' o 'optional'
    reusability_level: Optional[str]
    inferred_type: bool = False  # True si el tipo fue inferido por heurísticas


class ESCOSkillsExtractor:
    """Extractor de skills y knowledge ESCO"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self._knowledge_patterns = [re.compile(p, re.IGNORECASE) for p in KNOWLEDGE_PATTERNS]
        self._skill_patterns = [re.compile(p, re.IGNORECASE) for p in SKILL_PATTERNS]

    def connect(self):
        """Conecta a la base de datos"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

    def close(self):
        """Cierra la conexión"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _infer_skill_type(self, label: str) -> Tuple[str, bool]:
        """
        Infiere si un skill es 'skill' o 'knowledge' basado en el label.

        Returns:
            Tuple[str, bool]: (tipo, fue_inferido)
        """
        label_lower = label.lower().strip()

        # Primero verificar si parece knowledge
        for pattern in self._knowledge_patterns:
            if pattern.search(label_lower):
                return 'knowledge', True

        # Luego verificar si parece skill (acción)
        for pattern in self._skill_patterns:
            if pattern.search(label_lower):
                return 'skill', True

        # Por defecto, asumir skill
        return 'skill', True

    def get_occupation_by_uri(self, occupation_uri: str) -> Optional[dict]:
        """Obtiene información de una ocupación por URI"""
        self.connect()
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT occupation_uri, preferred_label_es, description_es, isco_code
            FROM esco_occupations
            WHERE occupation_uri = ?
        """, (occupation_uri,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_occupation_by_label(self, label: str) -> Optional[dict]:
        """Busca ocupación por label (parcial)"""
        self.connect()
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT occupation_uri, preferred_label_es, description_es, isco_code
            FROM esco_occupations
            WHERE preferred_label_es LIKE ?
            LIMIT 1
        """, (f'%{label}%',))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_skills_for_occupation(self, occupation_uri: str) -> Dict[str, List[dict]]:
        """
        Obtiene todos los skills y knowledge asociados a una ocupación.

        Args:
            occupation_uri: URI de la ocupación ESCO

        Returns:
            Dict con keys:
            - essential_skills: Lista de skills esenciales
            - optional_skills: Lista de skills opcionales
            - essential_knowledge: Lista de conocimientos esenciales
            - optional_knowledge: Lista de conocimientos opcionales
            - occupation_info: Info de la ocupación
        """
        self.connect()
        cursor = self.conn.cursor()

        # Obtener info de la ocupación
        occupation_info = self.get_occupation_by_uri(occupation_uri)
        if not occupation_info:
            return {
                'error': f'Ocupación no encontrada: {occupation_uri}',
                'essential_skills': [],
                'optional_skills': [],
                'essential_knowledge': [],
                'optional_knowledge': []
            }

        # Obtener skills asociados
        cursor.execute("""
            SELECT
                s.skill_uri,
                s.preferred_label_es,
                s.description_es,
                s.skill_type,
                s.skill_reusability_level,
                a.relation_type
            FROM esco_associations a
            JOIN esco_skills s ON a.skill_uri = s.skill_uri
            WHERE a.occupation_uri = ?
            ORDER BY a.relation_type, s.preferred_label_es
        """, (occupation_uri,))

        rows = cursor.fetchall()

        # Clasificar skills
        result = {
            'occupation_info': occupation_info,
            'essential_skills': [],
            'optional_skills': [],
            'essential_knowledge': [],
            'optional_knowledge': [],
            'stats': {
                'total_essential': 0,
                'total_optional': 0,
                'inferred_types': 0
            }
        }

        for row in rows:
            label = row['preferred_label_es'] or ''
            db_skill_type = row['skill_type']
            relation_type = row['relation_type']

            # Determinar tipo de skill
            if db_skill_type and db_skill_type in ('skill', 'knowledge', 'attitude'):
                skill_type = db_skill_type
                inferred = False
            else:
                skill_type, inferred = self._infer_skill_type(label)
                if inferred:
                    result['stats']['inferred_types'] += 1

            skill_info = {
                'uri': row['skill_uri'],
                'label': label,
                'description': row['description_es'],
                'type': skill_type,
                'relation': relation_type,
                'reusability_level': row['skill_reusability_level'],
                'type_inferred': inferred
            }

            # Clasificar en la categoría correcta
            if relation_type == 'essential':
                result['stats']['total_essential'] += 1
                if skill_type == 'knowledge':
                    result['essential_knowledge'].append(skill_info)
                else:
                    result['essential_skills'].append(skill_info)
            else:
                result['stats']['total_optional'] += 1
                if skill_type == 'knowledge':
                    result['optional_knowledge'].append(skill_info)
                else:
                    result['optional_skills'].append(skill_info)

        return result

    def get_skills_summary(self, occupation_uri: str) -> Dict[str, List[str]]:
        """
        Versión simplificada que retorna solo los labels.

        Returns:
            Dict con listas de strings (solo labels)
        """
        full_result = self.get_skills_for_occupation(occupation_uri)

        return {
            'occupation': full_result.get('occupation_info', {}).get('preferred_label_es', ''),
            'essential_skills': [s['label'] for s in full_result['essential_skills']],
            'optional_skills': [s['label'] for s in full_result['optional_skills']],
            'essential_knowledge': [s['label'] for s in full_result['essential_knowledge']],
            'optional_knowledge': [s['label'] for s in full_result['optional_knowledge']],
        }

    def search_occupations(self, query: str, limit: int = 10) -> List[dict]:
        """Busca ocupaciones por término"""
        self.connect()
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT occupation_uri, preferred_label_es, isco_code
            FROM esco_occupations
            WHERE preferred_label_es LIKE ?
            ORDER BY preferred_label_es
            LIMIT ?
        """, (f'%{query}%', limit))

        return [dict(row) for row in cursor.fetchall()]


def main():
    """CLI principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extrae skills y knowledge ESCO para una ocupación'
    )
    parser.add_argument('uri', nargs='?', help='URI de la ocupación ESCO')
    parser.add_argument('--label', '-l', help='Buscar por label (parcial)')
    parser.add_argument('--search', '-s', help='Buscar ocupaciones')
    parser.add_argument('--summary', action='store_true', help='Mostrar solo labels')
    parser.add_argument('--json', action='store_true', help='Output en JSON')

    args = parser.parse_args()

    extractor = ESCOSkillsExtractor()

    try:
        # Modo búsqueda
        if args.search:
            results = extractor.search_occupations(args.search)
            print(f"\n=== Ocupaciones que contienen '{args.search}' ===\n")
            for occ in results:
                print(f"  [{occ['isco_code']}] {occ['preferred_label_es']}")
                print(f"       URI: {occ['occupation_uri']}")
            return

        # Obtener URI
        occupation_uri = args.uri
        if args.label:
            occ = extractor.get_occupation_by_label(args.label)
            if occ:
                occupation_uri = occ['occupation_uri']
                print(f"Encontrada: {occ['preferred_label_es']}")
            else:
                print(f"No se encontró ocupación con label: {args.label}")
                return

        if not occupation_uri:
            parser.print_help()
            return

        # Extraer skills
        if args.summary:
            result = extractor.get_skills_summary(occupation_uri)
        else:
            result = extractor.get_skills_for_occupation(occupation_uri)

        # Output
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            occ_info = result.get('occupation_info') or result
            print(f"\n{'='*70}")
            print(f"OCUPACIÓN: {occ_info.get('preferred_label_es', occ_info.get('occupation', 'N/A'))}")
            print(f"{'='*70}")

            if 'stats' in result:
                stats = result['stats']
                print(f"\nEstadísticas:")
                print(f"  - Essential: {stats['total_essential']}")
                print(f"  - Optional: {stats['total_optional']}")
                print(f"  - Tipos inferidos: {stats['inferred_types']}")

            # Essential Skills
            es = result.get('essential_skills', [])
            print(f"\n--- ESSENTIAL SKILLS ({len(es)}) ---")
            for s in es[:15]:
                label = s if isinstance(s, str) else s.get('label', '')
                print(f"  • {label}")
            if len(es) > 15:
                print(f"  ... y {len(es) - 15} más")

            # Essential Knowledge
            ek = result.get('essential_knowledge', [])
            print(f"\n--- ESSENTIAL KNOWLEDGE ({len(ek)}) ---")
            for s in ek[:15]:
                label = s if isinstance(s, str) else s.get('label', '')
                print(f"  • {label}")
            if len(ek) > 15:
                print(f"  ... y {len(ek) - 15} más")

            # Optional Skills
            os_ = result.get('optional_skills', [])
            print(f"\n--- OPTIONAL SKILLS ({len(os_)}) ---")
            for s in os_[:10]:
                label = s if isinstance(s, str) else s.get('label', '')
                print(f"  • {label}")
            if len(os_) > 10:
                print(f"  ... y {len(os_) - 10} más")

            # Optional Knowledge
            ok = result.get('optional_knowledge', [])
            print(f"\n--- OPTIONAL KNOWLEDGE ({len(ok)}) ---")
            for s in ok[:10]:
                label = s if isinstance(s, str) else s.get('label', '')
                print(f"  • {label}")
            if len(ok) > 10:
                print(f"  ... y {len(ok) - 10} más")

            print()

    finally:
        extractor.close()


if __name__ == '__main__':
    main()
