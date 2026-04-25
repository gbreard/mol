# SPEC H — Re-matching de ocupación ESCO para ofertas sin regla

**Fecha:** 2026-04-25
**Autor:** Claude + Gerardo
**Estado:** Draft — pendiente análisis de factibilidad
**Scope:** Re-ejecutar el matching de ocupación ESCO para las 31,974 ofertas validadas donde `decision_metodo = 'semantico_unico'` (no tuvieron regla aplicada). No toca ofertas con regla ni con dual_coinciden.
**Dependencia:** SPEC E promocionado (embeddings de ocupaciones ya regenerados con texto enriquecido).
**Bloquea a:** SPEC G (filtro skills_nlp) + retropropagación final de skills. El ISCO debe estar correcto antes de re-extraer skills.
**Basado en:** Diagnóstico del 2026-04-24 sobre 200 ofertas — 97.5% cambiarían ISCO con embeddings nuevos, 89.5% con mejora de score semántico.

---

## 1. Contexto

### 1.1 Diagnóstico que motiva el spec

Al terminar SPEC E (embeddings ESCO enriquecidos promocionados a producción) nos preguntamos si el matching oferta→ocupación seguía siendo correcto. Los embeddings de ocupaciones ESCO se regeneraron de texto="label solo" → texto="label + jerarquía ISCO + top skills esenciales".

Diagnóstico sobre 200 ofertas validadas con `decision_metodo='semantico_unico'`:

| Métrica | Resultado |
|---|---|
| Ofertas donde el top-1 NO cambia | **5 (2.5%)** |
| Ofertas donde el top-1 cambia | **195 (97.5%)** |
| De los cambios, donde el score sube | **179 (89.5%)** |
| Score promedio viejo | ~0.60 |
| Score promedio nuevo | ~0.70 |

### 1.2 Ejemplos cualitativos (cambios correctos)

| Oferta | ISCO BD (viejo) | ISCO con nuevos embeddings |
|---|---|---|
| Técnico de reparaciones | gerente de tienda ortopédicos (1420) | técnico reparador de material de oficina (7421) |
| Operador línea producción | cuidador residencial (3412) | operador de máquinas (8121) |
| Seguridad y vigilancia | almacenero marroquinería (4321) | vigilante de accesos (5414) |
| Administrativo de compras | maestro maltero (7515) | jefe de compras (3323) |
| Secretario/a de servicio | supervisor de destilería (3122) | secretario/secretaria (4120) |
| Soporte técnico IT | encargado de relaciones públicas (2432) | gestor asistencia TIC (3512) |
| Lashista | responsable de procesos (2421) | esteticista (5142) |
| Integrante de cocina | director política turística (1213) | ayudante de cocina (9412) |
| Auxiliar de carnicería | responsable documentación sanitaria (3252) | vendedor especializado en carnicería (5223) |
| Asistente de producción | dinamitero (7542) | asistente de tienda (5223) |

### 1.3 Interpretación

Los ISCOs actuales de las ofertas sin regla son **en su mayoría erróneos** porque se calcularon con embeddings pobres (solo `label`). El diagnóstico muestra que los nuevos embeddings discriminan dominios con mucho mejor calidad. No se puede retropropagar skills sobre ISCOs incorrectos — el resultado sería coherente técnicamente pero incoherente en lo narrativo (una oferta "Lashista" con ISCO "responsable de procesos" y skills de belleza no tiene sentido).

### 1.4 Por qué no se detectó antes

- El 55% de las validaciones son `auto_transicion` del pipeline — aplican checks básicos sin revisar ISCO específico.
- El score semántico viejo (0.57-0.65) parecía aceptable pero era ruido del modelo. Los nuevos embeddings lo demuestran al elevar consistentemente a 0.65-0.75.
- Solo 15 ofertas tuvieron revisión manual por humano real (según `validado_por`).

---

## 2. Objetivo

Ejecutar un re-matching completo de las 31,974 ofertas sin regla usando el pipeline actual (`match_ofertas_v3`) que ya opera con los embeddings enriquecidos. Actualizar sus `isco_code`, `score_semantico`, `titulo_esco_code` y metadata asociada, manteniendo `estado_validacion` intacto.

## 3. Scope

### 3.1 Qué tocamos
- Solo ofertas donde `decision_metodo = 'semantico_unico'` (~31,974 ofertas).
- Actualizar: `isco_code`, `score_semantico`, `titulo_esco_code`, `matching_timestamp`, `matching_version`, `run_id`.
- Mantener intactos: `estado_validacion`, `validado_por`, `validado_timestamp`.

