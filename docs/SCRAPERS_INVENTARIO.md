# Inventario de Scrapers - Proyecto MOL

> **Fecha de análisis:** 2025-12-06
> **Última ejecución exitosa:** 2025-12-06 22:21
> **Resultado:** 701 ofertas nuevas, 10,223 IDs en tracking

---

## Resumen Ejecutivo

### El Error Cometido

Usé `bumeran_scraper.py` directamente, que scrapea **SIN keywords**. Esto activa el modo incremental que detecta que ya existen 9,371 IDs y solo trae las 14 nuevas desde la última ejecución.

**Lo correcto era usar:** `run_scheduler.py --test` o `scrapear_con_diccionario.py` que usa la estrategia `ultra_exhaustiva_v3_2` con **1,148 keywords**.

---

## Inventario Completo de Scrapers

### 1. BUMERAN (Portal Principal)

| Archivo | Descripción | Estado | Problema |
|---------|-------------|--------|----------|
| `bumeran_scraper.py` | API REST básico, SIN keywords | ✅ Funciona | Paginación rota (solo 20/página, duplicados) |
| `scrapear_con_diccionario.py` | Multi-keyword con estrategias | ✅ **RECOMENDADO** | Ninguno |
| `bumeran_selenium_scraper.py` | Selenium (bypass Cloudflare) | ⚠️ Legacy | Lento, innecesario (API funciona) |
| `run_scraping_completo.py` | Wrapper de bumeran_scraper | ⚠️ Incompleto | No usa keywords |

#### Bug de Paginación en Bumeran API

```
PROBLEMA: La API de Bumeran ignora page_size > 20
- Pedís: page_size=100
- Devuelve: 20 ofertas
- A partir de página 10-11: devuelve duplicados

SOLUCIÓN EN scrapear_con_diccionario.py:
- Usa max_paginas_por_keyword=1 (solo primera página por keyword)
- Compensa con 1,148 keywords diferentes
```

#### Gap Conocido - Se Va Cerrando

| Métrica | Antes | Ahora |
|---------|-------|-------|
| IDs en tracking | 9,385 | 10,223 |
| Ofertas en BD | 8,863 | 9,564 |
| Cobertura estimada | 82% | 89% |
| Ofertas nuevas | - | +701 |

**Confirmado:** El gap se cierra naturalmente con cada ejecución semanal.

### 2. ZONAJOBS

| Archivo | Estado | Problema |
|---------|--------|----------|
| `zonajobs_scraper_final.py` | ✅ Funciona | No soporta keywords |
| `zonajobs_playwright_scraper.py` | ⚠️ Experimental | Requiere Playwright |

### 3. OTROS PORTALES

| Portal | Archivo | Estado |
|--------|---------|--------|
| ComputRabajo | `computrabajo_scraper.py` | ⚠️ Requiere revisión |
| LinkedIn | `linkedin_scraper.py` | ⚠️ Usa JobSpy (rate limited) |
| Indeed | `indeed_scraper.py` | ⚠️ Usa JobSpy |

---

## Scripts de Ejecución

### Comparación de Scripts

| Script | Qué hace | Keywords | Resultado |
|--------|----------|----------|-----------|
| `run_scheduler.py` | **EL CORRECTO** - Usa diccionario v3.2 | ✅ 1,148 | 10,223 IDs (89%) |
| `run_full_pipeline.py` | Orquesta 5 portales | ✅ Sí | ~30,000 ofertas |
| `run_scraping_completo.py` | Solo Bumeran básico | ❌ No | ~200 ofertas |

### Configuración del Scheduler (`database/config.py`)

```python
SCHEDULER_CONFIG = {
    'days_of_week': [0, 3],  # Lunes y Jueves
    'hour': 8,
    'minute': 0,
}

# USA: scrapear_con_diccionario.py con estrategia 'ultra_exhaustiva_v3_2'
```

---

## Estrategias de Keywords Disponibles

| Estrategia | Keywords | Uso recomendado |
|------------|----------|-----------------|
| `ultra_exhaustiva_v3_2` | 1,148 | **Producción** - Máxima cobertura |
| `exhaustiva` | 1,073 | Alternativa a ultra_exhaustiva |
| `ultra_completa` | 268 | Cobertura completa |
| `maxima` | 90 | Primera ejecución |
| `completa` | 56 | Incremental balanceado |
| `general` | 30 | Rápido |
| `minima` | 4 | Testing |

