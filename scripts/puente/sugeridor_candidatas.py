"""
Sugeridor de candidatas del puente validacion->diccionario (mesa de Cyn, Eje 4).

Reemplaza al get_rule_suggestions roto (error 42804). Lee las correcciones de
ocupacion del wizard (ofertas_dashboard.validacion_correcciones), resuelve el
esco_uuid al catalogo (patron G3, nunca inventa), corre el clasificador congelado
y produce la BANDEJA MINIMA (markdown ordenado por senal) sobre la que Gerardo
confirma. NO escribe al diccionario: eso es C3 (aplicar_candidata via poller).

Uso:
    python scripts/puente/sugeridor_candidatas.py [--desde 2026-01-01] [--fecha 2026-07-03]

Salidas:
    exports/puente/candidatas_<fecha>.json
    exports/puente/bandeja_<fecha>.md
"""
import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from puente.clasificador import Clasificador, _norm  # noqa: E402

CATALOG = ROOT / "database" / "embeddings" / "esco_occupations_full.json"
DICT_PATH = ROOT / "config" / "sinonimos_argentinos_esco.json"
SQLITE = ROOT / "database" / "bumeran_scraping.db"
SUPA_CFG = ROOT / "config" / "supabase_config.json"
FIXTURE = ROOT / "tests" / "fixtures" / "clasificador_candidatas_fixture_2026-07-03.json"
OUT_DIR = ROOT / "exports" / "puente"


# ---------------- catalogo (resolucion G3) ----------------
def load_catalog():
    occ = json.loads(CATALOG.read_text(encoding="utf-8"))["occupations"]
    uri2occ = {o["uri"]: o for o in occ}
    return uri2occ


def resolver(oc, uri2occ):
    """esco_uuid -> occ del catalogo. Guarda de coherencia ISCO. Nunca inventa.
    Devuelve (occ|None, motivo_si_pendiente)."""
    uuid = oc.get("esco_uuid") or oc.get("esco_uri")
    if not uuid:
        return None, "sin esco_uuid en la correccion"
    uri = uuid if str(uuid).startswith("http") else f"http://data.europa.eu/esco/occupation/{uuid}"
    occ = uri2occ.get(uri)
    if not occ:
        return None, f"esco_uuid no resuelve al catalogo ({uuid})"
    # guarda de coherencia ISCO: el isco del catalogo debe ser prefijo del esco_code
    base = occ["esco_code"].split(".")[0]
    if occ.get("isco_code") and occ["isco_code"] != base:
        return None, f"incoherencia ISCO catalogo ({occ['isco_code']} vs {base})"
    # si la correccion trae isco_code del picker, verificar que coincide
    isco_pick = oc.get("isco_code")
    if isco_pick and isco_pick != occ["isco_code"]:
        return occ, f"aviso: isco del picker ({isco_pick}) != catalogo ({occ['isco_code']})"
    return occ, None


# ---------------- lectura del wizard ----------------
def es_correccion_ocupacion(vc):
    """FILTRO de entrada: entra por PRESENCIA de ocupacion_corregida (no por el flag;
    las correcciones se guardan con validacion_humana='revisar', no 'error')."""
    if isinstance(vc, str):
        try:
            vc = json.loads(vc)
        except Exception:
            return False
    return isinstance(vc, dict) and bool(vc.get("ocupacion_corregida"))


def read_correcciones(desde=None):
    from supabase import create_client
    cfg = json.loads(SUPA_CFG.read_text(encoding="utf-8"))
    client = create_client(cfg["url"], cfg["service_role_key"])
    rows, page = [], 0
    while True:
        r = (client.table("ofertas_dashboard")
             .select("id_oferta,titulo,titulo_limpio,validacion_correcciones,validacion_humana")
             .not_.is_("validacion_correcciones", "null")
             .range(page * 1000, page * 1000 + 999).execute())
        if not r.data:
            break
        rows.extend(r.data)
        if len(r.data) < 1000:
            break
        page += 1
    out = []
    for row in rows:
        vc = row["validacion_correcciones"]
        if isinstance(vc, str):
            try:
                vc = json.loads(vc)
            except Exception:
                continue
        if not es_correccion_ocupacion(vc):
            continue  # FILTRO: presencia de ocupacion_corregida, NO el flag
        fecha = vc.get("fecha") or vc.get("validado_at") or vc.get("timestamp")
        if desde and fecha and str(fecha) < desde:
            continue
        out.append({"row": row, "vc": vc})
    return out


