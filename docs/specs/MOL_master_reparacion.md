# MOL — Master S1.C: Reparación de la fábrica

> Versión 0.2 · 2026-06-12
> Documento operativo de la fase de reparación. Cruza las ~80 deudas observadas en los 7 specs de relevamiento (S1.B.1–S1.B.7), las organiza en ejes transversales, define el norte contra el cual se prioriza, y establece la lógica de secuencia. Es el primer documento del proyecto que prioriza con el cuadro completo a la vista.
> Antecedentes: `MOL_master_relevamiento.md` v0.2 (la fase que produjo el insumo), los 7 specs `SPEC_S1B*.md`, el modelo conceptual v1.0 (mayo 2026), los diagnósticos de mayo y el índice de investigaciones del harness.
> *Cambios desde v0.1:* integradas las 7 observaciones de la primera revisión del hilo del harness (corrección de la premisa refutada del Eje 3 — Cadena 8, experimento puente anclado en Fase 0 como primer consumidor del harness, SPEC S0 v0.2 referenciado como insumo, dos actas de decisión, criterio C8 de cobertura, los informes como tercer consumidor, y la sección de operación durante la reparación con el corte t1 como baseline) y las correcciones de la segunda ronda (2026-06-12): precisión numérica del acta de terminologia, verificación CLAE previa al backlog, y punto de partida completo de C4, y principio de método nº7 (residencia de datos) incorporado el 2026-06-12 tras verificación de las violaciones en ambas direcciones, y ajuste de §4.1 con el veredicto de V6 (la caída CLAE es regresión de 2026-03, no backlog pre-clasificador) el 2026-06-12.

---

## 1. El norte: la fábrica de alto nivel

### 1.1 La visión

MOL es **la fábrica**: el sistema que toma ofertas crudas del mercado laboral argentino y produce datos estructurados de calidad — ocupación granular, skills, tareas, atributos. Sus consumidores son tres: **OE** y las **aplicaciones comerciales** (los locales: consumen lo que la fábrica produce, no fabrican) y la **línea de informes** (el go-to-market: reporte sectorial gratuito → credibilidad → ventas a cámaras, universidades, gobierno). La inspiración es la familia Lightcast/Revelio: sistemas cuyo negocio es la fábrica y cuyo activo defendible es **la taxonomía propia que se acumula con cada oferta procesada**.

La tesis, que el modelo conceptual de mayo ya formuló: el estándar externo (ESCO) es capa de interoperabilidad, no dueño del dato. Lo que la fábrica acumula —emergentes capturadas, perfil argentino con evidencia multi-empresa, vocabulario que respira con el mercado— es lo que ningún competidor global tiene para Argentina y lo que ningún cliente local puede construir por su cuenta. **La ventaja es la inversa de la desventaja de escala**: a Lightcast no le rinde curar Argentina; a MOL sí.

De la visión se derivan las cinco propiedades de la fábrica de alto nivel:

1. **Corre sola.** El procesamiento es periódico y automatizado; el humano supervisa y atiende excepciones, no dispara corridas.
2. **Se observa.** Todo fallo notifica; todo estado es consultable; ninguna inconsistencia es silenciosa.
3. **Acumula el activo.** Cada oferta engorda el vocabulario argentino: las emergentes se capturan, el perfil argentino participa de las decisiones, nada que el mercado dice se pierde.
4. **El control de calidad humano está en la línea.** La curaduría de Cyn ocurre durante el procesamiento y vuelve al sistema — como Lightcast tiene taxonomistas, MOL tiene su validadora integrada al flujo, no corrigiendo a posteriori en un buffer que nadie drena.
5. **Las herramientas son intercambiables.** La fábrica sobrevive a sus modelos: cambiar de LLM o de embeddings es configuración más harness, no reescritura.

### 1.2 Los criterios de éxito (medibles, no retóricos)

La fase de reparación se declara exitosa cuando estos ocho enunciados son verdaderos y verificables:

