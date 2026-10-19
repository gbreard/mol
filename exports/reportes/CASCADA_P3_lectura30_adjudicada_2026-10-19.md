# [CASCADA] P3 — lectura de 30 intra RE-ADJUDICADA con vara v1.1 (2026-10-19)

Lista para cerrar el gate apenas Cyn laude las reglas-D. Shadow con capa+guard (seed=42,
muestra documentada). El refino de guard para "Bucket A" **no aplicó**: el diagnóstico mostró
que esos 3 no son falsos de la capa (ver abajo). Re-clasificación por CAUSA:

| Clase | n | qué es |
|---|---|---|
| **mejora** | 11 | v12.5 destino mejor (admin→contable ×3, mozo→restauración, técnico→especializado, PAS→seguros, ventas-calle 4110→3322, real-estate→inmobiliario, import/export legítimo…) |
| **neutral** | 12 | mismo grupo, re-ruteo fino sin mejor/peor claro |
| **pendiente-Cyn** | **5** | reglas-D del hub 5223.4 sobre términos GENUINOS (no la capa) → su laudo decide. **Ni mejora ni empeora hasta entonces.** |
| **empeora** | **2** | ruido de skills alucinadas v11 congeladas (no la capa, no las tareas) |

**Empeora atribuible a la cascada = 2 ≤ 3 (vara v1.1 OK), con los 5 pendiente-Cyn apartados.**

## Pendiente-Cyn (5) — se re-adjudican con su laudo, sin re-correr nada
- **D07 cajero→vendedor (4)**: 5664446798, 5869484297, 8924031306, 1118066091. v12.5 extrae caja **+ atención/ventas** → la D07 ("principalmente caja"→5230) deja de dominar → queda vendedor 5223.4. ¿Caja+atención va a 5230 o 5223.4?
- **D10 cajero→teleoperador (1)**: 8746914404. "por teléfono" genuino dispara D10 (→teleoperador) pero es venta de mostrador con atención telefónica. ¿Atención telefónica dispara teleoperador?
- Paquete: `exports/cyn_backlog/bucket_b_d07_caja_pura_2026-10-18.md` (D07 + D10).
- **Cierre instantáneo**: cuando Cyn responda, estos 5 se re-adjudican mejora/neutral/empeora y el conteo final cierra el gate SIN re-correr el shadow.

## Empeora por ruido de skills alucinadas (2) — NO es la cascada
- `8012750041` «Vendedor digital» → restauración: skill alucinada **"preparar comidas dietéticas"** (junto a "bengalí escrito", "materiales peligrosos") dispara D05. El skill es basura NLP v11 **congelada**.
- `2175883` «Ejecutiva de cuentas» → import/export: conocimiento alucinado **"licencias de importaciones y exportaciones"** (junto a "descontaminación de yacimientos") dispara D06.
- **Causa raíz**: el árbol lee los campos skills/conocimientos (NLP v11 congelado), que traen alucinaciones. **Se limpia cuando el frente O re-derive skills.** Flotan ahora porque el cambio de tareas v12.5 inclinó el comparativo. 2 casos en 30 (6,6%); se registran como residual conocido, no bloquean (bajo el techo de la vara v1.1).

## Diagnóstico: por qué el guard no "refinó" estos 3 (honesto)
El guard caza redirects-D cuyo único soporte es un concepto que matcheó **vía capa** (falso cross-dominio tipo showroom→seguros, ya corregido). Los 3 "Bucket A" NO son eso:
- #17 (teleoperador): "por teléfono" matchea **exacto** → regla-D genuina → Cyn.
- #5, #9: disparan por skills/conocimientos **alucinados** que matchean (exacto o morfología legítima) → problema de DATO congelado, no de la capa.
No hay tweak de guard que los arregle sin romper matches legítimos. El guard queda como está (showroom-type).

## Vara v1.1 (la que rige este gate)
> Las no-explicadas se miden netas de re-ruteo intra-familia **verificado por muestra**
> (mejora/neutral/empeora vs texto del aviso, semilla documentada), **empeoran ≤10% (≤3 de 30)**.
> Reglas-D sobre términos genuinos → **pendiente-laudo** (apartadas). Nunca por etiqueta sola.
> Ejes duros: costo <10%, cruza-familia <15%.

## Estado del gate
- Vara dual con guard: costo **8,5%** ✅, no-explicadas raw **11,8%** ✅, cruza **6,6%** ✅.
- 30-intra: empeora-cascada **2 ≤ 3** ✅ (vara v1.1), **5 pendiente-Cyn** apartados.
- **Gate VERDE condicional**: cierra cuando Cyn laude D07+D10 (re-adjudicación de 5, sin re-correr).
- Residual registrado: 2 por skills alucinadas → frente O.

El swap y el P4 siguen esperando: el laudo-D de Cyn sobre los 5 + tu OK. Capa+guard OFF por
defecto (producción intacta, 36/36 tests).
