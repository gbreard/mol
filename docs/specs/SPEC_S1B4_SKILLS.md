# SPEC S1.B.4 — Relevamiento de Skills

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo + Cyn + modelo conceptual) · 2026-06-05
> Cuarto spec de la fase S1.B — Relevamiento del sistema. Releva el componente de Skills del proyecto MOL. Sigue la plantilla común del master v0.2.
> **Particularidad**: este componente tiene marco teórico propio — el "Modelo conceptual del MOL: pipeline, escenarios de skills y vocabulario vivo" v1.0 (2026-05-30), que define los 5 escenarios de skills y un mapeo de capacidades que la capa 5.2 verifica contra el código.

---

## 5.1 Memoria operativa — Gerardo + Cyn + modelo conceptual

### El marco: el modelo conceptual de los 5 escenarios

Gerardo escribió en mayo 2026 un documento conceptual que teoriza el componente de Skills a partir de 7 meses de prueba y error. Sus piezas centrales:

- **Las tareas son el ancla confiable**: las empresas describen con precisión las tareas; las skills explícitas declaradas en requisitos son mezcla heterogénea. Principio: las skills se infieren de las tareas matcheando contra la ontología vectorizada.
- **Dos naturalezas de skill**: institucionalizada (tiene URI ESCO, interoperable) vs emergente (aparece en el mercado argentino, sin URI todavía — GCP, Grafana, RAG, Bejerman, Xubio). La ausencia de URI no equivale a ausencia de valor: las emergentes son la señal anticipada del mercado.
- **Cinco escenarios** según origen (tarea vs declarada) y relación con ESCO (en canon / fuera de canon / mapeo deficiente / sin URI / genérica): A conservar · B perfil argentino → conectar a la decisión de ocupación · C1 distorsión silenciosa / C2 pérdida · D emergente → capturar · E transversal → registrar sin peso.
- **El embudo único actual**: hoy toda skill pasa por un gate ESCO-cerrado (similitud ≥0.40 o se pierde). El modelo propone reemplazarlo por ruteo explícito por escenario con centinelas en las fronteras.
- **Mapeo de capacidades (sección 6 del documento)**: CONSERVAR (extracción de skills desde tareas; ocupación granular; atributos) · CONECTAR (perfil argentino que hoy solo ajusta presentación; training data de correcciones que no alimenta mejora; ciclo de detección de frecuentes incompleto) · CREAR (registro de emergentes con identidad propia; clasificador de ruteo; centinelas; abstracción de modelos de IA) · DESCARTAR (derivación inversa ocupación→skill arbitraria; log de descartes como cementerio).
- **Principio transversal — abstracción de modelos de IA**: ningún LLM ni modelo de embeddings clavado en el código. Converge exactamente con el contexto fundante registrado en S1.B.3 ("quisimos pasar a otro modelo y nos dimos cuenta que no se puede") y con el Principio 7 de Matching.

El documento es un punto de partida que puede cambiar (palabras de Gerardo), pero define el horizonte conceptual del componente. **Verificación pendiente en 5.2: si el documento está versionado en el repo.**

### Arquitectura conceptual confirmada por Gerardo

**Las tareas NO son skills.** De las tareas se infieren los skills usando ESCO (BGE-M3 sobre la ontología vectorizada). Las skills explícitas declaradas en la oferta complementan. Coincide con el ancla del modelo conceptual.

### El diccionario argentino — origen y rol actual

- **Cómo se armó**: junto con Claude (el LLM), combinando lo que Claude sabe sobre el mercado argentino con curaduría humana. 44 ocupaciones, 291 skills.
- **Rol actual**: actúa como **boost +0.05 post-match** — ajusta la presentación después de que la ocupación ya fue decidida. El modelo conceptual identifica esto como la desconexión central (Escenario B sin conectar): el perfil argentino captura las asociaciones que la realidad local demanda, pero no participa de la decisión de ocupación. Es la intervención de mayor retorno según el modelo (Sprint 1, esfuerzo chico, avance ~60%).

### Los embeddings ESCO — generados una vez, nunca actualizados

Respuesta textual de Gerardo (SK-3): los embeddings se generaron **una sola vez desde la ontología ESCO en RDF** y nunca se pensó en su actualización ni en su almacenamiento centralizado.

Dos consecuencias que Gerardo identifica:

