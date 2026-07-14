# Taxonomía de contexto ocupacional argentina — escrita por Cyn (ACTIVO Eje 4) · **v2**

> **v2 — cosecha 2026-07-13.** Incorpora la sesión Gerardo+Cyn (`docs/Sesion_Cyn_familias.docx`,
> julio 2026) y el lote de construcción/instalaciones que Cyn trabajó por su cuenta
> (`docs/REGLAS-v2.xlsx`). **Regla de precedencia: donde ambos documentos tocan la misma
> familia, el Word manda** (es posterior y salió de la sesión). La v1 (6 familias,
> 2026-06-30, fuente `export_validacion_denominaciones_cyn_2026-06-24-v1.xlsx`) se conserva
> tal cual dentro de este archivo.
>
> **La prosa de Cyn es LA VERDAD de dominio: se cita textual, no se reescribe.**

**Esto NO se carga al diccionario plano.** Cada denominación-raíz va a códigos ESCO
distintos **según las tareas del aviso** — cargar una plana rompería las demás. Es la
**especificación experta de las reglas de contexto del Eje 4**: cuando se ataquen las
reglas/desambiguación por calificador, estos árboles son el insumo del traductor. Las
denominaciones ESTABLES (van siempre al mismo código) NO están acá: van al diccionario
por el circuito del puente (bandeja + dry-run + confirmación).

Formato por familia: **raíz** · árbol (prosa de Cyn textual) · casos de evidencia
(denominación → código, con lo que el matcher había dicho cuando hay registro) · fuente ·
estado (definida / pendiente-Cyn).

---

## GRUPO B — denominación con DOS códigos según contexto (v1, se conserva)

**'Sobrestante de obra'** apareció con dos targets según las tareas del aviso:

| si las tareas describen… | → código ESCO |
|---|---|
| dirección/coordinación de personal de obra | `3123.1.1` capataz de construcción |
| traslado/movimiento de materiales (operativo-logístico) | `8322.2` conductor de vehículo de reparto |

> Tercera oferta 'Sobrestante de obra / capataz' → `3123.1.1` (coordina personal) **sí**
> entró al GRUPO A: confirma la regla — dirección de personal ⇒ capataz; traslado de
> materiales ⇒ conductor. Esa es la regla de contexto implícita de Cyn.
> **v2:** ver además la familia «sobrestante» (REGLAS.xlsx) — el árbol completo, que
> agrega el default `3123.1` supervisor general de construcción.

---

# PARTE 1 — Familias v1 (2026-06-30, se conservan tal cual)

### Familia «operario» (16 denominaciones)

**Operario de deposito** → `9333.3 operario de logística de almacén`
*Regla:* recibe, almacena, prepara y expide mercadería ⇒ operario/a de logística de almacén; solo picking ⇒ responsable de pedidos de almacén; recibe/etiqueta/embala/controla ⇒ mozo/a de almacén; maneja autoelevador ⇒ operador/a de carretilla elevadora; solo carga/descarga ⇒ estibador/a; registra inventario ⇒ coordinador/a de inventario; solo embala ⇒ responsable de empaquetado manual; dirige el depósito y su personal ⇒ jefe/a de almacén.

**Operario de ensamble de armas** → `8219.8 montador de productos metálicos`
*Regla:* monta componentes en línea ⇒ montador/a de productos metálicos; modifica/fabrica/repara armas especializado ⇒ armero/a; ensambla cartuchos/proyectiles ⇒ montador/a de municiones; solo controla calidad ⇒ inspector/a de control de calidad de productos metálicos.

**Operario de mantenimiento para metalúrgica** → `7412.3 mecánico electricista`
*Regla:* repara componentes mecánicos y eléctricos ⇒ mecánico/a electricista; predomina mecánica ⇒ mecánico/a de maquinaria industrial; instalaciones y cableado ⇒ electricista industrial; predomina electrónica ⇒ ingeniero/a técnico/a en electrónica; electromecánica especializada ⇒ ingeniero/a técnico/a en electromecánica; sistemas automatizados/robóticos ⇒ ingeniero/a técnico/a de mecatrónica; supervisa mantenimiento y personal ⇒ supervisor/a de mantenimiento industrial.

**Operario de produccion** → `8160.34 operario de producción de alimentos`
*Regla:* etapas varias + maquinaria general en alimenticia ⇒ operario/a de producción de alimentos; elabora panes ⇒ panadero/a; tartas/galletas/pasteles ⇒ pastelero/a; solo hornos ⇒ hornero/a de panadería; mezcla aceites/margarinas ⇒ operario/a de instalaciones de mezclado; solo asiste/limpia/repone ⇒ trabajador/a de fábrica.

**Operario de producción (envasado de bebidas)** → `8183.7 operario de máquinas de embalaje y llenado`
*Regla:* opera máquinas de llenado/embalaje ⇒ operario/a de máquinas de embalaje y llenado; controla botellas/latas en cinta ⇒ operario/a de línea de envasado y embotellado; varias fases de bebidas ⇒ operario/a de producción de alimentos; envasa/etiqueta manual ⇒ responsable de empaquetado manual.

**Operario de producción con experiencia en línea** → `8160.34 operario de producción de alimentos`
*Regla:* opera y controla maquinaria ⇒ operario/a de producción de alimentos; solo ayuda/limpia/repone ⇒ trabajador/a de fábrica; solo envasa manual ⇒ responsable de empaquetado manual; repara maquinaria ⇒ mecánico/a de maquinaria industrial.

**Operario de producción metalúrgico** → `7223.4 operador de máquinas de control numérico`
*Regla:* programa/controla maquinaria computarizada + verifica parámetros ⇒ operador/a de máquinas de control numérico; solo ensambla según procedimientos ⇒ montador/a de productos metálicos; predomina soldadura ⇒ soldador/a; solo ayuda/limpia/repone ⇒ trabajador/a de fábrica; repara maquinaria ⇒ mecánico/a de maquinaria industrial.

**Operario especializado para depósito** → `9333.8.1 responsable de pedidos de almacén`
*Regla:* picking/preparación/armado de pedidos ⇒ responsable de pedidos de almacén; recepción+almacenamiento+picking+expedición ⇒ operario/a de logística de almacén; recibe/etiqueta/embala/controla ⇒ mozo/a de almacén; maneja autoelevador ⇒ operador/a de carretilla elevadora; solo embala manual ⇒ responsable de empaquetado manual; solo carga/descarga ⇒ estibador/a; registra inventarios ⇒ coordinador/a de inventario; fabrica/ayuda a operadores ⇒ trabajador/a de fábrica; dirige depósito y personal ⇒ jefe/a de almacén.

**Operario maquinista** → `8160.34 operario de producción de alimentos`
*Regla:* línea continua de varios productos ⇒ operario/a de producción de alimentos; equipos de leche/helados ⇒ operario/a de procesamiento de productos lácteos; elabora/controla chocolate ⇒ chocolatero/a; solo moldeo de chocolate ⇒ moldeador/a de chocolate; solo ayuda/limpia/repone ⇒ trabajador/a de fábrica; máquinas de envasado ⇒ operario/a de máquinas de embalaje y llenado; envasa manual ⇒ responsable de empaquetado manual.

**Operario pickeador** → `9333.8.1 responsable de pedidos de almacén`
*Regla:* selecciona mercadería y organiza pedidos ⇒ responsable de pedidos de almacén; recepción+almacenamiento+control+expedición ⇒ operario/a de logística de almacén; recibe/etiqueta/controla/almacena ⇒ mozo/a de almacén; solo carga/descarga ⇒ estibador/a; solo empaqueta/etiqueta manual ⇒ responsable de empaquetado manual; maneja autoelevador ⇒ operador/a de carretilla elevadora.

**Operario pintor sobre metal (metalúrgica)** → `7132.1 operador de pistola pulverizadora de lacado`
*Regla:* pulveriza pintura sobre piezas metálicas ⇒ operador/a de pistola pulverizadora de lacado; solo lija/prepara superficies ⇒ operario/a de preparación de superficies; solo protección anticorrosiva ⇒ operador/a de protección anticorrosiva; máquina automática de recubrimiento ⇒ operador/a de máquina recubridora de metales; recubre por inmersión ⇒ operador/a de máquinas recubridoras por inmersión; pinta vehículos ⇒ pintor/a de vehículos; pinta edificios ⇒ pintor/a de obra; solo ayuda/limpia ⇒ trabajador/a de fábrica.

**Operario senior de chapa y pintura** → `7231.2 carrocero/a`
*Regla:* repara/endereza carrocerías + prepara/pinta ⇒ carrocero/a; solo prepara/pinta vehículos ⇒ pintor/a de vehículos; ensambla carrocerías nuevas en línea ⇒ montador/a de carrocería de vehículos de motor; repara motores/mecánica interna ⇒ técnico/a de reparación de automóviles; chapas para techos/conductos/estructuras ⇒ chapista; solo ayuda/limpia taller ⇒ trabajador/a de fábrica.

**Operario SR — corte y costura** → `8153.1 operador de máquinas de coser`
*Regla:* prepara materiales + opera máquinas de coser ⇒ operador/a de máquinas de coser; solo marca/corta textil según moldes ⇒ cortador/a textil; crea/modifica patrones CAD ⇒ técnico/a de diseño textil asistido por ordenador; controla/optimiza proceso y calidad ⇒ controlador/a de procesos textiles; revestimientos de autos ⇒ tapicero/a de vehículos de motor; solo inspecciona ⇒ inspector/a de montaje de productos textiles.

**Operario/a corte láser** → `7223.4.3 operador de cortadora láser`
*Regla:* configura/maneja cortadora láser sobre metal ⇒ operador/a de cortadora láser; solo punzonadora/prensa ⇒ operador/a de prensa de estampar; plasma ⇒ operador/a de cortadora de plasma; oxicorte ⇒ operador/a de máquina oxicortadora; chorro de agua ⇒ operador/a de máquina de corte por agua a alta presión; distintas CNC sin especialización ⇒ operador/a de máquinas de control numérico.

**Operario/a de depósito (congelados)** → `9333.8.1 responsable de pedidos de almacén`
*Regla:* selecciona/controla mercadería para envío ⇒ responsable de pedidos de almacén; recepción+almacenamiento+control+expedición ⇒ operario/a de logística de almacén; recibe/etiqueta/controla/almacena ⇒ mozo/a de almacén; zorra/autoelevador/elevación ⇒ operador/a de carretilla elevadora; solo carga/descarga ⇒ estibador/a; solo registra inventarios ⇒ coordinador/a de inventario; solo empaqueta/etiqueta manual ⇒ responsable de empaquetado manual.

**Operario/a soldador** → `7212.3 soldador/a`
*Regla:* regula máquina + une piezas por distintos procesos ⇒ soldador/a; solo por puntos ⇒ operador/a de soldadura por puntos; suelda e instala tuberías ⇒ soldador/a de tuberías; haz láser ⇒ operador/a de soldadura por haz láser; haz de electrones ⇒ operador/a de soldadura de haz de electrones; soldadura fuerte ⇒ soldador/a de soldadura fuerte; soldadura blanda ⇒ soldador/a de soldadura blanda; solo ensambla ⇒ montador/a de productos metálicos; solo inspecciona ⇒ inspector/a de control de calidad de productos metálicos; coordina soldadores ⇒ coordinador/a de soldadura.

### Familia «técnico» (13 denominaciones)

**Técnico de instalaciones de redes y wifi** → `3513.2 técnico de redes de TIC`
*Regla:* instala/configura/mantiene redes cableadas e inalámbricas ⇒ técnico/a de redes de TIC; soporte general PC/software/periféricos ⇒ técnico/a de TIC; administra LAN/WAN/servidores/VPN/seguridad ⇒ administrador/a de redes de TIC; diseña topología ⇒ arquitecto/a de redes de TIC; instalaciones eléctricas ⇒ electricista.

**Técnico de instalaciones/campo** → `7422.5 técnico en alarmas de seguridad`
*Regla:* CCTV/control de acceso/alarmas ⇒ técnico/a en alarmas de seguridad; redes cableadas/wifi ⇒ técnico/a de redes de TIC; soporte general ⇒ técnico/a de TIC; ciberseguridad ⇒ técnico/a de seguridad de TIC; responde señales sin instalar ⇒ técnico/a de servicio de respuesta a señales de sistemas de alarma.

**Técnico de mantenimiento eléctrico industrial** → `7411.1.1.2 electricista industrial`
*Regla:* tableros/cableados/sensores/motores/variadores/PLC ⇒ electricista industrial; componentes mecánicos y eléctricos de maquinaria ⇒ mecánico/a electricista; predomina programación/automatización PLC ⇒ ingeniero/a técnico/a de automatización; placas/circuitos/electrónica ⇒ ingeniero/a técnico/a en electrónica; repara maquinaria ⇒ mecánico/a de maquinaria industrial.

**Técnico electricista con experiencia en obra** → `7411.1.1 electricista de obras`
*Regla:* tableros BT + canalizaciones + tendido/conexionado ⇒ electricista de obras; mantenimiento de plantas/motores/PLC ⇒ electricista industrial; domiciliaria ⇒ electricista doméstico/a; mecánica y eléctrica de maquinaria ⇒ mecánico/a electricista; diseña planos/proyectos ⇒ ingeniero/a eléctrico/a.

**Técnico mecánico sector mantenimiento** → `7233.7 mecánico de maquinaria industrial`
*Regla:* diagnostica/mantiene/repara maquinaria + soldadura/neumática/hidráulica ⇒ mecánico/a de maquinaria industrial; mecánica y eléctrica con peso similar ⇒ mecánico/a electricista; tableros/cableados/motores/PLC ⇒ electricista industrial; mantenimiento electrónico ⇒ ingeniero/a técnico/a en electrónica; solo soldadura ⇒ soldador/a.

