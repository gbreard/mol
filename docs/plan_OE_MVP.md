# OE — Módulos de Oficina de Empleo

**Versión:** MVP  
**Para:** Gerardo  
**Estado:** Listos para implementar  
**Ubicación en producción:** `https://mol-nextjs.vercel.app/oficina-empleo`  
**Repo / rama:** `feature/si-sergio-ui` → merge a `main` → deploy Vercel

---

## Alcance — Reemplazo completo de la sección OE

Estos módulos **reemplazan por completo** el contenido actual de `/oficina-empleo`.

**Lo que se elimina:**
- Landing actual (KPIs de casos, tablas de candidatos recientes, vacantes, cursos)
- Páginas: `/casos`, `/casos/[id]`, `/casos/nuevo`, `/onboarding`, `/perfil`, `/perfil-puesto`, `/ofertas`, `/benchmark`, `/formacion`, `/vacantes`, `/vacantes/nueva`
- APIs: `/api/oficina-empleo/caso-detalle`, `/api/oficina-empleo/casos-list`, `/api/oficina-empleo/dashboard`, `/api/oficina-empleo/registro`

**Lo que queda en `/oficina-empleo`:**

| Ruta | Módulo |
|------|--------|
| `/oficina-empleo` | Nueva landing — hub de 4 módulos |
| `/oficina-empleo/perfiles` | M1 — Perfil de Competencias |
| `/oficina-empleo/perfiles/nuevo` | M1 — Captura |
| `/oficina-empleo/perfiles/[id]` | M1 — Vista limpia |
| `/oficina-empleo/perfiles/matching` | M2 — Oportunidades Laborales |
| `/oficina-empleo/perfiles/futuro` | M3 — Futuro Laboral |
| `/oficina-empleo/dashboard-ejecutivo` | M4 — Inteligencia del Mercado Laboral |

---

## Landing `/oficina-empleo` — Nueva

La landing es el hub de acceso a los 4 módulos. Sin KPIs, sin tablas, sin gestión de casos.

### Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│  Oficina de Empleo                                              │
│  Herramientas para el técnico y el equipo de gestión            │
├──────────────────┬──────────────────┬──────────────────────────┤
│                  │                  │                           │
│  📋              │  🎯              │  🗺️                       │
│  Perfil de       │  Oportunidades   │  Futuro Laboral           │
│  Competencias    │  Laborales       │                           │
│                  │                  │  Analizá la brecha de     │
│  Capturá el      │  Encontrá las    │  skills y el plan de      │
│  perfil de       │  ocupaciones     │  transición para un       │
│  skills de un    │  compatibles     │  candidato hacia una      │
│  candidato con   │  con el perfil   │  ocupación objetivo       │
│  la taxonomía    │  del candidato   │                           │
│  ESCO            │  y la demanda    │  [Abrir →]                │
│                  │  real de MOL     │                           │
│  [Abrir →]       │                  │                           │
│                  │  [Abrir →]       │                           │
│                  │                  │                           │
├──────────────────┴──────────────────┴──────────────────────────┤
│                                                                 │
│  📊                                                             │
│  Inteligencia del Mercado Laboral                               │
│                                                                 │
│  Panorama territorial de la demanda de empleo — sectores,       │
│  ocupaciones, skills más pedidas y perfil de requerimientos     │
│  por provincia y período                                        │
│                                                                 │
│  [Abrir →]                                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Layout:** 3 cards en fila superior (M1, M2, M3) + 1 card ancha abajo (M4).  
M4 es más ancha porque es para una audiencia diferente (funcionarios / política).

### Archivo a modificar

`app/oficina-empleo/page.tsx` — reemplazar todo el contenido actual por el hub de 4 cards.

No se crea ningún componente nuevo — son cards estáticas con `Link` a cada módulo.

---

## Navegación interna

El flujo M1 → M2 → M3 se maneja con botones dentro de cada página:

```
Landing
  ↓  [Abrir →] en card M1
Perfil de Competencias (/perfiles)
  ↓  [+ Nuevo perfil]
/perfiles/nuevo  →  guarda  →  /perfiles/[id]
  ↓  [Oportunidades →]
Oportunidades Laborales (/perfiles/matching)
  ↓  [Ver en detalle] en una card
Futuro Laboral (/perfiles/futuro)
```

M4 es independiente — se accede directo desde la landing.

**Breadcrumb** (`OEBreadcrumb.tsx`) en cada pantalla:

| Pantalla | Breadcrumb |
|----------|------------|
| `/perfiles` | Oficina de Empleo > Perfil de Competencias |
| `/perfiles/nuevo` | Oficina de Empleo > Perfil de Competencias > Nuevo |
| `/perfiles/[id]` | Oficina de Empleo > Perfil de Competencias > [Nombre] |
| `/perfiles/matching` | Oficina de Empleo > Oportunidades Laborales |
| `/perfiles/futuro` | Oficina de Empleo > Futuro Laboral |
| `/dashboard-ejecutivo` | Oficina de Empleo > Inteligencia del Mercado |

---

## Índice de módulos

