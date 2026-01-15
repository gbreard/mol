"""
Validador de Cobertura Total - Bumeran
======================================

Obtiene el total de ofertas disponibles en la API de Bumeran
y compara con las ofertas scrapeadas para calcular cobertura real.

Uso:
    python validar_cobertura_total.py
"""

import requests
import uuid
import json
import sys
from pathlib import Path
from datetime import datetime

# Agregar paths para imports
project_root = Path(__file__).parent.parent.parent.parent
tracking_path = project_root / "01_sources" / "bumeran" / "tracking"

sys.path.insert(0, str(project_root / "02_consolidation" / "scripts"))

try:
    from incremental_tracker import IncrementalTracker
except ImportError:
    IncrementalTracker = None


def obtener_total_ofertas_api(query=""):
    """
    Consulta la API de Bumeran para obtener el total de ofertas disponibles

    Args:
        query: Keyword para buscar (por defecto "" vacío que captura TODAS)

    Returns:
        int: Total de ofertas según campo "total" de la API
    """
    url = "https://www.bumeran.com.ar/api/avisos/searchV2"

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Origin': 'https://www.bumeran.com.ar',
        'Referer': 'https://www.bumeran.com.ar/empleos-busqueda.html',
        'x-site-id': 'BMAR',
        'x-pre-session-token': str(uuid.uuid4())
    }

    payload = {
        "pageSize": 1,  # Solo necesitamos el campo "total", no los resultados
        "page": 0,
        "sort": "FECHA"
    }

    # Solo agregar query si no está vacío
    if query:
        payload["query"] = query

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        total = data.get('total', 0)

        return total

    except Exception as e:
        print(f"Error consultando API: {e}")
        return None


def obtener_ofertas_scrapeadas():
    """
    Obtiene el número de ofertas únicas ya scrapeadas del tracking

    Returns:
        tuple: (count, set_ids)
    """
    if IncrementalTracker is None:
        print("WARNING: IncrementalTracker no disponible")
        return 0, set()

    try:
        tracker = IncrementalTracker(source='bumeran')
        ids_scrapeados = tracker.load_scraped_ids()

        return len(ids_scrapeados), ids_scrapeados

    except Exception as e:
        print(f"Error cargando tracking: {e}")
        return 0, set()


def validar_cobertura(verbose=True):
    """
    Valida la cobertura completa comparando API vs scrapeado

    Returns:
        dict: Resultados de validación
    """
    if verbose:
        print("="*70)
        print("VALIDADOR DE COBERTURA TOTAL - BUMERAN")
        print("="*70)
        print()

    # 1. Obtener total de API
    if verbose:
        print("1. Consultando total de ofertas en API...")

    total_api = obtener_total_ofertas_api()

    if total_api is None:
        print("ERROR: No se pudo obtener total de API")
        return None

    if verbose:
        print(f"   Total ofertas en API: {total_api:,}")
        print()

    # 2. Obtener ofertas scrapeadas
    if verbose:
        print("2. Cargando ofertas scrapeadas...")

    total_scrapeado, ids_scrapeados = obtener_ofertas_scrapeadas()

    if verbose:
        print(f"   Ofertas scrapeadas: {total_scrapeado:,}")
        print()

    # 3. Calcular cobertura
    if total_api > 0:
        cobertura_pct = (total_scrapeado / total_api) * 100
        faltantes = total_api - total_scrapeado
    else:
        cobertura_pct = 0
        faltantes = 0

    # 4. Determinar estado
    if cobertura_pct >= 99.5:
        estado = "EXCELENTE"
        emoji = "[OK]"
    elif cobertura_pct >= 95.0:
        estado = "BUENO"
        emoji = "[OK]"
    elif cobertura_pct >= 90.0:
        estado = "ACEPTABLE"
        emoji = "[!]"
    elif cobertura_pct >= 50.0:
        estado = "BAJO"
        emoji = "[ALERTA]"
    else:
        estado = "CRITICO"
        emoji = "[ERROR]"

    # 5. Resultados
    resultados = {
        'total_api': total_api,
        'total_scrapeado': total_scrapeado,
        'cobertura_pct': cobertura_pct,
        'ofertas_faltantes': faltantes,
        'estado': estado,
        'timestamp': datetime.now().isoformat()
    }

    if verbose:
        print("="*70)
        print("RESULTADOS DE COBERTURA")
        print("="*70)
        print(f"Total en API:        {total_api:,} ofertas")
        print(f"Total scrapeado:     {total_scrapeado:,} ofertas")
        print(f"Cobertura:           {cobertura_pct:.2f}%")
        print(f"Ofertas faltantes:   {faltantes:,}")
        print(f"Estado:              {emoji} {estado}")
        print()

        # Recomendaciones
        if cobertura_pct < 99.5:
            print("RECOMENDACIONES:")
            print(f"  - Faltan {faltantes:,} ofertas para cobertura completa")
            print(f"  - Ejecutar scraping con keywords adicionales")
            print(f"  - Meta: >={int(total_api * 0.995):,} ofertas (99.5%)")
        else:
            print("[OK] Cobertura completa alcanzada!")

        print()
        print("="*70)

    return resultados


def guardar_reporte(resultados, filepath=None):
    """Guarda reporte de cobertura en JSON"""
    if filepath is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = Path(__file__).parent.parent / "data" / "metrics" / f"cobertura_{timestamp}.json"

    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"Reporte guardado: {filepath}")


def main():
    """Función principal"""
    # Validar cobertura
    resultados = validar_cobertura(verbose=True)

    if resultados:
        # Guardar reporte
        guardar_reporte(resultados)

        # Exit code según estado
        if resultados['cobertura_pct'] >= 99.5:
            sys.exit(0)  # OK
        elif resultados['cobertura_pct'] >= 90.0:
            sys.exit(1)  # Warning
        else:
            sys.exit(2)  # Error
    else:
        sys.exit(3)  # Error crítico


if __name__ == "__main__":
    main()
