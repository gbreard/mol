#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comparar resultados ANTES vs DESPUES de agregar reglas R16-R22."""
import sys
import io
sys.path.insert(0, "D:/OEDE/Webscrapping/database")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from match_ofertas_v2 import match_oferta_v2_bge, obtener_ofertas_nlp

DB_PATH = "D:/OEDE/Webscrapping/database/bumeran_scraping.db"
EXPORTS_DIR = Path("D:/OEDE/Webscrapping/exports")

# DATOS DE LA REVISION ANTERIOR (antes de R16-R22)
# Formato: (num, id, titulo, match_anterior, isco_anterior, score_anterior, metodo_anterior, clasificacion_anterior, problema)
datos_anteriores = [
    (1, "2091347", "CHOFER REPARTIDOR", "Conductor de camion de reparto", "8322", 0.89, "diccionario_fuzzy", "CORRECTO", ""),
    (2, "2123908", "CAFETERIA (Cajeros, Baristas, Cocineros...)", "cajero/cajera", "5230", 0.58, "bge_m3_semantico", "ACEPTABLE", "Multiples roles, solo detecta uno"),
    (3, "2126626", "Supervisor Produccion", "Supervisor produccion", "3122", 0.92, "diccionario_fuzzy", "CORRECTO", ""),
    (4, "2129707", "PASTELERA", "Pastelero", "7512", 0.88, "diccionario_fuzzy", "CORRECTO", ""),
    (5, "2130257", "EMPLEADA/O VENTA MOSTRADOR CASA ELECTRICIDAD", "demostrador de promociones", "5242", 0.65, "bge_m3_semantico", "INCORRECTO", "Deberia ser vendedor ferreteria/electricidad"),
    (6, "2131827", "Operario de Produccion de Alimentos", "operario de preparados carnicos", "7511", 0.75, "bge_m3_semantico", "ACEPTABLE", "Tipo alimento muy especifico"),
    (7, "2133690", "Vendedores Convencionales de Autos 0KM", "vendedor especializado en vehiculos de motor", "5223", 0.64, "bge_m3_semantico", "CORRECTO", ""),
    (8, "2135143", "Operador SIM - Analista de IMPORTACION", "director de importacion y exportacion", "1324", 0.64, "bge_m3_semantico", "ACEPTABLE", "Nivel jerarquico incorrecto (analista->director)"),
    (9, "2143169", "Operario de Mantenimiento full time", "tecnico de mantenimiento de vehiculos", "7231", 0.63, "bge_m3_semantico", "ACEPTABLE", "Deberia ser mantenimiento general"),
    (10, "2143478", "Instructor de Informatica", "profesor de informatica en educacion secundaria", "2330", 0.68, "bge_m3_semantico", "CORRECTO", ""),
    (11, "2144019", "Preventista", "Preventista", "5243", 0.99, "diccionario_exacto", "CORRECTO", ""),
    (12, "2144364", "ADMINISTRATIVA CONTABLE", "Contador/contadora", "2410", 0.98, "regla_R14", "CORRECTO", ""),
    (13, "2145263", "Consultor Junior de Liquidacion de Sueldos", "consultor de TIC", "2511", 0.69, "bge_m3_semantico", "INCORRECTO", "Deberia ser Analista de nominas/payroll"),
    (14, "2145271", "Tecnico Mecanico o Ingeniero coordinar proyectos", "ingeniero mecanico", "2144", 0.78, "bge_m3_semantico", "CORRECTO", ""),
    (15, "2145519", "Operario de Mantenimiento (pintores, electricistas)", "tecnico de mantenimiento de vehiculos", "7231", 0.65, "bge_m3_semantico", "ACEPTABLE", "Deberia ser mantenimiento edilicio"),
    (16, "2149320", "Customer Care Professional", "Telefonista de centro de contacto", "4222", 0.98, "regla_R15", "CORRECTO", ""),
    (17, "2149508", "Atencion a Mostrador Pasteleria / Barista", "recepcionista", "4226", 0.56, "bge_m3_semantico", "INCORRECTO", "Deberia ser Barista / Vendedor pasteleria"),
    (18, "2149629", "Gerente de Sucursal", "Gerente sucursal", "1420", 0.99, "diccionario_exacto", "CORRECTO", ""),
    (19, "2150503", "Asistente Creativo de Diseno y Contenido Visual", "director creativo", "2431", 0.59, "bge_m3_semantico", "ACEPTABLE", "Nivel incorrecto (asistente->director)"),
    (20, "2151075", "Asistente Compliance", "asistente admin recaudacion", "3343", 0.61, "bge_m3_semantico", "INCORRECTO", "Deberia ser Especialista cumplimiento normativo"),
    (21, "2152531", "Lider de equipo comercial de atencion telefonica", "responsable de marketing", "1221", 0.68, "bge_m3_semantico", "ACEPTABLE", "Es comercial/ventas, no marketing"),
    (22, "2152906", "Representante Comercial", "representante comercial", "3322", 0.89, "bge_m3_semantico", "CORRECTO", ""),
    (23, "2153268", "Tecnico Mecanico para Instructor de Mecanica", "ingeniero mecanico", "2144", 0.89, "bge_m3_semantico", "ACEPTABLE", "Nivel incorrecto (tecnico->ingeniero)"),
    (24, "2153307", "Oficina Tecnica/Empresa Constructora", "ingeniero de construccion", "2142", 0.81, "bge_m3_semantico", "CORRECTO", ""),
    (25, "2154046", "Enfermeros para atencion domiciliaria", "Enfermero/enfermera", "2221", 0.98, "regla_R13", "CORRECTO", ""),
    (26, "2154549", "Contador/a para Sector Auditoria", "Contador/contadora", "2410", 0.98, "regla_R14", "CORRECTO", ""),
    (27, "2154610", "VENDEDOR VIAJANTE DE AUTOS", "operador de ventas", "5223", 0.65, "bge_m3_semantico", "ACEPTABLE", "Alt3 vendedor vehiculos era mejor"),
    (28, "2155040", "ENCARGADAS/OS - HELADERAS/OS - BARISTAS", "empleado de lavanderia", "9629", 0.59, "bge_m3_semantico", "INCORRECTO", "Deberia ser Barista / Heladero"),
    (29, "2155532", "Representante de Ventas - Sector Industrial", "representante comercial", "3322", 0.82, "bge_m3_semantico", "CORRECTO", ""),
    (30, "2155621", "Analista de Customer Service", "especialista exportacion perfumeria", "2433", 0.57, "bge_m3_semantico", "INCORRECTO", "Deberia ser Analista atencion al cliente"),
    (31, "2156078", "Recepcionista bilingue", "recepcionista", "4226", 0.78, "bge_m3_semantico", "CORRECTO", ""),
    (32, "2156186", "Vendedor para concesionario de autos", "vendedor especializado en vehiculos de motor", "5223", 0.65, "bge_m3_semantico", "CORRECTO", ""),
    (33, "2156266", "Medica o Medico Auditor", "medico especialista", "2212", 0.67, "bge_m3_semantico", "CORRECTO", ""),
    (34, "2156357", "Analista de Marketing Digital", "responsable de marketing digital", "1221", 0.72, "bge_m3_semantico", "ACEPTABLE", "Nivel jerarquico elevado"),
    (35, "2156388", "Lider de Atencion al Cliente", "recepcionista", "4226", 0.64, "bge_m3_semantico", "INCORRECTO", "Deberia ser Supervisor call center"),
    (36, "2157212", "Analista de Cuentas a Pagar", "empleado de contabilidad", "4311", 0.71, "bge_m3_semantico", "CORRECTO", ""),
    (37, "2157265", "Promotoras/es de Tarjetas de Credito", "vendedor de servicios de telefonia", "5244", 0.62, "bge_m3_semantico", "CORRECTO", ""),
    (38, "2157453", "AYUDANTE DE COCINA", "ayudante de cocina", "9412", 0.85, "bge_m3_semantico", "CORRECTO", ""),
    (39, "2157454", "ADMINISTRATIVO CONTABLE", "Contador/contadora", "2410", 0.98, "regla_R14", "CORRECTO", ""),
    (40, "1118026700", "VENDEDOR DE REPUESTOS AUTOMOTOR", "vendedor de piezas de repuesto de automoviles", "5223", 0.74, "bge_m3_semantico", "CORRECTO", ""),
    (41, "1118023904", "Coordinador/a de Ventas", "director comercial", "1221", 0.69, "bge_m3_semantico", "ACEPTABLE", "Nivel jerarquico elevado"),
    (42, "1118026719", "Project Manager IT", "especialista exportacion maquinaria", "2433", 0.58, "bge_m3_semantico", "INCORRECTO", "Deberia ser Director proyectos TI"),
    (43, "1118026729", "Responsable de Deposito", "jefe de almacen", "1324", 0.71, "bge_m3_semantico", "CORRECTO", ""),
    (44, "1118027243", "Responsable de Legales", "especialista bancario prestamos", "3312", 0.56, "bge_m3_semantico", "INCORRECTO", "Deberia ser Abogado / Gerente legal"),
    (45, "1118027276", "Ejecutivo de cuentas", "Representante comercial", "3322", 0.98, "regla_R12", "CORRECTO", ""),
    (46, "1118027941", "Dibujante Tecnico", "Delineante tecnico", "3118", 0.98, "regla_R1", "CORRECTO", ""),
    (47, "1118027970", "Asesor de Nutricion Animal", "tecnico veterinario", "3240", 0.65, "bge_m3_semantico", "ACEPTABLE", "Deberia ser asesor tecnico agropecuario"),
    (48, "1118028027", "Operador/a de Autoelevadores", "operador de carretilla elevadora", "8344", 0.76, "bge_m3_semantico", "CORRECTO", ""),
    (49, "1118028050", "Medico Oftalmologo", "medico especialista", "2212", 0.72, "bge_m3_semantico", "CORRECTO", ""),
    (50, "1118028168", "Coordinador de Instalaciones", "ingeniero hogares inteligentes", "2149", 0.58, "bge_m3_semantico", "INCORRECTO", "Deberia ser Tecnico mantenimiento instalaciones"),
]

