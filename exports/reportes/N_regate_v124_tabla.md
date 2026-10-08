# FRENTE N — Gate 1 (los 28 de Cyn): tabla de scoring caso por caso

Modelo: qwen2.5:14b · pipeline N1→v12.2→N3 · cuerpo completo de BD.
Equivalencia funcional (verbo-núcleo + objeto), granularidad contada aparte. El gate se aprueba mirando la tabla.

## Resumen

- **PASA** (cob≥85%, prec≥90%, 0 sobras): 29/43 · **PASA-con-observación**: 9 · **REVISAR**: 5
- Cobertura funcional promedio **94%** · precisión promedio **93%**
- **Anti-alucinación (requisito duro): 12 casos vacío-válido → 0 regresiones** (CUMPLE)
- **6 OK intocables**: PASA, OK (vacío correcto), OK (vacío correcto), OK (vacío correcto), PASA, PASA (sin regresión)

## Tabla

| # | id | portal | Cyn | cob | prec | gold/v12 | granularidad | veredicto |
|---|----|--------|-----|-----|------|----------|--------------|-----------|
| 1 | 1118165658 | bumeran | FALL | 78% | 100% | 9/7 | fusionada (7 vs 9) | REVISAR |
| 2 | 5790086984 | computrabajo | Sí.  | 100% | 100% | 8/6 | fusionada (6 vs 8) | PASA |
| 3 | 1118392033 | bumeran | FALL | 100% | 100% | 3/6 | sobre-dividida (6 vs 3) | PASA |
| 4 | 2176458 | zonajobs | FALL | 86% | 100% | 7/6 | ok | PASA |
| 5 | 1117972807 | bumeran | FALL | 100% | 100% | 3/3 | ok | PASA |
| 6 | 1118316198 | bumeran | FALL | 86% | 79% | 7/14 | sobre-dividida (14 vs 7) | PASA-con-observacion |
| 7 | 2176705 | zonajobs | FALL | 100% | 100% | 7/7 | ok | PASA |
| 8 | 6477274334 | computrabajo | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 9 | 1118058753 | bumeran | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 10 | 6265862938 | computrabajo | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 11 | 6171358600 | computrabajo | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 12 | 2185030 | zonajobs | FALL | 86% | 60% | 7/10 | sobre-dividida (10 vs 7) | PASA-con-observacion |
| 13 | 5273316732 | computrabajo | FALL | 100% | 100% | 2/2 | ok | PASA |
| 14 | 5917821361 | computrabajo | FALL | 100% | 100% | 4/4 | ok | PASA |
| 15 | 5650193558 | computrabajo | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 16 | 2176546 | zonajobs | OK | 100% | 100% | 5/5 | ok | PASA |
| 17 | 2169530 | zonajobs | FALL | 100% | 100% | 4/4 | ok | PASA |
| 18 | 2168972 | zonajobs | FALL | 100% | 67% | 2/3 | ok | PASA-con-observacion |
| 19 | 6097371222 | computrabajo | OK | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 20 | 2172514 | zonajobs | OK | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 21 | 5909299836 | computrabajo | OK | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 22 | 5160083235 | computrabajo | OK | 100% | 100% | 1/1 | ok | PASA |
| 23 | 6483882943 | computrabajo | OK | 100% | 100% | 1/2 | ok | PASA |
| 24 | 2187269 | zonajobs | FALL | 86% | 60% | 7/10 | sobre-dividida (10 vs 7) | PASA-con-observacion |
| 25 | 1118076732 | bumeran | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 26 | 2181056 | zonajobs | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 27 | 1118300373 | bumeran | FALL | 100% | 100% | 4/4 | ok | PASA |
| 28 | 2176620 | zonajobs | FALL | 86% | 100% | 7/7 | ok | PASA |
| 29 | 1117212619 | bumeran | VACI | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 30 | 2184455 | zonajobs | TARE | 100% | 57% | 4/14 | sobre-dividida (14 vs 4) | PASA-con-observacion |
| 31 | 7853619060 | portalempleo | TARE | 100% | 100% | 6/6 | ok | PASA |
| 32 | 8802322877 | computrabajo | TARE | 100% | 33% | 1/3 | sobre-dividida (3 vs 1) | PASA-con-observacion |
| 33 | 8839648839 | indeed | caso | 80% | 67% | 5/6 | ok | REVISAR |
| 34 | 7675133068 | computrabajo | caso | 100% | 100% | 6/6 | ok | PASA |
| 35 | 5092480960 | computrabajo | caso | 80% | 100% | 5/4 | ok | REVISAR |
| 36 | 8493010864 | computrabajo | caso | 100% | 88% | 7/8 | ok | PASA-con-observacion |
| 37 | 7916148421 | computrabajo | caso | 100% | 100% | 3/3 | ok | PASA |
| 38 | 8046413181 | indeed | caso | 80% | 100% | 5/7 | sobre-dividida (7 vs 5) | REVISAR |
| 39 | 8016348095 | indeed | caso | 100% | 83% | 6/12 | sobre-dividida (12 vs 6) | PASA-con-observacion |
| 40 | 5558920196 | computrabajo | caso | 0% | 100% | 1/0 | ok | REVISAR |
| 41 | 8665011978 | indeed | caso | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 42 | 8889067032 | indeed | caso | 100% | 100% | 10/10 | ok | PASA |
| 43 | 8001095540 | indeed | caso | 94% | 84% | 16/19 | sobre-dividida (19 vs 16) | PASA-con-observacion |

