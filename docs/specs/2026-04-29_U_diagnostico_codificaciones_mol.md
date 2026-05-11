# SPEC U — Diagnóstico de codificaciones MOL (input para revisión cruzada)

**Fecha:** 2026-04-29 (actualizado 2026-04-30 con hallazgos del cruce ESCO×MOL)
**Estado:** DIAGNÓSTICO COMPLETO — pre-implementación
**Objetivo:** consolidar todos los problemas detectados en la codificación de ocupaciones y competencias del MOL para permitir revisión cruzada (otra IA / humanos) antes de definir fixes.

---

## 1. Contexto

### 1.1 Disparador
Diego revisó manualmente 4 ocupaciones representativas en el dashboard MOL y reportó (`docs/Revisión de las codificaciones del MOL.docx`):

| Ocupación | Ofertas | Codificación | Skills | Tablero vs Skill Intelligence |
|---|---|---|---|---|
| Representante Comercial | 3.443 | correcta | con alucinaciones | perfil consolidado no coincide |
| Vendedor especializado | 3.535 | con errores (parte por inglés) | con alucinaciones | **ISCO ≠ ESCO entre vistas** |
| Empleado de Oficina | 1.817 | correcta | con alucinaciones | perfil consolidado no coincide |
| Desarrollador de software | 1.508 | con excepciones | con alucinaciones | perfil consolidado no coincide |

Skills "alucinadas" que Diego marcó (extraídas de las imágenes EMF del .docx, reconvertidas a PNG en `temp/diego_revision/`):
- "prever cambios en la tecnología automovilística" (4/4 ocupaciones)
- "interactuar verbalmente en montenegrino" (3/4)
- "funcionamiento eléctrico de un trolebús" (2/4)
- "custodiar las pruebas de un caso" (2/4)
- "informar sobre las subvenciones" (2/4)
- otras: fertilizantes, biología clínica, micología, logopedia, griego, etnolingüística, limpiar muebles, instalar suelos laminados…

### 1.2 Cambio de paradigma asumido en este diagnóstico
**ESCO > ISCO.** Para análisis, agrupaciones, filtros y consolidación de perfiles se debe usar ESCO (3.046 ocupaciones) en lugar de ISCO (~400 grupos). ISCO mezcla sub-especialidades; ESCO da granularidad útil.

### 1.3 Datos de referencia recién extraídos
Generamos `exports/ocupaciones_esco_con_skills.xlsx` (129.004 filas, formato long) con cada ocupación ESCO y sus skills (essential + optional) cruzadas con descripciones, L1/L2, reuse level, green flag, profesión regulada, altLabels y URI. Esta tabla es **ground-truth** del catálogo ESCO ocupación↔skill.

Cache JSON: `database/embeddings/esco_occupations_enriched.json` (descripciones, altLabels, regulated_status por ocupación) + `database/embeddings/esco_occupation_skills.json` (relaciones essential/optional).

---

## 2. Hallazgo principal

**No hay un solo problema, hay siete problemas independientes** que se manifiestan juntos en la observación de Diego. Cada uno tiene root cause distinto y fix distinto. Listados por gravedad:

| # | Problema | Tipo | Afecta | Severidad |
|---|---|---|---|---|
| A | Flags `is_essential_for_occupation` / `is_optional_for_occupation` nunca se poblan | regresión código | 1.061.051 filas (100%) | crítica |
| 1 | Mismatch `isco_code` ≠ prefix de `titulo_esco_code` | bug INSERT + backfill incompleto | 4.580 filas (8,6%) — y peor: 3 campos desincronizados | crítica |
| **F** | **`esco_occupation_uri` vacío (string '')** | **regla mapea a ISCO/label sin URI** | **3.759 ofertas (6,7%) — afecta especialmente a "empleado de oficina" (97%) y "vendedor/vendedora"** | **crítica** |
| 2 | `dual_coinciden` regla≠semántico en 47% | LoRA ausente + reglas mapean a ISCO genérico + umbral alto | 25.499 filas (47%) | alta |
| C | Dashboard ranquea perfil consolidado por frecuencia cruda | bug presentación | toda la app | alta |
| **E** | **Extractor MOL produce 10–50× más skills distintas que el catálogo ESCO de la ocupación** | **umbral 0.40 + sin filtro por catálogo** | **toda la BD — 12.722 skills MOL únicas vs ~50–340 ESCO por ocupación** | **alta** |
| D | Skills con `esco_skill_label = ''` | bug lookup labels | 7.254 filas (~0,7%) | baja |

