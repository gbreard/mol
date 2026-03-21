# Guia para Sergio — Skills Intelligence v5

> Branch: `feature/skills-intelligence-v5`
> Leeme antes de arrancar. Despues lee `docs/plan/09_ROADMAP.md` para el contexto completo.

## Estado del backend (actualizado por Gerardo)

| Componente | Estado | Commit | Sergio puede |
|-----------|--------|--------|-------------|
| Migration 018: `perfil_argentino_versiones` | ✅ Listo (SQL creado, pendiente ejecutar en Supabase) | `c0d89693` | S1: usar mock hasta que Gerardo ejecute migration |
| API `/api/perfil-argentino-versiones` GET/POST/PATCH | ✅ Listo | `c0d89693` | S1: desarrollar P-36 contra esta API (o mock) |
| Test unitario PCA (8 tests passing) | ✅ Listo | `c0d89693` | — |
| PCA-5: MySkillsSearch lee perfil activo | ✅ Listo | `9eede9d2` | Hook usePerfilArgentino + fallback ESCO |
| A-D3: Catálogo unificado (16,633 skills) | ✅ Listo | `deb161cf` | skills_searchable.json con emergentes argentinas |
| API `/api/skills-search` GET | ✅ Listo | `7469066b` | S2: puede conectar directo (Fase 1 full-text) |
| API `/api/skills-extract-from-text` POST | ✅ Listo | `7469066b` | S4: puede conectar directo (Fase 1 keywords) |
| API `/api/compatibility-report` GET/POST/PATCH | ✅ Listo | `c1a44477` | S5, S6: puede conectar directo. PDF generator en lib/generate-report-pdf.ts |
| API `/api/matching-offers` GET | ✅ Listo | `425dbf80` | S7: puede conectar directo. Gap personalizado + filtros |
| API `/api/training-suggestions` GET | ✅ Listo | `425dbf80` | S8: puede conectar directo. Multi-fuente + tendencia temporal |

**Que puede hacer Sergio HOY:**
- **S1 a S8** — TODAS las APIs del Bloque 1-4 listas (versiones, search, extract, report, offers, training)
- **S2-1 a S2-5** (Oficina Empleo) — Bloque 5 listo: multi-tenancy + import CSV + organizaciones API
- **Todas las tareas** — no queda ninguna API bloqueada

**NUEVO Bloque 5 (OE):**
- Migration 019: tablas `organizaciones` + `user_organizaciones` (pendiente ejecutar en Supabase)
- API `/api/organizaciones` GET/POST
- Parser CSV: `lib/parse-pool-import.ts` (sanitización S-25 incluida)
- Funciones SQL: `get_user_org()`, `get_perfiles_by_org()`

**Antes de arrancar:** `git pull origin feature/skills-intelligence-v5`

---

## Setup inicial

```bash
git clone git@github.com:gbreard/mol.git
cd mol
git checkout feature/skills-intelligence-v5
cd fase3_dashboard/mol-dashboard
npm install
```

Pedile a Gerardo:
- `config/supabase_config.json` (credenciales Supabase — no esta en git)
- `.env.local` para el dashboard (SUPABASE_URL + SUPABASE_ANON_KEY)

Para correr el dashboard en local:
```bash
cd fase3_dashboard/mol-dashboard
npm run dev
# Abrir http://localhost:3000
```

Para correr tests:
```bash
npm run test          # unit + component
npm run test:watch    # en modo watch mientras desarrollas
npm run test:e2e      # e2e con Playwright
```

## Tu rol

Vos haces **frontend/UI**: componentes React, paginas Next.js, estilos Tailwind, tests de componente.
Gerardo hace **backend/datos**: Supabase migrations, API routes, motor semantico, matching.

El flujo es:
1. Gerardo crea la API route y te pasa los tipos TypeScript
2. Vos creas el componente que consume esa API
3. Mientras Gerardo no tenga la API lista, vos usas **mocks** (MSW) para desarrollar

## Tu branch

```bash
# Crear tu branch desde el branch principal
git checkout -b feature/si-sergio-ui feature/skills-intelligence-v5

# Cuando termines algo, push
git push -u origin feature/si-sergio-ui

# PR a feature/skills-intelligence-v5 (NO a main)
```

