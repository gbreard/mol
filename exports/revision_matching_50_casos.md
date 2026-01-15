# Revisión Manual de Matching - 50 Casos
**Fecha:** 2026-01-03

## Resumen Ejecutivo

| Clasificación | Cantidad | % |
|---------------|----------|---|
| ✅ CORRECTO | 28 | 56% |
| ⚠️ ACEPTABLE | 12 | 24% |
| ❌ INCORRECTO | 10 | 20% |

**Precisión efectiva:** 80% (correctos + aceptables)

---

## Análisis Detallado por Caso

### ✅ CORRECTOS (28 casos)

| # | ID | Título | Match ESCO | Método |
|---|-----|--------|------------|--------|
| 01 | 2091347 | CHOFER REPARTIDOR | Conductor de camión de reparto | diccionario_fuzzy |
| 03 | 2126626 | Supervisor Producción | Supervisor producción | diccionario_fuzzy |
| 04 | 2129707 | PASTELERA | Pastelero | diccionario_fuzzy |
| 07 | 2133690 | Vendedores Convencionales de Autos 0KM | vendedor especializado en vehículos de motor | bge_m3_semantico |
| 10 | 2143478 | Instructor de Informática | profesor de informática en educación secundaria | bge_m3_semantico |
| 11 | 2144019 | Preventista | Preventista | diccionario_exacto |
| 12 | 2144364 | ADMINISTRATIVA CONTABLE | Contador/contadora | regla_R14 |
| 14 | 2145271 | Técnico Mecánico o Ingeniero para coordinar proyectos | ingeniero mecánico | bge_m3_semantico |
| 16 | 2149320 | Customer Care Professional | Telefonista de centro de contacto | regla_R15 |
| 18 | 2149629 | Gerente de Sucursal | Gerente sucursal | diccionario_exacto |
| 22 | 2152906 | Representante Comercial | representante comercial | bge_m3_semantico |
| 24 | 2153307 | Oficina Técnica/Empresa Constructora | ingeniero de construcción | bge_m3_semantico |
| 25 | 2154046 | Enfermeros para atención domiciliaria | Enfermero/enfermera | regla_R13 |
| 26 | 2154549 | Contador/a para Sector Auditoría | Contador/contadora | regla_R14 |
| 29 | 2155532 | Representante de Ventas - Sector Industrial | representante comercial | bge_m3_semantico |
| 31 | 2156078 | Recepcionista bilingüe | recepcionista | bge_m3_semantico |
| 32 | 2156186 | Vendedor para concesionario de autos | vendedor especializado en vehículos de motor | bge_m3_semantico |
| 33 | 2156266 | Médica o Médico Auditor | médico especialista | bge_m3_semantico |
| 36 | 2157212 | Analista de Cuentas a Pagar | empleado de contabilidad | bge_m3_semantico |
| 37 | 2157265 | Promotoras/es de Tarjetas de Crédito | vendedor de servicios de telefonía | bge_m3_semantico |
| 38 | 2157453 | AYUDANTE DE COCINA | ayudante de cocina | bge_m3_semantico |
| 39 | 2157454 | ADMINISTRATIVO CONTABLE | Contador/contadora | regla_R14 |
| 40 | 1118026700 | VENDEDOR DE REPUESTOS AUTOMOTOR | vendedor de piezas de repuesto de automóviles | bge_m3_semantico |
| 43 | 1118026729 | Responsable de Depósito | jefe de almacén | bge_m3_semantico |
| 45 | 1118027276 | Ejecutivo de cuentas | Representante comercial | regla_R12 |
| 46 | 1118027941 | Dibujante Técnico | Delineante técnico | regla_R1 |
| 48 | 1118028027 | Operador/a de Autoelevadores | operador de carretilla elevadora | bge_m3_semantico |
| 49 | 1118028050 | Médico Oftalmólogo | médico especialista | bge_m3_semantico |

---

### ⚠️ ACEPTABLES (12 casos)
*Match semánticamente cercano pero con algún problema menor*

