# Fábrica de Procesamiento — Diseño Completo

> Versión definitiva: 2026-03-22
> Rediseño del Bloque I+G como fábrica integrada con dos líneas de proceso.

---

## 1. Modelo conceptual: Dos líneas de proceso

La fábrica tiene dos procesos que se alimentan mutuamente:

```
═══════════════════════════════════════════════════════════════════════════
 LÍNEA DE FABRICACIÓN (producir datos clasificados)
═══════════════════════════════════════════════════════════════════════════

 [SCRAPING]→[NLP]→[GATE NLP]→[MATCHING]→[GATE MATCHING]→[VALID.]→[SYNC]
  6 portales  v11.4  35 reglas   v3.5.4     22 reglas     humana  Supabase
  ▶⏸⚙        ▶🔄⚙   📋🔄⚙      ▶🔄⚙       📋🔄⚙        ▶📊     ▶🔄

                 ↓ errores          ↓ errores      ↓ correcciones
                 └──────────┬───────┘──────────────┘
                            ↓
═══════════════════════════════════════════════════════════════════════════
 LÍNEA DE MEJORA CONTINUA (mejorar la fábrica)
═══════════════════════════════════════════════════════════════════════════

 [ERRORES]→[ISSUES]→[TRAINING PAIRS]→[FINE-TUNE]→[CATÁLOGO MOL]→[PERFIL]
  cola       Claude    602+ pares       modelo      skills/ocup    v1.0
             +humano                    mejorado    argentinas     v1.1
  📋         📋📝       📊               📊⚡         📋✅🏷          🏷📊

                                          ↓               ↓
                                    mejor modelo    nueva taxonomía
                                          ↓               ↓
                                    ←←← vuelve a FABRICACIÓN ←←←
```

### Los 3 actores de la fábrica

| Actor | Rol | Qué hace | Dónde trabaja |
|-------|-----|----------|---------------|
| **Pipeline** (automático) | Obrero | Ejecuta NLP, Matching, Gates, detecta errores, escala | Fábrica → Línea fabricación |
| **Claude** (agente IA) | Operario calificado | Revisa errores, diagnostica raíz, crea reglas, reprocesa | Fábrica → Cola errores + Diccionarios |
| **Humano** (analista) | Gerente + Inspector QA | Controla fábrica, valida ofertas, corrige, crea issues, aprueba catálogo | Todas las pantallas |

### Cómo se conectan las dos líneas

```
FABRICACIÓN genera errores → alimentan MEJORA CONTINUA
MEJORA CONTINUA genera:
  - Reglas nuevas en configs → mejoran FABRICACIÓN
  - Modelo fine-tuneado → mejora MATCHING en FABRICACIÓN
  - Skills/ocupaciones MOL → enriquecen catálogo → publican PERFIL ARGENTINO
  - Training pairs → acumulan para próximo fine-tuning
```

---

## 2. Menú Sidebar definitivo

```
ADMIN
│
├── Centro de Control              (J — vista general del sistema)
│
├── Scraping                       (H — adquisición de datos)
│   ├── Dashboard
│   ├── Comandos
│   └── Dinámica
│
├── Procesamiento                  (I+G — la fábrica completa)
│   ├── Fábrica                    ← Vista dual: fabricación + mejora continua
│   ├── Diccionarios               ← 6 tabs: reglas, NLP, sinón, oficios, skills, limpieza
│   ├── Catálogo MOL               ← Curación de skills/ocupaciones nuevas (input mejora)
│   ├── Perfil Argentino           ← Publicación versionada (output mejora)
│   └── Validación                 ← Estación del analista (alimenta ambos procesos)
│
├── Laboratorio                    (indicadores experimentales)
│   └── ... (7 indicadores)
│
├── Skills Intelligence
├── Issues                         (gestión general — bugs + errores pipeline + sugerencias)
├── Usuarios
├── Métricas
├── Configuración
└── Arquitectura
```

**Lógica de los 5 items de Procesamiento:**

