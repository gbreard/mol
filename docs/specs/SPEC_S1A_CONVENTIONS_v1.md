# SPEC S1.A — CONVENTIONS.md

> Versión v1.1 (borrador, secciones 1-4 con correcciones de hecho aplicadas) · 2026-06-03
> **Estado:** Borrador · **Carril:** desarrollo · **Fase:** Fundación · **Versión cerebro destino:** 1.0.1
> **Entregable principal:** `CONVENTIONS.md` en la raíz del repositorio (o `docs/` según se defina)
> Spec parte del paraguas S1.A — Setup documental. Define las convenciones operativas del proyecto MOL para humanos e IA. Primer entregable del setup, prioritario por urgencia operativa (limpieza de branches, formalización de flujo de PR).
>
> *Cambios desde la versión inicial:* sección 2 reescrita con la verdad de la verificación de Claude Code (`verificacion_spec_s1a_conventions_2026-06-02.md`) y con las decisiones tomadas en sesión + el cierre de SPEC W del 2026-06-03 (`reporte_ejecucion_cierre_spec_w_2026-06-03.md`).
>
> *Changelog v1.1 (2026-06-03):* correcciones de hecho (Tipo A) sobre §2, §3 y §4 a partir de la validación `exports/cyn_backlog/validacion_spec_s1a_secciones_3_4_2026-06-03.md`: (A1) sin `README.md` en raíz; (A2) sin `docs/MOL_modelo_conceptual.md`; (A3) `docs/` es heterogéneo (40+ archivos), no "2 masters"; (A4) specs en dos ubicaciones; (A5) tres patrones de naming de specs; (A8) eliminado `PROMPT_` (inexistente) y lista de prefijos de cyn_backlog corregida; (A9) B9 reusa la entrada de `.gitignore` ya aplicada. Añadidos Z1 (secciones obsoletas de CLAUDE.md) y Z2 (riesgo descartado: nada parsea nombres). Decisiones del Tipo B marcadas como `[DECISIÓN PENDIENTE — GERARDO]`.

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

  > **[DECISIÓN PENDIENTE — GERARDO] (B-04)** Los specs viven hoy en dos ubicaciones (`docs/specs/` y `docs/`). ¿Se consolidan a futuro a una sola ubicación, o coexisten ambas? Si coexisten, ¿qué criterio define dónde va un spec nuevo?

- **Naming de specs — TRES patrones, no dos** *(corrección A5)*: la validación encontró **tres** patrones conviviendo:
  - Legacy con fecha-prefijo: `<fecha>_<id>_<nombre>.md` (ej. `2026-04-27_T_flujo_propagacion_correcciones.md`), la mayoría, en `docs/specs/`.
  - Prefijo `SPEC_<id>_<nombre>_v<versión>.md` (ej. `SPEC_U-1_CRITICO_v3_1.md`), en `docs/specs/` y también en `docs/`.
  - **Sufijo** `<NOMBRE>_SPEC.md` (9 archivos en `docs/`, ej. `LAB-BRECHA-FORMATIVA_SPEC.md`, `M1-NIVEL-MAESTRIA_SPEC.md`, `VIP-PORTAL_SPEC.md`).

  El legacy se conserva tal cual (no se migran los viejos). Para los specs nuevos a partir de S1.A se usa `SPEC_<id>_<nombre>_v<versión>.md`.

  > **[DECISIÓN PENDIENTE — GERARDO] (B-05)** Conviven tres patrones de naming de specs. ¿Se consolidan o coexisten los tres? Si coexisten, ¿qué criterio define cuál usar (y aplica el sufijo `*_SPEC.md` solo a lo legacy de `docs/`)?

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
Cuando se reescriba CLAUDE.md, estas dos secciones deben armonizarse con CONVENTIONS.md (que manda).

### Cosas que requieren decisión humana antes de cerrar el spec

La verificación dejó dos áreas donde la convención no se puede inferir desde el código y requieren decisión explícita de Gerardo:

- **Responsabilidades por tipo de archivo**. No existe `CODEOWNERS` ni `MAINTAINERS.md` en el repo. Solo hay un `SERGIO.md` informal que documenta áreas específicas. CONVENTIONS.md tiene que definir si se introduce `CODEOWNERS` formal, si se documenta de manera informal en sí mismo, o si se omite por ahora. Esta decisión se toma en el desarrollo de la sección de Entregables (sección 3).

- **Convención de versionado de `exports/cyn_backlog/`**. Es el caso concreto que quedó abierto del cierre del 2026-06-03: el directorio tiene 35 `.md` valiosos (diagnósticos, verificaciones, inventarios) que están untracked, más los harness experimentales (`exp_raiz_skills/`) que también lo están. CONVENTIONS.md debe definir qué se versiona y qué no de este directorio, y por qué. Esta decisión también se toma en la sección 3.

---

## 3. Entregables (el qué)

El spec produce un único artefacto principal y dos artefactos auxiliares:

### Entregable principal

