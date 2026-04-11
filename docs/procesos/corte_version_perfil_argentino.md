# Proceso: Corte de version del Perfil Argentino

## Cuando hacerlo

- Cuando aparece la alerta "X skills aprobadas desde el ultimo corte" en `/admin/metricas`
- Cuando se aprobaron >= 10 emergentes nuevas
- Antes de un fine-tuning de BGE-M3

## Pasos

### 1. Verificar estado actual

Ir a `/admin/procesamiento/perfil-argentino`. Revisar:
- Cantidad de skills aprobadas desde ultimo corte
- Emergentes pendientes de revision (si hay, revisar primero)

### 2. Crear nueva version

1. Clickear "Crear nueva version"
2. Escribir nota describiendo los cambios (ej: "v1.3: +12 skills aprobadas, 3 ocupaciones nuevas")
3. Confirmar

Esto congela un snapshot JSONB de `esco_argentino` en `perfil_argentino_versiones`.

### 3. Regenerar embeddings (si hay skills nuevas con URI)

Correr localmente:

```bash
python scripts/db/regenerate_all_embeddings.py --incremental
```

Esto regenera solo los corpus afectados y verifica que el Gold Set no baje.

### 4. Verificar Gold Set

```bash
OLLAMA_HOST=172.17.0.1 python tests/matching/test_gold_set_manual.py
```

Debe mantener >= 76.6% (baseline - 5%). Si baja, investigar que skill nueva causo la regresion.

### 5. Sincronizar Gold Set local

```bash
python scripts/sync_gold_set.py
```

### 6. Commitear

```bash
git add database/embeddings/corpus_manifest.json
git add database/gold_set_manual_v2.json
git commit -m "chore: corte version perfil argentino vX.Y"
```

## Rollback

Si algo sale mal despues del corte:

1. Ir a `/admin/procesamiento/perfil-argentino`
2. En historial de versiones, click "Rollback" en la version anterior
3. Re-regenerar embeddings: `python scripts/db/regenerate_all_embeddings.py --incremental`

## Frecuencia sugerida

- Minimo: cada 10 emergentes aprobadas (alerta automatica)
- Maximo: 1 vez por semana
- Obligatorio antes de fine-tuning
