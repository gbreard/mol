# S1 / S2 / S3 — Especificación Detallada de Implementación

> Fecha: 2026-03-24
> Versión: 1.0 — basada en MOL_especificacion_extendida.docx + análisis del código actual
> Autor: análisis conjunto Sergio + Claude

---

## Contexto general

El sistema se organiza como un **motor de skills** con tres servicios sobre él.
El motor ya existe (NLP + matching + ESCO). Los servicios son la capa de UI que lo expone
a distintos usuarios.

```
┌─────────────────────────────────────────────────────────────────┐
│                        MOTOR MOL                                 │
│  16,633 skills ESCO-AR · 3,046 ocupaciones · matching semántico │
│  /api/skills-search · /api/matching-offers · /api/training-*    │
└──────────────┬────────────────┬──────────────────┬──────────────┘
               │                │                  │
         ┌─────▼──────┐  ┌──────▼──────┐  ┌───────▼──────┐
         │  S1         │  │  S2          │  │  S3           │
         │ Trabajador  │  │ Oficina      │  │ Empresa       │
         │ (público)   │  │ (auth OE)    │  │ (QR libre)    │
         └─────────────┘  └─────────────┘  └───────────────┘
```

**Principio de diseño del documento:**
- El mismo candidato puede estar en los 3 servicios al mismo tiempo
- S1 genera un reporte (PDF+QR) → S3 lo consume → S2 lo valida y gestiona
- Los 3 comparten el mismo motor de skills pero con vistas e interfaces distintas

---

# S1 — Mi Futuro Laboral

## Quién es el usuario

**Trabajador** — Persona que quiere conocer sus competencias, ver en qué trabajos encaja,
qué le falta para llegar a donde quiere, y llevarse un documento que lo acredite.

- No necesita cuenta para empezar (modo anónimo)
- Puede registrarse para guardar su perfil y generar reportes con historial
- Es el servicio más público del sistema

## Flujo completo

```
S1-1 LANDING ──► S1-2 ONBOARDING ──► S1-3 CAPTURA ──► S1-4 SKILLS
                                       (4 vías)        (confirmación)
                                                            │
                                                            ▼
S1-9 REPORTE ◄── S1-8 BRECHA ◄─────── S1-7 DESTINO ◄── S1-6 RESULTADOS
(PDF + QR)       (cursos para         (transición       (ocupaciones +
                  cerrar gap)          a dónde ir)        ofertas)
```

## Pantalla por pantalla

### S1-1 — Landing `/mi-futuro-laboral`
**Estado:** ✅ Existe

Propósito: Explicar al trabajador qué puede hacer.
CTA principal: "Empezar ahora" → S1-2 Onboarding

---

### S1-2 — Onboarding `/mi-futuro-laboral/onboarding`
**Estado:** ⬜ Por crear
**Componente a crear:** `OnboardingWizard.tsx`

Una sola pantalla de bienvenida con 3 pasos rápidos:

```
┌─────────────────────────────────────────────────┐
│ ¿Cómo querés empezar?                           │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ 🔍 Buscar    │  │ 📝 Escribir  │             │
│  │ por oficio   │  │ lo que hago  │             │
│  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ 📚 Por       │  │ 🏷️ Ya sé mi  │             │
│  │ título       │  │ ocupación    │             │
│  │ formativo    │  │              │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│ También podés hacerlo anónimo o con tu email    │
└─────────────────────────────────────────────────┘
```

Cada opción lleva a una vía distinta de S1-3.
**No requiere backend nuevo.** Solo routing.

---

### S1-3 — Captura de perfil `/mi-futuro-laboral/perfil`
**Estado:** ⚠️ Parcial (Vía 1 existe: `MySkillsSearch`)
**Componentes existentes:** `MySkillsSearch`, `SkillSearchByTask`, `FreeTextSkillExtractor`, `FormacionSearch`
**Lo que falta:** Ensamblarlos en una sola pantalla con navegación entre vías

**Las 4 vías de captura:**

| Vía | Descripción | Componente | API | Estado |
|-----|-------------|------------|-----|--------|
| Vía 1 | Buscar por ocupación ESCO | `MySkillsSearch` + `OccupationSelector` | `/api/skills-intelligence/occupation` | ✅ Existe |
| Vía 2 | Buscar skills por tarea/keyword | `SkillSearchByTask` | `/api/skills-search` | ✅ Existe |
| Vía 3 | Texto libre ("contá con tus palabras") | `FreeTextSkillExtractor` | `/api/skills-extract-from-text` | ✅ Existe |
| Vía 4 | Buscar por título formativo | `FormacionSearch` | `/api/skills-search` | ✅ Existe |

**Lo que falta en esta pantalla:**
- Integrar las 4 vías en tabs o pasos secuenciales
- Panel lateral derecho que acumula las skills confirmadas (de todas las vías)
- Cada skill usa `SkillWithDefinition` (confirmar ✓ / dudar ? / descartar ✗)
- Botón "Ver mis resultados" activo cuando hay ≥3 skills confirmadas

**No requiere backend nuevo.**

---

### S1-4 — Skills derivadas `/mi-futuro-laboral/perfil` (paso 2)
**Estado:** ✅ Existe como componente separado, necesita integración

Una vez cargadas las skills desde las vías, el sistema sugiere skills relacionadas
que el trabajador no mencionó pero suelen aparecer con las que sí tiene.

**API:** `/api/skills-search?q=...` filtrado por URIs relacionadas (ESCO relatedEssentialSkill)
**Componente:** `SkillWithDefinition` con origen "sugerida"

---

### S1-5 — Enriquecer perfil (datos contextuales)
**Estado:** ⬜ Por crear
**Componente a crear:** parte de la pantalla S1-3/S1-4

Campos opcionales que mejoran el matching:

```
Provincia donde buscás trabajo: [selector]
Modalidad preferida: [Presencial / Remoto / Híbrido]
¿Tenés carnet de conducir? [Sí / No]
Nivel educativo: [selector]
```

**No requiere backend nuevo.** Se pasa como parámetros al matching.

---

### S1-6 — Resultados `/mi-futuro-laboral/resultados`
**Estado:** ⚠️ Parcial (ocupaciones existe, ofertas no conectadas)
**Componentes existentes:** `OccupationCompare`, `OffersTab` (sin conectar)

Layout de 2 columnas:

```
┌───────────────────────┬───────────────────────┐
│  OCUPACIONES          │  OFERTAS REALES        │
│  que encajan         │  del mercado           │
│                       │                        │
│  ● Técnico en IT  87% │  → Empresa X - CABA    │
│    [Ver brecha]       │    Match: 82%          │
│                       │    Gap: Docker, Git    │
│  ● Soporte TI    75%  │                        │
│    [Ver brecha]       │  → Empresa Y - Online  │
│                       │    Match: 71%          │
│  ● Analista datos 60% │    Gap: Python         │
│    [Ver brecha]       │                        │
└───────────────────────┴───────────────────────┘
```

**APIs:**
- Ocupaciones: `/api/occupations/search?skills=...` (inferir ISCO de skills)
- Ofertas: `/api/matching-offers?isco_codes=...&skills=...`

**Lo que falta:** conectar `OffersTab` a `/api/matching-offers` con las skills del perfil.

---

### S1-7 — Elegir destino (transición) `/mi-futuro-laboral/resultados` (tab)
**Estado:** ⬜ Por crear
**Componente existente a reutilizar:** `TransitionDemand`

