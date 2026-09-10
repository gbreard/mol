# Validación de extracción de TAREAS — muestra para Cyn (2026-08-25)

**Qué es esto.** El sistema (NLP) lee cada aviso y separa las **tareas** del puesto. Detectamos que a veces falla: pierde tareas que estaban, o mete como tarea cosas que no lo son. Antes de tocar nada, necesitamos tu ojo sobre casos concretos.

## La definición de "tarea" que estamos usando (tu visto o corrección)

**TAREA** = una acción productiva que hace la persona en el puesto: **verbo + objeto + (dónde/con qué, cuando el aviso lo dice)**.
Ejemplos: *"Registrar asientos contables en SAP"*, *"Visitar clientes de la zona oeste"*, *"Supervisar el equipo de depósito"*.

**NO son tareas** (aunque el aviso las liste):
- **Requisitos del candidato** — lo que la persona debe *tener o ser*: *"experiencia de 2 años"*, *"secundario completo"*, *"estudiante avanzado de..."*, *"disponibilidad full time"*.
- **Beneficios / condiciones** — *"obra social"*, *"horario rotativo"*, *"sueldo + comisiones"*.
- **Skills sueltos** — *"Excel avanzado"* (solo es tarea si viene como acción: *"armar reportes en Excel"*).
- **Frases de la empresa sobre sí misma** — *"somos líderes en..."*.

> **Cyn: ¿esta definición te cierra?** Si la ajustarías (agregar/sacar algo, o un matiz argentino), escribilo acá — tu ajuste manda sobre cómo rediseñamos el sistema:
>
> _____________________________________________________________________

## Cómo marcar cada caso

Para cada aviso te mostramos: el **cuerpo del aviso** y las **tareas que extrajo el sistema**. Completá las 3 columnas:
- **¿Falta alguna tarea?** — ¿el aviso decía una tarea que el sistema no puso? ¿cuál?
- **¿Alguna sobra?** — ¿el sistema puso como "tarea" algo que en realidad es requisito / beneficio / skill / inventado?
- **Veredicto** — **OK** (bien extraído) o **FALLA** (le falta o le sobra).

Son 28 casos, elegidos para cubrir los distintos tipos de error que vimos (y algunos correctos, a propósito, para calibrar).


---

### Caso 1 — id `1118165658` · bumeran
**Título:** Analista de Créditos y Cobranzas

**Descripción (cuerpo del aviso):**
> Importante empresa metalúrgica se encuentra en la búsqueda de un/a Analista de Créditos y Cobranzas para sumarse a su equipo de trabajo. Zona Burzaco.Principales responsabilidades: Análisis y evaluación de riesgo crediticio para el otorgamiento de líneas de crédito a clientes. Seguimiento de pedidos y coordinación con el área comercial para su correcta entrega y cobranzas. Control y seguimiento de cuentas corrientes comerciales. Gestión integral de facturación. Seguimiento de cobranzas y control de vencimientos. Elaboración de reportes de crédito, facturación y morosidad. Trabajo coordinado con las áreas Comercial, Administración y Finanzas.Requisitos: Experiencia mínima de 2 años en análisis crediticio, facturación y cobranzas comerciales. (excluyente). Conocimiento en evaluación de riesgo crediticio (excluyente). Conocimientos sólidos en facturación electrónica y gestión de cuentas corrientes. Manejo de Excel y sistemas de gestión. Perfil analítico, organizado y con buenas habilidades de comunicación.Se valorará: Experiencia en empresas industriales o PyME. Capacidad de negociación y orientación a resultados.Modalidad: Lunes a viernes de 8:00 a 17:00 hs – presencial.

**Tareas que extrajo el sistema (1):**
- Análisis y evaluación de riesgo crediticio para el otorgamiento de líneas de crédito a clientes

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **a** — "Principales responsabilidades" lista 7 tareas; se extrajo 1_</sub>


---

### Caso 2 — id `5790086984` · computrabajo
**Título:** Ref. 21263: Analista QA Semi Sr / Híbrido CABA Centro

**Descripción (cuerpo del aviso):**
> Descripción: En ADN – Recursos Humanos estamos en la búsqueda de Analista QA Semi Sr / Híbrido CABA Centro para Importante Empresa.Requerimientos:-Al menos dos años consecutivos del último periodo ejerciendo funciones de Analista QA.-Conocimientos en  Bases de datos, especialmente en manejo de SQL para validación de datos y troubleshooting (Excluyente)Tareas a desarrollar:-Estrategia y planificación: Diseñar, planificar y ejecutar estrategias integrales de testing.-Documentación: Crear y mantener casos de prueba, planes de testing y documentación técnica detallada.-Gestión de defectos: Identificar, reportar y dar seguimiento a los bugs hasta su resolución.-Calidad integral: Asegurar que el producto cumpla con los requisitos funcionales y no funcionales (performance, seguridad y usabilidad).-Coordinación y trabajo en equipo: Participar de las ceremonias ágiles y articular activamente con desarrolladores, BAs y otros stakeholders.-Mirada de negocio: Aportar análisis crítico sobre los requerimientos y actuar como nexo entre los equipos técnicos y los clientes.Características:-Autonomía proactiva: Iniciativa para investigar causas raíz y proponer soluciones frente a bloqueos.-Pensamien

