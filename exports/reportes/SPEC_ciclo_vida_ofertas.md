# SPEC — Ciclo de vida de ofertas (estados + verificador + recómputo)

**Fecha:** 2026-09-02 · **Rama:** `spec/ciclo-vida-ofertas` · **Estado:** BORRADOR PARA APROBACIÓN
**Entregable de esta etapa:** esta spec. **No se escribe código de producción hasta el OK de Gerardo.**

---

## 0. Problema y encuadre

Hoy `database/detectar_bajas_integrado.py` (invocado en el post-proceso de `sync_from_vps.py`)
declara **baja** a toda oferta `activa` cuyo `id` no apareció en la última corrida
(`ids_activos_bd - ids_vistos → estado_oferta='baja'`, `fecha_baja=now`). Como el scraping es
**rotativo** (Bumeran: 165 de 1.148 keywords/día, 1 página/keyword), una oferta vigente puede
pasar semanas sin aparecer. Resultado real en la BD hoy:

```
estado_oferta:  baja = 114.543   ·   activa = 2.139
```

Las 114K "bajas" son **artefacto del muestreo, no hechos del mercado** (99,996 % del stock).
Los indicadores de **duración de ofertas** que MOL quiere construir necesitan fechas de baja
reales, y hoy no existen. Esta spec formaliza el modelo ya decidido por Gerardo: tres estados
graduales + verificador activo por portal + recómputo reversible del histórico.

**Insumo de medición** (commit `97353361`, rama `medicion/supervivencia-ofertas`,
`exports/reportes/supervivencia/`): curvas de supervivencia por portal y taxonomía de señales
viva/caída. Resumen operativo:

| portal | ~1 mes vivas | ~2 meses | ~3 meses | cruce 50 % | **umbral presunta_baja** | vía de verificación |
|---|---|---|---|---|---|---|
| ZonaJobs | ~90 % | ~27 % | ~0 % | ~5 sem | **35 d** | `POST /api/avisos/searchV2` (presencia en índice) |
| Bumeran | ~93 % | ~40 % | ~7 % | ~6 sem | **42 d** | `POST /api/avisos/searchV2` |
| ComputRabajo | ~95 % | ~56 % | ~7 % | ~8-9 sem | **63 d** | HTML de detalle (vía del PASO 2, ~2,2 s) |
| CABA | — | — | — | (listado completo) | **2 corridas ausente (~7 d)** | ninguna (ausencia = señal) |
| Portal Empleo | — | — | — | (listado completo) | **2 corridas ausente (~7 d)** | ninguna (ausencia = señal) |
| Indeed | no medible | — | — | — | **fromage-based** | **ninguna** → `baja_inferida` |

Hallazgos que fijan el diseño (de la medición):
- Bumeran/ZonaJobs son SPA: el HTML de detalle es **byte-por-byte idéntico** para vivas y caídas.
  La única señal es **presencia en `searchV2`** (la API que el scraper ya usa para el listado).
- `searchV2` verifica *presencia en el índice de búsqueda*, no *existencia del aviso* → un aviso
  pausado/moderado daría falso "caída". Por eso **una verificación caída = `presunta_baja`, no
  confirmada**; se exigen **dos** separadas en el tiempo.
- Indeed responde 401/403 idéntico para vivas/caídas por toda vía; además bloquea desde 2026-08-20.
  **No es verificable por diseño** → estado propio `baja_inferida`, nunca promovible a confirmada.

---

## 1. Modelo de estados (formalización)

### 1.1 Estados

| estado | significado | terminal? |
|---|---|---|
| `activa` | vista en la última corrida, o ausente pero con antigüedad < umbral del portal (la ausencia no informa) | no |
| `presunta_baja` | ausente ≥ umbral del portal → entra a cola de verificación | no |
| `baja_confirmada` | dos verificaciones "caída" separadas ≥ `gap` (o 2 ausencias completas en CABA/PE) | sí |
| `baja_inferida` | **solo Indeed**: ausencia + censura `fromage=14`. No verificable. **Nunca** pasa a confirmada | sí (especial) |
| `baja_no_verificada` | histórico recomputado que cruzó umbral pero nunca se verificó. Distinguible para siempre | sí (histórico) |

