# Conteos 8 — Fallback isco_familia

**Fecha:** 2026-05-05
**Pipeline activo:** No (verificado: ningún proceso `python.*pipeline|matching|nlp_from_db` en ejecución; sin logs vivos en `/tmp`).
**Tiempo total:** ~45 min
**Modo:** READ-ONLY estricto. SQLite con `?mode=ro`. No se ejecutó el matcher.
**Output:** este archivo. (`/mnt/user-data/outputs/` no accesible — mismo blocker reportes anteriores.)

---

## TL;DR

- **Universo real: 1.064 ofertas** (no 1.060). 100% URI vacía. Distribución por entrada: analista 357, gerente 302, operario 156, operador 145, técnico 104.
- **Las 5 entradas isco_familia NO asignan ISCO de familia genérico**: usan diccionario `contextos` (24 contextos en total) que mapea a ISCOs específicos (ej: `gerente.ventas|comercial → 1221`, `gerente.it|sistemas|tecnologia → 1330`). El bug es que devuelven label e ISCO específicos pero **no devuelven URI** (causa raíz documentada en conteos_7).
- **Cobertura por reglas (simulación estática)**: rango 6,1% – 79,2%. La estimación más probable está en torno a **79,2% (843/1.064)** pero **no se puede confirmar sin ejecutar el matcher** (54 reglas tienen condiciones NLP/tareas que la simulación no evalúa fielmente). **221 ofertas (20,8%) caerían sí o sí al semántico.**
- **Cobertura por entrada es muy desigual**: analista 100%, operario 100%, técnico 99%, **gerente 70% (91 al semántico)**, **operador 11% (129 al semántico)**. Las entradas `operador` y `gerente` son las que más dependerían del semántico.
- **C3 NO está restaurado**: `database/embeddings/esco_occupations_embeddings.npy` no existe en raíz. `_semantic_match_title()` devuelve `[]`. Pero `skills_first_v3` funciona sin él (vía `skills_matcher.match()`), y 99,87% de las ofertas con ese método tienen URI poblada hoy.
- **Riesgo principal de Opción 1**: aun si la cobertura es alta, las reglas asignan **ISCOs distintos al actual** en 719/843 casos (85% de las cubiertas). El "actual" es el que pone isco_familia, que ya está validado en BD (estado_validacion=validado o validado_claude para las 1.064). Quitar isco_familia significaría re-clasificar en masa.
- **Recomendación basada en datos**: **Opción 3 (URI por contexto)** es de menor riesgo. Mantiene clasificaciones actuales, solo agrega URI faltante. **Opción 1 (quitar) es disruptiva**: cambiaría 719+ ISCOs y dejaría 221 al semántico (con calidad incierta para "operador telefónico" y "manager" anglicismo).

---

## A — Identificación

### A1. Universo afectado

```
diccionario_argentino_analista         357
diccionario_argentino_gerente          302
diccionario_argentino_operario         156
diccionario_argentino_operador         145
diccionario_argentino_tecnico          104
TOTAL                                 1064
```

URIs vacías: **1.064 / 1.064 (100%)**. Confirma 100% bug determinístico.

> Nota: el prompt asumía 1.060. La cifra real en BD a hoy es **1.064** (4 más, sin impacto en conclusiones). Diferencia probable: ofertas nuevas matched desde la última cuantificación.

### A2. ISCO actual asignado

Las 5 entradas **NO usan ISCO de familia genérico**. Cada una tiene un sub-diccionario `contextos` que mapea regex de palabras clave → ISCO específico. Resultado:

```
analista (357):
  2511 (analista TIC)              140
  2423 (selección personal)         70
  2413 (financiero)                 67
  2431 (especialista publicidad)    40
  2411 (contable)                   28
  4312 (tesorería)                   6
  3312 (créditos/riesgos)            4
  2421 (funcional/negocios)          2

gerente (302):
  1330 (TIC)                       122
  1211 (finanzas)                   84
  1324 (logística/supply chain)     28
  1321 (operaciones/planta)         24
  1212 (RRHH)                       24
  1221 (ventas/comercial)           19
  4110 (admin oficinista)            1

operario (156):
  9333 (almacén)                    79
  8160 (producción/planta)          72
  8142 (plástico inyección)          4
  8131 (empaque)                     1

operador (145):
  4222 (call center / atención)     81
  9333 (almacén/logística)          30
  8211 (máquinas CNC)               22
  8160 (producción/planta)          12

tecnico (104):
  7233 (mant industrial)            38
  3111 (laboratorio químico)        24
  3512 (TIC support)                22
  7127 (refrigeración/aire)         12
  7421 (electrónica)                 7
  3257 (seguridad/higiene)           1
```

