# Curvas de supervivencia de ofertas — Bumeran y ZonaJobs

**Fecha:** 2026-09-01 · **Rama:** `medicion/supervivencia-ofertas` · **Alcance:** medición, sin tocar producción
**Muestra:** 120 ofertas por portal, estratificadas por antigüedad de `fecha_ultimo_visto`
**Datos crudos:** `muestra.json`, `resultado_bumeran.json`, `resultado_zonajobs.json` (este directorio)

Insumo para el rediseño del ciclo de vida de bajas. Hoy el sistema declara baja a toda
oferta no vista en la última corrida, lo que produce 111K "bajas" que son artefacto del
muestreo, no hechos del mercado. Lo que sigue son umbrales calibrados con datos.

---

## 1. Curvas de supervivencia

### Bumeran (n=120)

| antigüedad de `fecha_ultimo_visto` | n | VIVA | CAÍDA | AMBIGUA | **% vivas** |
|---|---|---|---|---|---|
| 0-2 semanas | 15 | 15 | 0 | 0 | **100 %** |
| 2-4 semanas | 15 | 13 | 2 | 0 | **87 %** |
| 4-6 semanas | 15 | 10 | 5 | 0 | **67 %** |
| 6-8 semanas | 15 | 6 | 9 | 0 | **40 %** |
| 8-10 semanas | 15 | 2 | 13 | 0 | **13 %** |
| 10-12 semanas | 15 | 1 | 14 | 0 | **7 %** |
| 12-16 semanas | 15 | 1 | 14 | 0 | **7 %** |
| 16+ semanas | 15 | 0 | 15 | 0 | **0 %** |
| **total** | **120** | **48** | **72** | **0** | 40 % |

### ZonaJobs (n=120)

| antigüedad de `fecha_ultimo_visto` | n | VIVA | CAÍDA | AMBIGUA | **% vivas** |
|---|---|---|---|---|---|
| 0-2 semanas | 15 | 14 | 1 | 0 | **93 %** |
| 2-4 semanas | 15 | 13 | 2 | 0 | **87 %** |
| 4-6 semanas | 15 | 7 | 8 | 0 | **47 %** |
| 6-8 semanas | 15 | 4 | 11 | 0 | **27 %** |
| 8-10 semanas | 15 | 2 | 13 | 0 | **13 %** |
| 10-12 semanas | 15 | 0 | 15 | 0 | **0 %** |
| 12-16 semanas | 15 | 0 | 15 | 0 | **0 %** |
| 16+ semanas | 15 | 1 | 14 | 0 | **7 %** |
| **total** | **120** | **41** | **79** | **0** | 34 % |

### Comparación con ComputRabajo (medida en el drenaje del 28-08 al 01-09)

| portal | ~1 mes | ~2 meses | ~3 meses | cruce del 50 % |
|---|---|---|---|---|
| **ComputRabajo** | ~95 % | ~56 % | ~7 % | ~8-9 semanas |
| **Bumeran** | ~93 %¹ | ~40 % | ~7 % | **~6 semanas** |
| **ZonaJobs** | ~90 %¹ | ~27 % | ~0 % | **~5 semanas** |

¹ promedio de los buckets 0-2w y 2-4w.

**ZonaJobs se apaga más rápido que Bumeran, y los dos más rápido que ComputRabajo.** La
diferencia entre plataformas es real y justifica umbrales por portal: usar un único
umbral global sobreestimaría la vida de ZonaJobs en ~3-4 semanas.

Notas de lectura:

- El 7 % del bucket 16+ de ZonaJobs es **1 sola oferta** viva sobre 15. Con n=15 por
  bucket, un caso equivale a 6,7 puntos: las diferencias de un punto entre buckets
  contiguos no son significativas. La **forma** de la curva sí lo es.
- La cola no llega a 0 nunca del todo: hay avisos que permanecen publicados meses
  (búsquedas permanentes, alta rotación). No conviene diseñar el verificador asumiendo
  que después de N semanas *todo* está caído.

---

## 2. Taxonomía de señales por portal

El dato de diseño más importante de esta medición.

### Bumeran y ZonaJobs (plataforma Navent) — el HTML **no sirve**

Ambos portales son SPA: el detalle devuelve un shell idéntico para avisos vivos y caídos.

```
GET https://www.bumeran.com.ar/empleos/{id}.html
  aviso vivo (ult_visto 2026-09-01) : HTTP 200, len=63595, sin <title>, sin JSON-LD
  aviso caído (ult_visto 2026-02-07): HTTP 200, len=63595, sin <title>, sin JSON-LD
                                       ^^^^^^^^^^^^^^ byte por byte lo mismo
```