### 1.2 Transiciones

```
                (vista en corrida) ─────────────────────────┐
                                                            ▼
  ┌─────────┐   ausente ≥ umbral[portal]      ┌───────────────┐   2 verif. caída (≥ gap)   ┌────────────────┐
  │ activa  │ ──────────────────────────────▶ │ presunta_baja │ ─────────────────────────▶ │ baja_confirmada│
  └─────────┘                                  └───────────────┘                            └────────────────┘
       ▲                                              │
       │      reaparece en scraping / verificación viva (RESET de contadores)
       └──────────────────────────────────────────────┘

  Indeed: activa → (ausente en 2 corridas dentro de fromage) → baja_inferida   [rama separada, sin verificación]
  CABA/PE: activa → (ausente en 2 corridas completas) → baja_confirmada        [sin verificador; la ausencia ES la señal]
```

Reglas:
- **activa → presunta_baja**: `hoy - fecha_ultimo_visto ≥ umbral_presunta_baja_dias[portal]`.
- **presunta_baja → baja_confirmada**: `verificaciones_caida_count ≥ 2` **y** las dos separadas
  `≥ verificacion_gap_horas` (default **72 h**, configurable). Cubre avisos pausados/moderados que reviven.
- **cualquier estado → activa**: reaparece en scraping **o** una verificación da "viva".
  **Resetea** `verificaciones_caida_count`, `fecha_primera_verificacion_caida`, y actualiza `fecha_ultimo_visto`.
- **CABA/Portal Empleo**: no usan verificador (el scraper baja el **listado completo** cada corrida,
  así que la ausencia es señal fuerte). `activa → baja_confirmada` con **2 corridas completas ausente**.
- **Indeed**: `activa → baja_inferida` tras **2 corridas consecutivas ausente dentro de la ventana
  `fromage=14`** (donde el muestreo sí es exhaustivo). Nunca `presunta_baja` ni `baja_confirmada`.

### 1.3 Configuración (NO hardcodear)

Nuevo archivo **`config/scraping/ciclo_vida_ofertas.json`** (hermano de `portal_cadencia.json`;
se mantiene separado porque son conceptos distintos — cadencia del monitor vs ciclo de vida):

```json
{
  "_doc": "Umbrales del ciclo de vida de ofertas. Calibrados con exports/reportes/supervivencia/ (2026-09-01).",
  "verificacion_gap_horas": 72,
  "verificaciones_para_confirmar": 2,
  "ventana_verificable_factor": 2,
  "portales": {
    "zonajobs":     { "umbral_presunta_baja_dias": 35, "via": "searchv2",  "corridas_ausente_confirma": null },
    "bumeran":      { "umbral_presunta_baja_dias": 42, "via": "searchv2",  "corridas_ausente_confirma": null },
    "computrabajo": { "umbral_presunta_baja_dias": 63, "via": "html_detalle", "corridas_ausente_confirma": null },
    "caba":         { "umbral_presunta_baja_dias": 7,  "via": "listado_completo", "corridas_ausente_confirma": 2 },
    "portalempleo": { "umbral_presunta_baja_dias": 7,  "via": "listado_completo", "corridas_ausente_confirma": 2 },
    "indeed":       { "umbral_presunta_baja_dias": null, "via": "ninguna", "estado_ausencia": "baja_inferida", "corridas_ausente_infiere": 2 }
  }
}
```

---

## 2. Schema (migración idempotente)

### 2.1 Columna de estado NUEVA, no reusar la legacy

