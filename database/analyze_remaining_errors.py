# -*- coding: utf-8 -*-
"""Analizar los 10 errores restantes del Gold Set."""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
GOLD_SET_PATH = Path(__file__).parent / 'gold_set_manual_v2.json'

def main():
    # Cargar gold set
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    # Filtrar errores
    errores = [g for g in gold_set if not g.get('esco_ok', True)]

    conn = sqlite3.connect(DB_PATH)

    print("=" * 80)
    print("ANALISIS DE 10 ERRORES RESTANTES - GOLD SET")
    print("=" * 80)

    analisis = []

    for i, err in enumerate(errores, 1):
        id_oferta = err['id_oferta']
        tipo_error = err.get('tipo_error', 'desconocido')
        comentario = err.get('comentario', '')

        # Buscar en ofertas_esco_matching (tiene titulo)
        cursor = conn.execute("""
            SELECT esco_occupation_label, isco_code, occupation_match_method,
                   titulo_normalizado, score_final_ponderado
            FROM ofertas_esco_matching WHERE id_oferta = ?
        """, (id_oferta,))
        row = cursor.fetchone()

        if row:
            esco = row[0][:50] if row[0] else 'N/A'
            isco = row[1] or 'N/A'
            metodo = row[2] or 'N/A'
            titulo = row[3][:55] if row[3] else 'N/A'
            score = row[4] or 0

            print(f"\n[{i}] ID: {id_oferta}")
            print(f"    Titulo:     {titulo}")
            print(f"    ESCO:       {esco}")
            print(f"    ISCO:       {isco}")
            print(f"    Score:      {score:.3f}")
            print(f"    Tipo Error: {tipo_error}")
            print(f"    Comentario: {comentario[:70]}")

            analisis.append({
                'id': id_oferta,
                'titulo': titulo,
                'esco': esco,
                'isco': isco,
                'tipo_error': tipo_error,
                'comentario': comentario,
                'metodo': metodo
            })

    conn.close()

    # Analisis por tipo de error y solucion propuesta
    print("\n" + "=" * 80)
    print("EVALUACION DE SOLUCIONES")
    print("=" * 80)

    diccionario_solucionable = []
    ambiguos = []
    otros = []

    for e in analisis:
        titulo_lower = e['titulo'].lower()
        tipo = e['tipo_error']

        # Evaluar si se puede resolver con diccionario
        solucion = None
        termino_propuesto = None
        label_esco_propuesto = None

        if tipo == 'nivel_jerarquico':
            # Casos donde el nivel jerarquico del titulo no matchea con ESCO
            if 'gerente de ventas' in titulo_lower:
                solucion = "DICCIONARIO: Ya existe pero bypass no activa (titulo tiene palabras extra)"
                termino_propuesto = None  # Ya existe
            elif 'ejecutiv' in titulo_lower and 'cuenta' in titulo_lower:
                solucion = "DICCIONARIO: Agregar variante 'ejecutiva comercial de cuentas'"
                termino_propuesto = "ejecutiva comercial de cuentas"
                label_esco_propuesto = "representante comercial"

        elif tipo == 'sector_funcion':
            # El sector/funcion asignado no corresponde
            if 'asistente' in titulo_lower and 'administrativo' in titulo_lower:
                solucion = "ACEPTABLE: Empleado administrativo es correcto para asistente administrativo"
            elif 'asistente' in titulo_lower and 'direccion' in titulo_lower:
                solucion = "ACEPTABLE: Empleado administrativo es correcto para asistente de direccion"

        elif tipo == 'sector_especifico':
            # Demasiado especifico (ej: asesor de ventas -> asesor de seguros)
            if 'asesor' in titulo_lower and 'venta' in titulo_lower:
                solucion = "DICCIONARIO: Agregar 'asesor de ventas' -> vendedor/vendedora"
                termino_propuesto = "asesor de ventas"
                label_esco_propuesto = "vendedor/vendedora"

        elif tipo == 'programa_general':
            # Programa de pasantias - dificil de resolver
            solucion = "AMBIGUO: Programa de pasantias no tiene ocupacion especifica"

        elif tipo == 'tipo_ocupacion':
            # Tipo de ocupacion incorrecta
            if 'farmaceutic' in titulo_lower:
                solucion = "REVISAR: Farmaceutico ya tiene bypass pero comentario antiguo"

        elif tipo == 'nivel_profesional':
            # Nivel profesional (medico vs esteticista)
            if 'medic' in titulo_lower or 'dermatolog' in titulo_lower:
                solucion = "REVISAR: Medico generalista es correcto, comentario habla de esteticista"

        elif tipo == 'tipo_funcion':
            # Funcion incorrecta
            if 'supervisor' in titulo_lower and 'auto' in titulo_lower:
                solucion = "DICCIONARIO: Agregar 'supervisor administracion autos'"
                termino_propuesto = "supervisor administracion"
                label_esco_propuesto = "supervisor administrativo"

        print(f"\n[{e['id']}] {e['titulo'][:40]}...")
        print(f"    Tipo: {tipo}")
        print(f"    ESCO actual: {e['esco']}")
        if solucion:
            print(f"    SOLUCION: {solucion}")
        else:
            print(f"    SOLUCION: Requiere analisis manual")

        if termino_propuesto:
            diccionario_solucionable.append({
                'termino': termino_propuesto,
                'label_esco': label_esco_propuesto,
                'caso': e['id']
            })

    # Resumen
    print("\n" + "=" * 80)
    print("PROPUESTA DE TERMINOS PARA DICCIONARIO")
    print("=" * 80)

    if diccionario_solucionable:
        for d in diccionario_solucionable:
            print(f"  '{d['termino']}' -> '{d['label_esco']}' (caso {d['caso']})")
    else:
        print("  No hay terminos adicionales propuestos automaticamente")

    print("\n" + "-" * 80)
    print("CASOS QUE REQUIEREN REVISION MANUAL:")
    print("-" * 80)
    print("""
1. Programa de pasantias (1118027188): No tiene ocupacion ESCO clara
   -> Podria ignorarse o crear categoria especial

2. Farmaceutico (1118027662): Comentario dice 'ingeniero farmaceutico' pero
   ESCO actual es 'Farmaceutico/farmaceutica' - POSIBLEMENTE YA CORRECTO

3. Medica/Dermatologa (1118017586): Comentario dice 'esteticista' pero ESCO
   actual es 'Medico generalista' - POSIBLEMENTE YA CORRECTO

4. Gerente de Ventas (1117984105): Bypass no activa por palabras extra en titulo
   -> Requiere matching mas flexible o normalizar titulo

5. Ejecutiva/o Comercial de Cuentas (1118028038): Variante femenina no matchea
   -> Agregar variantes al diccionario

6. Asistente Direccion/Administrativo (1117960588, 1117961954): Ya matchean
   'Empleado administrativo' - REVISAR SI ES CORRECTO

7. Asesor de Ventas (1118031991, 1118028048): Matchea 'Asesor de seguros'
   -> Agregar 'asesor de ventas' al diccionario

8. Supervisor Administracion Autos (2165301): Matchea construccion
   -> Caso dificil, combina supervisor + administracion + autos
""")

if __name__ == '__main__':
    main()