Ni status, ni redirect, ni longitud, ni marcadores de texto distinguen. **Cualquier
verificador basado en pedir la URL de detalle daría "vivo" para el 100 % del corpus.**
ZonaJobs se comporta igual (`len=63242/63595`).

Tampoco existe un endpoint REST de detalle: `/api/avisos/{id}`, `/api/avisos/detalle/{id}`,
`/api/avisos/{id}/detalle`, `/api/candidatos/avisos/{id}` y `/api/avisos/{id}/similares`
devuelven todos `{"statusCode":404,"error":"Not Found","message":"Cannot GET ..."}` — que
es "la ruta no existe", no "el aviso no existe".

**La señal utilizable es la presencia en el índice de búsqueda**, vía `POST /api/avisos/searchV2`,
que es la API que el scraper ya usa para el listado:

| señal | interpretación | ejemplo observado |
|---|---|---|
| el `id` aparece entre los resultados de buscar su título | **VIVA** | `1118411887` (*"EY - Manager en Finance Transformation"*) → 1 resultado, es él |
| la búsqueda devuelve **menos** resultados que el tope y el `id` no está | **CAÍDA** | `1118018624` (*"Chef Profesional"*) → 1 resultado, es otro aviso |
| la búsqueda devuelve **0** resultados | **CAÍDA** (caso fuerte) | `1118103912` (*"Conductores de Camión Cisterna…"*) → 0 resultados |
| la búsqueda llega al **tope** de resultados y el `id` no está | **AMBIGUA** — podría estar más allá | no ocurrió en esta muestra |

Configuración usada: `{"pageSize":100, "page":0, "sort":"RELEVANCE", "query": <título[:60]>}`
con los headers del scraper (`x-site-id`: `BMAR`/`ZJAR`, `x-pre-session-token` UUID nuevo).

**Cero ambiguas en 240 mediciones**: ninguna búsqueda alcanzó el tope de 100. La búsqueda
por título es suficientemente selectiva (mediana de resultados en las caídas: **0**;
máximo observado: 20). De las 151 caídas, **88 tuvieron 0 resultados** — el caso más
inequívoco.

### Indeed — no verificable por URL

Diez ofertas (5 recientes + 5 de más de 4 meses) más dos de control con la vía real del
scraper:

| vía | recientes | viejas | ¿distingue? |
|---|---|---|---|
| `requests` | HTTP **403**, `len=25742` | HTTP **403**, `len=25742` | **no** |
| `curl_cffi` (impersonate chrome, desde el VPS) | HTTP **401**, `len=1675` | HTTP **401**, `len=1675` | **no** |

La respuesta es idéntica para vivas y caídas por ambas vías. Indeed además está
bloqueando activamente desde el 2026-08-20 (403 sostenido en local y VPS, registrado por
`check_indeed_unblock.py`), así que el deep-link `/viewjob` no es una vía de verificación
ni siquiera potencial mientras dure el bloqueo. Ver sección 5.

---

## 3. Viabilidad del fetch individual como verificador activo

| portal | vía viable | costo por verificación | veredicto |
|---|---|---|---|
| **Bumeran** | `POST /api/avisos/searchV2` con el título | 1 request, ~0,4 s + pausa | **Sí**, con reserva (ver abajo) |
| **ZonaJobs** | idem, `x-site-id: ZJAR` | 1 request, ~0,4 s + pausa | **Sí**, con reserva |
| **ComputRabajo** | `GET` del detalle HTML (ya en uso en el PASO 2) | 1 request, ~2,2 s | **Sí**, ya probado a escala (8.500 fetches, 0 errores) |
| **Indeed** | ninguna | — | **No** |

Costo de una verificación completa del corpus vivo, a 3 s por request:
Bumeran ~31K ofertas → **~26 h**; ZonaJobs ~18K → **~15 h**. Inviable como barrido total,
razonable como **cola priorizada**: verificar solo lo que está en la franja de duda
(4-10 semanas), que es donde la curva decide.

**Reserva importante sobre `searchV2`.** Verifica *presencia en el índice de búsqueda*, no
*existencia del aviso*. Un aviso publicado pero despublicado del buscador (pausado por el
empleador, moderado, o con búsqueda saturada) daría falso "caída". El riesgo es acotado en
esta muestra —la mediana de resultados es 0, así que rara vez compite con otros avisos—
pero conviene tratar el resultado como **"presunta baja" y no como "baja confirmada"**, y
exigir dos verificaciones separadas en el tiempo antes de dar por muerta una oferta.

---

## 4. Umbrales recomendados de `umbral_presunta_baja`

Derivados del bucket donde la supervivencia cruza el 50 %:

