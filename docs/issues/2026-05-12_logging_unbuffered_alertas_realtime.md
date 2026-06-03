# Issue: procesos largos sin logging unbuffered ni alertas en tiempo real

**Fecha de observación:** 2026-05-12
**Origen:** A1.3 backfill CT (3.019 ofertas, ~1h50m)

## Problema

Durante el backfill, 285 ofertas (9.4%) fallaron por rate-limit de CT
después de ~2.200 requests sostenidos. El threshold de PAUSAR (>5% errores)
nunca se activó porque:

1. stdout estaba bufferizado (Python sin -u)
2. Los wakeups veían log = 0 bytes
3. Se usó throughput como proxy
4. Throughput se mantuvo estable porque cada fallo cuenta como tiempo
   (delay + timeout), no como ausencia de actividad

Resultado: 30 minutos de fallos acumulados sin detección.

## Patrón sistémico

Es la versión micro del mismo patrón observado en:
- Bug recurrente CT (11 días sin detección porque no había alerta)
- Bugs silenciosos del scraper VPS
- Validaciones humanas que no llegan al matcher

Patrón común: **procesos críticos sin observabilidad en tiempo real.**

## Solución requerida (para SPEC W o U-3)

1. Todo proceso de batch que tarde >15 min debe correr con `python3 -u`
   o equivalente (logging unbuffered).
2. Logs deben rotarse a archivo con timestamps + nivel de severidad.
3. Métricas críticas (tasa de error, throughput, progreso) deben
   exportarse a un endpoint consultable en tiempo real, no solo
   visibles en logs.
4. Thresholds de PAUSAR deben verificarse contra métricas reales,
   no proxies.

## Aplicación inmediata

Mientras no se diseñe la solución general, todo script de batch nuevo
o modificado debe incluir `-u` en su invocación y escribir log a archivo
con flushing explícito cada N operaciones.

## Esfuerzo estimado para solución general

4-8h para infraestructura de observabilidad básica.
