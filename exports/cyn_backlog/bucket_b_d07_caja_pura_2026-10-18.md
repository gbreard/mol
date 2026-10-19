# [CASCADA] Bucket B para Cyn — D07: caja pura ¿5230 (cajero) o 5223.4 (vendedor)? — 2026-10-18

Surgió en el shadow del árbol sobre tareas v12.5. **La capa de equivalencia es inocente acá**: los
términos de caja matchean exacto. El efecto lo produce la **extracción más completa de v12.5**.

## La regla D07 (hub 5223.4 «vendedor»), citada textual
- **destino**: 5230.1 (cajero/cajera)
- **modo**: `evaluacion_semantica_de_prosa` (comparativo: exige que la función de caja *predomine*)
- **prosa**: «Si la función principal es recibir pagos, registrar operaciones, emitir comprobantes y efectuar la apertura, arqueo y cierre de caja»

## El mecanismo
Con tareas **v11** (lista corta, centrada en caja) D07 **dominaba** → la oferta se ruteaba a **5230 (cajero)**.
Con tareas **v12.5** (lista más completa: caja **+ atención al cliente + reposición/ventas**), la función de
caja ya **no predomina** en el comparativo → D07 **no dispara** → la oferta queda en el núcleo del hub,
**5223.4 (vendedor)**. v12.5 no inventó: extrajo además las tareas de atención/venta que el aviso tenía.

## Los 4 casos (id · título · tareas v12.5 · v11 → v12.5)

### 5664446798 — «Cajera/o multisucursal»
- **5230.1 (cajero) → 5223.4 (vendedor)**
- tareas v12.5: ["Atender al cliente", "Facturar y cobrar en diferentes medios de pago", "Realizar arqueo de caja", "Rendir cuentas diariamente", "Registrar operaciones en el sistema"]

### 5869484297 — «Cajero / auxiliar mixto, la banda del río salí»
- **5230.1 (cajero) → 5223.4 (vendedor)**
- tareas v12.5: ["realizar la atención y cobro de los productos y servicios ofrecidos por la empresa", "manejar de forma eficiente y precisa la caja registradora, asegurando el correcto conteo y registro del efectivo y los documentos de pago", "realizar el cierre diario de caja y generar los informes correspondientes", "brindar una atención al cliente amable, cortés y eficiente, ofreciendo información sobre los productos y servicios que ofrece la empresa"]

### 8924031306 — «Cajero - beccar»
- **5230.1 (cajero) → 5223.4 (vendedor)**
- tareas v12.5: ["manejar integralmente la caja", "cobrar y registrar operaciones", "controlar efectivo y medios de pago", "realizar apertura y cierre de caja", "atender a cobradores y rendiciones"]

### 1118066091 — «Cajero/a, adicionista c/ experiencia en gastronomía»
- **5230.1 (cajero) → 5223.4 (vendedor)**
- tareas v12.5: ["Atender al cliente", "Realizar adiciones", "Cobrar con diferentes medios de pago", "Manejar portales delivery", "Efectuar arqueos y cierre de caja", "Asistir en el área de cafetería"]

## La pregunta para Cyn
Cuando una caja **suma atención al cliente y/o reposición/ventas** (no es sólo recibir pagos),
¿la ocupación correcta es **5230 (cajero)** o **5223.4 (vendedor)**?

Y en consecuencia, ¿D07 debería:
- **(a)** disparar con la **sola presencia** de tareas de caja (arqueo/cobro/cierre) → vuelve a 5230; o
- **(b)** seguir exigiendo **predominio** de la función de caja (como hoy) → con tareas mixtas queda en 5223.4?

Es un cambio de **destino/umbral en tu prosa compilada (D07)** → requiere tu firma; no se toca solo.
Nota: esto NO es un bug de la capa ni del evaluador — lo surfacea que v12.5 extrae la lista completa de tareas.