---

## 3. DIAG A — Trazabilidad ESCO catálogo no se popula (REGRESIÓN)

### 3.1 Evidencia
Query sobre `ofertas_esco_skills_detalle` (1.061.051 filas):
```
is_essential_for_occupation = 1:  0
is_essential_for_occupation = 0:  1.061.051
is_optional_for_occupation  = 1:  0
is_optional_for_occupation  = 0:  1.061.051
```
**Cero filas marcadas. Todas las skills extraídas quedan en estado "huérfana" frente al catálogo ESCO de la ocupación.**

### 3.2 Root cause
- INSERT en `database/match_ofertas_v3.py:1566-1590` (función `save_skills_detalle()` línea 1519) **omite ambas columnas**. Default SQLite = 0.
- La función no recibe el `occupation_uri` matcheado (disponible en línea 1751 como `occupation_uri = result.esco_uri` pero no se pasa en línea 1788).
- En la versión anterior `database/archive_old_versions/pipelines_old/populate_skills_detalle_v83.py:439-456` SÍ se hacía el cross-check contra `esco_associations` (tabla lookup) y se poblaban los flags. **Se eliminó al refactorizar a v3.5.4.**
- La tabla `esco_associations` existe en schema (`scripts/db/create_tables_nlp_esco.py:343`) pero **está sin poblar en producción**.

### 3.3 Implicaciones
- El sistema **sabe** matchear ocupación pero no **sabe** decir si una skill extraída pertenece al catálogo ESCO de esa ocupación.
- Las alucinaciones que ve Diego no se pueden filtrar porque el filtro natural (skill ∈ catálogo) no se calcula.
- Los datos para hacer el cross-check ya están disponibles (`esco_occupation_skills.json` + el xlsx generado hoy).

### 3.4 Fix natural (sin entrar en spec)
1. Backfill de las 1.061.051 filas cruzando `esco_skill_uri` con el catálogo ESCO de `esco_occupation_uri` matcheado de la oferta.
2. Re-incorporar la lógica de cross-check en `save_skills_detalle()` para futuras ofertas.
3. Decisión de diseño abierta: ¿filtramos skills no-essential/optional o solo las marcamos? Ver §8.

---

## 4. DIAG 1 — Mismatches `isco_code` ↔ `titulo_esco_code` (8,6% de la BD + 3 campos desincronizados)

### 4.1 Evidencia
Sobre 54.067 filas de `ofertas_esco_matching`:
```
OK         44.509  (84%)
esco_NULL   4.978  (9%)
MISMATCH    4.580  (8,6%)   ← isco_code != SUBSTR(titulo_esco_code, 1, 4)
```

Distribución de los 4.580 mismatches por método:
```
semantico_unico (sin regla)   4.165  (91%)
dual_coinciden                  294
regla_por_score_bajo             61
regla_prioridad                  28
regla_zona_gris                  14
otros                            18
```

Solo 29 son sub-ofertas → multi-position **NO** es la causa.

Top 5 pares (isco_BD → derived_isco) más frecuentes en mismatch:
```
9333 → 8160   n=92    label='mozo de almacén'
9334 → 9333   n=82    label='reponedor/reponedora'
2261 → 2269   n=11    label='odontólogo/odontóloga'
2431 → 1330   n=10    label='especialista en estrategias de expansión'
3122 → 5151   n=10    label='supervisor de producción'
```

### 4.2 Root cause confirmado
**Bug en `database/match_ofertas_v3.py:1437-1481`** método `save_matching_result()`:
- El INSERT OR REPLACE escribe `isco_code`, `esco_occupation_label`, `esco_occupation_uri`, etc. pero **OMITE `titulo_esco_code` y `titulo_normalizado`**.
- `titulo_esco_code` se popula por scripts separados:
  - `scripts/embeddings/backfill_titulo_esco_code.py:62`
  - `scripts/embeddings/rematch_isco_spec_h.py:256`
- Cuando una corrida posterior actualiza `esco_occupation_uri`, el `titulo_esco_code` queda con el valor del backfill anterior.

### 4.3 Hallazgo adicional MÁS GRAVE
**No es solo desincronización de un campo.** Inspección de los samples:

```
oferta=...3955  isco=4110  titulo_esco_code=1211.1  label='empleado de oficina'    sin regla
oferta=...3995  isco=8160  titulo_esco_code=9622.1  label='operario de prensado de fruta'  sin regla
oferta=...3912  isco=8332  titulo_esco_code=8322.2  label='conductor de grúa remolque'   sin regla
oferta=...1731  isco=7422  titulo_esco_code=7421.7  label='técnico reparador de telefonía'   sin regla
```

