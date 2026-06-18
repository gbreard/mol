#!/usr/bin/env python3
"""SPEC S1C-F0.6 — Clasificación a/b/c + 4 cortes. Lee la re-corrida y el ledger.

Recupera el target de ocupación de Cyn del TEXTO LIBRE (no solo del campo parseado),
distingue error real de ocupación (target != respuesta de mayo) de confirmaciones,
clasifica en (a) sigue errando / (b) acierta por parche de Cyn / (c) acierta por
canal general, y arma los 4 cortes.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LEDGER = ROOT / "exports/cyn_backlog/ledger_correcciones_cyn.jsonl"
RECORRIDA = ROOT / "tests/harness/anatomia_recorrida_2026-06-18.json"
UNIVERSO = ROOT / "tests/harness/universo_errores_cyn_2026-06-18.json"

RE_ESCO = re.compile(r'ESCO\s*(\d{4})(?:\.\d+)?\s*[—\-–:]\s*([^.\n]{3,80})', re.I)

# Familias ocupacionales por primer dígito ISCO (grandes grupos ISCO-08)
ISCO_FAMILIA = {
    "1": "Directivos", "2": "Profesionales/científicos",
    "3": "Técnicos/profesionales asociados", "4": "Apoyo administrativo",
    "5": "Servicios y ventas", "6": "Agro/pesca calificados",
    "7": "Oficios y artesanos", "8": "Operadores de planta/máquinas",
    "9": "Ocupaciones elementales", "0": "Fuerzas armadas",
}


def isco4(code):
    if not code:
        return None
    c = str(code).lstrip("C")
    return c[:4] if len(c) >= 4 else (c or None)


def get_desc(r):
    t = r.get("cyn_texto_original", {})
    return t.get("descripcion", "") if isinstance(t, dict) else str(t or "")


def main():
    recs = [json.loads(l) for l in open(LEDGER)]
    rec = json.load(open(RECORRIDA))
    hoy = rec["resultado_hoy"]
    origins = rec["rule_origins"]
    casos_uni = json.load(open(UNIVERSO))["casos"]

    # ofertas que originaron una regla (origen literal) -> set de id_oferta
    ofertas_origen_regla = set()
    rule_by_oferta = defaultdict(list)  # oferta_id -> [rule_id]
    for rid, o in origins.items():
        if o.get("oferta_ejemplo_id"):
            ofertas_origen_regla.add(str(o["oferta_ejemplo_id"]))
            rule_by_oferta[str(o["oferta_ejemplo_id"])].append(rid)

    by_oferta = defaultdict(list)
    for r in recs:
        by_oferta[r["id_oferta"]].append(r)

    # --- recuperar target + verdict de ocupacion por oferta ---
    analisis = {}
    for oid in casos_uni:
        h = hoy.get(oid)
        if not h:
            continue
        rs = by_oferta.get(oid, [])
        # target ISCO-4 (texto libre + parseado)
        cand = []
        verdict_ocup = None
        mayo_isco4 = None
        mayo_metodo = mayo_decision = mayo_regla = None
        for r in rs:
            cc = r["cyn_correccion"]; pa = r["pipeline_actual"]
            if pa.get("isco") and mayo_isco4 is None:
                mayo_isco4 = isco4(pa.get("isco"))
                mayo_metodo = pa.get("metodo_match")
                mayo_decision = pa.get("metodo_decision")
                mayo_regla = pa.get("regla_aplicada")
            if cc.get("ocupacion_verdict") and verdict_ocup is None:
                verdict_ocup = cc.get("ocupacion_verdict")
            for m in RE_ESCO.finditer(get_desc(r)):
                cand.append(m.group(1))
            if cc.get("isco_sugerido") and cc["isco_sugerido"] != "None":
                cand.append(isco4(cc["isco_sugerido"]))
            est = cc.get("esco_sugerido_texto")
            if est and est != "None":
                mm = re.search(r"(\d{4})", est)
                if mm:
                    cand.append(mm.group(1))
        # delta supabase target
        if casos_uni[oid].get("fuente") == "supabase_delta":
            t = casos_uni[oid].get("isco_sugerido")
            if t:
                cand.append(isco4(t))
        target = Counter([c for c in cand if c]).most_common(1)[0][0] if cand else None

        # es error real de ocupacion? target existe y != respuesta de mayo
        es_error_ocup = bool(target and mayo_isco4 and target != mayo_isco4)

        h4 = h["isco4_hoy"]
        # estado
        estado = None
        if es_error_ocup:
            acierta_hoy = (h4 == target)
            if not acierta_hoy:
                estado = "a_sigue_errando"
            else:
                # (b) decidido por regla nacida de ESTA correccion (origen literal)
                rid_hoy = h.get("rid_hoy")
                origen_literal = oid in ofertas_origen_regla and (
                    rid_hoy in rule_by_oferta.get(oid, []) if rid_hoy else False)
                # tambien: la regla que decide hoy tiene autor Cyn (parche humano, looser)
                regla_es_parche_cyn = bool(rid_hoy and origins.get(rid_hoy, {}).get("es_humano_cyn"))
                if origen_literal:
                    estado = "b_parche_circular_literal"
                elif h["canal_familia_hoy"] == "regla" and regla_es_parche_cyn:
                    estado = "b_parche_cyn_regla"
                else:
                    estado = "c_canal_general"
        analisis[oid] = {
            "verdict_ocup": verdict_ocup,
            "target_isco4": target,
            "mayo_isco4": mayo_isco4,
            "mayo_decision": mayo_decision,
            "mayo_regla": mayo_regla,
            "hoy_isco4": h4,
            "hoy_canal": h["canal_familia_hoy"],
            "hoy_decision": h["decision_metodo_hoy"],
            "hoy_regla": h.get("rid_hoy"),
            "es_error_ocup": es_error_ocup,
            "tiene_target": bool(target),
            "estado": estado,
            "canal_cambio_mayo_hoy": (mayo_decision != h["decision_metodo_hoy"]),
            "fam_target": ISCO_FAMILIA.get((target or "")[:1], "?") if target else None,
            "fam_hoy": ISCO_FAMILIA.get((h4 or "")[:1], "?") if h4 else None,
        }

    json.dump({"spec": "SPEC_S1C_F06", "fecha": "2026-06-18", "analisis": analisis},
              open(ROOT / "tests/harness/anatomia_clasificacion_2026-06-18.json", "w"),
              ensure_ascii=False, indent=2)

    # ---------- REPORTES ----------
    A = analisis
    err = {oid: a for oid, a in A.items() if a["es_error_ocup"]}
    print(f"UNIVERSO re-corrido: {len(A)}")
    print(f"  con target recuperable: {sum(1 for a in A.values() if a['tiene_target'])}")
    print(f"  ERROR REAL de ocupacion (target != mayo): {len(err)}")
    print()
    print("=== ESTADOS a/b/c (sobre errores reales con target) ===")
    print(dict(Counter(a["estado"] for a in err.values())))
    print()
    print("=== CORTE 1: canal que decide HOY los errores reales ===")
    print("  (sobre los que SIGUEN errando, estado a):")
    sigue = {oid: a for oid, a in err.items() if a["estado"] == "a_sigue_errando"}
    print("   ", dict(Counter(a["hoy_canal"] for a in sigue.values())))
    print("  (sobre TODOS los errores reales, canal hoy):")
    print("   ", dict(Counter(a["hoy_canal"] for a in err.values())))
    print()
    print("=== Veredicto hipotesis dirigente: decision_metodo hoy (errores reales) ===")
    print("   ", dict(Counter(a["hoy_decision"] for a in err.values())))
    print()
    print("=== CORTE 2: familia ocupacional del TARGET (errores reales) ===")
    print("   ", dict(Counter(a["fam_target"] for a in err.values())))
    print()
    print("=== CORTE 3: nivel de unidad del error (los que SIGUEN errando) ===")
    iscobad = sum(1 for a in sigue.values() if a["hoy_isco4"] != a["target_isco4"])
    print(f"    ISCO-4 mal (rubro entero mal): {iscobad} / {len(sigue)}")
    print()
    print("=== CANAL CAMBIO mayo->hoy (regla nueva en el medio) ===")
    print("    errores reales con cambio de canal:",
          sum(1 for a in err.values() if a["canal_cambio_mayo_hoy"]), "/", len(err))


if __name__ == "__main__":
    main()
