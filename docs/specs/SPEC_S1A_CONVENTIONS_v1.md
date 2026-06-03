# SPEC S1.A — CONVENTIONS.md

> Versión v1 (borrador, secciones 1-2) · 2026-06-02
> **Estado:** Borrador · **Carril:** desarrollo · **Fase:** Fundación · **Versión cerebro destino:** 1.0.1
> **Entregable principal:** `CONVENTIONS.md` en la raíz del repositorio (o `docs/` según se defina)
> Spec parte del paraguas S1.A — Setup documental. Define las convenciones operativas del proyecto MOL para humanos e IA. Primer entregable del setup, prioritario por urgencia operativa (limpieza de branches, formalización de flujo de PR).

---

## 1. Propósito

Definir y documentar las **convenciones operativas** del proyecto MOL —cómo se nombran los branches, cómo se hacen los pull requests, qué formato tienen los commits, dónde vive cada tipo de archivo, qué herramientas se usan— en un único documento que sea referencia tanto para personas como para agentes de IA que asisten en el desarrollo.

Hoy estas convenciones existen pero están dispersas o solo en la cabeza del equipo: hay reglas de deploy en `DEPLOY_RULES.md`, hay nombres de branches que siguen un patrón (`spec/w-validacion-estructurada`) pero no documentado, hay specs que viven en `docs/specs/` por costumbre pero sin convención escrita. Esa dispersión genera dos problemas concretos: cuando alguien nuevo se incorpora (un colaborador, un agente de IA en otro chat) tiene que reconstruir las reglas leyendo entre líneas; y cuando algo se desordena (branches stale, commits sin formato), no hay un documento contra el cual corregir. El incidente del 22/03/2026 documentado en `DEPLOY_RULES.md` —cuando se pisó el trabajo de un sprint entero por falta de coordinación— es el ejemplo de lo que pasa sin convenciones explícitas.

CONVENTIONS.md cierra ese hueco. **No es manual del proyecto** (la filosofía vive en el master conceptual, el método en el documento de planificación, la guía para IA en CLAUDE.md). Es estrictamente las convenciones operativas que afectan el día a día del trabajo en el código.

---

## 2. Reutilización del sistema existente

El proyecto ya tiene piezas que cubren parte de lo que CONVENTIONS.md debe documentar. El trabajo del spec es **extraerlas, ordenarlas y completarlas**, no inventarlas desde cero.

### Lo que ya existe y se conserva

- **`DEPLOY_RULES.md`** cubre las convenciones de deploy: ambientes, quién deploya a producción, flujo de PR previo al deploy. Está bien escrito y vigente. CONVENTIONS.md lo **referencia, no lo absorbe**. La razón es que DEPLOY_RULES tiene una historia (el incidente del 22/03/2026) y un foco específico (deploy) que conviene mantener separados; mezclarlo en CONVENTIONS.md diluiría su urgencia.

- **Convención de nombres de branches en uso**: el branch actual `spec/w-validacion-estructurada` sigue el patrón `<tipo>/<descripcion-corta>`. Los branches stale `feature/si-sergio-ui` y `feature/bloque-I-procesamiento` muestran que el patrón evolucionó: antes era `feature/<...>`, ahora es `spec/<...>` para los specs y presumiblemente `feature/<...>` para otros tipos. CONVENTIONS.md **documenta el patrón actual** y lo formaliza.

- **Ubicación de specs en `docs/specs/`**: los specs A-U existen ahí. CONVENTIONS.md formaliza esa ubicación y la convención de nombres `SPEC_<id>_<nombre_corto>_v<versión>.md`.

- **Ubicación de masters en `docs/specs/`** (según decisión de esta sesión): `MOL_master_specs.md` vive ahí. CONVENTIONS.md documenta dónde viven los masters del proyecto.

### Lo que no existe y hay que crear

- **Convención de formato de commits**. No vi evidencia en el material disponible (los 9 commits del branch `spec/w-validacion-estructurada` tienen mensajes descriptivos pero no se ve un formato estricto tipo Conventional Commits). CONVENTIONS.md propondrá un formato.

- **Flujo de PR**. Está parcialmente cubierto por DEPLOY_RULES.md ("crear PR a main, Gerardo revisa y mergea") pero no hay convención sobre títulos de PR, descripción mínima, cuándo se piden cambios, cuándo se squashea. CONVENTIONS.md lo completa.

- **Política de limpieza de branches stale**. Hoy hay dos branches stale ya mergeados que nadie borró. CONVENTIONS.md define cuándo y cómo se limpian.

- **Convenciones de nombres de archivos** fuera de specs: scripts (`scripts/`), diagnósticos (`exports/cyn_backlog/`), documentos maestros, prompts para Claude Code. Hay patrones de hecho pero no documentados.

### Lo que se aclara con esta investigación

Una verificación rápida del estado del sistema reveló cosas concretas que CONVENTIONS.md debe registrar como decisiones, no como inventos:

- El proyecto tiene un branch activo (`spec/w-validacion-estructurada`) con 9 commits sin mergear y 2 archivos sin commitear. Esto sugiere que el flujo "spec arranca en su branch, se mergea cuando está implementado" funciona en la práctica.
- Hay 0 PRs abiertos. Sumado al estado del branch activo, indica que el flujo es: trabajar en branch hasta tenerlo listo, después PR + merge. No hay práctica de PRs tempranos para revisión incremental. CONVENTIONS.md puede consagrar esta práctica o proponer otra.

### Cosas que requieren más lectura antes de definir

Hay áreas donde no tengo suficiente información para proponer convención y conviene que vos confirmes o que un próximo paso del spec lo investigue:

- **Convención de nombres de migraciones SQL** (vi `migrations/024_spec_w_audit_actions.sql` y `migrations/024_1_spec_w_performance_filtros.sql` referenciados por el inventario, lo que sugiere un patrón `<NNN>_<spec>_<descripcion>.sql` con sub-versiones).
- **Convención de versionado interno de specs** (vi `SPEC_U-1_CRITICO_v3_1.md`, lo que sugiere `v<mayor>_<menor>` o `v<mayor>.<menor>`, pero hay variantes).
- **Quién es el responsable de qué tipo de archivo** (¿Sergio toca la UI, vos el cerebro, Cyn las validaciones? ¿Hay solapamientos?). Esto afecta qué se documenta como "responsabilidad por tipo de archivo" en CONVENTIONS.md.

---

> *Secciones 3-7 (Entregables, Dependencias, Validación, Riesgos, Criterio de aceptación) a desarrollar en la próxima pasada, después de validar tono y formato de las dos primeras.*
