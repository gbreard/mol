#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
limpiar_titulos.py v2.0
========================
Limpia titulos de ofertas eliminando ruido empresarial/geografico.
Lee patrones desde config/nlp_titulo_limpieza.json

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
from typing import Dict, Any, List

base = Path(__file__).parent
config_dir = base.parent / "config"


def cargar_config() -> Dict[str, Any]:
    """Carga configuracion desde JSON"""
    config_path = config_dir / "nlp_titulo_limpieza.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# Cargar config una vez al importar
_CONFIG = cargar_config()


def limpiar_titulo(titulo: str, config: Dict[str, Any] = None) -> str:
    """
    Limpia un titulo de oferta eliminando ruido.

    Args:
        titulo: Titulo original de la oferta
        config: Config opcional (usa _CONFIG global si no se pasa)

    Returns:
        Titulo limpio, solo con la ocupacion

    Ejemplos:
        "Gerente de Operaciones - Gastronomia corporativa" -> "Gerente de Operaciones"
        "Analista de Cultivo - Roque Perez - BA" -> "Analista de Cultivo"
        "Representante Comercial (Consumo Masivo)" -> "Representante Comercial"
        "Venado Tuerto -Gerente de Ventas importante Concesionario" -> "Gerente de Ventas"
    """
    if not titulo:
        return titulo

    if config is None:
        config = _CONFIG

    original = titulo

    # 0. Eliminar ubicaciones AL INICIO del titulo
    ciudades = config.get("ciudades_inicio", {}).get("lista", [])
    for ciudad in ciudades:
        titulo = re.sub(rf'^{re.escape(ciudad)}\s*[-–]\s*', '', titulo, flags=re.IGNORECASE)

    # 1. Eliminar codigos de referencia
    for patron_info in config.get("codigos_referencia", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 2. Eliminar palabras de modalidad al final
    modalidades = config.get("modalidad_final", {}).get("palabras", [])
    if modalidades:
        modalidad_pattern = '|'.join(re.escape(m) for m in modalidades)
        titulo = re.sub(rf'\s*\(?\s*({modalidad_pattern})\s*\)?$', '', titulo, flags=re.IGNORECASE)

    # 3. Eliminar zonas/ubicaciones al final
    for patron_info in config.get("zonas_ubicaciones", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 4. Eliminar parentesis especificos
    for patron_info in config.get("parentesis_eliminar", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 5. Eliminar texto despues de guion que sea contexto empresarial
    palabras_contexto = config.get("contexto_empresarial", {}).get("palabras", [])
    for palabra in palabras_contexto:
        # Con guion
        titulo = re.sub(rf'\s*-\s*[^-]*{re.escape(palabra)}[^-]*$', '', titulo, flags=re.IGNORECASE)
        # Sin guion (despues de eliminar ubicacion al inicio)
        titulo = re.sub(rf'\s+{re.escape(palabra)}\s+.*$', '', titulo, flags=re.IGNORECASE)

    # 6. Limpieza final
    for patron_info in config.get("limpieza_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        reemplazo = patron_info.get("reemplazo", "")
        if patron:
            titulo = re.sub(patron, reemplazo, titulo)

    titulo = titulo.strip()

    return titulo


def agregar_columna_titulo_limpio():
    """Agrega columna titulo_limpio a ofertas_nlp si no existe"""
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    c = conn.cursor()

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

    # Cargar IDs del Gold Set (usar expandido si existe)
    gold_set_100 = base / 'gold_set_nlp_100_ids.json'
    gold_set_49 = base / 'gold_set_manual_v2.json'

    if gold_set_100.exists():
        with open(gold_set_100, 'r', encoding='utf-8') as f:
            ids = json.load(f)
        print(f"Usando Gold Set expandido: {len(ids)} ofertas")
    else:
        with open(gold_set_49, 'r', encoding='utf-8') as f:
            gold_set = json.load(f)
        ids = [str(x['id_oferta']) for x in gold_set]
        print(f"Usando Gold Set original: {len(ids)} ofertas")

    print(f"\nProcesando {len(ids)} titulos...")
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
            if cambios <= 10:  # Solo mostrar primeros 10
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
    print("LIMPIEZA DE TITULOS v2.0 - Config desde JSON")
    print("=" * 70)

    # Mostrar config cargada
    print(f"\nConfig cargada: {len(_CONFIG)} secciones")
    for key in _CONFIG:
        if not key.startswith('_'):
            print(f"  - {key}")

    # Tests unitarios
    print("\nTESTS UNITARIOS:")
    print("-" * 70)
    tests = [
        ("Gerente de Operaciones - Gastronomia corporativa y Facility management", "Gerente de Operaciones"),
        ("Analista de Cultivo - Roque Perez - BA", "Analista de Cultivo - Roque Perez"),
        ("Representante Comercial (Consumo Masivo / Grandes Cuentas)", "Representante Comercial"),
        ("Operario de Almacen/Logistica Z/Escobar", "Operario de Almacen/Logistica"),
        ("Repositor/a Externo/a (Eventual) Moreno", "Repositor/a Externo/a"),
        ("Administrativa Comercio Exterior (req199380) Eventual", "Administrativa Comercio Exterior"),
        ("Venado Tuerto -Gerente de Ventas importante Concesionario Oficial Maquinaria Agricola", "Gerente de Ventas"),
        ("Gerente General para Maderera (PYME)", "Gerente General para Maderera"),
        ("Vendedor con Experiencia (Corredor)", "Vendedor con Experiencia"),
        ("Asistente Compliance (part time)", "Asistente Compliance"),
        ("Chofer - Repartidor", "Chofer - Repartidor"),
        ("Mozo/Moza", "Mozo/Moza"),
    ]

    ok = 0
    for original, esperado in tests:
        resultado = limpiar_titulo(original)
        status = "OK" if resultado == esperado else "FAIL"
        if status == "OK":
            ok += 1
        print(f"  [{status}] {original[:50]}...")
        if status == "FAIL":
            print(f"       Esperado: {esperado}")
            print(f"       Obtenido: {resultado}")

    print(f"\nTests: {ok}/{len(tests)} OK")

    # Agregar columna y procesar
    print("\n" + "=" * 70)
    agregar_columna_titulo_limpio()
    procesar_gold_set()
