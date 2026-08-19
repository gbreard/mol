# [FRENTE H] ⛔ PARADA en P0.a.4 — clusters: el laudo es imposible tal como está escrito

**Regla aplicada:** «si algo resulta imposible tal como está escrito, PARAR y reportar»
— nada se re-decidió; esto es el reporte.

## El laudo afectado

«Clusters estáticos versionados (componentes conexas de las ~900 aristas →
`config/clusters_traductor.json`)», del que dependen: la telemetría
`familias_en_conflicto` (hubs de clusters DISTINTOS), la convergencia intra-cluster,
el sizing del P2 («cluster contable ~15 + vendedor ~10») y la activación atómica del
P4 («UN commit por cluster»).

## Lo medido (dos variantes, ambas computadas)

1. **Componentes sobre las 900 aristas literales** (hub→destino, satélites incluidos):
   **4 clusters, el mayor con 436 nodos y 82 de los 88 hubs.** Los satélites genéricos
   (empleado administrativo 3343.1, operario de producción, etc.) puentean familias
   ajenas.
2. **Variante conservadora, solo aristas hub→hub** (284 aristas; satélites como
   salidas, no miembros): **8 clusters, pero el mayor tiene 78 de los 88 hubs** —
   contable y vendedor caen en EL MISMO cluster. Los otros 7: enfermería (4 hubs) y
   6 hubs aislados.

**El puente es real y corto** (no un artefacto): `analista contable → contable →
recepcionista → vendedor` — las reglas de Cyn cross-referencian legítimamente entre
familias (la D de contable deriva a recepcionista; recepcionista deriva a vendedor).
El grafo es mundo-pequeño: hubs-pivote de alto grado (representante comercial 14,
mecánico electricista 13, electricista industrial 12, recepcionista 11, empleado de
oficina 11) conectan todo con todo.

## Por qué rompe lo congelado (mutuamente inconsistente)

- **P2**: «el piloto necesita ~25 (cluster contable ~15 + vendedor ~10)» — no existen
  esos dos clusters: es UNO de 78 hubs (~850 reglas). El sizing del piloto queda
  indefinido.
- **P4**: «UN commit por cluster: activo + reglas planas retiradas» — activar "el
  cluster contable" significaría activar 78 hubs de una vez: la antítesis del piloto
  gradual.
- **Contrato paso 3**: «hubs de clusters DISTINTOS → familias_en_conflicto» — con un
  mega-cluster, esa telemetría casi nunca dispararía; deja de discriminar lo que el
  laudo quería discriminar.

## Lo que NO se hizo

No se inventó un clustering alternativo (comunidades, cortes por grado, familias del
M1) — cualquiera de esos re-decide el laudo. `config/clusters_traductor.json` quedó
generado con la variante literal SOLO como evidencia, marcado `estado:
BLOQUEADO_PARADA_P0A4` — no debe consumirse.

## Opciones para el re-laudo (neutrales, para el hilo del harness / Gerardo)

a. **Vecindario dinámico**: "cluster" de una oferta = los hubs activados por su título
   + sus destinos-hub a 1 salto. Conserva convergencia/divergencia local; elimina el
   cluster global; P4 pasa a activación POR HUB (o por conjunto de hubs elegido a mano
   para el piloto).
b. **Clusters por familia del mapeo M1** (config existente): unidades del tamaño que
   P2/P4 asumen; el cross-family de las D se maneja como "salida a otro cluster" (¿con
   qué semántica? — a decidir).
c. **Cortar aristas de/hacia pivotes genéricos** (grado ≥ umbral) antes de componentes:
   mantiene la letra "componentes conexas" con una poda declarada — el umbral es una
   decisión nueva.
d. **Aceptar el mega-cluster** y redefinir P4 (activación por hub) + reinterpretar
   `familias_en_conflicto` (p.ej. por familia-M1 en lugar de por componente).

## Estado del resto del P0 (para no perder el día)

Puedo continuar sin tocar nada cluster-dependiente: P0.a.2 (observabilidad
`arbol_contexto` + traza), P0.a.3 (limpiezas: P-01 seco, target-muerto, keys muertas,
retiro de `técnico oficial`), P0.a.5 (auditoría de los 62 — su punto de control es
independiente), P0.a.6 (diff estático) y P0.b (conflictos y preguntas a Cyn). El P1
puede implementarse casi completo dejando el paso 3 (combinación de candidatos)
parametrizado a la resolución del re-laudo. **Espero la indicación.**
