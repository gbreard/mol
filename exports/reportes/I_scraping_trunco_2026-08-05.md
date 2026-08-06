# [FRENTE I — P1] La bandera del scraping: diagnóstico — 2026-08-05

## Veredicto: son DOS regresiones distintas, ambas activas HOY

**Distribución portal × mes (% descripciones <300 chars, universo completo desde marzo):**

| Portal | mar | abr | may | jun | jul | ago |
|---|---|---|---|---|---|---|
| **computrabajo** | 2% | 0% | **45%** | **100%** | **100%** | **100%** |
| **indeed** | 1% | 8% | 1% | 2% | **72%** | **100%** |
| bumeran | 1% | 1% | 1% | 1% | 0% | 0% |
| zonajobs | 1% | 1% | 1% | 1% | 1% | 1% |
| portalempleo | 41% | 35% | 50% | 42% | 35% | 0% |
| caba | 7% | 0% | 0% | 0% | 0% | 0% |

- **ComputRabajo: roto desde mediados de mayo, total desde junio.**
- **Indeed: roto desde julio, total en agosto** — regresión NUEVA, distinta.
- Bumeran/ZonaJobs sanos. **Portal Empleo NO está roto**: sus cortas son avisos
  genuinamente cortos (municipales, con metadata estructurada) — crónico estable, sin fix.

## Las 20 URLs (verificación en vivo)

- **CT (6/6 verificadas VIVAS): el aviso en el portal tiene la descripción COMPLETA**
  (7-11K chars de contenido); la BD guardó el boilerplate SEO («¿Buscas trabajo de X?
  Crea tu CV gratis…», 130-200 chars). **Preview-scrapeado confirmado.**
- **Indeed (5/5 verificadas): HTTP 403 uniforme** (página de bloqueo de 28.103 bytes,
  idéntica en todas) incluso con `curl_cffi impersonate=chrome` desde el entorno local.
  La BD guarda descripción **vacía** (0 chars). **Bloqueo Cloudflare, no truncamiento.**
- Portal Empleo (3/3): contenido real corto — genuino.

## Causa raíz (con evidencia, no especulación)

- **CT:** el portal cambió su HTML de detalle (~mayo): `div.box_detail` sigue existiendo
  pero **`p.mbB` (el selector primario, verificado 2026-03-11 en el código) ya no existe**;
  la descripción vive ahora en un `div.mb40.pb40.bb1` anidado (que el Método 2 no alcanza
  por `recursive=False`). Con los métodos 1 y 2 muertos, **el Método 3 —fallback a
  `meta description`, `computrabajo_scraper.py:376-380`— guarda el boilerplate SEO en
  silencio como si fuera dato.** Historial git: cero cambios al scraper CT en la ventana —
  la causa es 100% externa + el fallback venenoso propio.
- **Indeed:** Cloudflare endureció en julio; el bypass `impersonate='chrome131'` (commit
  `ce7e0e7b`) perdió la carrera. El fetch de detalle devuelve 403 y el scraper persiste
  descripción vacía.

## Fix recomendado

1. **CT (barato, alto impacto):**
   a. Nuevo selector primario para el contenedor actual (`div.mb40.pb40.bb1` dentro de
      `box_detail`) + Método 2 con búsqueda recursiva.
   b. **Guarda anti-veneno en el fallback**: si el texto matchea el patrón
      «Crea tu CV gratis y aplica» → guardar NULL, jamás el boilerplate. (Mismo criterio
      del issue `2026-07-25_computrabajo_descripcion_boilerplate.md`.)
2. **Indeed (incierto):** actualizar impersonation de curl_cffi (versiones chrome más
   nuevas) y probar; si Cloudflare ganó definitivamente, evaluar fuente alternativa.
   Trabajo experimental — no prometer plazo.
3. **Detección permanente:** una regla de validación post-scrape (% descripciones <300
   por portal por corrida; umbral 10% → alerta) para que la próxima regresión no tarde
   dos meses en verse.

## Plan de re-scrape (dimensión, no ejecución)

Truncas CT+Indeed desde mayo: **17.029** (CT 14.170 + Indeed 2.859). PERO el **88-91%
ya está de baja** en los portales — recuperables por re-scrape: **~1.617** (CT 1.270 +
Indeed 347). La cifra de ~7.000 candidatas del pedido sobreestima lo recuperable: los
avisos mueren más rápido que la ventana de detección. **El fix vale sobre todo hacia
adelante** (frenar el sangrado de ~2.500/mes por portal roto); hacia atrás, re-scrape
chico de ~1.6K vivas + aceptar ~15.4K como título-only permanentes.

## ⛔ Regla operativa

**La corrida semanal de NLP NO se programa hasta que el fix de CT esté aplicado** —
procesaría miles de boilerplates más. (Indeed bloquea menos: sus vacías ya no pasan el
filtro `desc>100` del selector NLP.)
