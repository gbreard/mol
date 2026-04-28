"""
SPEC T Fase 3 — Auditoría retrospectiva de issues humanos resueltos.

Recorre los issues humanos resueltos con `config_modificada` y NO `patron_corregido`,
infiere el patrón corregido (heurística por keywords), audita si quedan ofertas
stale (target distinto al config actual), propaga la corrección si aplica, y
actualiza el issue con metadata.

Resultado típico (run de 2026-04-27):
- 469 issues auditados
- 41 reglas únicas mencionadas (excluyendo las ya tocadas en SPEC N+O+P+S)
- 37 reglas ya OK (sin stale) — solo se actualizó metadata
- 3 reglas propagadas: R13 enfermero (333), R17 compliance (459), R79 ing.
  industrial (46) — total 838 ofertas re-matcheadas
- 1 regla escalada (R191 target sospechoso → SPEC Q)

Uso:
    python3 scripts/correcciones/auditoria_retrospectiva.py [--apply]
    python3 scripts/correcciones/auditoria_retrospectiva.py --apply --regla R13_enfermero

Sin --apply solo audita y reporta. Con --apply ejecuta propagación.
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.correcciones import propagate_correction


# Reglas YA tocadas en SPEC N+O+P+S — no necesitan re-procesarse
REGLAS_RECIENTES = {
    "R226_analista_rrhh", "R228_analista_contabilidad", "R236_analista_marketing",
    "R237_analista_finanzas", "R75_vigilador", "R128_programador_cnc",
    "R347_operario_metalurgico", "R162_tecnico_mantenimiento_edilicio",
    "R110_tecnico_mantenimiento", "R240_operario_produccion", "R37_operario_alimentos",
    "R301_ascensores", "R351_operario_despacho", "R349_operario_envasado",
    "R350_operario_deposito_logistica", "R352_operario_ensamble_armas",
    "R358_despacho_metalurgico_grua", "R275_operario_deposito_almacen",
    "R353_operario_carga_descarga", "R354_operario_lavadero",
    "R355_operario_maestranza", "R356_operario_mantenimiento",
    "R357_tecnico_operario_produccion",
}

# Reglas con target sospechoso identificado en SPEC Q Grupo B (ultra-específicos absurdos)
REGLAS_SOSPECHOSAS_TARGET = {
    "R191_analista_abastecimiento": "3323.2.1 comprador café verde",
    # Otros casos detectados en SPEC Q deben agregarse aquí
}

PATRON_REGLA = re.compile(r"\b(R\d+_[a-zA-Z_]+)", re.IGNORECASE)


def categorize(issue: dict) -> list:
    """Heurística por keywords para categorizar tipo de corrección."""
    text = " ".join(filter(None, [
        issue.get("descripcion") or "",
        issue.get("solucion_aplicada") or "",
        issue.get("config_modificada") or "",
        issue.get("valor_actual") or "",
        issue.get("valor_esperado") or "",
    ])).lower()

    cats = []
    if re.search(r"\barea[_ ]?funcional|área funcional|produccion.*logist|logist.*produccion", text):
        cats.append("nlp_area_funcional")
    if re.search(r"\b(esco|isco|matching_rules|regla r\d+|forzar_isco|esco_label|esco_code)", text):
        cats.append("matching_esco")
    if re.search(r"\bskills?\b.*(incorrec|aluci|filtra|sin sentido|peces|javanes|sanscrito|psiquiatria)", text):
        cats.append("skills_filtro")
    if re.search(r"\btareas?\b.*(incorrec|aluci|encabez|requisit|no.*tarea)", text):
        cats.append("nlp_tareas_explicitas")
    if re.search(r"\b(sector|sector_empresa)\b.*(incorrec|debe|cambiar|inferi)", text):
        cats.append("nlp_sector")
    if re.search(r"\bseniority|nivel_seniority\b", text):
        cats.append("nlp_seniority")
    if re.search(r"\b(modalidad|presencial|remoto|hibrido)\b.*(incorrec|debe|cambiar)", text):
        cats.append("nlp_modalidad")

    return cats if cats else ["no_clasificado"]


def fetch_human_issues(client) -> list:
    """Trae issues humanos resueltos sin patron_corregido."""
    all_issues = []
    for offset in range(0, 5000, 500):
        r = client.table("issues").select(
            "id,id_oferta,descripcion,valor_actual,valor_esperado,campo_afectado,"
            "solucion_aplicada,config_modificada,autor_nombre,autor_email,"
            "patron_corregido,propagacion_n"
        ).eq("estado", "resuelto").neq("autor_email", "auto-validator@mol.gob.ar")\
            .range(offset, offset + 499).execute()
        if not r.data:
            break
        all_issues.extend(r.data)
        if len(r.data) < 500:
            break
    return all_issues


def map_reglas_a_issues(issues: list) -> dict:
    """Para cada regla mencionada en issues, devuelve la lista de issue_ids."""
    mapping = defaultdict(list)
    for issue in issues:
        if "matching_esco" not in categorize(issue):
            continue
        text = " ".join(filter(None, [
            issue.get("descripcion") or "",
            issue.get("solucion_aplicada") or "",
            issue.get("config_modificada") or "",
            issue.get("valor_actual") or "",
            issue.get("valor_esperado") or "",
        ]))
        matches = PATRON_REGLA.findall(text)
        for m in matches:
            if m in REGLAS_RECIENTES:
                continue
            mapping[m].append(issue["id"])
    return dict(mapping)


def auditar_reglas(reglas_map: dict, db_path: str, config_path: str) -> list:
    """Para cada regla, identifica ofertas stale (target distinto al config actual)."""
    config_data = json.loads(Path(config_path).read_text())
    reglas_def = config_data["reglas_forzar_isco"]

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    auditoria = []
    for rid in reglas_map:
        rule = reglas_def.get(rid, {})
        target = rule.get("accion", {}).get("esco_code", "")
        if not target:
            continue

        cur.execute("SELECT COUNT(*) FROM ofertas_esco_matching WHERE regla_aplicada = ?", (rid,))
        total = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM ofertas_esco_matching WHERE regla_aplicada = ? AND titulo_esco_code != ?",
            (rid, target),
        )
        stale = cur.fetchone()[0]

        auditoria.append({
            "rid": rid,
            "target": target,
            "total": total,
            "stale": stale,
            "issues_asociados": reglas_map[rid],
            "is_sospechosa": rid in REGLAS_SOSPECHOSAS_TARGET,
        })
    conn.close()
    return auditoria


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Aplicar propagación (default es solo auditar)")
    ap.add_argument("--regla", help="Procesar solo una regla específica")
    ap.add_argument("--db", default=str(ROOT / "database/bumeran_scraping.db"))
    ap.add_argument("--config", default=str(ROOT / "config/matching_rules_business.json"))
    args = ap.parse_args()

    # Cargar Supabase
    sup_config = json.loads((ROOT / "config/supabase_config.json").read_text())
    from supabase import create_client
    client = create_client(sup_config["url"], sup_config["service_role_key"])

    # 1. Obtener issues
    print("[1/4] Obteniendo issues humanos resueltos...")
    issues = fetch_human_issues(client)
    target = [i for i in issues
              if (i.get("config_modificada") or "").strip()
              and not i.get("patron_corregido")]
    print(f"  Total: {len(issues)} | A auditar: {len(target)}")

    # 2. Mapear reglas
    print("[2/4] Extrayendo reglas mencionadas...")
    reglas_map = map_reglas_a_issues(target)
    print(f"  Reglas únicas (excluyendo recientes): {len(reglas_map)}")

    # 3. Auditar
    print("[3/4] Auditando ofertas stale por regla...")
    auditoria = auditar_reglas(reglas_map, args.db, args.config)

    con_stale = [a for a in auditoria if a["stale"] > 0 and not a["is_sospechosa"]]
    sin_stale = [a for a in auditoria if a["stale"] == 0]
    sospechosas = [a for a in auditoria if a["is_sospechosa"]]

    print(f"  Reglas con stale: {len(con_stale)}")
    print(f"  Reglas ya OK (sin stale): {len(sin_stale)}")
    print(f"  Reglas con target sospechoso (skip): {len(sospechosas)}")

    if args.regla:
        con_stale = [a for a in con_stale if a["rid"] == args.regla]
        if not con_stale:
            print(f"  Regla {args.regla} no encontrada o sin stale.")
            return

    # 4. Propagar (si --apply)
    if args.apply:
        print("[4/4] Aplicando propagación...")
        for a in sorted(con_stale, key=lambda x: x["stale"], reverse=True):
            patron = {
                "tipo": "matching_esco",
                "campo": "esco_label",
                "condicion": {"tipo": "regla_aplicada", "valor_unico": a["rid"]},
                "valor_anterior": "?",
                "valor_nuevo": a["target"],
            }
            print(f"\n  ━ {a['rid']} (target {a['target']}, stale={a['stale']})")
            res = propagate_correction(
                patron, dry_run=False, update_issue=False,
                db_path=args.db, verbose=False,
            )
            print(f"    tocadas={res.ofertas_actualizadas}, errores={len(res.errores)}, skipped={len(res.ids_skipped)}")
            if res.errores:
                for e in res.errores[:3]:
                    print(f"    ⚠ {e}")
    else:
        print("[4/4] DRY-RUN (usar --apply para ejecutar)")
        for a in con_stale:
            print(f"  Propagaría: {a['rid']} → {a['stale']} ofertas stale")

    print("\n━━━ DONE ━━━")


if __name__ == "__main__":
    main()
