"""
Skills Rules Matcher v1.0

Evalua reglas de skills (similar a evaluate_business_rules en match_ofertas_v3.py)
Patron: Reglas tienen PRIORIDAD sobre semantico (igual que ISCO matching)

Flujo:
1. Cargar reglas de config/skills_rules.json
2. Evaluar condiciones contra oferta
3. Si matchea regla -> retornar skills forzadas
4. Si no matchea -> retornar None (usar semantico)

Autor: Claude Code
Fecha: 2026-01-21
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SkillsRuleResult:
    """Resultado de evaluar reglas de skills"""
    skills_forzadas: List[Dict[str, str]]  # Lista de {skill_esco, skill_uri}
    regla_aplicada: str                     # ID de la regla (ej: RS01_desarrollador_python)
    nombre_regla: str                       # Nombre descriptivo
    razon: str                              # Por que matcheo


class SkillsRulesMatcher:
    """
    Evaluador de reglas de skills.

    Similar al evaluador de reglas de negocio en match_ofertas_v3.py,
    pero para skills en lugar de ISCO.

    Uso:
        matcher = SkillsRulesMatcher()
        result = matcher.evaluate(titulo, oferta_nlp)
        if result:
            # Usar skills de la regla
            skills = result.skills_forzadas
        else:
            # Usar extraccion semantica
            skills = extract_skills_semantico(...)
    """

    def __init__(self, config_path: str = None, verbose: bool = False):
        """
        Inicializa el matcher cargando las reglas.

        Args:
            config_path: Ruta al archivo de reglas (default: config/skills_rules.json)
            verbose: Si True, imprime info de debug
        """
        if config_path is None:
            # Calcular ruta relativa a este archivo
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "skills_rules.json")

        self.config_path = config_path
        self.verbose = verbose
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Carga las reglas desde el archivo JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get("reglas_forzar_skills", {})
        except FileNotFoundError:
            if self.verbose:
                print(f"[SkillsRulesMatcher] WARN: No se encontro {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"[SkillsRulesMatcher] ERROR: JSON invalido en {self.config_path}: {e}")
            return {}

    def reload_rules(self):
        """Recarga las reglas desde el archivo (util para testing)"""
        self.rules = self._load_rules()

    def evaluate(
        self,
        titulo: str,
        oferta_nlp: Dict[str, Any] = None,
        tareas: str = ""
    ) -> Optional[SkillsRuleResult]:
        """
        Evalua todas las reglas de skills contra una oferta.

        Args:
            titulo: Titulo de la oferta (ej: "Desarrollador Python Senior")
            oferta_nlp: Dict con campos NLP (area_funcional, sector_empresa, etc.)
            tareas: Tareas explicitas de la oferta (separadas por ;)

        Returns:
            SkillsRuleResult si alguna regla matchea, None si no
        """
        if oferta_nlp is None:
            oferta_nlp = {}

        titulo_lower = titulo.lower() if titulo else ""
        tareas_lower = tareas.lower() if tareas else ""

        for rule_id, rule in self.rules.items():
            if not isinstance(rule, dict):
                continue

            # Solo evaluar reglas activas
            if not rule.get("activa", False):
                continue

            # Obtener condicion y accion
            condicion = rule.get("condicion", {})
            accion = rule.get("accion", {})

            # Solo procesar si hay skills a forzar
            skills_forzadas = accion.get("forzar_skills", [])
            if not skills_forzadas:
                continue

            # Evaluar condiciones (AND entre todas)
            if self._check_conditions(condicion, titulo_lower, tareas_lower, oferta_nlp):
                if self.verbose:
                    print(f"[SkillsRulesMatcher] Regla {rule_id} matchea: {rule.get('nombre', '')}")

                return SkillsRuleResult(
                    skills_forzadas=skills_forzadas,
                    regla_aplicada=rule_id,
                    nombre_regla=rule.get("nombre", rule_id),
                    razon=self._build_razon(condicion, titulo_lower, oferta_nlp)
                )

        return None

    def _check_conditions(
        self,
        condicion: Dict,
        titulo_lower: str,
        tareas_lower: str,
        oferta_nlp: Dict
    ) -> bool:
        """
        Evalua si todas las condiciones se cumplen (AND).

        Condiciones soportadas:
        - titulo_contiene_alguno: OR entre terminos
        - titulo_contiene_todos: AND entre terminos
        - titulo_o_tareas_contiene_alguno: OR entre terminos en titulo o tareas
        - area_funcional_es: match exacto
        - area_funcional_es_alguno: OR entre areas
        - sector_empresa_es: match exacto
        - titulo_no_contiene_alguno: exclusion OR
        """
        condiciones_evaluadas = []

        # titulo_contiene_alguno (OR)
        terminos = condicion.get("titulo_contiene_alguno", [])
        if terminos:
            condiciones_evaluadas.append(
                any(t.lower() in titulo_lower for t in terminos)
            )

        # titulo_contiene_todos (AND)
        terminos_todos = condicion.get("titulo_contiene_todos", [])
        if terminos_todos:
            condiciones_evaluadas.append(
                all(t.lower() in titulo_lower for t in terminos_todos)
            )

        # titulo_o_tareas_contiene_alguno (OR en titulo o tareas)
        terminos_ot = condicion.get("titulo_o_tareas_contiene_alguno", [])
        if terminos_ot:
            texto_completo = f"{titulo_lower} {tareas_lower}"
            condiciones_evaluadas.append(
                any(t.lower() in texto_completo for t in terminos_ot)
            )

        # Si no hay condiciones de texto, no matchea
        if not condiciones_evaluadas:
            return False

        # Todas las condiciones de texto deben cumplirse (AND)
        if not all(condiciones_evaluadas):
            return False

        # Verificar area_funcional_es (filtro adicional)
        area_requerida = condicion.get("area_funcional_es")
        if area_requerida:
            area_actual = oferta_nlp.get("area_funcional", "").lower()
            if area_actual != area_requerida.lower():
                return False

        # Verificar area_funcional_es_alguno (OR entre areas)
        areas_validas = condicion.get("area_funcional_es_alguno", [])
        if areas_validas:
            area_actual = oferta_nlp.get("area_funcional", "").lower()
            if not any(a.lower() == area_actual for a in areas_validas):
                return False

        # Verificar sector_empresa_es
        sector_requerido = condicion.get("sector_empresa_es")
        if sector_requerido:
            sector_actual = oferta_nlp.get("sector_empresa", "").lower()
            if sector_actual != sector_requerido.lower():
                return False

        # Verificar EXCLUSIONES
        excluir_titulo = condicion.get("titulo_no_contiene_alguno", [])
        if excluir_titulo and any(t.lower() in titulo_lower for t in excluir_titulo):
            return False

        return True

    def _build_razon(self, condicion: Dict, titulo_lower: str, oferta_nlp: Dict) -> str:
        """Construye una explicacion de por que la regla matcheo"""
        razones = []

        terminos = condicion.get("titulo_contiene_alguno", [])
        if terminos:
            matched = [t for t in terminos if t.lower() in titulo_lower]
            if matched:
                razones.append(f"titulo contiene '{matched[0]}'")

        area_req = condicion.get("area_funcional_es")
        if area_req:
            razones.append(f"area={area_req}")

        return "; ".join(razones) if razones else "condicion cumplida"

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadisticas de las reglas cargadas"""
        total = len(self.rules)
        activas = sum(1 for r in self.rules.values() if isinstance(r, dict) and r.get("activa", False))

        return {
            "total_reglas": total,
            "reglas_activas": activas,
            "reglas_inactivas": total - activas,
            "config_path": self.config_path
        }

    def list_rules(self) -> List[Dict[str, Any]]:
        """Lista todas las reglas con su info basica"""
        result = []
        for rule_id, rule in self.rules.items():
            if not isinstance(rule, dict):
                continue
            result.append({
                "id": rule_id,
                "nombre": rule.get("nombre", rule_id),
                "activa": rule.get("activa", False),
                "skills_count": len(rule.get("accion", {}).get("forzar_skills", []))
            })
        return result


