# Indeed headed: el panel no entrega descripción durante las primeras ~3 h de sesión

**Detectado:** 2026-09-04, al diagnosticar la caída de rendimiento del 03-09.
**Estado:** abierto — instrumentación desplegada, esperando la primera corrida con preflight GO.
**Severidad:** alta para el canal Indeed — se pierde ~89 % de las fichas de cada corrida.

## Qué pasa

La corrida del 2026-09-03 recorrió 516 tarjetas y solo **56 trajeron descripción (10,9 %)**. Las
otras 460 quedaron "mudas": el click funcionó, no hubo login gate, pero ningún selector de
`DESC_SELECTORS` encontró texto en los 8 s de `desc_timeout`. **Las mudas se descartan**
(`# sin descripcion = muda -> se descarta`), así que esas 460 ofertas no llegaron a la BD.

El gate del 2026-09-01 sobre el mismo motor había medido **481/491 = 98 %**.

## El perfil temporal descarta la hipótesis obvia

Reconstruido desde los timestamps del log (ficha OK ≈ 5,5 s = `detail_delay` 4 s + ~1,5 s de
panel; ficha muda ≈ 12 s = 4 s + los 8 s de timeout agotados):

| quintil | keywords | fichas | con descripción |
|---|---|---|---|
| 1 | 1-17 | 160 | **0 %** |
| 2 | 18-34 | 116 | **0 %** |
| 3 | 35-51 | 104 | **0 %** |
| 4 | 52-70 | 83 | 57,8 % |
| 5 | 71-89 | 95 | **88,4 %** |

**La sesión se calienta; no se degrada.** Las primeras 380 fichas dieron cero y al final
recupera 88 %. Es lo contrario de lo que se temía (sesión que se agota por duración).

## Hipótesis descartadas, con evidencia

| hipótesis | veredicto | evidencia |
|---|---|---|
| (b) selector cambiado / cambio de código | **descartada** | El único commit entre el gate y la corrida es `f69c86c0`, que toca solo el cálculo del budget del gate en el runner: *"Sin cambio funcional del scraper"*. El motor es idéntico (`7019bd75`) |
| (d) sesión degradada por duración | **refutada** | El rendimiento **sube** con el tiempo (0 % → 88 %) |
| (c) mix de keywords | **descartada** | Gate 231-320 (`concesionaria`, `conductor`…) vs corrida 321-410 (`developer`, `devops`…): solo orden alfabético. No explica 380 fichas seguidas en cero |
| challenge en el click | **descartada** | `blocked: 0` y `challenges: 0` en el resumen. Un login gate habría puesto `_cut = True` y cortado la corrida |

Queda **(a) con matiz**: el panel embebido no entrega descripción al arranque de una sesión
nueva y empieza a hacerlo tras ~50 keywords (≈3 h de navegación). El mecanismo exacto —panel
lento, panel vacío, o contenido servido solo tras comportamiento sostenido— es lo que la
instrumentación tiene que responder.

## Lección: el gate midió en condiciones que no son las de producción

Esta es la parte que hay que no repetir.

| | gate del 01-09 | producción |
|---|---|---|
| Horario | **14:11-16:25** (diurno) | **05:00** |
| Estado de la sesión | navegador con **estado previo** — el motor se venía desarrollando ese mismo día (commit `7019bd75` a las 14:34, o sea el gate corrió entre pruebas manuales) | **navegador limpio**, primer arranque del día |
| Resultado | 98 % | 10,9 % |

El gate dio GO sobre una sesión ya "caliente" y en otra franja horaria. Midió el motor en su
mejor escenario, no en el que iba a correr.

**Regla para los gates futuros: correrlos en condiciones de producción** — mismo horario, mismo
arranque en frío, misma vía (cron/xvfb), sin navegación previa en la misma sesión. Un gate que
no reproduce las condiciones reales puede dar 98 % sobre algo que en producción rinde 11 %, y
el problema aparece días después atribuido a otra causa.

Corolario para este caso puntual: **el GO del gate del 01-09 no era válido** para autorizar el
paso a producción diaria, aunque el número fuera correcto para las condiciones en que se midió.

## Instrumentación desplegada (commit `be31ef13`)

El motor no registraba nada de las mudas. Ahora captura, con muestra acotada (25 por corrida,
400 chars de HTML):

- `title` del panel
- largo del HTML
- marcadores de challenge/login: `security check`, `verifying you are human`, `cf-challenge`,
  `iniciar sesión`, `captcha`, `just a moment`
- **por cada selector de `DESC_SELECTORS`: `ausente` | `presente/len=N` | `error`**

Esa última línea es la que decide el diagnóstico:

| lo que muestre | significa |
|---|---|
| selectores **ausentes** + marcadores de challenge | CF sirve otra página en el panel |
| selectores **ausentes** sin marcadores | el panel no cargó (o cambió el DOM) |
| selectores **`presente/len=0`** | el contenedor existe pero llega vacío → es cuestión de tiempo, y `desc_timeout` es el parámetro |
| selectores **`presente/len>0`** | el texto estaba y el timeout de 8 s no alcanzó a verlo → subir `desc_timeout` |

`desc_timeout` **no se tocó a propósito**: subirlo a ciegas taparía el síntoma si resulta que el
panel nunca carga, y perdería la señal.

## Próximo paso

La **primera corrida con preflight GO** es el experimento. Hoy 04-09 dio NO-GO (challenge en el
listado), igual que el 02-09; el 03-09 sí corrió. Con los datos de esa corrida se decide entre:

1. Subir `desc_timeout` (si los selectores aparecen con contenido o vacíos por tiempo).
2. Corregir/agregar selectores (si el DOM cambió).
3. Estrategia de "calentamiento" de sesión antes del tramo real (si el panel se habilita con el
   uso).
4. Replantear el canal Indeed con Gerardo (si aparecen marcadores de challenge en el panel: eso
   sería CF endureciendo listado **y** panel a la vez, y la conversación deja de ser un fix de
   selector).

## Referencias

- `01_sources/indeed/scrapers/indeed_scraper_headed.py` — motor e instrumentación
- `/tmp/indeed_headed.log` — logs de las corridas 02, 03 y 04 de septiembre
- `data/indeed_scraping_state.json` — `ultima_corrida`, `ultimo_nogo`, `proximo_offset`
- `exports/reportes/supervivencia/CURVAS_SUPERVIVENCIA_2026-09-01.md` §5 — por qué Indeed no es
  verificable por URL (contexto del canal)
