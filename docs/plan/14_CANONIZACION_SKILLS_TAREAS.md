# Canonización de Skills y Tareas — Optimización del Pipeline

> Versión: 1.0 — 2026-03-26
> Prioridad: CRÍTICA — afecta calidad de matching, gasto computacional, y datos del dashboard

---

## 1. Diagnóstico del problema

### 1.1 Skills ESCO: redundancia y dispersión

**Datos cuantitativos (14,247 skills en catálogo):**

| Métrica | Cantidad | % del total |
|---------|----------|-------------|
| Skills únicas (sin familia) | 13,177 | 92.5% |
| Familias con 2 variaciones | 316 familias (632 skills) | 4.4% |
| Familias con 3+ variaciones | 99 familias (434 skills) | 3.0% |
| Duplicados exactos | 31 labels (63 skills) | 0.4% |
| Skills contextuales (sobre/gestionar/asesorar) | 1,105 | 7.8% |
| Skills > 60 caracteres | 1,073 | 7.5% |

**Top verbos que generan familias redundantes:**
```
gestionar    510 skills  (gestionar inventario, gestionar personal, gestionar X...)
realizar     468 skills
mantener     321 skills
utilizar     319 skills
supervisar   286 skills
```

**Ejemplo concreto del problema:**
```
ESCO tiene 14 variaciones de "trabajar en equipo":
- "trabajar en equipo"
- "trabajar en equipos"
- "trabajar en equipos multidisciplinares"
- "trabajar en equipo en cuadrillas de construcción"
- "trabajar en equipo en entornos peligrosos"
- "trabajar en equipo en líneas de ensamble"
- "trabajar en equipos sanitarios multidisciplinarios"
- "facilitar el trabajo en equipo entre estudiantes"
- "promover el trabajo en equipo"
- "gestionar el trabajo en equipo"
- "principios del trabajo en equipo"
- etc.

En Argentina, una oferta pide: "trabajo en grupo" o "saber trabajar en equipo"
El modelo busca contra las 14 variaciones → dispersa el score semántico
```

**Mismo problema con "atención al cliente":**
```
- "servicio al cliente"
- "prestar un servicio de atención al cliente de primera calidad"
- "ofrecer un servicio de atención al cliente de fitness"
- "gestionar el servicio al cliente"
- "comunicarse con el departamento de atención al cliente"
- "establecer un proceso de TIC de atención al cliente"
- "enseñar técnicas de servicio al cliente"
- "analizar los cuestionarios de servicio al cliente"
```

### 1.2 Impacto en el pipeline

| Etapa | Problema | Impacto |
|-------|----------|---------|
| **Skills Extractor** | Busca contra 14,247 skills cuando muchas son variaciones | Scores bajos (max 0.45 vs umbral 0.40), 52% sin skills hasta fix reciente |
| **Matching** | Skills dispersas = embeddings difusos | Matching semántico menos preciso |
| **Cómputo** | Cada oferta calcula similitud contra 14,247 embeddings | CPU/GPU desperdiciada en variaciones redundantes |
| **Dashboard** | Skills reportadas son ultra-específicas de ESCO | "aconsejar a los clientes sobre bicicletas" no sirve para análisis argentino |

### 1.3 Tareas: mismo problema

El NLP extrae tareas en texto libre de cada oferta. Cada portal las describe distinto:
```
Portal A: "Atender clientes por teléfono y resolver consultas vía WhatsApp"
Portal B: "Atención al público en mostrador y vía telefónica"
Portal C: "Customer service, resolución de quejas"

→ Son la misma tarea pero 3 formulaciones distintas
→ Cuando el extractor de skills busca, cada formulación da scores diferentes
```

---

## 2. Solución propuesta: Canonización en 2 capas

### 2.1 Capa 1 — Catálogo de Skills Canónicas (offline)

Reducir las 14,247 skills ESCO a un catálogo canónico agrupado:

```
SKILL CANÓNICA: "Trabajo en equipo"
  ├── ESCO: "trabajar en equipo" (uri: esco/skill/xxx)
  ├── ESCO: "trabajar en equipos" (uri: esco/skill/yyy)
  ├── ESCO: "trabajar en equipo en entornos peligrosos"
  ├── ESCO: "promover el trabajo en equipo"
  ├── ARG: "trabajo en grupo"
  ├── ARG: "laburar en equipo"
  └── ARG: "capacidad de trabajo grupal"
```

**Estructura de una skill canónica:**
```json
{
  "id": "CAN-001",
  "label_canonico": "Trabajo en equipo",
  "tipo": "transversal",
  "skills_esco_agrupadas": ["uri1", "uri2", "uri3"],
  "sinonimos_argentinos": ["trabajo en grupo", "trabajo grupal"],
  "embedding_canonico": [0.12, 0.34, ...],  // 1 embedding por grupo
  "frecuencia_mercado": 45.2
}
```

