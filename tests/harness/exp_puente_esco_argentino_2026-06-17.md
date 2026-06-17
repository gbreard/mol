# Experimento puente · corrida 1 (esco_argentino) — 2026-06-17

> PRUEBA DE PLOMERÍA del mecanismo + MONITOR DE REGRESIÓN. NO es veredicto sobre si las aristas corrigen errores (solo 4 de 15 false en cobertura).

**Overlay:** 44 ocupaciones, 288 aristas skill→ocupación inyectadas (peso 2.0, espejo de essential EU). 113 casos.

## 1. ¿El mecanismo de inyección funciona?

- Casos que cambian ISCO-4: **4**
- Casos que cambian ESCO-URI: **4**
- Determinismo A vs baseline congelado: CAVEAT (1 difieren)
  - `1117969136` Programa de pasantías 2025/2026 stellantis - el palomar, gran: A re-run isco4=2511 (skills_first_v3, score 0.6) ≠ baseline — desempate inestable en el semántico, no es el overlay
  - ¿alguno es de las regresiones? NO — las 4 regresiones son cambios A→B limpios

## 2. ¿Rompe alguno de los true afectables?

- True afectables (match-A en las 44): **31**
- Rotos por el overlay (bien→mal): **0**

## 3. Matriz de transición A→B (doble nivel)

**isco4** — mal→bien 0 · bien→mal 4 · bien→bien 97 · mal→mal 2 · sin esperado 10 · **ganancia neta -4**
**esco_uri** — mal→bien 0 · bien→mal 4 · bien→bien 92 · mal→mal 5 · sin esperado 12 · **ganancia neta -4**

### Regresiones isco4
- `1118025212` Representante técnico/a comercial: esperado 2431 | A=2431 → B=3322 (semantico_unico)
- `1117975249` Gerente general para maderera: esperado 1420 | A=1420 → B=1219 (semantico_unico)
- `1117925089` Project control manager: esperado 1330 | A=1330 → B=2512 (semantico_unico)
- `1118031194` Assesor comercial em português: esperado 3339 | A=3339 → B=3322 (semantico_unico)

### Regresiones esco_uri
- `1118025212` Representante técnico/a comercial: esperado 2431 | A=2431 → B=3322 (semantico_unico)
- `1117975249` Gerente general para maderera: esperado 1420 | A=1420 → B=1219 (semantico_unico)
- `1117925089` Project control manager: esperado 1330 | A=1330 → B=2512 (semantico_unico)
- `1118031194` Assesor comercial em português: esperado 3339 | A=3339 → B=3322 (semantico_unico)

## 4. Desglose por método de las que cambiaron

- semantico_unico: 4

## 5. Lupa sobre los 4 false de ganancia medible

Por caso: ¿la arista argentina estaba en la oferta (disparó)? ¿con qué fuerza cambió el score del candidato esperado? ¿la decisión la gana una regla (boost moot)?

### `1118027276` Ejecutivo de cuentas ssr/sr
- Aristas argentinas de la ocup esperada: 42 · skills de la oferta: 46 · **disparan: 6** (ARISTA PRESENTE)
- Score candidato esperado (canal skills→occ): A=0.0 → B=8.121 (Δ 8.121); rank A=None → B=0
- Canal que decide la ocupación: **regla_negocio** (río arriba del semántico → boost MOOT)
- ¿Cambió la decisión? ISCO-4=False · URI=False
- **Diagnóstico:** NO MOVIÓ aunque la arista disparó y subió el score del candidato esperado (Δ8.121, rank None→0): la decisión la gana regla_negocio, RÍO ARRIBA del semántico. El boost es MOOT, no débil.

### `1118018714` Diseñador gráfico e-commerce
- Aristas argentinas de la ocup esperada: 7 · skills de la oferta: 22 · **disparan: 0** (ARISTA AUSENTE)
- Score candidato esperado (canal skills→occ): A=3.6469 → B=3.6469 (Δ 0.0); rank A=0 → B=0
- Canal que decide la ocupación: **regla_negocio** (río arriba del semántico → boost MOOT)
- ¿Cambió la decisión? ISCO-4=False · URI=False
- **Diagnóstico:** NO MOVIÓ: la decisión la gana regla_negocio (río arriba del semántico) y además la arista no estaba.

### `2171374` Administrativa contable
- Aristas argentinas de la ocup esperada: 5 · skills de la oferta: 14 · **disparan: 1** (ARISTA PRESENTE)
- Score candidato esperado (canal skills→occ): A=2.9523 → B=4.9323 (Δ 1.98); rank A=11 → B=5
- Canal que decide la ocupación: **diccionario_argentino** (río arriba del semántico → boost MOOT)
- ¿Cambió la decisión? ISCO-4=False · URI=False
- **Diagnóstico:** NO MOVIÓ aunque la arista disparó y subió el score del candidato esperado (Δ1.98, rank 11→5): la decisión la gana diccionario_argentino, RÍO ARRIBA del semántico. El boost es MOOT, no débil.

### `1117936517` Encargado de planta/capataz
- Aristas argentinas de la ocup esperada: 2 · skills de la oferta: 21 · **disparan: 0** (ARISTA AUSENTE)
- Score candidato esperado (canal skills→occ): A=6.6785 → B=6.6785 (Δ 0.0); rank A=0 → B=0
- Canal que decide la ocupación: **diccionario_argentino** (río arriba del semántico → boost MOOT)
- ¿Cambió la decisión? ISCO-4=False · URI=False
- **Diagnóstico:** NO MOVIÓ: la decisión la gana diccionario_argentino (río arriba del semántico) y además la arista no estaba.
