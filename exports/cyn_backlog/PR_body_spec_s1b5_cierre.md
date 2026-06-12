# docs(spec-s1b5): cierre SPEC S1.B.5 — Relevamiento de NLP

## Qué cierra

Quinto spec de la fase S1.B. Integra cuatro fuentes en la 5.1: Gerardo, Cyn, y los dos diagnósticos de mayo ("MOL en perspectiva v2" e "Informe MOL COMPLETO").

- **5.1** Memoria operativa + las discrepancias declaradas doc/código como hipótesis.
- **5.2** Estado relevado: las 5 discrepancias resueltas (versión 11.3.1, modelo 7b, schema 20/171, reglas 51, lag negativo localizado), el misterio de validation_errors resuelto, el diagnóstico estructural del colapso de sector, el inventario de acoplamiento a Qwen2.5.
- **5.3** Deuda observada (12 ítems en 7 categorías, sin priorizar).
- **5.4** Principios de diseño objetivo (7 principios).

## Hallazgos centrales

**El modelo real es qwen2.5:7b** — downgrade deliberado ("3x más rápido") decidido en código sin documentar. Los diagnósticos de mayo atribuyen los números de calidad al modelo equivocado.

**El colapso del sector es estructural**: el prompt pide el sector de la EMPRESA contra catálogo cerrado de 25 valores, pero los avisos describen el puesto. El gate ya lo detecta con 9 reglas (15.000+ marcas) y nadie consume las marcas.

**Misterio de S1.B.1 resuelto**: validation_errors (278K filas) es la telemetría del NLP Gate, creciendo sin consumidor — la instancia mayor del patrón D-15 en el proyecto.

**El inventario de acoplamiento a Qwen2.5** (5 puntos verificados) es el insumo directo de la futura capa de abstracción de modelos — la tarea que habilita la migración que detonó toda la fase.

**Patrón D-15: quinta aparición consecutiva.** Con 5 de 5 componentes, es la ley operativa del proyecto.

## Próximo paso

Sexto spec: S1.B.6 — Pipeline. Quedan Pipeline y UI antes del master S1.C.

## DEPLOY_RULES

Documento de relevamiento. Sin impacto en producción.
