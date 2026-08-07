# [FRENTE H — P2] Informe de validación RE-VALIDADO (v0.3.0) — 2026-08-07

> Post-gate: verificación (0) resuelta, ajustes 1-2 aplicados, matches re-atribuidos al hub ganador.

## Verificación (0) — los "decididos con matches vacíos": ERA ARTEFACTO DEL INFORME

El evaluador SIEMPRE decide con traza de match (contrato cumplido). El informe original
mostraba, para cada caso, los matches del hub de la SECCIÓN — pero en el vecindario multi-hub
la decisión puede venir de OTRO hub (el que redirige). Cuando hub-ganador ≠ hub-sección, la
columna quedaba vacía. Ej: «Empleada Administrativa contable» (sección 3313.2) decide por el
hub 2411.1.1 (su D01, match `carga de facturas@tareas` → redirige a 3313.2). Fix: la columna
ahora toma los matches del hub ganador. **Decididos con matches vacíos tras el fix: 0.**

## Ajustes aplicados (gate b)

1. **D06 hub 1** (asesor fiscal): `principalmente`+`impuestos` bare → **min_matches:2** con
   términos fiscales específicos. Efecto: 2 casos que decidían MAL hacia asesor fiscal
   («Analista contable.», «ASISTENTE CONTABLE» — genéricos con "impuestos") ahora no-fuerzan.
2. **~23 variantes de anclaje** en las inclusiones de 3322.1/5223.4/3313.2/4312.1. Efecto:
   4 casos reales recuperados (Vendedor Viajante, Agente Comercial, Analista de Auditoría Interna).
3. **Regresión cazada y revertida**: la variante "control de lo facturado" (4312.1) capturaba
   «Auditor Médico» → auditor financiero (es territorio de la regla plana R62→médico). Removida;
   Auditor Médico vuelve a familia_sin_rama (correcto).

## Diff de re-validación (125 casos comunes, 8 cambios de estado)

