# Issue: migración de BD + embeddings a filesystem Linux nativo

**Fecha de observación:** 2026-05-12
**Origen:** Fase 3a falló por I/O lento en 9p (WSL ↔ Windows)

## Problema

El sistema actual corre desde `/mnt/d/OEDE/Webscrapping/` que es Windows filesystem
accedido via protocolo 9p desde WSL2 Linux. Archivos críticos que el pipeline lee
al inicio:

| Archivo | Tamaño |
|---------|--------|
| `database/bumeran_scraping.db` | 3.1 GB |
| `database/embeddings/enriched/esco_skills_embeddings_full.npy` | 55.6 MB |
| `database/embeddings/enriched/esco_occupations_embeddings.npy` | 11.8 MB |
| `database/embeddings/esco_skill_to_occupations.json` | 31.1 MB |
| `database/embeddings/esco_occupation_skills.json` | 28.9 MB |
| `database/embeddings/esco_skills_metadata_full.json` | 17.4 MB |
| `database/embeddings/esco_skills_full.json` | 11.4 MB |

Cuando el page cache de Linux está frío (post-otros I/O intensivos o post-restart),
acceso via 9p es 1-2 órdenes de magnitud más lento que filesystem nativo.

## Incidente concreto

Fase 3a (1.488 ofertas matching solo) lanzada 12/05 13:26, quedó colgada **18+ min**
en estado `D` (uninterruptible sleep). Stack del proceso: `p9_client_rpc → pread64`
— SQLite leyendo páginas de la BD 3.1GB. Page cache estaba frío por:

1. Backfill A1.3 previo (~450MB I/O HTTP responses)
2. Canary unificado (NLP+matching 100 ofertas)
3. Posiblemente query de otro proyecto sobre la misma máquina (competencia por 9p)

**Resolución del incidente:** kill -9 + preload manual de archivos via `cat`
(~6s para queries que tocan tablas críticas + 0s adicional para embeddings,
porque el proceso muerto ya los había cargado al cache antes de morir).

Una vez con cache caliente, el pipeline arrancó normalmente.

## Solución requerida

Migrar a Linux filesystem nativo (`~/` o `/home/...`):

- BD SQLite (`bumeran_scraping.db`)
- Embeddings ESCO (`.npy` + JSONs de soporte)
- Modelos locales si están en `/mnt/d/`

Beneficios:
- Acceso nativo, sin 9p
- Page cache estable, no se evicta tan rápido
- No conflicto con otros proyectos del mismo Windows path
- I/O órdenes de magnitud más rápido

## Implicaciones operativas

- Cron `auto_sync.sh` debe actualizar paths.
- Scripts del pipeline (`run_validated_pipeline.py`, `match_ofertas_v3.py`, etc.)
  deben actualizar paths o leer desde env var.
- VPS sync target (`sync_from_vps.py`) escribe a la nueva BD ubicación.
- Backup actual de `/mnt/d/` queda como cold storage / snapshot.

## Esfuerzo estimado

4-6h:
- Migración física de archivos (1h)
- Update de paths en código (~2h, idealmente via env var `MOL_DATA_DIR`)
- Tests de funcionamiento (~1-2h)
- Validación de que cron y poller siguen funcionando (~1h)

## Workaround actual

Pre-cachear archivos via `cat *.npy *.json > /dev/null` + queries SQL ligeras
antes de cualquier batch grande. Esto se puede integrar en el wrapper
`run_batch_with_lock.py` como step 0 antes del lock.

Mientras el cache se mantenga caliente (cron horario auto_sync, accesos
periódicos), el pipeline funciona normalmente. El problema vuelve si:
- WSL se reinicia
- Otro proceso heavy I/O evicta el cache
- Largo periodo sin actividad

## Riesgos de la migración

- Pérdida de visibilidad desde Windows (Explorer no llega a `~/`).
- Backups deben configurarse en Linux también.
- Si compartís el repo con otros, paths se vuelven dependientes del usuario.

## Prioridad

Media-alta. No bloquea operación inmediata si el preload manual sigue funcionando,
pero cada vez que el page cache se enfría va a ser un incidente. SPEC U-3 o ventana
de mantenimiento dedicada.