**Técnico/a de mantenimiento eléctrico** → `7412.3 mecánico electricista`
*Regla:* mantenimiento general/eléctrico/mecánico en establecimiento ⇒ mecánico/a electricista; tableros/cableados/motores/PLC en planta ⇒ electricista industrial; instalaciones en obra ⇒ electricista de obras; domiciliaria ⇒ electricista doméstico/a; solo limpieza/vigilancia/reparaciones menores ⇒ conserje de edificio; repara maquinaria ⇒ mecánico/a de maquinaria industrial.

**Técnico/a de refrigeración** → `7127.1 técnico de calefacción, ventilación, refrigeración y aire acondicionado`
*Regla:* revisa/mantiene/repara equipos existentes ⇒ técnico/a HVAC-R; instala sistemas HVAC según planos ⇒ instalador/a de sistemas de calefacción, ventilación y aire acondicionado; repara electrodomésticos (heladeras/aires) ⇒ técnico/a reparador/a de electrodomésticos; diseña climatización ⇒ ingeniero/a de climatización.

**Técnico/a electricista** → `7411.1 electricista`
*Regla:* tareas amplias BT/MT, subestaciones, alumbrado, industrial, mediciones ⇒ electricista; principalmente instalaciones industriales internas ⇒ electricista industrial; en obra/edificios ⇒ electricista de obras; domiciliaria ⇒ electricista doméstico/a; alumbrado público vial ⇒ electricista de alumbrado viario; mecánica y eléctrica de maquinaria ⇒ mecánico/a electricista; autos/barcos/minas/eventos/material rodante ⇒ especialidad ESCO correspondiente. *General cuando mezcla áreas; especialidad solo cuando una domina.*

**Técnico/a en instalaciones electromecánicas** → `7412.3 mecánico electricista`
*Regla:* mantenimiento de equipos de elevación (ascensores/montacargas/rampas) ⇒ mecánico/a electricista; electricidad pura de obra/BT-MT/edilicia ⇒ electricista. *Mecánico/a electricista cuando domina mantenimiento electromecánico; electricista cuando domina instalación/reparación eléctrica sin componente mecánico claro.*

**Técnico/a en instalaciones electromecánicas de construcción** → `7412.3 mecánico electricista`
*Regla:* (variante de la anterior) equipos de elevación ⇒ mecánico/a electricista; electricidad pura/tableros/edilicia ⇒ electricista; mantenimiento general de planta/máquinas ⇒ ocupación de mantenimiento industrial que aplique. *Industrial solo cuando el contexto es planta/producción/maquinaria general.*

**Técnico/a en seguridad e higiene** → `2263.3 responsable de salud y seguridad`
*Regla:* matrícula + evaluación de riesgos + normativa + permisos + legajos + investigación + auditorías internas + EPP ⇒ responsable de salud y seguridad; inspección/fiscalización externa o auditor externo ⇒ inspector/a de seguridad y salud en el trabajo. *Responsable cuando domina gestión preventiva interna; inspector/a cuando domina fiscalización externa.*

**Técnico/a instalador** → `7422.5 técnico en alarmas de seguridad`
*Regla:* alarmas/control de accesos/CCTV/detección de incendio/redes/fibra ⇒ técnico/a en alarmas de seguridad; eje en infraestructura de redes/fibra/telecom sin seguridad electrónica ⇒ técnico/a en ingeniería de las telecomunicaciones. *Seguridad electrónica vs telecomunicaciones según qué domine.*

**Técnico/a electrónico/a (mantenimiento)** → `3114.1 ingeniero técnico en electrónica`
*Regla:* mantenimiento electrónico de equipos de campo, diagnóstico de sensores/módulos/automatización/software ⇒ ingeniero/a técnico/a en electrónica; medición/calibración/instrumentación de procesos ⇒ ingeniero/a técnico/a de instrumentación; redes/conectividad/telecom ⇒ técnico/a en ingeniería de las telecomunicaciones; reparación mecánica y eléctrica de maquinaria ⇒ mecánico/a electricista.

### Familia «arquitecto» (4 denominaciones)

**Arquitecto - administrativo** → `2161.1 arquitecto/a`
*Regla:* título de Arquitectura + control de trámites/normativa de obras ⇒ arquitecto/a; solo tareas administrativas ⇒ empleado/a de oficina.

**Arquitecto - lic. en diseño de interiores** → `3432.1 diseñador de interiores`
*Regla:* layouts de espacios de trabajo ⇒ diseñador/a de interiores; diseña/supervisa edificios u obras integrales ⇒ arquitecto/a.

**Arquitecto corp. de infraestructura** → `2511.14 arquitecto de sistemas de TIC`
*Regla:* integra cómputo/almacenamiento/redes/nube/continuidad ⇒ arquitecto/a de sistemas de TIC; solo topología y conectividad ⇒ arquitecto/a de redes de TIC; edificios y obras ⇒ arquitecto/a.

**Arquitecto egresado** → `1323.1 director de obra`
*Regla:* planifica/coordina obra + costos/certificaciones + subcontratistas ⇒ director/a de obra; función principal diseñar el proyecto ⇒ arquitecto/a.

### Familia «pintor» (2 denominaciones)

**Pintor con soplete** → `7132.1 operador de pistola pulverizadora de lacado`
*Regla:* pulveriza pintura/laca sobre metal/madera/plástico ⇒ operador/a de pistola pulverizadora de lacado; vehículos ⇒ pintor/a de vehículos; edificios ⇒ pintor/a de obra; embarcaciones ⇒ pintor/a naval; solo lija/prepara ⇒ operario/a de preparación de superficies; solo anticorrosiva ⇒ operador/a de protección anticorrosiva; planos/dibujos ⇒ dibujante técnico/a.

**Pintor de obra / mantenimiento general** → `7131.1 pintor de obra`
*Regla:* pinta interiores/exteriores + arreglos domiciliarios ⇒ pintor/a de obra; mantenimiento general (limpieza/vigilancia/reparaciones menores) ⇒ conserje de edificio; principalmente eléctrica ⇒ electricista; cañerías/agua ⇒ fontanero/a; pinta con soplete/pistola ⇒ operador/a de pistola pulverizadora de lacado; repara maquinaria industrial ⇒ mecánico/a de maquinaria industrial.

### Familia «editor» (1 denominación)

**Editor de videos** → `2654.5 editor/a de cine y televisión`
*Regla:* monta/corta imágenes + subtítulos/efectos ⇒ editor/a de cine y televisión; fotografías ⇒ editor/a de fotografía; música/diálogos/efectos sonoros ⇒ editor/a de sonido; corrige textos ⇒ corrector/a editorial.

> Nota: 'editor de videos' está cargada plana en el diccionario con su **código por
> defecto** (2654.5). Las ramas (fotografía/sonido/corrector) son denominaciones distintas
> y no colisionan; cuando se construya la regla de contexto del editor, este árbol la
> especifica.

### Familia «herrero» (1 denominación)

**Herrero/a** → `7221.1 herrero/a`
*Regla:* fabrica/corta/suelda/monta piezas metálicas a medida ⇒ herrero/a; herra caballos ⇒ herrero/a de herraje; solo suelda ⇒ soldador/a; monta armaduras/estructuras de acero ⇒ ferrallista; techos/conductos/canaletas de chapa ⇒ chapista; ensambla productos metálicos en serie ⇒ montador/a de productos metálicos.

---

# PARTE 2 — Familias de la sesión (Word, julio 2026)

### Familia «gerente / encargado / responsable / jefe» — conducción
**Raíz:** gerente · encargado · responsable · jefe | **Fuente:** Word sesión 2026-07 | **Estado:** definida

*Árbol de Cyn (textual, del docx):*

> «Son una misma familia porque gerente, encargado, responsable y jefe indican algún nivel
> de conducción o coordinación. Pero no siempre significan lo mismo. Primero miro el título,
> después las tareas y el nivel de decisión que tiene el puesto. Si dirige un área completa,
> define objetivos, toma decisiones de gestión y tiene responsabilidad sobre resultados, lo
> llevo a gerente/director del área. Si organiza tareas del día a día, coordina personal
> operativo, controla stock, turnos, entregas o funcionamiento del sector, lo llevo a
> supervisor, encargado o jefe operativo. También miro el sector, porque no es lo mismo
> dirigir administración, comercial, logística o depósito.»

> «Gerente, encargado, responsable o jefe indican conducción, pero se separan por el nivel
> de responsabilidad y por las tareas. Si dirige administración, finanzas, presupuesto,
> pagos o control económico, corresponde a director financiero; si dirige ventas, clientes,
> objetivos comerciales o estrategia comercial, corresponde a director comercial; si
> coordina transporte, distribución, stock, entregas o personal operativo de logística,
> corresponde a supervisor de logística; si organiza el depósito, controla mercadería,
> stock, ingresos, egresos, pedidos o personal de almacén, corresponde a jefe de almacén.
> Si el puesto toma decisiones de gestión sobre un área completa, se codifica como
> gerente/director; si coordina la operación diaria, se codifica como supervisor, encargado
> o jefe operativo.»

*Casos de evidencia (correcciones de Cyn, tabla del docx con criterio "qué mirar en el aviso"):*

| Denominación | → código de Cyn | Qué mirar en el aviso (textual) |
|---|---|---|
| Gerente Administración | `1211.1` director financiero | «Si habla de dirigir administración, finanzas, presupuesto, pagos, control financiero, contabilidad o gestión económica de la empresa.» |
| Gerente Comercial (Lobos) | `1221.3.2.1` director comercial | «Si habla de dirigir ventas, estrategia comercial, clientes, objetivos comerciales, equipo de ventas o desarrollo de negocios.» |
| Encargado de Logística | `1324.3.4` supervisor de logística | «Si habla de coordinar entregas, transporte, distribución, stock, rutas, depósito o personal operativo de logística.» |
| Responsable de Depósito | `1324.3.1.6.11` jefe de almacén | «Si habla de organizar el depósito, controlar stock, ingreso y egreso de mercadería, preparar pedidos o coordinar personal del almacén.» |

**Rama obra/construcción (REGLAS.xlsx — jefe operativo, jefe de obra, ingeniero civil o
arquitecto a cargo de obra).** El árbol consolidado de Cyn (textual, nota del Excel):

> «Jefe/a de obra, director/a de obra, coordinador/a de obra, responsable de obra, gerente/a de obra, líder de obra, ingeniero/a civil, ingeniero/a en construcciones, arquitecto/a responsable de obra o jefe/a operativo/a en obra que planifica, coordina, ejecuta y controla integralmente obras o proyectos de construcción, lidera equipos, cuadrillas, contratistas y subcontratistas, controla avances, producción, cronogramas, plazos, costos, calidad, seguridad, materiales, certificaciones, proveedores, recursos y reportes de obra corresponde a director/a de obra; también corresponde cuando participa en la contratación, negociación, auditoría o seguimiento de proveedores y subcontratistas para completar distintas etapas de la obra. Si solo supervisa cuadrillas o tareas operativas sin responsabilidad integral sobre cronograma, costos, contratistas, recursos y avance general de obra, corresponde a supervisor/a general de construcción; si diseña, calcula, proyecta o elabora especificaciones técnicas sin conducir la ejecución de obra, corresponde a ingeniero/a civil, ingeniero/a de construcción o arquitecto/a según el eje técnico; si realiza apoyo técnico, cómputos, presupuestos, mediciones, documentación o seguimiento bajo conducción de otro responsable, corresponde a técnico/a de obra, maestro/a mayor de obra o perfil técnico equivalente; si solo realiza tareas administrativas, compras, pagos, planillas o documentación de obra, corresponde a empleado/a administrativo/a o de oficina; y si ejecuta tareas manuales de construcción, corresponde al oficio específico de la construcción.»

*Casos de evidencia de la rama (Excel Hoja 1):*

| Denominación | matcher dijo | → código de Cyn |
|---|---|---|

| Jefe operativo | `1323` (matcher, MAL) | `1323.1` |
| Ingeniero/a civil | `3112` (matcher, MAL) | `1323.1` |
| Ingeniero civil | `1323` (matcher, MAL) | `1323.1` |
| Ingeniero civil o arquitecto jefe de obra | `1323` (matcher, MAL) | `1323.1` |
| Ingeniero civil | `2142` (matcher, MAL) | `1323.1` |
| Jefe de obra - ingeniero civil o arquitecto | `1323` (matcher, MAL) | `1323.1` |
| Jefe de obra - ingeniero civil o arquitecto | `1323` (matcher, MAL) | `1323.1` |

---

### Familia «operador / programador»
**Raíz:** operador · operario (frontera) · programador | **Fuente:** Word sesión 2026-07 | **Estado:** definida

*Árbol de Cyn (textual, del docx):*

> «"Operador u operario" se resuelve por lo que opera o por la tarea concreta del aviso. Si
> opera máquinas de producción, empaque o embalaje, corresponde a operario/a de máquinas de
> embalaje o de producción según el caso; si realiza tareas manuales en planta sin
> conducción de equipos complejos, corresponde a operario/a de producción; si opera equipos,
> vehículos o sistemas específicos, se busca la ocupación según ese equipo o sistema.
> "Programador" no siempre es software: si programa, organiza o planifica la producción,
> órdenes de trabajo, materiales, turnos o procesos productivos, corresponde a supervisor/a
> de producción; si programa sistemas, aplicaciones, código, bases de datos o software,
> corresponde a programador/a o desarrollador/a de software.»

*Preguntas de la sesión respondidas (imágenes del docx, textual):*

> ¿"Operador" y "operario" son la misma familia? — «Sí, pueden trabajarse como una misma
> familia operativa, pero se separan por la tarea concreta. Operador suele indicar que
> maneja una máquina, equipo, sistema o proceso; operario suele estar más asociado a tareas
> manuales o de producción.»

> ¿Cómo separar "programador" de software del que programa producción? — «Miro lo que sigue
> después de "programador" y las tareas. Si habla de código, sistemas, aplicaciones o
> desarrollo, es software. Si habla de planificar órdenes, turnos, materiales o procesos
> productivos, es programación de producción.»

