# Run Tracking - Versionado de Corridas

## El Problema

Cuando optimizás el pipeline cambiando JSONs de config, necesitás saber:
- ¿Mejoró o empeoró la precisión?
- ¿Qué config usé en la corrida anterior?
- ¿Qué ofertas procesé con qué versión?

Sin esto, es imposible comparar antes/después de cada cambio.

## La Solución: Runs

Un **run** es una "foto" de una ejecución del pipeline que guarda:
1. **Qué ofertas** se procesaron
2. **Qué configs** se usaron (copia exacta de los JSONs)
3. **Qué métricas** resultaron

## Estructura de Archivos

```
metrics/runs/
├── run_20260113_1550.json          ← "Procesé 100 ofertas con config X"
├── run_20260113_1550_config/       ← Copia de JSONs usados
│   ├── matching_config.json
│   ├── matching_rules_business.json
│   └── sector_isco_compatibilidad.json
└── run_20260113_1550_results.json  ← "Resultado: 64% precisión"
```

## Cómo Usar

### 1. Ejecutar pipeline (crea run automáticamente)

```python
from database.match_ofertas_v3 import run_matching_pipeline

stats = run_matching_pipeline(
    offer_ids=["123", "456", ...],  # IDs a procesar
    source="gold_set_100",           # Nombre descriptivo
    description="Agregué regla R53"  # Qué cambié
)

print(stats['run_id'])  # → "run_20260113_1625"
```

### 2. Comparar con corrida anterior

```bash
# Comparar últimos 2 runs
python scripts/compare_runs.py --latest

# Output:
# Configs cambiadas:
#   - matching_rules_business: 1.1 → 1.2 (+1 regla)
# Métricas:
#   - precision: 23% → 64% (+41%)
```

### 3. Listar runs disponibles

```bash
python scripts/compare_runs.py --list
```

## Flujo de Optimización

```
1. Cambiar config/*.json
2. Ejecutar: run_matching_pipeline(offer_ids=[...])
   → Crea run automáticamente
   → Copia configs
   → Guarda run_id en cada oferta
3. Comparar: python scripts/compare_runs.py --latest
4. Si mejora → commit
   Si empeora → revertir config (tenés la copia en el run anterior)
```

## Archivos del Sistema

| Archivo | Qué hace |
|---------|----------|
| `scripts/run_tracking.py` | Crea runs, copia configs, guarda métricas |
| `scripts/compare_runs.py` | Compara dos runs, muestra diferencias |
| `metrics/runs/` | Carpeta donde se guardan todos los runs |
| Columna `run_id` en BD | Cada oferta sabe en qué run se procesó |
