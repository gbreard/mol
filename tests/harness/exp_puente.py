#!/usr/bin/env python3
"""SPEC S1C-F0.5-exp · Corrida 1 — experimento puente (solo esco_argentino).

Mide si inyectar las aristas argentinas curadas (esco_argentino, 44 ocup / 291
skills) a la decisión de ocupación mueve la precisión del matcher, contra el
baseline fechado de F0.5-build.

ENCUADRE (acordado con Gerardo 2026-06-17): NO es veredicto sobre si las aristas
corrigen errores — solo 4 de los 15 false caen en cobertura. SÍ responde con
solidez: (1) ¿el mecanismo de inyección funciona técnicamente? (2) ¿rompe alguno
de los 31 true afectables? + lupa sobre los 4 false (fuerza del cambio, arista
ausente vs boost débil vs regla que gana).

Read-only: matcher en memoria, nunca match_and_persist, nunca escribe en
producción. Config A = baseline congelado (no se recalcula la decisión). Config B
= grafo skill→ocupación augmentado con las aristas argentinas (mismo shape y peso
'essential' que las aristas EU de esco_associations). El grafo de A nunca se muta:
B usa una copia.
"""

import copy
import json
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HARNESS_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
SUPABASE_CFG = PROJECT_ROOT / "config" / "supabase_config.json"

PRODUCTION_TABLES = ["ofertas_esco_matching", "ofertas_esco_skills_detalle", "ofertas_nlp"]

# Peso de las aristas argentinas inyectadas. Espejo de essential_weight de las
# aristas EU (SkillsBasedMatcher.essential_weight = 2.0): las aristas argentinas
# son asociaciones curadas y validadas por Cyn -> se les da la fuerza máxima fair.
# Si ni a 2.0 mueven la decisión, el diagnóstico es limpio.
ARG_EDGE_WEIGHT = 2.0


def _isco4(code):
    if not code:
        return None
    c = str(code).lstrip("C")
    return c[:4] if len(c) >= 4 else (c or None)


