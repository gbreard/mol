# SPEC S1.B.6 — Relevamiento de Pipeline

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo + consolidación de specs previos) · 2026-06-11
> Sexto spec de la fase S1.B — Relevamiento del sistema. Releva la orquestación del pipeline del proyecto MOL. Sigue la plantilla común del master v0.2.
> **Particularidad**: el pipeline es el componente orquestador. Parte de su memoria ya está capturada en los specs S1.B.1–S1.B.5; esta capa la consolida y suma las respuestas operativas de Gerardo del 2026-06-11.

---

## 5.1 Memoria operativa — Gerardo + consolidación

### Cómo se opera el pipeline hoy (la realidad, no el diseño)

**El operador del pipeline es Claude Code bajo demanda de Gerardo.** Gerardo no corre comandos directamente ni hay automatización periódica: le pide a Claude Code que ejecute el comando único, cuando puede o cuando se acuerda. Esa cadencia manual y esporádica explica la **latencia mediana de 6 días scraping→NLP** que midió el Informe de mayo — no es que el procesamiento sea lento; es que arranca tarde.

**Deseo declarado de Gerardo**: que la corrida sea **periódica y automatizada**. Es objetivo, no estado.

### El comando único — lo que ya sabemos de specs anteriores

- Orquesta NLP + matching (S1.B.1, refinado): **NO incluye la sincronización a Supabase**, que va aparte vía poller disparado desde la admin UI.
- El cron del VPS dispara los scrapers y el sync VPS→local al terminar cada corrida del scraper (S1.B.2).
- Identificación exacta de qué orquesta, en qué orden y con qué límites: a verificar en 5.2.

### La selección de qué procesar — "nunca quedó prolijo"

Respuesta textual de Gerardo sobre si el procesamiento es por lotes: **"sí y no, nunca logré que eso quede prolijo, tenemos que resolverlo"**. La selección de ofertas a procesar en cada corrida (¿todas las nuevas? ¿filtros? ¿límites?) es desprolija y Gerardo lo reconoce como deuda sin poder detallar el mecanismo. A verificar en 5.2: cómo decide realmente el comando único qué procesar.

### Reanudación tras fallo

Gerardo **cree** que el pipeline reanuda donde quedó si se corta a mitad de camino. No está seguro. A verificar en 5.2: mecanismo de checkpoint/estados, qué pasa con ofertas a medias, si quedan estados intermedios huérfanos.

### Los validadores intermedios que Gerardo no controla — el hallazgo de esta capa

Respuesta textual (P-5): hay **validadores intermedios dentro del pipeline** que Gerardo no sabe cómo funcionan — **uno después del NLP y otro después del matching**. "Son una especie de test, pero realmente no tengo control sobre ellos para ver qué están midiendo, cómo mejorarlos, qué ocupación dejar que pase."

**Hipótesis fuerte para la 5.2** (conexión con specs anteriores): el validador post-NLP es el **NLP Gate** (51 reglas, 278K marcas en `validation_errors` sin consumidor — S1.B.5 D-08); el post-matching es el **sistema de validación estructurada de SPEC W** (AutoCorrector, gates de validación). Si la hipótesis se confirma, la percepción de Gerardo ("no tengo control ni visibilidad") es exacta y ya está cuantificada: los validadores marcan y nadie consume las marcas.

### La visión de Gerardo: validación humana durante el procesamiento

Lo que Gerardo querría (textual, reformulado): que los validadores intermedios **alerten durante el procesamiento** cuando algunas ofertas están saliendo mal, que eso **se vea en la UI**, y que **Cyn pueda controlar en vivo** qué está pasando, corregir, y **volver a colocar la oferta en la cola con la corrección aplicada**.

Es una visión de *human-in-the-loop durante el procesamiento* (no después), que conecta tres deudas ya relevadas:
1. El **loop de aprendizaje roto** (S1.B.3 D-04): hoy la corrección de Cyn no vuelve al sistema; en esta visión, vuelve inmediatamente vía re-encolado.
2. La **telemetría sin consumidor** (S1.B.5 D-05/D-08): el gate ya detecta y marca; el consumidor que falta es exactamente esta alerta en vivo.
3. La **deuda de UI de Cyn** (S1.B.3 D-09): sus herramientas actuales ni siquiera muestran las correcciones pasadas, mucho menos el procesamiento en vivo.

Se registra como visión para la capa 5.4 y para S1.C — no se diseña acá.

### Hipótesis tentativas para la capa 5.2

1. **Los dos validadores intermedios son el NLP Gate y el sistema de validación de SPEC W** — identificarlos con evidencia y mapear qué hacen con las ofertas que fallan (¿bloquean, marcan y dejan pasar, descartan?).
2. **La selección de qué procesar usa estados/flags en la BD local** (algo tipo `procesado_nlp`, `procesado_matching`) con criterios acumulados poco coherentes — el "nunca quedó prolijo" de Gerardo tendría forma de flags superpuestos de épocas distintas.
3. **La reanudación funciona por estados por oferta** (si una oferta ya tiene NLP, no se reprocesa), no por checkpoint de corrida — lo que implica que un fallo a mitad de lote deja el lote parcialmente procesado sin marca de "corrida incompleta".
4. **Existió automatización que se abandonó** (candidato conocido: `launch_nlp_batch.py` roto según la lectura previa de CLAUDE.md) — instancias de D-15 esperables en orquestación.

### Notas para fases posteriores

- **Automatización periódica del pipeline**: deseo declarado de Gerardo, diseño en S1.C (requiere primero observabilidad y manejo de fallos sanos).
- **La visión human-in-the-loop con re-encolado**: input mayor para el diseño objetivo del sistema (S1.C) y para el spec de UI (S1.B.7).

---

> *Versión 0.1 — Capa 5.1 cerrada (Gerardo + consolidación de S1.B.1–S1.B.5). Capa 5.2 pendiente, próximo paso.*