### 3.2 Qué NO tocamos
- Ofertas con `regla_prioridad` (20,574). Sus ISCOs vienen de reglas curadas.
- Ofertas con `dual_coinciden` (9,707). Regla y semántico coincidían — cambio de uno solo no invalida la decisión dual.
- Ofertas con otros métodos de regla (`regla_critica`, `regla_override_*`, `regla_manual*`, `regla_por_score_bajo`, `regla_revisar`, `regla_zona_gris`) — 3,371 ofertas. Todas tienen componente de regla curada.
- Ofertas con `semantico_alta_confianza` (16) — ya son de alta confianza.
- Ofertas `pendiente` — las procesa el pipeline normal.
- El campo `skills_semantico_json` — ese se regenera en la retropropagación separada (SPEC E + G).

### 3.3 Tabla resumen del scope

| decision_metodo | Ofertas | Acción |
|---|---:|---|
| regla_prioridad | 20,574 | NO tocar |
| dual_coinciden | 9,707 | NO tocar |
| semantico_unico | **31,974** | **re-matchear** ✓ |
| regla_por_score_bajo | 1,307 | NO tocar |
| regla_zona_gris | 1,501 | NO tocar |
| Otros con regla | 563 | NO tocar |
| semantico_alta_confianza | 16 | NO tocar |
| **TOTAL afectado** | **31,974** | |

---

## 4. Diseño técnico

### 4.1 Qué pipeline usar

Reutilizar **`database/match_ofertas_v3.py`** que ya:
- Usa los embeddings nuevos (en producción post-SPEC E).
- Aplica la lógica completa: reglas de negocio → diccionario argentino → semántico → penalizaciones.
- Tiene tests del gold set.

No reinventamos matching. Solo lo ejecutamos sobre las 31,974 ofertas.

### 4.2 Script nuevo: `scripts/embeddings/rematch_isco_spec_h.py`

Responsabilidades:
1. Seleccionar ofertas a procesar (por tanda).
2. Llamar al matcher sobre cada una.
3. Validar que la regla NO dispare (si dispara, descartar — estaba en lugar incorrecto).
4. Hacer snapshot del estado previo en tabla `ofertas_matching_backup_spec_h` (solo columnas que vamos a cambiar).
5. Actualizar los 6 campos del scope.
6. Registrar en `spec_h_rematch_progress` para resumabilidad.
7. Commits por batch de 500.

### 4.3 Protección contra cambios indeseados

- Si el re-matching produce `decision_metodo != 'semantico_unico'` (ej. ahora dispara una regla), **saltar** la oferta y loggear. Significa que el matching descubrió que había una regla aplicable que no aplicó en su momento — ese caso merece revisión manual, no actualización automática.
- Si el re-matching produce el mismo ISCO, igual actualizar `score_semantico` (nuevo score). No es regresión.
- Si `score_semantico` nuevo es **menor** que el anterior y además cambia el ISCO, flaggear como sospechoso pero procesar (datos del diagnóstico muestran que esos casos son raros: solo 10.5%).

### 4.4 Orden de ejecución (gradual como SPEC E Fase 4)

- **Tanda 1 — PILOTO**: 100 ofertas random. Revisión manual de 20. Commit pre-tanda 2.
- **Tanda 2 — VERIFICACIÓN**: 1,000 estratificadas por ISCO actual (para ver distribución de cambios).
- **Tanda 3 — SCALE-UP**: 10,000 en background.
- **Tanda 4 — RESTO**: ~20,874 en background.

Cada tanda con snapshot previo + resumable.

### 4.5 Preservar trazabilidad

En `spec_h_rematch_progress`:
- `isco_anterior`, `isco_nuevo`, `score_anterior`, `score_nuevo`, `cambio_familia_2dig`, `procesada_at`, `tanda`, `run_id`.

Esto permite:
- Rollback por tanda o por oferta.
- Reporte agregado de impacto.
- Análisis de cambios problemáticos.

### 4.6 Efecto dominó — qué tablas se ven afectadas

| Tabla / Vista | Impacto |
|---|---|
| `ofertas_esco_matching` (isco_code, score) | Actualización directa |
| `ofertas_esco_skills_detalle` | No se toca aquí. Se re-genera en retropropagación posterior de skills. |
| Indicadores agregados (`concentracion_ocupacional`, `tension_ocupaciones`, etc.) | Se recalculan al próximo sync Supabase full. |
| Dashboard Supabase `ofertas_dashboard` | Se actualiza con próximo sync (incremental auto detecta `matching_timestamp`). |

---

## 5. Plan por fases

### Fase 1 — implementación (~3 h)

- Crear tabla `ofertas_matching_backup_spec_h` y `spec_h_rematch_progress`.
- Script `rematch_isco_spec_h.py` con selección por tanda, dry-run, resumable.
- Integración con `match_ofertas_v3` en modo "re-match".
- Script auxiliar `analyze_spec_h_impact.py` para reportes.

