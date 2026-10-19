# [CASCADA] P3 — gate de las DOS lecturas (shadow con guard) — 2026-10-18

**Veredicto honesto: la lectura de 30 intra da 7 empeora > 3 → PARAR (pre-registrado).** El
swap NO procede. Las dos lecturas y el chequeo D, abajo. La vara dual *agregada* pasa; el que
decide es el muestreo verificado, y surfacea dos patrones que hay que resolver antes del swap.

## Vara dual CON guard (shadow re-corrido, capa+guard ON)
| Eje | sin guard | **con guard** | techo | |
|---|---|---|---|---|
| Costo (decidía→abstiene) | 8,5% | **8,5%** | <10% | ✅ |
| No-explicadas RAW | 18,2% | **11,8%** | <15% | ✅ |
| No-explicadas cruza-familia | 7,2% | **6,6%** | <15% | ✅ |
| Estables (dd_igual) | 4.260 | **4.594** | — | recuperó 334 |
El guard (un redirect D sostenido por un solo concepto vía-capa exige 2º término) bajó el raw a 11,8% y eliminó el falso showroom→seguros (vuelve a 5244.1, su destino v11). Pero el gate lo decide la lectura, no el agregado.

## (1) LECTURA DE 30 INTRA (seed=42, aleatoria documentada) — **7 empeora → PARAR**
**11 mejora · 12 neutral · 7 empeora.** Expectativa pre-registrada: ≤3. **No pasa.** Los 7 en dos buckets:

**Bucket A — residual espurio de la capa (3):** destino v12.5 claramente peor, disparo vía-capa:
- `8012750041` «Vendedor digital» → *restauración* (D05 "preparar comidas" — las tareas son ventas por Instagram/WhatsApp, NO comida).
- `2175883` «Ejecutiva de cuentas» (cartera mayorista nacional) → *import/export* (D02 "asegurar" matcheó "asegurar un servicio").
- `8746914404` «Cajero/a vendedor» (gomería, mostrador+teléfono) → *teleoperador* (no es call center).

**Bucket B — D07 rutea cajero→vendedor (4):** `5664446798`, `5869484297`, `8924031306`, `1118066091` — «Cajero/a» con tareas de caja PURA (arqueo, cobro, cierre, rendir cuentas) pasan de **5230 (cajero)** a **5223.4 (vendedor)**. Para una caja pura, 5230 es más correcto → empeora contra el texto. **Causa: NO es la capa ni el guard** — los términos de D07 (`arqueo`, `cobrar`, `cierre de caja`) matchean **EXACTO**; es que la redacción más limpia de v12.5 dispara la regla **D07 de Cyn** (que rutea a vendedor) donde la redacción v11 no la activaba. **Es una pregunta de DESTINO de D07 → para Cyn** (¿caja pura va a 5230 o a 5223?). Cambio de fondo en su prosa, su firma.

Mejoras de ejemplo (11): técnico-mostrador→vendedor especializado; Mozo→restauración; admin→administrativo contable (×3, tareas contables reales); canal PAS→seguros; ventas-en-calle 4110(oficina)→rep comercial; real-estate→inmobiliario.

## (2) CHEQUEO DE DESLINDES D — sin bandera roja en lo examinado
El guard solo suprime un redirect D cuyo ÚNICO soporte es un concepto que matcheó vía-capa (raíz única). Verificado: el caso suprimido (showroom→seguros por "asegur-") era espurio → la supresión es correcta, no deshace un deslinde legítimo. El patrón cajero→vendedor (bucket B) NO lo toca el guard (términos exactos). No hay evidencia de un deslinde deliberado de Cyn deshecho por una movida intra. *(Verificación sobre la muestra + los guard-fires; una pasada exhaustiva de todos los guard-fires queda disponible si se pide.)*

## (3) LECTURA DE 20 CRUZA (seed=42) — no decide el gate, marca patrones
~6 mejora · ~11 neutral · ~3 empeora. **Patrones para anotar (frente O / regla):**
- **Consistente MEJORA**: «Ejecutivo de ventas en calle» 4110.1 (empleado de oficina) → 3322.1 (rep comercial) — v12.5 corrige un mal ruteo de v11 (×3 en la muestra).
- **Patrón a vigilar**: vendedor → 4225.1 (atención al cliente) disparado por `reclamos/reclamaciones` (`8892802868`, `6351250510`) — un término de queja re-rutea a atención al cliente. Candidato a refuerzo del guard o regla.

## (4) VARA v1.1 (versionada, para que el próximo gate no herede pase libre)
> **Vara dual v1.1 (2026-10-18):** las *no-explicadas* se miden **netas de re-ruteo intra-familia
> VERIFICADO POR MUESTRA** (lectura mejora/neutral/empeora contra el texto del aviso, muestra
> aleatoria con semilla documentada), con el criterio **empeoran ≤10% de la muestra**. NUNCA por
> la etiqueta intra/cruza sola. Si la muestra supera el 10% de empeora (o >3 de 30), el intra NO
> cuenta como explicado → PARAR. Ejes duros: costo <10%, cruza-familia <15%.

## Recomendación (PARAR)
7 de 30 > 3 → por el laudo, PARAR y re-mirar. Dos acciones antes de re-correr:
- **Bucket A (3 espurios)**: refinar el guard para los 3 disparos vía-capa restantes (D05 "preparar comidas", residual "asegurar", "reclamos"→teleoperador/atención). Son del mismo tipo que ya cazamos.
- **Bucket B (4 cajero→vendedor)**: **a Cyn** — destino de D07 para caja pura (5230 vs 5223). Es su prosa; no se toca sin su firma. (La capa es inocente acá; lo surfacea la mejor redacción de v12.5.)

El swap y el P4 esperan. Capa+guard OFF por defecto (producción intacta, 36/36 tests). Artefactos:
`CASCADA_P3_muestras_guard_2026-10-18.json`, `CASCADA_P3_shadow_equiv_2026-10-16.json`.