**Tareas que extrajo el sistema (2):**
- Asegurar que el producto cumpla con los requisitos funcionales y no funcionales (performance
- seguridad y usabilidad)

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **a** — "Tareas a desarrollar:" 6 tareas con encabezado; se extrajo 1 fragmento_</sub>


---

### Caso 3 — id `1118392033` · bumeran
**Título:** Repartidor de agua y soda con registro para camión

**Descripción (cuerpo del aviso):**
> Repartidor de MercaderíaResumen del PuestoEstamos en la búsqueda de un Repartidor de Mercadería para incorporarse a nuestro equipo de trabajo. Buscamos una persona responsable, puntual, con buena predisposición y compromiso.Responsabilidades Carga, descarga y reparto de mercadería a clientes. Brindar una atención cordial a los clientes. Cuidar el vehículo y la mercadería asignada.Requisitos Registro de conducir habilitante para camión. Experiencia comprobable en manejo de camiones. Excelentes habilidades de comunicación y trato interpersonal. Capacidad para trabajar de forma autónoma y organizada.

**Tareas que extrajo el sistema (2):**
- Brindar una atención cordial a los clientes
- Cuidar el vehículo y la mercadería asignada

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — perdió la tarea nuclear "Carga, descarga y reparto de mercadería"_</sub>


---

### Caso 4 — id `2176458` · zonajobs
**Título:** OFICIAL MUTIPLE SUPERIOR CENTRO CNC FAGOR - ZONA OESTE

**Descripción (cuerpo del aviso):**
> Nos encontramos en la búsqueda de un oficial CENTRO DE MECANIZADO CNC con experiencia comprobable en manejo de tolerancias y programación a pie de maquina con sistema FAGOR.Probada experiencia en tornería de precisión, acabados y terminación a la centésima de milímetro, roscado y demás operaciones en centro de mecanizado CNC- Muy buen manejo de instrumentos de medición: micrómetro, alesómetro, comparadores centesimales y milesimales, etc.- Muy buenos conocimientos de mecánica, neumática e hidráulica.- Experiencia en soldadura, no excluyente.- Interpretación de planos mecánicos, excluyente.- Título de técnico mecánico o equivalente (no excluyente).- Residencia en zona oeste preferentemente.DESCRIPCION DE TAREAS: Mecanizar en maquinas CNC con programacion a pie de maquina de sistema FAGOR Uso y mantenimiento de herramientas de medicion, calibre, micrometro, alesometro etc. Ejecutar las órdenes de trabajo Controlar la entrada y salida al taller de materiales y equipos de trabajo, utilizados en la ejecución de las tareas Llevar registro y control de los trabajos realizados y/o a realizar en el taller. Mantener en orden equipo y sitio de trabajo, reportando cualquier anomalía. Cumplir l

**Tareas que extrajo el sistema (5):**
- Uso y mantenimiento de herramientas de medición
- Ejecutar las órdenes de trabajo
- Controlar la entrada y salida al taller de materiales y equipos de trabajo
- Llevar registro y control de los trabajos realizados y/o a realizar en el taller
- Cumplir las normas y procedimientos en materia de seguridad integral

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — control limpio: perdió "Mecanizar en CNC con FAGOR" (define el puesto)_</sub>


---

### Caso 5 — id `1117972807` · bumeran
**Título:** Adm contable - ESTUDIO CONTABLE

**Descripción (cuerpo del aviso):**
> Importante Estudio Contable ubicado en Palermo, se encuentra en la búsqueda de:Administrativa ContableDeberá realizar las siguientes tareas:- Colaborar con la liquidación de sueldos- Tareas de Contabilidad general- Tareas generales de oficinaRequisitos:-Estudiante de la carrera de Contador Público (no excluyente)-Experiencia en la posición al menos 2 años (excluyente)Son un plus:- Experiencia en estudio contable*Nos orientamos a una persona de carácter proactivo, responsable y comprometida.Jornada laboral: Lunes a viernes 08 a 1 7 hsZona: Palermo, BSASSe ofrecen excelentes condiciones laborales y posibilidad de desarrollo profesional!

**Tareas que extrajo el sistema (2):**
- Tareas de Contabilidad general
- Tareas generales de oficina

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — perdió la concreta "Colaborar con liquidación de sueldos"_</sub>


---

### Caso 6 — id `1118316198` · bumeran
**Título:** Analista de Marketing Digital

