# PROPUESTA DE IMPLEMENTACIÓN - MOL v2.0
## Monitor de Ofertas Laborales - Roadmap de Implementación por Fases

---

**Oficina de Empleo y Dinámica Empresarial (OEDE)**
**Ministerio de Trabajo, Empleo y Seguridad Social**
**República Argentina**

**Versión:** 1.0
**Fecha:** Noviembre 2025
**Autor:** Equipo Técnico OEDE

---

## RESUMEN EJECUTIVO

Esta propuesta organiza la implementación del Plan Técnico MOL v2.0 en **5 fases incrementales** durante **6 meses**, priorizando:

1. **Valor temprano:** Mejoras visibles en las primeras semanas
2. **Bajo riesgo:** No interrumpir el sistema actual en producción
3. **Validación continua:** Testing y feedback en cada fase
4. **Sin pérdida de contexto:** Fases cortas (3-4 semanas) con entregables concretos

---

## ESTRUCTURA DE FASES

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIMELINE DE 6 MESES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ FASE 0: Preparación          [2 semanas]  ███                  │
│ FASE 1: Fundamentos de datos [4 semanas]  ████████             │
│ FASE 2: Dashboard renovado   [4 semanas]      ████████         │
│ FASE 3: Scraping ampliado    [3 semanas]          ██████       │
│ FASE 4: Automatización       [3 semanas]              ██████   │
│ FASE 5: Optimización         [4 semanas]                  ████ │
│                                                     ▲           │
│                                              Lanzamiento v2.0   │
└─────────────────────────────────────────────────────────────────┘

