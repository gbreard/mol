# MOL — Master de specs

> Versión 0.2 · 2026-06-02
> Documento operativo del plano técnico. Mientras `MOL_planificacion.md` define el qué y el por qué de cada sprint, este master organiza el cómo: qué specs existen, en qué carril y fase viven, qué entregan, cómo se validan, qué versión los incorpora, y dónde están sus dependencias. Es la vista panorámica de la evolución técnica del sistema.
>
> *Cambios desde v0.1:* S1 reorganizado como paraguas con dos sub-paraguas (S1.A documental, S1.B operativo por componente); CONVENTIONS.md marcado como primer entregable activo; agregada nota de alcance solo-cerebro; ubicación oficial del master definida en `docs/specs/MOL_master_specs.md`.

---

## 1. Cómo se usa este documento

Este es un master **híbrido**: índice panorámico de todos los specs (sección 3) y detalle expandido únicamente de los specs en desarrollo activo (sección 4). Los que están "en el índice" pero no expandidos se referencian para tener la vista completa, sin cargar el documento con información que aún no es accionable.

Un spec entra a la sección de "desarrollo activo" (sección 4) cuando cumple dos condiciones simultáneas: **(1)** pertenece a la fase de trabajo actual y **(2)** tiene información suficiente para escribirlo con detalle hoy. Si está en la fase actual pero falta investigar, queda en el índice con nota "a expandir". Si está claro pero no es su turno, queda en el índice como referencia futura.

El detalle de cada spec individual (el documento técnico completo, con código de ejemplo, schemas, etc.) vive en archivos separados en `docs/specs/`, siguiendo la convención de nombres de los specs A-U existentes: `SPEC_S<N>_<nombre_corto>_v<versión>.md`. Este master los referencia pero no los contiene.

### Alcance de este master

Este master cubre la **evolución técnica del cerebro del MOL** —el pipeline de procesamiento de ofertas, NLP, matching, perfil argentino, vocabulario vivo—. **No cubre las aplicaciones** que consumen los datos del cerebro (MOL Gestión, MOL Demanda, MOL Orientación), porque su evolución es independiente: cada app tiene su propio grado de madurez, sus propios usuarios y su propio versionado, que no coincide con las versiones del cerebro. MOL Gestión podría ir a v2.0 mientras el cerebro está en 1.1; MOL Orientación podría empezar de cero mientras Gestión está estable.

Las aplicaciones tendrán un **master de specs propio**, paralelo a éste, cuando llegue su momento de planificación a fondo. La filosofía del MOL es coherente con esta separación: el cerebro es infraestructura, las apps son productos sobre la infraestructura.

---

## 2. Convenciones

### Identificación

Los specs propios del cerebro siguen la convención **S1 a S11** definida en `MOL_planificacion.md` (sección "Mapa de specs para llegar a 1.0.1"). Los specs adyacentes existentes (serie A-U, serie M, SPEC W, etc.) conservan su identificación original.

### Versionado

Cada spec individual lleva su propio número de versión (`v1`, `v1.1`, `v2`...) independiente de la versión del cerebro. Un spec puede tener varias versiones antes de implementarse, y puede actualizarse después de implementado si cambia su alcance. La versión del **cerebro** (1.0.1, 1.1, 1.2…) indica en qué entrega se incorpora la implementación del spec, no su versión interna.

### Estados

Un spec atraviesa cuatro estados a lo largo de su vida:
- **Borrador**: el spec está siendo escrito, su contenido puede cambiar significativamente.
- **Aprobado**: el spec está cerrado, listo para implementar.
- **En implementación**: alguien (humano + IA) está construyendo el entregable según el spec.
- **Implementado**: el entregable existe, fue validado en los tres niveles, y forma parte de una versión del cerebro.

### Carriles y fases

Los specs se organizan en dos carriles (desarrollo, producción) y cuatro fases (fundación, específico 1.0.1, operación, cierre del ciclo), tal como define el "Mapa de specs para llegar a 1.0.1" del documento de planificación.

### Ubicación física

