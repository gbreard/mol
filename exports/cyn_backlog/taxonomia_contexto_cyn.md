# Taxonomía de contexto ocupacional argentina — escrita por Cyn (ACTIVO Eje 4)

> **Fuente:** `docs/export_validacion_denominaciones_cyn_2026-06-24-v1.xlsx`
> (hoja "Ambiguas por contexto") + GRUPO B de la hoja "Sin target". Procesado por el
> harness (`docs/DEVOLUCION_validacion_cyn_procesada.md`), archivado por SPEC S1C-G3.
> **2026-06-30.**

**Esto NO se carga al diccionario plano.** Cada denominación-raíz va a códigos ESCO
distintos **según las tareas del aviso** — cargar una plana rompería las demás (es lo que
hubiera pasado con "operario de producción → 72 ofertas"). Es la **especificación experta
de las reglas de contexto del Eje 4**: cuando se ataquen las reglas/desambiguación por
calificador, estos árboles son el insumo. Activo del Eje 4 junto a los 104 override-duro
y el fallback label-LIKE de `_resolve_rule_target` (deuda P-01 reubicada).

Formato: **denominación → código por defecto** (cuando el aviso no especializa) + *regla de
Cyn* (el árbol de "si las tareas son X → código Y").

---

## GRUPO B — denominación con DOS códigos según contexto (no al diccionario plano)

**'Sobrestante de obra'** apareció con dos targets según las tareas del aviso:

| si las tareas describen… | → código ESCO |
|---|---|
| dirección/coordinación de personal de obra | `3123.1.1` capataz de construcción |
| traslado/movimiento de materiales (operativo-logístico) | `8322.2` conductor de vehículo de reparto |

> Tercera oferta 'Sobrestante de obra / capataz' → `3123.1.1` (coordina personal) **sí**
> entró al GRUPO A: confirma la regla — dirección de personal ⇒ capataz; traslado de
> materiales ⇒ conductor. Esa es la regla de contexto implícita de Cyn.

---

## HOJA 2 — Árboles de desambiguación por familia (6 familias, 37 denominaciones)

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

## Para cuando se ataque el Eje 4

- Estas reglas se expresan como **calificador del título/tareas → código** (ej. "técnico"
  + "redes/wifi" → 3513.2; "técnico" + "obra" → 7411.1.1). Es el patrón de las reglas de
  contexto que hoy NO existen para estas familias.
- El **código por defecto** de cada familia es el target cuando el aviso no especializa —
  candidato a entrada de diccionario plana SOLO si se confirma que la raíz sin calificador
  es estable (no es el caso de 'operario de producción', por eso quedó acá).
- Cruzar con los **104 override-duro** y el **fallback label-LIKE de `_resolve_rule_target`**
  (deuda P-01 reubicada): el Eje 4 es donde conviven todos.
