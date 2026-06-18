# MOL — Master S1.C: Reparación de la fábrica

> Versión 0.2 · 2026-06-12
> Documento operativo de la fase de reparación. Cruza las ~80 deudas observadas en los 7 specs de relevamiento (S1.B.1–S1.B.7), las organiza en ejes transversales, define el norte contra el cual se prioriza, y establece la lógica de secuencia. Es el primer documento del proyecto que prioriza con el cuadro completo a la vista.
> Antecedentes: `MOL_master_relevamiento.md` v0.2 (la fase que produjo el insumo), los 7 specs `SPEC_S1B*.md`, el modelo conceptual v1.0 (mayo 2026), los diagnósticos de mayo y el índice de investigaciones del harness.
> *Cambios desde v0.1:* integradas las 7 observaciones de la primera revisión del hilo del harness (corrección de la premisa refutada del Eje 3 — Cadena 8, experimento puente anclado en Fase 0 como primer consumidor del harness, SPEC S0 v0.2 referenciado como insumo, dos actas de decisión, criterio C8 de cobertura, los informes como tercer consumidor, y la sección de operación durante la reparación con el corte t1 como baseline) y las correcciones de la segunda ronda (2026-06-12): precisión numérica del acta de terminologia, verificación CLAE previa al backlog, y punto de partida completo de C4, y principio de método nº7 (residencia de datos) incorporado el 2026-06-12 tras verificación de las violaciones en ambas direcciones, y ajuste de §4.1 con el veredicto de V6 (la caída CLAE es regresión de 2026-03, no backlog pre-clasificador) el 2026-06-12, y cierre del diagnóstico CLAE (F0.2): la caída no es regresión sino fin de backfill único; backlog desbloqueado, cobertura → C8; deuda nlp_processed_at NULL registrada (2026-06-12), y sección 7 (estado y secuencia viva de la Fase 0) con el reorden por la decisión de Gerardo del 2026-06-12 (harness antes que mejoras; backlog al final) y los hallazgos de F0.4a anclados a sus consumidores, y hallazgo del experimento puente F0.5-exp (doble desajuste del perfil argentino; hipótesis dirigente Eje 3 bloqueado por Eje 4, a confirmar en el discovery de anatomía del error) el 2026-06-17, y cierre del discovery de anatomía del error F0.6 (loop roto P-14 con (b)=0; hipótesis Eje3-bloqueado-por-Eje4 confirmada en universo amplio, residuo semántico sugerido a medir después; frente recalibrado a matching grueso en familias técnicas; Eje 4 piso 26-95/357; orden de frente de Fase 2) el 2026-06-18.

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

> *Nota a C8 (F0.2):* la cobertura CLAE real del camino vivo es ~42-76% según portal (diagnóstico F0.2: el ~100% histórico estaba inflado por un backfill único, no es una regresión). Subir esa tasa natural — y/o automatizar el backfill con mecanismo que lo sostenga — es trabajo de C8 (ver §4.1).

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

> *Deuda de observabilidad (F0.2):* `nlp_processed_at` está 100% NULL (0/69.794): el pipeline no estampa cuándo procesó cada oferta, lo que impide medir latencia de procesamiento real y obligó a F0.2 a usar fecha de publicación como proxy. Deuda de observabilidad del Eje 1.

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

**Hallazgo del experimento puente (F0.5-exp corrida 1, 2026-06-17) — el doble desajuste**: la primera medición real de inyectar `esco_argentino` al canal semántico dio ganancia neta −4 (empeora). El valor no es el número sino lo que reveló: (1) **por dónde cubre** — solo 4 de 15 errores del Gold Set caen en las 44 ocupaciones del perfil; el perfil está curado por volumen (las ocupaciones de alto tráfico) sobre zonas donde el sistema ya anda bien, no donde se equivoca (confirma a mayor escala el diagnóstico de mayo: dejaba afuera las ingenierías y oficios técnicos donde más falla); (2) **cómo decide el matcher** — de esos 4, ninguno lo decide el canal semántico; los gana una regla de negocio o el diccionario, río arriba (el sistema es 69% rule-driven, baseline F0.5). El boost NO es débil (en 2 de 4 la arista disparó a rank 0, score 0→8.12); no mueve porque el semántico no llega a opinar.

