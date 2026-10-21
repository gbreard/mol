# Chequeo drenaje CT — 1 semana de cron en régimen (2026-10-21)

**Tipo:** read-only. Cron local 07:00 `verificador_bajas.py --portales bumeran,zonajobs,computrabajo --regimen` (CT 1.000/día), re-agregado 14-10.

## 1. Estado actual CT (`estado_ciclo`)
| estado | n |
|---|---:|
| activa | 12.459 |
| presunta_baja | 21.383 |
| └ count=0 (sin 1ª verif) | 20.805 |
| └ **count=1 (espera 2ª verif)** | **578** |
| baja_confirmada | **550** |
| baja_no_verificada | 21.368 |

`baja_confirmada` pasó de **1 → 550** en la semana (549 confirmadas en los últimos 7d). El backlog de count=1 que estaba congelado (1.113) se drenó: 549 confirmadas, quedan 578 que se confirmarán en los próximos días.

## 2. EL DATO QUE IMPORTA — Resurrección CT con denominador real
- `→baja_confirmada` (denominador): **550**
- `baja_confirmada→activa` (resurrección): **0**
- **Resurrección CT = 0,00 %** · umbral 2 %

**→ < 2 %: la vía de verificación por búsqueda queda VALIDADA.** Ninguna de las 550 confirmadas reapareció en scraping. Cuando la vía dice "caída" (dos veces), acierta.

## 3. Ritmo y proyección — el problema real
6 corridas CT en la semana, 1.000 cola c/u = **6.000 slots procesados**, pero **solo 653 ofertas DISTINTAS avanzaron** (con `fecha_ultima_verificacion` en 7d). Es decir: la cuota se gasta re-clasificando las mismas ambiguas una y otra vez.
- Decididas reales ≈ **93/día** (549 confirmadas + 119 vivas en la semana).
- Entrada a la cola ≈ **213/día** (1.492 activa→presunta cruzando los 63d).
- **Entran más de las que se deciden → la cola no drena; el pool count=0 (20.805) no baja.**
- El backlog DECIDIBLE (los count=1 distintivos) está casi agotado. Lo que queda (count=0) es mayormente **indecidible por búsqueda** → se queda en presunta indefinidamente (límite PARCIAL-por-diseño, ya documentado).

## 4. Distribución viva/caída/ambigua (semana vs drenaje 09-10)
Agregado 6 corridas CT: viva 119, caída 566, ambigua 5.315 (de 6.000).

| | viva | caída | ambigua |
|---|---:|---:|---:|
| drenaje 09-10 | 4,5 % | 27,7 % | 67,8 % |
| **régimen esta semana** | **2,0 %** | **9,4 %** | **88,6 %** |
| última corrida sola | 0,9 % | 0,5 % | **98,6 %** |

**La ambigua subió fuerte y sigue subiendo corrida a corrida** (64 % → 98,6 %). Causa: drenado el backlog de títulos distintivos (count=1), la cola queda dominada por ofertas viejas cuyo slug de búsqueda es genérico → la vía no puede decidir.

## 5. Criterios de frenado
| criterio | umbral | medido | estado |
|---|---|---|---|
| bloqueos | — | 0 errores en todas las corridas CT | ✅ OK |
| viva alta | >15 % | máx 7,3 % (resto ≤2 %) | ✅ OK |
| resurrección | >2 % | **0,0 %** | ✅ OK |
| ambigua alta | >75 % | **86–99 % (5 de 6 corridas)** | ⚠️ SUPERADO |

El único criterio superado es ambigua>75 %. Pero ese era un guard del **drenaje**; en régimen no señala una falla de correctitud, sino que **la vía ya decidió todo lo que puede decidir** y ahora gira sobre ofertas indecidibles.

## Veredicto sobre la vía
**VALIDADA en correctitud** — resurrección 0/550 = 0 % (gate pre-registrado cumplido). No produce bajas falsas. Se mantiene el cron en régimen: es correcto y barato, y sigue cerrando los count=1 pendientes (578) + caídas frescas de títulos distintivos.

**PERO la cobertura colapsó** (ambigua ~99 %): la vía NO va a resolver el pool de ~20.8k count=0 — es el límite PARCIAL-por-diseño, ahora cuantificado. Dos cosas para decidir (no urgentes):
1. **Eficiencia:** el cron re-verifica las mismas ambiguas cada día (6.000 slots → 653 distintas). Un cooldown/skip para ofertas ya clasificadas ambigua haría que los 1.000/día apunten a count=1 + presunta fresca en vez de girar en falso.
2. **Cobertura:** ~20k CT quedan en presunta sin resolución (sin bajas falsas, pero sin decidirse). Necesitan una señal complementaria — no es trabajo de esta vía.

**Sin acción requerida.** El cron sigue como está; estas son observaciones para cuando se quiera optimizar.

---

## ADDENDUM 2026-10-21 — Cooldown de ambiguas implementado (rama `fix/cooldown-ambigua-ct`)

Medición que gatilló el cooldown (sobre `verificaciones_baja`, 7d): **flip tras ambigua = 2,1 %** (21 de 998 ambiguas re-verificadas cambiaron de veredicto). Bajo pero no cero → **cooldown 30 días** (re-chequeo mensual), NO skip permanente: solo demora ese 2,1 %, no lo pierde.

**Causa raíz del churn (encontrada al implementar):** `cola()` ordenaba `fecha_ultimo_visto ASC` y no filtraba las count=0 por timestamp; como ambigua nunca seteaba `fecha_ultima_verificacion`, las ~1.000 más viejas (ambigua-prone) se re-elegían cada día y **18.551 presuntas frescas quedaban starvadas**.

**Antes / después de "ofertas distintas avanzadas por corrida" (simulado sobre copia de la BD, sin tocar producción):**

| | cola de 1.000/día | efecto |
|---|---|---|
| **ANTES** | las mismas ~1.000 más viejas re-elegidas a diario | 6.000 slots/sem → **653 distintas** avanzaron (≈89 % re-churn de ambiguas) |
| **DESPUÉS** (cooldown poblado) | 2.253 ambiguas-recientes parqueadas 30d; la cuota fluye a **18.551 frescas** + 578 count=1 | la cola deja de girar en falso; apunta a ofertas más decidibles (nuevas, no sepultadas) |

Nota: el cooldown es *forward-looking* — las ambiguas actuales tienen timestamp NULL (el código viejo no lo seteaba), así que el efecto se puebla en el primer ciclo de re-clasificación y llega a régimen en pocos días.

Fix: `_aplicar` setea `fecha_ultima_verificacion` en ambigua; `cola()` excluye count=0 re-verificadas hasta `cooldown_ambigua_dias` (config). count=1 mantiene su gap de 72h. 8 tests nuevos + 12 de regresión (vía búsqueda) en verde. **PAUSA antes de mergear.**