**`/CONVENTIONS.md`** — en la raíz del repositorio, junto a `DEPLOY_RULES.md`, `CLAUDE.md`, `SERGIO.md` y `.gitignore` *(corrección A1: no hay `README.md` en la raíz)*. Documento markdown con las convenciones operativas del proyecto para humanos e IA: branches, PR, commits, ubicación de archivos, naming, política de tests al mergear.

### Artefactos auxiliares

**`/CODEOWNERS`** (o decisión documentada de no usarlo) — archivo estándar de GitHub que define responsabilidades por path. Si Gerardo decide no introducirlo formalmente, CONVENTIONS.md documenta la decisión y la razón. Esta decisión se toma durante la implementación de la sección "Responsabilidades por tipo de archivo". **Matiz importante (validación):** `CODEOWNERS` solo *enforza* revisión si el repo tiene branch protection rules que la exijan; sin eso, es solo documentación. Ver decisión B-10.

**Entrada nueva en `.gitignore`** — patrón explícito para `exports/cyn_backlog/` que defina qué se versiona y qué no, según la decisión de Gerardo sobre el contenido del directorio. La regla del cierre de SPEC W de hoy (versionar `.md`, ignorar dumps pesados) ya está en `.gitignore` y puede mantenerse o refinarse según lo que CONVENTIONS.md establezca.

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

Estas dos decisiones quedaron abiertas en la sección 2 y necesitan respuesta de Gerardo antes de poder escribir el contenido. Cada una se resuelve con una conversación corta (acá mismo, o en la herramienta de gestión) y la respuesta se anota en el spec antes de pasar a la Fase B.

**Paso A1 — Decisión sobre responsabilidades por tipo de archivo.**
Tres opciones: (i) introducir `CODEOWNERS` formal con áreas y responsables, (ii) documentar responsabilidades de manera informal en una sección de CONVENTIONS.md, (iii) no documentar responsabilidades por ahora y dejar la decisión para más adelante. La opción elegida define si el entregable `CODEOWNERS` se produce o no, y qué dice CONVENTIONS.md al respecto.

> **[DECISIÓN PENDIENTE — GERARDO] (B-10)** `CODEOWNERS` sin branch protection en GitHub es solo documentación, no enforcement (no obliga a que un owner revise antes de mergear). `[Branch protection NO VERIFICADO en GitHub — requiere acceso a Settings del repo]`. ¿Se verifica/configura branch protection antes de introducir `CODEOWNERS`, o se asume que será documental por ahora?

**Paso A2 — Decisión sobre versionado de `exports/cyn_backlog/`.**
El cierre de SPEC W ya estableció una regla provisoria (versionar `.md`, ignorar dumps pesados). CONVENTIONS.md tiene que confirmarla, refinarla o cambiarla. Sub-decisiones específicas: ¿se versionan los `.md` de diagnósticos y verificaciones (sí por defecto)? ¿se versionan los harness experimentales como `exp_raiz_skills/` (¿sí, no, depende del archivo?)? ¿hay límite de tamaño para `.md`? *(corrección A8: se elimina la sub-decisión sobre `PROMPT_*.md` — no existe ningún archivo `PROMPT_*` en `exports/cyn_backlog/`; no es una convención real del repo.)*

> **[DECISIÓN PENDIENTE — GERARDO] (B-09)** La regla actual de `.gitignore` (`exports/cyn_backlog/*.json`, `*.jsonl`, `*.xlsx`, conservando `!**/*.md`) **no cubre subdirectorios** para los dumps: `exp_raiz_skills/*.json` queda fuera del patrón top-level. ¿Se amplía a `exports/cyn_backlog/**/*.json` (y `.jsonl`/`.xlsx`) para cubrir subdirectorios, o se acepta el caveat actual?

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
  - **`docs/plan/`:** directorio de planificación del producto; CLAUDE.md lo declara "FUENTE DE VERDAD" (`docs/plan/INDEX.md`, roadmap, modelo de datos, 30 pantallas).
  - **`docs/specs/`:** master de specs (`MOL_master_specs.md`) y la mayoría de los specs individuales (ver §2 para las dos ubicaciones y los tres patrones de naming).
  - `scripts/`, `database/`, `config/`, `migrations/`, `fase3_dashboard/`, `exports/`: documentar el rol de cada uno en una línea cuando sea inferible; marcar como "documentar caso por caso" donde no sea claro.

  > **[DECISIÓN PENDIENTE — GERARDO] (B-07)** CLAUDE.md declara `docs/plan/INDEX.md` como "FUENTE DE VERDAD" de la planificación, y en la sesión se decidió que `MOL_planificacion.md` vive en `docs/`. ¿Cuál es la relación entre ambos? ¿Se mantienen separados (uno = roadmap detallado, otro = master), uno reemplaza al otro, o `MOL_planificacion.md` indexa a `docs/plan/`?
- **Verificación**: la sección muestra dónde va cada tipo de archivo, alguien nuevo al proyecto puede ubicar un archivo nuevo correctamente leyendo solo esta sección.

**Paso B8 — Sección "Naming de archivos".**

