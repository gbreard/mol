# SPEC S1C-F0.4a — Discovery de elegibilidad

> Versión 0.1 · 2026-06-12 · Fase 0 del master S1.C — Reparación
> Discovery read-only que produce los datos para diseñar el criterio único de elegibilidad (F0.4b). No diseña el criterio ni toca producción. Responde tres preguntas: el acoplamiento selección↔estados, la regla de negocio real de hoy, y el motivo de exclusión de las ~13K ofertas que nunca entraron.

## 1. Propósito

Reemplazar la decisión en abstracto por decisión informada: F0.4b (diseño del criterio único) necesita saber qué hace el sistema hoy, qué tan entrelazada está la lógica con los estados históricos, y por qué hay ofertas afuera. Este spec lo averigua sin tocar nada.

## 2. Reutilización

- BD local `database/bumeran_scraping.db` (read-only).
- `scripts/run_validated_pipeline.py` v3.3 y los módulos de selección (RunTracker, refresh_priorities, las queries de selección NLP/matching).
- Relevamiento S1.B.6 (los 4 mecanismos y 8 estados ya identificados) como punto de partida a verificar, no a asumir.

## 3. Entregables

Esta spec con la sección 8 (Hallazgos) completa: las tres preguntas respondidas con evidencia, en forma que Gerardo pueda reaccionar (reglas escritas en lenguaje claro, tabla de motivos de exclusión, veredicto de acoplamiento).

## 4. Implementación — el discovery en tres frentes

### D1 — La regla de negocio real de hoy (código + BD)
Reconstruir, leyendo el código de selección, **qué oferta entra a una corrida hoy** — la regla efectiva que resulta de combinar los 4 mecanismos.
- Trazar en `run_validated_pipeline.py` (y lo que invoque) las queries/condiciones exactas que deciden qué ofertas se toman para NLP y para matching. Transcribir los WHERE reales.
- Reconstruir la regla combinada en **lenguaje claro de negocio**, una o dos frases del tipo: "se procesa toda oferta que [condición], excepto [excepción], priorizando [criterio]". Que sea legible para alguien no técnico.
- Señalar las **contradicciones o solapamientos** entre los 4 mecanismos: ¿hay condiciones que se pisan? ¿un mecanismo puede incluir lo que otro excluye? ¿qué gana cuando hay conflicto?
- **Salida**: la regla efectiva escrita + lista de solapamientos/contradicciones.

### PUNTO DE CONTROL tras D1 — parar y reportar
Reportar a Gerardo la regla de negocio reconstruida en lenguaje claro y los solapamientos. Esta es la pieza que Gerardo necesita ver para opinar. Esperar OK antes de D2-D3.

### D2 — Acoplamiento selección ↔ estados (código)
Medir qué tan entrelazada está la lógica de selección con los 8 valores de `estado_validacion`.
- ¿Cuáles de los 4 mecanismos leen `estado_validacion`? ¿Cuáles de los 8 valores aparecen en condiciones de selección y cuáles son solo "residuo histórico" que nadie consulta?
- Para cada uno de los 8 valores: ¿algún código de selección/procesamiento lo lee hoy, o solo existe en datos? (grep de cada valor en el código).
- **Veredicto binario para F0.4b**: ¿la lógica de selección se puede unificar SIN tocar los datos históricos de `estado_validacion` (porque la selección solo mira un subconjunto), o están tan acoplados que hay que limpiarlos juntos? Con evidencia.

### D3 — Las ~13.000 excluidas, por motivo (BD)
Clasificar las ofertas que nunca entraron al procesamiento por **por qué** quedaron afuera.
- Identificar el universo: ofertas scrapeadas sin fila en `ofertas_nlp` (o el criterio real de "nunca procesada" que surja de D1). Confirmar el conteo (~13K) contra la BD.
- Clasificar por motivo de exclusión, cruzando con: portal de origen (¿son de portales sin keywords como CABA/PortalEmpleo?), fecha de scraping (¿son viejas previas a algún cambio?), presencia en `ofertas_prioridad` (¿quedaron fuera de la cola?), algún flag de exclusión deliberada.
- **Salida**: tabla "motivo de exclusión → cuántas ofertas", que permita a Gerardo decidir cuáles recuperar (bug a corregir) y cuáles son exclusión legítima.

## 5. Dependencias
- BD local (D1 parcial, D3).
- Código + git (D1, D2).
- Sin Supabase (todo el universo de selección es local).

## 6. Validación
Valida cuando D1 (regla + solapamientos), D2 (veredicto de acoplamiento) y D3 (tabla de motivos) están documentados con evidencia.

## 7. Riesgos
- **Read-only estricto**: SELECT y lectura de código/git. No reprocesar, no tocar estados, no correr el pipeline.
- No asumir los 4 mecanismos / 8 estados del relevamiento como verdad: verificarlos contra el código actual (pueden haber cambiado).
- Si el universo de "13K excluidas" no coincide con el conteo real, reportar el número real y su definición.

## 8. Hallazgos
*(Se completa al ejecutar.)*

## 9. Criterio de aceptación
TERMINADO cuando la sección 8 responde las tres preguntas con evidencia. Su consumidor es F0.4b (el diseño del criterio único), que arranca leyendo este discovery. Definición de terminado del Eje 6: el discovery tiene consumidor declarado y queda registrado.