| Item | Qué es | Para quién | Línea |
|------|--------|-----------|-------|
| **Fábrica** | Panel de control con las dos líneas | Gerente de planta | Ambas |
| **Diccionarios** | Herramientas (configs del pipeline) | Claude + analista | Herramientas compartidas |
| **Catálogo MOL** | Curación de lo nuevo que se descubre | Analista | Mejora continua (input) |
| **Perfil Argentino** | Publicación versionada del perfil | Analista | Mejora continua (output) |
| **Validación** | Revisión de calidad oferta por oferta | Analista | Alimenta ambas líneas |

---

## 3. Wireframe: FÁBRICA (vista principal)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Fábrica de Procesamiento                                    [⟳ Actualizar]│
│  Pipeline v3.3 · NLP v11.4 · Matching v3.5.4                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ═══ LÍNEA DE FABRICACIÓN ═══════════════════════════════════════════════   │
│                                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐  │
│  │ SCRAPING │──▶│   NLP    │──▶│ MATCHING │──▶│VALIDACIÓN│──▶│  SYNC  │  │
│  │ 6 port.  │   │  v11.4   │   │  v3.5.4  │   │  humana  │   │Supabase│  │
│  │          │   │          │   │          │   │          │   │        │  │
│  │ ✅ 42K   │   │ ⚠ 4.6K   │   │ ✅ 16K   │   │ ✅ 15.9K │   │ ✅ ok  │  │
│  │ ofertas  │   │ pend.    │   │ matched  │   │ validadas│   │ 15.9K  │  │
│  │          │   │          │   │          │   │          │   │        │  │
│  │[▶ Lanzar]│   │[▶ NLP500]│   │[▶ Match] │   │[▶ Valid.]│   │[▶ Sync]│  │
│  │[⏸ Pausar]│   │[🔄 Re-NLP]│  │[🔄 Re-M] │   │[📊Export]│   │[🔄Full]│  │
│  │[📋Estado]│   │[⚙ Config]│   │[⚙ Config]│   │[📋Issues]│   │[📋 Log]│  │
│  └──────────┘   └────┬─────┘   └────┬─────┘   └──────────┘   └────────┘  │
│                      │              │                                       │
│                 ┌────┴────┐    ┌────┴────┐                                 │
│                 │GATE NLP │    │  GATE   │                                 │
│                 │35 reglas│    │MATCHING │                                 │
│                 │99% aprob│    │22 reglas│                                 │
│                 │ 1% bloq │    │ 23 err  │                                 │
│                 │         │    │         │                                 │
│                 │[📋 Bloq.]│   │[📋 Errs]│                                 │
│                 │[🔄Re-val]│   │[🔄Re-val]│                                │
│                 │[⚙Reglas]│    │[⚙Reglas]│                                 │
│                 └─────────┘    └─────────┘                                 │
│                                                                             │
│  ═══ LÍNEA DE MEJORA CONTINUA ═══════════════════════════════════════════  │
│                                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐  │
│  │ ERRORES  │──▶│  ISSUES  │──▶│ TRAINING │──▶│FINE-TUNE │──▶│CATÁLOGO│  │
│  │ pipeline │   │ cola     │   │  PAIRS   │   │readiness │   │  MOL   │  │
│  │          │   │          │   │          │   │          │   │        │  │
│  │ 🟡 23    │   │ 🟡 5     │   │ 📊 602   │   │ ⚡almost │   │ 0 new  │  │
│  │ escalados│   │ pendient.│   │ pares    │   │ ready    │   │ skills │  │
│  │          │   │          │   │          │   │          │   │        │  │
│  │[📋 Ver]  │   │[📋 Ver]  │   │[📊Stats] │   │[📊 Dash] │   │[📋 Ver]│  │
│  │[🔄Repro.]│   │[📝Resolver]│ │[🔄Regen.]│   │[▶Entrenar]│  │[+ Cat.]│  │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘  │
│                                                                     │      │
│                                                              ┌──────┴───┐  │
│                                                              │ PERFIL   │  │
│                                                              │ARGENTINO │  │
│                                                              │  v1.0    │  │
│                                                              │[🏷Corte] │  │
│                                                              │[📊 Ver]  │  │
│                                                              └──────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ÚLTIMA ACTIVIDAD                                                           │
│                                                                             │
│  hace 2h — Cynthia marcó error ISCO en #4523 → issue creado               │
│  hace 3h — Claude creó regla R301 "data engineer" → 2521                   │
│  hace 5h — Pipeline procesó 500 ofertas (488 ok, 12 errores)              │
│  ayer    — Diego validó lote de 50 (48 OK, 2 error)                        │
│                                                    [Ver historial →]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Interacciones por nodo:**