| # | Criterio | Medida hoy | Medida objetivo |
|---|---|---|---|
| C1 | La fábrica procesa sin intervención humana | Latencia scraping→NLP: 6,6 días (tramo manual) | < 24 h de punta a punta, cero disparos manuales en operación normal |
| C2 | Ningún fallo es silencioso | Sync, scrapers y validadores fallan sin alerta | Todo fallo notifica por un canal real; "hoy no me entero" imposible |
| C3 | El loop de Cyn está cerrado | Corrección → issue → buffer muerto; la oferta "se ve igual" | La corrección es visible en la oferta, reutilizable, y vuelve al sistema (regla/training/re-encolado) |
| C4 | El vocabulario argentino crece | 431 emergentes pendientes, 0 aprobadas; cementerio de 7.564 sin drenar; 56.302 URIs fabricadas en el corpus; perfil AR sin peso en la decisión | Ciclo activo: captura → revisión → promoción mensual; perfil AR participa de la decisión de ocupación |
| C5 | Cambiar de modelo es posible | 5 puntos de acoplamiento a Qwen2.5; la migración que se intentó, fracasó | Probar un modelo nuevo = configuración + corrida de harness comparativa. El test final: la migración que detonó todo, ejecutada |
| C6 | El costo es predecible | Factura Supabase sorpresa, 3 causas candidatas sin confirmar | Desglose conocido, costo estable mes a mes |
| C7 | Lo que se construye queda vivo | D-15 en 7/7 componentes, 5 variantes, ~30 instancias | Cero instancias nuevas: definición de terminado aplicada a todo lo que se repare |
| C8 | El corpus procesado es el corpus scrapeado | ~84% (≈13.000 ofertas nunca entraron al procesamiento) | ~100%, con las exclusiones detectadas y justificadas. La cobertura es la métrica nº1 del consumidor de informes: una fábrica rápida sobre el 84% del mercado no es de alto nivel |

> *Nota a C8 (V6/F0.1):* la caída de cobertura CLAE desde 2026-03 es una **regresión a diagnosticar**, no solo exclusión de las 13K — afecta la medición de C8 (ver §4.1).

C5 es el criterio de cierre simbólico y real de toda la fase: la frase fundante fue "quisimos pasar a otro modelo y nos dimos cuenta que no se puede".

## 2. Principios de método (heredados y vigentes)

1. **No disruptividad.** La fábrica está en producción continua sirviendo datos. Toda reparación es incremental y live-safe; no hay "parar todo y rediseñar".
2. **El harness antes que el cambio.** Toda modificación al cerebro (NLP, matching, skills) se valida en aislamiento contra ground truth antes de promoverse. El harness deja de ser práctica ad-hoc y se vuelve infraestructura.
3. **Verificación previa antes de planificar.** El repo es la fuente de verdad; los specs de reparación arrancan verificando el estado actual, no asumiéndolo (los relevamientos tienen fecha; el sistema sigue vivo).
4. **Conectar antes que construir.** El hallazgo repetido de los 7 specs: el sistema está más construido y menos conectado de lo que se creía. La intervención preferida es siempre el cable, no la pieza nueva. Aplica también a los specs: lo ya diseñado y verificado se reutiliza, no se rediseña.
5. **Un spec es operativo o no es spec.** Tests ejecutables, criterios binarios de aceptación, comandos exactos.
6. **Branch + PR + merge de Gerardo.** CONVENTIONS.md sin excepciones.
7. **Residencia de datos.** El procesamiento lee y escribe en la BD local; Supabase presenta y captura interacción humana. Todo dato humano capturado en Supabase tiene bajada automática a local, que es la fuente de verdad del procesamiento; ninguna decisión del pipeline depende de leer Supabase en runtime. *Estado actual: el principio se viola en ambas direcciones.* **Bajada rota**: el dato humano queda varado arriba — el Gold Set ampliado vive en la tabla `gold_set` de Supabase mientras la regresión local mide contra el JSON de 49; lo mismo validaciones, emergentes y `approved_training_pairs` (es la mitad rota del loop, Eje 2, vista desde la arquitectura). **Subida indebida**: el núcleo lee Supabase en runtime para decidir en al menos tres puntos — `config_loader.py:316-339` (`config_overrides`: reglas de negocio y diccionario argentino que "ganan siempre"), `match_ofertas_v3.py:2094-2101` (RPC `get_latest_equiv_update`), `skills_implicit_extractor.py:1102+` (equivalencias y boost vía service_role). La dependencia "override Supabase → fallback local" se invierte: la UI escribe → baja a local → el pipeline lee local. La residencia es además **precondición de C5**: el harness corre en aislamiento solo si el pipeline no estira la mano a la red. Las violaciones se censan en V7 del SPEC S1C-F0.1; la bajada se repara en el Eje 2 y el corte de lecturas runtime en los Ejes 4/5.

