# docs(spec-s1b7): cierre SPEC S1.B.7 — Relevamiento de UI — PARAGUAS S1.B COMPLETO

## Qué cierra

El séptimo y último spec de la fase S1.B. **Con este merge, el relevamiento de los 7 componentes del sistema queda completo**: BD, Scraping, Matching, Skills, NLP, Pipeline, UI.

- **5.1** El marco fábrica/locales (metáfora de Gerardo), los usuarios reales, la deuda de Cyn consolidada, los consumidores faltantes heredados de los otros seis specs.
- **5.2** Cartografía de las 118 páginas (~32 fábrica real), el bug del guardado re-diagnosticado (auto-avance de diseño, no race condition), la desconfianza de Gerardo con raíz verificada (emergentes fallan en silencio), seguridad afinada (API sin guard con PII), la tabla de consumidores faltantes (1 de 6 cerrado).
- **5.3** Deuda observada (11 ítems en 6 categorías, sin priorizar). D-08 (seguridad) registra la decisión explícita de Gerardo de converger en S1.C sin excepción.
- **5.4** Principios de diseño objetivo (7 principios).

## Hallazgos centrales

**La UI es la salida de las cadenas muertas de los otros seis specs**: casi toda su deuda consiste en NO mostrar lo que el sistema ya produce y guarda. El pedido nº1 de Cyn está a un componente de distancia de datos que ya se persisten.

**Trazabilidad (Gerardo) e historial (Cyn) son el mismo consumidor faltante** — el audit-history por oferta visto desde dos roles. Una pieza cierra los dos pedidos número uno.

**El bug del guardado no era bug**: es auto-avance intencional sin escape. La reparación es de diseño UX.

**D-15 séptima aparición** con variante propia ("producido sin pantalla") — catálogo de variantes del patrón cerrado con el paraguas.

## Próximo paso

**S1.C — Master de reparación**: cruzar las ~80 deudas de los 7 specs, tratar D-15 como deuda de proceso de primer orden, y priorizar por primera vez con el cuadro completo.

## DEPLOY_RULES

Documento de relevamiento. Sin impacto en producción.
