# -*- coding: utf-8 -*-
"""
Expandir diccionario_arg_esco con términos faltantes.
Estos términos corrigen errores de nivel jerárquico en el Gold Set.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Nuevos términos a insertar
NUEVOS_TERMINOS = [
    # Ejecutivos de ventas/cuentas
    ('ejecutivo de cuentas', '3322', 'representante comercial', 'Account Executive - ventas B2B'),
    ('account executive', '3322', 'representante comercial', 'Account Executive inglés'),
    ('ejecutivo comercial', '3322', 'representante comercial', 'Vendedor B2B nivel ejecutivo'),
    ('key account', '3322', 'representante comercial', 'Key Account Manager'),

    # Community Manager / Redes sociales
    ('community manager', '2432', 'especialista en relaciones públicas', 'Gestión de redes sociales'),
    ('cm', '2432', 'especialista en relaciones públicas', 'Abreviatura Community Manager'),
    ('social media manager', '2432', 'especialista en relaciones públicas', 'Gestor de redes sociales'),

    # Gerentes de ventas (nivel alto)
    ('gerente de ventas', '1221', 'director de ventas y comercialización', 'Nivel gerencial de ventas'),
    ('gerente comercial', '1221', 'director de ventas y comercialización', 'Sinónimo gerente ventas'),
    ('sales manager', '1221', 'director de ventas y comercialización', 'Gerente de ventas en inglés'),

    # Médicos especialistas
    ('médico estético', '2212', 'médico especialista', 'Medicina estética'),
    ('médica estética', '2212', 'médico especialista', 'Medicina estética femenino'),
    ('dermatóloga', '2212', 'médico especialista', 'Dermatología'),
    ('dermatólogo', '2212', 'médico especialista', 'Dermatología masculino'),
    ('médica clínica', '2211', 'médico de medicina general', 'Médica generalista'),
    ('médico clínico', '2211', 'médico de medicina general', 'Médico generalista'),

    # Picking / Logística
    ('operario picking', '9321', 'peón de almacén', 'Preparador de pedidos'),
    ('picker', '9321', 'peón de almacén', 'Preparador de pedidos en inglés'),
    ('preparador de pedidos', '9321', 'peón de almacén', 'Picking manual'),

    # Analista de cultivo / Agronomía
    ('analista de cultivo', '2132', 'agrónomo', 'Análisis de cultivos agrícolas'),
    ('analista agrónomo', '2132', 'agrónomo', 'Agrónomo analista'),
]

def main():
    print("=" * 60)
    print("EXPANDIR DICCIONARIO ARGENTINO")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ver estructura de la tabla
    cursor.execute("PRAGMA table_info(diccionario_arg_esco)")
    cols = [c[1] for c in cursor.fetchall()]
    print(f"\nColumnas de tabla: {cols}")

    # Contar registros actuales
    cursor.execute("SELECT COUNT(*) FROM diccionario_arg_esco")
    count_antes = cursor.fetchone()[0]
    print(f"Registros actuales: {count_antes}")

    # Insertar nuevos términos
    insertados = 0
    duplicados = 0
    errores = 0

    print(f"\nInsertando {len(NUEVOS_TERMINOS)} términos...")

    for termino, isco, esco_label, notes in NUEVOS_TERMINOS:
        try:
            # Verificar si ya existe
            cursor.execute(
                "SELECT 1 FROM diccionario_arg_esco WHERE LOWER(termino_argentino) = LOWER(?)",
                (termino,)
            )
            if cursor.fetchone():
                print(f"  [SKIP] '{termino}' ya existe")
                duplicados += 1
                continue

            # Insertar
            cursor.execute("""
                INSERT INTO diccionario_arg_esco
                (termino_argentino, isco_target, esco_preferred_label, esco_terms_json)
                VALUES (?, ?, ?, ?)
            """, (termino, isco, esco_label, f'{{"notes": "{notes}"}}'))

            print(f"  [OK] '{termino}' -> {esco_label} (ISCO {isco})")
            insertados += 1

        except Exception as e:
            print(f"  [ERROR] '{termino}': {e}")
            errores += 1

    conn.commit()

    # Contar registros después
    cursor.execute("SELECT COUNT(*) FROM diccionario_arg_esco")
    count_despues = cursor.fetchone()[0]

    print(f"\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  Insertados:  {insertados}")
    print(f"  Duplicados:  {duplicados}")
    print(f"  Errores:     {errores}")
    print(f"  Total antes: {count_antes}")
    print(f"  Total ahora: {count_despues}")

    # Verificar términos insertados
    print(f"\n" + "-" * 60)
    print("VERIFICACION - Términos clave:")
    print("-" * 60)

    terminos_clave = ['ejecutivo de cuentas', 'community manager', 'gerente de ventas', 'dermatóloga']
    for t in terminos_clave:
        cursor.execute("""
            SELECT termino_argentino, isco_target, esco_preferred_label
            FROM diccionario_arg_esco
            WHERE LOWER(termino_argentino) = LOWER(?)
        """, (t,))
        row = cursor.fetchone()
        if row:
            print(f"  '{row[0]}' -> {row[2]} (ISCO {row[1]})")
        else:
            print(f"  '{t}' -> NO ENCONTRADO")

    # Limpiar cache del módulo normalizacion_arg
    print(f"\n[!] IMPORTANTE: Reiniciar proceso para limpiar cache de diccionario")

    conn.close()

    return insertados

if __name__ == '__main__':
    main()
