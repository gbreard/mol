# FRENTE N — Gate 1 (los 28 de Cyn): tabla de scoring caso por caso

Modelo: qwen2.5:14b · pipeline N1→v12.2→N3 · cuerpo completo de BD.
Equivalencia funcional (verbo-núcleo + objeto), granularidad contada aparte. El gate se aprueba mirando la tabla.

## Resumen

- **PASA** (cob≥85%, prec≥90%, 0 sobras): 23/28 · **PASA-con-observación**: 1 · **REVISAR**: 4
- Cobertura funcional promedio **97%** · precisión promedio **95%**
- **Anti-alucinación (requisito duro): 10 casos vacío-válido → 0 regresiones** (CUMPLE)
- **6 OK intocables**: PASA, OK (vacío correcto), OK (vacío correcto), OK (vacío correcto), PASA, PASA (sin regresión)

## Tabla

| # | id | portal | Cyn | cob | prec | gold/v12 | granularidad | veredicto |
|---|----|--------|-----|-----|------|----------|--------------|-----------|
| 1 | 1118165658 | bumeran | FALL | 78% | 100% | 9/7 | fusionada (7 vs 9) | REVISAR |
| 10 | 6265862938 | computrabajo | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 11 | 6171358600 | computrabajo | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 12 | 2185030 | zonajobs | FALL | 83% | 64% | 6/11 | sobre-dividida (11 vs 6) | REVISAR |
| 13 | 5273316732 | computrabajo | FALL | 100% | 100% | 2/2 | ok | PASA |
| 14 | 5917821361 | computrabajo | FALL | 100% | 100% | 4/4 | ok | PASA |
| 15 | 5650193558 | computrabajo | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 16 | 2176546 | zonajobs | OK | 100% | 100% | 5/5 | ok | PASA |
| 17 | 2169530 | zonajobs | FALL | 100% | 100% | 4/4 | ok | PASA |
| 18 | 2168972 | zonajobs | FALL | 100% | 100% | 2/2 | ok | PASA |
| 19 | 6097371222 | computrabajo | OK | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 2 | 5790086984 | computrabajo | Sí.  | 100% | 100% | 8/6 | fusionada (6 vs 8) | PASA |
| 20 | 2172514 | zonajobs | OK | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 21 | 5909299836 | computrabajo | OK | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 22 | 5160083235 | computrabajo | OK | 100% | 100% | 1/1 | ok | PASA |
| 23 | 6483882943 | computrabajo | OK | 100% | 100% | 1/1 | ok | PASA |
| 24 | 2187269 | zonajobs | FALL | 86% | 64% | 7/11 | sobre-dividida (11 vs 7) | PASA-con-observacion |
| 25 | 1118076732 | bumeran | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 26 | 2181056 | zonajobs | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 27 | 1118300373 | bumeran | FALL | 100% | 100% | 4/4 | ok | PASA |
| 28 | 2176620 | zonajobs | FALL | 83% | 86% | 6/7 | ok | REVISAR |
| 3 | 1118392033 | bumeran | FALL | 100% | 100% | 3/6 | sobre-dividida (6 vs 3) | PASA |
| 4 | 2176458 | zonajobs | FALL | 100% | 100% | 7/7 | ok | PASA |
| 5 | 1117972807 | bumeran | FALL | 100% | 100% | 3/2 | ok | PASA |
| 6 | 1118316198 | bumeran | FALL | 75% | 33% | 4/6 | sobre-dividida (6 vs 4) | REVISAR |
| 7 | 2176705 | zonajobs | FALL | 100% | 100% | 7/7 | ok | PASA |
| 8 | 6477274334 | computrabajo | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |
| 9 | 1118058753 | bumeran | FALL | 100% | 100% | 0/0 | ok | OK (vacío correcto) |

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

### Caso 12 — id `2185030` (zonajobs) — REVISAR
Cyn: FALLA · cobertura 83% · precisión 64% · granularidad sobre-dividida (11 vs 6)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| captar nuevos asociados | ✅ (100%) |
| comercializar planes de cobertura médica | ✅ (100%) |
| realizar prospección activa presencial y/o digital de nuevos clientes individuales y corporativos, gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta | ❌ (56%) |
| recibir y gestionar leads provenientes de distintos canales | ✅ (100%) |
| registrar y realizar seguimiento de la gestión comercial en CRM | ✅ (67%) |
| analizar la competencia y reportar acciones del mercado | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['asegurar una experiencia de asesoramiento cercana, profesional y efectiva', 'asegurar una respuesta oportuna y orientada al cierre', 'garantizar trazabilidad y eficiencia en cada interacción', 'aportar información clave para mejorar las estrategias comerciales']

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
| realizar extracciones de sangre para la obtención de plasma rico en plaquetas (PRP) | ✅ (62%) |
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