# ---------------- preview de impacto + solape de pileta ----------------
def preview_impacto(client, head_kw, isco):
    if client is None:
        return None
    try:
        r = client.rpc("preview_rule_impact",
                       {"p_titulo_contiene": head_kw, "p_forzar_isco": isco, "p_limit": 3}).execute()
        return r.data
    except Exception as e:
        return {"error": str(e)}


def solape_pileta(con, head_kw):
    """De las ofertas que matchean el head, cuantas tienen skills envenenadas
    (skill_tipo_fuente='terminologia') pendientes de reproceso (pileta, D1/F0.4b)."""
    like = f"%{head_kw.lower()}%"
    total = con.execute("SELECT COUNT(*) FROM ofertas WHERE LOWER(titulo) LIKE ?", (like,)).fetchone()[0]
    envenenadas = con.execute(
        """SELECT COUNT(DISTINCT o.id_oferta) FROM ofertas o
           JOIN ofertas_esco_skills_detalle d
             ON d.id_oferta=o.id_oferta AND d.skill_tipo_fuente='terminologia'
           WHERE LOWER(o.titulo) LIKE ?""", (like,)).fetchone()[0]
    return {"ofertas_titulo_match": total, "con_skills_envenenadas": envenenadas}


# ---------------- overlay de juicio humano (solo stock conocido) ----------------
def load_hj_overlay():
    try:
        fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {c["id_oferta"]: c["juicio_humano"]["clase"] for c in fx["casos"]}


def estado_bandeja(clase, hj):
    """AUTO / A-CONFIRMAR / CONDICIONAL->traductor / RUIDO. A-CONFIRMAR solo cuando
    hay juicio humano registrado que dice VOCABULARIO pero el clasificador lo mando
    a la bandeja (rescatable). Es advisory: para correcciones nuevas sin HJ no aplica."""
    if clase == "RUIDO":
        return "RUIDO"
    if clase == "VOCABULARIO":
        return "AUTO"
    if hj == "VOCABULARIO":
        return "A-CONFIRMAR"
    return "CONDICIONAL->traductor"


# ---------------- main ----------------
def build(desde=None, fecha="hoy", con=None, supa_client="auto"):
    uri2occ = load_catalog()
    clf = Clasificador()
    hj_overlay = load_hj_overlay()
    dict_lookup = clf._dict_esco_codes()
    con = con or sqlite3.connect(str(SQLITE))
    if supa_client == "auto":
        try:
            from supabase import create_client
            cfg = json.loads(SUPA_CFG.read_text(encoding="utf-8"))
            supa_client = create_client(cfg["url"], cfg["service_role_key"])
        except Exception:
            supa_client = None

    correcciones = read_correcciones(desde)
    candidatas = []
    for c in correcciones:
        row, vc = c["row"], c["vc"]
        oc = vc["ocupacion_corregida"]
        denom = row.get("titulo") or ""
        occ, motivo = resolver(oc, uri2occ)
        cid = str(row["id_oferta"])
        base = {
            "id_oferta": cid,
            "denominacion": denom,
            "titulo_limpio": row.get("titulo_limpio"),
            "validacion_humana": row.get("validacion_humana"),
        }
        if occ is None:
            candidatas.append({**base, "estado": "PENDIENTE", "motivo": motivo,
                               "esco_code": None})
            continue
        esco = occ["esco_code"]
        ruido = clf.es_ruido(denom)
        if ruido:
            res = {"clase": "RUIDO", "senal": "ruido", "conflicto_retroactivo": None}
        else:
            res = clf.clasificar(denom, esco, dict_lookup=dict_lookup)
        hj = hj_overlay.get(cid)
        estado = estado_bandeja(res["clase"], hj)
        head_kw = clf.head(denom)
        cand = {
            **base,
            "esco_code": esco,
            "esco_label": occ["esco_label"],
            "isco": occ["isco_code"],
            "head": head_kw,
            "clasificacion": res["clase"],
            "senal": res["senal"],
            "conflicto_retroactivo": res["conflicto_retroactivo"],
            "juicio_humano": hj,
            "estado": estado,
            "motivo_resolucion": motivo,
            "ruido_motivo": ruido,
        }
        # preview solo para cargables (AUTO / A-CONFIRMAR)
        if estado in ("AUTO", "A-CONFIRMAR"):
            cand["preview_impacto"] = preview_impacto(supa_client, head_kw, occ["isco_code"])
            cand["solape_pileta"] = solape_pileta(con, head_kw)
        candidatas.append(cand)

    return candidatas


