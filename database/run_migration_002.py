# -*- coding: utf-8 -*-
"""
run_migration_002.py - Execute migration 002 for NLP Schema v5 columns
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

NEW_COLUMNS = [
    # Bloque 8: Rol y Tareas
    ('tareas_explicitas', 'TEXT'),
    ('tareas_inferidas', 'TEXT'),
    ('tiene_gente_cargo', 'INTEGER'),
    ('tipo_equipo', 'TEXT'),
    ('producto_servicio', 'TEXT'),
    # Bloque 9: Condiciones Laborales
    ('area_funcional', 'TEXT'),
    ('nivel_seniority', 'TEXT'),
    ('tipo_contrato', 'TEXT'),
    # Bloque 2: Empresa
    ('sector_empresa', 'TEXT'),
    ('es_tercerizado', 'INTEGER'),
    # Bloque 6: Skills Expandido
    ('tecnologias_list', 'TEXT'),
    ('marcas_especificas_list', 'TEXT'),
    # Bloque 12: Metadatos NLP
    ('tipo_oferta', 'TEXT'),
    ('calidad_texto', 'TEXT'),
    ('pasa_a_matching', 'INTEGER'),
    # Bloque 13: Licencias
    ('licencia_conducir', 'INTEGER'),
    ('tipo_licencia', 'TEXT'),
    # Bloque 14: Calidad y Flags
    ('tiene_requisitos_discriminatorios', 'INTEGER'),
    ('requisito_edad_min', 'INTEGER'),
    ('requisito_edad_max', 'INTEGER'),
]

INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_area_funcional ON ofertas_nlp(area_funcional)',
    'CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_nivel_seniority ON ofertas_nlp(nivel_seniority)',
    'CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_tipo_oferta ON ofertas_nlp(tipo_oferta)',
    'CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_sector_empresa ON ofertas_nlp(sector_empresa)',
]

def run_migration():
    print(f"Conectando a: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute('PRAGMA table_info(ofertas_nlp)')
    existing_cols = {row[1] for row in cursor.fetchall()}
    print(f"Columnas existentes: {len(existing_cols)}")

    added = 0
    skipped = 0

    for col_name, col_type in NEW_COLUMNS:
        if col_name in existing_cols:
            print(f"  [SKIP] {col_name} ya existe")
            skipped += 1
        else:
            try:
                cursor.execute(f'ALTER TABLE ofertas_nlp ADD COLUMN {col_name} {col_type}')
                print(f"  [OK] {col_name} agregada")
                added += 1
            except Exception as e:
                print(f"  [ERROR] {col_name}: {e}")

    # Create indexes
    for idx_sql in INDEXES:
        try:
            cursor.execute(idx_sql)
            print(f"  [OK] Index creado")
        except Exception as e:
            print(f"  [ERROR] Index: {e}")

    # Register migration
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO schema_migrations (version, description, applied_at)
            VALUES ('002', 'Add NLP Schema v5 columns', datetime('now'))
        ''')
    except:
        pass  # Table might not exist

    conn.commit()
    conn.close()

    print(f"\n=== RESULTADO ===")
    print(f"Columnas agregadas: {added}")
    print(f"Columnas existentes (skip): {skipped}")
    print(f"Total nuevas columnas: {added + skipped}/20")

if __name__ == '__main__':
    run_migration()