**Descripción (cuerpo del aviso):**
> En bplay, somos pioneros en la industria del juego online en Argentina. Desde nuestro lanzamiento en noviembre de 2020, trabajamos día a día para brindar una experiencia de entretenimiento segura, innovadora y con fuerte impronta local.Nuestra cultura está impulsada por la pasión con la que vivimos el deporte y las apuestas, la cercanía con nuestra comunidad y un fuerte compromiso con la integridad, la seguridad y la responsabilidad. Creemos en el juego como una experiencia divertida y auténtica, por eso priorizamos siempre el entretenimiento responsable (+18) y el desarrollo de nuevas tecnologías que potencien la experiencia del usuario.Somos un equipo que valora la diversión, promueve la autenticidad argentina y apuesta a la innovación constante. Si te motiva formar parte de un entorno dinámico, en crecimiento y con impacto real, este es tu lugar.¡Entrá a la cancha a jugar!Sumate al #Equipobplay ¡Sumate al equipo de Performance de bplay!Serás responsable de planificar, ejecutar y optimizar la estrategia de performance digital de bplay, impulsando la adquisición de usuarios, el análisis de resultados y la identificación de oportunidades de mejora para potenciar el crecimiento del 

**Tareas que extrajo el sistema (2):**
- Monitorear y analizar indicadores clave como CPA, ROAS, conversión, retención y calidad de tráfico
- Identificar oportunidades de mejora a partir del análisis de datos y comportamiento de usuarios

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — "tareas fundamentales" 6; extrajo 2, perdió "Planificar/ejecutar campañas"_</sub>


---

### Caso 7 — id `2176705` · zonajobs
**Título:** Software Engineer .NET (con exp WPF) - Mix (Onsite - Remoto) - 1802

**Descripción (cuerpo del aviso):**
> ¿Qué hace la compañía?Empresa de tecnología con fuerte presencia internacional, especializada en el desarrollo de software y soluciones digitales para grandes organizaciones. Se destaca por trabajar en proyectos de alta complejidad técnica, con foco en calidad, innovación y buenas prácticas de ingeniería.¿Qué necesitás para ser parte del equipo?A nivel personal: Buscamos personas con perfil senior, autonomía y capacidad de liderazgo técnico. Pensamiento analítico y creativo para resolver problemas complejos Capacidad para trabajar en equipo, buenas habilidades de comunicación y trabajo colaborativo. Compromiso con la calidad, la diversidad y la mejora continua.A nivel técnico: Amplia experiencia práctica en desarrollo de software utilizando C# / .NET. Sólida experiencia en desarrollo de interfaces de usuario frontend, incluyendo WPF y tecnologías web modernas como React, Angular y TypeScript. Fuerte comprensión de diseño de sistemas, desarrollo, testing y estabilidad operativa. Conocimiento y experiencia en metodologías ágiles, prácticas de CI/CD, resiliencia de aplicaciones y seguridad. Experiencia trabajando en arquitecturas cloud-native. Conocimiento del dominio de Capital Marke

**Tareas que extrajo el sistema (2):**
- Contribuir al desarrollo de código productivo y participar activamente en revisiones de código dentro del equipo
- Identificar y ejecutar oportunidades de automatización para reducir incidentes recurrentes y mejorar la estabilidad operativa

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — "¿Qué vas a hacer?" 7; extrajo 2_</sub>


---

### Caso 8 — id `6477274334` · computrabajo
**Título:** Promotor/a

**Descripción (cuerpo del aviso):**
> Promotores Local gastronómico ubicado en Puerto Madero, está buscando promotores entusiastas y profesionales, con habilidades excepcionales de atención al cliente. Excelente presencia y herramientas de comunicación. Excluyente: 2 años de experiencia en ventas o atención al cliente. Se valorará la orientación al servicio, la excelencia en el trato al cliente, el dinamismo, la actitud carismática, la iniciativa y la buena presencia. Buscamos personal con compromiso y responsabilidad. Serán requisitos para cubrir la vacante: *Disponibilidad para trabajar fines de semana. -Requerimientos- Educación mínima: Secundaria 2 años de experiencia Edad: entre 23 y 28 años

**Tareas que extrajo el sistema (2):**
- Atención al cliente
- Disponibilidad para trabajar fines de semana

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **b** — extrajo "Atención al cliente" y "Disponibilidad fin de semana" (requisitos)_</sub>


---

### Caso 9 — id `1118058753` · bumeran
**Título:** Analista de RRHH Generalista (Movilidad propia-Zona Norte)

**Descripción (cuerpo del aviso):**
> Para empresa ubicada en Pillar requerimos profesional graduado de RRHH, RRLL o Lic en administración de empresas. Apuntamos a un profesional con sólida experiencia en Selección y Administración de personal en empresas con alto volumen de dotación .Quienes apliquen requerirán residir en zona y poseer movilidad propia (Auto /Moto). La empresa realiza reintegros de gastos.Requerimos: Profesional Graduado Al menos 5 años de experiencia en posición similar Disponibilidad para trabajar presencial Residir en zona aledaña Contar con Movilidad PropiaBeneficios: Prepaga 21 días de Vacaciones DescuentosCompletan el perfil excelentes habilidades de comunicación, capacidad para trabajar en equipo y muy buenas relaciones interpersonales. Apuntamos a un profesional expeditivo, autónomo y proactivo.Si la propuesta es de tu interés, aguardamos tu postulación. Equipo Hucap

