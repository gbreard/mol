# SPEC S1.B.3 — Relevamiento de Matching

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo + Cyn) · 2026-06-05
> Tercer spec de la fase S1.B — Relevamiento del sistema. Releva el estado actual del matching del proyecto MOL. Sigue la plantilla común definida en `docs/specs/MOL_master_relevamiento.md` v0.2.
> **Novedad**: la capa 5.1 integra dos fuentes — Gerardo (memoria técnica) y Cynthia (validadora humana, experiencia de uso diaria, cuestionario respondido por escrito el 2026-06-05).

---

## 5.1 Memoria operativa — Gerardo + Cyn

### Contexto fundante: por qué existe este relevamiento

Frase textual de Gerardo (2026-06-05): **"Todo este quilombo nace porque quisimos pasar a otro modelo y nos dimos cuenta que no se puede."**

El proyecto intentó migrar de modelo y descubrió que el sistema no estaba en condiciones de soportar el cambio. De ahí nace toda la fase de setup y relevamiento. Esto define el norte del diseño objetivo final: **un sistema donde cambiar de modelo sea posible**.

### Lo que Gerardo sabe (y lo que no) del matcher

- **Versión real (3.5.4 según doc vs 3.5.5 según archivo `MATCHER_VERSION`)**: Gerardo no sabe cuál corre en producción. A verificar en capa 5.2.
- **Reglas R-XXX** (quién las crea, cuándo, cómo se mantienen): a relevar por Claude Code.
- **Regresión R240** (la regla devuelve `esco_code = None` donde el gold set espera `9329.1`, detectada en los tests del 2026-06-03): a Gerardo no le suena la regla. A investigar en capa 5.2.
- **Tabla `ofertas_matching_history`** (111.357 filas en BD local): Gerardo no recuerda qué guarda.

### El Gold Set ampliado — historia conocida, ubicación desconocida

- El Gold Set se amplió hace aproximadamente un mes (mayo 2026) durante el fine-tuning del LoRA. **El propio modelo propuso casos**, se validaron, se agregaron. Pasó de 49 casos a **más de 100**.
- **Gerardo no sabe dónde está físicamente hoy** el Gold Set ampliado (¿archivo no versionado? ¿Supabase? ¿planilla?). El archivo del repo (`database/gold_set_manual_v2.json`) sigue en 49.
- Cyn recuerda que se agregaron al menos dos ofertas específicas: **una de Sommelier y otra de Carnicero**. Estas dos sirven como trazadores para encontrar el Gold Set ampliado: donde estén esos casos, ahí está la versión ampliada.

### La experiencia de Cyn con el matching (validadora humana)

**Frecuencia de errores**: "Seguido. Me pasa bastante encontrar ocupaciones ESCO que están claramente mal asignadas."

**El patrón de error dominante**: el sistema asigna una **ocupación parecida pero no la correcta**. El mecanismo que Cyn observa: **"el sistema parece quedarse con una palabra puntual del aviso y no con el contexto completo."**

**Ejemplos concretos documentados por Cyn**:
- Aviso "Sobrestante de obra" → el sistema asignó "7111 constructor inmobiliario/constructora inmobiliaria" (incorrecto).
- Aviso "Ing. eléctrica o electromecánica" → asignó "7412 mecánico electricista/mecánica electricista" (incorrecto: confunde nivel profesional con nivel técnico/oficio).

**Tipos de ofertas que siempre fallan**: aquellas donde el título puede confundirse con otra ocupación, o donde el sistema toma una palabra puntual en lugar del contexto.

**Lo que Cyn pide que el sistema entienda** (su respuesta N-5, aplica directamente al matching): extraer mejor **la acción principal, el objeto de trabajo, el nivel del rol y el contexto del aviso**. Su ejemplo: "no es lo mismo instalar iluminación en una vivienda que instalar iluminación para shows o eventos. La acción puede parecer parecida, pero la ocupación correcta cambia según el sector y el objeto de trabajo."