1. **ESCO saca versiones nuevas** y el sistema no tiene camino de actualización. La vectorización está congelada en la versión de ESCO con que se generó (¿cuál? — a verificar en 5.2).
2. **Idea arquitectónica de Gerardo**: la vectorización de ESCO debería ser un **repositorio centralizado en la máquina local** que provea vectores a todos los proyectos que los soliciten — por ejemplo, un harness en un sandbox que quiera probar contra ESCO sin regenerar todo. Hoy cada proyecto que necesita los vectores los duplica o no puede acceder.

### Las skills emergentes — estado desconocido

Gerardo cree que es deuda ("me parece que eso es deuda, no lo sé"). El sistema tiene una función `recalcular_emergentes` en Supabase con 3 versiones SQL conviviendo (hallazgo de S1.B.1, deuda D-07 de BD). El modelo conceptual dice que existe "un mecanismo de detección de skills frecuentes y un panel de aprobación humana, pero la cadena posterior a la aprobación está cortada" (Sprint 3, avance ~15%). A verificar en 5.2: qué existe realmente y en qué estado.

### El LoRA perdido (registrado también en S1.B.3)

El modelo fine-tuneado de mayo se hizo en disco C, se borró sin querer, no quedó nada. `data/finetuning/matching/` vacío. Se registra acá porque el fine-tuning era del componente de skills/matching semántico.

### La experiencia de Cyn con las skills (validadora humana)

- **Calidad de extracción**: mezclada. "Algunas skills salen de una palabra suelta y no de la tarea completa" — coincide con el patrón de error del matching (palabra puntual vs contexto).
- **Explícitas vs implícitas**: las explícitas (declaradas en el aviso) andan mejor que las implícitas (inferidas).
- **Evolución que Cyn nota**: antes el sistema inventaba skills que no estaban; ahora el problema dominante es la **omisión** — faltan skills que sí están en el aviso.
- **Duplicadas**: no ve duplicadas (ej. "Excel" y "Microsoft Excel" a la vez).
- **Su herramienta de trabajo está rota para skills**: **no puede agregar skills faltantes ni borrar incorrectas desde la UI**. Trabaja copiando todo al campo "observaciones" como texto libre y justificando por escrito. La validadora del sistema trabaja alrededor de la herramienta, no con ella. (Deuda de UI, S1.B.7, registrada también en S1.B.3 D-09.)

### Lo que Gerardo no sabe (a verificar en 5.2)

- **Gold set de skills** (`tests/nlp/gold_set.json`, 49 casos): cree que son de matching, una parte hecha a mano. Relación real con los gold sets de matching: a verificar.
- **`filtrar_por_trust`** (método eliminado del extractor, detectado en drift de tests): Gerardo ni sabía que existía.
- **Diccionarios de skills vivos vs abandonados**: no sabe cuáles son los vigentes.

### Hipótesis tentativas para la capa 5.2

1. **El mapeo de capacidades del modelo conceptual (sección 6) es verificable contra el código**: las 3 capacidades a CONECTAR existen pero desconectadas; las 4 a CREAR no existen; las 2 a DESCARTAR existen y estorban. La 5.2 confirma o corrige ese mapa.
2. **El gate del embudo único (similitud ≥0.40) existe en el código** y es el punto donde hoy se pierden las emergentes.
3. **El "log de descartes como cementerio"** del modelo conceptual probablemente se relacione con la tabla `validation_errors` (278K filas, sorpresa de S1.B.1) o con un log propio del extractor de skills.
4. **La vectorización ESCO no registra de qué versión de ESCO proviene** ni cuándo se generó — sin trazabilidad de origen.

### Notas para fases posteriores

- **Repo centralizado de vectores ESCO** (idea de Gerardo): principio arquitectónico para la 5.4 y candidato a spec propio en la reparación.
- **La conexión del perfil argentino a la decisión** (Sprint 1 del modelo) es la intervención de mayor retorno identificada — pero se diseña en S1.C con el cuadro completo, no acá.
- **Deuda de UI para skills** (no poder agregar/borrar): pertenece a S1.B.7.

---

> *Versión 0.1 — Capa 5.1 cerrada (fuentes: Gerardo + Cyn + modelo conceptual v1.0). Capa 5.2 pendiente, próximo paso.*