**Implicación para Opción 1**: si se quitan las 5 entradas, 1.064 ofertas pierden estos ISCOs específicos por contexto. Para preservar la clasificación actual con URI poblada, **Opción 3 necesita agregar URI por cada combinación (key, contexto) — no a nivel raíz**.

### A3. Sample de títulos (6 por entrada)

```
gerente:
  Gerente de Administración y Finanzas        → ISCO 1211 → "director financiero/directora..."
  Arquitecto/a Director de Obra               → ISCO 1330 → "director de tecnología/directora..."  ⚠️ MAL CLASIFICADO
  Arquitecto o Ingeniero Civil para DIRECTOR DE OBRA → ISCO 1330 ⚠️ debería ser 1323

analista:
  Analista administrativo contable            → ISCO 2411 → "contable"
  Analista Sr. de Sueldos Beneficios y ADP    → ISCO 2423 → "consultor de selección..."
  Analista de Datos Transporte y Logística    → ISCO 2511 → "analista de sistemas TIC"
  Analista de Datos Jr.                       → ISCO 2511
  Analista de sistemas                        → ISCO 2511
  Analista de Certificaciones de Calidad      → ISCO 2511 ⚠️ probablemente debería ser 2141 calidad

operario:
  Operario de Producción de Alimentos         → ISCO 8160 → "hornero de panadería..." ⚠️
  Operario/a de Deposito                      → ISCO 9333 → "operador de carretilla..."
  Operario de Embalaje y Depósito             → ISCO 9333
  Operario de Estacionamiento                 → ISCO 9333

operador:
  Analista Comercial para Importante Operador Logístico → ISCO 9333 ⚠️ MAL: el título es "Analista Comercial"
  Ayudante de Almacenes - Operadora de Gas    → ISCO 9333 ⚠️ MAL: el título es "Ayudante de Almacenes"
  Operador de atenciòn al paciente/cliente    → ISCO 4222
  Operador Telefónico Servicio de Emergencias → ISCO 4222
  OPERADOR DE MAQUINAS CHILLER                → ISCO 8211 → "montador de vehículos..." ⚠️ MAL

tecnico:
  PERSONAL TECNICO para BLINDAJE DE AUTOS     → ISCO 3257 → "inspector seguridad e higiene" ⚠️ MAL
  TECNICO ELECTRONICO INSTALADOR              → ISCO 7421
  Soporte Tecnico / IT Support                → ISCO 3512
  Tecnico Quimico                             → ISCO 3111
```

**Observación cualitativa**: incluso con isco_familia el matching no es perfecto. Hay errores conceptuales (Arquitecto Director de Obra clasificado como TIC, Operador Logístico que es Analista Comercial). Esto debilita la afirmación de "Opción 3 mantiene clasificaciones validadas" — algunas clasificaciones están objetivamente mal.

---

## B — Cobertura de reglas de negocio

### B1. Reglas relevantes en el JSON

- **Total reglas activas**: 354 (de 358 totales).
- **Solo con condiciones de título** (alta confianza para simulación estática): 300.
- **Con condiciones NLP/tareas/área/sector** (no evaluables sin BD NLP completa): 54.
- **Reglas que mencionan algún keyword (gerente/manager/director/analista/operario/operador/tecnico/técnico)**: 195.

### B2. Match conceptual al sample completo (n=1.064)

**Limitación importante**: la simulación es estática. Aplicó las reglas en orden de prioridad, evaluando solo `titulo_contiene_alguno`, `titulo_contiene_alguno_2` (AND con la primera), `titulo_contiene_todos`, `titulo_no_contiene_alguno` y `titulo_o_tareas_contiene_alguno` (aproximado solo con título). **No evaluó condiciones NLP** (`area_funcional_es`, `nlp_seniority_es`, etc.).

