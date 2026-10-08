# CT: verificación de bajas PARCIAL por diseño

**Fecha:** 2026-10-08 · **Estado:** activo (decisión de diseño, no un bug a arreglar)
**Relacionado:** `SPEC_ct_verificacion_busqueda.md`, `exports/reportes/micro_gate_ct_resultado_2026-10-08.md`

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
