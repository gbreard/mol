# MOL / OE — Preguntas Diagnósticas
## Gestión de Embeddings y Modelos · Spec para M-17 (Fine-tuning)

**Propósito:** Este documento contiene las 34 preguntas que deben responderse con código real antes de escribir el spec de gestión de embeddings. El driver es M-17: preparar la base de datos limpia para fine-tuning de BGE-M3.

**Instrucción:** Por cada pregunta, explorá el código o la base de datos según corresponda y respondé con el estado real. Si algo no existe, decilo explícitamente. No asumir ni inferir.

| Etiqueta | Sistema |
|----------|---------|
| `MOL` | Pipeline local (Python, ChromaDB) |
| `OE` | Supabase / pgvector (Next.js) |
| `Ambos` | Aplica a los dos |

---

## Bloque 0 — Estado actual del corpus

> Prerequisito para todo el spec. Sin esta información no se puede diseñar nada.

| # | Sistema | Pregunta |
|---|---------|----------|
| 1 | `MOL` | ¿Cuántas colecciones existen en ChromaDB hoy? ¿Cuáles son sus nombres y tamaños (cantidad de documentos)? |
| 2 | `MOL` | ¿Los documentos en ChromaDB tienen metadatos? ¿Qué campos tiene el objeto `metadata` en cada documento? |
| 3 | `MOL` | ¿Existe algún campo que indique la versión del modelo que generó el embedding, aunque sea informal (un string hardcodeado, un comentario)? |
| 4 | `MOL` | ¿El script que genera los embeddings ESCO / Perfil Argentino es idempotente? Si se corre dos veces, ¿duplica o reemplaza? |
| 5 | `MOL` | ¿ChromaDB está en disco local o en memoria? ¿Existe backup o está atado a la máquina local? |
| 6 | `OE` | ¿Las tablas `skills_embeddings` y `occupations_embeddings` en Supabase tienen columnas de metadatos además del vector? (ej: `created_at`, `model_version`, `embedding_dim`) |
| 7 | `OE` | ¿Los 14.247 embeddings de skills y los 3.045 de ocupaciones fueron todos generados en el mismo momento con el mismo modelo, o hay generaciones distintas mezcladas? |
| 8 | `OE` | ¿Existe alguna tabla o registro en Supabase que documente cuándo fue la última generación del corpus de embeddings? |

---

## Bloque 1 — Model Registry

> Versionado por fila: cada embedding sabe qué modelo lo generó.

| # | Sistema | Pregunta |
|---|---------|----------|
| 9 | `Ambos` | ¿Dónde está definida hoy la versión de BGE-M3 que se usa? ¿Es un string hardcodeado, variable de entorno, o archivo de configuración? |
| 10 | `Ambos` | ¿El mismo script/función que genera embeddings para ChromaDB (MOL) es el mismo que genera los que van a Supabase (OE), o son scripts separados? |
| 11 | `Ambos` | ¿Hay algún lugar donde se registre el hash o revisión exacta del modelo descargado de HuggingFace? (`BAAI/bge-m3` puede actualizarse silenciosamente si no se pinea una revisión específica.) |
| 12 | `Ambos` | ¿ChromaDB y Supabase usan la misma dimensión de vector (1024 dims)? ¿Está validado explícitamente en código o es una asunción? |

---

## Bloque 2 — Detección de drift y alertas push (M-02)

> El modelo BGE-M3 ya falló silenciosamente una vez. Este bloque evita que vuelva a pasar.

| # | Sistema | Pregunta |
|---|---------|----------|
| 13 | `MOL` | ¿Existe algún log de scores de matching por run que permita calcular distribución histórica? (media, percentil 10, tasa de scores bajo threshold por run) |
| 14 | `MOL` | Cuando BGE-M3 falló silenciosamente, ¿cómo se detectó finalmente? ¿Qué señal concreta hubiera permitido detectarlo de forma automática? |
| 15 | `MOL` | ¿Hay algún health check del modelo antes de que empiece el pipeline, o se asume que si el proceso arranca el modelo está ok? |
| 16 | `Ambos` | ¿Qué canales de notificación están disponibles y configurados hoy? (Telegram ya mencionado en M-02, email, ¿algo más?) |
| 17 | `MOL` | ¿El run actual registra timing por etapa (cuánto tardó el embedding, cuánto el matching)? Si no existe, ¿en qué punto del código podría insertarse ese registro? |

---

## Bloque 3 — Benchmark automático / Gold Set dinámico (M-10)

> El Gold Set es el único mecanismo de validación objetiva. Hoy tiene 49 casos estáticos.

