# -*- coding: utf-8 -*-
"""
Ejecutar Migración 004: Campos NLP faltantes
============================================

Agrega 10 columnas detectadas durante pruebas de NLP v10.0.0.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
BACKUP_DIR = PROJECT_ROOT / "backups"
MIGRATION_FILE = Path(__file__).parent / "004_add_missing_nlp_fields.sql"


def backup_database():
    """Crea backup de la BD antes de migrar."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"bumeran_scraping_{timestamp}_pre_migration_004.db"

    print(f"[1] Creando backup: {backup_path.name}")
    shutil.copy2(DB_PATH, backup_path)

    # Verificar
    original_size = DB_PATH.stat().st_size
    backup_size = backup_path.stat().st_size

    if original_size == backup_size:
        print(f"    OK - Backup creado ({backup_size / 1024 / 1024:.1f} MB)")
        return backup_path
    else:
        raise Exception("Error: Backup incompleto")


def get_existing_columns(conn):
    """Obtiene columnas existentes."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ofertas_nlp)")
    return {row[1] for row in cursor.fetchall()}


def run_migration(conn, existing_columns):
    """Ejecuta la migración, saltando columnas existentes."""
    cursor = conn.cursor()

    # Leer SQL
    with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Parsear ALTER TABLE statements
    statements = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line.startswith('ALTER TABLE ofertas_nlp ADD COLUMN'):
            statements.append(line)

    print(f"\n[2] Ejecutando migración ({len(statements)} columnas)")
    print("-" * 60)

    added = 0
    skipped = 0
    errors = []

    for stmt in statements:
        # Extraer nombre de columna
        parts = stmt.split('ADD COLUMN')[1].strip().split()
        col_name = parts[0]

        if col_name in existing_columns:
            print(f"    [SKIP] {col_name} (ya existe)")
            skipped += 1
            continue

        try:
            cursor.execute(stmt)
            print(f"    [ADD]  {col_name}")
            added += 1
        except sqlite3.Error as e:
            print(f"    [ERR]  {col_name}: {e}")
            errors.append((col_name, str(e)))

    conn.commit()

    return added, skipped, errors


def verify_migration(conn):
    """Verifica columnas después de migración."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ofertas_nlp)")
    columns = [row[1] for row in cursor.fetchall()]
    return len(columns), columns


def main():
    print("=" * 70)
    print("MIGRACIÓN 004: Campos NLP Faltantes")
    print("=" * 70)

    # 1. Backup
    backup_path = backup_database()

    # 2. Conectar
    conn = sqlite3.connect(DB_PATH)

    # 3. Columnas existentes
    existing = get_existing_columns(conn)
    print(f"\n    Columnas existentes: {len(existing)}")

    # 4. Ejecutar migración
    added, skipped, errors = run_migration(conn, existing)

    # 5. Verificar
    total, columns = verify_migration(conn)

    conn.close()

    # 6. Resumen
    print("\n" + "=" * 70)
    print("RESUMEN MIGRACIÓN")
    print("=" * 70)
    print(f"  Columnas antes:  {len(existing)}")
    print(f"  Agregadas:       {added}")
    print(f"  Saltadas:        {skipped}")
    print(f"  Errores:         {len(errors)}")
    print(f"  Total después:   {total}")
    print(f"\n  Backup en: {backup_path}")

    if errors:
        print("\n  ERRORES:")
        for col, err in errors:
            print(f"    - {col}: {err}")

    # Listar nuevas columnas
    nuevas = [
        "contratacion_inmediata", "indexacion_salarial",
        "empresa_contratante", "empresa_publicadora",
        "obra_social", "art", "prepaga",
        "disponibilidad_viajes", "dias_laborales",
        "beneficios_detectados"
    ]

    print("\n" + "-" * 70)
    print("NUEVAS COLUMNAS AGREGADAS")
    print("-" * 70)
    for col in nuevas:
        status = "OK" if col in columns else "FALTA"
        print(f"  [{status}] {col}")

    print("\n" + "=" * 70)

    return added, errors


if __name__ == "__main__":
    main()