**Decisión (recomendada):** crear **`estado_ciclo`** como columna nueva y **conservar `estado_oferta`
+ `fecha_baja` como legacy deprecado** (no reutilizar con semántica nueva). Razón: hay consumidores
en producción que filtran `estado_oferta='activa'` (ver §4); reusar la columna rompería su
semántica en caliente. Se hace dual-write durante la transición y se depreca cuando todos los
consumidores migraron.

### 2.2 Columnas nuevas en `ofertas` (SQLite)

| columna | tipo | uso |
|---|---|---|
| `estado_ciclo` | TEXT | activa / presunta_baja / baja_confirmada / baja_inferida / baja_no_verificada |
| `fecha_ultimo_visto` | (ya existe) | última vez vista en scraping o verificación viva |
| `verificaciones_caida_count` | INTEGER DEFAULT 0 | verificaciones caídas acumuladas sin reset |
| `fecha_primera_verificacion_caida` | TEXT | ancla del intervalo de baja |
| `fecha_ultima_verificacion` | TEXT | para respetar el `gap` |
| `fecha_baja_estimada` | TEXT | **punto medio** del intervalo (indicadores) |
| `fecha_baja_intervalo_desde` | TEXT | = `fecha_ultimo_visto` |
| `fecha_baja_intervalo_hasta` | TEXT | = 1ª verificación caída / 2ª ausencia; NULL si no_verificada/inferida |
| `fecha_baja_incertidumbre_dias` | INTEGER | ancho del intervalo (medio-ancho, en días) |
| `grupo_oferta_id` | TEXT NULL | **previsión dedup cross-portal** — sin lógica todavía (§6) |

Legacy conservado: `estado_oferta`, `fecha_baja`, `es_republicacion`, `numero_republicacion`,
`grupo_republicacion` (sin tocar semántica).

### 2.3 Tablas nuevas

**`verificaciones_baja`** — registro por verificación (auditoría + reconstrucción del intervalo):

| columna | tipo | |
|---|---|---|
| `id` | INTEGER PK | |
| `id_oferta` | INTEGER | FK lógica a ofertas |
| `portal` | TEXT | |
| `fecha` | TEXT | timestamp de la verificación |
| `via` | TEXT | searchv2 / html_detalle / listado_completo |
| `resultado` | TEXT | viva / caida / ambigua |
| `senal_cruda` | TEXT | n_resultados searchV2 / status+len HTML / ausente-en-listado (JSON corto) |

**`recompute_ciclo_vida_log`** — reversibilidad del recómputo (patrón `descripcion_anulada_log`):

| columna | tipo | |
|---|---|---|
| `id` | INTEGER PK | |
| `run_id` | TEXT | identifica la corrida de recómputo |
| `id_oferta` | INTEGER | |
| `estado_oferta_anterior` | TEXT | valor legacy antes |
| `estado_ciclo_anterior` | TEXT | NULL en el primer recómputo |
| `estado_ciclo_nuevo` | TEXT | |
| `fecha_ultimo_visto_usada` | TEXT | fecha base del cálculo (con fallback) |
| `antiguedad_dias` | INTEGER | |
| `timestamp` | TEXT | |

### 2.4 Migración

`database/migrations/0XX_ciclo_vida_ofertas.sql` **idempotente**: `ADD COLUMN` guardado por
verificación de `PRAGMA table_info` (patrón de `verificar_migracion_aplicada` ya usado por
`detectar_bajas_integrado.py`), `CREATE TABLE IF NOT EXISTS`, índices `IF NOT EXISTS` en
`estado_ciclo`, `portal+estado_ciclo`, `fecha_ultimo_visto`. **Reversible**: las columnas nuevas
son aditivas (rollback = dejar de escribirlas / DROP opcional); las tablas nuevas se pueden
DROPear sin tocar datos existentes.

---

## 3. Verificador (job local diario)

### 3.1 Cola

