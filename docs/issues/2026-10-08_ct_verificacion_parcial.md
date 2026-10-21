# CT: verificación de bajas PARCIAL por diseño

**Fecha:** 2026-10-08 · **Estado:** activo (decisión de diseño, no un bug a arreglar)
**Relacionado:** `SPEC_ct_verificacion_busqueda.md`, `exports/reportes/micro_gate_ct_resultado_2026-10-08.md`, `exports/reportes/chequeo_drenaje_ct_regimen_2026-10-21.md`

## ACTUALIZACIÓN 2026-10-21 — números medidos (1 semana de cron en régimen)

- **Vía VALIDADA: resurrección = 0 / 550 confirmadas = 0,00 %** (umbral pre-registrado 2 %). Ninguna baja_confirmada de CT reapareció en scraping (`baja_confirmada→activa` = 0). Cuando la vía confirma (2 caídas), acierta.
- **~20.800 CT indecidibles por búsqueda.** Drenado el backlog de títulos distintivos (los 1.113 count=1 → 549 confirmadas esta semana, 578 pendientes), la cola residual es **88-99 % ambigua** (subió corrida a corrida; última 98,6 %). Esas ~20.8k count=0 quedan en `presunta_baja` **indefinidamente** — es el límite PARCIAL-por-diseño, ahora cuantificado. La señal complementaria para resolverlas NO se abre por ahora (límite conocido documentado).
- **Flip tras ambigua = 2,1 %** (21/998 ambiguas re-verificadas cambiaron de veredicto en la semana, medido en `verificaciones_baja`). Bajo pero no cero → se agregó un **cooldown de 30 días** (no skip permanente): una count=0 ambigua no se re-verifica por 30d. Antes, el `ORDER BY fecha_ultimo_visto ASC` hacía que las ~1.000 más viejas (ambigua-prone, sin timestamp) monopolizaran la cuota y **18.551 presuntas frescas quedaban starvadas**; 6.000 slots/sem rendían solo 653 ofertas distintas. Config `cooldown_ambigua_dias` en `ciclo_vida_ofertas.json`. Ver rama `fix/cooldown-ambigua-ct`.
- **Reiterado — sesgo a declarar:** las bajas CONFIRMADAS de CT están sesgadas hacia títulos distintivos (los que el buscador surfacea sin ambigüedad). **Cualquier indicador de DURACIÓN / supervivencia que use bajas de CT debe declarar este sesgo** (sub-representa ofertas de título común).


## Qué
Desde 2026-10-08 CompuTrabajo se verifica por la vía BÚSQUEDA (presencia en el
buscador de CT; `discriminador: "busqueda"`). El gate primario (ground-truth)
confirmó que la vía es **segura**: 0% falsa-caída sobre 50 ofertas vivas → **no
confirma baja de ofertas vivas**.

## El caveat (declararlo en cualquier indicador que use CT)
La verificación de CT es **PARCIAL por diseño**. En la cola real (ofertas viejas,
63-126 días sin verse) ~**57% quedan AMBIGUAS**: una oferta vieja-pero-viva con
título común queda sepultada en el buscador (ordena por recencia) fuera de las 2
páginas que se miran → `tope_alcanzado` → ambigua. No se confirma ni se revive.

Consecuencia: **las bajas CONFIRMADAS de CT son un subconjunto SESGADO hacia
títulos distintivos** (los que el buscador surfacea sin ambigüedad). NO son una
muestra aleatoria de las bajas reales de CT.

- **Las ambiguas quedan como `presunta_baja` indefinidamente** — es honesto: no se
  puede afirmar su estado por esta vía.
- **Todo indicador de DURACIÓN / supervivencia que use bajas de CT debe declarar
  este sesgo.** La duración medida sobre bajas CT confirmadas sub-representa las
  ofertas de título común.

## Recalibración de la curva/umbral: NO con este drenaje
La curva CT (95/56/7 a 1/2/3 meses) y el umbral `presunta_baja` de **63 días**
quedan **como están**, con su caveat de "señal débil" ya documentado. **NO** se
recalibran con el subproducto del drenaje: el ~43% decidible es una submuestra
sesgada (hacia títulos distintivos), no aleatoria → recalibrar sobre eso daría un
número peor con apariencia de mejor. Si alguna vez se recalibra, será con un
muestreo diseñado para eso (aleatorio, con manejo explícito de la ambigüedad), no
con el drenaje.

## Alcance operativo
- Navent (bumeran/zonajobs): verificación por searchV2, 0 ambiguas → bajas
  confirmadas representativas.
- CT: verificación parcial (este caveat).
- CABA/Indeed: ver `SPEC_ciclo_vida_ofertas.md` (CABA sin corridas sincronizadas;
  Indeed `baja_inferida`, no verificable).