*Casos de evidencia:*

| Denominación | → código de Cyn | Qué mirar en el aviso (textual) |
|---|---|---|
| Operador de Producción | `8142.2` operario de máquinas de embalaje | «Si habla de operar máquinas, línea de producción, empaque, embalaje, control de máquina, carga de insumos o tareas manuales dentro de planta.» |
| Programador/a de la Producción | `3122.2` supervisor de producción — ¡no es programador de software! | «Si habla de programar, organizar o planificar la producción, coordinar órdenes, controlar tiempos, materiales, turnos o procesos productivos. No es software si no habla de sistemas, código o desarrollo.» |

> Cruce v1: la familia «operario» (16 denominaciones, PARTE 1) es la especialización fina
> de la rama "operario" de este árbol.

---

### Familia «analista»
**Raíz:** analista | **Fuente:** Word sesión 2026-07 (+ rama oficina técnica de REGLAS.xlsx, fusionada acá — Word manda) | **Estado:** definida

*Árbol de Cyn (textual, del docx):*

> «Lo primero que miro del aviso es el título; después miro bien las tareas y recién ahí
> busco en ESCO la ocupación que corresponde. En el caso de "analista", no alcanza con esa
> palabra sola: tengo que ver de qué es analista y qué tareas hace concretamente. Las ramas
> más comunes suelen ser sistemas o data center, datos, contabilidad o finanzas, recursos
> humanos, prevención e higiene y seguridad, oficina técnica, logística, procesos, mercado
> o precios. Las ramas más comunes de "analista" en Argentina son sistemas/TIC, datos,
> contabilidad y finanzas, recursos humanos, prevención e higiene y seguridad, oficina
> técnica, logística, procesos, marketing/mercado y calidad. Igualmente tambien se
> presentan casos en la rama construcción.»

*Casos de evidencia (tabla del docx con criterio textual):*

| Denominación | → código de Cyn | Qué mirar en el aviso (textual) |
|---|---|---|
| Analista de prevención | `2263.3` responsable de salud y seguridad | «Si habla de prevención de riesgos, higiene y seguridad, condiciones seguras de trabajo, normas de seguridad o accidentes laborales.» |
| Analista Corporativo — Data Center | `2522.1` administrador de sistemas TIC | «Si habla de data center, servidores, redes, infraestructura informática, monitoreo, soporte técnico o administración de sistemas.» |
| Analista de Oficina Técnica | `2142.1` ingeniero técnico / dibujante | «Si habla de planos, documentación técnica, cómputos, proyectos, relevamientos, obra o asistencia técnica de ingeniería.» |

**Rama «analista de oficina técnica» (REGLAS.xlsx, fusionada — el árbol completo de Cyn, textual):**

> «Analista de oficina técnica, técnico/a de oficina técnica o profesional de proyectos en constructora que coordina planos, cómputos, presupuestos, especificaciones técnicas, normativa y soporte técnico a obra corresponde a ingeniero/a de construcción; si diseña edificios o espacios arquitectónicos, a arquitecto/a; si dirige integralmente la obra, contratistas, plazos y ejecución, a director/a de obra; si realiza solo gestión documental, pagos, planillas o soporte administrativo, a empleado/a de oficina; y si hace dibujo técnico de planos sin responsabilidad profesional sobre el proyecto, a delineante.»

*Caso de evidencia de la rama:* Analista de oficina técnica | matcher dijo `2142` | → `2142.1.2`
ingeniero de construcción.

> Nota de fusión (Word manda): en la tabla de la sesión Cyn llevó «Analista de Oficina
> Técnica» a `2142.1` (ingeniero técnico/dibujante); en el Excel, con las tareas completas
> del aviso (coordina planos, cómputos y presupuestos de proyectos ejecutivos), a `2142.1.2`
> (ingeniero de construcción). No son contradicción: el árbol de la rama resuelve por
> tareas — el criterio operativo es el árbol del Excel, el encuadre general es el del Word.

---

### Familia «asesor / advisor / consultor»
**Raíz:** asesor · advisor · consultor | **Fuente:** Word sesión 2026-07 (imágenes verificadas) | **Estado:** definida

*Respuestas de Cyn (imágenes del docx, textual):*

> ¿"Asesor" en Argentina es casi siempre ventas? — «En muchos avisos sí, "asesor" suele
> aparecer ligado a ventas o atención comercial, salvo que el aviso diga otra cosa. Por eso
> miro si asesora clientes, vende, capta cuentas u ofrece productos o servicios.»

> ¿"Advisor" a secas se puede clasificar? — «No. "Advisor" solo es muy general y depende
> completamente del aviso. Hay que mirar las tareas, porque puede ser comercial, técnico,
> soporte, testing u otra función.»

> ¿"Consultor" va por el área que lo acompaña? — «Sí. "Consultor" se define por el área o
> sistema sobre el que trabaja: TIC, sueldos, recursos humanos, finanzas, gestión, ventas, etc.»

*Casos de evidencia (tabla del docx con criterio textual):*

| Denominación | → código de Cyn | Qué mirar en el aviso (textual) |
|---|---|---|
| Asesor comercial | `1221.3.2` responsable de marketing | «Si habla de ventas, atención a clientes, asesoramiento comercial, ofrecimiento de productos o servicios, captación de clientes, objetivos comerciales o seguimiento de cuentas.» |
| Advisor (aparece 2 veces) | `2519.7` probador de software | «"Advisor" solo no alcanza. Hay que mirar las tareas reales. Si el aviso habla de testeo, pruebas, validación de sistemas, detección de errores, reporte de fallas o control de funcionamiento de software, corresponde a probador/a de software.» / «Se mantiene el mismo criterio: no se clasifica por "advisor", sino por las tareas. Si las tareas son de testing o control de software, va a probador/a de software.» |
| Consultor Jr. de Liquidación de Sueldos | `2511.12` consultor TIC | «Si habla de sistemas de liquidación de sueldos, implementación, parametrización, soporte funcional, uso de software o asistencia a usuarios sobre una herramienta informática.» |

*Pendiente-Cyn:* «ASESOR COMERCIAL, TÉCNICO & LEGAL» (REGLAS.xlsx fila incompleta — sin
código ni árbol; va en devoluciones).

---

### Familia «vendedor»
**Raíz:** vendedor (y viajante) | **Fuente:** Word sesión 2026-07 (decisión del caso «vendedor viajante») | **Estado:** definida

*Decisión y árbol de Cyn (textual, del docx):*

> «Decisión y motivo: Confirmar. Se confirma vendedor viajante → representante comercial
> (3322.1), porque "vendedor viajante" refiere al trabajador que realiza venta externa:
> visita clientes, recorre zonas de venta, ofrece productos o servicios, toma pedidos y
> mantiene una cartera comercial fuera del local. Este mapeo es correcto siempre que el
> aviso hable de vendedor viajante, venta externa, recorrido de zona, cartera de clientes,
> visitas comerciales o toma de pedidos. No corresponde usar representante comercial
> (3322.1) si el aviso indica que la tarea principal es atención en local o mostrador,
> porque ahí corresponde vendedor/a (5223.4); si la tarea principal es reparto o entrega de
> mercadería, corresponde conductor/a de vehículo de reparto (8322.2); si promociona
> productos en punto de venta, entrega muestras o hace demostraciones, corresponde
> demostrador/a de promociones (5242.1); y si vende en la vía pública, calles, rutas o
> puestos de mercado, corresponde vendedor/a ambulante (9520.1).»

*Árbol resumido (derivado 1:1 de la prosa):* venta externa/recorre zonas/cartera/toma
pedidos ⇒ `3322.1` representante comercial · atención en local/mostrador ⇒ `5223.4`
vendedor/a · reparto/entrega ⇒ `8322.2` conductor de vehículo de reparto · promociona en
punto de venta/muestras ⇒ `5242.1` demostrador/a de promociones · vía pública ⇒ `9520.1`
vendedor/a ambulante.

> «vendedor viajante → 3322.1» es la denominación ESTABLE de esta familia: HOLD (blast 141)
> DESTRABADO por esta decisión escrita → va al diccionario por la bandeja de cosecha.

---

### Mini-familias de los casos sueltos NO estables (Word, tabla completada — image7)

### Familia «estudiante de abogacía»
**Raíz:** estudiante (de abogacía) | **Fuente:** Word sesión 2026-07 | **Estado:** definida
**⚠ RE-JUICIO de Cyn:** el código pasa de `3411.4` a **`3411.7`** (asistente jurídico).

*Criterio de Cyn (textual, image7):*

> «Depende de las tareas. Si asiste a abogados, prepara escritos, revisa expedientes o
> gestiona documentación legal, corresponde a asistente jurídico/a (3411.7). Si solo hace
> tareas administrativas generales en un estudio o área legal, puede corresponder a
> empleado administrativo en el ámbito jurídico-legal (3342.2). No usaría auxiliar judicial
> (3411.4) salvo que el aviso sea de tareas propias de juzgado o tribunal.»

### Familia «auxiliar de promociones y marketing»
**Raíz:** auxiliar (de promociones/marketing) | **Fuente:** Word sesión 2026-07 | **Estado:** definida

*Criterio de Cyn (textual, image7):*

> «Depende de las tareas. Si asiste en eventos, activaciones, ferias o acciones
> promocionales, puede ir a responsable de eventos (3332.2.1). Si promociona productos en
> punto de venta o hace demostraciones, corresponde a demostrador/a de promociones (5242.1).
> Si hace tareas de campañas, publicidad o comunicación, puede ir a especialista en
> publicidad (2431.3).»

### Familia «supervisor (de instalación / de obra)»
**Raíz:** supervisor | **Fuente:** Word sesión 2026-07 (manda) + REGLAS.xlsx (fusionado) | **Estado:** definida

*Criterio de Cyn — Word (textual, image7; MÁS FINO, manda sobre el Excel):*

> «Depende de qué instalación supervisa. Si es obra general, puede ir a supervisor general
> de construcción (3123.1). Si es instalación eléctrica, a supervisor de instalaciones
> eléctricas (3123.1.11). Si es ascensores, a supervisor de instalaciones de ascensores
> (3123.1.14). Si es alcantarillado o redes sanitarias, a supervisor de obras de
> alcantarillado (3123.1.22). Si solo instala sistemas de seguridad sin supervisar
> personal, puede ir a técnico en alarmas de seguridad (7422.5).»

*Fusión con REGLAS.xlsx (aportes que el Word no cubre):*

— «Supervisor de instalación» con tareas de montaje de pistas/estructuras/césped (nota del
Excel, textual — coincide con la rama 3123.1 del Word y agrega ramas metálicas/suelos/viales):

> «Supervisor/a de instalación, montaje u obra que dirige cuadrillas en sitio, controla estructuras, iluminación, superficies, acabados y entrega final corresponde a supervisor/a general de construcción; si supervisa principalmente estructuras metálicas, a supervisor/a de obras de estructuras metálicas; si supervisa solo tendido o redes eléctricas, a supervisor/a de tendido eléctrico; si supervisa solo instalación de suelos, a supervisor/a de obras de instalación de suelos; y si la obra es de carreteras o caminos, a supervisor/a de obras viales.»

— «Supervisor/a de montaje / ascensores» → `3123.1.14` (nota del Excel, textual — el detalle
de la rama ascensores del Word):

> «supervisor de instalaciones de ascensores/supervisora de instalaciones de ascensores Supervisor/a de montaje de ascensores, supervisor/a de instalación de ascensores, supervisor/a de montaje de medios de elevación, supervisor/a técnico/a de ascensores o responsable de montaje de ascensores que administra, coordina, controla, organiza y evalúa recursos, personal, materiales, tiempos, nuevas instalaciones y modernizaciones de ascensores o medios de elevación corresponde a supervisor/a de instalaciones de ascensores; usar cuando el aviso se centra en coordinar y controlar la ejecución del montaje, asignar recursos, asegurar cumplimiento de pautas contractuales y estándares, capacitar personal a cargo y brindar apoyo técnico al equipo. Si la tarea principal es montar, instalar, reparar, inspeccionar o mantener ascensores de forma operativa sin responsabilidad de coordinación del área o del personal, corresponde a técnico/a de ascensores; si supervisa montaje industrial general sin foco en ascensores o medios de elevación, corresponde a supervisor/a de montaje industrial; si dirige integralmente una obra de construcción con cronogramas, costos, contratistas y avance general, corresponde a director/a de obra; y si solo realiza mantenimiento eléctrico/electromecánico general sin foco en ascensores, corresponde a electricista industrial o mecánico/a electricista según las tareas dominantes.»

*Casos de evidencia:* Supervisor de Instalación (Word) → `3123.1.22` en el caso corregido
(alcantarillado) · Supervisor de instalación (Excel) `3123` → `3123.1` · Supervisor/a de
montaje / ascensores (Excel) `7412` → `3123.1.14`.

*Pendiente-Cyn:* «Supervisor de obra de mantenimiento en vía pública» (fila incompleta).

### Familia «ingeniero»
**Raíz:** ingeniero | **Fuente:** Word sesión 2026-07 (rama electrónico, manda) + REGLAS.xlsx (ramas civil/eléctrico/automatización/electromecánico/instrumentación) | **Estado:** definida

**Rama «ingeniero electrónico» (Word, textual — image7):**

> «Depende de las tareas. Si trabaja con electrónica general, circuitos, dispositivos,
> placas o equipos electrónicos, corresponde a ingeniero electrónico/a (2152.1). Si trabaja
> específicamente con electrónica de potencia, convertidores, inversores, variadores,
> fuentes o sistemas de potencia, corresponde a ingeniero electrónico/a de potencia
> (2152.1.12). Si trabaja con instrumentación y control, puede ir a ingeniero/a de
> instrumentación (2152.1.3). Si el puesto es más técnico, de instalación, ensayo o
> mantenimiento, puede corresponder a ingeniero/a técnico en electrónica (3114.1).»