**Resultado V2 (todas las reglas, condiciones NLP no evaluadas → contadas como verdaderas)**:

| Métrica                       | Valor               |
|-------------------------------|---------------------|
| Cubiertas por reglas          | **843 / 1.064 = 79,2%** |
| Caen al semántico             | **221 / 1.064 = 20,8%** |

**Resultado V3 (banda con confianza alta vs aproximada)**:

| Categoría                                | n     | %     |
|------------------------------------------|-------|-------|
| Alta confianza (regla solo de título)    | 65    | 6,1%  |
| Aproximada (regla con cond NLP no eval)  | 778   | 73,1% |
| Sin regla                                | 221   | 20,8% |

→ **La cobertura real está en la banda [6,1% – 79,2%]**. La cifra más representativa es **~79,2%** porque la mayoría de las reglas con condiciones NLP también tienen condiciones de título estrictas; cuando el título matchea, las cond NLP suelen también validar (no se confirma sin ejecutar).

### Cobertura por entrada del diccionario

```
diccionario_argentino_analista       357 │ cubre=357 (100,0%) │ semántico=  0
diccionario_argentino_operario       156 │ cubre=156 (100,0%) │ semántico=  0
diccionario_argentino_tecnico        104 │ cubre=103 ( 99,0%) │ semántico=  1
diccionario_argentino_gerente        302 │ cubre=211 ( 69,9%) │ semántico= 91
diccionario_argentino_operador       145 │ cubre= 16 ( 11,0%) │ semántico=129
```

**Asimetría crítica**: las entradas `analista`/`operario`/`tecnico` están casi totalmente cubiertas por reglas; **`operador` solo 11% — 129 ofertas caerían al semántico**. `gerente` queda en una zona intermedia (70%).

### B3. Top reglas que cubrirían (V2)

```
R238_analista_it                ISCO=2511  (268)  ← analista IT
R348_operario_plastico_soplado  ISCO=8142  (152)  ← operario plástico (sospechoso de over-match)
R4_nivel_gerencial              ISCO=?     (149)  ← regla con nlp_seniority+gente_cargo
R241_tecnico_it                 ISCO=3512  ( 87)  ← técnico IT
R239_analista_operaciones       ISCO=2421  ( 81)  ← analista operaciones
R303_gerente_admin              ISCO=1211  ( 42)  ← gerente admin
R180_soporte_infraestructura    ISCO=2522  ( 23)
R45_IT_analista_sap             ISCO=2511  ( 10)
R275_operario_deposito_almacen  ISCO=9333  (  5)
R171_logistica_entregas         ISCO=8322  (  4)
R125_gerente_finanzas           ISCO=1211  (  3)
R322_mecanico_industrial        ISCO=7233  (  3)
```

**Sospecha de over-match (revisión necesaria si se aplica Opción 1)**:
- `R348_operario_plastico_soplado` matchea 152 ofertas pero requiere keyword "operario" + título-o-tareas "soplado/inyección/etc". La simulación contó solo el título; el matcher real revisa también tareas → muchas de las 152 podrían NO matchear realmente.
- `R238_analista_it` matchea 268 pero requiere `area_funcional_es=Tecnología` además de "analista" en título. La simulación no evaluó área. Probablemente sub-set real más pequeño.

**ISCO de regla vs ISCO actual**: solo 124/843 (14,7%) coinciden. Las otras 719 (85,3%) cambiarían de ISCO. El "actual" puede ser correcto o incorrecto (ver A3).

### B4. Patrones recurrentes en las 221 sin cobertura

**Por entrada**:
- 129 operador (87% del backlog)
- 91 gerente (anglicismos)
- 1 técnico

**Top bigrams en títulos sin cobertura**:
```
operador telefonico         (33)  → debería ir a ISCO 4222
operadores telefonicos      (16)  → ISCO 4222
telefonicos ventas          (14)  → híbrido call center / ventas
ventas productos            (14)
productos bancarios         (14)  → call center bancario
engineering manager         ( 5)
operador maritimo           ( 5)
operador planta             ( 5)
marketing manager           ( 4)
```