El trabajador elige hacia dónde quiere ir: su ocupación actual vs una en crecimiento.

```
┌─────────────────────────────────────────────────┐
│ Ocupaciones en crecimiento accesibles para vos  │
│                                                  │
│ → Data Analyst    +34% demanda  · falta: Python  │
│   Match actual: 55%  Meses para llegar: ~3       │
│   [Quiero llegar acá]                            │
│                                                  │
│ → Cloud Engineer  +28% demanda  · falta: AWS     │
│   Match actual: 48%  Meses para llegar: ~6       │
│   [Quiero llegar acá]                            │
└─────────────────────────────────────────────────┘
```

**API:** `/api/training-suggestions?gaps=...&isco_codes=...&worker_skills=...`
**Problema conocido:** `current_match` y `skills_gap` siempre vacíos (ver M4 en plan de mejoras).
**Componente:** `TransitionDemand` (existe, necesita datos reales)

---

### S1-8 — Brecha específica + capacitación `/mi-futuro-laboral/brecha`
**Estado:** ⬜ Por crear
**Componentes existentes a reutilizar:** `TrainingByGap`, `TrainingImpact`

Una vez que eligió el destino, ver exactamente qué le falta y cómo cerrarlo:

```
┌─────────────────────────────────────────────────┐
│ Para ser Data Analyst te faltan 3 competencias  │
│                                                  │
│  ✗ Python           Cursos disponibles:         │
│                     → Fundamentos Python (CABA) │
│                       4 semanas · online        │
│                       [Inscribirme]             │
│                                                  │
│  ✗ SQL avanzado     → SQL para análisis         │
│                       2 semanas · presencial     │
│                                                  │
│  ✗ Tableau          → Sin cursos en tu zona     │
│                       [Buscar en otra región]   │
│                                                  │
│ Si completás Python + SQL → match sube a 89%   │
└─────────────────────────────────────────────────┘
```

**API:** `/api/training-suggestions` (cursos por gap)
**Componentes:** `TrainingByGap` + delta de match de `TrainingImpact`

---

### S1-9 — PDF + QR `/mi-futuro-laboral/reporte`
**Estado:** ⬜ Por crear
**Infraestructura lista:** `lib/generate-report-pdf.ts` + `/api/compatibility-report`

El trabajador genera un reporte que puede compartir con empleadores:

```
┌─────────────────────────────────────────────────┐
│ Tu reporte está listo                           │
│                                                  │
│  [Vista previa del PDF]                          │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ 📄 Reporte Compatibilidad Laboral       │    │
│  │ Juan García · Técnico en IT             │    │
│  │ Compatibilidad: 82%                     │    │
│  │ Válido hasta: 2026-05-24               │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  [⬇ Descargar PDF]  [📋 Copiar link QR]         │
│                                                  │
│  El empleador puede escanear el QR para         │
│  ver tu reporte y personalizar el análisis      │
└─────────────────────────────────────────────────┘
```

**Flujo técnico:**
1. Click "Generar reporte" → `POST /api/compatibility-report` → recibe `token`
2. Generar PDF → `lib/generate-report-pdf.ts` (existe)
3. QR apunta a `/reporte/{token}` (S3-1/S3-2)
4. Si el usuario está logueado, el reporte queda guardado en su historial

**Componente:** `GenerateReportModal` (existe) + nuevo `ReportConfirmation.tsx`

---

## Modelo de datos S1 — lo que ya existe en Supabase

| Tabla | Propósito | Estado |
|-------|-----------|--------|
| `reportes_compatibilidad` | Reportes generados con token | ✅ Existe (migration Gerardo) |
| `worker_profiles` | Perfiles de trabajadores | ✅ Existe vía `/api/worker-profiles` |
| `perfil_argentino_versiones` | Versiones del perfil consolidado | ✅ Existe |

**Lo que falta para S1:**
- Tabla `perfiles_s1` o extender `worker_profiles` con: skills_por_via, destino_elegido, estado_flujo
- (Opcional para MVP anónimo: guardar en `localStorage` y solo persistir si se registra)

---

## MVP de S1 — alcance mínimo funcional

Para tener algo desplegable:

1. S1-2 Onboarding (routing simple, sin backend)
2. S1-3 Captura unificada (ensamblar componentes existentes)
3. S1-6 Resultados con ofertas reales (conectar `OffersTab` a `matching-offers`)
4. S1-9 Generar reporte (conectar `GenerateReportModal`)

**Tiempo estimado:** 3-4 días de desarrollo frontend.

---
---

# S2 — Oficina de Empleo

## Quién es el usuario

**Técnico de OE** — Persona que atiende trabajadores en una Oficina de Empleo pública.
Usa el sistema durante la entrevista para hacer diagnósticos, buscar vacantes y derivar.

- Siempre tiene cuenta (login institucional)
- Pertenece a una organización (multi-tenancy)
- Solo ve datos de su jurisdicción + pool general del MOL en su región
- Sus casos son personas reales con nombre, DNI, situación

## Flujo completo

```
S2-1 IMPORT           S2-2 LOGIN
(cargar personas,  ─► (institucional,
 vacantes, cursos)     OE asignada)
                            │
                            ▼
                       S2-3 PANEL CASOS
                       (lista cartera)
                            │
                    ┌───────┴───────────┐
                    │                   │
               Abrir caso          Nueva atención
                    │                   │
                    ▼                   ▼
              S2-4 PERFIL          S2-4 CREAR CASO
              DEL CASO             (con skills
              (2 columnas)          desde 4 vías)
                    │
                    ├── S2-5 Nota técnico (carnet, motivación)
                    ├── S2-6 Matching vacantes (ver ofertas compatibles)
                    ├── S2-7 Vacante de empresa (empresa trae puesto)
                    ├── S2-8 Formación (cursos para el gap)
                    └── S2-11 Exportar PDF institucional

S2-9 COMPARAR CASOS (entre varios casos de la cartera)
S2-10 INTELIGENCIA LOCAL (tendencias de la jurisdicción)
```

## Pantalla por pantalla

### S2-1 — Hub / Importar datos `/oficina-empleo`
**Estado:** ⚠️ Existe como landing con cards "Próximamente"
**Componente existente:** `OEOnboarding` (onboarding primer ingreso)
**Infraestructura lista:** `lib/parse-pool-import.ts`

Para primer ingreso: importar la planilla Excel/CSV con las personas de la cartera.
Para uso recurrente: acceso directo a Panel de Casos.

```
┌─────────────────────────────────────────────────────────┐
│  Oficina de Empleo — [Nombre OE]                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 👥 Mis casos │  │ 📋 Vacantes  │  │ 📚 Formación │  │
│  │  47 activos  │  │  12 activas  │  │  23 cursos   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  [+ Nueva atención]    [⬆ Importar planilla]            │
│                                                          │
│  ─── Últimas atenciones ────────────────────────────    │
│  · García, Juan  · en diagnóstico  · hace 2h            │
│  · López, María  · derivada        · ayer               │
└─────────────────────────────────────────────────────────┘
```

**Componente a crear:** `OEDashboard.tsx`
**API:** `/api/organizaciones` (stats de la OE) + nueva `/api/casos?org_id=...`

---

### S2-2 — Login institucional
**Estado:** ⬜ Por crear (usa el login existente pero con rol `oficina_empleo`)