---

## Flujo de Datos Actual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  run_scheduler.py (CORRECTO)                                                │
│       ↓                                                                     │
│  scrapear_con_diccionario.py                                               │
│       ↓                                                                     │
│  BumeranMultiSearch.scrapear_multiples_keywords(                           │
│      estrategia='ultra_exhaustiva_v3_2',  ← 1,148 keywords                 │
│      max_paginas_por_keyword=1,           ← Solo página 1 (evita bug)      │
│      incremental=True                                                       │
│  )                                                                          │
│       ↓                                                                     │
│  10,223 IDs en tracking (89% cobertura)                                    │
│  9,564 ofertas en BD                                                        │
│       ↓                                                                     │
│  detectar_bajas_integrado.py (automático post-scraping)                    │
│       ↓                                                                     │
│  Marca ofertas dadas de baja + calcula permanencia                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  LO QUE HICE MAL                                                            │
│       ↓                                                                     │
│  bumeran_scraper.py DIRECTO (sin keywords)                                 │
│       ↓                                                                     │
│  BumeranScraper.scrapear_todo(                                             │
│      max_paginas=None,                                                      │
│      incremental=True                                                       │
│  )                                                                          │
│       ↓                                                                     │
│  Solo 14 ofertas nuevas (9,371 ya estaban en tracking)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Recomendación

### Para Scraping Semanal de Producción

```bash
# OPCIÓN 1: Ejecutar el scheduler en modo test (inmediato)
python run_scheduler.py --test

# OPCIÓN 2: Ejecutar directamente el multi-keyword
cd 01_sources/bumeran/scrapers
python -c "
from scrapear_con_diccionario import BumeranMultiSearch
scraper = BumeranMultiSearch()
df = scraper.scrapear_multiples_keywords(
    estrategia='ultra_exhaustiva_v3_2',
    max_paginas_por_keyword=1,
    incremental=True
)
print(f'Total: {len(df)} ofertas')
"
```

### Para Pipeline Completo (5 portales)

```bash
python run_full_pipeline.py
```

---

## Archivos a Deprecar/Eliminar

| Archivo | Razón |
|---------|-------|
| `bumeran_selenium_scraper.py` | Innecesario, API funciona |
| `run_scraping_completo.py` | Confuso, no usa keywords |
| `run_scraping_semanal.py` | Temporal, ya eliminado |

---

## Decisiones Tomadas

1. **`run_scheduler.py` es el único punto de entrada para scraping**
   - Simplifica el sistema
   - Usa la configuración correcta
   - Integra detección de bajas automática

2. **`bumeran_scraper.py` es interno**
   - Solo se usa desde `scrapear_con_diccionario.py`
   - Nunca ejecutar directamente

3. **Gap de ~2,000 ofertas: NO perseguir**
   - Las ofertas viejas irán bajando naturalmente
   - Las nuevas se capturan desde el día 1
   - El sistema se normaliza con el tiempo

4. **Otros portales: Futuro**
   - ZonaJobs funciona, activar cuando se necesite
   - ComputRabajo, LinkedIn, Indeed necesitan revisión

---

## Integración con Permanencia

```
FLUJO SEMANAL COMPLETO:
───────────────────────
run_scheduler.py --test
    │
    ├── 1. Scrapea con 1,148 keywords
    ├── 2. Guarda IDs en tracking JSON
    ├── 3. Inserta en BD
    │
    └── 4. Ejecuta detectar_bajas_integrado.py
             │
             ├── Lee IDs del tracking (snapshot actual)
             ├── Compara con BD.estado_oferta = 'activa'
             ├── Diferencia → marca como 'baja'
             └── Calcula permanencia
```

**Limitación conocida:** Ofertas que nunca entraron al tracking no se detectan como bajas. Esto se normaliza con el tiempo.

---

## Comando Único para Producción

```bash
# Ejecutar scraping completo + detección de bajas
python run_scheduler.py --test
```

Este comando:
1. Scrapea con 1,148 keywords
2. Actualiza tracking
3. Detecta bajas automáticamente
4. Calcula permanencia

---

*Documento actualizado: 2025-12-06*
