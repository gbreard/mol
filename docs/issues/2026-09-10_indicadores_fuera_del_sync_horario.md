# Los indicadores se recalculan en cada sync horario y son el 75% del tiempo

**Fecha:** 2026-09-10
**Origen:** Fase 5 / Etapa B.2 (medición del sync)
**Estado:** abierto, **no ahora** (decisión de Gerardo)
**Prioridad:** media

---

## La medición

Desglose de la corrida del 2026-09-10, `--full --skip-skills --skip-issues
--skip-estado`:

```
  15:52:44  --- subida de ofertas (969 batches)   [16.2 min]
  16:08:59  Calculando tensión de demanda...
  16:09:22  Calculando concentración ocupacional...   [4.7 min]
  16:14:03  Calculando brecha de calificación...      [2.2 min]
  16:16:13  Calculando digitalización por sector...   [2.4 min]
  16:18:37  Calculando transición skills-ocupación... [2.3 min]
  16:20:56  Calculando velocidad de cobertura...      [1.2 min]
  16:22:10  Calculando índice de trabajo remoto...
  → total 33 min
```

Con el filtro de vigencia de B.2 la fase de ofertas bajó de 16,2 a **3,1 min**
(20.592 filas en vez de 96.872). Los ~15 min de indicadores **no cambiaron**:
salen de agregaciones sobre la BD local completa y el filtro no los toca.

La corrida horaria queda entonces en ~20 min, de los cuales 15 son indicadores.
El cuello se mudó, no desapareció.

## Por qué no necesitan cadencia horaria

Los indicadores son agregados del panel entero —tensión de demanda por
ocupación, concentración, brecha de calificación, digitalización por sector—.
Una hora de ofertas nuevas mueve esos agregados en el tercer decimal. Se
recalculan 24 veces por día para producir, casi siempre, el mismo número.

El costo no es sólo tiempo: son 24 recorridas diarias de la base local y 24
tandas de escrituras a Supabase (free tier, ~15 req/s) que compiten con el sync
de ofertas, que sí es sensible a la frescura.

Detalle que lo hace más evidente: el checkpoint de **una sola oferta**
(`--ids <id>`) también recalculó los siete indicadores. El costo es fijo, no
proporcional al trabajo.

## Propuesta

Separarlos del sync horario y correrlos 1–2 veces por día:

1. Flag `--skip-indicadores` en `sync_to_supabase.py`, mismo patrón que
   `--skip-skills` / `--skip-issues` / `--skip-estado`: guarda tanto el cálculo
   como la subida, con log explícito de lo que se omite.
2. `auto_sync.sh` (horario) pasa a usarlo → corrida de ~5 min.
3. Entrada de cron aparte, 1–2 veces al día, con el sync completo. Toma el mismo
   `flock` que ya tiene `auto_sync.sh`, así no se superponen.

## Riesgo a mirar

Si alguna pantalla asume que el indicador está tan fresco como las ofertas, va a
mostrar un desfasaje de hasta 12 h. Antes de cambiar la cadencia conviene
publicar junto a cada indicador su timestamp de cálculo — que además es lo que
pide el issue de las RPCs sin filtro de vigencia
(`2026-09-10_rpcs_sin_filtro_vigencia.md`): un número sin su ventana declarada
se lee como "ahora".