**Consecuencia para el Eje 3**: expandir el perfil "más de lo mismo" (más ocupaciones de alto volumen) no tocará los errores. La expansión debe dirigirse a las ocupaciones-con-error, que son otras. Y el perfil no puede actuar mientras la precedencia regla→semántico le gane río arriba.

**Hipótesis dirigente (a confirmar, NO hecho cerrado)**: *el Eje 3 está bloqueado por el Eje 4* — el vocabulario argentino no tiene dónde actuar mientras las reglas decidan el ~69% de los casos antes de que el canal semántico opine. Si se confirma, el orden de la Fase 2 se invierte: primero ordenar la precedencia de canales (Eje 4), después conectar el vocabulario (Eje 3). Esta hipótesis viene de una sonda de 4 casos; se confirma o se matiza en el **discovery de anatomía del error** (próximo spec: universo completo de correcciones de Cyn × ocupación × canal de decisión), antes de comprometer cualquier refactor.

**Cierre de la hipótesis dirigente — discovery de anatomía del error (F0.6, 2026-06-18)**: medida sobre el universo completo de correcciones de Cyn (312 ofertas consolidadas, ledger 302 + delta Supabase 10), la hipótesis "Eje 3 bloqueado por Eje 4" **se confirma en el universo amplio y se matiza**:

- **Lo que el dato prueba**: en el universo amplio (119 casos incorrecta sin-target verificable), las reglas deciden el **80%** de los errores. Las reglas son el canal de error dominante — la hipótesis se confirma.
- **Lo que el dato sugiere (NO prueba)**: en el subconjunto medible (67 casos con target ISCO extraíble — 1/5 del universo, sesgado a los casos más claros, no muestra aleatoria), el reparto es regla 49% / semántico 41%. Esto *sugiere* un residuo semántico que sobreviviría tras arreglar las reglas, pero NO lo prueba: concluir "los dos canales rotos por igual" sobre 67 casos sesgados sería concluir fuerte sobre muestra chica. El residuo semántico se mide después, re-corriendo el discovery con las reglas ya arregladas — ese número (no el 41% de 67) decide si el semántico necesita trabajo propio.

**P-14 — el loop de Cyn está roto (evidencia dura, Eje 2)**: de los 67 errores medibles, el matcher de hoy sigue errando en **65**; solo 2 se arreglaron (ambos por el semántico, rescatando casos del default `0110`; ninguno por regla). **(b)=0**: ninguna corrección de Cyn volvió como regla que arregle su propio caso. El backlog de correcciones de Cyn no se tradujo en mejoras del procesamiento. Es el loop human-in-the-loop roto no solo en "no se muestra" (F0.1) sino en "no se aplica". Es el hallazgo más grave de la Fase 0 y el más habilitante: sin loop que devuelva, ninguna mejora vuelve al sistema.

**Frente del Eje 3, recalibrado**: el corte por nivel de unidad muestra que **el 75% de los errores son gruesos** (gran grupo ISCO-1 distinto), no afinamiento granular. Esto NO contradice el baseline F0.5 (que dio ISCO-4 91,7% sano sobre el Gold Set) — es población distinta: el Gold Set ya pasó por propagación (casos digeridos), el ledger completo expone la superficie cruda de error. El frente no es "afinar vocabulario fino" sino "corregir matching grueso en familias técnicas/profesionales" (Profesionales+Técnicos 48%, Oficios+Operadores 27% — familias donde el perfil argentino no cubre, confirma a escala la pata 1 del doble desajuste).

