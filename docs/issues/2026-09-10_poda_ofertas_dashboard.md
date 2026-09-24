# Poda de `ofertas_dashboard`: borrar lo que quedó fuera del filtro de vigencia

**Fecha:** 2026-09-10
**Origen:** Fase 5 / Etapa B.2
**Estado:** aprobado, **diferido a post-switch + 1 semana** (decisión de Gerardo)
**Opción elegida:** A — DELETE dirigido por lotes

---

## Qué hay que hacer

Desde B.2 el sync manda 20.592 filas (vigentes + confirmadas de 90 días +
transiciones recientes) en lugar de las 96.872 validadas. Las **~76.300
restantes siguen en Supabase**: nadie las actualiza y nadie las borra.

La poda las elimina por lotes. Queda `ofertas_dashboard` en ~39K filas como
techo (~20K hoy, el resto entra al reactivarse el pipeline de NLP).

## Prerequisito conceptual: el tapón de 7 días

El tapón que hoy vive en `extraer_ofertas_validadas` **es la versión provisoria
de esta poda**, y entender por qué evita que la poda se diseñe mal.

El problema que ambos resuelven es el mismo. Una oferta que pasa de `activa` a
`baja_no_verificada` sale del conjunto que el sync manda. Si sale y nadie hace
nada, Supabase la deja **congelada en `activa` para siempre**: ninguna corrida
futura la va a tocar, porque el filtro ya no la selecciona. El panel
sobre-cuenta, y el error es acumulativo e irreversible — cada oferta que muere
suma una activa fantasma que no se corrige sola.

El tapón lo evita mandando 7 días de salientes: la oferta se sincroniza una
última vez con su estado nuevo y recién después cae del conjunto. Es correcto
pero frágil: depende de que el sync corra al menos una vez cada 7 días y de que
la transición quede estampada en alguno de `fecha_ultima_verificacion`,
`fecha_baja` o `fecha_ultimo_visto`.

**La poda es el cierre definitivo del mismo agujero**, y por eso su diseño no
puede ser sólo "borrar lo viejo". Tiene que ser una **reconciliación**:

> `ofertas_dashboard` debe quedar igual al conjunto que define el filtro de
> vigencia. Upsert de lo que está adentro, DELETE de lo que está afuera.

Con esa formulación una oferta que muere no queda congelada: desaparece. Si en
cambio la poda se implementa como un borrado por antigüedad (`DELETE WHERE
fecha_baja < X`), el agujero sigue abierto y el tapón sigue siendo necesario
para siempre.

**Cuando la reconciliación esté andando, el tapón se puede retirar.** Antes no.

## Orden y precauciones

1. Esperar el switch de la Etapa C **+ 1 semana** de observación. Mientras la
   columna `estado` legacy siga viva como rollback, borrar filas elimina también
   la posibilidad de volver atrás sobre ellas.
2. Antes del primer DELETE, verificar que ninguna de las 22 RPCs analíticas
   dependa del histórico completo de un modo que la poda rompa
   (→ `2026-09-10_rpcs_sin_filtro_vigencia.md`). **Ese issue conviene resolverlo
   primero**: la poda cambia el universo sobre el que esos KPIs se calculan, de
   "todo el histórico" a "los últimos 90 días más las vigentes", que no es
   ninguna de las dos definiciones que alguien eligió.
3. Lotes con `time.sleep` entre chunks: free tier, ~15 req/s.
4. Contar antes y después, y dejar el número en la bitácora.

## Qué NO se borra del lado local

Nada. SQLite conserva las 118K ofertas completas. La poda es sólo de la copia de
presentación.
