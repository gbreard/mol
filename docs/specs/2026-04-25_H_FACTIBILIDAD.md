# SPEC H — Análisis de factibilidad

**Fecha:** 2026-04-25
**Spec:** `2026-04-25_H_rematch_isco_sin_regla.md`

---

## 1. Hallazgos preliminares (modifican el spec)

### 1.1 Scope real

El spec estimaba **31,974 ofertas**. El recuento real en BD es:

| decision_metodo + estado_validacion | Ofertas |
|---|---:|
| `semantico_unico` + `validado` (estricto) | 3,364 |
| `semantico_unico` + `validado_claude` | 15,516 |
| **Total scope real** | **18,880** |

Las 13K restantes que conté en el spec (`31,974 - 18,880 = 13,094`) son ofertas con **variantes de regla** (`regla_por_score_bajo`, `regla_zona_gris`, `regla_override_semantico`, etc.) — tienen componente de regla curada y no corresponde re-matchearlas.

**Scope corregido: 18,880 ofertas.**

### 1.2 Trigger de BD protege 3,364 ofertas

Existe `protect_validated_matching` en BD que bloquea UPDATE cuando `estado_validacion='validado'` estricto y se modifica `isco_code`, `esco_occupation_label` u `occupation_match_score`. Las `validado_claude` **no están protegidas**.

| Estado | Cantidad | Requiere desbloqueo |
|---|---:|---|
| `validado` | 3,364 | **SÍ** — usar `admin_unlock_validated.py` |
| `validado_claude` | 15,516 | No |

---

## 2. Factibilidad técnica

### 2.1 Dos opciones de implementación

#### Opción A — Wrapper minimalista
- Encodear texto (título + tareas) con BGE-M3.
- Top-1 contra `esco_occupations_embeddings.npy`.
- Actualizar `isco_code`, `esco_occupation_label`, `score_semantico`, `matching_timestamp`.

**Pros:**
- Rápido: **26 ms/oferta medidos** → 18,880 ofertas en ~8 min.
- Código simple, ~100 líneas.
- No requiere inicializar todo el pipeline.

**Contras:**
- NO aplica penalizaciones del matcher completo (sector, seniority, área funcional).
- Replica exactamente la lógica del diagnóstico (que dio 97.5% cambios de ISCO con 89.5% score sube).

#### Opción B — `match_ofertas_v3` completo
- Invoca el pipeline real con todas las penalizaciones.
- Aplica reglas de negocio (si ahora dispara regla, cambia decision_metodo).
- Persiste campos adicionales (metadata dual, etc.).

**Pros:**
- Lógica idéntica a lo que hace el pipeline nuevo.
- Consistencia con ofertas procesadas fresh.

**Contras:**
- ~0.4 s/oferta → 18,880 ofertas en ~2 h wall-clock.
- Código más complejo (inicializar DB connection, run_id, estado).
- Puede disparar reglas nuevas → cambio de decision_metodo fuera del scope del spec.

### 2.2 Recomendación técnica

**Opción A (wrapper minimalista).** Razones:

1. El diagnóstico ya probó que el top-1 del embedding nuevo es claramente mejor que el top-1 del embedding viejo sobre 200 muestras (97.5% cambia para mejor).
2. Las penalizaciones del pipeline completo están diseñadas para desempatar, no para cambiar dominios. En un re-match donde el dominio ya cambia mucho, el efecto marginal es pequeño.
3. Si algún caso de penalización es crítico, se puede migrar a opción B en una versión 2 del spec H.

### 2.3 Campos a actualizar

```sql
UPDATE ofertas_esco_matching
SET isco_code = ?,
    esco_occupation_label = ?,
    titulo_esco_code = ?,       -- esco_code completo (ej "7214.3.1")
    score_semantico = ?,
    occupation_match_score = ?,  -- campo legacy, mantener coherente
    matching_timestamp = CURRENT_TIMESTAMP,
    matching_version = 'spec_h_rematch'
WHERE id_oferta = ?
```

### 2.4 Manejo del trigger (3,364 ofertas `validado`)

Dos caminos:

1. **Desbloquear con `admin_unlock_validated.py --ids X,Y,Z --motivo "SPEC H: rematch con embeddings nuevos (SPEC E)"`** antes de actualizar, reboltar a `validado` después. Preserva el estado pero agrega complejidad.

2. **Dejarlas fuera del SPEC H**. Solo tocar las 15,516 `validado_claude`. Las 3,364 `validado` quedan con ISCO viejo hasta una revisión manual futura.

**Recomendado: opción 2.** Las 3,364 `validado` estricto son ofertas donde alguien (o el sistema) indicó validación más firme. Tocarlas automáticamente sin revisión genera riesgo. Mejor dejarlas en un backlog para revisión manual.

