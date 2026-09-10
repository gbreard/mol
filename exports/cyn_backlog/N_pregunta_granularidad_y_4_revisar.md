# FRENTE N — Para Cyn: pregunta de granularidad + los 4 casos a revisar

Tres cosas para tu ojo antes de habilitar la re-extracción. **Sin pre-juicio: son disensos de criterio, no errores.** Vos decidís.

---

## 1. La pregunta de granularidad

El sistema nuevo (v12) a veces **une en una sola tarea** dos acciones que vos, en tu validación, **separaste en dos**. Cuando las dos acciones caen sobre objetos distintos pero contiguos, y el aviso las presenta juntas en una misma oración, v12 tiende a dejarlas como una unidad funcional.

**La pregunta:** ¿esa fusión te resulta aceptable como "una unidad funcional", o exigís que se separen siempre en tareas distintas? Tu respuesta fija el criterio del sistema (y del control de calidad permanente).

### Ejemplos concretos (texto real de los avisos)

**C1 (Analista de Créditos y Cobranzas, id 1118165658)**

- Vos marcaste DOS tareas:
    - «realizar seguimiento de pedidos»
    - «coordinar con el área comercial la correcta entrega y cobranza de los pedidos»
- v12 extrajo UNA sola:
    - «seguir pedidos y coordinar con el área comercial para su correcta entrega y cobranzas»

**C1 (mismo aviso)**

- Vos marcaste DOS tareas:
    - «realizar seguimiento de cobranzas»
    - «controlar vencimientos»
- v12 extrajo UNA sola:
    - «seguir cobranzas y controlar vencimientos»

**C2 (Analista QA, id 5790086984)**

- Vos marcaste DOS tareas:
    - «participar de las ceremonias ágiles»
    - «articular activamente con desarrolladores, BAs y otros stakeholders»
- v12 extrajo UNA sola:
    - «participar en las ceremonias ágiles y articular activamente con desarrolladores, BAs y otros stakeholders»

**C2 (mismo aviso)**

- Vos marcaste DOS tareas:
    - «aportar análisis crítico sobre los requerimientos»
    - «actuar como nexo entre los equipos técnicos y los clientes»
- v12 extrajo UNA sola:
    - «aportar análisis crítico sobre los requerimientos y actuar como nexo entre los equipos técnicos y los clientes»

> Tu decisión (marcá una): ☐ la fusión es aceptable cuando es una misma oración/proceso · ☐ separar siempre acciones con verbo propio · ☐ depende (aclarar el criterio):

> _____________________________________________________________________

---

## 2. Los 4 casos a revisar

Quedaron cerca del umbral por granularidad/fidelidad (no por ceguera). Por caso: la tarea-oro que marcaste vos, lo que v12 extrajo, y el disenso puntual.


### Caso 1 — Analista de Créditos y Cobranzas (id 1118165658, bumeran)

| Tarea-oro (vos) | |
|---|---|
| analizar y evaluar riesgo crediticio para el otorgamiento de líneas de crédito a clientes | |
| realizar seguimiento de pedidos | |
| coordinar con el área comercial la correcta entrega y cobranza de los pedidos | |
| controlar y realizar seguimiento de cuentas corrientes comerciales | |
| gestionar integralmente la facturación | |
| realizar seguimiento de cobranzas | |
| controlar vencimientos | |
| elaborar reportes de crédito, facturación y morosidad | |
| trabajar coordinadamente con las áreas Comercial, Administración y Finanzas | |

**v12 extrajo (7):**
- analizar y evaluar riesgo crediticio para el otorgamiento de líneas de crédito a clientes
- seguir pedidos y coordinar con el área comercial para su correcta entrega y cobranzas
- controlar y seguir cuentas corrientes comerciales
- gestionar integralmente la facturación
- seguir cobranzas y controlar vencimientos
- elaborar reportes de crédito, facturación y morosidad
- trabajar coordinado con las áreas Comercial, Administración y Finanzas

**El disenso:** v12 fusionó 2 pares que vos separaste (ver ejemplos arriba) y omitió «trabajar coordinadamente con las áreas Comercial, Administración y Finanzas». Contenido completo salvo esa última.

> ¿Veredicto? ☐ v12 OK (granularidad aceptable) · ☐ corregir (aclarar): ____________________


### Caso 6 — Analista de Marketing Digital (id 1118316198, bumeran)

| Tarea-oro (vos) | |
|---|---|
| planificar, ejecutar y optimizar la estrategia de performance digital | |
| impulsar la adquisición de usuarios | |
| monitorear y analizar indicadores clave como CPA, ROAS, conversión, retención y calidad de tráfico | |
| identificar oportunidades de mejora a partir del análisis de datos y comportamiento de usuarios | |

**v12 extrajo (6):**
- planificar, ejecutar y optimizar campañas de performance en Google Ads, Meta Ads y otros canales digitales
- monitorear y analizar indicadores clave como CPA, ROAS, conversión, retención y calidad de tráfico
- implementar y validar herramientas de medición, tracking y atribución digital
- identificar oportunidades de mejora a partir del análisis de datos y comportamiento de usuarios
- gestionar acciones de CRM, segmentación y automatización para potenciar la retención
- utilizar herramientas de IA para optimizar procesos, generar insights y mejorar el rendimiento de las campañas

**El disenso:** v12 sobre-dividió «planificar, ejecutar y optimizar la estrategia» en 3, y en vez de «monitorear y analizar indicadores clave (CPA, ROAS...)» puso «analizar resultados» (perdió la especificidad de los indicadores).

> ¿Veredicto? ☐ v12 OK (granularidad aceptable) · ☐ corregir (aclarar): ____________________


