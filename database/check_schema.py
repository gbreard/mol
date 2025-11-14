#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

print("=" * 70)
print("ESTRUCTURA TABLA: ofertas_esco_matching")
print("=" * 70)

cursor.execute('PRAGMA table_info(ofertas_esco_matching)')
cols = cursor.fetchall()
for col in cols:
    pk_marker = " [PK]" if col[5] else ""
    print(f"  {col[1]}: {col[2]}{pk_marker}")

print("\n" + "=" * 70)
print("TEST: Insertar un match manualmente")
print("=" * 70)

# Intentar un INSERT de prueba
try:
    cursor.execute("""
        INSERT INTO ofertas_esco_matching (
            id_oferta, esco_occupation_uri, esco_occupation_label,
            occupation_match_score, occupation_match_rank, match_method
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, ("TEST123", "http://test.uri", "Test Label", 0.95, 1, "test"))

    conn.commit()
    print("  [OK] INSERT exitoso con id_oferta='TEST123'")

    # Verificar
    cursor.execute("SELECT * FROM ofertas_esco_matching WHERE id_oferta='TEST123'")
    row = cursor.fetchone()
    print(f"  [OK] Registro recuperado: {row[:3]}")

    # Limpiar
    cursor.execute("DELETE FROM ofertas_esco_matching WHERE id_oferta='TEST123'")
    conn.commit()
    print("  [OK] Test completado y limpiado")

except Exception as e:
    print(f"  [ERROR] INSERT falló: {e}")

print("\n" + "=" * 70)
print("VERIFICAR: Tipo de id_oferta en tabla ofertas")
print("=" * 70)

cursor.execute('PRAGMA table_info(ofertas)')
cols = cursor.fetchall()
for col in cols:
    if col[1] == 'id_oferta':
        pk_marker = " [PK]" if col[5] else ""
        print(f"  {col[1]}: {col[2]}{pk_marker}")

# Ver un ejemplo real
cursor.execute('SELECT id_oferta, titulo FROM ofertas LIMIT 1')
row = cursor.fetchone()
print(f"\n  Ejemplo real: id_oferta={row[0]} (tipo: {type(row[0]).__name__})")

conn.close()