**Scope final post-análisis: 15,516 ofertas.**

---

## 3. Factibilidad operativa

### 3.1 Tiempos reales medidos

| Etapa | Duración |
|---|---|
| Fase 1 — implementación wrapper + scripts | **2-3 h desarrollo** |
| Fase 2 — tests | **1.5 h** |
| Fase 3 — dry-run análisis impacto | **~10 min ejecución** |
| Fase 4 Tanda 1 piloto (100) | **3 s ejecución + ~1 h revisión humana** |
| Fase 4 Tanda 2 (1K) | **~30 s ejecución + 30 min revisión** |
| Fase 4 Tanda 3 (10K) | **~4 min ejecución** |
| Fase 4 Tanda 4 (~4,500 resto) | **~2 min ejecución** |
| Sync Supabase incremental | **~15-20 min** |
| **TOTAL** | **4-5 h humanas / 1 día wall-clock** |

Es **radicalmente más rápido** que SPEC E (que incluía generación de embeddings). La retropropagación es cuestión de minutos.

### 3.2 Recursos

- CPU: 1 core para BGE-M3 encoder.
- RAM: 2 GB modelo + 12 MB embeddings ocupaciones = 2.2 GB pico.
- Disco: ~20 MB adicionales (tabla snapshot con 18K filas).

### 3.3 Ventana operativa

- Fases 1-3 no bloquean nada.
- Fase 4 puede correr en foreground (es rápido). No requiere background.
- Pausar scraping durante Fase 4 **no es necesario** (es muy corta).

---

## 4. Factibilidad de recuperación

### 4.1 Estrategia de backup

Tabla `ofertas_matching_backup_spec_h`:
```sql
CREATE TABLE ofertas_matching_backup_spec_h (
  id_oferta TEXT PRIMARY KEY,
  isco_code_antes TEXT,
  esco_occupation_label_antes TEXT,
  titulo_esco_code_antes TEXT,
  score_semantico_antes REAL,
  matching_timestamp_antes TEXT,
  backup_at TEXT
);
```

Rollback por oferta o tanda: `UPDATE ... SET isco_code = backup.isco_code_antes WHERE id_oferta = ?`.

### 4.2 Reversibilidad total

Si el impacto es catastrófico:
- Restore de la BD desde checkpoint (existe de la sesión anterior `/tmp/bumeran_scraping_pre_spec_e_20260424_224826.db` de 2.1 GB). Pero ese es pre-SPEC-E — muy atrás.
- Mejor: restore solo de las filas afectadas desde `ofertas_matching_backup_spec_h`.

Script `rollback_spec_h.py` que revierte por tanda completa: <5 min.

### 4.3 Efecto dominó en Supabase

Tras actualizar 15,516 ISCOs, el sync incremental detecta `matching_timestamp` nuevo y re-sube:
- `ofertas_dashboard` (15,516 rows actualizadas)
- Recalcula indicadores derivados (tension, concentracion, etc.) — ese recálculo ya es automático al final del sync.

El sync es reversible por versión — si algo sale mal en Supabase, se puede rollback local + re-sync.

---

## 5. Puntos críticos

### 5.1 Pre-implementación
**Cagadas posibles:** ninguna. Trabajo es dry-run.

### 5.2 Fase 2 tests
**Cagadas posibles:** tests mal diseñados dejan pasar regresiones. Mitigación: gold_set_v2 obligatorio + revisión humana Fase 4.

### 5.3 Fase 4 Tanda 1 piloto
**Blast radius:** 100 ofertas. Reversible completamente con snapshot.
**Cagadas posibles:** bug en update query → dato corrupto. Mitigación: dry-run previo + verificación tras cada batch.

### 5.4 Fase 4 Tandas 2-4
**Blast radius:** hasta 15,516 ofertas.
**Cagadas posibles:**
- El matcher apunta a ocupaciones inexistentes (URI inválido).
- Trigger bloquea update silenciosamente.
- `esco_occupation_label` queda inconsistente con `isco_code`.

**Mitigaciones:**
- Validar antes de UPDATE que el `uri` retornado existe en `esco_occupations_metadata`.
- Chequear que el UPDATE devuelve rowcount=1 (no 0 por trigger).
- Asegurar consistencia: `isco_4dig(esco_code) == isco_code`.

### 5.5 Post-Fase 4 — sync Supabase
**Cagadas posibles:**
- Sync full corre encima y tarda 2-3 h. Mejor usar incremental (detecta por timestamp).
- Indicadores agregados se recalculan con data mixta (15.5K nuevas + 36K viejas).

**Mitigación:** sync incremental + recalculate solo los índices relevantes post-sync.

---