## Estructura de tests

Tests van en `__tests__/` con esta estructura:
```
__tests__/
  component/    ← tus tests van aca (render + interaccion)
  unit/         ← Gerardo (logica, calculos)
  integration/  ← entre los dos
  security/     ← Gerardo
  mocks/
    handlers.ts ← MSW handlers (agregar los nuevos aca)
    fixtures/   ← datos de prueba
```

Cada componente nuevo necesita su test. Patron:
```tsx
// __tests__/component/mi-componente.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MiComponente from '@/components/MiComponente'

describe('MiComponente', () => {
  it('renderiza correctamente', () => {
    render(<MiComponente />)
    expect(screen.getByText('algo')).toBeInTheDocument()
  })

  it('responde a interaccion', async () => {
    render(<MiComponente />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('resultado')).toBeInTheDocument()
  })
})
```

Antes de pushear: `npm run test` — todos los tests tienen que pasar (los tuyos + los 153 existentes).

---

## Tus tareas — Bloque por bloque

### BLOQUE 1° — Perfil Consolidado (Gerardo lidera, vos haces UI)

**Gerardo hace:** migration SQL `perfil_argentino_versiones`, API `/api/perfil-argentino-versiones`, conectar matching a perfil activo.

**Vos haces:**

#### Tarea S1: Pantalla P-36 — Gestion Perfil Argentino (`/admin/perfil-argentino`)

Wireframe completo en: `docs/plan/03_WIREFRAMES/oficina-empleo.md` → seccion P-36

```
Archivo a crear: app/admin/perfil-argentino/page.tsx
Componentes a crear:
  - components/PerfilArgentinoAdmin.tsx (pantalla principal)
  - components/VersionHistoryTable.tsx (tabla de versiones)
  - components/CreateVersionModal.tsx (modal para crear corte)
```

**Que tiene que hacer la pantalla:**
- Mostrar version activa con badge
- Tabla de historial de versiones (version, fecha, skills, emergentes, creado por, activa)
- Boton "Crear nueva version" que abre modal
- Modal: version propuesta, nota del corte, emergentes pendientes, boton confirmar
- Boton rollback (con confirmacion)

**API que va a consumir** (la crea Gerardo):
```typescript
// GET /api/perfil-argentino-versiones
// Retorna: { versiones: PerfilVersion[], activa: PerfilVersion }
type PerfilVersion = {
  id: string
  version: string        // "v1.0", "v2.1"
  total_skills: number
  total_emergentes: number
  total_ocupaciones: number
  nota: string | null
  creado_por: string     // email
  activa: boolean
  created_at: string
}

// POST /api/perfil-argentino-versiones
// Body: { nota: string }
// Retorna: { version: PerfilVersion }

// PATCH /api/perfil-argentino-versiones
// Body: { version_id: string, action: 'activar' | 'rollback' }
```

**Mock para desarrollar sin API** (agregar en `__tests__/mocks/handlers.ts`):
```typescript
http.get('/api/perfil-argentino-versiones', () => {
  return HttpResponse.json({
    activa: {
      id: 'uuid-1', version: 'v1.0', total_skills: 14257,
      total_emergentes: 0, total_ocupaciones: 3046,
      nota: 'Version base ESCO', creado_por: 'admin@oede.gob.ar',
      activa: true, created_at: '2026-01-15T00:00:00Z'
    },
    versiones: [
      // ... array de versiones
    ],
    estado_actual: {
      ofertas_desde_ultimo_corte: 2132,
      emergentes_nuevas: 8,
      emergentes_pendientes: 3,
      skills_aprobadas_desde_corte: 5
    }
  })
})
```

**Test requerido:** `__tests__/component/perfil-argentino-admin.test.tsx`
- Renderiza historial de versiones
- Badge "activa" en la version correcta
- Boton crear version abre modal
- Confirmar cierra modal y recarga
- Rollback pide confirmacion

---

### BLOQUE 2° — Motor Semantico (Gerardo lidera, vos haces UI)

**Gerardo hace:** endpoint busqueda semantica, NLP texto libre, catalogo unificado.

**Vos haces:**

#### Tarea S2: Componente busqueda de skills por tarea (Via 2)

```
Archivo a crear: components/SkillSearchByTask.tsx
```