**Tareas que extrajo el sistema (2):**
- Realizar selección y administración de personal
- Disponibilidad para trabajar presencial

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **b** — extrajo "Disponibilidad para trabajar presencial" (condición) como tarea_</sub>


---

### Caso 10 — id `6265862938` · computrabajo
**Título:** Vendedora para Panadería Turno Tarde

**Descripción (cuerpo del aviso):**
> Empresa gastronómica ubicada en la Zona Sur de Rosario se encuentra en la búsqueda de Vendedoras de mostrador para realizar turno tarde. Son Requisitos: -Experiencia mínima de dos años en atención al público -Secundario completo -Sexo Femenino -Disponibilidad horaria para trabajar de lunes a lunes con un franco durante la semana -Proactividad y simpatía  Se ofrecen: -Remuneración acorde a la función -Estabilidad laboral -Muy buen clima de trabajo -Capacitación constante

**Tareas que extrajo el sistema (1):**
- Atención al público

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **b** — "Atención al público" salió de la línea de Requisitos_</sub>


---

### Caso 11 — id `6171358600` · computrabajo
**Título:** Dibujante proyectista

**Descripción (cuerpo del aviso):**
> Constructora líder incorpora Dibujante Proyectista para instalaciones sanitarias, de gas e incendio.Sera requisito excluyente poseer amplio manejo de AutoCAD.Profesional o Estudiante Avanzado Arq / Ing.Horario: 08 a 17.00 horas.ZONA SUR.

**Tareas que extrajo el sistema (2):**
- realizar dibujos y planos
- manejar AutoCAD

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **d** — extrajo "realizar dibujos y planos": NO aparece en el aviso (inferido del título)_</sub>


---

### Caso 12 — id `2185030` · zonajobs
**Título:** Ejecutivo/a de Ventas Posadas

**Descripción (cuerpo del aviso):**
> Somos una institución prestadora de servicios de salud, con 40 años de trayectoria y experiencia en la administración de aportes y contribuciones de obra social del personal de dirección de empresas. Conocemos cuáles son tus necesidades, por eso nos orientamos a brindar cobertura médica a nivel nacional por medio de las redes prestadoras más importantes del país. Somos una obra social sólida y dinámica que prioriza el bienestar de 350.000 afiliados que confían en nosotros. ¡El match que buscamos podes ser vos! En Medifé trabajamos para brindar un servicio de calidad, cuidar a quienes nos rodean y marcar la diferencia con soluciones de impacto.Creemos en el compromiso, la eficiencia y el trabajo colaborativo como pilares fundamentales de nuestro propósito. Por eso buscamos sumar a una persona apasionada por la venta consultiva, motivada por los desafíos y orientada a generar valor a través de una gestión comercial de alto impacto.Si te entusiasma construir relaciones, trabajar por objetivos y desarrollar oportunidades comerciales desde cero, este rol es ideal para vos.¿Cuál es el desafío?Como Ejecutivo/a de Ventas, tu misión será captar nuevos asociados, comercializando nuestros pla

**Tareas que extrajo el sistema (2):**
- Prospección activa presencial y/o digital de nuevos clientes individuales y corporativos
- gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **a** — "Principales responsabilidades" 4; extrajo 1er bullet partido en 2 fragmentos_</sub>


---

### Caso 13 — id `5273316732` · computrabajo
**Título:** ¡Representante de Venta de Préstamos!

**Descripción (cuerpo del aviso):**
> ¡Sumate a CAT-Technologies como Telemarketer!Si te apasionan las ventas, los desafíos y querés crecer en un equipo dinámico y profesional, esta oportunidad es para vos. En CAT-Technologies, el Contact Center líder de Argentina, buscamos Telemarketers con experiencia en ventas para seguir expandiendo nuestro equipo.¿Quiénes somos?Somos el Contact Center de capitales nacionales más importante de Argentina, con más de 3.000 colaboradores y 3 centros operativos en CABA y La Punta, San Luis. Nos especializamos en la comercialización de productos intangibles y cobranzas para empresas líderes en Entretenimiento, Banca, Telecomunicaciones y más.¿Cuál será tu misión?Ofrecer productos bancarios, ayudando a mejorar la experiencia del clienteComunicarte de manera clara, efectiva y persuasiva para generar ventas.¿Qué buscamos en vos?Actitud comercial y ganas de superarte.Experiencia en ventas de Préstamos.Secundario completo (excluyente).Disponibilidad de lunes a viernes de 11 a 17 hs  Modalidad PRESENCIAL.¿Qué te ofrecemos?Sueldo básico + comisiones sin tope.Capacitación continua a cargo de la empresa.Plan de carrera en un entorno dinámico y colaborativo.Jornada part-time, ideal para equilibra

