#!/usr/bin/env python3
"""
Actualiza sector_empresa usando el catálogo de empresas.

Para ofertas existentes que tienen id_empresa:
- Si es empleador conocido: asigna sector + confianza='alta'
- Si es intermediario: marca es_intermediario=1

Uso:
    python scripts/update_sector_from_catalog.py --dry-run
    python scripts/update_sector_from_catalog.py
"""

import json
import sqlite3
import argparse
from pathlib import Path


def load_catalog():
    """Carga catálogo de empresas."""
    path = Path(__file__).parent.parent / "config" / "empresas_catalogo.json"
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_from_catalog(db_path: str, dry_run: bool = False):
    """Actualiza sector usando catálogo de empresas."""

    catalog = load_catalog()
    empleadores = catalog.get("empleadores", {})
    intermediarios = catalog.get("intermediarios", {})

    print(f"Catálogo cargado: {len(empleadores)} empleadores, {len(intermediarios)} intermediarios")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Obtener ofertas con id_empresa que no tienen confianza='alta' aún
    query = """
        SELECT n.id_oferta, o.id_empresa, o.empresa, n.sector_empresa, n.sector_confianza
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE o.id_empresa IS NOT NULL
          AND (n.sector_confianza IS NULL OR n.sector_confianza != 'alta')
    """
    cursor.execute(query)
    ofertas = cursor.fetchall()

    print(f"Ofertas a procesar: {len(ofertas)}")

    stats = {
        "empleador_match": 0,
        "intermediario_match": 0,
        "sin_match": 0,
        "updates": []
    }

    for id_oferta, id_empresa, empresa, sector_actual, confianza_actual in ofertas:
        id_str = str(id_empresa)

        # Buscar en empleadores
        if id_str in empleadores:
            emp = empleadores[id_str]
            new_sector = emp.get("sector")
            new_clae = emp.get("clae_code")
            new_seccion = emp.get("clae_seccion")

            stats["empleador_match"] += 1

            if not dry_run:
                cursor.execute("""
                    UPDATE ofertas_nlp SET
                        sector_empresa = ?,
                        sector_confianza = 'alta',
                        sector_fuente = 'empresa_conocida',
                        es_intermediario = 0,
                        clae_code = COALESCE(clae_code, ?),
                        clae_grupo = COALESCE(clae_grupo, ?),
                        clae_seccion = COALESCE(clae_seccion, ?)
                    WHERE id_oferta = ?
                """, (new_sector, new_clae, new_clae[:3] if new_clae else None, new_seccion, id_oferta))

            stats["updates"].append({
                "id": id_oferta,
                "empresa": empresa[:30],
                "tipo": "empleador",
                "sector_antes": sector_actual,
                "sector_despues": new_sector
            })

        # Buscar en intermediarios
        elif id_str in intermediarios:
            inter = intermediarios[id_str]
            stats["intermediario_match"] += 1

            if not dry_run:
                cursor.execute("""
                    UPDATE ofertas_nlp SET
                        es_intermediario = 1
                    WHERE id_oferta = ?
                """, (id_oferta,))

            stats["updates"].append({
                "id": id_oferta,
                "empresa": empresa[:30],
                "tipo": "intermediario",
                "sector_antes": sector_actual,
                "sector_despues": "(no confiable)"
            })
        else:
            stats["sin_match"] += 1

    if not dry_run:
        conn.commit()

    conn.close()

    # Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"Empleadores matcheados: {stats['empleador_match']}")
    print(f"Intermediarios matcheados: {stats['intermediario_match']}")
    print(f"Sin match en catálogo: {stats['sin_match']}")

    if dry_run:
        print("\n[DRY RUN] No se aplicaron cambios")
        print("\nEjemplos de cambios que se harían:")
        for upd in stats["updates"][:10]:
            print(f"  {upd['id']} | {upd['empresa']} | {upd['tipo']} | {upd['sector_antes']} -> {upd['sector_despues']}")
    else:
        print(f"\nActualizaciones aplicadas: {len(stats['updates'])}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Actualiza sector usando catálogo de empresas")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar cambios sin aplicar")
    parser.add_argument("--db", default="database/bumeran_scraping.db", help="Ruta a la BD")

    args = parser.parse_args()

    update_from_catalog(args.db, args.dry_run)


if __name__ == "__main__":
    main()