El login de Supabase ya funciona. Lo que falta:
- Pantalla de selección de OE al primer login (si el usuario está en múltiples OEs)
- Redirect automático a `/oficina-empleo` después del login si tiene rol OE
- **Requiere Gerardo:** lógica de roles en middleware

---

### S2-3 — Panel de casos `/oficina-empleo/casos`
**Estado:** ⬜ Por crear
**Componente a crear:** `CasosPanel.tsx`

```
┌───────────────────────────────────────────────────────────┐
│  Mis casos  [+ Nueva atención]  [Filtros ▼]               │
│                                                            │
│  Búsqueda: [___________]  Estado: [Todos ▼]  [Buscar]     │
│                                                            │
│  ┌─────┬────────────────┬──────────────────┬───────────┐  │
│  │ DNI │ Nombre         │ Estado           │ Última at │  │
│  ├─────┼────────────────┼──────────────────┼───────────┤  │
│  │ 123 │ García, Juan   │ 🔵 en_diagnóstico│ hoy 10:30 │  │
│  │ 456 │ López, María   │ 🟡 derivada      │ ayer      │  │
│  │ 789 │ Rodríguez, Ana │ 🟢 insertada     │ 2026-03-10│  │
│  └─────┴────────────────┴──────────────────┴───────────┘  │
└───────────────────────────────────────────────────────────┘
```

**Estados del caso y colores:**
| Estado | Color | Significado |
|--------|-------|-------------|
| `nuevo` | ⚪ gris | Ingresó pero no empezó diagnóstico |
| `en_diagnostico` | 🔵 azul | Técnico llenando el perfil |
| `perfil_completo` | 🟣 violeta | Perfil listo, pendiente matching |
| `derivado_vacante` | 🟡 amarillo | Enviado a una oferta de trabajo |
| `derivado_curso` | 🟠 naranja | Enviado a capacitación |
| `en_seguimiento` | 🔵 celeste | Se está monitoreando el resultado |
| `insertado` | 🟢 verde | Consiguió trabajo |
| `cerrado` | ⚫ negro | Caso cerrado sin inserción |

**API necesaria:** `GET /api/casos?org_id=...&estado=...&q=...` ← **Requiere Gerardo**

---

### S2-4 — Perfil del caso `/oficina-empleo/caso/[id]`
**Estado:** ⬜ Por crear
**Componente a crear:** `CasoPerfil.tsx`
**Componentes a reutilizar:** `SkillSearchByTask`, `SkillWithDefinition`, `SkillsMapEditable`

Layout 2 columnas fijo:

```
┌────────────────────┬───────────────────────────────────────┐
│ COLUMNA IZQUIERDA  │ COLUMNA DERECHA — TABS                 │
│ (datos fijos)      │                                        │
│                    │ [Skills] [Matching] [Formación] [Nota] │
│ Juan García        │                                        │
│ DNI: 12.345.678    │ TAB SKILLS:                           │
│ 34 años            │   Desde Vía 1 (ocupación):            │
│ CABA               │   ● Python ✓                          │
│ Secundario compl.  │   ● SQL ✓                             │
│                    │   ● Excel ?                           │
│ Estado:            │                                        │
│ [🔵 en_diagnóstico]│   Agregar skills: [buscar...]         │
│                    │                                        │
│ Técnico: Ana M.    │ TAB MATCHING:                         │
│ Desde: 2026-03-20  │   → [Ver S2-6]                        │
│                    │                                        │
│ [Cambiar estado ▼] │ TAB FORMACIÓN:                        │
│ [Exportar PDF]     │   → [Ver S2-8]                        │
│                    │                                        │
│                    │ TAB NOTA TÉCNICO:                     │
│                    │   → [Ver S2-5]                        │
└────────────────────┴───────────────────────────────────────┘
```

**APIs:**
- `GET /api/casos/[id]` → datos del caso ← **Requiere Gerardo**
- `/api/skills-search` → buscar skills para agregar ← existe
- `PATCH /api/casos/[id]` → cambiar estado ← **Requiere Gerardo**

---

### S2-5 — Nota del técnico (tab dentro de S2-4)
**Estado:** ⬜ Por crear

Campos que solo puede completar el técnico (no derivables del motor):

```
┌─────────────────────────────────────────────────┐
│ Nota del técnico                                │
│                                                  │
│ Licencia de conducir: [Ninguna ▼]               │
│ Vehículo propio: [ ] Sí                         │
│ Disponibilidad horaria: [Full time ▼]           │
│ Expectativa salarial: [___________]             │
│                                                  │
│ Motivación y situación:                         │
│ ┌────────────────────────────────────────────┐  │
│ │ Texto libre — contexto del técnico        │  │
│ └────────────────────────────────────────────┘  │
│                                                  │
│ [Guardar nota]                                   │
└─────────────────────────────────────────────────┘
```

**API:** `PATCH /api/casos/[id]` con campo `nota_tecnico` ← **Requiere Gerardo**

---

### S2-6 — Matching con vacantes (tab dentro de S2-4)
**Estado:** ⬜ Por crear
**Componente a reutilizar:** `OffersTab` + `GenerateReportModal`

Muestra las ofertas del mercado que más encajan con el caso:

