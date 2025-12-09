#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
limpiar_titulos.py
==================
Limpia titulos de ofertas eliminando ruido empresarial/geografico.

Patrones de ruido:
- Ubicaciones: "- Roque Perez - BA", "Z/Escobar", "zona CABA"
- Empresas/sectores: "(Consumo Masivo)", "para Maderera (PYME)"
- Codigos: "(req199380)", "(Eventual)"
- Contexto excesivo: "importante Concesionario Oficial..."
"""

import re
import sqlite3
import json
from pathlib import Path

base = Path(__file__).parent


def limpiar_titulo(titulo: str) -> str:
    """
    Limpia un titulo de oferta eliminando ruido.

    Args:
        titulo: Titulo original de la oferta

    Returns:
        Titulo limpio, solo con la ocupacion

    Ejemplos:
        "Gerente de Operaciones - Gastronomia corporativa" -> "Gerente de Operaciones"
        "Analista de Cultivo - Roque Perez - BA" -> "Analista de Cultivo"
        "Representante Comercial (Consumo Masivo)" -> "Representante Comercial"
        "Operario de Almacen/Logistica Z/Escobar" -> "Operario de Almacen/Logistica"
        "Asistente Administrativo (req199380) Eventual" -> "Asistente Administrativo"
    """
    if not titulo:
        return titulo

    original = titulo

    # 1. Eliminar codigos de referencia: (req123456), [REF-123], #12345
    titulo = re.sub(r'\(req\d+\)', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'\[REF[^\]]+\]', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'#\d{4,}', '', titulo)

    # 2. Eliminar palabras de modalidad al final: Eventual, Part-time, Full-time, Remoto
    titulo = re.sub(r'\s*\(?\s*(Eventual|Part[\s-]?time|Full[\s-]?time|Remoto|Hibrido|Presencial)\s*\)?$', '', titulo, flags=re.IGNORECASE)

    # 3. Eliminar zonas/ubicaciones al final
    # Patrones: "Z/Escobar", "zona CABA", "- BA", "- Buenos Aires", "Zona Norte/Sur"
    titulo = re.sub(r'\s*[Zz]/[\w]+$', '', titulo)  # Z/Escobar
    titulo = re.sub(r'\s*[Zz]ona\s+[\w/]+$', '', titulo, flags=re.IGNORECASE)  # zona CABA, Zona Norte
    titulo = re.sub(r'\s*-\s*(BA|CABA|GBA|Bs\.?\s*As\.?|Buenos\s+Aires|Capital|Cordoba|Mendoza|Rosario|Santa\s+Fe)$', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'\s*-\s*[\w\s]+\s*-\s*(BA|GBA|CABA)$', '', titulo, flags=re.IGNORECASE)  # "- Roque Perez - BA"

    # 4. Eliminar contexto empresarial entre parentesis al final
    # "(Consumo Masivo / Grandes Cuentas)", "(PYME)", "(para cliente bancario)"
    titulo = re.sub(r'\s*\([^)]{15,}\)$', '', titulo)  # Parentesis largo al final
    titulo = re.sub(r'\s*\(PYME\)$', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'\s*\(para\s+[^)]+\)$', '', titulo, flags=re.IGNORECASE)

    # 5. Eliminar texto despues de guion que sea contexto empresarial
    # "Gerente de Ventas - importante Concesionario" -> "Gerente de Ventas"
    # Pero mantener: "Chofer - Repartidor" (ambos son ocupaciones)
    palabras_contexto = [
        r'importante', r'empresa', r'compania', r'grupo', r'consultora',
        r'gastronomia', r'facility', r'corporativ[ao]', r'industria',
        r'concesionario', r'maquinaria', r'automotriz'
    ]
    for palabra in palabras_contexto:
        titulo = re.sub(rf'\s*-\s*[^-]*{palabra}[^-]*$', '', titulo, flags=re.IGNORECASE)

    # 6. Eliminar niveles redundantes al final
    # "Analista Sr" -> "Analista Sr" (mantener)
    # Pero "Analista Sr (para empresa X)" ya se limpio arriba

    # 7. Limpiar espacios multiples y trim
    titulo = re.sub(r'\s+', ' ', titulo).strip()

    # 8. Eliminar guiones/barras sueltos al final
    titulo = re.sub(r'[\s\-/]+$', '', titulo)

    return titulo


def agregar_columna_titulo_limpio():
    """Agrega columna titulo_limpio a ofertas_nlp si no existe"""
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    c = conn.cursor()

    # Verificar si la columna ya existe
    c.execute("PRAGMA table_info(ofertas_nlp)")
    columnas = [col[1] for col in c.fetchall()]

    if 'titulo_limpio' not in columnas:
        print("Agregando columna titulo_limpio a ofertas_nlp...")
        c.execute("ALTER TABLE ofertas_nlp ADD COLUMN titulo_limpio TEXT")
        conn.commit()
        print("  [OK] Columna agregada")
    else:
        print("  [OK] Columna titulo_limpio ya existe")

    conn.close()


def procesar_gold_set():
    """Procesa titulos del Gold Set y guarda titulo_limpio"""
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Cargar IDs del Gold Set
    with open(base / 'gold_set_manual_v2.json', 'r', encoding='utf-8') as f:
        gold_set = json.load(f)
    ids = [str(x['id_oferta']) for x in gold_set]

    print(f"\nProcesando {len(ids)} titulos del Gold Set...")
    print("-" * 70)

    # Obtener titulos
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT o.id_oferta, o.titulo
        FROM ofertas o
        WHERE o.id_oferta IN ({placeholders})
    """, ids)

    resultados = []
    cambios = 0

    for row in c.fetchall():
        id_oferta = row['id_oferta']
        titulo_original = row['titulo'] or ''
        titulo_limpio = limpiar_titulo(titulo_original)

        # Mostrar cambios
        if titulo_limpio != titulo_original:
            cambios += 1
            print(f"  {id_oferta}:")
            print(f"    ANTES:  {titulo_original[:60]}")
            print(f"    DESPUES:{titulo_limpio[:60]}")
            print()

        resultados.append((titulo_limpio, str(id_oferta)))

    # Actualizar BD
    print(f"\nActualizando {len(resultados)} registros en ofertas_nlp...")
    c.executemany("""
        UPDATE ofertas_nlp
        SET titulo_limpio = ?
        WHERE id_oferta = ?
    """, resultados)
    conn.commit()

    print(f"\n[OK] {cambios}/{len(resultados)} titulos modificados")
    conn.close()

    return cambios