## 3. Los seis ejes transversales

Las ~80 deudas de los 7 specs no se reparan componente por componente — se reparan por eje, porque las cadenas rotas atraviesan componentes. Cada eje agrupa deudas (referenciadas por spec y número, sin repetir contenido), nombra el cable que falta y fija su criterio de éxito.

### Eje 1 — La fábrica corre sola
*Alimenta C1, C2, C6, C8.*

**El cuadro**: los extremos ya están automatizados (auto_sync por hora, poller por minuto); solo el núcleo NLP+matching es on-demand, y ese único eslabón manual cuesta 6,6 días de latencia contra 1 día del resto. Los bloqueos para automatizarlo están inventariados (S1.B.6 5.2.4). Y la cola es parcial: ~13.000 ofertas nunca entraron (C8).

**Deudas que agrupa**: S1.B.6 D-01 (núcleo on-demand), D-02 (selección: 4 mecanismos + 8 estados), D-03 (sin acta de corrida), D-04 (cola parcial), D-09 (Ollama sin verificación), D-10 (paso bloqueante manual); S1.B.1 D-04 (sync sin observabilidad), D-01/D-02/D-03 (costo Supabase: N+1, RPCs, pollers); S1.B.2 D-01 (cambios de HTML sin detección), D-02 (alert_manager solo-logs), D-09 (cobertura solo Bumeran).

**El cable**: un criterio único de elegibilidad + acta de corrida + verificaciones previas + canal de alertas real → cron del núcleo. La observabilidad no es un proyecto aparte: es la condición de la automatización. La reincorporación de las 13K excluidas (C8) entra con el criterio único de elegibilidad.

**Éxito del eje**: el pipeline corre solo N veces por día; cada corrida deja acta; cada fallo notifica; la latencia de punta a punta baja de días a horas; el corpus procesado converge al scrapeado.

### Eje 2 — El loop humano cerrado
*Alimenta C3. La pieza central de la visión human-in-the-loop de Gerardo.*

**El cuadro**: el loop se rompe siempre en la segunda mitad. La corrección de Cyn se guarda (en dos lados) y no se muestra en ninguno; se convierte en training pair y nada lo consume; el gate marca 278K veces y bloquea 70. Y la infraestructura para cerrarlo existe más de lo que se creía: configurabilidad en JSON, audit-history que se consulta y no se pinta, estados de SPEC W persistidos sin UI.

**Deudas que agrupa**: S1.B.3 D-04 (loop roto), D-06 (73% reglas sin revisar), D-09 (herramientas de Cyn); S1.B.4 D-02 (regla_cynthia 0 filas), D-11 (dos almacenes de training pairs sin consumidor); S1.B.6 D-05 (validar sin consecuencias), D-07 (configurabilidad sin exposición), D-08 (re-encolado humano inexistente); S1.B.7 D-03 (auto-avance), D-04 (corrección invisible), D-05 (historial a un componente de distancia), D-10 (trazabilidad e historial = la misma pieza).

**El cable**: la vista de trazabilidad por oferta (cierra los pedidos nº1 de Gerardo y de Cyn de un golpe) + el flujo de validación rediseñado (sin auto-avance, con historial, con edición de skills) + el re-encolado con corrección + consecuencias por severidad.

**Éxito del eje**: Cyn ve lo que corrigió; el sistema no repite el error corregido (medible contra casos trazados); el trabajo humano validado nunca se pierde.

### Eje 3 — El vocabulario argentino como activo
*Alimenta C4. La tesis Lightcast: el moat.*

**El cuadro**: la materia prima ya se acumula y se desperdicia. El cementerio tiene 7.564 fallas estructuradas sin drenar (más una segunda fosa anónima del ~25%); hay 431 emergentes pendientes con la cadena de aprobación cableada a buffers muertos; el perfil argentino captura la divergencia AR↔EU (que es la condición del 90%+ del corpus, con 3.292 pares multi-empresa de evidencia) pero hoy no participa de la decisión de ocupación; los campos del NLP destruyen señal (sector → "Otro", listas sin verbo sin normalizar).

