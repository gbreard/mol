#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reapply Rules to Validated Offers v1.0
======================================

Reaplicar reglas de matching a ofertas ya validadas SIN cambiar su estado.
Útil cuando se crean reglas nuevas que corrigen errores detectados.

Flujo:
1. Lee ofertas validadas que tuvieron errores resueltos
2. Reaplicar SOLO matching (no NLP)
3. Actualiza campos de matching en BD
4. NO cambia estado_validacion

Uso:
    # Ver ofertas afectadas (dry-run)
    python scripts/reapply_rules_to_validated.py --dry-run

    # Reprocesar todas las que tuvieron errores resueltos
    python scripts/reapply_rules_to_validated.py

    # Reprocesar IDs específicos
    python scripts/reapply_rules_to_validated.py --ids 123,456,789

    # Luego sincronizar a Supabase
    python scripts/exports/sync_to_supabase.py
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "database"))

DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"


def get_offers_with_resolved_errors(conn) -> list:
    """Obtiene IDs de ofertas validadas que tuvieron errores resueltos."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ve.id_oferta
        FROM validation_errors ve
        JOIN ofertas_esco_matching m ON ve.id_oferta = m.id_oferta
        WHERE ve.resuelto = 1
          AND m.estado_validacion IN ('validado_claude', 'validado_humano')
        ORDER BY ve.id_oferta
    """)
    return [row[0] for row in cursor.fetchall()]


def get_oferta_nlp_data(conn, id_oferta: str) -> dict:
    """Obtiene datos NLP de una oferta para matching."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            o.id_oferta, o.titulo, o.descripcion,
            n.titulo_limpio, n.tareas_explicitas, n.nivel_seniority,
            n.area_funcional, n.sector_empresa, n.skills_tecnicas_list,
            n.soft_skills_list, n.modalidad, n.tipo_contrato,
            m.isco_code, m.esco_occupation_label, m.regla_aplicada
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE o.id_oferta = ?
    """, (id_oferta,))

    row = cursor.fetchone()
    if not row:
        return None

    return {
        'id_oferta': row[0],
        'titulo': row[1] or '',
        'descripcion': row[2] or '',
        'titulo_limpio': row[3] or row[1] or '',
        'tareas_explicitas': row[4] or '',
        'nivel_seniority': row[5],
        'area_funcional': row[6],
        'sector_empresa': row[7],
        'skills_tecnicas_list': row[8],
        'soft_skills_list': row[9],
        'modalidad': row[10],
        'tipo_contrato': row[11],
        'isco_anterior': row[12],
        'esco_anterior': row[13],
        'regla_anterior': row[14]
    }




def main():
    parser = argparse.ArgumentParser(description='Reapply rules to validated offers')
    parser.add_argument('--ids', help='IDs específicos separados por coma')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar, no modificar')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar detalles')
    args = parser.parse_args()

    print("=" * 60)
    print("REAPPLY RULES TO VALIDATED OFFERS")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))

    # Obtener IDs a procesar
    if args.ids:
        offer_ids = [id.strip() for id in args.ids.split(',')]
        print(f"IDs especificados: {len(offer_ids)}")
    else:
        offer_ids = get_offers_with_resolved_errors(conn)
        print(f"Ofertas con errores resueltos: {len(offer_ids)}")

    if not offer_ids:
        print("No hay ofertas para procesar.")
        return

    if args.dry_run:
        print(f"\n[DRY-RUN] Se reprocesarían {len(offer_ids)} ofertas:")
        print(f"IDs: {offer_ids[:10]}{'...' if len(offer_ids) > 10 else ''}")
        return

    # Importar matcher
    try:
        from match_ofertas_v3 import MatcherV3
        matcher = MatcherV3(conn)
        print("Matcher v3 cargado OK")
    except Exception as e:
        print(f"Error cargando matcher: {e}")
        import traceback
        traceback.print_exc()
        return

    # Generar run_id para tracking
    run_id = f"reapply_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Run ID: {run_id}")

    # Procesar ofertas
    cambios = 0
    errores = 0
    sin_cambio = 0

    for i, id_oferta in enumerate(offer_ids):
        try:
            # Obtener datos NLP de la oferta
            oferta_data = get_oferta_nlp_data(conn, id_oferta)

            if not oferta_data:
                print(f"  [{i+1}/{len(offer_ids)}] {id_oferta}: No encontrada")
                errores += 1
                continue

            isco_anterior = oferta_data.pop('isco_anterior')
            esco_anterior = oferta_data.pop('esco_anterior')
            regla_anterior = oferta_data.pop('regla_anterior')

            # Ejecutar matching (esto persiste automáticamente)
            result = matcher.match_and_persist(
                id_oferta=id_oferta,
                oferta_nlp=oferta_data,
                categorize_skills=True,
                run_id=run_id,
                _allow_no_run=True
            )

            # Restaurar estado de validación (el matcher lo resetea a 'pendiente')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ofertas_esco_matching
                SET estado_validacion = 'validado_claude',
                    validado_timestamp = datetime('now')
                WHERE id_oferta = ?
            """, (id_oferta,))
            conn.commit()

            isco_nuevo = result.isco_code
            regla_nueva = result.metadata.get('regla_aplicada') if result.metadata else None

            if isco_anterior != isco_nuevo:
                cambios += 1
                if args.verbose or True:  # siempre mostrar cambios
                    print(f"  [{i+1}/{len(offer_ids)}] {id_oferta}: {isco_anterior} -> {isco_nuevo} (regla: {regla_nueva})")
            else:
                sin_cambio += 1
                if args.verbose:
                    print(f"  [{i+1}/{len(offer_ids)}] {id_oferta}: sin cambio")

        except Exception as e:
            print(f"  [{i+1}/{len(offer_ids)}] {id_oferta}: EXCEPTION - {e}")
            errores += 1

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Procesadas:  {len(offer_ids)}")
    print(f"Con cambios: {cambios}")
    print(f"Sin cambios: {sin_cambio}")
    print(f"Errores:     {errores}")
    print(f"\nPróximo paso: python scripts/exports/sync_to_supabase.py")

    conn.close()


if __name__ == "__main__":
    main()