### Caso 18 — id `2168972` (zonajobs) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| asistir a audiencias | ✅ (100%) |
| realizar el seguimiento de la cartera de clientes | ✅ (100%) |

### Caso 19 — id `6097371222` (computrabajo) — OK (vacío correcto)
Cyn: OK · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| _(vacío válido)_ | ✅ v12 devolvió [] |

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
| realizar la carga y descarga de mercadería | ✅ (100%) |

### Caso 24 — id `2187269` (zonajobs) — PASA-con-observacion
Cyn: FALLA · cobertura 86% · precisión 64% · granularidad sobre-dividida (11 vs 7)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| captar nuevos asociados | ✅ (100%) |
| comercializar planes de cobertura médica | ✅ (100%) |
| realizar prospección activa presencial y/o digital de nuevos clientes individuales y corporativos, gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta | ❌ (56%) |
| recibir y gestionar leads provenientes de distintos canales | ✅ (100%) |
| registrar y realizar seguimiento de la gestión comercial en CRM | ✅ (67%) |
| analizar la competencia | ✅ (100%) |
| reportar acciones del mercado | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['asegurar una experiencia de asesoramiento cercana, profesional y efectiva', 'asegurar una respuesta oportuna y orientada al cierre', 'garantizar trazabilidad y eficiencia en cada interacción', 'aportar información clave para mejorar las estrategias comerciales']

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

### Caso 28 — id `2176620` (zonajobs) — REVISAR
Cyn: FALLA · cobertura 83% · precisión 86% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| desarrollar, configurar y mantener pantallas HMI en Fast Tools (Yokogawa) para sistemas SCADA de producción y facilities | ✅ (67%) |
| programar y configurar gráficos de proceso, tendencias y alarmas en DeltaV Operate para plantas de tratamiento y baterías de producción | ✅ (67%) |
| diseñar arquitecturas de visualización SCADA integradas, asegurando consistencia entre sistemas Fast Tools y DeltaV | ✅ (73%) |
| implementar estándares de HMI según ISA-101 y guías de alto rendimiento (High Performance HMI) | ✅ (80%) |
| coordinar con Operaciones para definir requerimientos de visualización y optimizar interfaces de operador | ✅ (100%) |
| elaborar documentación técnica de pantallas SCADA (especificaciones funcionales, narrativas de operación, manuales de usuario) | ❌ (55%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['supervisar contratistas de servicios de automatización en desarrollos SCADA']

### Caso 3 — id `1118392033` (bumeran) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad sobre-dividida (6 vs 3)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| realizar la carga, descarga y reparto de mercadería a clientes | ✅ (83%) |
| brindar una atención cordial a los clientes | ✅ (100%) |
| cuidar el vehículo y la mercadería asignada | ✅ (100%) |

### Caso 4 — id `2176458` (zonajobs) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| mecanizar en máquinas CNC con programación a pie de máquina mediante sistema FAGOR | ✅ (88%) |
| usar y mantener herramientas de medición | ✅ (100%) |
| ejecutar las órdenes de trabajo | ✅ (100%) |
| controlar la entrada y salida al taller de materiales y equipos de trabajo | ✅ (100%) |
| llevar registro y control de los trabajos realizados y/o a realizar en el taller | ✅ (86%) |
| mantener en orden el equipo y el sitio de trabajo, reportando cualquier anomalía | ✅ (100%) |
| cumplir las normas y procedimientos en materia de seguridad integral | ✅ (83%) |

### Caso 5 — id `1117972807` (bumeran) — PASA
Cyn: FALLA · cobertura 100% · precisión 100% · granularidad ok

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| colaborar con la liquidación de sueldos | ✅ (100%) |
| tareas de contabilidad general | ✅ (100%) |
| tareas generales de oficina | ✅ (67%) |

_N3 descartó:_ ['desempeñarse en tareas generales de oficina']

### Caso 6 — id `1118316198` (bumeran) — REVISAR
Cyn: FALLA · cobertura 75% · precisión 33% · granularidad sobre-dividida (6 vs 4)

| tarea-oro (Cyn) | ¿cubierta por v12? |
|---|---|
| planificar, ejecutar y optimizar la estrategia de performance digital | ✅ (83%) |
| impulsar la adquisición de usuarios | ❌ (33%) |
| monitorear y analizar indicadores clave como CPA, ROAS, conversión, retención y calidad de tráfico | ✅ (100%) |
| identificar oportunidades de mejora a partir del análisis de datos y comportamiento de usuarios | ✅ (100%) |

**Extraídas no soportadas por el oro (revisión: compatible/invención):** ['planificar, ejecutar y optimizar campañas de performance en Google Ads, Meta Ads y otros canales digitales', 'implementar y validar herramientas de medición, tracking y atribución digital', 'gestionar acciones de CRM, segmentación y automatización para potenciar la retención', 'utilizar herramientas de IA para optimizar procesos, generar insights y mejorar el rendimiento de las campañas']

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