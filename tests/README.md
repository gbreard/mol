# Tests MOL - Monitor de Ofertas Laborales

## Estructura

```
tests/
├── conftest.py              # Fixtures compartidos
├── README.md                # Esta documentación
│
├── matching/                # Tests de matching ESCO
│   ├── __init__.py
│   └── test_precision.py    # Validación con gold set
│
├── nlp/                     # Tests de extracción NLP
│   ├── __init__.py
│   ├── test_extraction.py   # Tests de extracción
│   └── gold_set.json        # Gold set NLP (vacío por ahora)
│
└── integration/             # Tests end-to-end
    └── __init__.py
```

## Ejecución

### Requisitos

```bash
pip install pytest
```

### Correr todos los tests

```bash
pytest tests/ -v
```

### Correr solo matching

```bash
pytest tests/matching/ -v
```

### Correr solo NLP

```bash
pytest tests/nlp/ -v
```

### Con reporte detallado

```bash
pytest tests/ -v --tb=short
```

### Solo un test específico

```bash
pytest tests/matching/test_precision.py::TestMatchingPrecision::test_matching_precision -v
```

## Gold Sets

### Matching (database/gold_set_manual_v2.json)

Gold set de matching ESCO con ~49 casos validados manualmente.

Estructura:
```json
{
  "id_oferta": "1118026700",
  "esco_ok": true,
  "comentario": "Match correcto. Vendedor -> vendedor de piezas.",
  "tipo_error": null  // Solo si esco_ok=false
}
```

Tipos de error:
- `sector_funcion`: Match en sector/área incorrecta
- `nivel_jerarquico`: Nivel jerárquico incorrecto
- `tipo_ocupacion`: Tipo de ocupación incorrecto
- `programa_general`: Ocupación demasiado general

### NLP (tests/nlp/gold_set.json)

Gold set de extracción NLP (pendiente de crear).

Estructura propuesta:
```json
{
  "id_oferta": "1118026700",
  "expected": {
    "area_funcional": "Ventas/Comercial",
    "nivel_seniority": "senior",
    "tiene_gente_cargo": false
  }
}
```

## Agregar casos al Gold Set

### Matching

1. Editar `database/gold_set_manual_v2.json`
2. Agregar nuevo caso con estructura correcta
3. Correr `pytest tests/matching/ -v` para validar

### NLP

1. Editar `tests/nlp/gold_set.json`
2. Agregar caso con campos esperados
3. Correr `pytest tests/nlp/ -v` para validar

## Métricas

Los resultados se guardan en `metrics/gold_set_history.json`.

Campos:
- `timestamp`: Fecha/hora del test
- `precision`: Precisión en porcentaje
- `total`: Total casos evaluados
- `correct`: Casos correctos
- `errors_by_type`: Errores por categoría

## Convenciones

1. **Nombres de tests**: `test_<descripcion>_<aspecto>`
2. **Clases de test**: `Test<Componente><Aspecto>`
3. **Fixtures**: En `conftest.py` para compartir
4. **Asserts**: Un assert principal por test
5. **Prints**: OK para debugging, pero assert debe validar

## Scripts Legacy

Los siguientes scripts en `database/` son equivalentes a estos tests:

| Script Legacy                    | Test Nuevo                              |
|----------------------------------|----------------------------------------|
| test_gold_set_manual.py          | tests/matching/test_precision.py       |
| check_gold_set_precision.py      | tests/matching/test_precision.py       |
| check_gold_set_v2_precision.py   | tests/matching/test_precision.py       |
| verify_gold_set_nlp.py           | tests/nlp/test_extraction.py           |

## Troubleshooting

### Error: Gold set not found

Verificar que existe `database/gold_set_manual_v2.json`.

### Error: Database not found

Verificar que existe `database/bumeran_scraping.db`.

### Tests skipped

Algunos tests se saltan si:
- Gold set vacío
- Sin datos en BD
- Columnas faltantes

---

*Última actualización: 2025-12-09*