**Rama «ingeniero civil» (REGLAS.xlsx, textual).** El árbol distingue el civil que DISEÑA
del que GESTIONA obra (→ familia conducción, rama obra):

> «Ingeniero/a civil, ingeniero/a de obra civil, ingeniero/a civil de proyectos, ingeniero/a civil estructural o profesional civil que diseña, revisa y valida fundaciones, estructuras civiles e infraestructura, analiza estudios de suelo, cálculos estructurales, documentación técnica, especificaciones, cómputos y materiales, y brinda soporte técnico durante la construcción corresponde a ingeniero/a civil; si la tarea principal es gestionar costos, presupuestos y control económico de proyectos de construcción sin diseño ni validación técnica civil dominante, corresponde a ingeniero/a de control de costes; si dirige integralmente la ejecución de obra, coordina contratistas, plazos, presupuesto y equipos en terreno, corresponde a director/a de obra; si solo supervisa tareas operativas de obra sin diseño técnico ni responsabilidad profesional de ingeniería, corresponde a supervisor/a de construcción; y si realiza planos o proyectos arquitectónicos de edificios como eje principal, corresponde a arquitecto/a.»

**Rama «ingeniero eléctrico» (REGLAS.xlsx, textual):**

> «Ingeniero/a eléctrico/a, ingeniero/a electricista, ingeniero/a eléctrico/a de proyectos, ingeniero/a de electricidad industrial o ingeniero/a eléctrico/a y de automatización que diseña y desarrolla sistemas, equipos y componentes eléctricos para proyectos industriales, realiza balances de potencia, dimensiona subestaciones, tableros de media y baja tensión, puesta a tierra, iluminación, cableado, canalizaciones, sistemas auxiliares y documentación técnica, y supervisa contratistas, inspecciones, pruebas, puesta en marcha y cumplimiento de normas corresponde a ingeniero/a eléctrico/a; si la tarea principal es exclusivamente diseñar subestaciones de media o alta tensión para transmisión, distribución o generación de energía, corresponde a ingeniero/a de subestaciones; si el eje principal es diseñar aplicaciones, PLC, robótica o sistemas de automatización de procesos productivos sin predominio del diseño eléctrico de potencia, corresponde a ingeniero/a de automatización; si fabrica, ensaya, monitorea o mantiene sistemas automatizados bajo conducción de ingenieros, corresponde a ingeniero/a técnico/a de automatización; y si solo opera o mantiene redes y centros de distribución eléctrica, corresponde a responsable técnico/a de redes y centros de distribución de energía eléctrica.»

**Rama «ingeniero en integración electrónica y electromecánica / automatización» (REGLAS.xlsx, textual):**

> «Ingeniero/a en integración electrónica y electromecánica, integrador/a electrónico/a industrial, integrador/a electromecánico/a industrial, ingeniero/a de automatización o especialista en automatización industrial que integra y pone en marcha sistemas electrónicos/electromecánicos, programa PLC, configura HMI/SCADA, diseña tableros, implementa protecciones y participa en proyectos de automatización de líneas de producción corresponde a ingeniero/a de automatización; si diseña y desarrolla circuitos, dispositivos o sistemas electrónicos sin foco principal en automatización productiva, a ingeniero/a electrónico/a; si diseña equipos o maquinaria que combinan tecnología eléctrica y mecánica, a ingeniero/a electromecánico/a; si fabrica, prueba, instala, calibra o mantiene sistemas automatizados bajo criterio técnico operativo, a ingeniero/a técnico/a de automatización; y si instala, repara o mantiene componentes mecánicos y eléctricos de maquinaria sin responsabilidad de ingeniería/proyecto, a mecánico/a electricista.»

**Rama «ingeniero mecánico/electromecánico» (con eje en supervisión de mantenimiento) (REGLAS.xlsx, textual):**

> «Ingeniero/a mecánico/a, ingeniero/a electromecánico/a, líder técnico/a de terreno, supervisor/a de mantenimiento o coordinador/a de instalaciones y reparaciones que planifica y supervisa instalación, reposición y mantenimiento de equipos, coordina inspecciones en campo, lidera equipos técnicos, controla fallas, pérdidas, desvíos y propone mejoras operativas corresponde a supervisor/a de mantenimiento industrial; si diseña y desarrolla equipos o maquinaria electromecánica, a ingeniero/a electromecánico/a; si diseña planes técnicos de mantenimiento y optimización de maquinaria con responsabilidad de ingeniería, a ingeniero/a de mantenimiento; si ejecuta personalmente reparaciones mecánicas y eléctricas sin supervisar equipos, a mecánico/a electricista; y si gestiona operaciones generales de toda la empresa, a director/a de operaciones.»

**Rama «técnico / ingeniero eléctrico-electrónico → instrumentación (Oil & Gas)» (REGLAS.xlsx, textual):**

> «Técnico/a o ingeniero/a eléctrico/a-electrónico/a, ingeniero/a de instrumentación y control, proyectista de instrumentación/control, técnico/a de documentación técnica I&C o profesional de ingeniería para Oil & Gas que desarrolla documentación técnica, realiza relevamientos de campo, aplica normas de la especialidad e informa avances sobre trabajos de Instrumentación y Control / Electricidad corresponde a ingeniero/a de instrumentación cuando el eje principal es proyectar, diseñar, relevar o documentar sistemas/equipos de control e instrumentación para procesos industriales; si el eje principal es diseño eléctrico de potencia, distribución eléctrica, tableros, instalaciones eléctricas o estudios eléctricos con ETAP, corresponde a ingeniero/a eléctrico/a; si el perfil es técnico y se dedica principalmente a construir, ensayar, supervisar, calibrar o mantener equipos de control como válvulas, relés, reguladores, sensores o instrumentos de proceso, corresponde a ingeniero/a técnico/a de instrumentación; si colabora en desarrollo, ensayo o mantenimiento de dispositivos electrónicos sin foco específico en instrumentación de procesos, corresponde a ingeniero/a técnico/a en electrónica; si realiza instalación o mantenimiento eléctrico operativo en campo, corresponde al técnico/oficio eléctrico específico; y si realiza soporte informático, redes, hardware, software o sistemas TIC, corresponde a técnico/a de TIC.»

*Casos de evidencia (Excel Hoja 1):*

| Denominación | matcher dijo | → código de Cyn |
|---|---|---|

| Ingeniero/a civil | `2149` (matcher, MAL) | `2142.1` |
| Ingeniero/a eléctrico | `2151` (matcher, MAL) | `2151.1` |
| Ingeniero/a en integración electrónica y electromecánica | `7412` (matcher, MAL) | `2141.3.2.1` |
| Ingeniero/a mecánico/electromecánico | `7412` (matcher, MAL) | `3115.1.6` |
| Técnico / ingeniero eléctrico-electrónico | `3512` (matcher, MAL) | `2152.1.3` |

*Pendientes-Cyn (filas incompletas del Excel):* Ingeniero en electrónica o en
telecomunicaciones · Ingeniero eléctrico o electromecánico · Ingeniero/a civil, responsable
de gestión de obras · Ingeniero / técnico en sistemas embedded, RF e infraestructura ·
Ingeniero civil, en construcciones o carreras afines.

### Familia «medio oficial de mantenimiento»
**Raíz:** medio oficial | **Fuente:** Word sesión 2026-07 | **Estado:** definida
**⚠ RE-JUICIO de Cyn:** `7233.8.1` queda SOLO para maquinaria agrícola.

*Criterio de Cyn (textual, image7):*

> «Depende del tipo de mantenimiento. Si mantiene maquinaria industrial, puede ir a
> mecánico/a de maquinaria industrial (7233.7). Si combina mecánica y electricidad
> industrial, puede ir a mecánico/a electricista (7412.3). Si es principalmente eléctrico,
> a electricista industrial (7411.1.1.2). Si es refrigeración o aire acondicionado, a
> técnico/a de refrigeración, aire acondicionado y calefacción (3115.1.17). Si es
> ascensores o equipos de elevación, a técnico/a de ascensores (7412.7). Solo usaría
> técnico/a de maquinaria agrícola (7233.8.1) si el aviso habla de maquinaria agrícola.»

---

# PARTE 3 — Familias del lote construcción/instalaciones (REGLAS.xlsx)

### Familia «administrativo»
**Raíz:** administrativo | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

**Rama «administrativo de obras» (textual):**

> «Administrativo de obras: desambiguar por el calificador “de obras” y por la función principal. Cuando las tareas son gestión documental, presentismo, planillas de horas, pagos, pedidos de materiales y coordinación administrativa de obra, corresponde a empleado/a de oficina. No usar ocupaciones técnicas o de dirección de obra si no planifica, dirige ni supervisa técnicamente la obra.»

**Rama «administrativo de infraestructura» (textual — el árbol más ramificado del lote,
recorre todos los administrativos ESCO):**

> «Administrativo/a de infraestructura, administrativo/a de mantenimiento, asistente administrativo/a de infraestructura, auxiliar administrativo/a de mantenimiento o empleado/a administrativo/a que gestiona órdenes de trabajo, registra y prioriza solicitudes de reparación y mantenimiento, arma cronogramas, coordina personal operativo, técnicos, proveedores y contratistas, controla stock e inventario, gestiona compras de insumos, organiza documentación técnica y registra cumplimiento de normas de seguridad corresponde a empleado/a administrativo/a; si solo realiza tareas generales de oficina como atender teléfonos, completar formularios, clasificar correo o agendar reuniones, corresponde a empleado/a de oficina; si el eje es archivo, clasificación y conservación de documentos, corresponde a empleado/a administrativo/a de archivos; si administra datos del registro civil, trámites de identidad, nacimientos, matrimonios o defunciones, corresponde a empleado/a administrativo/a de registro civil; si realiza gestión financiera, pagos, cobros, operaciones bancarias o documentación financiera, corresponde a empleado/a administrativo/a de gestión financiera o empleado/a bancario/a según el sector; si registra operaciones contables, facturas, pagos, ingresos o libros contables, corresponde a administrativo/a contable o empleado/a de contabilidad; si liquida sueldos, cargas sociales o novedades de personal, corresponde a administrativo/a de nóminas; si apoya tareas de selección, legajos o administración de personal, corresponde a ayudante de recursos humanos; si realiza trámites jurídico-legales, expedientes o documentación legal, corresponde a empleado/a administrativo/a jurídico-legal; si trabaja en administración de seguros o inversiones, corresponde al administrativo específico de seguros o inversión; si trabaja en administración sanitaria o centro médico, corresponde a administrativo/a de centro médico; si planifica y dirige estratégicamente mantenimiento, contratistas, seguridad, limpieza, infraestructura y gestión de espacios, corresponde a responsable de instalaciones; si ejecuta reparaciones o mantenimiento manual, corresponde a empleado/a de mantenimiento u oficio técnico específico; y no corresponde a empleado/a del hogar, perrera, guardarropa, lavandería o centro termal salvo que el aviso trate de esos servicios específicos.»

*Casos de evidencia:*

| Denominación | matcher dijo | → código de Cyn |
|---|---|---|

| Administrativo de obras | `4110` (matcher, MAL) | `4110.1` |
| Administrativo de infraestructura | `4110` (matcher, MAL) | `3343.1` |

### Familia «electricista»
**Raíz:** electricista (oficial / matriculado / industrial) | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

**Rama «electricista industrial» (textual):**

> «Electricista industrial que instala, mantiene y repara tableros, motores, canalizaciones, bandejas portacables, cañerías e instalaciones eléctricas industriales corresponde a electricista industrial; si principalmente instala, repara y mantiene componentes mecánicos y eléctricos de maquinaria o equipos electromecánicos, a mecánico/a electricista; si solo ensambla equipos eléctricos en línea o taller siguiendo planos, a montador/a de equipos eléctricos; y si realiza instalaciones eléctricas residenciales o de edificios no industriales, a electricista de obras y afines.»

**Rama «electricista matriculado / domiciliario» (textual):**

> «Electricista matriculado/a, electricista residencial, electricista domiciliario/a o técnico/a electricista de mantenimiento en hogares que diagnostica y repara fallas, trabaja con tableros, iluminación, tomacorrientes, equipos e instalaciones eléctricas residenciales corresponde a electricista doméstico/a; si instala o mantiene infraestructura eléctrica en edificios industriales o comerciales, a electricista industrial; si establece sistemas eléctricos temporales para eventos, a electricista de eventos; y si instala, repara y mantiene componentes mecánicos y eléctricos de maquinaria o equipos, a mecánico/a electricista.»

**Rama «oficial electricista / de obra» (textual):**

> «Oficial electricista, electricista de obra, electricista de mantenimiento edilicio, electricista instalador/a o electricista de construcción que realiza instalaciones, reparaciones o recambios eléctricos en obras, refacciones o edificios corresponde a electricista de obras y afines; si realiza instalaciones y mantenimiento eléctrico en domicilios particulares, a electricista doméstico/a; si instala y mantiene infraestructura eléctrica en edificios industriales o comerciales, a electricista industrial; si instala sistemas eléctricos temporales para eventos, a electricista de eventos; si instala, repara o mantiene componentes mecánicos y eléctricos de maquinaria o equipos, a mecánico/a electricista; y si pinta superficies, paredes o pisos, a pintor/a de construcción, no a pintor/a naval salvo que el trabajo sea específicamente en embarcaciones.»

*Casos de evidencia:*

| Denominación | matcher dijo | → código de Cyn |
|---|---|---|

| Electricista industrial | `8212` (matcher, MAL) | `7411.1.1.2` |
| Electricista matriculado | `7411` (matcher, MAL) | `7411.1.1.1` |
| Oficial electricista | `7131` (matcher, MAL) | `7411.1.1` |