Total: 20 semanas (~5 meses) + 1 mes de buffer
```

---

## FASE 0: PREPARACIÓN Y CONFIGURACIÓN
**Duración:** 2 semanas
**Objetivo:** Preparar el entorno y herramientas sin afectar producción

### Tareas

#### Semana 1: Infraestructura
- [ ] **Setup de entorno de desarrollo**
  - Clonar base de datos actual a BD de desarrollo
  - Configurar servidor de testing (localhost:3841 para Shiny, 8053 para Plotly)
  - Instalar dependencias actualizadas (R packages, Python libs)

- [ ] **Control de versiones**
  - Inicializar repositorio Git (si no existe)
  - Crear ramas: `main`, `development`, `feature/*`
  - Documentar workflow de Git para el equipo

- [ ] **Backup completo**
  - Backup de BD actual (ofertas_laborales.db)
  - Backup de código actual (scripts R y Python)
  - Backup de dashboards actuales

#### Semana 2: Documentación técnica
- [ ] **Mapeo de arquitectura actual**
  - Diagrama de flujo completo del sistema
  - Inventario de scripts (qué hace cada uno)
  - Dependencias entre componentes

- [ ] **Plan de testing**
  - Definir casos de prueba críticos
  - Preparar datos de prueba (100 ofertas sintéticas)
  - Establecer métricas de éxito por fase

- [ ] **Comunicación al equipo**
  - Reunión kickoff con stakeholders
  - Presentar roadmap y cronograma
  - Asignar roles y responsabilidades

### Entregables
✅ Entorno de desarrollo funcional
✅ Repositorio Git inicializado
✅ Plan de testing documentado
✅ Equipo alineado con el roadmap

### Criterios de éxito
- Sistema actual sigue funcionando sin cambios
- Equipo de desarrollo puede trabajar en paralelo sin conflictos
- Backups validados y recuperables

---

## FASE 1: FUNDAMENTOS DE DATOS
**Duración:** 4 semanas
**Objetivo:** Enriquecer y normalizar datos sin cambiar dashboards

### ¿Por qué empezar por aquí?
- **Bajo riesgo:** No toca la UI ni scraping, solo mejora datos internos
- **Alto impacto:** Habilita todas las mejoras futuras
- **Testeable:** Fácil validar con queries SQL

### Tareas

#### Semana 1-2: ESCO completo
- [ ] **Cargar 240,000 asociaciones ocupación-habilidad**
  - Script `cargar_esco_associations.py`
  - Leer archivo RDF local (1.35 GB)
  - Parsear relaciones `hasEssentialSkill` y `hasOptionalSkill`
  - Insertar en tabla `esco_occupation_skill_relations`
  - Validación: Verificar 240K registros insertados

- [ ] **Clasificación Knowledge vs Competencies**
  - Script `clasificar_skills_esco.py`
  - Implementar algoritmo de 3 niveles:
    - Nivel 1: Campo `skillType` de ESCO (75%)
    - Nivel 2: Campo `reuseLevel` (20%)
    - Nivel 3: Keywords en nombre (5%)
  - Nueva columna `skill_category` en tabla `esco_skills`
  - Validación: 90% con confianza >= 85%

#### Semana 3: Campos nuevos en NLP
- [ ] **Extender prompt de NLP v6.0**
  - Agregar 6 campos nuevos al prompt:
    1. `edad_min`, `edad_max`, `edad_categoria`
    2. `genero_requerido`
    3. `permanencia_tipo` (indefinido/plazo_fijo/temporal/pasantia)
    4. `ubicacion_requerida` (boolean)
    5. `provincia_codigo_indec`, `localidad_codigo_indec`
    6. `permanencia_oferta` (calculado: dias_activa)

- [ ] **Testing con 100 ofertas**
  - Ejecutar NLP v6.0 en subset de prueba
  - Validar manualmente 20 ofertas
  - Medir accuracy por campo (objetivo: >80%)

#### Semana 4: Normalización territorial
- [ ] **Tabla de códigos INDEC**
  - Crear tabla `indec_provincias` (24 registros)
  - Crear tabla `indec_localidades` (~5,000 registros)
  - Script de carga desde fuente oficial INDEC

- [ ] **Algoritmo de matching**
  - Script `normalizar_ubicaciones.py`
  - Fuzzy matching con threshold 85%
  - Manejo de casos especiales (CABA, GBA)
  - Validación manual de 50 ubicaciones ambiguas

### Entregables
✅ Tablas ESCO completas (3,008 ocupaciones + 14,247 skills + 240K relaciones)
✅ Skills clasificados en Knowledge/Competencies
✅ NLP v6.0 extrayendo 6 campos nuevos
✅ Ubicaciones normalizadas con códigos INDEC

### Criterios de éxito
```sql
-- Test 1: ESCO completo
SELECT COUNT(*) FROM esco_occupation_skill_relations;
-- Esperado: ~240,000

-- Test 2: Skills clasificados
SELECT skill_category, COUNT(*)
FROM esco_skills
GROUP BY skill_category;
-- Esperado: ~9,000 Knowledge, ~5,000 Competencies

-- Test 3: NLP v6.0
SELECT
  AVG(CASE WHEN edad_min IS NOT NULL THEN 1 ELSE 0 END) as cobertura_edad,
  AVG(CASE WHEN provincia_codigo_indec IS NOT NULL THEN 1 ELSE 0 END) as cobertura_ubicacion
FROM ofertas_nlp_v6;
-- Esperado: cobertura_edad > 0.3, cobertura_ubicacion > 0.8

-- Test 4: Normalización territorial
SELECT COUNT(DISTINCT provincia_codigo_indec) FROM ofertas_nlp_v6;
-- Esperado: 24 (las 24 provincias)
```

### Riesgos y mitigaciones
| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| Archivo RDF corrupto | Baja | Validar checksum antes de procesar |
| NLP v6.0 más lento | Media | Ejecutar solo en ofertas nuevas (incremental) |
| Ubicaciones no matchean | Alta | Crear diccionario manual de casos edge |

---

## FASE 2: DASHBOARD RENOVADO (SHINY v3.0)
**Duración:** 4 semanas
**Objetivo:** Lanzar nueva UI con 3 paneles y filtros globales

### ¿Por qué ahora?
- **Datos ya enriquecidos:** Fase 1 completó preparación de datos
- **Máximo impacto visible:** Usuarios ven mejoras inmediatamente
- **No depende de scraping:** Puede lanzarse con datos actuales

### Tareas

#### Semana 1: Arquitectura del dashboard
- [ ] **Diseño de estructura**
  - Crear mockups finales de los 3 paneles
  - Definir schema reactivo (filtros globales)
  - Planificar módulos Shiny reutilizables

- [ ] **Setup de proyecto Shiny v3.0**
  - Nuevo archivo `app_v3.R`
  - Estructura modular (archivos separados por panel)
  - Configuración de temas y estilos CSS

#### Semana 2: Panel izquierdo (Filtros globales)
- [ ] **Implementar 5 filtros**
  1. **Territorial:** Dropdown provincia → localidad (cascada)
  2. **Período:** Radio buttons (última semana/mes/año)
  3. **Permanencia:** Checkboxes (baja/media/alta)
  4. **Ocupación:**
     - Buscador de texto libre
     - Árbol navegable ISCO (4 niveles)
  5. **[Otros según panel]:** Dinámico

- [ ] **Lógica reactiva global**
  - `reactiveValues()` compartido entre paneles
  - Observers para actualizar subtítulo dinámico
  - Función `aplicar_filtros()` reutilizable

#### Semana 3: Los 3 paneles
- [ ] **Panel 1: PANORAMA GENERAL**
  - 3 InfoBoxes (ofertas/ocupaciones/habilidades)
  - Gráfico evolución temporal
  - Top 10 ocupaciones (barras horizontales)
  - Top 10 empresas (barras horizontales)
  - Botones "Exportar a Excel" en cada gráfico

- [ ] **Panel 2: REQUERIMIENTOS**
  - Gráfico torta: Requisito edad
  - Gráfico torta: Requisito género
  - Gráfico barras: Nivel educativo
  - Top 20 Conocimientos técnicos (separado)
  - Top 20 Competencias blandas (separado)

- [ ] **Panel 3: OFERTAS LABORALES**
  - DataTable interactivo con paginación
  - Filtros adicionales (edad, género, educación)
  - Modal con detalle completo al hacer click
  - Botón "Descargar base completa" (CSV)

#### Semana 4: Testing y refinamiento
- [ ] **Testing de usabilidad**
  - 5 usuarios internos prueban el dashboard
  - Recoger feedback con formulario
  - Identificar bugs y UX issues

- [ ] **Optimización de performance**
  - Implementar caché de datos (1 hora TTL)
  - Lazy loading de gráficos pesados
  - Testing de carga con 10,000 ofertas

- [ ] **Documentación de usuario**
  - Guía rápida (1 página PDF)
  - Tutorial en video (5 minutos)
  - Sección "Metodología" integrada

### Entregables
✅ Dashboard Shiny v3.0 funcional en testing
✅ 3 paneles implementados con todas las visualizaciones
✅ Filtros globales funcionando correctamente
✅ Guía de usuario documentada

### Criterios de éxito
- [ ] Usuario puede filtrar por provincia y ver reflejado en los 3 paneles
- [ ] Búsqueda de ocupaciones encuentra "desarrollador" en <2 segundos
- [ ] Exportación de gráficos genera Excel válido
- [ ] Dashboard carga en <5 segundos con 1,000 ofertas
- [ ] 5/5 usuarios completan tarea "Encontrar ofertas de desarrolladores en CABA" en <3 minutos

### Riesgos y mitigaciones
| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| Filtros globales complejos | Alta | Empezar con 3 filtros, agregar resto después |
| Performance con 10K ofertas | Media | Implementar paginación server-side |
| Árbol ISCO confuso | Media | Agregar tooltips explicativos |

---

## FASE 3: SCRAPING AMPLIADO
**Duración:** 3 semanas
**Objetivo:** Automatizar ComputRabajo y ZonaJobs

### ¿Por qué ahora?
- **Dashboard ya mejorado:** Nuevos datos tendrán dónde mostrarse
- **Independiente de otros cambios:** Puede fallar sin romper lo demás
- **Incremento de cobertura:** +1,200 ofertas/mes

### Tareas

#### Semana 1: Scraper ComputRabajo
- [ ] **Análisis de estructura web**
  - Inspeccionar HTML de ComputRabajo
  - Identificar selectores CSS para extracción
  - Mapear flujo de navegación (búsqueda → detalle)

- [ ] **Desarrollo del scraper**
  - Script `scraper_computrabajo.py`
  - Adaptación de lógica de Bumeran
  - Implementación de retry y error handling
  - Rate limiting (2 segundos entre requests)

- [ ] **Testing con 50 keywords**
  - Ejecutar scraper con subset de keywords
  - Validar campos extraídos (título, empresa, ubicación, etc.)
  - Medir tasa de éxito (objetivo: >90%)

#### Semana 2: Scraper ZonaJobs
- [ ] **Análisis de estructura web**
  - Inspeccionar HTML de ZonaJobs (más complejo que ComputRabajo)
  - Identificar si requiere JavaScript rendering (Selenium)
  - Mapear campos disponibles

- [ ] **Desarrollo del scraper**
  - Script `scraper_zonajobs.py`
  - Decidir: requests simples vs Playwright
  - Manejo de sesiones y cookies
  - Testing con 30 keywords

#### Semana 3: Integración y automatización
- [ ] **Scheduler unificado**
  - Modificar `scheduler.py` para incluir 3 portales
  - Configuración: Bumeran diario, ComputRabajo/ZonaJobs lun-mie-vie
  - Logging centralizado

- [ ] **Detección de duplicados cross-portal**
  - Mejorar algoritmo de similitud
  - Detectar misma oferta en Bumeran + ComputRabajo
  - Consolidar en un solo registro (preferir más completo)

- [ ] **Validación en producción**
  - Ejecutar scraping completo de 3 portales
  - Revisar dashboard técnico (tab "Scraping Monitor")
  - Ajustar umbrales de alertas

### Entregables
✅ Scraper ComputRabajo automatizado
✅ Scraper ZonaJobs automatizado
✅ Scheduler ejecutando 3 portales
✅ +1,200 ofertas/mes nuevas capturadas

### Criterios de éxito
```sql
-- Test: Ofertas por portal (último mes)
SELECT portal, COUNT(*) as ofertas
FROM ofertas_raw
WHERE fecha_scraping >= DATE('now', '-30 days')
GROUP BY portal;

-- Esperado:
-- bumeran: ~4,100
-- computrabajo: ~800
-- zonajobs: ~400
-- TOTAL: ~5,300 (+20% vs antes)
```

### Riesgos y mitigaciones
| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| Portal detecta y bloquea bot | Media | User-Agent realista, delays aleatorios |
| Estructura web cambia | Alta | Monitoreo semanal, alertas automáticas |
| ZonaJobs requiere Selenium | Media | Plan B: continuar scraping manual |

---

## FASE 4: AUTOMATIZACIÓN DEL PIPELINE
**Duración:** 3 semanas
**Objetivo:** Ejecutar NLP, ESCO y actualización de dashboard automáticamente

### ¿Por qué ahora?
- **Scraping ya ampliado:** Más datos requieren procesamiento automático
- **NLP v6.0 ya probado:** En Fase 1 se validó funcionamiento
- **Eliminar trabajo manual:** De 2 horas/semana a 0

### Tareas

#### Semana 1: Automatización NLP
- [ ] **Pipeline incremental**
  - Script `pipeline_nlp_incremental.py`
  - Procesar solo ofertas nuevas (WHERE nlp_procesado = 0)
  - Batch de 100 ofertas por ejecución (evitar timeout)
  - Guardar progreso cada 50 ofertas

- [ ] **Scheduler nocturno**
  - Configurar ejecución diaria a las 2:00 AM
  - Después de scraping, antes de ESCO
  - Timeout: 2 horas máximo
  - Alertas si falla

#### Semana 2: Automatización ESCO matching
- [ ] **Pipeline de clasificación**
  - Script `pipeline_esco_matching.py`
  - Procesar ofertas con NLP completo
  - Usar asociaciones ocupación-skill (cargadas en Fase 1)
  - Calcular score ponderado (esenciales 70%, opcionales 30%)

- [ ] **Validación continua**
  - Cada ejecución guarda métricas:
    - % ofertas clasificadas
    - Confidence promedio
    - Top 10 ocupaciones del día
  - Dashboard técnico muestra histórico de métricas

#### Semana 3: Actualización automática del dashboard
- [ ] **Regeneración de CSV**
  - Script `exportar_dashboard_data.py`
  - Genera `ofertas_esco_shiny.csv` actualizado
  - Solo incluye ofertas con ESCO confidence >= 70%
  - Se ejecuta después de ESCO matching

- [ ] **Despliegue automático a shinyapps.io**
  - Script `deploy_dashboard.sh`
  - Sube CSV actualizado a shinyapps.io
  - Reinicia aplicación Shiny
  - Se ejecuta después de regenerar CSV

- [ ] **Orquestación completa**
  - Pipeline unificado `run_daily_pipeline.py`:
    1. Scraping (8:00 AM)
    2. NLP (2:00 AM siguiente día)
    3. ESCO matching (4:00 AM)
    4. Exportar CSV (5:00 AM)
    5. Deploy dashboard (5:30 AM)
  - Email con reporte diario del pipeline

### Entregables
✅ Pipeline NLP automático
✅ Pipeline ESCO automático
✅ Dashboard público autoactualizado
✅ 0 horas de trabajo manual semanal

### Criterios de éxito
- [ ] Pipeline completo se ejecuta diariamente sin intervención
- [ ] Dashboard público muestra datos de ayer como máximo
- [ ] Email de reporte llega cada mañana con status OK
- [ ] Si falla un paso, no rompe los siguientes

### Riesgos y mitigaciones
| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| NLP timeout con muchas ofertas | Media | Limitar a 500 ofertas/día, procesar resto mañana siguiente |
| Despliegue a shinyapps.io falla | Baja | Retry 3 veces, alerta si falla |
| Pipeline se traba y nadie se entera | Media | Heartbeat cada hora, alerta si >2hrs sin actividad |

---

## FASE 5: OPTIMIZACIÓN Y CIERRE
**Duración:** 4 semanas
**Objetivo:** Pulir detalles, optimizar performance, documentar

### Tareas

#### Semana 1: Optimización de performance
- [ ] **NLP v6.0 más rápido**
  - Probar modelos más rápidos (llama3.1:8b → phi-3)
  - Batch processing en paralelo (4 ofertas simultáneas)
  - Medir mejora (objetivo: -30% tiempo)

- [ ] **Dashboard más rápido**
  - Implementar caché agresivo (4 horas)
  - Precomputar agregaciones pesadas
  - Lazy loading de tabs no visibles

- [ ] **Base de datos optimizada**
  - Crear índices en campos más consultados
  - Vacuum y optimización de SQLite
  - Archivar ofertas >1 año

#### Semana 2: Mejoras del dashboard técnico
- [ ] **Agregar tabs faltantes**
  - Tab "NLP": Métricas de extracción por campo
  - Tab "ESCO": Distribución de confidence
  - Tab "Alertas": Sistema de alertas implementado

- [ ] **Dashboard de datos**
  - Tab "Datos": Explorador de ofertas completo
  - Tab "Diccionario": Documentación de variables
  - Tab "SQL Explorer": Query builder básico

#### Semana 3: Testing integral
- [ ] **Testing de regresión**
  - Verificar que sistema actual sigue funcionando
  - Comparar métricas v2.0 vs v1.0 (cobertura, accuracy)
  - Testing con usuarios reales (5 personas)

- [ ] **Testing de carga**
  - Simular 10 usuarios simultáneos en dashboard
  - Verificar pipeline con 1,000 ofertas nuevas
  - Medir tiempos de respuesta

#### Semana 4: Documentación y capacitación
- [ ] **Documentación técnica**
  - README actualizado con arquitectura v2.0
  - Guía de deployment y mantenimiento
  - Troubleshooting de problemas comunes

- [ ] **Documentación de usuario**
  - Manual de usuario del dashboard (10 páginas)
  - Videos tutoriales (3 videos de 5 min c/u)
  - FAQ con 20 preguntas frecuentes

- [ ] **Capacitación al equipo**
  - Workshop de 2 horas para analistas
  - Workshop de 2 horas para equipo técnico
  - Q&A y recolección de feedback

### Entregables
✅ Sistema v2.0 optimizado y testeado
✅ Dashboard técnico completo
✅ Documentación completa (técnica y usuario)
✅ Equipo capacitado

### Criterios de éxito
- [ ] NLP procesa 100 ofertas en <30 minutos (antes: 45 min)
- [ ] Dashboard carga en <3 segundos (antes: 5 seg)
- [ ] 5/5 usuarios pueden usar dashboard sin ayuda
- [ ] 0 bugs críticos detectados en testing

---

## CRONOGRAMA DETALLADO

```
┌──────────┬───────────────────────────────────────────────────┐
│  Fase    │  Semana 1  2  3  4  5  6  7  8  9  10 11 12 13... │
├──────────┼───────────────────────────────────────────────────┤
│ FASE 0   │  ██████                                           │
│          │  Prep infraestructura                             │
├──────────┼───────────────────────────────────────────────────┤
│ FASE 1   │      ████████████████████                         │
│          │      ESCO + NLP v6 + Normalización                │
├──────────┼───────────────────────────────────────────────────┤
│ FASE 2   │                      ████████████████████         │
│          │                      Dashboard Shiny v3.0         │
├──────────┼───────────────────────────────────────────────────┤
│ FASE 3   │                                      ██████████   │
│          │                                      Scraping x3  │
├──────────┼───────────────────────────────────────────────────┤
│ FASE 4   │                                            ██████ │
│          │                                            Pipeline│
├──────────┼───────────────────────────────────────────────────┤
│ FASE 5   │                                                ████│
│          │                                                Optim│
└──────────┴───────────────────────────────────────────────────┘

Semanas totales: ~20 (5 meses)
```

### Hitos clave

| Semana | Hito | Criterio de aprobación |
|--------|------|------------------------|
| 2 | Kickoff completado | Equipo alineado, Git funcionando |
| 6 | ESCO completo | 240K relaciones cargadas, queries validan |
| 10 | Dashboard v3.0 lanzado | 5 usuarios aprueban usabilidad |
| 13 | Scraping x3 automatizado | +20% ofertas/mes capturadas |
| 16 | Pipeline automático | 0 intervención manual por 1 semana |
| 20 | v2.0 en producción | Documentación completa, equipo capacitado |

---

## GESTIÓN DE RIESGOS

### Riesgos técnicos

| Riesgo | Impacto | Probabilidad | Mitigación | Plan B |
|--------|---------|--------------|------------|--------|
| **NLP v6.0 muy lento** | Alto | Media | Optimizar con batching paralelo | Usar modelo más rápido (phi-3) |
| **Portales bloquean scraping** | Alto | Media | User-agents realistas, delays | Explorar APIs oficiales de pago |
| **ESCO RDF corrupto** | Medio | Baja | Validar checksum antes de leer | Re-descargar de fuente oficial |
| **Dashboard Shiny crash con 10K ofertas** | Medio | Media | Paginación server-side | Limitar a 5K ofertas más recientes |
| **Pipeline automático se traba** | Alto | Media | Heartbeat + alertas | Restart automático cada 24hrs |

### Riesgos de proyecto

| Riesgo | Impacto | Probabilidad | Mitigación | Plan B |
|--------|---------|--------------|------------|--------|
| **Pérdida de contexto entre fases** | Alto | Media | Fases cortas (3-4 semanas) | Documentar decisiones en Git |
| **Equipo sobrecargado** | Medio | Alta | Priorizar tareas críticas | Extender timeline 2 semanas |
| **Stakeholders cambian prioridades** | Medio | Media | Presentar roadmap al inicio | Replantear fases 4-5 |
| **Testing insuficiente** | Alto | Baja | Testing en cada fase | Agregar semana de QA final |

---

## RECURSOS NECESARIOS

### Equipo

| Rol | Dedicación | Responsabilidades principales |
|-----|------------|-------------------------------|
| **Desarrollador Backend (Python)** | 100% (5 meses) | NLP, ESCO, scraping, pipeline |
| **Desarrollador Frontend (R Shiny)** | 100% (3 meses, fases 2-4) | Dashboard v3.0, visualizaciones |
| **Analista de datos** | 30% (5 meses) | Testing, validación, feedback |
| **DevOps/Sysadmin** | 20% (5 meses) | Infraestructura, deployment |
| **Product Owner** | 10% (5 meses) | Priorización, aprobación de fases |

**Total estimado:** 2.6 FTE (personas a tiempo completo equivalente)

### Infraestructura

| Recurso | Costo mensual | Justificación |
|---------|---------------|---------------|
| **Servidor de desarrollo** | $0 (usar PCs existentes) | Testing local |
| **shinyapps.io Pro** | USD 99/mes | Hosting dashboard público |
| **Backup en cloud (Google Drive)** | $0 (cuenta institucional) | Backups automáticos |
| **Dominio .gob.ar** | $0 (ya existe) | URL del dashboard |

**Total estimado:** USD 99/mes × 6 meses = **USD 594**

### Software

| Herramienta | Licencia | Costo |
|-------------|----------|-------|
| R + RStudio | Open source | $0 |
| Python + Ollama | Open source | $0 |
| SQLite | Open source | $0 |
| Git + GitHub | Free tier | $0 |
| Pandoc (conversión docs) | Open source | $0 |

**Total:** **$0** (todo open source)

---

## CRITERIOS DE ÉXITO GLOBAL

Al finalizar las 5 fases, el sistema MOL v2.0 debe cumplir:

### Métricas técnicas

| Métrica | Valor actual | Objetivo v2.0 | Mejora |
|---------|--------------|---------------|--------|
| **Ofertas capturadas/mes** | 6,100 | 8,500 | +39% |
| **Portales automatizados** | 1/5 (20%) | 3/5 (60%) | +40pp |
| **Trabajo manual semanal** | 2 horas | 0 horas | -100% |
| **Campos extraídos por oferta** | 11 | 17 | +55% |
| **Ocupaciones clasificadas** | 268 (4%) | 6,000+ (70%) | +66pp |
| **Accuracy de clasificación ESCO** | 65% | 90% | +38% |
| **Tiempo de carga dashboard** | 5 seg | <3 seg | -40% |

### Métricas de producto

| Criterio | Cómo medirlo | Objetivo |
|----------|--------------|----------|
| **Usabilidad** | Test con 5 usuarios (tareas predefinidas) | 5/5 completan sin ayuda |
| **Performance** | Simular 10 usuarios simultáneos | <5 seg carga |
| **Confiabilidad** | Monitoreo 1 mes post-lanzamiento | >99% uptime |
| **Completitud de datos** | % ofertas con todos los campos | >80% completos |

### Criterios de aceptación

- [ ] Dashboard v3.0 aprobado por 5 stakeholders (directores, analistas)
- [ ] Pipeline automático ejecutándose sin fallos por 2 semanas
- [ ] Documentación completa y actualizada
- [ ] 0 bugs críticos en producción
- [ ] Equipo capacitado y puede mantener el sistema

---

## PLAN DE ROLLBACK

Si en cualquier fase algo falla críticamente:

### Estrategia general
1. **Sistema actual sigue en producción** (no se toca hasta Fase 5)
2. **Desarrollo en paralelo** (rama `development`, no afecta `main`)
3. **Backups semanales** de BD y código

### Rollback por fase

| Fase | Si falla... | Plan de rollback |
|------|-------------|------------------|
| **Fase 1** | ESCO no carga correctamente | Revertir cambios en BD, usar ESCO parcial (solo ocupaciones) |
| **Fase 2** | Dashboard v3.0 tiene bugs | Mantener dashboard v2.4 en producción, arreglar en desarrollo |
| **Fase 3** | Scrapers nuevos no funcionan | Continuar solo con Bumeran, scraping manual de otros portales |
| **Fase 4** | Pipeline se traba constantemente | Volver a ejecución manual, revisar logs |
| **Fase 5** | Performance peor que antes | Revertir optimizaciones, usar versión estable anterior |

### Criterio para activar rollback

**ROLLBACK AUTOMÁTICO si:**
- Sistema actual deja de funcionar por >4 horas
- Pérdida de datos detectada
- Bug que impide uso del dashboard por >24 horas

**ROLLBACK POR DECISIÓN si:**
- 3+ stakeholders solicitan volver atrás
- Costo de arreglar > costo de rehacer
- Timeline se extiende >2 semanas de lo planeado

---

## COMUNICACIÓN Y REPORTING

### Ceremonias semanales

**Lunes 10:00 AM - Planning semanal (30 min)**
- Qué se hizo la semana pasada
- Qué se hará esta semana
- Blockers y riesgos

**Viernes 15:00 PM - Demo y retrospectiva (45 min)**
- Demo de lo desarrollado (si hay entregable)
- Qué salió bien / mal
- Ajustes para próxima semana

### Reportes

**Reporte semanal (email):**
- Progreso de fase actual (% completado)
- Hitos alcanzados
- Riesgos detectados
- Próximos pasos

**Reporte de fin de fase (presentación):**
- Demostración en vivo de entregables
- Métricas de éxito alcanzadas
- Lessons learned
- Aprobación para pasar a siguiente fase

### Stakeholders a mantener informados

| Rol | Frecuencia | Canal |
|-----|------------|-------|
| **Director OEDE** | Fin de fase (mensual) | Presentación 30 min |
| **Analistas usuarios** | Semanal | Email + demos |
| **Equipo técnico** | Diario | Stand-up 15 min |
| **Ministerio (si aplica)** | Fin de proyecto | Presentación formal |

---

## SIGUIENTE PASO INMEDIATO

Para comenzar la implementación:

1. **Aprobar esta propuesta** con stakeholders
2. **Asignar equipo** y confirmar dedicación
3. **Agendar kickoff meeting** (Fase 0, Semana 1)
4. **Crear repositorio Git** y estructura de proyecto
5. **Comenzar Fase 0** la próxima semana

---

## ANEXO: CHECKLIST DE INICIO

Antes de comenzar Fase 0, verificar:

- [ ] Presupuesto aprobado (USD 594 para shinyapps.io)
- [ ] Equipo asignado y disponible
- [ ] Acceso a servidor de desarrollo
- [ ] Acceso a BD de producción (solo lectura)
- [ ] Acceso a repositorio de código actual
- [ ] Backup de sistema actual completado
- [ ] Stakeholders alineados con roadmap
- [ ] Fecha de kickoff confirmada

---

**FIN DE PROPUESTA DE IMPLEMENTACIÓN**

---

**Contacto:**
Equipo Técnico OEDE
oede@trabajo.gob.ar
