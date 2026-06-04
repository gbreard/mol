# MOL — Master de relevamiento del sistema (Fase S1.B)

> Versión 0.1 (borrador) · 2026-06-04
> Documento operativo de la fase de relevamiento. Define qué relevar, en qué orden, cómo, y cómo lo relevado se conecta con la fase posterior de reparación. Es el mapa de la fase intermedia entre el setup documental (S1.A, en curso) y los sprints de mejora del cerebro (Sprint 1 en adelante).

---

## 1. Propósito

El proyecto MOL evolucionó más rápido que su documentación, sus tests y su código verificable. Las dos sesiones de los días 2026-06-02 y 2026-06-03 destaparon que la deuda no es solo documental: el repo tiene archivos desactualizados respecto al sistema corriendo, hay componentes con historia operativa que ningún archivo registra ("patos rengos" como el LoRA borrado del disco), y datos críticos (como el Gold Set ampliado) viven en operación pero no están versionados.

Esto significa que **no podemos planificar nuevos sprints sobre supuestos**. Antes de cualquier refactor del matcher (Sprint 1) o cualquier reescritura sustantiva, hace falta saber con qué realidad estamos trabajando.

La fase S1.B — Relevamiento del sistema produce ese conocimiento. Es la aplicación sistemática del principio "Descubrir antes de definir" (`docs/MOL_planificacion.md` v0.5) a todos los componentes del sistema. No es documentación por documentación: cada spec de relevamiento produce además **la deuda detectada** y **el diseño objetivo**, para que lo relevado sirva como cimiento de las reparaciones que vienen después.

## 2. Decisiones de método registradas el 2026-06-04

Las tres decisiones que estructuran esta fase, tomadas explícitamente al diseñar el master:

**Decisión 1 — Tres capas por spec de relevamiento.** Cada uno de los 7 specs produce: (a) estado actual relevado, (b) deuda detectada con prioridad, (c) diseño objetivo del componente sano. Sin la capa (b) el relevamiento se vuelve archivo descriptivo; sin la capa (c) la reparación posterior se diseña improvisando.

**Decisión 2 — Master de reparación al final.** Cuando los 7 specs estén terminados, se arma un master de reparación que reúne todas las deudas detectadas, las ordena por urgencia y dependencia, y produce la lista priorizada de specs de reparación que vienen después. Esto cierra el círculo relevar → diagnosticar → diseñar → reparar.

**Decisión 3 — Sprint 1 se mueve más atrás.** La secuencia real es: Setup documental (S1.A, en curso) → Relevamiento (S1.B, esta fase) → Reparación (S1.C, a definir con el master de reparación) → Sprints de mejora del cerebro. No se toca el matcher hasta tener base sólida para hacerlo.

## 3. Los 7 specs de relevamiento

Cada uno con alcance, qué cubre y qué no cubre.

### S1.B.1 — Relevamiento de Bases de Datos
**Alcance**: VPS, BD local, Supabase, sincronización entre ellas, cron asociado.
**Cubre**: qué tablas viven en cada BD, qué se sincroniza con qué frecuencia, migraciones aplicadas vs declaradas (los 4 árboles SQL ya identificados), volúmenes productivos actuales, estado de la sincronización (¿funciona, falla, falla a veces?), tabla ofertas × skills y su crecimiento.
**No cubre**: rediseño de la arquitectura de BD, decisiones de migración, optimización de queries. Eso es trabajo de specs de reparación posteriores.

### S1.B.2 — Relevamiento de Scraping
**Alcance**: scrapers por portal de empleo, dónde corren (VPS / local / ambos), cron de orquestación, alimentación de BDs.
**Cubre**: lista de portales scrapeados, estado de cada scraper, detección de duplicados, detección de republicaciones, manejo de errores, frecuencias de corrida, conexión con UI (paneles de monitoreo si existen).
**No cubre**: agregar portales nuevos, rediseñar el sistema de scraping. Solo relevamiento del estado actual.

### S1.B.3 — Relevamiento de Matching
**Alcance**: matcher v3.5.x (resolver primero qué versión corre realmente), reglas R-XXX activas, Gold Set, conexión con UI.
**Cubre**: versión real corriendo, archivo de versión vs código, Gold Set ampliado (la historia del fine-tuning del LoRA y casos validados), reglas R-XXX vigentes y cómo se mantienen, regresión R240 detectada en tests del 2026-06-03, conexión con paneles de validación humana, ruta de las correcciones.
**No cubre**: refactor del matcher (eso es Sprint 1, post-reparación).

