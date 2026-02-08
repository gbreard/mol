#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación de Protección de Ofertas Validadas

Audita que el sistema esté correctamente configurado para proteger
ofertas validadas de reprocesamiento accidental.

Uso:
    python scripts/check_validated_protection.py
    python scripts/check_validated_protection.py --fix  # Aplicar migración de triggers

Verificaciones:
1. Conteo de ofertas por estado
2. Triggers de protección existentes
3. Simulación de query de export (detectar ofertas en riesgo)
4. Verificar que queries de selección excluyen validadas
"""

import argparse
import io
import sqlite3
import sys
from pathlib import Path

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Paths
DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
MIGRATION_PATH = Path(__file__).parent.parent / "migrations" / "016_protect_validated_offers.sql"


def get_connection():
    """Conexión a BD."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def check_offers_by_state():
    """Verificación 1: Conteo de ofertas por estado."""
    conn = get_connection()

    print("\n1. OFERTAS POR ESTADO DE VALIDACIÓN")
    print("=" * 50)

    cur = conn.execute("""
        SELECT
            COALESCE(estado_validacion, 'NULL') as estado,
            COUNT(*) as cantidad
        FROM ofertas_esco_matching
        GROUP BY estado_validacion
        ORDER BY cantidad DESC
    """)

    total = 0
    protegidas = 0
    for row in cur.fetchall():
        estado = row['estado']
        cantidad = row['cantidad']
        total += cantidad

        if estado in ('validado', 'descartado'):
            protegidas += cantidad
            icon = "🔒"
        else:
            icon = "🔓"

        print(f"  {icon} {estado}: {cantidad}")

    print(f"\n  Total: {total} ofertas")
    print(f"  Protegidas: {protegidas} ofertas")

    conn.close()
    return protegidas


def check_triggers_exist():
    """Verificación 2: Triggers de protección."""
    conn = get_connection()

    print("\n2. TRIGGERS DE PROTECCIÓN")
    print("=" * 50)

    cur = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'trigger'
        AND name LIKE 'protect%'
    """)
    triggers = [row['name'] for row in cur.fetchall()]

    expected = ['protect_validated_matching', 'protect_validated_status']
    all_exist = True

    for trigger in expected:
        if trigger in triggers:
            print(f"  ✓ {trigger}")
        else:
            print(f"  ✗ {trigger} - FALTA")
            all_exist = False

    conn.close()
    return all_exist


def check_at_risk_offers():
    """Verificación 3: Ofertas validadas que serían seleccionadas por query antigua."""
    conn = get_connection()

    print("\n3. OFERTAS EN RIESGO (query sin filtro)")
    print("=" * 50)

    # Simular query ANTIGUA (sin filtro)
    cur = conn.execute("""
        SELECT n.id_oferta, m.estado_validacion
        FROM ofertas_nlp n
        LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
        WHERE m.estado_validacion = 'validado'
        LIMIT 100
    """)
    at_risk = cur.fetchall()

    if at_risk:
        print(f"  ⚠️  {len(at_risk)} ofertas validadas serían seleccionadas con query sin filtro")
        print(f"  Ejemplos: {[row['id_oferta'] for row in at_risk[:5]]}")
    else:
        print(f"  ✓ Ninguna oferta validada en las primeras 100 de ofertas_nlp")

    conn.close()
    return len(at_risk)


def check_export_query_fixed():
    """Verificación 4: Query de export actualizada."""
    conn = get_connection()

    print("\n4. QUERY DE EXPORT (nueva con filtro)")
    print("=" * 50)

    # Simular query NUEVA (con filtro)
    cur = conn.execute("""
        SELECT n.id_oferta
        FROM ofertas_nlp n
        LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
        WHERE m.estado_validacion IS NULL
           OR m.estado_validacion NOT IN ('validado', 'descartado')
        ORDER BY n.id_oferta DESC
        LIMIT 100
    """)
    offers = cur.fetchall()

    # Verificar que ninguna es validada
    ids = [row['id_oferta'] for row in offers]
    if ids:
        cur = conn.execute(f"""
            SELECT id_oferta FROM ofertas_esco_matching
            WHERE id_oferta IN ({','.join(['?']*len(ids))})
            AND estado_validacion = 'validado'
        """, ids)
        validadas_en_resultado = cur.fetchall()

        if validadas_en_resultado:
            print(f"  ✗ ERROR: {len(validadas_en_resultado)} ofertas validadas en resultado")
            return False
        else:
            print(f"  ✓ Query nueva excluye ofertas validadas correctamente")
            print(f"  Seleccionaría {len(offers)} ofertas para export")

    conn.close()
    return True


def apply_migration():
    """Aplica la migración de triggers."""
    if not MIGRATION_PATH.exists():
        print(f"[ERROR] No se encuentra migración: {MIGRATION_PATH}")
        return False

    print(f"\nAplicando migración: {MIGRATION_PATH}")

    conn = get_connection()
    with open(MIGRATION_PATH, 'r', encoding='utf-8') as f:
        sql = f.read()

    try:
        conn.executescript(sql)
        print("✓ Migración aplicada exitosamente")
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"✗ Error aplicando migración: {e}")
        conn.close()
        return False


def main():
    parser = argparse.ArgumentParser(description='Verificar protección de ofertas validadas')
    parser.add_argument('--fix', action='store_true', help='Aplicar migración de triggers si faltan')
    args = parser.parse_args()

    print("=" * 60)
    print("  VERIFICACIÓN DE PROTECCIÓN DE OFERTAS VALIDADAS")
    print("=" * 60)

    # Ejecutar verificaciones
    protegidas = check_offers_by_state()
    triggers_ok = check_triggers_exist()
    at_risk = check_at_risk_offers()
    export_ok = check_export_query_fixed()

    # Resumen
    print("\n" + "=" * 60)
    print("  RESUMEN")
    print("=" * 60)

    all_ok = True

    if protegidas > 0:
        print(f"  ✓ {protegidas} ofertas protegidas (validadas/descartadas)")
    else:
        print(f"  ⚠️  No hay ofertas validadas aún")

    if triggers_ok:
        print(f"  ✓ Triggers de protección activos")
    else:
        print(f"  ✗ Faltan triggers de protección")
        all_ok = False
        if args.fix:
            if apply_migration():
                triggers_ok = True
                all_ok = True

    if at_risk == 0:
        print(f"  ✓ Sin ofertas en riesgo")
    else:
        print(f"  ⚠️  {at_risk} ofertas validadas estarían en riesgo con query antigua")

    if export_ok:
        print(f"  ✓ Query de export corregida")
    else:
        print(f"  ✗ Query de export NO excluye validadas")
        all_ok = False

    print()
    if all_ok:
        print("  ✅ SISTEMA PROTEGIDO CORRECTAMENTE")
        return 0
    else:
        print("  ❌ HAY PROBLEMAS DE PROTECCIÓN")
        if not triggers_ok:
            print("\n  Para aplicar triggers: python scripts/check_validated_protection.py --fix")
        return 1


if __name__ == "__main__":
    sys.exit(main())
