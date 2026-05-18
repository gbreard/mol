#!/usr/bin/env python3
"""
Pre-commit guard: si modificás match_ofertas_v3.py o process_nlp_from_db_v11.py,
debes bumpear database/MATCHER_VERSION o database/NLP_VERSION en el mismo commit.

Regla: aplica solo cuando el cambio toca lógica (cualquier modificación al .py).
Si el cambio es trivial (comentarios, docstring), pasá --allow-no-bump como flag
manual (NO automatizado: requiere intervención explícita).

Uso (desde hook):
    python scripts/check_version_bumped.py

Salida:
    0 → OK
    1 → falta bump
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

WATCHED = {
    "database/match_ofertas_v3.py": "database/MATCHER_VERSION",
    "database/process_nlp_from_db_v11.py": "database/NLP_VERSION",
}


def staged_files() -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def main() -> int:
    if "--allow-no-bump" in sys.argv:
        print("check_version_bumped: --allow-no-bump activo, salteando guard")
        return 0

    files = staged_files()
    problemas = []
    for src, version_file in WATCHED.items():
        if src in files and version_file not in files:
            problemas.append((src, version_file))

    if not problemas:
        return 0

    print("\n❌ Falta bump de versión:\n")
    for src, version_file in problemas:
        print(f"  Modificaste {src} pero no tocaste {version_file}")
    print(
        "\nQué hacer:\n"
        "  1. Si el cambio modifica comportamiento del algoritmo:\n"
        "     - Bumpear el archivo VERSION correspondiente (ej: 3.5.5 → 3.5.6)\n"
        "     - git add database/MATCHER_VERSION  # o NLP_VERSION\n"
        "     - git commit otra vez\n"
        "  2. Si el cambio es trivial (comentarios, fix de typo, log):\n"
        "     - git commit --no-verify  # solo si estás seguro de que no cambia lógica\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