### Fase 2 — tests (~2 h)

- Unit: selección de scope (no tocar con regla, tocar solo semantico_unico).
- Integración: re-match sobre 10 ofertas, verificar que mantiene estado_validacion.
- Regresión: gold_set_v2 sigue pasando 47/48.
- Manual: revisar 20 casos del piloto.

### Fase 3 — análisis de impacto dry-run (~30 min)

Sobre las 31,974 ofertas, sin persistir, reportar:
- % que cambiarían ISCO.
- Distribución de cambios por familia ISCO (1-dig, 2-dig).
- Score avg antes/después.
- Casos sospechosos (score baja + cambio de ISCO).
- Ofertas donde ahora dispararía una regla que antes no → flag para revisión manual.

### Fase 4 — retropropagación gradual (~4 h wall-clock)

- Tanda 1 piloto (100) → revisión humana de 20 casos.
- Tanda 2 (1K) → verificación.
- Tanda 3 (10K) background.
- Tanda 4 (resto) background.

Cada tanda: snapshot → re-match → commit → report.

---

## 6. Tests

### 6.1 Unit (`tests/matching/test_spec_h_rematch.py`)

- `test_seleccion_respeta_scope`: ofertas con regla_prioridad NO aparecen en la muestra.
- `test_seleccion_respeta_scope_dual`: ofertas con dual_coinciden NO aparecen.
- `test_estado_validacion_intacto`: tras re-match, `estado_validacion` no cambia.
- `test_backup_se_crea`: antes de actualizar, el backup tiene el estado anterior.
- `test_resumable`: al reiniciar, salta ofertas ya en progress.
- `test_rollback_por_oferta`: puede revertir una oferta específica al snapshot.
- `test_caso_regla_ahora_dispara`: si re-match dispara una regla, se salta y se loggea.

### 6.2 Regresión

- Gold set v2 (`tests/matching/test_gold_set_v2_verified.py`) sigue en 47/48.
- Tests existentes de `match_ofertas_v3` pasan.

### 6.3 Validación manual

- Revisión de 20 ofertas del piloto: ¿el ISCO nuevo parece correcto al humano?

---

## 7. Criterios de éxito

### 7.1 Cuantitativos

- **Ninguna** oferta con regla (20K + 10K + 3K) fue tocada.
- `estado_validacion` intacto en el 100% de ofertas procesadas.
- Score semántico promedio sube (esperado 0.60 → 0.70 según diagnóstico).
- Ofertas con ISCO que cambia: 95-98% (alineado con diagnóstico).
- **Cambios consistentes con dominio de la oferta** según revisión manual del piloto.

### 7.2 Cualitativos (sobre el piloto de 100)

- Al menos 18/20 revisadas: el ISCO nuevo es más coherente con el título+tareas que el ISCO viejo.
- Casos "edge" (score baja + cambio) revisados uno a uno.

### 7.3 Operacionales

- Rollback completo de una tanda: <5 min vía snapshot.
- Retropropagación total de 32K: <4 h wall-clock.
- 0 errores en commits (transacciones atómicas por batch).

---

## 8. Riesgos y mitigaciones

### 8.1 ISCO cambia pero el nuevo también es incorrecto

**Riesgo:** el matcher con nuevos embeddings tampoco acierta; solo cambia un error por otro. El diagnóstico sobre 200 muestra que las skills son coherentes (89.5% score sube), pero no es prueba absoluta.

**Mitigación:** piloto de 100 con revisión humana de 20. Si <15/20 son mejoras, abortamos y reconsideramos.

### 8.2 Cambio de ISCO rompe indicadores históricos

**Riesgo:** métricas como "tensión de ocupaciones" están calculadas sobre los ISCOs viejos. Cambiar 32K ISCOs a la vez rompe la narrativa temporal.

**Mitigación:** documentar explícitamente en el dashboard "recalibración 2026-04-25 post-SPEC-E". Recalcular indicadores después de la retropropagación completa.

### 8.3 Dashboard muestra cambios masivos visibles

**Riesgo:** usuarios del dashboard notan que sus ofertas "cambiaron de categoría". Puede generar confusión.

**Mitigación:** nota visible en el dashboard explicando la recalibración. Si hay usuarios externos activos, aviso previo.

### 8.4 El pipeline `match_ofertas_v3` no soporta modo "re-match"

**Riesgo:** el matcher puede asumir que la oferta es nueva y no bien manejar ofertas que ya tienen estado.

**Mitigación:** Fase 2 incluye test integración específico. Si hay bugs, agregamos modo `--rematch` explícito al matcher.

### 8.5 Dispara regla donde antes no

**Riesgo:** una oferta que antes era `semantico_unico` ahora dispara una regla — qué hacer.

