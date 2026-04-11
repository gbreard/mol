#!/usr/bin/env python3
"""
E4.3 — Consolidar dataset de entrenamiento para fine-tuning BGE-M3.

Combina todas las fuentes de pares de entrenamiento y genera
un resumen con métricas go/no-go para fine-tuning.

Fuentes de entrenamiento (alta confianza):
  - data/fine_tuning/train_human.json (issues humanos)
  - data/fine_tuning/train_correcciones.json (correcciones aprobadas)
  - data/fine_tuning/train_argentino.json (esco_argentino)

Fuentes de validación:
  - data/fine_tuning/validation_auto.json (pares automáticos)
  - database/gold_set_manual_v2.json (gold set manual)

Output:
  - data/fine_tuning/dataset_summary.json

Uso:
    python scripts/ml/consolidate_training_dataset.py
    python scripts/ml/consolidate_training_dataset.py --dry-run
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FT_DIR = PROJECT_ROOT / "data" / "fine_tuning"
OUTPUT_PATH = FT_DIR / "dataset_summary.json"

# Go/no-go thresholds
MIN_TRAIN_PAIRS = 500
MIN_GOLD_SET = 150


def count_json_file(path: Path) -> int:
    """Count items in a JSON array file. Returns 0 if file doesn't exist."""
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(data, list):
            return len(data)
        return 0
    except (json.JSONDecodeError, Exception):
        return 0


def main():
    parser = argparse.ArgumentParser(description="E4.3: Consolidate training dataset")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("E4.3: Consolidando dataset de entrenamiento")
    print("=" * 60)

    # Count all sources
    sources = {
        "train_human": {
            "path": str(FT_DIR / "train_human.json"),
            "pares": count_json_file(FT_DIR / "train_human.json"),
            "confianza": "alta",
            "descripcion": "Pares de issues humanos (Cynthia, Diego, Gerardo)",
        },
        "train_correcciones": {
            "path": str(FT_DIR / "train_correcciones.json"),
            "pares": count_json_file(FT_DIR / "train_correcciones.json"),
            "confianza": "alta",
            "descripcion": "Correcciones expertas aprobadas",
        },
        "train_argentino": {
            "path": str(FT_DIR / "train_argentino.json"),
            "pares": count_json_file(FT_DIR / "train_argentino.json"),
            "confianza": "alta",
            "descripcion": "Pares contrastivos desde esco_argentino (44 ocupaciones)",
        },
        "validation_auto": {
            "path": str(FT_DIR / "validation_auto.json"),
            "pares": count_json_file(FT_DIR / "validation_auto.json"),
            "confianza": "baja",
            "descripcion": "Pares automáticos baja confianza",
        },
        "validation_gold": {
            "path": str(PROJECT_ROOT / "database" / "gold_set_manual_v2.json"),
            "pares": count_json_file(PROJECT_ROOT / "database" / "gold_set_manual_v2.json"),
            "confianza": "alta",
            "descripcion": "Gold set manual de referencia",
        },
    }

    # Create empty train_correcciones.json if it doesn't exist
    correcciones_path = FT_DIR / "train_correcciones.json"
    if not correcciones_path.exists():
        FT_DIR.mkdir(parents=True, exist_ok=True)
        correcciones_path.write_text("[]", encoding='utf-8')
        print(f"  Creado archivo vacío: {correcciones_path}")

    # Calculate totals
    total_alta = sum(
        s["pares"] for s in sources.values()
        if s["confianza"] == "alta" and not s["path"].endswith("gold_set_manual_v2.json")
    )
    total_validacion = (
        sources["validation_auto"]["pares"] +
        sources["validation_gold"]["pares"]
    )
    gold_actual = sources["validation_gold"]["pares"]

    gap_train = max(0, MIN_TRAIN_PAIRS - total_alta)
    gap_gold = max(0, MIN_GOLD_SET - gold_actual)
    listo = total_alta >= MIN_TRAIN_PAIRS and gold_actual >= MIN_GOLD_SET

    # Print summary
    print("\nFuentes de entrenamiento (alta confianza):")
    for key in ["train_human", "train_correcciones", "train_argentino"]:
        s = sources[key]
        print(f"  {key:25s}: {s['pares']:4d} pares")
    print(f"  {'TOTAL':25s}: {total_alta:4d} pares")

    print("\nFuentes de validación:")
    for key in ["validation_auto", "validation_gold"]:
        s = sources[key]
        print(f"  {key:25s}: {s['pares']:4d} pares")
    print(f"  {'TOTAL':25s}: {total_validacion:4d} pares")

    print(f"\nGo/No-Go:")
    print(f"  Pares entrenamiento: {total_alta}/{MIN_TRAIN_PAIRS} (gap: {gap_train})")
    print(f"  Gold set:            {gold_actual}/{MIN_GOLD_SET} (gap: {gap_gold})")
    print(f"  Listo para FT:       {'SI' if listo else 'NO'}")

    # Build summary
    summary = {
        "generado_at": datetime.now(timezone.utc).isoformat(),
        "fuentes": {k: {kk: vv for kk, vv in v.items() if kk != "path"} for k, v in sources.items()},
        "totales": {
            "entrenamiento_alta_confianza": total_alta,
            "validacion": total_validacion,
            "go_no_go": {
                "pares_requeridos": MIN_TRAIN_PAIRS,
                "pares_actuales": total_alta,
                "gap": gap_train,
                "gold_set_requerido": MIN_GOLD_SET,
                "gold_set_actual": gold_actual,
                "gap_gold_set": gap_gold,
                "listo_para_fine_tuning": listo,
            },
        },
    }

    if args.dry_run:
        print("\n[DRY-RUN] No se guarda archivo.")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    FT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
