# [CASCADA — LAUDO 4] Deslinde de familias contables (Cyn, hoja 3, C5-C127) — spec del mini-frente

Compilado TEXTUAL de la prosa de Cyn. Es un **desambiguador COMPLEMENTARIO** del dominio contable:
"no reemplaza las reglas MOL consolidadas" (C123). Se implementa como su propio mini-frente (como
el del árbol): buckets de término por núcleo + las 7 prohibiciones como guards + REQUIERE REVISIÓN,
con su shadow/gate propio. NO se folddeó al evaluador en el cierre P3 (rule nueva = riesgo; no
gate-blocking: los movimientos contables de la lectura-30 ya son mejoras consistentes con esta regla).

## Principio (C «OBJETIVO»)
Clasificar por las **tareas efectivamente realizadas, el núcleo funcional predominante, el alcance
de la intervención y la responsabilidad atribuida** — NO por el título, antigüedad, formación, ni
palabras aisladas (facturación, conciliación, cierre, balance, análisis, impuestos). Basarse en la
evidencia de la oferta y respetar las reglas MOL consolidadas.

## Las 5 familias (textual)
- **4311.1 empleado de contabilidad**: predominan tareas AUXILIARES de emisión/tratamiento de
  facturas, NC, actualización de registros y documentación, SIN intervención más amplia. Emitir
  facturas / registrar / tratamiento documental NO demuestran responsabilidad sobre el proceso integral.
- **3313.2 administrativo contable**: núcleo = registrar y organizar operaciones, asientos, actualizar
  libros, conciliar, controlar saldos, COLABORAR en balances. El diferencial vs 4311.1 es el **alcance
  sobre el CIRCUITO contable**, no la presencia aislada de una conciliación/asiento/registro.
- **3343.1 empleado administrativo**: predominan tareas administrativas generales, gestión documental,
  comunicaciones, coordinación, apoyo de oficina, SIN núcleo contable. Trabajar en un depto contable
  NO convierte automáticamente en contable.
- **2411.1.1 analista contable**: núcleo = **evaluar e interpretar SUSTANTIVAMENTE** información
  contable/cuentas/partidas/cierres/balances para elaborar conclusiones. Conciliaciones/registraciones/
  imputaciones/cierres pueden formar parte pero NO alcanzan por sí solos. "Analizar cuentas" es
  AMBIGUO: puede ser comprobación operativa o evaluación sustantiva — no asumir el significado fuerte.
- **2411.1 contable**: núcleo = revisión/evaluación PROFESIONAL, detección de irregularidades,
  resolución de cuestiones contables/fiscales, preparación con responsabilidad. Calcular IVA/retenciones
  NO convierte en contador. La firma/certificación es evidencia relevante de autoridad pero **no es
  condición universal**.

## Criterio de decisión obligatorio (10 — las #5-#10 son los GUARDS)
1. Extraer tareas reales sin incorporar funciones de una ocupación supuesta.
2. Identificar si predomina: administrativa general / tratamiento documental / registración-control
   operativo / análisis sustantivo / responsabilidad profesional.
3. Evaluar el conjunto por función/finalidad/alcance. No por cantidad de verbos ni coincidencia de palabras.
4. Distinguir **registrar** de **analizar**, **ejecutar cierres** de **evaluar resultados**, **calcular
   impuestos** de **asumir responsabilidad profesional**.
5. **NO elevar** 4311.1 → 3313.2 por una conciliación aislada.
6. **NO elevar** 3313.2 → 2411.1.1 por mencionar cierres/balances/análisis sin alcance definido.
7. **NO elevar** a 2411.1 por calcular impuestos, registrar devengamientos, asientos o documentación fiscal.
8. **NO clasificar** por "analista/junior/semisenior/senior/contador" sin evidencia funcional.
9. Con tareas de varias familias, identificar el núcleo predominante; las demás son complementarias.
10. Sin distinción segura entre ocupaciones cercanas → conservar candidatas + **REQUIERE REVISIÓN**.
    No inventar autonomía/firma/asesoramiento/autoridad.
- **No fusionar 2411.1.1 con 2411.1** (C119).

## Sus 4 casos (adjudicación)
- **C1 «Analista contable administrativo»** (registrar/emitir facturas, cobranzas/pagos, conciliar) →
  candidata **3313.2**, verificar contra la oferta completa antes de adjudicar.
- **C2** → candidata **3313.2**, verificar contra la oferta completa.
- **C3, C4** → **REQUIERE REVISIÓN** (la abstención es la respuesta correcta).
- Validación: los movimientos contables de la lectura-30 (contador-de-título con tareas operativas →
  3313.2) son **consistentes con esta regla** → se confirman como mejora.

## Estado
Spec lista. Implementación = mini-frente propio (buckets de término núcleo + guards #5-#10 + abstención),
con shadow/gate como el del árbol. NO bloquea el cierre P3 ni el swap (complementario; las mejoras
contables ya observadas son consistentes). Fuente: `residuales_respuestas_2026-10-19.xlsx` hoja 3.