**Patrones reconocibles sin regla actual**:
1. **Operador telefónico / Call center** (~50): no hay regla específica. Existe R15_customer_care y R155_asesor_telefonico que ya cubren parcialmente, pero no estos casos exactos. Skills extraídas (ej: "comunicarse por teléfono", "transferir llamadas") apuntan a 4222.
2. **Manager (anglicismo)** (~80): Office Manager, People Manager, Project Manager Senior, Engineering Manager. Existen R19_project_manager, R30_community_manager, R152_ecommerce_manager pero no cubren genéricos.
3. **Operador marítimo / Operador planta** (~10): industriales específicos.

→ Estos patrones podrían ameritar reglas nuevas si se aplica Opción 1.

---

## C — Comportamiento esperado del semántico

### C1. Estado del semántico hoy

**C3 NO está restaurado.** El archivo esperado por el matcher:

```
database/match_ofertas_v3.py:150
  emb_path = base_path / "embeddings" / "esco_occupations_embeddings.npy"
```

Estado en disco:
```
database/embeddings/esco_occupations_embeddings.npy        ❌ NO EXISTE
database/embeddings/esco_occupations_metadata.json         ❌ NO EXISTE
database/embeddings/enriched/esco_occupations_embeddings.npy   ✓ existe (12 MB)
database/embeddings/baselines/esco_occupations_embeddings_baseline.npy  ✓ existe
```

**Consecuencia en el matcher**:
- `_load_occupation_embeddings()` → `self.occ_embeddings = None`, `self.occ_metadata = []`.
- `_semantic_match_title(titulo)` → return `[]` por early-return en línea 1288.
- `code_to_occupation` queda vacío (loop sobre `self.occ_metadata or []`).

**Pero `skills_first_v3` SÍ funciona sin C3**: usa `skills_matcher.match(skills_extracted)` que opera sobre `esco_skills_embeddings_full.npy` (existe) y un mapeo skill→ocupación. Resultados:
- 14.673 ofertas con `skills_first_v3` hoy. URIs pobladas: **14.673 / 14.673 (100%)**.
- 1.098 ofertas con `semantic_fallback_v3`. URIs pobladas: **1.098 / 1.098 (100%)**.

→ Si las 221 caen al semántico, irían a `skills_first_v3` (siempre que `candidates_by_skills` esté no-vacío).

### C2. Skills de las 221 sin cobertura

- **194 / 195 tienen `skills_oferta_json` poblado** (>= 1 skill extraída).
- Sin embargo, `skills_matcheados_esco = 0` para las 1.064 (incluyendo las 221). **Pero esto NO es información sobre cómo se comportaría el matcher**: el path `diccionario_argentino_*` no ejecuta el matching contra ESCO skills, así que ese 0 refleja la rama tomada, no la calidad del matching potencial.

**Sample de skills (titulos sin cobertura)**:

```
"Operador Telefónico Servicio de Emergencias"
  skills: ["responder a las llamadas", "comunicarse por teléfono", 
           "transferir llamadas", "registrar electróni..."]
  → skills concentradas, deberían resolver a ISCO 4222

"Senior People Manager - Latam"
  skills: ["liderar a otras personas", "gestionar equipos de ventas", 
           "gestionar procesos", "gestión del personal..."]
  → genéricas, podrían resolver a director comercial (1221) o gestor (1349/1213)

"Senior Manager, FP&A and Treasury"
  skills: ["liderar a otras personas", "gestionar equipos de ventas", 
           "conservar ejemplares de discos", "proce..."]  ⚠️ "conservar discos" sugiere ruido
  → mezcla, podría caer en cualquier nivel directivo

"OPERADOR DE MAQUINAS CHILLER"
  skills: ["mantener equipos de almacenamiento de agua", 
           "mantener equipos de distribución de agua"]
  → coherente con técnico mantenimiento, no con call center

"Operadores de Atención Telefónica - part time"
  skills: ["garantizar la satisfacción del cliente", "telemarketing", 
           "ofrecer un servicio excelente", "comuni..."]
  → claramente 4222 / 5244
```

**Variabilidad**: las skills tienen calidad mixta. Para "operador telefónico" están concentradas (alta probabilidad de matchear 4222). Para "Manager" anglicismo son genéricas (riesgo de matcheo arbitrario). Para "Senior Manager FP&A" hay ruido ("conservar ejemplares de discos") que podría desviar el matcher.