**Que tiene que hacer:**
- Input de busqueda con debounce (300ms)
- Dropdown de resultados con: label, tipo (skill/knowledge), definicion truncada
- Click en resultado lo agrega al perfil
- Cada skill agregada muestra definicion completa + checkbox confirmar/dudar/descartar

**API que va a consumir** (la crea Gerardo):
```typescript
// GET /api/skills-search?q=soldar&limit=10
type SkillSearchResult = {
  uri: string
  label: string
  type: 'skill' | 'knowledge'
  description: string
  source: 'esco' | 'argentina_approved'  // origen
  frequency?: number                      // % en ofertas argentinas
}
```

**Test requerido:** `__tests__/component/skill-search-input.test.tsx`
- Render del input
- Debounce: no llama API en cada tecla
- Resultados desplegables con definicion
- Click agrega al perfil
- Sin resultados muestra mensaje

#### Tarea S3: Componente skill con definicion (confirmar/dudar/descartar)

```
Archivo a crear: components/SkillWithDefinition.tsx
```

**Que tiene que hacer:**
- Muestra: label + badge tipo (skill/knowledge) + badge origen (ESCO/emergente)
- Muestra definicion ESCO completa (expandible si es larga)
- Checkbox de 3 estados: ✓ (confirmo), ? (no estoy seguro), ✗ (descarto)
- Boton quitar (✕)
- Tag de via: "via ocupacion", "via busqueda", "via texto libre"

**Test requerido:** `__tests__/component/skill-with-definition.test.tsx`
- Muestra label + definicion
- Checkbox cambia entre 3 estados
- Click quitar dispara onRemove
- Badge tipo y origen correctos

#### Tarea S4: Componente texto libre (Via 3)

```
Archivo a crear: components/FreeTextSkillExtractor.tsx
```

**Que tiene que hacer:**
- Textarea para texto libre ("Conta con tus palabras...")
- Boton "Identificar competencias"
- Loading state mientras procesa
- Muestra skills identificadas usando SkillWithDefinition (tarea S3)
- Boton "Agregar todas al perfil" o agregar una por una

**API que va a consumir** (la crea Gerardo):
```typescript
// POST /api/skills-extract-from-text
// Body: { text: string }
// Retorna: { skills: SkillSearchResult[] }
```

**Test requerido:** `__tests__/component/free-text-extractor.test.tsx`
- Render textarea
- Boton deshabilitado si texto vacio
- Loading state al procesar
- Skills identificadas se muestran con definicion
- Agregar todas funciona

---

### BLOQUE 3° — Report Engine (Gerardo lidera, vos haces UI)

**Gerardo hace:** API reporte, generacion PDF, QR, tabla BD.

**Vos haces:**

#### Tarea S5: Pagina /reporte/[token] (vista reclutador)

Wireframe en: `docs/plan/03_WIREFRAMES/oficina-empleo.md` → seccion P-35

```
Archivo a crear: app/reporte/[token]/page.tsx
Componentes a crear:
  - components/CompatibilityReport.tsx (pantalla completa)
  - components/SkillsMapEditable.tsx (mapa de competencias editable)
  - components/AffinityMatrix.tsx (matriz detectadas vs brechas)
```

**Que tiene que hacer:**
- Carga datos del reporte por token (API GET)
- Seccion datos del perfil: candidato, vacante, % compatibilidad con barra
- Mapa de competencias: tabla con estado (detectada/faltante), boton quitar, boton agregar
- Al editar: recalcular % en frontend (NO llama API)
- Boton "Restaurar original"
- Matriz de afinidad: 2 columnas (detectadas | brechas) con tipo [S]/[K]/[T]
- Bloque "Sobre el MOL" con link
- Token expirado: mensaje claro
- Token invalido: 404

**API que va a consumir** (la crea Gerardo):
```typescript
// GET /api/compatibility-report?token=abc123
type ReportData = {
  candidato_nombre: string
  ocupacion_label: string
  ocupacion_isco: string
  match_score: number
  perfil_consolidado_version: string
  skills_candidato: SkillItem[]
  skills_requeridas: SkillItem[]
  skills_cubiertas: SkillItem[]
  skills_gap: SkillItem[]
  estado: 'activo' | 'expirado' | 'revocado'
  created_at: string
  expira_at: string
}

type SkillItem = {
  uri: string
  label: string
  type: 'skill' | 'knowledge' | 'transversal'
  source: 'esco' | 'argentina_approved'
  description?: string
}
```