> Cruce v1: la familia «técnico» v1 ya traía árboles de electricista vistos desde la raíz
> "técnico" (técnico electricista, mantenimiento eléctrico industrial). Coinciden en los
> targets (7411.1.1 obras / 7411.1.1.1 doméstico / 7411.1.1.2 industrial / 7412.3 mecánico
> electricista); esta familia los expresa desde la raíz "electricista".

### Familia «encargado de edificio»
**Raíz:** encargado (de edificio/consorcio) | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

> NO es la rama conducción de la familia «gerente/encargado/responsable/jefe» (Word):
> encargado de edificio es el oficio de consorcio.

*Árbol de Cyn (textual):*

> «Encargado/a de edificio, encargado/a de consorcio, portero/a de edificio, conserje de edificio o personal de mantenimiento edilicio residencial que realiza limpieza, mantenimiento general, control del reglamento interno, contacto con la administración, atención cotidiana del edificio y supervisión de proveedores corresponde a conserje de edificio; si presta servicios a huéspedes en un hotel, ayuda con equipaje o asistencia hotelera, a portero/a de hotel; si planifica y dirige el mantenimiento integral de edificios, contratistas, seguridad, limpieza e infraestructura a escala organizacional, a responsable de instalaciones; si realiza solo reparaciones generales sin función cotidiana de control del edificio, a mantenedor/a; si se ocupa principalmente de recepción, acceso o atención de visitantes, a recepcionista o vigilante de accesos según la tarea; y si dirige un área administrativa o departamento interno de una empresa, a jefe/a de departamento.»

*Caso de evidencia:* Encargado de edificio | matcher dijo `1219` | → `5153.1` conserje de edificio.

### Familia «responsable de mantenimiento edilicio / facilities»
**Raíz:** responsable (mantenimiento edilicio) | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

*Árbol de Cyn (textual):*

> «Responsable de mantenimiento edilicio, responsable de instalaciones, jefe/a de mantenimiento edilicio o encargado/a de facilities que planifica, coordina y controla el mantenimiento preventivo y correctivo de edificios, equipos de mantenimiento y limpieza, trabajos tercerizados, seguridad, emergencias técnicas y estado general de las instalaciones corresponde a responsable de instalaciones; si supervisa mantenimiento de máquinas, sistemas y equipos industriales de planta, a supervisor/a de mantenimiento industrial; si realiza personalmente reparaciones generales de edificios sin gestión de equipos ni contratistas, a mantenedor/a; y si cuida edificios con tareas menores de limpieza, reparaciones y atención cotidiana, a conserje de edificio.»

*Caso de evidencia:* Responsable de mantenimiento edilicio | matcher dijo `3115` | → `1219.1.1`
responsable de instalaciones.

### Familia «aprendiz / trabajos verticales»
**Raíz:** aprendiz (de instalador) · técnico oficial (redes de seguridad/altura) | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

**Rama «aprendiz de instalador» (textual):**

> «Aprendiz de instalador/a, ayudante de instalador/a, instalador/a de redes de seguridad, trabajador/a en altura, operario/a vertical, técnico/a en trabajos verticales o especialista en trabajos verticales que instala o aprende a instalar redes de seguridad y realiza tareas en altura sobre edificios o estructuras, usando herramientas manuales y colaborando en obras, instalaciones, construcción, herrería o albañilería, corresponde a especialista en trabajos verticales; si la tarea principal es montar, desmontar o mantener andamios o plataformas para permitir otros trabajos en altura, corresponde a montador/a de andamios; si realiza solo tareas generales de ayuda en obra sin instalación específica ni trabajo en altura, corresponde a peón/a de construcción; si instala cableado eléctrico, tableros, arneses, conexiones eléctricas o sistemas eléctricos, corresponde a montador/a o ensamblador/a de cableado eléctrico según la tarea; y si diseña, calibra o mantiene instrumentos de medición y control industrial, corresponde a ingeniería técnica de instrumentación.»

**Rama «técnico oficial» (mismo target, desde la raíz "técnico", textual):**

> «Técnico oficial, técnico/a instalador/a, instalador/a de redes de seguridad, trabajador/a en altura, operario/a vertical, oficial en trabajos verticales o técnico/a en trabajos verticales que instala redes de seguridad y realiza tareas en altura sobre edificios o estructuras, usando herramientas y aplicando buenas prácticas de trabajo y seguridad, corresponde a especialista en trabajos verticales; si la tarea principal es montar, desmontar o mantener andamios o plataformas para permitir trabajos en altura, corresponde a montador/a de andamios; si realiza tareas generales de ayuda en obra sin instalación específica ni trabajo en altura, corresponde a peón/a de construcción; si instala cableado eléctrico, alarmas, cámaras o sistemas electrónicos de seguridad, corresponde al instalador técnico específico; y si fabrica, trenza o procesa redes/textiles como producto industrial, corresponde a técnico/a de trenzado textil u otra ocupación textil.»

*Casos de evidencia:*

| Denominación | matcher dijo | → código de Cyn |
|---|---|---|

| Aprendiz de instalador | `3114` (matcher, MAL) | `7119.4` |
| Técnico oficial | `8159` (matcher, MAL) | `7119.4` |

### Familia «sobrestante»
**Raíz:** sobrestante | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

*Árbol de Cyn (textual):*

> «Sobrestante de obra, sobrestante, supervisor/a de obra, encargado/a de obra, jefe/a de obra operativo/a, coordinador/a de obra en terreno, arquitecto/a de obra o ingeniero/a civil en obra que realiza presencia diaria en obra, controla rendimiento de mano de obra, administra materiales, coordina contratistas y proveedores, articula con la dirección de obra, tracciona plazos, objetivos y criterios técnicos, resuelve problemas operativos y controla seguridad e higiene corresponde a supervisor/a general de construcción; usar cuando el aviso se centra en seguimiento operativo de la obra, coordinación de equipos, control de ejecución, materiales, proveedores, contratistas, plazos y cumplimiento de criterios definidos por la dirección de obra. Si dirige integralmente la obra con responsabilidad sobre planificación general, presupuesto, contratación, subcontratistas, costos, cronograma y avance global del proyecto, corresponde a director/a de obra; si diseña, calcula, proyecta o elabora especificaciones técnicas de ingeniería como eje principal, corresponde a ingeniero/a civil o ingeniero/a de construcción; si el eje principal es diseño arquitectónico, planos o proyecto, corresponde a arquitecto/a; si realiza apoyo técnico, cómputos, presupuestos, mediciones o documentación bajo conducción de otro responsable, corresponde a técnico/a de obra o perfil técnico equivalente; y si solo realiza tareas administrativas, compras, pagos, planillas o documentación de obra, corresponde a empleado/a administrativo/a.»

*Caso de evidencia:* Sobrestante de obra - arq. o ing. civil | matcher dijo `2142` | → `3123.1`
supervisor general de construcción.

> Cruce GRUPO B (v1): 'sobrestante de obra' ya tenía la bifurcación capataz/conductor por
> tareas; este árbol agrega el encuadre completo con default supervisor general.

### Familia «instalador»
**Raíz:** instalador (medidores de agua) | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

*Árbol de Cyn (textual):*

> «Instalador/a de medidores de agua, colocador/a de medidores de agua, plomero/a instalador/a, ayudante de plomería para instalación de medidores, personal de instalación de medidores, instalador/a domiciliario/a de agua o técnico/a de colocación de medidores que instala, coloca, conecta, ajusta o verifica medidores de agua en redes, domicilios, comercios o instalaciones de servicios de agua, realiza tareas asociadas de plomería o albañilería, registra y documenta instalaciones, cumple plazos de trabajo y reporta incidencias al supervisor corresponde a fontanero/a; usar cuando el eje del aviso es la instalación operativa de componentes del sistema de agua y no el riego agrícola. Si solo lee consumos de medidores sin instalar, reparar ni intervenir cañerías o conexiones, corresponde a lector/a de contadores; si instala infraestructura de riego para campos, cultivos, aspersores o sistemas agrícolas, corresponde a instalador/a de sistemas de riego agrícola o técnico/a de instalación y mantenimiento de sistemas de riego según el alcance; si mantiene redes hidráulicas, estaciones de bombeo, tuberías principales, desagües o alcantarillado, corresponde a técnico/a de redes hidráulicas; si realiza únicamente tareas de albañilería sin intervención de plomería o sistemas de agua, corresponde al oficio específico de construcción; y si supervisa equipos de instalación sin ejecutar tareas operativas, corresponde a supervisor/a de obra o de instalaciones según las responsabilidades reales.»

*Caso de evidencia:* Instaladores de medidores de agua | matcher dijo `7126` | → `7126.8`
fontanero/a.

### Familia «ayudante»
**Raíz:** ayudante | **Fuente:** REGLAS.xlsx Cyn + Word sesión 2026-07 | **Estado:** definida

**Rama «ayudante de terminación (industria gráfica)» (REGLAS.xlsx, textual):**

> «Ayudante de terminación gráfica, operario/a de terminación gráfica, ayudante de encuadernación, operario/a de encuadernación, ayudante de postimpresión, operario/a de postimpresión, auxiliar de terminación, ayudante de imprenta, operario/a gráfico/a de terminación o personal de acabado gráfico que colabora en la etapa final del proceso de producción gráfica, realiza o asiste en tareas de doblado, guillotinado, encuadernado, troquelado, plastificado, presentación, embalaje, control de calidad de productos impresos, abastecimiento del área de producción, orden y limpieza de máquinas o sector de trabajo y acondicionamiento de planchas corresponde a encuadernador/a, como ocupación más cercana dentro de terminación gráfica y postimpresión. Si la tarea principal es operar exclusivamente una guillotina o máquina cortadora de papel, corresponde a operador/a de guillotina de papel; si opera máquinas plegadoras como tarea dominante, corresponde a operador/a de impresoras plegadoras; si imprime en offset, flexografía, serigrafía, huecograbado u otra técnica de impresión como tarea principal, corresponde al tipo de impresor/a específico; si supervisa equipos o procesos de impresión y encuadernación, corresponde a supervisor/a de procesos de impresión y encuadernación; si solo realiza embalaje, depósito, carga, descarga o abastecimiento sin tareas gráficas de terminación, corresponde a ocupaciones de embalaje, depósito o producción general; y si vende productos gráficos, papelería o electrodomésticos en comercio, corresponde a vendedor/a según el rubro real de venta.»

**Rama «ayudante de taller (lonas y toldos)» (Word, ESTABLE → va al diccionario, criterio textual):**

> «Es estable si el aviso habla de confección, reparación, armado o colocación de lonas,
> toldos, coberturas o materiales similares.» → `7533.4`

*Casos de evidencia:* Ayudante de terminación (industria gráfica) | matcher dijo `5223` (¡vendedor
de electrodomésticos!) | → `7323.1` encuadernador/a · Ayudante de taller (lonas y toldos) → `7533.4`.

### Familia «colocador»
**Raíz:** colocador | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

*Árbol de Cyn (textual):*

> «Colocador/a de porcelanato, colocador/a de cerámicos, colocador/a de azulejos, colocador/a de pisos, colocador/a de revestimientos o alicatador/a que instala baldosas, azulejos, cerámicos o porcelanato en pisos y paredes corresponde a alicatador/a; si coloca linóleo, vinilo, caucho o corcho, a instalador/a de suelos resistentes; si trabaja con losas/terrazo de cemento y mármol, a solador/a; si realiza albañilería general, mampostería, demoliciones o reparaciones de obra gruesa, a albañil; y si pinta superficies, a pintor/a de construcción.»

*Caso de evidencia:* Colocador de porcelanato | matcher dijo `7131` (¡pintor naval!) | → `7122.4`
alicatador/a.

### Familia «mampostero / albañil»
**Raíz:** mampostero · albañil | **Fuente:** REGLAS.xlsx Cyn | **Estado:** definida

**Rama «mampostero» (textual):**

> «Mampostero/a, albañil, oficial albañil, albañil de obra, oficial de obra gruesa o trabajador/a de mampostería que levanta, repara o interviene muros, estructuras de ladrillo, obra gruesa, pisos, techos, demoliciones y tareas generales de albañilería corresponde a albañil; si solo supervisa cuadrillas y asigna tareas de obra, a capataz de construcción; si coloca porcelanato, cerámicos, azulejos o baldosas, a alicatador/a; si prepara y pinta paredes, pisos o superficies, a pintor/a de obra; si realiza instalaciones o recambios eléctricos, a electricista de obras y afines; si realiza soldadura o armado de estructuras metálicas, a soldador/a; y si pinta embarcaciones o estructuras navales, a pintor/a naval.»

**Rama «oficial albañil» (textual):**

> «Oficial albañil, albañil, mampostero/a, albañil de obra, oficial de obra gruesa o trabajador/a de albañilería que realiza tareas generales de obra, obra gruesa, mampostería, demoliciones, reparación de pisos, sanitarios y albañilería general corresponde a albañil; si la tarea principal es cubrir, montar, reparar o impermeabilizar techos y cubiertas, a albañil de tejados y cubiertas; si solo supervisa cuadrillas y asigna tareas de obra, a capataz de construcción; si coloca porcelanato, cerámicos, azulejos o baldosas, a alicatador/a; si prepara y pinta paredes, pisos o superficies, a pintor/a de obra; si realiza instalaciones o recambios eléctricos, a electricista de obras y afines; si realiza soldadura o armado de estructuras metálicas, a soldador/a; y si solo realiza limpieza o apoyo no calificado de obra, a peón de construcción.»

*Casos de evidencia:*

| Denominación | matcher dijo | → código de Cyn |
|---|---|---|

| Mampostero | `7131` (matcher, MAL) | `7112.1` |
| Oficial albañil | `7112` (matcher, MAL) | `7112.1` |

### Ramas NUEVAS de familias v1 (REGLAS.xlsx — se suman a las de la PARTE 1)

**Familia «técnico» — ramas nuevas del lote (textual, cada una con su árbol completo):**