| # | ID | Título | Match ESCO | Problema |
|---|-----|--------|------------|----------|
| 02 | 2123908 | CAFETERIA (Cajeros, Baristas, Cocineros...) | cajero/cajera | Múltiples roles, solo detecta uno |
| 06 | 2131827 | Operario de Producción de Alimentos | operario de preparados cárnicos | Tipo de alimento muy específico |
| 08 | 2135143 | Operador SIM – Analista de IMPORTACION | director de importación y exportación | Nivel jerárquico incorrecto (analista→director) |
| 09 | 2143169 | Operario de Mantenimiento full time | técnico de mantenimiento de vehículos | Debería ser mantenimiento general |
| 15 | 2145519 | Operario de Mantenimiento (pintores, electricistas) | técnico de mantenimiento de vehículos | Debería ser mantenimiento edilicio |
| 19 | 2150503 | Asistente Creativo de Diseño y Contenido Visual | director creativo | Nivel incorrecto (asistente→director) |
| 21 | 2152531 | Líder de equipo comercial de atención telefónica | responsable de marketing | Es comercial/ventas, no marketing |
| 23 | 2153268 | Técnico Mecánico para Instructor de Mecánica | ingeniero mecánico | Nivel incorrecto (técnico→ingeniero) |
| 27 | 2154610 | VENDEDOR VIAJANTE DE AUTOS | operador de ventas | Alt3 "vendedor vehículos" era mejor |
| 34 | 2156357 | Analista de Marketing Digital | responsable de marketing digital | Nivel jerárquico elevado |
| 41 | 1118023904 | Coordinador/a de Ventas | director comercial | Nivel jerárquico elevado |
| 47 | 1118027970 | Asesor de Nutrición Animal | técnico veterinario | Debería ser "asesor técnico agropecuario" |

---

### ❌ INCORRECTOS (10 casos)
*Match claramente incorrecto que requiere corrección*

| # | ID | Título | Match ESCO | Match Correcto |
|---|-----|--------|------------|----------------|
| 05 | 2130257 | EMPLEADA/O VENTA MOSTRADOR CASA ELECTRICIDAD | demostrador de promociones | vendedor especializado en ferretería/electricidad |
| 13 | 2145263 | Consultor Junior de Liquidación de Sueldos | consultor de TIC | Analista de nóminas/Especialista payroll |
| 17 | 2149508 | Atención a Mostrador Pastelería / Barista | recepcionista | Barista / Vendedor pastelería |
| 20 | 2151075 | Asistente Compliance | asistente admin recaudación | Especialista en cumplimiento normativo |
| 28 | 2155040 | ENCARGADAS/OS - HELADERAS/OS - BARISTAS | empleado de lavandería | Barista / Heladero |
| 30 | 2155621 | Analista de Customer Service | especialista exportación perfumería | Analista de atención al cliente |
| 35 | 2156388 | Líder de Atención al Cliente | recepcionista | Supervisor de call center |
| 42 | 1118026719 | Project Manager IT | especialista exportación maquinaria | Director de proyectos TI |
| 44 | 1118027243 | Responsable de Legales | especialista bancario préstamos | Abogado / Gerente legal |
| 50 | 1118028168 | Coordinador de Instalaciones | ingeniero hogares inteligentes | Técnico de mantenimiento de instalaciones |

---

## Patrones de Error Identificados

### 1. Nivel Jerárquico Incorrecto
**Casos:** 08, 19, 21, 23, 34, 41
**Problema:** El matching no considera bien el nivel seniority
**Ejemplo:** "Asistente Creativo" → "Director Creativo"
**Solución:** Reforzar penalización por seniority mismatch

### 2. Área Funcional Ignorada
**Casos:** 13, 20, 30, 42, 44
**Problema:** El área funcional del NLP no filtra bien
**Ejemplo:** "Consultor Liquidación Sueldos" (RRHH) → "Consultor TIC" (IT)
**Solución:** Agregar reglas de negocio para payroll, compliance, legal

### 3. Títulos con Múltiples Roles
**Casos:** 02, 28
**Problema:** Títulos que mencionan varios puestos
**Ejemplo:** "Cajeros, Baristas, Sandwicheros, Cocineros" → solo detecta "cajero"
**Solución:** Priorizar el primer rol o el más relevante

### 4. Ocupaciones Gastronómicas/Servicios
**Casos:** 17, 28
**Problema:** Baristas, heladeros mal clasificados
**Solución:** Agregar regla R16 para gastronomía específica

### 5. Roles Legales/Compliance
**Casos:** 20, 44
**Problema:** Compliance y legales no tienen reglas
**Solución:** Agregar regla R17 para roles legales

---

## Acciones Recomendadas

### Alta Prioridad (10 casos incorrectos)
1. **Regla R16_gastronomia:** barista, heladero, pastelero mostrador
2. **Regla R17_legal:** compliance, legales, abogado
3. **Regla R18_payroll:** liquidación sueldos, nóminas, payroll
4. **Regla R19_project_manager:** project manager, PM, jefe de proyectos

### Media Prioridad (12 casos aceptables)
5. Ajustar penalización por seniority mismatch (asistente→director)
6. Agregar "operario mantenimiento" al diccionario argentino

---

## Métricas por Método

| Método | Total | ✅ | ⚠️ | ❌ |
|--------|-------|-----|-----|-----|
| bge_m3_semantico | 37 | 18 | 11 | 8 |
| diccionario_exacto/fuzzy | 5 | 5 | 0 | 0 |
| reglas_negocio | 8 | 7 | 1 | 0 |

**Conclusión:** Las reglas de negocio y diccionario tienen 100% precisión. El matching semántico tiene 49% correcto, 30% aceptable, 22% incorrecto.