**Tests requeridos:** `__tests__/component/compatibility-report.test.tsx`
- Render con datos completos
- Token expirado muestra mensaje
- Editar skills recalcula %
- Restaurar vuelve a original
- No muestra DNI

`__tests__/component/skills-map-editable.test.tsx`
- Quitar skill actualiza lista
- Agregar skill actualiza lista
- Badge origen visible (ESCO/emergente)

#### Tarea S6: Modal confirmar datos del reporte

```
Archivo a crear: components/GenerateReportModal.tsx
```

**Que tiene que hacer:**
- Campos: nombre candidato (pre-llenado), DNI, titulo vacante (pre-llenado)
- Nota: "El reporte estara disponible por 60 dias"
- Botones: Cancelar / Generar Reporte + PDF
- Loading state al generar
- Exito: mostrar opciones (Descargar PDF / Copiar link / Ver reporte)

**Test requerido:** `__tests__/component/generate-report-modal.test.tsx`
- Campos pre-llenados
- Validacion nombre requerido
- Boton genera y muestra exito
- Copiar link funciona

---

### BLOQUE 4° — Tabs de Resultados (Sergio lidera)

**Gerardo hace:** funciones de matching ofertas y cursos (API).

**Vos haces:**

#### Tarea S7: Tab Ofertas Laborales

```
Archivo a crear: components/OffersTab.tsx
```

Wireframe en: `docs/plan/03_WIREFRAMES/oficina-empleo.md` → Tab 2

**Que tiene que hacer:**
- Filtros: provincia, ocupacion, modalidad, ordenar
- Cards de ofertas con: titulo, empresa, ubicacion, modalidad, fecha
- Barra de compatibilidad con %
- Skills que tenes / te faltan
- Botones: Ver oferta (link externo) + Reporte (genera reporte vinculado a oferta)
- Paginacion: "Mostrando N de M" + Cargar mas
- Empty state si no hay ofertas

**API que va a consumir** (la crea Gerardo):
```typescript
// GET /api/matching-offers?profile_id=xxx&page=1&provincia=CABA
type MatchingOffer = {
  id_oferta: number
  titulo: string
  empresa: string
  provincia: string
  localidad: string
  modalidad: string
  fecha_publicacion: string
  url_oferta: string
  match_score: number
  skills_cubiertas: string[]
  skills_gap: string[]
}
```

**Test requerido:** `__tests__/component/offers-tab.test.tsx`
- Render cards con datos
- Filtros cambian resultados
- Cargar mas agrega cards
- Empty state
- Boton ver oferta tiene href correcto

#### Tarea S8: Tab Capacitacion

```
Archivo a crear: components/TrainingTab.tsx
Componentes auxiliares:
  - components/TrainingByGap.tsx (cursos agrupados por brecha)
  - components/TransitionPreference.tsx (opcion A: elegir destino)
  - components/TransitionDemand.tsx (opcion B: por demanda mercado)
```

Wireframe en: `docs/plan/03_WIREFRAMES/oficina-empleo.md` → Tab 3

**Que tiene que hacer:**
- Seccion cursos por brecha: agrupados por skill faltante, card con nombre/cert/duracion/modalidad/cubre
- Seccion transicion A (preferencia): input buscar ocupacion destino, mostrar gap + cursos
- Seccion transicion B (demanda): tabla ocupaciones en crecimiento cercanas al perfil, con tendencia %
- Cada ocupacion sugerida: compatibilidad, skills faltantes, tiempo estimado, links [Ver cursos] [Ver ofertas]
- Nota de fuente: "Portal de Capacitacion CABA | 2,255 cursos"

**API que va a consumir** (la crea Gerardo):
```typescript
// GET /api/training-suggestions?profile_id=xxx
type TrainingSuggestions = {
  by_gap: {
    skill_label: string
    courses: Course[]
  }[]
  transition_demand: {
    ocupacion_label: string
    isco: string
    trend_pct: number       // +35%
    match_score: number
    skills_gap: string[]
    estimated_months: number
  }[]
}

type Course = {
  id: number
  name: string
  certificacion: string
  duracion: string
  modalidad: string
  covers_skills: string[]
  url?: string
}
```