Todos los specs viven en `docs/specs/` del repositorio, junto a los specs A-U existentes. Esta convención facilita el cruce entre nuevos y existentes sin separar artificialmente.

---

## 3. Índice por carril y fase

### 3.1. Carril de desarrollo

#### Fase 1 — Fundación (transversal a todas las versiones)

| Spec | Nombre | Estado | Versión cerebro | Detalle |
|---|---|---|---|---|
| **S1** | Setup del sistema actual *(paraguas, ver §4.1 y §4.2)* | Borrador | 1.0.1 | **§4.1, §4.2** |
| **S3** | Harness como infraestructura permanente | Borrador | 1.0.1 | **§4.3** *(activo)* |
| **S5** | Versionado del dato | Borrador | 1.0.1 | **§4.4** *(activo)* |

S1 se trabaja como **paraguas** con dos sub-paraguas:
- **S1.A — Setup documental** (§4.1): cuatro entregables documentales que se trabajan en orden y se cierran en semanas.
- **S1.B — Setup operativo por componente** (§4.2): cómo se trabaja cada componente vivo del sistema bajo los dos carriles. Se aborda componente por componente, después de tener S1.A cerrado.

#### Fase 2 — Específico de 1.0.1

| Spec | Nombre | Estado | Versión cerebro | Detalle |
|---|---|---|---|---|
| **S2** | Reutilización para 1.0.1 | Por escribir | 1.0.1 | índice (depende de S1) |
| **S4** | Compuerta de score | Por escribir | 1.0.1 | índice (requiere investigación previa del matcher) |

#### Fase 6 — Promoción y cierre del ciclo de versiones

| Spec | Nombre | Estado | Versión cerebro | Detalle |
|---|---|---|---|---|
| **S6** | Promoción de versiones (validación y rollback) | Por escribir | 1.0.1 | índice (depende de S3) |

### 3.2. Carril de producción

#### Fase 3 — Operación del run

| Spec | Nombre | Estado | Versión cerebro | Detalle |
|---|---|---|---|---|
| **S7** | Operación del run productivo | Por escribir | 1.0.1 | índice |
| **S8** | Lectura de calidad por run | Por escribir | 1.0.1 | índice |
| **S9** | Gestión de la cola de revisión humana | Por escribir | 1.0.1 (parcial: SPEC W + T existentes) | índice |

#### Fase 4 — Cierre del ciclo entre carriles

| Spec | Nombre | Estado | Versión cerebro | Detalle |
|---|---|---|---|---|
| **S10** | Reproceso selectivo | Por escribir | 1.1 (no 1.0.1) | índice (requiere saneo previo del drift de SPEC H) |
| **S11** | Retroalimentación producción → desarrollo | Por escribir | 1.0.1 (parcial: SPEC T Fase 1 existe) | índice |

### 3.3. Frente transversal — Abstracción de modelos

| Spec | Nombre | Estado | Versión cerebro | Detalle |
|---|---|---|---|---|
| Interfaz unificada de modelos | Por escribir | 1.1 o posterior | índice |
| Versionado de modelos | Por escribir | 1.1 o posterior | índice (SPEC E es primer paso parcial) |
| Evaluación comparativa en harness | Por escribir | 1.2 o posterior | índice (depende de S3) |

---

## 4. Specs en desarrollo activo

Los specs activos siguen este **template estándar** de 7 secciones:

1. **Propósito**: qué problema resuelve el spec, en una o dos frases.
2. **Reutilización del sistema existente**: qué del código actual, de los specs adyacentes y de la UI existente sirve a este spec. Este ejercicio se hace al inicio del desarrollo del spec, no antes, y es parte del trabajo del spec mismo. Se apoya en el inventario y en lectura directa del código en el momento.
3. **Entregables**: qué produce el spec (código, configuración, documentación, esquema de base, etc.), en qué archivos vive, en qué forma.
4. **Dependencias**: qué otros specs o piezas del sistema necesitan estar listos antes.
5. **Validación**: cómo se verifica que el entregable funciona, en tres niveles integrados:
   - **Tests de código**: qué se verifica automatizado a nivel unitario y de integración.
   - **Test end-to-end**: cómo se verifica que la función completa atraviesa el sistema y produce el output esperado.
   - **QA humana**: qué requiere mirada de un humano para considerarse aceptado (quién, sobre qué muestra, qué mira, umbral de aceptación, qué pasa si no pasa).
