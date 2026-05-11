# Baselines canarios — post-F0 SPEC U-1 v3.1

**Fecha:** 2026-05-05 14:59:07 (timestamp del snapshot)
**Snapshots:**
- Local: `data/snapshots/pre_spec_u1_v3_20260505_145907.db.gz` (509 MB, conteos íntegros verificados)
- Supabase: `data/snapshots/pre_spec_u1_v3_supabase_20260505_145907.json.gz` (122 MB)

## Snapshots Supabase — conteos por tabla

| Tabla | Filas | Notas |
|---|---:|---|
| `ofertas_dashboard` | 52.563 | **MUCHO más que ~16K que decía CLAUDE.md** |
| `ofertas_skills` | 1.144.527 | **29K MÁS que validadas locales (1.115.010)** — confirma hipótesis de skills zombies |
| `issues` | 212.860 | Incluye automáticos (CLAUDE.md menciona 99.4% ruido) |
| `rule_candidates` | 0 | Tabla vacía |
| `validacion_humana` | — | **Tabla NO existe en Supabase** (SPEC v3.1 §3.1 listaba — corregir) |

## Baselines confirmadas (BD local)

| Canario | Baseline | Notas |
|---|---:|---|
| C-Q1: ofertas con `esco_occupation_uri = ''` | **3.762** | 3.758 dict + 4 mixtos (semantico/regla) |
| C-Q2: filas en skills con flags=0 | **1.116.011** | Total — DIAG A |
| C-Q3: URIs con drift de labels | **1.237** | C1 debe bajarlo a < 50 |
| C-Q6: ofertas validadas locales | **56.397** | Esperado en Supabase (drift +3.834 vs ofertas_dashboard) |
| C-Q7: matching_version=spec_h_rematch | **8.221** | C1 las re-matchea |

## Baselines actualizadas (drift Local↔Supabase REAL)

| Métrica | Esperado SPEC v3.1 | Real BD/Supabase | Comentario |
|---|---:|---:|---|
| ofertas_dashboard rows | "~16K" | **52.563** | SPEC desactualizado |
| diff Local−Supabase | "~40K" | **3.834** | El backlog era mucho menor de lo asumido |
| ofertas_skills rows | (no declara) | 1.144.527 | 29K más que local validadas |

→ Ajuste para canarios: C-Q5 baseline real es **3.834**, no 40K. Esto reduce el alcance del trabajo de C5 (sync masivo) substancialmente.

## Estado de canarios

| Q | Valor actual | Baseline | Alarma |
|---|---:|---:|---|
| Q1 | 3.762 | 3.762 | OK |
| Q2 | 1.116.011 | 1.116.011 | OK |
| Q3 | 1.237 | 1.237 | OK |
| Q6 | 56.397 | 56.397 | OK |
| Q7 | 8.221 | 8.221 | OK |

## Recomendación para SPEC v3.2 (no aplicada todavía)

1. Quitar `validacion_humana` de la lista de tablas en F0 (no existe).
2. Actualizar baselines C5 a drift real ~3.834 (no 40K). Esto cambia:
   - C5 sync masivo: ~3.834 ofertas (no 40K) → ~5-10 min (no 60-90 min).
   - C5 esfuerzo total: 2-4h (no 6-10h).
3. Plan operacional C5 más simple — el sync incremental probablemente cubre todo en una corrida normal.

## Restauración

Para restaurar SQLite desde snapshot:
```bash
# Verificar integridad antes de restaurar
gunzip -t data/snapshots/pre_spec_u1_v3_20260505_145907.db.gz
# Restaurar
gunzip -c data/snapshots/pre_spec_u1_v3_20260505_145907.db.gz > database/bumeran_scraping_RESTORE.db
# Validar
python3 -c "import sqlite3; c = sqlite3.connect('database/bumeran_scraping_RESTORE.db'); print(c.execute('SELECT COUNT(*) FROM ofertas_esco_matching').fetchone())"
# Reemplazar (con backup del activo)
mv database/bumeran_scraping.db database/bumeran_scraping_PRE_RESTORE.db
mv database/bumeran_scraping_RESTORE.db database/bumeran_scraping.db
```

Para restaurar Supabase desde snapshot JSON: requiere RPC custom o restore a tabla temporal + UPSERT.