**Tests requeridos:**
`__tests__/component/training-tab.test.tsx`
- Render cursos por brecha
- Switch entre modo A y modo B
- Cards de cursos con datos

`__tests__/component/transition-demand.test.tsx`
- Tabla con tendencia %
- Ordenado por accesibilidad
- Links funcionales

---

## Resumen de archivos que creas

| # | Componente | Bloque | Test |
|---|-----------|--------|------|
| S1 | PerfilArgentinoAdmin + VersionHistoryTable + CreateVersionModal | 1° | perfil-argentino-admin.test.tsx |
| S2 | SkillSearchByTask | 2° | skill-search-input.test.tsx |
| S3 | SkillWithDefinition | 2° | skill-with-definition.test.tsx |
| S4 | FreeTextSkillExtractor | 2° | free-text-extractor.test.tsx |
| S5 | CompatibilityReport + SkillsMapEditable + AffinityMatrix | 3° | compatibility-report.test.tsx + skills-map-editable.test.tsx |
| S6 | GenerateReportModal | 3° | generate-report-modal.test.tsx |
| S7 | OffersTab | 4° | offers-tab.test.tsx |
| S8 | TrainingTab + TrainingByGap + TransitionPreference + TransitionDemand | 4° | training-tab.test.tsx + transition-demand.test.tsx |

**Total: 18 componentes + 10 archivos de test**

## Estilo y diseno

**NO inventes estilos nuevos.** El dashboard ya tiene un sistema de diseno definido. Reutiliza lo que existe:

**Stack UI:**
- Tailwind CSS (clases utilitarias)
- Radix UI (componentes base: dialogs, dropdowns, tabs, tooltips)
- Recharts (graficos)
- Lucide React (iconos)

**Componentes existentes para reutilizar:**
- `components/ui/` — botones, inputs, badges, cards (Radix + Tailwind)
- `components/ChartContainer.tsx` — wrapper de graficos con export
- `components/ExportButton.tsx` — patron de export
- `components/OccupationDetail.tsx` — layout de detalle de ocupacion
- `components/MySkillsSearch.tsx` — referencia de flujo de 3 pasos (897 lineas)

**Colores del sistema:**
- Primario: azul (`blue-600`, `blue-700`)
- Exito/detectada: verde (`green-600`, `emerald`)
- Error/faltante: rojo (`red-600`, `rose`)
- Warning/dudoso: amarillo (`amber-500`)
- Backgrounds: `gray-50`, `gray-100`, `white`
- Texto: `gray-900` (principal), `gray-500` (secundario)

**Patron de pagina:**
```tsx
// Todas las paginas admin siguen este patron:
export default function MiPagina() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Titulo</h1>
      {/* contenido */}
    </div>
  )
}
```

**Antes de crear un componente nuevo:** busca si ya existe algo parecido en `components/`. Si hay algo similar, extiendelo — no dupliques.

---

## Bloque F: Responsive (mobile + tablet) — TU BLOQUE

Ademas de las tareas S1-S8, tenes asignado el **Bloque F** completo: hacer que el sistema funcione en celular y tablet.

**Prioridad:**
1. **S1 en mobile** (ALTA) — el trabajador entra desde el celular
2. **S3 reporte QR en mobile** (ALTA) — el reclutador escanea con el teléfono
3. **S2 en tablet** (MEDIA) — el técnico de OE puede usar tablet en la atención

**Criterios:**
- Botones e inputs: mínimo 44x44px (touch WCAG)
- Sin scroll horizontal
- Tablas → cards en mobile
- 3 breakpoints: 375px (mobile), 768px (tablet), 1280px (desktop)

**Tests requeridos:**
- `component/responsive-s1-mobile.test.tsx`
- `component/responsive-s3-qr-mobile.test.tsx`
- `e2e/responsive-flow.spec.ts` (Playwright en viewport mobile)

Ver detalle completo en `docs/plan/09_ROADMAP.md` → Bloque F.

---

## Tareas adicionales de UI (de la planificación completa)

