# Archivos Deprecados - MOL

> **ADVERTENCIA:** Los archivos en este directorio NO deben usarse.
> Estan aqui solo como referencia historica.

---

## Estructura del Archive

```
archive_old_versions/
├── DEPRECATED.md              # Este archivo
├── process_nlp_from_db_v4.py  # NLP Pipeline v4 (obsoleto)
├── process_nlp_from_db_v5.py  # NLP Pipeline v5 (obsoleto)
│
├── nlp_pipeline/              # NLP Pipelines v6-v9
│   └── process_nlp_from_db_v7.py  # Archivado 2025-12-10
│
├── process_nlp_old/
│   └── process_nlp_from_db_v6.py  # NLP v6 (historico)
│
├── prompts/                   # Prompts de extraccion v8-v9
│   └── extraction_prompt_v8.py    # Archivado 2025-12-10
│
├── matching_rules_old/        # Reglas de matching anteriores
│   ├── matching_rules_v81.py      # ESCO matching v8.1
│   └── matching_rules_v82.py      # ESCO matching v8.2
│
├── evaluadores_old/           # Scripts de evaluacion obsoletos
│   ├── evaluar_matching_esco.py
│   ├── evaluar_matching_esco_v2.py
│   └── match_ofertas_to_esco.py
│
└── fix_historical/            # Scripts de fix puntuales (ya aplicados)
    ├── fix_17_rechazados.py
    ├── fix_all_unicode.py
    ├── fix_encoding_db.py
    ├── fix_isco_codes.py
    ├── fix_repositor.py
    ├── fix_repositor_v2.py
    └── fix_unicode_chars.py
```

---

## Versiones Activas (USAR ESTAS)

| Componente | Archivo ACTIVO | Version |
|------------|----------------|---------|
| **NLP Pipeline** | `database/process_nlp_from_db_v10.py` | v10.0 |
| **NLP Prompt** | `02.5_nlp_extraction/prompts/extraction_prompt_v10.py` | v10.0 |
| **Matching Rules** | `database/matching_rules_v83.py` | v8.3 |
| **Matching Algorithm** | `database/match_ofertas_multicriteria.py` | v8.1 |
| **Normalizador** | `database/normalize_nlp_values.py` | v1.0 |

---

## Por Que Fueron Deprecados

### NLP Pipeline (v4-v9)
- **v4-v6:** Schema NLP antiguo (menos de 50 columnas)
- **v7-v9:** Schema intermedio, reemplazado por v10 con 153 columnas (NLP Schema v5)
- **v10:** Version actual con soporte completo para skills ESCO, booleanos normalizados, campos geograficos expandidos

### Prompts (v8-v9)
- **v8:** Prompt basico sin normalizacion de valores
- **v9:** Prompt intermedio
- **v10:** Prompt actual con vocabulario controlado y normalizacion automatica

### Matching Rules (v81-v82)
- **v81:** Primera version multicriteria
- **v82:** Mejoras en sector_funcion
- **v83:** Version actual con cascada de matching mejorada

### Evaluadores
- Reemplazados por `test_gold_set_manual.py` que usa el Gold Set oficial

### Fix Scripts
- Scripts puntuales para corregir problemas de datos ya aplicados
- No deben ejecutarse nuevamente

---

## Historial de Archivado

| Fecha | Archivo | Razon |
|-------|---------|-------|
| 2025-12-10 | process_nlp_from_db_v7.py | Reemplazado por v10 |
| 2025-12-10 | process_nlp_from_db_v8.py | Reemplazado por v10 |
| 2025-12-10 | extraction_prompt_v8.py | Reemplazado por v10 |
| 2025-12-10 | extraction_prompt_v9.py | Reemplazado por v10 |
| 2025-12-08 | matching_rules_v81.py | Reemplazado por v83 |
| 2025-12-08 | matching_rules_v82.py | Reemplazado por v83 |
| 2025-12-02 | process_nlp_from_db_v6.py | Schema obsoleto |
| 2025-12-02 | evaluadores varios | Reemplazados por Gold Set |
| 2025-11-XX | fix_*.py | Scripts de migracion ya aplicados |

---

## Scripts Experimentales (PENDIENTES DE ARCHIVAR)

Los siguientes scripts en `database/` son experimentales y usan versiones deprecadas.
NO deben ejecutarse en produccion:

```
# Scripts v81 (usan matching_rules_v81.py)
- apply_v81_rules_gold19.py
- simulate_v81_gold19.py
- experiment_nlp_v81.py
- check_v81_*.py
- match_v81_*.py
- compare_v80_v81.py
- debug_v81_join.py
- insert_v81_records.py
- rerun_matching_v81.py

# Scripts v82 (usan matching_rules_v82.py)
- verify_v82_confirmados.py
- apply_v82_rules_*.py
- export_batch_v82_csv.py

# Tests con prompts deprecados
- test_nlp_v8_regression.py (usa extraction_prompt_v8)
```

**Accion recomendada:** Mover estos scripts a `archive_old_versions/experiments/`
cuando se confirme que no se necesitan mas.

---

## Importante

1. **NO modificar** archivos en este directorio
2. **NO importar** modulos desde aqui
3. Si necesitas funcionalidad similar, usa las versiones activas
4. Para referencia historica, los archivos estan disponibles en git history

---

> Ultima actualizacion: 2025-12-10
