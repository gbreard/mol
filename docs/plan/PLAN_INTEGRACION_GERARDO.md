# Plan de Integración — Backend (Gerardo) + Frontend (Sergio)
# Skills Intelligence: S1 · S2 · S3

> Versión: 2.0 — Actualizado 2026-03-25
> Base: `MOL_Especificacion_Claude_Code.docx` + análisis del código actual en `main`
> Branch frontend activo: `feature/si-sergio-ui`

---

## Resumen ejecutivo

El motor de datos MOL ya existe y funciona (NLP + matching ESCO + 16K ofertas validadas).
Lo que falta es la **capa de gestión de personas y casos** que conecta los tres servicios.

**División de trabajo:**
- **Gerardo** → Tablas Supabase + APIs (contratos definidos en este documento)
- **Sergio + Claude** → UI/UX de todas las pantallas (consume las APIs de Gerardo)

**Prioridad de implementación:**
1. Modelo de datos base (Gerardo) — desbloquea todo lo demás
2. S2 módulo casos — primer cliente real (OE)
3. S1 flujo trabajador — reutiliza APIs de S2
4. S3 modo activo — reutiliza matching de S2

---

## Estado actual por servicio

| Servicio | Backend | Frontend | Integrados |
|----------|---------|----------|------------|
| S1 Mi Futuro Laboral | ⚠️ APIs parciales | ⚠️ Landing + exploración | ❌ No conectados |
| S2 Oficina de Empleo | ❌ Sin casos/derivaciones | ⚠️ Wireframes | ❌ No conectados |
| S3 Modo pasivo (QR) | ✅ `/api/compatibility-report` | ✅ `/reporte/[token]` | ⚠️ Bug menor |
| S3 Modo activo | ❌ Sin APIs empresa | ❌ Sin pantallas | ❌ |

### APIs existentes (Gerardo — ya disponibles)

| API | Qué hace | Usada por |
|-----|----------|-----------|
| `GET /api/skills-search` | Buscar skills ESCO por keyword | S1 Vía 2, S2 diagnóstico |
| `GET /api/skills-extract-from-text` | NLP texto libre → skills | S1 Vía 3 |
| `GET /api/occupations/search` | Buscar ocupaciones ESCO | S1 Vía 1, S2 matching |
| `GET /api/occupations/skills` | Skills de una ocupación | S1 Vía 1 |
| `GET /api/matching-offers` | Perfil → vacantes rankeadas | S1, S2 |
| `GET /api/training-impact` | Brechas → cursos con delta match% | S1, S2 |
| `GET /api/training-suggestions` | Brechas → cursos + tendencias | S1, S2 |
| `GET/POST /api/compatibility-report` | Generar/leer reporte QR | S3 pasivo, S1 PDF |
| `GET /api/worker-profiles` | Perfiles básicos de trabajadores | S2 parcial |
| `GET /api/organizaciones` | Multi-tenancy OE | S2 |
| `GET /api/inteligencia-local` | Tendencias mercado jurisdicción | S2 módulo 3 |

---

## BLOQUE 1 — Modelo de datos (Gerardo — BLOQUEANTE)

Sin estas tablas no se puede construir nada de S1 ni S2.

### B1-T1 — Tablas de personas y perfiles

```sql
-- Persona registrada en el sistema (por S1 o S2)
CREATE TABLE personas (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre       TEXT NOT NULL,
  dni          TEXT,                    -- búsqueda rápida en S2
  edad         INTEGER,
  nivel_educativo TEXT,                 -- Primario/Secundario/Terciario/Universitario
  ubicacion    TEXT,                    -- Localidad o municipio
  telefono     TEXT,
  email        TEXT,
  opt_in       BOOLEAN DEFAULT FALSE,   -- autoriza visibilidad para empresas
  origen       TEXT CHECK (origen IN ('S1','S2')),
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Perfil de skills de una persona
CREATE TABLE perfiles (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  persona_id      UUID REFERENCES personas(id) ON DELETE CASCADE,
  origen          TEXT CHECK (origen IN ('S1','S2')),
  completitud     INTEGER DEFAULT 0,    -- cantidad de skills confirmadas
  nivel_confianza DECIMAL DEFAULT 0,    -- ponderación global (interno)
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Skills individuales dentro de un perfil
CREATE TABLE perfil_skills (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  perfil_id            UUID REFERENCES perfiles(id) ON DELETE CASCADE,
  skill_uri            TEXT NOT NULL,   -- URI ESCO
  skill_label          TEXT NOT NULL,
  via_captura          TEXT CHECK (via_captura IN ('ocupacion','tarea','texto','formacion')),
  estado               TEXT CHECK (estado IN ('confirmada','sugerida','descartada')) DEFAULT 'sugerida',
  confianza            DECIMAL DEFAULT 0.5,
  validado_por_tecnico BOOLEAN DEFAULT FALSE,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para búsqueda por DNI (S2)
CREATE INDEX ON personas(dni);
CREATE INDEX ON perfil_skills(perfil_id, estado);
```