- [Módulo 1 — Perfil de Competencias](#módulo-1--perfil-de-competencias)
- [Módulo 2 — Oportunidades Laborales](#módulo-2--oportunidades-laborales)
- [Módulo 3 — Futuro Laboral](#módulo-3--futuro-laboral)
- [Módulo 4 — Inteligencia del Mercado Laboral](#módulo-4--inteligencia-del-mercado-laboral)

---

---

# Módulo 1 — Perfil de Competencias

**Referencia UI:** mol-nextjs.vercel.app/admin/skills

## Propósito

Módulo standalone para capturar el perfil de skills de un candidato.  
No depende del flujo de casos OE. Persiste en Supabase.  
Los perfiles guardados son insumo para el Módulo 2 (Oportunidades Laborales).

---

## Rutas

| Ruta relativa | URL completa | Pantalla |
|---------------|-------------|---------|
| `/oficina-empleo/perfiles/nuevo` | `mol-nextjs.vercel.app/oficina-empleo/perfiles/nuevo` | Pantalla 1 — Captura (dos paneles) |
| `/oficina-empleo/perfiles` | `mol-nextjs.vercel.app/oficina-empleo/perfiles` | Lista de perfiles guardados |
| `/oficina-empleo/perfiles/[id]` | `mol-nextjs.vercel.app/oficina-empleo/perfiles/[id]` | Pantalla 2 — Vista limpia del perfil |

---

## Lista de perfiles (`/perfiles`)

```
┌─────────────────────────────────────────────────────────────────┐
│  Perfiles de Competencias                    [+ Nuevo perfil]   │
├──────────────────────────────────────────────────────────────── │
│  🔍 Buscar por nombre o DNI...                                  │
├──────────────────────────────────────────────────────────────── │
│  Nombre              DNI           Competencias  Estado         │
├──────────────────────────────────────────────────────────────── │
│  María González      28.450.123    14            ● Validado     │
│  Jorge Ramírez       33.121.009     8            ○ Borrador     │
│  Ana López           41.887.220    11            ● Validado     │
│  ...                                                            │
└─────────────────────────────────────────────────────────────────┘
```

- Cada fila es clickeable → abre `/perfiles/[id]`
- Buscador filtra en tiempo real por nombre o DNI (client-side si la lista es chica, o `?search=` si es grande)
- Badge **● Validado** (verde) / **○ Borrador** (gris)
- Ordenado por `created_at DESC` por default
- Sin paginación en MVP (asumir volumen manejable por oficina)
- Botón `+ Nuevo perfil` → `/perfiles/nuevo`

---

## Pantalla 1 — Captura de Skills

Layout de dos paneles:

```
┌─────────────────────────┬──────────────────────────┐
│  PANEL IZQUIERDO        │  PANEL DERECHO           │
│  (captura)              │  (perfil acumulado)      │
│                         │                          │
│  [V1][V2][V3]           │  OCUPACIONES             │
│                         │    • Albañil (7112)      │
│  Vía activa con         │                          │
│  buscador / selector    │  SKILLS ESENCIALES       │
│  → click agrega al      │    • Aplicar mortero [x] │
│    panel derecho        │    • Leer planos     [x] │
│                         │                          │
│                         │  SKILLS TÉCNICAS         │
│                         │    • Soldadura  ███  [x] │
│                         │                          │
│                         │  HABILIDADES DIGITALES   │
│                         │    • Excel — Medio   [x] │
│                         │                          │
│                         │  TRANSVERSALES           │
│                         │  CONOCIMIENTOS           │
│                         │  IDIOMAS                 │
│                         │  OTRAS                   │
│                         │                          │
│                         │  ── 12 competencias ──   │
│                         │  [Nombre]  [DNI]         │
│                         │  [Guardar perfil]        │
└─────────────────────────┴──────────────────────────┘
```

---

## Las tres vías de captura (panel izquierdo)

> - **Vía 1** = lo que eras (tu rol/ocupación)  
> - **Vía 2** = lo que hacías (tareas, actividades)  
> - **Vía 3** = lo que manejás (herramientas, tecnologías, idiomas)

---

### Vía 1 — Ocupación (`OccupationSkillPicker`)

**Pregunta al usuario:** "¿En qué trabajaste? ¿Cuál era tu ocupación?"

**Flujo:**
1. Input de texto → `GET /api/occupations/search?q=...&limit=10`
2. Lista de ocupaciones sugeridas (label + ISCO code)
3. Click en ocupación → `GET /api/occupations/skills?id=...`
4. Muestra skills esenciales (pre-seleccionadas ✓) y opcionales (desmarcadas) con checkboxes
5. Botón "Agregar al perfil" → skills chequeadas van al panel derecho
6. Puede repetir con múltiples ocupaciones — el perfil se acumula

**Reglas:**
- Skill ya en perfil: checkbox disabled + ícono ✓
- "Seleccionar todas" como acción secundaria
- Ocupaciones ya agregadas aparecen como chips sobre el buscador

**APIs:**
- `GET /api/occupations/search?q={texto}&limit=10` → `{ results: [{id, label, isco_code}] }`
- `GET /api/occupations/skills?id={id}` → `{ occupation, essential: [{skill_uri, skill_label, type, L1, L2, total}], optional: [...] }`

---

### Vía 2 — Tareas que sabés hacer (`TaskSkillSearch`)

**Pregunta al usuario:** "¿Qué otras tareas o actividades sabés hacer?"

Dos modos en un mismo componente — toggle visible entre ellos:

**Modo búsqueda rápida** (default)
- Input corto con autocomplete, debounce 300ms, mínimo 2 caracteres
- `GET /api/skills-search?q=...&limit=15`
- Click en resultado → se agrega al perfil instantáneamente
- Sin resultados: "No encontramos esa habilidad, probá con otras palabras"

**Modo relato libre**
- Textarea — el técnico escribe un párrafo de experiencia
- Ejemplo: "Trabajé 5 años en una fábrica haciendo soldadura y coordinando al equipo"
- Botón "Extraer habilidades" → `POST /api/skills-extract-from-text`
- Devuelve lista de skills con confianza: `high / medium / low`
- Lista para confirmar (✓) o descartar (✗) cada una individualmente

**Reglas:**
- Skills ya en perfil no se pueden re-agregar (aparecen con ✓ deshabilitado)

**APIs:**
- `GET /api/skills-search?q={texto}&limit=15` → `{ results: [{uri, label, type, description}] }`
- `POST /api/skills-extract-from-text` body: `{ text }` → `{ results: [{id, label, type, L1, L2, confidence, matchedKeyword}] }`

---

### Vía 3 — Otras habilidades (`StructuredSkills`)

**Pregunta al usuario:** "¿Manejás algún idioma, programa o herramienta específica?"

Selección estructurada por categoría — lista fija, sin llamadas a API.

| Categoría | Opciones | Nivel |
|-----------|----------|-------|
| **Idiomas** | Inglés / Portugués / Francés / Italiano / Alemán / Otro | Básico / Intermedio / Avanzado / Nativo |
| **Herramientas ofimáticas** | Excel / Word / PowerPoint / Otro | Básico / Intermedio / Avanzado |
| **Software / Programación** | Python / JavaScript / SAP / AutoCAD / Photoshop / Otro (texto libre) | Básico / Intermedio / Avanzado |

**Resultado por entrada:**
```
{ label: 'Inglés — Avanzado',    type: 'knowledge', source: 'estructurado', category: 'idioma' }
{ label: 'Excel — Intermedio',   type: 'skill',     source: 'estructurado', category: 'herramienta' }
{ label: 'Python — Avanzado',    type: 'skill',     source: 'estructurado', category: 'software' }
```

**Reglas:**
- Puede agregar múltiples entradas de cada categoría
- No permite duplicar la misma combinación (ej: dos veces "Inglés — Avanzado")

---

## Panel derecho — Perfil acumulado (`SkillProfilePanel`)

### Clasificación por sección

| Sección | Condición de inclusión |
|---------|------------------------|
| **Ocupaciones** | Guardadas aparte — `{ id, label, isco_code }` |
| **Skills esenciales** | `source='ocupacion'` + `essential_for_occupation=true` |
| **Skills técnicas** | `type='skill'` + `L1` en S1, S2, S3, S4, S6, S7, S8 |
| **Habilidades digitales** | `L1='S5'` ó `source='estructurado'` + `category='herramienta'` ó `category='software'` |
| **Transversales** | `L1` en T1, T2, T3, T4, T5, T6 |
| **Conocimientos** | `type='knowledge'` |
| **Idiomas** | `source='estructurado'` + `category='idioma'` |
| **Otras** | Sin `L1` o no clasificable (fallback) |

**Nota sobre L1:** los datos de `skills_searchable.json` tienen `L1` para ~14.000 skills. 2.703 no tienen L1 — esas van a "Otras".

### Indicadores de ponderación (visibles por skill)

Barra de demanda en mercado (campo `market_frequency` = campo `total` de skills_searchable.json):
- `███` **Alta**: `market_frequency > 100`
- `██` **Media**: `market_frequency > 30`
- `█` **Baja**: el resto

Badge `[esencial]` para skills con `essential_for_occupation = true`.

### Reglas del panel
- Secciones vacías se ocultan automáticamente
- Botón `[x]` por skill para remover
- Deduplicación por `uri` (o `label` normalizado lowercase si no hay uri)
- Contador total: "N competencias"

### Datos de persona + guardar (parte inferior del panel)
- Campo: Nombre (obligatorio)
- Campo: DNI (obligatorio)
- Botón "Guardar perfil" → POST a Supabase → redirige a `/perfiles/[id]`

---

## Pantalla 2 — Vista limpia del perfil (`/perfiles/[id]`)

Solo lectura. Presentable. Para mostrar al candidato, imprimir o consumo de otros módulos.

```
┌─────────────────────────────────────────┐
│  María González  · DNI 28.450.123       │
│  12 competencias · 2 ocupaciones        │
│                              ┌────────┐ │
│  OCUPACIONES                 │  [QR]  │ │
│  [Albañil]  [Electricista]   │        │ │
│                              └────────┘ │
├─────────────────────────────────────────┤
│  SKILLS ESENCIALES              (6)     │
│  ● Soldadura                            │
│  ● Leer planos                          │
│  ● Aplicar mortero  ...                 │
├─────────────────────────────────────────┤
│  HABILIDADES DIGITALES          (2)     │
│  ● Excel — Intermedio                   │
│  ● AutoCAD — Básico                     │
├─────────────────────────────────────────┤
│  IDIOMAS                        (1)     │
│  ● Inglés — Avanzado                    │
├─────────────────────────────────────────┤
│  Generado por MOL · 03/04/2026          │
├─────────────────────────────────────────┤
│  [← Editar]  [Imprimir]  [Matching →]  │
└─────────────────────────────────────────┘
```

### Acciones de la pantalla

| Botón | Acción |
|-------|--------|
| **Editar perfil** | Carga el perfil en Pantalla 1 con datos pre-cargados |
| **Validar perfil** | Cambia `estado` de `borrador` → `validado` (PATCH API) |
| **Imprimir** | `window.print()` |
| **Oportunidades →** | Navega al Módulo 2 con `?perfil_id=[id]` pre-cargado |

**Estado del perfil:**
- Perfil nuevo: badge gris `Borrador`
- Perfil validado: badge verde `Validado · 03/04/2026`
- Una vez validado el botón cambia a "Quitar validación" (permite revertir)

---

### QR e impresión

**QR:**
- Librería: `qrcode.react`
- Contenido: `https://mol-nextjs.vercel.app/oficina-empleo/perfiles/[id]`
- Tamaño: 80×80px

**Impresión:**
- `window.print()` con `@media print`: ocultar botones y sidebar, mostrar solo contenido + QR

---

## Modelo de datos

### `SelectedSkill`

```typescript
interface SelectedSkill {
  uri: string
  label: string
  type: 'skill' | 'knowledge'
  L1: string
  L2: string
  source: 'ocupacion' | 'busqueda' | 'estructurado'
  category?: 'idioma' | 'herramienta' | 'software'
  essential_for_occupation: boolean
  market_frequency: number
}
```

### `SkillCaptureState`

```typescript
interface SkillCaptureState {
  nombre: string
  dni: string
  ocupaciones: { id: string; label: string; isco_code: string }[]
  skills: SelectedSkill[]
}
```

---

## Persistencia — Supabase

### Tabla nueva: `perfiles_skills`

```sql
CREATE TABLE perfiles_skills (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre       text NOT NULL,
  dni          text NOT NULL,
  ocupaciones  jsonb NOT NULL DEFAULT '[]',
  skills       jsonb NOT NULL DEFAULT '[]',
  estado       text NOT NULL DEFAULT 'borrador',  -- 'borrador' | 'validado'
  validado_at  timestamptz,
  created_at   timestamptz DEFAULT now(),
  updated_at   timestamptz DEFAULT now()
);
```

### APIs nuevas a crear

| Endpoint | Método | Body / Params | Respuesta |
|----------|--------|---------------|-----------|
| `/api/oficina-empleo/perfiles` | POST | `{ nombre, dni, ocupaciones, skills }` | `{ id, nombre, dni, estado }` |
| `/api/oficina-empleo/perfiles` | GET | `?search=` | `[{ id, nombre, dni, estado, validado_at, created_at }]` |
| `/api/oficina-empleo/perfiles/[id]` | GET | — | perfil completo |
| `/api/oficina-empleo/perfiles/[id]` | PATCH | `{ estado }` | `{ id, estado, validado_at }` |
| `/api/oficina-empleo/perfiles/[id]` | PUT | `{ nombre, dni, ocupaciones, skills }` | perfil actualizado |

---

## APIs existentes que se reutilizan

| Endpoint | Archivo | Función |
|----------|---------|---------|
| `GET /api/occupations/search` | `app/api/occupations/search/route.ts` | Buscar ocupaciones |
| `GET /api/occupations/skills` | `app/api/occupations/skills/route.ts` | Skills de una ocupación |
| `GET /api/skills-search` | `app/api/skills-search/route.ts` | Autocomplete skills |
| `POST /api/skills-extract-from-text` | `app/api/skills-extract-from-text/route.ts` | Extraer skills de texto |

---

## Archivos a crear

| Archivo | Descripción |
|---------|-------------|
| `app/oficina-empleo/perfiles/nuevo/page.tsx` | Pantalla 1 — captura dos paneles |
| `app/oficina-empleo/perfiles/page.tsx` | Lista de perfiles guardados |
| `app/oficina-empleo/perfiles/[id]/page.tsx` | Pantalla 2 — vista limpia |
| `components/oficina-empleo/OccupationSkillPicker.tsx` | Vía 1 |
| `components/oficina-empleo/TaskSkillSearch.tsx` | Vía 2 |
| `components/oficina-empleo/StructuredSkills.tsx` | Vía 3 |
| `components/oficina-empleo/SkillProfilePanel.tsx` | Panel derecho |
| `components/oficina-empleo/useSkillCapture.ts` | Hook de estado compartido |
| `app/api/oficina-empleo/perfiles/route.ts` | POST + GET lista |
| `app/api/oficina-empleo/perfiles/[id]/route.ts` | GET + PATCH + PUT por ID |

**Código base reutilizable:** `components/oficina-empleo/SkillCapturePanel.tsx`

---

## Dependencias npm

```bash
npm install qrcode.react
```

---

## Pendiente para versiones futuras (Módulo 1 — Perfil de Competencias)

- URL pública del perfil (para que el QR sea escaneable por empleadores)
- Nivel de dominio por skill (básico/intermedio/avanzado)
- Vía formación / título educativo
- Validación institucional de skills

---

---

# Módulo 2 — Oportunidades Laborales

**Depende de:** Módulo 1 — Perfil de Competencias (`perfiles_skills`)

## Propósito

Dado un perfil del Módulo 1, mostrar las ocupaciones ESCO más compatibles con dos dimensiones:

- **Match ESCO** — cuántas skills esenciales de la taxonomía tiene el candidato
- **Demanda real MOL** — cuántas ofertas hay en Argentina para esa ocupación y qué skills pide el mercado

---

## Ruta

| Ruta | Pantalla |
|------|----------|
| `/oficina-empleo/perfiles/matching` | `mol-nextjs.vercel.app/oficina-empleo/perfiles/matching` |

**Entry point:** botón "Oportunidades →" de `mol-nextjs.vercel.app/oficina-empleo/perfiles/[id]` → navega con `?perfil_id=xxx`.

---

## Patrón de UI

Igual al tab "Ocupacion" de `/admin/skills`: selector arriba → contenido abajo.

| Tab "Ocupacion" | Módulo 2 |
|-----------------|----------|
| Selector de ocupación ESCO | Selector de persona (`perfiles_skills`) |
| Contenido: skills de esa ocupación | Contenido: ocupaciones compatibles con su perfil |

---

## UI/UX — Pantalla completa

### Estado inicial

```
┌─────────────────────────────────────────────────────────────┐
│  🎯  Matching de Perfil con Ocupaciones                     │
│  Seleccioná un perfil para ver ocupaciones compatibles      │
│  con sus competencias y demanda real del mercado            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Persona                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔍  Buscar por nombre o DNI...               [▾]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            👤                                       │   │
│  │     Seleccioná una persona                          │   │
│  │     Buscá por nombre o DNI para ver sus             │   │
│  │     ocupaciones compatibles                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Dropdown del selector

```
  ┌─────────────────────────────────────────────────────┐
  │  🔍  gonza                                    [▾]   │
  └─────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────┐
  │  3 perfiles encontrados                             │
  ├─────────────────────────────────────────────────────┤
  │  María González       DNI 28.450.123                │
  │  14 competencias · Albañil, Electricista  ● Validado│
  ├─────────────────────────────────────────────────────┤
  │  Jorge González       DNI 33.121.009                │
  │  8 competencias · Vendedor               ○ Borrador │
  ├─────────────────────────────────────────────────────┤
  │  Ana González         DNI 41.887.220                │
  │  11 competencias · Cajera, Administrativa ● Validado│
  └─────────────────────────────────────────────────────┘
```

### Ficha activa (persona seleccionada)

```
  ┌─────────────────────────────────────────────────────┐
  │  👤  María González · DNI 28.450.123           [×]  │
  │  14 competencias · Albañil, Electricista            │
  │  ● Validado · 03/04/2026                            │
  └─────────────────────────────────────────────────────┘
```

### Lista de resultados

```
┌──────────────────────────────────────────────────────────────┐
│  Ocupaciones compatibles  (38 encontradas)                   │
│                                      Ordenar: [Match% ▾]    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1.  Albañil                                   ISCO 7112     │
│      ████████████████░░░░  87%                              │
│      13/15 esenciales · +3 opcionales · gap: 1              │
│      🟢 12 ofertas en MOL                                   │
│      [▼ Ver análisis completo]                              │
│                                                              │
│  2.  Operario general de construcción          ISCO 7119     │
│      ██████████████░░░░░░  74%                              │
│      11/15 esenciales · +1 opcional · gap: 4                │
│      🟢 7 ofertas en MOL                                    │
│      [▼ Ver análisis completo]                              │
│                                                              │
│  3.  Instalador de revestimientos              ISCO 7122     │
│      ████████████░░░░░░░░  63%                              │
│      gap: 5 · ⚪ Sin ofertas activas                         │
│      [▼ Ver análisis completo]                              │
│                                                              │
│  4.  Pintor de obra                            ISCO 7131     │
│      ██████████░░░░░░░░░░  51%                              │
│      gap: 7 · 🟡 2 ofertas en MOL                           │
│      [▼ Ver análisis completo]                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Badge de ofertas:** 🟢 ≥5 · 🟡 1–4 · ⚪ sin ofertas  
**Barra:** verde ≥80% · amarilla 50–79% · roja <50%

### Panel expandido (uno a la vez, inline)

```
┌──────────────────────────────────────────────────────────────┐
│  1.  Albañil                                   ISCO 7112     │
│      ████████████████░░░░  87%   🟢 12 ofertas en MOL       │
│      [▲ Cerrar]                                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐  ┌───────────────────────────┐   │
│  │  GAP ESCO            │  │  MERCADO REAL (MOL)        │   │
│  │  Skills que le faltan│  │  Qué pide Argentina        │   │
│  ├──────────────────────┤  ├───────────────────────────┤   │
│  │  ● Armado andamios   │  │  ✓ Aplicar mortero  92%   │   │
│  │    [esencial]        │  │  ✓ Leer planos      87%   │   │
│  │                      │  │  ✓ Albañilería      81%   │   │
│  │  1 skill faltante    │  │  ✓ Herram. manuales 74%   │   │
│  │                      │  │  ✗ Armado andamios  68%   │   │
│  │                      │  │                           │   │
│  │                      │  │  ✓ candidato la tiene     │   │
│  │                      │  │  ✗ candidato no la tiene  │   │
│  └──────────────────────┘  └───────────────────────────┘   │
│                                                              │
│  Ofertas disponibles              [Ver las 12 ofertas →]    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Ayudante albañil · Constructora XYZ · CABA · 3d      │ │
│  │  Oficial albañil · Empresa ABC · Bs As · 1sem         │ │
│  │  Albañil · Constructora Norte · Córdoba · 2sem        │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Gap ESCO:** skills esenciales de la taxonomía que faltan. Si gap=0: `✓ Perfil completo`.  
**Mercado real:** top 5 skills más pedidas en ofertas reales (`getOccupationMOLProfile`), con frecuencia y si el candidato las tiene.  
**Ofertas:** primeras 3 de `getOfertasByIsco()`. Botón abre `OfertasOcupacionModal` (existe).

---

## Lógica de matching

```typescript
const profileUris = new Set(perfil.skills.map(s => s.uri))

for (const [id, occ] of Object.entries(occupationsData)) {
  const essential = occ.essential_skills ?? []
  const optional  = occ.optional_skills  ?? []

  const essentialCovered = essential.filter(s => profileUris.has(s.uri)).length
  const optionalCovered  = optional.filter(s => profileUris.has(s.uri)).length
  const essentialTotal   = essential.length

  if (essentialCovered === 0) continue

  const matchScore = essentialTotal > 0
    ? Math.round((essentialCovered / essentialTotal) * 100)
    : 0

  const gapSkills = essential
    .filter(s => !profileUris.has(s.uri))
    .map(s => ({ uri: s.uri, label: s.label }))

  matches.push({
    id, label, isco, matchScore,
    essentialTotal, essentialCovered, optionalCovered,
    gapCount: gapSkills.length, gapSkills
  })
}
```

Matching corre en el cliente con `occupation_full_detail.json`.

---

## Carga de datos — estrategia

```
AL CARGAR LA PÁGINA:
  → getOfertasCountByIsco()  (una vez, aplica a todas las cards)
  → Si ?perfil_id en URL → cargar perfil directo

AL SELECCIONAR PERSONA:
  → GET /api/oficina-empleo/perfiles/[id]
  → fetch /data/occupation_full_detail.json (si no está en memoria)
  → useMemo calcula matchingOccupations

AL EXPANDIR UNA CARD (lazy + cache):
  → getOccupationMOLProfile(esco_uri)
  → getOfertasByIsco(isco_code, limit=3)
  → cachear en molProfiles[id] y ofertasPreview[id]
```

---

## Ordenamiento

| Opción | Lógica |
|--------|--------|
| Mejor match (default) | `matchScore DESC`, desempate `gapCount ASC` |
| Menor gap | `gapCount ASC`, desempate `matchScore DESC` |
| Más ofertas | `ofertasCount DESC`, desempate `matchScore DESC` |
| Alfabético | `label ASC` |

---

## APIs — todas ya existen

| Endpoint / Función | Cuándo |
|--------------------|--------|
| `GET /api/oficina-empleo/perfiles?search=...` | Selector de persona |
| `GET /api/oficina-empleo/perfiles/[id]` | Cargar perfil |
| `getOfertasCountByIsco()` | Al cargar página |
| `getOccupationMOLProfile(esco_uri)` | Al expandir card (lazy) |
| `getOfertasByIsco(isco_code, 3)` | Al expandir card (lazy) |
| `OfertasOcupacionModal` | Botón "Ver todas" |

**No se crea ninguna API nueva.**

---

## Archivos a crear

| Archivo | Descripción |
|---------|-------------|
| `app/oficina-empleo/perfiles/matching/page.tsx` | Página principal |
| `components/oficina-empleo/PersonaSelector.tsx` | Selector con buscador (patrón OccupationDetail) |
| `components/oficina-empleo/OccupationMatchCard.tsx` | Card con barra + panel expandible |

**Código reutilizable:**
- `components/OccupationDetail.tsx` → patrón del selector
- `components/MySkillsSearch.tsx` → lógica matching + UI cards
- `components/OfertasOcupacionModal.tsx` → modal de ofertas (sin cambios)
- `lib/supabase.ts` → `getOfertasCountByIsco`, `getOccupationMOLProfile`, `getOfertasByIsco`

---

## Estado React

```typescript
const [searchTerm, setSearchTerm]         = useState('')
const [perfilesList, setPerfilesList]     = useState<PerfilResumen[]>([])
const [perfilId, setPerfilId]             = useState<string | null>(null)
const [perfil, setPerfil]                 = useState<PerfilSkills | null>(null)
const [occupationsData, setOccData]       = useState<OccupationFullDetailIndex | null>(null)
const [ofertasCount, setOfertasCount]     = useState<Record<string, number>>({})
const [sortBy, setSortBy]                 = useState<'match'|'gap'|'ofertas'|'alpha'>('match')
const [expandedId, setExpandedId]         = useState<string | null>(null)
const [molProfiles, setMolProfiles]       = useState<Record<string, OccupationMOLProfileData>>({})
const [ofertasPreview, setOfertasPreview] = useState<Record<string, OfertaPorOcupacion[]>>({})
const [modalIsco, setModalIsco]           = useState('')
const [showModal, setShowModal]           = useState(false)
```

---

## Pendiente para versiones futuras (Módulo 2 — Oportunidades Laborales)

- Filtro por sector / familia ISCO
- Exportar lista de matches a PDF
- Guardar ocupación sugerida en el perfil (`ocupacion_sugerida` en `perfiles_skills`)
- Contexto geográfico en el panel expandido (provincias con más ofertas)
- Rango salarial promedio por ocupación

---

---

# Módulo 3 — Futuro Laboral

**Depende de:** Módulo 1 — Perfil de Competencias + Módulo 2 — Oportunidades Laborales (lógica de matching, datos en memoria)

## Propósito

El técnico elige una persona y una ocupación objetivo — ya sea una de sus mejores opciones actuales o un rumbo completamente nuevo. El módulo muestra qué tiene, qué le falta, cuánto vale en el mercado lo que le falta, y qué caminos intermedios puede recorrer.

Está basado en `OccupationCompare` (tab "Comparar" de `/admin/skills`) pero reemplaza "Ocupación A" por el perfil real de la persona y suma los datos de mercado de MOL.

---

## Ruta

| Ruta | Pantalla |
|------|----------|
| `/oficina-empleo/perfiles/futuro` | `mol-nextjs.vercel.app/oficina-empleo/perfiles/futuro` |

**Entry points:**
- Botón "Ver en detalle" en una card de `mol-nextjs.vercel.app/oficina-empleo/perfiles/matching` → llega con `?perfil_id=xxx&occ_id=yyy`
- Acceso directo → elige persona y ocupación desde cero

---

## UI/UX — Pantalla completa

### Estado vacío

```
┌─────────────────────────────────────────────────────────────┐
│  🗺️  Futuro Laboral                                         │
│  Elegí una persona y una ocupación objetivo para ver        │
│  el plan de transición laboral                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Persona                    Ocupación objetivo              │
│  ┌───────────────────────┐  ┌───────────────────────────┐  │
│  │ 🔍 Nombre o DNI... [▾]│  │ [Mis matches] [Otro rumbo]│  │
│  └───────────────────────┘  │  Seleccioná una persona   │  │
│                             │  primero                  │  │
│                             └───────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Seleccioná una persona y una ocupación objetivo    │   │
│  │  para ver el plan de transición                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

El selector de ocupación está deshabilitado hasta que haya una persona. Una vez elegida la persona, se habilita con los matches ya calculados.

---

### Selector de persona (igual al Módulo 2 — Oportunidades Laborales)

```
  Persona
  ┌─────────────────────────────────────────────────────┐
  │  👤  María González · DNI 28.450.123           [×]  │
  │  14 competencias · Albañil, Electricista            │
  │  ● Validado · 03/04/2026                            │
  └─────────────────────────────────────────────────────┘
```

---

### Selector de ocupación — dos modos

**Modo "Mis matches"** (default una vez que hay persona):

```
  Ocupación objetivo
  ┌─────────────────────────────────────────────────────┐
  │  [Mis matches ●]  [Otro rumbo]                      │
  ├─────────────────────────────────────────────────────┤
  │  Mejores matches de María González                  │
  │                                                     │
  │  Albañil              ISCO 7112  ████████████  87%  │
  │  Op. construcción     ISCO 7119  ██████████░░  74%  │
  │  Inst. revestimientos ISCO 7122  █████████░░░  63%  │
  │  Pintor de obra       ISCO 7131  ███████░░░░░  51%  │
  │  Techista             ISCO 7121  ██████░░░░░░  48%  │
  │  ...  (top 15, scrollable)                          │
  └─────────────────────────────────────────────────────┘
```

Reutiliza `matchingOccupations` del Módulo 2 (Oportunidades Laborales) — ya calculado en memoria si la persona ya fue cargada. Si no, corre el mismo `useMemo`. Sin query adicional.

**Modo "Otro rumbo"** (el candidato quiere algo distinto):

```
  Ocupación objetivo
  ┌─────────────────────────────────────────────────────┐
  │  [Mis matches]  [Otro rumbo ●]                      │
  ├─────────────────────────────────────────────────────┤
  │  🔍  electricista...                                │
  ├─────────────────────────────────────────────────────┤
  │  Electricista domiciliario   ISCO 7411              │
  │  Electricista industrial     ISCO 7412              │
  │  Técnico electricista        ISCO 7421              │
  └─────────────────────────────────────────────────────┘
```

Búsqueda libre en las ~3.000 ocupaciones ESCO. Sin filtro de match mínimo — cualquier ocupación es válida aunque el match sea bajo o nulo.

**Ficha activa** (una vez elegida la ocupación, igual en ambos modos):

```
  ┌─────────────────────────────────────────────────────┐
  │  ⚡  Electricista domiciliario                  [×] │
  │  ISCO 7411 · 14 esenciales · 8 opcionales           │
  └─────────────────────────────────────────────────────┘
```

---

### Banner de situación

Aparece una vez que persona y ocupación están seleccionadas.

```
┌─────────────────────────────────────────────────────────────┐
│  María González  →  Electricista domiciliario               │
│                                                             │
│  ┌──────────────────────────┐  ┌────────────────────────┐  │
│  │  COMPATIBILIDAD          │  │  DEMANDA EN MOL         │  │
│  │  ████████░░░░░  63%      │  │  🟢 18 ofertas activas  │  │
│  │  9 de 14 esenciales      │  │  [Ver las 18 ofertas →] │  │
│  │  5 skills a cubrir       │  │                         │  │
│  └──────────────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

Barra coloreada: verde ≥70% · amarilla 40–69% · roja <40% (igual que `OccupationCompare`).
Badge de ofertas con botón que abre `OfertasOcupacionModal` directo.

---

### Panel 1 — Lo que ya tiene ✅

```
┌─────────────────────────────────────────────────────────────┐
│  ✅  Lo que ya tiene  (9 skills)                            │
│  Del perfil del candidato, requeridas por la ocupación      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ESENCIALES PARA LA OCUPACIÓN  (6)                         │
│  ★  Leer planos de construcción          ███ Alta demanda  │
│  ★  Herramientas manuales                ███ Alta demanda  │
│  ★  Trabajo en altura                    ██  Media demanda │
│  ★  Interpretación de esquemas           ██  Media demanda │
│  ★  Seguridad laboral                    ██  Media demanda │
│  ★  Albañilería básica                   █   Baja demanda  │
│                                                             │
│  OPCIONALES PARA LA OCUPACIÓN  (3)                         │
│  ○  Trabajo en equipo                    ███ Alta demanda  │
│  ○  Soldadura básica                     ██  Media demanda │
│  ○  Aplicar mortero                      █   Baja demanda  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Fuente de la barra de demanda:** `market_frequency` de cada `SelectedSkill` — guardada en el perfil del Módulo 1 (Perfil de Competencias). Sin query adicional.

Equivale a `gapAnalysis.shared` de `OccupationCompare` pero comparando perfil real vs ocupación.

---

### Panel 2 — Lo que necesita aprender 📚

```
┌─────────────────────────────────────────────────────────────┐
│  📚  Lo que necesita aprender  (5 skills)                   │
│  Requeridas por la ocupación, ausentes en el perfil         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIORIDAD ALTA — Esenciales para la ocupación  (3)        │
│  ★  Instalaciones eléctricas      pedida en 94% de ofertas │
│  ★  Normativa eléctrica           pedida en 87% de ofertas │
│  ★  Circuitos de baja tensión     pedida en 71% de ofertas │
│                                                             │
│  PRIORIDAD MEDIA — Opcionales para la ocupación  (2)       │
│  ○  Pruebas de aislamiento        pedida en 58% de ofertas │
│  ○  Conexión de tableros          pedida en 52% de ofertas │
│                                                             │
│  (si skill no aparece en MOL → solo badge [ESCO])          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Fuente del "pedida en X%":** `getOccupationMOLProfile(esco_uri)` — cargado lazy al seleccionar la ocupación. Cruza las skills del gap con `MOLSkillAggregated.frequency`.

Equivale a `gapAnalysis.gapEssential` + `gapAnalysis.gapOptional` de `OccupationCompare`.

---

### Panel 3 — Conocimientos 📖

```
┌──────────────────────────────┬──────────────────────────────┐
│  Ya tiene  (4)               │  Necesita adquirir  (3)      │
├──────────────────────────────┼──────────────────────────────┤
│  ○ Física básica             │  ○ Electrotecnia             │
│  ○ Matemática aplicada       │  ○ Normativa NEC             │
│  ○ Materiales de construc.   │  ○ Diagramas eléctricos      │
│  ○ Seguridad e higiene       │                              │
└──────────────────────────────┴──────────────────────────────┘
```

Equivale a `sharedKnowledge` / `gapKnowledge` de `OccupationCompare`. Datos de `occupationsData` — sin query.

---

### Panel 4 — Skills transferibles 🔄

```
┌─────────────────────────────────────────────────────────────┐
│  🔄  Skills transferibles  (5)                              │
│  Las tiene pero la ocupación objetivo no las requiere.      │
│  Pueden ser útiles para otras ocupaciones del área.         │
├─────────────────────────────────────────────────────────────┤
│  ○  Aplicar mortero    ○  Encofrado    ○  Nivelación        │
│  ○  Armado estructuras ○  Colocación cerámicos             │
└─────────────────────────────────────────────────────────────┘
```

Equivale a `gapAnalysis.transferable` de `OccupationCompare`. Muestra máximo 10, con "+N más" si hay más.

---

### Panel 5 — Caminos alternativos 🪜

Solo aparece si `gapCount ≥ 3`. Ocupa la parte inferior.

```
┌─────────────────────────────────────────────────────────────┐
│  🪜  Caminos alternativos — menor gap, misma área           │
│  Ocupaciones similares que puede alcanzar antes             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Ayudante electricista       ISCO 7412                      │
│  ████████████████████  94%   gap: 1  · 🟡 4 ofertas        │
│  [Elegir como objetivo →]                                   │
│                                                             │
│  Técnico en instalaciones    ISCO 7422                      │
│  ████████████████░░░░  79%   gap: 3  · 🟢 9 ofertas        │
│  [Elegir como objetivo →]                                   │
│                                                             │
│  Operario de mantenimiento   ISCO 7233                      │
│  ██████████████░░░░░░  72%   gap: 3  · 🟢 6 ofertas        │
│  [Elegir como objetivo →]                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Fuente:** `occ.similar` de `occupation_full_detail.json` — ya en memoria. Se cruza con el perfil de la persona para calcular match y gap de cada alternativa. Badge de ofertas desde `ofertasCountMap` — ya cargado.

Click en "Elegir como objetivo →": recarga el módulo con esa ocupación como nuevo objetivo, manteniendo la persona seleccionada. El modo del selector pasa automáticamente a "Otro rumbo" (ya que puede no estar entre los matches principales).

---

## Lógica de gap analysis

Adaptación directa de `OccupationCompare.gapAnalysis` — reemplazando `allSkillsA` (skills de ocupación A) por `perfil.skills` (skills reales del candidato):

```typescript
const profileSkillIds = new Set(perfil.skills.map(s => s.uri))
const profileKnowledgeIds = new Set(
  perfil.skills.filter(s => s.type === 'knowledge').map(s => s.uri)
)

const allSkillsB     = [...occB.skills.essential, ...occB.skills.optional]
const essentialIdsB  = new Set(occB.skills.essential.map(s => s.id))

// Lo que ya tiene (skills del perfil que B requiere)
const shared         = allSkillsB.filter(s => profileSkillIds.has(s.id))
const sharedEssential = shared.filter(s => essentialIdsB.has(s.id))
const sharedOptional  = shared.filter(s => !essentialIdsB.has(s.id))

// Gap (skills de B que el perfil no tiene)
const gapToCover     = allSkillsB.filter(s => !profileSkillIds.has(s.id))
const gapEssential   = gapToCover.filter(s => essentialIdsB.has(s.id))
const gapOptional    = gapToCover.filter(s => !essentialIdsB.has(s.id))

// Transferibles (skills del perfil que B no requiere)
const bSkillIds      = new Set(allSkillsB.map(s => s.id))
const transferable   = perfil.skills.filter(s => !bSkillIds.has(s.uri))

// Compatibilidad
const compatibility  = occB.skills.essential.length > 0
  ? Math.round(sharedEssential.length / occB.skills.essential.length * 100)
  : 0
```

---

## Carga de datos — estrategia

```
AL CARGAR LA PÁGINA:
  → getOfertasCountByIsco()  (una vez)
  → Si ?perfil_id + ?occ_id en URL → cargar ambos directo

AL SELECCIONAR PERSONA:
  → GET /api/oficina-empleo/perfiles/[id]
  → fetch /data/occupation_full_detail.json (si no está)
  → calcular matchingOccupations (useMemo) → alimenta "Mis matches"

AL SELECCIONAR OCUPACIÓN:
  → gapAnalysis calculado (useMemo, instantáneo)
  → getOccupationMOLProfile(esco_uri) (lazy, para frecuencias del Panel 2)
  → getOfertasByIsco(isco_code, 3) (lazy, para preview ofertas del banner)

AL CLICK EN "Elegir como objetivo":
  → reemplaza occId en estado → recalcula gapAnalysis → recarga MOL profile
```

---

## APIs — todas ya existen

| Endpoint / Función | Cuándo |
|--------------------|--------|
| `GET /api/oficina-empleo/perfiles?search=...` | Selector de persona |
| `GET /api/oficina-empleo/perfiles/[id]` | Cargar perfil |
| `getOfertasCountByIsco()` | Al cargar página |
| `getOccupationMOLProfile(esco_uri)` | Al seleccionar ocupación (lazy) |
| `getOfertasByIsco(isco_code, 3)` | Preview de ofertas en banner (lazy) |
| `OfertasOcupacionModal` | Botón "Ver las N ofertas" |

**No se crea ninguna API nueva.**

---

## Archivos a crear

| Archivo | Descripción |
|---------|-------------|
| `app/oficina-empleo/perfiles/futuro/page.tsx` | Página principal |
| `components/oficina-empleo/OcupacionObjetivoSelector.tsx` | Selector dual: Mis matches / Otro rumbo |
| `components/oficina-empleo/TransicionAnalysis.tsx` | Los 5 paneles de análisis |

**Código reutilizable:**
- `components/OccupationCompare.tsx` → lógica `gapAnalysis` + UI de paneles (adaptar)
- `components/MySkillsSearch.tsx` → `matchingOccupations` useMemo para "Mis matches"
- `components/OfertasOcupacionModal.tsx` → sin cambios
- `lib/supabase.ts` → `getOfertasCountByIsco`, `getOccupationMOLProfile`, `getOfertasByIsco`
- `PersonaSelector.tsx` → creado en Módulo 2 (Oportunidades Laborales), reutilizar sin cambios

---

## Estado React

```typescript
// Persona
const [perfil, setPerfil]               = useState<PerfilSkills | null>(null)

// Ocupación objetivo — selector dual
const [occMode, setOccMode]             = useState<'matches' | 'otro'>('matches')
const [occId, setOccId]                 = useState<string | null>(null)
const [occDetail, setOccDetail]         = useState<OccupationDetail | null>(null)

// Datos compartidos con Módulo 2 — Oportunidades Laborales (en memoria si ya pasó por ahí)
const [occupationsData, setOccData]     = useState<OccupationFullDetailIndex | null>(null)
const [ofertasCount, setOfertasCount]   = useState<Record<string, number>>({})

// Matching (para "Mis matches")
// matchingOccupations → useMemo igual que Módulo 2

// Gap analysis → useMemo (instantáneo una vez que hay perfil + ocup)

// MOL data (lazy)
const [molProfile, setMolProfile]       = useState<OccupationMOLProfileData | null>(null)
const [ofertasPreview, setOfertasPreview] = useState<OfertaPorOcupacion[]>([])

// Modal
const [showModal, setShowModal]         = useState(false)
```

---

## Vinculación entre módulos

```
Módulo 1 (Perfil de Competencias) → guarda perfil
  ↓  botón "Oportunidades →"
Módulo 2 (Oportunidades Laborales) → lista todas las ocupaciones compatibles
  ↓  botón "Ver en detalle" en una card
Módulo 3 (Futuro Laboral) → análisis profundo de UNA ocupación objetivo
  ↓  click en "Elegir como objetivo" en caminos alternativos
Módulo 3 → recarga con nueva ocupación, misma persona
```

---

## Pendiente para versiones futuras (Módulo 3 — Futuro Laboral)

- Exportar el plan de transición a PDF (gap + caminos + ofertas)
- Guardar ocupación objetivo en el perfil (`ocupacion_objetivo` en `perfiles_skills`)
- Provincias con más ofertas para la ocupación objetivo
- Rango salarial de la ocupación objetivo vs ocupación actual
- Estimación de tiempo de transición basada en cantidad de skills a aprender

---

---

# Módulo 4 — Inteligencia del Mercado Laboral

**Versión:** MVP  
**Audiencia:** Funcionarios, autoridades políticas, responsables de área  
**Estado:** Listo para implementar  
**Depende de:** Ninguno (usa datos MOL existentes)

---

## Propósito

Vista de alto nivel del mercado laboral para tomadores de decisión.  
No es para el técnico de la OE: no tiene candidatos, no tiene casos.  
Responde la pregunta: **¿qué está demandando el mercado en mi territorio?**

---

## Ruta

| Ruta | Pantalla |
|------|----------|
| `/oficina-empleo/dashboard-ejecutivo` | `mol-nextjs.vercel.app/oficina-empleo/dashboard-ejecutivo` |

---

## UI/UX — Pantalla completa

### Filtros globales (parte superior, prominentes)

```
┌─────────────────────────────────────────────────────────────────┐
│  📊  Panorama del Mercado Laboral                               │
│  Demanda de empleo en Argentina · datos MOL                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Territorio          Período                                    │
│  ┌───────────────┐   ┌───────────────────────────────────────┐  │
│  │ Todo el país ▾│   │ Últimos 3 meses                    ▾  │  │
│  └───────────────┘   └───────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Selector de territorio:** Todo el país / por provincia (24 opciones).  
**Período:** Última semana / Último mes / Últimos 3 meses / Último año.

---

### Bloque 1 — KPIs (fila de 4 cards)

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────┐  │
│  │  12.430      │  │  284         │  │  62%     │  │  38%   │  │
│  │  Ofertas     │  │  Ocupaciones │  │  Requiere│  │  Pide  │  │
│  │  activas     │  │  distintas   │  │  terciario│  │  skills│  │
│  │              │  │              │  │  o más   │  │ digit. │  │
│  └──────────────┘  └──────────────┘  └──────────┘  └────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

| KPI | Fuente | Campo |
|-----|--------|-------|
| Ofertas activas | `get_panorama` RPC | `total_ofertas` |
| Ocupaciones distintas | `get_panorama` RPC | `ocupaciones_distintas` |
| Requiere terciario o más | `get_requerimientos` RPC | distribución `nivel_educativo` |
| Pide skills digitales | `get_panorama` RPC | `pct_digital` (o cálculo local) |

---

### Bloque 2 — Sectores con mayor demanda

```
┌─────────────────────────────────────────────────────────────────┐
│  Sectores con mayor demanda                                     │
├─────────────────────────────────────────────────────────────────┤
│  Comercio minorista        ████████████████████████  2.840      │
│  Construcción              ████████████████░░░░░░░░  1.920      │
│  Servicios empresariales   ██████████████░░░░░░░░░░  1.650      │
│  Industria manufacturera   ████████████░░░░░░░░░░░░  1.320      │
│  Gastronomía y hotelería   ██████████░░░░░░░░░░░░░░  1.100      │
│  Transporte y logística    ████████░░░░░░░░░░░░░░░░    890      │
│  Salud                     ██████░░░░░░░░░░░░░░░░░░    670      │
│  Educación                 ████░░░░░░░░░░░░░░░░░░░░    440      │
└─────────────────────────────────────────────────────────────────┘
```

**Fuente:** `get_sidebar_counts` → agrupado por `clae_seccion_desc`.  
Barras horizontales simples, valor absoluto a la derecha.

---

### Bloque 3 — Evolución temporal

```
┌─────────────────────────────────────────────────────────────────┐
│  Evolución de ofertas publicadas                                │
│                                                                 │
│  1.400 ┤                                             ╭──╮      │
│  1.200 ┤                              ╭──╮          ╭╯  ╰─     │
│  1.000 ┤               ╭─╮          ╭─╯  ╰──╮    ╭─╯          │
│    800 ┤   ╭──╮      ╭─╯ ╰─╮      ╭╯        ╰╮ ╭─╯            │
│    600 ┤───╯  ╰──────╯     ╰──────╯           ╰─╯              │
│        └──────────────────────────────────────────────         │
│        Ene   Feb   Mar   Abr   May   Jun   Jul   Ago           │
└─────────────────────────────────────────────────────────────────┘
```

**Fuente:** `get_evolucion` RPC — `fecha_publicacion`, `count`.  
Línea simple, sin stacking. Filtrada por provincia si hay territorio seleccionado.

---

### Bloque 4 — Perfil de requerimientos

```
┌────────────────────────────────────────────────────────────────┐
│  Perfil de los puestos demandados                              │
├───────────────────┬───────────────────┬────────────────────────┤
│  Nivel educativo  │  Seniority        │  Modalidad             │
├───────────────────┼───────────────────┼────────────────────────┤
│  Sin req.   38%  │  Junior      41%  │  Presencial    72%     │
│  Secundario 29%  │  Semi-senior 33%  │  Híbrida       18%     │
│  Terciario  18%  │  Senior      17%  │  Remota        10%     │
│  Universitario14%│  Gerencial    9%  │                        │
└───────────────────┴───────────────────┴────────────────────────┘
```

**Fuente:** `get_requerimientos` RPC → distribuciones `nivel_educativo`, `seniority`, `modalidad`.  
Tres columnas de distribución porcentual. Sin gráficos — tabla limpia.

---

### Bloque 5 — Top skills territoriales

```
┌─────────────────────────────────────────────────────────────────┐
│  Competencias más demandadas en el territorio                   │
├─────────────────────────────────────────────────────────────────┤
│  1.  Atención al cliente           1.840 ofertas   ████████    │
│  2.  Manejo de caja / POS          1.620 ofertas   ███████     │
│  3.  Microsoft Excel               1.390 ofertas   ██████      │
│  4.  Trabajo en equipo             1.210 ofertas   █████       │
│  5.  Conducción de vehículos       1.080 ofertas   █████       │
│  6.  Gestión de inventario           940 ofertas   ████        │
│  7.  Ventas                          880 ofertas   ████        │
│  8.  Albañilería                     820 ofertas   ███         │
│  9.  SAP / ERP                       760 ofertas   ███         │
│  10. Idioma inglés                   640 ofertas   ███         │
└─────────────────────────────────────────────────────────────────┘
```

**Fuente:** `get_skills_resumen` — top 10 skills por `frequency`.  
Filtrable por territorio. Lista con barra proporcional.

---

## Carga de datos — estrategia

```
AL CARGAR LA PÁGINA (con filtros default: todo el país, últimos 3 meses):
  → get_panorama({ territorio, fechaDesde, fechaHasta })
  → get_sidebar_counts({ territorio, fechaDesde, fechaHasta })
  → get_evolucion({ territorio, fechaDesde, fechaHasta, granularidad: 'semana' })
  → get_requerimientos({ territorio, fechaDesde, fechaHasta })
  → get_skills_resumen({ territorio, fechaDesde, fechaHasta, limit: 10 })

AL CAMBIAR FILTRO (territorio o período):
  → Re-ejecutar todos los RPCs con los nuevos parámetros
  → Mostrar skeleton/spinner por bloque mientras carga
  → Los bloques cargan en paralelo (Promise.all)
```

---

## APIs

| RPC / función | Datos que provee | Ya existe |
|---------------|-----------------|-----------|
| `get_panorama` | total_ofertas, ocupaciones_distintas, pct_digital | ✅ |
| `get_sidebar_counts` | conteos por sector/CLAE | ✅ |
| `get_evolucion` | series temporales por semana/mes | ✅ |
| `get_requerimientos` | distribuciones educativo/seniority/modalidad | ✅ |
| `get_skills_resumen` | top skills con frecuencia | ✅ |

**No se crea ninguna API nueva.**

Todos los RPCs ya reciben `territorio` (provincia) y rango de fechas como parámetros — solo hay que pasarlos desde el selector de filtros.

---

## Estado React

```typescript
// Filtros (globales, arriba)
const [provincia, setProvincia]       = useState<string>('') // '' = todo el país
const [periodo, setPeriodo]           = useState<'7d'|'30d'|'90d'|'365d'>('90d')

// Datos por bloque (cargan en paralelo)
const [panorama, setPanorama]         = useState<PanoramaData | null>(null)
const [sectores, setSectores]         = useState<SectorCount[]>([])
const [evolucion, setEvolucion]       = useState<EvolucionPoint[]>([])
const [requerimientos, setReqs]       = useState<RequerimientosData | null>(null)
const [topSkills, setTopSkills]       = useState<SkillCount[]>([])

// Loading por bloque (skeleton independiente)
const [loadingKpis, setLoadingKpis]   = useState(true)
const [loadingRest, setLoadingRest]   = useState(true)
```

---

## Archivos a crear

| Archivo | Descripción |
|---------|-------------|
| `app/oficina-empleo/dashboard-ejecutivo/page.tsx` | Página principal — filtros + 5 bloques |
| `components/oficina-empleo/KpiCard.tsx` | Card de KPI reutilizable (número + label + ícono) |
| `components/oficina-empleo/SectorBarChart.tsx` | Barras horizontales de sectores |
| `components/oficina-empleo/TopSkillsList.tsx` | Lista top skills con barra proporcional |

El gráfico de evolución temporal puede reutilizar el componente ya existente en el dashboard principal (`/dashboard`).  
El bloque de requerimientos es una tabla simple — sin componente separado.

---

## Flujo completo

```
1. Técnico / funcionario abre la pantalla
   → Filtros: "Todo el país" + "Últimos 3 meses" (default)
   → Los 5 bloques cargan en paralelo con skeleton

2. Funcionario selecciona su provincia
   → Re-fetch inmediato de todos los bloques
   → KPIs, sectores, evolución, requerimientos y skills se actualizan

3. Funcionario cambia el período (ej: "Último año")
   → Re-fetch con nuevo rango de fechas

4. Lectura: el funcionario ve los bloques y toma decisiones de política
   (sin acciones, sin casos, sin candidatos)
```

---

## Conexión con los otros módulos

Este módulo es independiente en datos, pero complementario en uso:

| Flujo | Cómo se relaciona |
|-------|-------------------|
| Módulo 1 (Perfil de Competencias) → Módulo 4 | Futuro: cruzar perfiles_skills con ofertas para mostrar brecha oferta/demanda por territorio |
| Módulo 4 → Módulos 2 y 3 | El funcionario ve que falta personal en construcción → deriva al técnico para hacer matching de candidatos |

---

## Pendiente para versiones futuras (Módulo 4 — Inteligencia del Mercado Laboral)

- **Brecha oferta/demanda territorial**: cruzar `perfiles_skills` (skills disponibles en la población) con `ofertas_dashboard` (skills demandadas por el mercado) para cada provincia. Requiere volumen suficiente en Módulo 1 (Perfil de Competencias).
- Mapa coroplético por provincia (intensidad de demanda)
- Descarga de reporte en PDF para presentaciones
- Comparación entre dos provincias / dos períodos
- Alertas automáticas (ej: sector con crecimiento > 20% mensual)
