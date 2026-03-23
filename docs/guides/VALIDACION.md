# Sistema de Tracking y Validación (v2.0)

Sistema centralizado en BD para:
- Registrar cada corrida del pipeline (runs)
- Comparar antes/después de cambios
- Proteger ofertas validadas de reprocesamiento
- Auditar todos los cambios de estado

## Tablas BD

| Tabla | Propósito |
|-------|-----------|
| `pipeline_runs` | Registro de corridas (configs, métricas, ofertas) |
| `validacion_historial` | Auditoría de cambios de estado |
| `ofertas_esco_matching` | +4 columnas: estado_validacion, validado_timestamp, validado_por, notas_revision |

## Estados de Validación

| Estado | Significado | Reprocesable? |
|--------|-------------|---------------|
| `pendiente` | Sin revisar | Si |
| `en_revision` | Siendo optimizada | Si |
| `validado` | Aprobada para producción | **NO** |
| `rechazado` | Con errores, necesita fix | Si |
| `descartado` | Oferta inválida/spam | **NO** |

## Flujo de Trabajo

```
1. PROCESAR
   run_matching_pipeline(ids, source="gold_set")
   → Crea registro en pipeline_runs
   → estado_validacion = 'pendiente'

2. REVISAR
   export_validation_excel.py --ids ...
   → Revisar Excel, detectar errores

3. CORREGIR
   → Modificar config/*.json
   → Re-procesar (nuevo run)
   → compare_runs.py --latest

4. VALIDAR (cuando OK)
   validar_ofertas.py --ids ... --estado validado
   → Ofertas quedan PROTEGIDAS

5. DASHBOARD
   → Solo exporta estado='validado'
```

## Protección de Datos

El pipeline verifica antes de procesar:
- Si algún ID tiene `estado_validacion = 'validado'` → ERROR
- Usar `force=True` para forzar (no recomendado)

```python
# Esto falla si hay IDs validados
run_matching_pipeline(offer_ids=[...])

# Esto fuerza el reprocesamiento (cuidado!)
run_matching_pipeline(offer_ids=[...], force=True)
```

## Scripts del Sistema

| Script | Función |
|--------|---------|
| `scripts/run_tracking.py` | Crear/gestionar runs |
| `scripts/compare_runs.py` | Comparar dos runs |
| `scripts/validar_ofertas.py` | Cambiar estado de ofertas |
| `scripts/review_batch.py` | Triage y diagnóstico de ofertas |
| `scripts/apply_config_changes.py` | Aplicar cambios de config recomendados |

## Queries Útiles

```sql
-- Ver ofertas por estado
SELECT estado_validacion, COUNT(*) FROM ofertas_esco_matching GROUP BY estado_validacion;

-- Ver historial de una oferta
SELECT * FROM validacion_historial WHERE id_oferta = '123' ORDER BY timestamp;

-- Ver runs y sus métricas
SELECT run_id, timestamp, metricas_precision, ofertas_count FROM pipeline_runs ORDER BY timestamp DESC;

-- Ofertas listas para dashboard
SELECT * FROM ofertas_esco_matching WHERE estado_validacion = 'validado';
```

## Proceso de Revisión Claude + Humano

Proceso de revisión multi-capa para optimizar el pipeline.

### Arquitectura de Capas

```
CAPA 1: TRIAGE (Claude)
   Input: titulo + descripcion + ISCO + label
   Output: [OK] Correcto | [??] Sospechoso | [XX] Incorrecto

CAPA 2: DIAGNOSTICO (Claude - solo para [??] y [XX])
   Output: Punto de falla identificado
   - error_limpieza, error_nlp_area, error_nlp_seniority
   - error_nlp_skills, error_matching, falta_regla

CAPA 3: RECOMENDACION (Claude)
   Output: Config específico a modificar + cambio sugerido

CAPA 4: VALIDACION HUMANA
   Output: Aprobación / Corrección / Rechazo
```

### Comandos de Revisión

