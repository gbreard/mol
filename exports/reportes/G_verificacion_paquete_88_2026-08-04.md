# [FRENTE G] Verificación del paquete Cyn 88 — 2026-08-04

> Verificación de entrada del paquete (manual v3.0 + 88 reglas consolidadas + molde
> modelo_ocupacion_1.1) ANTES de que el spec del traductor lo consuma. La prosa de Cyn
> es verdad de dominio y no se cuestionó; los códigos (pasados por su copiloto
> "Juan Domingo"/ChatGPT) se verificaron todos. Branch `chore/g-verificacion-paquete-88`.
> Nada cargado a configs.

## P1 — Los 88 códigos contra el catálogo

**88/88 OK-exacto. Cero CÓDIGO-NO-EXISTE, cero LABEL-OTRO-CONCEPTO, cero que devolver
a Cyn.** Los labels del Excel son copia literal del catálogo (incluidas las formas de
género duales) — el copiloto claramente trabajó CON el catálogo a la vista. Verificación
extendida: los **212 códigos-satélite** citados dentro de la prosa como destinos de
desambiguación («corresponde a X —código—») también existen TODOS en el catálogo
(212/212). El paquete entra limpio por la puerta.

Método: existencia en `esco_occupations_metadata.json` (3.045 códigos) + label
normalizado (género /a múltiple, mayúsculas, acentos); clase leve por Jaccard de tokens.
Tabla completa por regla: en el índice máquina (P3), campo `clase`.

## P2 — Solapamiento con lo existente

**P2.1 — Contra el diccionario (225 entradas, 647 títulos-trigger extraídos):**
- 62 triggers ya están en el diccionario con el MISMO código → consolidan.
- **11 colisiones**, que se dividen en:
  - **5 conflictos reales** (código/concepto distinto — decisión de precedencia para el spec):
    1. `administrativo/a contable` + `auxiliar contable`: regla 3 → **3313.2** vs dict → ISCO 4311 (empleado de contabilidad).
    2. `vendedor/a mayorista`: regla 16 → **3322.1** (representante comercial) vs dict → ISCO 5223 (vendedor especializado).
    3. `jefe/a de mantenimiento`: regla 67 → **3115.1.6** (supervisor de mantenimiento industrial) vs dict → ISCO 1219 (director de mantenimiento).
    4. `operario/a de depósito`: regla 75 → **9333.3** (operario de logística de almacén) vs dict → mismo ISCO 9333 pero label "mozo de almacén" (conflicto de label fino — la clase del bug LIMIT-1).
    5. `técnico/a de servicio técnico industrial`: regla 78 → **3113.1.2** (ingeniero técnico en electromecánica) vs dict → **7412.3** (mecánico electricista) — el más grueso (ISCO 3 vs 7).
  - **6 aparentes**: entradas pre-G3 del dict sin `esco_code` (solo ISCO primario) donde
    el ISCO coincide con el código de la regla — no son conflicto, son granularidad
    faltante que las 88 vienen a completar.

**P2.2 — Mapa territorial de las 88** (por raíces sobre ocupación-destino + triggers):
- **RESPONDE-HUÉRFANA: 43** — el paquete ES en gran parte la respuesta al pedido de
  familias huérfanas del 14/jul: mecánico 9, contador/auditor 6, customer care 5,
  legal 5, cocina 4, **monitoreo 4**, enfermería 3, ejecutivo de ventas 2,
  recepcionista 2, mozo/camarero 2, cajero 1.
- **CONSOLIDA-EXISTENTE: 41** (técnico, operario, conducción, vendedor, ingeniero…).
- **NUEVO: 4** — coordinador de transporte (11), fisioterapeuta (43), asistente de
  dirección (44), director de centro educativo (48).

**P2.3 — Chofer/conductor: CONFIRMADO AUSENTE de las 88.** (El único match del patrón
es la regla 8, mecánico de vehículos — falso positivo léxico.) **La familia sigue
esperando su sesión.**

**P2.3b — Las 52 preguntas destino-abierto vs las 88:** 12 con TODOS sus candidatos
ahora cubiertos por regla consolidada (≈ respondidas, sujeto a que la prosa de la regla
desambigüe la disyunción — verificar al compilar), 24 parcialmente cubiertas, 16 sin
cobertura. El paquete achica la deuda de preguntas en ~un cuarto directo.

## P3 — Índice máquina

`exports/cyn_backlog/indice_reglas_consolidadas_88_2026-08-04.json`: por regla — n°,
código + clase P1, label Excel y de catálogo, URI, **títulos-trigger extraídos (647)**
y la **prosa completa textual** (jamás reescrita). Solo-lectura para el diseño del spec;
nada cargado a configs.

## P4 — Veredicto del molde (modelo_ocupacion_1.1, analista contable)

**Fidelidad: 12/12 reglas D trazan a prosa real de Cyn — cero invención del compilador.**
Trazado por tokens distintivos: D01–D12 aparecen íntegras (4-6/6 tokens) en la prosa de
la PROPIA regla 1 del Excel, que es autocontenida: Cyn embebió el mapa de fronteras
(«Si… corresponde a X —código—») dentro de cada regla consolidada.

**El hallazgo estructural de clusters — la respuesta es doble:**
1. **El compilador NO necesita clusters externos para las D**: la prosa de cada regla
   ya trae sus comparativos («principalmente», «únicamente», «predominan») con sus
   destinos-frontera. El molde compila regla-por-regla.
2. **PERO el paquete define implícitamente ~300 ocupaciones, no 88**: los 12 destinos
   de la regla 1 incluyen 8 SIN fila propia (empleado de contabilidad 4311.1, nóminas
   4313.1, asesor fiscal 2411.1.12, auditor de cuentas 2411.1.7, presupuestos 2411.1.4,
   costes 2411.1.5, analista financiero 2413.1, empleado administrativo 3343.1) —
   globalmente son **212 satélites**: ocupaciones alcanzables SOLO como salida de
   desambiguación, sin regla de inclusión propia. **El modelo del spec necesita
   representar esa asimetría** (hub con regla completa vs satélite solo-destino): un
   aviso cuyo título entra por un satélite no dispara ninguna regla — o se acepta ese
   límite o se pide a Cyn la "vuelta" de los satélites de mayor volumen.

## Para el spec (síntesis)

La fuente nueva entra verificada y limpia: 88 hubs + 212 satélites, triggers extraídos,
5 precedencias a decidir contra el diccionario, 43 huérfanas respondidas, chofer afuera,
molde fiel. El re-diseño puede arrancar sobre `indice_reglas_consolidadas_88`.
