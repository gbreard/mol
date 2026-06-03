# Investigación — Uso de denominaciones argentinas en el pipeline

**Fecha:** 2026-05-19
**Origen:** SPEC W sub-tarea D.3 bloqueada por cero ofertas con `denominacion_arg`/`denominacion_esp` pobladas.
**Tipo:** Read-only, sin modificar código ni datos.
**Pedido por:** Gerardo (entender qué se rompe entre catálogo curado y display final).

---

## Resumen ejecutivo

Las columnas `denominacion_arg` y `denominacion_esp` se agregaron a `ofertas_dashboard`
en la migration 024 (SPEC W sub-tarea A) **sin ninguna lógica de escritura** asociada.
No existe código en el pipeline Python, en sync_to_supabase, ni en backfills que las
pueble. Tampoco existe una columna "denominación argentina" en la tabla `esco_argentino`
(que solo guarda skills consolidadas, no etiquetas alternativas).

El catálogo argentino curado (`config/sinonimos_argentinos_esco.json`, 22 ocupaciones)
**sí se usa** — pero solo como matcher de keywords para decidir ISCO/ESCO,
no como fuente de denominación legible. La "denominación argentina" como concepto
está implícita en las KEYS del JSON (ej `"jefe de mantenimiento"`, `"gerente"`),
pero esa información nunca se persiste por oferta.

El `esco_occupation_label` que las 68,152 ofertas ya muestran **es la denominación
española de España** ("mecánico de vehículos/mecánica de vehículos", "contable"), no
inglés. Cyn está viendo terminología europea sin saberlo, y por eso pidió "información
en español y argentina" — la española europea ya está, solo falta etiquetarla como tal
y agregar la argentina como complemento.

**Severidad:** baja. Es un gap de feature, no un bug. El pipeline funciona; las columnas
son nuevas y nunca tuvieron lógica de write.

---

## Inventario de fuentes argentinas

### Archivos en filesystem

| Path | Tamaño | Contenido relevante |
|---|---|---|
| `config/sinonimos_argentinos_esco.json` | 19 KB (mod. 2026-05-19) | 22 ocupaciones argentinas mapeadas a ESCO. **La KEY es la denominación argentina** (ej `"jefe de mantenimiento"`). El campo `esco_label` interno tiene el label europeo. NO hay un campo `denominacion_argentina` explícito. |
| `config/sinonimos_argentinos_esco_v1_legacy.json` | 12 KB | Versión vieja, no se usa. |
| `config/sinonimos_skills_argentinos.json` | 20 KB (mod. 2026-04-24) | Mapeo de skills argentinas. |
| `config/oficios_arg.json` | 5 KB | 170 oficios para regex extraction. Listas planas de strings, no estructura "argentino→ES". |
| `data/fine_tuning/train_argentino.json` | — | Pares contrastivos para entrenar embeddings. |

### Tablas en Supabase

| Tabla | Filas | Columnas con denominaciones |
|---|---|---|
| `esco_argentino` | 44 | `esco_occupation_uri`, **`esco_occupation_label`** (texto ES europeo), `isco_code`, `skills_consolidadas` (JSONB con skills curadas). **Sin columna `denominacion_argentina` ni `denominacion_espana`.** |
| `ofertas_dashboard` | 68,152 | `esco_occupation_label` (poblado en 100% — ES europeo), `denominacion_arg` (poblado en 0), `denominacion_esp` (poblado en 0). |

### Muestra de etiquetas europeas que Cyn ya está viendo

Las 68K ofertas tienen este texto en el campo `esco_occupation_label`:

```
ISCO 7231 → "mecánico de vehículos/mecánica de vehículos"
ISCO 4222 → "agente de centro de atención al cliente"
ISCO 4311 → "empleado de contabilidad/empleada de contabilidad"
ISCO 9333 → "mozo de almacén/moza de almacén"
ISCO 3322 → "representante comercial"
ISCO 2411 → "contable"
ISCO 9412 → "ayudante de cocina"
```

Esto es español de España (notar "contable" vs argentino "contador"; "mozo de almacén"
vs argentino "operario de depósito").

---

## Mapeo de uso en el matcher

### Lectura del JSON argentino

**`database/match_ofertas_v3.py:239-254`** carga `sinonimos_argentinos_esco.json` al
inicializar el matcher.

**`database/match_ofertas_v3.py:271-319`** (`_match_by_argentino_dict`) recorre las
KEYs del JSON y, si el título de la oferta contiene alguna de las variantes:

