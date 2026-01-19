# Exports

Contiene archivos exportados para validacion y analisis externo.

## Contenido

- **Gold Sets en Excel** - NLP_Gold_Set_*.xlsx
- **Exports manuales** - Datos exportados para validacion humana
- **CSVs temporales** - Exports para analisis ad-hoc

## Convencion de Nombres

Los archivos se generan automaticamente con timestamp:
```
{tipo}_{fecha}_{hora}.xlsx
```

Ejemplos:
- `NLP_Gold_Set_20251230.xlsx`
- `gold_set_nlp_20251230_121356.xlsx`

## Scripts de Generacion

| Script | Proposito |
|--------|-----------|
| `scripts/export_gold_set_nlp_excel.py` | Export Gold Set NLP |
| `database/export_skills_detalle_csv.py` | Export skills detalle |

## Notas

- Los archivos Excel son para validacion humana
- NO son fuente de verdad - la BD es la fuente
- Limpiar periodicamente archivos antiguos

---

> Ultima revision: 2026-01-03