1. Ofertas que **cruzan a `presunta_baja`** (post-sync las marca; el verificador las toma).
2. **Re-verificación** de `presunta_baja` con `verificaciones_caida_count = 1` cuya
   `fecha_ultima_verificacion` sea `≥ gap` (72 h) atrás.
- Orden: por `fecha_ultimo_visto` ascendente (las más viejas primero) hasta el tope diario.
- **CABA/PE/Indeed no entran** (sin verificador; sus transiciones son por ausencia en el post-sync).

### 3.2 Vías por portal (de la taxonomía medida)

- **Bumeran / ZonaJobs → `POST /api/avisos/searchV2`** con `{"pageSize":100,"page":0,"sort":"RELEVANCE","query":<título[:60]>}`,
  headers del scraper (`x-site-id`: `BMAR`/`ZJAR`, `x-pre-session-token` UUID nuevo). Clasificación:
  - `id` entre los resultados → **viva**
  - resultados < tope y `id` ausente → **caída** (mediana de resultados en caídas medidas: 0)
  - 0 resultados → **caída** (caso fuerte)
  - resultados == tope (100) y `id` ausente → **ambigua** → reintentar con query más específica
    (título completo / + empresa); si sigue ambigua, no contar la verificación.
  - Costo ~0,4 s/req + pausa. Cero ambiguas en 240 mediciones.
- **ComputRabajo → GET del HTML de detalle** (la vía del PASO 2, ya probada a 8.500 fetches sin
  errores, ~2,2 s). Clasificación por los marcadores de detalle vivo vs página de baja (definir el
  discriminador exacto en implementación a partir de la muestra de CT del drenaje 28-08/01-09).
- **CABA / Portal Empleo → sin verificador** (listado completo; la ausencia en 2 corridas confirma).
- **Indeed → sin verificación** (`baja_inferida`).

### 3.3 Operación

- **Pacing conservador**: pausas 2-4 s aleatorias, sesión única por portal, UA de Chrome (igual que la medición).
- **Lockfile-aware**: no correr si hay scraping en curso (chequear `/tmp/mol_scraping.lock` local y
  el lock del VPS; abortar limpio si están tomados, como el guard de `run_scraping_vps.sh`).
- **Tope diario configurable** por portal (`tope_diario`), para drenar en tandas sin quemar IP.
- **Registro** en `verificaciones_baja` por cada verificación (fecha, vía, resultado, señal cruda).
- **Reserva searchV2**: verifica presencia en índice, no existencia. Por eso 2 verificaciones ≥72 h;
  un aviso pausado que revive vuelve a `activa` al reaparecer.

### 3.4 Dimensionamiento (query real a la BD, 2026-09-02)

Stock inicial de la **franja de duda** (lo que el recómputo deja en `presunta_baja` → cola del
verificador), franja `[umbral, 2×umbral)` por portal:

| portal | presunta_baja inicial | costo/verif | 1 ronda | drenaje inicial (2 rondas, ≥72 h) |
|---|---|---|---|---|
| computrabajo | **13.259** | ~2,2 s +pausa (~3 s) | ~11 h | ~2-3 días a `tope_diario≈5.000` |
| bumeran | **3.590** | ~0,4 s +pausa (~3 s) | ~3 h | ~1 día |
| zonajobs | **2.260** | ~0,4 s +pausa (~3 s) | ~2 h | ~1 día |
| caba | 2 | — (sin verificador) | — | — |
| portalempleo | 14 | — (sin verificador) | — | — |
| **total** | **~19.125** | | | **~1 semana con topes conservadores** |

Plan de drenaje: mismo patrón que el drenaje de descripciones de CT — tandas diarias con
`tope_diario` por portal, checkpoint de 1 unidad verificado en BD antes del run completo, y
parada ante bloqueo estructural. Régimen permanente (post-drenaje): sólo entran las ofertas que
cruzan umbral cada día (goteo bajo).