| Título | Antes | Después | Match ganador |
|---|---|---|---|
| Administrativo Contable /Estud.Avanzad | evidencia_mixta(—) | decidido(2411.1) | liquidacion de impuestos@tareas, impuestos@tareas |
| GERENTE ADMINISTRATIVO CONTABLE (Cia.  | decidido(2411.1.12) | decidido(2411.1.1) | elaborar reportes contables@tareas |
| ASISTENTE CONTABLE | decidido(2411.1.12) | familia_sin_rama(—) | — |
| Vendedor Viajante/Itinerante | familia_sin_rama(—) | decidido(5223.4) | asesorar@skills, ofrecer productos@tareas |
| Agente Comercial / FULL TIME - Belgran | familia_sin_rama(—) | decidido(3322.1) | comercializar@sistemas, desarrollar relaciones comerciales@tareas |
| Vendedor Viajante Técnico – Región NOA | familia_sin_rama(—) | decidido(3322.1) | negociacion@skills, visitar prospectos@tareas |
| Analista contable. | decidido(2411.1.12) | familia_sin_rama(—) | — |
| Analista de Auditoría Interna | familia_sin_rama(—) | decidido(4312.1) | control interno@tareas, garantizar la fiabilidad@tareas |

**Resumen global v0.3.0:** decidido 66 · familia_sin_rama 55 · evidencia_mixta 4 (de 125 casos)

## Estado de congelamiento

- **Congelados v0.3.0 (validados, 7 hubs):** 2411.1.1, 2411.1, 3313.2, 4312.1, 1211.1.1, 3322.1, 5223.4.
- **Propuesta, NO congelados (3 hubs, muestra corta → shadow P3):** 2411.1.9 (auditor forense, 2 casos), 4110.1 (empleado oficina/obra, 3 casos), 5223.7 (vendedor especializado, 4 casos).

## Secciones por hub (con matches del ganador)


### [1] Analista contable (`2411.1.1`) — 8 casos — congelado

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Analista contable. | — | — | — | familia_sin_rama |
| Analista Contable | — | — | — | familia_sin_rama |
| Analista Contable (SAP excluyente) | 3313.2 | D01 | asientos@tareas, conciliaciones@tareas | decidido |
| Analista Contable | — | — | — | familia_sin_rama |
| Contador junior ambos sexos | — | — | — | familia_sin_rama |
| Contador Junior | 4311.1 | D02 | facturación@tareas | decidido |
| Administrativo Contable y/o Contador Jun | — | — | — | familia_sin_rama |
| Contador Junior/estudiante avanzado | — | — | — | familia_sin_rama |

### [2] Contable (`2411.1`) — 17 casos — congelado

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Contador o estudiante | 3313.2 | D02 | libros contables@tareas | decidido |
| Contador/a recibido impositivo | — | — | — | familia_sin_rama |
| Contador o estudiante avanzado de CsEc p | 2411.1 | inclusion | liquidacion de impuestos@tareas, impuestos@tareas | decidido |
| Responsable Contable | — | — | — | familia_sin_rama |
| Responsable contable | — | — | — | familia_sin_rama |
| Responsable contable | 2411.1 | inclusion | impuestos@skills, cierres contables@tareas | decidido |
| Responsable Contable | 3313.2 | D02 | libro mayor@skills | decidido |
| Contadora Pública con experiencia | 2411.1 | inclusion | estados contables@tareas, cierres contables@tareas | decidido |
| EMPRESA CYLGEM S.A RUBRO ELECTRONICA EST | 3313.2 | D02 | conciliaciones@tareas | decidido |
| Contadora Impositiva Ssr | — | — | — | familia_sin_rama |
| Contadora | 3313.2 | D02 | registraciones@tareas, conciliaciones@tareas | decidido |
| Administrativo contable generalista/cba  | 4311.1 | D02 | facturación@tareas | decidido |
| Administrativo Contable Generalista. Zon | 3343.1 | D03 | tareas administrativas generales@tareas | decidido |
| Analista Contable Generalista | 4311.1 | D02 | facturación@tareas | decidido |
| Administrativa Contable generalista | 4311.1 | D03 | facturacion@tareas | decidido |
| Estudiante/Profesional Contable | 2411.1 | inclusion | liquidacion de impuestos@tareas, impuestos@tareas | decidido |
| Profesional contable Ssr. (con foco en i | 3313.2 | D02 | registraciones@tareas, conciliaciones@tareas | decidido |

### [3] Administrativo contable/administrativa contable (`3313.2`) — 19 casos — congelado

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| auxiliar administrativo contable | 4311.1 | D02 | facturación@skills | decidido |
| Administrativo Contable /Estud.Avanzado  | 2411.1 | inclusion | liquidacion de impuestos@tareas, impuestos@tareas | decidido |
| Administrativo contable | 4311.1 | D02 | emitir facturas@skills, facturación@skills, notas de crédito@tar | decidido |
| GERENTE ADMINISTRATIVO CONTABLE (Cia. de | 2411.1.1 | inclusion | elaborar reportes contables@tareas | decidido |
| SECRETARIA ADMINISTRATIVA CONTABLE | — | — | — | familia_sin_rama |
| Encargada Administrativa Contable | — | — | — | evidencia_mixta |
| Empleada Administrativa contable | 3313.2 | D01 | carga de facturas@tareas | decidido |
| Administrativa Contable. Asistente | 4311.1 | D03 | emitir facturas@skills | decidido |
| Asistente Contable | — | — | — | familia_sin_rama |
| Asistente Contable/Impositivo | 3313.2 | D01 | registraciones@tareas | decidido |
| ASISTENTE CONTABLE | — | — | — | familia_sin_rama |
| Asistente Contable | — | — | — | evidencia_mixta |
| Auxiliar Contable | 4311.1 | D03 | facturacion@skills | decidido |
| Auxiliar Contable con Experiencia en Sis | — | — | — | familia_sin_rama |
| Auxiliar Contable | 3313.2 | inclusion | asientos@tareas, asientos contables@tareas, conciliaciones@tarea | decidido |
| auxiliar contable | 2411.1.1 | D01 | analisis de cuentas contables@tareas | decidido |
| Administrativa de facturacion y cobranza | 3343.1 | D05 | tareas administrativas generales@tareas | decidido |
| EMPLEADO CONTABLE CON EXPERIENCIA EN MAN | — | — | — | familia_sin_rama |
| Administrativo de facturación y cobranza | — | — | — | familia_sin_rama |

### [4] Auditor/auditora (`4312.1`) — 11 casos — congelado

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| CG Soluciones Humanas selecciona Supervi | 3343.1 | D05 | archivo@tareas, planillas@tareas | decidido |
| 624 BE | SENIOR AUDITOR | FINANCIAL | BA | — | — | — | familia_sin_rama |
| Jefe Auditor de Obras Sociales con exper | — | — | — | familia_sin_rama |
| Auditor Médico | — | — | — | familia_sin_rama |
| Analista de Auditoría Interna - Paternal | — | — | — | familia_sin_rama |
| Analista de Auditoría Interna | — | — | — | familia_sin_rama |
| Analista de Auditoría Interna | 4312.1 | inclusion | control interno@tareas, auditoria interna@skills, garantizar la  | decidido |
| Analista de Auditoría Interna | 4312.1 | inclusion | control interno@tareas, garantizar la fiabilidad@tareas, fiabili | decidido |
| ABOGADA AUDITORA EXTERNA-SAN FERNANDO | — | — | — | familia_sin_rama |
| Supervisora  Auditora de Clientes (BOPE) | — | — | — | familia_sin_rama |
| Auditora Bioquímica | — | — | — | familia_sin_rama |

### [15] director de contabilidad/directora de contabilidad (`1211.1.1`) — 22 casos — congelado

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Responsable de Administración y Finanzas | — | — | — | familia_sin_rama |
| Responsable de Administración y Finanzas | — | — | — | familia_sin_rama |
| Responsable de Administración y Finanzas | — | — | — | familia_sin_rama |
| RESPONSABLE DE ADMINISTRACIÓN Y FINANZAS | 4311.1 | D05 | facturacion@tareas | decidido |
| Jefe de Contabilidad, Costos y control d | — | — | — | familia_sin_rama |
| Jefe de Contabilidad | — | — | — | familia_sin_rama |
| Jefe de Contabilidad | 1211.1.1 | inclusion | conciliaciones@tareas, cierres@tareas, cierres contables@tareas, | decidido |
| Jefe de Contabilidad | — | — | — | familia_sin_rama |
| Responsable de Contabilidad Global | 1211.1.1 | inclusion | conciliaciones@tareas, cierres@tareas, cierres contables@tareas, | decidido |
| Responsable de Contabilidad y Administra | 1211.1.1 | inclusion | cierres@tareas, cierres contables@tareas, balances@tareas | decidido |
| Responsable de contabilidad | 1211.1.1 | inclusion | cierres@tareas, cierres contables@tareas | decidido |
| Responsable de Contabilidad y Administra | 1211.1.1 | inclusion | cierres@tareas, cierres contables@tareas, balances@tareas | decidido |
| Coordinador Contable | 2411.1.1 | D03 | analisis de cuentas@tareas | decidido |
| Coordinador contable | — | — | — | familia_sin_rama |
| Coordinador Contable | — | — | — | familia_sin_rama |
| Coordinador contable | — | — | — | familia_sin_rama |
| Coordinador de Administración y Contabil | 1211.1.1 | inclusion | conciliaciones@tareas, cierres@tareas, cierres contables@tareas, | decidido |
| Coordinador de Administración y Contabil | — | — | — | familia_sin_rama |
| Coordinador de Administración y Contabil | — | — | — | familia_sin_rama |
| Gerente de contabilidad | 4311.1 | D05 | facturacion@skills | decidido |
| Gerente de Contabilidad | 1211.1.1 | inclusion | balances@tareas, impuestos@tareas | decidido |
| gerente de contabilidad | 1211.1 | D07 | inversiones@tareas | decidido |

### [36] auditor forense/auditora forense (`2411.1.9`) — 2 casos — PROPUESTA (a shadow)

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Compliance/Forensic Auditor - Americas | — | — | — | familia_sin_rama |
| Compliance/Forensic Auditor - Americas | — | — | — | familia_sin_rama |

### [58] empleado de oficina/empleada de oficina (`4110.1`) — 3 casos — PROPUESTA (a shadow)

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Administrativo de obras | 4110.1 | inclusion | presentismo@tareas, fondos fijos@tareas, pedidos de materiales@t | decidido |
| Administrativo de Obras | — | — | — | familia_sin_rama |
| Administrativo de construccion | — | — | — | familia_sin_rama |

### [16] representante comercial (`3322.1`) — 24 casos — congelado

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Ejecutivo Comercial - Prospección y Desa | 3322.1 | inclusion | prospeccion@tareas, cotizaciones@tareas, negociar precios@skills | decidido |
| Ejecutivo Comercial | 2422.18 | D08 | desarrollo de canales@tareas | decidido |
| Ejecutivo Comercial de Cuentas (Calle) - | 2433.6 | D01 | asesoramiento tecnico@tareas, venta tecnica@skills | decidido |
| Ejecutivo Comercial | 3322.1 | inclusion | fidelizar@tareas, cartera de clientes@tareas, oportunidades come | decidido |
| Ejecutivo de Ventas | 3322.1 | inclusion | presentacion de productos@tareas, prospeccion@tareas, fidelizaci | decidido |
| EJECUTIVO DE VENTAS (Exclusivo Comercio  | 4110.1 | D13 | seguir instrucciones@skills | decidido |
| Ejecutivo de Ventas Semi Senior | 3322.1 | inclusion | prospeccion@tareas, cartera de clientes@tareas, oportunidades co | decidido |
| EJECUTIVO DE VENTAS CONVENCIONALES - FOR | 5244.1 | D05 | venta telefonica@tareas | decidido |
| EJECUTIVO DE CUENTAS INTERNACIONAL | — | — | — | familia_sin_rama |
| Ejecutivo de Cuentas - Johnson Acero S.A | 2422.18 | D08 | distribuidores@tareas | decidido |
| Ejecutivo de Cuentas Comercial | — | — | — | familia_sin_rama |
| Ejecutivo de cuentas | — | — | — | familia_sin_rama |
| Vendedor Viajante/Itinerante | 5223.4 | inclusion | asesorar@skills, ofrecer productos@tareas | decidido |
| Vendedor viajante | 4225.1 | D12 | consultas@skills | decidido |
| Vendedor Viajante | 4225.1 | D12 | consultas@skills | decidido |
| Representante de Ventas Comercial | — | — | — | familia_sin_rama |
| Representante de Ventas - Bahia Blanca | 5244.1 | D05 | llamados@tareas, venta telefonica@tareas | decidido |
| Representante de Ventas Rosario | 3322.1 | inclusion | comercializacion@skills, negociacion@skills, desarrollar relacio | decidido |
| Representante de ventas | — | — | — | familia_sin_rama |
| Agente Comercial Técnico - Energía Renov | — | — | — | familia_sin_rama |
| Agente Comercial / FULL TIME - Belgrano  | 3322.1 | inclusion | comercializar@sistemas, desarrollar relaciones comerciales@tarea | decidido |
| Agente comercial de Seguros- Zona CABA | 3322.1 | inclusion | fidelizacion@tareas, propuestas comerciales@tareas | decidido |
| agente comercial | 3322.1 | inclusion | fidelizar@tareas, fidelizacion@skills, cartera de clientes@tarea | decidido |
| Vendedor Corporativo - Importante Corral | — | — | — | evidencia_mixta |

### [51] vendedor/vendedora (`5223.4`) — 15 casos — congelado

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Vendedor Viajante Técnico – Región NOA ( | 3322.1 | inclusion | negociacion@skills, visitar prospectos@tareas | decidido |
| Vendedor/a de seguros part time San Juan | 5223.4 | inclusion | atencion al cliente@skills, asesoramiento@tareas, cierre de vent | decidido |
| Vendedor técnico | 5223.4 | inclusion | asesoramiento@tareas, asesorar@skills | decidido |
| Vendedor/a mayorista rubro aberturas. Is | 3322.1 | D11 | prospeccion@tareas, cartera de clientes@tareas, negociar precios | decidido |
| Vendedora en Shopping - Zona Norte | — | — | — | familia_sin_rama |
| VENDEDORA con experiencia en venta y ate | — | — | — | familia_sin_rama |
| Vendedora Recoleta Full time | 5223.7.4 | D03 | pasteleria@tareas | decidido |
| Vendedora / Telemarketer | 5244.1 | D10 | llamadas@tareas, ventas telefonicas@skills | decidido |
| Personal de Atencion al Publico en Estac | — | — | — | familia_sin_rama |
| Personal de Atencion al Publico en Farma | 5223.6 | D01 | reposicion@tareas, control de stock@tareas, orden y limpieza del | decidido |
| Personal de Atencion al Publico | — | — | — | familia_sin_rama |
| Personal de Atencion al Publico en Venta | — | — | — | familia_sin_rama |
| ASISTENTE DE VENTA | — | — | — | familia_sin_rama |
| ASISTENTE DE VENTA | — | — | — | familia_sin_rama |
| Asistente de Venta para sucursal en Zona | — | — | — | familia_sin_rama |

### [52] vendedor especializado/vendedora especializada (`5223.7`) — 4 casos — PROPUESTA (a shadow)

| Título | Decisión | Regla | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Vendedor Especializado Hogar y Equipamie | 5223.6 | D01 | colocacion de precios@tareas, etiquetado@skills | decidido |
| Vendedor Especializado en Neumáticos par | — | — | — | evidencia_mixta |
| vendedor especializado | — | — | — | familia_sin_rama |
| Vendedor especializado en destilados,vin | — | — | — | familia_sin_rama |