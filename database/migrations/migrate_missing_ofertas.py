"""
Script de Migracion de Ofertas Faltantes - v1 a v2
===================================================

Migra las ofertas que fueron scrapeadas el 2025-11-03 pero no se escribieron
en v2 porque el dual-write no estaba habilitado.

Uso:
    python migrate_missing_ofertas.py
"""

import sys
import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("="*70)
print("MIGRACION DE OFERTAS FALTANTES - 2025-11-03")
print("="*70)
print()

# Conectar a la base de datos
db_path = Path(__file__).parent.parent / 'bumeran_scraping.db'
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    # 1. Contar ofertas faltantes
    print("1. Identificando ofertas faltantes...")
    cursor.execute("""
        SELECT COUNT(*)
        FROM ofertas
        WHERE DATE(scrapeado_en) = '2025-11-03'
    """)
    ofertas_faltantes = cursor.fetchone()[0]
    print(f"   Ofertas faltantes: {ofertas_faltantes:,}")
    print()

    if ofertas_faltantes == 0:
        print("   No hay ofertas faltantes. Saliendo...")
        sys.exit(0)

    # 2. Obtener o crear sesión de scraping
    print("2. Buscando sesión de scraping del 2025-11-03...")
    cursor.execute("""
        SELECT id, session_uuid
        FROM scraping_sessions
        WHERE DATE(start_time) = '2025-11-03'
        AND source = 'bumeran'
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    if row:
        session_id = row[0]
        session_uuid = row[1]
        print(f"   Sesión encontrada: ID={session_id}, UUID={session_uuid[:8]}...")
    else:
        # Crear sesión
        import uuid
        session_uuid = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO scraping_sessions (
                session_uuid, source, mode, start_time, end_time, status
            ) VALUES (?, 'bumeran', 'full', ?, ?, 'completed')
        """, (
            session_uuid,
            '2025-11-03T10:31:00',
            datetime.now().isoformat()
        ))
        session_id = cursor.lastrowid
        print(f"   Sesión creada: ID={session_id}, UUID={session_uuid[:8]}...")

    print()

    # 3. Migrar ofertas
    print("3. Migrando ofertas a v2 (ofertas_raw)...")

    # Obtener ofertas del 3 de noviembre
    cursor.execute("""
        SELECT * FROM ofertas
        WHERE DATE(scrapeado_en) = '2025-11-03'
    """)

    ofertas = cursor.fetchall()
    migradas = 0

    for oferta in ofertas:
        # Convertir Row a dict
        oferta_dict = dict(oferta)

        # Generar JSON y hash
        raw_json = json.dumps(oferta_dict, ensure_ascii=False)
        content_hash = hashlib.sha256(raw_json.encode('utf-8')).hexdigest()

        # Insertar en ofertas_raw
        cursor.execute("""
            INSERT OR IGNORE INTO ofertas_raw (
                id_oferta, scraping_session_id, raw_json, content_hash,
                scrapeado_en, source, url_oferta
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            oferta_dict['id_oferta'],
            session_id,
            raw_json,
            content_hash,
            oferta_dict['scrapeado_en'],
            'bumeran',
            oferta_dict['url_oferta']
        ))

        if cursor.rowcount > 0:
            migradas += 1

        if migradas % 500 == 0:
            conn.commit()
            print(f"   Progreso: {migradas:,} ofertas migradas...")

    # Commit final
    conn.commit()

    print(f"   Total migradas: {migradas:,}")
    print()

    # 4. Actualizar sesión
    print("4. Actualizando sesión de scraping...")
    cursor.execute("""
        UPDATE scraping_sessions
        SET ofertas_total = ?,
            ofertas_nuevas = ?,
            end_time = ?
        WHERE id = ?
    """, (
        migradas,
        migradas,
        datetime.now().isoformat(),
        session_id
    ))
    conn.commit()
    print("   Sesión actualizada")
    print()

    # 5. Verificar resultados
    print("5. Verificando resultados...")
    cursor.execute("SELECT COUNT(*) FROM ofertas_raw")
    total_v2 = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ofertas")
    total_v1 = cursor.fetchone()[0]

    print(f"   Total en v1 (ofertas):     {total_v1:,}")
    print(f"   Total en v2 (ofertas_raw): {total_v2:,}")
    print()

    if total_v1 == total_v2:
        print("   ✓ SINCRONIZACION COMPLETA - v1 y v2 tienen la misma cantidad")
    else:
        print(f"   ⚠ DIFERENCIA: {abs(total_v1 - total_v2):,} ofertas")

    print()
    print("="*70)
    print("MIGRACION COMPLETADA EXITOSAMENTE")
    print("="*70)

except Exception as e:
    print()
    print("="*70)
    print("ERROR DURANTE MIGRACION")
    print("="*70)
    print(f"Error: {e}")
    conn.rollback()
    sys.exit(1)

finally:
    cursor.close()
    conn.close()