```
┌─────────────────────────────────────────────────────────┐
│ Vacantes compatibles para Juan García                    │
│ Filtros: [Provincia ▼] [Modalidad ▼] [Score mín: 60%]  │
│                                                          │
│ ┌───────────────────────────────────────────────────┐   │
│ │ Técnico IT Junior — Empresa XYZ            [82%]  │   │
│ │ CABA · Presencial · hace 3 días                   │   │
│ │ Cubre: Python, SQL · Falta: Docker               │   │
│ │ [Ver oferta] [Derivar →] [Generar reporte QR]    │   │
│ └───────────────────────────────────────────────────┘   │
│                                                          │
│ ┌───────────────────────────────────────────────────┐   │
│ │ Analista de datos — Startup ABC             [71%]  │   │
│ │ GBA · Híbrido · hace 1 semana                     │   │
│ │ Cubre: Python · Falta: Tableau, Power BI         │   │
│ │ [Ver oferta] [Derivar →] [Generar reporte QR]    │   │
│ └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**APIs:**
- `/api/matching-offers?isco_codes=...&skills=...&provincia=...` ← existe
- `POST /api/compatibility-report` al generar reporte QR ← existe
- `POST /api/derivaciones` al derivar ← **Requiere Gerardo**

**"Derivar"** crea una derivación en estado `derivado` y cambia el estado del caso a `derivado_vacante`.

---

### S2-7 — Gestión de vacantes / empresa trae puesto
**Estado:** ⬜ Por crear
**Componente a reutilizar:** `JobProfileForm` (ya existe — S18)

Cuando una empresa contacta a la OE con un puesto, el técnico lo carga y el sistema
rankea la cartera de casos por match:

```
┌─────────────────────────────────────────────────┐
│ Nueva vacante de empresa                        │
│                                                  │
│ Empresa: [___________]                           │
│ Puesto: [___________]                            │
│ Competencias requeridas: [buscar skills...]      │
│   ● Atención al cliente (requerida)             │
│   ● Caja registradora (requerida)               │
│   ● Excel (deseable)                            │
│                                                  │
│ [Buscar candidatos en mi cartera]               │
│                                                  │
│ ─── Ranking de mi cartera ──────────────────    │
│ 1. López, María     [88%] — falta: Excel        │
│ 2. García, Juan     [72%] — falta: Caja         │
│ [Derivar ▼]                                     │
└─────────────────────────────────────────────────┘
```

**API:** `/api/matching-offers` en modo inverso (skills de vacante → buscar en pool OE)
**Componente:** `JobProfileForm` + nueva lógica de "buscar en cartera"

---

### S2-8 — Formación (tab dentro de S2-4)
**Estado:** ⬜ Por crear
**Componente a reutilizar:** `TrainingByGap`, `TrainingImpact` (S17)

Qué cursos hay en la jurisdicción para cerrar el gap del caso:

```
┌─────────────────────────────────────────────────┐
│ Formación para Juan García                      │
│ Gap identificado: Docker, Git, Bash             │
│                                                  │
│ [Pool OE] [Pool MOL] [Ambos]                    │
│                                                  │
│ Docker:                                         │
│ → Administración de contenedores — CGPC          │
│   3 semanas · presencial · CABA                 │
│   Si completa: match sube de 82% a 91%          │
│   [Inscribir] [Derivar a este curso]            │
│                                                  │
│ Git:                                            │
│ → Control de versiones — Min. Trabajo           │
│   Online · 2 semanas                            │
│   [Inscribir]                                   │
└─────────────────────────────────────────────────┘
```

**API:** `/api/training-suggestions?gaps=...&isco_codes=...` ← existe
**"Derivar a este curso"** crea derivación en estado `derivado` y cambia caso a `derivado_curso`.

---

### S2-9 — Comparar casos `/oficina-empleo/comparar`
**Estado:** ⬜ Por crear (v2, baja prioridad)

Comparar el perfil de skills de 2 o más casos de la cartera.
Útil para decidir a quién derivar cuando hay una sola vacante.

---

### S2-10 — Inteligencia local `/oficina-empleo/inteligencia`
**Estado:** ⬜ Por crear (v2)
**Componente a reutilizar:** pantalla S16 ya construida (`/admin/inteligencia-local` tipo)

Dashboard de tendencias del mercado en la jurisdicción de la OE:
- Skills más demandadas en la provincia
- Brechas frecuentes de la cartera vs el mercado
- Cursos con mayor impacto en inserción

**API:** `/api/inteligencia-local?provincia=...` ← existe (fue S16)

---

### S2-11 — PDF institucional
**Estado:** ⬜ Por crear
**Infraestructura lista:** `lib/generate-report-pdf.ts`

PDF con membrete de la OE + firma del técnico + perfil completo del caso.
Distinto al PDF de S1 (más formal, incluye nota técnica).

**Flujo:** botón "Exportar PDF" en S2-4 → llama `generate-report-pdf.ts` con plantilla OE.

---

## Modelo de datos S2 — LO QUE FALTA (requiere Gerardo)

```sql
-- Tabla principal de casos
CREATE TABLE casos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizaciones(id),
  tecnico_id UUID REFERENCES auth.users(id),
  nombre VARCHAR(200) NOT NULL,
  dni VARCHAR(20),
  edad INTEGER,
  provincia VARCHAR(100),
  nivel_educativo VARCHAR(50),
  estado VARCHAR(50) DEFAULT 'nuevo',
  -- estados: nuevo | en_diagnostico | perfil_completo |
  --          derivado_vacante | derivado_curso | en_seguimiento |
  --          insertado | cerrado
  skills_json JSONB,              -- array de { uri, label, estado: confirmo|duda|descarto, via }
  nota_tecnico JSONB,             -- carnet, motivacion, disponibilidad, etc.
  perfil_id UUID,                 -- link a worker_profiles si tiene cuenta S1
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de derivaciones
CREATE TABLE derivaciones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  caso_id UUID REFERENCES casos(id),
  tipo VARCHAR(20) NOT NULL,      -- 'vacante' | 'curso'
  referencia_id VARCHAR(200),     -- id_oferta o id_curso
  referencia_label VARCHAR(300),  -- nombre de la oferta/curso
  match_score INTEGER,
  estado VARCHAR(30) DEFAULT 'derivado',
  -- estados: derivado | entrevistado | rechazado | aceptado
  fecha_derivacion TIMESTAMPTZ DEFAULT NOW(),
  fecha_resultado TIMESTAMPTZ,
  nota VARCHAR(500),
  created_by UUID REFERENCES auth.users(id)
);
```

**APIs que Gerardo necesita crear:**
- `GET/POST /api/casos` — listar y crear casos
- `GET/PATCH /api/casos/[id]` — ver y actualizar un caso
- `GET/POST /api/derivaciones` — listar y crear derivaciones
- `PATCH /api/derivaciones/[id]` — actualizar estado (entrevistado, aceptado, etc.)

---

## MVP de S2 — alcance mínimo funcional

1. S2-3 Panel de casos (lista con estados)
2. S2-4 Perfil del caso (datos + tab Skills)
3. S2-6 Matching con vacantes (usando `/api/matching-offers`)
4. S2-1 Import CSV (usando `parse-pool-import.ts`)

**Bloqueante:** migrations + APIs de Gerardo (`casos`, `derivaciones`).
**Tiempo estimado post-unblocking:** 4-5 días de desarrollo frontend.

---
---

# S3 — Empresas

## Quién es el usuario

**Empresa/reclutador** — Dos tipos:

- **Libre (sin cuenta):** Recibe un link QR del candidato o de la OE. Ve el reporte de compatibilidad.
- **Registrada (v2):** Tiene cuenta, publica búsquedas, ve candidatos, usa inteligencia de mercado.

El MVP está 100% orientado al usuario libre.

## Flujo MVP (S3-1, S3-2, S3-3)

```
El trabajador genera su reporte (S1-9)
          │
          ▼ QR o link
Empresa escanea → /reporte/{token}
          │
          ▼
S3-2 Reporte de compatibilidad (sin auth)
          │
          ├── Ver skills del candidato
          ├── Ver match % vs la ocupación
          ├── Ver el gap (qué le falta)
          │
          ▼ (opcional)
S3-3 Personalizar competencias
          │
          ├── Quitar skills que no les importan
          ├── Agregar skills que necesitan
          └── Ver cómo cambia el match %