Cada nodo del pipeline es clickeable y tiene 2-3 botones:

| Nodo | Botón 1 (ejecutar) | Botón 2 (re-hacer) | Botón 3 (configurar) |
|------|-------------------|--------------------|--------------------|
| SCRAPING | ▶ Lanzar portales | ⏸ Pausar | 📋 Ver estado |
| NLP | ▶ Procesar 500 | 🔄 Re-NLP errores | ⚙ → Diccionarios tab NLP |
| GATE NLP | 📋 Ver bloqueados | 🔄 Re-validar | ⚙ → Diccionarios tab reglas NLP |
| MATCHING | ▶ Match pendientes | 🔄 Re-match errores | ⚙ → Diccionarios tab Reglas |
| GATE MATCHING | 📋 Ver errores | 🔄 Re-validar | ⚙ → Diccionarios tab Reglas |
| VALIDACIÓN | ▶ Abrir validación | 📊 Exportar Excel | 📋 Ver issues |
| SYNC | ▶ Sync incremental | 🔄 Sync full | 📋 Ver log |
| ERRORES | 📋 Ver cola | 🔄 Reprocesar | — |
| ISSUES | 📋 Ver pendientes | 📝 Resolver | — |
| TRAINING | 📊 Ver stats | 🔄 Regenerar | — |
| FINE-TUNE | 📊 Ver readiness | ▶ Entrenar (futuro) | — |
| CATÁLOGO | 📋 Ver no clasificados | + Catalogar | — |
| PERFIL | 📊 Ver actual | 🏷 Crear versión | — |

---

## 4. Wireframe: DICCIONARIOS (herramientas compartidas)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Diccionarios del Pipeline                                   [⟳ Recargar] │
│  Reglas y configuraciones que la fábrica usa para procesar                 │
│                                                                             │
│  ┌──────────┬───────────┬───────────┬──────────┬──────────┬──────────────┐ │
│  │ Reglas   │ NLP       │ Sinónimos │ Oficios  │ Skills   │ Limpieza     │ │
│  │ Matching │ Inference │ ARG       │ ARG      │ Rules    │ Títulos      │ │
│  │  (300)   │  (~50)    │  (17)     │  (170)   │  (27)    │  (~30)       │ │
│  ├──────────┴───────────┴───────────┴──────────┴──────────┴──────────────┤ │
│  │                                                                        │ │
│  │  [Tab activo muestra el editor correspondiente]                        │ │
│  │                                                                        │ │
│  │  - Buscar, agregar, editar, eliminar, toggle activar                  │ │
│  │  - Preview de impacto (en Reglas Matching)                            │ │
│  │  - Sugerencias automáticas (en Reglas Matching)                       │ │
│  │  - Guardar override a Supabase                                        │ │
│  │  - Changelog al pie (quién, cuándo, qué cambió)                      │ │
│  │                                                                        │ │
│  │  ┌── Historial de cambios ──────────────────────────────────────────┐  │ │
│  │  │ v4 │ Editado 300 reglas           │ admin@oede  │ 22/mar 15:00 │  │ │
│  │  │ v3 │ Claude creó R301             │ claude      │ 22/mar 10:00 │  │ │
│  │  │ v2 │ Cynthia agregó sinónimo      │ cynthia     │ 21/mar 14:00 │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