> Nota: ya existe `scripts/scraping/verificar_ofertas_activas.py` (chequea existencia y actualiza
> `fecha_ultimo_visto`). El verificador nuevo **supersede** ese script (misma familia, semántica
> nueva de estados). Decisión en §7.

---

## 4. Fecha de baja para indicadores

La baja real ocurrió en algún punto de **`[fecha_ultimo_visto, fecha_primera_verificacion_caida]`**
(para CABA/PE: `[fecha_ultimo_visto, fecha_segunda_ausencia]`).

- `fecha_baja_intervalo_desde` = `fecha_ultimo_visto`
- `fecha_baja_intervalo_hasta` = 1ª verificación caída (o 2ª ausencia)
- `fecha_baja_estimada` = **punto medio** del intervalo (estimador puntual)
- `fecha_baja_incertidumbre_dias` = medio-ancho del intervalo (± días)

Casos especiales:
- `baja_no_verificada`: `hasta = NULL`, sin punto medio confiable → `fecha_baja_estimada = fecha_ultimo_visto`
  con `incertidumbre = NULL` (marcado "sin cota superior"). Los indicadores de duración **excluyen o
  ponderan aparte** estas ofertas.
- `baja_inferida` (Indeed): `desde = fecha_ultimo_visto`, `hasta = NULL`, marcado no-observable.

---

## 5. Recómputo histórico (reversible)

Reclasifica las **114.543** bajas actuales con la definición nueva, **sobre `fecha_ultimo_visto`,
sin re-scrapear**. Definición **inequívoca** (`antiguedad = recompute_date − COALESCE(fecha_ultimo_visto,
fecha_baja, scrapeado_en)`; `fecha_ultimo_visto` presente en 110.424 de 114.543 = 96 %):

```
indeed                                   → baja_inferida
antiguedad <  umbral[portal]             → activa           (la ausencia no informaba)
umbral ≤ antiguedad < ventana_verificable→ presunta_baja    (siembra la cola del verificador)
antiguedad ≥ ventana_verificable         → baja_no_verificada (histórico, cota superior desconocida)
```
`ventana_verificable = ventana_verificable_factor × umbral` (default 2×; parámetro para Gerardo, §8).

### 5.1 Conteos estimados (query real, ref 2026-09-02, ventana = 2×umbral)

| destino | conteo | detalle por portal |
|---|---|---|
| **→ activa** (recuperadas) | **17.698** | CT 11.441 · bumeran 3.297 · zonajobs 2.932 · caba 3 · PE 25 |
| **→ presunta_baja** (a verificar) | **19.125** | CT 13.259 · bumeran 3.590 · zonajobs 2.260 · caba 2 · PE 14 |
| **→ baja_no_verificada** | **58.637** | CT 21.368 · bumeran 23.567 · zonajobs 12.361 · caba 59 · PE 1.282 |
| **→ baja_inferida** (Indeed) | **19.083** | indeed |

**Cambio de cara del dashboard a anticipar:** las `activas` pasan de **2.139 → ~19.837** (2.139
actuales + 17.698 recuperadas, menos las actuales que crucen umbral). Las "bajas" reales
(confirmadas + no_verificada + inferida) bajan de 114K a ~78K + lo que confirme el verificador.
Es un cambio grande y visible — coordinar comunicación/tiempo del deploy.

### 5.2 Reversibilidad

Cada fila recomputada se registra en `recompute_ciclo_vida_log` con `estado_oferta_anterior` y
`estado_ciclo_nuevo`. Rollback = re-aplicar el estado anterior desde el log por `run_id`. El
recómputo NO borra `estado_oferta`/`fecha_baja` legacy (dual-write), así que el estado viejo queda
también in situ.

---

## 6. Previsión de deduplicación (sólo el hueco)