**Corrección de premisa (revisión del harness, Cadena 8)**: el modelo conceptual estimaba la conexión del perfil argentino a la decisión como "~60% hecha". La verificación lo refutó: el matcher de producción no invoca el camino skills→ocupación (`match_occupations_by_skills`); el RPC con el flag existe pero está desconectado del camino real. **Es refactor de `match_ofertas_v3.py`, no activación.** Sigue siendo la intervención de mayor retorno del catálogo; el esfuerzo es mayor al que la estimación heredada sugería — por eso el experimento puente (Fase 0) calibra con número antes de comprometer el refactor.

**Deudas que agrupa**: S1.B.4 D-03 (cementerio sin reuso), D-04 (filtro L2 poda señal AR), D-05 (emergentes a buffers muertos), A-3 (segunda fosa), A-4 (cuantificación de la divergencia); S1.B.5 D-04/D-05 (sector colapsado y sus marcas sin consumidor), D-07 (listas sin verbo); el Sprint 0 y el Sprint 1 del modelo conceptual.

**Nota comercial**: el campo sector no es solo señal destruida — es la **dimensión de corte de la mitad del catálogo de informes** (reportes sectoriales para cámaras). Su reparación tiene retorno comercial directo; dato para la priorización interna del eje.

**El cable**: registro de emergentes con identidad propia (drenando el cementerio e instrumentando la segunda fosa) + perfil argentino conectado a la decisión de ocupación + ciclo de promoción con validación de Cyn (que es el Eje 2 aplicado al vocabulario). **Insumo existente**: el SPEC S0 v0.2 (captura de emergentes sobre M-06) ya está diseñado y verificado contra el código (factibilidad 2026-06-10, ajustes a v0.3 identificados) — entra como punto de partida, no se rediseña de cero.

**Acta de decisión (cierra la "Prioridad 2" pendiente de mayo)**: el diccionario `terminologia` **no se amplía**. El mecanismo de URIs fabricadas se retira o se reconvierte a entradas con URI ESCO real (56.302 filas con URI fabricada detectadas en total: ~29,7K inyectadas por `terminologia`, ~26,5K por `derived`/`declared`, 51 por regla); la captura de tech stack moderno pasa por el registro de emergentes con identidad propia, no por fabricar URIs.

**Éxito del eje**: emergentes promovidas participando del matching; el perfil argentino pesa en la decisión y se mide su efecto en el harness; el conteo del vocabulario propio crece mes a mes.

### Eje 4 — Modelos intercambiables
*Alimenta C5. El criterio de cierre de toda la fase.*

**El cuadro**: el inventario de acoplamiento está hecho (5 puntos, S1.B.5). La tarea habilitante está identificada: clasificar las ~357 reglas del matcher entre dominio genuino (60-100) y parches de Qwen2.5 (180-220) — "mientras esa clasificación no se haga, no se puede migrar". Y la evaluación comparativa necesita lo que hoy no existe: un gold set canónico cuya precisión se mida de verdad (la del ampliado de 112 nunca se midió) y un harness formalizado.

**Deudas que agrupa**: S1.B.5 D-01 (acoplamiento), D-02 (downgrade sin versionar), D-03 (prompt hardcodeado); S1.B.3 D-02/D-03 (gold sets fragmentados, el ampliado sin función de regresión), D-05 (LoRA perdido — la política de respaldo de artefactos); S1.B.4 D-06/D-07/D-08 (embeddings sin release ESCO, sin repo centralizado de vectores, multi-época), A-2 (URIs huérfanas: embeddings vs catálogo de runtime).

**El cable**: capa de abstracción de modelos (nombre/params/parsing/prompt en config, versionado de qué modelo procesó qué) + gold set canónico único con precisión recomputada + harness como infraestructura + repo centralizado de vectores ESCO con release estampada + clasificación de reglas.

**Acta de decisión (anti-circularidad del fine-tuning)**: cualquier fine-tuning futuro **no entrena con menciones de score ≥0.70 generadas por el propio modelo base** (circularidad). Los positivos válidos son pares validados por humanos + pares B_FUERTE con respaldo multi-empresa. Esta acta supersede cualquier recomendación contraria que haya circulado en documentos de mayo.

**Éxito del eje**: la corrida comparativa Qwen2.5 vs un candidato, ejecutada en el harness, con decisión basada en evidencia. La migración que fracasó, posible.