**Tareas que extrajo el sistema (1):**
- Ofrecer productos bancarios

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — "¿Cuál será tu misión?" 2; perdió "Comunicarte para generar ventas"_</sub>


---

### Caso 14 — id `5917821361` · computrabajo
**Título:** promotores Sala y Vía Publica

**Descripción (cuerpo del aviso):**
> ¡Súmate al equipo de Atención al Cliente de importante empresa de entretenimiento!Buscamos perfiles dinámicos, con excelente dicción y marcada vocación de servicio para ser la cara visible de nuestra sala. Tu rol será clave para atraer, fidelizar y brindar una experiencia única a nuestros clientes, tanto en el salón como en acciones de vía pública.¿Qué ofrecemos?Estabilidad: Contratación inmediata en relación de dependencia.Salud y Bienestar: Obra social incluida.Crecimiento: Plan de carrera y oportunidades reales de desarrollo interno.Beneficios Extra: Premios por desempeño, capacitaciones constantes,  y regalo de cumpleaños.Tus principales funciones:Brindar atención cordial, eficiente y resolutiva a los clientes en sala y vía pública.Promocionar los servicios, eventos y beneficios del Bingo.Garantizar una experiencia satisfactoria y segura bajo los protocolos de servicio.Colaborar en acciones de marketing y fidelización de clientes.¿Qué buscamos?Perfil: Personas proactivas, con excelente presencia y habilidades comunicativas.Experiencia: Valoramos perfiles con experiencia en promociones, ventas, recepciones o atención al público (Deseable).Disponibilidad: Capacidad para trabajar 

**Tareas que extrajo el sistema (2):**
- Garantizar una experiencia satisfactoria y segura bajo los protocolos de servicio
- Colaborar en acciones de marketing y fidelización de clientes

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — "Tus principales funciones" 4; perdió "Brindar atención cordial"_</sub>


---

### Caso 15 — id `5650193558` · computrabajo
**Título:** Personal de maestranza. Lugar de trabajo: Garin, Munro y Parque Saavedra

**Descripción (cuerpo del aviso):**
> Nos encontramos en búsqueda de personal de limpieza, con compromiso y ganas de trabajar , con experiencia en tareas similares (limpieza de oficinas, casas, sanatorios, etc). Zonas de trabajo: Parque industrial de Garin, Parque Saavedra y Munro Vacantes disponibles en turno mañana, tarde y noche.  REQUISITOS: * Manejo de maquinas de limpieza

**Tareas que extrajo el sistema (1):**
- Manejo de maquinas de limpieza

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **b** — extrajo "Manejo de máquinas" (requisito); tarea real "limpieza de oficinas" afuera_</sub>


---

### Caso 16 — id `2176546` · zonajobs
**Título:** Enfermera Extraccionista

**Descripción (cuerpo del aviso):**
> Enfermera Extraccionista Resumen del Puesto Buscamos una Enfermera Extraccionista con experiencia para unirse a nuestro equipo. El candidato ideal será responsable, con buena predisposición y orientación al paciente, y poseerá experiencia específica en la aplicación de plasma rico en plaquetas (PRP) y sueros vitamínicos. Responsabilidades Realizar extracciones de sangre para la obtención de plasma rico en plaquetas (PRP). Administrar sueros vitamínicos según protocolos establecidos. Brindar atención y orientación a los pacientes durante los procedimientos. Mantener un ambiente de trabajo seguro y estéril. Colaborar con el equipo para asegurar la calidad del servicio. Requisitos Título de Enfermería. Experiencia comprobable en extracciones para PRP y administración de sueros vitamínicos. Habilidades de comunicación y trato interpersonal. Capacidad para trabajar de forma autónoma y en equipo. Responsabilidad y atención al detalle.

**Tareas que extrajo el sistema (5):**
- Realizar extracciones de sangre para la obtención de plasma rico en plaquetas (PRP)
- Administrar sueros vitamínicos según protocolos establecidos
- Brindar atención y orientación a los pacientes durante los procedimientos
- Mantener un ambiente de trabajo seguro y estéril
- Colaborar con el equipo para asegurar la calidad del servicio

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **f** — 5 responsabilidades, las 5 extraídas fielmente_</sub>


---

### Caso 17 — id `2169530` · zonajobs
**Título:** Técnico Mecánico para flota Vehicular pesada. Ciudadela

