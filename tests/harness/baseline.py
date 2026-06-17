#!/usr/bin/env python3
"""SPEC S1C-F0.5-build · Capa 4 — Comparación doble nivel + baseline fechado.

Corre el matcher read-only sobre el Gold Set (capa 3), compara su output contra
el esperado a DOS niveles por separado (ISCO-4 y ESCO granular), captura el
output del baseline como ground-truth-candidato de los casos `true` sin esperado
(criterio de aceptación 2), y guarda el reporte de baseline fechado en
tests/harness/baseline_<fecha>.json + un resumen legible.

Este es el baseline honesto: reemplaza el 81,63% estático de diciembre. Si el
número es bajo, es el dato real — no es un error a corregir, es el cero honesto.

Lectura del número (registrado a pedido de Gerardo):
- La precisión global sobre los 113 será alta por construcción (98 ya marcados
  `true` = "coincide con lo que el sistema hacía", NO una verdad independiente).
- El número que importa es la precisión sobre los 15 casos `false` (¿el matcher
  ya los corrige?) y el desglose a ESCO granular.
"""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from ground_truth import GoldCase, load_ground_truth_default
from runner import RunRecord, run_matcher_over_ids

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HARNESS_DIR = Path(__file__).resolve().parent


def _cmp(actual: Optional[str], esperado: Optional[str]) -> Optional[bool]:
    """True/False si hay esperado; None si no hay esperado (no medible)."""
    if esperado is None:
        return None
    return actual == esperado


def build_baseline(fecha: str) -> dict:
    casos, conn = load_ground_truth_default(fecha)
    by_id: Dict[str, GoldCase] = {c.id_oferta: c for c in casos}
    ids = [c.id_oferta for c in casos]

    recs = run_matcher_over_ids(ids, conn, verify_readonly=True)
    rec_by_id: Dict[str, RunRecord] = {r.id_oferta: r for r in recs}
    conn.close()

    casos_out: List[dict] = []
    for oid in ids:
        gc = by_id[oid]
        r = rec_by_id.get(oid)
        if r is None:
            casos_out.append({"id_oferta": oid, "medible": False, "motivo": "sin_resultado_matcher"})
            continue

        # Nivel ISCO-4
        isco4_ok = _cmp(r.isco4, gc.isco4_esperado)
        # Nivel ESCO granular (comparación por URI, no por string de label)
        esco_ok = _cmp(r.esco_uri, gc.esco_uri_esperado)

        # Captura de target implícito para los `true` sin esperado:
        # el output del baseline ES su ground-truth-candidato (pendiente Cyn).
        target_implicito = None
        if gc.target_implicito_pendiente:
            target_implicito = {
                "isco4": r.isco4,
                "esco_uri": r.esco_uri,
                "esco_label": r.esco_label,
                "metodo": r.decision_metodo,
                "validacion_cyn": "pendiente",
            }

        casos_out.append(
            {
                "id_oferta": oid,
                "titulo": r.titulo,
                "esco_ok_gold": gc.esco_ok,
                "es_error_gold": not gc.esco_ok,
                # esperado resuelto
                "isco4_esperado": gc.isco4_esperado,
                "esco_uri_esperado": gc.esco_uri_esperado,
                "esco_esperado_label": gc.esco_esperado_label,
                "esco_label_sin_resolver": gc.esco_label_sin_resolver,
                # output del matcher (baseline)
                "isco4_matcher": r.isco4,
                "esco_uri_matcher": r.esco_uri,
                "esco_label_matcher": r.esco_label,
                "metodo": r.decision_metodo,
                "regla_aplicada": r.regla_aplicada,
                "score": r.score,
                # veredictos por nivel (None = no medible a ese nivel)
                "isco4_acierto": isco4_ok,
                "esco_acierto": esco_ok,
                # target implícito capturado (criterio de aceptación 2)
                "target_implicito": target_implicito,
            }
        )

    # ---- Agregados ----
    def _acc(items, key):
        medibles = [c for c in items if c.get(key) is not None]
        aciertos = sum(1 for c in medibles if c[key])
        return {
            "medibles": len(medibles),
            "aciertos": aciertos,
            "precision": round(aciertos / len(medibles), 4) if medibles else None,
        }

    errores = [c for c in casos_out if c.get("es_error_gold")]
    explicitos_isco = [c for c in casos_out if c.get("isco4_esperado")]
    explicitos_esco = [c for c in casos_out if c.get("esco_uri_esperado")]

    # Desglose por método (sobre los medibles a ISCO-4)
    metodo_breakdown: Dict[str, Dict[str, int]] = {}
    for c in casos_out:
        if c.get("isco4_acierto") is None:
            continue
        m = c.get("metodo") or "desconocido"
        b = metodo_breakdown.setdefault(m, {"medibles": 0, "aciertos": 0})
        b["medibles"] += 1
        if c["isco4_acierto"]:
            b["aciertos"] += 1
    # método sobre TODOS (incluye true sin esperado) para ver por dónde decide
    metodo_global: Dict[str, int] = {}
    for c in casos_out:
        if "metodo" in c:
            m = c.get("metodo") or "desconocido"
            metodo_global[m] = metodo_global.get(m, 0) + 1

    baseline = {
        "spec": "S1C-F0.5-build",
        "tipo": "baseline_honesto",
        "fecha_baseline": fecha,
        "fuente_gt": f"tests/harness/gold_set_snapshot_{fecha}.json",
        "reemplaza": "81.63% estatico de diciembre 2025 (marca humana nunca recomputada)",
        "lectura": (
            "Precision global alta por construccion (98/113 marcados true = "
            "coincide con lo que el sistema hacia, no verdad independiente). "
            "El numero que importa: precision sobre los 15 false y desglose ESCO."
        ),
        "n_casos": len(casos_out),
        "precision_isco4_explicito": _acc(explicitos_isco, "isco4_acierto"),
        "precision_esco_explicito": _acc(explicitos_esco, "esco_acierto"),
        "precision_isco4_sobre_errores": _acc(errores, "isco4_acierto"),
        "precision_esco_sobre_errores": _acc(errores, "esco_acierto"),
        "n_target_implicito_capturado": sum(
            1 for c in casos_out if c.get("target_implicito")
        ),
        "n_esco_sin_resolver": sum(
            1 for c in casos_out if c.get("esco_label_sin_resolver")
        ),
        "metodo_breakdown_isco4": metodo_breakdown,
        "metodo_global": metodo_global,
        "limites": [
            "Gold Set sesgado a true (98 vs 15): matriz de transicion con esperado "
            "explicito es chica (19 ISCO / 11 ESCO); el grueso de deteccion de "
            "regresion futura se apoya en el target implicito de los 91 (confirma diseno §7).",
            "2 casos sin resolver a ESCO (Delineante tecnico 3118, Gerente de comercio 1221) "
            "son AUSENCIAS GENUINAS de ESCO, no fallas de resolucion: ocupacion argentina "
            "que ESCO no cubre (conecta Eje 3, vocabulario propio). Medibles a ISCO-4.",
            "Acierto en los true significa 'coincide con lo que el sistema hacia al validar', "
            "no verdad independiente. El target implicito capturado queda pendiente de Cyn.",
        ],
        "casos": casos_out,
    }
    return baseline