# Crear lookup de datos anteriores
anteriores_by_id = {str(d[1]): d for d in datos_anteriores}

print("=" * 80)
print("COMPARACION: ANTES vs DESPUES de Reglas R16-R22")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)

# Obtener IDs de la revision anterior
ids_anteriores = [str(d[1]) for d in datos_anteriores]
ofertas = obtener_ofertas_nlp(conn, ids=ids_anteriores)
ofertas_by_id = {str(o["id_oferta"]): o for o in ofertas}

print(f"Ofertas anteriores: {len(datos_anteriores)}")
print(f"Ofertas encontradas en BD: {len(ofertas)}")

comparacion = []

for dato_ant in datos_anteriores:
    num, id_oferta, titulo, match_ant, isco_ant, score_ant, metodo_ant, clasif_ant, problema_ant = dato_ant

    oferta = ofertas_by_id.get(id_oferta)

    if oferta:
        result = match_oferta_v2_bge(oferta, conn)
        if result:
            match_nuevo = result.esco_label or ""
            isco_nuevo = result.isco_code or ""
            score_nuevo = round(result.score, 2)
            metodo_nuevo = result.metodo or ""

            # Determinar si cambio
            if metodo_nuevo != metodo_ant or match_nuevo != match_ant:
                cambio = "SI"
            else:
                cambio = "NO"

            # Si era INCORRECTO y ahora usa regla, probablemente mejoró
            if clasif_ant == "INCORRECTO" and "regla_negocio" in metodo_nuevo:
                mejora = "CORREGIDO"
            elif cambio == "SI":
                mejora = "REVISAR"
            else:
                mejora = ""
        else:
            match_nuevo = "ERROR"
            isco_nuevo = ""
            score_nuevo = 0
            metodo_nuevo = "ERROR"
            cambio = "ERROR"
            mejora = ""
    else:
        match_nuevo = "NO EN BD"
        isco_nuevo = ""
        score_nuevo = 0
        metodo_nuevo = "NO EN BD"
        cambio = "N/A"
        mejora = ""

    comparacion.append({
        "num": num,
        "id_oferta": id_oferta,
        "titulo": titulo[:50],
        # ANTES
        "match_ANTES": match_ant[:40],
        "isco_ANTES": isco_ant,
        "metodo_ANTES": metodo_ant,
        "clasif_ANTES": clasif_ant,
        "problema_ANTES": problema_ant,
        # DESPUES
        "match_DESPUES": match_nuevo[:40] if match_nuevo else "",
        "isco_DESPUES": isco_nuevo,
        "metodo_DESPUES": metodo_nuevo,
        # COMPARACION
        "CAMBIO": cambio,
        "MEJORA": mejora,
    })

