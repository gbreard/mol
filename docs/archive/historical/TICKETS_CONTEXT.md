# MOL - Contexto Expandido de Issues

> **Linear:** https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f
> **Metodología:** [MOL_LINEAR_METODOLOGIA.md](./MOL_LINEAR_METODOLOGIA.md)
> **Última actualización:** 2025-12-04

---

## Índice por Épica

### Épica 1: Scraping y Captura
- [MOL-18](#mol-18-automatizar-scrapers-faltantes) - Automatizar scrapers (Alta)
- [MOL-22](#mol-22-documentar-apis-scrapers) - Documentar APIs (Baja)
- [MOL-26](#mol-26-drift-detection) - Drift detection (Media)

### Épica 2: Normalización y NLP
- [MOL-10](#mol-10-regex-abreviaciones) - Regex abreviaciones (Baja)
- [MOL-11](#mol-11-niveles-jerárquicos) - Niveles jerárquicos (Baja)
- [MOL-12](#mol-12-consolidar-nlp) - Consolidar NLP v6+v7 (Baja)
- [MOL-28](#mol-28-spike-ner-spacy) - Spike: NER spaCy vs regex (Media)

### Épica 3: Matching ESCO
- [MOL-5](#mol-5-resolver-sector_funcion) - Resolver sector_funcion (Alta)
- [MOL-8](#mol-8-casos-bilingües) - Casos bilingües (Media)
- [MOL-27](#mol-27-spike-embeddings-e5) - Spike: embeddings multilingual-e5 (Media)
- [MOL-29](#mol-29-spike-prompt-engineering) - Spike: prompt engineering LLM (Media)

### Épica 4: Dashboards y Visualización
- [MOL-13](#mol-13-panel-admin) - Panel administración (Baja)
- [MOL-16](#mol-16-shinytree) - Fix shinyTree (Media)
- [MOL-17](#mol-17-auth-shinymanager) - Auth shinymanager (Baja)
- [MOL-21](#mol-21-deprecar-dashboards) - Deprecar dashboards (Baja)

### Épica 5: Evaluación de Calidad
- [MOL-6](#mol-6-expandir-gold-set) - Expandir Gold Set a 50+ (Alta)
- [MOL-7](#mol-7-métricas-recall) - Métricas Recall y F1 (Media)
- [MOL-9](#mol-9-cicd) - CI/CD tests automáticos (Baja)

### Épica 6: Infraestructura
- [MOL-14](#mol-14-alertas) - Alertas email/Slack (Media)
- [MOL-15](#mol-15-limpieza-jsons) - Limpieza JSONs (Baja)
- [MOL-19](#mol-19-pipeline-automático) - Pipeline automático (Media)
- [MOL-20](#mol-20-centralizar-logs) - Centralizar logs (Baja)
- [MOL-23](#mol-23-backup-sqlite) - Backup automático SQLite (Alta)
- [MOL-24](#mol-24-versionado-datos) - Versionado de datos (Alta)
- [MOL-25](#mol-25-entity-resolution) - Entity resolution cross-source (Media)

---

# ÉPICA 1: SCRAPING Y CAPTURA

**Objetivo:** Traer ofertas de 5 plataformas con esquema común

---

## MOL-18: Automatizar scrapers faltantes

**Épica:** 1 - Scraping y Captura | **Prioridad:** Alta | **Labels:** scraping, infra

### Contexto
Solo Bumeran tiene scheduler automatizado (L/J 8am). Las otras 4 fuentes requieren ejecución manual, capturando solo ~20% del mercado de forma consistente.

### Archivos
```
run_scheduler.py                              ← Modificar
01_sources/zonajobs/scrapers/zonajobs_scraper_final.py
01_sources/indeed/scrapers/indeed_scraper.py
01_sources/computrabajo/scrapers/computrabajo_scraper.py
01_sources/linkedin/scrapers/linkedin_scraper.py
config/scraper_config.yaml                    ← Crear
```

### Criterios de Aceptación
- [ ] Los 5 scrapers ejecutan automáticamente
- [ ] Rate limiting configurado por fuente
- [ ] Reintentos con backoff exponencial
- [ ] Timeout máximo (30 min por fuente)
- [ ] Logging a archivo dedicado
- [ ] Manejo de errores no detiene otros scrapers

### Dependencias
- **Bloquea:** MOL-19 (pipeline), MOL-25 (entity resolution)

---

## MOL-22: Documentar APIs scrapers

**Épica:** 1 - Scraping y Captura | **Prioridad:** Baja | **Labels:** docs, scraping

### Contexto
APIs descubiertas por reverse engineering sin documentación formal.

### Criterios de Aceptación
- [ ] Documentar endpoint, headers, payload para cada API
- [ ] Documentar rate limits conocidos
- [ ] Crear `docs/SCRAPER_APIS.md`

---

## MOL-26: Drift Detection

**Épica:** 1 - Scraping y Captura | **Prioridad:** Media | **Labels:** scraping, infra

### Contexto
Si un portal cambia su API/HTML, el scraper puede fallar silenciosamente.

### Criterios de Aceptación
- [ ] Alerta si ofertas_nuevas < threshold diario
- [ ] Alerta si campos obligatorios vienen vacíos (>10%)
- [ ] Health check validable manualmente
- [ ] Integrado con sistema de alertas (MOL-14)

---

# ÉPICA 2: NORMALIZACIÓN Y NLP

**Objetivo:** Parsear y estructurar información de ofertas

---

## MOL-10: Regex abreviaciones argentinas

**Épica:** 2 - Normalización y NLP | **Prioridad:** Baja | **Labels:** nlp, regex

### Contexto
El regex v4 no detecta abreviaciones: Adm., Gte., Coord., Jfe., Aux.

### Archivos
```
02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py
```

### Criterios de Aceptación
- [ ] Detecta: Adm., Gte., Coord., Jfe., Aux., Ing., Lic., Dr.
- [ ] Expande a forma completa
- [ ] Cobertura regex aumenta (60-70% → 70-75%)

---

## MOL-11: Niveles jerárquicos

**Épica:** 2 - Normalización y NLP | **Prioridad:** Baja | **Labels:** nlp, matching

### Contexto
2 errores de nivel_jerarquico en gold set (Vendedora → Director).

### Criterios de Aceptación
- [ ] Detecta nivel desde años de experiencia requeridos
- [ ] Detecta nivel desde salario (si disponible)
- [ ] Casos nivel_jerarquico en gold set = 0

---

## MOL-12: Consolidar NLP v6+v7

**Épica:** 2 - Normalización y NLP | **Prioridad:** Baja | **Labels:** nlp, tech-debt

### Contexto
Existen múltiples versiones de scripts NLP, dificulta mantenimiento.

### Criterios de Aceptación
- [ ] Un solo script: `process_nlp_unified.py`
- [ ] Versiones antiguas movidas a archive/

---

## MOL-28: Spike: NER spaCy vs regex

**Épica:** 2 - Normalización y NLP | **Prioridad:** Media | **Labels:** spike, nlp, eval-calidad

### Contexto
**Hipótesis:** spaCy con modelo es-core-news-lg podría detectar skills con mejor cobertura que regex.

### Criterios de Aceptación
- [ ] Implementar extractor de skills con spaCy
- [ ] Crear mini gold set de skills (20 ofertas anotadas)
- [ ] Medir precision/recall de ambos métodos
- [ ] Decisión: Go/NoGo documentada

### Resultado esperado
Tabla comparativa: regex vs spaCy (precision, recall, coverage)

---

# ÉPICA 3: MATCHING ESCO

**Objetivo:** Asignar ocupaciones y skills ESCO a cada oferta

---

## MOL-5: Resolver sector_funcion

**Épica:** 3 - Matching ESCO | **Prioridad:** Alta | **Labels:** matching, esco

### Contexto
El 50% de los errores del gold set (4 de 8) son del tipo `sector_funcion`. El sistema mapea ofertas a ocupaciones de sectores completamente diferentes.

**Historia de intentos:**
- v8.1: Ajustes por nivel jerárquico → No resolvió
- v8.2: 6 familias funcionales → Mejoró categorización
- v8.3: +4 familias específicas → Mejora parcial (57.9% → 63.2%)

### Archivos
```
database/matching_rules_v84.py     ← Crear (copiar de v83)
database/matching_rules_v83.py     ← Referencia (NO modificar)
database/gold_set_manual_v1.json   ← Casos de prueba
database/test_gold_set_manual.py   ← Validación
```

### Casos específicos del Gold Set

| ID | Título | Match Actual | Match Esperado |
|----|--------|--------------|----------------|
| 1118027276 | Ejecutivo de cuentas comercial | Técnico contadores | Ejecutivo cuentas (2433) |
| 1118028376 | Analista administrativo/a | Analista negocios | Empleado admin (4110) |
| 1118028833 | Asesor comercial plan ahorro | Agente alquiler | Vendedor (5223) |
| 1118028887 | Account Executive (Hunter) | Agente empleo | Representante comercial (3322) |

### Criterios de Aceptación
- [ ] Precisión gold set ≥85% (actual: ~80%)
- [ ] Casos sector_funcion ≤1 (actual: 4)
- [ ] NO hay regresiones en casos que antes funcionaban
- [ ] Test pasa: `python database/test_gold_set_manual.py`

### Dependencias
- **Bloquea:** MOL-9 (CI/CD necesita estabilidad)

---

## MOL-8: Casos bilingües

**Épica:** 3 - Matching ESCO | **Prioridad:** Media | **Labels:** matching, embeddings

### Contexto
Títulos en inglés no matchean bien con ocupaciones ESCO en español. "Account Executive" → debería ser "Ejecutivo de cuentas".

### Criterios de Aceptación
- [ ] Diccionario con ≥50 traducciones comunes
- [ ] "Account Executive" matchea a ventas
- [ ] "Software Developer" matchea a desarrollador
- [ ] Sin regresiones en títulos en español

---

## MOL-27: Spike: embeddings multilingual-e5

**Épica:** 3 - Matching ESCO | **Prioridad:** Media | **Labels:** spike, matching, embeddings

### Contexto
**Hipótesis:** multilingual-e5 podría tener mejor representación cross-lingual que BGE-M3 para casos bilingües.

### Criterios de Aceptación
- [ ] Implementar función de matching con e5 (no reemplazar BGE-M3)
- [ ] Medir F1 en gold set completo
- [ ] Medir F1 específicamente en casos bilingües (5 casos)
- [ ] Decisión: Go/NoGo documentada

### Resultado esperado
Conclusión: "mejora F1 de X a Y" o "no mejora significativamente"

---

## MOL-29: Spike: prompt engineering LLM

**Épica:** 3 - Matching ESCO | **Prioridad:** Media | **Labels:** spike, matching, eval-calidad

### Contexto
**Hipótesis:** Un LLM con buen prompt podría clasificar directamente, especialmente casos difíciles.

### Criterios de Aceptación
- [ ] Diseñar 3-5 variantes de prompts para clasificación ESCO
- [ ] Evaluar en 20 casos problemáticos del gold set
- [ ] Analizar costo/latencia vs mejora
- [ ] Decisión: Go/NoGo documentada

---

# ÉPICA 4: DASHBOARDS Y VISUALIZACIÓN

**Objetivo:** Tableros para usuarios finales y administradores

---

## MOL-16: Fix shinyTree

**Épica:** 4 - Dashboards | **Prioridad:** Media | **Labels:** dashboard

### Contexto
El componente shinyTree para navegar la jerarquía ESCO está deshabilitado por bug de input/output binding.

### Criterios de Aceptación
- [ ] Árbol ESCO visible y navegable
- [ ] Al seleccionar ocupación, filtran ofertas
- [ ] Sin errores en consola R ni browser

---

## MOL-17: Auth shinymanager

**Épica:** 4 - Dashboards | **Prioridad:** Baja | **Labels:** dashboard, infra

### Contexto
Autenticación deshabilitada para debug. Dashboard públicamente accesible.

### Dependencias
- **Requiere:** MOL-16 (estabilidad del dashboard)

---

## MOL-13: Panel administración

**Épica:** 4 - Dashboards | **Prioridad:** Baja | **Labels:** dashboard, infra

### Contexto
Todo se maneja por CLI. No hay forma visual de ver el estado del sistema.

### Criterios de Aceptación
- [ ] Ver estado de scrapers
- [ ] Ver estado de pipeline NLP/Matching
- [ ] Ejecutar tareas manualmente
- [ ] Ver logs recientes

### Dependencias
- **Requiere:** MOL-20 (logs centralizados)

---

## MOL-21: Deprecar dashboards

**Épica:** 4 - Dashboards | **Prioridad:** Baja | **Labels:** tech-debt, dashboard

### Contexto
Múltiples versiones de dashboards obsoletos.

### Criterios de Aceptación
- [ ] Solo 2 dashboards activos
- [ ] Dashboards obsoletos en archive/

---

# ÉPICA 5: EVALUACIÓN DE CALIDAD

**Objetivo:** Medir y mejorar calidad del matching

---

## MOL-6: Expandir Gold Set a 50+

**Épica:** 5 - Evaluación | **Prioridad:** Alta | **Labels:** eval-calidad

### Contexto
Con solo 19 casos, el gold set no es estadísticamente representativo. Un cambio de 1 caso = 5.3pp de precisión.

### Archivos
```
database/gold_set_manual_v2.json     ← Crear
database/gold_set_manual_v1.json     ← Mantener backup
database/test_gold_set_manual.py     ← Actualizar
```

### Estratificación requerida

| Sector | Casos mínimos |
|--------|---------------|
| IT/Tech | 8 |
| Comercial/Ventas | 8 |
| Administrativo | 6 |
| Operarios/Producción | 6 |
| Salud | 5 |
| Servicios/Atención | 5 |
| Legal | 4 |
| Marketing | 4 |

### Criterios de Aceptación
- [ ] Gold set v2 tiene ≥50 casos
- [ ] Cobertura de 8+ sectores
- [ ] Cada caso tiene: id_oferta, esco_ok, tipo_error, esco_esperado_uri, sector, nivel

---

## MOL-7: Métricas Recall y F1

**Épica:** 5 - Evaluación | **Prioridad:** Media | **Labels:** eval-calidad

### Contexto
Solo medimos precisión. No sabemos cuántas ofertas quedan sin matchear correctamente.

### Criterios de Aceptación
- [ ] Benchmark reporta Precision, Recall, F1-Score
- [ ] Benchmark reporta Top-3 Accuracy
- [ ] Output formateado con todas las métricas

### Dependencias
- **Requiere:** MOL-6 (gold set con esco_esperado_uri)

---

## MOL-9: CI/CD tests automáticos

**Épica:** 5 - Evaluación | **Prioridad:** Baja | **Labels:** infra, eval-calidad

### Contexto
Un push puede romper el matching sin que nadie se entere.

### Criterios de Aceptación
- [ ] GitHub Action en cada push a main
- [ ] Corre test_gold_set_manual.py
- [ ] Falla si precision < 75%
- [ ] Badge de estado en README

### Dependencias
- **Requiere:** MOL-5 estable (precisión consistente)

---

# ÉPICA 6: INFRAESTRUCTURA

**Objetivo:** Soporte técnico del sistema

---

## MOL-23: Backup automático SQLite

**Épica:** 6 - Infraestructura | **Prioridad:** Alta | **Labels:** infra

### Contexto
Toda la data está en un único archivo (`bumeran_scraping.db` ~14MB). Sin backups automatizados.

### Criterios de Aceptación
- [ ] Backup diario automático después del scraping
- [ ] Formato: `backups/bumeran_scraping_YYYY-MM-DD.db.gz`
- [ ] Retención: últimos 30 backups
- [ ] Verificación de integridad post-backup

---

## MOL-24: Versionado de datos

**Épica:** 6 - Infraestructura | **Prioridad:** Alta | **Labels:** infra

### Contexto
Solo se versiona código (git), no datasets. No se puede reproducir métricas históricas.

### Criterios de Aceptación
- [ ] Gold sets versionados: `data/gold_sets/gold_set_v1_FECHA.json`
- [ ] Snapshots de BD: `data/snapshots/ofertas_FECHA.csv.gz`
- [ ] Archivo LATEST.json apunta a versiones activas

---

## MOL-14: Alertas email/Slack

**Épica:** 6 - Infraestructura | **Prioridad:** Media | **Labels:** infra

### Contexto
`alert_manager.py` existe pero tiene `email_enabled=False`.

### Criterios de Aceptación
- [ ] Alerta cuando scraping falla
- [ ] Alerta cuando ofertas_nuevas < threshold
- [ ] Al menos un canal funcional (email o Slack)

---

## MOL-19: Pipeline automático post-scraping

**Épica:** 6 - Infraestructura | **Prioridad:** Media | **Labels:** infra, etl

### Contexto
Después del scraping hay que ejecutar manualmente: consolidación → NLP → matching.

### Criterios de Aceptación
- [ ] Un comando ejecuta todo: `python scripts/run_full_pipeline.py`
- [ ] Si un paso falla, no ejecuta los siguientes
- [ ] Log de cada paso con tiempo de ejecución

### Dependencias
- **Requiere:** MOL-18 (scrapers automatizados)

---

## MOL-20: Centralizar logs

**Épica:** 6 - Infraestructura | **Prioridad:** Baja | **Labels:** infra

### Contexto
Logs distribuidos en múltiples carpetas.

### Criterios de Aceptación
- [ ] Directorio único: logs/
- [ ] Rotación automática (7 días)
- [ ] Formato unificado

---

## MOL-15: Limpieza JSONs

**Épica:** 6 - Infraestructura | **Prioridad:** Baja | **Labels:** tech-debt

### Contexto
10,800 archivos JSON en 01_sources/*/data/raw/, muchos duplicados.

### Criterios de Aceptación
- [ ] Eliminar JSONs > 30 días ya procesados
- [ ] Liberar >1GB de espacio

---

## MOL-25: Entity resolution cross-source

**Épica:** 6 - Infraestructura | **Prioridad:** Media | **Labels:** etl, infra

### Contexto
Con 5 scrapers, la misma oferta puede aparecer en múltiples portales.

### Criterios de Aceptación
- [ ] Detección de duplicados basada en (titulo + empresa + ubicacion)
- [ ] Hash de deduplicación: `canonical_id`
- [ ] Sin falsos positivos

### Dependencias
- **Requiere:** MOL-18 (datos de múltiples fuentes)

---

# Grafo de Dependencias

```
                     ┌─────────────────────────────────┐
                     │         MOL-6                   │
                     │   Expandir Gold Set (Alta)      │
                     └─────────┬───────────────────────┘
                               │ mejora
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
     ┌─────────┐         ┌─────────┐         ┌─────────┐
     │  MOL-5  │         │  MOL-7  │         │  MOL-8  │
     │sector_fn│         │ Recall  │         │bilingüe │
     └────┬────┘         └─────────┘         └─────────┘
          │ estabiliza
          ▼
     ┌─────────┐
     │  MOL-9  │ CI/CD
     └─────────┘

     ┌─────────┐         ┌─────────┐
     │ MOL-18  │ ───────▶│ MOL-19  │
     │scrapers │         │pipeline │
     └────┬────┘         └─────────┘
          │
          ▼
     ┌─────────┐
     │ MOL-25  │ entity resolution
     └─────────┘

     ┌─────────┐         ┌─────────┐
     │ MOL-20  │ ───────▶│ MOL-13  │
     │  logs   │         │  admin  │
     └─────────┘         └─────────┘

     ┌─────────┐         ┌─────────┐
     │ MOL-16  │ ───────▶│ MOL-17  │
     │shinyTree│         │  auth   │
     └─────────┘         └─────────┘
```

---

> **Documento actualizado:** 2025-12-04
> **Total issues:** 29 (incluyendo 3 spikes)
> **Estructura:** 6 Épicas según MOL_LINEAR_METODOLOGIA.md