### C3. Casos donde el semántico históricamente falla

**No se puede medir directamente**: la columna `validacion_humana` no existe en `ofertas_esco_matching` (verificado vía PRAGMA). Sí existen `estado_validacion`, `validado_por`, `notas_revision`, `requiere_revision`.

**Estado de las 1.064**:
- 604 con `estado_validacion = 'validado_claude'`
- 460 con `estado_validacion = 'validado'`
- 0 con `requiere_revision = 1`
- 0 con `notas_revision` no vacía

→ **Las 1.064 ya están validadas en BD a pesar del bug de URI vacía.** Esto es relevante: cualquier cambio (Opción 1 u Opción 3) reabre clasificaciones validadas.

**Análogo de comportamiento del semántico en ofertas similares**:

Para "operador telef%" en otras ofertas (no afectadas por isco_familia.operador):
```
diccionario_argentino_operador → ISCO=4222 ( 41) ← bug propio (las otras del bug)
regla_negocio_R15_customer_care → ISCO=4222 (  3)
regla_negocio_R155_asesor_telefonico → ISCO=4222 (  1)
regla_negocio_R173_gestor_cobranzas → ISCO=4214 (  1)
semantic_fallback_v3 → ISCO=4214 cobrador deudas (  1)  ← caso semántico real
```

Para "manager" (excluyendo dict.gerente y R152):
```
regla_negocio_R30_community_manager → ISCO=2432 (178)
regla_negocio_R19b_project_manager_it → ISCO=1330 ( 78)
regla_negocio_R19_project_manager → ISCO=1213 ( 73)
skills_first_v3 → ISCO=1221 director comercial ( 34)  ← caso semántico
skills_first_v3 → ISCO=1221 responsable de marketing ( 34)
```

→ Para títulos genéricos con "manager" el semántico tiende a `1221 director comercial` o `responsable marketing`. Para call center con título coherente, el semántico (1 caso) cayó en `4214 cobrador de deudas` en lugar de `4222 call center`. Riesgo bajo pero real.

---

## D — Comparativo de estrategias

### D1. Tabla de impacto estimado

| Estrategia | Cubiertas reglas | Caen al semántico | Manten ISCO actual | URIs vacías esperadas |
|---|---:|---:|---:|---:|
| **Hoy** (con isco_familia) | 0 | 0 | 1.064 (con bug) | 1.064 |
| **Opción 1** (quitar 5 entradas) | ~843 (ver banda 6,1%-79,2%) | ~221 | ~124 (14,7%) | 0 si semántico funciona; 0-221 si falla |
| **Opción 3** (URI por contexto) | 1.064 (mantenidas) | 0 | 1.064 (con clasificaciones actuales) | 0 |

### D2. Riesgo cualitativo

**Opción 1 (quitar las 5 entradas)**:
- ✅ Menos código en JSON; centralización en reglas/semántico.
- ❌ **719 ofertas (85% de las cubiertas) cambiarían de ISCO**. Disruptivo. Algunas migrarían a ISCO más correcto, otras a ISCOs claramente incorrectos por sobre-match (ej: R348 operario plástico capturando "Operario producción alimentos").
- ❌ **221 ofertas dependen del semántico**. Para "operador telefónico" (50+) deberían resolver a 4222 con skills, pero el único precedente real (semantic_fallback_v3) cayó en 4214 cobrador. Riesgo medio.
- ❌ **C3 NO está restaurado**. Aunque skills_first_v3 funciona, sin embeddings de ocupación el semántico está degradado. Impacto incierto para títulos cortos sin skills ricas.
- ❌ **Reabre 1.064 ofertas validadas**. Habría que re-validar.

**Opción 3 (agregar URI por contexto)**:
- ✅ **Mantiene 1.064 clasificaciones actuales** (incluyendo las que están objetivamente mal — ver A3).
- ✅ **Cero impacto en validaciones existentes**.
- ✅ **No depende de C3**.
- ❌ **Requiere agregar URI a cada combinación (key, contexto)**: 24 contextos en total (7 gerente + 8 analista + 5 operario + 4 operador + 6 técnico = 30 sub-claves de contexto, ya descontadas algunas que comparten ISCO).
- ❌ **No corrige los errores de clasificación** que ya existen (Arquitecto Director de Obra → TIC, Operador Logístico cuyo título es "Analista Comercial").
- ❌ **No es escalable a futuras entradas similares** (agrega complejidad estructural al JSON).