- Specs *(correcciones A4, A5)*: viven en **dos ubicaciones** (`docs/specs/` y `docs/`) y conviven **tres patrones** de naming:
  - Legacy fecha-prefijo `<fecha>_<id>_<nombre>.md` (mayoría, en `docs/specs/`). No se migran los viejos.
  - Prefijo `SPEC_<id>_<nombre>_v<ver>.md` (en `docs/specs/` y `docs/`); es el formato para specs nuevos a partir de S1.A.
  - Sufijo `<NOMBRE>_SPEC.md` (9 archivos en `docs/`).
  - El criterio de consolidación/coexistencia es decisión pendiente (ver B-04 y B-05 en §2).
- Archivos en `exports/cyn_backlog/`: prefijo-por-tipo, fecha opcional como sufijo. Prefijos **reales** presentes en el repo *(corrección A8 — se elimina `PROMPT_`, que no existe)*: `diagnostico_`, `verificacion_`, `experimento_`, `plan_`, `reporte_`, `inventario_`, `catalogo_`, `familia_`, `paso1_`, `clasificacion_`, `cruce_`, `bugs_`, `analisis_`, `informe_`, `investigacion_`, `validacion_`.
- Migraciones SQL: patrón `<NNN>_<nombre_descriptivo>.sql`, pero existen **dos árboles** *(validación)*: `migrations/` (12 archivos, ej. `024_spec_w_audit_actions.sql`, con sub-versión `024_1`) y `fase3_dashboard/sql/` (78 archivos, con **numeración colisionada** — números repetidos `018, 019, 042, 047, 048, 050, 051, 052, 053, 054b, 057, 065`).

  > **[DECISIÓN PENDIENTE — GERARDO] (B-06)** Hay dos árboles de migraciones SQL: `migrations/` (pipeline) y `fase3_dashboard/sql/` (dashboard/Supabase, hipótesis). ¿CONVENTIONS.md documenta los dos? ¿Resuelve/normaliza la colisión de numeración del segundo árbol, o la declara deuda conocida? ¿O documenta solo uno y declara el otro fuera de alcance?
- **Verificación**: la sección da 5 ejemplos concretos de archivos del repo (de cada patrón y ubicación) y muestra cómo cada uno encaja en su patrón.

**Paso B9 — Sección "Versionado de exports/cyn_backlog/".**

- Documentar la decisión del paso A2 (qué se versiona, qué no, por qué).
- **Reusar la entrada de `.gitignore` ya aplicada** *(corrección A9)*: el cierre de SPEC W del 2026-06-03 ya agregó el bloque "Limpieza pre-S1.A" con las reglas de `exports/cyn_backlog/` (ignorar `*.json`/`*.jsonl`/`*.xlsx`, conservar `!**/*.md`). B9 **referencia esa entrada existente, no la recrea** (evitar líneas duplicadas).
- Documentar el caveat conocido: el patrón top-level `exports/cyn_backlog/*.json` **no cubre subdirectorios** (`exp_raiz_skills/*.json` queda fuera). La ampliación a `**/*.json` es decisión pendiente (B-09, ver paso A2).
- **Verificación**: la sección coincide con lo que ya está en `.gitignore`, hay coherencia entre decisión escrita y configuración aplicada (sin duplicar reglas).

**Paso B10 — Sección "Responsabilidades por tipo de archivo" (condicional al paso A1).**

- Si la decisión del A1 fue introducir `CODEOWNERS`: crear el archivo `/CODEOWNERS`, listar las áreas y responsables, y desde CONVENTIONS.md referenciarlo.
- Si la decisión fue documentar informalmente: escribir la sección con las áreas y responsables en prosa, sin crear `CODEOWNERS`.
- Si la decisión fue no documentar por ahora: escribir una sección breve que diga "Esta sección queda pendiente; ver SERGIO.md para responsabilidades parciales" o equivalente.
- **Verificación**: la decisión del A1 está reflejada en CONVENTIONS.md de la forma elegida.

### Verificación de cierre de la Fase B

Una vez completados B1 a B10:

- `/CONVENTIONS.md` existe en la raíz, tiene las 9 secciones, todas con contenido (ninguna queda "por completar").
- Si correspondió por A1: `/CODEOWNERS` existe y es coherente con CONVENTIONS.md.
- `.gitignore` es coherente con la sección B9.
- Todos los links internos de CONVENTIONS.md resuelven (no apuntan a archivos inexistentes).

### Z2 — Riesgo descartado: ningún script parsea nombres de branches/specs

La validación confirmó que **ningún script del repo parsea nombres de branch ni de spec**. El único enforcement automatizado es `scripts/check_version_bumped.py`, que parsea los **archivos cambiados** de un commit (no nombres) para exigir bump de `database/MATCHER_VERSION` / `database/NLP_VERSION`. Conclusión operativa: **formalizar o renombrar convenciones de branch/spec no rompe ninguna automatización existente**. Este riesgo queda explícitamente descartado.

---

> *Secciones 5-8 (Dependencias, Validación, Riesgos, Criterio de aceptación) a desarrollar en la próxima tanda, una vez validados Entregables e Implementación.*