**Eje 4 — primer corte de reglas-parche (consumidor: C5 migración)**: piso de **26 reglas con autor Cyn explícito / 95 con algún marcador de origen, sobre 357**. NO se puede confirmar la estimación del master (180-220 parches) desde `_linaje` (cubre solo 27% de las reglas) — el número es un **piso, no la confirmación**. Objetivo puntual identificado: **`R240_operario_produccion` decide 9 de los 67 errores ella sola** (sobre-dispara) — fix directo y medible.

**Dos observaciones de residencia (Eje 2/5, no se resuelven acá)**: (1) 34 ofertas están en el ledger pero no en `validacion_correcciones` de Supabase — desincronización del dato humano (el issue existe pero no se escribió de vuelta al JSONB); (2) 9 de 67 errores cambiaron de canal entre mayo y hoy — el sistema se modificó en el ínterin (siguen errando, por otro canal).

**Datos menores del experimento, registrados**: (a) atractor desproporcionado — `representante comercial` (3322, 42 skills) se "come" casos por peso plano → candidato a peso escalado por frecuencia, no plano; (b) caso no-determinista en el desempate semántico (1117969136: 3 corridas, 3 respuestas distintas, todas 0.6) → deuda del tiebreaker, ajena al overlay, registrada en el Eje 4/5.

**Corrida 2 (3.292 pares B_FUERTE) — despriorizada**: a la luz del doble desajuste, inyectar más aristas al mismo canal semántico chocaría contra el mismo muro de precedencia. Queda pendiente del export del harness, pero detrás del discovery de anatomía del error, que define si el cuello es la precedencia (Eje 4) o la cobertura del perfil (Eje 3).

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

**Verificación previa al procesamiento del backlog — RESUELTA (V6 de F0.1 + diagnóstico F0.2)**: la caída de cobertura CLAE desde 2026-03 **no es una regresión**. El diagnóstico F0.2 confirmó en tres patas que es el fin del efecto de un backfill único: (1) estabilidad — post-marzo cada portal se asienta en un plateau plano (Bumeran ~69%, ZonaJobs ~68%, ComputRabajo ~66%, Indeed ~42%, PortalEmpleo ~76%), no sigue degradando como haría una regresión; (2) aislamiento — la caída está solo en CLAE; provincia, localidad, seniority, área y modalidad se mantienen o mejoran; (3) alcance — 13.021 ofertas post-marzo sin CLAE (99% de todos los CLAE-null), con el corpus histórico íntegramente cubierto. El ~100% histórico estaba inflado por un pase de backfill (`populate_clae_seccion.py`/`reprocesar_clae.py`) corrido una vez y nunca repetido ni automatizado (instancia de D-15). **Consecuencia para la operación durante la reparación**: el backlog se suelta ya — la cobertura baja es la tasa real del camino vivo, no un bug. El corte t1 (baseline del harness) se toma con esa tasa real como baseline honesto. Subir la cobertura CLAE pasa a ser objetivo de C8, no precondición del backlog. (La fecha exacta de corrida del backfill no está en logs locales; queda como dato menor verificable en una ventana viva, sin bloquear nada.)

## 5. Lo que se difiere conscientemente

- **Seguridad (S1.B.7 D-08)**: por decisión explícita de Gerardo (2026-06-11), converge acá sin tratamiento de excepción. La Fase 0 incluye su verificación contra el deploy vivo (datos para decidir), no su reparación. Cuando los locales avancen hacia usuarios reales, este ítem sube solo.
- **Limpieza total de sprawl** (páginas mock, .db vacíos, columnas muertas que ningún eje toca, dashboard legacy): se limpia lo que los ejes atraviesan; el resto espera a que un eje lo necesite o a una pasada final de higiene.
- **CLAUDE.md**: se reescribe cuando la Fase 0 esté cerrada, contra el sistema ya relevado y con las primeras reparaciones hechas — para no documentar dos veces.

## 6. Próximos pasos inmediatos

1. Merge de este master al repo (branch + PR).
2. Apertura de la Fase 0: diseño del primer spec de reparación (la ventana de conexión viva + cimientos del Eje 1 + formalización del harness con el experimento puente), con verificación previa del estado del repo.

