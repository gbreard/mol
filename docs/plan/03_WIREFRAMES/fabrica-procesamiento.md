# Wireframes: Fábrica de Procesamiento

> Rediseño del Bloque I (Procesamiento) como fábrica integrada.
> Fecha: 2026-03-22

---

## 1. Reorganización del Menú Sidebar

### ANTES (9 items sueltos):
```
Procesamiento
├── Metricas
├── Reglas Matching
├── NLP Inference
├── Sinonimos ARG
├── Oficios ARG
├── Catalogo MOL
├── Fine-Tuning
├── Otros Editores
└── Validacion
```

### DESPUÉS (4 items agrupados):
```
Procesamiento
├── Fábrica           ← Vista principal: pipeline visual + control + cola
├── Diccionarios      ← Todos los editores de config en tabs
├── Catálogo MOL      ← Taxonomía propia (ciclo de vida)
└── Validación        ← Panel de validación humana + issues
```

**Lógica:**
- **Fábrica** = vista de gerente de planta (monitoreo + control + métricas)
- **Diccionarios** = todos los configs editables en un solo lugar con tabs
- **Catálogo MOL** = se mantiene aparte (tiene su propio ciclo de vida)
- **Validación** = se mantiene aparte (es la estación de trabajo del analista)

---

## 2. Wireframe: FÁBRICA (vista principal)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Fábrica de Procesamiento                                    [⟳ Actualizar]│
│  Pipeline v3.3 · NLP v11.4 · Matching v3.5.4                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌────────┐  │
│  │SCRAPING │───▶│  NLP    │───▶│MATCHING │───▶│VALIDACIÓN│───▶│  SYNC  │  │
│  │ 6 port. │    │ v11.4   │    │ v3.5.4  │    │ 2 gates  │    │Supabase│  │
│  │         │    │         │    │         │    │          │    │        │  │
│  │ ✅ 42K  │    │ ⚠ 4.6K  │    │ ✅ 16K  │    │ ✅ 15.9K │    │ ✅ ok  │  │
│  │ ofertas │    │ pend.   │    │ matched │    │ validadas│    │ 15.9K  │  │
│  └─────────┘    └────┬────┘    └────┬────┘    └──────────┘    └────────┘  │
│                      │              │                                       │
│                 ┌────┴────┐    ┌────┴────┐                                 │
│                 │GATE NLP │    │GATE     │                                 │
│                 │35 reglas│    │MATCHING │                                 │
│                 │99% aprob│    │22 reglas│                                 │
│                 │ 1% bloq │    │ 23 err  │                                 │
│                 └─────────┘    └─────────┘                                 │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  CONTROL                                                                    │
│                                                                             │
│  [▶ Procesar 500]  [▶ Reprocesar errores]  [▶ Sync Supabase]  [⏸ Pausar] │
│                                                                             │
│  Última corrida: run_20260322_1430 · 500 ofertas · 12 errores · 2m 34s    │
│  Próxima corrida programada: Lun 24/03 08:00                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  COLA DE TRABAJO                                           [Ver todo →]     │
│                                                                             │
│  🔴 4,653 ofertas sin NLP (requiere Ollama)                                │
│  🟡 23 errores de matching escalados                                        │
│  🟡 8 reglas editadas sin reprocesar                     [Reprocesar]       │
│  🟡 5 issues de analistas pendientes                     [Ver issues →]     │
│  🟢 0 pendientes de sync a Supabase                                        │
│                                                                             │
├──────────────────────────────────┬──────────────────────────────────────────┤
│  MÉTRICAS DEL PIPELINE           │  INTERVENCIONES RECIENTES               │
│                                  │                                          │
│  NLP Gate aprobados:   99.2%     │  hace 2h — Cynthia marcó error ISCO     │
│  Match por regla:      45%       │            en #4523 → issue creado       │
│  Match semántico:      55%       │  hace 3h — Claude creó regla R301       │
│  Dual coinciden:       78%       │            "data engineer" → 2521        │
│  Errores pendientes:   23        │  hace 5h — Diego validó lote de 50      │
│  Training pairs:       602       │            ofertas (48 OK, 2 error)      │
│  Fine-tuning:     ⚡ almost ready│  ayer    — Pipeline procesó 500          │
│                                  │            ofertas (488 ok, 12 err)      │
│  [Ver métricas detalladas →]     │                                          │
│  [Ver fine-tuning readiness →]   │  [Ver historial completo →]             │
│                                  │                                          │
└──────────────────────────────────┴──────────────────────────────────────────┘
```

**Nodos del pipeline son clickeables:**
- Click en SCRAPING → va a `/admin/scraping`
- Click en NLP → muestra detalle NLP (versión, campos, tasa aprobación)
- Click en GATE NLP → muestra reglas activas y errores bloqueados
- Click en MATCHING → muestra distribución método, top reglas
- Click en GATE MATCHING → muestra errores pendientes con detalle
- Click en VALIDACIÓN → va a `/admin/validacion`
- Click en SYNC → muestra último sync, pendientes

---

## 3. Wireframe: DICCIONARIOS (editores unificados)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Diccionarios del Pipeline                                   [⟳ Recargar] │
│  Editá reglas y configuraciones que el pipeline usa para procesar          │
│                                                                             │
│  ┌────────┬───────────┬───────────┬──────────┬──────────┬────────────────┐ │
│  │ Reglas │ NLP       │ Sinónimos │ Oficios  │ Skills   │ Limpieza      │ │
│  │Matching│ Inference │ ARG       │ ARG      │ Rules    │ Títulos       │ │
│  │ (300)  │ (~50)     │ (17)      │ (170)    │ (27)     │ (~30)         │ │
│  ├────────┴───────────┴───────────┴──────────┴──────────┴────────────────┤ │
│  │                                                                        │ │
│  │  [Tab activo: Reglas Matching]                                         │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │ [🔍 Buscar...]  [+ Nueva regla]  [💡 Sugerencias]  [💾 Guardar] │  │ │
│  │  ├──────────────────────────────────────────────────────────────────┤  │ │
│  │  │ # │ ID / Nombre        │ Condición            │ ISCO │ Activa │  │ │
│  │  │───┤────────────────────┤──────────────────────┤──────┤────────│  │ │
│  │  │ 1 │ R1_gerente_ventas  │ titulo: "gerente..."│ 1221 │  ✅    │  │ │
│  │  │ 2 │ R2_contador        │ titulo: "contador"  │ 2411 │  ✅    │  │ │
│  │  │ 3 │ R3_data_engineer   │ titulo∈["data e.." ]│ 2521 │  ✅    │  │ │
│  │  │...│ ...                │ ...                  │ ...  │  ...   │  │ │
│  │  ├──────────────────────────────────────────────────────────────────┤  │ │
│  │  │ 300 reglas · fuente: override v4 · admin@oede.gob.ar            │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  │  ┌── Historial de cambios ──────────────────────────────────────────┐  │ │
│  │  │ v4 │ Editado 300 reglas           │ admin@oede  │ 22/mar 15:00 │  │ │
│  │  │ v3 │ Agregar regla R301           │ admin@oede  │ 22/mar 10:00 │  │ │
│  │  │ v2 │ Agregar regla contador       │ admin@oede  │ 21/mar 14:00 │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Cada tab contiene:**
- Reglas Matching → tabla de reglas con CRUD + preview impacto + sugerencias
- NLP Inference → secciones (modalidad, seniority, área) con keywords
- Sinónimos ARG → tabla término → ISCO con variantes
- Oficios ARG → categorías colapsables con chips
- Skills Rules → tabla condición → skills forzadas
- Limpieza Títulos → patrones regex (readonly por ahora, editable via genérico)

**Todos comparten:**
- Mismo patrón: carga override de Supabase, fallback a JSON local
- Changelog al pie (componente `ConfigChangelog`)
- Botón "Guardar" que upserta en `config_overrides`

---

## 4. Wireframe: VALIDACIÓN (estación del analista)

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
│  │   #4524     │  │ Empresa: Acme Corp     │  │ Label: Vendedor       │  │
│  │   #4525     │  │ Portal: Bumeran        │  │ Score: 0.42           │  │
│  │   #4526     │  │ Provincia: CABA        │  │ Método: semántico     │  │
│  │   #4527     │  │                        │  │                        │  │
│  │   ...       │  │ Descripción:           │  │ Skills:               │  │
│  │              │  │ Buscamos un gerente... │  │ - ventas (0.89)       │  │
│  │              │  │                        │  │ - negociación (0.85)  │  │
│  │ Filtros:    │  │ Tareas:               │  │ - liderazgo (0.78)    │  │
│  │ [Grupo ISCO]│  │ - Liderar equipo      │  │                        │  │
│  │ [Portal    ]│  │ - Definir estrategia  │  │ Gate NLP: ✅ aprobado  │  │
│  │ [Provincia ]│  │ - Reportar a director │  │ Gate Match: ⚠ error   │  │
│  │ [Score     ]│  │                        │  │   → "ISCO incorrecto  │  │
│  │ [Estado    ]│  │ NLP:                  │  │     para cargo con     │  │
│  │              │  │ Seniority: NULL ❌    │  │     gente a cargo"    │  │
│  │              │  │ Área: Comercial       │  │                        │  │
│  │              │  │ Modalidad: presencial │  │                        │  │
│  │              │  │                        │  │                        │  │
│  └──────────────┘  └────────────────────────┘  └────────────────────────┘  │
│                                                                             │
│  ┌── Acciones ──────────────────────────────────────────────────────────┐  │
│  │ [✅ OK Alt+1] [❌ Error Alt+2] [🔍 Revisar Alt+3] [🗑 Basura Alt+4]│  │
│  │                                                          [✏ Editar] │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Al marcar Error/Revisar → abre Wizard:                                    │
│  ┌── Wizard Corrección ────────────────────────────────────────────────┐  │
│  │ [Tab NLP] [Tab Tareas/Skills] [Tab Ocupación]                       │  │
│  │                                                                      │  │
│  │ Tab Ocupación (activa):                                              │  │
│  │ ISCO correcto: [1221_____]  Label: director comercial               │  │
│  │ Justificación: [Título dice "gerente" con gente a cargo,           ]│  │
│  │                [corresponde a directivo, no vendedor               ]│  │
│  │                                                                      │  │
│  │                                   [Cancelar]  [💾 Guardar + Issue]  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  → Al guardar: actualiza ofertas_dashboard + auto-crea issue en Supabase   │
│  → Issue queda en cola para Claude o dev que lo resuelve creando regla     │
│  → Al resolver issue → genera training pair → alimenta fine-tuning         │
│                                                                             │
│  ┌── Issues recientes (de esta sesión) ────────────────────────────────┐  │
│  │ 🟡 #4523 │ ISCO incorrecto: 5223 → 1221 │ Cynthia │ hace 2 min    │  │
│  │ 🟢 #4501 │ Seniority NULL → manager      │ Diego   │ hace 1h       │  │
│  │                                                    [Ver todos →]    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Wireframe: CATÁLOGO MOL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Catálogo MOL — Taxonomía Argentina                          [⟳ Actualizar]│
│  Skills y ocupaciones que ESCO no cubre · Versión actual: v1.0             │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Skills   │  │  Ocup.   │  │  Pend.   │  │ Version. │                   │
│  │ catalog. │  │ catalog. │  │ revisar  │  │          │                   │
│  │   45     │  │   12     │  │   85     │  │    3     │                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│                                                                             │
│  ┌────────────────┬──────────────┬──────────────────┬───────────────────┐  │
│  │ No clasificados│ Skills MOL   │ Ocupaciones MOL  │ Versiones         │  │
│  ├────────────────┴──────────────┴──────────────────┴───────────────────┤  │
│  │                                                                       │  │
│  │  [Tab: No clasificados]                                               │  │
│  │                                                                       │  │
│  │  Frecuencia mín: [5+ ofertas ▾]                                       │  │
│  │                                                                       │  │
│  │  ── Skills sin clasificar (23) ──────────────────────────────         │  │
│  │  │ Docker Compose        │ 45 ofertas │ 0.28% │ [+ Catalogar] │      │  │
│  │  │ Terraform             │ 12 ofertas │ 0.08% │ [+ Catalogar] │      │  │
│  │  │ Scrum Master          │  8 ofertas │ 0.05% │ [+ Catalogar] │      │  │
│  │                                                                       │  │
│  │  ── Títulos sin ocupación ESCO (12) ─────────────────────────         │  │
│  │  │ Community Manager     │ 30 of. │ score 0.35 │ [+ Catalogar] │     │  │
│  │  │ Data Engineer Sr      │ 22 of. │ score 0.41 │ [+ Catalogar] │     │  │
│  │                                                                       │  │
│  │  Ciclo: Detectada → En revisión → Catalogada → Versionada            │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Flujo completo de la fábrica (documentación)

```
                    FÁBRICA DE PROCESAMIENTO MOL
                    ═══════════════════════════

    ┌─────────────────── ADQUISICIÓN ───────────────────┐
    │                                                    │
    │   VPS (6 portales) ──cron──▶ BD local (42K)       │
    │   [Admin: /admin/scraping → lanzar/pausar]        │
    │                                                    │
    └──────────────────────┬─────────────────────────────┘
                           │
    ┌──────────────────────▼─────────────────────────────┐
    │              PROCESAMIENTO NLP                      │
    │                                                    │
    │   Oferta cruda ──▶ NLP v11.4 (Qwen2.5:7b)        │
    │     - 20 campos extraídos                          │
    │     - Source-aware pre-fill                         │
    │     - Postprocessor (configs NLP)                   │
    │                                                    │
    │   Configs: nlp_preprocessing, nlp_inference_rules, │
    │            nlp_extraction_patterns, nlp_normalization│
    │   [Admin: Diccionarios → tab NLP Inference]        │
    │                                                    │
    │        ┌──────────────────────┐                    │
    │        │    GATE NLP (v1.1)   │                    │
    │        │    35+ reglas        │                    │
    │        │                      │                    │
    │        │  ✅ Aprobado → sigue │                    │
    │        │  🔴 Bloqueado:       │                    │
    │        │    → auto-corrección │                    │
    │        │    → re-validación   │                    │
    │        │    → escalar a cola  │                    │
    │        └──────────┬───────────┘                    │
    │                   │                                │
    └───────────────────┼────────────────────────────────┘
                        │
    ┌───────────────────▼────────────────────────────────┐
    │              MATCHING v3.5.4                        │
    │                                                    │
    │   1. Reglas negocio (300) → GANAN SIEMPRE          │
    │   2. Diccionario argentino (17 ocup)               │
    │   3. Semántico (LoRA + título 40% + skills 60%)    │
    │   4. Penalizaciones (sector, seniority)            │
    │                                                    │
    │   Configs: matching_rules_business,                │
    │            sinonimos_argentinos_esco,               │
    │            matching_config, skills_rules,           │
    │            oficios_arg                              │
    │   [Admin: Diccionarios → tabs Reglas/Sinónimos/    │
    │           Oficios/Skills]                           │
    │                                                    │
    │        ┌──────────────────────┐                    │
    │        │  GATE MATCHING       │                    │
    │        │  22 reglas           │                    │
    │        │                      │                    │
    │        │  ✅ Aprobado → sigue │                    │
    │        │  🟡 Errores:         │                    │
    │        │    → auto-corrección │                    │
    │        │    → escalar a cola  │                    │
    │        └──────────┬───────────┘                    │
    │                   │                                │
    └───────────────────┼────────────────────────────────┘
                        │
    ┌───────────────────▼────────────────────────────────┐
    │          COLA DE ERRORES                           │
    │                                                    │
    │   Errores agrupados por tipo y patrón:             │
    │                                                    │
    │   ┌─────────────┐    ┌─────────────────┐          │
    │   │   CLAUDE     │    │   HUMANO         │          │
    │   │   (agente)   │    │   (analista)     │          │
    │   │              │    │                  │          │
    │   │ • Revisa     │    │ • Valida 1x1    │          │
    │   │   errores    │    │ • Marca OK/Err  │          │
    │   │ • Diagnos-   │    │ • Wizard correc │          │
    │   │   tica raíz  │    │ • Auto-crea     │          │
    │   │ • Crea       │    │   issue         │          │
    │   │   reglas     │    │ • Justifica     │          │
    │   │ • Reprocesa  │    │   (→ training)  │          │
    │   └──────┬───────┘    └────────┬────────┘          │
    │          │                     │                    │
    │          └─────────┬───────────┘                    │
    │                    ▼                                │
    │   Reglas actualizadas en configs                    │
    │   Issues resueltos con solucion_aplicada            │
    │   Training pairs generados (602+)                   │
    │   [Admin: Fábrica → ver cola + intervenciones]      │
    │                                                    │
    └───────────────────┬────────────────────────────────┘
                        │
    ┌───────────────────▼────────────────────────────────┐
    │              SYNC & PRESENTACIÓN                   │
    │                                                    │
    │   Validadas → sync_to_supabase → Dashboard         │
    │   Training pairs → fine-tuning (cuando ready)      │
    │   No clasificados → Catálogo MOL                   │
    │                                                    │
    │   [Admin: Fábrica → botón Sync Supabase]           │
    │   [Admin: Catálogo MOL → revisar no clasificados]  │
    │   [Admin: Fábrica → ver fine-tuning readiness]     │
    │                                                    │
    └────────────────────────────────────────────────────┘
