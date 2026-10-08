# Monitor: falta alerta "corrió pero extrajo 0"

**Fecha:** 2026-10-08 · **Estado:** abierto · **Prioridad:** media · **No ahora**

## Problema
El monitor de scraping detecta portales caídos por **antigüedad de datos**
("ofertas_dashboard / portal sin actualizar hace N horas", umbral por cadencia).
Eso llega **tarde** cuando el cron corre limpio pero no extrae nada:

- **Portal Empleo:** 24 días en cero (cron 06:15 corría todos los días, scraper
  apuntaba a la estructura vieja → 0 ofertas). El sitio migró ~09-15.
- **Indeed:** 21 días en cero (cron cada 3h corría, preflight GO, pero el panel
  cambió de DOM → 466 tarjetas, 0 descripciones, 0 insertadas).

En ambos el cron terminaba con exit 0 y "sin errores". El monitor solo los agarró
cuando la antigüedad cruzó el umbral de horas — días después de que la extracción
ya estaba rota.

## Señal que falta
Distinguir **"no corrió"** de **"corrió y extrajo 0"**. Un cron que ejecuta
exitosamente pero inserta ~0 ofertas durante K corridas consecutivas es un fallo
de extracción (selector/DOM/ruta cambiados), y debería alertar **de inmediato**,
no tras N horas de antigüedad.

## Propuesta (no implementar ahora)
- Registrar por corrida: portal, timestamp, `n_listado`/`tarjetas`, `insertadas`,
  `con_descripcion` (ya existe parte en `corridas_scraping` para PE; Indeed lo
  tiene en el resumen JSON del log). Unificar a una tabla/consulta común.
- Regla de alerta: si un portal tuvo ≥K corridas (p.ej. 2-3) con
  `ejecutó=sí ∧ insertadas≈0` (o `tarjetas>0 ∧ con_descripcion=0`, el caso Indeed)
  → alerta "extracción rota" en el panel, independiente del umbral de antigüedad.
- El caso Indeed (`tarjetas>0 ∧ con_descripcion=0`) es especialmente diagnóstico:
  distingue "bloqueado/sin listado" de "listó pero no pudo extraer detalle".

## Contexto
Detectado en el relevamiento de scraping 2026-10-07 y los fixes de PE
(`2026-...portalempleo`) e Indeed (sonda+advance, `fix/indeed-run-vacio`). El fix
del advance de Indeed ya mitiga en parte (no auto-oculta el fallo marchando el
offset), pero la alerta proactiva del monitor sigue faltando como señal general.