## 7. Estado y secuencia de la Fase 0 (vivo — actualizado 2026-06-12)

Esta sección registra el avance real de la Fase 0 y su secuencia, que se reordenó sobre la marcha por una decisión de Gerardo. Es el mapa único de la fase — evita que el orden viva en la memoria de las conversaciones.

### 7.1 Specs cerrados

- **F0.1 — Ventana de conexión viva** (`SPEC_S1C_F01_VENTANA_CONEXION.md`): V1-V7 cerrados. Gold Set confirmado (113), huérfanas (multi-época), emergentes (508/0), seguridad viva (200 sin auth, diferida), costo refutado como problema de facturación, censo de residencia.
- **F0.2 — Diagnóstico CLAE** (`SPEC_S1C_F02_DIAGNOSTICO_CLAE.md`): la caída no es regresión sino fin de backfill único; backlog técnicamente desbloqueado, cobertura → C8.
- **F0.3 — Observabilidad del Eje 1** (`SPEC_S1C_F03_OBSERVABILIDAD.md`): acta de corrida local + alertas + panel. En main; pendientes 3 pasos manuales de Gerardo (066 Supabase + deploy + corrida) para el panel en vivo.
- **F0.4a — Discovery de elegibilidad** (`SPEC_S1C_F04a_DISCOVERY_ELEGIBILIDAD.md`): las tres preguntas de diseño respondidas con datos (ver 7.3 — hallazgos anclados a sus consumidores).
- **F0.5 — Harness formalizado + experimento puente** (`SPEC_S1C_F05_HARNESS_DESIGN.md` + `SPEC_S1C_F05_EXP_PUENTE.md`): baseline honesto fechado (ISCO-4 91,7% / ESCO 60% sobre los false del Gold Set); corrida 1 del puente dio el doble desajuste (ver Eje 3).
- **F0.6 — Discovery de anatomía del error** (`SPEC_S1C_F06_ANATOMIA_ERROR.md`): re-corrida read-only de las 312 correcciones de Cyn por el matcher de hoy. Cierra la hipótesis dirigente (ver Eje 3): P-14 loop roto (b)=0, hipótesis confirmada en universo amplio, residuo semántico sugerido a medir después, frente recalibrado a matching grueso, Eje 4 piso 26-95/357.

### 7.2 Acta de decisión — el backlog se suelta después de mejorar el procesamiento

Gerardo (2026-06-12): el backlog de 10.787 ofertas elegibles **no se suelta con el pipeline actual**. Soltarlo ahora produciría 10.787 ofertas más con la calidad mediocre conocida (sector colapsado, perfil argentino sin decidir, emergentes perdidas). La prioridad no es la cobertura sino la **calidad del procesamiento**. Consecuencia de secuencia:

1. **Primero el harness** (F0.5): es la precondición para saber si una mejora al procesamiento mejora o empeora, sin romper producción. Sin harness, mejorar es un acto de fe.
2. **Después, las mejoras del procesamiento medidas** (Eje 3 y vecinos): sector, perfil argentino a la decisión, emergentes — cada una probada en el harness antes de producción.
3. **El criterio único de elegibilidad + el candado de inmutabilidad** (F0.4b): cuando se vaya a soltar el backlog en serio.
4. **El backlog se suelta al final**, con el procesamiento ya mejorado y medido. El corte t1 (baseline del harness) nace con la calidad nueva, no la vieja.

Esto reordena la Fase 0: el harness pasa al frente; elegibilidad/candado/backlog van al final. La acción "gratis" de recuperar las 10.787 con un refresh (sin código) queda **deliberadamente en pausa** hasta el paso 4 — recuperarlas ahora sería procesarlas mal. (Esto matiza §4.1, que con el diagnóstico F0.2 daba el backlog por "desbloqueado ya": técnicamente lo está; por decisión de calidad, se posterga.)

### 7.3 Hallazgos del discovery F0.4a anclados a sus consumidores