def _table_counts(conn):
    out = {}
    for t in PRODUCTION_TABLES:
        try:
            out[t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        except sqlite3.Error:
            out[t] = -1
    return out


def load_esco_argentino():
    """44 ocupaciones argentinas curadas. Devuelve:
    - edges: skill_uri -> list[(occ_uri, weight)]  (las aristas a inyectar)
    - occ_skills: occ_uri -> set(skill_uri)        (para diagnóstico de firing)
    - occ_uris: set de las 44 ocupaciones cubiertas
    """
    cfg = json.loads(SUPABASE_CFG.read_text())
    from supabase import create_client

    client = create_client(cfg["url"], cfg["service_role_key"])
    rows = (
        client.table("esco_argentino")
        .select("esco_occupation_uri,esco_occupation_label,skills_consolidadas")
        .execute()
        .data
        or []
    )
    edges = {}
    occ_skills = {}
    occ_uris = set()
    n_skills = 0
    for r in rows:
        occ = r.get("esco_occupation_uri")
        if not occ:
            continue
        occ_uris.add(occ)
        occ_skills.setdefault(occ, set())
        for s in r.get("skills_consolidadas") or []:
            suri = s.get("uri") or s.get("esco_uri")
            if not suri:
                continue
            edges.setdefault(suri, []).append((occ, ARG_EDGE_WEIGHT))
            occ_skills[occ].add(suri)
            n_skills += 1
    return edges, occ_skills, occ_uris, len(rows), n_skills


def augment_graph(base_graph, arg_edges):
    """Copia el grafo skill->occ y le agrega las aristas argentinas. NO muta base."""
    aug = {k: list(v) for k, v in base_graph.items()}
    for suri, occ_weights in arg_edges.items():
        aug.setdefault(suri, [])
        existing = {ow[0] for ow in aug[suri]}
        for occ, w in occ_weights:
            if occ not in existing:  # no duplicar si la arista EU ya existe
                aug[suri].append((occ, w))
    return aug


def main(fecha):
    t0 = time.time()
    sys.path.insert(0, str(HARNESS_DIR))
    sys.path.insert(0, str(PROJECT_ROOT / "database"))

    from ground_truth import load_ground_truth_default  # noqa: E402
    from match_ofertas_v3 import MatcherV3  # noqa: E402

    # Ground truth + baseline congelado (config A)
    casos, conn = load_ground_truth_default(fecha)
    baseline = json.loads((HARNESS_DIR / f"baseline_{fecha}.json").read_text())
    base_by_id = {c["id_oferta"]: c for c in baseline["casos"]}

    conn.row_factory = sqlite3.Row
    cols = [r[1] for r in conn.execute("PRAGMA table_info(ofertas_nlp)")]

    counts_before = _table_counts(conn)

    print(f"[init] cargando matcher... ({time.time()-t0:.0f}s)", flush=True)
    matcher = MatcherV3(db_conn=conn, verbose=False)
    sm = matcher.skills_matcher
    base_graph = sm.skill_to_occupations  # referencia al cache de clase — NO mutar
    print(f"[init] matcher listo ({time.time()-t0:.0f}s)", flush=True)

    arg_edges, occ_skills, occ_uris, n_occ, n_arg_skills = load_esco_argentino()
    aug_graph = augment_graph(base_graph, arg_edges)
    print(
        f"[init] esco_argentino: {n_occ} ocupaciones, {n_arg_skills} aristas "
        f"skill->occ inyectadas ({time.time()-t0:.0f}s)",
        flush=True,
    )

    real_extract = sm  # placeholder; capture set per-case below
    real_extract_fn = matcher.skills_extractor.extract_skills_dual

    resultados = []
    # ids con esperado-ESCO en las 44 -> lupa (los 4 false de ganancia medible)
    lupa_ids = set()
    for c in baseline["casos"]:
        if c["es_error_gold"] and c.get("esco_uri_esperado") in occ_uris:
            lupa_ids.add(c["id_oferta"])

    for caso in casos:
        oid = caso.id_oferta
        b = base_by_id.get(oid)
        if b is None:
            continue
        row = conn.execute("SELECT * FROM ofertas_nlp WHERE id_oferta=?", (oid,)).fetchone()
        if row is None:
            continue
        nlp = {k: row[k] for k in cols}

        # --- Config A: reusar decisión congelada del baseline; capturar skills
        #     extraídas para diagnóstico (re-corremos A en memoria solo para eso).
        captured = {}

        def capturing(*a, **k):
            r = real_extract_fn(*a, **k)
            captured["dual"] = r
            return r

        matcher.skills_extractor.extract_skills_dual = capturing
        res_a = matcher.match(nlp)
        matcher.skills_extractor.extract_skills_dual = real_extract_fn

        a_isco4 = _isco4(res_a.isco_code)
        a_uri = res_a.esco_uri
        # check de determinismo vs baseline congelado
        determinista = (a_isco4 == b["isco4_matcher"]) and (a_uri == b["esco_uri_matcher"])

        skills_final = (captured.get("dual") or {}).get("skills_final") or []
        offer_skill_uris = {s.get("skill_uri") for s in skills_final if s.get("skill_uri")}

        # --- Config B: grafo augmentado, mismo input
        sm.skill_to_occupations = aug_graph
        res_b = matcher.match(nlp)
        sm.skill_to_occupations = base_graph  # restaurar SIEMPRE

        b_isco4 = _isco4(res_b.isco_code)
        b_uri = res_b.esco_uri

        rec = {
            "id_oferta": oid,
            "titulo": nlp.get("titulo_limpio") or nlp.get("titulo"),
            "es_error_gold": b["es_error_gold"],
            "esco_ok_gold": b["esco_ok_gold"],
            # esperado (false=explícito; true=target implícito = salida A)
            "isco4_esperado": b.get("isco4_esperado") if b["es_error_gold"] else (b.get("target_implicito") or {}).get("isco4"),
            "esco_uri_esperado": b.get("esco_uri_esperado") if b["es_error_gold"] else (b.get("target_implicito") or {}).get("esco_uri"),
            # A (congelado) y B
            "a_isco4": a_isco4, "a_uri": a_uri, "a_metodo": res_a.metodo,
            "a_decision": (res_a.metadata or {}).get("decision_metodo"),
            "a_regla": (res_a.metadata or {}).get("regla_aplicada"),
            "a_score": round(res_a.score, 4) if res_a.score is not None else None,
            "b_isco4": b_isco4, "b_uri": b_uri, "b_metodo": res_b.metodo,
            "b_decision": (res_b.metadata or {}).get("decision_metodo"),
            "b_regla": (res_b.metadata or {}).get("regla_aplicada"),
            "b_score": round(res_b.score, 4) if res_b.score is not None else None,
            "cambio_isco4": a_isco4 != b_isco4,
            "cambio_uri": a_uri != b_uri,
            "determinista_vs_baseline": determinista,
        }

        # --- Lupa sobre los 4 false de ganancia medible ---
        if oid in lupa_ids:
            occ_esp = b["esco_uri_esperado"]
            arg_sk = occ_skills.get(occ_esp, set())
            firing = offer_skill_uris & arg_sk  # aristas argentinas que SÍ disparan
            # score del candidato esperado en A vs B (canal skills->occ)
            cand_a = sm.match(skills_final, top_n=50)
            score_a_esp = next((c["score"] for c in cand_a if c["occupation_uri"] == occ_esp), 0.0)
            rank_a_esp = next((i for i, c in enumerate(cand_a) if c["occupation_uri"] == occ_esp), None)
            sm.skill_to_occupations = aug_graph
            cand_b = sm.match(skills_final, top_n=50)
            sm.skill_to_occupations = base_graph
            score_b_esp = next((c["score"] for c in cand_b if c["occupation_uri"] == occ_esp), 0.0)
            rank_b_esp = next((i for i, c in enumerate(cand_b) if c["occupation_uri"] == occ_esp), None)
            # La decisión la gana un canal RÍO ARRIBA del semántico (regla de
            # negocio o diccionario argentino) si el método final empieza con esos
            # prefijos o hay una regla aplicada. En ese caso el boost al canal
            # skills→ocupación es MOOT (no compite), aunque haya disparado fuerte.
            b_metodo_str = res_b.metodo or ""
            decide_rio_arriba = (
                b_metodo_str.startswith("regla_negocio")
                or b_metodo_str.startswith("diccionario_argentino")
                or bool((res_b.metadata or {}).get("regla_aplicada"))
            )
            canal_decision = (
                "regla_negocio" if b_metodo_str.startswith("regla_negocio") or (res_b.metadata or {}).get("regla_aplicada")
                else "diccionario_argentino" if b_metodo_str.startswith("diccionario_argentino")
                else "semantico"
            )
            rec["lupa"] = {
                "ocupacion_esperada_uri": occ_esp,
                "n_aristas_argentinas_ocup": len(arg_sk),
                "n_skills_oferta": len(offer_skill_uris),
                "aristas_que_disparan": len(firing),
                "arista_presente": len(firing) > 0,
                "cand_esperado_score_A": round(score_a_esp, 4),
                "cand_esperado_score_B": round(score_b_esp, 4),
                "delta_score_canal_skills": round(score_b_esp - score_a_esp, 4),
                "cand_esperado_rank_A": rank_a_esp,
                "cand_esperado_rank_B": rank_b_esp,
                "canal_que_decide": canal_decision,
                "decision_rio_arriba_del_semantico": decide_rio_arriba,
            }

        resultados.append(rec)
        if oid in lupa_ids or rec["cambio_isco4"] or rec["cambio_uri"]:
            print(
                f"{oid} false={rec['es_error_gold']} A={a_isco4}/{(a_uri or '')[-12:]} "
                f"B={b_isco4}/{(b_uri or '')[-12:]} cambioISCO={rec['cambio_isco4']} "
                f"cambioURI={rec['cambio_uri']} ({time.time()-t0:.0f}s)",
                flush=True,
            )

    counts_after = _table_counts(conn)
    if counts_before != counts_after:
        raise RuntimeError(
            f"VIOLACIÓN READ-ONLY: conteos de producción cambiaron.\n"
            f"  antes:  {counts_before}\n  después: {counts_after}"
        )

    out = build_report(resultados, occ_uris, fecha, n_occ, n_arg_skills)
    (HARNESS_DIR / f"exp_puente_esco_argentino_{fecha}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    (HARNESS_DIR / f"exp_puente_esco_argentino_{fecha}.md").write_text(render_md(out))
    print(f"\n[done] {time.time()-t0:.0f}s — resultado en tests/harness/exp_puente_esco_argentino_{fecha}.json")
    conn.close()
    return out


def _transition(casos, nivel):
    """Matriz de transición A->B a un nivel ('isco4' o 'uri').
    bien = coincide con esperado. Para true cases (target implícito = A),
    A siempre es 'bien'. Devuelve conteos + listas de regresiones/ganancias."""
    key_exp = "isco4_esperado" if nivel == "isco4" else "esco_uri_esperado"
    key_a = "a_isco4" if nivel == "isco4" else "a_uri"
    key_b = "b_isco4" if nivel == "isco4" else "b_uri"
    cuad = {"mal_bien": 0, "bien_mal": 0, "bien_bien": 0, "mal_mal": 0, "sin_esperado": 0}
    regresiones, ganancias = [], []
    for c in casos:
        exp = c.get(key_exp)
        if not exp:
            cuad["sin_esperado"] += 1
            continue
        a_ok = c[key_a] == exp
        b_ok = c[key_b] == exp
        if not a_ok and b_ok:
            cuad["mal_bien"] += 1
            ganancias.append(c)
        elif a_ok and not b_ok:
            cuad["bien_mal"] += 1
            regresiones.append(c)
        elif a_ok and b_ok:
            cuad["bien_bien"] += 1
        else:
            cuad["mal_mal"] += 1
    cuad["ganancia_neta"] = cuad["mal_bien"] - cuad["bien_mal"]
    return cuad, regresiones, ganancias


def build_report(resultados, occ_uris, fecha, n_occ, n_arg_skills):
    n = len(resultados)
    n_cambio_isco4 = sum(1 for c in resultados if c["cambio_isco4"])
    n_cambio_uri = sum(1 for c in resultados if c["cambio_uri"])
    nd = [c for c in resultados if not c["determinista_vs_baseline"]]

    trans_isco4, reg_isco4, gan_isco4 = _transition(resultados, "isco4")
    trans_uri, reg_uri, gan_uri = _transition(resultados, "uri")
    reg_ids = {c["id_oferta"] for c in reg_isco4} | {c["id_oferta"] for c in reg_uri}
    nd_en_regresiones = [c["id_oferta"] for c in nd if c["id_oferta"] in reg_ids]

    # Afectables (true) regresión: true cases cuyo B != A
    true_afect = [c for c in resultados if not c["es_error_gold"] and c["a_uri"] in occ_uris]
    true_rotos = [c for c in true_afect if c["cambio_uri"] or c["cambio_isco4"]]

    # Desglose por método de las que cambiaron (a nivel URI)
    metodo_cambios = {}
    for c in resultados:
        if c["cambio_uri"] or c["cambio_isco4"]:
            k = c["b_decision"] or c["b_metodo"] or "?"
            metodo_cambios[k] = metodo_cambios.get(k, 0) + 1

    lupa = [c["lupa"] | {"id_oferta": c["id_oferta"], "titulo": c["titulo"],
                          "cambio_isco4": c["cambio_isco4"], "cambio_uri": c["cambio_uri"]}
            for c in resultados if "lupa" in c]

    def slim(cs):
        return [{"id_oferta": c["id_oferta"], "titulo": c["titulo"],
                 "esperado_isco4": c["isco4_esperado"], "esperado_uri": c["esco_uri_esperado"],
                 "a_isco4": c["a_isco4"], "b_isco4": c["b_isco4"],
                 "a_uri": c["a_uri"], "b_uri": c["b_uri"],
                 "a_metodo": c["a_decision"], "b_metodo": c["b_decision"],
                 "es_error_gold": c["es_error_gold"]} for c in cs]

    return {
        "spec": "S1C-F0.5-exp corrida 1",
        "fecha": fecha,
        "encuadre": "PRUEBA DE PLOMERÍA del mecanismo + MONITOR DE REGRESIÓN. "
                    "NO es veredicto sobre si las aristas corrigen errores (solo 4 de 15 false en cobertura).",
        "overlay": {"ocupaciones": n_occ, "aristas_skill_occ_inyectadas": n_arg_skills,
                    "peso_arista": ARG_EDGE_WEIGHT},
        "n_casos": n,
        "mecanismo_funciona": {
            "n_casos_que_cambian_isco4": n_cambio_isco4,
            "n_casos_que_cambian_uri": n_cambio_uri,
            "interpretacion": "Si >0, la inyección altera decisiones -> el mecanismo opera técnicamente.",
        },
        "determinismo_A_vs_baseline": {
            "n_no_determinista": len(nd),
            "ok": len(nd) == 0,
            "ids_no_deterministas": [{"id_oferta": c["id_oferta"], "titulo": c["titulo"],
                                       "a_isco4_rerun": c["a_isco4"], "a_metodo": c["a_metodo"],
                                       "a_score": c["a_score"]} for c in nd],
            "nd_que_son_regresiones": nd_en_regresiones,
            "nota": "Casos donde el re-run de A difiere del baseline congelado (inestabilidad "
                    "de desempate en el semántico, no causada por el overlay). Las regresiones "
                    "reportadas NO incluyen estos casos salvo que figuren en nd_que_son_regresiones.",
        },
        "regresion_true_afectables": {
            "n_true_afectables": len(true_afect),
            "n_rotos": len(true_rotos),
            "rotos": slim(true_rotos),
        },
        "matriz_transicion": {
            "isco4": trans_isco4,
            "esco_uri": trans_uri,
        },
        "regresiones_caso_por_caso": {
            "isco4": slim(reg_isco4),
            "esco_uri": slim(reg_uri),
        },
        "ganancias_caso_por_caso": {
            "isco4": slim(gan_isco4),
            "esco_uri": slim(gan_uri),
        },
        "desglose_metodo_de_las_que_cambiaron": metodo_cambios,
        "lupa_4_false": lupa,
        "casos": resultados,
    }


def render_md(o):
    L = []
    L.append(f"# Experimento puente · corrida 1 (esco_argentino) — {o['fecha']}\n")
    L.append(f"> {o['encuadre']}\n")
    ov = o["overlay"]
    L.append(f"**Overlay:** {ov['ocupaciones']} ocupaciones, {ov['aristas_skill_occ_inyectadas']} "
             f"aristas skill→ocupación inyectadas (peso {ov['peso_arista']}, espejo de essential EU). "
             f"{o['n_casos']} casos.\n")

    mf = o["mecanismo_funciona"]
    L.append("## 1. ¿El mecanismo de inyección funciona?\n")
    L.append(f"- Casos que cambian ISCO-4: **{mf['n_casos_que_cambian_isco4']}**")
    L.append(f"- Casos que cambian ESCO-URI: **{mf['n_casos_que_cambian_uri']}**")
    det = o["determinismo_A_vs_baseline"]
    L.append(f"- Determinismo A vs baseline congelado: {'OK' if det['ok'] else 'CAVEAT (%d difieren)' % det['n_no_determinista']}")
    for c in det.get("ids_no_deterministas", []):
        L.append(f"  - `{c['id_oferta']}` {c['titulo']}: A re-run isco4={c['a_isco4_rerun']} "
                 f"({c['a_metodo']}, score {c['a_score']}) ≠ baseline — desempate inestable en el semántico, no es el overlay")
    if not det["ok"]:
        L.append(f"  - ¿alguno es de las regresiones? {det['nd_que_son_regresiones'] or 'NO — las 4 regresiones son cambios A→B limpios'}")
    L.append("")

    rt = o["regresion_true_afectables"]
    L.append("## 2. ¿Rompe alguno de los true afectables?\n")
    L.append(f"- True afectables (match-A en las 44): **{rt['n_true_afectables']}**")
    L.append(f"- Rotos por el overlay (bien→mal): **{rt['n_rotos']}**")
    for r in rt["rotos"]:
        L.append(f"  - `{r['id_oferta']}` {r['titulo']}: A={r['a_isco4']}/{(r['a_uri'] or '')[-12:]} → "
                 f"B={r['b_isco4']}/{(r['b_uri'] or '')[-12:]} ({r['b_metodo']})")
    L.append("")

    L.append("## 3. Matriz de transición A→B (doble nivel)\n")
    for niv in ("isco4", "esco_uri"):
        m = o["matriz_transicion"][niv]
        L.append(f"**{niv}** — mal→bien {m['mal_bien']} · bien→mal {m['bien_mal']} · "
                 f"bien→bien {m['bien_bien']} · mal→mal {m['mal_mal']} · "
                 f"sin esperado {m['sin_esperado']} · **ganancia neta {m['ganancia_neta']}**")
    L.append("")
    for niv in ("isco4", "esco_uri"):
        regs = o["regresiones_caso_por_caso"][niv]
        if regs:
            L.append(f"### Regresiones {niv}")
            for r in regs:
                L.append(f"- `{r['id_oferta']}` {r['titulo']}: esperado {r['esperado_isco4']} | "
                         f"A={r['a_isco4']} → B={r['b_isco4']} ({r['b_metodo']})")
            L.append("")

    L.append("## 4. Desglose por método de las que cambiaron\n")
    for k, v in sorted(o["desglose_metodo_de_las_que_cambiaron"].items(), key=lambda x: -x[1]):
        L.append(f"- {k}: {v}")
    L.append("")

    L.append("## 5. Lupa sobre los 4 false de ganancia medible\n")
    L.append("Por caso: ¿la arista argentina estaba en la oferta (disparó)? ¿con qué fuerza cambió el "
             "score del candidato esperado? ¿la decisión la gana una regla (boost moot)?\n")
    for x in o["lupa_4_false"]:
        L.append(f"### `{x['id_oferta']}` {x['titulo']}")
        L.append(f"- Aristas argentinas de la ocup esperada: {x['n_aristas_argentinas_ocup']} · "
                 f"skills de la oferta: {x['n_skills_oferta']} · **disparan: {x['aristas_que_disparan']}** "
                 f"({'ARISTA PRESENTE' if x['arista_presente'] else 'ARISTA AUSENTE'})")
        L.append(f"- Score candidato esperado (canal skills→occ): A={x['cand_esperado_score_A']} → "
                 f"B={x['cand_esperado_score_B']} (Δ {x['delta_score_canal_skills']}); "
                 f"rank A={x['cand_esperado_rank_A']} → B={x['cand_esperado_rank_B']}")
        L.append(f"- Canal que decide la ocupación: **{x['canal_que_decide']}** "
                 f"({'río arriba del semántico → boost MOOT' if x['decision_rio_arriba_del_semantico'] else 'es el semántico'})")
        L.append(f"- ¿Cambió la decisión? ISCO-4={x['cambio_isco4']} · URI={x['cambio_uri']}")
        # diagnóstico
        if not x["cambio_uri"] and not x["cambio_isco4"]:
            if x["decision_rio_arriba_del_semantico"]:
                if x["arista_presente"] and x["delta_score_canal_skills"] > 0:
                    diag = (f"NO MOVIÓ aunque la arista disparó y subió el score del candidato esperado "
                            f"(Δ{x['delta_score_canal_skills']}, rank {x['cand_esperado_rank_A']}→{x['cand_esperado_rank_B']}): "
                            f"la decisión la gana {x['canal_que_decide']}, RÍO ARRIBA del semántico. El boost es MOOT, no débil.")
                else:
                    diag = (f"NO MOVIÓ: la decisión la gana {x['canal_que_decide']} (río arriba del semántico) "
                            f"y además la arista {'no estaba' if not x['arista_presente'] else 'disparó pero no compite'}.")
            elif not x["arista_presente"]:
                diag = "NO MOVIÓ porque la arista no estaba en la oferta (la ocup esperada no recibió señal argentina)."
            elif x["delta_score_canal_skills"] > 0:
                diag = "NO MOVIÓ aunque la arista disparó y subió el score: el boost fue demasiado débil para superar al candidato vigente en el semántico."
            else:
                diag = "NO MOVIÓ: arista presente pero sin efecto medible en el score."
            L.append(f"- **Diagnóstico:** {diag}")
        L.append("")

    return "\n".join(L)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--fecha", required=True)
    main(p.parse_args().fecha)