— **ascensores** («Técnico/a en instalaciones electromecánicas», «Técnico en ascensores»,
«Técnico de puesta en marcha de ascensores», «Ref.21177: técnico mecánico de elevadores»):

> «Técnico/a en instalaciones electromecánicas, técnico/a de mantenimiento de ascensores, ascensorista o mecánico/a de mantenimiento de equipos de elevación que instala, mantiene o repara ascensores, montacoches, montacargas y rampas vehiculares corresponde a técnico/a de ascensores; si mantiene componentes mecánicos y eléctricos de maquinaria o equipos industriales no específicos de elevación, a mecánico/a electricista; si supervisa cuadrillas de instalación de ascensores, a supervisor/a de instalaciones de ascensores; y si opera montacargas como vehículo/equipo de movimiento de cargas, a operador/a de carretilla elevadora.»

> «Técnico/a en ascensores, técnico/a de mantenimiento de ascensores, instalador/a de ascensores, electromecánico/a de ascensores o técnico/a de equipos de elevación que realiza mantenimiento preventivo y correctivo, reparación de componentes mecánicos y eléctricos, modernización, detección y resolución de fallas en ascensores corresponde a técnico/a de ascensores; si el aviso especifica mantenimiento de otros equipos de elevación como montacargas, montacoches o rampas vehiculares, también puede corresponder a técnico/a de ascensores/equipos de elevación cuando el eje sea instalación, mantenimiento o reparación electromecánica de esos sistemas; si realiza mantenimiento electromecánico general de maquinaria industrial sin foco en ascensores o elevadores, corresponde a mecánico/a electricista; si realiza solo cableado, tableros o instalaciones eléctricas edilicias/industriales, corresponde a electricista o electricista industrial; si coordina equipos y contratos sin ejecutar tareas técnicas, corresponde a supervisor/a o jefe/a de mantenimiento según el alcance; y si realiza tareas generales de obra sin especialización en ascensores, corresponde al oficio de construcción correspondiente.»

> «técnico de ascensores/técnica de ascensores Técnico/a de puesta en marcha de ascensores, técnico/a de ascensores, técnico/a electromecánico/a de ascensores, técnico/a electrónico/a de ascensores, instalador/a de ascensores, técnico/a de mantenimiento de ascensores o técnico/a de equipos de elevación que realiza puesta en marcha, ajuste fino, calibración, conexión, verificación, testeo, configuración de parámetros, regulación de sistemas de seguridad, preparación para inspecciones y habilitaciones, reportes técnicos o mantenimiento técnico de ascensores corresponde a técnico/a de ascensores; usar cuando el aviso se centra en tareas técnicas directas sobre ascensores, obras nuevas, modernizaciones, circuitos eléctricos y electrónicos, velocidad, frenado, nivelación, confort de cabina, limitadores, paracaídas, finales de carrera, planos, mediciones o placas electrónicas. Si la tarea principal es administrar, coordinar, organizar y controlar recursos, personal, materiales y montaje de ascensores sin ejecución técnica dominante, corresponde a supervisor/a de instalaciones de ascensores; si supervisa montaje industrial general sin foco en ascensores o medios de elevación, corresponde a supervisor/a de montaje industrial; si realiza mantenimiento electromecánico general de maquinaria industrial sin foco en ascensores, corresponde a mecánico/a electricista; si realiza solo instalaciones eléctricas, tableros o circuitos sin foco en ascensores, corresponde a electricista o electricista industrial; y si dirige integralmente una obra de construcción con cronogramas, costos, contratistas y avance general, corresponde a director/a de obra. consolidada»

— **seguridad electrónica / alarmas** («Técnico en instalación y mantenimiento de equipos de
seguridad», «Técnico instalador de alarmas», «Técnico electrónico, movilidad propia, empresa
de seguridad»):

> «Técnico/a instalador/a de sistemas de seguridad, técnico/a de alarmas, instalador/a de CCTV o técnico/a de seguridad electrónica que instala y mantiene cámaras, alarmas, sistemas integrados, cableado estructurado, redes básicas e infraestructura de seguridad corresponde a técnico/a en alarmas de seguridad; si instala y mantiene redes informáticas como función principal, a técnico/a de redes de TIC; si brinda soporte general sobre equipos informáticos y periféricos, a técnico/a de TIC; si realiza solo vigilancia o monitoreo operativo de cámaras/alarmas, a vigilante de seguridad; y si coordina equipos/proveedores sin instalar ni mantener sistemas, a gestor/a de servicio o supervisor/a según el alcance.»

> «Técnico/a instalador/a de alarmas, técnico/a en alarmas de seguridad, técnico/a de mantenimiento de alarmas, instalador/a de sistemas de seguridad, técnico/a de sistemas de seguridad, técnico/a de Verisure, instalador/a de sensores, instalador/a de alarmas domiciliarias o comerciales o personal técnico que instala, mantiene, revisa, configura, repara o resuelve incidencias en sistemas de alarma, sensores, paneles de control, dispositivos conectados, sistemas de seguridad contra robo o incendio y conexiones eléctricas o de telecomunicaciones en domicilios, comercios o empresas corresponde a técnico/a en alarmas de seguridad; usar cuando el aviso se centra en instalación, mantenimiento, resolución de problemas técnicos, asistencia al cliente, explicación del uso del sistema, detección de mejoras de seguridad y servicio técnico en sistemas de seguridad. Si la tarea principal es reparar electrónica de consumo como televisores, audio, video o cámaras digitales, corresponde a técnico/a reparador/a de electrónica de consumo; si instala y mantiene sistemas de domótica general del hogar como climatización, iluminación, riego, protección solar, seguridad y dispositivos inteligentes integrados, corresponde a instalador/a de hogares inteligentes; si brinda respuesta operativa ante señales de alarma e investiga eventos de seguridad sin instalar ni mantener los equipos, corresponde a técnico/a de servicio de respuesta a señales de sistemas de alarma; si realiza vigilancia presencial, control de accesos o patrullaje, corresponde a vigilante de seguridad o vigilante de accesos; y si instala o repara redes de telecomunicaciones, internet, cableado o equipos TIC sin foco en alarmas de seguridad, corresponde al instalador o técnico TIC correspondiente.»

> «Técnico/a electrónico/a de seguridad, técnico/a de seguridad electrónica, técnico/a instalador/a de alarmas, técnico/a de CCTV, técnico/a de control de acceso, técnico/a de barreras y molinetes, técnico/a de sistemas de seguridad, técnico/a de servicio técnico de calle en seguridad electrónica o técnico/a instalador/a de equipamiento de seguridad que instala, mantiene, configura, testea, diagnostica o repara equipos electrónicos, electromecánicos, sensores, alarmas, cámaras, CCTV, molinetes, barreras, controles de acceso, cableados de red, software asociado, PC, periféricos o sistemas electrónicos de seguridad en clientes corresponde a técnico/a en alarmas de seguridad; usar cuando el eje del aviso es la instalación, reparación y mantenimiento técnico de sistemas de seguridad electrónica en campo o en clientes. Si solo repara televisores, audio, video, cámaras digitales u otros aparatos de electrónica de consumo, corresponde a técnico/a reparador/a de electrónica de consumo; si realiza vigilancia física, monitoreo, control de accesos o respuesta a señales sin instalación ni reparación técnica, corresponde a vigilante de seguridad o técnico/a de servicio de respuesta a señales de sistemas de alarma según el caso; si instala redes informáticas, fibra óptica o cableado estructurado sin foco en seguridad electrónica, corresponde a instalador/a o técnico/a de telecomunicaciones/TIC; si realiza mantenimiento eléctrico industrial general de tableros, baja/media tensión o instalaciones eléctricas, corresponde a electricista industrial o mecánico/a electricista según las tareas dominantes; y si solo configura software sin intervención sobre equipamiento físico, corresponde a soporte técnico informático.»

— **artes escénicas / shows** («Técnico instalador / electricista para shows»):

> «Técnico/a instalador/a para shows, técnico/a de eventos, técnico/a escénico/a o técnico/a de luces y montaje que instala, prepara, verifica, mantiene, monta y desmonta sistemas de iluminación, automatización, rigging, estructuras y equipamiento para espectáculos en vivo corresponde a técnico/a de artes escénicas; si trabaja específicamente estableciendo y desmontando sistemas eléctricos temporales para eventos, a electricista de eventos; si solo monta escenarios o estructuras temporales, a montador/a de escenarios y estructuras temporales; si opera principalmente iluminación durante el espectáculo, a operador/a de luminotecnia; y si realiza instalaciones eléctricas residenciales, a electricista doméstico/a.»

— **electromecánico de mantenimiento** (variantes de taller/flota/planta → `7412.3`, y la
variante servicio-técnico-industrial → `3113.1.2`):

> «Técnico/a electromecánico/a de mantenimiento, técnico/a electromecánico/a, técnico/a de mantenimiento electromecánico, técnico/a de servicio técnico industrial o técnico/a de instalación y reparación de equipos industriales que instala, prueba, mantiene, diagnostica y repara equipos, circuitos o sistemas electromecánicos en clientes, con soporte remoto, informes técnicos y coordinación con áreas internas, corresponde a ingeniero/a técnico/a en electromecánica; si el eje principal es mantenimiento y reparación mecánica de maquinaria industrial sin componente eléctrico/electromecánico dominante, corresponde a mecánico/a de maquinaria industrial; si la tarea principal es instalación, reparación o mantenimiento eléctrico de equipos, cableado, motores o instalaciones eléctricas, corresponde a mecánico/a electricista; si diseña y desarrolla maquinaria o equipos electromecánicos a nivel de ingeniería, corresponde a ingeniero/a electromecánico/a; y si solo realiza soporte administrativo, atención al cliente o coordinación logística sin intervención técnica, corresponde a la ocupación administrativa o logística correspondiente.»

> «Técnico/a electricista de taller, técnico/a electromecánico/a de taller, mecánico/a electricista, electromecánico/a o técnico/a de mantenimiento eléctrico/electromecánico que instala, mantiene, diagnostica y repara componentes mecánicos y eléctricos de equipos, maquinaria, herramientas, equipamiento vial o flota vehicular, usando instrumentos de medición y diagnóstico, corresponde a mecánico/a electricista; si la tarea principal es instalar, mantener y reparar sistemas eléctricos y electrónicos específicos de vehículos de motor como baterías, cableado, alternadores, luces, calefacción, aire acondicionado o radios, corresponde a electricista de automóviles; si realiza mantenimiento mecánico general de vehículos, motores, lubricantes, frenos, suspensión o neumáticos, corresponde a mecánico/a de vehículos; si trabaja principalmente sobre maquinaria industrial no vehicular, montaje, diagnóstico y reparación de máquinas, corresponde a mecánico/a de maquinaria industrial; y si realiza instalaciones eléctricas generales en edificios, obras o locales, corresponde a electricista.»

> «Técnico/a eléctrico/a, técnico/a electromecánico/a, técnico/a de mantenimiento eléctrico/electromecánico, mecánico/a electricista o personal técnico de mantenimiento industrial que instala, repara, mantiene, diagnostica y prueba componentes mecánicos y eléctricos de maquinaria, herramientas, equipos o sistemas industriales corresponde a mecánico/a electricista; usar especialmente cuando el aviso combina electricidad, mecánica, electromecánica, automatización, diagnóstico de fallas y mantenimiento de equipos productivos, como frigoríficos o plantas industriales. Si la tarea principal es instalar y mantener cables, tableros, canalizaciones, infraestructura eléctrica o sistemas eléctricos de edificios industriales o comerciales, corresponde a electricista industrial; si el eje es mantenimiento mecánico de maquinaria sin componente eléctrico dominante, corresponde a mecánico/a de maquinaria industrial; si diseña sistemas eléctricos o electromecánicos a nivel profesional, corresponde a ingeniero/a eléctrico/a o ingeniero/a electromecánico/a; y si realiza tareas de instalación eléctrica domiciliaria o de obra no industrial, corresponde a electricista.»

> «Técnico/a electricista, técnico/a electromecánico/a, técnico/a de mantenimiento eléctrico, electricista industrial o técnico/a electricista/electromecánico/a que realiza mantenimiento eléctrico preventivo y correctivo, detecta y registra fallas, elabora informes técnicos, realiza ensayos de puesta a tierra, termografías, mediciones eléctricas, interpreta planos y trabaja sobre instalaciones monofásicas/trifásicas, protecciones, equipos de baja y media tensión, transformadores, subestaciones, grupos generadores y tableros de transferencia corresponde a electricista industrial; si el aviso combina de forma dominante electricidad con mecánica/electromecánica, reparación de componentes mecánicos y eléctricos de maquinaria, herramientas o equipos, corresponde a mecánico/a electricista; si solo realiza instalaciones eléctricas generales domiciliarias o de obra sin contexto industrial, corresponde a electricista; si diseña sistemas eléctricos, redes, subestaciones o proyectos eléctricos a nivel profesional, corresponde a ingeniero/a eléctrico/a; y si realiza gestión técnico-administrativa, atención al cliente, análisis de facturas de energía o trámites ante entes reguladores sin ejecución técnica, corresponde a una ocupación administrativa/comercial, no a electricista.»

> «Técnico/a electromecánico/a de mantenimiento, técnico/a electromecánico/a, técnico/a de servicio técnico industrial, técnico/a de mantenimiento de equipos industriales, mecánico/a electricista o personal técnico que instala, mantiene, diagnostica, repara, monta y pone en funcionamiento equipos o sistemas industriales con componentes mecánicos y eléctricos corresponde a mecánico/a electricista; usar especialmente cuando el aviso combina mantenimiento, instalación, reparación, diagnóstico de fallas, montaje y movimiento de equipos en clientes o plantas industriales. Si la tarea principal es solo mantenimiento eléctrico, tableros, circuitos, cables, planos eléctricos o instalaciones de BT/MT, corresponde a electricista industrial; si el eje es mantenimiento mecánico de maquinaria sin componente eléctrico dominante, corresponde a mecánico/a de maquinaria industrial; si diseña, desarrolla o proyecta equipos/sistemas electromecánicos a nivel de ingeniería, corresponde a ingeniero/a electromecánico/a o ingeniero/a técnico/a en electromecánica según el nivel; y si solo realiza atención al cliente, coordinación logística o informes sin intervención técnica, corresponde a ocupación administrativa o logística.»