**Híbrida (sub-pregunta E3)**:
- Conservar entradas con 100% cobertura (analista, operario, tecnico) pero arreglarles URI: tratar como Opción 3 parcial.
- Quitar `operador` (11% cobertura) y `gerente` (70%): tratar como Opción 1 parcial. 91+129 = 220 al semántico. Riesgo medio.

---

## E — Decisiones que se desbloquean

### E1. ¿% cobertura > 70%?

**Sí, ~79,2% si las reglas con condiciones NLP cuentan**. Pero la franja "alta confianza solo título" es solo 6,1% (65 ofertas). La realidad probable está entre estos extremos, más cercana al 79%.

→ **Opción 1 sería viable EN AGREGADO**, pero la asimetría por entrada lo complica:
- analista, operario, tecnico: cobertura ≥ 99% → Opción 1 viable.
- **operador**: cobertura 11% → **Opción 1 NO viable** (89% al semántico, calidad incierta).
- gerente: cobertura 70% → marginal.

### E2. ¿% cobertura < 50%?

**Sí, para `operador` (11%)**. Para esa entrada Opción 1 es destructiva: 129 ofertas al semántico.

### E3. Decisión por entrada (recomendación basada en datos)

| Entrada | Cobertura reglas | Recomendación basada en datos |
|---|---:|---|
| analista | 100% | Opción 1 (quitar) viable, **PERO** revisar over-match de R87/R238 (sospechoso) |
| operario | 100% | Opción 1 (quitar) viable, **PERO** revisar over-match de R348 (sospechoso) |
| tecnico | 99% | Opción 1 (quitar) viable |
| gerente | 70% | Híbrida o Opción 3. 91 al semántico es demasiado para anglicismos |
| operador | 11% | **Opción 3 (agregar URI)** o agregar reglas nuevas para "operador telefónico" |

→ **Recomendación global**: **híbrida** o **Opción 3 conservadora**, dependiendo del apetito por cambios. Ninguna de las 5 entradas debería ser quitada sin antes:
1. Validar el over-match de R87/R238/R348 ejecutando el matcher en sample.
2. Confirmar que C3 (occupation embeddings) está restaurado antes de quitar `gerente` u `operador`.
3. Agregar reglas nuevas para "operador telefónico" si se decide quitar `operador`.

---

## F — Hallazgos colaterales

1. **Universo real es 1.064, no 1.060**. Diferencia probable: ofertas nuevas matched desde el último conteo. Sin impacto material.

2. **Las 5 entradas isco_familia NO usan ISCO de familia genérico — usan diccionario `contextos` con ISCOs específicos**. El nombre "isco_familia" es engañoso. Implica que Opción 3 necesita URI por contexto (no a nivel raíz), agregando complejidad.

3. **C3 (occupation embeddings) NO está restaurado** en `database/embeddings/esco_occupations_embeddings.npy`. Pero el matcher tiene degradación parcial: `skills_first_v3` funciona vía `skills_matcher` (que usa `esco_skills_embeddings_full.npy`, presente). Solo se degrada `_semantic_match_title()` (busca por embedding del título contra ocupaciones). Si se aplica Opción 1, este degradado importa para títulos sin skills ricas.

4. **Las 1.064 ofertas con URI vacía están todas validadas** (`estado_validacion='validado'` o `'validado_claude'`). El bug pasó controles de validación. Cambiar la estrategia (Opción 1 u Opción 3) reabre estas validaciones.

5. **Errores conceptuales preexistentes**: el sample en A3 muestra que isco_familia + sus contextos clasifican mal varios casos:
   - "Arquitecto/a Director de Obra" → 1330 (TIC) cuando debería ser 1323 (director de obra).
   - "Analista Comercial para Importante Operador Logístico" → 9333 (almacén) cuando el título es "Analista Comercial" (debería ser ~3322).
   - "OPERADOR DE MAQUINAS CHILLER" → 8211 con label "montador de vehículos de motor" — incoherente.
   - "PERSONAL TECNICO para BLINDAJE DE AUTOS" → 3257 (seguridad e higiene) — inadecuado.
   → Opción 3 perpetúa estos errores. Opción 1 podría corregirlos vía reglas o semántico (pero también podría introducir errores nuevos).