### S1.B.4 — Relevamiento de Skills
**Alcance**: extractor de skills, modelo semántico activo, diccionarios, gold sets de skills.
**Cubre**: la historia del LoRA (cuándo se hizo, dónde estaba, por qué se borró, qué quedó), modelo activo real (BGE-M3 base si no hay LoRA), diccionarios argentinos vs ESCO vs curados, umbrales, gold sets de skills, conexión con UI (dashboard de skills, canonización).
**No cubre**: rehacer el LoRA, decidir si volver al modelo dual. Solo relevar qué hay.

### S1.B.5 — Relevamiento de NLP
**Alcance**: NLP v11.x (resolver primero qué versión corre), reglas, configs, gold sets de NLP.
**Cubre**: versión real corriendo (el desfase 11.3.1 vs texto "v11.4 source-aware" a resolver), reglas activas, configs vigentes, gold set NLP (verificado en 49 en disco, posiblemente desactualizado como el de matching), conexión con UI (revisión humana, validación de reglas, dashboard de severidades).
**No cubre**: cambios al NLP, nuevas reglas. Solo estado actual.

### S1.B.6 — Relevamiento de Pipeline operativo
**Alcance**: orquestación general del sistema, comandos del día a día, herramientas administrativas.
**Cubre**: cron del VPS, secuencia de procesamiento, locks y anti-pollers, `.ai/learnings.yaml` y cómo se mantiene, comandos de operación, paneles de monitoreo del pipeline en UI.
**No cubre**: rediseñar la orquestación. Solo relevar lo que está.

### S1.B.7 — Relevamiento de UI / Dashboard
**Alcance**: arquitectura del frontend, módulos, rutas, conexiones con el cerebro.
**Cubre**: estructura del dashboard, módulos vigentes (OE, validación humana de Cyn, paneles de Cyn, paneles administrativos), rutas API y su estado (la deuda de OE-11 con 13 endpoints sin guard que aparecieron en los tests del 2026-06-03), autenticación, tabla de qué pantalla lee de qué tabla.
**No cubre**: rediseñar UI, decidir sobre OE-11. Solo relevar.

## 4. Orden y dependencias

El orden es **Bases de Datos → Scraping → Matching → Skills → NLP → Pipeline → UI**.

Razones del orden:

- **BD primero** porque todo lo demás se apoya en saber qué tablas hay, dónde viven, qué se sincroniza. Sin esto, los otros relevamientos asumen estructuras de BD que pueden no ser ciertas.
- **Scraping segundo** porque es la primera fase del modelo del sistema (Adquisición → Procesamiento → Presentación) y alimenta todo lo que viene después.
- **Matching tercero** porque es el sprint más cercano (Sprint 1) y conviene relevarlo cerca, para que la deuda detectada pueda alimentar el master de reparación pronto.
- **Skills y NLP cuarto y quinto** porque dependen conceptualmente de Matching (las skills se matchean, el NLP alimenta el matching), pero su relevamiento es relativamente independiente.
- **Pipeline sexto** porque cubre la orquestación general y conviene hacerlo cuando ya entendemos los componentes individuales.
- **UI séptimo** porque consume todo lo anterior. Releva las conexiones con el cerebro, así que se beneficia de tener los otros 6 ya relevados.

Esto es orden recomendado, no rígido. Si durante el relevamiento de un spec descubrimos que necesitamos saber algo del siguiente, podemos hacer una pasada corta de verificación adelantada sin escribir el spec completo.

## 5. Plantilla común de los specs de relevamiento

Cada uno de los 7 specs sigue la misma estructura interna:

### 5.1 Memoria operativa de Gerardo

Pasada inicial donde Gerardo vuelca lo que sabe sobre el componente que ningún archivo registra: historia del componente, decisiones tomadas en algún momento, "patos rengos" conocidos, excepciones, cosas que se hicieron y se desandaron, intuiciones sobre qué anda mal.

Esto **se documenta apenas Gerardo lo dice**, no se mantiene solo en el chat. Es input crítico, no comentario complementario.

### 5.2 Estado actual relevado (capa A)

Claude Code verifica contra el código y los archivos del repo todo lo que Gerardo aportó en 5.1, más una pasada general de la realidad del componente. Produce: qué hay efectivamente, dónde, en qué condición, qué desfases hay entre lo que dice la doc, lo que dicen los archivos y lo que efectivamente corre.