### Eje 5 — Contratos y datos sanos
*Base de todos los demás. Alimenta C6 y la confiabilidad comercial.*

**El cuadro**: datos que se producen y se pierden en el camino (el esco_code de 350 reglas), columnas zombi que la documentación señala como buenas (origen_tipo, match_method), 171 columnas con 150 muertas, timestamps corruptos sin marcar, frontera fábrica/local solo por carpetas, históricos y backups sin política.

**Deudas que agrupa**: S1.B.3 D-01 (esco_code perdido); S1.B.4 D-01 (columnas zombi), A-5 (match_method); S1.B.5 D-10 (171 columnas), D-11 (lag negativo); S1.B.1 D-05...D-10 (históricos, sprawl, migraciones duplicadas, credenciales); S1.B.7 D-02 (frontera fábrica/local), D-01 (90 páginas muertas o mock).

**El cable**: contratos tipados extremo a extremo en los puntos que los ejes 1-4 tocan (no limpieza total por limpieza misma: lo que ningún eje toca, espera), una sola columna de verdad por señal, y la capa de acceso para los consumidores. **El patrón de consumo de informes**: snapshot versionado local (tipo DuckDB, demostrado en el sandbox del harness) — los informes no cargan Supabase (alimenta C6 directo) y cada informe declara contra qué corte y qué versión del pipeline se produjo.

**Éxito del eje**: ningún dato definido se pierde en el camino; la documentación señala columnas vivas; los tres consumidores (OE, apps, informes) consumen por interfaz con trazabilidad de versión.

### Eje 6 — El proceso que mantiene vivo lo construido (D-15)
*Alimenta C7. La causa raíz del "siempre anduvo para el orto".*

**El cuadro**: el patrón apareció en 7/7 componentes con cinco variantes (abandonado tras uso, nunca encendido, declarado completado sin estarlo, documentado sin existir, producido sin pantalla). ~30 instancias. No es deuda técnica: es la ausencia de tres prácticas de proceso.

**El remedio (de proceso, no de código)**:
1. **Definición de terminado**: nada se declara completo sin su consumidor conectado, su test verde y su entrada de documentación. "Construido" no es "terminado"; "terminado" es "alguien lo usa".
2. **Revisión periódica de capacidades latentes**: lo apagado se decide — se enciende o se retira. Un inventario corto, revisado con cadencia fija (puede ser parte del cierre de cada spec de reparación).
3. **El acta de decisión**: toda decisión que cambia el comportamiento del sistema (un downgrade de modelo, un threshold, una regla) deja registro en DECISIONES.md en el momento, no en la arqueología posterior. (Este master ya incluye dos: terminologia en el Eje 3 y anti-circularidad en el Eje 4.)

**Éxito del eje**: cero instancias nuevas de D-15 en todo lo que la fase de reparación produzca. Se audita al cierre de cada spec.

## 4. Lógica de secuencia (fases, no cronograma)

El orden no es por eje completo sino por dependencia y retorno. Tres fases:

**Fase 0 — Cimientos, ventana de verificación y el experimento puente.**
(a) La **ventana única de conexión viva** que quedó agrupada: trazadores en `gold_set`, conteo enriched vs esco_skills, estado real de emergentes en Supabase, facturación de Supabase para confirmar el candidato de costo, y la verificación de seguridad contra el deploy que Gerardo decidió diferir (se verifica, no se repara — para que S1.C decida con datos).
(b) Los **cimientos del Eje 1**: criterio único de elegibilidad, acta de corrida, canal de alertas. Son prerequisito de todo lo automático y del harness.
(c) La **formalización del harness** (Eje 4) — **con consumidor inmediato: su primer entregable es el experimento puente**. Nadie midió todavía qué pasa si las aristas argentinas entran al grafo de decisión; el experimento es read-only, los harnesses de `exp_raiz_skills/` existen como base, y el ground truth está disponible (Gold Set 113 + las 19 validaciones de Cyn + los 3.292 pares B_FUERTE como aristas candidatas). El resultado **calibra el Eje 3 antes de comprometer la Fase 2**: si la inyección mejora fuerte, el refactor del matcher se justifica con número; si mejora débil, se rediseña antes de gastar. Es el principio 2 de este master aplicado a su intervención más cara — y evita que el harness nazca como infraestructura sin consumidor (D-15 en potencia).