**Beneficio computacional:**
```
HOY:    1 oferta × 14,247 embeddings = 14,247 comparaciones
FUTURO: 1 oferta × ~3,000 canónicas  = 3,000 comparaciones (5x más rápido)
```

### 2.2 Capa 2 — Canonización de Tareas (en tiempo real)

Cada oferta nueva que entra al pipeline:

```
NLP extrae tareas originales
  ↓
Buscador de tarea canónica (embedding similarity)
  ↓
Si matchea (score > 0.80) → asigna tarea_canonica existente
Si no matchea → queda como "tarea nueva sin canónico" → cola para analista
  ↓
Skills se extraen usando la tarea ORIGINAL (preserva varianza)
Skills se AGRUPAN usando el canónico (para análisis)
```

**Importante:** La tarea original NUNCA se reemplaza. El canónico es metadata adicional.

### 2.3 Relación Skills ↔ Tareas

```
Tarea original: "Soldar estructuras metálicas con MIG y TIG"
  ↓
Tarea canónica: "Soldadura"
  ↓
Skills del original: "soldadura MIG", "soldadura TIG", "lectura de planos"
  ↓
Skills canónicas: "Soldadura" (agrupa MIG+TIG+arco+punto)
  ↓
En análisis: "45% de ofertas industriales piden Soldadura"
En detalle: "de esas, 60% piden MIG, 30% TIG, 10% arco"
```

---

## 3. Cambios en el Pipeline

### 3.1 Pipeline actual
```
Scraping → NLP → Gate NLP → Skills (BGE-M3 vs 14,247) → Matching → Gate Matching → Sync
```

### 3.2 Pipeline propuesto
```
Scraping → NLP → Gate NLP → CANONIZAR TAREAS → Skills (BGE-M3 vs ~3,000 canónicas) → Matching → Gate Matching → Sync
                                    ↓
                              Tareas nuevas → cola analista
```

### 3.3 Proceso de creación del catálogo canónico (una vez)

```
1. CLUSTERING AUTOMÁTICO
   - Tomar los 14,247 embeddings de skills ESCO
   - Clustering jerárquico (similitud > 0.80)
   - Resultado: ~3,000-4,000 clusters

2. REVISIÓN HUMANA
   - Analista revisa los clusters grandes (>3 miembros)
   - Asigna label canónico argentino
   - Agrega sinónimos locales
   - Aprueba/rechaza agrupaciones

3. GENERAR EMBEDDINGS CANÓNICOS
   - Para cada cluster: promedio de embeddings de sus miembros
   - O: embedding del label canónico
   - Guardar en nuevo archivo: esco_skills_canonical_embeddings.npy

4. ACTUALIZAR EXTRACTOR
   - SkillsImplicitExtractor usa embeddings canónicos en vez de los 14,247
   - Resultado: una skill por oferta apunta al grupo canónico
   - Detalle: se guarda qué skill ESCO específica matcheó dentro del grupo
```

---

## 4. Modelo de datos

### 4.1 Nueva tabla: `skills_canonical`