**Descripción (cuerpo del aviso):**
> Nos encargamos del proceso de búsqueda, selección y contratación de personal técnico para fabricas y empresas de ingeniería. Realizamos procesos de evaluación técnica de acuerdo a las necesidades del puesto a cubrir. Cubrimos posiciones para diferentes niveles en áreas de Producción, Mantenimiento, Calidad, Operaciones, Procesos, ingeniería, Supply Chain, Customer Service, Logística, Seguridad & Higiene, Compras y Ventas Técnicas. ¡Estamos buscando un Técnico Mecánico para sumarse a un equipo en constante crecimiento!Empresa versátil y sólida en obras de Infraestructura y Civiles, así como en servicios de mantenimiento de redes e instalaciones electromecánicas, con más de 20 años de trayectoria en el mercado. Ubicación: Ciudadela, Provincia de Buenos Aires Modalidad: Presencial | Lunes a Viernes de 8 a 17 hs. Sabados de 7 a 12 hsTu misión será realizar el mantenimiento preventivo y correctivo de una flota vehicular, incluyendo máquinas viales, camiones y utilitarios. Principales tareas: Reparación de maquinarias pesadas, camiones y utilitarios. Diagnóstico y resolución de fallas mecánicas en sistemas hidráulicos y neumáticos. Reparaciones generales y trabajos de soldadura. Perfil b

**Tareas que extrajo el sistema (3):**
- Reparación de maquinarias pesadas
- Diagnóstico y resolución de fallas mecánicas en sistemas hidráulicos y neumáticos
- Reparaciones generales y trabajos de soldadura

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **f** — "Principales tareas" 3; las 3 extraídas_</sub>


---

### Caso 18 — id `2168972` · zonajobs
**Título:** Abogado/a - Derecho Laboral

**Descripción (cuerpo del aviso):**
> Abogado/a - Derecho LaboralResumen del PuestoEstamos buscando un/a Abogado/a para unirse a nuestro equipo en el área de derecho laboral. Buscamos una persona con ganas de aprender, crecer y formar parte de un equipo joven, dinámico y con un excelente clima de trabajo.Responsabilidades Asistir a audiencias. Realizar el seguimiento de la cartera de clientes. Trabajar en conjunto con un equipo comprometido y en constante crecimiento.Requisitos Ser Abogado/a con título habilitante. (excluyente) Contar con matrícula profesional. No ejercer en forma particular. Experiencia en atención al cliente o trato con personas (deseable). Disponibilidad full time. Enviar remuneracion pretendida (excluyente)

**Tareas que extrajo el sistema (3):**
- Asistir a audiencias
- Realizar el seguimiento de la cartera de clientes
- Trabajar en conjunto con un equipo comprometido y en constante crecimiento

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **f** — 3 responsabilidades, las 3 extraídas_</sub>


---

### Caso 19 — id `6097371222` · computrabajo
**Título:** Vendedor telefonico con experiencia

**Descripción (cuerpo del aviso):**
> ¡Sé parte del Call Center líder en ventas de Argentina! ¿Te apasionan las ventas y tenés un talento natural para lo comercial? ¡Esta es tu oportunidad! En VOICENTER, buscamos Vendedores Telefónicos ambiciosos, dinámicos y entusiastas para sumarse a nuestro equipo en constante crecimiento. ¿QUE BUSCAMOS EN VOS? Actitud comercial y resiliencia frente a los desafíos (excluyente). Experiencia mínima de 1 año en ventas con objetivos y comisiones (excluyente). Se valorará experiencia en ventas en frío. Excelentes habilidades de comunicación. Capacidad para manejar múltiples plataformas de gestión. Actitud positiva, autonomía y trabajo en equipo (excluyente). Secundario completo (excluyente). Disponibilidad para trabajar los sábados (excluyente). ¿QUÉ OFRECEMOS? Sueldo competitivo + atractivas comisiones. Jornada laboral de 30 horas semanales (100% presencial). Oportunidades de crecimiento y capacitación continua. Ambiente dinámico y colaborativo. Descuentos en instituciones educativas. Estabilidad laboral y excelentes condiciones de contratación.  ¡Súmate a este equipo ganador y desarrolla tu carrera en el Call Center número uno en ventas de Argentina!

**Tareas que extrajo el sistema (0):**
- _(ninguna)_

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **g** — cuerpo = "¿Qué buscamos?/¿Qué ofrecemos?"; sin enunciado de tareas_</sub>


---

### Caso 20 — id `2172514` · zonajobs
**Título:** Operario de Planta para Industria

**Descripción (cuerpo del aviso):**
> Operario de PlantaResumen del PuestoEstamos buscando un Operario de Planta para unirse a nuestro equipo de producción. Requisitos Sexo Masculino. Referencias de trabajos anteriores

**Tareas que extrajo el sistema (0):**
- _(ninguna)_

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **g** — solo requisitos (sexo, referencias); sin tareas_</sub>


---

### Caso 21 — id `5909299836` · computrabajo
**Título:** administración de ventas

**Descripción (cuerpo del aviso):**
> "¡Oportunidad laboral! Buscamos chicas con experiencia en administración de agencias de motos para unirse a nuestro equipo. Solo con experiencia comprobable. Requisitos: experiencia en gestión administrativa, conocimientos en ventas y servicio al cliente. Ofrecemos buen ambiente laboral y oportunidades de crecimiento. Envía tu CV

**Tareas que extrajo el sistema (0):**
- _(ninguna)_

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **g** — solo requisitos ("experiencia en gestión administrativa"); extrajo 0 (correcto)_</sub>


---

