# -*- coding: utf-8 -*-
"""
Extractor de Códigos ISCO desde RDF de ESCO
Extrae todas las ocupaciones con sus códigos ISCO directamente del archivo RDF
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
from pathlib import Path
import rdflib
from rdflib.namespace import SKOS, RDF

# Paths
RDF_PATH = Path(r"D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf")
ESCO_DIR = Path(r"D:\Trabajos en PY\EPH-ESCO\07_esco_data")
OUTPUT_PATH = ESCO_DIR / "esco_ocupaciones_con_isco_completo.json"

# Namespace ESCO
ESCO_MODEL = rdflib.Namespace("http://data.europa.eu/esco/model#")
ESCO_RESOURCE = rdflib.Namespace("http://data.europa.eu/esco/")

print("=" * 80)
print("EXTRACCIÓN DE CÓDIGOS ISCO DESDE RDF")
print("=" * 80)

if not RDF_PATH.exists():
    print(f"\n[ERROR] No se encontró el archivo RDF: {RDF_PATH}")
    sys.exit(1)

print(f"\n[LOAD] Cargando RDF: {RDF_PATH.name}")
print(f"[INFO] Tamaño: {RDF_PATH.stat().st_size / (1024**3):.2f} GB")
print("[WAIT] Esto puede tomar varios minutos...")

# Cargar grafo RDF
g = rdflib.Graph()
try:
    g.parse(RDF_PATH, format="xml")
    print(f"[OK] RDF cargado exitosamente")
    print(f"[INFO] Total triples: {len(g):,}")
except Exception as e:
    print(f"[ERROR] Error cargando RDF: {e}")
    sys.exit(1)

print("\n[PROCESS] Extrayendo ocupaciones con códigos ISCO...")

# Query SPARQL para extraer ocupaciones con ISCO
query = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX esco: <http://data.europa.eu/esco/model#>

SELECT ?occupation ?labelES ?labelEN ?isco
WHERE {
    ?occupation a skos:Concept .

    # Label en español
    OPTIONAL {
        ?occupation skos:prefLabel ?labelES .
        FILTER (lang(?labelES) = "es")
    }

    # Label en inglés
    OPTIONAL {
        ?occupation skos:prefLabel ?labelEN .
        FILTER (lang(?labelEN) = "en")
    }

    # Código ISCO (notation)
    OPTIONAL {
        ?occupation skos:notation ?isco .
    }

    # Filtrar solo ocupaciones (no skills)
    FILTER (CONTAINS(STR(?occupation), "/occupation/"))
}
"""

results = g.query(query)
print(f"[OK] Query ejecutada, procesando resultados...")

ocupaciones = {}
stats = {
    'total': 0,
    'con_isco': 0,
    'sin_isco': 0,
    'con_label_es': 0,
    'con_label_en': 0,
    'isco_4d': 0,
    'isco_3d': 0,
    'isco_2d': 0,
    'isco_1d': 0
}

for row in results:
    occ_uri = str(row.occupation)
    occ_id = occ_uri.split('/')[-1]

    label_es = str(row.labelES) if row.labelES else None
    label_en = str(row.labelEN) if row.labelEN else None
    isco = str(row.isco) if row.isco else None

    # Crear o actualizar entrada
    if occ_id not in ocupaciones:
        ocupaciones[occ_id] = {
            'uri': occ_uri,
            'label_es': label_es,
            'label_en': label_en,
            'isco': isco,
            'alt_labels_es': [],
            'alt_labels_en': []
        }
        stats['total'] += 1
    else:
        # Actualizar con mejor información
        if label_es and not ocupaciones[occ_id]['label_es']:
            ocupaciones[occ_id]['label_es'] = label_es
        if label_en and not ocupaciones[occ_id]['label_en']:
            ocupaciones[occ_id]['label_en'] = label_en
        if isco and not ocupaciones[occ_id]['isco']:
            ocupaciones[occ_id]['isco'] = isco

    # Estadísticas
    if label_es:
        stats['con_label_es'] += 1
    if label_en:
        stats['con_label_en'] += 1
    if isco:
        stats['con_isco'] += 1