**Mitigación:** saltar y flaggear para revisión manual. Esas ofertas son probablemente casos donde reglas nuevas (ej. R345-R352 de SPEC A) se agregaron después del matching original y habría que reprocesar con regla aplicada. Spec aparte.

### 8.6 Cambios en score_semantico afectan el dual_coinciden de ofertas no tocadas

**Riesgo:** una oferta con `dual_coinciden` quedó marcada así porque regla y semántico apuntaban al mismo ISCO. Con nuevos embeddings, el semántico puede apuntar a otro. ¿Se invalida el "dual"?

**Mitigación:** fuera de scope. El ISCO de las dual sigue siendo correcto porque la regla aplicó. Solo que la metadata "semántico también estuvo de acuerdo" es menos sólida. Registrar como debt técnico.

---

## 9. Decisiones pendientes

1. **¿Usar `match_ofertas_v3` tal cual o escribir wrapper minimalista?**
   - **Recomendado:** wrapper. Solo necesitamos el re-matching semántico de ocupación, no toda la lógica del pipeline. Wrapper que (a) detecta regla → salta, (b) hace solo embedding + top-1 + penalizaciones básicas.
   - Alternativa: usar `match_ofertas_v3` completo con flag `--rematch-only`.

2. **¿Qué hacer con ofertas donde ahora dispararía una regla?**
   - Opción A: saltar y flaggear (recomendado).
   - Opción B: aplicar la regla, cambiar decision_metodo a `regla_prioridad`. Implica más cambio del que queremos en este spec.

3. **¿Recalibrar indicadores agregados post-spec o dejarlos con ISCOs mixtos?**
   - Recomendado: recalibrar al final. Ya hay scripts de sync que los recalculan.

4. **¿Bloquear actualizaciones del pipeline durante el rematch?**
   - Recomendado: sí, pausar scraping + pipeline durante Fase 4 Tanda 3-4. Evita condiciones de carrera.

---

## 10. Dependencias entre specs

```
SPEC E (embeddings)         ─┐
                              ├──> SPEC H (rematch ISCO) ──> SPEC G (filtrar skills_nlp)
                              │                                    │
SPEC A/C (reglas matching)  ─┘                                    │
                                                                  ├──> Retropropagación final skills
Extract_skills v2.7 (SPEC E)  ────────────────────────────────────┘
```

- SPEC H **requiere** embeddings nuevos (SPEC E promocionado — hecho).
- SPEC H **bloquea** retropropagación completa de skills (hay que tener ISCO correcto primero).
- SPEC G puede implementarse en paralelo a SPEC H Fase 1-2. Solo se combina en Fase 4.

---

## 11. Cronograma propuesto

| Día | Actividad |
|---|---|
| D1 | SPEC H Fase 1 (implementación) + Fase 2 (tests) |
| D1 | SPEC G Fase 1 (implementación `_filter_llm_skills`) en paralelo |
| D2 | SPEC H Fase 3 (análisis impacto dry-run) |
| D2 | SPEC H Fase 4 Tanda 1 (100 piloto) + revisión humana |
| D3 | SPEC H Fase 4 Tanda 2 (1K) → GO/NO-GO |
| D3 | SPEC H Fase 4 Tanda 3 (10K) background |
| D4 | SPEC H Fase 4 Tanda 4 (20K) background |
| D5 | Retropropagación final skills (SPEC E + G combinados) |
| D5 | Sync Supabase full |

Total wall-clock estimado: **5 días**. Total humano efectivo: **8-10 h** (desarrollo + revisiones).

---

## 12. Lo que este spec NO hace

- NO cambia código de matching (`match_ofertas_v3`), solo lo invoca.
- NO re-procesa NLP.
- NO modifica skills (lo hace la retropropagación final post-SPEC-G).
- NO toca reglas de matching ni diccionario argentino.
- NO re-valida ofertas con ISCO cambiado (mantiene estado).
- NO actualiza Supabase — eso es un sync posterior.

---

## 13. Preguntas para el stakeholder

1. ¿Aceptamos que el dashboard muestre ISCOs cambiados para 32K ofertas? (Respuesta anticipada: sí, es mejora sistémica.)
2. ¿Pausamos scraping durante Fase 4 Tanda 3-4?
3. ¿Cómo comunicamos el cambio a usuarios del dashboard si los hay?

---

## 14. Anexos

- Diagnóstico 200 ofertas: no persiste — ver conversación 2026-04-24 23:xx con Claude.
- Prototipo de script diagnóstico: `/tmp/diagnostico_matching.py`
- Informe factibilidad SPEC E: `2026-04-24_E_FACTIBILIDAD.md`
- Spec E draft: `2026-04-24_E_embeddings_enriquecidos.md`
- Spec G Fase 0: `2026-04-24_G_FASE0_filtro_skills_nlp.md`