| portal | cruce del 50 % | **umbral sugerido** | supervivencia esperada en el umbral |
|---|---|---|---|
| **ZonaJobs** | entre 4-6w (47 %) | **5 semanas** | ~50 % |
| **Bumeran** | entre 4-6w (67 %) y 6-8w (40 %) | **6 semanas** | ~50 % |
| **ComputRabajo** | ~8-9 semanas | **9 semanas** | ~50 % |
| **Indeed** | no medible | **no aplicar por URL** — ver 5 | — |

Cómo usarlos, en tres estados en vez de dos:

```
vista en la última corrida            -> ACTIVA
no vista, antigüedad < umbral         -> ACTIVA (ausencia sin valor informativo:
                                         el muestreo rotativo no la cubrió)
no vista, antigüedad >= umbral        -> PRESUNTA_BAJA  -> entra a cola de verificación
verificada caída 2 veces separadas    -> BAJA_CONFIRMADA
```

El punto central: **la ausencia de una oferta en una corrida no es evidencia de baja**, y
en Bumeran es evidencia casi nula. Su scraping es rotativo —165 de 1.148 keywords por día,
1 página por keyword— así que una oferta vigente puede pasar semanas sin aparecer. Ese es
el mecanismo que produce las 111K bajas actuales: el sistema está midiendo su propio
muestreo, no el mercado.

Con estos umbrales, una estimación gruesa sobre el corpus actual (~31K Bumeran + ~18K
ZonaJobs) es que la mayoría de las bajas declaradas seguirían siendo bajas, pero se
recuperarían como activas las de menos de 5-6 semanas sin ver — que son justamente las
relevantes para cualquier indicador de demanda reciente.

Si hay que elegir un único parámetro por simplicidad de implementación, **6 semanas** es
el compromiso razonable para los tres portales medibles; cuesta ~3 semanas de precisión en
ZonaJobs.

---

## 5. Limitación de Indeed

Indeed **no será verificable por URL**, ni ahora ni previsiblemente:

1. El deep-link `/viewjob?jk=…` responde igual para vivas y caídas (401/403 con cuerpo de
   longitud idéntica). No hay señal que extraer.
2. Está bloqueando activamente desde el 2026-08-20; la última corrida exitosa fue esa
   fecha, y el vigía de 3 h reporta 403 sostenido en las dos IPs.

Vías alternativas, en orden de preferencia:

- **Inferencia por ausencia + `fromage`**: el scraper ya usa `--fromage 14`, o sea que
  cada corrida ve la ventana de los últimos 14 días. Una oferta que no aparece en dos
  corridas consecutivas *dentro de su ventana de frescura* es una señal más fuerte que en
  los otros portales, porque acá el muestreo sí es exhaustivo para esa ventana. Es la
  opción de menor costo y no requiere requests adicionales.
- **Búsqueda headed** (navegador real) contra el listado, no el deep-link. Sirve para
  reponer el scraping, pero como verificador de bajas es caro y frágil.
- **No modelar bajas de Indeed** y marcar su ciclo de vida como *no observable*, dejando
  el campo explícitamente nulo en vez de inferido. Preferible a inventar un estado que no
  se puede sostener.

**Recomendación:** la primera. Y, sea cual sea la elegida, que el modelo de datos permita
distinguir "baja" de "no observable", porque hoy los dos casos colapsan en el mismo valor.

---

## 6. Cómo se hizo (reproducibilidad)

- Muestra: `muestra.json` (240 ofertas con id, url, título, bucket, `fecha_ultimo_visto`,
  `scrapeado_en`), semilla `random.seed(2026)`.
- Estratos: 8 buckets por antigüedad de `fecha_ultimo_visto` respecto del 2026-09-01;
  15 ofertas por bucket, muestreo aleatorio dentro de cada uno. Todos los buckets tenían
  universo suficiente (el más chico: 872 ofertas).
- Requests: pausas de 2-4 s aleatorias, User-Agent de Chrome, sesión única por portal.
  Total: 240 mediciones + 22 de sondeo y taxonomía + 12 de Indeed.
- Verificado antes de empezar que no hubiera scraping en curso (sin lock en el VPS, sin
  procesos locales).
- Ninguna escritura en BD ni en producción.

### Observación colateral

Bumeran y ZonaJobs **comparten el backend de Navent y parte del índice**: 23 de las 120
ofertas de la muestra de ZonaJobs tienen `id` con prefijo `1118…`, que es el rango de
Bumeran, y una búsqueda en el índice de ZonaJobs devuelve ids de ambos. No afecta esta
medición (la verificación es por id contra el índice del portal correspondiente), pero
conviene tenerlo presente al analizar solapamiento de corpus entre los dos portales: puede
haber duplicación real de avisos que hoy se cuentan como ofertas distintas.
