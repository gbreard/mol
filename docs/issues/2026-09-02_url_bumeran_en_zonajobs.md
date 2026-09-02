# El scraper de Bumeran guarda URL de Bumeran para avisos de ZonaJobs

**Detectado:** 2026-09-02, computando el proxy retroactivo de la guarda de colisiones de id.
**Estado:** abierto, sin agendar.
**Severidad:** media — 5.359 filas con URL incorrecta, y el bug **sigue activo**.
**Fuera del alcance** de `fix/guarda-colisiones-id` (esa rama trata colisiones de id; esto es
atribución de URL).

## Qué pasa

`01_sources/bumeran/scrapers/bumeran_scraper.py:796` toma el portal del payload de Navent
—que es correcto y puede decir `zonajobs`— pero construye la URL **siempre** como Bumeran:

```python
'portal': oferta.get('portal'),          # <- correcto: puede ser 'zonajobs'
...
'url_oferta': f"https://www.bumeran.com.ar/empleos/{oferta.get('id')}.html"
              # <- SIEMPRE bumeran, ignora el portal real del aviso
```

Bumeran y ZonaJobs comparten el backend de Navent, así que la API de búsqueda de Bumeran
devuelve también avisos de ZonaJobs. Esos avisos quedan **bien etiquetados** (`portal='zonajobs'`)
pero con una URL que apunta al portal equivocado.

## Magnitud

```
filas con portal='zonajobs':
  url zonajobs.com.ar/aviso/{id}         12.588   2026-03-10 .. 2026-08-31
  url bumeran.com.ar/empleos/{id}.html    5.359   2025-10-30 .. 2026-09-02  <- el bug
```

**23,6 % de ZonaJobs tiene la URL de otro portal.** No es un residuo histórico: la fila más
reciente es de hoy. Aparece de forma continua desde 2025-10, con un pico en 2026-03 (1.237)
que coincide con la puesta en marcha del scraping en el VPS.

El scraper propio de ZonaJobs (`run_zonajobs_vps.py`, desde 2026-03-10) construye la URL bien;
el problema es exclusivamente la vía Bumeran, que sigue corriendo **a diario**.

## Impacto

1. **Links del dashboard**: 5.359 ofertas mandan al usuario a `bumeran.com.ar` cuando el aviso
   se publicó en ZonaJobs. Puede funcionar por el backend compartido, pero no está verificado
   y es dato incorrecto.
2. **Cualquier verificación por URL**: la medición de supervivencia (2026-09-01) usa
   `url_oferta` para decidir si un aviso sigue vivo. Sobre estas filas estaría consultando el
   portal equivocado. No invalida esa medición —la muestra se tomó de ZonaJobs y el veredicto
   se resolvió por `searchV2`, no por la URL— pero el verificador activo que se diseñe a partir
   de ella sí se vería afectado.
3. **Análisis por portal**: el `portal` es correcto, así que los conteos por portal no están
   sesgados. El daño es solo en la URL.

## Fix

**El scraper: una línea.** Construir la URL según el portal real del aviso:

```python
_BASES = {'zonajobs': 'https://www.zonajobs.com.ar/aviso/{id}',
          'bumeran':  'https://www.bumeran.com.ar/empleos/{id}.html'}
_portal = (oferta.get('portal') or 'bumeran').lower()
'url_oferta': _BASES.get(_portal, _BASES['bumeran']).format(id=oferta.get('id'))
              if oferta.get('id') else None
```

Conviene confirmar antes qué otros valores puede traer `oferta.get('portal')` en el payload de
Navent (¿solo `bumeran`/`zonajobs`, o hay más sitios del grupo?), y dejar el fallback explícito.

**El backfill de las 5.359: hay que decidirlo, no es automático.**

El formato correcto es deducible de los propios datos: los ids afectados van de **2.062.759 a
2.189.175**, dentro del rango que el scraper v2 sí publica como `zonajobs.com.ar/aviso/{id}`
(1.914.954 – 1.118.421.294). O sea que el reemplazo sería:

```sql
UPDATE ofertas
   SET url_oferta = 'https://www.zonajobs.com.ar/aviso/' || id_oferta
 WHERE portal = 'zonajobs' AND url_oferta LIKE '%bumeran.com.ar%';
```

Antes de correrlo hay que resolver dos cosas:

1. **Verificar el formato con una muestra real** (10-20 fetches): que
   `zonajobs.com.ar/aviso/{id}` responda para ids de ese rango. Ojo que ZonaJobs es una SPA y
   devuelve HTTP 200 con el mismo shell para todo, así que **el status no alcanza como
   verificación** — hay que comprobar por `searchV2`, como se documentó en
   `exports/reportes/supervivencia/CURVAS_SUPERVIVENCIA_2026-09-01.md`.
2. **Decidir si el backfill viaja a Supabase.** Si el dashboard ya publicó esos links, el
   `UPDATE` local necesita su sync correspondiente para que el usuario final vea el link
   corregido.

Y una precaución del contexto actual: `export_nuevas.py` solo exporta por `scrapeado_en` o
`descripcion_actualizada_en`, así que **un UPDATE de `url_oferta` en local no viaja solo** al
resto del sistema. Conviene hacer el fix del scraper primero, dejar que las corridas nuevas
entren bien, y recién después decidir el backfill del histórico.

## Cómo se detectó

Computando el proxy retroactivo de colisiones de id (comparar `portal` declarado contra el
dominio de `url_oferta`). Ese proxy buscaba colisiones de id y **no encontró ninguna** —sigue
siendo ciego a ellas por las razones documentadas en el reporte de esa sesión— pero destapó
este bug distinto.

## Referencias

- `01_sources/bumeran/scrapers/bumeran_scraper.py:796` — el origen
- `scripts/scraping/run_zonajobs_vps.py` — construye la URL bien, sirve de referencia
- `exports/reportes/medicion_duplicacion_crossportal.md` — backend Navent compartido
- `exports/reportes/supervivencia/CURVAS_SUPERVIVENCIA_2026-09-01.md` — por qué el status HTTP
  no sirve para verificar avisos de ZonaJobs
- Rama `fix/guarda-colisiones-id` (commit `bef4b104`) — donde salió el hallazgo