### Caso 22 — id `5160083235` · computrabajo
**Título:** Repositor Part Time  (req203252) Eventual

**Descripción (cuerpo del aviso):**
> ¡Tenemos una oportunidad para vos!  Nos encontramos en la búsqueda de personal para Repositor  Las principales tareas del puesto serán: Reponer los productos en góndolasRequisitos:   Experiencia previa en cargos similares (Excluyente)  Secundario completo  Lugar de trabajo: San Martin de los Andes-Neuquen  Modalidad de contratación: Eventual  En ManpowerGroup promovemos una cultura inclusiva y diversa basada en el respeto y en la igualdad de oportunidades.

**Tareas que extrajo el sistema (1):**
- Reponer los productos en góndolas

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **f** — cuerpo real = 1 tarea ("Reponer productos en góndolas"); extraída bien_</sub>


---

### Caso 23 — id `6483882943` · computrabajo
**Título:** Operario de carga y descarga

**Descripción (cuerpo del aviso):**
> BÚSQUEDA ACTIVA  OPERARIOS DE CARGA Y DESCARGA | ZONA LA TABLADA Buenos días  Nos encontramos en la búsqueda de operarios para tareas de carga y descarga para una empresa ubicada en La Tablada .  IMPORTANTE: Es un trabajo por convocatoria, lo que significa que te llamaremos según la necesidad de la empresa. Si bien suelen convocar varios días por semana, sigue siendo una modalidad eventual.  Horario: de 07:00 a 16:00 hs  Pago: $4.937 bruto por hora + premio por presentismo  Tarea principal: Carga y descarga de mercadería Si te interesa, postulate!

**Tareas que extrajo el sistema (1):**
- carga y descarga de mercadería

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **f** — "Tarea principal: Carga y descarga" (única); extraída_</sub>


---

### Caso 24 — id `2187269` · zonajobs
**Título:** Ejecutivo/a de Ventas Rosario

**Descripción (cuerpo del aviso):**
> Somos una institución prestadora de servicios de salud, con 40 años de trayectoria y experiencia en la administración de aportes y contribuciones de obra social del personal de dirección de empresas. Conocemos cuáles son tus necesidades, por eso nos orientamos a brindar cobertura médica a nivel nacional por medio de las redes prestadoras más importantes del país. Somos una obra social sólida y dinámica que prioriza el bienestar de 350.000 afiliados que confían en nosotros. ¡El match que buscamos podes ser vos! En Medifé trabajamos para brindar un servicio de calidad, cuidar a quienes nos rodean y marcar la diferencia con soluciones de impacto.Creemos en el compromiso, la eficiencia y el trabajo colaborativo como pilares fundamentales de nuestro propósito. Por eso buscamos sumar a una persona apasionada por la venta consultiva, motivada por los desafíos y orientada a generar valor a través de una gestión comercial de alto impacto.Si te entusiasma construir relaciones, trabajar por objetivos y desarrollar oportunidades comerciales desde cero, este rol es ideal para vos.¿Cuál es el desafío?Como Ejecutivo/a de Ventas, tu misión será captar nuevos asociados, comercializando nuestros pla

**Tareas que extrajo el sistema (2):**
- Prospección activa presencial y/o digital de nuevos clientes individuales y corporativos
- gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **a** — separador ; partió el único bullet extraído en 2 fragmentos_</sub>


---

### Caso 25 — id `1118076732` · bumeran
**Título:** Abogado/a Semi Senior Banking

**Descripción (cuerpo del aviso):**
> Marval O’Farrell Mairal es el estudio jurídico líder en el país con reconocimiento a nivel mundial, asesorando hace más de 100 años a empresas multinacionales e instituciones internacionales, en asuntos de alto grado de exigencia y complejidad. Buscamos construir un lugar de trabajo de excelencia, innovador, con programas de eficiencia y prácticas que fomentan al equilibrio y bienestar de nuestros profesionales. Marval O’Farrell Mairal es el estudio jurídico líder en el país con reconocimiento a nivel mundial, asesorando hace más de 100 años a empresas multinacionales e instituciones internacionales. Buscamos construir un lugar de trabajo de excelencia, que sea innovador, con programas de eficiencia y prácticas que fomenten al equilibrio y bienestar de nuestros profesionales.Nos encontramos en la búsqueda de un/a Abogado/a para formar parte de nuestro equipo de Bancos y Finanzas. Requisitos: Estudios universitarios en Abogacía finalizados. Será un plus contar con Posgrados de especialización y/o Maestría Experiencia profesional mínima de 3 años en el área, con participación en asesoramiento financiero, en normativa y procesos de prevención de lavado de activos. Inglés avanzado/bili

**Tareas que extrajo el sistema (2):**
- asesoramiento financiero
- normativa y procesos de prevención de lavado de activos

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **b** — "asesoramiento financiero" sale de línea "Experiencia en..." (requisito)_</sub>


---

### Caso 26 — id `2181056` · zonajobs
**Título:** Secretaria Administrativa Escribania

