# Issue: desincronización entre `nlp_validation_rules.json` y `sector_canonico.json`

**Fecha:** 2026-05-14
**Origen:** Revisión pre-régimen continuo (`run_20260514_0634`, --limit 1000)

## Problema

La regla **NV02** (validación de sector canónico en NLP Gate) tiene su propia lista
hardcoded de ~60 sectores válidos en `config/nlp_validation_rules.json`.

`config/sector_canonico.json` existe pero lo usa otro componente (CLAE mapping),
**NO** NV02.

Las dos listas están desincronizadas:
- `sector_canonico.json`: tiene `"Servicios Profesionales"` (mayúscula), `"Farmacéutica"`
- `nlp_validation_rules.json` (NV02): NO tenía esos antes del fix del 2026-05-14

Resultado: falsos positivos del NLP Gate sobre ofertas con sectores válidos pero
ausentes en la lista hardcoded de NV02.

## Síntoma

5 ofertas bloqueadas en test `--limit 1000` (0.5% del lote) por NV02 sobre
sectores legítimos: `"Servicios personales"`, `"Servicios profesionales"`, `"Farmacéutica"`.

## Causa raíz

Lógica duplicada en dos archivos sin fuente única de verdad. Mismo patrón que
otros casos del proyecto (scripts huérfanos, fixes parciales).

## Solución estructural (no urgente)

Refactorizar NV02 para que lea de `sector_canonico.json` como fuente única.
Eliminar lista inline en `nlp_validation_rules.json`.

Trabajo estimado: 1-2h. Requiere:
- Modificar carga de regla NV02 para leer JSON externo
- Normalizar formato (mayúsculas, tildes) entre ambos archivos
- Test sobre Gold Set para confirmar no-regresión

## Aplicación inmediata (fix aplicado 2026-05-14)

Agregados 3 sectores a la lista inline de NV02 para resolver falsos positivos
detectados:
- `"Servicios personales"`
- `"Servicios profesionales"`
- `"Farmacéutica"`

La desincronización subyacente queda como deuda.

## Prioridad

Baja-media. No bloquea operación. Pero cada sector nuevo que se agregue al canon
tiene que duplicarse en NV02 hasta resolver. Acumula fricción.

---

## Actualización 2026-05-14 (parte 2) — Fix NV04 typo `semi_senior`

Detectado en la misma revisión pre-régimen: 1 oferta del test `--limit 1000`
fue bloqueada por NV04 (`error_nlp_seniority_invalido`).

### Investigación

- LLM extrajo `'senior'` correctamente
- Postprocessor lo sobrescribió a `'semi_senior'` (con underscore) vía la regla
  `seniority_no_junior_experiencia_req` en `config/nlp_correction_rules.json:145`
- NV04 espera `'semisenior'` (sin separador) — formato coherente con todas
  las demás reglas y con `nlp_inference_rules.json`

### Diagnóstico

**NO es el mismo patrón sistémico que NV02.** Es un **typo aislado**: solo 1 línea
del proyecto producía `semi_senior` con underscore; el resto del sistema (canon,
NV04, otras reglas de inferencia) usa formato sin separador.

Histórico afectado: 2 ofertas en 60.422 (0.003%).

### Fix aplicado

`config/nlp_correction_rules.json:145`:
```diff
-        "resultado": "semi_senior"
+        "resultado": "semisenior"
```

### Recuperación de históricas

Las 2 ofertas ya estaban con `gate=bloqueado` y sin matching. Aplicado UPDATE
puntual (`UPDATE ofertas_nlp SET nivel_seniority = 'semisenior' WHERE nivel_seniority = 'semi_senior'`)
+ re-corrida de matching con `--skip-nlp --ids`. Ambas con `gate=aprobado` y
matching persistido en `run_20260514_1214`.

### Por qué NO requiere refactor estructural

A diferencia de NV02 (que tiene problema de duplicación de listas), NV04 sigue
el canon correcto. La regla bugueada simplemente escribía un valor mal-formateado.
No hay deuda estructural acá — la corrección de typo es la solución completa.
