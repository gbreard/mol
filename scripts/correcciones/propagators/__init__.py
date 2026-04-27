"""Propagators de correcciones humanas — SPEC T Fase 1."""
from .base import (
    PatronInvalido,
    PropagationResult,
    PropagatorBase,
    validar_patron,
    VALID_TIPOS,
)
from .matching_esco import MatchingESCOPropagator
from .nlp_area import NLPAreaPropagator
from .nlp_tareas import NLPTareasPropagator
from .skills_filtro import SkillsFiltroPropagator

# Registry: tipo → clase
PROPAGATORS = {
    NLPAreaPropagator.TIPO: NLPAreaPropagator,
    MatchingESCOPropagator.TIPO: MatchingESCOPropagator,
    SkillsFiltroPropagator.TIPO: SkillsFiltroPropagator,
    NLPTareasPropagator.TIPO: NLPTareasPropagator,
}


def get_propagator(tipo: str, **kwargs) -> PropagatorBase:
    """Factory: devuelve la instancia correcta según el tipo del patrón."""
    cls = PROPAGATORS.get(tipo)
    if not cls:
        raise PatronInvalido(
            f"tipo='{tipo}' no tiene propagator registrado. "
            f"Disponibles: {sorted(PROPAGATORS.keys())}"
        )
    return cls(**kwargs)


__all__ = [
    "PROPAGATORS",
    "PatronInvalido",
    "PropagationResult",
    "PropagatorBase",
    "MatchingESCOPropagator",
    "NLPAreaPropagator",
    "NLPTareasPropagator",
    "SkillsFiltroPropagator",
    "VALID_TIPOS",
    "get_propagator",
    "validar_patron",
]