```bash
# Ver ofertas en revisión
python scripts/review_batch.py --list

# Ver detalle de una oferta
python scripts/review_batch.py --detail 2171813

# Evaluar oferta
python scripts/review_batch.py --evaluate 2171813 correcto
python scripts/review_batch.py --evaluate 2171813 incorrecto --diagnostico error_matching

# Aplicar cambios de config
python scripts/apply_config_changes.py --input recommendations.json --dry-run
python scripts/apply_config_changes.py --rollback
```

### Mapeo Error -> Config

| Tipo de Error | Config a Editar |
|---------------|-----------------|
| error_limpieza | `config/nlp_titulo_limpieza.json` |
| error_nlp_area | `config/nlp_inference_rules.json` |
| error_nlp_seniority | `config/nlp_inference_rules.json` |
| error_nlp_skills | `config/skills_database.json` |
| error_matching | `config/matching_rules_business.json` |
| falta_regla | `config/matching_rules_business.json` |

---

## Sistema de Validación Humana (UI Dashboard)

La validación humana se realiza desde el panel `/admin/validacion` del dashboard, con una interfaz split-view de 3 columnas diseñada para revisión eficiente.

### Layout

El panel de validación usa un layout de 3 columnas:
- **Columna izquierda:** Lista de ofertas pendientes de validación (filtrable por estado, portal, fecha)
- **Columna central:** Detalle completo de la oferta seleccionada (datos NLP, skills, matching, metadata)
- **Columna derecha:** Panel de acciones (estado, wizard de corrección, historial)

### Estados de Validación Humana

| Estado | Tecla | Significado |
|--------|-------|-------------|
| **OK** | `Alt+1` | La oferta está correctamente clasificada, pasa a producción |
| **Error** | `Alt+2` | Hay errores en la clasificación, requiere corrección |
| **Revisar** | `Alt+3` | Caso dudoso, necesita segunda opinión o más contexto |
| **Basura** | `Alt+4` | Oferta inválida, spam, duplicada o sin información útil |

### Wizard de Corrección

Al marcar una oferta como **Error** o **Revisar**, se abre un wizard de corrección con 3 tabs:

| Tab | Campos editables |
|-----|-----------------|
| **NLP** | Título limpio, ubicación, seniority, área funcional, modalidad, jornada |
| **Tareas/Skills** | Tareas extraídas, skills detectadas, skills faltantes |
| **Ocupación** | ISCO asignado, ESCO label, justificación del cambio |

El wizard permite corregir los campos que están mal y registrar la justificación humana del error.

### Comportamiento al marcar Error/Revisar

Cuando el validador marca una oferta como **Error** o **Revisar**:
1. Se guarda el estado y las correcciones en `ofertas_dashboard`
2. Se **auto-crea un issue** en la tabla `issues` de Supabase con los datos de la corrección
3. El issue queda vinculado a la oferta (`id_oferta`) y contiene `valor_actual` / `valor_esperado`

### Columnas en `ofertas_dashboard`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `validacion_humana` | text | Estado: `ok`, `error`, `revisar`, `basura` |
| `validacion_humana_at` | timestamptz | Timestamp de la última validación |
| `validacion_humana_por` | text | Identificador del validador |
| `validacion_correcciones` | jsonb | Correcciones aplicadas (campos originales y corregidos) |

### RPC de Supabase

La validación se persiste mediante la función RPC `guardar_validacion_humana` (definida en migration 016), que:
- Actualiza las 4 columnas de validación humana en `ofertas_dashboard`
- Crea el issue asociado en la tabla `issues` (si el estado es `error` o `revisar`)
- Registra el historial del cambio
- Retorna confirmación con el ID del issue creado (si aplica)

### Keyboard Shortcuts

| Atajo | Acción |
|-------|--------|
| `Alt+1` | Marcar como OK |
| `Alt+2` | Marcar como Error (abre wizard) |
| `Alt+3` | Marcar como Revisar (abre wizard) |
| `Alt+4` | Marcar como Basura |
| `Alt+N` | Siguiente oferta |
| `Alt+P` | Oferta anterior |

---