6. **Sospecha de over-match en simulación V2** (no confirmable sin ejecutar):
   - `R348_operario_plastico_soplado` capturó 152 ofertas operario, incluyendo "Operario de Producción de Alimentos". Esto es probablemente falso positivo: la regla requiere "soplado/inyección/etc" en título-o-tareas, y la simulación solo evaluó el título.
   - `R238_analista_it` capturó 268 ofertas analista. La regla requiere `area_funcional_es=Tecnología` además. Probablemente falsos positivos para analistas no-IT.
   - `R65_jefe_delegacion` capturó 127 (en V1). La regla requiere "delegación/sucursal/agencia" en título_2 — V2 corrigió esto.
   - **Implicación**: la cobertura real podría ser **bastante menor que 79%**. Sin ejecutar el matcher no se puede confirmar.

7. **`skills_matcheados_esco = 0` en las 1.064**: este valor refleja que la rama del diccionario no computó el match contra ESCO skills, no que las skills serían incompatibles. Las skills extraídas existen en 1.063/1.064 ofertas y son procesables.

8. **"semantic_fallback_v3" tiene 1.098 ofertas con URI 100% poblada** — pero estas son ofertas viejas matched antes del destrackeo SPEC E. La rama "fallback solo semántico" NO funciona hoy (occ_embeddings=None). Toda nueva oferta sin regla cae a `skills_first_v3` o `no_match`.

9. **Pendiente para diagnóstico 9** (sin expandir alcance aquí): el comportamiento exacto del matcher para las 221 sin cobertura sin C3 restaurado (¿caen a no_match o a skills_first_v3?). Solo se puede confirmar ejecutando el matcher en una muestra.

---

## Resumen ejecutivo

- **% cobertura por reglas** (estimación, sin ejecutar matcher): **rango 6,1%–79,2%**, más probable ~79%. La banda inferior es lo que la simulación pudo confirmar con condiciones de solo título; la superior incluye reglas con condiciones NLP no evaluadas.
- **% cae al semántico**: **20,8% (221 / 1.064)**. Confirmado, no depende de NLP.
- **Por entrada**: analista 100%, operario 100%, tecnico 99%, gerente 70%, **operador 11%**.
- **Opción recomendada por datos**: **híbrida o Opción 3 conservadora**.
  - **No quitar `operador`** (11% cobertura — destructivo).
  - **No quitar `gerente` sin C3 restaurado** (70% — marginal con riesgo en anglicismos).
  - Para `analista`/`operario`/`tecnico` Opción 1 podría ser viable, pero antes hay que **confirmar over-match en R87/R238/R348** ejecutando el matcher en muestra.
- **Riesgos detectados**:
  1. Reglas con condición NLP (R238, R348, R87, R65) probablemente over-matchean en simulación → cobertura real podría ser menor.
  2. C3 NO está restaurado → semántico degradado para títulos sin skills ricas (Manager anglicismos en particular).
  3. 1.064 ofertas ya validadas → cualquier cambio reabre validaciones.
  4. Opción 3 perpetúa errores de clasificación preexistentes (~5-10% de las 1.064 tienen ISCOs claramente incorrectos por contexto).
  5. Opción 1 podría dejar 50+ "Operador Telefónico" sin clasificación clara (no hay regla específica + semántico incierto).

**Decisiones desbloqueadas para SPEC U-1 §5 (C2)**:
- Reescribir alcance de C2 si se opta por **Opción 3 con URI por contexto** (no por entrada raíz). Necesita 24-30 mappings.
- Si se opta por **híbrida**: especificar exactamente qué entradas se quitan y cuáles se conservan con URI agregada.
- Antes de cualquier opción que quite entradas: agregar a SPEC U-1 una verificación previa (ejecución del matcher en muestra de 50 ofertas por entrada) para validar la cobertura real.
- **C3 debe estar resuelto antes de quitar `operador` o `gerente`** (sus 220 ofertas dependerían de semántico).