print(f"\n[OK] Procesadas {stats['total']} ocupaciones únicas")

# Procesar códigos ISCO y generar jerarquía
print("\n[PROCESS] Procesando códigos ISCO y generando jerarquía...")

for occ_id, occ_data in ocupaciones.items():
    isco = occ_data.get('isco')

    if isco:
        # Limpiar código ISCO: puede tener formato "2359.4" o "2411.1.10"
        isco_clean = isco.strip()

        # Extraer solo dígitos (remover puntos)
        isco_digits = isco_clean.replace('.', '')

        if isco_digits.isdigit() and len(isco_digits) >= 4:
            # Usar los primeros 4 dígitos como código ISCO-08
            isco_4d = isco_digits[:4]

            occ_data['codigo_isco'] = isco_clean  # Original con puntos
            occ_data['codigo_isco_4d'] = isco_4d
            occ_data['codigo_isco_3d'] = isco_4d[:3]
            occ_data['codigo_isco_2d'] = isco_4d[:2]
            occ_data['codigo_isco_1d'] = isco_4d[0]

            stats['isco_4d'] += 1
        elif isco_digits.isdigit() and len(isco_digits) == 3:
            occ_data['codigo_isco'] = isco_clean
            occ_data['codigo_isco_3d'] = isco_digits
            occ_data['codigo_isco_2d'] = isco_digits[:2]
            occ_data['codigo_isco_1d'] = isco_digits[0]
            stats['isco_3d'] += 1
        elif isco_digits.isdigit() and len(isco_digits) == 2:
            occ_data['codigo_isco'] = isco_clean
            occ_data['codigo_isco_2d'] = isco_digits
            occ_data['codigo_isco_1d'] = isco_digits[0]
            stats['isco_2d'] += 1
        elif isco_digits.isdigit() and len(isco_digits) == 1:
            occ_data['codigo_isco'] = isco_clean
            occ_data['codigo_isco_1d'] = isco_digits
            stats['isco_1d'] += 1
    else:
        stats['sin_isco'] += 1

# Guardar resultados
print(f"\n[SAVE] Guardando resultados en: {OUTPUT_PATH.name}")

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(ocupaciones, f, indent=2, ensure_ascii=False)

print(f"[OK] Guardado exitosamente")

# Mostrar estadísticas
print("\n" + "=" * 80)
print("ESTADÍSTICAS DE EXTRACCIÓN")
print("=" * 80)
print(f"\nTotal ocupaciones extraídas: {stats['total']:,}")
print(f"Con label español: {stats['con_label_es']:,}")
print(f"Con label inglés: {stats['con_label_en']:,}")
print(f"\nCódigos ISCO:")
print(f"  Con código ISCO: {stats['con_isco']:,} ({stats['con_isco']/stats['total']*100:.1f}%)")
print(f"  Sin código ISCO: {stats['sin_isco']:,} ({stats['sin_isco']/stats['total']*100:.1f}%)")
print(f"\nDistribución por nivel:")
print(f"  ISCO 4 dígitos: {stats['isco_4d']:,}")
print(f"  ISCO 3 dígitos: {stats['isco_3d']:,}")
print(f"  ISCO 2 dígitos: {stats['isco_2d']:,}")
print(f"  ISCO 1 dígito: {stats['isco_1d']:,}")

# Mostrar ejemplos
print(f"\n[MUESTRA] Primeras 5 ocupaciones con ISCO 4D:")
ejemplos = [(occ_id, occ) for occ_id, occ in ocupaciones.items()
            if occ.get('codigo_isco_4d')][:5]

for occ_id, occ in ejemplos:
    print(f"  {occ['label_es']}: {occ['codigo_isco_4d']}")

print("\n" + "=" * 80)
print("EXTRACCIÓN COMPLETADA")
print("=" * 80)
