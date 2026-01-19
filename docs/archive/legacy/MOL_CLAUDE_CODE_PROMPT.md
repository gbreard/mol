# MOL - System Prompt para Claude Code

> **Uso:** Copiar al inicio de cada sesión de Claude Code
> **Actualizado:** 2025-12-07

---

## Contexto del Proyecto

**MOL (Monitor de Ofertas Laborales)** es un sistema para OEDE que:
1. Scrapea ofertas de empleo de portales argentinos
2. Extrae información estructurada con NLP (Qwen2.5:14b)
3. Clasifica ofertas según taxonomía ESCO
4. Provee dashboards para analistas de mercado laboral

---

## Estado Actual

| Componente | Versión | Estado | Precisión |
|------------|---------|--------|-----------|
| Scraping | v1.0 | ✅ Operativo | 89% cobertura |
| NLP | v8.0 | ✅ Operativo | ~90% |
| Matching | v8.3 | ✅ Operativo | 78.9% |
| Dashboard Admin | - | 🔨 Por crear | - |
| Dashboard Validación | - | 🔨 Por crear | - |
| Dashboard Producción | - | 🔨 Por crear | - |

**Datos:**
- 9,564 ofertas en BD
- 10,223 IDs en tracking
- 1,148 keywords activos
- 1 portal activo (Bumeran)

---

## Stack Técnico

```
LOCAL:
├── Python 3.10+
├── SQLite (mol_database.db)
├── Ollama + Qwen2.5:14b
├── ChromaDB (embeddings)
└── Streamlit (Dashboard Admin)

CLOUD:
├── AWS S3 sa-east-1 (mol-validation-data)
├── Vercel (Dashboards Next.js)
└── Lambda + API Gateway (API)
```

---

## Estructura de Directorios

```
MOL/
├── 01_sources/bumeran/scrapers/    # Scrapers
├── database/                        # BD, matching, tests
├── nlp/                            # Pipeline NLP
├── data/tracking/                  # IDs vistos
├── dashboards/                     # Dashboards nuevos
│   ├── admin/                      # Streamlit
│   ├── optimization/               # Next.js
│   └── production/                 # Next.js
├── exports/                        # Scripts export
├── run_scheduler.py                # PUNTO DE ENTRADA SCRAPING
└── docs/                           # Documentación
```

---

## Comandos Clave

```bash
# Scraping (SIEMPRE usar este)
python run_scheduler.py --test

# Test Matching
python database/test_gold_set_manual.py

# Dashboard Admin
streamlit run dashboards/admin/app.py
```

---

## Reglas de Desarrollo

1. **Scraping:** SIEMPRE usar `run_scheduler.py`, NUNCA `bumeran_scraper.py` directo
2. **Tests:** Todo cambio en NLP/Matching debe pasar gold set
3. **Umbrales:** NLP >= 90%, Matching >= 95%
4. **S3:** Experimentos van a `/experiment/`, producción a `/production/`
5. **UI:** Dashboard producción SIN siglas técnicas (CIUO, ESCO)

---

## Documentación Relevante

| Documento | Contenido |
|-----------|-----------|
| MOL_CONTEXT_MASTER.md | Contexto completo del sistema |
| MOL_LINEAR_ISSUES_V3.md | Issues detallados |
| SISTEMA_VALIDACION_V2.md | Arquitectura de validación |
| NLP_SCHEMA_V5.md | Schema de campos NLP |
| DASHBOARD_WIREFRAMES.md | Wireframes de dashboards |
| SCRAPERS_INVENTARIO.md | Inventario de scrapers |

---

## Épicas Activas

| Épica | Prioridad | Issues |
|-------|-----------|--------|
| 1. Scraping | Alta | Dashboard tab, ZonaJobs |
| 2. NLP | Alta | Gold set, tests, export |
| 3. Matching | Alta | sector_funcion, gold set |
| 4. Validación | Alta | Tests, S3 sync |
| 5. Dashboards | Media | Admin, Validación, Producción |
| 6. Infraestructura | Baja | Logs, alertas, CI/CD |

---

## Métricas de Éxito

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Precisión NLP | ~90% | >= 90% |
| Precisión Matching | 78.9% | >= 95% |
| Gold Set NLP | 0 | 200+ |
| Gold Set Matching | 19 | 200+ |
| Portales | 1 | 5 |

---

*Al trabajar en un issue, consultar MOL_LINEAR_ISSUES_V3.md para especificación completa*
