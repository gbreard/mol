# [FRENTE K] P1 — Verificación de entrada: auditoría de Cyn sobre las reglas planas (2026-08-13)

**Fuente auditada:** `docs/DICCIONARIO_MOL_ESCO_FINAL_RECONSTRUIDO_AUDITADO_2026-08-12.json` (schema 3.0, 306 entradas + 8 auxiliares).
**Contra:** catálogo ESCO propio (`esco_occupations_metadata.json`, 3.046), `config/matching_rules_business.json` vivo (357 reglas + 2 filtro), M1 del FRENTE C, hub-set del piloto (frente H, `config/hubs_activos.json` en `spec/e4-traductor-piloto`), BD local (83.396 filas de matching), y las 88 consolidadas.
**Read-only: nada aplicado.** Scripts: `frente_k_p1.py`, `frente_k_p1b.py` (scratchpad).

## 1. Códigos contra NUESTRO catálogo — LIMPIO

Los **292 `codigo_esco` no nulos resuelven todos OK-exacto**: existen en `code_to_occupation` y el `ocupacion_esco_oficial` coincide con el label del catálogo (normalizado, 0 label-difiere-leve, 0 no-existe, 0 otro-concepto). La verificación independiente confirma el control declarado del archivo en este punto.

## 2. Mapeo por regla_id — NO es 1:1, y el modelo es REEMPLAZO

| Estado | n | Detalle |
|---|---|---|
| EXISTE (regla viva con mismo id) | 243 | editables |
| NUEVA-POR-DIVISIÓN (sufijo a/b/c, no existe viva) | 63 | de **35 madres** |
| SIN-MATCH-ID | 0 | — |
| **Vivas SIN contraparte en la auditoría** | **71** | uso 5.254 — casi todas R300+ |

**Hallazgo estructural 1 — el export que auditó Cyn es ANTERIOR al config vivo.** Las 71 sin contraparte son mayormente reglas creadas después (R303–R358: cosecha, frentes recientes — ej. R323_atencion_publico 591, R353_operario_carga_descarga 543, R305_electromecanico 518). No se tocan; van a la próxima ronda con Cyn.

**Hallazgo estructural 2 — las 35 madres NO están entre las 306 finales.** El modelo de la auditoría es **reemplazo madre→hijas**, no altas sueltas: aplicar las divisiones implica retirar/reemplazar 35 reglas vivas con 7.973 ofertas de territorio. Ver §Plan.

**Hallazgo 3 — condiciones truncadas.** 144/306 entradas tienen la `condicion` cortada con `...` literal (ej. R33: 3 keywords+"..." vs 12 + exclusiones en vivo), pese a que el autodeclarado dice `condiciones_truncadas: 0` (tercer matiz del patrón G). No afecta la aplicación (la auditoría es de destinos, los triggers vivos no se tocan) pero **sí obliga a ignorar cualquier "cambio de condición" aparente en entradas EXISTE**. Las 63 divisiones traen condición COMPLETA (0 truncadas).

## 3. Diff de destinos (sobre las 243 mapeadas)

| Diff | n | Cruce con `estado_refinamiento_esco` |
|---|---|---|
| IGUAL (validada, nada que hacer) | 164 | 120 sin-observación + 44 corregidas-que-el-vivo-ya-tenía |
| **DISTINTO (corrección de Cyn)** | **68** | todas `corregido_y_validado_esco` — uso 10.758 |
| NULO-AHORA (retiro de destino) | 9 | 7 desambiguación + 2 ISCO-familia |
| REGLA-SIN-ESCO-CODE | 1 | R10 (caso especial, abajo) |
| **CONTRADICTORIO** | **1** | R210_telefonista_ventas: Cyn la marca "validada sin observación" con 5244.1, el vivo dice 4222.1 → drift post-export, **se lista, no se resuelve** |

Cuadratura con el resumen declarado: 122 corregidas = 68 DISTINTO + 44 ya-iguales + 1 R10 + 9 divisiones corregidas ✓. Las 49 "validadas ESCO específico" son TODAS divisiones nuevas ✓. 121 sin observación = 120 IGUAL + R210 ✓.

**R10_electricista_industrial (caso especial):** está viva pero **desactivada** (`activa: false`) y su condición usa solo claves MUERTAS (`titulo_contiene` singular + `tareas_contiene_alguno`); su acción es `preferir_isco` (no forzar). Cyn le asigna 7411.1.1.2. Convertirla en regla real es un ALTA con condición nueva, no una edición → decisión aparte.

## 4. Cruce con M1 y hub-set piloto

De las 77 reglas vivas con corrección o retiro: **CUBIERTA 11 · CUBIERTA-PENDIENTE 2 · AMBIGUA 38 · HUÉRFANA 27** (M1). Es decir: **65 de 77 reciben el fix SOLO por esta vía** (el piloto del traductor no las alcanza).

En el hub-set piloto (target actual ∈ 10 hubs): 4 reglas. La más pesada del diff entero es exactamente territorio del piloto: **R111_vendedor_generico (3.882 ofertas): 5223.7 → 5223.4** — converge con el deslinde vendedor/vendedor-especializado de las 88 (hub 51/52).

## 5. Las 14 con código nulo

**(a) Las 12 `requiere_desambiguacion_funcional`** = 7 vivas a retirar + 5 divisiones-NULL (no se crean; son el "no forzar genérico" explícito):

