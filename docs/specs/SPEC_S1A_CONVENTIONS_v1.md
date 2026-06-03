# SPEC S1.A — CONVENTIONS.md

> Versión v1.3 (borrador completo, secciones 1-8 con coherencia interna) · 2026-06-03
> **Estado:** Borrador · **Carril:** desarrollo · **Fase:** Fundación · **Versión cerebro destino:** 1.0.1
> **Entregable principal:** `CONVENTIONS.md` en la raíz del repositorio (o `docs/` según se defina)
> Spec parte del paraguas S1.A — Setup documental. Define las convenciones operativas del proyecto MOL para humanos e IA. Primer entregable del setup, prioritario por urgencia operativa (limpieza de branches, formalización de flujo de PR).
>
> *Cambios desde la versión inicial:* sección 2 reescrita con la verdad de la verificación de Claude Code (`verificacion_spec_s1a_conventions_2026-06-02.md`) y con las decisiones tomadas en sesión + el cierre de SPEC W del 2026-06-03 (`reporte_ejecucion_cierre_spec_w_2026-06-03.md`).
>
> *Changelog v1.1 (2026-06-03):* correcciones de hecho (Tipo A) sobre §2, §3 y §4 a partir de la validación `exports/cyn_backlog/validacion_spec_s1a_secciones_3_4_2026-06-03.md`: (A1) sin `README.md` en raíz; (A2) sin `docs/MOL_modelo_conceptual.md`; (A3) `docs/` es heterogéneo (40+ archivos), no "2 masters"; (A4) specs en dos ubicaciones; (A5) tres patrones de naming de specs; (A8) eliminado `PROMPT_` (inexistente) y lista de prefijos de cyn_backlog corregida; (A9) B9 reusa la entrada de `.gitignore` ya aplicada. Añadidos Z1 (secciones obsoletas de CLAUDE.md) y Z2 (riesgo descartado: nada parsea nombres). Decisiones del Tipo B marcadas como `[DECISIÓN PENDIENTE — GERARDO]`.
>
> *Changelog v1.2 (2026-06-03):* aplicadas las 6 decisiones del Tipo B (B-04, B-05, B-06, B-07, B-09, B-10), resueltas por Gerardo. B-06 incorpora la verificación de los **cuatro** árboles de SQL (`exports/cyn_backlog/verificacion_arboles_sql_2026-06-03.md`). Z1 ampliado: `docs/plan/INDEX.md` ("FUENTE DE VERDAD") se suma a las secciones obsoletas de CLAUDE.md tras B-07.
>
> *Changelog v1.3 (2026-06-03):* spec completo (8 secciones). Se **ensamblaron** las §1-4 corregidas (recuperadas del commit `b742fe84`, que tenían Tipo A + Tipo B aplicadas) con las §5-8 nuevas (Dependencias, Validación, Riesgos, Criterio de aceptación) — una versión intermedia había revertido §1-4 al borrador v1, generando contradicciones internas detectadas en `exports/cyn_backlog/verificacion_spec_s1a_completo_2026-06-03.md`. Además: corregido el bug de rutas absolutas en los comandos de §6 y §8 (`/CONVENTIONS.md` → `CONVENTIONS.md`, `/.gitignore` → `.gitignore`, `/CODEOWNERS` → `CODEOWNERS`; se corren desde la raíz del repo).

---

## 1. Propósito

Definir y documentar las **convenciones operativas** del proyecto MOL —cómo se nombran los branches, cómo se hacen los pull requests, qué formato tienen los commits, dónde vive cada tipo de archivo, qué herramientas se usan— en un único documento que sea referencia tanto para personas como para agentes de IA que asisten en el desarrollo.

Hoy estas convenciones existen pero están dispersas o solo en la cabeza del equipo: hay reglas de deploy en `DEPLOY_RULES.md`, hay nombres de branches que siguen un patrón (`spec/w-validacion-estructurada`) pero no documentado, hay specs que viven en `docs/specs/` por costumbre pero sin convención escrita. Esa dispersión genera dos problemas concretos: cuando alguien nuevo se incorpora (un colaborador, un agente de IA en otro chat) tiene que reconstruir las reglas leyendo entre líneas; y cuando algo se desordena (branches stale, commits sin formato), no hay un documento contra el cual corregir. El incidente del 22/03/2026 documentado en `DEPLOY_RULES.md` —cuando se pisó el trabajo de un sprint entero por falta de coordinación— es el ejemplo de lo que pasa sin convenciones explícitas.

CONVENTIONS.md cierra ese hueco. **No es manual del proyecto** (la filosofía vive en el master conceptual, el método en el documento de planificación, la guía para IA en CLAUDE.md). Es estrictamente las convenciones operativas que afectan el día a día del trabajo en el código.

---

## 2. Reutilización del sistema existente

El proyecto ya tiene piezas que cubren parte de lo que CONVENTIONS.md debe documentar. El trabajo del spec es **extraerlas, ordenarlas y completarlas**, no inventarlas desde cero.

> **Sustento de esta sección**: las afirmaciones que siguen están basadas en la verificación read-only de Claude Code documentada en `exports/cyn_backlog/verificacion_spec_s1a_conventions_2026-06-02.md`, y en el cierre del repo ejecutado el 2026-06-03 (`exports/cyn_backlog/reporte_ejecucion_cierre_spec_w_2026-06-03.md`).

### Lo que ya existe y se conserva

- **`DEPLOY_RULES.md`** cubre las convenciones de deploy: ambientes, quién deploya a producción, flujo de PR previo al deploy. Está vigente y bien escrito. CONVENTIONS.md lo **referencia, no lo absorbe**: tiene una historia propia (el incidente del 22/03/2026) y un foco específico (deploy) que conviene mantener separados.

