# Re-laudo — Harness → Hilo del sistema: la parada de clusters (P0.a.4)

> **Fecha:** 2026-08-06 · **Asunto:** re-laudo de la condición de clusters estáticos (era del harness, cae refutada por el grafo real) y respuesta a las tres preguntas. **Veredicto: (a) con la elaboración hub-set, RE-LAUDADO — con dos precisiones que completan el contrato.** La parada se levanta.

---

## 0. El reconocimiento previo

La condición de clusters estáticos era del harness y **el grafo la refutó**: era andamiaje para una distinción (parientes vs extraños) que el material de Cyn no tiene — 78/88 hubs conectados, y los puentes son criterio experto, no ruido. Tercera hipótesis del harness que cae ante la medición; así debe funcionar. La parada de Claude Code sin inventar clustering fue el comportamiento correcto, y el análisis de las 4 opciones del sistema es impecable — en particular el rechazo de (c): **podar aristas de la experta por conveniencia de grafo viola el principio más viejo del proyecto.** Ese rechazo queda como precedente citable.

## 1. RE-LAUDO: (a) vecindario dinámico + hub-set declarado + activo-gobierna-trigger — SÍ

Las tres piezas de la elaboración quedan laudadas tal como están propuestas:
- **Vecindario dinámico**: la combinación es local a los hubs que la oferta activó (convergen → decide · divergen → no-forzar). Es la semántica del cruce 4 menos una precondición vacua.
- **Activación por hub-set declarado** (`config/hubs_activos.json`, versionado): un commit = un hub-set + sus reglas planas cubiertas retiradas. Atomicidad intacta; el "cluster" siempre fue proxy de "conjunto que se activa junto" — ahora se declara en vez de derivarse.
- **ACTIVO gobierna el TRIGGER, no el DESTINO**: los títulos del hub-set disparan; las D redirigen a cualquier código verificado sin que el destino necesite estar activo. Crecimiento por decisión, no por contagio. Es la pieza elegante — sin ella, activar contable exigía activar 78.

**Precisión 1 — lo que cambia de outcome, dicho explícito (para que el spec no lo herede en silencio):** el contrato viejo tenía "hubs de clusters distintos → no_forzar SIN EVALUAR". Ese atajo desaparece: ahora TODOS los hubs activados se evalúan, y si exactamente uno satisface, DECIDE — donde antes se rehusaba a ciegas. Esto es mejora, no riesgo: es resolución basada en evidencia (lo que la experta haría), y los casos genuinamente mixtos siguen cayendo a no-forzar por empate/divergencia. Las guardas que lo contienen ya existen: términos validados por hub, empate-no-decide, validada_por_casos como gate. **Consecuencia en tests:** el caso-borde 8 se reformula — "dos hubs sin relación activados: solo uno satisface → decide (con traza de ambos) · ambos satisfacen con destinos distintos → evidencia_mixta". Los 12 tests quedan en 12, con el 8 nuevo.

## 2. Telemetría (pregunta 2): unificada en runtime + anotación derivada en el análisis

`evidencia_mixta` unificada con traza de qué-hubs-y-qué-destinos: **alcanza para el runtime.** Pero la distinción que la categoría vieja pretendía dar NO se tira — se muda a donde vale: **anotación offline en la clasificación de divergencias del shadow**, computada del grafo-como-dato:
- Divergencia entre hubs **con arista directa** → las condiciones D del puente no discriminaron → el fix es refinar esa D (trabajo de compilación/Cyn).
- Divergencia entre hubs **sin arista** → colisión de triggers entre dominios → el fix es el trigger (títulos compartidos, auditoría tipo los-62).
Son fallas distintas con arreglos distintos — la anotación las separa gratis en el análisis, sin categoría de runtime que no parte nada. El grafo queda commiteado como dato de diagnóstico (y para el piso de satélites), como propone la nota.

## 3. El hub-set del piloto (pregunta 3): la lista propuesta, no más chica

**Grupo contable del Excel + vecinos directos que el P2 compile (~15) + grupo vendedor (51/52/16, ~10).** No arrancar más chico: el piloto existe para estresar la mecánica de convergencia multi-hub — con solo 2 hubs activos casi no habría solapamiento de triggers y el mecanismo central quedaría sin probar. La lista propuesta prueba: convergencia intra-grupo (analista→administrativo contable), redirección a destino-no-activo (las D que salen del grupo), y la convivencia con el diccionario (vendedor). Es exactamente el estrés que P4 necesita haber pasado antes de la fase 5.

## 4. Ajustes menores derivados (para que el spec los absorba sin re-cruce)

- `config/clusters_traductor.json` → **`config/hubs_activos.json`** + el grafo commiteado como artefacto de análisis (no config de runtime).
- El "diff estático de destinos por familia solapada" (cruce 4) cambia su unidad de comparación de cluster a **hub-set/grupo** — mismo contenido, otro nombre.
- Para la adenda del índice cuando el piloto cierre, la lección de método queda registrada así: *una estructura estática derivada del material experto debe validarse contra el grafo real ANTES de volverse precondición de runtime* — la condición de clusters se congeló en el cruce sin ese paso, y costó una parada (barata, gracias al freno correcto del spec).

## 5. La parada se levanta

Con este re-laudo: P0.a.4 se resuelve como hub-set + grafo-como-dato, el sizing del P2 queda restaurado (~25), el test 8 se reformula, y el H sigue sin nada bloqueado. Todo lo demás congelado sigue congelado.

> Vía Gerardo como bus.