En estos casos `isco_code` y `titulo_esco_code` son códigos de ocupaciones **completamente distintas**. El `esco_uri` también puede estar desalineado.

Caso especialmente claro: 87 ofertas con `esco_uri` apuntando a ESCO 8160.35 ("operario de prensado de fruta") **pero** `isco_code='9333'` y `label='mozo de almacén'`. Tres campos que deberían derivar uno del otro están en estados inconsistentes.

### 4.4 Hipótesis sobre las 3 desincronizaciones
- Bug histórico de migration: distintos backfills (`backfill_titulo_esco_code.py`, `rematch_isco_spec_h.py`, `reapply_rules_to_validated.py`) escribieron distintos campos sin coordinarse.
- O regla de matching escribió `isco_code` + `label` desde su propia tabla de mapping pero no actualizó `esco_uri` que estaba seteado por una corrida anterior del semántico.

**Confirmar la hipótesis requiere:** revisar `reapply_rules_to_validated.py` y los backfills mencionados, y ver el flujo histórico. Pendiente.

---

## 5. DIAG 2 — `dual_coinciden = 0` en 47% (regla vs semántico DIFIEREN)

### 5.1 Evidencia
```
Total ofertas_esco_matching:  54.067
DIFIEREN (dual_coinciden=0):  25.499  (47%)
sin_regla (dual NULL):        18.683  (35%)
COINCIDEN:                     9.885  (18%)
```

Distribución por `decision_metodo`:
```
regla_prioridad         22.119  → 100% DIFIEREN  (la regla siempre gana)
semantico_unico         18.491  → mayormente sin_regla
dual_coinciden          10.002  → 97% coinciden (correcto, son los OK)
regla_zona_gris          1.436  → 100% DIFIEREN
regla_por_score_bajo     1.293  → 98% DIFIEREN
regla_override_sem_alto    107  → 100% DIFIEREN
```

Top 5 reglas con desacuerdo casi total:
| Regla | Total | DIFIEREN | % | Par regla→sem |
|---|---:|---:|---:|---|
| R240_operario_produccion | 1.108 | 1.100 | 99,3% | 9329→8160 |
| R48_secretaria_admin | 328 | 322 | 98,2% | 4120→4110 |
| R229_analista_comercial | 510 | 501 | 98,2% | — |
| R230_asesor_comercial | 341 | 334 | 97,9% | — |
| R49_jefe_generico | 1.071 | 1.047 | 97,8% | 1219→1221 |

### 5.2 Root cause: TRES causas concurrentes confirmadas

#### Causa 1 — LoRA model NO existe en disco
```
/mnt/d/OEDE/Webscrapping/data/finetuning/matching/model_lora  → NO EXISTE
Solo está: training.log
```
- El semántico cae a base BGE-M3 vía fallback en `database/skills_implicit_extractor.py:83-87`.
- Documentado en CLAUDE.md línea 53: "BGE-M3 base (LoRA fine-tuned NO disponible — model_lora no existe en disco, umbral 0.40)".
- Manifestación: el semántico produce labels mal calibrados. Sample real: para "Analista funcional de core bancario SR" el semántico devuelve "consultor de TIC verdes" con score 0.90. Para "Cajero/a polivalente" devuelve label 5223 (vendedor) en lugar de 5230 (cajero).

#### Causa 2 — Reglas mapean a ISCO genérico cuando el semántico identifica más específico
Pares más frecuentes en DIFIEREN:
```
R170_asesor_comercial:  regla=3322 (rep. comercial general)  vs sem=2431/2433/5223 (varios específicos)
R109_ejecutivo_ventas:  regla=3322                             vs sem=1221/2433/5223
R49_jefe_generico:      regla=1219 (jefes admin generales)    vs sem=1221 (gerente ventas) / 4110 (oficina)
```

**El semántico distribuye entre sub-ocupaciones; la regla aplasta todo en una clase paraguas.** Esto conecta con el problema observado por Diego: muchas ofertas con perfiles heterogéneos quedan agrupadas en "representante comercial" porque la regla las absorbe → el perfil consolidado mezcla skills de muchas ocupaciones distintas.

#### Causa 3 — Umbral 0.95 muy alto para que el semántico gane
Lógica en `_decide_dual_match()` (líneas 1103-1181):
- score_semantico < 0.55 → regla gana
- 0.55 ≤ score < 0.95 → regla gana
- score ≥ 0.95 → semántico override
- regla_critica → siempre gana
- override_semantico → regla gana (v3.5.5 para términos no ambiguos)

