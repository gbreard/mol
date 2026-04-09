#!/usr/bin/env python3
"""
E4.1 — Separar training pairs por confianza y convertir a formato contrastivo.

Lee config/training_pairs.json y genera:
  data/fine_tuning/train_human.json    → pares alta confianza (formato contrastivo)
  data/fine_tuning/validation_auto.json → pares baja confianza (formato original)

Formato contrastivo (para sentence-transformers MultipleNegativesRankingLoss):
  {
    "query": título/tarea de la oferta,
    "positive": label de la clasificación correcta,
    "negatives": [label de la clasificación incorrecta],
    "autor": quien validó,
    "confianza": "alta",
    "split": "train"
  }

Uso:
    python scripts/ml/tag_training_pairs_confidence.py
    python scripts/ml/tag_training_pairs_confidence.py --dry-run
"""

import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = PROJECT_ROOT / "config" / "training_pairs.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "fine_tuning"

AUTORES_ALTA_CONFIANZA = {
    "Cynthia",
    "cinvazquez4@gmail.com",
    "Diego Javier Schleser",
    "Gerardo Breard",
    "gerardo",
}


def build_contrastive_pair(par: dict) -> dict:
    """Convierte un par supervised a formato contrastivo."""
    inp = par.get("input", {})
    query = inp.get("titulo_limpio") or inp.get("titulo_original") or ""

    # Agregar tareas si existen (enriquece el query)
    tareas = inp.get("tareas_explicitas") or ""
    if tareas and len(tareas) > 10:
        query = f"{query}; {tareas[:200]}"

    correcta = par.get("clasificacion_correcta", {})
    incorrecta = par.get("clasificacion_incorrecta", {})

    positive = correcta.get("label") or correcta.get("esco_label") or ""
    negative = incorrecta.get("label") or incorrecta.get("esco_label") or ""

    return {
        "query": query,
        "positive": positive,
        "negatives": [negative] if negative else [],
        "positive_isco": correcta.get("isco") or correcta.get("isco_code") or "",
        "negative_isco": incorrecta.get("isco") or incorrecta.get("isco_code") or "",
        "id_oferta": par.get("id_oferta"),
        "autor": par.get("autor"),
        "confianza": "alta",
        "split": "train",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tp = json.load(open(INPUT_PATH, encoding="utf-8"))
    pares = tp.get("pares", [])
    print(f"Total pares en input: {len(pares)}")

    train_pares = []
    validation_pares = []

    for par in pares:
        autor = par.get("autor") or ""
        if autor in AUTORES_ALTA_CONFIANZA:
            contrastive = build_contrastive_pair(par)
            train_pares.append(contrastive)
        else:
            par_tagged = {**par, "confianza": "baja", "split": "validation"}
            validation_pares.append(par_tagged)

    print(f"Alta confianza (train):   {len(train_pares)}")
    print(f"Baja confianza (validation): {len(validation_pares)}")

    # Validar formato contrastivo
    invalid = [p for p in train_pares if not p.get("query") or not p.get("positive")]
    if invalid:
        print(f"WARNING: {len(invalid)} pares sin query o positive")
        for p in invalid[:3]:
            print(f"  id_oferta={p['id_oferta']}, query='{p['query'][:40]}', positive='{p['positive'][:40]}'")

    if args.dry_run:
        print("\n[DRY-RUN] No se guardan archivos.")
        print(f"\nSample train (contrastivo):")
        if train_pares:
            print(json.dumps(train_pares[0], ensure_ascii=False, indent=2)[:300])
        print(f"\nSample validation:")
        if validation_pares:
            print(json.dumps({k: v for k, v in validation_pares[0].items() if k in ['id_oferta','autor','confianza','split']}, indent=2))
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train_out = OUTPUT_DIR / "train_human.json"
    with open(train_out, "w", encoding="utf-8") as f:
        json.dump(train_pares, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado: {train_out} ({len(train_pares)} pares)")

    val_out = OUTPUT_DIR / "validation_auto.json"
    with open(val_out, "w", encoding="utf-8") as f:
        json.dump(validation_pares, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {val_out} ({len(validation_pares)} pares)")


if __name__ == "__main__":
    main()