Se agrega `grupo_oferta_id TEXT NULL` a `ofertas`, **sin lógica**. La spec hermana de
deduplicación cross-portal la poblará (la medición ya detectó solapamiento real Bumeran↔ZonaJobs:
comparten backend Navent y parte del índice; 23/120 de la muestra ZonaJobs tienen `id` de rango
Bumeran). **Los indicadores agregarán por `grupo_oferta_id` cuando exista** (una oferta publicada
en 2 portales = 1 puesto, no 2). Hasta entonces agregan por `id_oferta`.

---

## 7. Integración

| Pieza | Dónde corre | Cambio |
|---|---|---|
| Transiciones `activa→presunta` y CABA/PE/Indeed por ausencia | **post-sync local** (`sync_from_vps.py` post-import), reemplaza/extiende `detectar_bajas_integrado.py` | nueva lógica con umbral por portal; escribe `estado_ciclo` (+ dual-write legacy) |
| Verificador | **cron local diario nuevo** | toma cola `presunta_baja`, verifica, escribe `verificaciones_baja` + transición a confirmada/activa |
| Recómputo | one-shot manual (script dedicado) | logged, reversible |

**Horario del verificador (crontab local):** ya hay `05:00` Indeed (headed), `06:15` Portal Empleo,
`0 * * * *` auto_sync, `* * * * *` poller. Propuesta: **`0 8 * * *`** (08:00), después de PE y del
auto_sync de las 08:00; lockfile-aware para no pisar nada. El `gap` de 72 h hace que cada corrida
sólo re-verifique lo elegible, así que correr a diario es barato en régimen permanente.

---

## 8. Consumidores (inventario real + qué cambia)

Grep de `estado_oferta`/`fecha_baja` (excluye archive/detectar_bajas):

| consumidor | uso hoy | cambio |
|---|---|---|
| `fase3_dashboard/.../app/api/matching-offers/route.ts` | `.eq('estado_oferta','activa')` (ofertas para OE/matching) | migrar a `estado_ciclo`; **decisión**: ¿`presunta_baja` cuenta como activa para OE hasta confirmarse? (recomiendo sí) |
| `scripts/exports/sync_to_supabase.py` | sincroniza `estado_oferta`, `fecha_ultimo_visto`; agrega activas/cerradas (l.1286) | añadir `estado_ciclo` + `fecha_baja_estimada` + intervalo; recalcular agregados sobre `estado_ciclo` |
| `scripts/exports/supabase_schema.sql` (ofertas_dashboard) | `estado_oferta TEXT`, `fecha_ultimo_visto` | agregar `estado_ciclo`, `fecha_baja_estimada`, `fecha_baja_incertidumbre_dias`, `grupo_oferta_id` |
| `scripts/sync_scraping_dinamica.py` | vida media con `fecha_baja` | usar `fecha_baja_estimada`; contar sólo `baja_confirmada` (+ `baja_no_verificada` ponderada aparte); excluir `baja_inferida` |
| `scripts/scraping/verificar_ofertas_activas.py` | chequea existencia + actualiza `fecha_ultimo_visto` | **superseded** por el verificador nuevo (archivar) |
| `scripts/db/calcular_permanencia.py`, `database/detectar_republicaciones.py` | permanencia/republicación sobre `fecha_baja`/`estado_oferta` | revisar; migrar a `fecha_baja_estimada`/`estado_ciclo` |
| `scripts/sync_learnings.py`, `scripts/db/optimize_db.py`, `query_builder.py` | conteos/índices | ajustar conteos a `estado_ciclo` |

---

## 9. Impacto en Supabase

- `ofertas_dashboard` gana `estado_ciclo`, `fecha_baja_estimada`, `fecha_baja_incertidumbre_dias`,
  `grupo_oferta_id` (migración SQL en `fase3_dashboard/sql/`, backfill con RPC temporal, **no `--full`**).
- Viajan a Supabase: `estado_ciclo`, `fecha_baja_estimada`, `fecha_baja_intervalo_desde/hasta`,
  `fecha_baja_incertidumbre_dias`, `grupo_oferta_id`. **No** viaja `verificaciones_baja` (auditoría
  local) salvo que un panel lo pida.
