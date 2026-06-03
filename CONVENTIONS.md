# MOL — Convenciones operativas

> Convenciones operativas del proyecto MOL para humanos e IA. Es el documento de referencia para cómo se trabaja en este repo.
>
> **Versión v1** · 2026-06-03 · Entregable de SPEC S1.A — CONVENTIONS.

**Tabla de contenidos**

1. [Cómo se usa este documento](#cómo-se-usa-este-documento)
2. [Branches](#branches)
3. [Commits](#commits)
4. [Pull Requests](#pull-requests)
5. [Política de tests al mergear](#política-de-tests-al-mergear)
6. [Ubicación de archivos](#ubicación-de-archivos)
7. [Naming de archivos](#naming-de-archivos)
8. [Versionado de exports/cyn_backlog/](#versionado-de-exportscyn_backlog)
9. [Responsabilidades por tipo de archivo](#responsabilidades-por-tipo-de-archivo)

---

## Cómo se usa este documento

Este documento es la **fuente de verdad sobre las convenciones operativas** del proyecto MOL: cómo se nombran los branches, cómo se hacen los commits y los pull requests, dónde vive cada tipo de archivo, qué se versiona y qué no. Sirve tanto a las personas del equipo como a los agentes de IA que asisten en el desarrollo.

**Jerarquía: CONVENTIONS.md manda sobre CLAUDE.md.** Cuando otro documento del repo —en particular `CLAUDE.md`— contradiga lo que dice acá sobre una convención operativa, **vale lo que dice CONVENTIONS.md**. `CLAUDE.md` es la guía de trabajo para la IA; cuando se reescriba, debe alinearse a este documento.

**Qué NO es este documento.** No es el manual del proyecto ni su planificación. La filosofía y el modelo conceptual viven en los documentos maestros; el método de trabajo y los sprints, en `docs/MOL_planificacion.md`; las reglas de deploy, en `DEPLOY_RULES.md` (que CONVENTIONS.md referencia, no absorbe). Acá viven estrictamente las convenciones que afectan el día a día del trabajo en el código.

**Cuándo se actualiza.** Es un artefacto vivo. Se actualiza cuando una convención cambia o aparece una nueva, y se revisa al cierre de cada versión del cerebro como parte del ciclo de release. Si el sistema cambia (nuevo tipo de branch, nueva ubicación, nueva práctica) y este documento no se actualiza, deja de ser confiable: mantenerlo al día es parte del trabajo, no un extra.

---

## Branches

Los branches siguen el patrón **`<tipo>/<descripcion-corta>`**, con la descripción en minúsculas y separada por guiones.

**Tipos vigentes:**

| Tipo | Uso | Ejemplo |
|------|-----|---------|
| `spec/` | Trabajo asociado a un spec (el tipo vigente para el método de specs actual). | `spec/w-validacion-estructurada`, `spec/s1a-conventions` |
| `feature/` | Trabajo de feature, principalmente frontend/UI o líneas paralelas de Sergio. | `feature/skills-intelligence-v5`, `feature/si-sergio-ui` |

El patrón es **extensible**: si surge una necesidad distinta (por ejemplo `fix/` para un hotfix aislado), se nombra con la misma forma `<tipo>/<descripcion-corta>`. Hoy los dos tipos en uso real son `spec/` (trabajo actual) y `feature/` (legacy y líneas de Sergio); no se agregan tipos nuevos hasta que haya trabajo que los justifique.

**Política de limpieza de branches.** Un branch **mergeado a `main` y a 0 commits ahead** se borra, local y remoto:

```bash
git branch -d <branch>                  # local
git push origin --delete <branch>       # remoto
```

Esta regla se aplicó en el cierre de SPEC W del 2026-06-03: al mergear el PR #16 se borraron los branches stale `feature/si-sergio-ui` y `feature/bloque-I-procesamiento`, que estaban mergeados pero nunca limpiados. Un branch sin mergear o con commits propios **no** se borra: o se mergea o se decide explícitamente descartarlo.

**Ejemplo de ciclo completo.** `spec/w-validacion-estructurada`: se creó para el trabajo de SPEC W, acumuló 9 commits temáticos, se mergeó a `main` vía PR #16 con merge commit `--no-ff`, y se borró local y remoto una vez confirmado el merge.

---

## Commits

El proyecto usa **Conventional Commits**. No es una propuesta nueva: es la convención **ya en uso fuerte y estable** (196 de los últimos 200 commits la siguen; los 4 restantes son merges/reverts automáticos de git).

**Formato:** `<tipo>(<scope>): <descripción en minúsculas, modo imperativo>`

**Tipos en uso** (del historial real): `feat`, `docs`, `fix`, `chore`, `test`, `data`.

**Scopes frecuentes** (guía, no lista cerrada): `spec-w`, `spec-t`, `spec-u1`, `spec-s1a`, `issues`, `aprendizaje`, `admin`, `validacion`, `catalogo-mol`, `infra`, `sync`, `matching`, `nlp`, `repo`, `gitignore`, `versions`. El scope refleja el área o el spec tocado; se elige el que mejor describa el cambio.

**Ejemplos reales del repo:**

```
feat(spec-w): cierre Sprint 1 Etapa 1 (D.4)
docs(spec-s1a): aplicar decisiones tipo B (B-04 a B-10)
fix(admin): corrección en analizar-correcciones
```

**Hook pre-commit.** El repo tiene un hook (`scripts/hooks/pre-commit` → `scripts/check_version_bumped.py`) que **bloquea el commit** si se modifica `database/match_ofertas_v3.py` o `database/process_nlp_from_db_v11.py` **sin** bumpear el archivo de versión correspondiente (`database/MATCHER_VERSION` / `database/NLP_VERSION`). Solo parsea los archivos cambiados, no nombres de branch ni de commit. Para una excepción genuina (refactor sin cambio funcional) se puede usar `git commit --no-verify`, **pero solo con autorización explícita** — no es el camino por defecto.

Instalar el hook (una vez por desarrollador):

```bash
ln -sf ../../scripts/hooks/pre-commit .git/hooks/pre-commit
```

---

## Pull Requests

**Política de merge: merge commit con `--no-ff`** (no squash, no rebase). Razón: mantiene el historial de `main` consistente y deja visible cada cierre de trabajo como un merge commit identificable.

```bash
gh pr merge <N> --merge        # merge commit, equivalente a --no-ff
```

**Título del PR:** Conventional Commits, mismo formato que los commits (ej. `feat(spec-w): cierre Sprint 1 Etapa 1 — validación estructurada para Cyn`).

**Body del PR:** se escribe en un **archivo separado** y se pasa con `--body-file`, no inline. Esto permite versionar y revisar el cuerpo del PR antes de abrirlo.

```bash
gh pr create --title "<titulo conventional>" --body-file <ruta-al-body.md>
```

Estructura mínima sugerida del body:
- **Qué cierra** (spec, sprint o issue).
- **Cambios incluidos**, agrupados por tema.
- **Tests** corridos y su resultado.
- **DEPLOY_RULES**: confirmación de que se respetan (quién mergea, qué ambiente).

**Quién mergea: solo Gerardo.** El merge a `main` es responsabilidad exclusiva de Gerardo (DEPLOY_RULES regla #1: "producción es solo para Gerardo"). Nadie más mergea a `main` ni hace push directo a `main`.

**Ejemplo concreto:** PR #16 (`feat(spec-w): cierre Sprint 1 Etapa 1 — validación estructurada para Cyn`), cierre de SPEC W, mergeado a `main` el 2026-06-03 con merge commit `5562ca6b` usando `--no-ff`, body pasado por `--body-file`.

---

## Política de tests al mergear

Antes de mergear un spec a `main` se corren los **tests específicos de los archivos que el spec tocó** (política "Nivel B", aplicada en el cierre de SPEC W). La regla tiene tres casos:

1. **Tests del spec OK** → avanzar al merge.
2. **Tests del spec fallan** → **bloquear el merge**, reportar el fallo y esperar instrucciones. No se mergea con tests rojos del propio spec.
3. **Commits temáticos sin tests propios** (cambios que entran en el mismo PR pero no tienen tests asociados) → se registran como **"riesgo asumido"** en el reporte de ejecución; **no bloquean** el merge, pero quedan documentados.

No se exige correr toda la suite del repo en cada merge: el foco es lo que el spec cambió. La suite completa es responsabilidad del ciclo de release, no de cada PR.

**Ejemplo del flujo:** el cierre de SPEC W (`exports/cyn_backlog/reporte_ejecucion_cierre_spec_w_2026-06-03.md`) corrió 87/87 tests de los archivos tocados antes de habilitar el merge del PR #16.

---

## Ubicación de archivos

Esta sección documenta **dónde vive cada tipo de archivo en el repo tal como está hoy**. No propone reorganizar nada: describe el estado real para que alguien nuevo (persona o IA) pueda ubicar un archivo correctamente.

**Raíz del repo** — documentos de gobierno del proyecto:
- `CONVENTIONS.md` (este archivo), `DEPLOY_RULES.md`, `CLAUDE.md`, `SERGIO.md`, `.gitignore`.
- **No hay `README.md` en la raíz** (existe `docs/README.md`). **No hay `CODEOWNERS`** (decisión B-10, ver sección Responsabilidades).

**`docs/`** — directorio **heterogéneo** con 40+ archivos: mezcla documentos maestros, specs sueltos (con prefijo `SPEC_*` y con sufijo `*_SPEC.md`), diagnósticos y reportes. CONVENTIONS.md documenta el estado, no propone reorganizar `docs/`.
- `docs/MOL_planificacion.md` — planificación del **enfoque vigente** (dos carriles, sprints, specs operativos). Es la **fuente de verdad de planificación activa**.
- `docs/plan/` — planificación del **enfoque pre-spec**: archivo de referencia histórica, **no** fuente de verdad vigente. La declaración de `CLAUDE.md` de que `docs/plan/INDEX.md` es "FUENTE DE VERDAD" está **obsoleta** (se corrige en la reescritura de CLAUDE.md, siguiente entregable de S1.A).

**`docs/specs/`** — master de specs (`MOL_master_specs.md`) y la mayoría de los specs individuales. Es la ubicación para **specs nuevos** (ver sección Naming para las dos ubicaciones y los tres patrones que conviven).

**Resto de directorios** — rol en una línea cuando es inferible:

| Directorio | Rol |
|------------|-----|
| `scripts/` | Utilidades y entry points (pipeline, scraping, exports, sync). Subcarpetas por área (`db/`, `nlp/`, `matching/`, `exports/`, `scraping/`, `hooks/`). |
| `database/` | BD SQLite, procesadores NLP, matching, prompts, patterns, archivos `*_VERSION`. |
| `config/` | JSONs de configuración (reglas de NLP, matching, skills, sinónimos). |
| `migrations/` | Migraciones SQL del pipeline (árbol vivo; ver Naming). |
| `fase3_dashboard/` | Dashboard Next.js + SQL del dashboard/Supabase. |
| `exports/` | Salidas generadas: Excel de validación, dumps, `cyn_backlog/` (diagnósticos y planes). |
| `01_sources/` | Scrapers por portal (bumeran, zonajobs, computrabajo, caba, portalempleo, indeed). |
| `tests/` | Tests pytest del pipeline. Los tests del frontend van en `fase3_dashboard/mol-dashboard/__tests__/`. |

Donde el rol de un archivo no sea claro, se documenta **caso por caso** al tocarlo, no se infiere.

---

## Naming de archivos

**Specs** — conviven **tres patrones** en **dos ubicaciones** (`docs/specs/` y `docs/`):

| Patrón | Forma | Ejemplo | Estado |
|--------|-------|---------|--------|
| Legacy fecha-prefijo | `<fecha>_<id>_<nombre>.md` | `2026-04-27_T_flujo_propagacion_correcciones.md` | No se migran los viejos |
| Sufijo | `<NOMBRE>_SPEC.md` | `LAB-BRECHA-FORMATIVA_SPEC.md` | No se migran los viejos (9 archivos en `docs/`) |
| **Prefijo (vigente)** | `SPEC_<id>_<nombre>_v<ver>.md` | `SPEC_U-1_CRITICO_v3_1.md` | **Formato para specs nuevos** |

> **Regla vigente (decisiones B-04 y B-05):** los tres patrones coexisten y los viejos **no se migran ni se renombran** (son archivo de referencia). **Todo spec nuevo se nombra `SPEC_<id>_<nombre>_v<ver>.md` y se ubica en `docs/specs/`.** `docs/` queda como archivo de specs del enfoque anterior.

**Archivos en `exports/cyn_backlog/`** — **prefijo-por-tipo**, con fecha opcional como sufijo. Prefijos reales presentes en el repo: `diagnostico_`, `verificacion_`, `experimento_`, `plan_`, `reporte_`, `inventario_`, `catalogo_`, `familia_`, `paso1_`, `clasificacion_`, `cruce_`, `bugs_`, `analisis_`, `informe_`, `investigacion_`, `validacion_`. Ejemplo: `verificacion_arboles_sql_2026-06-03.md`.

**Migraciones SQL** — patrón `<NNN>_<nombre_descriptivo>.sql`, pero el repo tiene **cuatro árboles**, no uno (verificado el 2026-06-03, `exports/cyn_backlog/verificacion_arboles_sql_2026-06-03.md`):

| Árbol | Estado | Función |
|-------|--------|---------|
| `migrations/` | **VIVO** | Pipeline; numeración secuencial limpia (12 archivos). Último cambio: SPEC W (2026-05-20). |
| `fase3_dashboard/sql/` | **VIVO** | Dashboard/Supabase (78 archivos). Numeración colisionada: distintas features tomaron el mismo número en paralelo. |
| `database/migrations/` | **ARCHIVO** | Era SQLite, congelado desde 2026-02-24. Algunos scripts aún leen archivos puntuales. |
| `fase3_dashboard/mol-dashboard/supabase/migrations/` | **EXPERIMENTO ABANDONADO** | Intento de adoptar Supabase CLI; un solo archivo, sin continuidad. |

> **Punto crítico (decisión B-06):** **ningún runner aplica migraciones en orden numérico.** Se corren manualmente en el SQL Editor de Supabase, o por archivo suelto ad-hoc. La numeración es **etiqueta, no secuencia ejecutable** — por eso la colisión de números en `fase3_dashboard/sql/` no rompe nada hoy.
>
> **Convención:** los archivos SQL nuevos se agregan al **árbol vivo que corresponda según el destino** — `migrations/` para el pipeline, `fase3_dashboard/sql/` para dashboard/Supabase. Los otros dos árboles quedan como archivo. Cualquier consolidación futura es trabajo de un spec aparte, fuera del alcance de S1.A.

---

## Versionado de exports/cyn_backlog/

`exports/cyn_backlog/` acumula trabajo intelectual del proyecto (diagnósticos, verificaciones, inventarios, planes, reportes) junto con dumps de datos pesados y regenerables. La regla separa **lo que se versiona** de **lo que se ignora**:

- **Se versionan los `.md`** en cualquier nivel (incluidos subdirectorios). Son trabajo de análisis valioso, no regenerable automáticamente.
- **Se ignoran los dumps pesados** (`.json`, `.jsonl`, `.xlsx`) en cualquier nivel — son datos derivados, regenerables, y pesan.

> **Decisión B-09** — la regla aplica a **todos los niveles** (`**/`), no solo al directorio superior. Esto cubre dumps en subdirectorios como `exp_raiz_skills/*.json`, que el patrón top-level anterior dejaba fuera.

Entrada vigente en `.gitignore`:

```gitignore
# Datos pesados de cyn_backlog (incluye subdirectorios) — decisión B-09
exports/cyn_backlog/**/*.json
exports/cyn_backlog/**/*.jsonl
exports/cyn_backlog/**/*.xlsx
# ...pero conservar los .md (diagnósticos, verificaciones, inventarios, planes) en cualquier nivel
!exports/cyn_backlog/**/*.md
```

Si dejás un `.md` de análisis en cualquier subcarpeta de `exports/cyn_backlog/`, se versiona. Si dejás un `.json`/`.jsonl`/`.xlsx`, git lo ignora.

---

## Responsabilidades por tipo de archivo

**No se usa `CODEOWNERS` (decisión B-10).** En un equipo donde Gerardo es prácticamente el único committer y **no hay branch protection configurada en GitHub**, `CODEOWNERS` sería solo documentación sin enforcement real (no obliga a que un owner revise antes de mergear): ceremonia sin efecto. Por eso las responsabilidades se documentan acá, de manera **informal**.

**Responsabilidades por área:**

| Área | Responsable | Referencia |
|------|-------------|------------|
| Pipeline (NLP, matching, skills, scraping), BD, configs | Gerardo | `CLAUDE.md` |
| Merge a `main` y deploy a producción | Gerardo (exclusivo) | `DEPLOY_RULES.md` regla #1 |
| Frontend / Skills Intelligence (UI, dashboard) | Sergio | `SERGIO.md` |
| Deploy a desarrollo (`mol-dev.vercel.app`) | Sergio | `DEPLOY_RULES.md` |

`SERGIO.md` (en la raíz) documenta el detalle de las áreas y tareas de Sergio en el frontend; es la referencia vigente para esas responsabilidades.

**Reversibilidad:** la decisión B-10 es revisable. Si el equipo crece o si Gerardo deja de ser el único mergeador, conviene configurar branch protection en GitHub e introducir `CODEOWNERS` con enforcement real.