Cada tab reutiliza los editores que ya existen (reglas/page.tsx, sinonimos/page.tsx, etc.)
pero embebidos como componentes en vez de páginas separadas.

---

## 5. Wireframe: CATÁLOGO MOL (curación — input de mejora)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Catálogo MOL — Taxonomía Argentina                          [⟳ Actualizar]│
│  Skills y ocupaciones que ESCO no cubre                                    │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Skills   │  │  Ocup.   │  │  Pend.   │  │ Version. │                   │
│  │ catalog. │  │ catalog. │  │ revisar  │  │          │                   │
│  │   45     │  │   12     │  │   85     │  │    3     │                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│                                                                             │
│  ┌─────────────────┬───────────────┬──────────────────┬──────────────────┐ │
│  │ No clasificados │ Skills MOL    │ Ocupaciones MOL  │ Versiones        │ │
│  ├─────────────────┴───────────────┴──────────────────┴──────────────────┤ │
│  │                                                                        │ │
│  │  [Contenido del tab activo]                                            │ │
│  │  - No clasificados: skills/títulos sin ESCO, catalogar inline          │ │
│  │  - Skills MOL: CRUD con workflow (detectada → revisión → catalogada)  │ │
│  │  - Ocupaciones MOL: CRUD con ISCO parent y skills esenciales          │ │
│  │  - Versiones: crear cortes, historial con deltas                      │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Ciclo: Detectada → En revisión → Catalogada → Versionada                  │
│  Las catalogadas alimentan el Perfil Argentino                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Wireframe: PERFIL ARGENTINO (publicación — output de mejora)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Perfil Consolidado Argentino                                [⟳ Actualizar]│
│  Snapshot versionado del mercado laboral — ESCO + MOL                      │
│                                                                             │
│  ┌── Versión activa ────────────────────────────────────────────────────┐  │
│  │  v1.0 · 14,257 skills · 3,046 ocupaciones · 0 emergentes aprobadas │  │
│  │  Creado por: admin@oede.gob.ar · 15/ene/2026                       │  │
│  │                                                     [Crear v1.1 →]  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌── Estado desde último corte ─────────────────────────────────────────┐  │
│  │  2,132 ofertas nuevas procesadas                                     │  │
│  │  8 skills emergentes detectadas                                      │  │
│  │  3 emergentes pendientes de revisión                                 │  │
│  │  5 skills aprobadas desde v1.0                                       │  │
│  │                                                                       │  │
│  │  Recomendación: hay material para un nuevo corte v1.1                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌── Historial de versiones ────────────────────────────────────────────┐  │
│  │  v1.0 │ 14,257 skills │ 3,046 ocup │ Activa │ 15/ene │ [Rollback] │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Wireframe: VALIDACIÓN (estación del analista)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Validación Humana                     [📊 Stats]  [📋 Issues]  [⟳]      │
│                                                                             │
│  ┌── Stats ─────────────────────────────────────────────────────────────┐  │
│  │  Pendientes: 2,340  │  OK: 15,200  │  Error: 89  │  Basura: 340    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Lista ──────┐  ┌─ Puesto ──────────────┐  ┌─ Clasificación ────────┐  │
│  │              │  │                        │  │                        │  │
│  │ ▶ #4523     │  │ Gerente de Ventas      │  │ ISCO: 5223            │  │
│  │   #4524     │  │ Empresa: Acme Corp     │  │ Score: 0.42           │  │
│  │   #4525     │  │ Provincia: CABA        │  │ Método: semántico     │  │
│  │   ...       │  │                        │  │                        │  │
│  │              │  │ Tareas:               │  │ Gate NLP: ✅ aprobado  │  │
│  │ Filtros:    │  │ - Liderar equipo      │  │ Gate Match: ⚠ error   │  │
│  │ [Grupo ISCO]│  │ - Definir estrategia  │  │                        │  │
│  │ [Portal    ]│  │                        │  │ Skills:               │  │
│  │ [Score     ]│  │ NLP:                  │  │ - ventas (0.89)       │  │
│  │ [Estado    ]│  │ Seniority: NULL ❌    │  │ - liderazgo (0.78)    │  │
│  └──────────────┘  └────────────────────────┘  └────────────────────────┘  │
│                                                                             │
│  ┌── Acciones ──────────────────────────────────────────────────────────┐  │
│  │ [✅ OK Alt+1] [❌ Error Alt+2] [🔍 Revisar Alt+3] [🗑 Basura Alt+4]│  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Al marcar Error/Revisar → Wizard (3 tabs: NLP, Tareas/Skills, Ocupación) │
│  Al guardar → auto-crea issue → cola para Claude/dev                      │
│  Issue resuelto → training pair → alimenta fine-tuning                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Gateway local: tabla pipeline_commands