> «Técnico/a electromecánico/a de mantenimiento, técnico/a electromecánico/a, técnico/a electrónico/a de mantenimiento industrial, técnico/a de mantenimiento de equipos industriales, técnico/a de servicio técnico industrial, mecánico/a electricista, electromecánico/a o personal técnico que instala, mantiene, diagnostica, repara, modifica, prueba o pone en funcionamiento equipos, instalaciones, máquinas o sistemas de planta con componentes eléctricos, electrónicos y/o mecánicos corresponde a mecánico/a electricista; usar especialmente cuando el aviso combina mantenimiento preventivo y correctivo, diagnóstico de fallas eléctricas o electrónicas, intervención sobre equipos industriales, uso de manuales técnicos, reemplazo de repuestos, prueba de equipos reparados, registros de intervención y trabajo operativo en planta industrial. Si la tarea principal es solo mantenimiento eléctrico, tableros, circuitos, cableados, motores, variadores, sensores, planos eléctricos o instalaciones de baja/media tensión, corresponde a electricista industrial; si el eje es mantenimiento mecánico de maquinaria sin componente eléctrico o electrónico dominante, corresponde a mecánico/a de maquinaria industrial; si instala, mantiene o repara sistemas eléctricos y electrónicos específicos de automóviles, corresponde a electricista de automóviles; si diseña, desarrolla o proyecta equipos o sistemas electromecánicos a nivel de ingeniería, corresponde a ingeniero/a electromecánico/a o ingeniero/a técnico/a en electromecánica según el nivel; y si solo realiza registros, compras, pedidos de materiales o tareas administrativas sin intervención técnica, corresponde a ocupación administrativa o logística.»

— **eléctrico industrial** («Técnico de mantenimiento eléctrico industrial», «Técnicos
eléctricos/electrónicos»):

> «Técnico/a de mantenimiento eléctrico industrial, electricista industrial, técnico/a electricista industrial, técnico/a de mantenimiento eléctrico de planta o electricista de planta que instala, mantiene, inspecciona, diagnostica y repara sistemas eléctricos, tableros, circuitos, cables, instalaciones e infraestructura eléctrica en plantas, industrias, edificios industriales o comerciales corresponde a electricista industrial; usar cuando el aviso se centra en mantenimiento preventivo y correctivo eléctrico, lectura de planos eléctricos, mediciones eléctricas, armado o seguimiento de tableros y cumplimiento de normas de seguridad eléctrica. Si además el aviso combina de forma dominante electricidad con mecánica/electromecánica, reparación de componentes mecánicos y eléctricos de maquinaria, herramientas o equipos, corresponde a mecánico/a electricista; si realiza instalaciones eléctricas generales en viviendas, locales u obras no industriales, corresponde a electricista; si mantiene maquinaria industrial principalmente desde lo mecánico, sin eje eléctrico dominante, corresponde a mecánico/a de maquinaria industrial; y si diseña sistemas eléctricos, tableros, redes o proyectos eléctricos a nivel profesional, corresponde a ingeniero/a eléctrico/a.»

> «Técnico/a de mantenimiento eléctrico industrial, electricista industrial, técnico/a electricista industrial, técnico/a de mantenimiento eléctrico de planta o electricista de planta que instala, mantiene, inspecciona, diagnostica y repara sistemas eléctricos, tableros, circuitos, cables, instalaciones, equipos de baja y media tensión, transformadores, subestaciones, grupos generadores, tableros de transferencia e infraestructura eléctrica en plantas, industrias, edificios industriales o comerciales corresponde a electricista industrial; usar cuando el aviso se centra en mantenimiento preventivo y correctivo eléctrico, lectura de planos eléctricos, mediciones eléctricas, ensayos de puesta a tierra, termografías, armado o seguimiento de tableros y cumplimiento de normas de seguridad eléctrica. Si además el aviso combina de forma dominante electricidad con mecánica/electromecánica, reparación de componentes mecánicos y eléctricos de maquinaria, herramientas o equipos, corresponde a mecánico/a electricista; si realiza instalaciones eléctricas generales en viviendas, locales u obras no industriales, corresponde a electricista; si mantiene maquinaria industrial principalmente desde lo mecánico, sin eje eléctrico dominante, corresponde a mecánico/a de maquinaria industrial; y si diseña sistemas eléctricos, tableros, redes o proyectos eléctricos a nivel profesional, corresponde a ingeniero/a eléctrico/a.»

— **electrónica** («Técnico en electrónica/ingeniero junior»):

> «Técnico/a en electrónica, técnico/a electrónico/a, ingeniero/a junior en electrónica, ingeniero/a técnico/a en electrónica, técnico/a de producción electrónica, técnico/a de ensamble electrónico, técnico/a de puesta en marcha electrónica o técnico/a de servicio electrónico que ensambla, construye, prueba, mide, mantiene, repara, instala o pone en marcha equipos eléctricos, electrónicos o dispositivos electrónicos, utiliza tester, multímetro u otros instrumentos de medición, aplica conocimientos de electrónica, Ley de Ohm, circuitos, componentes eléctricos o electrónicos, y puede realizar tareas en taller, producción u obra en campo corresponde a ingeniero/a técnico/a en electrónica. Si el puesto se centra en diseño, desarrollo, cálculo o ingeniería de productos electrónicos con responsabilidad profesional plena, corresponde a ingeniero/a en electrónica; si solo repara equipos electrónicos como oficio operativo sin tareas técnicas de ensayo, medición, puesta en marcha o apoyo a ingeniería, corresponde a mecánico/a y reparador/a en electrónica; si únicamente ensambla componentes o cableados siguiendo planos sin diagnóstico, medición, reparación ni puesta en marcha, corresponde a montador/a de equipos electrónicos; si instala equipos electrónicos en vehículos, corresponde a instalador/a de equipos electrónicos en vehículos; y si el eje principal es mantenimiento eléctrico industrial de tableros, instalaciones, baja/media tensión o infraestructura eléctrica, corresponde a electricista industrial o mecánico/a electricista según las tareas dominantes.»

— **telecomunicaciones** («Técnicos en electrónica, o en telecomunicaciones» — ⚠ la celda de
código dice `2153` ingeniero, pero el árbol de Cyn resuelve el default del TÉCNICO a
técnico/a en ingeniería de las telecomunicaciones [= `3522.1`] e ingeniero solo si el aviso
exige título de ingeniero; queda como CONDICIONAL, va en devoluciones para confirmar):

> «Técnico/a en telecomunicaciones, técnico/a electrónico/a en telecomunicaciones, técnico/a de telecos, técnico/a de comunicaciones, técnico/a de sistemas de telecomunicaciones, técnico/a de campo en telecomunicaciones o técnico/a de mantenimiento de telecomunicaciones que desarrolla, instala, mantiene, repara, supervisa, prueba o asiste técnicamente sistemas, equipos, redes o infraestructura de telecomunicaciones corresponde a técnico/a en ingeniería de las telecomunicaciones; usar cuando el aviso exige título técnico y experiencia comprobable en telecomunicaciones, aunque mencione electrónica, minería, campo, roster o mantenimiento. Si exige título de ingeniero/a y responsabilidad profesional de diseño, planificación o gestión integral de sistemas de telecomunicaciones, corresponde a ingeniero/a de telecomunicaciones; si el eje real es construcción, ensayo, reparación o mantenimiento de dispositivos electrónicos sin foco en telecomunicaciones, corresponde a ingeniero/a técnico/a en electrónica; si solo instala cableado estructurado, redes informáticas, fibra óptica o conectividad TIC sin alcance de telecomunicaciones más amplio, corresponde a técnico/a o instalador/a TIC según tareas; y si no hay tareas suficientes para diferenciar electrónica de telecomunicaciones, marcar revisión y priorizar el requisito principal del aviso.»

— **monitoreo TIC / NOC** («Technical monitoring operations»):

> «Technical monitoring operations, técnico/a de monitoreo, operador/a NOC, técnico/a de operaciones TIC, operador/a de monitoreo, técnico/a de soporte operativo, analista de monitoreo, operador/a de plataforma o personal de operaciones que monitorea infraestructura, aplicaciones, sistemas, flujos transaccionales, logs, métricas, alertas e incidentes, ejecuta pruebas funcionales básicas, realiza triaje inicial, sigue runbooks, escala incidentes, gestiona tickets, valida despliegues, registra actividades y contribuye a la disponibilidad y continuidad del servicio corresponde a operador/a de centro de datos; usar cuando el aviso se centra en operación técnica, monitoreo continuo, detección temprana de incidentes, troubleshooting inicial, escalamiento, herramientas de monitoreo, gestión de incidentes, tickets, entornos productivos, alta disponibilidad o soporte operativo de plataformas digitales. Si la tarea principal es brindar ayuda directa a usuarios finales sobre hardware, software o uso de sistemas, corresponde a agente del servicio de asistencia de TIC; si instala, mantiene o repara equipos, redes, servidores, periféricos o software de forma técnica general, corresponde a técnico/a de TIC; si administra servidores, redes, sistemas o infraestructura con responsabilidad técnica de configuración y mantenimiento avanzado, corresponde a administrador/a de sistemas de TIC o técnico/a de redes de TIC según el eje; si analiza requisitos, diseña soluciones o mejora sistemas a nivel funcional/profesional, corresponde a analista de sistemas de TIC; y si coordina o dirige estratégicamente servicios, infraestructura, recursos o equipos TIC, corresponde a gestor/a de operaciones de TIC.»

*Casos de evidencia (todas las filas "técnico" del lote):*

| Denominación | matcher dijo | → código de Cyn |
|---|---|---|

| Técnico/a en instalaciones electromecánicas | `7412` (matcher, MAL) | `7412.7` |
| Técnico instalador / electricista | `7411` (matcher, MAL) | `3435.23` |
| Técnico en instalación y mantenimiento de equipos de seguridad | `3512` (matcher, MAL) | `7422.5` |
| Técnico en instalación de equipos de seguridad | `7422` (matcher, MAL) | `7422.5` |
| Técnico en instalación de equipos de seguridad | `3512` (matcher, MAL) | `7422.5` |
| Técnico electromecánico de mantenimiento | `7412` (matcher, MAL) | `3113.1.2` |
| Técnico electricista / electromecánico de taller | `7411` (matcher, MAL) | `7412.3` |
| Técnico eléctrico / electromecánico | `7412` (matcher, MAL) | `7412.3` |
| Técnico de mantenimiento eléctrico industrial | `7412` (matcher, MAL) | `7411.1.1.2` |
| Técnico electricista / electromecánico de taller | `7411` (matcher, MAL) | `7412.3` |
| Técnico en ascensores | `7412` (matcher, MAL) | `7412` |
| Técnico electricista / electromecánico | `7411` (matcher, MAL) | `7411.1.1.2` |
| Técnico electromecánico de mantenimiento | `7412` (matcher, MAL) | `7412.3` |
| Técnico de puesta en marcha de ascensores | `7412` (matcher, MAL) | `7412` |
| Technical monitoring operations | `2132` (matcher, MAL) | `3511.1` |
| Técnicos eléctricos/electrónicos | `3114` (matcher, MAL) | `7411.1.1.2` |
| Técnico instalador de alarmas | `7421` (matcher, MAL) | `7422.5` |
| Ref.21177: técnico mecánico de elevadores | `7412` (matcher, MAL) | `7412` |
| Técnico electromecánico - electrónico | mantenimiento | `7412` (matcher, MAL) | `7412.3` |
| Técnico en electrónica/ingeniero junior | `3114` (matcher, MAL) | `3114.1` |
| Técnico electrónico, movilidad propia, empresa de seguridad | `7421` (matcher, MAL) | `7422.5` |
| Técnicos en electrónica, o en telecomunicaciones | `2153` (matcher, MAL) | `2153` |

**Familia «arquitecto» — rama nueva:** «Arquitecto/a junior - dibujo y modelado técnico» (textual):

> «Arquitecto/a junior, arquitecto/a recién recibido/a, arquitecto/a dibujante, arquitecto/a modelador/a técnico/a, arquitecto/a proyectista junior, arquitecto/a de documentación técnica o arquitecto/a que desarrolla legajos técnicos, planos constructivos, planos municipales, documentación ejecutiva, modelado técnico, integración de sistemas estructurales y MEP, seguimiento de presentaciones ante entidades públicas y trabajo técnico bajo dirección de proyecto corresponde a arquitecto/a; usar cuando el aviso exige título de arquitecto/a y las tareas se centran en diseño, documentación, planos, modelado, proyecto, trámites técnicos o apoyo profesional en arquitectura. Si la tarea principal es solo dibujar o pasar planos sin título profesional ni intervención arquitectónica, corresponde a delineante o dibujante técnico según el caso; si el eje es modelado 3D artístico, renderizado o visualización sin documentación arquitectónica, corresponde a modelador/a 3D o diseñador/a gráfico/multimedia; si se trata de diseño de interiores, distribución y ambientación de espacios interiores, corresponde a interiorista; si dirige integralmente una obra con cronograma, costos, contratistas y avance general, corresponde a director/a de obra; y si realiza soporte informático, redes, software o asistencia TIC, corresponde a técnico/a de TIC.»

*Caso:* matcher dijo `3512` (¡técnico de TIC!) | → `2161.1` arquitecto/a.

**Familia «pintor» — rama nueva:** «Oficial pintor» (textual):

