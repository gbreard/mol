"""
aplicar_candidata — escritura git-first del puente validacion->diccionario (C3).

Aplica candidatas CONFIRMADAS a config/sinonimos_argentinos_esco.json con esquema
post-G3 completo (esco_code OBLIGATORIO, validado contra el catalogo; sin resolucion
= rechazo ruidoso) + linaje por entrada. Respeta longest-match (rechazo ruidoso ante
colision, nunca pisa en silencio). Squash por sesion: N candidatas -> UN commit.

Git-first POR CONSTRUCCION: escribe el JSON local que el matcher lee via load_config
(fallback local); config_overrides queda fuera del circuito. NO pasa por el editor de
Sinonimos del dashboard (que stripea esco_code).

Invocado por el poller (COMMAND_MAP['aplicar_candidata']) o directo:
    python scripts/puente/aplicar_candidata.py --payload-json '{"session":"...","candidatas":[...]}'

payload: {session, candidatas: [{denominacion, esco_code, variantes?, notas?, linaje:{
    confirmado_por, fecha, id_oferta, correccion_fuente}}]}
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "database" / "embeddings" / "esco_occupations_full.json"
DICT_PATH = ROOT / "config" / "sinonimos_argentinos_esco.json"
MIRROR_PATH = ROOT / "fase3_dashboard" / "mol-dashboard" / "public" / "data" / "sinonimos_argentinos_esco.json"


def cargar_catalogo():
    occ = json.loads(CATALOG.read_text(encoding="utf-8"))["occupations"]
    return {o["esco_code"]: o for o in occ}


def _lower(s):
    """Normalizacion del matcher: lowercase, SIN strip de acentos (el matcher hace
    `v.lower() in titulo.lower()`, con acentos)."""
    return (s or "").lower().strip()


def validar(cand, code2occ):
    """Valida una candidata contra el catalogo. Devuelve (occ|None, motivo)."""
    denom = (cand.get("denominacion") or "").strip()
    esco = (cand.get("esco_code") or "").strip()
    if not denom:
        return None, "sin denominacion"
    if not esco:
        return None, "sin esco_code (rechazo ruidoso: nunca se degrada a label)"
    occ = code2occ.get(esco)
    if not occ:
        return None, f"esco_code '{esco}' NO resuelve al catalogo (rechazo ruidoso: nunca se inventa)"
    return occ, None


def colision_longest_match(denom_key, variantes, esco_code, ocupaciones):
    """Rechazo ruidoso ante colision longest-match: si el nuevo termino (o alguna
    variante) tiene relacion de substring con una entrada existente que resuelve a
    OTRO esco_code, uno sombrearia al otro en silencio. Devuelve motivo o None."""
    nuevos = [_lower(denom_key)] + [_lower(v) for v in (variantes or [])]
    for termino, config in ocupaciones.items():
        if termino.startswith("_"):
            continue
        code_exist = config.get("esco_code")
        exist_terms = [_lower(termino)] + [_lower(v) for v in (config.get("variantes") or [])]
        for nt in nuevos:
            for et in exist_terms:
                if not nt or not et:
                    continue
                if nt == et:
                    if code_exist and code_exist != esco_code:
                        return (f"colision EXACTA con '{termino}' ({code_exist} != {esco_code}) "
                                f"— rechazo ruidoso, no se pisa")
                    # exact + mismo codigo -> idempotencia (se maneja aparte)
                elif nt in et or et in nt:
                    if code_exist and code_exist != esco_code:
                        return (f"colision longest-match: '{nt}' <-> '{et}' de '{termino}' "
                                f"({code_exist} != {esco_code}) — sombreado silencioso, rechazo ruidoso")
    return None


def ya_existe(denom_key, esco_code, ocupaciones):
    """Idempotencia: la denominacion ya esta cargada. Devuelve 'noop' (mismo codigo),
    'conflicto' (otro codigo) o None (no existe)."""
    nk = _lower(denom_key)
    for termino, config in ocupaciones.items():
        if termino.startswith("_"):
            continue
        terms = [_lower(termino)] + [_lower(v) for v in (config.get("variantes") or [])]
        if nk in terms:
            return "noop" if config.get("esco_code") == esco_code else "conflicto"
    return None


def construir_entrada(cand, occ):
    esco = cand["esco_code"]
    variantes = list(dict.fromkeys([cand["denominacion"]] + list(cand.get("variantes") or [])))
    entrada = {
        "esco_code": esco,
        "isco_primario": occ["isco_code"],
        "esco_label": occ["esco_label"],
        "esco_uri": occ["uri"],
        "variantes": variantes,
        "_linaje": cand.get("linaje", {}),
    }
    if cand.get("notas"):
        entrada["nota"] = cand["notas"]
    return entrada


def aplicar(candidatas, session, commit=True, dict_path=DICT_PATH, mirror_path=MIRROR_PATH,
            code2occ=None, verbose=True):
    """Aplica una tanda (squash: un commit). Devuelve report {aplicadas, rechazadas, noop}."""
    code2occ = code2occ or cargar_catalogo()
    dict_path = Path(dict_path)
    dic = json.loads(dict_path.read_text(encoding="utf-8"))
    ocupaciones = dic["ocupaciones_titulo"]

    aplicadas, rechazadas, noop = [], [], []
    for cand in candidatas:
        denom = cand.get("denominacion")
        occ, motivo = validar(cand, code2occ)
        if occ is None:
            rechazadas.append({"denominacion": denom, "motivo": motivo})
            if verbose:
                print(f"[APLICAR] RECHAZO '{denom}': {motivo}")
            continue
        # idempotencia
        est = ya_existe(denom, cand["esco_code"], ocupaciones)
        if est == "noop":
            noop.append({"denominacion": denom, "motivo": "ya existe con el mismo esco_code"})
            if verbose:
                print(f"[APLICAR] NO-OP '{denom}': ya existe (mismo codigo)")
            continue
        if est == "conflicto":
            rechazadas.append({"denominacion": denom,
                               "motivo": "ya existe con OTRO esco_code (conflicto)"})
            if verbose:
                print(f"[APLICAR] RECHAZO '{denom}': ya existe con otro codigo")
            continue
        # colision longest-match
        col = colision_longest_match(denom, cand.get("variantes"), cand["esco_code"], ocupaciones)
        if col:
            rechazadas.append({"denominacion": denom, "motivo": col})
            if verbose:
                print(f"[APLICAR] RECHAZO '{denom}': {col}")
            continue
        # aplicar
        key = _lower(denom)
        ocupaciones[key] = construir_entrada(cand, occ)
        aplicadas.append({"denominacion": denom, "key": key, "esco_code": cand["esco_code"]})
        if verbose:
            print(f"[APLICAR] OK '{denom}' -> {cand['esco_code']} (key '{key}')")

    if aplicadas:
        dict_path.write_text(json.dumps(dic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # sync espejo de display: QUIRURGICO — inserta solo las claves aplicadas, no
        # sobrescribe el resto del espejo (que puede estar desfasado; PR #49 lo sincroniza
        # completo aparte). Asi el commit del puente solo muestra las entradas nuevas.
        if mirror_path and Path(mirror_path).exists():
            mir = json.loads(Path(mirror_path).read_text(encoding="utf-8"))
            for a in aplicadas:
                mir["ocupaciones_titulo"][a["key"]] = dic["ocupaciones_titulo"][a["key"]]
            Path(mirror_path).write_text(json.dumps(mir, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
        if commit:
            _commit(session, aplicadas, dict_path, mirror_path)

    return {"session": session, "aplicadas": aplicadas, "rechazadas": rechazadas, "noop": noop}


def _commit(session, aplicadas, dict_path, mirror_path):
    """Squash: un commit por sesion con la lista de candidatas."""
    files = [str(dict_path)]
    if mirror_path and Path(mirror_path).exists():
        files.append(str(mirror_path))
    subprocess.run(["git", "add"] + files, cwd=str(ROOT), check=True)
    lista = "\n".join(f"  - {a['denominacion']} -> {a['esco_code']}" for a in aplicadas)
    msg = (f"feat(spec-s1c-puente): aplicar candidatas sesion {session} ({len(aplicadas)})\n\n"
           f"{lista}\n\nEscritura git-first via aplicar_candidata (poller). "
           f"esco_code validado contra catalogo, linaje por entrada.\n\n"
           f"Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>")
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=str(ROOT), check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload-json", required=True)
    ap.add_argument("--no-commit", action="store_true")
    args = ap.parse_args()
    payload = json.loads(args.payload_json)
    rep = aplicar(payload["candidatas"], payload.get("session", "sin-sesion"),
                  commit=not args.no_commit)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    # exit 1 si hubo rechazos y ninguna aplicada (fallo total)
    if rep["rechazadas"] and not rep["aplicadas"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