Ademas de S1-S8 y Bloque F, estos wireframes y pantallas te tocan:

### De la Integración S1↔S2

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S9 | UI opt-in en S1: toggle provincial/nacional + explicación anonimización | `oficina-empleo.md` → "Trabajador configura opt-in" | Componente toggle con select provincia, texto explicativo |
| S10 | Búsqueda por DNI en S2: input + resultado perfil existente + botón vincular | `oficina-empleo.md` → "Técnico busca perfil por DNI" | Componente búsqueda + card resultado + modal confirmación |
| S11 | Perfil anonimizado en búsqueda pool: card sin nombre, solo skills y match | `oficina-empleo.md` → "Perfil anonimizado en búsqueda" | Componente card anonimizada + botón solicitar contacto |

**APIs que consume (Gerardo las crea):**
```typescript
// GET /api/worker-profiles?dni=30123456 — buscar por DNI
// PATCH /api/worker-profiles — vincular a OE (organizacion_id)
// GET /api/pool-search?isco=2512&jurisdiccion=CABA — buscar pool anonimizado
```

### Del Onboarding OE

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S12 | Pantalla bienvenida primer ingreso: 3 cards (personas/vacantes/cursos) + descargar template | `oficina-empleo.md` → "Onboarding OE" | Página con detección primer ingreso + 3 cards + links descarga |
| S13 | Preview importación: tabla con primeras filas + resumen + botón confirmar | `oficina-empleo.md` → "Preview de importación" | Componente tabla preview + resumen (válidas/saltadas/errores) |
| S14 | Post-importación: mensaje éxito + estadísticas + siguientes pasos | `oficina-empleo.md` → "Post-importación" | Componente resultado + 3 botones (panel/vacantes/cursos) |

**API que consume:**
```typescript
// POST /api/import-pool — sube CSV, retorna preview
// POST /api/import-pool/confirm — confirma importación
```

### Del Bloque 9° (Curación perfil)

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S15 | Badge emergentes en P-36: número rojo si hay pendientes | `oficina-empleo.md` → P-36 | Badge numérico en botón "Revisar emergentes" |

**API que consume:**
```typescript
// GET /api/emergentes-pendientes/count — retorna { count: N }
```

### Del Bloque 10° (Inteligencia local)

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S16 | Pantalla S2-10 inteligencia local: 2 paneles (demandadas/disponibles) + tabla brecha + cursos faltantes | `oficina-empleo.md` → S2-10 | Dashboard con 4 secciones + botón exportar PDF |

**API que consume:**
```typescript
// GET /api/inteligencia-local?jurisdiccion=CABA — retorna brechas + cursos faltantes
```

### Del Bloque 8° (Formación con impacto)

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S17 | Pantalla S2-8 formación: cursos por brecha con delta match % | `oficina-empleo.md` → S2-8 | Cards de cursos agrupados por brecha + caja impacto + botón derivar |

**API que consume:**
```typescript
// GET /api/training-impact?profile_id=xxx — retorna cursos con delta match
```

### Del Bloque 11° (S3 registrado)

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S18 | S3-6 perfil de puesto: form skills requeridas + guardar/duplicar | `oficina-empleo.md` → S3-6 | Form con búsqueda skills + badges ESCO/emergente + CRUD |
| S19 | S3-9 benchmark mercado: tabla disponibilidad skills + alertas escasez | `oficina-empleo.md` → S3-9 | Dashboard con tabla + indicadores dificultad |

### Del Bloque 12° (Vía 4)

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S20 | UI Vía 4 en paso 2: búsqueda título + resultados con skills derivadas + badge verificado | `oficina-empleo.md` → Vía 4 | Input búsqueda + cards resultado con skills + botón agregar |

**API que consume:**
```typescript
// GET /api/formacion-search?q=tecnicatura+redes — buscar en resoluciones
```

---

## Resumen total de tareas Sergio