Para que el admin pueda controlar la fábrica sin terminal ni Claude:

```sql
CREATE TABLE pipeline_commands (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  comando         TEXT NOT NULL,      -- ver tabla abajo
  params          JSONB DEFAULT '{}', -- parámetros del comando
  estado          TEXT DEFAULT 'pendiente'
                  CHECK (estado IN ('pendiente','ejecutando','completado','error')),
  log             TEXT,               -- output en tiempo real
  resultado       JSONB,              -- métricas al terminar
  creado_por      TEXT,               -- email del admin
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  started_at      TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ
);
```

**Comandos soportados:**

| Comando | Parámetros | Qué ejecuta | Nodo |
|---------|-----------|-------------|------|
| `run_pipeline` | `{limit: 500}` | `run_validated_pipeline.py --limit 500` | NLP+Matching |
| `run_nlp` | `{limit: 500, ids: [...]}` | `process_nlp_from_db_v11.py --limit 500` | NLP |
| `run_matching` | `{ids: [...]}` | `run_validated_pipeline.py --skip-nlp --ids X` | Matching |
| `reprocess_errors` | `{}` | `run_validated_pipeline.py --only-errors` | NLP+Matching |
| `revalidate_nlp` | `{ids: [...]}` | `nlp_validator.py --ids X` | Gate NLP |
| `revalidate_matching` | `{ids: [...]}` | `auto_validator.py --ids X` | Gate Matching |
| `reapply_rules` | `{}` | `reapply_rules_to_validated.py` | Matching |
| `export_excel` | `{ids: [...]}` | `export_validation_excel.py --ids X` | Validación |
| `sync_supabase` | `{}` | `sync_to_supabase.py` | Sync |
| `sync_supabase_full` | `{}` | `sync_to_supabase.py --full` | Sync |
| `generate_training` | `{}` | `generate_training_pairs.py` | Training |

**Poller local (cron cada 1 min):**
```
1. Lee pipeline_commands WHERE estado = 'pendiente' ORDER BY created_at LIMIT 1
2. Marca estado = 'ejecutando', started_at = NOW()
3. Ejecuta el comando correspondiente
4. Actualiza log en tiempo real (cada 5 seg)
5. Al terminar: estado = 'completado'|'error', resultado = {...}, completed_at
```

**Mismo patrón que scraping_commands** (ya funciona en producción con systemd en VPS).

---

## 9. Plan de implementación

### Fase 1: Infraestructura (base)
| # | Tarea | Tipo | Dependencia |
|---|-------|------|-------------|
| F1.1 | Migration SQL `031_pipeline_commands.sql` | SQL | — |
| F1.2 | Ejecutar migration en Supabase | Manual | F1.1 |
| F1.3 | API `/api/pipeline-commands` (POST crear, GET listar) | API route | F1.1 |
| F1.4 | Poller local `scripts/pipeline_command_poller.py` | Python | F1.1 |
| F1.5 | Testear poller manualmente | Manual | F1.4 |

