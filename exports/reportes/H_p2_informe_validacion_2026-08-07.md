# [FRENTE H — P2] Informe de validación por casos, por hub — 2026-08-07

> **PUNTO DE CONTROL (el gate):** nada se congela ni activa hasta el OK de Gerardo
> sobre este informe. 139 casos reales muestreados estratificadamente por trigger
> (máx. 4 por título distinto, hasta 25 por hub), evaluados en memoria con el léxico
> v0.2.0-propuesta + hub 1 del modelo 1.1. Contenidos mapeados del NLP:
> tareas_explicitas · skills (técnicas+soft) · conocimientos_especificos ·
> tecnologias_list · herramientas_list.

## Resumen global

| Estado | Casos | % |
|---|---|---|
| decidido | 70 | 50,4% |
| familia_sin_rama (no_forzar) | 60 | 43,2% |
| evidencia_mixta (no_forzar) | 9 | 6,5% |

Lectura: mitad decide con traza completa; el no-forzar restante se reparte entre
**correcto-conservador** (evidencia fina, territorio de otras reglas, inglés) y
**anclaje mejorable** (variantes que faltan — lista concreta por hub abajo).
Ningún caso decidió hacia un destino disparatado en la revisión manual.


## [1] Analista contable (`2411.1.1`) — 20 casos

