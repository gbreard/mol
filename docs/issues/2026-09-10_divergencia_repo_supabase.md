# El repo no es inventario confiable de lo que hay en Supabase

**Fecha:** 2026-09-10
**Origen:** Fase 5 / Etapa B.3
**Estado:** abierto
**Prioridad:** media (higiene; no bloquea nada hoy, muerde en cada migración)

---

## Qué pasó

B.3 tenía que listar los consumidores server-side de `estado` para preparar el
switch a `estado_ciclo`. Lo hice con `grep` sobre `fase3_dashboard/sql/` y
encontré una función. Antes de darlo por cerrado corrí el mismo inventario
**contra la base** (`068_inventario_funciones.sql`, `pg_proc`/`pg_views`).

Los dos inventarios no coinciden, y fallan en las dos direcciones:

| | repo | base |
|---|---|---|
| funciones que tocan `ofertas_dashboard` | no contadas | **22** |
| objetos que usan `estado` | 1 (`buscar_skill`) | 1 (`v_empresas_activas`) |

El objeto que el grep señaló **no es** el que aparece en la base. La definición
real de `buscar_skill` en Postgres no menciona `estado`: la línea 208 de
`004_catalogos_esco.sql` que le atribuí pertenece a la vista
`v_empresas_activas`, definida más abajo en el mismo archivo. Mi grep leyó el
archivo, no la función.

## Por qué importa

Si el switch de la Etapa C se hubiera planificado contra el inventario del repo,
habría tocado una función que no lo necesita y dejado sin migrar la vista que sí,
que es la única que cambia de cara al usuario. La verificación contra la base
costó una consulta y corrigió el alcance entero.

El problema de fondo: **el repo describe la intención, no el estado**. Entre los
dos hay deriva acumulada — objetos creados en el SQL Editor que nunca se
versionaron, y archivos versionados cuya versión viva difiere. Nada garantiza
que converjan, porque no hay ningún paso que los compare.

## Lo que NO propongo

Migrar todo a un sistema de migraciones estricto. Es correcto en abstracto y
desproporcionado acá: el equipo es chico, el SQL Editor es la herramienta real
de trabajo y prohibirlo solo lograría que el DDL se haga igual pero sin dejar
rastro.

## Lo que sí

**Un dump de esquema versionado, regenerado periódicamente.** Un script que
vuelque `pg_proc` + `pg_views` + `information_schema.columns` a un archivo del
repo. Ese archivo no es la fuente —la base lo es— pero es un espejo consultable:
`grep` sobre él responde lo que hoy solo responde abrir el SQL Editor, y su
`git diff` muestra qué cambió en la base entre dos fechas.

Costo: un script y una corrida ocasional. Beneficio: el inventario deja de ser
un acto de fe, y cada migración futura arranca del universo real.

Mientras no exista: **todo inventario previo a una migración se corre contra la
base**, no contra el repo. `068_inventario_funciones.sql` queda como plantilla.
