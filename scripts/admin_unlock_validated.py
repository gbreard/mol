#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin: Desbloquear Ofertas Validadas

Script de administración para desbloquear ofertas validadas.
USO EXCEPCIONAL - requiere justificación obligatoria.

El desbloqueo:
1. Registra en validacion_historial quién, cuándo y por qué
2. Cambia estado de 'validado' a 'en_revision'
3. La oferta queda disponible para reprocesar

Uso:
    python scripts/admin_unlock_validated.py --ids 123,456 --motivo "Error detectado post-validación"
    python scripts/admin_unlock_validated.py --ids 123 --motivo "Corrección ISCO solicitada" --admin "fzazworka"

Verificar estado:
    python scripts/admin_unlock_validated.py --status
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Path a la BD
DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"


def get_connection():
    """Conexión a BD."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def show_status():
    """Muestra estado actual de ofertas por estado_validacion."""
    conn = get_connection()

    print("\n=== ESTADO DE OFERTAS POR VALIDACIÓN ===\n")

    cur = conn.execute("""
        SELECT
            estado_validacion,
            COUNT(*) as cantidad
        FROM ofertas_esco_matching
        GROUP BY estado_validacion
        ORDER BY cantidad DESC
    """)

    for row in cur.fetchall():
        estado = row['estado_validacion'] or 'NULL'
        proteccion = "🔒 PROTEGIDA" if estado in ('validado', 'descartado') else "🔓 Reprocesable"
        print(f"  {estado}: {row['cantidad']} ofertas {proteccion}")

    # Mostrar últimos desbloqueos
    print("\n=== ÚLTIMOS DESBLOQUEOS ===\n")
    cur = conn.execute("""
        SELECT id_oferta, estado_anterior, estado_nuevo, timestamp, usuario, motivo
        FROM validacion_historial
        WHERE estado_anterior = 'validado' AND estado_nuevo = 'en_revision'
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  [{row['timestamp'][:16]}] ID {row['id_oferta']}: {row['usuario']} - {row['motivo']}")
    else:
        print("  (ningún desbloqueo registrado)")

    conn.close()


def unlock_offers(ids: list, motivo: str, admin: str = "claude"):
    """
    Desbloquea ofertas validadas para reprocesamiento.

    Args:
        ids: Lista de IDs a desbloquear
        motivo: Justificación obligatoria
        admin: Usuario que realiza el desbloqueo

    Returns:
        Cantidad de ofertas desbloqueadas
    """
    if not motivo or len(motivo) < 10:
        print("[ERROR] El motivo debe tener al menos 10 caracteres.")
        return 0

    conn = get_connection()
    desbloqueadas = 0
    errores = []

    print(f"\n=== DESBLOQUEANDO {len(ids)} OFERTAS ===")
    print(f"Admin: {admin}")
    print(f"Motivo: {motivo}\n")

    for id_oferta in ids:
        # Verificar que existe y está validada
        cur = conn.execute(
            'SELECT estado_validacion FROM ofertas_esco_matching WHERE id_oferta = ?',
            (str(id_oferta),)
        )
        row = cur.fetchone()

        if not row:
            errores.append(f"{id_oferta}: No encontrada en ofertas_esco_matching")
            print(f"  [SKIP] {id_oferta} - No encontrada")
            continue

        # SPEC U-1 v3.1 sub-fase D: aceptar validado, validado_claude, validado_humano.
        # Los triggers (protect_validated_*) solo bloquean 'validado'; los otros dos
        # estados no tienen protección pero igualmente requieren audit trail al desbloquear.
        ESTADOS_VALIDADOS = ('validado', 'validado_claude', 'validado_humano')
        estado_actual = row['estado_validacion']
        if estado_actual not in ESTADOS_VALIDADOS:
            errores.append(f"{id_oferta}: Estado actual es '{estado_actual}', no validado")
            print(f"  [SKIP] {id_oferta} - Estado es '{estado_actual}', no validado")
            continue

        try:
            # Registrar en historial ANTES de cambiar estado
            conn.execute('''
                INSERT INTO validacion_historial
                (id_oferta, estado_anterior, estado_nuevo, timestamp, usuario, motivo)
                VALUES (?, ?, 'en_revision', ?, ?, ?)
            ''', (str(id_oferta), estado_actual, datetime.now().isoformat(), admin, motivo))

            # Cambiar estado
            conn.execute('''
                UPDATE ofertas_esco_matching
                SET estado_validacion = 'en_revision',
                    notas_revision = ?
                WHERE id_oferta = ?
            ''', (f"[DESBLOQUEO {datetime.now().strftime('%Y-%m-%d')}] {motivo}", str(id_oferta)))

            print(f"  [OK] {id_oferta} desbloqueada -> en_revision")
            desbloqueadas += 1

        except sqlite3.Error as e:
            errores.append(f"{id_oferta}: Error BD - {e}")
            print(f"  [ERROR] {id_oferta} - {e}")

    conn.commit()
    conn.close()

    # Resumen
    print(f"\n=== RESUMEN ===")
    print(f"Desbloqueadas: {desbloqueadas}/{len(ids)}")
    if errores:
        print(f"Errores: {len(errores)}")
        for e in errores[:5]:
            print(f"  - {e}")

    return desbloqueadas


def main():
    parser = argparse.ArgumentParser(
        description='Desbloquear ofertas validadas para reprocesamiento',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s --status                          # Ver estado actual
  %(prog)s --ids 123,456 --motivo "Error ISCO detectado"
  %(prog)s --ids 123 --motivo "Corrección solicitada" --admin "fzazworka"
        """
    )
    parser.add_argument('--status', action='store_true', help='Mostrar estado actual')
    parser.add_argument('--ids', help='IDs separados por coma')
    parser.add_argument('--motivo', help='Justificación del desbloqueo (obligatorio, min 10 chars)')
    parser.add_argument('--admin', default='claude', help='Usuario que desbloquea (default: claude)')

    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    if not args.ids:
        parser.print_help()
        print("\n[ERROR] Debe especificar --ids o --status")
        return 1

    if not args.motivo:
        print("[ERROR] Debe especificar --motivo con la justificación del desbloqueo")
        return 1

    ids = [x.strip() for x in args.ids.split(',')]
    unlock_offers(ids, args.motivo, args.admin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