- **Convención de formato de commits — Conventional Commits, ya en uso fuerte y estable.** La verificación encontró que **196 de los últimos 200 commits siguen Conventional Commits** (`feat(scope):`, `fix(...)`, `docs(...)`, `chore(...)`); los 4 restantes son merges o reverts automáticos de git. No es accidente, es disciplina del equipo. CONVENTIONS.md **documenta el patrón en uso**, no propone uno nuevo. Esta es una de las correcciones más importantes respecto al borrador anterior del spec.

- **Convención de nombres de branches en uso**: el patrón vigente es `<tipo>/<descripcion-corta>` con dos tipos confirmados (`spec/` para specs como `spec/w-validacion-estructurada`, `feature/` para los stale como `feature/si-sergio-ui` y `feature/bloque-I-procesamiento`). Los `feature/*` antiguos quedaron como evidencia de la convención anterior; los nuevos usan `spec/*`. CONVENTIONS.md documenta este patrón y la transición.

- **Ubicación de specs — DOS ubicaciones, no una** *(corrección A4)*: la validación encontró que los specs viven en **dos lugares**:
  - `docs/specs/` — la mayoría (24+ archivos), incluido el ejemplo del patrón nuevo `SPEC_U-1_CRITICO_v3_1.md`.
  - `docs/` (nivel superior) — varios specs con prefijo `SPEC_*` (ej. `SPEC_M08_DECLARED_SKILLS.md`, `SPEC_Motor_Conocimiento_V2.md`).

  > **Decisión (B-04) — coexisten ambas ubicaciones:** los specs existentes en `docs/` quedan donde están (son trabajo hecho, no aporta moverlos); los nuevos van a `docs/specs/`. CONVENTIONS.md documenta esta coexistencia como criterio: **`docs/specs/` es la ubicación para specs nuevos; `docs/` es archivo de referencia** con specs del enfoque anterior. No se migran los viejos.

- **Naming de specs — TRES patrones, no dos** *(corrección A5)*: la validación encontró **tres** patrones conviviendo:
  - Legacy con fecha-prefijo: `<fecha>_<id>_<nombre>.md` (ej. `2026-04-27_T_flujo_propagacion_correcciones.md`), la mayoría, en `docs/specs/`.
  - Prefijo `SPEC_<id>_<nombre>_v<versión>.md` (ej. `SPEC_U-1_CRITICO_v3_1.md`), en `docs/specs/` y también en `docs/`.
  - **Sufijo** `<NOMBRE>_SPEC.md` (9 archivos en `docs/`, ej. `LAB-BRECHA-FORMATIVA_SPEC.md`, `M1-NIVEL-MAESTRIA_SPEC.md`, `VIP-PORTAL_SPEC.md`).

  > **Decisión (B-05) — coexisten los tres patrones:** los viejos (legacy fecha-prefijo y sufijo `<NOMBRE>_SPEC.md`) no se migran ni se renombran (son archivo de referencia, no trabajo activo). **Regla vigente: cualquier spec nuevo se nombra `SPEC_<id>_<nombre>_v<ver>.md`** (ej. `SPEC_U-1_CRITICO_v3_1.md`); los existentes mantienen su nombre actual.

- **Ubicación de masters en `docs/specs/`**: `MOL_master_specs.md` vive ahí, junto a los specs individuales. CONVENTIONS.md documenta dónde vive cada tipo de documento maestro del proyecto.

### Lo que no existe y hay que crear

- **Flujo de PR formalizado**. Está parcialmente cubierto por DEPLOY_RULES.md ("crear PR a main, Gerardo revisa y mergea") pero no hay convención escrita sobre títulos de PR, descripción mínima, uso de `--body-file`, cuándo se piden cambios, política de merge. La práctica vigente —confirmada por el cierre de SPEC W del 2026-06-03— es: merge commit con `--no-ff` (no squash, no rebase), título en Conventional Commits, body en archivo separado. CONVENTIONS.md formaliza estos puntos.

- **Política de limpieza de branches stale**. Hasta el cierre del 2026-06-03 había dos branches remotos stale ya mergeados sin borrar (`feature/si-sergio-ui`, `feature/bloque-I-procesamiento`). Se borraron como parte del cierre, pero no había convención escrita sobre cuándo y cómo limpiarlos. CONVENTIONS.md define la regla: branch mergeado y a 0 commits ahead de main → se borra local y remoto.

- **Convenciones de nombres de archivos** fuera de specs: scripts, diagnósticos, prompts. Hay patrones de hecho pero la verificación encontró que algunos son distintos a lo que se asumía. Por ejemplo, los archivos de `exports/cyn_backlog/` no siguen `<fecha>_<tipo>_...` como yo había supuesto, sino **prefijo-por-tipo** (`diagnostico_`, `verificacion_`, `experimento_`, `plan_`, `reporte_`) con fecha como sufijo opcional inconsistente. CONVENTIONS.md documenta los patrones reales y, donde haga falta, los formaliza.

- **Política de tests al mergear**. Hasta el cierre del 2026-06-03 no había convención escrita sobre qué tests deben correrse antes de mergear a main. La práctica que aplicamos en ese cierre (correr los tests específicos de los archivos tocados, bloquear si los del spec en cuestión fallan, registrar como riesgo asumido si los nuevos no tienen tests propios) funcionó bien. CONVENTIONS.md la consagra como política.

### Lo que se hizo en esta sesión

Antes de escribir el detalle de CONVENTIONS.md, el repo estaba con trabajo significativo sin integrar: el branch `spec/w-validacion-estructurada` con 9 commits sobre main (cierre de SPEC W Etapa 1), 3 archivos tracked modificados, y ~18 untracked. Eso es trabajo real (validación estructurada para Cyn, master de specs, este spec, infra de locking, fix de admin) que vivía en working tree y en un branch sin mergear.

