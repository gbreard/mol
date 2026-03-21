# 9. Roadmap de Implementación

> Última actualización: 2026-03-20
> Versión: 4.0 — Roadmap unificado (Dashboard + Skills Intelligence)

## Referencias

| Documento | Relación |
|-----------|----------|
| [06_SEGURIDAD](./06_SEGURIDAD.md) | Fase 0 completa |
| [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) | Fase 1 |
| [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md) | Fases 2-4 |
| [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md) | Modelo híbrido v2.0 |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Prioridades | Este documento |
| Issues resueltos | Marcar como completado aquí |
| Nuevos issues | Agregar a fase correspondiente |

---

## Visión General

El proyecto tiene dos dimensiones que avanzan en paralelo compartiendo el motor de datos:

```
DASHBOARD (análisis)          SKILLS INTELLIGENCE (servicios)
═══════════════════          ════════════════════════════════

Fase 0 Seguridad ✅ (parcial)
Fase 1 Escalabilidad ✅
                              Bloque A: Componentes compartidos
Fase 2 Valor datos 🟡          (report engine, PDF, QR, vías captura)
                              Bloque B: S2 — Oficina de Empleo (primer cliente)
Fase 3 Features 🟡            Bloque C: S1 — Mi Futuro Laboral (trabajador)
                              Bloque D: S3 — Empresas (libre + registrado)
Fase 4 Diferenciación ⬜      Bloque E: Inteligencia avanzada + certificación

    DATOS ──────────────────► alimentan ambas dimensiones
    (pipeline scraping + NLP + matching + validación)
```

### Estado actual de los datos (2026-03-20)

| Métrica | Valor | Estado |
|---------|-------|--------|
| Ofertas en BD | 37,785 | ✅ |
| Con NLP | 37,776 (99%) | ✅ Superado (era 49%) |
| Validadas | 15,968 (42%) | ✅ Superado (era 1%) |
| En Supabase | 15,968 | ✅ Sincronizado |
| ESCO Argentino | Implementado | ✅ Tabla + API + panel |
| Cursos CABA scrapeados | 2,255 | ✅ Disponible |
| Portales scraping activos | 6 (VPS) | ✅ Cron Lun/Jue |

---

## DIMENSIÓN 1: DASHBOARD DE ANÁLISIS

### Fase 0: Seguridad (BLOQUEANTE)

**Estado:** 🟡 En progreso (4/5 tareas — falta rotar key Supabase)

### Tareas

| ID | Tarea | Prioridad | Estado |
|----|-------|-----------|--------|
| S-01 | Rotar tokens expuestos | CRITICO | 🟡 Código limpio, **rotación manual pendiente** |
| S-02 | Fix open redirect en callback | CRITICO | ✅ Completado 2026-02-22 |
| S-03 | Implementar RLS en tablas | CRITICO | ⬜ |
| S-04 | Verificar rol en APIs admin | CRITICO | ✅ Completado 2026-02-22 |
| S-07 | Headers de seguridad | ALTO | ⬜ |

### Checklist Pre-Fase-1

```
□ Tokens de Supabase rotados (código limpio, rotación manual PENDIENTE)
✓ .env* en .gitignore
✓ Redirect validado contra whitelist (S-02)
□ RLS activo en suscripciones, pagos, alertas, solicitudes_acceso, contenidos
✓ Middleware verifica rol admin (S-04)
□ Headers de seguridad en next.config.js
```

### Criterio de Éxito

- 0 vulnerabilidades críticas
- Penetration test básico sin hallazgos graves

---

## Fase 1: Escalabilidad Básica

**Estado:** 🟢 Completada (5/7 tareas core, 2 mejoras pendientes)
**Duración estimada:** 1 semana

### Tareas

| ID | Tarea | Prioridad | Estado |
|----|-------|-----------|--------|
| E-01 | Reemplazar .limit(10000) | CRITICO | ✅ Completado 2026-02-23 (SQL RPCs) |
| E-02 | Usar vistas SQL existentes | CRITICO | ✅ Completado 2026-02-23 (5 RPCs) |
| E-03 | Implementar React Query | CRITICO | ✅ Completado 2026-02-23 |
| **E-16** | **Insights SQL (no fetchAllPaginated)** | **CRITICO** | ✅ Completado 2026-02-07 |
| E-05 | Agregar índices críticos | ALTO | ✅ Completado 2026-02-23 (3 índices performance) |
| S-05 | Rate limiting en APIs | ALTO | ⬜ |
| S-06 | Validación con Zod | ALTO | ⬜ |

> **E-01/E-02/E-03 Resueltos:** 5 SQL RPCs (`get_panorama`, `get_evolucion`, `get_requerimientos`, `get_skills_resumen`, `get_sidebar_counts`) + React Query hooks + componentes migrados. 153 tests passing.

### Criterio de Éxito

| Métrica | Antes | Después |
|---------|-------|---------|
| Time to First Byte | ~800ms | < 400ms |
| Queries por página | ~10 | < 5 |
| Datos truncados | Sí | No |

---

### Fase 2: Valor de Datos

**Estado:** 🟢 Superado en datos (NLP 99%, validadas 42%). Pendiente UI de salarios y tendencias.

| ID | Tarea | Prioridad | Estado |
|----|-------|-----------|--------|
| V-02 | Backfill NLP | CRITICO | ✅ 99% procesado (37,776/37,785) |
| V-01 | Acelerar validación | CRITICO | ✅ 42% validadas (15,968) |
| V-04 | Habilitar análisis salarios | CRITICO | ⬜ Datos existen, UI pendiente |
| V-07 | Gráficos tendencias | ALTO | ⬜ |
| V-16 | Tensión de demanda | ALTO | ⚠️ Parcial (datos + laboratorio admin, falta dashboard público) |

---

## Fase 3: Features Comerciales + Modelo Híbrido

**Estado:** 🟡 En progreso (acceso gated implementado, CMS y pagos pendientes)
**Duración estimada:** 4-6 semanas

### Tareas — Acceso y Autenticación

