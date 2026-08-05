# [FRENTE J] Fix scraper ComputRabajo — selector + guarda anti-boilerplate + alerta

Arregla la regresión de CT (mayo/2026): el portal sirve variantes de template y el
fallback a meta-description guardaba el SEO («Crea tu CV gratis») como dato — 14K
ofertas envenenadas may-ago. Reporte completo: `exports/reportes/J_fix_scraper_ct_2026-08-05.md`.

## Cambios

- **`computrabajo_scraper.py`**: cadena de selectores nueva — (0) **JSON-LD
  JobPosting.description** (el más estable, verificado con descripción completa en
  vivo), (1) `p.mbB` clásico, (2) div anidado recursivo (variante mayo), (3) meta SOLO
  con **guarda dura anti-boilerplate → NULL + log ruidoso**. Detección de
  redirect-a-listado. Documentado con fecha y ejemplos.
- **`sync_from_vps.py`**: `check_salud_descripciones()` — % cortas por portal por
  corrida, umbral 10% (Portal Empleo 60% propio), alerta destacada +
  `metrics/salud_scrape.json`. Probada en vivo (alertó CT e Indeed 100%).
- **Tests**: 7 casos (5 variantes + guarda + corto-legítimo), verdes; verificado además
  contra 8 páginas reales capturadas.

## Operación ejecutada (no en el diff)

Re-scrape de las 1.270 CT truncas vivas: **1.118 recuperadas (88%)** con descripción
real, en backlog de NLP; 152 muertas → boilerplate anulado (NULL). Cero errores.

## Deploy VPS (coordina Gerardo)

`scp` del scraper a `/opt/mol/01_sources/computrabajo/scrapers/` — detalle en el reporte.

## ✅ Desbloqueo

Con el veneno muerto y la alerta instalada, **la corrida semanal de NLP queda
desbloqueada** (decisión de programarla: de Gerardo; `run_con_tmpfs.sh` listo).
Indeed (Cloudflare 403) NO es de este PR — espera decisión aparte.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