**El 2026-06-03 se ejecutó el cierre de SPEC W** (plan `exports/cyn_backlog/plan_cierre_spec_w_ejecutable_2026-06-03.md`, reporte de ejecución `exports/cyn_backlog/reporte_ejecucion_cierre_spec_w_2026-06-03.md`): 6 commits temáticos, 87/87 tests pasados, PR #16 mergeado a main con merge commit `--no-ff`, branches stale borrados. **El repo quedó en estado conocido y limpio para arrancar la implementación de este spec.**

### Conflicto explícito a resolver con S1.A: CLAUDE.md desactualizado

La verificación encontró que **CLAUDE.md describe un flujo de branches que no existe**: menciona `main ← develop ← feature/*`, pero el branch `develop` no existe en el repo y el tipo vigente para specs es `spec/*`. Esto es deuda activa: si CONVENTIONS.md documenta el flujo real (sin `develop`, con `spec/*`) y CLAUDE.md sigue diciendo otra cosa, los dos documentos van a contradecirse desde el día uno.

**Decisión tomada en esta sesión**: cuando CONVENTIONS.md y CLAUDE.md se contradigan, **manda CONVENTIONS.md**. Por lo tanto, **la reescritura de CLAUDE.md (otro de los entregables de S1.A) debe alinearse a lo que CONVENTIONS.md establezca**. La corrección del flujo de branches en CLAUDE.md no se hace en este spec; se hace en el siguiente entregable de S1.A (CLAUDE.md reescrito). Pero se anota acá para que no se pierda.

**Z1 — Secciones de CLAUDE.md que quedan obsoletas/redundantes** (insumo para el entregable de reescritura de CLAUDE.md): la validación detectó que CLAUDE.md ya documenta convenciones que CONVENTIONS.md va a cubrir, y que quedarán redundantes o contradictorias:
- **`## Flujo de Branches`** (CLAUDE.md ~L1482): describe `main ← develop ← feature/*`. El branch `develop` **no existe** (confirmado, CLAUDE.md ~L1486) y el tipo vigente para specs es `spec/*`. Reemplazar por la sección "Branches" de CONVENTIONS.md (paso B3).
- **`## Regla de Versionado`** (CLAUDE.md ~L1381): solapa con las secciones "Commits" (B4) y la regla del hook `check_version_bumped.py`. Mantener lo específico del bump de `*_VERSION` (es real y vigente) pero remitir a CONVENTIONS.md para la convención de commits.
- **Declaración de `docs/plan/INDEX.md` como "FUENTE DE VERDAD"** (obsoleta tras B-07): CLAUDE.md presenta `docs/plan/` como fuente de verdad de planificación, pero la planificación vigente es `docs/MOL_planificacion.md` (`docs/plan/` quedó como archivo de referencia del enfoque pre-spec). Corregir en la reescritura de CLAUDE.md.
Cuando se reescriba CLAUDE.md, estas tres cosas deben armonizarse con CONVENTIONS.md (que manda).

### Cosas que requerían decisión humana antes de cerrar el spec [RESUELTAS]

La verificación dejó dos áreas donde la convención no se podía inferir desde el código. **Ambas fueron resueltas por Gerardo** (las decisiones completas están en los pasos A1 y A2 de §4):

- **Responsabilidades por tipo de archivo** → **B-10**: no se introduce `CODEOWNERS` (ceremonia sin enforcement real sin branch protection); se documentan responsabilidades de manera informal, referenciando `SERGIO.md`.

- **Convención de versionado de `exports/cyn_backlog/`** → **B-09**: se amplía el patrón de `.gitignore` a `**/*.json`/`*.jsonl`/`*.xlsx` (cubre subdirectorios), conservando `!exports/cyn_backlog/**/*.md`.

---

## 3. Entregables (el qué)

El spec produce un único artefacto principal y un artefacto auxiliar (la decisión B-10 descartó `CODEOWNERS`):

### Entregable principal

**`/CONVENTIONS.md`** — en la raíz del repositorio, junto a `DEPLOY_RULES.md`, `CLAUDE.md`, `SERGIO.md` y `.gitignore` *(corrección A1: no hay `README.md` en la raíz)*. Documento markdown con las convenciones operativas del proyecto para humanos e IA: branches, PR, commits, ubicación de archivos, naming, política de tests al mergear.

### Artefactos auxiliares

**~~`/CODEOWNERS`~~ — descartado (B-10).** No se introduce: sin branch protection en GitHub es solo documentación sin enforcement, y Gerardo es prácticamente el único committer. Las responsabilidades se documentan de manera informal dentro de CONVENTIONS.md, referenciando `SERGIO.md`. Revisable si el equipo crece y se configura branch protection.

**Entrada actualizada en `.gitignore`** — patrón para `exports/cyn_backlog/` que define qué se versiona y qué no. Por **B-09**, la regla definitiva amplía la del cierre de SPEC W a subdirectorios: `exports/cyn_backlog/**/*.json` (y `.jsonl`/`.xlsx`), conservando `!exports/cyn_backlog/**/*.md`. La aplicación al `.gitignore` real es trabajo de la implementación posterior (no de este spec).

### Lo que NO produce este spec

Para evitar inflar el alcance, queda explícito qué no es entregable de S1.A — CONVENTIONS.md:

- **CLAUDE.md reescrito**: es el siguiente entregable del paraguas S1.A (no de este spec). Se trabajará después, alineado a lo que CONVENTIONS.md establezca.
- **INDEX.md** (mapa de navegación de los documentos maestros): entregable posterior del paraguas S1.A.
- **Formalización del inventario como práctica recurrente**: entregable posterior del paraguas S1.A.
- **Convenciones de subdirectorios de scripts** o cualquier reorganización del código existente: fuera de alcance. CONVENTIONS.md documenta lo que está, no propone refactor.