> «Oficial pintor/a, pintor/a de obra, pintor/a de construcción, pintor/a edilicio/a o pintor/a de mantenimiento que prepara superficies, obra seca, paredes, pisos industriales u otras superficies de edificios y realiza pintura general en obras, refacciones o mantenimiento edilicio corresponde a pintor/a de obra; si pinta embarcaciones o estructuras navales, a pintor/a naval; si pinta vehículos, a pintor/a de vehículos; si aplica pintura o recubrimientos en piezas, máquinas o productos industriales fuera de obra edilicia, a pintor/a industrial; si realiza principalmente albañilería, demoliciones, mampostería o reparaciones de obra gruesa, a albañil; y si coloca porcelanato, cerámicos o revestimientos, a alicatador/a.»

*Caso:* matcher dijo `7131` | → `7131.1` pintor de obra.

**Familia «herrero» — rama nueva:** «Oficial herrero / soldador» (textual):

> «Oficial herrero/a soldador/a, herrero/a soldador/a, soldador/a de obra, soldador/a metalúrgico/a o soldador/a de mantenimiento que une, repara, arma, monta o desmonta piezas y estructuras metálicas mediante soldadura corresponde a soldador/a; si fabrica o repara piezas metálicas mediante forja o herrería sin soldadura como tarea principal, a herrero/a; si principalmente monta estructuras metálicas sin soldar, a montador/a de estructuras metálicas; si realiza albañilería, demoliciones o reparaciones de obra gruesa, a albañil; y si pinta estructuras o superficies, a pintor/a de obra.»

*Caso:* matcher dijo `7212` | → `7212.3` soldador/a.

**Familia «operario» — casos nuevos:** «Operario de depósito» (el árbol v1 ya lo tiene; el
lote lo confirma con la nota del Excel) y «Operario de carga y descarga» (textual):

> «Operario/a especializado/a de depósito, picker, preparador/a de pedidos o auxiliar de picking que arma pedidos, selecciona productos, maneja cajas y organiza mercadería para envío corresponde a responsable de pedidos de almacén; si recibe, etiqueta, embala, controla y almacena mercadería, a mozo/a de almacén; si realiza carga, descarga y traslado general de materiales, a operario/a de logística de almacén; si principalmente maneja autoelevador, a operador/a de carretilla elevadora; y si realiza tareas generales de asistencia en una línea fabril sin preparación de pedidos, a trabajador/a de fábrica.»

> «Operario/a de carga y descarga, operario/a de depósito, peón/a de depósito, auxiliar de depósito, mozo/a de almacén o trabajador/a eventual de logística que realiza carga, descarga, movimiento, manipulación y acomodamiento de mercadería en depósitos corresponde a mozo/a de almacén; si además prepara pedidos, controla stock, embala o etiqueta mercadería como tarea principal, puede corresponder a preparador/a de pedidos o empleado/a de almacén según el alcance; si opera autoelevador o zorra motorizada como tarea principal, corresponde a conductor/a de autoelevador; si realiza tareas administrativas de logística, remitos o sistema de gestión, corresponde a empleado/a administrativo/a de logística; y si atiende mesas o sirve alimentos, no corresponde a mozo/a de almacén sino a camarero/a.»

*Casos:* Operario de depósito | `9329` | → `9333.8.1` · Operario de carga y descarga | `9333` | → `9333.3`.

---

### Familia «desarrollador»
**Raíz:** desarrollador · developer · programador (software) | **Fuente:** REGLAS respuesta Cyn 2026-07-13 (post-punto-de-control) | **Estado:** definida

*Contexto:* resuelve la discrepancia 2512.9→**2512.4** detectada en la bandeja de cosecha
(el caso «Desarrollador Python Sr», estable del Word). Árbol de Cyn (textual):

> «Desarrollador/a Python, desarrollador/a Python Senior, Python Developer, desarrollador/a backend Python, programador/a Python, software developer, desarrollador/a de software, desarrollador/a backend, desarrollador/a de aplicaciones, ingeniero/a de software o perfil técnico que diseña, desarrolla, programa, prueba, despliega, mantiene, integra u optimiza aplicaciones, APIs, sistemas backend, servicios cloud, soluciones informáticas, modelos de lenguaje, flujos con LangChain/LangGraph, CI/CD, arquitectura de software o componentes de software corresponde a desarrollador/a de software; usar cuando el aviso se centra en programación y desarrollo de soluciones informáticas, aunque mencione proyectos bancarios, inteligencia artificial, LLMs, APIs de terceros, cloud, contenedores, buenas prácticas de arquitectura, acompañamiento técnico a perfiles junior o mejora de eficiencia del software. Si el eje principal es Internet de las Cosas, sensores, dispositivos conectados, hardware embebido, firmware, conectividad entre dispositivos o plataformas IoT, corresponde a desarrollador/a de IdC/IoT; si el foco es análisis funcional, relevamiento de requerimientos, documentación y nexo entre negocio y tecnología sin programación como tarea principal, corresponde a analista de sistemas o analista funcional según el catálogo; si administra servidores, infraestructura, redes, despliegues o pipelines sin desarrollar software como eje central, corresponde a perfil de administración de sistemas, DevOps o infraestructura según las tareas reales; y si solo realiza soporte técnico, atención de incidencias o mantenimiento operativo de sistemas sin diseño ni programación, corresponde a técnico/a de soporte informático.»

*Caso de evidencia:* Desarrollador Python Senior («Desarrollador python SR para proyectos
bancarios») | matcher dijo `2512` | → `2512.4` desarrollador de software. Denominaciones de la
consolidada cargadas al diccionario (cosecha 2026-07-13, todas → 2512.4).

---

### Familia «chofer / conductor»
**Raíz:** chofer · conductor · transportista | **Fuente:** REGLAS respuesta Cyn 2026-07-13 (post-punto-de-control) | **Estado:** definida

*Contexto:* resuelve la discrepancia 8332.2→**8332.8** (caso «Chofer de recolección de
residuos», estable del Word). Es el árbol más ramificado del material: deslinda residuos /
carga general / reparto / pasajeros / taxi / ambulancia / autoelevador / maquinaria pesada /
mercancías peligrosas / recolector manual. **Complementa (no pisa) los deslindes existentes
de la familia «operario» (depósito): autoelevador dentro de depósito ⇒ operador/a de
carretilla elevadora, igual que en los árboles v1.** Árbol de Cyn (textual):

> «Chofer de recolección de residuos, chofer de camión recolector, conductor/a de camión de basura, chofer recolector, conductor/a de vehículo de recolección, chofer de higiene urbana, chofer de servicios ambientales, chofer de camión compactador, chofer de residuos domiciliarios, chofer de residuos urbanos, chofer de contenedores o transportista de residuos que conduce vehículos destinados a recoger basura, residuos, contenedores o materiales descartados en recorridos urbanos, industriales, comerciales o municipales corresponde a conductor/a de vehículo de recogida de basura; usar cuando el aviso se centra en conducir camiones recolectores, compactadores o vehículos de higiene urbana para realizar recorridos de recolección, carga de residuos, retiro de contenedores, traslado de basura o apoyo al servicio de limpieza urbana. Si el puesto conduce camiones para transportar mercadería, materiales, insumos, productos, cargas generales, encomiendas, pallets, áridos, maquinaria, alimentos, bebidas o carga de larga, media o corta distancia sin foco en residuos, corresponde a conductor/a de vehículo de carga; si realiza reparto urbano, distribución, entregas a clientes, paquetería, e-commerce, cadetería o reparto de mercadería con camioneta, utilitario, furgón, moto o vehículo liviano, corresponde a conductor/a de automóvil, taxi o furgoneta, repartidor/a o mensajero/a según el tipo de vehículo y la tarea dominante; si transporta pasajeros en colectivo, ómnibus, micro, combi, minibús, charter, transporte escolar, transporte de personal o servicios turísticos, corresponde a conductor/a de autobús o transporte de pasajeros según el vehículo y el servicio; si conduce taxi, remis, auto de aplicación, traslado ejecutivo, traslado particular de personas o chofer privado, corresponde a conductor/a de taxi o automóvil; si conduce ambulancia, móvil sanitario o vehículo de emergencias médicas, corresponde a conductor/a de ambulancia o transporte sanitario según el catálogo disponible; si maneja autoelevador, montacargas, zorra, apilador, reach, carretilla elevadora o equipos de movimiento interno dentro de depósito, planta, fábrica, puerto, centro logístico o almacén, no corresponde a chofer de ruta ni a conductor/a de vehículo de carga, sino a operador/a de carretilla elevadora o montacargas; si opera maquinaria vial, maquinaria pesada o equipos de obra como retroexcavadora, pala cargadora, motoniveladora, topadora, excavadora, grúa, hidrogrúa, camión volcador usado como equipo de obra, mixer, compactadora, rodillo, terminadora de asfalto o maquinaria similar, no corresponde automáticamente a chofer, sino a operador/a de maquinaria pesada, operador/a de maquinaria de movimiento de tierras, operador/a de grúa u oficio específico según el equipo y las tareas; si transporta combustibles, químicos, sustancias peligrosas, residuos patógenos, residuos peligrosos, cisternas, gases o materiales regulados, revisar si existe ocupación específica para transporte de mercancías peligrosas o residuos especiales y no usar carga general sin validar las tareas; si no conduce y solo acompaña al camión, levanta bolsas, carga residuos, barre, limpia, descarga, clasifica materiales o realiza tareas manuales de recolección, corresponde a recolector/a de residuos, peón/a de carga, estibador/a o trabajador/a de limpieza urbana según la tarea dominante; si el aviso combina conducción con tareas de depósito, carga y descarga, reparto, mantenimiento, cobranza, atención al cliente o gestión logística, se debe codificar por la tarea principal, el tipo de vehículo efectivamente conducido, la carga transportada y el contexto real del servicio.»

*Caso de evidencia:* Chofer de recolección de residuos | corrección previa decía `8332.2`
(conductor de vehículo de carga — genérico) | → `8332.8` conductor de vehículo de recogida
de basura. Denominaciones de la consolidada cargadas al diccionario (cosecha 2026-07-13,
todas → 8332.8).

---

# PARTE 4 — Familias PENDIENTES (para el próximo intercambio con Cyn)

| Familia | Qué hay | Qué falta |
|---|---|---|
| «coordinador» | «Coordinador de mantenimiento de flota» (MAL EXTRAIDA — bug NLP de título, sin tareas) · «Coordinador de servicios eléctricos» (fila vacía) | tareas reales + árbol + código |
| «director» | «Director/a de finanzas» (fila vacía; la familia conducción del Word cubre "dirige administración/finanzas → director financiero 1211.1" — confirmar si alcanza) | confirmación de Cyn |
| «monitoreo» | «Operador/a de monitoreo» (54 avisos): muestra heterogénea con 3 ramas detectadas — NOC/plataformas TIC (→3511.1, criterio original de Cyn), CCTV/seguridad, satelital/flota. NO se cargó plana (decisión Gerardo 2026-07-13); muestra en devoluciones | árbol de Cyn con las 3 ramas |
| «montador» | «Montador de estructuras de hormigón» — REQUIERE REVISION (nota de Cyn: «Realiza el montaje de estructuras de hormigón en obra, con traslado fuera de la localidad, trabajo en altura y experiencia en tareas de montaje») | código destino |
| «estudiante» (fuera de abogacía) | solo la rama abogacía definida | otras carreras si aparecen |
| ~12 filas incompletas Hoja 1 | denominaciones sin código ni árbol (listadas en devoluciones_para_cyn) | completar |

---

# ÍNDICE — conteo de familias

**Definidas (28):**
v1 conservadas (6): operario · técnico · arquitecto · pintor · editor · herrero/soldador.
Sesión Word (10): gerente/encargado/responsable/jefe (conducción, + rama obra del Excel) ·
operador/programador · analista (+ rama oficina técnica) · asesor/advisor/consultor ·
vendedor · estudiante de abogacía · auxiliar de promociones y marketing · supervisor
(instalación/obra, fusión Word-manda) · ingeniero (5 ramas: electrónico Word + civil,
eléctrico, automatización, electromecánico, instrumentación Excel) · medio oficial de
mantenimiento.
Lote REGLAS.xlsx (10): administrativo · electricista · encargado de edificio · responsable
de mantenimiento edilicio · aprendiz/trabajos verticales · sobrestante · instalador ·
ayudante · colocador · mampostero/albañil.
Respuesta post-punto-de-control (2, 2026-07-13): desarrollador · chofer/conductor.

**Pendientes-Cyn (4 familias + colas):** coordinador · director · montador · monitoreo (+ ramas
pendientes marcadas dentro de asesor, supervisor, ingeniero, técnico-telecomunicaciones;
+ ~12 filas incompletas de Hoja 1 → `exports/cyn_backlog/devoluciones_para_cyn_*.md`).

**Total catalogado: 32 familias-raíz (28 definidas / 4 pendientes).**

---

## Para cuando se ataque el Eje 4 (se conserva de v1)

- Estas reglas se expresan como **calificador del título/tareas → código** (ej. "técnico"
  + "redes/wifi" → 3513.2; "técnico" + "obra" → 7411.1.1). Es el patrón de las reglas de
  contexto que hoy NO existen para estas familias.
- El **código por defecto** de cada familia es el target cuando el aviso no especializa —
  candidato a entrada de diccionario plana SOLO si se confirma que la raíz sin calificador
  es estable (no es el caso de 'operario de producción', por eso quedó acá).
- Cruzar con los **104 override-duro** y el **fallback label-LIKE de `_resolve_rule_target`**
  (deuda P-01 reubicada): el Eje 4 es donde conviven todos.
- **v2:** la evidencia de error del matcher del lote REGLAS (57 pares extraído→correcto)
  está organizada en `exports/puente/evidencia_errores_matcher_REGLAS_2026-07-13.md` —
  mismo molde que los override-duro, insumo del diseño del traductor.
