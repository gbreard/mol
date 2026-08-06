# [FRENTE J] Fix scraper ComputRabajo — 2026-08-05

Branch `fix/scraper-ct-selector`. Diagnóstico base: `I_scraping_trunco_2026-08-05.md`.

## Hallazgo adicional durante el fix (refina el diagnóstico del I)

El análisis en vivo sobre 8+ avisos de distintas categorías mostró que **CT sirve
VARIANTES de template según origen/sesión** (la misma URL devolvió `p.mbB` un día y
`div.mb40.pb40.bb1` el anterior), **403 al user-agent obviamente-bot**, y redirect a
listado para avisos caídos. El boilerplate almacenado es exactamente la meta-description
de la página de detalle («¿Buscas trabajo de {título}? Crea tu CV gratis…») — al momento
del scrape desde el VPS los métodos 1-2 no encontraban contenido y el fallback lo
guardaba. **Y la pieza clave: el detalle trae JSON-LD `JobPosting.description` con la
descripción COMPLETA** (obligatorio para SEO — el selector más estable posible, inmune a
los cambios de template).

## P1+P2 — La cadena nueva (commit `fix(scraping)`)

`_extraer_descripcion()` en `computrabajo_scraper.py`, documentada con fecha y ejemplos:

0. **JSON-LD JobPosting.description** (primario, en `@graph`) — HTML stripped.
1. `p.mbB` en `box_detail` (template clásico, sigue activo en variante A).
2. Div de texto largo en `box_detail`, **búsqueda recursiva** (la variante ~mayo anida
   la descripción donde el `recursive=False` anterior no llegaba), nodos hoja, sin ruido.
3. Meta description **SOLO con guarda dura**: patrón `buscas trabajo (de|en) … crea tu cv`
   → **NULL + log ruidoso** («descripción no extraída — selector falló»). El fallback
   sin guarda fue el veneno de may-ago.

Además: detección de redirect-a-listado (título «Empleos en …») → NULL ruidoso.
**Principio aplicado: mejor ausencia ruidosa que basura silenciosa.**

**Tests (7, verdes):** JSON-LD / mbB / div-anidado / selector-falla+meta-boilerplate→NULL /
meta-legítima-se-usa / aviso-genuinamente-corto-se-guarda / redirect→NULL.
**Verificación en vivo:** 8 páginas reales capturadas → 6 descripciones completas
(723-2.537 chars), 2 NULL correctos (redirects de avisos caídos).

## P3 — Alerta de salud post-scrape (commit `feat(scraping)`)

`check_salud_descripciones()` en `sync_from_vps.py` (el punto que ve los datos frescos
de TODOS los portales, corre local a diario): % de descripciones <300 por portal en la
ventana de 3 días; umbral 10% general, **Portal Empleo 60% propio** (crónico genuino);
mínimo 20 ofertas para señal. Log destacado + `metrics/salud_scrape.json` (última
corrida + historia de 60). **Probada en vivo: alertó CT 100% e Indeed 100%** con los
datos frescos de esta semana — la próxima regresión se ve en la corrida siguiente, no
en dos meses.

## P4 — Re-scrape acotado de las vivas

Candidatas: CT truncas desde mayo, no-baja, no-'validado' (los triggers de protección
cubren solo `validado` humano; las `validado_claude` son actualizables). Por cada
recuperada: UPDATE de descripción + DELETE de su fila `ofertas_nlp` → **re-entra al
backlog normal de NLP** (no se corre NLP en este frente).

**Resultado (corrida 2026-08-05, ~55 min, delay 2s):**
- Candidatas vivas: **1.270** (de 14.170 truncas CT — el resto ya de baja).
- **Recuperadas: 1.118 (88,0%)** — descripción real actualizada + fila NLP borrada →
  **en el backlog normal de NLP** (verificado en BD: 1.270 sin fila NLP; 1.084 con
  descripción ≥300 — la diferencia son recuperadas genuinamente cortas).
- No recuperadas: **152 (12%)** — redirect a listado (avisos caídos entre la detección
  y el re-scrape; el detector de bajas aún no los marcó). A esas 152 se les **anuló el
  boilerplate** (descripción NULL, mismo principio del fix) para que no re-entren al
  NLP como veneno.