### Caso 12 — Ejecutivo/a de Ventas Posadas (id 2185030, zonajobs)

| Tarea-oro (vos) | |
|---|---|
| captar nuevos asociados | |
| comercializar planes de cobertura médica | |
| realizar prospección activa presencial y/o digital de nuevos clientes individuales y corporativos, gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta | |
| recibir y gestionar leads provenientes de distintos canales | |
| registrar y realizar seguimiento de la gestión comercial en CRM | |
| analizar la competencia y reportar acciones del mercado | |

**v12 extrajo (11):**
- captar nuevos asociados
- comercializar planes de cobertura médica
- asegurar una experiencia de asesoramiento cercana, profesional y efectiva
- gestionar el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta
- recibir y gestionar leads provenientes de distintos canales
- asegurar una respuesta oportuna y orientada al cierre
- registrar y seguir la gestión comercial en CRM
- garantizar trazabilidad y eficiencia en cada interacción
- analizar la competencia
- reportar acciones del mercado
- aportar información clave para mejorar las estrategias comerciales

**El disenso:** v12 recuperó la misión (captar/comercializar) pero difiere en granularidad de las etapas del proceso de venta y del análisis+reporte de competencia.

> ¿Veredicto? ☐ v12 OK (granularidad aceptable) · ☐ corregir (aclarar): ____________________


### Caso 28 — Ingeniero Scada - Importante Petrolera (Neuquén) (id 2176620, zonajobs)

| Tarea-oro (vos) | |
|---|---|
| desarrollar, configurar y mantener pantallas HMI en Fast Tools (Yokogawa) para sistemas SCADA de producción y facilities | |
| programar y configurar gráficos de proceso, tendencias y alarmas en DeltaV Operate para plantas de tratamiento y baterías de producción | |
| diseñar arquitecturas de visualización SCADA integradas, asegurando consistencia entre sistemas Fast Tools y DeltaV | |
| implementar estándares de HMI según ISA-101 y guías de alto rendimiento (High Performance HMI) | |
| coordinar con Operaciones para definir requerimientos de visualización y optimizar interfaces de operador | |
| elaborar documentación técnica de pantallas SCADA (especificaciones funcionales, narrativas de operación, manuales de usuario) | |

**v12 extrajo (7):**
- desarrollar, configurar y mantener pantallas HMI en Fast Tools
- programar y configurar gráficos de proceso, tendencias y alarmas en DeltaV Operate
- diseñar arquitecturas de visualización SCADA integradas
- implementar estándares de HMI según ISA-101 y guías de alto rendimiento
- coordinar con Operaciones para definir requerimientos de visualización y optimizar interfaces de operador
- elaborar documentación técnica de pantallas SCADA
- supervisar contratistas de servicios de automatización en desarrollos SCADA

**El disenso:** v12 fusionó/dividió distinto las unidades SCADA (desarrollar/configurar/mantener; programar/configurar) respecto de tu marca; contenido técnico cubierto.

> ¿Veredicto? ☐ v12 OK (granularidad aceptable) · ☐ corregir (aclarar): ____________________

---

## 3. La pregunta de las nominalizaciones escuetas del oficio

En la muestra fresca del gate 2 aparecieron 3 avisos donde el sistema nuevo (v12) devolvió **cero tareas**, pero el sistema viejo (v11) sí tenía las tareas del oficio. Los tres comparten forma: **el oficio se describe con nominalizaciones cortas, sin verbo** («Manejo de chasis», «Instalación de tendidos eléctricos», «Reposición de mercadería»). La regla estricta de atribución de v12 —la misma que logra descartar los requisitos disfrazados de tarea— parece estar comiéndose también estas nominalizaciones que **sí son la tarea nuclear** del puesto.

### Ejemplos (texto real del aviso)

**Chofer de camiones (id 1117212619, bumeran)** — el aviso lista: «Manejo de Chasis de 8 pallets; Manejo de Chasis de 12 pallets; Manejo de Balancines y/o Semis; Control de la mercadería despachada y recibida; Manejo de Remitos».
- v12 extrajo: **(ninguna)**

**Electricista/Montador/Herrero (id 2184455, zonajobs)** — el aviso lista por puesto: «Instalación de tendidos eléctricos en automotores; Laminación y pulido de PRFV; Fabricación y reparación de piezas en fibra…».
- v12 extrajo: **(ninguna)**

**Atención de mostrador (id 7853619060, portalempleo)** — «Tareas principales: tareas de depósito, embalaje, carga y descarga de mercadería. Reposición de mercadería, atención al público, limpieza…».
- v12 extrajo: **(ninguna)**

**La pregunta:** cuando el oficio viene como nominalización escueta sin verbo («Manejo de X», «Instalación de Y», «Reposición de Z»), ¿debe extraerse como tarea (manejar X, instalar Y, reponer Z)? El riesgo del otro lado: «Manejo de Excel», «Manejo de AutoCAD» son requisitos, no tareas (los marcaste así en los casos 11, 15, 26). ¿Cómo distinguís "manejo de [vehículo/herramienta del oficio]" (tarea) de "manejo de [software/skill]" (requisito)?

> Tu criterio: _____________________________________________________________________

**Caso-frontera (id 8802322877, "Ejecutivo de ventas en calle"):** el aviso arranca con «…buscamos incorporar un/a Ejecutivo de ventas en calle para desarrollar y potenciar nuestra cartera de clientes…». ¿«desarrollar y potenciar la cartera», dicho en el párrafo de presentación, es una tarea atribuida o es pitch? v12 lo tomó como pitch y devolvió cero.

> Tu criterio: ☐ es tarea · ☐ es pitch, no cuenta · ☐ depende: __________________
