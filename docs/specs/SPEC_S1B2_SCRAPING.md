# SPEC S1.B.2 — Relevamiento de Scraping

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo) · 2026-06-05
> Segundo spec de la fase S1.B — Relevamiento del sistema. Releva el estado actual del scraping del proyecto MOL, la deuda observada y los principios de diseño objetivo. Sigue la plantilla común definida en `docs/specs/MOL_master_relevamiento.md` v0.2.

---

## 5.1 Memoria operativa de Gerardo

Lo que Gerardo aporta sobre el scraping antes de la verificación contra el código. Información que ningún archivo del repo registra, capturada en la conversación del 2026-06-05.

### Mapa de portales

El sistema scrapea actualmente **6 portales de empleo**. El más antiguo es **Bumeran**.

**Nombres específicos de los 4 portales restantes**: a relevar por Claude Code en capa 5.2.

**Crecimiento planeado**: hay en agenda **agregar más de 10 portales nuevos**. Esto importa para el diseño objetivo (capa 5.4): cualquier arquitectura sana debe escalar a ~16 portales, no quedarse en 6.

### Dónde corren los scrapers

**Mezcla de ubicaciones**: no todos los scrapers corren en el mismo lugar. Configuración conocida:
- **Bumeran**: corre en VPS.
- **Indeed**: arrancó en VPS, pero **Indeed filtra la IP del VPS**, así que se migró a **local**. Es un pato rengo operativo: la arquitectura "uniforme VPS-first" se rompió por restricción del portal, sin que esto esté documentado como decisión consciente.
- **Otros 4**: distribución a relevar por Claude Code.

Frecuencia de corrida y orquestación (paralelo vs secuencial): a relevar por Claude Code.

### Cómo se scrapea — el dato más importante de este spec

**El scraping NO es mayoritariamente por API**. Algunos scrapers pueden serlo, pero **la mayoría usa palabras clave**: cada scraper le manda al portal una búsqueda con términos de un **diccionario de palabras clave**, y procesa lo que ese portal devuelve.

Esto tiene tres consecuencias operativas importantes:

1. **El universo de ofertas del sistema no es "todas las ofertas argentinas"**. Es **"las ofertas que aparecen cuando buscás con estas palabras concretas en estos 6 portales"**. Es una decisión arquitectónica con consecuencias enormes para todo lo que viene después.

2. **El diccionario de palabras clave nunca se actualizó** desde que se creó. El mercado laboral cambia: profesiones nuevas, terminología nueva. Hay una brecha creciente entre lo que el sistema ve y lo que realmente pasa en el mercado, y nadie sabe cuán grande es esa brecha porque nunca se midió.

3. **No hay análisis de eficiencia palabra clave → ofertas traídas**. Probablemente hay palabras que traen miles de ofertas relevantes y otras que traen 5 ofertas por mes que son ruido. Sin esa métrica, es imposible optimizar.

### Control de cobertura — solo Bumeran lo tiene

Algunos portales publican **el total de ofertas disponibles** en su catálogo. Para **Bumeran** se implementó un control de cobertura que compara ese total contra cuántas ofertas el scraper efectivamente extrae. Es la única forma actual de saber si el scraper está agarrando "todo lo que hay" o solo una fracción.

**Para los otros 5 portales no se hizo este control**, aunque técnicamente sería posible donde los portales publiquen ese dato. Gerardo identifica esto explícitamente como deuda: **hay que homogeneizar el control de cobertura entre todos los scrapers**.

### Calidad y observabilidad del scraping

**No hay indicador de calidad del scraper.** El sistema sabe si el scraper corrió o no, pero no si lo que trajo es bueno.

**La causa más frecuente de scraping degradado son los cambios de HTML en los portales**. Cuando un portal cambia su estructura HTML, el scraper sigue corriendo pero trae datos malos o vacíos en silencio. El sistema no detecta el cambio. Gerardo lo dice textualmente: "muchas veces es lo que frena el scraping".

**Cuándo se entera Gerardo de un scraper roto**:
- A veces durante el procesamiento (algo más abajo en el pipeline rompe con el dato sucio y eso lanza el error).
- Otras veces **pasa silenciosamente** y no se descubre nunca, o se descubre tarde.

No hay garantía de que un scraper roto sea detectado en ventana razonable.

### UI de scraping