6. **Riesgos identificados**: qué cosas pueden salir mal o dejar deuda nueva (drift, contradicciones con specs adyacentes, dependencias frágiles), con una idea de cómo mitigarlas.
7. **Criterio de aceptación**: las condiciones binarias que el spec debe cumplir para considerarse implementado.

El detalle técnico completo de cada spec (código de ejemplo, schemas SQL, contratos de API, etc.) vive en su archivo individual en `docs/specs/`. Lo que sigue en este master es el **marco** de cada spec activo, no el spec técnico completo.

---

### 4.1. SPEC S1.A — Setup documental

**Estado:** Borrador · **Carril:** desarrollo · **Fase:** Fundación · **Versión cerebro destino:** 1.0.1

**Alcance**: cuatro entregables documentales que definen dónde vive cada cosa y cómo se trabaja a nivel de proyecto. Se desarrollan en orden, cerrando cada uno antes de pasar al siguiente, porque el equipo es chico y el método pide entregables verificables.

| Entregable | Función | Estado | Activo |
|---|---|---|---|
| **CONVENTIONS.md** | Convenciones operativas para humanos e IA: branches, PR, formato de commits, ubicación de specs, ubicación de masters | Borrador | **Activo** |
| **CLAUDE.md** (reescrito) | Guía operativa para agentes de IA (Claude Code, Cursor, etc.). Referencia a CONVENTIONS.md para todo lo que aplica también a humanos | Por escribir | Agendado |
| **INDEX.md** | Mapa de navegación del proyecto: lista de documentos maestros, su función y cómo se relacionan | Por escribir | Agendado |
| **Inventario formalizado** | Formalización del inventario como práctica recurrente: gatillo (al cierre de cada versión del cerebro), criterio de actualización (puntual o entera según tamaño del cambio), ubicación (`exports/cyn_backlog/inventario_mol_<fecha>.md`) | Por escribir | Agendado |

**Orden de desarrollo**: CONVENTIONS → CLAUDE.md → INDEX → Inventario formalizado.

**Razón del orden**: CONVENTIONS es lo más urgente operativamente (sin convenciones escritas los branches y commits se desordenan); CLAUDE.md se reescribe después porque referencia CONVENTIONS; INDEX se hace cuando los otros documentos están vivos para indexarlos; el inventario se formaliza al final porque es la práctica que sostiene a las demás.

> *Detalle (las 7 secciones del template) del primer entregable —CONVENTIONS.md— a desarrollar en la próxima pasada del master.*

### 4.2. SPEC S1.B — Setup operativo por componente

**Estado:** Agendado · **Carril:** desarrollo · **Fase:** Fundación · **Versión cerebro destino:** 1.0.1 → 1.1

**Alcance**: para cada componente vivo del sistema, definir cómo se trabaja bajo los dos carriles (desarrollo y producción), cómo se versiona, qué validación aplica, cómo se introduce un cambio sin romper la producción. Es lo que vuelve concreto el método de dos carriles para cada parte del sistema; sin esto, el método queda abstracto y se improvisa cada vez.

**Componentes a cubrir, en el orden de trabajo decidido**:

| # | Componente | Razón del orden | Estado |
|---|---|---|---|
| 1 | **Scraping** | Es la entrada del pipeline. Sin definir cómo se trabaja el scraping, no sabemos qué llega al NLP | Agendado |
| 2 | **NLP** | Es lo siguiente en el flujo y ya hay diagnósticos sólidos sobre su comportamiento | Agendado |
| 3 | **Skills + ocupaciones + matching** | Es lo más entrelazado y el corazón de los sprints planificados (0, 1, 2) | Agendado |
| 4 | **Diccionario / perfil argentino + reglas** | Son configuraciones que dependen de cómo trabaja el resto | Agendado |

