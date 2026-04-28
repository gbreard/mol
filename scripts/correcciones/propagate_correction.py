"""
SPEC T — Orchestador de propagación de correcciones humanas.

Función central del sistema. Toma un patrón estructurado y lo propaga
a todas las ofertas similares, registrando metadata en el issue origen.

Ejemplo de uso:
    from scripts.correcciones import propagate_correction

    patron = {
        "tipo": "nlp_area_funcional",
        "campo": "area_funcional",
        "condicion": {
            "tipo": "titulo_contiene_alguno",
            "keywords": ["operario de deposito", "operario de almacen"]
        },
        "valor_anterior": "Produccion",
        "valor_nuevo": "Logistica"
    }

    # Dry-run primero (estima sin tocar BD)
    result = propagate_correction(patron, dry_run=True)
    print(result.summary())  # "[DRY-RUN] Propagación 'nlp_area_funcional': 174 ofertas"

    # Ejecutar
    result = propagate_correction(patron, dry_run=False, issue_id="abc123")
    # → actualiza columnas patron_corregido, propagacion_n, propagacion_ids del issue.

CLI:
    python -m scripts.correcciones.propagate_correction <patron.json>
"""
import json
import sys
from pathlib import Path
from typing import Optional

# Ensure package imports work when invoked as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.correcciones.propagators import (
    PropagationResult,
    get_propagator,
    validar_patron,
)


def propagate_correction(
    patron: dict,
    *,
    dry_run: bool = True,
    issue_id: Optional[str] = None,
    db_path: str = "database/bumeran_scraping.db",
    verbose: bool = False,
    update_issue: bool = True,
) -> PropagationResult:
    """
    Aplica un patrón de corrección a todas las ofertas similares.

    Args:
        patron: dict con schema {tipo, campo, condicion, valor_anterior, valor_nuevo}.
                Ver scripts/correcciones/propagators/base.py para detalles.
        dry_run: si True, identifica ofertas y retorna conteos sin tocar BD/Supabase.
        issue_id: si se pasa Y dry_run=False Y update_issue=True, actualiza el issue
                  en Supabase con patron_corregido, propagacion_n, propagacion_ids.
        db_path: path a SQLite local.
        verbose: imprime info adicional.
        update_issue: si False, NO toca Supabase issues table (útil para tests o
                      para correr propagación sin issue asociado).

    Returns:
        PropagationResult con conteos, IDs tocados, errores y verificación.
    """
    validar_patron(patron)

    propagator = get_propagator(patron["tipo"], db_path=db_path, verbose=verbose)
    result = propagator.run(patron, dry_run=dry_run)

    if verbose:
        print(result.summary())
        if result.errores:
            print(f"  Errores: {len(result.errores)}")
            for err in result.errores[:5]:
                print(f"    - {err}")

    # Si no es dry_run y hay issue_id, actualizar issue en Supabase
    if not dry_run and issue_id and update_issue and result.ofertas_actualizadas > 0:
        try:
            _update_issue_propagacion(issue_id, patron, result, verbose=verbose)
        except Exception as e:
            result.errores.append(f"Error update issue {issue_id}: {str(e)[:200]}")

    return result


def _update_issue_propagacion(
    issue_id: str, patron: dict, result: PropagationResult, verbose: bool = False
) -> None:
    """Actualiza columnas patron_corregido, propagacion_n, propagacion_ids del issue."""
    config_path = Path(__file__).resolve().parent.parent.parent / "config" / "supabase_config.json"
    config = json.loads(config_path.read_text())

    from supabase import create_client
    client = create_client(config["url"], config["service_role_key"])

    update_data = {
        "patron_corregido": patron,
        "propagacion_n": result.ofertas_actualizadas,
        "propagacion_ids": [str(i) for i in result.ids_tocados],
    }
    client.table("issues").update(update_data).eq("id", issue_id).execute()
    if verbose:
        print(f"  Issue {issue_id[:8]} actualizado: propagacion_n={result.ofertas_actualizadas}")


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Propagar corrección humana")
    parser.add_argument(
        "patron_file",
        help="Path a JSON con el patrón. Usar '-' para leer de stdin (preferible en serverless).",
    )
    parser.add_argument("--apply", action="store_true",
                        help="Aplicar (default es dry-run)")
    parser.add_argument("--issue-id", help="UUID del issue para actualizar metadata")
    parser.add_argument("--no-update-issue", action="store_true",
                        help="No tocar Supabase issues table")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.patron_file == "-":
        patron = json.loads(sys.stdin.read())
    else:
        patron = json.loads(Path(args.patron_file).read_text())
    result = propagate_correction(
        patron,
        dry_run=not args.apply,
        issue_id=args.issue_id,
        verbose=args.verbose,
        update_issue=not args.no_update_issue,
    )

    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    sys.exit(0 if not result.errores else 1)


if __name__ == "__main__":
    main()