| Regla viva | uso (decide hoy) | destino actual que se retira |
|---|---|---|
| R49_jefe_generico | **1.623** | 1219.4 |
| R240_operario_produccion (**P-17**) | **1.584** | 9329.1 |
| R235_mecanico | **1.242** | 7231.10 |
| R158_jefe_operaciones | 188 | 1321.2.1 |
| R160_tecnico_instalador | 43 | 7411.1.1.1 |
| R176_auditor_franquicias | 5 | 2421.2 |
| R250_supervisor_fractura | 1 | 3121.1 |
| **Total** | **4.686** | |

Divisiones-NULL (nada que crear): R208b_analista_compras_generico, R214c_analista_comercial_ventas_generico, R65b_jefe_delegacion_generico, R17c_compliance_no_financiero, R68b_supervisor_gastronomia.

**Muestreo con ojo (15 ofertas c/u, seed 42) — ¿a dónde caerían sin la regla?**

- **R49_jefe_generico → el retiro MEJORA.** El semántico ya persistido es razonable en la mayoría: "Responsable de finanzas"→1211 (0.79), "Jefe de fábrica"→1321 (0.78), "Responsable de taller automotriz"→7231 (0.81), "Jefe de marketing"→1221 (0.82). Hoy TODAS van a 1219.4 genérico. Pocos disparates (score 0.6 default: "Jefe de taller"→3435).
- **R240_operario_produccion → trade-off real.** 14/15 caen al semántico y la zona de disparates existe: "Operarios por una semana"→2265 Dietistas (0.6), "Operario en fábrica de muebles"→2141 Ingenieros (0.6), "Operario ecommerce"→5222 (0.6). Los aciertos son plausibles ("Operario de producción"→8160 0.9). Hoy TODAS van a 9329.1 peón genérico: falso positivo sistemático según Cyn, pero al menos familia-9 coherente en parte. **El retiro cambia falsos-positivos-uniformes por mezcla acierto/disparate a 0.6.** Sin diccionario que las contenga ("operario" no es entrada del dict).
- **R235_mecanico → mixto.** ~1/3 del semántico es correcto (7231 para mecánica vehicular), ~1/3 disparate ("Mecánicos de camiones"→2310 Profesores 0.6, "Mecánico de motos"→8159 0.6). 5/15 tocan la entrada contextual `tecnico` del dict (resuelve por contexto de tareas o delega).
- R158: 9/15 caen en la entrada contextual `gerente` del dict; semántico 1321 (0.9) coherente para "gerente de operaciones". R160: 15/15 tocan `tecnico` (contextual → resuelve por tareas o delega).

Nota para leer el trade-off: esto afecta **corridas frescas** (el corpus histórico no se reprocesa acá) y es exactamente el estado que el shadow del H debe ver — la zona sin forzador es el territorio que el traductor viene a resolver.

**(b) Las 2 `validado_isco_sin_esco_especifico` (NO se apagan):** R263_operario_limpieza_industrial (uso 4, hoy 9129.2, ISCO defendible 9129) y R82_operario_farmaceutico (uso 69, hoy 8131.20, ISCO 8131). **GAP confirmado:** el matcher NO soporta destino a nivel ISCO-familia — `_resolve_rule_target` exige `esco_code` o `esco_label`; una acción con solo `forzar_isco` no resuelve target (0 reglas vivas usan esa forma). **Se reporta como decisión** (§Plan T2), no se improvisa.

## 6. Las 8 auxiliares — conducta REAL en el matcher vivo

| Regla | Conducta hoy | uso |
|---|---|---|
| **R1_skills_cad** | **ASIGNA ocupación por `skills∈[autocad, solidworks...]` → 3118.3** | **238** |
| **R2_skills_diseno_grafico** | **ASIGNA por skills → 2166.9** | **89** |
| **R137_tareas_picking_crossdocking** | **ASIGNA → 9333.8** (título/tareas picking) | **221** |
| R6_sector_gastronomia | prioriza/penaliza familias (no asigna) | 0 |
| R7_sector_educacion | prioriza familia 23 (no asigna) | 0 |
| R4_nivel_gerencial | prioriza/penaliza (no asigna) | 0 |
| R9_tareas_logisticas | prioriza/penaliza — **condición muerta (FRENTE C)** | 0 |
| R11_titulo_compuesto | usar_primer_rol (no asigna) | 0 |

**Confirmado: el forzado-por-semejanza-de-skill OPERA en producción** (R1+R2 = 327 ofertas asignadas por skills; R137 221 más). La "separación" de Cyn es conceptual (no son denominaciones del diccionario) y **sus destinos (3118.3 / 2166.9 / 9333.8) quedaron SIN validar por la experta** (codigo_esco null en las 8). Su eventual retiro/corrección es una decisión con blast propio — se lista, no se aplica en este frente.

## 7. Convergencia con las 88 — LIMPIA

12 entradas de la auditoría solapan (por keyword de título ↔ `titulos_aviso`) con ocupaciones de las 88: **12/12 convergen al mismo `codigo_esco`, 0 contradicciones**. Fuente-única funcionando (la nota de R275 "corregido según regla consolidada MOL" se verifica en los hechos).

## Discrepancias con lo declarado (para constancia)

1. `condiciones_truncadas: 0` — falso: 144/306 con `...` literal (no bloquea porque los triggers no se tocan).
2. "306 entradas finales" mapea a solo 243 vivas: 63 son divisiones cuyo modelo implícito (madres ausentes) es reemplazo de 35 reglas vivas — el documento no lo dice explícitamente.
3. El vivo tiene 357 reglas, no 299: 71 posteriores al export quedaron fuera de la auditoría (uso 5.254).
4. R210: contradicción interna (validada-sin-observación pero difiere del vivo).