**Respuesta esperada de Gerardo:** Sí/No a este schema + cualquier ajuste antes de implementar.

---

### B1-T2 — Tablas del sistema de casos S2

```sql
-- Caso: relación entre una persona y una OE
CREATE TABLE casos (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  persona_id      UUID REFERENCES personas(id),
  organizacion_id UUID,                  -- OE que gestiona el caso
  estado          TEXT CHECK (estado IN (
                    'nuevo','en_diagnostico','perfil_completo',
                    'derivado_vacante','derivado_curso',
                    'en_seguimiento','insertado','cerrado'
                  )) DEFAULT 'nuevo',
  objetivo        TEXT CHECK (objetivo IN ('empleo','formacion')),
  prioridad       TEXT CHECK (prioridad IN ('normal','urgente')) DEFAULT 'normal',
  nota_tecnico    TEXT,
  checkboxes_tecnico JSONB DEFAULT '{}', -- carnet_conducir, turno_tarde, etc.
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Derivación: envío de una persona a una vacante o curso
CREATE TABLE derivaciones (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  caso_id          UUID REFERENCES casos(id) ON DELETE CASCADE,
  tipo             TEXT CHECK (tipo IN ('vacante','curso')),
  destino_id       UUID,                 -- ID de la vacante o curso
  estado           TEXT CHECK (estado IN (
                     'derivado','entrevistado','no_se_presento','rechazado','aceptado'
                   )) DEFAULT 'derivado',
  motivo           TEXT,
  fecha_derivacion TIMESTAMPTZ DEFAULT NOW(),
  fecha_resultado  TIMESTAMPTZ
);

-- Log de auditoría: todo cambio de estado genera un evento
CREATE TABLE eventos_caso (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entidad     TEXT CHECK (entidad IN ('caso','perfil','vacante','derivacion')),
  entidad_id  UUID NOT NULL,
  tipo        TEXT NOT NULL,             -- caso_creado, perfil_completado, etc.
  usuario_id  UUID,
  payload     JSONB DEFAULT '{}',
  timestamp   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON casos(organizacion_id, estado);
CREATE INDEX ON casos(persona_id);
CREATE INDEX ON derivaciones(caso_id);
CREATE INDEX ON eventos_caso(entidad_id);
```

---

### B1-T3 — Tablas de vacantes y cursos de la OE