- Lee `esco_label` (línea 307): **el label europeo** → se persiste en
  `ofertas_esco_matching.esco_occupation_label`.
- Lee `esco_uri` (línea 309): URI ESCO.
- Lee `contextos` para desambiguar (ej "gerente" + "ventas" → ISCO 1221).

**La KEY del JSON (ej `"jefe de mantenimiento"`) se usa solo como matcher de keyword
en el título de la oferta. Nunca se guarda como dato.**

### Lectura de la tabla `esco_argentino` (Supabase)

| Archivo | Línea | Uso |
|---|---|---|
| `database/skills_implicit_extractor.py` | 1211–1278 | Carga `skills_consolidadas` para **boostear skills** (decisión D6 "boosting over filtering", +5pp). NO consulta denominaciones. |
| `fase3_dashboard/sql/056_rpc_match_occupations_argentino.sql` | toda | RPC que boostea similitud de ocupaciones con `prioritize_argentino=TRUE`. Lee `skills_consolidadas`. NO devuelve denominaciones. |
| `fase3_dashboard/mol-dashboard/app/api/esco-argentino/route.ts` | toda | CRUD del catálogo. Solo expone `esco_occupation_label` (europeo) + skills. |
| `scripts/ml/generate_training_pairs_from_argentino.py` | 46–127 | Genera pares contrastivos para fine-tuning. Lee `esco_occupation_label` + skills. |

### Escritura a `ofertas_dashboard`

| Archivo | Línea | Qué escribe |
|---|---|---|
| `scripts/exports/sync_to_supabase.py` | 717+ | Upsert principal. Mapea campos de SQLite a Supabase. **No mapea `denominacion_arg` ni `denominacion_esp`** (no existen en SQLite). |
| `scripts/db/populate_clae_seccion.py` | 130 | Backfill puntual de CLAE. |
| `scripts/exports/backfill_validation_columns.py` | 66 | Backfill de columnas de validación. NO toca denominaciones. |

**No existe ningún script ni función que escriba a `denominacion_arg` o `denominacion_esp`.**

### Referencias a `denominacion_arg`/`denominacion_esp` en TODO el repo

```
docs/specs/spec_w/SPEC_W_etapa1_visualizador.md   ← spec que las pidió
fase3_dashboard/mol-dashboard/lib/types.ts        ← agregadas en D.1 (este sprint)
fase3_dashboard/mol-dashboard/lib/supabase.ts     ← agregadas en D.1 (este sprint)
migrations/024_spec_w_audit_actions.sql           ← ALTER TABLE en sub-tarea A
tests/spec_w/test_migration_024.py                ← tests de la migration
```

**Cero referencias en código del pipeline.** Es feature spec'eada, columnas creadas,
pero ninguna lógica que las pueble.

---

## Conteos en BD

```sql
-- Total
SELECT count(*) FROM ofertas_dashboard;
-- → 68,152

-- Con denominación europea ya poblada
SELECT count(*) FROM ofertas_dashboard WHERE esco_occupation_label IS NOT NULL;
-- → 68,152 (100%)

-- Con denominación argentina poblada
SELECT count(*) FROM ofertas_dashboard WHERE denominacion_arg IS NOT NULL;
-- → 0

-- Con denominación española explícita
SELECT count(*) FROM ofertas_dashboard WHERE denominacion_esp IS NOT NULL;
-- → 0

-- Distribución de decision_metodo (proxy de cuánto se usa el diccionario argentino)
regla_prioridad:        531
semantico_unico:        234
dual_coinciden:         173
regla_zona_gris:         31
regla_por_score_bajo:    26
regla_override_semantico: 5
```

Nota sobre `decision_metodo`: el matcher v3 **usa `sinonimos_argentinos_esco.json`
dentro de la lógica `regla_prioridad`**. Las 531 ofertas con ese método pasaron por
el diccionario argentino para decidir su ISCO. Pero la denominación argentina no se
persiste — solo el ISCO y el `esco_label` europeo.

---

## Punto de ruptura identificado

**Escenario 2 confirmado: no existe lógica de write.**

```
       Catálogo argentino curado
   ┌──────────────────────────────────┐
   │ config/sinonimos_argentinos_esco │
   │  22 ocupaciones, KEYs argentinas │
   └──────────────────────────────────┘
                  │
                  ▼ se usa SOLO como matcher
        match_ofertas_v3.py:271-319
                  │
                  ▼ persiste isco + esco_label europeo
        ofertas_esco_matching.esco_occupation_label
                  │
                  ▼ sync_to_supabase.py
        ofertas_dashboard.esco_occupation_label  ← 68,152 pobladas (ES europeo)
        ofertas_dashboard.denominacion_arg       ← 0  ⛔ creada en M024, sin lógica
        ofertas_dashboard.denominacion_esp       ← 0  ⛔ creada en M024, sin lógica
```

