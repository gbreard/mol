# Handoff Sergio — S1 a S8 completados

**Branch:** `feature/si-sergio-ui`
**Commit:** `c021a45`
**Fecha:** 2026-03-21
**Para mergear a:** `feature/skills-intelligence-v5`

---

## Estado: todo listo para review

18 componentes creados, 63 tests nuevos, suite total ~444 pasando.
Los 2 únicos failures existentes (`export-button.test.tsx`) son pre-existentes y no son nuestros.

---

## Qué se hizo

### BLOQUE 1 — Perfil Consolidado

#### S1: `/admin/perfil-argentino`
- `components/PerfilArgentinoAdmin.tsx` — pantalla principal con historial de versiones y badge activa
- `components/VersionHistoryTable.tsx` — tabla de versiones
- `components/CreateVersionModal.tsx` — modal crear corte con nota y warning de emergentes
- `app/admin/perfil-argentino/page.tsx`
- Consume: `GET/POST/PATCH /api/perfil-argentino-versiones` (ya existía)

---

### BLOQUE 2 — Motor Semántico

#### S2: `SkillSearchByTask`
- Input con debounce 300ms → dropdown con label + tipo + definición truncada
- Click agrega skill al perfil con estado `confirmed` + `via: busqueda`
- Consume: `GET /api/skills-search?q=...&limit=10`

#### S3: `SkillWithDefinition`
- Card de skill con 3 estados: ✓ confirmar / ? dudar / ✗ descartar
- Badges: tipo (competencia/conocimiento), origen (ESCO/emergente), vía
- Definición expandible si es larga

#### S4: `FreeTextSkillExtractor`
- Textarea → botón "Identificar competencias" → loading → lista de skills
- Botón "Agregar todas" o agregar una por una
- Consume: `POST /api/skills-extract-from-text`

---

### BLOQUE 3 — Report Engine

#### S5: `/reporte/[token]` (pública, sin auth)
- `app/reporte/[token]/page.tsx` — server component, maneja 404 y estados expirado/revocado
- `components/CompatibilityReport.tsx` — layout completo con barra de score recalculable
- `components/SkillsMapEditable.tsx` — tabla editable (quitar/agregar skills), recalcula % en frontend sin llamar API
- `components/AffinityMatrix.tsx` — 2 columnas detectadas vs brechas con badges [S]/[K]/[T]/[E]
- Consume: `GET /api/compatibility-report?token=...`

**Nota importante:** los cambios del reclutador son solo en frontend. Si recarga, vuelve al original. El DNI no aparece en ninguna parte del reporte visible.

#### S6: `GenerateReportModal`
- Campos: nombre (pre-llenado), DNI (opcional, no va al reporte), título vacante
- Estados: form → loading → success (Descargar PDF / Copiar link / Ver reporte)
- Consume: `POST /api/compatibility-report`

---

### BLOQUE 4 — Tabs de Resultados

#### S7: `OffersTab`
- Filtros: provincia, modalidad, ocupación, orden
- Cards con: título, empresa, ubicación, modalidad, fecha, barra de compatibilidad %
- Skills "tenés" (verde) y "te faltan" (rojo) por oferta
- Botones: "Ver oferta" (link externo) + "Reporte" (llama `onGenerateReport`)
- Paginación: "Mostrando N de M" + "Cargar más"
- Consume: `GET /api/matching-offers?profile_id=...&page=...&provincia=...`

#### S8: `TrainingTab` + sub-componentes
- **`TrainingTab`** — orquesta 3 tabs: cursos por brecha / transición elegir / transición demanda
- **`TrainingByGap`** — cursos agrupados por skill faltante, card con cert/duración/modalidad/cubre
- **`TransitionPreference`** — input buscar ocupación destino → gap + cursos
- **`TransitionDemand`** — tabla de ocupaciones en crecimiento, ordenada por accesibilidad (match_score), con tendencia %, tiempo estimado, botones Ver cursos / Ver ofertas
- Consume: `GET /api/training-suggestions?profile_id=...`
- Nota de fuente: "Portal de Capacitación CABA | 2,255 cursos"

---

## Dev mock (solo para localhost sin Supabase)

Se agregó bypass de auth para desarrollo local. **NO va a producción** porque `.env.local` está gitignoreado.

- `lib/supabase/middleware.ts` — si `DEV_MOCK_AUTH=true`, inyecta usuario admin mock y saltea Supabase
- `lib/api-auth.ts` — mismo bypass en `requireAuth`, `requireAdmin`, `requireSubscriber`

Para activar: agregar `DEV_MOCK_AUTH=true` al `.env.local` local.

---

## APIs que se consumen (todas ya existentes según Gerardo)

| API | Método | Usado en |
|-----|--------|----------|
| `/api/perfil-argentino-versiones` | GET/POST/PATCH | S1 |
| `/api/skills-search` | GET | S2 |
| `/api/skills-extract-from-text` | POST | S4 |
| `/api/compatibility-report` | GET/POST | S5, S6 |
| `/api/matching-offers` | GET | S7 |
| `/api/training-suggestions` | GET | S8 |

---

## Tests

| Archivo | Tests |
|---------|-------|
| `perfil-argentino-admin.test.tsx` | 6 |
| `skill-search-input.test.tsx` | 5 |
| `skill-with-definition.test.tsx` | 8 |
| `free-text-extractor.test.tsx` | 7 |
| `compatibility-report.test.tsx` | 6 |
| `skills-map-editable.test.tsx` | 6 |
| `generate-report-modal.test.tsx` | 5 |
| `offers-tab.test.tsx` | 7 |
| `training-tab.test.tsx` | 6 |
| `transition-demand.test.tsx` | 7 |
| **Total** | **63** |

Todos los mocks MSW están en `__tests__/mocks/handlers.ts`.
