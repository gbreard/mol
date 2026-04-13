#!/usr/bin/env python3
"""
Transicionar ofertas pendiente → validado_claude.

Lee la política de errores bloqueantes de validation_rules.json.
Ofertas sin errores bloqueantes pasan a validado_claude.
Ofertas con V02/V10/NV02 quedan en pendiente.

Uso:
    python scripts/transicionar_pendientes.py
    python scripts/transicionar_pendientes.py --dry-run
    python scripts/transicionar_pendientes.py --limit 100
"""

import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
CONFIG_DIR = PROJECT_ROOT / "config"


def load_errores_bloqueantes() -> set:
    vr = json.loads((CONFIG_DIR / "validation_rules.json").read_text(encoding='utf-8'))
    return set(vr.get("politica_transicion", {}).get("errores_bloqueantes", []))


def main():
    parser = argparse.ArgumentParser(description="Transicionar pendientes a validado_claude")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, help="Limitar cantidad")
    args = parser.parse_args()

    print("Transición pendiente → validado_claude")
    print("=" * 50)

    bloqueantes = load_errores_bloqueantes()
    print(f"Errores bloqueantes: {bloqueantes}")

    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row

    # Get all pendientes
    query = "SELECT id_oferta FROM ofertas_esco_matching WHERE estado_validacion = 'pendiente'"
    if args.limit:
        query += f" LIMIT {args.limit}"
    pendientes = [r['id_oferta'] for r in conn.execute(query).fetchall()]
    print(f"Pendientes: {len(pendientes)}")

    if not pendientes:
        print("Nada que transicionar.")
        conn.close()
        return

    # Find which have blocking errors
    placeholders = ','.join(['?'] * len(pendientes))
    bloq_placeholders = ','.join(['?'] * len(bloqueantes))
    blocked = conn.execute(f"""
        SELECT DISTINCT id_oferta FROM validation_errors
        WHERE id_oferta IN ({placeholders})
        AND resuelto = 0
        AND error_id IN ({bloq_placeholders})
    """, pendientes + list(bloqueantes)).fetchall()
    blocked_ids = set(r['id_oferta'] for r in blocked)

    to_transition = [oid for oid in pendientes if oid not in blocked_ids]

    print(f"A transicionar: {len(to_transition)}")
    print(f"Bloqueadas: {len(blocked_ids)}")

    if blocked_ids:
        # Show why they're blocked
        for bid in list(blocked_ids)[:5]:
            errs = conn.execute("""
                SELECT error_id FROM validation_errors
                WHERE id_oferta = ? AND resuelto = 0 AND error_id IN ({})
            """.format(bloq_placeholders), [bid] + list(bloqueantes)).fetchall()
            print(f"  {bid}: {[e['error_id'] for e in errs]}")
        if len(blocked_ids) > 5:
            print(f"  ... +{len(blocked_ids) - 5} más")

    if args.dry_run:
        print("\n[DRY-RUN] No se transiciona.")
        return

    # Batch transition in chunks of 500
    timestamp = datetime.now().isoformat()
    transitioned = 0
    chunk_size = 500
    for i in range(0, len(to_transition), chunk_size):
        chunk = to_transition[i:i + chunk_size]
        ph = ','.join(['?'] * len(chunk))
        conn.execute(f"""
            UPDATE ofertas_esco_matching
            SET estado_validacion = 'validado_claude',
                validado_timestamp = ?,
                validado_por = 'auto_transicion_batch'
            WHERE id_oferta IN ({ph})
            AND estado_validacion = 'pendiente'
        """, [timestamp] + chunk)
        conn.commit()
        transitioned += len(chunk)
        print(f"  [{transitioned}/{len(to_transition)}] transicionadas")

    # Verify
    remaining = conn.execute(
        "SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion = 'pendiente'"
    ).fetchone()[0]
    total_vc = conn.execute(
        "SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion = 'validado_claude'"
    ).fetchone()[0]

    print(f"\nResultado:")
    print(f"  Transicionadas: {transitioned}")
    print(f"  Quedan pendiente: {remaining}")
    print(f"  Total validado_claude: {total_vc}")

    conn.close()


if __name__ == "__main__":
    main()
