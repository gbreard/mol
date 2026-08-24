# M — P2/P3: publicación del export post-L y canal de descarga

**Fecha:** 2026-08-24 · **Branch:** `feat/export-colegas-postL`
**Estado: PUBLICADO y verificado de punta a punta. Falta sólo la prueba con un colega antes de anunciar.**

## Lo publicado

| | |
|---|---|
| **Época** | `corpus_2026-08-22_matcher-3.6.0_post-L` |
| **Archivo** | `/srv/datasette/colegas_corpus_2026-08-22_matcher-3.6.0_post-L.sqlite` |
| **Symlink** | `/srv/datasette/colegas.sqlite` → la versión nueva |
| **Peso** | 2.264.186.880 bytes (2,16 GB) · comprimido **463 MB** (ratio 4,66×) |
| **sha256** | `b398ab86a34e5275b74b4bcecfcfc4381d15dfdaebd0059e3bdf269f6549da27` |
| **URL** | `https://187-124-150-28.sslip.io/descargas/` (usuario `colegas`) |

Contenido: `ofertas` 97.185 · `oferta_tareas` 547.401 · `oferta_skills` 2.827.507 ·
`ocupaciones` 828.377 · `mr_seguimiento` 51 · `_meta_version` 1 · **11 índices**.

Todo salió del `05b`: **cero pasos manuales en el servidor.** La ceremonia de junio —subir el
archivo y después agregarle a mano columnas, índices y una tabla curada— quedó muerta.

## Verificación de punta a punta

La prueba que importa no es "el script dijo OK", sino bajar el archivo como lo haría un colega y
comprobar que lo que llega es lo que se publicó:

```
curl -u colegas:*** https://.../colegas_...sqlite.gz | gunzip -c | sha256sum
  → b398ab86a34e5275b74b4bcecfcfc4381d15dfdaebd0059e3bdf269f6549da27
sha256 publicado
  → b398ab86a34e5275b74b4bcecfcfc4381d15dfdaebd0059e3bdf269f6549da27   ✓ idéntico
```

Se descargaron los 463 MB reales por HTTPS, se descomprimieron al vuelo y el hash del resultado
coincide con el publicado. **El camino completo está probado.**

Además: sin credencial responde **401**; el listado con credencial muestra los tres archivos con
sus tamaños; un `Range` devuelve **206** (las descargas cortadas se reanudan — importante con la
red del ministerio); `Content-Type: application/octet-stream` para que baje en vez de abrirse; y
`X-Robots-Tag: noindex`. **Metabase sigue respondiendo 200 en `/`**: el cambio de nginx no tocó
el sitio existente.

## El canal (P3)

`location /descargas/` sobre el nginx que ya existía, con dos decisiones que conviene registrar:

- **Sirve `/srv/descargas` (symlinks a lo publicado), no `/srv/datasette`.** Ese directorio
  contiene `datasette.env`, con el hash de la contraseña del Datasette viejo: servirlo lo habría
  expuesto.
- **Va con contraseña.** El archivo trae texto crudo de avisos —puede incluir nombres, mails y
  teléfonos— y la guía dice "uso interno del equipo, no redistribuir". Sin auth quedaría accesible
  a cualquiera que pase por la IP, y además indexable. El Datasette de junio también tenía clave;
  esto conserva ese criterio.

El instalador (`scripts/ops/instalar_canal_descargas.sh`) es idempotente, hace backup de la config
y valida con `nginx -t`: **si la validación falla restaura el backup y no recarga**, para que el
peor caso sea "no se instaló el canal" y nunca "se cayó el sitio".

## Dos fallas encontradas en la corrida real

**1. La rotación borraba justo lo que debía conservar.** El listado de candidatos usaba
`ls -1t *.sqlite`, que incluye el symlink `colegas.sqlite`. Por ser el más nuevo, el symlink se
quedaba con el lugar de "la anterior" y mandaba a borrar la versión previa de verdad: la rotación
de uno dejaba el sistema **sin destino de rollback**. Se vio en vivo — conservó el symlink y borró
`colegas_pre-M_2026-06-26.sqlite`.

*Consecuencia real: ninguna.* Lo único irreproducible de la copia de junio ya estaba rescatado en
el PR #66, y el spec la daba explícitamente por descartable. Pero el bug habría mordido en serio
en la publicación siguiente, cuando la "anterior" sí sea una versión que se quiera conservar.
**Corregido** (`find -type f`): ya no entran symlinks al listado.

**2. El `--dry-run` abortó en el primer intento — y eso estuvo bien.** El guard que exige leer la
época desde `_meta_version` se negó a publicar algo que no podía verificar. La causa era que el
CLI de `sqlite3` no está instalado en el WSL de trabajo. Se le agregó fallback a Python.

## Pendientes

- **Prueba con un colega**, de punta a punta, antes de anunciar a todos. La credencial ya está
  creada; el canal está probado del lado técnico.
- **`05b` y guía v3 sin versionar.** Ambos viven en `D:\Trabajos en PY\MOL_escenarios\`, que no es
  un repositorio git. Todo lo del lado de `Webscrapping` está en el PR, pero las dos piezas que
  *son* el reemplazo de la ceremonia artesanal quedaron sin control de versiones. Vale decidir si
  se copian acá o si `MOL_escenarios` pasa a tener git propio.
- **Estado de la rotación hoy:** hay una sola versión publicada. La próxima publicación dejará dos
  y a partir de ahí la rotación (ya corregida) mantiene el par.