### Fase 2: Vista Fábrica (la pantalla principal)
| # | Tarea | Tipo | Dependencia |
|---|-------|------|-------------|
| F2.1 | Componente `PipelineNode` (nodo visual con estado + botones) | React | — |
| F2.2 | Componente `PipelineGate` (gate con métricas + errores) | React | — |
| F2.3 | Componente `MejoraContinuaNode` (nodo de la línea de mejora) | React | — |
| F2.4 | Página `/admin/procesamiento/fabrica/page.tsx` | React | F2.1-F2.3, F1.3 |
| F2.5 | Sección "Línea de Fabricación" (6 nodos + 2 gates) | React | F2.4 |
| F2.6 | Sección "Línea de Mejora Continua" (5 nodos + perfil) | React | F2.4 |
| F2.7 | Sección "Última actividad" (timeline reciente) | React | F2.4 |
| F2.8 | Conexión a API pipeline-commands (botones ejecutan comandos) | React | F1.3, F2.4 |
| F2.9 | Polling estado de comandos (actualiza nodos en tiempo real) | React | F2.8 |

### Fase 3: Diccionarios unificados
| # | Tarea | Tipo | Dependencia |
|---|-------|------|-------------|
| F3.1 | Extraer editores existentes como componentes embebibles | Refactor | — |
| F3.2 | Página `/admin/procesamiento/diccionarios/page.tsx` con 6 tabs | React | F3.1 |
| F3.3 | Migrar imports y estado a tabs | React | F3.2 |

### Fase 4: Reorganizar sidebar + limpiar
| # | Tarea | Tipo | Dependencia |
|---|-------|------|-------------|
| F4.1 | Actualizar `layout.tsx` con nuevo menú (5 items) | React | F2.4, F3.2 |
| F4.2 | Mover Perfil Argentino bajo Procesamiento | React | F4.1 |
| F4.3 | Eliminar rutas viejas (`/procesamiento/reglas`, etc.) o redirect | React | F3.2 |
| F4.4 | Actualizar links internos (Centro Control, etc.) | React | F4.3 |

### Fase 5: Tests + Deploy
| # | Tarea | Tipo | Dependencia |
|---|-------|------|-------------|
| F5.1 | Tests API pipeline-commands (auth, crear, listar, estados) | Test | F1.3 |
| F5.2 | Tests componente PipelineNode + PipelineGate | Test | F2.1-F2.3 |
| F5.3 | Tests página Fábrica (render, botones, polling) | Test | F2.4 |
| F5.4 | Tests página Diccionarios (tabs, carga, switch) | Test | F3.2 |
| F5.5 | Run full suite (debe seguir 700+) | Test | F5.1-F5.4 |
| F5.6 | Deploy a Vercel | Deploy | F5.5 |

### Orden de ejecución recomendado

```
F1 (infraestructura) → F2 (fábrica) → F3 (diccionarios) → F4 (sidebar) → F5 (tests+deploy)
```

Cada fase es deployable independientemente. F2 es la más grande (la vista de fábrica).

---

## 10. Páginas de detalle del pipeline (Bloque K, 2026-03-26)

> Actualización: cada etapa del embudo de la Fábrica tiene su propia página de detalle.
> Plan completo: `docs/plan/14_CANONIZACION_SKILLS_TAREAS.md`

### P-47: Detalle NLP (`/fabrica/nlp`)