**El concepto "denominación argentina" existe pero está enterrado:**
- Vive como **KEY del JSON sinonimos** (ej `"jefe de mantenimiento"`).
- Cuando una oferta matchea esa KEY, el sistema sabe internamente que la denominación
  argentina aplicable es esa string — pero solo persiste el ISCO y el label europeo.

**El concepto "denominación española explícita" en realidad es lo que ya existe** —
`esco_occupation_label` siempre tuvo texto en ES europeo. La feature D.3 pedía
mostrarlo como "🇪🇸 España" (etiqueta visual), no traerlo de una fuente nueva.

### Respuestas a las 5 preguntas de la consigna

1. **¿Existe la tabla/archivo `esco_argentino` con denominación local?**
   - Tabla `esco_argentino`: SÍ existe (44 filas), pero **no tiene columna de
     denominación argentina** — solo `esco_occupation_label` europeo + skills.
   - Archivo `config/sinonimos_argentinos_esco.json`: SÍ existe (22 ocupaciones).
     La denominación argentina es la KEY del objeto. NO es un campo explícito.

2. **¿El matcher consulta esa fuente?**
   - SÍ. `match_ofertas_v3.py` carga y usa el JSON sinonimos para resolver
     ISCO/ESCO en 531 ofertas (regla_prioridad). Pero **no escribe denominaciones
     a ofertas_dashboard** — solo persiste ISCO y label europeo.

3. **¿Existe equivalente en español de España?**
   - Sí, **ya está poblado en las 68K ofertas**. El campo
     `ofertas_dashboard.esco_occupation_label` siempre fue español europeo
     (proviene del catálogo ESCO oficial v1.2.0 que el sistema importó en ES).
     No es necesario importar `occupations_es.csv` aparte: ya está allí, solo
     que no estaba etiquetado como "ES" en la UI.

4. **¿Por qué `denominacion_arg`/`esp` nunca se pobló?**
   - **Escenario 2**: la lógica de write no existe. Las columnas fueron creadas
     preventivamente en migration 024 (sub-tarea A de SPEC W) anticipando el
     trabajo de D.3, pero nadie escribió el código que las puebla.
   - El backfill no existe, el sync_to_supabase no las mapea, y el matcher v3
     no las setea en ofertas_esco_matching local antes del sync.

5. **¿Cyn está viendo denominaciones argentinas en algún lugar?**
   - **NO directamente.** Cyn solo ve `esco_occupation_label` (europeo) en
     `ClasificacionPanel.tsx:116-121`. La denominación argentina existe en el
     sistema (como KEY de sinonimos JSON y como variantes regex en oficios_arg)
     pero **no se muestra en ninguna pantalla**.

---

## Severidad

**BAJA.** No es un bug. Es un gap de feature:
- El pipeline funciona correctamente — el matching argentino sí ocurre, solo no
  expone su vocabulario al usuario final.
- Las columnas nuevas no rompen nada (son TEXT nullables, sin constraints).
- Cero ofertas afectadas en producción por la ausencia.
- Cyn pidió la feature pero puede operar sin ella; ve labels europeos hoy.

---

## Opciones de resolución

### Opción A — Backfill barato desde JSON sinonimos (escala limitada)

Poblar `denominacion_arg` solo para las ~531 ofertas que matchearon por
`regla_prioridad` con el diccionario argentino:

1. Script Python que itere por `ofertas_dashboard` con `decision_metodo='regla_prioridad'`
   y `regla_aplicada IS NOT NULL`.
2. Para cada una, leer la KEY de `sinonimos_argentinos_esco.json` que disparó la regla
   (esto requiere mapping del `regla_aplicada` a la KEY del JSON — habría que verificar
   si ese mapping ya existe en BD).
3. Escribir esa KEY como `denominacion_arg`.

**Costo:** ~2-4h.
**Cobertura:** ~531/68,152 = 0.78%. Las otras 67K ofertas seguirían con `denominacion_arg = NULL`.
**Pro:** dato real, viene del diccionario curado.
**Contra:** cobertura ridícula. La feature se ve "rota" en el 99% de los casos.

### Opción B — Backfill amplio via diccionario inverso ISCO → AR

Construir un mapeo manual ISCO → denominación argentina canónica (ej `7231 →
"mecánico automotor"`, `2411 → "contador"`) y poblar TODAS las ofertas con
ISCO mapeado.