- RPCs que cuentan activas/bajas se actualizan a `estado_ciclo`. Los indicadores de duración leen
  `fecha_baja_estimada` + incertidumbre.

---

## 10. Plan de tests y despliegue por fases (cada fase reversible)

| Fase | Qué | Reversibilidad | Tests |
|---|---|---|---|
| **1. Migración** | columnas + tablas + índices idempotentes | aditivo; DROP tablas nuevas | migración corre 2× sin error; pragma verifica columnas |
| **2. Recómputo** | one-shot logged sobre `fecha_ultimo_visto` | rollback desde `recompute_ciclo_vida_log` por `run_id` | conteos == estimados (§5.1) ±; rollback restaura estado_oferta; dry-run |
| **3. Transiciones** | nueva lógica post-sync, `detectar_bajas` legacy OFF detrás de flag | re-activar legacy | unit: umbral por portal, contadores, reset al reaparecer, CABA/PE 2-ausencias, Indeed fromage |
| **4. Verificador** | cron nuevo, primero `--dry-run` | desactivar cron | unit: clasificación searchV2 (viva/caída/ambigua) con fixtures de `muestra.json`; gap 72 h; tope diario; lockfile |
| **5. Consumidores** | dashboard/RPCs/sync → `estado_ciclo` | revertir a `estado_oferta` (dual-write vigente) | e2e: panel cuenta activas nuevas; API matching; indicadores de duración |

Regla: cada fase se despliega y verifica sola; el dual-write legacy permite volver atrás en
cualquier momento hasta la Fase 5.

---

## 11. Riesgos y decisiones abiertas (para Gerardo)

1. **`ventana_verificable_factor`** (recómputo): default 2×umbral deja **19.125** en `presunta_baja`
   (cola inicial del verificador). Subirlo baja la cola (más a `no_verificada`); bajarlo la sube.
   ¿2× o preferís otro?
2. **¿`presunta_baja` cuenta como "activa"** para la API de OE/matching y para indicadores de demanda
   reciente, hasta que se confirme? (recomiendo sí; una presunta aún no probada muerta).
3. **Falso "caída" de searchV2** (aviso pausado/moderado): mitigado por 2 verif. ≥72 h, pero queda
   riesgo residual. ¿Aceptable, o querés 3 verificaciones para portales Navent?
4. **IP del verificador**: `searchV2` desde IP local, pacing conservador. Riesgo de bloqueo si se
   drena agresivo. El tope diario lo acota; ¿algún límite duro que quieras fijar?
5. **Cambio de cara del dashboard** (activas 2.139 → ~19.837): grande y visible. ¿Coordinamos el
   deploy del recómputo con aviso, o va directo?
6. **Legacy `estado_oferta`/`fecha_baja`**: ¿cuánto tiempo dual-write antes de deprecar y dejar de
   escribirlos? (propongo: hasta cerrar Fase 5 + 1 sprint de observación).
7. **CABA/PE "2 corridas completas ausente"**: depende de que el listado sea realmente completo cada
   corrida. PE pasó a local hace días; CABA sigue en VPS. Confirmar completitud antes de confiar la
   confirmación a la ausencia.
8. **Indeed `baja_inferida`**: nunca confirmable; los indicadores deben excluirla o marcarla. Además
   Indeed está bloqueado → su `fecha_ultimo_visto` está congelada; sus inferidas serán ruidosas.
9. **Discriminador HTML de ComputRabajo**: la vía existe (PASO 2) pero el marcador exacto vivo/caído
   hay que fijarlo con la muestra del drenaje; riesgo bajo, se valida en Fase 4.

---

## PAUSA

Spec redactada. No se escribe código hasta la aprobación de Gerardo (y sus respuestas a las
decisiones abiertas de §11). Al aprobar, se implementa por fases (§10), cada una reversible y
verificada antes de la siguiente.
