#!/usr/bin/env python3
"""SPEC S1C-G3 · P.1 — Ground-truth de denominación argentina.

Parsea, de las anotaciones G3 de Cyn (texto libre del ledger), los pares
(denominacion_ar, esco_label_cyn) y resuelve cada esco_label a su esco_uri REAL
del catálogo (esco_occupations) con la normalización robusta de F0.5
(EscoResolver de ground_truth.py: acentos, slash, variante masculina, alt-labels).

Regla dura del spec: si un label de Cyn NO resuelve a URI real, se marca
"pendiente_validacion_cyn" — NUNCA se inventa URI.

Read-only: SELECT sobre el catálogo + lectura de artefactos. NO persiste en BD.
Salida: tests/harness/g3_ground_truth_denominacion_<fecha>.json
"""
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/mnt/d/OEDE/Webscrapping")
DB = ROOT / "database" / "bumeran_scraping.db"
sys.path.insert(0, str(ROOT / "tests" / "harness"))
from ground_truth import EscoResolver, isco4  # noqa: E402

FECHA = "2026-06-23"

# ---- fuentes ----
g3_ids = [str(x) for x in json.load(open("/tmp/g3_ids.json"))]
ledger = {}
for line in open(ROOT / "exports" / "cyn_backlog" / "ledger_correcciones_cyn.jsonl"):
    r = json.loads(line)
    ledger[str(r["id_oferta"])] = r
v14 = {d["oid"]: d for d in json.load(open("/tmp/g3_v14_result.json"))["detalle"]}

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
resolver = EscoResolver(conn)

# ---- patrones de extracción de label-target de Cyn ----
# Cada patrón captura (codigo_esco_opcional, label). Se prueban en orden;
# se acumulan TODOS los candidatos y se intenta resolver cada uno.
# Variabilidad real del texto de Cyn:
#  - código tipo 3122.4 / 8160.34 / 1330.7 (ISCO4 + subcódigo)
#  - separador código→label: a veces "-", a veces solo espacios, a veces ":"
#  - label entre comillas tipográficas o rectas, o sin comillas hasta ./;/\n
#  - typos del encabezado: "CLASIFICACIO ESCO" (sin N), "CLASIFICACIÓN"
CODE = r"(\d{4}(?:\.\d+)*)"  # ISCO4 + cualquier profundidad de subcódigo
# label: o entre comillas (captura todo hasta la comilla de cierre),
# o sin comillas (hasta . ; comilla suelta de cierre, \n o " - " de cláusula)
LBL_Q = r'["“]([^"”]+)["”]'
LBL_U = r'([^"”\n.;]+?)(?:\s*[.;]|["”]|\n|\s+[-–—]\s|$)'
SEP = r"\s*[-–—:]?\s*"  # separador opcional código→label
PATRONES = [
    re.compile(r"CLASIFICACI[OÓ]?N?\s+ESCO\s*[:;]?\s*" + CODE + SEP + LBL_Q, re.I),
    re.compile(r"CLASIFICACI[OÓ]?N?\s+ESCO\s*[:;]?\s*" + CODE + SEP + LBL_U, re.I),
    re.compile(r"CLASIFICACI[OÓ]?N?\s+ISCO\s*[:;]?\s*" + CODE + SEP + LBL_Q, re.I),
    re.compile(r"Ubicaci[oó]n sugerida dentro del Excel\s*[:;]?\s*ESCO\s*" + CODE + SEP + LBL_Q, re.I),
    re.compile(r"Ubicaci[oó]n sugerida dentro del Excel\s*[:;]?\s*ESCO\s*" + CODE + SEP + LBL_U, re.I),
    re.compile(r"denominaci[oó]n ESCO (?:m[aá]s adecuada|pertinente|correcta)[^\n]{0,40}?\bes\b[^\n]{0,30}?" + CODE + SEP + LBL_U, re.I),
    re.compile(r"ocupaci[oó]n ESCO (?:pertinente|correcta|adecuada)[^\n]{0,20}?es\s+" + LBL_U, re.I),
    re.compile(r"DENOMINACI[OÓ]N\s+CORRECTA\s*[:;]?\s*" + LBL_Q, re.I),
    re.compile(r"DENOMINACI[OÓ]N\s+CORRECTA\s*[:;]?\s*" + LBL_U, re.I),
    re.compile(r"\bESCO\s+" + CODE + SEP + LBL_Q, re.I),
]
# Señal explícita de Cyn de que el target queda sin determinar
RE_PENDIENTE = re.compile(r"queda pendiente de validaci[oó]n|pendiente de validaci[oó]n si no", re.I)
# Denominación argentina
RE_DENOM_AR = re.compile(r"DENOMINACI[OÓ]N\s*:?\s*Argentina\s*:?\s*([^\n]+?)(?:\s*[-–—]?\s*Espa[nñ]a|\n|$)", re.I)


# conectores que en el texto de Cyn suelen colgar una cláusula explicativa
# DESPUÉS del nombre de la ocupación. Cortamos ahí para no arrastrar ruido
# (que hace fallar el full-label y dispara fallbacks erróneos).
RE_CORTE = re.compile(
    r"\s*(?:,|;|\bcomo\b|\bseg[uú]n\b|\basociad[oa]\b|\bpertenecient|\bperteneci|"
    r"\bc[oó]digo\b|\bgrupo\b|\bporque\b|\bya que\b|\(|\bcuyo\b|\bque \b)",
    re.I,
)


