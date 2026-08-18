# [FRENTE H — v0.3.3] Los laudos P1/P2/P3 bajados + la regla de interacción — fixes, re-shadow y matriz v3

> Prerequisito: P0 (registro L3 completado con las validadas-IGUAL) y la paridad /a ya ejecutados o en curso (instrucción anterior). Esta bajada completa la vuelta. **Nada se activa — la matriz v3 es el gate.**

## P1 — Modo satélite-exacto (laudado)
Título = label COMPLETO de un satélite → **solo las D del hub proponen; la inclusión NO participa.** Ninguna D matchea → abstención (no_forzar). Racional en el contrato, textual: *el título que es label-exacto de un satélite es evidencia de primera clase de la ocupación-satélite; la inclusión capturándolo con hits débiles es semejanza-textual venciendo a evidencia.* Las D siguen pudiendo redirigir — las tareas deciden.
**Telemetría obligatoria: tag `satelite_exacto_abstencion` con el DESTINO FINAL aguas-abajo** (a qué canal cayó y qué decidió) — la v3 verifica que las abstenciones aterrizan bien y detecta satélites sin red (sin plana subordinada) antes de que duelan.

## P2 — Guard de evidencia mínima + anclas (laudado)
(a) **D redirectora con la inclusión en 0 hits necesita ≥2 hits en TÉRMINOS DISTINTOS** (términos, no ocurrencias — la misma palabra en dos tareas es una sola evidencia). 1-0 → familia_sin_rama. Racional citado: *el título que disparó el hub es evidencia implícita pro-inclusión; revertirlo exige más que una palabra suelta.*
(b) **Anclas de venta-externa al léxico desde la prosa de la regla 16** (la fuente ya lista las variantes — es compilación, con marca de siempre).
**Telemetría: tag `guard_1a0_bloqueo`** — la muestra de la v3 audita que el guard no suprime redirects verdaderos.

## La regla de interacción P1×P2 (laudada — el evaluador la necesita)
En modo satélite-exacto (inclusión N/A): **una D cuyo destino COINCIDE con el satélite del título redirige con 1 hit** (el título es la segunda evidencia — redirect confirmatorio); **una D hacia OTRO destino necesita ≥2 en términos distintos** (contradecir al título exige evidencia fuerte).

## P3 — Binario (laudado)
La rama de responsabilidad del hub contable (análisis/cierres/balances vs registración): **si sale de los marcadores de la prosa SIN interpretación del compilador → compilar en v0.3.3** con `compilacion: prosa_directa` + **tag propio en telemetría** (su efecto separable del resto). **Si exige interpretación → documentar y fase 2** (2 regresiones — el costo de esperar es chico). Reportar cuál de las dos aplicó, con la prosa citada.

## Tests testigo nuevos (además de los existentes, todos verdes)
1. «Cajero/a» + tareas mayormente venta + 1 mención de caja → la D07 (destino cajero = el satélite del título) redirige con 1 hit — confirmatorio. ✔
2. «Cajero/a» + 1 mención de RRHH (D hacia OTRO destino) → NO redirige (necesita ≥2 distintos) → abstención con tag. ✔
3. «Camarero/a» sin D matcheada → abstención (la inclusión no participa) + tag con destino aguas-abajo. ✔
4. «vendedor en calle» + "cobros" (D caja 1 hit, inclusión 0) → familia_sin_rama + tag guard_1a0. ✔
5. El mismo caso con 2 términos distintos de caja → la D redirige legítimo. ✔
6. (Si P3 entra) el caso «Contador senior» → 2411.x por la rama nueva, con su tag. ✔

## Re-shadow + matriz v3 (el gate)
1. Con v0.3.3 completo (P0 + paridad + P1 + P2 + interacción + P3-si-directa): re-shadow, baseline post-K2 (58,4/11,1/30,5).
2. **La matriz v3 reporta el EFECTO POR TAG**: cuántos casos tocó cada fix/laudo (satelite_exacto_abstencion con sus destinos, guard_1a0_bloqueo, la rama P3, y el delta de cobertura de la paridad /a como denominador nuevo declarado). El bundle conserva la atribución.
3. Muestra NUEVA estratificada de 30 (ids v1 y v2 excluidos), clasificada una por una con banderas.
4. Regresión del case-set P2 completo + todos los tests borde y testigo verdes.
5. Gate: **regresión <15% neta con las mejoras intactas → GO** (decide-cuando-decide + subordinación, hubs congelados solamente). Chat + `exports/reportes/H_p3_matriz_shadow_v3_<fecha>.md`. Nada se activa hasta el OK de Gerardo.
