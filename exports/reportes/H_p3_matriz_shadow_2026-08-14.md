# [FRENTE H — P3] Matriz del shadow — punto de control (2026-08-14)

**NADA activado.** Shadow del traductor (léxico v0.3.1, 7 hubs congelados + 3 en propuesta leídos aparte) sobre el corpus completo (84.524 ofertas con NLP), comparado contra el **baseline post-K** (reglas 59,4% / dict 11,0% / semántico 29,7% — `K_baseline_post_correccion_2026-08-13.md`), NO el 63,5% del spec (quedó viejo: el frente K aplicó la auditoría de Cyn a las reglas planas).

**Nota de lectura obligatoria:** R14_contador_auditor y R226_analista_rrhh siguen forzando ~2.504 ofertas hasta la respuesta de Cyn. Toda divergencia contra esas dos reglas lleva la bandera `r14r226` = **baseline en revisión, no firme** (656 de las 3.852 divergencias de los 7 hubs = 17%).

## 0. Parte 1 (pre-shadow): léxico v0.3.1 — hecha, regresión limpia

- Conflicto #1 (administrativo/a contable) **resuelto-confirmatorio**: la auditoría K de Cyn corrigió R14d a 3313.2 = confirma la regla consolidada 3. Entrada desbloqueada.
- Regla 16, «vendedor/a mayorista» = **denominación-trampa**: sigue como trigger del hub 3322.1, pero `ventas mayoristas` salió de los términos de inclusión (mencionar venta mayorista NO es evidencia de representante B2B).
- Regresión sobre el case-set del P2: **cero cambios de estado** v0.3.0→v0.3.1. Fidelidad de reconstrucción: el spec citaba 139 casos; el informe versionado del P2 tiene 125; recuperados de BD 124 (el 125º, «624 BE|SENIOR AUDITOR…», es irrecuperable por truncado-con-pipes). 87/124 reproducen exactamente el estado del informe; las 37 diferencias son ambigüedad del truncado a 40 chars sobre títulos duplicados (ofertas concretas distintas), no cambios del evaluador. Tests del evaluador: 14/14 verdes. Commit `db849311`.

## 1. Los números del shadow — 7 hubs congelados

| Telemetría | n | % del corpus |
|---|---|---|
| decidido | **5.484** | 6,5% |
| familia_sin_rama | 6.667 | 7,9% |
| evidencia_mixta | 1.222 | 1,4% |
| no_aplica (trigger sin word-boundary) | 1.408 | — |

| Comparación vs baseline post-K | n |
|---|---|
| convergente (mismo destino) | 1.579 (29% de lo decidido) |
| **divergencia** (ambos fuerzan, destinos distintos) | **3.852** |
| trad fuerza / baseline no forzaba | 53 |
| trad no fuerza / baseline sí | 7.828 |
| ambos no fuerzan | 61 |

Decididas por hub ganador: 5223.4 (1.750) · 3322.1 (1.477) · 2411.1.1 (677) · 3313.2 (631) · 2411.1 (337) · 1211.1.1 (325) · 4312.1 (287).

Anotaciones sobre las 3.852 divergencias: **con-arista 2.118 (55%)** (el destino del baseline está en el vecindario D del hub ganador — redistribución esperada) / sin-arista 1.734 / bandera R14-R226: 656 / bandera scraping (tareas vacías): 12.

## 2. Divergencias CLASIFICADAS (muestra estratificada de 30, a ojo con evidencia)

**Mejora 7 (23%) · Neutral 8 (27%) · Regresión 15 (50%).**

**Las mejoras son exactamente el diseño de Cyn funcionando:**
- «Encargado administrativo para ferretería industrial» (tareas: facturación, conciliaciones, IVA): baseline R20→vendedor de ferretería; traductor→4311.1 empleado de contabilidad. La regla plana fuerza por la palabra "ferretería"; el traductor leyó las tareas.
- «Vendedor de drones agrícolas» / «Vendedor técnico comercial SR» (cartera, visitas B2B): 5223.4→**3322.1 representante** vía D11 — el deslinde vendedor/representante de la regla 16.
- «Vendedor de intangibles» (llamados en frío, venta telefónica): →5244.1 teleoperador, correcto contra el 5223.4 plano.
- «Administrativa/asistente contable» (pagos, caja, facturación): R14→2411.1 contable era demasiado; traductor→4311.1.
- «Auditor externo semi senior» (ejecución de auditoría completa): R14→contable; traductor→4312.1 auditor.

**Las regresiones se concentran en DOS mecanismos, nombrados con el caso testigo:**

**(M1) `principalmente` no compara contra la inclusión** — la D redirectora gana con una mención accesoria porque el comparativo solo mira a las D hermanas, no a la actividad nuclear del hub: «Vendedor(a)» (ventas efectivas, fidelizar, asesorar + "apoyo en manejo de caja") → **5230.1 cajero** por D07; «Vendedor en calle» ("saldos y cobros") → cajero; «Vendedor» ("control de stock" accesorio) → asistente de tienda; «Contador interno» / «Analista contable» (análisis + balances, con "conciliaciones" en la lista) → D01/D02 los baja a 3313.2 administrativo; «Administrativa de diag. por imágenes» ("atención telefónica") → teleoperadora; «Vendedor externo a comisión» → teleoperador. **~11 de las 15 regresiones muestreadas son este mecanismo.** Fix quirúrgico: incluir los términos de la INCLUSIÓN del hub como hermana en el comparativo `principalmente` de las D redirectoras (o pasarlas a `min_matches:2` con `excluye` de términos de venta/análisis). Es cambio de compilación (léxico v0.3.2) + una línea de semántica en el evaluador — decisión de laudo, no se aplicó.