Distribución de score_semantico cuando regla gana sobre semántico (DIFIEREN):
```
score ~0.6:   15.617  (mayoría)
score ~0.7:    1.084
score ~0.8:    1.224
score ~0.9:    4.190    ← semántico MUY confiado, igual pierde
score ~1.0:        4
```
**5.500+ ofertas tienen score semántico ≥ 0.8 y la regla aún las override.**

### 5.3 Análisis interpretativo del sample humano

Mirando 25 samples reales (`/tmp/diag6.py` output):

| Caso | Regla → Sem | Cuál parece correcto |
|---|---|---|
| "Cajero/a polivalente" | 5230 → 5223 | regla |
| "Community manager" | 2432 → 1330 | regla |
| "Cocinero/a" | 5120 → 3434 | regla |
| "Abogado/a junior" | 2611 → 3411 | regla |
| "Analista funcional de core bancario SR" | 2511 → 2421 | regla (sem dice "TIC verde") |
| "Operario de expedición" | 9329 → 8160 | sem (es fábrica de pastas) |
| "Asistente administrativa/o" | 4120 → 4110 | ambos válidos |
| "Responsable de marketing" (sem score 0.97) | 1219 → 1221 | sem |
| "Sales executive" | 3322 → 5223 | regla |

**Conclusión:** la métrica `dual_coinciden = 0` al 47% NO equivale a "errores de matching". Está dominada por desviaciones del semántico mal calibrado, NO por errores sistémicos de las reglas. Las reglas están en general bien.

**Pero** los grupos `regla_zona_gris` (1.436), `regla_por_score_bajo` (1.293), `regla_override_semantico_alto` (107) y los casos donde sem_score ≥ 0.9 sí merecen revisión humana caso por caso.

---

## 6. DIAG C — Dashboard ranquea perfil consolidado por frecuencia cruda

### 6.1 Evidencia
**Archivo:** `fase3_dashboard/mol-dashboard/lib/supabase.ts:1912-2016` función `getOccupationMOLProfile(escoUri: string)`.

Lógica del ranking (línea 1990):
```typescript
.sort((a, b) => b.frequency - a.frequency)
```

- ✅ Agrupa por `esco_occupation_uri` (correcto).
- ❌ Sin umbral mínimo de frecuencia.
- ❌ Sin TF-IDF / saliency / percentil.
- ❌ Calcula `avg_score` (línea 2000) y `is_essential` (línea 2001) **pero NO los usa para ranquear**.

**Tablero (la otra vista que Diego compara contra):** `app/oficina-empleo/benchmark/page.tsx` + `lib/api/inteligencia-local/route.ts:38-69`. También ranking por count crudo, pero agrupa por **jurisdicción** y `canonical_label`. Por eso no coincide con Skill Intelligence (distinto scope, distinto agregado).

### 6.2 Manifestación
Para "Representante Comercial" (3.576 ofertas en BD), las skills que Diego marcó como alucinaciones tienen estas posiciones reales en el ranking de frecuencia (sobre 3.894 skills distintas):

| Skill marcada por Diego | Posición | Frecuencia |
|---|---:|---:|
| funcionamiento eléctrico de un trolebús | 1.013 | 10 |
| gestionar quejas sobre el juego | 1.269 | 7 |
| informar sobre las subvenciones | 2.060 | 3 |
| prever cambios en la tecnología automovilística | 2.392 | 2 |
| dirigir un departamento de educación secundaria | 3.585 | 1 |
| custodiar las pruebas de un caso | 3.636 | 1 |
| interactuar verbalmente en montenegrino | NO APARECE | 0 |

**Una skill con frecuencia 1 entre 3.576 ofertas no debería entrar al perfil consolidado.** Diego las ve porque el dashboard probablemente muestra todas sin tope inferior.

### 6.3 Skills "magnéticas" globalmente (agrupando por ESCO)
Top 5 skills que aparecen en más ESCOs distintas (de 3.046 totales):
```
trabajar en equipo                        775 ESCOs    5.062 apariciones
crear un espíritu de equipo               702         4.329
analizar problemas para buscar soluciones 663         4.847
identificar acciones de mejora            566         4.503
ocuparse de la orientación al cliente     506         5.601
```
Estas son skills **L1=T (Transversales)** según ESCO. Es legítimo que aparezcan en muchas ocupaciones, pero el dashboard las ranquea junto a las específicas. **Hay que distinguir transversales vs sectoriales en la presentación.**

