#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica si las nuevas reglas R16-R22 corrigen los 10 casos INCORRECTO."""
import sys
import io
sys.path.insert(0, "D:/OEDE/Webscrapping/database")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sqlite3
from match_ofertas_v2 import match_oferta_v2_bge, obtener_ofertas_nlp

DB_PATH = "D:/OEDE/Webscrapping/database/bumeran_scraping.db"

# Los 10 casos INCORRECTO de la revision anterior
casos_incorrecto = [
    ("2130257", "EMPLEADA/O VENTA MOSTRADOR CASA ELECTRICIDAD", "vendedor ferreteria", "R20"),
    ("2145263", "Consultor Junior de Liquidacion de Sueldos", "payroll", "R18"),
    ("2149508", "Atencion a Mostrador Pasteleria / Barista", "Barista", "R16"),
    ("2151075", "Asistente Compliance", "compliance/abogado", "R17"),
    ("2155040", "ENCARGADAS/OS - HELADERAS/OS - BARISTAS", "Barista", "R16"),
    ("2155621", "Analista de Customer Service", "atencion cliente", "R15"),
    ("2156388", "Lider de Atencion al Cliente", "Supervisor call center", "R21"),
    ("1118026719", "Project Manager IT", "Director proyectos", "R19"),
    ("1118027243", "Responsable de Legales", "Abogado", "R17"),
    ("1118028168", "Coordinador de Instalaciones", "Tecnico mantenimiento", "R22"),
]

print("=" * 80)
print("VERIFICACION DE NUEVAS REGLAS R16-R22")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Obtener todas las ofertas NLP de una vez
ids_list = [c[0] for c in casos_incorrecto]
ofertas_nlp = obtener_ofertas_nlp(conn, ids=ids_list)

# Crear lookup por id_oferta
ofertas_by_id = {str(o["id_oferta"]): o for o in ofertas_nlp}

corregidos = 0
no_corregidos = []

for id_oferta, titulo, esperado, regla_esperada in casos_incorrecto:
    oferta = ofertas_by_id.get(id_oferta)
    if not oferta:
        print(f"\n[ERROR] ID {id_oferta} - No encontrada en BD")
        no_corregidos.append((id_oferta, titulo, esperado, regla_esperada, "NO ENCONTRADA", ""))
        continue

    result = match_oferta_v2_bge(oferta, conn)

    if result:
        metodo = result.metodo or ""
        match = (result.esco_label or "")[:50]
        isco = result.isco_code or ""

        # Verificar si la regla esperada se aplico
        regla_aplicada = regla_esperada.lower() in metodo.lower() or f"regla_{regla_esperada}".lower() in metodo.lower()

        if regla_aplicada:
            print(f"\n[OK] ID {id_oferta}")
            print(f"     Titulo: {titulo[:50]}")
            print(f"     Match: {match} (ISCO {isco})")
            print(f"     Metodo: {metodo}")
            print(f"     Regla {regla_esperada} APLICADA")
            corregidos += 1
        else:
            print(f"\n[??] ID {id_oferta}")
            print(f"     Titulo: {titulo[:50]}")
            print(f"     Match: {match} (ISCO {isco})")
            print(f"     Metodo: {metodo}")
            print(f"     Se esperaba regla: {regla_esperada}")
            no_corregidos.append((id_oferta, titulo, esperado, regla_esperada, match, metodo))
    else:
        print(f"\n[ERROR] ID {id_oferta} - No se pudo procesar")
        no_corregidos.append((id_oferta, titulo, esperado, regla_esperada, "ERROR", "ERROR"))

conn.close()

print("\n" + "=" * 80)
print(f"RESUMEN: {corregidos}/10 casos corregidos por nuevas reglas")
print("=" * 80)

if no_corregidos:
    print("\nCasos que aun necesitan atencion:")
    for id_oferta, titulo, esperado, regla_esperada, match_actual, metodo_actual in no_corregidos:
        print(f"  - ID {id_oferta}: {titulo[:40]}...")
        print(f"    Esperado: {esperado} (via {regla_esperada})")
        print(f"    Actual: {match_actual} ({metodo_actual})")