```

---

## 7. Menú sidebar final

```
ADMIN
├── Centro de Control        (J — dashboard general)
├── Scraping                 (H — portales + comandos)
│   ├── Dashboard
│   ├── Comandos
│   └── Dinámica
│
├── Procesamiento            (I + G — la fábrica)
│   ├── Fábrica              ← NUEVA: vista pipeline + control + cola
│   ├── Diccionarios         ← NUEVA: 6 tabs unificados
│   ├── Catálogo MOL         (G — taxonomía propia)
│   └── Validación           (panel analista + issues)
│
├── Laboratorio              (indicadores experimentales)
│   ├── Tensión Demanda
│   ├── Brecha Calificación
│   └── ... (7 indicadores)
│
├── Skills Intelligence      (taxonomía ESCO)
├── Perfil Argentino         (versiones perfil consolidado)
├── Issues                   (gestión issues)
├── Usuarios                 (CRUD usuarios)
├── Métricas                 (analytics)
├── Configuración            (settings generales)
└── Arquitectura             (diagrama del sistema)
```

**Cambios vs actual:**
- `Metricas` (procesamiento) → absorbido por `Fábrica`
- `Reglas Matching` → absorbido por `Diccionarios` (tab 1)
- `NLP Inference` → absorbido por `Diccionarios` (tab 2)
- `Sinónimos ARG` → absorbido por `Diccionarios` (tab 3)
- `Oficios ARG` → absorbido por `Diccionarios` (tab 4)
- `Skills Rules` → absorbido por `Diccionarios` (tab 5)
- `Limpieza Títulos` → absorbido por `Diccionarios` (tab 6)
- `Fine-Tuning` → absorbido por `Fábrica` (sección métricas)
- `Otros Editores` → eliminado (todo está en Diccionarios)
- `Catálogo MOL` → se mantiene (ciclo de vida propio)
- `Validación` → se mantiene (estación de trabajo analista)

---

## 8. Interacciones clave

### Desde Fábrica (gerente de planta):
| Acción | Qué hace | Cómo |
|--------|----------|------|
| Procesar N | Lanza pipeline para N ofertas nuevas | POST /api/pipeline-commands |
| Reprocesar errores | Re-procesa ofertas con errores pendientes | POST /api/pipeline-commands |
| Sync Supabase | Sube validadas a Supabase | POST /api/pipeline-commands |
| Ver cola | Muestra errores agrupados por tipo | GET /api/pipeline-status |
| Ver métricas | Abre detalle de métricas (inline o modal) | Datos de get_processing_metrics |
| Ver fine-tuning | Abre readiness (inline o modal) | GET /api/training-readiness |

### Desde Diccionarios (editor de reglas):
| Acción | Qué hace |
|--------|----------|
| Editar regla | Modifica regla existente |
| Nueva regla | Formulario + preview impacto |
| Sugerencias | Reglas sugeridas por correcciones |
| Guardar | Upsert a config_overrides |
| Ver changelog | Timeline de cambios |

### Desde Validación (analista):
| Acción | Qué hace |
|--------|----------|
| OK | Marca oferta como correcta |
| Error | Abre wizard → corrige → auto-crea issue |
| Revisar | Abre wizard → sugiere corrección → auto-crea issue |
| Basura | Descarta oferta |

### Desde Catálogo MOL (curación):
| Acción | Qué hace |
|--------|----------|
| Catalogar skill | Detectada → En revisión → Catalogada |
| Catalogar ocupación | Detectada → En revisión → Catalogada |
| Crear versión | Corte con snapshot de catalogadas |
| Descartar | Soft delete |

---

## 9. Gateway local (sin Claude)

Para que el admin pueda dar órdenes al pipeline local sin intervención de Claude:

```
TABLA: pipeline_commands (Supabase)
─────────────────────────────────────
id            UUID
comando       TEXT    (run_pipeline, reprocess_errors, sync_supabase,
                       reapply_rules, export_excel)
params        JSONB   ({limit: 500, ids: [1,2,3], skip_nlp: true})
estado        TEXT    (pendiente, ejecutando, completado, error)
log           TEXT    (output del proceso, actualizado en tiempo real)
resultado     JSONB   ({procesadas: 500, errores: 12, duracion: "2m 34s"})
creado_por    TEXT    (email del admin)
created_at    TIMESTAMPTZ
started_at    TIMESTAMPTZ
completed_at  TIMESTAMPTZ

POLLER LOCAL (cron cada 1 min):
─────────────────────────────────
1. Lee pipeline_commands WHERE estado = 'pendiente'
2. Marca 'ejecutando' + started_at
3. Ejecuta: python scripts/run_validated_pipeline.py --limit N
4. Actualiza log en tiempo real
5. Al terminar: estado = 'completado', resultado = {...}

FLUJO:
Admin click "Procesar 500"
  → POST /api/pipeline-commands {comando: "run_pipeline", params: {limit: 500}}
  → INSERT en pipeline_commands
  → Poller local lo lee en <1 min
  → Ejecuta pipeline
  → Admin ve progreso en la UI (polling cada 5s)
```

Mismo patrón que `scraping_commands` (ya funciona en producción).