---

## 7. DIAG D — Skills con `esco_skill_label = ''` (bug acotado)

### 7.1 Evidencia
- 7.254 filas con label vacío (~0,7% del total).
- 10 URIs distintas afectadas. Las 10 existen en el catálogo ESCO completo (`database/embeddings/esco_skills_metadata_full.json`) — el label real está disponible.
- Top URI: `68d17d2e-2761-438b-af13-0f8d107720d8` con 1.397 apariciones.
- Todas vienen del extractor: `match_method = 'implicit_bge_m3'`.

### 7.2 Root cause (probable, pendiente confirmar)
Bug de lookup/cache en el extractor: el BGE-M3 trajo URIs válidas pero el cache de labels no devolvió label en el momento del INSERT. Persistió la skill con label vacío.

### 7.3 Fix simple
UPDATE cruzando con `esco_skills_metadata_full.json` para repoblar labels. Una sola corrida.

---

## 7-bis. DIAG F — `esco_occupation_uri` vacío (NUEVO, hallado el 30/04 en cruce ESCO×MOL)

### 7-bis.1 Evidencia
Cruce de URIs en BD vs catálogo ESCO oficial (3.046 ocupaciones):
```
URIs distintas en BD:           2.233
  En catálogo ESCO:             2.232  (correcto)
  FUERA de catálogo:                1  ← string vacío ''

Total ofertas matcheadas:      56.430
  Con URI EN catálogo:         52.671  (93,3%)
  Con URI VACÍA:                3.759  (6,7%)  ← BUG
```

**No hay URIs "inventadas" o de versiones viejas. Hay un único patrón: `esco_occupation_uri = ''` (string vacío).** El matcher escribe `esco_occupation_label` y `isco_code` correctamente pero deja el URI sin setear.

Top ocupaciones con URI vacío:
```
empleado de oficina/empleada de oficina    1.904 ofertas
vendedor/vendedora                           465
analista de sistemas de TIC                  140
director de tecnología/directora             122
operador de carretilla elevadora             108
ayudante de recursos humanos                  97
```

### 7-bis.2 Caso específico — Empleado de oficina
De 1.962 ofertas matcheadas como "empleado de oficina/empleada de oficina":
- 1.904 (97%) tienen `esco_occupation_uri = ''`
- 58 tienen URI válida en catálogo

**Por eso en la comparación ESCO×MOL para esta ocupación de Diego apareció "0 skills en catálogo ESCO":** simplemente no había URI con la cual mapear contra el catálogo.

### 7-bis.3 Root cause (probable)
Las reglas de matching que cubren estas ocupaciones (R196_pasante_administrativo, R48_secretaria_admin, etc. para empleado de oficina; R111_vendedor_generico para vendedor; etc.) **mapean a un ISCO/label conocido pero no tienen el `esco_occupation_uri` asociado en `config/matching_rules_business.json`**. El matcher persiste lo que tiene; el URI queda vacío.

Pendiente confirmar: revisar la columna `esco_uri` (o equivalente) en `matching_rules_business.json` para las reglas afectadas.

### 7-bis.4 Implicaciones
- **6,7% de ofertas no se pueden cruzar con el catálogo ESCO oficial** — pierden cualquier filtro o consolidación basada en URI.
- Skill Intelligence agrupa por `esco_occupation_uri`. Las 3.759 ofertas con URI vacía probablemente caen en un "bucket fantasma" o se descartan del dashboard.
- Los conteos del SPEC U previos (DIAG A: "1.061.051 filas con flag = 0") incluyen estas ofertas: aunque tuviéramos el cross-check funcionando, sin URI no se puede mapear.

### 7-bis.5 Fix natural
- Auditar `matching_rules_business.json` y completar el `esco_uri` de las reglas que no lo tienen.
- Backfill: para las 3.759 ofertas afectadas, buscar la URI ESCO correspondiente al `(esco_code, esco_occupation_label)` que sí tienen, vía `database/embeddings/esco_occupations_full.json`.

---

## 7-ter. DIAG E — Cola larga del extractor: 10–50× más skills MOL que catálogo ESCO

### 7-ter.1 Evidencia (cruce ESCO×MOL para las 4 ocupaciones de Diego)