1. Curar un JSON nuevo `denominaciones_argentinas_por_isco.json` (~50-100 entradas
   manuales para los ISCOs más frecuentes).
2. Backfill que mira `isco_code` y aplica el mapeo.

**Costo:** ~6-10h (la mayor parte es el trabajo manual de curación).
**Cobertura:** 80-95% si se cubren los ISCOs top.
**Pro:** Cyn ve denominación argentina en casi todas las ofertas.
**Contra:** ISCO es 4 dígitos = mucha pérdida de granularidad. Ej ISCO 5223
incluye "vendedor", "cajero", "repositor" → ¿cuál denominación argentina ponés?
La "denominación argentina canónica" por ISCO es debatible.

### Opción C — Resolución on-the-fly en el read (sin backfill)

NO poblar las columnas. En vez de eso, el panel `ClasificacionPanel` resuelve
en tiempo de render:

- `denominacion_arg` viene de un mapping ISCO → AR (similar a B) que se carga al
  inicio del dashboard como JSON estático.
- `denominacion_esp` es directamente el `esco_occupation_label` ya existente,
  solo se re-etiqueta visualmente como "🇪🇸 España".

**Costo:** ~3-4h (curar mapping ISCO → AR + UI).
**Cobertura:** 100% si el mapping cubre todos los ISCOs vistos.
**Pro:** sin migration de datos. Sin re-sync. Cambio JSON-only se propaga sin
re-deploy del pipeline.
**Contra:** el mapping queda solo en frontend. Si después se quiere usar para
filtros SQL, tipo "ver todas las ofertas de operarios", hay que tirarlo a BD.

### Opción D — Diferir D.3 indefinidamente, cerrar Sprint 1 sin esa sub-tarea

No implementar nada ahora. Documentar que la feature requiere trabajo de
curación previo (opciones B o C) y dejarla para Sprint 2 o más adelante.

**Costo:** 0h.
**Cobertura:** 0%.
**Pro:** Sprint 1 cierra limpio con A/B/C/D.1/D.2 funcionando. Cyn igual tiene
todo lo demás de SPEC W.
**Contra:** la feature de Cyn no se entrega. Tampoco hay calendario claro de
cuándo se entregaría.

---

## Recomendación

**Opción D + reabrir como ticket aparte cuando se priorice.**

Razones:
1. Las opciones A, B y C requieren trabajo de **curación de datos** (decidir qué
   string mostrar para 50+ ISCOs), que no es trabajo de Claude — es decisión de
   producto. Cyn o el equipo OEDE tendrían que sentarse y armar el diccionario AR.
2. El gap es de feature, no de bug. Sprint 1 de SPEC W ya entregó las mejoras
   más críticas (filtros, audit toolbar, Excel B2).
3. La opción C es la más limpia técnicamente para futuro, pero depende del
   diccionario curado de la opción B. Hacerla con tabla vacía es la misma
   conclusión que el bloqueo actual.
4. El campo `esco_occupation_label` ya muestra denominación europea (aunque sin
   bandera 🇪🇸). Si Cyn quiere distinguirla visualmente, eso sí es una sub-tarea
   chica e independiente que podría hacerse fuera de D.3.

**Mini-tarea alternativa que SÍ se puede hacer ya** (sin curación de datos):
agregar al `ClasificacionPanel` un pequeño indicador `(ES)` o tooltip que
explique que `esco_occupation_label` proviene de ESCO oficial en español europeo.
Esto cubre 50% del pedido de Cyn ("información en español visible") sin requerir
curar denominaciones argentinas.

---

## Observaciones adicionales no concluyentes

- En `scripts/update_esco_metadata.py:8` el comentario dice
  `esco_label: Label en español` — esto sugiere que **históricamente el equipo
  asumía que `esco_label` era ES, no inglés**. Esa intuición es correcta pero
  nunca se etiquetó "europeo" vs "argentino" en el código ni en el dashboard.
- La migration 024 fue diseñada **como parte de SPEC W**, no como parte del
  pipeline general. Quien la escribió (probablemente yo en sub-tarea A) creó
  las columnas anticipando D.3 sin coordinar con un script de write. Es un caso
  típico de "schema first, fill later" donde el "later" nunca llega.
- No se encontraron triggers, funciones SQL, ni stored procedures que escriban
  a `denominacion_arg`/`denominacion_esp`.

---

**Cierre:** investigación read-only completa. Sin cambios en código ni datos.
Decisión pendiente de Gerardo: A / B / C / D.