---

## 4. Implementación (el cómo)

La implementación tiene dos fases: **(a) decisiones humanas que conviene resolver antes de escribir**, y **(b) construcción del documento siguiendo un orden definido**. Los pasos están numerados y son ejecutables.

### Fase A — Decisiones humanas (resolver antes de escribir CONVENTIONS.md)

Estas decisiones quedaron abiertas en la sección 2 y necesitaban respuesta de Gerardo antes de escribir el contenido. **Ya están resueltas** (B-10 para A1, B-09 para A2; ver bloques de decisión abajo). El paso A3 (alcance de tipos de branches) sigue abierto y se resuelve en la sección de branches de CONVENTIONS.md.

**Paso A1 — Responsabilidades por tipo de archivo. [RESUELTA — B-10]**

> **Decisión (B-10) — no se introduce `CODEOWNERS` en esta versión del spec.** Razón: en un equipo donde Gerardo es prácticamente el único committer y no hay branch protection configurada en GitHub, `CODEOWNERS` es solo documentación sin enforcement real (no obliga a que un owner revise antes de mergear). Si en algún momento el equipo crece y se configura branch protection, vale la pena revisar la decisión. Mientras tanto, CONVENTIONS.md documenta las responsabilidades de manera **informal** en una sección breve, referenciando `SERGIO.md` (que ya existe en la raíz y documenta áreas específicas de Sergio).

**Paso A2 — Decisión sobre versionado de `exports/cyn_backlog/`.**
El cierre de SPEC W ya estableció una regla provisoria (versionar `.md`, ignorar dumps pesados). CONVENTIONS.md tiene que confirmarla, refinarla o cambiarla. Sub-decisiones específicas: ¿se versionan los `.md` de diagnósticos y verificaciones (sí por defecto)? ¿se versionan los harness experimentales como `exp_raiz_skills/` (¿sí, no, depende del archivo?)? ¿hay límite de tamaño para `.md`? *(corrección A8: se elimina la sub-decisión sobre `PROMPT_*.md` — no existe ningún archivo `PROMPT_*` en `exports/cyn_backlog/`; no es una convención real del repo.)*

> **Decisión (B-09) — se amplía el patrón a subdirectorios.** La entrada de `.gitignore` para `exports/cyn_backlog/` se amplía respecto a la versión provisoria del cierre de SPEC W (que cubría solo el nivel superior). Regla definitiva:
>
> ```gitignore
> # Datos pesados de cyn_backlog (incluye subdirectorios)
> exports/cyn_backlog/**/*.json
> exports/cyn_backlog/**/*.jsonl
> exports/cyn_backlog/**/*.xlsx
> # Forzar que los .md valiosos se conserven, en cualquier nivel
> !exports/cyn_backlog/**/*.md
> ```
>
> Razón: cubre los dumps pesados en subdirectorios (ej. `exp_raiz_skills/*.json`) que la versión anterior dejaba fuera. Los `.md` siguen forzados a versionarse porque son trabajo intelectual valioso (diagnósticos, verificaciones, inventarios, planes, reportes). *(La aplicación al `.gitignore` real es trabajo de la implementación posterior, no de esta edición del spec.)*

**Paso A3 — Decisión sobre el alcance de tipos de branches.**
La verificación confirmó dos tipos vivos (`spec/`, `feature/`). ¿Se reconocen solo esos dos, o se admiten más (`fix/`, `chore/`, `experimento/`)? ¿Qué prefijo usa cada tipo de trabajo? La decisión se documenta en la sección de branches de CONVENTIONS.md.

### Fase B — Construcción del documento

Los pasos están en el orden de implementación. Cada uno produce contenido concreto en `/CONVENTIONS.md` (en la raíz del repo).

**Paso B1 — Crear el archivo con su encabezado y tabla de contenidos.**

- Crear `/CONVENTIONS.md` en la raíz del repositorio.
- Encabezado: título "MOL — Convenciones operativas", una línea de propósito ("Convenciones operativas del proyecto MOL para humanos e IA. Es el documento de referencia para cómo se trabaja en este repo."), versión inicial v1, fecha.
- Tabla de contenidos con las nueve secciones que se van a escribir en los pasos siguientes (B2 a B10).
- **Verificación del paso**: el archivo existe en `/CONVENTIONS.md`, tiene el encabezado, tiene la TOC con las 9 entradas listadas.

**Paso B2 — Sección "Cómo se usa este documento".**

- Párrafo corto que diga: CONVENTIONS.md es la fuente de verdad sobre convenciones operativas; cuando otros documentos (especialmente CLAUDE.md) lo contradigan, manda CONVENTIONS.md; se actualiza cuando una convención cambia o se introduce una nueva.
- **Verificación**: la sección existe, queda explícito el principio "CONVENTIONS.md manda sobre CLAUDE.md".

**Paso B3 — Sección "Branches".**

- Documentar el patrón `<tipo>/<descripcion-corta>` con los tipos confirmados por la decisión del paso A3.
- Para cada tipo, una línea explicando su uso.
- Política de limpieza: branch mergeado y a 0 commits ahead de main → se borra local y remoto (regla aplicada en el cierre de SPEC W del 2026-06-03).
- **Verificación**: la sección lista los tipos vigentes, define cuándo se borra un branch, da un ejemplo concreto.

**Paso B4 — Sección "Commits".**

- Documentar Conventional Commits como convención del proyecto (no proponer, documentar).
- Listar los `scope` más usados según la verificación (`spec-w`, `infra`, `admin`, etc.) como guía, sin cerrarlos a una lista fija.
- Mencionar el hook pre-commit (`check_version_bumped.py`) y qué bloquea.
- **Verificación**: la sección dice Conventional Commits, da 3 ejemplos reales del repo, menciona el hook.