| Ocupación | URIs ESCO asignadas | Ofertas | Skills ESCO catálogo (essential+optional) | Skills MOL extraídas | Ratio MOL/ESCO |
|---|---:|---:|---:|---:|---:|
| Representante comercial | 16 distintas | 3.648 | 76 | 3.984 | **52×** |
| Vendedor especializado | 28 distintas | 2.873 | 339 | 3.508 | 10× |
| Empleado de oficina | 7 (URI principal vacía — DIAG F) | 1.962 | 0 | 4.651 | ∞ |
| Desarrollador de software | 3 distintas | 1.510 | 108 | 3.005 | 28× |

**Globalmente:**
- Skills MOL únicas: **12.722** (de 14.257 totales en catálogo ESCO)
- Pares ocupación-skill en catálogo ESCO: 128.987
- Pares ocupación-skill en MOL extraído: **334.864** (Hoja 2 del xlsx generado)

### 7-ter.2 Patrones de la cola larga
- El extractor actual (BGE-M3 base, umbral 0.40) genera muchas skills distintas por oferta.
- Cada oferta produce ~17–20 skills extraídas en promedio (966.342 / 56.430 ≈ 17,1).
- En una ocupación con miles de ofertas, la unión de cola larga acumula 3.000-5.000 skills distintas.
- **No es ruido aleatorio:** las skills son URIs ESCO válidas (no inventadas), pero NO son las que ESCO marca como pertenecientes a la ocupación.

### 7-ter.3 Conexión con DIAG A y DIAG C
Estas tres condiciones se suman para producir el síntoma que reportó Diego:
1. **DIAG E:** el extractor genera 50× más skills que el catálogo ESCO.
2. **DIAG A:** los flags `is_essential_for_occupation`/`is_optional_for_occupation` están vacíos → no se puede filtrar.
3. **DIAG C:** el dashboard ranquea por frecuencia cruda → la cola larga de skills raras (frecuencia 1-10) entra al perfil consolidado junto con las de frecuencia 1.000+.

Resultado: skills como "interactuar verbalmente en montenegrino" (frecuencia 0-1 en una ocupación de 3.500 ofertas) son visibles en el dashboard.

### 7-ter.4 Skills "magnéticas" (aparecen en muchas ESCO distintas)
Top 10 skills MOL globales por número de ESCOs distintas donde aparecen:
```
trabajar en equipo                         775 ESCOs   5.062 apariciones
crear un espíritu de equipo                702         4.329
analizar problemas para buscar soluciones  663         4.847
animar a los equipos a procurar mejoras    663         4.692
hacer recomendaciones de reparaciones      593         3.879
utilizar aparatos para escanear cód. barras 567         2.799
identificar acciones de mejora             566         4.503
aplicar normas de calidad                  520         2.962
gestionar el inventario                    519         5.838
ocuparse de la orientación al cliente      506         5.601
```
Casi todas son **L1 = T (Transversales)** según ESCO — es legítimo que aparezcan en múltiples ocupaciones, pero el ranking debería distinguirlas de las específicas.

### 7-ter.5 Datos disponibles para análisis
- `exports/ocupaciones_mol_con_skills.xlsx` (55.9 MB, 3 hojas) — espejo MOL del catálogo ESCO con métricas de cobertura, magneticidad, ranking, ID de ofertas (cap 200).
- `exports/comparacion_esco_vs_mol_diego.xlsx` (2.9 MB) — comparación lado a lado para las 4 ocupaciones de Diego (ESCO_only / MOL_only / both, con IDs de ofertas).

---

## 7-quater. DIAG 1-bis — Alta dispersión de URIs por label (subhallazgo de DIAG 1)

Para las 4 ocupaciones de Diego, cuántas URIs ESCO **distintas** se asignaron al mismo `esco_occupation_label`:

| Label | URIs distintas | Ofertas en URI principal | Ofertas en URIs minoritarias |
|---|---:|---:|---:|
| representante comercial | 16 | 3.670 | 13 (sumadas) |
| vendedor especializado | 28 | 2.895 | 31 |
| empleado de oficina | 7 | 1.904 (URI vacía) | 58 |
| desarrollador de software | 3 | 1.508 | 2 |

**El label es estable; las URIs no.** Para "vendedor especializado" 28 URIs distintas se asignaron a 2.873 ofertas. La URI principal cubre 99% pero el label se reusó en URIs de ocupaciones completamente distintas (consistente con los mismatches isco/esco del DIAG 1: caso "vendedor especializado" con esco_code apuntando a 1221.3.2.1, 5131.2.1, 1324.8, etc.).

---

## 8. Mapa de fixes propuestos (sin ejecutar)

