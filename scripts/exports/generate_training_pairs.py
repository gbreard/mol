"""
Genera pares de entrenamiento para fine-tuning de clasificación ESCO
a partir de issues resueltos en Supabase.

Uso:
    python scripts/exports/generate_training_pairs.py
    python scripts/exports/generate_training_pairs.py --since 2026-02-01
    python scripts/exports/generate_training_pairs.py --stats

Cada par contiene:
    - input: título, descripción, tareas, sector (datos de la oferta)
    - clasificacion_incorrecta: lo que el sistema asignó mal
    - clasificacion_correcta: lo que quedó después de la corrección
    - justificacion_humana: razonamiento del experto (oro para CoT fine-tuning)

Enfoques de fine-tuning soportados:
    - Supervisado: input → clasificacion_correcta
    - DPO/RLHF: input → (correcta=chosen, incorrecta=rejected)
    - Chain-of-Thought: input + justificacion_humana → clasificacion_correcta
"""

import json
import sqlite3
import argparse
import sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE / "database" / "bumeran_scraping.db"
CONFIG_PATH = BASE / "config" / "supabase_config.json"
OUTPUT_PATH = BASE / "config" / "training_pairs.json"


def load_supabase_client():
    from supabase import create_client
    config = json.load(open(CONFIG_PATH))
    return create_client(config["url"], config["service_role_key"])


def fetch_resolved_issues(client, since=None):
    query = client.table("issues").select("*").eq("estado", "resuelto")
    if since:
        query = query.gte("resuelto_at", since)
    result = query.order("resuelto_at", desc=False).execute()
    return result.data


def build_training_pair(issue, conn):
    oid = issue["id_oferta"]

    oferta = conn.execute(
        "SELECT titulo, descripcion, empresa FROM ofertas WHERE id_oferta = ?",
        (oid,),
    ).fetchone()

    nlp = conn.execute(
        """SELECT titulo_limpio, tareas_explicitas, area_funcional,
                  nivel_seniority, sector_empresa, modalidad, provincia
           FROM ofertas_nlp WHERE id_oferta = ?""",
        (oid,),
    ).fetchone()

    matching = conn.execute(
        """SELECT isco_code, isco_label, esco_occupation_label, esco_occupation_uri,
                  occupation_match_score, occupation_match_method, regla_aplicada,
                  isco_semantico, score_semantico, decision_metodo
           FROM ofertas_esco_matching WHERE id_oferta = ?""",
        (oid,),
    ).fetchone()

    # Primer matching histórico (el incorrecto)
    hist = conn.execute(
        """SELECT isco_code, isco_label, match_method, score, created_at
           FROM ofertas_matching_history
           WHERE id_oferta = ?
           ORDER BY created_at ASC LIMIT 1""",
        (oid,),
    ).fetchone()

    # Si no hay historial, no podemos armar el par before/after
    if not oferta and not nlp:
        return None

    pair = {
        "id_oferta": oid,
        "issue_id": issue["id"],
        "autor": issue.get("autor_nombre", "unknown"),
        "issue_tipo": issue.get("tipo"),
        "issue_titulo": issue["titulo"],
        "resuelto_at": issue.get("resuelto_at"),
        "input": {
            "titulo_original": oferta["titulo"] if oferta else None,
            "titulo_limpio": nlp["titulo_limpio"] if nlp else None,
            "empresa": oferta["empresa"] if oferta else None,
            "descripcion": oferta["descripcion"] if oferta else None,
            "tareas_explicitas": nlp["tareas_explicitas"] if nlp else None,
            "area_funcional": nlp["area_funcional"] if nlp else None,
            "nivel_seniority": nlp["nivel_seniority"] if nlp else None,
            "sector_empresa": nlp["sector_empresa"] if nlp else None,
            "modalidad": nlp["modalidad"] if nlp else None,
            "provincia": nlp["provincia"] if nlp else None,
        },
        "clasificacion_incorrecta": (
            {
                "isco_code": hist["isco_code"],
                "isco_label": hist["isco_label"],
                "score": hist["score"],
                "metodo": hist["match_method"],
            }
            if hist
            else None
        ),
        "clasificacion_correcta": (
            {
                "isco_code": matching["isco_code"],
                "isco_label": matching["isco_label"],
                "esco_label": matching["esco_occupation_label"],
                "esco_uri": matching["esco_occupation_uri"],
                "score": matching["occupation_match_score"],
                "metodo": matching["occupation_match_method"],
                "regla": matching["regla_aplicada"],
                "decision_metodo": matching["decision_metodo"],
                "isco_semantico": matching["isco_semantico"],
                "score_semantico": matching["score_semantico"],
            }
            if matching
            else None
        ),
        "justificacion_humana": issue["descripcion"],
        "correccion": {
            "solucion_aplicada": issue.get("solucion_aplicada"),
            "config_modificada": issue.get("config_modificada"),
        },
    }

    return pair


