# Metrics

Contiene metricas de experimentos y tracking de precision del sistema MOL.

## Archivos

| Archivo | Proposito |
|---------|-----------|
| `experiments.json` | Tracking de experimentos NLP/Matching |
| `gold_set_history.json` | Historial de precision Gold Set |
| `timing_logs/` | Metricas de tiempo de ejecucion |

## gold_set_history.json

Registra la evolucion de la precision:
```json
{
  "2025-12-14": {
    "nlp_precision": 96,
    "matching_precision": 100,
    "gold_set_size": 49
  }
}
```

## experiments.json

Documenta experimentos realizados:
```json
{
  "experiment_id": "exp_001",
  "date": "2025-12-10",
  "description": "Test BGE-M3 vs multilingual-e5",
  "results": {...}
}
```

## Uso

Estos archivos se actualizan automaticamente por los scripts de test:
- `database/test_gold_set_v211.py`
- `tests/nlp/test_extraction.py`

---

> Ultima revision: 2026-01-03