- Errores HTTP/excepciones: **0**.
El fix probado a escala real: 88% de extracción sobre avisos vivos, 100% de los fallos
explicados (avisos muertos), cero basura nueva almacenada.

## FOLLOW-UP (2026-08-06) — Limpieza retroactiva del boilerplate histórico

Con el grifo cerrado, se vació la pileta (`scripts/db/limpieza_boilerplate_ct.py`,
ejecutado vía la ceremonia tmpfs del frente F, con dry-run previo):

- **Detección con EL MISMO regex de la guarda** (fuente única:
  `ComputRabajoScraper.BOILERPLATE_RE`, importado — test que verifica la identidad):
  **8.835 ofertas con boilerplate vivo** (no ~12.900: el estimado contaba cortas
  no-boilerplate). Por mes: may 571 / jun 2.603 / jul 4.864 / ago 797. Todas CT.
- **Guarda del trabajo humano: 0 validadas por humano en la población** — nada
  intocable, nada excluido.
- **Anuladas: 8.835** descripciones → NULL, con registro trazable y reversible en la
  tabla nueva `descripcion_anulada_log` (id, texto original, motivo
  `boilerplate_seo_ct`, timestamp). Con NULL no re-entran al backlog.
- **Segunda generación invalidada** (procesadas por NLP sobre el boilerplate):
  **5.497 filas NLP + 5.491 matching + 31.526 skills** borradas (DELETE — el
  mecanismo que el pipeline regenera; sus matching eran `validado_claude`, no humano).
- **Verificación post: 0 ofertas con el patrón vivo.** Spot-check de 5 con
  antes/después OK. La alerta `check_salud_descripciones` seguirá roja para CT en la
  ventana fresca **y eso es correcto**: ahora mide NULLs honestos; se pondrá verde
  cuando el fix llegue al VPS y entren scrapes limpios.
- Nota: las 152 del re-scrape de ayer se anularon antes de existir el log — quedaron
  sin texto original registrado (solo esta mención). Backup íntegro pre-limpieza:
  `database/bumeran_scraping.db.bak_tmpfs` (borrable tras validar el PR).
- **Cierre dashboard (2026-08-06, autorizado por Gerardo):** delete dirigido ejecutado
  en Supabase — presencia contada ANTES: **5.481** en `ofertas_dashboard` (calzó con
  las 5.481 `validado_claude` de la detección) + **31.505** filas en `ofertas_skills`.
  **Borradas 5.481 + 31.505; verificación post: 0 restantes.** Hard DELETE por ids
  del log (el schema no tiene soft-delete; el propio sync usa DELETE+INSERT). El
  dashboard ya no muestra ninguna oferta boilerplate.

## Despliegue al VPS (coordina Gerardo)

El fix vive en `01_sources/computrabajo/scrapers/computrabajo_scraper.py` (archivo
compartido repo↔VPS). Paso exacto:
```bash
scp 01_sources/computrabajo/scrapers/computrabajo_scraper.py \
    root@187.124.150.28:/opt/mol/01_sources/computrabajo/scrapers/
# (la proxima corrida de cron Lun/Jue lo usa; no hay servicio que reiniciar)
```
Nota: si el VPS sigue recibiendo variantes degradadas/walls de CT, el método 0 (JSON-LD)
tiene la mejor chance; si aun así falla, la guarda garantiza NULL ruidoso (visible en la
alerta P3 de la corrida siguiente) — nunca más boilerplate como dato.

## ⛔→✅ Corrida semanal de NLP: DESBLOQUEADA

Con el veneno muerto (NULL en vez de boilerplate) y la alerta instalada, **la condición
del frente I queda cumplida: la corrida semanal de NLP vuelve a la mesa de Gerardo** —
con `scripts/ops/run_con_tmpfs.sh` (frente F) listo como camino de I/O. Indeed sigue
roto (Cloudflare) y NO es de este frente; sus ofertas no envenenan (vacías → no pasan
el filtro del selector NLP).