### 5.3 Deuda detectada (capa B)

Lista de problemas concretos encontrados, con: descripción, urgencia (bloquea sprint, bloquea producción, no bloquea pero genera ruido, etc.), qué spec o sprint debería resolverlo, qué hacer mientras tanto.

### 5.4 Diseño objetivo (capa C)

Cómo debería verse este componente cuando esté sano. No es "cómo se repara" — eso es trabajo de specs de reparación posteriores. Es el norte hacia el cual diseñar las reparaciones.

### 5.5 Validación

Cómo se verifica que el spec de relevamiento está terminado: criterios binarios, lo que tiene que estar presente, lo que no se cierra hasta resolverse.

## 6. División de trabajo

- **Gerardo**: aporta memoria operativa (apartado 5.1), autoriza decisiones, valida contenido al cerrar cada spec.
- **Claude (en la conversación)**: estructura los specs, redacta, propone formato, sugiere recomendaciones.
- **Claude Code**: verifica contra el código y los archivos, releva el estado real, aplica las correcciones acordadas, ejecuta operaciones git.
- **Sergio**: no participa en esta fase. El spec de UI (S1.B.7) lo releva Gerardo aunque toque área de Sergio. Es relevamiento, no rediseño.

## 7. Conexión con la fase siguiente (S1.C — Master de reparación)

Cuando los 7 specs de relevamiento estén cerrados, se arma el master de reparación. Su trabajo es:

1. **Reunir todas las deudas detectadas** en los 7 specs (capa B de cada uno).
2. **Ordenarlas por urgencia y dependencia**: qué bloquea qué, qué desbloquea qué.
3. **Agrupar las deudas afines** en specs de reparación: por ejemplo, si BD y NLP tienen deuda relacionada con sincronización, puede ser un solo spec de reparación que las cubra.
4. **Producir el plan de reparación**: lista priorizada de specs de reparación que vienen, con su alcance y su urgencia.

Sin ese master no se arranca a reparar. La razón es la misma que la de esta fase: no improvisar las reparaciones tampoco.

## 8. Criterio de "spec de relevamiento cerrado"

Cada spec de relevamiento se considera cerrado cuando:

1. La memoria operativa de Gerardo (5.1) está documentada.
2. La capa A (estado actual relevado) está completa y verificada por Claude Code.
3. La capa B (deuda detectada) tiene cada ítem con descripción, urgencia y propietario.
4. La capa C (diseño objetivo) está escrita en un nivel que permite diseñar reparaciones contra ella.
5. Gerardo validó contenido.
6. El spec está mergeado a main siguiendo CONVENTIONS.md.

## 9. Estado actual de la fase

**Spec 1 (Bases de Datos)**: pendiente de arranque.
**Specs 2-7**: pendientes.
**Master de reparación (S1.C)**: pendiente, posterior a los 7 relevamientos.

El orden de arranque es S1.B.1 (Bases de Datos) en cuanto se cierre el setup documental S1.A o en paralelo si las decisiones operativas lo permiten.

---

## Anexo — Lo que se sabe de antemano antes de relevar cada componente

Memoria preliminar de Gerardo aportada el 2026-06-04, antes de escribir los specs individuales. Se actualizará a medida que cada spec arranque.

**Bases de Datos**:
- Son varias BD. Deberían poder estar sincronizadas. Hay problemas operativos para "enchufar" ofertas con skills.
- La tabla intermedia (ofertas × skills) está creciendo mucho, posiblemente más de 1 millón de filas. Riesgo de escalamiento futuro.

**Skills**:
- El LoRA se hizo en el disco C local, consumió toda la capacidad disponible, hubo que borrarlo.
- El estado quedó como "pato rengo": el doc menciona el LoRA como activo, el código probablemente lo intenta cargar con fallback, en operación corre BGE-M3 base.

**Matching**:
- El Gold Set se amplió hace aproximadamente un mes (mayo 2026) durante el fine-tuning del LoRA. El propio modelo propuso casos, se validaron, se agregaron.
- Pasó de 49 casos a más de 100. Esa ampliación nunca se reflejó en el repo (`gold_set_manual_v2.json` sigue en 49).
- Ubicación actual: desconocida para Gerardo en este momento.

**NLP, Scraping, Pipeline, UI**: memoria preliminar a aportar al inicio de cada spec.

---

*Versión 0.1, borrador para discusión.*
