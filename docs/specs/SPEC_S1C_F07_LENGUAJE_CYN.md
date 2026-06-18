# SPEC S1C-F0.7 — Discovery del lenguaje de Cyn (read-only)

> **Estado:** Fase 2 completa · categorías validadas por Cyn · clasificación + split listos · **Fecha:** 2026-06-18
> **Branch:** `spec/s1c-f07-lenguaje-cyn` · **Tipo:** discovery puro (read-only, cero implementación).

## Propósito

Primer paso de la Fase 2 del master y habilitante del **cierre del loop de Cyn (Eje 2)**.
Antes de devolver las correcciones de Cyn al sistema, hay que **entender qué escribe
Cyn realmente** en el texto libre — trabajo humano experto sobre datos argentinos
(ocupaciones, skills, CLAE, sectores) que hoy está muerto en una tabla. F0.6 probó que
no vuelve al sistema (**(b)=0**, loop roto). Este discovery lo lee para entenderlo.

## Reencuadre que rige el spec

**"Cerrar el loop" NO es "convertir cada corrección en una regla."** F0.6 mostró que las
reglas son la mayor fuente de error (80% del universo amplio); fabricar una regla por
corrección **empeoraría** el problema. Las correcciones vuelven por **vías distintas según
su tipo** (vocabulario/perfil, training pairs, reducir reglas, CLAE…), y para eso primero
hay que saber qué tipos existen. **Las categorías deben salir de leer a Cyn, no imponerse
antes** — y el matiz argentino ("está mal la ocupación" vs "está mal porque acá se llama
distinto") es justo lo que una agrupación automática puede aplanar. Por eso esta Fase 1
**propone** grupos tentativos; **Gerardo/Cyn validan** las categorías finales.

## Naturaleza: read-only absoluto

Lee y ordena texto, propone grupos, prepara (en Fase 2) el split. **No cierra el loop, no
genera reglas/vocabulario/training, no toca código/datos/config.** Lo único que escribe es
documentación (este spec) y artefactos de análisis fechados, vía branch + PR que mergea
Gerardo.

## Insumos y corpus extraído

| fuente | qué aporta | fragmentos |
|---|---|---:|
| `exports/cyn_backlog/ledger_correcciones_cyn.jsonl` → `cyn_texto_original.descripcion` | texto libre **issue-level** (lo más granular) | **811** |
| Supabase `ofertas_dashboard.validacion_correcciones.nota` (ofertas **no** en el ledger) | delta per-oferta consolidado | **7** |
| Supabase `validacion_correcciones` (`issues` = misma fuente del ledger) | redundante con el ledger; no se re-cuenta | — |

- **Corpus total: 818 fragmentos literales de Cyn · 309 ofertas únicas.**
- La nota de Supabase es la **consolidación per-oferta** (272 notas, largo medio ~2.900
  caracteres); el ledger es la versión **issue-level** (811, multi-issue por oferta). Mismo
  género de texto. Se toma el ledger como maestro y se suman solo las 7 notas de las ofertas
  que el ledger no cubre (delta F0.6).
- Artefacto con cada fragmento literal + sus marcadores:
  `tests/harness/lenguaje_cyn_extraccion_2026-06-18.json`.

## Hallazgo de forma (antes de los grupos)

Cyn **no escribe una corrección por dimensión** — escribe **revisiones estructuradas
multi-dimensionales**: una misma nota suele tocar ocupación + sector + skills + tareas +
target ESCO + denominación argentina, a la vez. Por eso los grupos de abajo **NO son
exclusivos**: los conteos son **presencia del marcador**, no una partición (suman más que
818). Esto ya es información para el cierre del loop: una nota alimenta varias vías a la vez.

La nota tiene además un **vocabulario de marcado propio y consistente** que Cyn reusa:
`❌ Incorrecto` / `✔ Explícita correcta` / `⚠ Implícita` / `ATRIBUTOS DEL AVISO` /
`DENOMINACION — Argentina: … / España (equivalente funcional): …` / `ISCO actual:` /
`Ubicación sugerida dentro del Excel: ESCO XXXX`. Es casi un esquema semi-formal — explotable.

## Grupos tentativos (PARA VALIDAR — no son las categorías finales)

> Etiqueta tentativa · marcador típico · conteo de presencia (no exclusivo) · ejemplos **literales**.

### G1 — Corrige la ocupación (dice que la ocupación asignada está mal) · ~241 + ~47 en prosa libre
Marca que la ocupación/ISCO asignado no corresponde. A veces con `❌`, a veces en prosa
("No corresponde clasificar como…", "El puesto es … no …").
- *"No corresponde clasificar este aviso como tornero/tornera, porque el aviso no menciona tareas de torneado… El aviso habla de otra cosa: ensamble de piezas en línea de producción de pistolas…"* (7879857202)
- *"El puesto es administrativo-corporativo y no realiza actividades agrícolas ni rurales. Corresponde a Recursos Humanos / Administración y gestión empresarial"* (1118133545)
- *"La ocupación 'Martillero/a Público/a' corresponde a un profesional matriculado dedicado a la intermediación, venta y alquiler de bienes inmuebles… sin vinculación con actividades de defensa o fuerzas armadas."* (2174645)

### G2 — Da el target ESCO/ISCO correcto · ~235
El código de destino que Cyn propone (lo que F0.6 recuperó del texto libre). Suele venir
anidado en G1/G3.
- *"ISCO correcto: C2519 — ESCO corregido: probador de software/probadora de software"* (1117985442)
- *"ESCO: 4311.1 - empleado de contabilidad/empleada de contabilidad"* (1118032342)
- *"Ubicación sugerida dentro del Excel: 3123.1.24 supervisor de obras de instalación de suelos / 3123 Supervisores de la construcción"* (2180269)
- *"Código ESCO: 7223.5"* (7937139991, delta Supabase)

### G3 — Denominación argentina ↔ España/ESCO (el matiz local) · ~240
**El activo de vocabulario.** Cyn escribe un bloque bilingüe explícito: el nombre argentino,
el equivalente funcional español/ESCO, y el código. No es "está mal" sino "acá se llama así".
- *"DENOMINACION — Argentina: advisor de soporte a usuarios / agente de soporte de app / soporte operativo a usuarios. España / ESCO: agente del servicio de asistencia de TIC"* (1117985442)
- *"Argentina: Capataz de Obra (especialidad hormigón) / Oficial especializado en hormigón. España (equivalente funcional): Encargado de Obra (especialidad hormigón)."* (1118050314)
- *"Argentina: Supervisor eléctrico / Encargado eléctrico / Capataz eléctrico. España (equivalente funcional): Encargado de instalaciones eléctricas / Supervisor de obra eléctrica."* (1118041226)
- *"Argentina: Gestor de operaciones / Administrativo contable / Analista operativo. España (equivalente funcional): Administrativo / Técnico administrativo"* (1118032342)

### G4 — Corrige atributos del aviso (sector / área / experiencia / modalidad / localidad) · ~232
Errores de metadatos NLP, no de ocupación. Bloque `ATRIBUTOS DEL AVISO`.
- *"ATRIBUTOS DEL AVISO INCORRECTO: Sector: ❌ Incorrecto. El sistema marcó Otro, pero el aviso informa que el cliente pertenece al sector Retail de Moda."* (1117999916)
- *"Área: ❌ Incorrecto. El sistema marcó Marketing, pero… Corresponde a Producción / Operaciones, porque se trata de un puesto operativo de producción."* (1118014258)
- *"Experiencia: ❌ Incorrecto. El sistema indicó 0 años, pero el aviso pide experiencia demostrable en edición de videos."* (1117994728)
- *"Provincia / Localidad: El aviso menciona Kavak TOM / Kavak DOT, no 'El Pato'."* (1117983846)

### G5 — Skills: marca ruido / alucinación · ~131
Lista skills que el sistema puso pero "provienen de otros dominios ocupacionales". Señal
negativa pura.
- *"Skills incorrectas (ruido NLP): montar un arma de fuego / coordinar eventos / supervisar procedimientos de facturación / supervisar la administración de préstamos. Estas provienen de otros dominios ocupacionales."* (1117983846)
- *"SKILLS incorrectas que NO corresponden al puesto que se busca: supervisar planificación del espacio aéreo / gestionar consultas de usuarios de bibliotecas / preparar informes meteorológicos"* (1117955657)
- *"Skills incorrectas: transportar materiales de construcción / seguir normas y reglamentos aeroportuarios / practicar movimientos de danza / gráficos en movimiento"* (1118019188)

### G6 — Skills: sugiere faltantes / valida pertinentes (con trazabilidad a la tarea) · ~324
La señal positiva más voluminosa: skills faltantes alineadas a ESCO, y validación
skill↔tarea de origen marcada `✔ Explícita` / `⚠ Implícita`.
- *"Skills nuevas sugeridas (alineadas a ESCO): gestionar cartera de clientes / realizar visitas comerciales / promocionar productos de consumo masivo / negociar condiciones comerciales con clientes"* (1118138730)
- *"Skills faltantes: monitorización de infraestructura IT / administración de data center / instalación de equipos informáticos / gestión de ciberseguridad"* (1117978310)
- *"Skill: gestionar proyectos. Tarea de origen: asumir la responsabilidad del alcance, progreso, coste, calidad y resultados. Validación: ✔ Explícita correcta. Justificación: Es la skill central del aviso."* (1117925089)

### G7 — Tareas: faltantes / mal extraídas / no extraídas · ~90
- *"TAREAS INCORRECTAS: Competencias técnicas valoradas → ❌ Incorrecta. Es un encabezado, no una tarea. Experiencia operando maquinaria industrial → ❌ Incorrecta. Es experiencia requerida/valorada, no tarea."* (9255109063)
- *"El sistema LLM no extrajo tareas ni skills para este aviso… Describe un programa de pasantía… con finalidad formativa."* (1118201193)
- *"EL SISTEMA NO EXTRAJO NI SKILLS NI TAREAS: Tarea sugerida desde el aviso: Atender pacientes en consultorio de traumatología."* (8340966205)

### G8 — Título agrupa múltiples ocupaciones (desagregar en subofertas) · ~4
- *"El titulo agrupa varias ocupaciones bajo un mismo encabezado como si fuera una sola. No puede codificarse como una única ocupación… Se requiere su desagregación en subofertas independientes para su correcta codificación."* (1118161376_2)

### G9 — Confirma que está correcto (total o parcial) · conteo ruidoso (~243 con marcador, ver nota)
No es un error: Cyn valida que la clasificación/atributos están bien. **Señal de oro
(positivos).** Ojo: el conteo se infla porque "✔ … correcta" de las validaciones de skill
(G6) también dispara el marcador; el grupo "puro" (categoría `ocupacion_confirmada` /
`confirmacion_parcial` en el ledger) es **43**.
- *"CLASIFICACION ACTUAL CORRECTA: ISCO 8322 — Oferta: Chofer de reparto"* (9209739433)
- *"ATRIBUTOS DEL AVISO CORRECTOS."* (1118009744)
- *"Clasificación actual: 7131 - pintor de obra/pintora de obra. Validación: ✔ Correcta… el puesto es Oficial Pintor y las tareas se centran en pintura de pisos industriales…"* (2180463_4, delta)

### AMB — Ambiguos / incertidumbre / sin texto · pocos
No fuerzan grupo; se reportan aparte.
- *"Revisar clasificacion, no estoy seguro"* (2164348) — **marcador de incertidumbre del propio humano**, dato para el Eje 2.
- 3 ofertas delta de Supabase **sin nota** (corrección estructurada pero texto vacío).
- ~47 fragmentos no matchean ningún marcador: en su gran mayoría son **G1 en prosa libre**
  (corrección de ocupación sin el símbolo `❌`), no un grupo nuevo.

## Nota metodológica (límites de la Fase 1)

1. **Grupos no exclusivos.** Los conteos son presencia de marcador sobre 818 fragmentos;
   suman más que el total porque una nota toca varias dimensiones. No tomar como partición.
2. **G9 sobre-cuenta** por la colisión "✔ correcta" de skills; el confirmado puro es 43.
3. **El marcador es triage, no verdad.** ~47 sin-grupo son correcciones de ocupación en
   prosa. La agrupación fina (y el matiz argentino) la debe **validar Cyn/Gerardo** — es el
   punto de la Fase 1.
4. La separación G1 (ocupación mal) vs G3 (mal porque el nombre argentino difiere) es **la
   distinción de mayor valor para el Eje 3** y la más sujeta a criterio humano: muchas notas
   tienen las dos. Es la primera pregunta a llevar a la validación.

## PUNTO DE CONTROL — esperando validación

Estos grupos tentativos van a Gerardo/Cyn para **validar, ajustar, fusionar o separar** las
categorías. **No se corre la Fase 2** (clasificar las 309 completas + mapeo categoría→vía +
train/test split) hasta que las categorías estén confirmadas.

## Artefactos (Fase 1)

```
docs/specs/SPEC_S1C_F07_LENGUAJE_CYN.md                  este spec
tests/harness/lenguaje_cyn_extraccion_2026-06-18.json    818 fragmentos literales + marcadores + conteos
```

---

# FASE 2 — Clasificación con las categorías validadas por Cyn (2026-06-18)

## Categorías validadas (las finales)

Los 9 grupos de Fase 1 quedan confirmados. Ajustes de la validación de Cyn:

- **G1 (ocupación) y G3 (denominación argentina) SEPARADOS** (decisión de Gerardo) — G3 es
  el activo de vocabulario (Eje 3), no se fusiona para no perder la señal. Una nota puede
  tener ambos.
- **G2 (target ESCO/ISCO)**: atributo presente en G1/G3 (el código destino), no categoría
  autónoma. La clasificación lo confirma: de 200 ofertas con target, solo **14 son puras** de
  G2; el resto va anidado.
- **G4/G5/G6/G7 SEPARADOS por campo** pero etiquetados todos como **"corrección de lectura
  del aviso (NLP)"** — comparten que alimentan la lectura de avisos, vuelven por mecanismos
  distintos.
- **G7 partido en dos** (refinamiento de Cyn): **G7a** tareas no extraídas · **G7b** tareas
  presentes pero mal normalizadas (encabezados/requisitos tomados como tarea, o listas de
  actividades sin verbo). G7b lleva la regla textual de Cyn: *transformar actividades en
  tareas con verbo SIN inventar contenido nuevo* (conecta con la deuda de S1.B.5).
- **G8 (multi-ocupación)**: caso real; vía especial = desagregar en subofertas, NO
  reclasificar a una sola.
- **G9 (confirma correcto)**: señal de oro (positivos).
- **AMB (dudas)**: además de categoría, es **pedido de funcionalidad** — un estado "pendiente
  de revisión" que hoy no existe (insumo del Eje 2).

## Clasificación de las 309 ofertas (presencia, NO exclusiva)

| categoría | ofertas | vía de vuelta | Eje |
|---|---:|---|---|
| **G3** denominación argentina | **229** | perfil argentino / vocabulario (el activo) | 3 |
| **G6** skills faltantes/validadas | 237 | registro de emergentes / perfil | 3 |
| **G4** atributos del aviso | 225 | corrección NLP (prompt/catálogo sector…) | 3/NLP |
| **G2** target ESCO/ISCO | 200 | dato de apoyo del training pair | 2 |
| **G1** ocupación mal | 161 | training pair; si expone bug de regla → corregir regla | 2/4 |
| **G5** skills ruido | 122 | señal negativa para el extractor | 3/NLP |
| **G9** confirma correcto | 49 | positivos para el harness (ground truth) | medición |
| **G7a** tareas no extraídas | 20 | corrección NLP (extracción) | 3/NLP |
| **G7b** tareas sin verbo / mal normalizadas | 14 | normalización lista→tarea con verbo, sin inventar | 3/NLP |
| **G8** multi-ocupación | 3 | marcar para desagregar en subofertas | 2 (proceso) |
| **AMB** dudas | 4 | estado "pendiente de revisión" para Cyn | 2 |
| *(sin categoría)* | 5 | — (texto truncado / nota vacía) | — |

Suma > 309: **no exclusivas.** El mapeo categoría→vía se confirma tal cual el del prompt;
el único matiz que la clasificación agrega es que **G2 casi nunca es autónomo** (es atributo).

## El activo es mayormente multi-dimensional

| | ofertas |
|---|---:|
| **multi-categoría (≥2)** | **267** |
| puras (1 sola) | 37 |
| sin categoría | 5 |

Distribución de nº de categorías por oferta: la moda es **6** (76 ofertas). **Una corrección
de Cyn alimenta varias vías a la vez** — esto manda en el diseño del cierre del loop: no se
puede rutear "una corrección → un mecanismo".

## Dimensión del activo por tipo (ofertas con presencia)

| bloque | ofertas | % de 309 |
|---|---:|---:|
| **Lectura del aviso / NLP** (G4+G5+G6+G7) | **259** | 84% |
| └ skills (G5+G6) | 239 | 77% |
| └ atributos (G4) | 225 | 73% |
| └ tareas (G7a+G7b) | 34 | 11% |
| **Vocabulario argentino** (G3) | **229** | 74% |
| **Ocupación** (G1) | 161 | 52% |
| **Confirmaciones** (G9, ground truth) | 49 | 16% |
| **Multi-ocupación** (G8) | 3 | 1% |
| **Dudas** (AMB) | 4 | 1% |

Lectura-de-aviso (84%) y vocabulario argentino (74%) son los dos frentes más grandes — ambos
del **Eje 3/NLP**, no de las reglas. Coherente con el reencuadre: el grueso del activo **no**
vuelve como regla.

## Train/test split (fijado y fechado — NO se usa acá)

- **Criterio:** aleatorio **estratificado por categoría primaria** (prioridad: categorías
  raras/valiosas primero), `seed=42`, **test = 30%**.
- **TRAIN = 216 ofertas** (alimenta el loop) · **TEST = 93 ofertas** (reservado, **nunca**
  usado para generar nada — mide si el loop funcionó).
- **Balance verificado por presencia no-exclusiva** (lo que importa): cada categoría sustancial
  queda **27–32%** en test (G1 27%, G2 31%, G3 30%, G4 32%, G5 30%, G6 30%, G9 27%). Las
  categorías chicas (G7a/G7b/G8/AMB, N<20) quedan ruidosas (35–43%) por tamaño, inevitable.
- **Regla de oro:** si los dos conjuntos se mezclan una vez, la medición posterior queda
  contaminada y no se limpia. El split va **desde el día uno**; se documenta y commitea, **no
  se usa** (el loop no se cierra en este spec).

## Nota de método (Fase 2)

La clasificación es **marcador-triage**, igual que Fase 1: ~5 ofertas sin marcador (prosa /
texto truncado), y G7a/G7b se separan por marcador con margen (la palabra "normalización" la
usa Cyn también para ocupación, no solo tareas — se acotó G7b a señales de tarea). Los números
de las categorías chicas (G7, G8, AMB) son indicativos, no exactos.

## Artefactos (Fase 2)

```
tests/harness/lenguaje_cyn_clasificacion_2026-06-18.json   309 ofertas × 11 categorías + pureza + dimensión
tests/harness/lenguaje_cyn_split_2026-06-18.json           train(216)/test(93) estratificado, seed=42
```
