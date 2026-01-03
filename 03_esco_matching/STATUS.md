# STATUS: CODIGO LEGACY - EXPERIMENTAL

> **Estado actual**: No en uso
> **Razon**: El matching evoluciono a database/match_ofertas_v2.py
> **Codigo actual**: database/match_ofertas_v2.py (BGE-M3, 100% gold set)

---

## Que contiene

30+ scripts experimentales de matching que fueron refinados y movidos a database/:
- `integracion_esco_semantica.py` - Matching semantico (experimental)
- `esco_semantic_matcher.py` - Embeddings (experimental)
- `esco_hybrid_matcher.py` - Metodo hibrido (experimental)
- Scripts de analisis y debugging

---

## NO usar directamente

El matching actual esta en:
- `database/match_ofertas_v2.py` (v2.1.1 BGE-M3)
- `config/matching_config.json`
- `config/area_funcional_esco_map.json`
- `config/nivel_seniority_esco_map.json`

**Precision Gold Set**: 100% (49/49 casos)

---

## Historia

Este directorio contiene iteraciones experimentales del matching ESCO.
El codigo fue refinado y consolidado en database/match_ofertas_v2.py
que usa:
- BGE-M3 embeddings
- Filtros ISCO contextuales
- Configuracion externalizada en JSON

---

> Ultima revision: 2026-01-03