| Grupo | Tareas | Componentes | Tests |
|-------|--------|-------------|-------|
| S1-S8 (Bloques 1-4) | 8 | 18 | 10 |
| Bloque F (responsive) | F1-F6 | adaptar existentes | 3 |
| Integración S1↔S2 | S9-S11 | 3 | 3 |
| Onboarding OE | S12-S14 | 3 | 2 |
| Curación perfil | S15 | 1 (badge) | 1 |
| Inteligencia local | S16 | 1 | 1 |
| Formación impacto | S17 | 1 | 1 |
| S3 registrado | S18-S19 | 2 | 2 |
| Vía 4 | S20 | 1 | 1 |
| Catálogo MOL | S21-S22 | 2 | 2 |
| Scraping admin | S23-S24 | 2 | 2 |
| **Total** | **S1-S22 + F1-F6** | **~32 componentes** | **~32 tests (1 por componente mínimo)** |

### Del Bloque G (Catálogo MOL)

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S21 | Panel "No clasificados": tabla skills/ocupaciones sin match ESCO, filtros, acciones | `oficina-empleo.md` → "Panel No clasificados" | Tabla con tabs skills/ocupaciones + filtro frecuencia + botones catalogar/sinónimo/descartar |
| S22 | Editor ficha MOL: modal para crear skill/ocupación con definición, tipo, categoría, relaciones | `oficina-empleo.md` → "Editor de ficha MOL" | Modal form con campos definición, radio tipo, select categoría, búsqueda ESCO parent, lista relaciones |

**APIs que consume (Gerardo las crea):**
```typescript
// GET /api/catalogo-mol/no-clasificados?tipo=skills&min_freq=30
// POST /api/catalogo-mol — crear ficha
// PATCH /api/catalogo-mol — marcar como sinónimo o descartar
```

### Del Bloque H (Scraping admin)

| # | Tarea | Wireframe en | Qué hacer |
|---|-------|-------------|-----------|
| S23 | Dashboard scraping: KPIs + gráfico temporal + cards por portal con alertas | `oficina-empleo.md` → "H1 Dashboard monitoreo" | Dashboard con Recharts (línea temporal) + cards estado + badge alertas |
| S24 | Control comandos: botones lanzar/pausar/sync + log en tiempo real + historial | `oficina-empleo.md` → "H2 Control de comandos" | Botones con confirmación + textarea log con polling + tabla historial |

**APIs que consume:**
```typescript
// GET /api/scraping-stats — KPIs + historia + alertas
// GET /api/scraping-commands — listar comandos
// POST /api/scraping-commands — crear comando (lanzar/pausar/sync)
```

### Regla de testing obligatoria

```
CADA COMPONENTE NUEVO = 1 ARCHIVO DE TEST MÍNIMO

El test debe cubrir:
1. Renderiza sin errores
2. Muestra los datos que recibe por props
3. Responde a interacción principal (click, input, toggle)
4. Maneja estados: loading, error, empty
5. No rompe los tests existentes (npm run test antes de push)

SIN TEST = NO SE PUSHEA
```

---

## Division de trabajo clara

| Gerardo hace | Sergio hace |
|-------------|------------|
| Supabase: migrations, RLS, funciones SQL | Componentes React (UI) |
| API routes (Next.js /api/*) | Páginas Next.js (layout, navegación) |
| Lógica de negocio (matching, cálculos) | Estilos Tailwind + responsive |
| Integración frontend ↔ backend | Consumir APIs (fetch/React Query) |
| Tests unitarios (lógica) | Tests de componente (@testing-library) |
| Tests de seguridad | Tests e2e (Playwright) |
| Deploy (Vercel + Supabase) | — |
| Motor semántico (búsqueda, NLP) | — |
| Perfil Consolidado Argentino | — |

**Sergio NO hace:** APIs, migrations, RLS, deploy, lógica de matching, integración con Supabase directo.

**Sergio SÍ hace:** todo lo que se ve en pantalla + tests de que se ve bien y funciona.

---

## Reglas

1. **No toques Supabase** — Gerardo hace todas las migrations y RLS
2. **No toques API routes** — Gerardo las crea, vos las consumes
3. **Usa mocks (MSW)** para desarrollar sin esperar la API
4. **Cada componente con su test** — no se pushea sin test
5. **`npm run test` antes de pushear** — 0 failing
6. **PR a `feature/skills-intelligence-v5`** — nunca a main
7. **Commits chicos y frecuentes** — no acumular
8. **Lee los wireframes** — `docs/plan/03_WIREFRAMES/oficina-empleo.md` tiene el diseno de cada pantalla