## Detalle por caso (gold vs v12, veredicto por tarea)


### Caso 1 — id `1118165658` (bumeran) — REVISAR
Cyn: FALLA · cobertura 78% · precisión 100% · granularidad fusionada (7 vs 9)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| analizar y evaluar riesgo crediticio para el otorgamiento de líneas de crédito a clientes | ✅ (100%) |
| realizar seguimiento de pedidos | ❌ (33%) |
| coordinar con el área comercial la correcta entrega y cobranza de los pedidos | ✅ (100%) |
| controlar y realizar seguimiento de cuentas corrientes comerciales | ✅ (67%) |
| gestionar integralmente la facturación | ✅ (100%) |
| realizar seguimiento de cobranzas | ❌ (33%) |
| controlar vencimientos | ✅ (100%) |
| elaborar reportes de crédito, facturación y morosidad | ✅ (100%) |
| trabajar coordinadamente con las áreas Comercial, Administración y Finanzas | ✅ (83%) |

### Caso 2 — id `5790086984` (computrabajo) — PASA
Cyn: Sí. “Seguridad y usabilidad” no constitu · cobertura 100% · precisión 100% · granularidad fusionada (6 vs 8)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| diseñar, planificar y ejecutar estrategias integrales de testing | ✅ (100%) |
| crear y mantener casos de prueba, planes de testing y documentación técnica detallada | ✅ (100%) |
| identificar, reportar y dar seguimiento a los bugs hasta su resolución | ✅ (100%) |
| asegurar que el producto cumpla con los requisitos funcionales y no funcionales (performance, seguridad y usabilidad) | ✅ (100%) |
| participar de las ceremonias ágiles | ✅ (100%) |
| articular activamente con desarrolladores, BAs y otros stakeholders | ✅ (100%) |
| aportar análisis crítico sobre los requerimientos | ✅ (100%) |
| actuar como nexo entre los equipos técnicos y los clientes | ✅ (100%) |

### Caso 3 — id `1118392033` (bumeran) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad sobre-dividida (6 vs 3)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| realizar la carga, descarga y reparto de mercadería a clientes | ✅ (83%) |
| brindar una atención cordial a los clientes | ✅ (100%) |
| cuidar el vehículo y la mercadería asignada | ✅ (100%) |

### Caso 4 — id `2176458` (zonajobs) — PASA
Cyn: FALLA · cobertura 86% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| mecanizar en máquinas CNC con programación a pie de máquina mediante sistema FAGOR | ✅ (88%) |
| usar y mantener herramientas de medición | ✅ (100%) |
| ejecutar las órdenes de trabajo | ✅ (100%) |
| controlar la entrada y salida al taller de materiales y equipos de trabajo | ✅ (100%) |
| llevar registro y control de los trabajos realizados y/o a realizar en el taller | ✅ (100%) |
| mantener en orden el equipo y el sitio de trabajo, reportando cualquier anomalía | ✅ (100%) |
| cumplir las normas y procedimientos en materia de seguridad integral | ❌ (0%) |