```

## Pantalla por pantalla

### S3-1 — Acceso vía QR `/reporte/[token]`
**Estado:** ✅ Existe (la ruta ya funciona, tiene manejo de expirado/revocado)

La URL del QR apunta directamente a `/reporte/{token}`. No hay una pantalla S3-1 separada:
el token es la "auth". El servidor valida y muestra o devuelve error.

**Fix pendiente (bug):** el fetch devuelve `{ report: data }` pero se usa `data` directo.
(Ver T1 en plan de mejoras — ya parcialmente corregido)

---

### S3-2 — Reporte de compatibilidad `/reporte/[token]`
**Estado:** ✅ Existe (`CompatibilityReport.tsx`)

Lo que ya muestra:
- Datos del candidato (nombre, ocupación, ISCO)
- Score de compatibilidad con barra de color
- Skills cubiertas / gap
- Fecha y versión del perfil consolidado
- Matriz de afinidad (`AffinityMatrix`)

Lo que falta:
- Mostrar `oferta_titulo` si el reporte fue generado para una vacante específica
- Botón "Descargar PDF" (conectar a `generate-report-pdf.ts`)
- Sección "Verificado por OE" si el reporte viene de S2 (badge institucional)

---

### S3-3 — Personalizar competencias (dentro de `/reporte/[token]`)
**Estado:** ⚠️ UI existe, falta persistir

El componente `CompatibilityReport` ya tiene:
- `SkillsMapEditable` con edición de skills requeridas
- `isEdited` flag
- `handleRestore` (restaurar original)
- Recálculo dinámico del score

**Lo que falta:**
- Botón "Guardar mis ajustes" cuando `isEdited = true`
- Llamar `PATCH /api/compatibility-report` con las skills personalizadas
- (Esto NO modifica el reporte original del candidato — crea una "vista empresa")

**Diseño del botón:**
```tsx
{isEdited && (
  <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 flex items-center justify-between">
    <p className="text-sm text-blue-700">
      Modificaste {n} competencias. El score recalculado es {score}%
    </p>
    <div className="flex gap-2">
      <button onClick={handleRestore}>Restaurar</button>
      <button onClick={handleSave}>Guardar mis ajustes</button>
    </div>
  </div>
)}
```

---

### S3 v2 — Registrada (futuro, no MVP)

Las pantallas S3-4 a S3-12 son todas v2. No se implementan en esta fase.
Quedan documentadas en `docs/plan/02_ARQUITECTURA_PANTALLAS.md`.

---

## Modelo de datos S3 — lo que ya existe

| Tabla | Propósito | Estado |
|-------|-----------|--------|
| `reportes_compatibilidad` | Reportes con token, vistas, expiración | ✅ Existe |

El campo `skills_requeridas` en el reporte puede almacenar la versión personalizada
por la empresa si se hace PATCH. El reporte original queda en `skills_requeridas_original`
(nuevo campo que habría que agregar) o simplemente se sobreescribe (decisión de Gerardo).

---
---

# Dependencias entre S1, S2 y S3

```
S1 genera reporte ──────────────────► S3 consume reporte
     │                                     │
     │ (opt-in del trabajador)             │ (si OE valida)
     ▼                                     ▼
S2 gestiona el caso ──► La OE valida el perfil S1 → badge "verificado OE" en S3
```

**Vínculo S1 ↔ S2:** El técnico busca al trabajador por DNI (S2-3).
Si el trabajador tiene perfil S1, los datos se pre-cargan en el caso S2.
Si no tiene, el técnico construye el perfil desde cero en S2-4.

**Vínculo S2 → S3:** La OE genera un reporte QR para una derivación específica
(`POST /api/compatibility-report` con `origen: 'oficina_empleo'`).
La empresa recibe el link, lo abre en S3-2/S3-3.

---

# Resumen de implementación por prioridad

## Sprint A — Sin backend nuevo (Sergio solo)
| Tarea | Servicio | Effort |
|-------|----------|--------|
| Fix bug fetchReport | S3 | 🟢 1h |
| S3-3 botón guardar ajustes (PATCH) | S3 | 🟢 2h |
| S1-3 unificar 4 vías en una pantalla | S1 | 🟡 4h |
| S1-6 conectar OffersTab a matching-offers | S1 | 🟡 3h |
| S1-9 conectar GenerateReportModal | S1 | 🟡 3h |
| S2-1 import CSV (parse-pool-import.ts) | S2 | 🟡 4h |

## Sprint B — Con backend nuevo (requiere Gerardo)
| Tarea | Servicio | Bloqueante |
|-------|----------|------------|
| S2-3 Panel de casos | S2 | `GET /api/casos` |
| S2-4 Perfil del caso | S2 | `GET/PATCH /api/casos/[id]` |
| S2-6 Matching + derivar | S2 | `POST /api/derivaciones` |
| S2-5 Nota técnico | S2 | `PATCH /api/casos/[id]` |
| S2-11 PDF institucional | S2 | plantilla OE en generate-pdf |

## Sprint C — Completar flujos (ambos)
| Tarea | Servicio | Effort |
|-------|----------|--------|
| S1-7 Transición (TransitionDemand real) | S1 | 🟡 (fix M4) |
| S1-8 Brecha + capacitación | S1 | 🟡 3h |
| S2-7 Empresa trae vacante | S2 | 🟠 6h |
| S2-10 Inteligencia local | S2 | 🟠 4h |

---
---

# SECCIONES FALTANTES — Agregadas 2026-03-25

---

## S2 — Pantallas faltantes

### S2-0 — Onboarding OE (primera vez) `/oficina-empleo/onboarding`
**Estado:** ⚠️ Existe como wireframe vacío
**Componente a crear:** `OEOnboardingWizard.tsx`
**Cuándo se muestra:** Solo al primer login de la OE. Después redirige directo al hub.

Flujo de 3 pasos con stepper visible:

```
┌─────────────────────────────────────────────────────────┐
│  Configuración inicial — Oficina de Empleo               │
│                                                          │
│  [1 Personas] ──── [2 Vacantes] ──── [3 Cursos]         │
│       ▲                                                  │
│       │ activo                                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Paso 1: Importar cartera de personas             │  │
│  │                                                   │  │
│  │  Subí tu planilla Excel o CSV con las personas    │  │
│  │  registradas en la oficina.                       │  │
│  │                                                   │  │
│  │  Columnas requeridas: nombre, dni                 │  │
│  │  Columnas opcionales: edad, nivel_educativo,      │  │
│  │                       ultimo_trabajo, provincia   │  │
│  │                                                   │  │
│  │  [⬆ Subir archivo]  o  [Omitir este paso →]      │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Después de subir el archivo — Preview antes de confirmar:**

```
┌─────────────────────────────────────────────────────────┐
│  Vista previa de importación                             │
│                                                          │
│  Total: 150 filas   ✅ Válidas: 142   ⚠️ Errores: 8    │
│                                                          │
│  ┌──────────────┬────────────┬──────────────────────┐   │
│  │ Nombre       │ DNI        │ Estado               │   │
│  ├──────────────┼────────────┼──────────────────────┤   │
│  │ García, Juan │ 32.456.789 │ ✅ OK                │   │
│  │ López, Ana   │ —          │ ⚠️ DNI faltante      │   │
│  │ Torres, P.   │ 28.111.222 │ ✅ OK                │   │
│  └──────────────┴────────────┴──────────────────────┘   │
│                                                          │
│  [← Volver]                    [Confirmar importación →]│
└─────────────────────────────────────────────────────────┘
```

**Paso 2 y 3** tienen el mismo patrón: subir CSV, preview, confirmar.

**Vacantes** — columnas: `empresa`, `puesto`, `descripcion` (sistema mapea a ESCO).
**Cursos** — columnas: `nombre`, `institucion`, `duracion`, `modalidad`.

**APIs:** `POST /api/import-pool/personas`, `/api/import-pool/vacantes`, `/api/import-pool/cursos` ← Requiere Gerardo

**Al finalizar:** redirige al hub con los datos cargados.

---

### S2-12 — Lista de vacantes de la OE `/oficina-empleo/vacantes`
**Estado:** ⬜ No existe
**Componente a crear:** `VacantesOEList.tsx`

Gestión del pool propio de vacantes que traen las empresas locales:

```
┌─────────────────────────────────────────────────────────┐
│  Vacantes activas  [+ Nueva vacante]  [Filtros ▼]        │
│                                                          │
│  Búsqueda: [___________]  Estado: [Activa ▼]  [Buscar]  │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Operario textil — Textil del Norte SA      🟢 Activa │ │
│ │ Skills: costura, corte de telas, máquina plana       │ │
│ │ 12 candidatos compatibles en cartera                 │ │
│ │ [Ver candidatos] [Editar] [Cerrar vacante]           │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Cajero/a — Supermercado Norte                🟡 En   │ │
│ │                                              proceso  │ │
│ │ Skills: atención al cliente, caja, stock             │ │
│ │ 3 candidatos en proceso de entrevista                │ │
│ │ ⚠️ 0 candidatos con match > 70%                      │ │
│ │ [Ver candidatos] [Editar]                            │ │
│ └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Estados de vacante y colores:**
| Estado | Color | Qué significa |
|--------|-------|---------------|
| `activa` | 🟢 verde | Buscando candidatos |
| `en_proceso` | 🟡 amarillo | Hay candidatos en entrevista |
| `cubierta` | 🔵 azul | Posición ocupada |
| `cerrada` | ⚫ gris | Cerrada sin cubrir |

**Alerta especial:** Si la vacante tiene 0 candidatos con match ≥ 50%, mostrar banner naranja
"No hay candidatos suficientes en tu cartera para este puesto."

**API:** `GET /api/vacantes-oe?org_id=X&estado=Y` ← Requiere Gerardo

---

### S2-13 — Nueva vacante `/oficina-empleo/vacantes/nueva`
**Estado:** ⬜ No existe
**Componente a reutilizar:** `JobProfileForm` (S18) + nueva lógica de preview ESCO

```
┌─────────────────────────────────────────────────────────┐
│  Cargar vacante de empresa                               │
│                                                          │
│  Empresa: [___________________________________________]  │
│  Nombre del puesto: [__________________________________] │
│                                                          │
│  Descripción del puesto (lenguaje libre):               │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Buscamos una persona para atender clientes en     │ │
│  │ mostrador, manejar caja registradora y             │ │
│  │ controlar el stock...                              │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [Extraer competencias automáticamente →]               │
└─────────────────────────────────────────────────────────┘
```

**Después de extraer — preview del mapeo ESCO:**

```
┌─────────────────────────────────────────────────────────┐
│  Competencias detectadas                                 │
│  Revisá y ajustá antes de confirmar                     │
│                                                          │
│  ● Atención al cliente         [✓ Confirmar] [✗]        │
│  ● Operación de caja           [✓ Confirmar] [✗]        │
│  ● Gestión de inventario       [✓ Confirmar] [✗]        │
│  ● Manejo de efectivo          [✓ Confirmar] [✗]        │
│                                                          │
│  + Agregar competencia: [buscar en ESCO...]             │
│                                                          │
│  [← Volver a editar]     [Confirmar y publicar →]       │
└─────────────────────────────────────────────────────────┘
```

**Flujo técnico:**
1. Técnico escribe descripción → click "Extraer competencias"
2. API extrae skills ESCO (mismo motor que el pipeline NLP)
3. Muestra preview editable — técnico confirma, quita o agrega
4. "Confirmar" → crea vacante en `vacantes_oe` con estado `activa`
5. Redirige a `/oficina-empleo/vacantes/[id]` para ver candidatos

**APIs:**
- `POST /api/vacantes-oe` con descripción → devuelve skills sugeridas ← Requiere Gerardo
- `GET /api/skills-search` para agregar skills manualmente ← existe

---

### S2-14 — Detalle de vacante + candidatos rankeados `/oficina-empleo/vacantes/[id]`
**Estado:** ⬜ No existe
**Componente a crear:** `VacanteDetalle.tsx`

```
┌────────────────────┬───────────────────────────────────┐
│ VACANTE            │ CANDIDATOS DE MI CARTERA           │
│                    │                                    │
│ Operario textil    │ Ordenados por match (mayor→menor) │
│ Textil del Norte   │                                    │
│ 🟢 Activa          │ ┌──────────────────────────────┐  │
│                    │ │ López, María          [88%]  │  │
│ Skills requeridas: │ │ Falta: máquina plana         │  │
│ ● costura          │ │ [Ver caso] [Derivar →]       │  │
│ ● corte de telas   │ └──────────────────────────────┘  │
│ ● máquina plana    │                                    │
│                    │ ┌──────────────────────────────┐  │
│ Benchmark:         │ │ García, Juan          [72%]  │  │
│ 65% de la cartera  │ │ Falta: costura, plana        │  │
│ tiene ≥1 skill     │ │ [Ver caso] [Derivar →]       │  │
│                    │ └──────────────────────────────┘  │
│ [Cerrar vacante]   │                                    │
│ [Editar skills]    │ Benchmark territorial:             │
│                    │ 18% del mercado tiene estas skills │
└────────────────────┴───────────────────────────────────┘
```

**"Derivar →"** abre un modal que crea una derivación directamente desde la vacante,
sin tener que ir al caso primero. Actualiza el estado del caso a `derivado_vacante`.

**APIs:**
- `GET /api/vacantes-oe/[id]` ← Requiere Gerardo
- `GET /api/matching-candidates?vacante_id=X&org_id=Y` ← Requiere Gerardo (C2)

---

### S2-15 — Catálogo de cursos `/oficina-empleo/cursos`
**Estado:** ⬜ No existe
**Componente a crear:** `CursosOEList.tsx`

```
┌─────────────────────────────────────────────────────────┐
│  Catálogo de cursos  [+ Agregar curso]  [⬆ Importar]    │
│                                                          │
│  Filtros: [Modalidad ▼] [Skills ▼]                      │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Administración de contenedores (Docker)              │ │
│ │ CGPC · 3 semanas · Presencial · Gratuito             │ │
│ │ Skills: Docker, contenedores, DevOps                 │ │
│ │ Impacto: 23 personas de la cartera se benefician     │ │
│ │ [Ver detalle] [Derivar candidato]                    │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ ⚠️ Brechas sin cobertura de formación:                   │
│ → Python (38 personas lo necesitan, 0 cursos en tu OE)  │
│ → Excel avanzado (12 personas, 0 cursos)                │
│ [Buscar cursos en el catálogo MOL →]                    │
└─────────────────────────────────────────────────────────┘
```

**Sección de alertas de brecha:** lista las skills más frecuentes en el gap de la cartera
que no tienen ningún curso en el catálogo de la OE. Es insumo para que la OE gestione
la apertura de nuevos cursos.

**API:** `GET /api/training-impact` con `org_id` para calcular impacto en la cartera real ← existe

---

## S3 — Pantallas faltantes (modo activo v2)

> Estas pantallas corresponden a la **Etapa 3** del roadmap.
> No son MVP. Se documentan para tener el diseño listo cuando llegue el momento.

### S3-4 — Landing empresas `/empresas`
**Estado:** ⬜ No existe
**Componente a crear:** `EmpresasLanding.tsx`

```
┌─────────────────────────────────────────────────────────┐
│  MOL para Empresas                                       │
│  Encontrá candidatos por competencias reales,           │
│  no por palabras clave en el CV.                        │
│                                                          │
│  [Modo libre]              [Crear cuenta empresa]        │
│  Recibís un QR →           Publicar búsquedas +         │
│  análisis inmediato        Candidatos rankeados +        │
│                            Inteligencia de mercado       │
│                                                          │
│  ─── Ya estás usando MOL si ────────────────────        │
│  "Escaneaste el QR de un candidato en entrevista"        │
│  [Ver análisis del candidato →]                          │
└─────────────────────────────────────────────────────────┘
```

**Sin backend.** Solo routing y copy.

---

### S3-5 — Dashboard empresa `/empresas/dashboard`
**Estado:** ⬜ No existe
**Componente a crear:** `EmpresaDashboard.tsx`

```
┌─────────────────────────────────────────────────────────┐
│  TechStartup SA — Dashboard                              │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ Búsquedas    │ │ Candidatos   │ │ Match         │    │
│  │ activas: 3   │ │ evaluados:42 │ │ promedio: 74% │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                          │
│  ─── Búsquedas activas ─────────────────────────        │
│  · Dev Senior React  · 12 candidatos · match avg 68%    │
│  · Data Analyst      · 8 candidatos  · match avg 71%    │
│                                                          │
│  ─── Últimas evaluaciones QR ──────────────────         │
│  · Candidato anónimo · Dev React · 82% · hace 2h        │
│  · Candidato anónimo · Data Ana. · 65% · ayer           │
└─────────────────────────────────────────────────────────┘
```

**Requiere:** autenticación de empresa (Supabase auth + rol `empresa`).

---

### S3-6 — Mis vacantes empresa `/empresas/vacantes`
**Estado:** ⬜ No existe
**Componente a crear:** `EmpresaVacantesList.tsx`

Similar a S2-12 pero desde la perspectiva de la empresa. Pool de candidatos = todos con `opt_in=true`.

---

### S3-7 — Nueva vacante empresa `/empresas/vacantes/nueva`
**Estado:** ⬜ No existe
**Reutiliza:** mismo flujo que S2-13 (descripción libre → ESCO → confirmar).

Diferencia: la empresa ve el pool MOL (candidatos con opt-in) en lugar de la cartera OE.

---

### S3-8 — Candidatos de vacante `/empresas/vacantes/[id]`
**Estado:** ⬜ No existe
**Componente a crear:** `EmpresaCandidatosRanking.tsx`

```
┌─────────────────────────────────────────────────────────┐
│  Dev Senior React — Candidatos del mercado               │
│                                                          │
│  Total con opt-in activo: 28 candidatos                 │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Candidato #1                               [91%]   │  │
│ │ React, TypeScript, Next.js, Node ✓                 │  │
│ │ Falta: GraphQL                                     │  │
│ │ Skills validadas por OE: sí                        │  │
│ │ [Ver reporte completo →] [Comparar]                │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ NOTA: Los datos de contacto no se muestran.             │
│ El candidato puede autorizar el contacto desde S1.      │
└─────────────────────────────────────────────────────────┘
```

**Privacidad:** Nombre y datos de contacto nunca se muestran. Si el candidato tiene opt-in
pero sin datos de contacto compartidos, la empresa debe enviar solicitud de contacto
(flujo futuro — Etapa 4).

**API:** `GET /api/matching-candidates?vacante_id=X&pool=mol` ← Requiere Gerardo (C2)

---

### S3-9 — Perfiles de puesto guardados `/empresas/perfiles-puesto`
**Estado:** ⬜ No existe
**Componente a crear:** `PerfilesPuesto.tsx`

Biblioteca de mapas de skills por rol. La empresa los reutiliza en múltiples búsquedas
para garantizar comparación homogénea entre candidatos.

```
┌─────────────────────────────────────────────────────────┐
│  Perfiles de puesto  [+ Crear perfil]                    │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Dev Senior React                        Usado 3 veces│ │
│ │ 12 skills · actualizado 2026-03-10                   │ │
│ │ [Usar en nueva búsqueda] [Editar] [Duplicar]         │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Data Analyst                            Usado 1 vez  │ │
│ │ 9 skills · actualizado 2026-02-20                    │ │
│ │ [Usar en nueva búsqueda] [Editar] [Duplicar]         │ │
│ └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