**Estrategia de trabajo**: componente por componente, después de tener S1.A cerrado. Cada componente es un mini-spec dentro de S1.B con su propio propósito, reutilización, entregables, validación, riesgos y criterio de aceptación. No hace falta tener todos los componentes definidos para empezar a trabajar el primero; se cierra uno y se pasa al siguiente.

**Bloqueante**: S1.A debe estar cerrado antes de empezar S1.B, porque CONVENTIONS y CLAUDE.md son donde van a vivir las referencias que S1.B necesite.

> *Detalle de cada componente a desarrollar en pasadas posteriores, una vez S1.A esté cerrado y el primer componente (Scraping) entre a trabajo activo.*

### 4.3. SPEC S3 — Harness como infraestructura permanente

**Estado:** Agendado · **Versión:** v1 · **Carril:** desarrollo · **Fase:** Fundación · **Versión cerebro destino:** 1.0.1

> *Detalle (las 7 secciones del template) a desarrollar después de cerrar S1.A.*

### 4.4. SPEC S5 — Versionado del dato

**Estado:** Agendado · **Versión:** v1 · **Carril:** desarrollo · **Fase:** Fundación · **Versión cerebro destino:** 1.0.1

> *Detalle (las 7 secciones del template) a desarrollar después de cerrar S1.A.*

---

## 5. Vista inversa: qué specs materializa cada sprint del master conceptual

Esta vista permite, partiendo de un sprint del master conceptual, ver qué specs del master de specs lo materializan. Es el cruce inverso del índice de §3.

| Sprint del master | Specs compartidos (del mapa S1-S11) | Specs propios del sprint |
|---|---|---|
| **Acción inmediata / 1.0.1** | S1, S2, S3, S4, S5, S6, S7, S8, S9, S11 | — (toda la base ya está en el mapa) |
| **Sprint 0 — Captura de emergentes** | S1 act., S2, S3, S5, S6, S10, S11 | Spec de captura de skills sin URI; spec de almacenamiento con identidad propia; spec de separación señal/ruido. **Lectura previa:** SPEC M-06, SPEC M-13 |
| **Sprint 1 — Conexión perfil argentino** | S1 act., S2, S3, S5, S6, S10, S11 | Spec de refactor del matcher (no activación de flag); spec de calibración y medición de impacto. **Lectura previa:** SPEC U-1 v3.1, SPEC J |
| **Sprint 2 — Ruteo por escenario** | S1 act., S2, S3, S5, S6, S10, S11 | Spec del clasificador de ruteo; spec de los centinelas; spec de convergencia C2/D; spec del flujo nuevo (embudo → ruteo) |
| **Sprint 3 — Institucionalización** | S1 act., S2, S3, S5, S6, S10, S11 | Spec de identidad propia argentina; spec del umbral y validación de promoción; **spec del invocador del cierre de cadena post-aprobación** (la maquinaria SQL existe, falta el invocador en código) |
| **Sprint 4 — Autopropagación** | S1 act., S5 | Spec de métrica de migración tarea/requisito entre cortes temporales |
| **Sprint 5+ — Soberanía** | — | Documento estratégico de decisión, no spec técnico |
| **Frente transversal — Modelos** | S1, S3, S5 | Spec de interfaz unificada; spec de versionado de modelos; spec de evaluación comparativa |

---

## 6. Specs adyacentes existentes

Specs identificados por el inventario `inventario_mol_2026-06-01.md` que ya existen en `docs/specs/` y que conviene tener mapeados para evitar duplicación o contradicción con specs nuevos.

> *Esta sección se llena en una pasada posterior, agrupando los specs A-U, serie M, SPEC W, etc., con su estado declarado y sus cruces verificados con los specs nuevos del mapa.*

---

## Próximas pasadas de este documento

1. **Validar este esqueleto** con vos antes de avanzar.
2. **Desarrollar el detalle** de los tres specs activos (S1, S3, S5) en §4, con los tres niveles de validación incluidos.
3. **Completar §6** con el mapeo de specs adyacentes existentes.
4. **Mantener el índice al día** a medida que specs entren o salgan del estado "activo".
