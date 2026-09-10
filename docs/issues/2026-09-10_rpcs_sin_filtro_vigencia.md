# 22 RPCs analíticas cuentan la tabla entera, sin filtro de vigencia

**Fecha:** 2026-09-10
**Origen:** Fase 5 / Etapa B.3 — inventario `068_inventario_funciones.sql`
**Estado:** abierto
**Prioridad:** alta (no bloquea el switch de la Etapa C; lo sobrevive)

---

## El hallazgo

El inventario contra la base real (no contra el repo) devolvió:

- **22 funciones** tocan `ofertas_dashboard`.
- **Ninguna** filtra por `estado`.
- Solo **2 objetos** mencionan el campo, y uno de ellos (`buscar_skill`) resultó
  ser un falso positivo de mi propio grep: su definición real no lo usa.

O sea: el único consumidor server-side de `estado` es la vista
`v_empresas_activas`. Todo el resto de la analítica —panorama, series
temporales, rankings de ocupación, distribución por provincia, skills más
demandadas— corre sobre **todas las filas de la tabla**, sin distinguir una
oferta publicada ayer de una caída hace ocho meses.

Esto **no lo introduce la Fase 5**. Es el estado previo, que la Fase 5 vuelve
visible: hasta ahora `estado` estaba tan roto (111K "bajas" que eran artefacto
del muestreo rotativo de Bumeran) que filtrar por él habría sido peor que no
filtrar. Con `estado_ciclo` el filtro pasa a ser posible, y entonces la ausencia
deja de ser una omisión inocua y pasa a ser una decisión.

## Por qué importa, en una frase

Después del switch de la Etapa C:

> el panel mostrará 17.687 activas junto a KPIs calculados sobre 119.123
> ofertas; un lector razonable asumirá que describen a las activas.

El número grande y el chico van a convivir en la misma pantalla sin que nada
indique que miden universos distintos.

## Lo que NO es

No es un bug de cálculo: las 22 funciones hacen bien lo que les pidieron. Es una
pregunta de producto sin responder: **¿cada indicador describe el mercado de hoy
o el acumulado histórico?** Las dos respuestas son legítimas y para algunos
indicadores la histórica es la correcta (una serie temporal de demanda necesita
el acumulado; un "top 10 de ocupaciones demandadas" casi seguro no).

Por eso no se resuelve con un `WHERE` global: hay que decidir indicador por
indicador, y eso es de Cyn/Diego, no mío.

## Trabajo pendiente

1. Clasificar las 22 funciones en tres cubetas: **vigente** (filtra por
   `estado_ciclo='activa'`), **histórica** (no filtra, por diseño), **ambas**
   (necesita el filtro como parámetro).
2. Para las de cubeta "histórica", que la UI lo diga: el rótulo del KPI tiene
   que declarar su ventana. Un número sin ventana declarada se lee como "hoy".
3. Recién ahí, tocar SQL.

## Relación con la poda

La poda aprobada (opción A, DELETE dirigido, post-switch + 1 semana) **enmascara
parcialmente este problema sin resolverlo**: al bajar la tabla de 97K a ~39K
filas, los KPIs históricos pasan a calcularse sobre un acumulado recortado a la
ventana de 90 días. Queda un número que ya no es "todo el histórico" ni "hoy":
es "los últimos 90 días más las vigentes". Si esa es la definición deseada, hay
que escribirla; si no lo es, la poda empeora la lectura en vez de mejorarla.

Conviene resolver la clasificación de indicadores **antes** de podar.