| ID | Tarea | Prioridad | Pantalla | Estado |
|----|-------|-----------|----------|--------|
| - | Registro libre (sin plan) | ALTO | P-05 | ⬜ |
| - | Área de contenido (registrados) | ALTO | P-26, P-27 | ✅ Placeholder (2026-03-03) |
| - | Solicitud de acceso al tablero | ALTO | P-28 | ✅ Completado (2026-03-03) |
| - | Gestión solicitudes (admin) | ALTO | P-29 | ✅ Completado (2026-03-03) |
| - | Workflow aprobación + email | ALTO | P-29 → email | 🟡 Aprobación OK, email pendiente |
| - | Activación trial automática (7 días) | ALTO | Función BD | ✅ Completado (2026-03-03) |
| - | Middleware dashboard gating (trial/suscriptor) | ALTO | middleware.ts | ✅ Completado (2026-03-03) |
| - | Oficina de Empleo wireframes | MEDIO | /oficina-empleo/* | ✅ Wireframes (2026-03-03) |
| - | GlobalNav plan-aware | ALTO | GlobalNav.tsx | ✅ Completado (2026-03-03) |
| - | Home page 4-state CTAs | ALTO | /home | ✅ Completado (2026-03-03) |

> **Sprint 13 (2026-03-03):** Implementado sistema completo de acceso gated: solicitar-acceso → admin aprueba → trial 7 días se activa automáticamente. Middleware protege /dashboard (requiere admin/suscriptor/trial activo). GlobalNav muestra items según rol+plan. Oficina de empleo con wireframes estáticos. Contenido como placeholder. Migration SQL 017 + RLS en solicitudes_acceso.

### Tareas — CMS

| ID | Tarea | Prioridad | Pantalla |
|----|-------|-----------|----------|
| - | CRUD de contenidos (admin) | ALTO | P-30 |
| - | Distribución por email | ALTO | Sistema |
| - | Métricas de contenido (aperturas, descargas) | MEDIO | P-30 |

### Tareas — Pago Dual

| ID | Tarea | Prioridad | Pantalla |
|----|-------|-----------|----------|
| - | Checkout MercadoPago | ALTO | P-06, P-07, P-08 |
| - | Flujo pago institucional (orden compra) | ALTO | P-06 variante |
| - | Gestión suscripciones | ALTO | P-15 |
| - | Webhook MercadoPago (F-04) | ALTO | API |

### Tareas — Features Dashboard

| ID | Tarea | Prioridad | Pantalla |
|----|-------|-----------|----------|
| V-05 | Alertas por email | ALTO | P-13 |
| V-09 | Export Excel/PDF | ALTO | P-12 |
| V-08 | API pública (Institucional) | ALTO | Nueva |
| V-10 | Skills gap analysis | ALTO | Nueva |
| V-17 | Reporte Compatibilidad Laboral (PDF+QR+web interactivo) | ALTO | P-10 (mod), P-35 (nueva) |

### Criterio de Éxito

| Métrica | Meta |
|---------|------|
| Usuarios registrados | 200 |
| Solicitudes de tablero | 50 |
| Suscriptores activos | 10 |
| Contenidos publicados | 6 |
| Tasa apertura emails | > 30% |

---

## Fase 4: Diferenciación

**Estado:** ⬜ Pendiente
**Duración estimada:** 2-3 meses

### Tareas

| ID | Tarea | Descripción |
|----|-------|-------------|
| V-03 | ML Predictivo | Tendencias futuras de ocupaciones |
| V-06 | Comparador salarios | Por ocupación, provincia |
| V-14 | Dashboard personalizable | Widgets drag & drop |
| - | Integración LinkedIn | Import de perfil |
| - | Segmentación de contenido | CMS envía por interés/perfil |

---

---

## DIMENSIÓN 2: SKILLS INTELLIGENCE

> **Fuente:** `docs/MOL_Skills_Intelligence.docx` v5.0 + `docs/mol_screens_v5.html`
> **Estrategia:** Las Oficinas de Empleo son el primer cliente (ya tienen datos). El trabajador individual se activa cuando hay datos reales de OEs.

### Bloque A: Componentes compartidos (habilita todo lo demás)

**Dependencia:** Ninguna — se puede empezar ya. Estos componentes son usados por S1, S2 y S3.

| # | Tarea | Componente técnico | Existe |
|---|-------|--------------------|--------|
| A1 | Vía 2 de captura: búsqueda por tarea/habilidad | Búsqueda en 14K+ skills por nombre + definición | ❌ |
| A2 | Vía 3 de captura: texto libre → skills | NLP que identifica competencias de texto narrativo | ❌ |
| A3 | Definiciones ESCO visibles en cada skill | UI: mostrar descripción + checkbox confirmar/dudar/descartar | ❌ |
| A4 | Tab Ofertas laborales en resultados | JOIN ocupaciones compatibles × ofertas_dashboard con gap | ❌ |
| A5 | Tab Capacitación en resultados | Matching brechas × cursos CABA + transición dual (preferencia/demanda) | ❌ |
| A6 | Generación de reporte + PDF + QR | API /api/compatibility-report + jsPDF + qrcode | ❌ |
| A7 | Página /reporte/{token} | Reporte web público interactivo (S3 nivel libre) | ❌ |
| A8 | Tabla reportes_compatibilidad | Migration SQL + RLS por token | ❌ |

**Lo que ya existe y se reutiliza:**
- Motor de matching MySkillsSearch (897 líneas) ✅
- API perfiles trabajadores CRUD ✅
- ESCO Argentino + panel aprobación ✅
- 14,257 skills con definición + embeddings (100%) ✅
- Vía 1 (por ocupación) ✅
- NLP v11.4 (extracción de skills de texto) ✅
- Skills extractor LoRA fine-tuned (BGE-M3) ✅
- occupation_similarity.json (similitud entre ocupaciones) ✅
- Export Excel (xlsx) ✅

### Motor de datos y semántica por bloque

Cada bloque tiene una capa de UI y una capa de **datos/semántica** que es el corazón. Sin la capa de datos, la UI no tiene qué mostrar.

#### Bloque A — Motor semántico

| # | Tarea datos/semántica | Detalle técnico | Existe |
|---|----------------------|-----------------|--------|
| A-D1 | Búsqueda de skills (2 fases) | **Fase 1 (MVP):** Búsqueda full-text por label + description en catálogo unificado (16,633 skills). Frontend puro, sin infra adicional. **Fase 2 (evolución):** Búsqueda semántica con embeddings pre-calculados — generar vectors de las 16K skills con BGE-M3 offline, almacenar en pgvector (Supabase) o JSON estático, comparar en query time. "soldar" encontraría "unión de piezas metálicas" sin contener la palabra. Requiere pgvector en Supabase (disponible en free tier) | ❌ → Fase 1 primero |
| A-D2 | NLP texto narrativo → skills (2 fases) | **Fase 1 (MVP):** Extraer keywords del texto + buscar en catálogo con full-text (misma lógica A-D1). **Fase 2 (evolución):** Usar embeddings del texto completo contra embeddings de skills para matching semántico | ❌ → Fase 1 primero |
| A-D3 | Catálogo unificado: ESCO + emergentes argentinas | `skills_searchable.json` con 16,633 skills (14,257 ESCO + 2,376 emergentes). Campo `source` en cada skill. Script `regenerate_skills_searchable.py` | ✅ `deb161cf` |
| A-D4 | Matching perfil × ofertas con gap personalizado | Función que cruza skills del trabajador contra skills de cada oferta en `ofertas_dashboard`. Retorna: cubiertas, faltantes, % | ❌ |
| A-D5 | Matching brechas × cursos CABA | **Fase 1:** Búsqueda full-text de skills faltantes contra nombre + descripción + plan de estudio de los 2,255 cursos. **Fase 2:** Embeddings de cursos para matching semántico | ❌ → Fase 1 primero |
| A-D6 | Tendencia temporal por ISCO | Query: count ofertas por isco_code en ventana reciente vs anterior. Calcular % crecimiento | ❌ (datos existen) |
| A-D7 | Distancia entre ocupaciones | Calcular "N skills te separan de X" usando perfil argentino, no solo ESCO puro | ⚠️ Parcial (similarity.json existe pero usa ESCO puro) |

#### Gestión del Perfil Consolidado Argentino

> El perfil consolidado es la taxonomía de referencia para todo el sistema. Su calidad determina la calidad de todo lo demás.

| # | Tarea | Detalle | Existe |
|---|-------|---------|--------|
| PCA-1 | Corte de versión global + UI admin | Pantalla en /admin/skills o dedicada donde el analista: (1) ve estado actual del perfil (emergentes pendientes, cambios desde último corte), (2) hace click "Crear versión X.Y", (3) el sistema congela un snapshot completo, (4) el sistema apunta a esa versión para todo el matching. Historial de versiones consultable. Posibilidad de rollback | ❌ |
| PCA-2 | Proceso de curación definido | Workflow automatizado en Supabase (ver detalle abajo) | ⚠️ Panel existe, proceso por crear |
| PCA-3 | Recálculo automático post-sync | Función RPC `recalcular_emergentes()` en Supabase llamada al final de `sync_to_supabase.py`. Recalcula frecuencias y detecta emergentes nuevas | ❌ |
| PCA-4 | Regenerar catálogo búsqueda (A-D3) | Trigger: cuando se aprueba/rechaza una emergente → regenerar `skills_searchable.json` incluyendo emergentes | ❌ (script existe, falta trigger) |
| PCA-5 | Integrar perfil argentino en matching del trabajador | MySkillsSearch compara contra perfil consolidado. Hook `usePerfilArgentino` + fallback ESCO puro | ✅ `9eede9d2` |
| PCA-6 | Métricas y monitoreo del perfil | Badge en P-36 con emergentes pendientes + dashboard métricas | ⚠️ Parcial |
| PCA-7 | Regenerar reporte contra versión nueva | Si el trabajador quiere, puede regenerar su reporte contra la versión actual del perfil (el original queda como snapshot) | ❌ |

#### Bloque 9° — Workflow curación automática del perfil (detalle PCA-2 + PCA-3)

> **Decisión de diseño:** Función RPC en Supabase (no trigger por fila). Se llama una vez al final del sync. Tabla `emergentes_pendientes` para almacenar resultados. Badge en P-36 para notificar.

**Flujo completo:**

```
sync_to_supabase.py sube ofertas nuevas a ofertas_dashboard
    ↓
Al final del sync: supabase.rpc('recalcular_emergentes')
    ↓
La función SQL en Supabase:
  1. Cruza ofertas_skills × esco_argentino por ocupación
  2. Calcula frecuencia de cada skill por ISCO (% de ofertas que la mencionan)
  3. Identifica skills con frecuencia ≥30% que NO están en el perfil consolidado activo
  4. INSERT/UPDATE en tabla emergentes_pendientes (skill, isco, frecuencia, fecha_deteccion)
  5. Retorna: { nuevas: N, actualizadas: M }
    ↓
P-36 muestra badge: "5 emergentes nuevas para revisar"
    ↓
Analista va al panel Consolidado → revisa → aprueba/rechaza
    ↓
Cuando está conforme → corte de versión en P-36
    ↓
Post-corte: regenerar skills_searchable.json (script existente)
```

**Componentes a crear:**

| # | Componente | Tipo | Detalle |
|---|-----------|------|---------|
| PCA-3a | Tabla `emergentes_pendientes` | Migration SQL | skill_label, skill_uri, isco_code, ocupacion_label, frecuencia_pct, estado (pendiente/aprobada/rechazada), fecha_deteccion, fecha_resolucion |
| PCA-3b | Función `recalcular_emergentes()` | RPC Supabase | Query: ofertas_skills GROUP BY isco + skill, filtra ≥30%, compara con perfil activo, inserta nuevas en emergentes_pendientes |
| PCA-3c | Llamada post-sync | Python | Agregar `supabase.rpc('recalcular_emergentes')` al final de `sync_to_supabase.py` |
| PCA-6a | Badge emergentes en P-36 | UI (Sergio) | GET /api/emergentes-pendientes/count → badge numérico en botón "Revisar emergentes" |
| PCA-6b | API `/api/emergentes-pendientes` | API route | GET: lista pendientes. PATCH: aprobar/rechazar (actualiza esco_argentino + marca resuelta) |

**Tests:**

| Test | Tipo | Qué valida |
|------|------|------------|
| `unit/recalcular-emergentes.test.ts` | Unit | Skills con ≥30% se detectan. Skills ya aprobadas no se duplican. Skills <30% no aparecen. Retorna conteo correcto |
| `integration/post-sync-emergentes.test.ts` | Integration | Después del sync, emergentes_pendientes tiene datos. Badge muestra número correcto |

#### Bloque B — Datos de pools OE

| # | Tarea datos/semántica | Detalle técnico | Existe |
|---|----------------------|-----------------|--------|
| B-D1 | Parser Excel/CSV → modelo interno | Mapear columnas de planillas OE a estructura interna. Detectar formato, validar, sanitizar | ❌ |
| B-D2 | NLP sobre vacantes texto libre de OE | La empresa local describe la vacante en texto → NLP extrae skills ESCO (reusar pipeline v11.4) | ❌ (pipeline existe, adaptar) |
| B-D3 | Mapeo cursos OE → skills ESCO | Catálogo de cursos de la OE (nombre + desc) mapeado a skills con embeddings o keywords | ❌ |
| B-D4 | Cálculo impacto formación | "Si completás este curso, tu match con estas vacantes sube de X% a Y%" — requiere simular el perfil + curso | ❌ |

#### Bloque E — Datos de inteligencia

| # | Tarea datos/semántica | Detalle técnico | Existe |
|---|----------------------|-----------------|--------|
| E-D1 | Agregación brechas por jurisdicción | Skills más demandadas vs disponibles en cartera de la OE. Gap estructural | ❌ (datos base existen) |
| E-D2 | Detección cursos faltantes | Brechas frecuentes sin oferta formativa en el territorio | ❌ |
| E-D3 | Base resoluciones oficiales → skills (Vía 4) | Scraping resoluciones ministeriales de carreras argentinas + mapeo a skills ESCO | ❌ |

### Bloque B: S2 — Oficina de Empleo (primer cliente)

**Dependencia:** Bloque A (componentes compartidos)
**Estrategia:** La OE ya tiene personas, vacantes y cursos. El MOL aporta el motor. No hay chicken-and-egg.

| # | Tarea | Pantalla | Existe |
|---|-------|----------|--------|
| B1 | Importar pools OE via Excel/CSV (personas, vacantes, cursos) | S2-1 | ❌ |
| B2 | Tablas multi-tenancy: organizaciones + user_organizaciones | — | ❌ |
| B3 | RLS multi-tenancy (S-19, S-22): aislamiento entre OEs | — | ❌ |
| B4 | Login institucional + panel de casos | S2-2, S2-3 | ❌ |
| B5 | Perfil del caso (conectar wireframe con MySkillsSearch) | S2-4 | ⚠️ Wireframe |
| B6 | Nota del técnico (campos no derivables por ESCO) | S2-5 | ❌ |
| B7 | Matching bidireccional: vacante → ranking cartera OE | S2-6, S2-7 | ❌ |
| B8 | Formación: catálogo OE mapeado a ESCO + impacto medible | S2-8 | ❌ |
| B9 | Comparar casos para priorizar derivaciones | S2-9 | ❌ |
| B10 | Exportar diagnóstico PDF institucional (emisor = OE) | S2-11 | ❌ |
| B11 | Validación input Excel/CSV (S-25) | — | ✅ `88a52d6e` |
| B12 | Onboarding OE: pantalla bienvenida + importación guiada | S2-1 | ❌ |
| B13 | Templates Excel descargables (personas, vacantes, cursos) | S2-1 | ❌ |
| B14 | Preview importación + confirmación | S2-1 | ❌ |
| B15 | P-37 Admin: gestión organizaciones (crear OE, asignar usuarios) | /admin/organizaciones | ❌ |
| B16 | PDF capacitación técnico (2 páginas) + video 5 min | — | ❌ |

### Bloque C: S1 — Mi Futuro Laboral (trabajador independiente)

**Dependencia:** Bloque A + datos reales de al menos una OE (Bloque B parcial)

| # | Tarea | Pantalla | Existe |
|---|-------|----------|--------|
| C1 | Flujo autónomo en /mi-futuro-laboral (no redirigir a /skills) | S1-1 a S1-9 | ⚠️ Landing existe |
| C2 | Onboarding: nombre + tipo de uso, sin cuenta todavía | S1-2 | ❌ |
| C3 | 4 vías de captura embebidas en el flujo | S1-3 | ⚠️ Vía 1 existe |
| C4 | Skills derivadas con barra de completitud | S1-4 | ⚠️ Parcial |
| C5 | Enriquecer perfil: + trabajos + skills informales + títulos | S1-5 | ❌ |
| C6 | Resultados: ocupaciones + ofertas + capacitación (3 tabs) | S1-6 | ⚠️ Ocupaciones existe |
| C7 | Elegir destino: campo libre + sugerencias del sistema | S1-7 | ❌ |
| C8 | Brecha específica: "N skills te separan" con cursos | S1-8 | ❌ |
| C9 | PDF + QR (generado por el propio trabajador) | S1-9 | ❌ |
| C10 | Opt-in para visibilidad en pool (S-20): toggle provincial/nacional, anonimización, revocable | — | ❌ |
| C12 | Vinculación S1↔S2 por DNI: buscar perfil existente, vincular a OE con aceptación | — | ❌ |
| C13 | UI opt-in en S1 (toggle + alcance + explicación anonimización) | — | ❌ |
| C11 | Rate limiting APIs públicas S1 (S-23) | — | ❌ |

### Bloque D: S3 — Empresas

**Dependencia:** Bloque A (nivel libre) / Bloques B+C (nivel registrado)

| # | Tarea | Pantalla | Nivel | Existe |
|---|-------|----------|-------|--------|
| D1 | Acceso vía QR (= A7) | S3-1 | Libre MVP | ❌ |
| D2 | Reporte de compatibilidad interactivo | S3-2 | Libre MVP | ❌ |
| D3 | Personalizar competencias + recalcular | S3-3 | Libre MVP | ❌ |
| D4 | Landing empresas | S3-4 | Registrado v2 | ❌ Futuro |
| D5 | Dashboard empresa | S3-5 | Registrado v2 | ❌ Futuro |
| D6 | Perfil de puesto reutilizable | S3-6 | Registrado v2 | ❌ Futuro |
| D7 | Historial + comparar candidatos | S3-7, S3-8 | Registrado v2 | ❌ Futuro |
| D8 | Benchmark + buscar en pool | S3-9, S3-10 | Registrado v2 | ❌ Futuro |
| D9 | Reskilling de plantilla | S3-11 | Registrado v2 | ❌ Futuro |
| D10 | Inteligencia sectorial | S3-12 | Registrado v2 | ❌ Futuro |

### Bloque E: Inteligencia avanzada + certificación

**Dependencia:** Bloques B, C, D operativos

| # | Tarea | Servicio | Existe |
|---|-------|----------|--------|
| E1 | Inteligencia local: brechas jurisdicción, reportes institucionales | S2-10 | ❌ |
| E2 | Validación institucional: skills verificadas por técnico OE en reporte | S2-5 → S3-2 | ❌ |
| E3 | Vía 4: captura por formación/título (base resoluciones oficiales) | S1, S2 | ❌ |
| E4 | Sello certificación MOL para instituciones de formación adheridas | — | ❌ Futuro |
| E5 | QR evoluciona a credencial verificable | — | ❌ Futuro |
| E6 | API pública para portales de empleo de gobiernos | — | ❌ Futuro |

### Bloque I: Panel Evolución del Procesamiento (3 fases)

**Dependencia:** Datos de pipeline ya existen (pipeline_runs, validation_errors, learning_history, ofertas_esco_matching)
**Asignado a:** Gerardo (RPCs, APIs, lógica preview) + Sergio (UI dashboards + editor)

> Hoy para saber si el NLP mejoró hay que correr scripts. Para editar una regla hay que abrir un JSON. Para saber si conviene fine-tunear hay que preguntar. Este bloque lo lleva todo a la UI.

#### Fase I1 — Dashboards de métricas (solo lectura)

Datos ya existen en BD. Solo RPCs + UI para mostrarlos.

| # | Componente | Tipo | Quién |
|---|-----------|------|-------|
| I1a | RPC `get_nlp_metrics()`: tasa aprobados/bloqueados NLP Gate, campos problemáticos, por versión | RPC Supabase | Gerardo |
| I1b | RPC `get_matching_metrics()`: distribución método (regla/diccionario/semántico), dual match %, score promedio | RPC Supabase | Gerardo |
| I1c | RPC `get_validation_metrics()`: errores por tipo, resueltos vs pendientes, evolución temporal | RPC Supabase | Gerardo |
| I1d | RPC `get_learning_timeline()`: reglas creadas, tasa error por lote, convergencia | RPC Supabase | Gerardo |
| I1e | RPC `get_gold_set_results()`: resultados actuales vs históricos sobre gold set | RPC Supabase | Gerardo |
| I1f | API /api/processing-metrics (agrega todas las RPCs) | API route | Gerardo |
| I1g | Dashboard NLP: gráficos aprobados/bloqueados, campos problemáticos, comparación versiones | UI | Sergio |
| I1h | Dashboard Matching: pie distribución método, evolución dual match, reglas más/menos usadas | UI | Sergio |
| I1i | Dashboard Validación: errores por tipo (bar chart), resueltos/pendientes (donut), timeline | UI | Sergio |
| I1j | Dashboard Aprendizaje: timeline reglas creadas, tasa error temporal, convergencia por lote | UI | Sergio |
| I1k | Gold Set: tabla resultados actuales, comparación histórica, regresiones detectadas | UI | Sergio |

**Tests:**
- `unit/processing-metrics.test.ts` — cálculos de métricas, agregaciones
- `component/nlp-dashboard.test.tsx` — render gráficos, datos correctos
- `component/matching-dashboard.test.tsx` — render distribución, dual match
- `component/validation-dashboard.test.tsx` — render errores, timeline

#### Fase I2 — Edición de diccionarios y reglas

**Decisión: Opción C (híbrida).** Los JSONs del repo siguen como fallback. Los cambios desde la UI se guardan en `config_overrides` en Supabase. El pipeline lee primero el override, si no existe usa el JSON local.

| # | Componente | Tipo | Quién |
|---|-----------|------|-------|
| I2a | Tabla `config_overrides`: config_key, json_value, version, updated_by | Migration SQL | Gerardo |
| I2b | API /api/config-editor: GET (leer JSON + override), PUT (guardar override) | API route | Gerardo |
| I2c | Función `load_config_with_override()`: lee override de Supabase, fallback a JSON local | Python (pipeline) | Gerardo |
| I2d | Preview de impacto: antes de guardar, calcular "afecta a N ofertas, cambia X→Y" | API route | Gerardo |
| I2e | Editor reglas de negocio (matching_rules_business.json): tabla + agregar/editar/desactivar + preview | UI | Sergio |
| I2f | Editor sinónimos argentinos: tabla + agregar/editar + preview | UI | Sergio |
| I2g | Editor reglas NLP (nlp_inference_rules.json): tabla + agregar/editar | UI | Sergio |
| I2h | Editor skills rules: tabla + agregar/editar | UI | Sergio |
| I2i | Editor oficios argentinos: tabla + agregar | UI | Sergio |
| I2j | Changelog de cambios: quién editó qué, cuándo, diff | UI + datos | Ambos |

**Configs editables desde UI:**

| Config JSON | Reglas actuales | Qué se edita |
|-------------|----------------|-------------|
| matching_rules_business.json | 297 reglas | titulo_contiene → forzar_isco + esco_label |
| sinonimos_argentinos_esco.json | 17 ocupaciones | término argentino → ISCO |
| nlp_inference_rules.json | ~50 reglas | keyword → seniority/area/modalidad |
| skills_rules.json | 25 reglas | titulo_contiene → forzar skills |
| oficios_arg.json | ~170 oficios | oficio → ISCO |
| nlp_titulo_limpieza.json | ~30 patrones | regex limpiar títulos |

**Preview de impacto (lo más valioso):**
```
Antes de guardar regla nueva:
"titulo_contiene: 'community manager' → forzar_isco: 2431"

Preview:
  Ofertas afectadas: 45
  Matching actual: 23 matchean a 2431, 15 a 2642, 7 a otros
  Con esta regla: 45 matchean a 2431
  Cambios: 22 ofertas cambian de ISCO
  [Ver ofertas afectadas]  [Cancelar]  [Aplicar]
```

**Tests:**
- `unit/config-override.test.ts` — lee override, fallback JSON, merge correcto
- `unit/preview-impacto.test.ts` — calcula ofertas afectadas, diff correcto
- `component/rules-editor.test.tsx` — render tabla, agregar, editar, preview modal
- `security/config-editor-auth.test.ts` — solo admin puede editar

#### Fase I3 — Fine-tuning readiness

| # | Componente | Tipo | Quién |
|---|-----------|------|-------|
| I3a | RPC `get_training_pairs_stats()`: cantidad pares, distribución por ISCO, diversidad | RPC Supabase | Gerardo |
| I3b | Sugerencia automática: "N pares, X% IT, necesitás más diversidad en Y" | Lógica | Gerardo |
| I3c | Historial fine-tuning: qué modelo, cuántos datos, qué mejora | Tabla + UI | Ambos |
| I3d | Comparación pre/post fine-tuning sobre gold set | Lógica + UI | Ambos |
| I3e | Dashboard fine-tuning readiness: pares acumulados, diversidad, sugerencia, historial | UI | Sergio |

**Tests:**
- `unit/training-pairs-stats.test.ts` — diversidad calculada, sugerencia correcta
- `component/finetuning-dashboard.test.tsx` — render métricas, sugerencia

---

### Bloque H: Gestión de Scraping desde Admin (3 fases)

**Dependencia:** Datos de scraping ya existen en BD. VPS operativo con cron.
**Asignado a:** Gerardo (APIs, queries, VPS poller) + Sergio (UI dashboard)

> Hoy el scraping se gestiona por SSH al VPS. Este bloque lo lleva a la UI del admin.

#### Fase H1 — Monitoreo (sin tocar VPS)

Se calcula todo desde datos que ya existen en `ofertas` (SQLite) u `ofertas_dashboard` (Supabase).

| # | Componente | Tipo | Quién |
|---|-----------|------|-------|
| H1a | RPC `get_scraping_stats()`: ofertas por portal, última fecha, volumen diario | RPC Supabase | Gerardo |
| H1b | RPC `get_scraping_history(days)`: serie temporal ofertas/día por portal | RPC Supabase | Gerardo |
| H1c | Detección anomalías: portal sin datos >3 días o caída >50% vs corrida anterior | Lógica en RPC | Gerardo |
| H1d | Pantalla admin scraping: dashboard con KPIs + gráfico temporal + alertas | UI | Sergio |
| H1e | Cards por portal: estado (activo/alerta/sin datos), última corrida, ofertas, tasa éxito | UI | Sergio |

**Tests:**
- `unit/scraping-stats.test.ts` — cálculo anomalías, agregación por portal
- `component/scraping-dashboard.test.tsx` — render cards, gráfico, alertas

#### Fase H2 — Control remoto del VPS (cola de comandos en Supabase)

El admin crea un comando en Supabase. Un poller en el VPS lo lee cada 1 minuto y ejecuta.

| # | Componente | Tipo | Quién |
|---|-----------|------|-------|
| H2a | Tabla `scraping_commands`: comando, estado, resultado, timestamps | Migration SQL | Gerardo |
| H2b | Script poller en VPS: consulta Supabase cada 1 min, ejecuta comandos pendientes | Python (VPS) | Gerardo |
| H2c | API /api/scraping-commands: POST (crear comando), GET (listar estado) | API route | Gerardo |
| H2d | Botones en UI: "Lanzar Bumeran", "Lanzar todos", "Pausar portal", "Sync VPS→local" | UI | Sergio |
| H2e | Log en tiempo real: el poller actualiza progreso en Supabase, la UI lo lee con polling/realtime | UI + datos | Ambos |
| H2f | Comandos soportados: lanzar_portal, lanzar_todos, pausar, reanudar, sync_vps_local, sync_local_supabase | Lógica VPS | Gerardo |

**Flujo:**
```
Admin click "Lanzar Bumeran"
    ↓
POST /api/scraping-commands → INSERT {comando: "lanzar_portal", params: {portal: "bumeran"}, estado: "pendiente"}
    ↓
VPS poller (cada 1 min) → SELECT * FROM scraping_commands WHERE estado = 'pendiente'
    ↓
Ejecuta: python run_scheduler.py --portal bumeran
    ↓
UPDATE scraping_commands SET estado = 'ejecutando', log = '...'
    ↓
Al terminar: UPDATE SET estado = 'completado', resultado = {ofertas: 391, errores: 0}
    ↓
Admin ve en la UI: "Bumeran: completado — 391 ofertas — 0 errores"
```

**Seguridad:**
- Solo admin puede crear comandos (requireAdmin en API)
- El poller en el VPS usa service_role_key (no anon)
- Comandos peligrosos (cancelar, reconfigurar) requieren confirmación doble

**Tests:**
- `unit/scraping-commands.test.ts` — crear comando, estados válidos, solo admin
- `security/scraping-commands-auth.test.ts` — no admin → 403

#### Fase H3 — Configuración (futuro)

| # | Componente | Tipo | Quién |
|---|-----------|------|-------|
| H3a | Editar master_keywords.json desde UI | UI + API | Ambos |
| H3b | Editar frecuencia cron desde UI | UI + API + VPS | Ambos |
| H3c | Agregar/quitar portales | UI + API | Ambos |
| H3d | Configurar delays y headers por portal | UI + API | Ambos |

**Nota:** Fase H3 puede esperar. Se cambia poco y el riesgo de error es alto (un keyword mal puede romper un scraper).

---

### Bloque G: Catálogo MOL — Taxonomía propia (skills + ocupaciones)

**Dependencia:** Bloque 9° (curación perfil) + datos suficientes (>30K ofertas procesadas)
**Asignado a:** Gerardo (datos, estructura, curación) + Sergio (UI edición)

> El mercado laboral argentino genera skills y ocupaciones que ESCO no tiene. Hoy las capturamos como "emergentes" pero son un label suelto sin estructura. El Catálogo MOL les da la misma jerarquía que ESCO: definición, categoría, relaciones.

**Diferencia con lo actual:**

| Hoy (emergentes) | Catálogo MOL |
|-------------------|-------------|
| Label suelto ("Docker") | Ficha completa: nombre, definición, categoría, tipo |
| Sin relaciones | Relacionada con otras skills (Docker → contenedores → DevOps) |
| Solo aprobada/rechazada | Ciclo de vida: detectada → revisada → catalogada → versionada |
| Solo skills | Skills MOL + Ocupaciones MOL |

**Estructura de una Skill MOL:**

```
{
  id: "mol-skill-docker-config",
  label: "Configurar Docker",
  label_normalized: "configurar docker",
  definicion: "Crear, gestionar y orquestar contenedores Docker para
    despliegue de aplicaciones. Incluye Dockerfiles, docker-compose,
    redes y volúmenes.",
  tipo: "skill",                    // skill | knowledge | transversal
  categoria_L1: "S1",              // Alineada a ESCO si existe equivalente
  categoria_L2: "S1.8",
  source: "mol_catalogo",          // mol_catalogo | esco
  esco_parent_uri: "http://...",   // Skill ESCO más cercana (si existe)
  relaciones: [
    { skill: "Kubernetes", tipo: "related" },
    { skill: "CI/CD", tipo: "related" },
    { skill: "Linux", tipo: "prerequisite" },
  ],
  frecuencia_mercado: 45.2,        // % de ofertas que la mencionan
  primera_deteccion: "2026-01-15",
  aprobada_por: "admin@oede.gob.ar",
  version_catalogo: "v2.0",
}
```

**Estructura de una Ocupación MOL:**

```
{
  id: "mol-occ-community-manager",
  label: "Community Manager",
  definicion: "Gestiona la presencia digital de una organización en
    redes sociales. Crea contenido, interactúa con la audiencia,
    analiza métricas de engagement.",
  isco_parent: "2431",             // Ocupación ISCO más cercana
  esco_parent_uri: "http://...",   // Ocupación ESCO más cercana
  source: "mol_catalogo",
  skills_esenciales: ["marketing digital", "redes sociales", "copywriting"],
  skills_opcionales: ["diseño gráfico", "analítica web"],
  frecuencia_mercado: 3.1,         // % de ofertas que piden este título
  primera_deteccion: "2025-11-20",
  version_catalogo: "v1.0",
}
```

**Ciclo de vida:**

```
DETECCIÓN AUTOMÁTICA
  Pipeline procesa ofertas → NLP extrae skills/títulos
  → algunos no matchean con ESCO
  → se acumulan como "no clasificados"
    ↓
REVISIÓN (analista en UI)
  Panel muestra: "85 skills no clasificadas, 12 títulos sin ocupación ESCO"
  Analista revisa cada una:
  - ¿Es genuinamente nueva? → Crear ficha MOL (definición, categoría, relaciones)
  - ¿Es variante de algo que existe? → Mapear a skill/ocupación existente (sinónimo)
  - ¿Es ruido? → Descartar
    ↓
CATALOGACIÓN
  Skill/ocupación nueva → entra al Catálogo MOL con ficha completa
  Se agrega al catálogo de búsqueda (skills_searchable.json)
  Se agrega al matching (perfil consolidado)
    ↓
VERSIONADO
  Cada corte del perfil argentino incluye las skills/ocupaciones MOL vigentes
  Changelog: qué se agregó, qué se modificó, qué se descartó
    ↓
ACTUALIZACIÓN PERIÓDICA (cada 2 semanas, como Lightcast)
  Re-procesar ofertas recientes → detectar nuevas emergentes
  Analista revisa → cataloga → corte de versión
```

**Componentes a crear:**

| # | Componente | Tipo | Quién |
|---|-----------|------|-------|
| G1 | Tabla `catalogo_mol_skills` (ficha completa con definición, relaciones) | Migration SQL | Gerardo |
| G2 | Tabla `catalogo_mol_ocupaciones` (ficha completa con skills esenciales) | Migration SQL | Gerardo |
| G3 | Detección automática de "no clasificados" post-pipeline | RPC Supabase | Gerardo |
| G4 | API /api/catalogo-mol (CRUD skills + ocupaciones MOL) | API route | Gerardo |
| G5 | Panel admin: "No clasificados" (skills y títulos sin match ESCO) | UI | Sergio |
| G6 | Editor de ficha MOL: definición, categoría, relaciones, preview | UI | Sergio |
| G7 | Changelog público del catálogo (qué cambió en cada versión) | UI + datos | Ambos |
| G8 | Integrar skills/ocupaciones MOL en matching y búsqueda | Lógica | Gerardo |
| G9 | Proceso periódico de actualización (cada 2 semanas) | Workflow | Gerardo |

**Tests:**

| Test | Tipo | Qué valida |
|------|------|------------|
| `unit/catalogo-mol-skills.test.ts` | Unit | Ficha tiene campos requeridos. Relaciones válidas. Frecuencia calculada. |
| `unit/catalogo-mol-ocupaciones.test.ts` | Unit | Ocupación MOL tiene ISCO parent. Skills esenciales no vacías. |
| `unit/deteccion-no-clasificados.test.ts` | Unit | Skills sin match ESCO se detectan. Títulos sin ocupación se detectan. Duplicados filtrados. |
| `component/catalogo-editor.test.tsx` | Component | Form crear skill MOL. Preview definición. Selector relaciones. |

---

### Bloque F: Responsive — Mobile y Tablet (Sergio)

**Dependencia:** Bloques C y D (las pantallas tienen que existir primero)
**Asignado a:** Sergio (puro frontend — CSS/Tailwind)

> El sistema actual está diseñado desktop-first. Para S1 (Mi Futuro Laboral) y S3 libre (reporte QR) el acceso mobile es crítico: el trabajador entra desde el celular y el reclutador escanea el QR en la entrevista con el teléfono.

| # | Tarea | Pantallas afectadas | Prioridad |
|---|-------|-------------------|-----------|
| F1 | Responsive S1: flujo Mi Futuro Laboral completo en mobile | S1-1 a S1-9 | ALTA — el trabajador entra desde el celular |
| F2 | Responsive S3 libre: reporte QR legible en mobile | S3-1 a S3-3 (reporte + personalizar) | ALTA — el reclutador escanea con el teléfono |
| F3 | Responsive S2: panel OE usable en tablet | S2-1 a S2-11 | MEDIA — el técnico puede usar tablet en la atención |
| F4 | Responsive dashboard existente | P-09, P-10, P-17 a P-25 | BAJA — analistas usan desktop |
| F5 | Touch-friendly: botones, inputs, dropdowns con tamaño mínimo 44px | Todos | ALTA — estándar WCAG |
| F6 | Test visual en 3 breakpoints (mobile 375px, tablet 768px, desktop 1280px) | Todos | — |

**Criterios:**
- Mobile-first para S1 y S3 (la mayoría de los usuarios van a entrar desde el celular)
- Tablet-friendly para S2 (técnico de OE puede usar tablet en la atención presencial)
- Desktop se mantiene como está para el dashboard de análisis
- Todos los botones e inputs: mínimo 44x44px (touch target WCAG)
- Sin scroll horizontal en ningún breakpoint
- Tablas: se convierten en cards en mobile

**Tests:**
| Test | Tipo | Qué valida |
|------|------|------------|
| `component/responsive-s1-mobile.test.tsx` | Component | S1 renderiza correctamente en viewport 375px |
| `component/responsive-s3-qr-mobile.test.tsx` | Component | Reporte QR legible en mobile, botones touch-friendly |
| `e2e/responsive-flow.spec.ts` | E2E (Playwright) | Flujo completo S1 en mobile: onboarding → perfil → resultados → reporte |

---

## MAPA DE DEPENDENCIAS

```
BLOQUE A (componentes compartidos) ✅
    │
    ├──────────────────────┐
    │                      │
    ▼                      ▼
BLOQUE B (S2 - OE) ✅     BLOQUE D (S3 libre)
    │                  D1, D2, D3 = A6+A7
    │
    ▼
BLOQUE C (S1 - Trabajador)
    │
    ├──────────────────────┬──────────────────┐
    │                      │                  │
    ▼                      ▼                  ▼
BLOQUE D (S3 registrado)  BLOQUE E (avanzado) BLOQUE F (responsive)
D4 a D10                   E1 a E6            F1 a F6 (Sergio)
```

### Orden sugerido de ejecución

| Orden | Qué | Tareas clave | Requisito |
|-------|-----|-------------|-----------|
| **1°** | **Perfil Consolidado como fuente** | PCA-5 (integrar en matching), PCA-1 (corte versión global), A-D3 (catálogo unificado) | Nada — perfil y panel ya existen. Es reconectar el matching para que use el perfil argentino en vez de ESCO puro |
| **2°** | **Motor semántico compartido** | A-D1 (búsqueda semántica skills), A-D2 (texto libre → skills), A3 (definiciones visibles) | PCA-5 (el catálogo contra el que se busca debe ser el argentino) |
| **3°** | **Report engine** | A6 (API reporte), A7 (página /reporte), A8 (tabla BD), A-D4 (matching perfil × ofertas) | Motor semántico funcionando |
| **4°** | **Tabs de resultados** | A4 (ofertas), A5 (capacitación), A-D5 (matching cursos), A-D6 (tendencia temporal) | Report engine + ofertas en Supabase + cursos CABA |
| **5°** | **S2 MVP: Oficina de Empleo** | B1-B5, B-D1 (parser Excel), B-D2 (NLP vacantes), B2-B3 (multi-tenancy + RLS) | Bloques 1°-4° completos |
| **6°** | **S3 libre: QR para empresas** | D1-D3 | Report engine (3°) |
| **7°** | **S1: Trabajador independiente** | C1-C11, A-D7 (distancia ocupaciones) | Todo lo anterior + datos reales de OE |
| **8°** | **S2 completo** | B6-B11, B-D3 (mapeo cursos OE), B-D4 (impacto formación) | S2 MVP operativo |
| **9°** | **Proceso curación perfil** | PCA-2 (workflow), PCA-3 (recálculo auto), PCA-4 (regenerar catálogo), PCA-6 (métricas) | Pipeline procesando ofertas continuamente |
| **10°** | **Inteligencia + validación** | E1-E3, E-D1 (brechas jurisdicción), E-D2 (cursos faltantes) | S2 + S1 operativos |
| **11°** | **S3 registrado** | D4-D10 | Pool con datos (S1 + S2 activos) |
| **12°** | **Vía 4 + certificación** | E-D3 (resoluciones oficiales), E4-E6 (sello MOL, credencial, API) | Todo lo anterior maduro |

### Paralelo con Dashboard

| En paralelo con Skills Int. | Dashboard |
|---------------------------|-----------|
| Bloques A + B | Fase 2 pendientes (salarios, tendencias UI) |
| Bloques C + D libre | Fase 3 pendientes (CMS, checkout) |
| Bloques D reg + E | Fase 4 (ML predictivo, personalización) |

---

## PLAN DE TESTING

> **Infraestructura existente:** Vitest + @testing-library/react + Playwright (e2e) + MSW (mocks API). 4 categorías: `__tests__/{unit, component, integration, security}`. 153 tests passing.

Cada bloque incluye su plan de testing. No se mergea sin tests verdes.

### Testing Bloque A: Componentes compartidos

| Tarea | Tipo test | Archivo | Qué valida |
|-------|-----------|---------|------------|
| A1 Vía 2 (búsqueda por tarea) | Unit | `unit/skill-search-by-task.test.ts` | Búsqueda por nombre + definición retorna skills correctas. Fuzzy matching. Sin resultados para basura. |
| A1 Vía 2 (búsqueda por tarea) | Component | `component/skill-search-input.test.tsx` | Render del input, debounce, resultados desplegables, definición visible, click agrega al perfil. |
| A2 Vía 3 (texto libre → skills) | Unit | `unit/text-to-skills.test.ts` | Textos en español rioplatense → skills ESCO. "Soldar" → soldadura. "Depósito" → logística. Texto vacío → []. |
| A3 Definiciones visibles | Component | `component/skill-with-definition.test.tsx` | Muestra label + definición. Checkbox ✓/?/✗ cambia estado. Tooltip en hover. |
| A4 Tab Ofertas | Unit | `unit/match-offers-to-profile.test.ts` | JOIN perfil × ofertas retorna ranking correcto. Gap personalizado calculado bien. Filtros (provincia, modalidad) funcionan. |
| A4 Tab Ofertas | Component | `component/offers-tab.test.tsx` | Render de cards con %, skills cubiertas/faltantes, botones funcionales. Loading state. Empty state. |
| A5 Tab Capacitación | Unit | `unit/match-gaps-to-courses.test.ts` | Brecha "Docker" → cursos con "docker" en nombre/desc/plan. Transición por demanda: calcula tendencia correctamente. |
| A5 Tab Capacitación | Component | `component/training-tab.test.tsx` | Render por brecha. Modo A (preferencia) y Modo B (demanda) switcheables. Cards de cursos con link. |
| A6 Report engine | Unit | `unit/generate-report.test.ts` | Genera token UUID válido. Snapshot inmutable. perfil_consolidado_version registrado. Expiración calculada (60d). |
| A6 PDF + QR | Integration | `integration/pdf-generation.test.ts` | PDF contiene: logo, nombre, DNI, vacante, QR. QR apunta a URL correcta. |
| A7 Página /reporte | Component | `component/compatibility-report.test.tsx` | Render con datos. Token inválido → error. Token expirado → mensaje. Editar skills recalcula %. Restaurar original funciona. |
| A7 Página /reporte | Security | `security/report-token-access.test.ts` | Token UUID v4 (no secuencial). Token expirado → 410 Gone. Token inexistente → 404. No se expone DNI en respuesta API. |
| A8 API report | Unit | `unit/api-compatibility-report.test.ts` | POST crea registro. GET por token retorna datos. PATCH revoca. Campos requeridos validados. |

### Testing Perfil Consolidado Argentino (PCA)

| Tarea | Tipo test | Archivo | Qué valida |
|-------|-----------|---------|------------|
| PCA-1 Crear versión | Unit | `unit/perfil-argentino-versiones.test.ts` | Crear snapshot congela datos. Solo una versión activa a la vez. Constraint unique funciona. Version string es válido (semver). |
| PCA-1 Rollback | Unit | `unit/perfil-argentino-rollback.test.ts` | Rollback desactiva actual y activa anterior. Matching apunta a la nueva activa. No se pueden borrar versiones referenciadas por reportes. |
| PCA-1 UI admin | Component | `component/perfil-argentino-admin.test.tsx` | Render historial de versiones. Badge "activa" en la correcta. Botón crear versión muestra modal. Confirmar crea y recarga. Rollback pide confirmación. |
| PCA-3 Recálculo auto | Unit | `unit/perfil-recalculo-frecuencias.test.ts` | Después de N ofertas procesadas, frecuencias actualizadas. Emergentes nuevas (≥30%) detectadas. Notificación generada. |
| PCA-4 Regenerar catálogo | Integration | `integration/catalogo-regeneracion.test.ts` | Al crear versión → `skills_searchable.json` incluye emergentes aprobadas. Búsqueda Vía 2 encuentra emergentes. |
| PCA-5 Matching usa perfil activo | Integration | `integration/matching-usa-perfil-activo.test.ts` | Matching retorna skills del perfil argentino (no ESCO puro). Cambiar versión activa → matching retorna skills de la nueva. Reporte registra versión usada. |
| PCA-7 Regenerar reporte | Unit | `unit/regenerar-reporte-nueva-version.test.ts` | Reporte viejo mantiene su versión. Regenerar crea nuevo reporte con versión actual. Token original sigue funcionando. |

### Testing Bloque B: S2 — Oficina de Empleo

| Tarea | Tipo test | Archivo | Qué valida |
|-------|-----------|---------|------------|
| B1 Import Excel/CSV | Unit | `unit/parse-pool-import.test.ts` | Parsea CSV correcto. Rechaza columnas faltantes. Sanitiza fórmulas Excel (=, +, @). Límite de filas. Caracteres especiales. |
| B1 Import Excel/CSV | Security | `security/s25-import-validation.test.ts` | Inyección de fórmulas bloqueada. HTML strippeado. SQL en celdas sanitizado. Archivo > límite rechazado. |
| B2 Multi-tenancy | Unit | `unit/organization-helpers.test.ts` | get_user_org() retorna org correcta. Usuario sin org → error. Org inactiva → acceso denegado. |
| B3 RLS multi-tenancy | Security | `security/s19-s22-oe-isolation.test.ts` | OE-A no ve datos de OE-B. Técnico solo ve su cartera. Admin ve todo. Pool amplio: solo lectura en jurisdicción. |
| B4 Panel de casos | Component | `component/case-panel.test.tsx` | KPIs calculados. Tabla filtrable. Estados correctos (activo/derivado/insertado). |
| B5 Perfil del caso | Integration | `integration/case-profile-flow.test.ts` | Flujo completo: cargar perfil → 4 vías → skills derivadas → matching → resultado. |
| B7 Matching bidireccional | Unit | `unit/vacancy-to-candidates.test.ts` | Vacante → ranking de cartera por match %. Candidato sin skills → match 0%. Ordenamiento correcto. |
| B10 Export PDF inst. | Integration | `integration/institutional-export.test.ts` | PDF tiene logo OE (no solo MOL). Nombre técnico. Nota incluida. |

### Testing Bloque C: S1 — Mi Futuro Laboral

| Tarea | Tipo test | Archivo | Qué valida |
|-------|-----------|---------|------------|
| C1 Flujo autónomo | Integration | `integration/s1-full-flow.test.ts` | Landing → onboarding → captura → resultados → reporte. Sin redirección a /skills. |
| C2 Onboarding | Component | `component/onboarding.test.tsx` | Solo nombre requerido. Tipo de uso opcional. Sin cuenta hasta que quiera guardar. |
| C6 3 tabs resultados | Component | `component/results-tabs.test.tsx` | Tab ocupaciones, ofertas y capacitación renderizan. Switch entre tabs mantiene estado. Datos consistentes entre tabs. |
| C7 Elegir destino | Component | `component/choose-destination.test.tsx` | Campo libre acepta texto. Sugerencias del sistema aparecen. Ofertas activas por destino visibles. |
| C10 Opt-in | Security | `security/s20-opt-in-consent.test.ts` | Default es FALSE (no visible). Toggle persiste. Sin opt-in → perfil no aparece en búsquedas de OE/empresa. |
| C11 Rate limiting | Security | `security/s23-s1-rate-limit.test.ts` | > 20 req/min matching → 429. > 10 req/min generar reporte → 429. Auth aumenta límite. |

### Testing Bloque D: S3 — Empresas

| Tarea | Tipo test | Archivo | Qué valida |
|-------|-----------|---------|------------|
| D1 Acceso QR | Security | `security/s18-qr-token.test.ts` | Token no predecible (UUID v4). Expirado → mensaje claro. Revocado → mensaje. Vistas incrementan. IP registrada. |
| D2 Reporte interactivo | Component | `component/employer-report.test.tsx` | Muestra datos candidato (sin DNI). Skills con origen (ESCO/emergente). Badge validado por OE (cuando aplique). |
| D3 Personalizar skills | Component | `component/personalize-skills.test.tsx` | Quitar skill → % recalcula. Agregar skill → % recalcula. Restaurar → vuelve a original. No persiste en backend. |

### Testing Bloque E: Avanzado

| Tarea | Tipo test | Archivo | Qué valida |
|-------|-----------|---------|------------|
| E1 Inteligencia local | Unit | `unit/local-intelligence.test.ts` | Brechas frecuentes calculadas. Cursos que faltan detectados. Datos filtrados por jurisdicción. |
| E2 Validación institucional | Unit | `unit/institutional-validation.test.ts` | Skills verificadas por técnico marcadas en reporte. Distinción autodeclarado vs verificado visible. |
| E3 Vía 4 (formación) | Unit | `unit/qualification-to-skills.test.ts` | Título → skills ESCO mapeadas. Título no encontrado → fallback búsqueda. Base de resoluciones consultada. |

### Estrategia de testing por tipo

| Tipo | Herramienta | Cuándo corre | Umbral |
|------|-------------|-------------|--------|
| **Unit** | Vitest | Pre-commit + CI | 100% de utils/helpers nuevos |
| **Component** | Vitest + Testing Library | Pre-commit + CI | Render + interacción principal de cada componente nuevo |
| **Integration** | Vitest + MSW | CI en PR | Flujos completos (captura → matching → reporte) |
| **Security** | Vitest | CI en PR + deploy | Cada issue S-18 a S-25 tiene su test |
| **E2E** | Playwright | Pre-deploy | Flujo crítico: crear perfil → generar reporte → acceder por QR |

### Regla de testing

```
NINGÚN bloque se considera completo sin:
1. Tests unitarios de la lógica nueva (helpers, cálculos, validaciones)
2. Tests de componente de la UI nueva (render, interacción, estados)
3. Tests de seguridad para los issues S-* que apliquen
4. Test de integración del flujo completo del bloque
5. Todos los tests existentes siguen pasando (no regresión)
```

> **Nota:** No se incluyen estimaciones de tiempo porque la velocidad depende de recursos disponibles. El orden de ejecución está definido por dependencias técnicas, no por plazos.

---

## HITOS Y RELEASES

### Release 0.9 — Estado actual (2026-03-20)

```
✅ Seguridad básica (4/5 críticos — falta rotar key)
✅ Escalabilidad (RPCs + React Query + índices)
✅ 99% ofertas con NLP (era 49%)
✅ 42% ofertas validadas (era 1%)
✅ 15,968 ofertas en Supabase sincronizadas
✅ 6 portales scraping activos en VPS
✅ Acceso gated (solicitud → aprobación → trial)
✅ ESCO Argentino (tabla + API + panel aprobación)
✅ Motor de matching MySkillsSearch funcional
✅ 153 tests passing
```

### Release 1.0 — Skills Intelligence MVP

**Meta:** Ciclo completo trabajador → reporte → reclutador

```
Bloques 1° a 4° del orden de ejecución:
□ Perfil Consolidado como fuente del matching (PCA-1, PCA-5)
□ Motor semántico: búsqueda por tarea + texto libre + definiciones
□ Report engine: API + PDF + QR + página /reporte/{token}
□ Tabs resultados: ofertas reales + capacitación + transición dual
□ S3 nivel libre: reclutador escanea QR
```

### Release 1.5 — OE como primer cliente

**Meta:** Una oficina de empleo operativa con pools cargados

```
Bloques 5° y 6° del orden de ejecución:
□ S2 MVP: importar pools, panel casos, perfil caso, matching
□ Multi-tenancy + RLS entre oficinas
□ PDF institucional con firma del técnico
```

### Release 2.0 — Trabajador independiente

**Meta:** /mi-futuro-laboral como flujo autónomo con datos reales

```
Bloque 7° del orden de ejecución:
□ S1 completo: 9 pantallas, flujo sin intermediario
□ Opt-in para visibilidad en pool
□ S2 completo (nota técnico, formación, comparar)
```

### Release 3.0 — Inteligencia + Empresas

**Meta:** Valor avanzado para OEs y empresas registradas

```
Bloques 9° a 12° del orden de ejecución:
□ Proceso curación perfil argentino (workflow + recálculo auto)
□ Inteligencia local + validación institucional
□ S3 registrado: cuenta empresa, búsquedas, benchmark
□ Vía 4 (formación/título) + certificación MOL
```

---

## MÉTRICAS DE SEGUIMIENTO

### Datos (pipeline)

| Métrica | Actual | Meta R1.0 | Meta R2.0 |
|---------|--------|-----------|-----------|
| Ofertas en BD | 37,785 | 50,000+ | 75,000+ |
| Con NLP | 99% | 99% | 99% |
| Validadas | 42% | 60% | 80% |
| Portales activos | 6 | 6+ | 8+ |
| Perfil Argentino versiones | 0 (sin corte formal) | v1.0 | v2.0+ |

### Skills Intelligence

| Métrica | R1.0 | R1.5 | R2.0 | R3.0 |
|---------|------|------|------|------|
| Reportes generados | - | 50 (OE) | 200 (S1+S2) | 1,000+ |
| OEs operativas | 0 | 1 | 3 | 10 |
| Trabajadores con perfil | 0 | 50 (vía OE) | 500 | 2,000 |
| Empresas (QR escaneados) | 0 | 20 | 100 | 500 |
| Tests passing | 153 | 200+ | 250+ | 300+ |

### Dashboard (negocio)

| Métrica | Actual | R1.0 | R2.0 |
|---------|--------|------|------|
| Usuarios registrados | ~30 | 200 | 1,000 |
| Suscriptores tablero | 0 | 10 | 50 |
| Institucionales | 0 | 1 (OE) | 3 |

---

## PRÓXIMO PASO INMEDIATO

**Bloque 1° — Perfil Consolidado como fuente del sistema:**

1. `PCA-5`: Modificar MySkillsSearch para que compare contra `esco_argentino` (versión activa) en vez de `occupation_full_detail.json` (ESCO puro)
2. `PCA-1`: Crear tabla `perfil_argentino_versiones` + pantalla P-36 para corte de versión
3. `A-D3`: Regenerar `skills_searchable.json` incluyendo emergentes aprobadas
4. Tests: `matching-usa-perfil-activo.test.ts` + `perfil-argentino-versiones.test.ts`

**Pendiente URGENTE del dashboard:** Rotar service_role_key de Supabase (S-01, manual en dashboard)

---

## CICLO DE DESARROLLO → DEPLOY POR PASO

Cada paso del roadmap pasa por el mismo ciclo. No es solo código: es base de datos + backend + frontend + deploy.

### Flujo de trabajo por paso

```
1. SUPABASE (base de datos)
   ├── Crear migration SQL (tablas, columnas, índices)
   ├── Crear/actualizar políticas RLS
   ├── Crear/actualizar funciones RPC (si aplica)
   ├── Ejecutar en Supabase Dashboard → SQL Editor
   └── Verificar RLS con distintos roles

2. DESARROLLO LOCAL (Next.js)
   ├── Crear/modificar API routes (app/api/*)
   ├── Crear/modificar componentes React
   ├── Crear/modificar lib/ helpers
   ├── Conectar con Supabase client
   ├── Probar en localhost:3000
   └── Escribir tests (unit + component + integration + security)

3. TESTING
   ├── npm run test (vitest — unit + component)
   ├── npm run test:e2e (playwright — flujos críticos)
   ├── Verificar 0 regresiones en tests existentes
   └── Tests de seguridad para issues S-* que apliquen

4. DEPLOY
   ├── git add + commit + push a GitHub
   ├── cd fase3_dashboard/mol-dashboard
   ├── npx vercel --prod --yes
   ├── npx vercel alias [url] mol-nextjs.vercel.app
   └── Verificar variables de entorno en Vercel (si hay nuevas)

5. VERIFICACIÓN POST-DEPLOY
   ├── Smoke test en producción (mol-nextjs.vercel.app)
   ├── Verificar que Supabase responde (RLS, RPCs)
   └── Verificar que no se rompió nada existente
```

### Infraestructura por paso del roadmap

| Paso | Supabase (migrations) | Vercel (deploy) | Env vars nuevas |
|------|----------------------|-----------------|-----------------|
| **1° Perfil como fuente** | `perfil_argentino_versiones` + constraint unique activa | Deploy P-36 + modificación matching | No |
| **2° Motor semántico** | No (es lógica frontend/API) | Deploy nuevos endpoints búsqueda | No |
| **3° Report engine** | `reportes_compatibilidad` + RLS por token + `reporte_accesos` | Deploy API + página /reporte/[token] | No |
| **4° Tabs resultados** | No (lee ofertas_dashboard existente + cursos estáticos) | Deploy componentes tabs | No |
| **5° S2 MVP (OE)** | `organizaciones` + `user_organizaciones` + RLS multi-tenancy + `vacantes_oe` + `cursos_oe` | Deploy S2 completo (11 pantallas) | Posible: SMTP para notificaciones |
| **6° S3 libre (QR)** | No (usa reportes_compatibilidad del paso 3°) | Deploy flujo QR → reporte | No |
| **7° S1 (trabajador)** | Posible: campo `opt_in_pool` en perfiles_trabajadores | Deploy /mi-futuro-laboral (9 pantallas) | No |
| **8° S2 completo** | Posible: campos nota_tecnico en perfiles | Deploy pantallas S2-6 a S2-11 | No |
| **9° Curación perfil** | Posible: trigger/función para recálculo | Deploy métricas admin | No |
| **10° Inteligencia** | Posible: vistas materializadas para agregaciones | Deploy S2-10 | No |
| **11° S3 registrado** | `vacantes_empresa` + RLS por empresa_id | Deploy S3-4 a S3-12 (9 pantallas) | Posible: API keys para empresas |
| **12° Certificación** | Posible: tabla certificaciones + sellos | Deploy funcionalidades certificación | Posible: integración proveedores |

### Consideraciones de deploy

| Aspecto | Detalle |
|---------|---------|
| **Supabase free tier** | Límite ~500MB BD + 1GB storage + ~15 req/s. Monitorear con cada paso. Si se excede: upgrade o rate limiting |
| **Vercel free tier** | Deploy NO vinculado a GitHub (limitación plan gratuito). Cada deploy es manual via CLI. Alias necesario para mantener URL estable |
| **Variables de entorno** | Hoy: SUPABASE_URL + SUPABASE_ANON_KEY en Vercel. Si se agregan nuevas (SMTP, API keys), configurar en Vercel Dashboard → Settings → Environment Variables |
| **Migrations rollback** | Supabase no tiene rollback automático. Cada migration debe tener su `DOWN` script documentado (o al menos el DROP correspondiente) |
| **RLS testing en producción** | Después de cada migration con RLS: verificar con anon key (visitante), con user token (trabajador/técnico), y con service_role (admin). Un error en RLS es invisible hasta que un usuario ve datos que no debería |
| **Cold starts Vercel** | Rate limiter in-memory pierde estado en cold starts. Suficiente para uso actual. Si Skills Intelligence escala: migrar a Upstash Redis |

---

## NOTAS

- No hay estimaciones de tiempo — la velocidad depende de recursos disponibles
- El orden de ejecución está definido por dependencias técnicas
- Skills Intelligence y Dashboard avanzan en paralelo compartiendo el motor de datos
- Cada bloque tiene sus tests; no se avanza sin tests verdes + no regresión
- Cada paso incluye: migration Supabase → desarrollo local → tests → deploy Vercel → verificación
- Pricing pendiente — ver [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md#decisiones-pendientes)

---

## Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-02-05 | 1.0 | Roadmap SaaS (Free/Pro/Enterprise) |
| 2026-02-07 | 2.0 | Modelo híbrido en Fase 3: acceso gated, CMS, pago dual, workflow aprobación. Métricas actualizadas |
| 2026-02-11 | 2.1 | V-16 tensión de demanda en Fase 2 (parcial: datos existen, UI pendiente) |
| 2026-03-03 | 2.2 | Fase 3 parcial: acceso gated (solicitar-acceso, trial 7 días, middleware), oficina empleo wireframes, contenido placeholder, GlobalNav plan-aware |
| 2026-03-18 | 2.3 | V-17 Reporte Compatibilidad Laboral agregado a Fase 3 (PDF + QR + reporte web interactivo para reclutadores) |
| 2026-03-20 | 4.0 | Roadmap unificado: Dashboard (Fases 0-4) + Skills Intelligence (Bloques A-E). Estado datos actualizado (99% NLP, 42% validadas). Mapa de dependencias entre bloques. Orden de ejecución sugerido sin estimaciones de tiempo |