| # | Fix | Archivo objetivo | Esfuerzo | Reqs |
|---|---|---|---:|---|
| F1 | Backfill flags `is_essential_for_occupation` / `is_optional_for_occupation` en 1.06M filas | nuevo script + `esco_occupation_skills.json` | bajo | A |
| F2 | Re-incorporar cross-check en pipeline | `match_ofertas_v3.py:1519,1751,1788` | medio | A |
| F3 | Backfill labels vacíos | nuevo script + `esco_skills_metadata_full.json` | bajo | D |
| F4 | Agregar `titulo_esco_code` al INSERT del matcher | `match_ofertas_v3.py:1437-1481` | bajo | 1 |
| F5 | Backfill global de los 4 campos (isco_code, esco_uri, label, titulo_esco_code) consistentes | nuevo script | medio-alto | 1 |
| F6 | Cambiar ranking del perfil consolidado | `lib/supabase.ts:1912-2016` | bajo | C |
| F7 | Distinguir skills transversales (L1=T) en presentación | mismo archivo + UI | medio | C |
| F8 | Re-entrenar / restaurar LoRA | `data/finetuning/matching/model_lora` | alto | 2 |
| F9 | Revisar reglas con desacuerdo extremo (`regla_zona_gris`, `regla_por_score_bajo`) | `config/matching_rules_business.json` + revisión manual | alto | 2 |
| **F10** | **Auditar reglas sin `esco_uri` y completar URI faltante** | **`config/matching_rules_business.json`** | **bajo-medio** | **F** |
| **F11** | **Backfill de `esco_occupation_uri` para las 3.759 ofertas con URI vacío** | **nuevo script** | **bajo** | **F** |
| **F12** | **Aplicar filtro de skills (hard o soft) en el extractor o presentación** | **`skills_implicit_extractor.py` o `lib/supabase.ts`** | **medio** | **E (depende de §9.1)** |

**Lo bueno:** F1, F3, F4, F5, F6 son fixes de **datos / lógica de presentación** que no requieren reprocesar el pipeline NLP. Se pueden hacer mientras el pipeline corre.

**Lo dependiente:** F2 (re-incorporar cross-check) requiere modificar `match_ofertas_v3.py` y reprocesar futuras ofertas con la lógica corregida. F8 y F9 son trabajo mayor.

---

## 9. Preguntas abiertas (input para revisión cruzada)

### 9.1 Política de filtrado de skills "fuera de catálogo ESCO"
Una vez con flags `is_essential_for_occupation` / `is_optional_for_occupation` poblados:
- **Opción A — Hard filter:** solo conservar/mostrar skills que están en el catálogo ESCO de la ocupación matcheada.
  - Pro: elimina alucinaciones de raíz.
  - Contra: el catálogo ESCO 3322 tiene solo 112 skills entre 3 sub-ocupaciones; muchas skills coherentes ("vender productos", "identificar oportunidades comerciales") no están y se perderían.
- **Opción B — Soft filter (boost):** mantener todas las skills extraídas, pero ranquearlas premiando las del catálogo ESCO.
  - Pro: no pierde skills coherentes que ESCO no catalogó.
  - Contra: las alucinaciones siguen presentes en cola larga.
- **Opción C — Multi-nivel:** mostrar primero las del catálogo (essential → optional → none), separadas en bloques.

¿Cuál preferimos?

### 9.2 Ranking del perfil consolidado en el dashboard
Variables a definir:
- ¿TF-IDF? ¿Frecuencia con umbral mínimo? ¿Score-weighted (`avg_score`)? ¿Combinación?
- Umbral mínimo: ¿N ≥ 5 ofertas? ¿N ≥ 1% del total? ¿top-50 capeado?
- Transversales (L1=T) vs sectoriales (L1=S): ¿separadas en la UI? ¿peso menor? ¿filtradas opcionalmente?

### 9.3 Política para los 4.580 mismatches isco/esco
- ¿Reprocesarlos individualmente con el matcher v3 corregido?
- ¿Backfill masivo recalculando los 4 campos desde `esco_occupation_uri` como fuente única de verdad?
- ¿Cuál de los 3 campos desincronizados es el "correcto" cuando difieren? Hipótesis: `esco_occupation_uri` (porque es el que setea el matcher al final).

### 9.4 Política para los 47% DIFIEREN
- Como interpretamos: las reglas en general son correctas; el semántico está mal calibrado por falta de LoRA. **¿Aceptar el 47% como ruido del semántico hasta restaurar LoRA?**
- Subset que sí amerita revisión: `regla_zona_gris` (1.436) + `regla_por_score_bajo` (1.293) + casos con score_sem ≥ 0.9 que la regla overrideó (~4.190). ¿Hacer revisión humana sample-driven?
- ¿Vale la pena restaurar LoRA antes que cualquier otra cosa? ¿Qué se necesita para entrenarlo de nuevo?

