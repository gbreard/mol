# Cambio en el conteo de ofertas activas del tablero

**Fecha:** 2026-09-10 · **Actualizado con números frescos:** 2026-09-24
**Alcance:** tablero MOL y `v_empresas_activas`. No cambia ninguna oferta, ni su
clasificación, ni ningún dato ya validado.

---

## Qué van a ver

El tablero pasa de mostrar **0 ofertas activas** a mostrar **~4.800**.

No aparecieron ofertas nuevas. Estaban en la base desde siempre, marcadas como
dadas de baja por un criterio equivocado.

> **Nota sobre las cifras (24-09):** cuando se redactó esta nota (10-09) el número
> proyectado era ~7.100. Bajó a **~4.800** porque en estas dos semanas el
> **verificador confirmó bajas reales** (chequeó una por una las presuntas y
> confirmó ~7.200 caídas). Es el sistema funcionando: el número que muestra el
> tablero es el de **hoy**, dinámico, no una foto fija. El día del deploy va a
> reflejar el conteo de ese día.

## Por qué estaban mal marcadas

El sistema daba por caída a toda oferta que no apareciera en la última corrida
de scraping. Ese criterio sería razonable si cada corrida recorriera el portal
entero, pero no lo hace: el scraping de Bumeran es **rotativo**, mira 165 de
1.148 búsquedas por día. Una oferta viva que simplemente no cayó en el sorteo
del día quedaba marcada como baja.

El resultado es el que se esperaría de esa mecánica: de las ofertas **validadas**,
el criterio viejo hoy marca como baja al **100%** — el tablero muestra **0
activas**. Todas las que el equipo validó quedaron "caídas" por no haber
aparecido en la última corrida rotativa.

En lugar de eso, ahora una oferta se da de baja cuando **se verifica** que ya no
está publicada, y la baja queda registrada con su fecha estimada y un intervalo
de incertidumbre (una baja detectada con 40 días de margen no vale lo mismo que
una de 2). Los estados posibles pasan a ser: activa, presunta baja, baja
confirmada, baja no verificada, baja inferida.

Números de hoy (24-09), para dimensionar:
- **~4.800** validadas y verificadas como **activas** → las que muestra el tablero.
- **~8.400** validadas en **presunta baja** (en cola de verificación). **No** se
  cuentan como activas: una presunta todavía no está confirmada viva, y el tablero
  sirve a personas reales, así que solo mostramos lo verificado.

## El otro número, que también hay que decir

Además de esas ~4.800, hay **más de ~9.500 ofertas** captadas que **no llegan al
tablero**.

No es un problema de este cambio ni de la validación: esas ofertas no pasaron
por el procesamiento de lenguaje natural, que es el paso que extrae tareas,
ubicación y seniority y habilita la clasificación ocupacional. Sin ese paso una
oferta no tiene qué mostrar y el tablero no la puede incluir.

El pipeline de procesamiento está **suspendido desde el 4 de septiembre por
decisión de Gerardo**, mientras se estabiliza el scraping y se mejora la calidad
del procesamiento. Es una pausa deliberada, no una falla. Hoy hay **27.613
ofertas sin procesar** acumuladas. Cuando se reactive, esas se incorporan y el
número de activas del tablero va a subir de nuevo.

Dicho de otro modo: **~4.800 es lo que el tablero puede mostrar hoy, no el total
de ofertas activas del mercado que tenemos captadas.** Conviene tenerlo presente
al leer cualquier cifra absoluta.

## Qué más cambia de cara

`v_empresas_activas` —la vista que lista empresas con búsquedas abiertas—
depende del mismo criterio, así que también cambia de cara: pasa de 0 a las
~4.800, agrupadas por empresa. Van a ver muchas más empresas que antes. Vale la
misma aclaración: no son empresas nuevas, estaban escondidas detrás del filtro roto.

## Qué NO cambia

- Ninguna oferta cambia de clasificación ocupacional ni de skills.
- Nada de lo validado por el equipo se toca ni se reprocesa.
- Las series históricas y los indicadores acumulados siguen calculándose igual.

Sobre esto último hay una salvedad que estamos trabajando aparte: varios
indicadores del tablero se calculan sobre el acumulado histórico completo, no
sobre las ofertas vigentes. Con el número de activas ahora visible al lado, la
diferencia entre "el mercado de hoy" y "todo lo acumulado" se vuelve más
notoria. Estamos revisando indicador por indicador cuál de las dos ventanas
corresponde a cada uno; hasta que eso se resuelva, conviene no leer un KPI
histórico como si describiera a las activas.

## Reversibilidad

El criterio viejo (`estado_oferta`) se sigue calculando en paralelo y **no se
apaga** con este cambio (el switch que lo apaga queda para más adelante). Si algo
no cuadra, se vuelve atrás sin pérdida de datos.
