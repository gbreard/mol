# L — Rescate de los dos artefactos irreproducibles del VPS

**Fecha:** 2026-08-23 · **Branch:** `chore/rescate-artefactos-vps` · **Commit:** `b96f26db`
**Bloqueo que levanta:** la publicación post-L puede pisar `/srv/datasette/colegas.sqlite` sin destruir nada.

## Qué se rescató y por qué

La forénsica previa encontró dos artefactos que existían en **una sola copia, en el VPS, sin fuente
en ningún repositorio**. Uno de ellos vive *dentro* del SQLite remoto, así que el primer `scp` de la
publicación post-L lo habría borrado sin dejar rastro.

| Artefacto | Dónde vivía | Riesgo | Destino |
|---|---|---|---|
| Tabla `mr_seguimiento` (51 filas) | dentro de `colegas.sqlite` | **destrucción en el primer scp** | `D:\OEDE\Voucher\data\` (fuente) + espejo en MOL |
| `uri2esco.json` (3.046 entradas) | archivo suelto en `/srv/datasette/` | única copia, single point of failure | `config/uri2esco.json` (repo MOL) |

## P1 — `mr_seguimiento` → Voucher (su casa real)

No es de MOL: son los **Marcos de Referencia del INET/CFE** (perfiles ocupacionales oficiales de
certificación; varios traen el nº de resolución en el nombre — 108/10, 204/13) mapeados al
vocabulario de MOL. El dominio es Formación Profesional, cuyo proyecto es `D:\OEDE\Voucher\`.

- **Archivo:** `D:\OEDE\Voucher\data\mr_seguimiento_INET_2026-08-23.csv`
  *Nota de ubicación:* el prompt indicaba `datos\`; la carpeta no existe — la convención real del
  proyecto es `data\`, y ahí quedó. Voucher no tiene git: el versionado es nombre-con-fecha + LEEME.
- **Procedencia escrita:** `mr_seguimiento_INET_LEEME.md` al lado.
- **Contenido:** Construcción 22 · Automotriz 16 · Gastronomía 9 · Textil 4.
  `canon`: 39 exacto · 9 aprox · 2 SIN CANON · 1 "exacto · CUAR".

**Verificación:** 51 filas · 9 columnas (`num, sector, mr, ocupacion_esco, esco_code, isco, canon,
termino, mr_buscar`) · UTF-8 válido, sin BOM · sectores y distribución de `canon` idénticos al
remoto · spot-check de las filas 1, 32 y 51 carácter por carácter contra el VPS: exacto, sin
truncamiento por comas ni por acentos. Las únicas celdas vacías son `esco_code`/`isco` en las 2
filas SIN CANON — es el dato real, no pérdida.

## P2 — `uri2esco.json` → repo MOL

Mapeo URI ESCO → código jerárquico que ancla el vocabulario de las 88 reglas y del traductor.

- **Ubicación usada:** `config/uri2esco.json`.
  *Nota de ubicación:* el prompt indicaba `data_in\`, que no existe en este repo. La ubicación
  idiomática para insumos de referencia es `config/` — ahí ya viven `isco_labels_es.json`,
  `isco_preferred_labels.json`, `area_funcional_esco_map.json`, `mapeo_reglas_familias.json` y
  `lexico_traductor.json`. `data/` guarda estado de runtime y logs, no catálogos.
- **Integridad:** 3.046 entradas · `sha256` local **==** remoto:
  `26b0bd940901c27f157cce282c0cfc168163bfedcd16b5dba209951365a3e03a`.
- **No regenerable desde el pipeline:** `esco_occupations.esco_code` está 100% vacía (0 de 3.045) y
  el único mapeo vivo (`ofertas_esco_matching.titulo_esco_code`) cubre 810 URIs = 27%.

## P3 — El espejo declarado

`config/mr_seguimiento_INET.csv` + `config/mr_seguimiento_INET_LEEME.md`, que declara en la primera
línea: **fuente en Voucher, MOL consume, Voucher posee, si cambia allá re-sincronizar acá.**
Duplicación consciente y anotada — evita que MOL dependa de una ruta de otro proyecto que puede
moverse, sin crear una segunda fuente de verdad silenciosa. Espejo y fuente comparten sha256
(`d7de4249…`).

## Cumplimiento

- **VPS read-only:** solo `sqlite3 -readonly`, `scp` de bajada y `sha256sum`. El CSV se generó por
  streaming a stdout — **no se escribió ni un archivo temporal en el servidor**. `colegas.sqlite`
  intacto, nada subido, nada borrado.
- **Sin `git add -A`:** los tres archivos se agregaron por ruta explícita. Las modificaciones
  preexistentes del árbol (`.ai/learnings.yaml`, `config/training_pairs.json`,
  `metrics/gold_set_history.json` y los untracked) quedaron **sin tocar y sin commitear**.
- **PR abierto, sin mergear.**

## Pendiente (fuera de este frente)

Hallazgo lateral de la forénsica: `/srv/metabase/build_full.py` tiene usuario y contraseña de
Metabase **en texto plano**, con permisos 644 en el VPS. Conviene rotar la credencial y moverla a
variable de entorno la próxima vez que se toque esa carpeta.
