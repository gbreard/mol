# [FRENTE K3] P1 + P2 — Verificación y clasificación de las 49 (PUNTO DE CONTROL — nada aplicado)

**Fuentes:** `tercera_ronda_71_respuestas_2026-08-19.xlsx` (71 = 49 Corregir / 8 MANTENER / 14 RETIRAR) + `anexo_v4_respuestas_2026-08-19.xlsx` (las 4 respuestas, prosa operativa). Linaje: `tercera_ronda_cyn_2026-08-19`.

## P1 — Verificación: LIMPIA

- **Códigos: 70/70 OK-exacto** contra catálogo (incluidos todos los multi-destino parseados de las celdas «X / Y según tareas»). Sin paradas.
- **Censo: las 71 existen**; 5 tocadas desde el export, listadas antes de tocar: R228/R317/R303 **subordinadas** (P4), **R132 L3-marcada** (sale en P3.4), R314 ya **inactiva** (su retiro es formalización).
- **Convergentes marcadas**: R228→2411.1.1-restringida = hub 1 · R350→9333.8/9333.3 = conflicto #4 precompilado · R303 = la rama de jerarquía del anexo · R345→7223.4/2514.4 = R128a/b ya vivas (T4a) · R131b consolida con R131 (L3).

## P2 — La tabla de las 49 (clase · tratamiento · blast)

**Clases: 16 (a) destino-simple · 19 (b) restricción · 14 (c) género-hub.** Blast medido sobre las ofertas que cada regla decide HOY (retiene = cumple la condición propuesta; des-fuerza = cae al canal siguiente: árbol→subordinadas→semántico).

### (a) Destino-simple — aplicables directo (blast = re-destino de su volumen)

| Regla | vol | actual → nuevo | Nota |
|---|---|---|---|
| R353_operario_carga_descarga | 543 | 9333.8 → **9333.3** (+excl. título `produccion`: 59 quedan fuera) | consolidada 75 |
| R305_electromecanico | 518 | 7412.3 → **3113.1.2** | la denominación ES la consolidada 78 |
| R274_coordinador_ops_logistica | 460 | 3331.2 → **4323.9** | regla 11 del dicc consolidado |
| R309_responsable_deposito | 123 | 1324.3.1 → **1324.3.4** | |
| R132_vendedor_medicina_prepaga | 102 | 3321.3.1 → **3322.1** + quitar keywords de beneficio + **SALIDA de L3** | el caso testigo, corregido por la fuente |
| R90_supervisor_ventas | 64 | 3322.1 → **1221.3.2.1** | conducción, ya validado |
| R345_operario_cnc | 59 | 7223.7 → **7223.4** (+excl. `programador`→R128a; 16 fuera) | converge R128a/b |
| R336 (48→3257.7) · R333 (30→9112.2) · R321 (20→7422.5) · R131b (11→1219.1.1) · R330 (10→5223.7.23) · R304 (7→7422.7 default familia) · R335 (6→5243.1) · R325 (2→7422.7) · R340 (2→3123.1 default) | | | |

### (b) Destino-con-restricción — patrón R137 (título+tareas) o exclusiones de título

| Regla | vol | retiene | des-fuerza | Restricción propuesta |
|---|---|---|---|---|
| **R323_atencion_publico** | 591 | 215 | **376** | 4225.1 solo con tareas de consultas/reclamos/pedidos/problemas + excl. título vendedor/ventas/repositor |
| **R228_analista_contabilidad** | 288 | 150 | 138 | solo análisis/cierres/estados en tareas — CONVERGENTE hub 1 (ya subordinada: el árbol desambigua la cola) |
| R349_operario_envasado | 177 | 163 | 14 | tareas de envasado/embotellado/llenado |
| R329_tecnico_electronico_mant | 172 | 69 | 103 | tareas electrónicas + excl. potencia/electromecánico |
| R322_mecanico_industrial | 141 | 126 | 15 | excl. título jefe/coordinador/agrícola/electro |
| R355_operario_maestranza | 114 | 108 | 6 | excl. jerárquicos |
| R337_psicologo_laboral | 88 | 86 | 2 | excl. docencia |
| R301_ascensores | 68 | 43 | 25 | quitar `elevador` (¡captura «relevador»!) + excl. comerciales |
| R302 (42: 42/0) · R319 (28: quitar `operario textil`) · R346 (22: 19/3) · R320 (15: 10/5 evidencia de venta) · R334 (10: 7/3) · R316 (8: 1/7 técnico-comercial) · R327 (31: **5/26** solo gastronomía) · R348 (12: **1/11** solo soplado) · R328 (3) · R324 (1: 0/1) · R180 (0: quitar soporte/helpdesk) | | | | |