```sql
CREATE TABLE skills_canonical (
  id TEXT PRIMARY KEY,                    -- CAN-001
  label_canonico TEXT NOT NULL,           -- "Trabajo en equipo"
  label_canonico_normalizado TEXT NOT NULL,
  tipo TEXT CHECK (tipo IN ('skill', 'knowledge', 'transversal')),
  skills_esco_uris JSONB DEFAULT '[]',   -- URIs agrupadas
  skills_esco_labels JSONB DEFAULT '[]', -- Labels agrupados
  sinonimos_argentinos JSONB DEFAULT '[]',
  embedding_index INTEGER,               -- Índice en archivo .npy
  frecuencia_mercado NUMERIC(5,2) DEFAULT 0,
  estado TEXT DEFAULT 'auto' CHECK (estado IN ('auto', 'revisado', 'aprobado')),
  aprobado_por TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 Nueva tabla: `tareas_canonical`

```sql
CREATE TABLE tareas_canonical (
  id TEXT PRIMARY KEY,                    -- TAR-001
  label_canonico TEXT NOT NULL,           -- "Atención al cliente"
  variantes JSONB DEFAULT '[]',          -- ["atender clientes", "customer service", ...]
  skills_asociadas JSONB DEFAULT '[]',   -- CAN-IDs típicos de esta tarea
  frecuencia_mercado NUMERIC(5,2) DEFAULT 0,
  estado TEXT DEFAULT 'auto' CHECK (estado IN ('auto', 'revisado', 'aprobado')),
  aprobado_por TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.3 Columnas nuevas en `ofertas_nlp`

```sql
ALTER TABLE ofertas_nlp ADD COLUMN tareas_canonicas JSONB;       -- ["TAR-001", "TAR-005"]
ALTER TABLE ofertas_nlp ADD COLUMN skills_canonicas JSONB;       -- ["CAN-001", "CAN-012"]
ALTER TABLE ofertas_nlp ADD COLUMN skills_canonicas_detalle JSONB; -- [{can_id, esco_uri, score}]
```

---

## 5. Wireframes

### 5.1 Página: `/fabrica/skills` — Monitor de Skills

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Skills — Monitor del Extractor                                [Actualizar]│
│                                                                             │
│  ┌── Estado del modelo ─────────────────────────────────────────────────┐  │
│  │ Modelo: BAAI/bge-m3 (base)              Estado: ● Operativo         │  │
│  │ Catálogo: 14,247 ESCO → 3,200 canónicas  Umbral: 0.40              │  │
│  │ LoRA fine-tuned: ✗ No disponible        Última actualización: hoy   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌── Métricas de extracción ────────────────────────────────────────────┐  │
│  │ Con skills:  42,636 (96.6%)  ████████████████████████████████████░░  │  │
│  │ Sin skills:   1,515 (3.4%)   ░░                                     │  │
│  │   Sin tareas: 1,276                                                 │  │
│  │   No matcheó:   239                                                 │  │
│  │ Promedio skills/oferta: 5.2                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌── Top skills extraídas ─────────┐  ┌── Alertas ─────────────────────┐  │
│  │ 1. Servicio al cliente   3,450  │  │ ⚠ LoRA no disponible           │  │
│  │ 2. Gestión de ventas     2,100  │  │ ⚠ 239 ofertas no matchearon    │  │
│  │ 3. Trabajo en equipo     1,890  │  │ ℹ Umbral 0.40 (base, no tuned) │  │
│  │ 4. Contabilidad          1,650  │  │                                 │  │
│  │ 5. Excel                 1,420  │  │ [Canonizar skills →]            │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
│  ┌── Skills sin canónico (por revisar) ─────────────────────────────────┐  │
│  │ "aconsejar clientes sobre bicicletas" → sugerir: "Asesoramiento"    │  │
│  │ "trabajar en equipo en líneas de ensamble" → sugerir: "Trabajo eq." │  │
│  │                                                    [Ver todas →]     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Página: `/fabrica/canonizacion` — Editor de Canónicas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Canonización de Skills                                        [Actualizar]│
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ ESCO     │  │ Canónicas│  │ Tareas   │  │ Pendientes│                  │
│  │ 14,247   │  │ 3,200    │  │ 850      │  │ 120      │                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│                                                                             │
│  ┌────────────────┬──────────────────┬────────────────────────────────────┐ │
│  │ Skills ESCO    │ Skills Canónicas │ Tareas Canónicas                  │ │
│  ├────────────────┴──────────────────┴────────────────────────────────────┤ │
│  │                                                                        │ │
│  │  [Tab: Skills Canónicas]                                               │ │
│  │                                                                        │ │
│  │  Buscar: [________________________]                                    │ │
│  │                                                                        │ │
│  │  CAN-001 | Trabajo en equipo           | 14 ESCO | transversal | ✅   │ │
│  │    └── ESCO: trabajar en equipo, trabajar en equipos,                  │ │
│  │        trabajar en equipo en cuadrillas, promover trabajo en equipo    │ │
│  │    └── ARG: trabajo en grupo, trabajo grupal                           │ │
│  │    └── Frecuencia: 45.2% de ofertas                                    │ │
│  │                                                          [Editar]      │ │
│  │                                                                        │ │
│  │  CAN-002 | Atención al cliente         | 9 ESCO  | skill       | ✅   │ │
│  │    └── ESCO: servicio al cliente, prestar servicio de atención...      │ │
│  │    └── ARG: atención al público                                        │ │
│  │                                                          [Editar]      │ │
│  │                                                                        │ │
│  │  CAN-003 | Soldadura                   | 8 ESCO  | skill       | 🔍   │ │
│  │    └── ESCO: soldadura MIG, soldadura TIG, soldadura por arco...       │ │
│  │    └── Sin sinónimos ARG                           [Agregar] [Editar]  │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [Tab: Tareas Canónicas]                                                    │
│  │                                                                        │ │
│  │  TAR-001 | Atención al cliente  | 3,450 ofertas | ✅                   │ │
│  │    └── Variantes: "atender clientes", "customer service",              │ │
│  │        "atención al público", "resolver consultas"                      │ │
│  │    └── Skills asociadas: CAN-002, CAN-015, CAN-089                     │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Páginas de detalle del pipeline (las 5 planificadas antes)

```
/fabrica/nlp              → Estado modelo Ollama + métricas extracción + campos
/fabrica/validacion-nlp   → Gate NLP: reglas, errores por tipo/severidad, evolución
/fabrica/skills           → Extractor: modelo, umbral, métricas, canonización
/fabrica/matching         → Método, scores, distribución regla/semántico
/fabrica/validacion-matching → Gate Matching: errores, issues, tasa por run
/fabrica/tareas           → Tareas canónicas, frecuencias, nuevas sin canónico
/fabrica/canonizacion     → Editor de skills y tareas canónicas
```

---

## 6. Roadmap de implementación

### Fase 0 — Preparación (1 sesión)
| # | Tarea | Tipo |
|---|-------|------|
| 0.1 | Ejecutar clustering de las 14,247 skills ESCO | Script Python |
| 0.2 | Generar propuesta automática de ~3,000 clusters | Script Python |
| 0.3 | Crear tabla `skills_canonical` en Supabase | Migration SQL |
| 0.4 | Crear tabla `tareas_canonical` en Supabase | Migration SQL |
| 0.5 | Poblar con clusters automáticos (estado: 'auto') | Script Python |

### Fase 1 — Páginas de detalle del pipeline (2 sesiones)
| # | Tarea | Tipo |
|---|-------|------|
| 1.1 | API `/api/pipeline-detail` (una API, múltiples secciones) | API route |
| 1.2 | Página `/fabrica/nlp` (estado Ollama, métricas, campos) | React |
| 1.3 | Página `/fabrica/validacion-nlp` (gate, errores, evolución) | React |
| 1.4 | Página `/fabrica/skills` (modelo, umbral, métricas) | React |
| 1.5 | Página `/fabrica/matching` (método, scores, distribución) | React |
| 1.6 | Página `/fabrica/validacion-matching` (errores, issues, tasa) | React |
| 1.7 | Página `/fabrica/tareas` (tareas canónicas, frecuencias) | React |
| 1.8 | Tests para cada página + API | Tests |
| 1.9 | Links desde Fábrica a cada página de detalle | React |

### Fase 2 — Canonización de Skills (2 sesiones)
| # | Tarea | Tipo |
|---|-------|------|
| 2.1 | Script de clustering jerárquico (cosine similarity > 0.80) | Python |
| 2.2 | Generar embeddings canónicos (promedio por cluster) | Python |
| 2.3 | Actualizar `SkillsImplicitExtractor` para usar canónicas | Python |
| 2.4 | Página `/fabrica/canonizacion` (editor CRUD) | React |
| 2.5 | API `/api/skills-canonical` (CRUD + clustering) | API route |
| 2.6 | Re-extraer skills de las 44K ofertas con canónicas | Script |
| 2.7 | Tests | Tests |

### Fase 3 — Canonización de Tareas (1 sesión)
| # | Tarea | Tipo |
|---|-------|------|
| 3.1 | Script de clustering de tareas frecuentes | Python |
| 3.2 | Integrar canonizador de tareas en pipeline | Python |
| 3.3 | Página `/fabrica/tareas` con editor | React |
| 3.4 | API `/api/tareas-canonical` | API route |
| 3.5 | Tests | Tests |

### Fase 4 — Comando validate_nlp_only en Fábrica (1 sesión)
| # | Tarea | Tipo |
|---|-------|------|
| 4.1 | Agregar comando `validate_nlp` al poller | Python |
| 4.2 | Agregar comando `extract_skills` al poller | Python |
| 4.3 | Actualizar Fábrica con botones correspondientes | React |
| 4.4 | Tests | Tests |

---

## 7. Métricas de éxito

| Métrica | Hoy | Objetivo |
|---------|-----|----------|
| Skills ESCO en catálogo | 14,247 | ~3,000-4,000 canónicas |
| Ofertas con skills | 96.6% (con umbral 0.40) | >98% (con canónicas) |
| Skills promedio/oferta | ~5 | ~8-10 (más precisas) |
| Score promedio extracción | 0.42 | >0.55 (canónicas mejor match) |
| Tiempo extracción/oferta | 0.06s (14K comparaciones) | ~0.02s (3K comparaciones) |
| Tareas canónicas | 0 | ~500-800 |
| Trazabilidad por run | No existe | % error, modelo, versión |

---

## 8. Riesgos

| Riesgo | Mitigación |
|--------|-----------|
| Clustering agrupa skills que no deberían estar juntas | Revisión humana obligatoria para clusters grandes |
| Bajar granularidad pierde detalle | Mantener link canónica → ESCO originales |
| Tareas nuevas no matchean con canónicas | Cola de "nuevas sin canónico" + sugerencia automática |
| Cambiar extractor rompe matching existente | Re-extraer skills con canónicas antes de re-matchear |
| Proceso largo (re-extraer 44K) | Ya probamos: 22 min para 23K con BGE-M3 |

---

> Próxima acción: Fase 0 (clustering) + Fase 1 (páginas detalle) en paralelo.