# Funcion helper para uso rapido
def evaluate_skills_rules(
    titulo: str,
    oferta_nlp: Dict = None,
    tareas: str = "",
    verbose: bool = False
) -> Optional[SkillsRuleResult]:
    """
    Funcion helper para evaluar reglas de skills.

    Uso:
        result = evaluate_skills_rules("Desarrollador Python", oferta_nlp)
        if result:
            print(f"Regla {result.regla_aplicada} aplicada")
            for skill in result.skills_forzadas:
                print(f"  - {skill['skill_esco']}")
    """
    matcher = SkillsRulesMatcher(verbose=verbose)
    return matcher.evaluate(titulo, oferta_nlp, tareas)


if __name__ == "__main__":
    # Test basico
    print("=== Test SkillsRulesMatcher ===\n")

    matcher = SkillsRulesMatcher(verbose=True)
    stats = matcher.get_stats()
    print(f"Reglas cargadas: {stats['reglas_activas']} activas de {stats['total_reglas']} total\n")

    # Test cases
    test_cases = [
        ("Desarrollador Python Senior", {}),
        ("Contador Junior", {}),
        ("Vigilador Nocturno", {}),
        ("Chofer de Camion", {}),
        ("Administrativa Contable", {}),
        ("Vendedor de Retail", {}),
        ("Recepcionista Hotel", {}),
        ("Mucama Hotel", {}),
        ("Data Scientist", {}),  # No deberia matchear
    ]

    print("=== Evaluando casos de prueba ===\n")
    for titulo, nlp in test_cases:
        result = matcher.evaluate(titulo, nlp)
        if result:
            print(f"[MATCH] {titulo}")
            print(f"        Regla: {result.regla_aplicada}")
            print(f"        Skills: {[s['skill_esco'] for s in result.skills_forzadas]}")
        else:
            print(f"[NO MATCH] {titulo} -> usar semantico")
        print()
