#!/usr/bin/env python3
"""SPEC S1C-F0.5-build · Capa 2 — Cargador de ground truth + resolución de niveles.

Carga el snapshot fechado y normaliza el esperado de cada caso a DOS niveles
comparables:

  - ISCO-4: de `isco_esperado` (string de 4 dígitos, tal cual). El output del
    matcher se compara derivando ISCO-4 de su `isco_code`.
  - ESCO granular: resolviendo `esco_esperado` (ETIQUETA LEGIBLE, no URI ni
    código) a un occupation_uri / esco_code vía la tabla ESCO local. NO es
    comparación de strings (riesgo "representación heterogénea", diseño §7):
    el matcher devuelve esco_uri y esco_label, así que el esperado debe
    resolverse al mismo identificador (uri) para comparar sin contar diferencias
    de redacción como errores.

Los casos `esco_ok=true` sin esperado explícito quedan marcados como
TARGET IMPLÍCITO PENDIENTE: su target se completa en la capa 4 con el output
del baseline (criterio de aceptación 2).

Read-only: solo SELECT sobre esco_occupations + alt labels y lectura del snapshot.
"""

import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HARNESS_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"


def normalize_label(s: Optional[str]) -> str:
    """Normaliza una etiqueta de ocupación para comparación robusta.

    Despoja acentos (el gold set los pierde: 'tecnico' vs 'técnico'), pasa a
    minúsculas, quita comillas tipográficas, normaliza espaciado alrededor de
    '/' y colapsa espacios. Resuelve la mayoría del desajuste de redacción
    entre el label del gold set y el preferred_label_es de ESCO.
    """
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("“", "").replace("”", "").replace('"', "")
    s = re.sub(r"\s*/\s*", "/", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


class EscoResolver:
    """Resuelve etiqueta legible de ocupación → (occupation_uri, esco_code, isco_code)."""

    def __init__(self, conn: sqlite3.Connection):
        # preferred_label_es → (uri, esco_code, isco_code)
        self._pref: Dict[str, Tuple[str, Optional[str], Optional[str]]] = {}
        # alt label → uri (resolvemos el resto vía _by_uri)
        self._alt: Dict[str, str] = {}
        self._by_uri: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
        for uri, esco_code, isco_code, lab in conn.execute(
            "SELECT occupation_uri, esco_code, isco_code, preferred_label_es FROM esco_occupations"
        ):
            self._by_uri[uri] = (esco_code, isco_code)
            if lab:
                self._pref.setdefault(normalize_label(lab), (uri, esco_code, isco_code))
        for uri, lab in conn.execute(
            "SELECT occupation_uri, label FROM esco_occupation_alternative_labels"
        ):
            if lab:
                self._alt.setdefault(normalize_label(lab), uri)

    def resolve(self, label: Optional[str]) -> Optional[dict]:
        """Devuelve {uri, esco_code, isco_code, via} o None si no resuelve."""
        if not label:
            return None
        candidatos = [normalize_label(label)]
        # Fallback: tomar solo la variante masculina (antes de la primera '/')
        # para casos como 'delineante tecnico/delineante tecnica'.
        norm = candidatos[0]
        if "/" in norm:
            candidatos.append(norm.split("/", 1)[0].strip())
        for idx, cand in enumerate(candidatos):
            via = "label_completo" if idx == 0 else "label_masculino"
            if cand in self._pref:
                uri, esco_code, isco_code = self._pref[cand]
                return {"uri": uri, "esco_code": esco_code, "isco_code": isco_code, "via": f"preferred/{via}"}
            if cand in self._alt:
                uri = self._alt[cand]
                esco_code, isco_code = self._by_uri.get(uri, (None, None))
                return {"uri": uri, "esco_code": esco_code, "isco_code": isco_code, "via": f"alt/{via}"}
        return None


def isco4(code: Optional[str]) -> Optional[str]:
    """Deriva ISCO-4 de un código ISCO crudo (quita prefijo 'C', toma 4 dígitos)."""
    if not code:
        return None
    c = str(code).lstrip("C")
    return c[:4] if len(c) >= 4 else (c or None)


@dataclass
class GoldCase:
    id_oferta: str
    esco_ok: bool
    es_true_sin_esperado: bool
    # Esperado explícito resuelto a dos niveles (None si no hay)
    isco4_esperado: Optional[str] = None
    esco_uri_esperado: Optional[str] = None
    esco_esperado_label: Optional[str] = None
    esco_resolucion_via: Optional[str] = None
    esco_label_sin_resolver: Optional[str] = None  # label que no resolvió
    tipo_error: Optional[str] = None
    comentario: Optional[str] = None
    # Target implícito (se completa en capa 4 para los true sin esperado)
    target_implicito_pendiente: bool = False


def load_ground_truth(snapshot_path: Path, conn: sqlite3.Connection) -> List[GoldCase]:
    snap = json.loads(snapshot_path.read_text(encoding="utf-8"))
    resolver = EscoResolver(conn)
    casos: List[GoldCase] = []
    for c in snap["casos"]:
        gc = GoldCase(
            id_oferta=str(c["id_oferta"]),
            esco_ok=bool(c["esco_ok"]),
            es_true_sin_esperado=bool(c.get("es_true_sin_esperado")),
            tipo_error=c.get("tipo_error"),
            comentario=c.get("comentario"),
        )
        # Nivel ISCO-4
        if c.get("isco_esperado"):
            gc.isco4_esperado = isco4(c["isco_esperado"])
        # Nivel ESCO granular (resolución label→uri)
        if c.get("esco_esperado"):
            gc.esco_esperado_label = c["esco_esperado"]
            res = resolver.resolve(c["esco_esperado"])
            if res:
                gc.esco_uri_esperado = res["uri"]
                gc.esco_resolucion_via = res["via"]
                # Si no había isco_esperado pero el ESCO resolvió, derivamos ISCO-4
                if gc.isco4_esperado is None and res.get("isco_code"):
                    gc.isco4_esperado = isco4(res["isco_code"])
            else:
                gc.esco_label_sin_resolver = c["esco_esperado"]
        # Marca de target implícito pendiente
        gc.target_implicito_pendiente = gc.es_true_sin_esperado
        casos.append(gc)
    return casos


def load_ground_truth_default(fecha: str) -> Tuple[List[GoldCase], sqlite3.Connection]:
    conn = sqlite3.connect(str(DB_PATH))
    snap = HARNESS_DIR / f"gold_set_snapshot_{fecha}.json"
    return load_ground_truth(snap, conn), conn


def _summary(casos: List[GoldCase]) -> dict:
    return {
        "n_casos": len(casos),
        "n_esco_ok_true": sum(1 for c in casos if c.esco_ok),
        "n_esco_ok_false": sum(1 for c in casos if not c.esco_ok),
        "n_con_isco4_esperado": sum(1 for c in casos if c.isco4_esperado),
        "n_con_esco_esperado_label": sum(1 for c in casos if c.esco_esperado_label),
        "n_esco_resuelto": sum(1 for c in casos if c.esco_uri_esperado),
        "n_esco_sin_resolver": sum(1 for c in casos if c.esco_label_sin_resolver),
        "n_true_sin_esperado": sum(1 for c in casos if c.target_implicito_pendiente),
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Cargador de ground truth (capa 2)")
    p.add_argument("--fecha", required=True)
    args = p.parse_args()
    casos, conn = load_ground_truth_default(args.fecha)
    s = _summary(casos)
    print("Resumen ground truth resuelto:")
    for k, v in s.items():
        print(f"  {k}: {v}")
    sin = [c for c in casos if c.esco_label_sin_resolver]
    if sin:
        print("\nESCO sin resolver (label→código):")
        for c in sin:
            print(f"  {c.id_oferta}: {c.esco_label_sin_resolver!r}")
    conn.close()
