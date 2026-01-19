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
