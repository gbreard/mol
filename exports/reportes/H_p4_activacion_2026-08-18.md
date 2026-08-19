# [FRENTE H — P4] ACTIVACIÓN del piloto Eje 4 (2026-08-18) — GO de Gerardo, lectura (ii)

El traductor de contexto (las reglas consolidadas de Cyn) decide en el flujo real. **Modo: decide-cuando-decide + subordinación (L4). Hubs congelados solamente (7). El merge del PR es de Gerardo — con él, activo en producción.**

## 1. Lo activado

| Pieza | Estado |
|---|---|
| `config/hubs_activos.json` | 7 hubs → `activo` (fundamento: sha256 matriz v4 `6048d8ee10c03a21`, gate neta 6,7% / mejoras 57%); los 3 propuesta siguen su ciclo |
| `config/matching_config.json` | `traductor_activo: true` (+2 líneas, CRLF preservado) |
| `config/traductor_piso_satelites.json` | NUEVO: piso L2 + satélites P1 compilados a runtime (239 triggers, 164 satélites) — el grafo de exports/ queda como análisis |
| `database/match_ofertas_v3.py` | **v3.5.9 → v3.6.0**: con flag ON el orden es **diccionario → reglas L3 (preceden) → TRADUCTOR → resto de reglas (subordinación estructural) → semántico**; traza completa a `arbol_*` (migración 026) + tags en traza y `decision_razon`. Flag OFF = v3.5.x idéntico |
| Subordinación L4 | **9 reglas** marcadas `subordinada_al_traductor` (CUBIERTA del M1 con destino en territorio de los 7 hubs + **R14 pactada**; las 63 L3 quedan FUERA — preceden). **Ninguna se retira** |
| Retiro pactado del dict | los 3 CONTEXTUAL `_migra_en_piloto` (`vendedor`, `ejecutivo comercial`, `vendedor viajante`) retirados con registro en `_meta_retiros`; las **42 exclusiones de trigger vigentes sin cambios** (dict 225→222) |
| Telemetría viva | `satelite_exacto_abstencion` / `guard_1a0_bloqueo` / `excluye_venta_externa` viajan en `arbol_traza_json` y en `decision_razon` (`| piloto: …`) — el monitoreo de los riesgos anotados |

## 2. La verificación

- **Suite completa**: 228 passed / **7 preexistentes idénticos** (3 gold_v2 + m10 + 3 spec_h persist — el drift documentado desde el K). Tres tests que codificaban el estado PRE-retiro del dict se actualizaron por protocolo: señal versionada en la fixture de las 34 (caso 1118133126, la CLASE no cambia), raíz `vendedor` retirada del test S1b con nota, caso `sales executive` del G3 ahora asserta la retirada. Tests nuevos: subordinación L4 ×3 + los 28 del evaluador.
- **KPI antes/después** (en memoria, 3.000 más frescas con NLP):

| Canal | v3.5.x (antes) | v3.6.0 (después) |
|---|---|---|
| regla_plana | 53,3% | 46,1% |
| **arbol_contexto** | — | **3,7% (112)** |
| diccionario | 4,9% | 9,1% (efecto dict-primero del spec) |
| semántico | 41,8% | 41,1% |

- **Casos ejemplares** (traza término@campo): «Vendedor/a comercial» → **3322.1 por D11 de la regla 16** (detectar oportunidades + visitas comerciales en tareas — antes R111→5223.4); «Jefe/a de contabilidad y finanzas» → **1211.1.4 tesorero por D08** (flujo de caja + tesorería — antes semántico); «Vendedor técnico de mostrador» → 5223.4 por inclusión (antes semántico).
- **Smoke real (20 ofertas por `run_validated_pipeline`, persistido en BD):** 20/20 filas; 2 `arbol_contexto` con traza completa persistida (hub, regla, camino, matches con campo). **Las dos leyes del laudo verificadas en BD**: «Vendedor/a comercial» matchea R111 (subordinada) pero decidió el árbol → la subordinada NO disparó; «Vendedores de plan de ahorro» sin evidencia → el árbol se abstuvo y R111 SÍ disparó. Dict-primero visible («Administrativo contable» → diccionario).

## 3. El anexo para Cyn

`exports/cyn_backlog/anexo_preguntas_v4_2026-08-18.md`: las 4 preguntas del gate con evidencia trazable (id | título | tareas | traductor | antes): denominación «representante comercial» en regla 16, la rama de jerarquía del vecindario contable (con los 2 casos P3-género), venta-telefónica-con-cartera, y la frontera R15-vs-venta.

## 4. Registro

- El corpus histórico NO se reprocesó (re-matching masivo = spec propio, siguiente en agenda).
- learnings.yaml quedó actualizado por el PASO 8 del pipeline del smoke (conteos: 360 reglas, 222 sinónimos) — fuera del PR como siempre.
- Serie completa del frente: P0 (observabilidad+laudo clusters→hub-set) → P1 (evaluador+contrato) → P2 (léxico 107/107+gate) → P3 (shadow v1→v4, laudos H_v032/H_v033/H_v034) → **P4 (activación)**. Matrices y laudos commiteados en `exports/reportes/` y `docs/specs/`.
