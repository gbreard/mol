# Cambios para Captura Automática de total_api

## Objetivo
Capturar automáticamente el `total_api` (total de ofertas disponibles en Bumeran) cada vez que se ejecuta un scraping y guardarlo en un archivo JSON de métricas.

## Archivos a Modificar

### 1. `01_sources/bumeran/scrapers/scrapear_con_diccionario.py`

#### Cambio 1.1: Modificar `__init__` (línea 60-69)
**Antes:**
```python
def __init__(self, delay_between_requests=1.5, delay_between_keywords=3.0):
    self.scraper = BumeranScraper(delay_between_requests)
    self.delay_keywords = delay_between_keywords
    self.keywords_config_path = Path(__file__).parent.parent / "config" / "search_keywords.json"
```

**Después:**
```python
def __init__(self, delay_between_requests=1.5, delay_between_keywords=3.0):
    self.scraper = BumeranScraper(delay_between_requests)
    self.delay_keywords = delay_between_keywords
    self.keywords_config_path = Path(__file__).parent.parent / "config" / "search_keywords.json"
    self.last_total_api = 0  # Total de ofertas disponibles en la API (capturado durante scraping)
```

#### Cambio 1.2: Capturar total_api durante scraping
Agregar después de la línea 173 (dentro del bucle de keywords), necesitamos capturar el `total_api` de la primera búsqueda exitosa.

#### Cambio 1.3: Agregar nuevo método `guardar_metricas_cobertura()` (después de línea 359)
```python
def guardar_metricas_cobertura(self, total_scrapeado: int) -> Optional[str]:
    """
    Guarda métricas de cobertura del scraping en archivo JSON.

    Args:
        total_scrapeado: Total de ofertas scrapeadas en esta ejecución

    Returns:
        Path del archivo JSON generado, o None si no se pudo guardar
    """
    try:
        # Directorio de métricas
        metrics_dir = Path(__file__).parent.parent / "data" / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)

        # Generar timestamp
        timestamp = datetime.now()
        filename = f"cobertura_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = metrics_dir / filename

        # Calcular métricas
        total_api = self.last_total_api or 0
        cobertura_pct = (total_scrapeado / total_api * 100) if total_api > 0 else 0
        ofertas_faltantes = max(0, total_api - total_scrapeado)

        # Determinar estado
        if cobertura_pct >= 90:
            estado = "EXCELENTE"
        elif cobertura_pct >= 70:
            estado = "BUENO"
        elif cobertura_pct >= 50:
            estado = "ACEPTABLE"
        else:
            estado = "CRITICO"

        # Construir objeto de métricas
        metricas = {
            "total_api": total_api,
            "total_scrapeado": total_scrapeado,
            "cobertura_pct": cobertura_pct,
            "ofertas_faltantes": ofertas_faltantes,
            "estado": estado,
            "timestamp": timestamp.isoformat()
        }

        # Guardar JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metricas, f, indent=2, ensure_ascii=False)

        logger.info(f"\nMétricas de cobertura guardadas en: {filepath}")
        logger.info(f"  Total API: {total_api:,} | Scrapeado: {total_scrapeado:,} | Cobertura: {cobertura_pct:.1f}% | Estado: {estado}")

        return str(filepath)

    except Exception as e:
        logger.error(f"Error guardando métricas de cobertura: {e}")
        return None
```

#### Cambio 1.4: Modificar `guardar_resultados()` (línea 360-377)
**Después de línea 376** (después de guardar archivos), agregar:
```python
# Guardar métricas de cobertura automáticamente
self.guardar_metricas_cobertura(total_scrapeado=len(df))
```

## Resultado Esperado

Cada vez que se ejecute un scraping, se generará automáticamente un archivo JSON con formato:
```json
{
  "total_api": 12174,
  "total_scrapeado": 5704,
  "cobertura_pct": 46.85,
  "ofertas_faltantes": 6470,
  "estado": "ACEPTABLE",
  "timestamp": "2025-11-04T19:30:45.123456"
}
```

Este archivo se guardará en: `01_sources/bumeran/data/metrics/cobertura_YYYYMMDD_HHMMSS.json`

Y el dashboard podrá leerlo automáticamente para mostrar la evolución temporal del `total_api`.