| # | Sistema | Pregunta |
|---|---------|----------|
| 18 | `MOL` | ¿El Gold Set actual (49 casos) está en un formato fijo? ¿En qué formato exacto vive (Excel, JSON, SQLite)? ¿Quién puede modificarlo hoy? |
| 19 | `MOL` | ¿Existe algún mecanismo que impida modificar un caso del Gold Set para "pasar" un test que antes fallaba? ¿Hay control de versiones sobre el Gold Set? |
| 20 | `MOL` | ¿Las 15.968 validaciones humanas existentes tienen suficiente estructura para ser candidatas al Gold Set? ¿Qué campos tienen exactamente? |
| 21 | `MOL` | ¿Cuál es el criterio de calidad para que una validación humana entre al Gold Set? ¿Hay acuerdo documentado o es implícito? |
| 22 | `Ambos` | ¿El test del Gold Set debería correr solo sobre MOL, o también debería validar los embeddings de OE en Supabase? ¿Existen casos de test para OE? |

---

## Bloque 4 — Linaje end-to-end

> Trazabilidad completa desde texto crudo hasta vector almacenado. Prerequisito directo de M-17.

| # | Sistema | Pregunta |
|---|---------|----------|
| 23 | `MOL` | ¿Cada oferta procesada puede trazarse desde el texto crudo hasta el skill ESCO asignado en un solo query? ¿O requiere joins complejos entre múltiples tablas/archivos? |
| 24 | `MOL` | ¿Los `training_pairs` registran con qué versión del pipeline fueron generados? ¿Tienen campo de versión o timestamp? |
| 25 | `OE` | En Supabase, cuando se ejecuta un match `perfil → ocupación`, ¿queda registrado qué embeddings se compararon y con qué scores? ¿O solo el resultado final? |
| 26 | `MOL` | ¿Existe algún registro de qué versión de los embeddings ESCO estaba activa cuando se procesó una oferta específica? ¿O es imposible saberlo retroactivamente? |

---

## Bloque 5 — Pipeline de regeneración controlada

> Cuando cambie el modelo, todos los embeddings almacenados deben regenerarse de forma segura.

| # | Sistema | Pregunta |
|---|---------|----------|
| 27 | `Ambos` | ¿Cuánto tiempo tarda hoy generar todos los embeddings ESCO para ChromaDB? ¿Y para Supabase? (tiempo aproximado del proceso completo) |
| 28 | `OE` | ¿Existe algún script para regenerar los embeddings de Supabase, o solo existe el script de carga inicial? ¿Hay diferencia entre "crear desde cero" y "actualizar"? |
| 29 | `OE` | Si se regeneran los embeddings en Supabase con un modelo nuevo, ¿las RPCs existentes (`match_occupations_by_skills`, `expand_skills_semantic`) siguen funcionando sin cambios? ¿Dependen de la dimensión o normalización actual? |
| 30 | `MOL` | ¿ChromaDB permite tener dos colecciones con el mismo corpus pero modelos distintos en paralelo (para blue/green)? ¿Cuánto espacio en disco ocupa duplicar el corpus ESCO? |

---

## Bloque 6 — Conexión con M-17 (el driver real)

> Estas preguntas conectan los 5 bloques anteriores con el objetivo de fine-tuning.

| # | Sistema | Pregunta |
|---|---------|----------|
| 31 | `MOL` | ¿Los `training_pairs` acumulados tienen suficiente información para construir un dataset de fine-tuning? ¿Qué les falta exactamente para ser usables en entrenamiento? |
| 32 | `MOL` | ¿Cuántos pares `(tarea_argentina, skill_ESCO_correcta)` existen hoy con validación humana confirmada? ¿En qué tabla o archivo viven? |
| 33 | `Ambos` | ¿El proceso de fine-tuning de BGE-M3 correría local (64GB RAM / 12GB VRAM) o en cloud? ¿Hay alguna restricción de hardware que condicione el diseño del pipeline? |
| 34 | `Ambos` | Cuando exista un modelo fine-tuned, ¿necesita coexistir con el modelo base durante el período de validación, o puede reemplazarlo directamente? ¿Cuál es el criterio de go/no-go para el reemplazo? |

---

## Tabla resumen — Completar con las respuestas

| Característica | Estado actual | Gap identificado | Prioridad para M-17 |
|----------------|---------------|------------------|---------------------|
| Model Registry | | | |
| Detección de drift / M-02 | | | |
| Gold Set dinámico / M-10 | | | |
| Linaje end-to-end | | | |
| Pipeline regeneración | | | |
