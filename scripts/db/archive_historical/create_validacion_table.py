#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
create_validacion_table.py
==========================
Crea la tabla validacion_humana para almacenar feedback de validadores.

Estructura:
- id_oferta: FK a ofertas
- score_humano: 1-5 (1=incorrecto, 5=perfecto)
- comentario: observaciones del validador
- validador: nombre del validador
- timestamp_validacion: cuando se validó
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "bumeran_scraping.db"

def main():
    print("=" * 70)
    print("CREAR TABLA validacion_humana")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar si la tabla ya existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='validacion_humana'
    """)
    existe = cursor.fetchone()

    if existe:
        print("\n[!] La tabla validacion_humana ya existe")
        cursor.execute("SELECT COUNT(*) FROM validacion_humana")
        count = cursor.fetchone()[0]
        print(f"    Registros existentes: {count:,}")
    else:
        print("\n[1] Creando tabla validacion_humana...")
        cursor.execute("""
            CREATE TABLE validacion_humana (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_oferta TEXT NOT NULL,
                score_humano INTEGER CHECK(score_humano BETWEEN 1 AND 5),
                esco_correcto INTEGER DEFAULT NULL,
                comentario TEXT,
                validador TEXT DEFAULT 'anonimo',
                timestamp_validacion TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
            )
        """)
        print("    [OK] Tabla creada")

        # Crear índice para búsquedas rápidas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_validacion_id_oferta
            ON validacion_humana(id_oferta)
        """)
        print("    [OK] Índice creado")

    conn.commit()

    # Mostrar schema
    print("\n[2] Schema de validacion_humana:")
    cursor.execute("PRAGMA table_info(validacion_humana)")
    for row in cursor.fetchall():
        print(f"    {row[1]:<25} {row[2]}")

    print("\n" + "=" * 70)
    conn.close()


if __name__ == '__main__':
    main()