### S3-10 — Comparar candidatos `/empresas/comparar`
**Estado:** ⬜ No existe
**Componente a crear:** `CandidatosComparar.tsx`

Vista side-by-side de 2 candidatos evaluados contra el mismo perfil de puesto:

```
┌─────────────────────────────────────────────────────────┐
│  Comparar candidatos — Dev Senior React                  │
│                                                          │
│           Candidato A          Candidato B               │
│           91%                  78%                       │
│                                                          │
│ React     ✓                    ✓                         │
│ TypeScript✓                    ✓                         │
│ Next.js   ✓                    ✓                         │
│ Node.js   ✓                    ✓                         │
│ GraphQL   ✗ falta              ✓                         │
│ Docker    ✗ falta              ✗ falta                   │
│           Falta: 1             Falta: 1                  │
│                                                          │
│ Val. OE   ✓ sí                 ✗ no                      │
│                                                          │
│ Diferencias resaltadas en naranja                        │
└─────────────────────────────────────────────────────────┘
```

**Criterio de desempate sugerido por el sistema:**
Si el match es igual, priorizar candidatos con validación OE.

---

## S1 — Pantallas faltantes / más detalle

### S1-2 — Onboarding `/mi-futuro-laboral/onboarding` (detalle completo)
**Estado:** ⬜ Por crear
**Componente a crear:** `S1Onboarding.tsx`

Pantalla de bienvenida — única, no stepper. Captura nombre y propósito:

```
┌─────────────────────────────────────────────────────────┐
│          Mi Futuro Laboral                               │
│                                                          │
│  En menos de 5 minutos vas a saber:                     │
│  · Qué trabajos encajan con lo que sabés hacer           │
│  · Qué te falta para llegar a donde querés ir           │
│  · Un documento listo para llevar a la entrevista        │
│                                                          │
│  Tu nombre (para el reporte):                           │
│  [_________________________________________________]    │
│                                                          │
│  ¿Para qué lo usás hoy?                                 │
│  ○ Busco trabajo                                        │
│  ○ Quiero cambiar de rubro                              │
│  ○ Quiero saber qué vale lo que sé                      │
│  ○ Me mandaron desde la Oficina de Empleo               │
│                                                          │
│                     [Empezar →]                         │
│                                                          │
│  No necesitás crear cuenta. Podés guardar tu perfil     │
│  al final si querés.                                    │
└─────────────────────────────────────────────────────────┘
```

**Estado local:** nombre y propósito se guardan en `sessionStorage`. No requiere backend.

**Si viene "desde la OE":** mostrar mensaje especial: "Tu técnico de la Oficina de Empleo
puede ver tu perfil cuando lo construyas."

---

### S1-5 — Datos contextuales (parte de la pantalla de captura)

Aparece como sección colapsable al final de S1-3, después de agregar las primeras skills:

```
┌─────────────────────────────────────────────────────────┐
│  [▾] Mejorá tu búsqueda (opcional)                       │
│                                                          │
│  ¿Dónde buscás trabajo?                                 │
│  [Provincia ▼]  [Ciudad ___________]                    │
│                                                          │
│  Modalidad preferida:                                   │
│  [✓] Presencial  [✓] Remoto  [ ] Solo remoto            │
│                                                          │
│  Nivel educativo:                                       │
│  [Secundario completo ▼]                                │
│                                                          │
│  ¿Tenés carnet de conducir?  [ ] Sí                     │
└─────────────────────────────────────────────────────────┘
```

