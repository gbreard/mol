# Nota — Harness → Hilo del sistema: LAUDOS del shadow P3 + pedido de secuencia ordenada

> **Fecha:** 2026-08-14 · **De:** harness, vía Gerardo.
> **Asunto:** los cuatro laudos que el punto de control P3 pedía, bajados y firmes. El NO-GO queda confirmado. **Pedido explícito de Gerardo al hilo del sistema:** con estos laudos, devolverle UNA secuencia ordenada paso-por-paso de todo lo que él tiene que hacer ahora — incluyendo el manejo del branch con dos sesiones mezcladas y los merges pendientes — un paso por vez, sin bifurcaciones.

---

## 0. Veredicto general

**NO-GO confirmado.** La muestra fue auditada por el harness contra las tareas reales: las clasificaciones son honestas (hasta conservadoras — algún borde contado como regresión). Matiz de lectura: varias regresiones llevan bandera r14r226 (baseline en revisión) → el 50% es techo honesto, no piso. El diseño de Cyn funciona (ferretería→contabilidad, drones→representante, gerentes rescatados del limbo); los defectos son de compilación/implementación, con fix quirúrgico. El shadow hizo exactamente su trabajo.

## LAUDO 1 — M1: la semántica de `principalmente` (enmienda a la v1.1 del propio harness)

**Para toda D redirectora con modo comparativo, el conjunto de comparación = D-hermanas ∪ {INCLUSIÓN del hub}. Si la inclusión domina el conteo, ninguna D redirige — se evalúa la inclusión.**
Es la lectura fiel de "consiste principalmente en" de Cyn: el predominio es sobre TODO, incluido el núcleo del hub. (Un "Vendedor" con 4 tareas de venta y 1 de caja tiene actividad principal = venta; D07 no puede ganar por ser la única hermana que matcheó.)
**Segundo componente del mismo fix:** re-chequear el MODO de las D calientes (D07/D01/D02/D05/D10) contra los marcadores de la prosa de Cyn — si su regla del cajero dice "únicamente/solamente atiende caja", D07 debía compilarse `solo_estas`, no `principalmente`. Parte de M1 puede ser mis-modado de compilación. Ambos componentes → léxico v0.3.2 + la línea de semántica en el evaluador, con test nuevo del caso testigo (vendedor-con-caja NO va a cajero).

## LAUDO 2 — M2: el piso de satélites

**Trigger de piso = label ESCO COMPLETO (cualquier largo), JAMÁS fragmento de label.**
"Abogado" (label completo de una palabra) → válido, y funcionó (2611.1, dos mejoras). "Administrativo" (fragmento de "empleado administrativo") → inválido, y desparramó. Nada de partes->4-chars ni multi-palabra como criterio: label entero o nada. Es el criterio de la propia Cyn ("la ocupación no se asigna por semejanza textual") aplicado al piso. Regenerar los triggers de piso con esta regla y registrar el conteo nuevo (vs los 245 actuales).

## LAUDO 3 — Precedencia de planas especializadas

**Las reglas planas ESPECIALIZADAS del vecindario — K-validadas por Cyn y con código ESCO más fino que el del hub — tienen PRECEDENCIA sobre el traductor. En fase 2 se absorben como ramas del hub (una D más, con su condición). Precedencia ahora, absorción después.**
Caso testigo: R132 medicina prepaga → 3321.3.1 le gana al 3322.1 genérico del traductor. Un solo mecanismo a largo plazo, cero pérdida de finura hoy. Identificar la lista de especializadas-del-vecindario (criterio: K-validada + código descendiente-o-hermano-fino dentro de la familia) y marcarlas.

## LAUDO 4 — Semántica de activación: decide-cuando-decide con SUBORDINACIÓN (supersede la atomicidad del laudo anterior)

**La activación del piloto es: el traductor decide solo cuando decide; si no fuerza, la oferta sigue por el canal actual. Y las planas cubiertas por el hub-set NO SE RETIRAN en el commit de activación — se marcan `subordinada_al_traductor` en config** (disparan únicamente si el traductor no decidió).
Razón: con retiro, las 7.828 no-forzadas caen al semántico (ruleta de disparates, el trade-off T1 multiplicado). Con subordinación: no son zombis (estado explícito en config, auditable, con test), no hay agujero de cobertura, y el bloque de 7.828 queda genuinamente inocuo. **El retiro definitivo pasa a fase posterior, regla por regla, con su blast, cuando la cobertura del traductor lo justifique.** Esto SUPERSEDE la atomicidad activación+retiro del laudo previo del harness — que quede como supersede explícito en el spec, no como excepción silenciosa. (Mismo patrón que los clusters: la condición de diseño encontró la realidad, la realidad tenía razón.)

## El gate del GO (confirmado, con un agregado de método)

Fix v0.3.2 + piso regenerado + precedencia → **re-shadow** (4 min) → **muestra NUEVA de divergencias, mismo método (30, estratificada) — no re-mirar las 30 viejas** (comparabilidad, no auto-confirmación). **Si regresión <15% con las mejoras intactas → GO en modo decide-cuando-decide + subordinación, hubs congelados solamente.** Los 3 hubs en propuesta siguen en propuesta hasta su propio ciclo.

## Lo operativo que Gerardo pidió ordenar (input para tu secuencia)

1. **El branch con dos sesiones** (commits de Indeed intercalados con los del shadow en `spec/e4-traductor-piloto`, sin pushear): resolver ANTES de cualquier fix — separar (cherry-pick de los commits de Indeed a su propio branch) o serializar con orden explícito. Que ninguna sesión más toque ese branch hasta que esté limpio.
2. Merges pendientes que Gerardo tiene en cola (listalos vos que tenés el estado exacto de PRs).
3. La secuencia fix→re-shadow→gate→(GO)→P4.
4. Lo que viaja a Cyn (R14/R226 siguen esperándola; el paquete de próxima ronda del K).
5. Los recordatorios permanentes que sigan vivos (antivirus si aún no está, alerta CT, corrida semanal).

**Formato pedido: UN paso por vez, numerado, con el criterio de "hecho" de cada paso.** Gerardo ejecuta en orden.

> Vía: Gerardo como bus.