def generate(since=None):
    client = load_supabase_client()
    issues = fetch_resolved_issues(client, since)

    if not issues:
        print("No hay issues resueltos" + (f" desde {since}" if since else ""))
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    pairs = []
    skipped = 0
    for issue in issues:
        pair = build_training_pair(issue, conn)
        if pair:
            pairs.append(pair)
        else:
            skipped += 1

    conn.close()

    # Deduplicar por id_oferta (mismo oferta puede tener 2 issues)
    seen = {}
    unique_pairs = []
    for p in pairs:
        key = p["id_oferta"]
        if key not in seen:
            seen[key] = p
            unique_pairs.append(p)
        else:
            # Mergear justificaciones si hay múltiples issues para la misma oferta
            existing = seen[key]
            if p["justificacion_humana"] != existing["justificacion_humana"]:
                existing["justificacion_humana"] += "\n---\n" + p["justificacion_humana"]

    return unique_pairs


def save(pairs):
    # Cargar existente si hay
    existing_pairs = []
    existing_ids = set()
    if OUTPUT_PATH.exists():
        try:
            data = json.load(open(OUTPUT_PATH, encoding='utf-8'))
            existing_pairs = data.get("pares", [])
            existing_ids = {p["id_oferta"] for p in existing_pairs}
        except (json.JSONDecodeError, KeyError):
            pass

    # Agregar nuevos (no duplicar)
    new_count = 0
    updated_count = 0
    for pair in pairs:
        if pair["id_oferta"] in existing_ids:
            # Actualizar par existente
            existing_pairs = [
                pair if p["id_oferta"] == pair["id_oferta"] else p
                for p in existing_pairs
            ]
            updated_count += 1
        else:
            existing_pairs.append(pair)
            new_count += 1

    output = {
        "version": "1.0",
        "descripcion": "Pares de entrenamiento para fine-tuning de clasificación ESCO.",
        "fecha_generacion": datetime.utcnow().isoformat() + "Z",
        "fuente": "Issues resueltos Supabase + matching_history BD local",
        "total_pares": len(existing_pairs),
        "notas_fine_tuning": [
            "justificacion_humana: razonamiento experto (chain-of-thought)",
            "clasificacion_incorrecta: output rechazado (para DPO/RLHF)",
            "clasificacion_correcta: output aceptado (para supervisado)",
            "input.descripcion: texto completo de la oferta laboral",
        ],
        "pares": existing_pairs,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return new_count, updated_count, len(existing_pairs)


def show_stats():
    if not OUTPUT_PATH.exists():
        print("No existe training_pairs.json. Correr sin --stats primero.")
        return

    data = json.load(open(OUTPUT_PATH, encoding='utf-8'))
    pairs = data.get("pares", [])

    print(f"Total pares: {len(pairs)}")
    print(f"Generado: {data.get('fecha_generacion', '?')}")

    # Por autor
    autores = {}
    for p in pairs:
        a = p.get("autor", "unknown")
        autores[a] = autores.get(a, 0) + 1
    print(f"\nPor autor:")
    for a, c in sorted(autores.items(), key=lambda x: -x[1]):
        print(f"  {a}: {c}")

    # Por tipo de corrección
    cambios = {}
    for p in pairs:
        antes = p.get("clasificacion_incorrecta", {})
        despues = p.get("clasificacion_correcta", {})
        if antes and despues:
            key = f"{antes.get('isco_code', '?')} → {despues.get('isco_code', '?')}"
            cambios[key] = cambios.get(key, 0) + 1
    print(f"\nCorrecciones ISCO:")
    for k, c in sorted(cambios.items(), key=lambda x: -x[1]):
        print(f"  {k}: {c} ofertas")

    # Con justificación
    con_just = sum(1 for p in pairs if p.get("justificacion_humana"))
    print(f"\nCon justificación humana: {con_just}/{len(pairs)}")


def main():
    parser = argparse.ArgumentParser(
        description="Genera pares de entrenamiento desde issues resueltos"
    )
    parser.add_argument(
        "--since", help="Solo issues resueltos desde esta fecha (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Mostrar estadísticas del dataset"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Mostrar sin guardar"
    )
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    print("Generando pares de entrenamiento desde issues resueltos...")
    pairs = generate(since=args.since)

    if not pairs:
        return

    if args.dry_run:
        print(f"\n[DRY RUN] {len(pairs)} pares generados (no guardados)")
        for p in pairs:
            antes = (
                p["clasificacion_incorrecta"]["isco_code"]
                if p["clasificacion_incorrecta"]
                else "?"
            )
            despues = (
                p["clasificacion_correcta"]["isco_code"]
                if p["clasificacion_correcta"]
                else "?"
            )
            titulo = (
                p["input"]["titulo_limpio"] or p["input"]["titulo_original"] or "?"
            )[:40]
            print(f"  {p['id_oferta']:<16} {titulo:<42} {antes} → {despues}")
        return

    new, updated, total = save(pairs)
    print(f"\nResultado:")
    print(f"  Nuevos: {new}")
    print(f"  Actualizados: {updated}")
    print(f"  Total en dataset: {total}")
    print(f"  Guardado en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