**Observaciones:** 10/20 deciden. LO BUENO: «Analista Contable (SAP)»→3313.2 por D01 (registrar-asientos predominante) — el anti-captura D-primero funcionando; convergencia multi-hub real en «auxiliar administrativo contable»→4311.1. ⚠ AJUSTE PROPUESTO: D06 (asesor fiscal) decidió con UN solo match ('impuestos') una oferta de cuentas-corrientes-y-pagos — la D del modelo 1.1 quedó laxa; subir a min_matches:2 o exigir término fiscal específico. Los 7 sin-rama: 4 con tareas genéricas finas (no-forzar correcto), 3 con vocabulario no anclado ('registración contable', 'armado de balances') — variantes a agregar.

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Analista contable. | 2411.1.12 asesor fiscal/asesora fi | D06/D_directa | impuestos@tareas | decidido |
| Analista Contable | — | —/— | — | familia_sin_rama |
| Analista Contable (SAP excluyente) | 3313.2 administrativo contable/ | D01/D_directa | asientos@tareas, conciliaciones@tareas | decidido |
| Analista Contable | — | —/— | — | familia_sin_rama |
| auxiliar administrativo contable | 4311.1 empleado de contabilidad | D02/convergencia | facturación@skills | decidido |
| Administrativo Contable /Estud.Avanzado Cont | — | —/— | impuestos@tareas | evidencia_mixta ⚔['2411.1', '2411.1.12'] |
| Administrativo contable | 4311.1 empleado de contabilidad | D02/convergencia | emitir facturas@skills, facturación@skills, notas de crédito@tareas | decidido |
| GERENTE ADMINISTRATIVO CONTABLE (Cia. de Seg | 2411.1.12 asesor fiscal/asesora fi | D06/D_directa | impuestos@skills | decidido |
| SECRETARIA ADMINISTRATIVA CONTABLE | — | —/— | — | familia_sin_rama |
| Encargada Administrativa Contable | — | —/— | asientos@tareas, conciliaciones@tareas | evidencia_mixta ⚔['3313.2', '4311.1'] |
| Empleada Administrativa contable | 3313.2 administrativo contable/ | D01/D_directa | carga de facturas@tareas | decidido |
| Administrativa Contable. Asistente | 4311.1 empleado de contabilidad | D03/D_directa | — | decidido |
| Asistente Contable | — | —/— | — | familia_sin_rama |
| Asistente Contable/Impositivo | 3313.2 administrativo contable/ | D01/D_directa | registraciones@tareas | decidido |
| ASISTENTE CONTABLE | 2411.1.12 asesor fiscal/asesora fi | D06/D_directa | impuestos@tareas | decidido |
| Asistente Contable | — | —/— | legislación fiscal@skills, impuestos@skills | evidencia_mixta ⚔['2411.1.12', '3313.2'] |
| Contador junior ambos sexos | — | —/— | — | familia_sin_rama |
| Contador Junior | 4311.1 empleado de contabilidad | D02/D_directa | facturación@tareas | decidido |
| Administrativo Contable y/o Contador Junior | — | —/— | — | familia_sin_rama |
| Contador Junior/estudiante avanzado | — | —/— | — | familia_sin_rama |

## [2] Contable (`2411.1`) — 18 casos

**Observaciones:** 13/18 deciden — el hub más sano. Redirecciones limpias a analista/administrativo/nóminas. Sin ajustes urgentes.

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Contador o estudiante | 3313.2 administrativo contable/ | D02/D_directa | libros contables@tareas | decidido |
| Contador/a recibido impositivo | — | —/— | — | familia_sin_rama |
| Administrativo Contable /Estud.Avanzado Cont | — | —/— | liquidacion de impuestos@tareas, impuestos@tareas | evidencia_mixta ⚔['2411.1', '2411.1.12'] |
| Contador o estudiante avanzado de CsEc para  | 2411.1 contable | inclusion/inclusion | liquidacion de impuestos@tareas, impuestos@tareas | decidido |
| Responsable Contable | — | —/— | — | familia_sin_rama |
| Responsable contable | — | —/— | — | familia_sin_rama |
| Responsable contable | 2411.1 contable | inclusion/inclusion | impuestos@skills, cierres contables@tareas | decidido |
| Responsable Contable | 3313.2 administrativo contable/ | D02/D_directa | libro mayor@skills | decidido |
| Contadora Pública con experiencia | 2411.1 contable | inclusion/inclusion | estados contables@tareas, cierres contables@tareas | decidido |
| EMPRESA CYLGEM S.A RUBRO ELECTRONICA ESTA EN | 3313.2 administrativo contable/ | D02/D_directa | conciliaciones@tareas | decidido |
| Contadora Impositiva Ssr | — | —/— | — | familia_sin_rama |
| Contadora | 3313.2 administrativo contable/ | D02/D_directa | registraciones@tareas, conciliaciones@tareas | decidido |
| Administrativo contable generalista/cba capi | 4311.1 empleado de contabilidad | D02/convergencia | facturacion@tareas | decidido |
| Administrativo Contable Generalista. Zona Pa | 3343.1 empleado administrativo/ | D03/D_directa | — | decidido |
| Analista Contable Generalista | 4311.1 empleado de contabilidad | D02/convergencia | facturacion@tareas | decidido |
| Administrativa Contable generalista | 4311.1 empleado de contabilidad | D03/D_directa | — | decidido |
| Estudiante/Profesional Contable | 2411.1 contable | inclusion/inclusion | liquidacion de impuestos@tareas, impuestos@tareas | decidido |
| Profesional contable Ssr. (con foco en impue | 3313.2 administrativo contable/ | D02/D_directa | registraciones@tareas, conciliaciones@tareas | decidido |

## [3] Administrativo contable/administrativa contable (`3313.2`) — 19 casos

**Observaciones:** 11/19 deciden. Convergencias correctas con hubs 1/2. Las 3 evidencia_mixta son títulos dobles genuinos («administrativo contable y RRHH») — no-forzar defendible. 5 sin-rama por anclaje ('carga de facturas' vs 'carga de comprobantes') — variantes a agregar.

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| auxiliar administrativo contable | 4311.1 empleado de contabilidad | D02/convergencia | facturacion@skills | decidido |
| Administrativo Contable /Estud.Avanzado Cont | — | —/— | — | evidencia_mixta ⚔['2411.1', '2411.1.12'] |
| Administrativo contable | 4311.1 empleado de contabilidad | D02/convergencia | emitir facturas@skills, emision de facturas@tareas, facturacion@skills | decidido |
| GERENTE ADMINISTRATIVO CONTABLE (Cia. de Seg | 2411.1.12 asesor fiscal/asesora fi | D06/D_directa | — | decidido |
| SECRETARIA ADMINISTRATIVA CONTABLE | — | —/— | — | familia_sin_rama |
| Encargada Administrativa Contable | — | —/— | facturacion@tareas | evidencia_mixta ⚔['3313.2', '4311.1'] |
| Empleada Administrativa contable | 3313.2 administrativo contable/ | D01/D_directa | — | decidido |
| Administrativa Contable. Asistente | 4311.1 empleado de contabilidad | D03/D_directa | emitir facturas@skills | decidido |
| Asistente Contable | — | —/— | — | familia_sin_rama |
| Asistente Contable/Impositivo | 3313.2 administrativo contable/ | D01/D_directa | — | decidido |
| ASISTENTE CONTABLE | 2411.1.12 asesor fiscal/asesora fi | D06/D_directa | — | decidido |
| Asistente Contable | — | —/— | registros contables@skills, conciliaciones@tareas | evidencia_mixta ⚔['2411.1.12', '3313.2'] |
| Auxiliar Contable | 4311.1 empleado de contabilidad | D03/D_directa | facturacion@skills | decidido |
| Auxiliar Contable con Experiencia en Sistema | — | —/— | — | familia_sin_rama |
| Auxiliar Contable | 3313.2 administrativo contable/ | inclusion/inclusion | asientos@tareas, asientos contables@tareas, conciliaciones@tareas | decidido |
| auxiliar contable | 2411.1.1 analista contable | D01/D_directa | analisis de cuentas contables@tareas | decidido |
| Administrativa de facturacion y cobranzas | 3343.1 empleado administrativo/ | D05/D_directa | tareas administrativas generales@tareas | decidido |
| EMPLEADO CONTABLE CON EXPERIENCIA EN MANEJO  | — | —/— | — | familia_sin_rama |
| Administrativo de facturación y cobranzas | — | —/— | — | familia_sin_rama |

## [4] Auditor/auditora (`4312.1`) — 11 casos

**Observaciones:** Solo 2/11 deciden — el hub más estricto. Los 9 sin-rama se parten en: 3 CORRECTOS (Auditor Médico → territorio de la regla plana R62; ofertas en inglés — gap conocido), 6 por términos de auditoría demasiado formales ('papeles de trabajo', 'gobernanza') vs vocabulario real ('liderar equipo de auditoría', 'control de lo facturado'). AJUSTE: ampliar variantes de inclusión.

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| CG Soluciones Humanas selecciona Supervisor/ | 3343.1 empleado administrativo/ | D05/D_directa | archivo@tareas, planillas@tareas | decidido |
| 624 BE | SENIOR AUDITOR | FINANCIAL | BANKIN | — | —/— | — | familia_sin_rama |
| Jefe Auditor de Obras Sociales con experienc | — | —/— | — | familia_sin_rama |
| Auditor Médico | — | —/— | — | familia_sin_rama |
| Analista de Auditoría Interna - Paternal (CA | — | —/— | — | familia_sin_rama |
| Analista de Auditoría Interna | — | —/— | — | familia_sin_rama |
| Analista de Auditoría Interna | 4312.1 auditor/auditora | inclusion/inclusion | control interno@tareas, auditoria interna@skills | decidido |
| Analista de Auditoría Interna | — | —/— | — | familia_sin_rama |
| ABOGADA AUDITORA EXTERNA-SAN FERNANDO | — | —/— | — | familia_sin_rama |
| Supervisora  Auditora de Clientes (BOPE) | — | —/— | — | familia_sin_rama |
| Auditora Bioquímica | — | —/— | — | familia_sin_rama |

## [15] director de contabilidad/directora de contabilidad (`1211.1.1`) — 22 casos

**Observaciones:** 11/22 deciden. Los sin-rama: mayormente jefaturas contables con tareas escuetas — conservador razonable. D15 (primer ejecutivo) nunca disparó: bien.

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Responsable de Administración y Finanzas | — | —/— | — | familia_sin_rama |
| Responsable de Administración y Finanzas | — | —/— | — | familia_sin_rama |
| Responsable de Administración y Finanzas | — | —/— | — | familia_sin_rama |
| RESPONSABLE DE ADMINISTRACIÓN Y FINANZAS | 4311.1 empleado de contabilidad | D05/D_directa | facturacion@tareas | decidido |
| Jefe de Contabilidad, Costos y control de Ge | — | —/— | — | familia_sin_rama |
| Jefe de Contabilidad | — | —/— | — | familia_sin_rama |
| Jefe de Contabilidad | 1211.1.1 director de contabilidad | inclusion/inclusion | conciliaciones@tareas, cierres@tareas, cierres contables@tareas, balan | decidido |
| Jefe de Contabilidad | — | —/— | — | familia_sin_rama |
| Responsable de Contabilidad Global | 1211.1.1 director de contabilidad | inclusion/inclusion | conciliaciones@tareas, cierres@tareas, cierres contables@tareas, infor | decidido |
| Responsable de Contabilidad y Administración | 1211.1.1 director de contabilidad | inclusion/inclusion | cierres@tareas, cierres contables@tareas, balances@tareas | decidido |
| Responsable de contabilidad | 1211.1.1 director de contabilidad | inclusion/inclusion | cierres@tareas, cierres contables@tareas | decidido |
| Responsable de Contabilidad y Administración | 1211.1.1 director de contabilidad | inclusion/inclusion | cierres@tareas, cierres contables@tareas, balances@tareas | decidido |
| Coordinador Contable | 2411.1.1 analista contable | D03/D_directa | analisis de cuentas@tareas | decidido |
| Coordinador contable | — | —/— | — | familia_sin_rama |
| Coordinador Contable | — | —/— | — | familia_sin_rama |
| Coordinador contable | — | —/— | — | familia_sin_rama |
| Coordinador de Administración y Contabilidad | 1211.1.1 director de contabilidad | inclusion/inclusion | conciliaciones@tareas, cierres@tareas, cierres contables@tareas, balan | decidido |
| Coordinador de Administración y Contabilidad | — | —/— | — | familia_sin_rama |
| Coordinador de Administración y Contabilidad | — | —/— | — | familia_sin_rama |
| Gerente de contabilidad | 4311.1 empleado de contabilidad | D05/D_directa | facturacion@skills | decidido |
| Gerente de Contabilidad | 1211.1.1 director de contabilidad | inclusion/inclusion | balances@tareas, impuestos@tareas | decidido |
| gerente de contabilidad | 1211.1 director financiero/dire | D07/D_directa | inversiones@tareas | decidido |

## [36] auditor forense/auditora forense (`2411.1.9`) — 2 casos

**Observaciones:** Solo 2 casos en el corpus (ocupación rara) — ambos sin-rama con tareas genéricas. Muestra insuficiente: validar en shadow (P3) con corpus completo.

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Compliance/Forensic Auditor - Americas | — | —/— | — | familia_sin_rama |
| Compliance/Forensic Auditor - Americas | — | —/— | — | familia_sin_rama |

## [58] empleado de oficina/empleada de oficina (`4110.1`) — 3 casos

**Observaciones:** Solo 3 casos: sus triggers son administrativos DE OBRA (contexto construcción) — el corpus casi no los tiene con ese vocabulario. 1 decide correcto. Muestra insuficiente: shadow.

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Administrativo de obras | 4110.1 empleado de oficina/empl | inclusion/inclusion | presentismo@tareas, fondos fijos@tareas, pedidos de materiales@tareas, | decidido |
| Administrativo de Obras | — | —/— | — | familia_sin_rama |
| Administrativo de construccion | — | —/— | — | familia_sin_rama |

## [16] representante comercial (`3322.1`) — 25 casos

**Observaciones:** 15/25 deciden — sólido. «Vendedor/a mayorista aberturas»→D11 con prospección+cartera+negociar: la regla de Cyn trabajando exactamente como fue escrita. Los 9 sin-rama: 5 por anclaje ('generar nuevos clientes'≠'buscar nuevos clientes', 'cerrar acuerdos'≠'cerrar operaciones' — variantes a agregar), 4 con evidencia fina (correcto).

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Ejecutivo Comercial - Prospección y Desarrol | 3322.1 representante comercial | inclusion/inclusion | prospeccion@tareas, cotizaciones@tareas, negociar precios@skills, nego | decidido |
| Ejecutivo Comercial | 2422.18 responsable del desarrol | D08/D_directa | desarrollo de canales@tareas | decidido |
| Ejecutivo Comercial de Cuentas (Calle) - Ins | 2433.6 representante técnico de | D01/D_directa | asesoramiento tecnico@tareas, venta tecnica@skills | decidido |
| Ejecutivo Comercial | 3322.1 representante comercial | inclusion/inclusion | fidelizar@tareas, cartera de clientes@tareas, oportunidades comerciale | decidido |
| Ejecutivo de Ventas | 3322.1 representante comercial | inclusion/inclusion | presentacion de productos@tareas, prospeccion@tareas, fidelizacion@tar | decidido |
| EJECUTIVO DE VENTAS (Exclusivo Comercio de i | 4110.1 empleado de oficina/empl | D13/D_directa | seguir instrucciones@skills | decidido |
| Ejecutivo de Ventas Semi Senior | 3322.1 representante comercial | inclusion/inclusion | prospeccion@tareas, cartera de clientes@tareas, oportunidades comercia | decidido |
| EJECUTIVO DE VENTAS CONVENCIONALES - FORD y  | 5244.1 teleoperador/teleoperado | D05/D_directa | venta telefonica@tareas | decidido |
| EJECUTIVO DE CUENTAS INTERNACIONAL | — | —/— | — | familia_sin_rama |
| Ejecutivo de Cuentas - Johnson Acero S.A. | 2422.18 responsable del desarrol | D08/D_directa | distribuidores@tareas | decidido |
| Ejecutivo de Cuentas Comercial | — | —/— | — | familia_sin_rama |
| Ejecutivo de cuentas | — | —/— | — | familia_sin_rama |
| Vendedor Viajante Técnico – Región NOA (Base | — | —/— | — | familia_sin_rama |
| Vendedor Viajante/Itinerante | — | —/— | — | familia_sin_rama |
| Vendedor viajante | 4225.1 agente de servicio de at | D12/D_directa | consultas@skills | decidido |
| Vendedor Viajante | 4225.1 agente de servicio de at | D12/D_directa | consultas@skills | decidido |
| Representante de Ventas Comercial | — | —/— | — | familia_sin_rama |
| Representante de Ventas - Bahia Blanca | 5244.1 teleoperador/teleoperado | D05/D_directa | llamados@tareas, venta telefonica@tareas | decidido |
| Representante de Ventas Rosario | 3322.1 representante comercial | inclusion/inclusion | comercializacion@skills, negociacion@skills | decidido |
| Representante de ventas | — | —/— | — | familia_sin_rama |
| Agente Comercial Técnico - Energía Renovable | — | —/— | — | familia_sin_rama |
| Agente Comercial / FULL TIME - Belgrano CABA | — | —/— | — | familia_sin_rama |
| Agente comercial de Seguros- Zona CABA | 3322.1 representante comercial | inclusion/inclusion | fidelizacion@tareas, propuestas comerciales@tareas | decidido |
| agente comercial | 3322.1 representante comercial | inclusion/inclusion | fidelizar@tareas, fidelizacion@skills, cartera de clientes@tareas | decidido |
| Vendedor Corporativo - Importante Corralón d | — | —/— | fidelizacion@tareas, cotizaciones@tareas, propuestas comerciales@tarea | evidencia_mixta ⚔['3322.1', '5230.1'] |

## [51] vendedor/vendedora (`5223.4`) — 15 casos

**Observaciones:** 6/15 deciden. Deriva correcta de mayoristas a 3322.1. Los 9 sin-rama: mitad evidencia fina (no-forzar correcto: «Vendedora en Shopping» con solo 'atención al cliente; manejo de caja'), mitad anclaje (variantes).

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Vendedor/a de seguros part time San Juan Eve | 5223.4 vendedor/vendedora | inclusion/inclusion | atencion al cliente@skills, asesoramiento@tareas, cierre de ventas@tar | decidido |
| Vendedor técnico | 5223.4 vendedor/vendedora | inclusion/inclusion | asesoramiento@tareas, asesorar@skills | decidido |
| Vendedor Viajante Técnico – Región NOA (Base | — | —/— | — | familia_sin_rama |
| Vendedor/a mayorista rubro aberturas. Isidro | 3322.1 representante comercial | D11/D_directa | prospeccion@tareas, cartera de clientes@tareas, negociar precios@skill | decidido |
| Vendedora en Shopping - Zona Norte | — | —/— | — | familia_sin_rama |
| VENDEDORA con experiencia en venta y atenció | — | —/— | — | familia_sin_rama |
| Vendedora Recoleta Full time | 5223.7.4 vendedor especializado e | D03/D_directa | pasteleria@tareas | decidido |
| Vendedora / Telemarketer | 5244.1 teleoperador/teleoperado | D10/D_directa | llamadas@tareas, ventas telefonicas@skills | decidido |
| Personal de Atencion al Publico en Estaciona | — | —/— | — | familia_sin_rama |
| Personal de Atencion al Publico en Farmacia | 5223.6 asistente de tienda | D01/D_directa | reposicion@tareas, control de stock@tareas, orden y limpieza del local | decidido |
| Personal de Atencion al Publico | — | —/— | — | familia_sin_rama |
| Personal de Atencion al Publico en Ventas | — | —/— | — | familia_sin_rama |
| ASISTENTE DE VENTA | — | —/— | — | familia_sin_rama |
| ASISTENTE DE VENTA | — | —/— | — | familia_sin_rama |
| Asistente de Venta para sucursal en Zona Nor | — | —/— | — | familia_sin_rama |

## [52] vendedor especializado/vendedora especializada (`5223.7`) — 4 casos

**Observaciones:** Solo 4 casos (el título 'vendedor especializado' casi no existe literal en avisos — llega vía D02 del hub 51, no por trigger propio). 1 decide, 1 mixta. Muestra insuficiente: shadow.

| Título | Decisión | Regla/Camino | Matches (término@campo) | Estado |
|---|---|---|---|---|
| Vendedor Especializado Hogar y Equipamiento  | 5223.6 asistente de tienda | D01/D_directa | — | decidido |
| Vendedor Especializado en Neumáticos para Mo | — | —/— | atencion al cliente@tareas, prestaciones@tareas | evidencia_mixta ⚔['5223.4', '5223.7'] |
| vendedor especializado | — | —/— | — | familia_sin_rama |
| Vendedor especializado en destilados,vinos y | — | —/— | — | familia_sin_rama |

## Ajustes propuestos (NO aplicados — esperan el OK del gate)

1. **D06 del hub 1** (asesor fiscal): exigir 2 matches o término fiscal específico (hoy decide con «impuestos» solo).
2. **Variantes de anclaje** (~15 términos): generar nuevos clientes · cerrar acuerdos comerciales · registración contable · armado de balances · carga de facturas · liderar equipo de auditoría · control de lo facturado · entre otros listados por hub.
3. **Hubs 36/58/52 con muestra insuficiente** en el trigger-sampling: validarlos con el shadow del P3 (corpus completo) antes de congelar su parte.
4. Ofertas en inglés: gap declarado (sin-rama correcto hoy; léxico EN es fase posterior si se decide).