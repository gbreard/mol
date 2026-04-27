"""
Clase base para propagadores de correcciones humanas.

SPEC T — Fase 1.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────
# Schema del patrón
# ─────────────────────────────────────────────────────────────────────

# Estructura JSON del patron_corregido:
# {
#   "tipo": "nlp_area_funcional" | "matching_esco" | "skills_filtro" | "nlp_tareas_explicitas",
#   "campo": "area_funcional" | "esco_label" | ...,
#   "condicion": {
#     "tipo": "titulo_contiene_alguno" | "regla_aplicada" | ...,
#     "keywords": [...] | "valor_unico": "X"
#   },
#   "valor_anterior": "...",
#   "valor_nuevo": "..."
# }

VALID_TIPOS = {
    "nlp_area_funcional",
    "matching_esco",
    "skills_filtro",
    "nlp_tareas_explicitas",
}


@dataclass
class PropagationResult:
    """Resultado de aplicar (o simular) una propagación."""

    tipo: str
    ofertas_identificadas: int = 0
    ofertas_actualizadas: int = 0
    ids_tocados: list = field(default_factory=list)
    ids_skipped: list = field(default_factory=list)
    regla_creada: Optional[str] = None
    config_modificada: Optional[str] = None
    errores: list = field(default_factory=list)
    dry_run: bool = True
    detalles: dict = field(default_factory=dict)

    def summary(self) -> str:
        prefijo = "[DRY-RUN] " if self.dry_run else ""
        return (
            f"{prefijo}Propagación '{self.tipo}': "
            f"{self.ofertas_actualizadas}/{self.ofertas_identificadas} ofertas tocadas"
        )

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "ofertas_identificadas": self.ofertas_identificadas,
            "ofertas_actualizadas": self.ofertas_actualizadas,
            "ids_tocados": self.ids_tocados,
            "ids_skipped": self.ids_skipped,
            "regla_creada": self.regla_creada,
            "config_modificada": self.config_modificada,
            "errores": self.errores,
            "dry_run": self.dry_run,
            "detalles": self.detalles,
        }


# ─────────────────────────────────────────────────────────────────────
# Validación del patrón
# ─────────────────────────────────────────────────────────────────────

class PatronInvalido(ValueError):
    pass


def validar_patron(patron: dict) -> None:
    """Lanza PatronInvalido si el patrón no cumple el schema."""

    if not isinstance(patron, dict):
        raise PatronInvalido("patron debe ser dict")

    tipo = patron.get("tipo")
    if tipo not in VALID_TIPOS:
        raise PatronInvalido(
            f"tipo='{tipo}' no válido. Opciones: {sorted(VALID_TIPOS)}"
        )

    if not patron.get("campo"):
        raise PatronInvalido("campo es obligatorio")

    cond = patron.get("condicion") or {}
    if not isinstance(cond, dict) or not cond.get("tipo"):
        raise PatronInvalido("condicion.tipo es obligatorio")

    # valor_nuevo es obligatorio (excepto skills_filtro que solo elimina)
    if tipo != "skills_filtro" and patron.get("valor_nuevo") is None:
        raise PatronInvalido("valor_nuevo es obligatorio (excepto skills_filtro)")


# ─────────────────────────────────────────────────────────────────────
# Clase base
# ─────────────────────────────────────────────────────────────────────

class PropagatorBase(ABC):
    """
    Cada subclase implementa la propagación de un tipo de corrección.

    El flujo es:
      1. identify(patron) → lista de id_oferta candidatas
      2. apply(patron, ids, dry_run) → ejecuta los UPDATE/re-process
      3. verify(patron, ids) → confirma que el cambio se aplicó

    El orchestador llama estos 3 pasos en orden.
    """

    TIPO: str = ""  # subclases lo overridean

    def __init__(self, db_path: str = "database/bumeran_scraping.db", verbose: bool = False):
        self.db_path = db_path
        self.verbose = verbose

    @abstractmethod
    def identify(self, patron: dict) -> list:
        """Devuelve lista de id_oferta candidatas para propagación."""

    @abstractmethod
    def apply(self, patron: dict, ids: list, dry_run: bool = True) -> PropagationResult:
        """Aplica el cambio a las ofertas. Si dry_run=True NO toca BD."""

    def verify(self, patron: dict, ids: list) -> dict:
        """Verifica post-fix. Default: re-llama identify y compara.

        Subclases pueden overridear para validación específica.
        """
        post = self.identify(patron)
        # Las que YA NO matchean = se aplicó el fix
        aplicadas = set(ids) - set(post)
        return {
            "verificadas_ok": len(aplicadas),
            "aun_matchean_patron": list(set(ids) & set(post)),
        }

    def run(self, patron: dict, dry_run: bool = True) -> PropagationResult:
        """Pipeline completo: identify → apply → verify."""
        validar_patron(patron)
        if patron["tipo"] != self.TIPO:
            raise PatronInvalido(
                f"Propagator {self.TIPO} no acepta patron tipo={patron['tipo']}"
            )

        ids = self.identify(patron)
        if self.verbose:
            print(f"[{self.TIPO}] identificadas {len(ids)} ofertas")

        result = self.apply(patron, ids, dry_run=dry_run)
        result.tipo = self.TIPO
        result.dry_run = dry_run

        if not dry_run and result.ofertas_actualizadas > 0:
            verification = self.verify(patron, result.ids_tocados)
            result.detalles["verificacion"] = verification

        return result