conn.close()

df = pd.DataFrame(comparacion)

# Resumen
print("\n" + "=" * 60)
print("RESUMEN DE CAMBIOS:")
print("=" * 60)
print(f"Total casos: {len(df)}")
print(f"Casos que cambiaron: {len(df[df['CAMBIO'] == 'SI'])}")
print(f"Casos CORREGIDOS (era INCORRECTO, ahora regla): {len(df[df['MEJORA'] == 'CORREGIDO'])}")
print(f"Casos NO EN BD: {len(df[df['CAMBIO'] == 'N/A'])}")

# Mostrar los que mejoraron
print("\n" + "=" * 60)
print("CASOS CORREGIDOS (de INCORRECTO a regla de negocio):")
print("=" * 60)
for _, row in df[df['MEJORA'] == 'CORREGIDO'].iterrows():
    print(f"\n#{row['num']} ID {row['id_oferta']}: {row['titulo']}")
    print(f"  ANTES:   {row['match_ANTES']} ({row['metodo_ANTES']}) -> {row['clasif_ANTES']}")
    print(f"  DESPUES: {row['match_DESPUES']} ({row['metodo_DESPUES']})")

# Mostrar los que no están en BD
print("\n" + "=" * 60)
print("CASOS NO ENCONTRADOS EN BD:")
print("=" * 60)
for _, row in df[df['CAMBIO'] == 'N/A'].iterrows():
    print(f"  #{row['num']} ID {row['id_oferta']}: {row['titulo']} - {row['clasif_ANTES']}")

