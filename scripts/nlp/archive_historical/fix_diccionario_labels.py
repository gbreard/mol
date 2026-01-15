# -*- coding: utf-8 -*-
"""
Corregir diccionario_arg_esco con labels ESCO exactos.
El bypass requiere que esco_preferred_label coincida EXACTAMENTE con preferred_label_es en esco_occupations.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Correcciones de labels (termino_argentino -> esco_preferred_label correcto)
# IMPORTANTE: El label debe existir EXACTAMENTE en esco_occupations.preferred_label_es
CORRECCIONES = [
    # Gerente de Ventas - el label correcto en ESCO
    ('gerente de ventas', 'director de ventas/directora de ventas', 'C1221'),
    ('gerente comercial', 'director de ventas/directora de ventas', 'C1221'),
    ('sales manager', 'director de ventas/directora de ventas', 'C1221'),

    # Community Manager -> gestor de la información para las redes sociales
    ('community manager', 'gestor de la información para las redes sociales/gestora de la información para las redes sociales', 'C2432'),
    ('cm', 'gestor de la información para las redes sociales/gestora de la información para las redes sociales', 'C2432'),
    ('social media manager', 'gestor de la información para las redes sociales/gestora de la información para las redes sociales', 'C2432'),

    # Ejecutivo de cuentas/ventas
    ('ejecutivo de cuentas', 'representante comercial', 'C3322'),
    ('account executive', 'representante comercial', 'C3322'),
    ('ejecutivo comercial', 'representante comercial', 'C3322'),
    ('key account', 'representante comercial', 'C3322'),

    # Operario picking -> reponedor/reponedora
    ('operario picking', 'reponedor/reponedora', 'C9334'),
    ('picker', 'reponedor/reponedora', 'C9334'),
    ('preparador de pedidos', 'reponedor/reponedora', 'C9334'),

    # Analista cultivo -> ingeniero agrícola
    ('analista de cultivo', 'ingeniero agrícola/ingeniera agrícola', 'C2144'),
    ('analista agrónomo', 'ingeniero agrícola/ingeniera agrícola', 'C2144'),
]

def main():
    print("=" * 60)
    print("CORREGIR LABELS EN DICCIONARIO ARGENTINO")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar que los labels correctos existen en esco_occupations
    print("\n[1] VERIFICANDO LABELS EN ESCO_OCCUPATIONS:")
    labels_unicos = set(label for _, label, _ in CORRECCIONES)
    for label in labels_unicos:
        cursor.execute("""
            SELECT occupation_uri, preferred_label_es, isco_code
            FROM esco_occupations
            WHERE LOWER(preferred_label_es) = LOWER(?)
        """, (label,))
        row = cursor.fetchone()
        if row:
            print(f"  [OK] '{label}' -> {row[2]}")
        else:
            print(f"  [X] '{label}' NO EXISTE EN ESCO")

    # Aplicar correcciones
    print("\n[2] APLICANDO CORRECCIONES:")
    for termino, nuevo_label, nuevo_isco in CORRECCIONES:
        # Verificar que el término existe
        cursor.execute("""
            SELECT id, esco_preferred_label, isco_target
            FROM diccionario_arg_esco
            WHERE LOWER(termino_argentino) = LOWER(?)
        """, (termino,))
        row = cursor.fetchone()

        if row:
            old_label = row[1]
            old_isco = row[2]
            if old_label != nuevo_label or old_isco != nuevo_isco:
                cursor.execute("""
                    UPDATE diccionario_arg_esco
                    SET esco_preferred_label = ?, isco_target = ?
                    WHERE LOWER(termino_argentino) = LOWER(?)
                """, (nuevo_label, nuevo_isco, termino))
                print(f"  [UPDATED] '{termino}': '{old_label}' -> '{nuevo_label}'")
            else:
                print(f"  [SKIP] '{termino}' ya tiene label correcto")
        else:
            print(f"  [NOTFOUND] '{termino}' no existe en diccionario")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("CORRECCIONES APLICADAS")
    print("Ejecutar: python rematch_gold_set_errors.py")
    print("=" * 60)

if __name__ == '__main__':
    main()