Estos datos se pasan como parámetros de filtro a `/api/matching-offers`.

---

## Flujos transversales completos

### Flujo F1 — Trabajador completo (S1 → S3)

```
1. /mi-futuro-laboral          → Landing, click "Empezar"
2. /mi-futuro-laboral/onboarding → Nombre + propósito
3. /mi-futuro-laboral/perfil   → Agregar skills (Vías 1-4)
                                  Panel derecho acumula skills confirmadas
                                  Barra de completitud: 0 → 1 → 2 → [3+ desbloquea]
4. /mi-futuro-laboral/resultados → Tabs: Ocupaciones / Ofertas / Formación
5. /mi-futuro-laboral/brecha   → Elegir destino → ver gap exacto + cursos
6. /mi-futuro-laboral/reporte  → Preview PDF → [Descargar] + [Copiar link QR]
7. mol.gob.ar/reporte/[token]  → Empresa escanea QR → ve reporte S3
```

---

### Flujo F2 — Técnico OE atendiendo un caso (S2)

```
1. /oficina-empleo             → Hub con KPIs
2. /oficina-empleo/cartera     → Buscar por DNI → encontró → abrir caso
                                                → no encontró → [+ Nuevo caso]
3. /oficina-empleo/cartera/nueva → Formulario persona → crear caso (estado: nuevo)
4. /oficina-empleo/cartera/[id] → Vista de caso
   Tab "Skills":  cargar skills por las 4 vías
                  caso → en_diagnostico → (3 skills) → perfil_completo
   Tab "Matching": ver vacantes compatibles
                   [Derivar →] → modal → caso → derivado_vacante
                   [Generar QR] → reporte para que el trabajador lleve a entrevista
   Tab "Formación": ver cursos para el gap
                   [Derivar →] → caso → derivado_curso
   Tab "Nota": carnet, motivación, checkboxes
5. Seguimiento: técnico actualiza la derivación (entrevistado / aceptado / rechazado)
               Si aceptado → caso → insertado  ✅
               Si rechazado → caso vuelve a perfil_completo → nueva derivación
```

---

### Flujo F3 — Empresa recibe candidato vía QR (S3 modo pasivo)

```
1. Trabajador le manda el link o el reclutador escanea el QR físico
2. /reporte/[token]           → carga sin login
3. Ve: nombre, ocupación, match%, skills cubiertas, skills faltantes
4. (Opcional) Personaliza skills: agrega/quita según su empresa
   → score recalcula en tiempo real
   → [Guardar mis ajustes] persiste la vista empresa
5. Si le interesa más → [Crear cuenta empresa →] → S3 modo activo
```

---

### Flujo F4 — Empresa carga vacante en OE (S2-7 empresa trae puesto)

```
1. Empresa llama a la OE con una vacante
2. Técnico va a /oficina-empleo/vacantes/nueva
3. Escribe descripción libre del puesto
4. Sistema extrae skills ESCO → técnico confirma/ajusta
5. Vacante creada en pool OE
6. Sistema rankea automáticamente la cartera por match
7. Técnico ve ranking → elige candidatos → deriva
8. Puede generar reporte QR para cada candidato derivado
   → empresa recibe link → accede en S3-2 sin login
```

---

## Resumen de pantallas por estado (actualizado)

| ID | Pantalla | Ruta | S1/S2/S3 | Estado |
|----|----------|------|----------|--------|
| S1-1 | Landing | `/mi-futuro-laboral` | S1 | ✅ Existe |
| S1-2 | Onboarding | `/mi-futuro-laboral/onboarding` | S1 | ⬜ Crear |
| S1-3 | Captura 4 vías | `/mi-futuro-laboral/perfil` | S1 | ⬜ Crear |
| S1-4 | Validar skills | `/mi-futuro-laboral/perfil/validar` | S1 | ⬜ Crear |
| S1-5 | Datos contextuales | (parte de S1-3) | S1 | ⬜ Crear |
| S1-6 | Resultados | `/mi-futuro-laboral/resultados` | S1 | ⬜ Crear |
| S1-7 | Elegir destino | `/mi-futuro-laboral/resultados` tab | S1 | ⬜ Crear |
| S1-8 | Brecha + cursos | `/mi-futuro-laboral/brecha` | S1 | ⬜ Crear |
| S1-9 | PDF + QR | `/mi-futuro-laboral/reporte` | S1 | ⬜ Crear |
| S2-0 | Onboarding OE | `/oficina-empleo/onboarding` | S2 | ⚠️ Wireframe |
| S2-1 | Hub + KPIs | `/oficina-empleo` | S2 | ⚠️ Mejorar |
| S2-2 | Login institucional | (login existente) | S2 | ⚠️ Ajustar |
| S2-3 | Panel de casos | `/oficina-empleo/cartera` | S2 | ⬜ Crear |
| S2-4 | Vista de caso | `/oficina-empleo/cartera/[id]` | S2 | ⬜ Crear |
| S2-5 | Nota técnico | (tab en S2-4) | S2 | ⬜ Crear |
| S2-6 | Matching vacantes | (tab en S2-4) | S2 | ⬜ Crear |
| S2-7 | Empresa trae puesto | `/oficina-empleo/vacantes/nueva` | S2 | ⬜ Crear |
| S2-8 | Formación del caso | (tab en S2-4) | S2 | ⬜ Crear |
| S2-9 | Comparar casos | `/oficina-empleo/comparar` | S2 | ⬜ Baja prioridad |
| S2-10 | Inteligencia local | `/oficina-empleo/inteligencia` | S2 | ✅ Existe |
| S2-11 | PDF institucional | (modal en S2-4) | S2 | ⬜ Crear |
| S2-12 | Lista vacantes OE | `/oficina-empleo/vacantes` | S2 | ⬜ Crear |
| S2-13 | Nueva vacante OE | `/oficina-empleo/vacantes/nueva` | S2 | ⬜ Crear |
| S2-14 | Detalle vacante + candidatos | `/oficina-empleo/vacantes/[id]` | S2 | ⬜ Crear |
| S2-15 | Catálogo cursos | `/oficina-empleo/cursos` | S2 | ⬜ Crear |
| S3-1 | Acceso QR | `/reporte/[token]` | S3 | ✅ Existe |
| S3-2 | Reporte compatibilidad | `/reporte/[token]` | S3 | ✅ Existe |
| S3-3 | Personalizar skills | (en S3-2) | S3 | ⚠️ Falta persistir |
| S3-4 | Landing empresas | `/empresas` | S3 v2 | ⬜ Crear |
| S3-5 | Dashboard empresa | `/empresas/dashboard` | S3 v2 | ⬜ Crear |
| S3-6 | Mis vacantes | `/empresas/vacantes` | S3 v2 | ⬜ Crear |
| S3-7 | Nueva vacante empresa | `/empresas/vacantes/nueva` | S3 v2 | ⬜ Crear |
| S3-8 | Candidatos rankeados | `/empresas/vacantes/[id]` | S3 v2 | ⬜ Crear |
| S3-9 | Perfiles de puesto | `/empresas/perfiles-puesto` | S3 v2 | ⬜ Crear |
| S3-10 | Comparar candidatos | `/empresas/comparar` | S3 v2 | ⬜ Crear |

**Totales:** 5 ✅ existentes · 4 ⚠️ parciales · 26 ⬜ por crear
| S2-2 Login institucional + roles | S2 | Gerardo |