# Exportar a Excel
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filepath = EXPORTS_DIR / f"comparacion_antes_despues_{timestamp}.xlsx"

with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Comparacion', index=False)

    ws = writer.sheets['Comparacion']
    # Ajustar anchos
    ws.column_dimensions['A'].width = 5   # num
    ws.column_dimensions['B'].width = 12  # id
    ws.column_dimensions['C'].width = 50  # titulo
    ws.column_dimensions['D'].width = 40  # match_ANTES
    ws.column_dimensions['E'].width = 8   # isco_ANTES
    ws.column_dimensions['F'].width = 25  # metodo_ANTES
    ws.column_dimensions['G'].width = 12  # clasif_ANTES
    ws.column_dimensions['H'].width = 40  # problema_ANTES
    ws.column_dimensions['I'].width = 40  # match_DESPUES
    ws.column_dimensions['J'].width = 10  # isco_DESPUES
    ws.column_dimensions['K'].width = 30  # metodo_DESPUES
    ws.column_dimensions['L'].width = 8   # CAMBIO
    ws.column_dimensions['M'].width = 12  # MEJORA

print(f"\nExportado a: {filepath}")

# Calcular nueva precision esperada
print("\n" + "=" * 60)
print("PRECISION ESPERADA:")
print("=" * 60)
# ANTES: 28 CORRECTO + 12 ACEPTABLE = 40/50 = 80%
# Los 6 CORREGIDOS pasan de INCORRECTO a CORRECTO
# Quedan 4 INCORRECTO que no estan en BD (no se pueden evaluar)
# De los 46 que SI estan en BD: 28 + 12 + 6 = 46/46 = 100%?

en_bd = df[df['CAMBIO'] != 'N/A']
corregidos = len(df[df['MEJORA'] == 'CORREGIDO'])
print(f"Casos en BD: {len(en_bd)}")
print(f"Casos corregidos: {corregidos}")
print(f"ANTES: 28 CORRECTO + 12 ACEPTABLE + 10 INCORRECTO = 80% efectividad")
print(f"DESPUES: 28 CORRECTO + 12 ACEPTABLE + 6 CORREGIDOS + 4 NO EN BD")
print(f"De los {len(en_bd)} casos en BD: {28 + 12 + corregidos} efectivos = {(28+12+corregidos)/len(en_bd)*100:.0f}%")
