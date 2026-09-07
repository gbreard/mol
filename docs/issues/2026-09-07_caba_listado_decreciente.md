# CABA: el listado se achica y hace 5 corridas que no aporta ofertas nuevas

**Detectado:** 2026-09-07, en los chequeos de rutina.
**Estado:** abierto, **sin acción** — registro para diagnóstico futuro.
**Severidad:** baja — es el portal más chico del corpus (66 ofertas totales).

## Serie observada

`Total ofertas en listado` por corrida, del log del VPS:

| corrida | listado | nuevas insertadas |
|---|---:|---:|
| 2026-08-20 | 14 | 1 |
| 2026-08-24 | 15 | 1 |
| 2026-08-25 | 15 | 0 |
| 2026-08-27 | **8** | 0 |
| 2026-08-31 | 9 | 2 |
| 2026-09-03 | 9 | 0 |
| **2026-09-07** | **7** | 0 |

El listado bajó de 14-15 a 7-9 a fines de agosto y se quedó ahí. **Cinco de las últimas seis
corridas no aportaron ninguna oferta nueva**; la última fue el 31-08 (2 ofertas). Total
acumulado estancado en **66**.

## Qué NO es

- **No es un fallo del scraper**: corre completo, sin errores, en ~20 s. El 2026-09-07 hizo
  `Listado offset=0… → 7 ofertas encontradas (total: 7) → Total ofertas en listado: 7` y las
  7 resultaron duplicadas.
- **No es la guarda de colisiones de id** (desplegada el 02-09): la serie ya venía bajando
  desde el 27-08, y CABA usa la banda `6e9`, que no se solapa con ninguna otra.
- **No es falta de detalle**: `Fetch details: True` y las fichas se bajan bien.

## Hipótesis a verificar cuando se tome

1. **El portal efectivamente tiene menos avisos publicados.** Es un portal municipal chico; 7-15
   avisos simultáneos es plausible. Se verifica abriendo el listado a mano.
2. **La paginación quedó corta.** El scraper pagina con `offset` de a 8 y en la última corrida
   hizo un solo `offset=0`. Si el portal cambió el tamaño de página o el criterio de corte, el
   scraper podría estar viendo solo la primera pantalla. **Esta es la que conviene descartar
   primero**, porque explicaría la caída sin que el portal haya cambiado.
3. **Cambio de HTML** que rompa el conteo del listado sin romper el parseo de lo que sí ve.

## Por qué se registra y no se actúa

CABA aporta 66 ofertas de ~119.000 (0,06 % del corpus). Aun si estuviera perdiendo la mitad de
su listado, el impacto sobre cualquier indicador es despreciable. Se anota para que la serie
quede documentada y, si alguna vez se revisa el portal, no haya que reconstruirla.

Un dato relevante para cuando se mire: **el 47 % de CABA son republicaciones de avisos que ya
están en otro portal** (ver `exports/reportes/medicion_duplicacion_crossportal.md`), así que su
aporte único al corpus es todavía menor que su conteo.

## Referencias

- `01_sources/caba/scrapers/caba_scraper.py` — paginación por `offset`
- `scripts/scraping/run_caba_vps.py` — runner
- Logs: `/opt/mol/logs/scraping_2026*.log`, bloque `[4/7] CABA`
