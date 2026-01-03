# Documentacion MOL - Monitor de Ofertas Laborales

> **Actualizado:** 2025-01-03
> **Fuente de verdad:** `CLAUDE.md` (raiz del proyecto)

---

## Documentacion Actual

### current/
Documentos **activos y actualizados** del sistema:

| Documento | Descripcion |
|-----------|-------------|
| [MOL_CONTEXT_MASTER.md](current/MOL_CONTEXT_MASTER.md) | Contexto completo del sistema, arquitectura, diagramas |
| [ARCHITECTURE.md](current/ARCHITECTURE.md) | Arquitectura tecnica detallada |
| [NLP_SCHEMA_V5.md](current/NLP_SCHEMA_V5.md) | Schema de 153 campos NLP |
| [MATCHING_STRATEGY_V2.md](current/MATCHING_STRATEGY_V2.md) | Estrategia Matching v2.1.1 BGE-M3 |
| [CHANGELOG.md](current/CHANGELOG.md) | Historial de cambios |
| [STATUS.md](current/STATUS.md) | Estado actual del proyecto |

---

## Guias de Uso

### guides/
Guias practicas para usar el sistema:

| Guia | Descripcion |
|------|-------------|
| [QUICKSTART_BUMERAN.md](guides/QUICKSTART_BUMERAN.md) | Inicio rapido scraping Bumeran |
| [FLUJO_BUMERAN.md](guides/FLUJO_BUMERAN.md) | Flujo completo de scraping |
| [AUTOMATION_GUIDE.md](guides/AUTOMATION_GUIDE.md) | Automatizacion del sistema |
| [GUIA_MONITOREO_SISTEMA.md](guides/GUIA_MONITOREO_SISTEMA.md) | Monitoreo y alertas |
| [DASHBOARD_WIREFRAMES.md](guides/DASHBOARD_WIREFRAMES.md) | Disenos de dashboards |
| [COMPARTIR_DASHBOARD_NGROK.md](guides/COMPARTIR_DASHBOARD_NGROK.md) | Compartir dashboard via ngrok |

---

## Planificacion

### planning/
Issues, roadmaps y planificacion:

| Documento | Descripcion |
|-----------|-------------|
| [MOL_LINEAR_ISSUES_V3.md](planning/MOL_LINEAR_ISSUES_V3.md) | Issues Linear con specs detalladas |
| [MOL_CLAUDE_CODE_PROMPT.md](planning/MOL_CLAUDE_CODE_PROMPT.md) | Prompt para inicio de sesion |
| [PLANIFICACION_MOL_COMPLETA.md](planning/PLANIFICACION_MOL_COMPLETA.md) | Planificacion completa |

---

## Referencia Tecnica

### reference/
Documentacion tecnica de referencia:

| Documento | Descripcion |
|-----------|-------------|
| [INTEGRACION_ESCO.md](reference/INTEGRACION_ESCO.md) | Integracion con taxonomia ESCO |
| [ZONAJOBS_API_DOCUMENTATION.md](reference/ZONAJOBS_API_DOCUMENTATION.md) | Documentacion API ZonaJobs |
| [MAPA_COMPLETO_DEL_PROYECTO.md](reference/MAPA_COMPLETO_DEL_PROYECTO.md) | Mapa de archivos del proyecto |
| [arquitectura.md](reference/arquitectura.md) | Arquitectura (version alternativa) |

---

## Dashboard R Shiny (Produccion)

El dashboard R Shiny esta en **`Visual--/`** y esta en produccion.

| Recurso | Ubicacion |
|---------|-----------|
| App principal | `Visual--/app.R` |
| Documentacion | `Visual--/docs/` |
| Deploy config | `Visual--/rsconnect/` |

**NO modificar Visual--/** sin coordinacion con el equipo.

---

## Archivo Historico

### archive/
Documentacion de fases anteriores y versiones legacy:

```
archive/
├── fases_completadas/     # Mejoras de fases 1, 2, 3
├── analisis/              # Analisis historicos
└── legacy/                # Documentos obsoletos
```

---

## Otras Ubicaciones

| Ubicacion | Contenido |
|-----------|-----------|
| `02.5_nlp_extraction/docs/` | Documentacion del pipeline NLP |
| `01_sources/*/README.md` | READMEs de cada scraper |
| `shared/schemas/` | Schema unificado y documentacion |

---

## Navegacion Rapida

- **Empezar:** Lee `CLAUDE.md` (raiz) primero
- **Arquitectura:** `current/MOL_CONTEXT_MASTER.md`
- **Versiones:** `current/CHANGELOG.md`
- **Issues:** `planning/MOL_LINEAR_ISSUES_V3.md`