**Existe una sección especial de scraping en la UI**. Gerardo señala explícitamente que **Claude Code debe relevar esta sección en la capa 5.2** porque tiene información que vale la pena mapear: estado por scraper, métricas, configuración, lo que sea que esté implementado ahí.

**Funcionalidad de la UI conocida**:
- Tiene un botón para disparar scrapers manualmente. Pero **Gerardo no lo usa porque no le tiene confianza**. La herramienta existe pero está degradada.
- Tiene un botón para probar un scraper aislado, pero **no permite el nivel de precisión que Gerardo querría**: idealmente debería poder seguir el proceso completo (scraping → NLP → matching → dashboard) para un conjunto de ofertas o una sola. Hoy esa trazabilidad por oferta no existe.

### Campos extraídos

Lista exhaustiva de campos por portal: a relevar por Claude Code.

**Lo que sí se sabe**: **casi ningún portal trae salarios**. Esto significa que cualquier análisis del mercado laboral basado en salarios arranca cojo desde el scraping, no es problema del NLP ni del matcher. Cobertura baja por origen.

### Detección de duplicados y republicaciones

**Republicación dentro del mismo portal** (una empresa vuelve a publicar la misma oferta a los días): existe sistema implementado, **pero Gerardo desconfía del resultado**. No sabe si funciona bien. Mismo patrón que el botón de la UI: la funcionalidad está pero la confianza no.

**Republicación entre portales** (misma oferta en Bumeran y en otro portal): Gerardo no recuerda si existe control. Probablemente no, o exista parcialmente, o exista pero nadie lo usa. A confirmar en capa 5.2.

### Portales que andan bien vs portales que andan mal

**Bumeran es estable**. Lleva años funcionando, es el más antiguo, y Gerardo confía en él.

**Sobre los otros 5**: Gerardo no tiene información clara. Podría ser que ninguno tenga problemas conocidos, o que algunos tengan problemas que nadie está mirando porque no hay observabilidad. **El silencio aquí es ambiguo**.

Esto sugiere para la capa 5.2: cuando Claude Code releve los scrapers, conviene que **mire qué tiene Bumeran que los otros no** (manejo de errores, estructura, frecuencia de fallos en commits, edad de la última modificación). Bumeran puede ser el modelo a seguir, o puede que sea estable solo porque nadie lo tocó.

### Documentación interna

**No existe documentación interna del scraping**. Cómo agregar un portal nuevo, cómo arreglar uno cuando rompe, cómo probarlo localmente — todo es conocimiento que vive en la cabeza de Gerardo o que se pierde. Esto es deuda crítica especialmente considerando los 10+ portales nuevos en agenda.

### Cron del VPS

Qué dispara el cron del VPS además de los scrapers (limpieza de logs, backups, otros jobs): a relevar por Claude Code.

### Hipótesis tentativas para la capa 5.2

Articuladas en la conversación del 2026-06-05, **son hipótesis, no conclusiones**. La verificación de Claude Code tiene que confirmarlas, refutarlas o refinarlas:

1. **El diccionario de palabras clave probablemente tiene huecos significativos**. Profesiones del mercado actual que no están en el diccionario y por lo tanto sus ofertas nunca llegan al sistema. La brecha es ciega desde adentro.

2. **Es probable que la eficiencia palabra clave → ofertas sea muy desigual**. Algunas palabras pueden estar trayendo el 80% del volumen y otras estar generando ruido o nada. Sin datos, no se puede saber.

3. **Algunos scrapers de los 5 no-Bumeran probablemente estén degradados** sin que nadie lo note. Cambios de HTML que pasaron sin alerta, formatos cambiados, campos que ya no se extraen bien. Difícil saber cuántos sin auditar uno por uno.

### Notas para fases posteriores

Cosas que aparecieron en la conversación pero que **están fuera del alcance del spec S1.B.2** y se registran para que no se pierdan:

- **Trazabilidad por oferta a través del pipeline**: Gerardo querría poder seguir desde la UI todo el proceso (scraping → NLP → matching → dashboard) para una oferta o un conjunto. Es un principio de diseño que va a aparecer en la capa 5.4 pero también es input para el spec de UI (S1.B.7).

- **Crecimiento a ~16 portales**: el diseño objetivo de cualquier reparación tiene que considerar esta meta, no solo los 6 actuales.

---

> *Versión 0.1 — Capa 5.1 cerrada. Capa 5.2 (estado actual relevado por Claude Code) pendiente, próximo paso.*
