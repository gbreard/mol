# -*- coding: utf-8 -*-
"""Re-ejecutar matching para casos de error del Gold Set."""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
GOLD_SET_PATH = Path(__file__).parent / 'gold_set_manual_v2.json'

def main():
    print("=" * 70)
    print("RE-EJECUTAR MATCHING PARA ERRORES GOLD SET")
    print("=" * 70)

    # Cargar gold set
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    # Obtener IDs de errores
    error_ids = [g['id_oferta'] for g in gold_set if not g.get('esco_ok', True)]
    print(f"\nCasos con error: {len(error_ids)}")
    print(f"IDs: {error_ids}")

    # Mostrar términos del diccionario que podrían aplicar
    conn = sqlite3.connect(DB_PATH)
    print("\n" + "-" * 70)
    print("TERMINOS NUEVOS EN DICCIONARIO:")
    print("-" * 70)

    terminos_clave = [
        'ejecutivo de cuentas', 'community manager', 'gerente de ventas',
        'dermatóloga', 'operario picking', 'analista de cultivo'
    ]

    for t in terminos_clave:
        cursor = conn.execute("""
            SELECT termino_argentino, isco_target, esco_preferred_label
            FROM diccionario_arg_esco
            WHERE LOWER(termino_argentino) = LOWER(?)
        """, (t,))
        row = cursor.fetchone()
        if row:
            print(f"  '{row[0]}' -> {row[2]} (ISCO {row[1]})")
        else:
            print(f"  '{t}' -> NO ENCONTRADO")

    conn.close()

    # Re-ejecutar matching usando CLI
    print("\n" + "=" * 70)
    print("RE-EJECUTANDO MATCHING VIA CLI...")
    print("=" * 70)

    ids_str = ' '.join(error_ids)
    script_path = Path(__file__).parent / 'match_ofertas_multicriteria.py'

    cmd = [sys.executable, str(script_path), '--ids'] + error_ids
    print(f"\nComando: python match_ofertas_multicriteria.py --ids {ids_str[:50]}...")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent))

    print("\n--- STDOUT ---")
    print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)

    if result.stderr:
        print("\n--- STDERR ---")
        print(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)

    # Verificar resultados
    print("\n" + "=" * 70)
    print("VERIFICACION POST-MATCHING:")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)

    cambios = []
    for id_oferta in error_ids:
        # Buscar en gold set
        gs_entry = next((g for g in gold_set if g['id_oferta'] == id_oferta), None)
        tipo_error = gs_entry.get('tipo_error', 'desconocido') if gs_entry else 'desconocido'

        # Buscar resultado actual
        cursor = conn.execute("""
            SELECT esco_occupation_label, isco_code, occupation_match_method
            FROM ofertas_esco_matching
            WHERE id_oferta = ?
        """, (id_oferta,))
        row = cursor.fetchone()

        if row:
            esco_label = (row[0] or 'N/A')[:50]
            isco = row[1] or 'N/A'
            metodo = row[2] or 'N/A'

            # Marcar si usó diccionario
            bypass = "[BYPASS]" if "diccionario" in metodo.lower() or "bypass" in metodo.lower() else ""

            print(f"\n[{id_oferta}] ({tipo_error})")
            print(f"  -> {esco_label} (ISCO {isco}) {bypass}")
            print(f"     Método: {metodo}")

            if bypass:
                cambios.append(id_oferta)

    conn.close()

    print("\n" + "=" * 70)
    print(f"CASOS CON BYPASS DICCIONARIO: {len(cambios)}")
    print("=" * 70)
    print("\nAHORA EJECUTAR: python test_gold_set_manual.py")

if __name__ == '__main__':
    main()