def limpiar_label(lab: str) -> str:
    lab = (lab or "").strip(" -–—\"“”").strip()
    m = RE_CORTE.search(lab)
    if m:
        lab = lab[: m.start()].strip(" -–—\"“”").strip()
    return lab


def candidatos_label(texto: str):
    """Devuelve lista de (codigo, label) candidatos, en orden de aparición de patrón."""
    out = []
    seen = set()
    for pat in PATRONES:
        for m in pat.finditer(texto):
            gs = m.groups()
            if len(gs) == 2:
                cod, lab = gs
            else:
                cod, lab = None, gs[0]
            lab = limpiar_label(lab)
            if lab and len(lab) > 3 and (cod, lab.lower()) not in seen:
                seen.add((cod, lab.lower()))
                out.append((cod, lab))
    return out


def texto_cyn(rec):
    cc = rec.get("cyn_correccion") or {}
    partes = [
        (rec.get("cyn_texto_original") or {}).get("descripcion", "") or "",
        cc.get("justificacion", "") or "",
        cc.get("esco_sugerido_texto", "") or "",
    ]
    return "\n".join(p for p in partes if p)


resultados = []
stats = Counter()
for oid in g3_ids:
    rec = ledger.get(oid)
    entry = {
        "oid": oid,
        "canal_inicial": (v14.get(oid) or {}).get("bucket"),
        "metodo_inicial": (v14.get(oid) or {}).get("metodo"),
        "denominacion_ar": None,
        "esco_label_cyn": None,
        "esco_code_cyn": None,
        "esco_uri": None,
        "esco_label_resuelto": None,
        "isco_resuelto": None,
        "via_resolucion": None,
        "estado": None,  # resuelto | pendiente_validacion_cyn | sin_texto
    }
    if rec is None:
        entry["estado"] = "sin_texto"
        stats["sin_texto"] += 1
        resultados.append(entry)
        continue
    txt = texto_cyn(rec)
    # denominación argentina (para futuras keys/variantes del diccionario)
    mden = RE_DENOM_AR.search(txt)
    if mden:
        entry["denominacion_ar"] = mden.group(1).strip(" -–—")
    cands = candidatos_label(txt)
    resuelto = None
    descartados_incoherentes = []
    for cod, lab in cands:
        res = resolver.resolve(lab)
        if not res:
            continue
        # Guarda de coherencia: si Cyn dio un código ESCO, su ISCO-4 es
        # autoritativo. Una resolución de label que aterriza en otro ISCO-4
        # es un falso positivo (p.ej. masculino "editor" -> "editor jefe"
        # 1349 cuando Cyn pidió 2654.5). Se descarta -> pendiente.
        if cod:
            isco_cod = cod[:4]
            isco_res = isco4(res["isco_code"])
            if isco_res and isco_res != isco_cod:
                descartados_incoherentes.append((cod, lab, isco_res))
                continue
        resuelto = (cod, lab, res)
        break
    if resuelto:
        cod, lab, res = resuelto
        entry.update(
            esco_label_cyn=lab,
            esco_code_cyn=cod,
            esco_uri=res["uri"],
            esco_label_resuelto=None,  # se completa abajo
            isco_resuelto=isco4(res["isco_code"]),
            via_resolucion=res["via"],
            estado="resuelto",
        )
        # label canónico del catálogo (para verificar)
        row = conn.execute(
            "SELECT preferred_label_es FROM esco_occupations WHERE occupation_uri=?",
            (res["uri"],),
        ).fetchone()
        entry["esco_label_resuelto"] = row[0] if row else None
        stats["resuelto"] += 1
    else:
        entry["estado"] = "pendiente_validacion_cyn"
        if descartados_incoherentes:
            entry["esco_label_cyn"] = descartados_incoherentes[0][1]
            entry["esco_code_cyn"] = descartados_incoherentes[0][0]
            entry["nota"] = (
                f"label resolvió a ISCO {descartados_incoherentes[0][2]} != código Cyn "
                f"{descartados_incoherentes[0][0][:4]} -> descartado por incoherencia"
            )
            stats["pendiente_incoherente"] += 1
        elif RE_PENDIENTE.search(txt):
            stats["pendiente_explicito"] += 1
        elif cands:
            entry["esco_label_cyn"] = cands[0][1]
            entry["esco_code_cyn"] = cands[0][0]
            stats["pendiente_no_resolvio"] += 1
        else:
            stats["pendiente_sin_parseo"] += 1
    resultados.append(entry)

out = {
    "generado": FECHA,
    "spec": "S1C-G3 / P.1",
    "fuente": "ledger_correcciones_cyn.jsonl (descripcion+justificacion+esco_sugerido_texto)",
    "resolutor": "EscoResolver de tests/harness/ground_truth.py (F0.5)",
    "regla": "label que no resuelve a URI real -> pendiente_validacion_cyn (NO se inventa URI)",
    "total": len(resultados),
    "stats": dict(stats),
    "ground_truth": resultados,
}
outpath = ROOT / "tests" / "harness" / f"g3_ground_truth_denominacion_{FECHA}.json"
json.dump(out, open(outpath, "w"), ensure_ascii=False, indent=1)

print("=== P.1 — ground-truth de denominación G3 ===")
print(f"total G3: {len(resultados)}")
for k, n in stats.most_common():
    print(f"  {n:4}  {k}")
resu = sum(1 for r in resultados if r["estado"] == "resuelto")
pend = sum(1 for r in resultados if r["estado"] == "pendiente_validacion_cyn")
print(f"\n>> resueltos a URI real: {resu}")
print(f">> pendientes validación Cyn (NO se inventó URI): {pend}")
print(f"\nartefacto: {outpath}")
