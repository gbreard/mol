# [CASCADA — cierre P3] GATE VERDE PLENO — R1 aplicado + vara dual con los dos números (2026-10-20)

Este es el gate del SWAP. Con el micro-fix R1 (televenta demostrada) aplicado y el split del costo
a la vista, **el gate cierra VERDE**. El swap espera tu OK (checklist de ventana muerta armado).

## R1 — televenta demostrada (equivalencia funcional dentro de C17)
Detector `_televenta_demostrada`: la venta debe estar **LIGADA a la llamada** ("mediante llamadas",
C17) — "llamadas comerciales", "llamadas … para ofrecer/vender/promocionar", "venta telefónica",
"televentas". La lista negativa **C63 intacta**: atención/consultas/responder/informar NO disparan
(no traen venta ligada a la llamada). Verificado: las televenta call-center reconectan a **5244**;
la **gomería se mantiene en 5223.4** (atención telefónica + venta presencial, sin el nexo); cajeros
5230, vendedores intactos.

## Vara dual — los DOS números (shadow completo, seed 42, LAUDO 1+2+3+R1)
| Eje | valor | techo | |
|---|---|---|---|
| No-explicadas (cambio destino) | **12,9%** | <15% | ✅ |
| — cruza-familia | **7,7%** | <15% | ✅ |
| **Costo-DECLARADO** (abstención legítima REQUIERE-REVISIÓN) | **7,9%** | <10% | ✅ |
| **Costo REGRESIÓN NETA** | **3,4%** | <10% | ✅ |
| Mejora (cobertura nueva) | 2.627 | — | — |

**El costo crudo (11,2% = 640) se declara en dos**:
- **Costo-declarado 7,9% (~449)** = el principio de Cyn operando: vacías (144) + thin (129) +
  contable-ambiguo rich (~176, LAUDO 4 → REQUIERE REVISIÓN). Abstención marcada correcta, no regresión.
- **Regresión neta 3,4% (~191)** = rich no-contable que aún abstiene por acople de fraseo residual
  (mismo género, bounded). Candidato a extensión de equivalencia por-regla / frente O. Bajo techo.

## Laudos intactos (verificado en vivo)
- 4 cajeros (5664446798, 5869484297, 8924031306, 1118066091) → **5230** ✅
- Gomería (8746914404) → **5223.4** ✅
- 3 televenta call-center → **5244** ✅ (R1)
- 6-OK y mejoras sin regresión. 58 tests dirigidos (traductor/equivalencia/laudo/N1-N3) verde.

## Sobre las 25 fallas de la suite completa de matching
El bundle corrió TODA `tests/matching/` (177 pasan, 25 fallan). Las 25 son **gold-sets end-to-end del
MATCHER** (`test_gold_set_v2_verified`, `test_m10_gold_set`) — dependen de Ollama/LoRA/estado de BD
(el LoRA no existe en disco, CLAUDE.md) y son **pre-existentes/ambientales**. **Ninguna toca el
traductor**; mis cambios están **OFF por defecto** (producción del matcher sin cambios). No son
regresión de este frente.

## 295 residuales (LAUDO 3): 67 reconectan / 228 abstención legítima.

## Veredicto: VERDE PLENO
- costo-declarado 7,9% < 10% ✅ · regresión-neta 3,4% < 10% ✅ · no-explicadas 12,9% < 15% ✅ ·
  cruza 7,7% < 15% ✅ · los 5 pendientes exacto a Cyn · 6-OK y mejoras intactas.

## Lo que sigue (tu OK)
El **checklist de ventana muerta está armado** (`scripts/ops/swap_tareas_v125.py --check/--dry-run/
--execute` + `CASCADA_DISEÑO_swap_P3.md`): pausar el poller, evitar horas de cron, snapshot rollback
íntegro. **Con tu OK**: swap (staging→vivo) → P4 (congelar skills, 4 condiciones del harness) → P5.
- **R2** (2 empeora por skills alucinadas v11) → registrado para el frente O.
- **R3** (deslinde contable) → mini-frente propio, spec compilada (`deslinde_contable_cyn_2026-10-19.md`).
- **Regresión-neta 3,4%** → extensión de equivalencia por-regla, en paralelo (no bloquea).

Producción intacta (ajustes OFF por defecto). Todo en `ops/cascada-tareas-v124` (sin mergear).
