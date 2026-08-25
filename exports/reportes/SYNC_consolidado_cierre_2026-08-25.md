# SYNC CONSOLIDADO v2 — Cierre (2026-08-25)

El dashboard quedó **entero en matcher 3.6.0** (destino + traza + versión): re-matching masivo del frente L + backlog NLP publicados en un solo evento, sin base híbrida. Sin recorte de A (decisión de Gerardo: la traza es parte del release).

## Ejecución

- **Lanzado** 2026-08-23 12:58 ART; el propio script esperó a horario valle y arrancó 21:00.
- **Fase ofertas:** 21:01 → ~04:45 (~7 h 45 m) — **96.928 upserts** a `ofertas_dashboard`, 970 batches de 100 con pausa 1 s.
- **Fase skills:** 04:45 → 09:00 (25.000, ~4 h 15 m) → **PAUSA automática por horario pico** → retoma 21:00 → 02:59 (restantes 34.317, ~5 h 50 m) — **59.317 ofertas con reemplazo de skills** (delete+insert por oferta, pausa 0,25 s), ~1,8M filas.
- **Cierre:** 2026-08-25 02:59:41.

**Tiempo de trabajo real ~17 h 50 m** (≈7¾ ofertas + ≈10 skills) + **12 h de pausa de valle** = ~30 h de reloj. Dentro de la ventana estimada (6-13 h de trabajo, previsto cruzar dos noches). La guarda **pausa-y-retoma** (instrucción de Gerardo) operó en vivo: pausó a las 09:00 con 25.000 skills y retomó sola a las 21:00 sin intervención.

## Calidad

- **Cero errores HTTP 4xx/5xx** en toda la corrida (monitor con filtro sobre status reales; el único "429" que apareció era el milisegundo `,429` de un timestamp, no un rate-limit). Único warning: 1 skill duplicado semántico deduplicado (comportamiento normal).
- **Spot-check 10/10** (seed 7, IDs del set que viajó): destino ESCO + método + `regla_aplicada` coinciden BD local vs `ofertas_dashboard`. Traza visible en el front (columna `regla_aplicada` poblada: R15, R33, R152, R353, dict argentino, skills_first). Ejemplos: `2182077` R15→agente centro atención; `5612077621` R353→operario logística almacén; `8283181483` R33→desarrollador software.

## Consumo de I/O — CALIBRACIÓN para syncs futuros

**Panel de Supabase leído el día después (2026-08-25):**

| Métrica | Valor | Techo |
|---|---|---|
| IOPS | 6 | 3.000 (**0,2%**) |
| Throughput de disco | — | **0,3%** del máximo |
| CPU | 1,4% | — |
| IOwait | nulo | — |
| Disco usado | 2,4 GB (**+600 MB** = esta publicación) | 8 GB |

**Contraste con el 22/08:** en el plan **Nano**, el Disk IO estaba al **100%** — ese era el presupuesto agotado que forzó el diferimiento. El upgrade a **Micro** + el goteo rate-limited dejó el consumo en ~0,2-0,3% de los techos: **presupuesto holgado por ~2 órdenes de magnitud.**

**Conclusión operativa:** los syncs futuros (K4, re-syncs) pueden **duplicar o triplicar el ritmo de batches** si la ventana de tiempo lo pide, sin riesgo de I/O. El goteo actual (~8 req/s de diseño, ~1,6 ofertas/s reales por round-trip) fue deliberadamente conservador para el primer evento grande; ya no hay razón de presupuesto para mantenerlo tan bajo. Volumen de referencia de esta corrida: ~96.928 + ~118.634 = **~215K requests** en ~18 h de trabajo.

## Estado

- `config/supabase_sync_log.json` actualizado (last_sync 2026-08-25T02:59:41, 96.928 ofertas / 59.317 skills-ofertas).
- El DATA_RELEASE puede quitar la salvedad "dashboard pre-sync" en su próxima edición: **BD local = dashboard** desde este evento.
- Backlog NLP: cerrado. Frente L: cerrado y publicado.