```
┌─────────────────────────────────────────────────────────────┐
│  NLP — Detalle del extractor                    [Actualizar]│
│                                                             │
│  ┌── Estado del modelo ─────────────────────────────────┐  │
│  │ Modelo: Qwen2.5:7b via Ollama   Estado: ● Operativo │  │
│  │ Host: 172.17.0.1:11434          Versión: v11.4       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌── Métricas ──────────────────────────────────────────┐  │
│  │ Procesadas: 44,151 / 44,920 (98.3%)                  │  │
│  │ Pendientes: 769                                       │  │
│  │ Último run: run_20260320 · 500 ofertas · 3h 55m      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌── Completitud por campo ─────────────────────────────┐  │
│  │ titulo_limpio   ████████████████████ 100%             │  │
│  │ provincia       ████████████████████  99%             │  │
│  │ tareas          ██████████████████░░  95%             │  │
│  │ area_funcional  █████████████████░░░  92%             │  │
│  │ seniority       ████████████████░░░░  88%             │  │
│  │ jornada_laboral █████░░░░░░░░░░░░░░░  35%             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### P-48: Gate NLP (`/fabrica/validacion-nlp`)

```
┌─────────────────────────────────────────────────────────────┐
│  Validación NLP — Gate de calidad               [Actualizar]│
│                                                             │
│  51 reglas activas · 100% aprobación · 0 bloqueadas        │
│                                                             │
│  ┌── Errores por severidad ─────────────────────────────┐  │
│  │ info     ████████████████████  12,589 (56%)          │  │
│  │ medio    ██████████████░░░░░░   8,960 (40%)          │  │
│  │ warning  █░░░░░░░░░░░░░░░░░░░     713 (3%)           │  │
│  │ bajo     ░░░░░░░░░░░░░░░░░░░░     258 (1%)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌── Top errores ───────────────────────────────────────┐  │
│  │ error_scraping         info   6,385  (desc corta)    │  │
│  │ error_nlp_skills       medio  6,374  (pocas skills)  │  │
│  │ error_clae             info   5,888  (sector dudoso) │  │
│  │ error_nlp_ubicacion    medio  1,132  (ubic mal)      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### P-49: Skills (`/fabrica/skills`)

```
┌─────────────────────────────────────────────────────────────┐
│  Skills — Monitor del extractor                 [Actualizar]│
│                                                             │
│  Modelo: BAAI/bge-m3 (base)    LoRA: ✗ No disponible      │
│  Catálogo: 14,247 ESCO → planificado ~3,000 canónicas     │
│  Umbral: 0.40                                               │
│                                                             │
│  Con skills:  42,636 (96.6%)  ████████████████████████████  │
│  Sin skills:   1,515 (3.4%)   ░                            │
│    Sin tareas: 1,276 · No matcheó: 239                     │
│                                                             │
│  [Ver canonización →]  [Re-extraer pendientes]              │
└─────────────────────────────────────────────────────────────┘
```

### P-50: Matching (`/fabrica/matching`)

```
┌─────────────────────────────────────────────────────────────┐
│  Matching — Clasificación ESCO                  [Actualizar]│
│                                                             │
│  Versión: v3.5.4 ESCO-First                                │
│  Con matching: 37,776 · Pendientes: 6,375                  │
│                                                             │
│  ┌── Método de decisión ────────────────────────────────┐  │
│  │ Regla de negocio  ████████████  45%  (299 reglas)    │  │
│  │ Semántico         ██████████░░  55%                   │  │
│  │ Diccionario ARG   ░░░░░░░░░░░   2%  (17 ocup)       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Dual coinciden: 78% · Score promedio: 0.72                │
│  [Ver reglas →]  [Lanzar matching →]                        │
└─────────────────────────────────────────────────────────────┘
```

### P-51: Gate Matching (`/fabrica/validacion-matching`)

Similar a P-48 pero con errores de matching (divergencia dual, skills incoherentes, etc.)

### P-52: Tareas (`/fabrica/tareas`)

```
┌─────────────────────────────────────────────────────────────┐
│  Tareas — Canonización                          [Actualizar]│
│                                                             │
│  Tareas únicas extraídas: ~35,000                          │
│  Canónicas aprobadas: 0 (pendiente implementación)         │
│                                                             │
│  ┌── Top tareas más frecuentes ─────────────────────────┐  │
│  │ 1. Atención al cliente              3,450 ofertas    │  │
│  │ 2. Gestión de ventas                2,100            │  │
│  │ 3. Mantenimiento preventivo         1,890            │  │
│  │ 4. Liquidación de sueldos           1,650            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  [Iniciar clustering →]  [Ver plan canonización →]          │
└─────────────────────────────────────────────────────────────┘
```

### P-53: Editor Canonización (`/fabrica/canonizacion`)

Ver wireframe detallado en `docs/plan/14_CANONIZACION_SKILLS_TAREAS.md` sección 5.2.