**(M2) El piso de satélites — tal como LO IMPLEMENTÉ — mete triggers de palabra única:** los labels/alt-labels de satélites se partieron por «/» y quedaron palabras sueltas: **«administrativo» solo activa 4 hubs** (3313.2/4312.1/1211.1.1/3322.1); «camarero» activa 5223.4 → «Camarero de hotel 5 estrellas» forzado a **vendedor** por inclusión ("tomar pedidos"); «Gerente administrativo financiero» → **auditor 4312.1**; «Administrativo de cobranzas y siniestros» → representante comercial. **3-4 de las 15 regresiones + inflación del bloque no-fuerza vienen de acá.** Aclaración de método: el spec citaba "212 labels+alt-labels" y no pude reproducir ese número con ninguna definición (satélites de los hubs activos: 40 ocupaciones, 187 strings; con destinos-hub: 253) — mi implementación usó partes-de-label >4 chars (245 triggers agregados). Fix: piso solo con labels COMPLETOS multi-palabra (sin partir por género a palabra única), o exigir match de label entero.

**El tercer patrón (menor):** pérdida de especificidad contra reglas planas especializadas correctas («Ejecutivo ventas medicina prepaga»: R132→asesor de seguros 3321.3.1 es más fino que el 3322.1 genérico del traductor). Las reglas especializadas del vecindario deben tener precedencia o compilarse como ramas.

## 3. Los otros dos bloques

- **trad fuerza / baseline no (53 casos, 14 clasificados): mejora 10 · neutral 3 · regresión 1.** Es la recuperación neta: «Gerente/Jefe de contabilidad» →1211.1.1 (el dict contextual `gerente` no resolvía), «Agente comercial inmobiliario» →3334.2, «Empleado de facturación» →4311.1 (el piso funcionando BIEN: título = label del satélite), «Abogado/a» →2611.1 (hub 36). Chico pero consistente.
- **trad no fuerza / baseline sí (7.828): INOCUO bajo la semántica de activación correcta.** Si la activación es «el traductor decide solo cuando decide; si no fuerza, la oferta sigue por el canal actual (reglas→dict→semántico)», este bloque no cambia NADA. Solo sería pérdida si la activación reemplazara reglas del vecindario. **La semántica de activación debe laudarse ANTES del P4** — la matriz asume decide-cuando-decide con fallback.

## 4. Los 3 hubs en propuesta (pasada separada) — se quedan en propuesta

Deciden 1.728; divergencias 1.366 (con-arista 830). Muestra clasificada (8 divergencias): **mejora 2 · neutral 1 · regresión 5** — dominan los mismos mecanismos amplificados: D07 de 5223.7 manda vendedores a **cajero**; D05/D07 de 4110.1 manda administrativos contables a **coordinador de inventario**; D02 de 5223.7 manda «Vendedor consumo masivo» a **vendedor de ordenadores** (aunque el mismo D02 acierta perfecto en «Vendedor/a de mostrador» de tecnología). En el bloque fuerza-donde-baseline-no: 4 mejoras («Abogado/a»→2611.1 ×2, «Empleado de facturación»→4311.1 ×2), 4 neutrales. **Recomendación: siguen en propuesta, mismos fixes M1/M2, re-shadow.**

## 5. Recomendación de activación

**NO GO ahora.** El shadow muestra el diseño de Cyn funcionando exactamente donde debe (deslinde vendedor/representante, ferretería-contable, gerentes de contabilidad recuperados del limbo) — pero con una tasa de regresión del ~50% en divergencias muestreadas, concentrada en **dos mecanismos con fix quirúrgico**, no en el diseño:

1. **v0.3.2**: `principalmente` de las D redirectoras compara también contra la inclusión (laudo de semántica de modos — es la interpretación fiel de "tarea principal del aviso" de Cyn) + revisar D07/D01/D05/D10 de los hubs de venta.
2. **Piso de satélites**: labels completos, nunca palabra-única. («administrativo» y «camarero» no son denominaciones, son sustantivos.)
3. **Laudo de precedencia**: reglas planas ESPECIALIZADAS del vecindario (R132 y afines) ganan al traductor, o se compilan como ramas.
4. **Re-shadow** (barato ahora: ~4 min con BD en tmpfs) y re-clasificación de la muestra. Si la tasa de regresión baja a <15% con las mejoras intactas → GO en modo **decide-cuando-decide con fallback al canal actual**, hubs congelados solamente.

El costo de esperar es bajo (el traductor no está en producción); el costo de activar con M1/M2 vivos serían ~1.900 regresiones extrapoladas sobre 3.852 divergencias.

---
*Datos crudos: `h_p3_shadow.json` + muestra clasificable `h_p3_muestra.txt` (scratchpad de sesión). Baseline: réplica fiel v3.5.8 (reglas post-K + dict + semántico persistido como aproximación del residual). Corpus histórico intacto; el shadow no escribió nada en BD.*