def render_bandeja(candidatas, fecha):
    order = {"AUTO": 0, "A-CONFIRMAR": 1, "CONDICIONAL->traductor": 2, "RUIDO": 3, "PENDIENTE": 4}
    cs = sorted(candidatas, key=lambda c: (order.get(c.get("estado"), 9), c.get("senal") or ""))
    lines = [f"# Bandeja de candidatas — puente validacion->diccionario ({fecha})", ""]
    cnt = Counter(c.get("estado") for c in candidatas)
    lines.append("**Resumen:** " + " · ".join(f"{k}={cnt[k]}" for k in order if cnt.get(k)))
    lines.append("")
    lines.append("| estado | denominacion | esco_code | clasif | senal | evidencia (id) | impacto | solape pileta |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for c in cs:
        pv = c.get("preview_impacto")
        imp = "-"
        if isinstance(pv, dict) and "total_afectadas" in pv:
            imp = f"{pv.get('total_afectadas')} match head / {pv.get('cambiarian')} cambiarian"
        elif isinstance(pv, dict) and pv.get("error"):
            imp = "preview n/d"
        sp = c.get("solape_pileta")
        sp_s = "-"
        if sp:
            sp_s = f"{sp['con_skills_envenenadas']}/{sp['ofertas_titulo_match']} envenenadas (F0.4b)"
        conf = ""
        if c.get("conflicto_retroactivo"):
            conf = f" ⚠conflicto→{c['conflicto_retroactivo']['esco_code_dic']}"
        den = (c.get("denominacion") or "")[:40]
        lines.append(f"| {c.get('estado')} | {den} | {c.get('esco_code') or '-'} | "
                     f"{c.get('clasificacion') or c.get('motivo','')} | {c.get('senal','')}{conf} | "
                     f"{c['id_oferta']} | {imp} | {sp_s} |")
    lines.append("")
    lines.append("> **AUTO**: clasificador=VOCABULARIO (auto-cargable, Gerardo eyeballs). "
                 "**A-CONFIRMAR**: el clasificador la mando a la bandeja pero hay juicio humano "
                 "registrado que dice VOCABULARIO (rescatable). **CONDICIONAL->traductor**: evidencia "
                 "para el Eje 4. **RUIDO**: titulo no-denominacion.")
    lines.append("> Solape pileta: de las ofertas que matchean el head, cuantas tienen skills "
                 "envenenadas (terminologia) pendientes de reproceso (deuda D1, candado F0.4b).")
    lines.append("> Impacto = blast por HEAD (cota superior/caution): un head de familia amplia "
                 "(ej. 'tecnico'=921) matchea mucho mas que la denominacion especifica que se cargaria. "
                 "El write real (P4) usa longest-match + rechazo por colision.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default=None, help="cursor por fecha ISO (solo correcciones nuevas)")
    ap.add_argument("--fecha", default="2026-07-03", help="etiqueta de fecha para los archivos de salida")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidatas = build(desde=args.desde, fecha=args.fecha)
    (OUT_DIR / f"candidatas_{args.fecha}.json").write_text(
        json.dumps(candidatas, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / f"bandeja_{args.fecha}.md").write_text(
        render_bandeja(candidatas, args.fecha), encoding="utf-8")

    cnt = Counter(c.get("estado") for c in candidatas)
    print(f"candidatas: {len(candidatas)} -> {dict(cnt)}")
    print(f"  exports/puente/candidatas_{args.fecha}.json")
    print(f"  exports/puente/bandeja_{args.fecha}.md")


if __name__ == "__main__":
    main()
