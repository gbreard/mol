#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validar Ofertas v1.0 - Cambiar estado de validación de ofertas
==============================================================

Permite cambiar el estado de validación de ofertas en ofertas_esco_matching.
Cada cambio de estado queda registrado en validacion_historial para auditoría.

Estados disponibles:
- pendiente: Sin revisar, puede reprocesarse
- en_revision: Siendo optimizada, puede reprocesarse
- validado: Aprobada para producción, NO se puede reprocesar
- rechazado: Con errores, necesita fix, puede reprocesarse
- descartado: Oferta inválida/spam, NO se reprocesa

Uso:
    # Validar ofertas específicas
    python scripts/validar_ofertas.py --ids 123,456,789 --estado validado --motivo "Revisión OK"

    # Validar todas las ofertas de un run
    python scripts/validar_ofertas.py --run run_20260113_1550 --estado validado

    # Marcar como en revisión
    python scripts/validar_ofertas.py --ids 123 --estado en_revision --motivo "Detectado error ISCO"

    # Ver estado actual
    python scripts/validar_ofertas.py --status

    # Ver historial de una oferta
    python scripts/validar_ofertas.py --historial 123
"""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Paths
BASE = Path(__file__).parent.parent
DB_PATH = BASE / "database" / "bumeran_scraping.db"

# Estados válidos
ESTADOS_VALIDOS = ['pendiente', 'en_revision', 'validado', 'rechazado', 'descartado']


def get_conn() -> sqlite3.Connection:
    """Obtiene conexión a la BD."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def validar_ofertas(
    ids: List[str],
    estado: str,
    motivo: str = "",
    usuario: str = "manual"
) -> int:
    """
    Cambia el estado de validación de ofertas.

    Args:
        ids: Lista de IDs de ofertas
        estado: Nuevo estado
        motivo: Motivo del cambio
        usuario: Usuario que realiza el cambio

    Returns:
        Número de ofertas actualizadas
    """
    if estado not in ESTADOS_VALIDOS:
        raise ValueError(f"Estado inválido: {estado}. Válidos: {ESTADOS_VALIDOS}")

    conn = get_conn()
    cur = conn.cursor()
    timestamp = datetime.now().isoformat()
    updated = 0

    for id_oferta in ids:
        # Obtener estado actual y run_id
        cur.execute('''
            SELECT estado_validacion, run_id FROM ofertas_esco_matching
            WHERE id_oferta = ?
        ''', (str(id_oferta),))
        row = cur.fetchone()

        if not row:
            print(f"[WARN] Oferta {id_oferta} no encontrada en matching")
            continue

        estado_anterior = row['estado_validacion']
        run_id = row['run_id']

        if estado_anterior == estado:
            print(f"[SKIP] Oferta {id_oferta} ya tiene estado '{estado}'")
            continue

        # Actualizar estado
        cur.execute('''
            UPDATE ofertas_esco_matching
            SET estado_validacion = ?,
                validado_timestamp = ?,
                validado_por = ?
            WHERE id_oferta = ?
        ''', (estado, timestamp, usuario, str(id_oferta)))

        # Registrar en historial
        cur.execute('''
            INSERT INTO validacion_historial (
                id_oferta, run_id, estado_anterior, estado_nuevo,
                timestamp, motivo, usuario
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(id_oferta), run_id, estado_anterior, estado, timestamp, motivo, usuario))

        updated += 1
        print(f"[OK] Oferta {id_oferta}: {estado_anterior} → {estado}")

    conn.commit()
    conn.close()

    return updated


def validar_run(run_id: str, estado: str, motivo: str = "", usuario: str = "manual") -> int:
    """
    Cambia el estado de todas las ofertas de un run.

    Args:
        run_id: ID del run
        estado: Nuevo estado
        motivo: Motivo del cambio
        usuario: Usuario que realiza el cambio

    Returns:
        Número de ofertas actualizadas
    """
    conn = get_conn()
    cur = conn.cursor()

    # Obtener IDs del run
    cur.execute('''
        SELECT id_oferta FROM ofertas_esco_matching WHERE run_id = ?
    ''', (run_id,))
    ids = [row['id_oferta'] for row in cur.fetchall()]
    conn.close()

    if not ids:
        print(f"[ERROR] No se encontraron ofertas para run: {run_id}")
        return 0

    print(f"[INFO] Procesando {len(ids)} ofertas del run {run_id}")
    return validar_ofertas(ids, estado, motivo, usuario)


def show_status():
    """Muestra resumen de estados de validación."""
    conn = get_conn()
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("ESTADO DE VALIDACIÓN")
    print("=" * 60)

    # Por estado
    cur.execute('''
        SELECT estado_validacion, COUNT(*) as cnt
        FROM ofertas_esco_matching
        GROUP BY estado_validacion
        ORDER BY cnt DESC
    ''')
    print("\nPor estado:")
    for row in cur.fetchall():
        estado = row['estado_validacion'] or 'NULL'
        print(f"  {estado}: {row['cnt']}")

    # Por run
    cur.execute('''
        SELECT run_id, estado_validacion, COUNT(*) as cnt
        FROM ofertas_esco_matching
        GROUP BY run_id, estado_validacion
        ORDER BY run_id DESC
    ''')
    print("\nPor run:")
    current_run = None
    for row in cur.fetchall():
        if row['run_id'] != current_run:
            current_run = row['run_id']
            print(f"\n  {current_run}:")
        estado = row['estado_validacion'] or 'NULL'
        print(f"    {estado}: {row['cnt']}")

    # Ofertas validadas
    cur.execute('''
        SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion = 'validado'
    ''')
    validated = cur.fetchone()[0]
    print(f"\n[INFO] Ofertas listas para dashboard: {validated}")

    conn.close()


def show_historial(id_oferta: str):
    """Muestra historial de una oferta."""
    conn = get_conn()
    cur = conn.cursor()

    print(f"\n" + "=" * 60)
    print(f"HISTORIAL OFERTA: {id_oferta}")
    print("=" * 60)

    # Info actual
    cur.execute('''
        SELECT estado_validacion, run_id, validado_timestamp, validado_por
        FROM ofertas_esco_matching WHERE id_oferta = ?
    ''', (str(id_oferta),))
    row = cur.fetchone()

    if not row:
        print(f"[ERROR] Oferta {id_oferta} no encontrada")
        conn.close()
        return

    print(f"\nEstado actual: {row['estado_validacion']}")
    print(f"Run: {row['run_id']}")
    print(f"Última validación: {row['validado_timestamp'] or 'N/A'}")
    print(f"Por: {row['validado_por'] or 'N/A'}")

    # Historial
    cur.execute('''
        SELECT estado_anterior, estado_nuevo, timestamp, motivo, usuario
        FROM validacion_historial
        WHERE id_oferta = ?
        ORDER BY timestamp ASC
    ''', (str(id_oferta),))
    rows = cur.fetchall()

    if rows:
        print(f"\nHistorial de cambios ({len(rows)} registros):")
        for row in rows:
            ant = row['estado_anterior'] or 'NULL'
            nuevo = row['estado_nuevo']
            ts = row['timestamp'][:19] if row['timestamp'] else 'N/A'
            motivo = row['motivo'] or '-'
            usuario = row['usuario'] or 'sistema'
            print(f"  {ts} | {ant} → {nuevo} | {usuario} | {motivo}")
    else:
        print("\n(Sin historial de cambios)")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Validar ofertas - Cambiar estado de validación",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Estados válidos:
  pendiente   - Sin revisar, puede reprocesarse
  en_revision - Siendo optimizada, puede reprocesarse
  validado    - Aprobada para producción, NO se puede reprocesar
  rechazado   - Con errores, necesita fix, puede reprocesarse
  descartado  - Oferta inválida/spam, NO se reprocesa

Ejemplos:
  python scripts/validar_ofertas.py --ids 123,456 --estado validado --motivo "OK"
  python scripts/validar_ofertas.py --run run_baseline_20260113 --estado validado
  python scripts/validar_ofertas.py --status
  python scripts/validar_ofertas.py --historial 123
        """
    )

    parser.add_argument('--ids', type=str, help='IDs de ofertas separados por coma')
    parser.add_argument('--run', type=str, help='Validar todas las ofertas de un run')
    parser.add_argument('--estado', type=str, choices=ESTADOS_VALIDOS,
                        help='Nuevo estado de validación')
    parser.add_argument('--motivo', type=str, default='', help='Motivo del cambio')
    parser.add_argument('--usuario', type=str, default='manual', help='Usuario que valida')
    parser.add_argument('--status', action='store_true', help='Mostrar resumen de estados')
    parser.add_argument('--historial', type=str, help='Mostrar historial de una oferta')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.historial:
        show_historial(args.historial)
        return

    if not args.estado:
        parser.error("Se requiere --estado para validar ofertas")

    if args.ids:
        ids = [id.strip() for id in args.ids.split(',')]
        updated = validar_ofertas(ids, args.estado, args.motivo, args.usuario)
        print(f"\n[DONE] {updated} ofertas actualizadas")
    elif args.run:
        updated = validar_run(args.run, args.estado, args.motivo, args.usuario)
        print(f"\n[DONE] {updated} ofertas actualizadas")
    else:
        parser.error("Se requiere --ids o --run para validar ofertas")


if __name__ == "__main__":
    main()