### (c) Género-hub — default restringido + cola no-forzada + precompilación fase 2

| Regla | vol | retiene | des-fuerza | Tratamiento |
|---|---|---|---|---|
| R95_tech_lead_ia_ml | 174 | 101 | 73 | **alta R95a** (títulos AI/ML engineer → 2511.11); resto cola + precompilación |
| R350_operario_deposito_logistica | 164 | 71 | 93 | retiene 9333.8 con núcleo depósito; carga/picking → cola (conflicto #4, hub futuro) |
| R303_gerente_admin | 122 | 84 | 38 | retiene 1211.1 solo finanzas-en-título; resto → cola (la rama de jerarquía del anexo la toma) |
| R306_mantenimiento_electrico | 92 | 81 | 11 | default **7411.1.1.2** (eléctrico puro, el grueso) + excl. electromecánico/jerárquicos; 3-vías a precompilación |
| R66_arquitecto_software | 79 | 43 | 36 | split por título: R66→**2512.3** restringida + **alta R66b→2511.14** (solutions); ambiguo → cola |
| R80_administrativo_almacen | 76 | 56 | 20 | retiene 4321.1 con tareas de inventario; conducción/compras → cola |
| R344_project_manager | 62 | 62 | 0 | split: señal IT → 1330.7; **alta R344b → 1219.6** catch-all |
| R313_encargado_logistica | 48 | 48 | 0 | split: logística→1324.3 / **alta R313b** depósito→1324.3.4; transporte → cola |
| R356_operario_mantenimiento | 46 | 9 | **37** | retiene 7233.7 solo mecánico; 3-vías a precompilación |
| R307_ingeniero_electronico | 28 | 5 | 23 | retiene 2152.1 solo diseño; 4 destinos a precompilación |
| R354_operario_lavadero | 25 | 5 | 20 | split: vehículos→9122.1 / **alta R354b** lavandería→8157.1 |
| R351 (9: 7/2) · R312 (3→2511.10 default) · R358 (1: puente grúa) | | | |

### Los otros dos bloques (van directo en P3, sin ambigüedad)

- **RETIRAR (14, vol 160)**: R347 (62) y R315 — las primas de R240 que la ronda anticipó —, R331/R332 (57, sin destino único sostenible), y 10 chicas (R314 ya inactiva = formalización). Cohort snapshot previo.
- **MANTENER (8, K-validadas)**: R317 (157, ya subordinada), R186 (108), R326 (74), R343, R352, y las 3 de auditor médico (R14b/c, R113 → candidatas L3: 2212.1 comparte familia con... no — familia 221 fuera del hub-set: NO califican L3 por prefijo ni grafo; se marcan solo K-validadas).

## Totales del blast propuesto

| Movimiento | Ofertas |
|---|---|
| Re-destino (las 16 (a) + defaults (c)) | ~2.100 |
| **Des-forzadas** (restricciones (b) + colas (c)) | **1.164** → caen a árbol→subordinadas→semántico |
| Retiros (14) | 160 |
| Splits: 5 altas nuevas (R95a, R66b, R344b, R313b, R354b) | dentro del re-destino |

## Lo que espera tu OK

1. La tabla entera, o ajustes por regla (los tratamientos (b)/(c) son mi lectura de la prosa — la prosa manda y está citada en el JSON de trabajo).
2. En paralelo quedó listo el diseño del P4 (anexo al léxico: rama de jerarquía prosa-directa, canal-remoto vs cartera, representante comercial al trigger con `fuente_pendiente_jd`, R15 restringida) — se aplica tras el OK junto con P3.
