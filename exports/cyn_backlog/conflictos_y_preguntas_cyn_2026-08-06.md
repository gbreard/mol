# Conflictos y preguntas para Cyn — 2026-08-06 (FRENTE H, P0.b)

> Material listo para reenviar. Tres bloques: (1) los 5 títulos donde el diccionario
> vigente y las 88 reglas consolidadas dicen códigos distintos — ambas fuentes citadas,
> la decisión de precedencia es tuya; (2-3) dos preguntas de trazabilidad del JSON 2.0.
> Las entradas en conflicto NO se compilan al traductor hasta tu respuesta.

## Bloque 1 — Conflictos diccionario ↔ reglas consolidadas

### 1. «administrativo/a contable»

- **Regla consolidada 3** → `3313.2` Administrativo contable/administrativa contable
  > «Los títulos de aviso administrativo/a contable, empleado/a contable, auxiliar contable, asistente contable, tenedor/a de libros, administrativo/a contable SSR o administrativo/a de facturación y cobranzas corresponden a “administrativo contable/administrativa contable” cuando el eje principal es registrar y reunir las operaciones financieras cotidianas de una empresa —ventas, compras, pagos e ingr…»

- **Diccionario vigente** (entrada `administrativo contable`) → (solo isco 4311) — empleado de contabilidad/empleada de contabilidad

**Pregunta:** ¿cuál de los dos destinos corresponde para este título, o bajo qué condición cada uno?

### 2. «vendedor/a mayorista»

- **Regla consolidada 16** → `3322.1` representante comercial
  > «Los títulos de aviso ejecutivo/a de ventas, ejecutivo/a comercial, ejecutivo/a de cuentas, asesor/a comercial B2B, representante de ventas, agente comercial, vendedor/a corporativo/a, vendedor/a mayorista, vendedor/a viajante, ejecutivo/a de canal o ejecutivo/a de desarrollo de clientes corresponden a “representante comercial” —3322.1— cuando el eje principal es comercializar bienes o servicios pa…»

- **Diccionario vigente** (entrada `vendedor mayorista`) → (solo isco 5223) — vendedor especializado/vendedora especializada

**Pregunta:** ¿cuál de los dos destinos corresponde para este título, o bajo qué condición cada uno?

### 3. «jefe/a de mantenimiento»

- **Regla consolidada 67** → `3115.1.6` supervisor de mantenimiento industrial/supervisora de mantenimiento industrial
  > «Supervisor/a de mantenimiento, jefe/a de mantenimiento, coordinador/a de mantenimiento, líder técnico/a de campo o coordinador/a de instalaciones y reparaciones corresponde a “supervisor de mantenimiento industrial/supervisora de mantenimiento industrial” (3115.1.6) cuando planifica y controla el mantenimiento preventivo y correctivo de maquinaria, equipos o sistemas industriales; organiza inspecc…»

- **Diccionario vigente** (entrada `jefe de mantenimiento`) → (solo isco 1219) — director de mantenimiento de una fábrica/directora de mantenimiento de una fábrica

**Pregunta:** ¿cuál de los dos destinos corresponde para este título, o bajo qué condición cada uno?

### 4. «operario/a de depósito»

- **Regla consolidada 75** → `9333.3` operario de logística de almacén/operaria de logística de almacén
  > «Operario/a de logística, operario/a de depósito, operario/a de carga y descarga, peón/a de depósito, auxiliar de depósito, mozo/a de almacén, empleado/a de almacén o trabajador/a eventual de logística corresponde a “operario de logística de almacén/operaria de logística de almacén” —9333.3— cuando realiza tareas operativas y físicas de recepción, carga, descarga, traslado, manipulación, clasificac…»

- **Diccionario vigente** (entrada `operario de deposito`) → (solo isco 9333) — mozo de almacén/moza de almacén

**Pregunta:** ¿cuál de los dos destinos corresponde para este título, o bajo qué condición cada uno?

### 5. «técnico/a de servicio técnico industrial»

- **Regla consolidada 78** → `3113.1.2` ingeniero técnico en electromecánica/ingeniera técnica en electromecánica
  > «Técnico/a electromecánico/a, técnico/a de mantenimiento electromecánico, técnico/a de servicio técnico industrial, técnico/a de campo, técnico/a posventa, técnico/a instalador/a de maquinaria o técnico/a de reparación de equipos industriales corresponde a “ingeniero técnico en electromecánica/ingeniera técnica en electromecánica” —3113.1.2— cuando instala, monta, pone en funcionamiento, prueba, in…»

- **Diccionario vigente** (entrada `técnico de servicio técnico industrial`) → 7412.3 — mecánico electricista/mecánica electricista

**Pregunta:** ¿cuál de los dos destinos corresponde para este título, o bajo qué condición cada uno?

## Bloque 2 — Trazabilidad de las 4 reglas ajustadas (904 → 900)

El resumen del JSON 2.0 declara «reglas_desambiguacion_duplicadas_equivalentes_eliminadas: 3»
y «referencias_no_operativas_separadas: 1», pero el archivo no dice CUÁLES. Para el registro
de compilación necesitamos que Juan Domingo liste: las 3 D eliminadas como duplicadas
(de qué ocupación, qué decían) y la 1 referencia separada como no operativa.

## Bloque 3 — La regla 11 (coordinador de transporte, 4323.9) llegó con 0 desambiguaciones

Su prosa en el Excel deriva ~10 destinos («corresponde a X; si…, a Y»), pero en el JSON 2.0
la ocupación 11 tiene `reglas_desambiguacion: []`. ¿Se perdieron en la generación o es
intencional? Si es pérdida, ¿puede Juan Domingo regenerar esa ocupación?
