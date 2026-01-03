# STATUS: RESERVADO PARA EXPANSION

> **Estado actual**: No en uso
> **Razon**: Solo hay 1 portal activo (Bumeran)
> **Cuando se usara**: Cuando se active ZonaJobs u otro portal

---

## Que contiene

Scripts para consolidar datos de multiples portales en schema unificado:
- `consolidar_fuentes.py` - Orquestador principal
- `normalizar_campos.py` - Normalizadores por fuente
- `deduplicacion.py` - Deteccion de duplicados
- `validacion.py` - Validacion de schema

---

## Pipeline actual (sin consolidacion)

```
run_scheduler.py --> 01_sources/bumeran/ --> database/bumeran_scraping.db
```

## Pipeline futuro (con consolidacion)

```
01_sources/* (5 portales)
    |
    v
02_consolidation/ (merge multi-fuente)
    |
    v
database/
```

---

## Cuando se reactivara

Este codigo sera necesario cuando:
1. Se active ZonaJobs como segundo portal
2. Se agregue Computrabajo, LinkedIn o Indeed
3. Se necesite deduplicacion cross-portal

---

> Ultima revision: 2026-01-03