**Paso B5 — Sección "Pull Requests".**

- Política de merge confirmada: merge commit con `--no-ff` (no squash, no rebase). Razón: consistencia con el historial de `main`.
- Título del PR: Conventional Commits, mismo formato que los commits.
- Body del PR: en archivo separado, usar `--body-file`. Estructura mínima sugerida (qué cierra, cambios incluidos por grupo, tests, deploy-rules).
- Quién mergea: solo Gerardo (referencia explícita a DEPLOY_RULES regla #1).
- **Verificación**: la sección define merge mode, formato de título, uso de `--body-file`, y referencia DEPLOY_RULES.

**Paso B6 — Sección "Política de tests al mergear".**

- Regla: antes de mergear a main, correr los tests específicos de los archivos tocados por el spec que se está cerrando.
- Si los tests del spec en cuestión fallan: bloquear el merge.
- Si hay commits temáticos en el mismo PR sin tests propios: registrarlo como "riesgo asumido" en el reporte de ejecución, no bloquear.
- Esta política se aplicó en el cierre de SPEC W de 2026-06-03; ver `exports/cyn_backlog/reporte_ejecucion_cierre_spec_w_2026-06-03.md` como ejemplo.
- **Verificación**: la sección define la regla con tres casos (tests del spec OK, tests del spec fallan, sin tests propios), referencia el reporte como ejemplo.

**Paso B7 — Sección "Ubicación de archivos".**

- Documentar la convención emergente con la estructura **real** del repo *(correcciones A1, A2, A3)*:
  - **Raíz del repo:** `CONVENTIONS.md` (este entregable), `DEPLOY_RULES.md`, `CLAUDE.md`, `SERGIO.md`, `.gitignore`, y `CODEOWNERS` (si aplica según paso A1). *No hay `README.md` en la raíz* (existe `docs/README.md`).
  - **`docs/`:** directorio **heterogéneo** con 40+ archivos — mezcla de documentos maestros (`MOL_planificacion.md`), specs sueltos (con prefijo `SPEC_*` y con sufijo `*_SPEC.md`), diagnósticos y reportes. `MOL_modelo_conceptual.md` **no existe** en el repo: si se considera un master, queda como documento a crear/migrar, no como archivo presente. CONVENTIONS.md **documenta el estado**, no propone reorganizar `docs/` (fuera de alcance).
  - **`docs/plan/`:** planificación del **enfoque pre-spec** — archivo de referencia histórica, **no** fuente de verdad vigente (ver B-07). La declaración de CLAUDE.md de que `docs/plan/INDEX.md` es "FUENTE DE VERDAD" está obsoleta.
  - **`docs/MOL_planificacion.md`:** planificación del **enfoque vigente** (dos carriles, sprints, specs operativos). Es la fuente de verdad de planificación activa.
  - **`docs/specs/`:** master de specs (`MOL_master_specs.md`) y la mayoría de los specs individuales (ver §2 para las dos ubicaciones y los tres patrones de naming).
  - `scripts/`, `database/`, `config/`, `migrations/`, `fase3_dashboard/`, `exports/`: documentar el rol de cada uno en una línea cuando sea inferible; marcar como "documentar caso por caso" donde no sea claro.

  > **Decisión (B-07) — dos enfoques sucesivos de planificación:**
  > - **Pre-spec (`docs/plan/`):** planificación previa al método de specs. Material valioso como referencia histórica de qué se pensó en su momento, pero no es fuente de verdad vigente; muchas cosas pueden estar implementadas, a medias o descartadas, y verificar caso por caso es costoso.
  > - **Vigente (`docs/MOL_planificacion.md`):** planificación con el método actual (dos carriles, sprints, specs operativos, verificación previa). Es la **fuente de verdad de planificación activa**.
  >
  > CONVENTIONS.md documenta esta distinción explícitamente. La declaración de CLAUDE.md de que `docs/plan/INDEX.md` es "FUENTE DE VERDAD" está **obsoleta** y se suma a la lista de cosas a corregir en el siguiente entregable del paraguas S1.A (reescritura de CLAUDE.md). Ver Z1 en §2.
- **Verificación**: la sección muestra dónde va cada tipo de archivo, alguien nuevo al proyecto puede ubicar un archivo nuevo correctamente leyendo solo esta sección.

**Paso B8 — Sección "Naming de archivos".**

- Specs *(correcciones A4, A5)*: viven en **dos ubicaciones** (`docs/specs/` y `docs/`) y conviven **tres patrones** de naming:
  - Legacy fecha-prefijo `<fecha>_<id>_<nombre>.md` (mayoría, en `docs/specs/`). No se migran los viejos.
  - Prefijo `SPEC_<id>_<nombre>_v<ver>.md` (en `docs/specs/` y `docs/`); es el formato para specs nuevos a partir de S1.A.
  - Sufijo `<NOMBRE>_SPEC.md` (9 archivos en `docs/`).
  - Criterio (B-04 y B-05, ya resueltos en §2): los tres coexisten, los viejos no se migran, y **todo spec nuevo se nombra `SPEC_<id>_<nombre>_v<ver>.md` en `docs/specs/`**.
- Archivos en `exports/cyn_backlog/`: prefijo-por-tipo, fecha opcional como sufijo. Prefijos **reales** presentes en el repo *(corrección A8 — se elimina `PROMPT_`, que no existe)*: `diagnostico_`, `verificacion_`, `experimento_`, `plan_`, `reporte_`, `inventario_`, `catalogo_`, `familia_`, `paso1_`, `clasificacion_`, `cruce_`, `bugs_`, `analisis_`, `informe_`, `investigacion_`, `validacion_`.
- Migraciones SQL: patrón `<NNN>_<nombre_descriptivo>.sql`, pero la verificación del 2026-06-03 encontró **cuatro árboles**, no dos (ver B-06).

  > **Decisión (B-06) — documentar el estado real, sin consolidar.** El repo tiene **cuatro** árboles de SQL, con estados verificados el 2026-06-03 (`exports/cyn_backlog/verificacion_arboles_sql_2026-06-03.md`):
  >
  > | Árbol | Estado | Función |
  > |---|---|---|
  > | `migrations/` | **VIVO** | Pipeline; numeración secuencial limpia (12 archivos). Último cambio: SPEC W (2026-05-20). |
  > | `fase3_dashboard/sql/` | **VIVO** | Dashboard/Supabase (78 archivos). Numeración colisionada porque distintas features tomaron el mismo número en paralelo. |
  > | `database/migrations/` | **ARCHIVO** | Era SQLite, congelado desde 2026-02-24. Algunos scripts aún leen archivos puntuales. |
  > | `fase3_dashboard/mol-dashboard/supabase/migrations/` | **EXPERIMENTO ABANDONADO** | Intento de adoptar Supabase CLI; un solo archivo, sin continuidad. |
  >
  > **Punto crítico:** **ningún runner aplica migraciones en orden numérico** — se corren manualmente en Supabase (SQL Editor) o por archivo suelto ad-hoc. La numeración es **etiqueta, no secuencia ejecutable**; por eso la colisión de números en `fase3_dashboard/sql/` no rompe nada hoy (es desprolijidad de etiqueta, no deuda funcional).
  >
  > **Convención:** los archivos SQL nuevos se agregan al árbol vivo que corresponda según el destino (`migrations/` para pipeline, `fase3_dashboard/sql/` para dashboard/Supabase). Los otros dos árboles quedan como archivo. Cualquier consolidación futura es trabajo de un spec aparte, **fuera del alcance de S1.A**.
- **Verificación**: la sección da 5 ejemplos concretos de archivos del repo (de cada patrón y ubicación) y muestra cómo cada uno encaja en su patrón.

**Paso B9 — Sección "Versionado de exports/cyn_backlog/".**

- Documentar la decisión del paso A2 / **B-09** (qué se versiona, qué no, por qué).
- **Actualizar la entrada de `.gitignore`** *(corrección A9 + B-09)*: el cierre de SPEC W del 2026-06-03 dejó un bloque "Limpieza pre-S1.A" que cubría solo el nivel superior. B9 lo **amplía a subdirectorios** con la regla definitiva (`exports/cyn_backlog/**/*.json`/`.jsonl`/`.xlsx`, conservando `!**/*.md`) — editar la entrada existente, **no duplicarla**.
- El caveat que motivaba la decisión (el patrón top-level no cubría `exp_raiz_skills/*.json`) queda resuelto por el patrón `**/*.json`.
- **Verificación**: la sección coincide con lo que está en `.gitignore`, hay coherencia entre decisión escrita y configuración aplicada (sin duplicar reglas).

**Paso B10 — Sección "Responsabilidades por tipo de archivo".**

Resuelto por **B-10**: documentación **informal** (sin `CODEOWNERS`).

- Escribir la sección con las áreas y responsables en prosa, sin crear `CODEOWNERS`.
- Referenciar `SERGIO.md` (responsabilidades parciales de Sergio, ya documentadas en la raíz).
- Dejar anotado que la decisión es revisable si el equipo crece y se configura branch protection en GitHub.
- **Verificación**: la sección documenta responsabilidades en prosa, referencia `SERGIO.md`, y no se creó `CODEOWNERS`.

### Verificación de cierre de la Fase B

Una vez completados B1 a B10:

- `/CONVENTIONS.md` existe en la raíz, tiene las 9 secciones, todas con contenido (ninguna queda "por completar").
- Si correspondió por A1: `/CODEOWNERS` existe y es coherente con CONVENTIONS.md.
- `.gitignore` es coherente con la sección B9.
- Todos los links internos de CONVENTIONS.md resuelven (no apuntan a archivos inexistentes).

### Z2 — Riesgo descartado: ningún script parsea nombres de branches/specs

La validación confirmó que **ningún script del repo parsea nombres de branch ni de spec**. El único enforcement automatizado es `scripts/check_version_bumped.py`, que parsea los **archivos cambiados** de un commit (no nombres) para exigir bump de `database/MATCHER_VERSION` / `database/NLP_VERSION`. Conclusión operativa: **formalizar o renombrar convenciones de branch/spec no rompe ninguna automatización existente**. Este riesgo queda explícitamente descartado.

---

## 5. Dependencias

Este spec tiene dependencias mínimas porque es fundacional —es el primer entregable del paraguas S1.A—. Las que hay son operativas, no de otros specs:

**Dependencia cumplida**: el repo debe estar en estado conocido y limpio antes de poder implementar este spec. Cumplido por el cierre de SPEC W del 2026-06-03 (`exports/cyn_backlog/reporte_ejecucion_cierre_spec_w_2026-06-03.md`): main mergeado, branches stale borrados, working tree limpio sobre `main`.

**Dependencia operativa actual**: estar en el branch `spec/s1a-conventions` para todo el trabajo del spec. Verificable con `git branch --show-current`.

**Dependencia de información**: las verificaciones previas que sustentan el contenido del spec (`verificacion_spec_s1a_conventions_2026-06-02.md`, `validacion_spec_s1a_secciones_3_4_2026-06-03.md`, `verificacion_arboles_sql_2026-06-03.md`). Si alguna se vuelve obsoleta porque el sistema cambia, el spec debe re-verificarse antes de implementar.

**No depende** de otros specs (no hay spec previo que cubra convenciones operativas). **Sí bloquea** a los siguientes entregables del paraguas S1.A: la reescritura de CLAUDE.md depende de que CONVENTIONS.md exista para poder alinearse a él; INDEX.md y la formalización del inventario también lo referencian.

---

## 6. Validación

Tres niveles integrados, todos con comandos exactos, entradas concretas, salidas esperadas, y criterio binario de pase/falla. Esta sección se diseñó después de aprender que la sección "Validación" abstracta no alcanza para que el spec sea ejecutable.

### Tests de código

CONVENTIONS.md es un documento markdown, no código. Los tests automatizados son mínimos pero útiles para evitar errores tipográficos y referencias rotas:

**Test 6.1.1 — El archivo existe en la ubicación correcta.**

```bash
# (correr desde la raíz del repo)
test -f CONVENTIONS.md && echo "OK: archivo existe en raíz" || echo "FALLA: no existe"
```

- Salida esperada: `OK: archivo existe en raíz`.
- Criterio: si dice "FALLA", el paso B1 de la implementación no se completó.

**Test 6.1.2 — El archivo tiene las 9 secciones esperadas.**

```bash
grep -c "^## " CONVENTIONS.md
```

- Salida esperada: `9` (las 9 secciones de nivel H2: Cómo se usa, Branches, Commits, PRs, Política de tests, Ubicación, Naming, Versionado de cyn_backlog, Responsabilidades).
- Criterio: si el conteo es menor a 9, hay secciones faltantes; si es mayor, hay secciones de más que conviene revisar.

**Test 6.1.3 — No hay marcadores residuales de borrador.**

```bash
grep -nE "TODO|FIXME|XXX|\[PENDIENTE\]|\[DECISIÓN PENDIENTE\]" CONVENTIONS.md
```

- Salida esperada: vacía (sin coincidencias).
- Criterio: cualquier coincidencia indica que el documento quedó con notas internas que deberían haberse resuelto antes de cerrar el spec.

**Test 6.1.4 — Coherencia entre CONVENTIONS.md y `.gitignore` sobre cyn_backlog.**

```bash
grep -E "exports/cyn_backlog/\*\*/\*\.(json|jsonl|xlsx)" .gitignore && \
grep -E "!exports/cyn_backlog/\*\*/\*\.md" .gitignore && \
echo "OK: gitignore coincide con decisión B-09"
```

- Salida esperada: las dos líneas de gitignore impresas + `OK: gitignore coincide con decisión B-09`.
- Criterio: si alguna no aparece, el paso B9 quedó inconsistente entre la decisión escrita y la configuración aplicada.

### Test end-to-end

El test E2E para un spec documental es de orientación humana: alguien que no participó del proyecto debe poder ubicar qué convenciones aplican leyendo solo CONVENTIONS.md.

**Test 6.2 — Test de orientación de tres minutos.**

Procedimiento:
1. Tomar una persona que no haya leído el documento (puede ser Sergio, Cynthia, o alguien externo si está disponible).
2. Darle acceso a `/CONVENTIONS.md` y un cronómetro de 3 minutos.
3. Pedirle que responda **sin abrir ningún otro archivo**:
   - ¿Cómo se nombra un branch nuevo si voy a trabajar el spec S5?
   - ¿Dónde tengo que poner el archivo del nuevo spec?
   - ¿Qué formato tiene el mensaje de commit cuando agrego una documentación?
   - ¿Quién mergea a main?
   - ¿Qué pasa con los archivos `.json` que dejo en `exports/cyn_backlog/exp_raiz_skills/`?

Salida esperada: las cinco respuestas correctas en los tres minutos.

Criterio de aceptación:
- 5/5 correctas: el documento cumple su función orientadora.
- 4/5: aceptable; el spec se cierra, pero la pregunta fallada se anota como mejora para v1.1 de CONVENTIONS.md.
- 3/5 o menos: el documento no está cumpliendo su función. Bloquea el cierre del spec; conviene reescribir las secciones problemáticas.

### QA humana

La validación humana es la que más peso tiene en un spec documental, porque verifica que el contenido es **correcto, completo y útil**, no solo "está".

**QA 6.3.1 — Validación de contenido (responsable: Gerardo).**

Procedimiento:
1. Leer `/CONVENTIONS.md` entero.
2. Para cada una de las 9 secciones, responder: ¿la información acá es correcta y refleja cómo trabajamos hoy?

Criterio: las 9 secciones deben ser "sí" para que el spec se considere cerrado. Cualquier "no" o "más o menos" genera ajuste antes de mergear.

**QA 6.3.2 — Validación de flujos operativos (responsable: Sergio, sobre las secciones que tocan dev).**

Procedimiento:
1. Sergio lee las secciones de Branches, Commits, PRs y Política de tests.
2. Responde: ¿esto coincide con lo que efectivamente hacés cuando trabajás en el proyecto? ¿Hay algo que falta o que está descrito de forma engañosa?

Criterio: si Sergio reporta inconsistencias entre el documento y la práctica, se ajusta el documento (la práctica es la fuente, el documento la refleja).

**QA 6.3.3 — Validación de la sección Responsabilidades (responsable: Gerardo).**

Procedimiento:
1. Leer la sección de responsabilidades de CONVENTIONS.md.
2. Confirmar que la referencia a SERGIO.md sigue siendo válida y que no hay áreas críticas sin responsable visible.

Criterio: si hay áreas críticas sin asignación clara, la decisión B-10 (no introducir CODEOWNERS por ahora) puede revisarse, aunque el spec se cierra igual.

---

## 7. Riesgos identificados

Los riesgos del spec, con su mitigación. Algunos son inherentes a su naturaleza documental; otros surgen del sistema preexistente.

**Riesgo 7.1 — Desactualización rápida.**
CONVENTIONS.md describe convenciones de un sistema vivo. Si el sistema cambia (nuevo tipo de branch, nueva ubicación, nueva práctica) y CONVENTIONS.md no se actualiza, el documento se vuelve fuente de información falsa.
*Mitigación*: declarar en la sección "Cómo se usa este documento" que se actualiza cuando una convención cambia; revisarlo al cierre de cada versión del cerebro como parte del ciclo de release; tratarlo como artefacto vivo, no como entregable terminado.

**Riesgo 7.2 — Sobre-documentación.**
Tentación de documentar todo lo que se hace, incluyendo cosas que cambian todo el tiempo o que no aportan. Resultado: documento largo, difícil de mantener, que nadie lee.
*Mitigación*: mantener el alcance en lo **estructural** (qué hay y cómo se trabaja a alto nivel), no en lo operativo de cada día. Si algo es muy específico de un componente, va a la sección de S1.B correspondiente cuando se trabaje ese componente, no a CONVENTIONS.md.

**Riesgo 7.3 — Contradicciones cruzadas con CLAUDE.md.**
CLAUDE.md tiene secciones obsoletas (flujo de branches con `develop` inexistente, `docs/plan/INDEX.md` como FUENTE DE VERDAD) que van a contradecir CONVENTIONS.md desde el día uno.
*Mitigación*: el spec declara explícitamente que **CONVENTIONS.md manda** sobre CLAUDE.md cuando hay conflicto, y la reescritura de CLAUDE.md queda como siguiente entregable del paraguas S1.A. Hasta que ese entregable se haga, existe contradicción documentada pero con jerarquía clara.

**Riesgo 7.4 — Las convenciones de hecho no estaban en lugares visibles.**
Las verificaciones del 2026-06-02 y 2026-06-03 destaparon que el sistema acumuló capas no documentadas (cuatro árboles de migraciones, tres patrones de naming de specs, una credencial hardcodeada). Es probable que CONVENTIONS.md también deje cosas afuera por no haberlas detectado todavía.
*Mitigación*: CONVENTIONS.md se trata como versión 1 que va a tener actualizaciones; cuando aparezca una convención de hecho no documentada, se agrega. Esto es consecuencia natural del principio "es un quilombo documentado y verificado, distinto del quilombo escondido".

**Riesgo 7.5 — Falsa sensación de cobertura por la decisión B-10 (no CODEOWNERS).**
Sin CODEOWNERS ni branch protection, no hay enforcement automático de responsabilidades. Si el equipo crece o si Gerardo deja de ser el único mergeador, la falta de enforcement se vuelve problema real.
*Mitigación*: la decisión B-10 queda explícitamente como reversible — el spec dice "si el equipo crece y se configura branch protection, vale la pena revisar la decisión". Revisar la decisión es trabajo de mantenimiento del spec, no rotura.

**Riesgo 7.6 — Riesgo descartado: nada parsea nombres.**
La verificación confirmó que ningún script parsea nombres de branches ni de specs (solo `check_version_bumped.py` parsea archivos cambiados). Por lo tanto, las convenciones de naming que CONVENTIONS.md establece **no rompen automatización existente**. Este riesgo queda registrado como descartado para que no resurja en futuras evaluaciones.

---

## 8. Criterio de aceptación

Condiciones binarias para considerar el spec implementado. Cada una con un sí/no claro, sin "más o menos":

1. **`/CONVENTIONS.md` existe en la raíz del repositorio.**
   *Verificación* (desde la raíz del repo): `test -f CONVENTIONS.md`.

2. **`/CONVENTIONS.md` tiene las 9 secciones de nivel H2 definidas en la sección 4 del spec (B2 a B10).**
   *Verificación*: `grep -c "^## " CONVENTIONS.md` devuelve 9.

3. **`/CONVENTIONS.md` no tiene marcadores residuales de borrador.**
   *Verificación*: `grep -nE "TODO|FIXME|XXX|\[PENDIENTE\]|\[DECISIÓN PENDIENTE\]" CONVENTIONS.md` devuelve vacío.

4. **`.gitignore` refleja la decisión B-09** (cubre `**/*.json`, `**/*.jsonl`, `**/*.xlsx` de cyn_backlog en cualquier nivel, conservando `!**/*.md`).
   *Verificación*: el test 6.1.4 pasa.

5. **No se introdujo `CODEOWNERS`** (decisión B-10), y la sección Responsabilidades de CONVENTIONS.md menciona explícitamente la decisión y referencia `SERGIO.md`.
   *Verificación*: `test ! -f CODEOWNERS` y la sección Responsabilidades de CONVENTIONS.md contiene la palabra "SERGIO.md".

6. **El test E2E (6.2) pasa con al menos 4/5 respuestas correctas.**
   *Verificación*: ejecutar el procedimiento y registrar el resultado.

7. **La QA humana (6.3.1) registra "sí" en las 9 secciones por parte de Gerardo.**
   *Verificación*: revisión documentada (puede ser un comentario en el PR de cierre del spec).

8. **El branch `spec/s1a-conventions` se mergea a `main` con merge commit `--no-ff`**, siguiendo la propia política que CONVENTIONS.md establece (validación circular pero deliberada: el spec se cierra aplicando la convención que él mismo documenta).
   *Verificación*: `git log main --oneline -3` muestra el merge commit del spec.

9. **El branch `spec/s1a-conventions` se borra local y remoto post-merge**, también siguiendo la convención del propio spec.
   *Verificación*: `git branch -a | grep spec/s1a-conventions` devuelve vacío.

Si los 9 criterios se cumplen, el spec S1.A — CONVENTIONS está implementado y el primer entregable del paraguas S1.A queda cerrado. El siguiente entregable del paraguas (reescritura de CLAUDE.md) puede arrancar.

---

> *Spec completo. Versiones 1-8 cerradas. Listo para implementar: aplicar los pasos B1 a B10 de la sección 4 en el branch `spec/s1a-conventions`, validar contra los 9 criterios de aceptación de la sección 8, mergear a `main`.*
