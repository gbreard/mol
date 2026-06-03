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