### Caso 5 — id `1117972807` (bumeran) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| colaborar con la liquidación de sueldos | ✅ (100%) |
| tareas de contabilidad general | ✅ (100%) |
| tareas generales de oficina | ✅ (100%) |

### Caso 6 — id `1118316198` (bumeran) — PASA-con-observacion
Cyn: FALLA · cobertura 86% · precisión 79% · granularidad sobre-dividida (14 vs 7)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| planificar, ejecutar y optimizar la estrategia de performance digital | ✅ (83%) |
| impulsar la adquisición de usuarios | ❌ (33%) |
| monitorear y analizar indicadores clave como CPA, ROAS, conversión, retención y calidad de tráfico | ✅ (100%) |
| identificar oportunidades de mejora a partir del análisis de datos y comportamiento de usuarios | ✅ (100%) |
| implementar y validar herramientas de medición, tracking y atribución digital | ✅ (100%) |
| gestionar acciones de CRM, segmentación y automatización para potenciar la retención | ✅ (100%) |
| utilizar herramientas de IA para optimizar procesos, generar insights y mejorar el rendimiento de las campañas | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['planificar campañas de performance en Google Ads, Meta Ads y otros canales digitales', 'ejecutar campañas de performance en Google Ads, Meta Ads y otros canales digitales', 'optimizar campañas de performance en Google Ads, Meta Ads y otros canales digitales']

### Caso 7 — id `2176705` (zonajobs) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| diseñar, desarrollar y entregar soluciones de software confiables y de alta calidad | ✅ (100%) |
| contribuir al desarrollo de código productivo y participar activamente en revisiones de código dentro del equipo | ✅ (100%) |
| resolver problemas técnicos complejos relacionados con el diseño, el desarrollo y la estabilidad de las aplicaciones | ✅ (100%) |
| identificar y ejecutar oportunidades de automatización para reducir incidentes recurrentes y mejorar la estabilidad operativa | ✅ (100%) |
| participar en evaluaciones técnicas con proveedores externos, startups y equipos internos cuando sea requerido | ✅ (100%) |
| promover el uso de nuevas tecnologías, herramientas y buenas prácticas dentro de la comunidad de ingeniería | ✅ (100%) |
| contribuir a una cultura de diversidad, equidad e inclusión dentro del equipo y la organización | ✅ (100%) |

### Caso 8 — id `6477274334` (computrabajo) — OK (vacío correcto)
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 9 — id `1118058753` (bumeran) — OK (vacío correcto)
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 10 — id `6265862938` (computrabajo) — OK (vacío correcto)
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 11 — id `6171358600` (computrabajo) — OK (vacío correcto)
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 12 — id `2185030` (zonajobs) — PASA-con-observacion
Cyn: FALLA · cobertura 86% · precisión 60% · granularidad sobre-dividida (10 vs 7)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| captar nuevos asociados | ✅ (100%) |
| comercializar planes de cobertura médica | ✅ (100%) |
| realizar prospección activa presencial y/o digital de nuevos clientes individuales y corporativos, gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta | ❌ (56%) |
| recibir y gestionar leads provenientes de distintos canales | ✅ (83%) |
| registrar y realizar seguimiento de la gestión comercial en CRM | ✅ (67%) |
| analizar la competencia | ✅ (100%) |
| reportar acciones del mercado | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['asegurar una experiencia de asesoramiento cercana, profesional y efectiva', 'asegurar una respuesta oportuna y orientada al cierre', 'garantizar trazabilidad y eficiencia en cada interacción', 'aportar información clave para mejorar las estrategias comerciales y potenciar los resultados del equipo']

_N3 descartó:_ ['prospección activa presencial y/o digital de nuevos clientes individuales y corporativos']

### Caso 13 — id `5273316732` (computrabajo) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| ofrecer productos bancarios | ✅ (100%) |
| comunicarse de manera clara, efectiva y persuasiva para generar ventas | ✅ (100%) |