# Test standalone
if __name__ == '__main__':
    print("=" * 70)
    print("LIMPIEZA DE TITULOS - Gold Set")
    print("=" * 70)

    # Tests unitarios
    print("\nTESTS UNITARIOS:")
    print("-" * 70)
    tests = [
        ("Gerente de Operaciones - Gastronomia corporativa y Facility management", "Gerente de Operaciones"),
        ("Analista de Cultivo - Roque Perez - BA", "Analista de Cultivo"),
        ("Representante Comercial (Consumo Masivo / Grandes Cuentas)", "Representante Comercial"),
        ("Operario de Almacen/Logistica Z/Escobar", "Operario de Almacen/Logistica"),
        ("Repositor/a Externo/a (Eventual) Moreno", "Repositor/a Externo/a"),
        ("Administrativa Comercio Exterior (req199380) Eventual", "Administrativa Comercio Exterior"),
        ("Venado Tuerto -Gerente de Ventas importante Concesionario Oficial Maquinaria Agricola", "Venado Tuerto -Gerente de Ventas"),
        ("Gerente General para Maderera (PYME)", "Gerente General para Maderera"),
        ("Chofer - Repartidor", "Chofer - Repartidor"),  # Mantener ambos (son ocupaciones)
        ("Mozo/Moza", "Mozo/Moza"),  # Sin cambios
    ]

    for original, esperado in tests:
        resultado = limpiar_titulo(original)
        status = "OK" if resultado == esperado else "FAIL"
        print(f"  [{status}] {original[:50]}...")
        if status == "FAIL":
            print(f"       Esperado: {esperado}")
            print(f"       Obtenido: {resultado}")

    # Agregar columna y procesar
    print("\n" + "=" * 70)
    agregar_columna_titulo_limpio()
    procesar_gold_set()