Para que el discovery no quede huérfano (sería D-15 dentro de la fase que lo combate), sus hallazgos quedan apuntados al spec que los consumirá:

- **La regla de negocio efectiva + las 4 contradicciones** (candado fantasma · tres definiciones de "no tocar" que no coinciden · filtro de descripción solo en la cola · prioridad solo prioriza NLP) → **las consume F0.4b** (diseño del criterio único). F0.4b arranca leyendo F0.4a §8, no rehace el análisis.
- **El candado de inmutabilidad nunca se conectó**: el check protege `validado_humano` (0 filas) mientras la validación manual escribe `validado`; discrepancia de string desde el 2026-01-23 (commit 2052761c). Las ~60K ofertas validadas son reprocesables hoy — **no hay candado efectivo**. → F0.4b debe **decidir cuál es el candado real** antes de cualquier reproceso masivo. Es deuda y decisión abierta, no solo dato.
- **El acoplamiento selección↔estados es bajo**: la selección se puede unificar sin migrar las 68K filas históricas (keya por presencia/ausencia + 3 literales; los otros 5 estados son residuo que solo leen el sync y SPEC U-1). → F0.4b puede unificar el criterio sin tocar datos; si renombra estados, debe tocar `sync_to_supabase.py` y `scripts/spec_u1/`.
- **Las 14.189 "nunca procesadas"**: 3.402 exclusión legítima (sin descripción útil) + 10.787 backlog reciente (may-jun, ningún refresh corrió). 0 elegibles sin NLP anteriores a mayo (el throughput histórico cerró). → lo consume el paso 4 de 7.2 (soltar el backlog), no antes.

### 7.4 Specs pendientes de la Fase 0 (orden vigente)

1. **F0.5 — Harness formalizado + experimento puente** (próximo): infraestructura para medir mejoras contra ground truth (Gold Set 113 + pares de Cyn). Primer consumidor: la inyección de aristas argentinas (calibra el Eje 3).
2. **Specs de mejora del procesamiento** (post-harness, cada uno medido): sector, perfil argentino a la decisión, captura de emergentes.
3. **F0.4b — Criterio único de elegibilidad + candado de inmutabilidad** (lee F0.4a).
4. **Soltar el backlog + corte t1** (con procesamiento mejorado y medido).

Diferidos vivos: 3 pasos manuales de F0.3 (panel en vivo); seguridad OE-11 (verificada en F0.1, reparación diferida por decisión de Gerardo); datos menores de ventana viva (fecha del backfill CLAE, pico egress 09-jun).

### 7.5 Orden de frente de la Fase 2 (derivado de F0.6, 2026-06-18)

El discovery de anatomía del error fija el orden por gravedad y dependencia:

1. **Loop de Cyn / Eje 2 primero.** (b)=0 es lo más grave y es habilitante: sin un loop que devuelva las correcciones al sistema, ninguna mejora de reglas o vocabulario vuelve — es llenar un balde agujereado. Cerrar el loop desbloquea todo lo demás.
2. **Reglas / Eje 4 segundo.** Las reglas deciden el 80% de los errores del universo; `R240_operario_produccion` (9/67) es el objetivo puntual de arranque. Fix directo y medible rápido.
3. **Medir el residuo semántico tercero.** Recién con las reglas arregladas, re-correr el discovery: ese número decide si el semántico necesita trabajo propio (no el 41% de los 67 sesgados). La corrida 2 del experimento puente (los 3.292 pares B_FUERTE) re-entra acá — cuando el semántico tenga espacio para decidir, recién tiene sentido medir si más aristas argentinas lo mejoran.

---

> *Versión 0.2 — incorpora la revisión del hilo del harness (2026-06-11). El norte (sección 1) es la visión de Gerardo formulada contra el relevamiento completo; los criterios C1-C8 son la definición operativa de "fábrica de alto nivel". Si un criterio no convence, se discute acá — todo lo demás se deriva de ellos.*