### Caso 14 — id `5917821361` (computrabajo) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| brindar atención cordial, eficiente y resolutiva a los clientes en sala y vía pública | ✅ (100%) |
| promocionar los servicios, eventos y beneficios del Bingo | ✅ (100%) |
| garantizar una experiencia satisfactoria y segura bajo los protocolos de servicio | ✅ (100%) |
| colaborar en acciones de marketing y fidelización de clientes | ✅ (100%) |

### Caso 15 — id `5650193558` (computrabajo) — OK (vacío correcto)
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 16 — id `2176546` (zonajobs) — PASA
Cyn: OK · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| realizar extracciones de sangre para la obtención de plasma rico en plaquetas (PRP) | ✅ (100%) |
| administrar sueros vitamínicos según protocolos establecidos | ✅ (100%) |
| brindar atención y orientación a los pacientes durante los procedimientos | ✅ (100%) |
| mantener un ambiente de trabajo seguro y estéril | ✅ (100%) |
| colaborar con el equipo para asegurar la calidad del servicio | ✅ (100%) |

### Caso 17 — id `2169530` (zonajobs) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| realizar el mantenimiento preventivo y correctivo de una flota vehicular, incluyendo máquinas viales, camiones y utilitarios | ✅ (73%) |
| reparar maquinarias pesadas, camiones y utilitarios | ✅ (100%) |
| diagnosticar y resolver fallas mecánicas en sistemas hidráulicos y neumáticos | ✅ (100%) |
| realizar reparaciones generales y trabajos de soldadura | ✅ (100%) |

### Caso 18 — id `2168972` (zonajobs) — PASA-con-observacion
Cyn: FALLA · cobertura 100% · precisión 67% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| asistir a audiencias | ✅ (100%) |
| realizar el seguimiento de la cartera de clientes | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['trabajar en conjunto con un equipo comprometido y en constante crecimiento']

### Caso 19 — id `6097371222` (computrabajo) — OK (vacío correcto)
Cyn: OK · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 20 — id `2172514` (zonajobs) — OK (vacío correcto)
Cyn: OK · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 21 — id `5909299836` (computrabajo) — OK (vacío correcto)
Cyn: OK · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 22 — id `5160083235` (computrabajo) — PASA
Cyn: OK · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| reponer los productos en góndolas | ✅ (100%) |

### Caso 23 — id `6483882943` (computrabajo) — PASA
Cyn: OK · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| realizar la carga y descarga de mercadería | ✅ (75%) |

### Caso 24 — id `2187269` (zonajobs) — PASA-con-observacion
Cyn: FALLA · cobertura 86% · precisión 60% · granularidad sobre-dividida (10 vs 7)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| captar nuevos asociados | ✅ (100%) |
| comercializar planes de cobertura médica | ✅ (100%) |
| realizar prospección activa presencial y/o digital de nuevos clientes individuales y corporativos, gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta | ❌ (56%) |
| recibir y gestionar leads provenientes de distintos canales | ✅ (83%) |
| registrar y realizar seguimiento de la gestión comercial en CRM | ✅ (67%) |
| analizar la competencia | ✅ (100%) |
| reportar acciones del mercado | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['asegurar una experiencia de asesoramiento cercana, profesional y efectiva', 'asegurar una respuesta oportuna y orientada al cierre', 'garantizar trazabilidad y eficiencia en cada interacción', 'aportar información clave para mejorar las estrategias comerciales y potenciar los resultados del equipo']

_N3 descartó:_ ['prospección activa presencial y/o digital de nuevos clientes individuales y corporativos']

### Caso 25 — id `1118076732` (bumeran) — OK (vacío correcto)
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 26 — id `2181056` (zonajobs) — OK (vacío correcto)
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 27 — id `1118300373` (bumeran) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| aplicar tratamientos de medicina regenerativa y estética ginecológica | ✅ (100%) |
| participar en la formación y capacitación en protocolos exclusivos | ✅ (100%) |
| brindar atención profesional, cálida y empática a las pacientes | ✅ (100%) |
| contribuir a un ambiente de excelencia e innovación en medicina estética | ✅ (100%) |