### El hallazgo doble: el loop de aprendizaje no existe

Dos fuentes independientes confirman la misma deuda desde ángulos distintos:

- **Cyn (experiencia)**: "En la mayoría de los casos siento que el sistema vuelve a cometer el mismo error. Aunque una oferta se corrija manualmente, después aparecen casos parecidos con el mismo problema. Mi impresión es que la corrección manual todavía no siempre se transforma en una regla que el sistema aplique después."
- **Gerardo (técnica)**: el pipeline de feedback está **desconectado** — las correcciones de Cyn no vuelven al NLP/matcher de forma automática.

La percepción de Cyn tiene explicación técnica exacta: el sistema no aprende porque el loop no existe. Las correcciones se acumulan como issues pero no se transforman en mejoras del sistema.

### Las herramientas de validación de Cyn — deuda de UI que afecta al matching

- **Las correcciones no quedan visibles en la oferta**: cuando Cyn corrige una ocupación, la corrección se envía como issue, pero si vuelve a entrar a la oferta la ve igual que al principio. No puede hacer seguimiento ni reutilizar el criterio en casos parecidos.
- **Pedido explícito de Cyn (su cambio número uno)**: historial visible de correcciones dentro de la oferta — qué trajo el sistema, qué corrigió, qué observación dejó, cuál fue la validación final. Más estados claros por oferta (pendiente / en revisión / corregida / finalizada).
- **Bug de UX que hace perder trabajo**: al guardar una corrección, el sistema **cambia automáticamente a otra oferta**. Si Cyn no está muy atenta, la corrección queda incompleta sin que se dé cuenta. Es pérdida silenciosa de trabajo humano validado.
- **Filtros imprecisos**: muchas ofertas filtradas no corresponden al sector que Cyn está trabajando; pierde tiempo revisando ofertas que no deberían estar en el filtro.

Estas deudas son de UI (S1.B.7) pero afectan directamente la calidad y eficiencia de la validación de matching, por eso se registran acá también.

### Convergencia de principio: trazabilidad

El pedido número uno de Cyn (historial de correcciones visible) y el pedido de Gerardo registrado en el spec de Scraping (seguir una oferta a través del pipeline completo) son **el mismo principio desde dos usuarios distintos: trazabilidad**. Esto lo eleva a principio de diseño de primer orden para el sistema entero.

### Hipótesis tentativas para la capa 5.2

Son hipótesis, no conclusiones. La verificación debe confirmarlas, refutarlas o refinarlas:

1. **La regresión R240 podría ser síntoma del Gold Set desincronizado**: el archivo versionado dice 49 casos, la realidad operativa es 100+. Los tests corren contra una mezcla de expectativas viejas y nuevas. R240 podría ser una regla correcta evaluada contra una expectativa obsoleta, o viceversa.
2. **El Gold Set ampliado existe en algún lado**: Supabase (tablas de validación), archivos no versionados en el working tree, exports, planillas. Los casos "Sommelier" y "Carnicero" son los trazadores para encontrarlo.
3. **El camino del issue de Cyn termina en una tabla y no vuelve**: la corrección se guarda (probablemente en la tabla `issues` de Supabase) pero ningún proceso la transforma en regla, ajuste o entrenamiento del matcher. A verificar el camino completo.

### Notas para fases posteriores

- **Deuda de UI registrada acá pero perteneciente a S1.B.7**: correcciones no visibles, bug del cambio automático de oferta, filtros imprecisos, estados de oferta inexistentes.
- **La meta de migración de modelo** (el origen del quilombo) es el criterio de éxito final de toda la fase de reparación: cuando el sistema esté sano, cambiar de modelo debería ser posible.

---

> *Versión 0.1 — Capa 5.1 cerrada (fuentes: Gerardo + Cyn). Capa 5.2 (estado actual relevado por Claude Code) pendiente, próximo paso.*