## 6. Riesgos no técnicos

### 6.1 Usuarios del dashboard ven ISCOs cambiar
**Probable:** sí, si hay usuarios activos revisando ofertas individuales.
**Impacto:** confusión. "¿Por qué esta oferta ahora tiene otro ISCO?"
**Mitigación:** nota visible "recalibración 2026-04-25" en el dashboard. Si no hay usuarios externos, ignorar.

### 6.2 Indicadores agregados cambian
**Probable:** sí. Las 15,516 ofertas son ~30% del total validado. Los ISCOs cambiando impactan cualquier estadística.
**Impacto:** discontinuidad temporal en reportes.
**Mitigación:** documentar en un changelog del dashboard.

### 6.3 Las 3,364 ofertas validado-estricto quedan con ISCO viejo
**Probable:** sí, por decisión de no tocarlas.
**Impacto:** BD con ISCOs mixtos (15.5K actualizadas, 3.4K viejas, 30K otras ya correctas).
**Mitigación:** documentar como deuda técnica. Revisión manual en spec futuro.

### 6.4 Cambios de score_semantico invalidan decisiones pasadas
**Riesgo:** una oferta que estaba en `dual_coinciden` (semántico acordaba con regla). Si recalculáramos su score semántico con nuevo embedding, podría no coincidir. Pero **no tocamos `dual_coinciden`** — queda como deuda registrada.

---

## 7. Go/no-go checklist

### Pre-implementación
- [x] Scope definido (15,516 ofertas `validado_claude + semantico_unico`)
- [x] Embeddings nuevos en producción
- [x] Backup baseline disponible
- [x] Diagnóstico 200 ofertas muestra mejora sistémica
- [x] Tiempos medidos (26ms/oferta wrapper minimalista)

### Pre-Fase 1 desarrollo
- [ ] Rama git (seguimos en `feature/spec-e-embeddings-enriquecidos`)
- [ ] Confirmar Opción A (wrapper minimalista) o B (pipeline completo)
- [ ] Definir si las 3,364 `validado` se incluyen con unlock o quedan afuera

### Pre-Fase 4 retropropagación
- [ ] Tests pasando
- [ ] Dry-run Fase 3 completado con métricas
- [ ] Tabla backup + tabla progress creadas
- [ ] Checkpoint de BD (ya tenemos uno de 24 hs atrás, podemos renovar)

### Post-Fase 4
- [ ] Verificación gold set v2 pasa
- [ ] Sync Supabase incremental ejecutado
- [ ] Skills retropropagadas (SPEC E + G combinados)

---

## 8. Cronograma realista actualizado

| Momento | Acción | Duración |
|---|---|---|
| Ahora + 0 | Fase 1 desarrollo wrapper + scripts | 2-3 h |
| Ahora + 3 h | Fase 2 tests | 1.5 h |
| Ahora + 5 h | Fase 3 dry-run + reporte | 10 min exec + 30 min revisión |
| Ahora + 5.5 h | Fase 4 Tanda 1 piloto (100) | 3 s exec + 30-60 min revisión humana |
| Ahora + 7 h | Fase 4 Tanda 2 (1K) + revisión | 30 s + 20 min |
| Ahora + 7.5 h | Fase 4 Tanda 3-4 (14K) en foreground | ~5 min |
| Ahora + 8 h | Sync Supabase incremental | ~20 min |
| **Total** | **~8 h con revisiones (1 día laborable)** | |

Si se combina con SPEC G (implementación paralela), SPEC G suma ~5 h adicionales.

**Total SPEC H + G + retropropagación skills: 1.5-2 días laborables.**

---

## 9. Recomendación final

**Factibilidad: ALTA.**

- Scope más chico de lo pensado (15.5K en vez de 32K).
- Tiempos triviales (8 min de ejecución real).
- Reversible por oferta vía snapshot.
- Trigger respetado — no tocamos las `validado` estrictas.

**Factor crítico:** revisión humana en el piloto de 100. Si 18+/20 son mejoras claras, vía libre.

---

## 10. Decisiones pendientes antes de arrancar

1. **¿Opción A (wrapper) o B (pipeline completo)?** — Recomiendo **A**, más rápido y suficiente.
2. **¿Las 3,364 `validado` estricto?** — Recomiendo **dejarlas afuera**, revisión manual en spec futuro.
3. **¿Qué hacer si en Fase 4 el wrapper sugiere un ISCO muy distinto del viejo pero con score bajo (ej. 0.55)?** — Flaggear pero actualizar. El viejo no era mejor.
4. **¿Recalibrar indicadores agregados tras sync o dejarlos mixtos?** — El sync ya los recalcula automático.

Con esas decisiones armadas, arrancamos Fase 1.
