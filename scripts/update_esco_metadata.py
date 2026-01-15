#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actualiza la metadata de ocupaciones ESCO con códigos numéricos de la API oficial.

Obtiene para cada ocupación:
- esco_code: Código numérico ESCO (ej: "5244.1")
- esco_label: Label en español
- isco_code: Código ISCO-08 4 dígitos (ej: "5244")
- isco_label: Label ISCO en español

Uso:
    python scripts/update_esco_metadata.py --test      # Prueba con 10 ocupaciones
    python scripts/update_esco_metadata.py --full      # Actualiza todo (lento)
    python scripts/update_esco_metadata.py --resume    # Continúa desde donde quedó
"""

import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
METADATA_PATH = PROJECT_ROOT / "database" / "embeddings" / "esco_occupations_metadata.json"
OUTPUT_PATH = PROJECT_ROOT / "database" / "embeddings" / "esco_occupations_metadata_v2.json"
ISCO_LABELS_PATH = PROJECT_ROOT / "config" / "isco_labels_es.json"
PROGRESS_PATH = PROJECT_ROOT / "database" / "embeddings" / ".esco_update_progress.json"

# API
ESCO_API_BASE = "https://ec.europa.eu/esco/api"
LANG = "es"


def fetch_occupation(uri: str) -> Optional[Dict]:
    """Obtiene datos de una ocupación ESCO."""
    url = f"{ESCO_API_BASE}/resource/occupation"
    params = {"uri": uri, "language": LANG}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  Error {response.status_code} para {uri}")
            return None
    except Exception as e:
        print(f"  Excepción para {uri}: {e}")
        return None


def fetch_isco_group(isco_code: str) -> Optional[Dict]:
    """Obtiene datos de un grupo ISCO."""
    uri = f"http://data.europa.eu/esco/isco/C{isco_code}"
    url = f"{ESCO_API_BASE}/resource/concept"
    params = {"uri": uri, "language": LANG}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None


def load_metadata() -> List[Dict]:
    """Carga metadata actual."""
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_progress(updated: List[Dict], processed_uris: set):
    """Guarda progreso para poder continuar."""
    progress = {
        "processed_count": len(processed_uris),
        "processed_uris": list(processed_uris)
    }
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(progress, f)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)


def load_progress() -> tuple:
    """Carga progreso previo si existe."""
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        return set(progress.get("processed_uris", [])), progress.get("processed_count", 0)
    return set(), 0


def update_metadata(limit: int = None, resume: bool = False):
    """
    Actualiza metadata de ocupaciones con datos de la API ESCO.

    Args:
        limit: Número máximo de ocupaciones a procesar
        resume: Si continuar desde progreso guardado
    """
    metadata = load_metadata()
    total = len(metadata)
    print(f"Total ocupaciones en metadata: {total}")

    # Cargar progreso si es resume
    if resume and OUTPUT_PATH.exists():
        processed_uris, processed_count = load_progress()
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            updated = json.load(f)
        print(f"Continuando desde {processed_count} ocupaciones procesadas")
    else:
        processed_uris = set()
        updated = []

    # Cache de labels ISCO
    isco_labels_cache = {}

    # Procesar
    processed = 0
    errors = 0

    for i, item in enumerate(metadata):
        uri = item["uri"]

        # Skip si ya procesada
        if uri in processed_uris:
            continue

        # Límite
        if limit and processed >= limit:
            break

        print(f"[{i+1}/{total}] Procesando: {item['label'][:50]}...")

        # Fetch de API
        data = fetch_occupation(uri)

        if data:
            esco_code = data.get("code", "")
            esco_label = data.get("title", item["label"])

            # Derivar ISCO code (primeros 4 dígitos)
            if esco_code and "." in esco_code:
                isco_code = esco_code.split(".")[0]
            elif esco_code:
                isco_code = esco_code[:4]
            else:
                # Fallback al código actual (quitar C prefix)
                old_code = item.get("isco_code", "")
                isco_code = old_code[1:] if old_code.startswith("C") else old_code

            # Obtener ISCO label si no está en cache
            if isco_code and isco_code not in isco_labels_cache:
                isco_data = fetch_isco_group(isco_code)
                if isco_data:
                    isco_labels_cache[isco_code] = isco_data.get("title", "")
                time.sleep(0.1)  # Rate limit

            isco_label = isco_labels_cache.get(isco_code, "")

            updated.append({
                "uri": uri,
                "esco_code": esco_code,
                "esco_label": esco_label,
                "isco_code": isco_code,
                "isco_label": isco_label
            })
            processed += 1
        else:
            # Mantener datos originales si falla
            old_code = item.get("isco_code", "")
            isco_code = old_code[1:] if old_code.startswith("C") else old_code

            updated.append({
                "uri": uri,
                "esco_code": "",
                "esco_label": item["label"],
                "isco_code": isco_code,
                "isco_label": ""
            })
            errors += 1

        processed_uris.add(uri)

        # Guardar progreso cada 50 ocupaciones
        if processed % 50 == 0:
            save_progress(updated, processed_uris)
            print(f"  Guardado progreso: {processed} procesadas, {errors} errores")

        # Rate limiting
        time.sleep(0.2)

    # Guardar final
    save_progress(updated, processed_uris)

    # Guardar cache de ISCO labels
    with open(ISCO_LABELS_PATH, 'w', encoding='utf-8') as f:
        json.dump(isco_labels_cache, f, ensure_ascii=False, indent=2)

    print(f"\n=== Completado ===")
    print(f"Procesadas: {processed}")
    print(f"Errores: {errors}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"ISCO labels: {ISCO_LABELS_PATH}")

    return updated


def test_sample():
    """Prueba con unas pocas ocupaciones para verificar."""
    print("=== Test con muestra ===\n")

    # URIs de prueba
    test_uris = [
        "http://data.europa.eu/esco/occupation/0ededdc2-050a-4ec3-8e70-6295105fcd19",  # teleoperador
        "http://data.europa.eu/esco/occupation/00030d09-2b3a-4efd-87cc-c4ea39d27c34",  # director técnico
    ]

    for uri in test_uris:
        print(f"URI: {uri}")
        data = fetch_occupation(uri)
        if data:
            esco_code = data.get("code", "N/A")
            title = data.get("title", "N/A")
            print(f"  ESCO Code: {esco_code}")
            print(f"  ESCO Label: {title}")

            if esco_code and "." in esco_code:
                isco_code = esco_code.split(".")[0]
                isco_data = fetch_isco_group(isco_code)
                if isco_data:
                    print(f"  ISCO Code: {isco_code}")
                    print(f"  ISCO Label: {isco_data.get('title', 'N/A')}")
        print()


def main():
    parser = argparse.ArgumentParser(description='Actualiza metadata ESCO con códigos de API')
    parser.add_argument('--test', action='store_true', help='Prueba con muestra')
    parser.add_argument('--full', action='store_true', help='Actualiza todas las ocupaciones')
    parser.add_argument('--resume', action='store_true', help='Continúa desde progreso guardado')
    parser.add_argument('--limit', type=int, default=10, help='Límite de ocupaciones (default: 10)')

    args = parser.parse_args()

    if args.test:
        test_sample()
    elif args.full:
        update_metadata(limit=None, resume=args.resume)
    elif args.resume:
        update_metadata(limit=None, resume=True)
    else:
        update_metadata(limit=args.limit, resume=False)


if __name__ == "__main__":
    main()