def render_summary(b: dict) -> str:
    L = []
    L.append(f"# Baseline honesto del matcher de ocupación — {b['fecha_baseline']}")
    L.append("")
    L.append(f"Casos: {b['n_casos']} | reemplaza: {b['reemplaza']}")
    L.append("")
    L.append("## Precisión por nivel (sobre casos con esperado EXPLÍCITO)")

    def line(name, acc):
        if acc["precision"] is None:
            return f"- {name}: sin casos medibles"
        return f"- {name}: {acc['aciertos']}/{acc['medibles']} = {acc['precision']*100:.1f}%"

    L.append(line("ISCO-4 (explícito)", b["precision_isco4_explicito"]))
    L.append(line("ESCO granular (explícito)", b["precision_esco_explicito"]))
    L.append("")
    L.append("## ⭐ Precisión sobre los 15 casos `false` (el número que importa)")
    L.append(line("ISCO-4 sobre errores", b["precision_isco4_sobre_errores"]))
    L.append(line("ESCO sobre errores", b["precision_esco_sobre_errores"]))
    L.append("")
    L.append("## Target implícito capturado (criterio de aceptación 2)")
    L.append(f"- {b['n_target_implicito_capturado']} casos `true` sin esperado → "
             f"output baseline guardado como ground-truth-candidato (pendiente Cyn)")
    L.append("")
    L.append("## Desglose por método de decisión (sobre medibles a ISCO-4)")
    for m, v in sorted(b["metodo_breakdown_isco4"].items()):
        prec = f"{v['aciertos']}/{v['medibles']}" if v["medibles"] else "0/0"
        L.append(f"- {m}: {prec}")
    L.append("")
    L.append("## Método global (cómo decide el matcher sobre los 113)")
    for m, n in sorted(b["metodo_global"].items(), key=lambda x: -x[1]):
        L.append(f"- {m}: {n}")
    L.append("")
    L.append("## Límites del baseline")
    for lim in b["limites"]:
        L.append(f"- {lim}")
    L.append("")
    return "\n".join(L)


def main():
    p = argparse.ArgumentParser(description="Baseline honesto (capa 4)")
    p.add_argument("--fecha", required=True)
    args = p.parse_args()

    b = build_baseline(args.fecha)
    out_json = HARNESS_DIR / f"baseline_{args.fecha}.json"
    out_md = HARNESS_DIR / f"baseline_{args.fecha}.md"
    out_json.write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_summary(b), encoding="utf-8")
    print(render_summary(b))
    print(f"\nGuardado: {out_json.relative_to(PROJECT_ROOT)}")
    print(f"Guardado: {out_md.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