```sql
-- Vacantes que la OE carga (pool propio, distinto de pool MOL)
CREATE TABLE vacantes_oe (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organizacion_id  UUID NOT NULL,
  titulo           TEXT NOT NULL,
  empresa          TEXT,
  descripcion      TEXT,
  skills_requeridas JSONB DEFAULT '[]',  -- [{uri, label, peso}]
  ubicacion        TEXT,
  estado           TEXT CHECK (estado IN ('activa','en_proceso','cubierta','cerrada')) DEFAULT 'activa',
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Cursos del catálogo de la OE
CREATE TABLE cursos_oe (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organizacion_id  UUID NOT NULL,
  nombre           TEXT NOT NULL,
  skills_cubiertas JSONB DEFAULT '[]',   -- [{uri, label}]
  duracion         TEXT,
  modalidad        TEXT CHECK (modalidad IN ('presencial','virtual','hibrido')),
  institucion      TEXT,
  gratuito         BOOLEAN DEFAULT TRUE,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

---

## BLOQUE 2 — APIs que necesita Gerardo implementar

Contratos funcionales ordenados por prioridad. Sergio no puede avanzar en UI hasta que estén disponibles.

---

### GRUPO A — Personas y perfiles (desbloquea S1 y S2)

#### A1 — `POST /api/personas`
Crea una persona nueva o devuelve la existente si ya existe el DNI.

**Request:**
```json
{
  "nombre": "María García",
  "dni": "32456789",
  "edad": 35,
  "nivel_educativo": "Secundario completo",
  "ubicacion": "Rosario",
  "origen": "S2"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "nombre": "María García",
  "dni": "32456789",
  "es_nueva": true
}
```

**Lógica:** Si existe persona con ese DNI, devolver la existente con `"es_nueva": false`. No duplicar.

---

#### A2 — `GET /api/personas?dni=X&nombre=Y`
Búsqueda de personas para la cartera de la OE (buscador en S2).

**Response:**
```json
[
  {
    "id": "uuid",
    "nombre": "María García",
    "dni": "32456789",
    "caso_activo_id": "uuid-o-null",
    "caso_estado": "perfil_completo"
  }
]
```

---

#### A3 — `POST /api/perfiles`
Crea un perfil vacío para una persona.

**Request:** `{ "persona_id": "uuid", "origen": "S2" }`

**Response 201:** `{ "id": "uuid", "persona_id": "uuid", "completitud": 0 }`

---

#### A4 — `POST /api/perfiles/:id/skills`
Agrega una o varias skills al perfil. Calcula `completitud` automáticamente.
Si llega a 3 skills `confirmadas`, actualiza el caso asociado a `perfil_completo`.

**Request:**
```json
{
  "skills": [
    {
      "skill_uri": "http://data.europa.eu/esco/skill/xxx",
      "skill_label": "Python",
      "via_captura": "ocupacion",
      "estado": "confirmada"
    }
  ]
}
```

**Response:** Perfil actualizado con `completitud` recalculado.

---

#### A5 — `PATCH /api/perfiles/:id/skills/:skill_id`
Cambia el estado de una skill (confirmada / descartada / sugerida).

**Request:** `{ "estado": "confirmada" }`

**Response:** Skill actualizada + `completitud` recalculado en el perfil.

---

#### A6 — `GET /api/perfiles/:id`
Devuelve el perfil completo con todas sus skills.

**Response:**
```json
{
  "id": "uuid",
  "persona_id": "uuid",
  "completitud": 5,
  "skills": [
    {
      "skill_uri": "...",
      "skill_label": "Python",
      "via_captura": "ocupacion",
      "estado": "confirmada",
      "validado_por_tecnico": false
    }
  ]
}
```

---

### GRUPO B — Gestión de casos S2 (desbloquea todo el módulo OE)

#### B1 — `GET /api/casos?org_id=X&estado=Y&q=nombre_o_dni`
Lista casos de la OE. Filtros opcionales por estado y búsqueda textual.

**Response:**
```json
[
  {
    "id": "uuid",
    "persona_nombre": "María García",
    "persona_dni": "32456789",
    "estado": "perfil_completo",
    "prioridad": "normal",
    "mejor_match": 78,
    "ultima_atencion": "2026-03-20T10:00:00Z"
  }
]
```

---

#### B2 — `POST /api/casos`
Crea un caso nuevo. Si la persona ya tiene caso activo en esa OE, devolver error.

**Request:**
```json
{
  "persona_id": "uuid",
  "organizacion_id": "uuid",
  "objetivo": "empleo"
}
```

**Response 201:** Caso creado en estado `nuevo` + evento `caso_creado` en log.

---

#### B3 — `GET /api/casos/:id`
Devuelve el caso completo: datos de la persona, perfil de skills, derivaciones activas, historial de eventos.

**Response:**
```json
{
  "id": "uuid",
  "estado": "perfil_completo",
  "persona": { "nombre": "...", "dni": "...", "edad": 35 },
  "perfil": { "id": "uuid", "completitud": 5, "skills": [] },
  "derivaciones": [],
  "eventos": [],
  "nota_tecnico": "Tiene carnet de conducir",
  "checkboxes_tecnico": { "carnet_conducir": true, "turno_tarde": false }
}
```

---

#### B4 — `PATCH /api/casos/:id`
Actualiza nota, checkboxes, prioridad o estado del caso.
Valida transiciones permitidas según la máquina de estados.
Genera evento en el log.

**Request:**
```json
{
  "nota_tecnico": "Prefiere trabajos en zona norte",
  "checkboxes_tecnico": { "carnet_conducir": true },
  "prioridad": "urgente"
}
```

**Transiciones de estado válidas:**

| Desde | Hacia | Condición |
|-------|-------|-----------|
| `nuevo` | `en_diagnostico` | Técnico agrega ≥1 skill |
| `en_diagnostico` | `perfil_completo` | Perfil llega a ≥3 skills confirmadas (automático) |
| `perfil_completo` | `derivado_vacante` | Técnico registra derivación a vacante |
| `perfil_completo` | `derivado_curso` | Técnico registra derivación a curso |
| `derivado_*` | `en_seguimiento` | Se registra contacto |
| `en_seguimiento` | `insertado` | Derivación con estado `aceptado` |
| `en_seguimiento` | `perfil_completo` | Derivación rechazada — vuelve al pool |
| `en_seguimiento` | `cerrado` | Técnico cierra explícitamente |
| `cerrado` | `nuevo` | Caso reabierto |

---

#### B5 — `POST /api/casos/:id/derivar`
Registra una derivación. Valida que el caso esté en `perfil_completo` o superior.

**Request:**
```json
{
  "tipo": "vacante",
  "destino_id": "uuid-de-la-vacante",
  "motivo": "Buen match en IT, empresa local"
}
```

**Response:** Derivación creada + estado del caso actualizado + evento en log.

---

#### B6 — `PATCH /api/casos/:id/derivaciones/:derivacion_id`
Actualiza el resultado de una derivación.

**Request:** `{ "estado": "aceptado" }`

**Lógica:** Si `aceptado` → propagar a caso como `insertado`. Si `rechazado` → caso vuelve a `perfil_completo`.

---

### GRUPO C — Matching extendido (mejoras sobre APIs existentes)

#### C1 — `GET /api/matching-offers` — agregar soporte de `perfil_id`

**Actualmente** recibe `isco_codes` y `skills` como arrays de strings.
**Nuevo parámetro opcional:** `perfil_id=uuid`

Si se pasa `perfil_id`, la API lee las skills confirmadas del perfil desde Supabase
y aplica el matching directamente, sin que el frontend tenga que pasar la lista de skills.

**Parámetro adicional:** `org_id` para priorizar vacantes del pool OE en el ranking.

---

#### C2 — `GET /api/matching-candidates` *(nueva)*
Ranking de candidatos de la cartera de una OE para una vacante dada.

**Request:** `GET /api/matching-candidates?vacante_id=X&org_id=Y`

**Response:**
```json
[
  {
    "caso_id": "uuid",
    "persona_nombre": "María García",
    "match": 84,
    "skills_ok": ["Python", "SQL"],
    "skills_gap": ["Docker"],
    "opt_in": true
  }
]
```

**Lógica:** Solo candidatos con `perfil_completo` o superior. Si la vacante es del pool OE de esa organización, incluir todos. Si es del pool MOL, solo candidatos con `opt_in=true`.

---

#### C3 — `GET /api/matching-occupations` *(nueva)*
Dado un perfil, devuelve ocupaciones ESCO compatibles ordenadas por match.

**Request:** `GET /api/matching-occupations?perfil_id=X`

**Response:**
```json
[
  {
    "occupation_uri": "http://data.europa.eu/esco/occupation/xxx",
    "occupation_label": "Técnico en sistemas",
    "isco_code": "3511",
    "match": 87,
    "skills_gap": ["Docker", "Kubernetes"],
    "ofertas_activas": 42
  }
]
```

---

### GRUPO D — Vacantes y cursos de la OE

#### D1 — `GET /api/vacantes-oe?org_id=X&estado=Y`
Lista vacantes del pool propio de la OE.

**Response:**
```json
[
  {
    "id": "uuid",
    "titulo": "Operario textil",
    "empresa": "Textil del Norte SA",
    "skills_requeridas": [{ "uri": "...", "label": "Costura", "peso": 0.8 }],
    "candidatos_compatibles": 12,
    "estado": "activa"
  }
]
```

---

#### D2 — `POST /api/vacantes-oe`
Crea una vacante a partir de descripción en lenguaje libre.

**Request:**
```json
{
  "org_id": "uuid",
  "titulo": "Operario textil",
  "empresa": "Textil del Norte SA",
  "descripcion": "Necesitamos una persona con experiencia en costura y corte de telas..."
}
```

**Response:** Vacante con skills ESCO extraídas automáticamente (mismo motor que el pipeline NLP).
La vacante queda en estado `borrador` hasta que la OE confirma el mapeo.

---

#### D3 — `POST /api/import-pool/personas`
Importa CSV/Excel de personas. Procesa y devuelve preview antes de confirmar.

**Request:** `multipart/form-data` con archivo CSV.

**Campos mínimos del CSV:** `nombre`, `dni`, `ultimo_trabajo`

**Response (preview):**
```json
{
  "total": 150,
  "validas": 142,
  "duplicadas": 5,
  "con_errores": 3,
  "preview": [
    { "nombre": "Juan García", "dni": "28xxx", "estado": "ok" },
    { "nombre": "Ana López", "dni": "", "estado": "error: falta DNI" }
  ]
}
```

**Confirmación:** `POST /api/import-pool/personas/confirmar?import_id=X`

---

#### D4 — `POST /api/import-pool/vacantes`
Importa CSV de vacantes. Mismo patrón que D3: preview + confirmación separada.

---

#### D5 — `POST /api/import-pool/cursos`
Importa CSV de cursos del catálogo. Mismo patrón.

---

### GRUPO E — Reportes y QR

#### E1 — `POST /api/reportes`
Genera un reporte PDF + token QR para un perfil.

**Request:**
```json
{
  "perfil_id": "uuid",
  "tipo": "generico",
  "ocupacion_uri": "http://data.europa.eu/esco/occupation/xxx"
}
```

**Response:**
```json
{
  "id": "uuid",
  "token": "tok_abc123",
  "url_qr": "https://mol.gob.ar/reporte/tok_abc123",
  "url_pdf": "https://storage.supabase.co/...",
  "validez_hasta": "2026-06-25T00:00:00Z"
}
```

**Nota:** La API `/api/compatibility-report` (GET) ya existe y funciona. Este endpoint es el POST que la genera desde un `perfil_id`. Evaluar si se puede extender el existente o crear uno nuevo.

---

### GRUPO F — KPIs operativos S2

#### F1 — `GET /api/kpis-oe?org_id=X`
KPIs del hub de la OE.

**Response:**
```json
{
  "personas_cartera": 312,
  "sin_diagnostico": 45,
  "vacantes_activas": 18,
  "atendidos_hoy": 7,
  "casos_sin_diagnostico": [
    { "caso_id": "uuid", "persona_nombre": "Juan García", "dias_sin_atencion": 12 }
  ],
  "derivaciones_sin_respuesta": [
    { "derivacion_id": "uuid", "persona_nombre": "Ana López", "empresa": "Textil SA", "dias": 5 }
  ]
}
```

---

## BLOQUE 3 — Pantallas UI (Sergio) y dependencias de APIs

### S1 — Mi Futuro Laboral

| Pantalla | Ruta | APIs que consume | Depende de | Estado UI |
|----------|------|-----------------|------------|-----------|
| S1-1 Landing | `/mi-futuro-laboral` | — | — | ✅ Existe (mejorar CTA) |
| S1-2 Onboarding | `/mi-futuro-laboral/onboarding` | — | — | ⬜ Por crear |
| S1-3 Captura (4 vías) | `/mi-futuro-laboral/perfil` | `A3, A4, A5` + skills existentes | A3-A5 | ⬜ Por crear |
| S1-4 Validar skills | `/mi-futuro-laboral/perfil/validar` | `A5` | A5 | ⬜ Por crear |
| S1-6 Resultados | `/mi-futuro-laboral/resultados` | `C1, C3` | C1, C3 | ⬜ Por crear |
| S1-7 Elegir destino | `/mi-futuro-laboral/resultados` (tab) | `/api/training-suggestions` | M4 fix | ⬜ Por crear |
| S1-8 Brecha + cursos | `/mi-futuro-laboral/brecha` | `/api/training-impact` | — | ⬜ Por crear |
| S1-9 PDF + QR | `/mi-futuro-laboral/reporte` | `E1` | E1 | ⬜ Por crear |

**MVP S1 sin dependencias de APIs nuevas:**
S1-1 (mejorar), S1-2 (solo routing), S1-3 parcial (Vías 1 y 2 con APIs existentes).

---

### S2 — Oficina de Empleo

| Pantalla | Ruta | APIs que consume | Depende de | Estado UI |
|----------|------|-----------------|------------|-----------|
| S2-1 Onboarding (import CSV) | `/oficina-empleo/onboarding` | `D3, D4, D5` | D3-D5 | ⚠️ Wireframe |
| S2-2 Hub + KPIs | `/oficina-empleo` | `F1` | F1 | ⚠️ Mejorar landing |
| S2-3 Cartera casos | `/oficina-empleo/cartera` | `B1` | B1 | ⬜ Por crear |
| S2-4 Crear caso | `/oficina-empleo/cartera/nueva` | `A1, A2, B2` | A1-A2, B2 | ⬜ Por crear |
| S2-5 Vista caso | `/oficina-empleo/cartera/[id]` | `B3, B4, A4, A5, C1, C3` | B3-B4 | ⬜ Por crear |
| S2-6 Derivar | (modal en S2-5) | `B5` | B5 | ⬜ Por crear |
| S2-7 Vacantes OE | `/oficina-empleo/vacantes` | `D1` | D1 | ⬜ Por crear |
| S2-8 Nueva vacante | `/oficina-empleo/vacantes/nueva` | `D2` | D2 | ⬜ Por crear |
| S2-9 Detalle vacante | `/oficina-empleo/vacantes/[id]` | `C2` | C2 | ⬜ Por crear |
| S2-10 Cursos catálogo | `/oficina-empleo/cursos` | `D5` | D5 | ⬜ Por crear |
| S2-11 Inteligencia local | `/oficina-empleo/inteligencia` | `/api/inteligencia-local` | — | ✅ Existe |
| S2-12 Generar PDF caso | (modal en S2-5) | `E1` | E1 | ⬜ Por crear |

---

### S3 — Empresas (modo activo)

| Pantalla | Ruta | APIs que consume | Depende de | Estado UI |
|----------|------|-----------------|------------|-----------|
| S3-1 QR (modo pasivo) | `/reporte/[token]` | `/api/compatibility-report` (GET) | — | ✅ Funciona |
| S3-2 Landing empresas | `/empresas` | — | — | ⬜ Por crear |
| S3-3 Dashboard empresa | `/empresas/dashboard` | (nueva API empresa) | Nueva API | ⬜ Por crear |
| S3-4 Mis vacantes | `/empresas/vacantes` | (nueva API empresa) | Nueva API | ⬜ Por crear |
| S3-5 Nueva vacante | `/empresas/vacantes/nueva` | `D2` adaptado | — | ⬜ Por crear |
| S3-6 Candidatos rankeados | `/empresas/vacantes/[id]` | `C2` con opt_in | C2 | ⬜ Por crear |
| S3-7 Perfiles de puesto | `/empresas/perfiles-puesto` | (nueva API empresa) | Nueva API | ⬜ Por crear |
| S3-8 Comparar candidatos | `/empresas/comparar` | `C2` | C2 | ⬜ Por crear |

**Nota S3 modo activo:** Requiere autenticación de empresa (cuenta). Es la fase más alejada del MVP. Se puede construir después de tener S1 y S2 funcionando.

---

## BLOQUE 4 — Fixes sobre lo ya desarrollado

Estos no requieren APIs nuevas — son mejoras al código existente.

### Fix 1 — Bug en `/reporte/[token]/page.tsx` *(URGENTE — Sergio)*
**Estado:** Parcialmente arreglado en `feature/si-sergio-ui` (sin commitear).

La API devuelve `{ report: data, estado: "..." }` pero el fetch anterior no manejaba `estado` en respuestas no-200. Ya corregido, falta commitear.

---

### Fix 2 — Persistir cambios de skills en `CompatibilityReport` *(Sergio + Gerardo)*
La UI de edición ya existe (`SkillsMapEditable`). Falta:
- **Sergio:** botón "Guardar análisis" que llame `PATCH /api/compatibility-report`
- **Gerardo:** confirmar que el endpoint PATCH acepta el nuevo `skills_requeridas` modificado

---

### Fix 3 — `transition_demand` incompleto en `/api/training-suggestions` *(Gerardo)*
`current_match` y `skills_gap` siempre devuelven `0` y `[]` (hay un TODO en el código).
Necesita cruzar `worker_skills` con las skills de cada ocupación trending.

---

### Fix 4 — Ranking `matching-offers` sin prioridad OE ni contexto geográfico *(Gerardo)*
El score actual es solo `cubiertas / totales`. Mejorar con:
- `+15%` si la vacante es del pool OE de la organización del usuario
- `+10%` si misma localidad, `+5%` si misma provincia

**Parámetros a agregar:** `org_id`, `user_provincia`

---

## BLOQUE 5 — Orden de implementación sugerido

### Sprint 1 — Desbloquear el modelo de datos (Gerardo, ~3 días)
1. Crear tablas: `personas`, `perfiles`, `perfil_skills`, `casos`, `derivaciones`, `eventos_caso`
2. Implementar APIs Grupo A (personas y perfiles) — A1 a A6
3. Implementar APIs Grupo B (casos) — B1 a B6
4. Fix 3 (transition_demand) y Fix 4 (ranking OE)

**Una vez que Sprint 1 esté listo, Sergio puede arrancar S2 completo.**

### Sprint 2 — S2 módulo casos (Sergio, ~5 días)
1. S2-3 Cartera de casos con búsqueda DNI/nombre
2. S2-4 Crear caso (form persona + skills iniciales)
3. S2-5 Vista de caso (2 columnas, tabs, estados)
4. S2-6 Derivar (modal)
5. S2-2 Hub mejorado con KPIs reales (F1)

### Sprint 3 — S2 vacantes + S1 MVP (Sergio, ~4 días)
1. S2-7/S2-8/S2-9 Vacantes de la OE (requiere D1, D2 de Gerardo)
2. S1-2/S1-3 Onboarding + captura (Vías 1 y 2, APIs ya existen)
3. S1-6 Resultados (C1 de Gerardo)
4. S1-9 Generar reporte PDF+QR (E1 de Gerardo)

### Sprint 4 — S1 completo + S2 imports (Sergio + Gerardo, ~3 días)
1. S1-7/S1-8 Destino + brecha + cursos
2. S2-1 Onboarding import CSV (D3, D4, D5 de Gerardo)
3. S2-10 Catálogo de cursos

### Sprint 5 — S3 modo activo (Sergio + Gerardo, ~5 días)
1. S3-2 Landing empresas
2. S3-5/S3-6 Vacante empresa + candidatos rankeados (C2)
3. S3-7/S3-8 Perfiles de puesto + comparar

---

## BLOQUE 6 — Preguntas para Gerardo

Antes de que Sergio empiece, necesitamos alinearnos en:

| # | Pregunta | Impacta en |
|---|----------|------------|
| Q1 | ¿`worker_profiles` reemplaza a `perfiles` o conviven? ¿Cuál es el schema actual? | Modelo de datos A3-A6 |
| Q2 | ¿`organizaciones` ya tiene tabla en Supabase? ¿Qué campos tiene? | Multi-tenancy S2 |
| Q3 | ¿El endpoint `POST /api/compatibility-report` puede recibir `perfil_id` directo o solo `skills[]`? | E1, S1-9 |
| Q4 | ¿La tabla `reportes_compatibilidad` tiene campo `expirado_at` o es manual? | S3 QR expiración |
| Q5 | ¿Querés que Sergio agregue Fix 4 (ranking OE) directamente en `matching-offers/route.ts`? | C1 |
| Q6 | ¿El onboarding import CSV es un flujo de una sola OE o multi-OE con selección? | D3-D5, S2-1 |

---

## Referencias

| Documento | Contenido |
|-----------|-----------|
| `docs/plan/S1_S2_S3_ESPECIFICACION_DETALLADA.md` | Especificación pantalla por pantalla |
| `MOL_Especificacion_Claude_Code.docx` | Documento funcional completo |
| `docs/plan/02_ARQUITECTURA_PANTALLAS.md` | Mapa de rutas P-01 a P-30 |
| `docs/plan/04_MODELO_DATOS.md` | Schema de datos existente |
| `docs/plan/09_ROADMAP.md` | Fases de producto |

---

> Próxima acción: Gerardo revisa Q1-Q6 y confirma schema antes de implementar Sprint 1.
