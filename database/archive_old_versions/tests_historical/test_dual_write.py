"""
Test de Dual-Write - db_manager.py
===================================

Verifica que db_manager.py escribe correctamente en v1 y v2 simultáneamente.
"""
import sys
import pandas as pd
from pathlib import Path

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager

print("="*70)
print("TEST DE DUAL-WRITE - db_manager.py")
print("="*70)
print()

# Crear oferta de prueba
print("1. Creando oferta de prueba...")
oferta_test = pd.DataFrame([{
    'id_oferta': 'TEST_DUAL_WRITE_001',
    'id_empresa': '12345',
    'titulo': 'Test Dual Write - Data Engineer',
    'empresa': 'Test Company SRL',
    'descripcion': 'Esta es una oferta de prueba para validar dual-write',
    'confidencial': 0,
    'localizacion': 'Buenos Aires, Argentina',
    'modalidad_trabajo': 'Híbrido',
    'tipo_trabajo': 'Full-time',
    'fecha_publicacion_original': '2025-11-03',
    'fecha_publicacion_iso': '2025-11-03',
    'fecha_publicacion_datetime': '2025-11-03 10:30:00',
    'url_oferta': 'https://test.com/ofertas/test_dual_write_001',
    'scrapeado_en': '2025-11-03T10:30:00'
}])

print(f"   Oferta creada: {oferta_test['id_oferta'].iloc[0]}")
print()

# Conectar con dual-write habilitado
print("2. Inicializando DatabaseManager con DUAL-WRITE habilitado...")
db = DatabaseManager(
    db_path='bumeran_scraping.db',
    enable_dual_write=True
)

if not db.enable_dual_write:
    print("   ERROR: Dual-write no está habilitado!")
    sys.exit(1)

print("   OK - Dual-write habilitado")
print()

# Conectar
print("3. Conectando a base de datos...")
db.connect()
print("   Conexiones establecidas")
print()

# Verificar conteos antes
print("4. Conteos ANTES de insertar:")
db.cursor.execute("SELECT COUNT(*) FROM ofertas WHERE id_oferta = ?", ('TEST_DUAL_WRITE_001',))
count_v1_before = db.cursor.fetchone()[0]

db.db_v2.cursor.execute("SELECT COUNT(*) FROM ofertas_raw WHERE id_oferta = ?", ('TEST_DUAL_WRITE_001',))
count_v2_before = db.db_v2.cursor.fetchone()[0]

print(f"   v1 (ofertas):     {count_v1_before}")
print(f"   v2 (ofertas_raw): {count_v2_before}")
print()

# Insertar con dual-write
print("5. Insertando oferta con DUAL-WRITE...")
try:
    result = db.insert_ofertas(oferta_test)
    print(f"   OK - {result} oferta insertada")
except Exception as e:
    print(f"   ERROR: {e}")
    db.disconnect()
    sys.exit(1)

print()

# Verificar conteos después
print("6. Conteos DESPUES de insertar:")
db.cursor.execute("SELECT COUNT(*) FROM ofertas WHERE id_oferta = ?", ('TEST_DUAL_WRITE_001',))
count_v1_after = db.cursor.fetchone()[0]

db.db_v2.cursor.execute("SELECT COUNT(*) FROM ofertas_raw WHERE id_oferta = ?", ('TEST_DUAL_WRITE_001',))
count_v2_after = db.db_v2.cursor.fetchone()[0]

print(f"   v1 (ofertas):     {count_v1_after}")
print(f"   v2 (ofertas_raw): {count_v2_after}")
print()

# Validar resultados
print("7. VALIDACION:")
v1_ok = (count_v1_after - count_v1_before) == 1
v2_ok = (count_v2_after - count_v2_before) == 1

print(f"   v1 insertada: {'OK' if v1_ok else 'ERROR'}")
print(f"   v2 insertada: {'OK' if v2_ok else 'ERROR'}")
print()

# Verificar contenido en v2
if v2_ok:
    print("8. Verificando contenido en v2 (ofertas_raw):")
    db.db_v2.cursor.execute("""
        SELECT id_oferta, raw_json, content_hash, scrapeado_en
        FROM ofertas_raw
        WHERE id_oferta = ?
    """, ('TEST_DUAL_WRITE_001',))

    row = db.db_v2.cursor.fetchone()
    if row:
        print(f"   id_oferta: {row[0]}")
        print(f"   raw_json length: {len(row[1])} chars")
        print(f"   content_hash: {row[2][:16]}...")
        print(f"   scrapeado_en: {row[3]}")
        print("   OK - Datos en v2 completos")
    else:
        print("   ERROR: No se encontró la oferta en v2")
    print()

# Limpiar (eliminar oferta de prueba)
print("9. Limpiando datos de prueba...")
db.cursor.execute("DELETE FROM ofertas WHERE id_oferta = ?", ('TEST_DUAL_WRITE_001',))
db.conn.commit()

db.db_v2.cursor.execute("DELETE FROM ofertas_raw WHERE id_oferta = ?", ('TEST_DUAL_WRITE_001',))
db.db_v2.conn.commit()

print("   Oferta de prueba eliminada")
print()

# Desconectar
db.disconnect()

print("="*70)
if v1_ok and v2_ok:
    print("RESULTADO: DUAL-WRITE FUNCIONA CORRECTAMENTE")
else:
    print("RESULTADO: ERROR EN DUAL-WRITE")
print("="*70)

sys.exit(0 if (v1_ok and v2_ok) else 1)