### 9.5 Orden de ejecución de fixes
Mi propuesta tentativa (actualizada con DIAG E y F):
1. **F11 + F10** (URI vacíos, sin riesgo): habilita todo lo demás. Sin URI no hay cruce con catálogo.
2. **F1 + F3** (backfills datos: flags y labels vacíos, sin riesgo)
3. **F4 + F5** (mismatches isco/esco, sin riesgo)
4. **F6 + F7** (ranking dashboard, decisión de diseño primero — §9.1 y §9.2)
5. **F12** (filtro de skills — depende de §9.1)
6. **F2** (modificar matcher, requiere prueba)
7. **F8 / F9** (decisión de proyecto mayor — LoRA)

**Argumento del nuevo orden:** F11+F10 antes que F1 porque sin `esco_occupation_uri` poblada no se puede hacer el cross-check de F1 sobre las 3.759 ofertas afectadas (~6,7%).

¿Acuerdo? ¿Otro orden?

### 9.6 Política para el ratio 50× del extractor (DIAG E)
El extractor produce 3.000-5.000 skills distintas por ocupación, vs ~50-340 que ESCO marca como pertinentes. Tres estrategias posibles:
- **(a) Bajar el ratio en el extractor:** subir threshold de 0.40 a 0.55-0.65, top-N capeado por oferta (ej. top-10 skills por oferta).
  - Pro: trabajamos en el origen.
  - Contra: requiere reprocesar todas las ofertas.
- **(b) Filtrar/ranquear en presentación:** el extractor sigue produciendo, pero el dashboard solo muestra top-N o filtra por catálogo.
  - Pro: no requiere reprocesar.
  - Contra: la BD sigue inflada con cola larga.
- **(c) Ambos:** extractor más conservador + presentación con filtro adicional.

¿Cuál es preferible? Liga con §9.1 (filtro hard/soft) y §9.2 (ranking).

---

## 10. Anexos / archivos generados durante el diagnóstico

| Archivo | Contenido |
|---|---|
| `exports/ocupaciones_esco_con_skills.xlsx` (27,8 MB) | 129K filas: ocupación ESCO × skill (essential/optional) con L1/L2, descripción, URI, reuse, green, etc. **Ground-truth ESCO.** |
| `exports/ocupaciones_mol_con_skills.xlsx` (55,9 MB, 3 hojas) | **NUEVO 30/04.** Espejo MOL del catálogo ESCO. Hoja 1 (3.046 ocupaciones), Hoja 2 (334.864 pares ocupación-skill), Hoja 3 (12.722 skills globales). Incluye id_ofertas (cap 200) en cada fila. |
| `exports/comparacion_esco_vs_mol_diego.xlsx` (2,9 MB) | **NUEVO 30/04.** 15.787 filas: comparación ESCO_only / MOL_only / both para las 4 ocupaciones de Diego. Con id_ofertas (cap 200). |
| `database/embeddings/esco_occupations_enriched.json` | Cache de descripciones, altLabels, regulated_status por ocupación |
| `temp/diego_revision/image1-4.png` | 4 cuadros de Diego convertidos de EMF a PNG |
| `scripts/exports/generate_ocupaciones_skills_xlsx.py` | Script generador del xlsx ESCO ground-truth |
| `scripts/exports/generate_ocupaciones_mol_con_skills.py` | **NUEVO.** Script generador del espejo MOL |
| `scripts/exports/generate_comparacion_esco_vs_mol_diego.py` | **NUEVO.** Script generador de la comparación Diego |
| `/tmp/diag5.out`, `/tmp/diag6.py`, `/tmp/diag_uris_huerfanas.py` | Outputs de las queries diagnósticas |

---

## 11. Estado del pipeline durante el diagnóstico
Pipeline en producción **siguió corriendo todo el tiempo**: PID 74477, `run_validated_pipeline.py --force-new-batch --limit 1000 --max-nlp-iterations 1` desde 15:28. Todo el diagnóstico se hizo en modo READ-ONLY sobre la BD SQLite (`?mode=ro`) sin afectar la corrida activa.

---

**Próximo paso:** revisión cruzada por otra IA / humanos. El objetivo es que respondan §9 (decisiones de diseño) antes de empezar a implementar.
