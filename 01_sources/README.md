# 01_sources - Fuentes de Scraping

## 🎯 Propósito

Este directorio contiene los scrapers independientes para cada fuente de ofertas laborales. Cada fuente es un módulo aislado con su propia lógica, configuración y almacenamiento de datos crudos.

## 📁 Estructura

```
01_sources/
├── zonajobs/           # ZonaJobs.com.ar
├── bumeran/            # Bumeran.com.ar
├── computrabajo/       # ComputRabajo.com.ar
├── linkedin/           # LinkedIn
└── README.md           # Este archivo
```

## 🔧 Cada Fuente Incluye

Cada subdirectorio de fuente debe tener:

```
fuente/
├── scrapers/          # Scripts de scraping
│   ├── main_scraper.py
│   ├── api_discovery.py
│   └── utils.py
├── data/
│   ├── raw/          # Datos crudos extraídos
│   └── logs/         # Logs específicos de esta fuente
├── tests/            # Tests unitarios del scraper
├── config/           # Configuración específica
│   └── config.ini
└── README.md         # Documentación de la fuente
```

## 🚀 Uso

### Ejecutar un scraper individual

```bash
cd 01_sources/zonajobs/scrapers
python zonajobs_scraper_final.py
```

### Salida

Los datos se guardan en formato crudo en `fuente/data/raw/`:
- CSV
- JSON
- Excel (opcional)

Formato de nombre: `{fuente}_raw_{YYYYMMDD}_{HHMMSS}.{ext}`

Ejemplo: `zonajobs_raw_20251021_143000.csv`

## ✅ Requisitos

Cada fuente debe:
1. ✅ Respetar robots.txt
2. ✅ Implementar rate limiting
3. ✅ Usar User-Agent identificable
4. ✅ Guardar datos con timestamp
5. ✅ Loggear errores y progreso
6. ✅ Ser ejecutable independientemente

## 📊 Datos Extraídos

Los datos crudos pueden tener cualquier estructura, ya que serán normalizados en la etapa `02_consolidation/`.

Campos recomendados mínimos:
- ID de la oferta
- Título
- Empresa
- URL
- Fecha de publicación
- Timestamp de extracción

## ➡️ Siguiente Etapa

Los datos crudos pasan a:
- **02_consolidation/** para normalización y unificación

## 🔗 Referencias

- [Schema Unificado](../shared/schemas/SCHEMA_DOCUMENTATION.md)
- [Pipeline Completo](../docs/arquitectura.md)

---

**Última actualización**: 2025-10-21