**Fase 1 — Los dos motores en paralelo.**
(a) **Automatización del núcleo** (Eje 1 completo): el retorno más inmediato y visible — la latencia cae de días a horas y la fábrica empieza a "correr sola".
(b) **La vista de trazabilidad + flujo de validación de Cyn** (Eje 2, primera mitad): el retorno humano más inmediato — los dos pedidos número uno del proyecto, con los datos ya guardados esperando pantalla.

**Fase 2 — El activo y la libertad.**
(a) **Vocabulario** (Eje 3): captura de emergentes (desde S0 v0.2→v0.3), perfil argentino a la decisión (calibrado por el experimento puente de la Fase 0), ciclo de promoción — sobre el harness ya formalizado.
(b) **Abstracción de modelos + clasificación de reglas + gold set canónico** (Eje 4): culmina en la corrida comparativa — el criterio C5.
(c) El **Eje 5 acompaña transversalmente**: cada spec de reparación sanea los contratos del camino que toca.

El **Eje 6 (D-15) no es una fase: es el reglamento de todas** — la definición de terminado se aplica desde el primer spec de la Fase 0.

### 4.1 Operación durante la reparación

La fábrica **sigue operando con el proceso manual vigente durante toda la reparación** — la reparación no detiene ni espera. En particular: el backlog acumulado se procesa con la versión vigente del pipeline, sin esperar a la automatización de la Fase 1. Ese procesamiento produce el **corte t1**, que es el **baseline de todas las comparaciones del harness** (incluida la corrida comparativa de C5): el backlog no es un estorbo de la reparación — es su grupo de control.

**Verificación previa al procesamiento del backlog — RESUELTA (V6 de la ventana F0.1)**: el diagnóstico CLAE por mes × portal × estado mostró que la cobertura es ~100% en todos los portales hasta 2026-02 y cae desde 2026-03 incluso en Bumeran (100% → 69%) y ZonaJobs (91% → 68%). Esto **descarta la hipótesis de backlog pre-clasificador** (sería al revés: lo viejo sin cobertura, lo nuevo con) y apunta a una **regresión introducida ~2026-03**. (Indeed arrastra un piso propio ~50%, factor de portal independiente.) **Consecuencia para la operación durante la reparación**: soltar el backlog con la versión vigente del pipeline propagaría la regresión a todo lo que se procese. Por lo tanto, "backlog habilitado" pasa a **"habilitado solo si primero se diagnostica y corrige la regresión CLAE de 2026-03, o se acepta conscientemente procesar con ella y reprocesar después"**. El corte t1 (baseline del harness) debe tomarse con esta decisión ya tomada, no antes — de lo contrario el grupo de control nace contaminado. Diagnosticar la regresión de marzo es candidato a spec temprano de la Fase 1 (toca el Eje 5, contratos/datos sanos, y el Eje 1, cobertura C8).

## 5. Lo que se difiere conscientemente

- **Seguridad (S1.B.7 D-08)**: por decisión explícita de Gerardo (2026-06-11), converge acá sin tratamiento de excepción. La Fase 0 incluye su verificación contra el deploy vivo (datos para decidir), no su reparación. Cuando los locales avancen hacia usuarios reales, este ítem sube solo.
- **Limpieza total de sprawl** (páginas mock, .db vacíos, columnas muertas que ningún eje toca, dashboard legacy): se limpia lo que los ejes atraviesan; el resto espera a que un eje lo necesite o a una pasada final de higiene.
- **CLAUDE.md**: se reescribe cuando la Fase 0 esté cerrada, contra el sistema ya relevado y con las primeras reparaciones hechas — para no documentar dos veces.

## 6. Próximos pasos inmediatos

1. Merge de este master al repo (branch + PR).
2. Apertura de la Fase 0: diseño del primer spec de reparación (la ventana de conexión viva + cimientos del Eje 1 + formalización del harness con el experimento puente), con verificación previa del estado del repo.

---

> *Versión 0.2 — incorpora la revisión del hilo del harness (2026-06-11). El norte (sección 1) es la visión de Gerardo formulada contra el relevamiento completo; los criterios C1-C8 son la definición operativa de "fábrica de alto nivel". Si un criterio no convence, se discute acá — todo lo demás se deriva de ellos.*