**Descripción (cuerpo del aviso):**
> BÚSQUEDA LABORAL – ESCRIBANÍANos encontramos en la búsqueda del puesto de Secretaria Administrativa, para sumarse al equipo de trabajo de importante Escribanía, ubicada en la ciudad de Santa Rosa, La Pampa.Modalidad: presencial – full timeRequisitos:- Conocimiento en redacción de escrituras y manejo de protocolo- Perfil ordenado, metódico y responsable- Buen trato y predisposición para el trabajo en equipoSe valorará:- Experiencia previa- Atención al detalle y prolijidad en la tarea- Interés en desarrollarse y consolidarse profesionalmente en el ámbito notarial: Estudiantes o graduados de la carrera de Abogacía.Esperamos tu postulación!!

**Tareas que extrajo el sistema (1):**
- Manejo de protocolo

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **b** — "Manejo de protocolo" sale de línea de Requisitos_</sub>


---

### Caso 27 — id `1118300373` · bumeran
**Título:** Ginecóloga/o - Medicina Regenerativa y Estética

**Descripción (cuerpo del aviso):**
> Ginecóloga/o - Medicina Regenerativa y Estética Resumen del Puesto Buscamos incorporar una Ginecóloga/o con interés en medicina regenerativa y estética ginecológica para unirse a nuestro equipo. El candidato ideal tendrá pasión por la innovación y el bienestar femenino, buscando un espacio de excelencia y crecimiento profesional. Responsabilidades Aplicar tratamientos de medicina regenerativa y estética ginecológica. Valoraremos experiencia en rejuvenecimiento vaginal con Láser, colocación de pellets/chip de testosterona, PRP vaginal y tratamientos regenerativos íntimos femeninos. Participar en la formación y capacitación en protocolos exclusivos. Brindar atención profesional, cálida y empática a las pacientes. Contribuir a un ambiente de excelencia e innovación en medicina estética. Requisitos Título de Ginecóloga/o. Interés y/o experiencia en medicina regenerativa y estética ginecológica. Se valorará experiencia específica en las técnicas mencionadas. Perfil profesional, cálido y empático. Orientación al crecimiento profesional y al bienestar femenino. Capacidad para trabajar en un equipo enfocado en la vanguardia médica.

**Tareas que extrajo el sistema (2):**
- Aplicar tratamientos de medicina regenerativa y estética ginecológica
- Participar en la formación y capacitación en protocolos exclusivos

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — "Responsabilidades" 4; extrajo 2, perdió "Brindar atención profesional"_</sub>


---

### Caso 28 — id `2176620` · zonajobs
**Título:** Ingeniero Scada - Importante Petrolera (Neuquén)

**Descripción (cuerpo del aviso):**
> Buscamos para trabajar en relación de dependencia directa con una Importante Petrolera un Ingeniero Scada. La Compañía, con gran presencia en Vaca Muerta, se encuentra en un fuerte proceso de crecimiento e incorporación de tecnología de última generación para los Nuevos Proyectos.En este caso, puede ser una persona que resida en Argentina y le interese relocación en Neuquén.Ofrecen: Bono, OSDE 310 o Swiss Medical Familiar, Semana adicional de Vacaciones, Políticas de Relocación (para residentes fuera de Neuquén), Reintegro de gastos por Conectividad, Actividades Físicas, entre otros y la oportunidad de hacer Carrera en una Empresa con muy fuerte crecimiento.Tareas: Desarrollar, configurar y mantener pantallas HMI en Fast Tools (Yokogawa) para sistemas SCADA de producción y facilities. Programar y configurar gráficos de proceso, tendencias y alarmas en DeltaV Operate para plantas de tratamiento y baterías de producción. Diseñar arquitecturas de visualización SCADA integradas, asegurando consistencia entre sistemas Fast Tools y DeltaV Implementar estándares de HMI según ISA-101 y guías de alto rendimiento (High Performance HMI) Coordinar con Operaciones para definir requerimientos de

**Tareas que extrajo el sistema (4):**
- Desarrollar, configurar y mantener pantallas HMI en Fast Tools (Yokogawa) para sistemas SCADA de producción y facilities
- Implementar estándares de HMI según ISA-101 y guías de alto rendimiento (High Performance HMI)
- Coordinar con Operaciones para definir requerimientos de visualización y optimizar interfaces de operador
- Elaborar documentación técnica de pantallas SCADA (especificaciones funcionales, narrativas de operación, manuales de usuario)

**Para Cyn:**

| ¿Falta alguna tarea? ¿cuál? | ¿Alguna sobra? ¿por qué (requisito/beneficio/skill/inventada)? | ¿Veredicto? (OK / FALLA) |
|---|---|---|
|  |  |  |

<sub>_(referencia interna, ocultar a Cyn): pre-clasificación Claude = tipo **e** — "Tareas" 7; extrajo 4, perdió "Programar DeltaV/Diseñar arquitecturas"_</sub>
