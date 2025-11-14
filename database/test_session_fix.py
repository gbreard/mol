"""Test script para verificar el fix de db_manager_v2"""
from db_manager_v2 import DatabaseManagerV2

print("Probando creación de sesión con db_manager_v2 corregido...")
print()

# Crear instancia con dual-write habilitado
db = DatabaseManagerV2(enable_dual_write=True)
db.connect()

# Crear sesión de prueba (source debe ser valor válido del CHECK constraint)
session_id, session_uuid = db.create_scraping_session(
    source='bumeran',
    mode='full'
)

if session_id and session_uuid:
    print(f"OK - Sesion creada exitosamente:")
    print(f"  - ID: {session_id}")
    print(f"  - UUID: {session_uuid}")
    print()
    print("Fix aplicado correctamente. El metodo ya no intenta insertar 'metadata'.")
else:
    print("ERROR: No se pudo crear sesion")

db.disconnect()