## Issues → Training Pairs → Fine-Tuning

Cada corrección humana alimenta un pipeline de mejora continua que va desde el issue reportado hasta datos de entrenamiento para fine-tuning del modelo.

### Flujo Completo

```
Corrección humana (UI /admin/validacion)
    → Auto-crea issue en Supabase (tabla `issues`, estado: pendiente)
        → Claude/dev resuelve el issue (modifica configs, reprocesa)
            → Issue pasa a `resuelto` con solucion_aplicada
                → sync_learnings.py se ejecuta
                    → generate_training_pairs.py (auto-trigger)
                        → config/training_pairs.json (dataset acumulado)
```

### Estado del Dataset

- **602+ pares de entrenamiento** acumulados
- **103 ISCOs distintos** representados
- **9 de 10 grupos mayores** ISCO cubiertos
- Dataset crece automáticamente con cada issue resuelto

### 3 Enfoques de Fine-Tuning Soportados

| Enfoque | Datos que usa | Para qué |
|---------|---------------|----------|
| **Supervised** | input → clasificacion_correcta | Entrenamiento directo: dado un título/descripción, predecir ISCO correcto |
| **DPO/RLHF** | correcto=chosen, incorrecto=rejected | Preferencia de pares: el modelo aprende qué clasificación es mejor |
| **Chain-of-Thought** | input + justificacion_humana → correcta | Razonamiento paso a paso: el modelo aprende a explicar por qué |

### Auto-ejecución

`generate_training_pairs.py` se ejecuta automáticamente como parte de `sync_learnings.py`. Cada vez que se resuelve un issue y se hace sync, el dataset se actualiza sin intervención manual.

```bash
# Ejecución automática (dentro de sync_learnings.py)
python scripts/sync_learnings.py

# Ejecución manual
python scripts/exports/generate_training_pairs.py

# Ver estadísticas del dataset
python scripts/exports/generate_training_pairs.py --stats
```

### Visibilidad en Dashboard

El estado de readiness para fine-tuning es visible en `/admin/procesamiento/fine-tuning`, donde se muestran:
- Cantidad de pares acumulados y distribución por ISCO
- Cobertura de grupos mayores
- Calidad del dataset (pares con justificación humana vs automática)
- Indicador de readiness para cada enfoque (supervised, DPO, CoT)

---

## Validación en la Fábrica de Dos Líneas

La validación humana tiene un rol dual en el sistema, alimentando simultáneamente dos líneas de producción independientes.

### Línea 1: Fabricación (oferta → dashboard)

La validación determina qué ofertas llegan al dashboard de usuarios finales:

```
Oferta procesada (NLP + Matching)
    → Validación humana: OK
        → estado_validacion = 'validado'
            → sync_to_supabase.py la incluye
                → Visible en dashboard público
```

Las ofertas marcadas como **OK** pasan a producción. Las marcadas como **Basura** se descartan permanentemente. Las ofertas en **Error** o **Revisar** quedan bloqueadas hasta que se resuelvan.

### Línea 2: Mejora (corrección → modelo mejor)

Cada corrección humana alimenta el ciclo de mejora del modelo:

```
Oferta procesada (NLP + Matching)
    → Validación humana: Error (con correcciones en wizard)
        → Auto-crea issue en Supabase
            → Issue resuelto (regla nueva en config/*.json)
                → generate_training_pairs.py
                    → training_pairs.json (dataset crece)
                        → Fine-tuning futuro (modelo más preciso)
```

### Impacto Dual

Cada sesión de validación humana produce **dos outputs simultáneos**:

| Output | Línea | Efecto inmediato | Efecto a largo plazo |
|--------|-------|------------------|----------------------|
| Ofertas marcadas OK | Fabricación | Aparecen en dashboard | Más datos validados para métricas |
| Correcciones de errores | Mejora | Issue creado, regla agregada | Training pair para fine-tuning |

Esto significa que el trabajo del validador humano nunca se desperdicia: incluso cuando encuentra errores, esa corrección mejora el sistema para el futuro.