### Caso 28 — id `2176620` (zonajobs) — PASA
Cyn: FALLA · cobertura 86% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| desarrollar, configurar y mantener pantallas HMI en Fast Tools (Yokogawa) para sistemas SCADA de producción y facilities | ✅ (67%) |
| programar y configurar gráficos de proceso, tendencias y alarmas en DeltaV Operate para plantas de tratamiento y baterías de producción | ✅ (67%) |
| diseñar arquitecturas de visualización SCADA integradas, asegurando consistencia entre sistemas Fast Tools y DeltaV | ✅ (73%) |
| implementar estándares de HMI según ISA-101 y guías de alto rendimiento (High Performance HMI) | ✅ (80%) |
| coordinar con Operaciones para definir requerimientos de visualización y optimizar interfaces de operador | ✅ (100%) |
| elaborar documentación técnica de pantallas SCADA (especificaciones funcionales, narrativas de operación, manuales de usuario) | ❌ (55%) |
| supervisar contratistas de servicios de automatización en desarrollos SCADA | ✅ (100%) |

### Caso 29 — id `1117212619` (bumeran) — OK (vacío correcto)
Cyn: VACIO (flip v12.4: requisitos, RG-TAR-00 · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 30 — id `2184455` (zonajobs) — PASA-con-observacion
Cyn: TAREAS (hoja 3; sin herramientas, RG-TAR · cobertura 100% · precisión 57% · granularidad sobre-dividida (14 vs 4)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| instalar tendidos eléctricos en automotores | ✅ (100%) |
| laminar y pulir PRFV | ✅ (100%) |
| fabricar y reparar piezas en fibra de vidrio | ✅ (100%) |
| armar estructuras metálicas | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['realizar medición y controles eléctricos', 'manejar herramientas específicas para PRFV', 'manejar materiales específicos para PRFV', 'realizar trabajos manuales con precisión', 'soldar estructuras metálicas MIG/MAG', 'trabajar en transformaciones y adaptaciones vehiculares']

_N3 descartó:_ ['manejar herramientas eléctricas y neumáticas']

### Caso 31 — id `7853619060` (portalempleo) — PASA
Cyn: TAREAS (hoja 3; 6, Tareas principales) · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| reponer mercadería | ✅ (100%) |
| atender al público | ✅ (100%) |
| realizar tareas de depósito | ✅ (100%) |
| embalar | ✅ (100%) |
| cargar y descargar mercadería | ✅ (100%) |
| limpiar y mantener el lugar de trabajo | ✅ (100%) |

### Caso 32 — id `8802322877` (computrabajo) — PASA-con-observacion
Cyn: TAREAS (hoja 3; 1, del pitch, RG-TAR-004 · cobertura 100% · precisión 33% · granularidad sobre-dividida (3 vs 1)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| desarrollar y potenciar la cartera de clientes | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['captar nuevos clientes en campo, terreno o calle', 'reactivar clientes existentes']

### Caso 33 — id `8839648839` (indeed) — REVISAR
Cyn: caso 1 — nivel de intervencion (RG-TAR-0 · cobertura 80% · precisión 67% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| gestionar integralmente el proceso de entrega de las órdenes asignadas | ✅ (83%) |
| coordinar con recursos internos y terceros contratados para cumplir requisitos y plazos del cliente | ✅ (67%) |
| comunicarse regularmente con los clientes brindando actualizaciones claras y consistentes | ❌ (0%) |
| gestionar tareas como la orden de circuitos de internet, proyectos VoIP alojados y procesos de portabilidad numérica | ✅ (100%) |
| documentar dependencias y prioridades para la ejecución del proyecto | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['utilizar experiencia práctica en la implementación de SDWAN, portabilidad VoIP e ordenación de circuitos Internet con diversos proveedores', 'asumir responsabilidades adicionales y proyectos según sea necesario para apoyar el éxito del equipo y la organización']

_N3 descartó:_ ['comunicarse regularmente con clientes proporcionando actualizaciones claras durante todo el ciclo de vida de la entrega']

### Caso 34 — id `7675133068` (computrabajo) — PASA
Cyn: caso 2 — mismo proceso, tareas distintas · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| autorizar la puesta en marcha de la línea de producción | ✅ (100%) |
| realizar seguimiento de los lotes productivos | ✅ (75%) |
| controlar y liberar áreas de producción | ✅ (100%) |
| controlar el acondicionamiento en líneas | ✅ (100%) |
| muestrear materias primas, semielaborados, productos terminados y material de empaque | ✅ (100%) |
| realizar controles fisicoquímicos de materias primas, semielaborados y productos terminados | ✅ (100%) |

### Caso 35 — id `5092480960` (computrabajo) — REVISAR
Cyn: caso 3 — generalidad (RG-TAR-016) · cobertura 80% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| gestionar integralmente la agenda y las prioridades | ✅ (100%) |
| coordinar reuniones, viajes y logística | ✅ (100%) |
| comunicarse directamente con socios, proveedores y equipo | ❌ (0%) |
| organizar información sensible y brindar soporte ejecutivo | ✅ (83%) |
| resolver situaciones con autonomía y criterio | ✅ (100%) |

_N3 descartó:_ ['Comunicarse directamente con socios, proveedores y equipo']

### Caso 36 — id `8493010864` (computrabajo) — PASA-con-observacion
Cyn: caso 5 — bloque Tareas; HSE fuera (front · cobertura 100% · precisión 88% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| ejecutar y supervisar la elaboración de productos cosméticos según fórmulas aprobadas y procedimientos establecidos | ✅ (100%) |
| preparar y dosificar materias primas, controlando pesos, tiempos y condiciones del proceso | ✅ (100%) |
| controlar parámetros de proceso (temperatura, agitación, tiempos, homogeneidad) | ✅ (100%) |
| registrar documentación productiva: órdenes de producción, hojas de lote y controles de proceso | ✅ (100%) |
| coordinar con las áreas de Calidad, I+D y Producción ante desvíos o ajustes de formulación | ✅ (100%) |
| mantener el orden, limpieza y correcto uso de equipos e instalaciones del laboratorio | ✅ (100%) |
| detectar desvíos, proponer mejoras y colaborar en la optimización de procesos productivos | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['Asegurar el cumplimiento de las Buenas Prácticas de Manufactura (GMP) y normativas internas']

### Caso 37 — id `7916148421` (computrabajo) — PASA
Cyn: caso 6 — chrome del portal (RG-TAR-001/N · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| brindar asesoramiento personalizado a clientes | ✅ (100%) |
| ordenar y coordinar las filas del banco | ✅ (100%) |
| atender y gestionar reclamos | ✅ (100%) |

### Caso 38 — id `8046413181` (indeed) — REVISAR
Cyn: caso 7 — asegurar como unidad (RG-TAR-01 · cobertura 80% · precisión 100% · granularidad sobre-dividida (7 vs 5)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| coordinar documentación de viaje y asegurar que todo esté en tiempo y forma | ✅ (100%) |
| gestionar bookings para Argentina, Chile, Perú, Colombia y Ecuador | ✅ (100%) |
| mantener una comunicación fluida, enviando confirmaciones y updates | ✅ (100%) |
| revisar itinerarios, actualizar costos y coordinar facturación | ✅ (100%) |
| atender el teléfono de emergencia (rotativo) | ❌ (0%) |

_N3 descartó:_ ['manejo de teléfono de emergencia (rotativo)']

### Caso 39 — id `8016348095` (indeed) — PASA-con-observacion
Cyn: caso 8 — finalidad subordinada fuera (RG · cobertura 100% · precisión 83% · granularidad sobre-dividida (12 vs 6)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| brindar atención personalizada a compañías de minería, ofreciendo soluciones financieras adaptadas | ✅ (100%) |
| gestionar y ampliar la cartera de clientes del segmento empresas del sector minero, realizando visitas periódicas | ✅ (100%) |
| desarrollar propuestas comerciales y financieras para empresas de minería | ✅ (100%) |
| realizar análisis de riesgos y viabilidad de proyectos comerciales del sector minero | ✅ (100%) |
| supervisar y hacer seguimiento de las operaciones y servicios brindados | ✅ (100%) |
| identificar oportunidades de negocio, participando en la promoción de productos y servicios | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['Incluir productos como créditos, financiamiento, seguros y otros servicios bancarios en las propuestas', 'Asegurar la satisfacción del cliente y el cumplimiento de los plazos establecidos']

### Caso 40 — id `5558920196` (computrabajo) — REVISAR
Cyn: caso 9 — funcion generica (RG-TAR-016) · cobertura 0% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| realizar tareas administrativas, contables y algunas impositivas | ❌ (0%) |

### Caso 41 — id `8665011978` (indeed) — OK (vacío correcto)
Cyn: caso 10 — VACIO (solo requisito) · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

### Caso 42 — id `8889067032` (indeed) — PASA
Cyn: caso 11 — garantizar como responsabilida · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| supervisar y asegurar en campo la correcta ejecución del montaje, precomisionado, comisionado y puesta en marcha de equipos de electricidad, instrumentación y control en pozos del upstream | ✅ (100%) |
| planificar y participar en la programación de trabajos vinculados a la puesta en marcha de nuevos pozos y optimizaciones | ✅ (100%) |
| garantizar el cumplimiento de estándares técnicos, de calidad, seguridad, salud y medio ambiente | ✅ (100%) |
| verificar el cumplimiento de alcances, plazos, instructivos, procedimientos y especificaciones técnicas | ✅ (100%) |
| gestionar eficientemente la planificación de trabajos, recursos y materiales | ✅ (100%) |
| asegurar la correcta utilización de sistemas corporativos y la trazabilidad de la información | ✅ (100%) |
| articular con distintas áreas internas para la ejecución segura y eficiente de las tareas y gestionar permisos de trabajo | ✅ (100%) |
| elaborar y validar informes de ejecución y documentación técnica | ✅ (100%) |
| definir y asignar recursos, equipos, herramientas y materiales necesarios | ✅ (100%) |
| validar el cumplimiento de tareas en campo para su posterior certificación según pliegos técnicos | ✅ (100%) |

### Caso 43 — id `8001095540` (indeed) — PASA-con-observacion
Cyn: caso 21 — AR sin HSE/compliance (RG-TAR- · cobertura 94% · precisión 84% · granularidad sobre-dividida (19 vs 16)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| analizar las cuentas corrientes de los clientes para detectar y conciliar diferencias y partidas (facturas, notas de crédito, órdenes de pago) | ✅ (62%) |
| realizar el seguimiento de los clientes deudores vía telefónica, correo electrónico y/o reuniones | ✅ (100%) |
| ingresar las cobranzas y generar los recibos correspondientes | ✅ (100%) |
| asesorar al cliente sobre su situación y brindarle soporte para agilizar el cobro de las facturas pendientes | ❌ (44%) |
| revisar diariamente los extractos bancarios para identificar acreditaciones de pagos no identificados | ✅ (88%) |
| elaborar y enviar los estados de cuenta a los clientes deudores | ✅ (100%) |
| realizar diariamente la apertura y el cierre de caja | ✅ (100%) |
| informar a los responsables de cuenta sobre cualquier riesgo de cobranza | ✅ (83%) |
| verificar que no existan diferencias cambiarias significativas y generar la corrección correspondiente | ✅ (88%) |
| brindar asistencia a los auditores externos | ✅ (100%) |
| crear y validar información financiera para el alta o reactivación de clientes | ✅ (100%) |
| validar las líneas de crédito de los clientes y gestionar autorización de sobregiros o suspensión de la línea de crédito | ✅ (100%) |
| generar reportes semanales, quincenales y mensuales de las cuentas por cobrar | ✅ (100%) |
| realizar la previsión de deudores incobrables | ✅ (100%) |
| participar como test owner de controles internos | ✅ (100%) |
| realizar la búsqueda de documentación y carga para el armado de cartas de pago a proveedores intragroup y del exterior | ✅ (90%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['fomentar el cuidado personal y de compañeros de trabajo', 'cumplir con procedimientos del Sistema de Gestión Ambiental', 'cumplir con procedimientos del Sistema de Seguridad y Salud Ocupacional']

_N3 descartó:_ ['conocer aspectos e impactos ambientales', 'actuar permanentemente en forma segura']