# M-08b — Equivalencias: Cerrar el Loop (v3)

> **Estado:** ⬜ No iniciado
> **Prioridad:** ALTO
> **Prerequisito de:** M-08 ✅, SPEC_EQUIV_UI_MEJORAS_V2 ✅
> **Supersede:** SPEC_M08B_V2.md (v2, corregida por 3 ajustes: texto_original, esfuerzo re-clustering, secuencia)
> **Versión:** 3.0

---

## El problema real que resuelve

El MOL intenta responder "¿qué competencias pide el mercado argentino
para cada ocupación?". La respuesta debería ser una lista ordenada por
demanda real. Hoy la respuesta está fragmentada.

**El caso concreto:**
```
"analizar datos"                  → 25% de ofertas de Analista de datos
"realizar un análisis de datos"   → 20% de ofertas
"análisis de datos"               → 13% de ofertas

Ninguna supera el umbral de 30% → ninguna se detecta como emergente
Combinadas suman 58%             → claramente emergente, el sistema no lo ve
```

El sistema de equivalencias agrupa esas variantes correctamente —
1,292 grupos con scores de confianza. Pero el agrupamiento no llega
a los lugares donde se toman decisiones.

---

## Correcciones respecto a v2

La v2 tenía 3 problemas identificados al verificar contra el código real:

1. **Texto original no disponible para Parte 2:** `save_skills_detalle()`
   guarda `skill_mencionado` = label ESCO matcheado, no el texto original
   declarado ("CRM"). El dato viaja como `texto_fuente` en el dict pero
   no se persiste. Sin este dato, `generate_equiv_candidates.py` no puede
   detectar co-matcheo. La v3 agrega `texto_original` como columna + fix
   en la persistencia.

2. **Estimación de Parte 3 imprecisa:** La v2 no estimaba esfuerzo.
   Verificado: medio día de trabajo. `--partial` es un path nuevo que no
   toca el comportamiento default. Riesgo principal: asignación de IDs sin
   colisión con grupos protegidos.

3. **Secuencia incompleta:** La v2 empezaba por el backfill de
   equivalence_id, pero antes de todo hay que persistir `texto_original` —
   sin eso, Parte 2 no tiene datos. La v3 agrega Paso 0.

---

## Objetivo

Cerrar el loop de tres formas:

```
Parte 0 → Persistir texto original (prerequisito de todo)
Parte 1 → El Perfil Argentino usa equivalencias para contar
           demanda real; emergentes que hoy no se detectan
Parte 2 → El mercado alimenta el sistema de equivalencias
           candidatos desde co-matcheo de skills declaradas
Parte 3 → El analista puede mejorar el clustering
           re-clustering controlado con frozen groups
```

---

## Parte 0 — Persistir texto original (PREREQUISITO)

### El problema

Cuando M-08 procesa "CRM" de `tecnologias_list`:

```
_parse_declared_source() → ["CRM"]                    ← texto original VIVE
extract_declared_skills() → {
    "skill_esco": "gestionar relaciones...",            ← label ESCO (reemplaza)
    "texto_fuente": "CRM",                              ← texto original VIVE ACÁ
}
match_and_persist() → merge                            ← texto_fuente VIVE
save_skills_detalle() → INSERT skill_mencionado        ← guarda label ESCO
                                                          "CRM" SE PIERDE
```

El dato existe hasta el último momento — solo falta persistirlo.

### Migration SQL

```sql
ALTER TABLE ofertas_esco_skills_detalle
ADD COLUMN IF NOT EXISTS texto_original TEXT;
```

### Fix en save_skills_detalle()

**Archivo:** `database/match_ofertas_v3.py`

En el INSERT de `save_skills_detalle()`, agregar `texto_original`
tomándolo de `texto_fuente` del dict de cada skill:

```
skill dict tiene:
  "skill_esco": "gestionar relaciones..."  → va a skill_mencionado
  "texto_fuente": "CRM"                    → va a texto_original (NUEVO)
```

Para skills de tareas (no declaradas): `texto_fuente` ya existe en el
dict con el texto de la tarea. Para skills de reglas: `texto_original = NULL`.

### Fix en extract_from_tasks()

Las skills extraídas de tareas ya tienen `"tarea": tarea[:100]` en el
dict. Renombrar/mapear a `texto_fuente` para consistencia, o usar
`tarea` como `texto_original` en save_skills_detalle().

---

## Parte 1 — Cerrar el loop del Perfil Argentino (URGENTE)

### El cambio

**Archivo:** RPC `recalcular_emergentes()` en Supabase

**Hoy:**
```sql
GROUP BY os.preferred_label, os.skill_uri
```

**Con M-08b:**
```sql
GROUP BY COALESCE(os.canonical_label, os.preferred_label),
         COALESCE(os.equivalence_id, os.skill_uri)
```

**Patrón ya probado:** `get_skills_resumen()` (migration 011) usa
exactamente `COALESCE(canonical_label, preferred_label)` para agrupar.

**Comparación contra el perfil consolidado:**

Sin cambiar schema de esco_argentino:
```sql
-- Hoy:
LOWER(ps.skill) = LOWER(sf.skill_label)

-- Con M-08b:
LOWER(ps.skill) = LOWER(COALESCE(sf.canonical_label, sf.skill_label))
```

El `ON CONFLICT (skill_label, isco_code)` en la tabla
`emergentes_pendientes` sigue siendo correcto — si dos variantes se
consolidan al mismo canonical_label + isco_code, el constraint hace
UPDATE en vez de INSERT. Eso es el comportamiento deseado.

### El label que se muestra

Precedencia para el label visible:
```
1. label_argentino del grupo (si existe)
2. canonical_label del representante
3. preferred_label (fallback)
```

### Backfill de equivalence_id

**Cobertura actual:** 23.5% (83,357 de 355,019)

Correr `backfill_skill_equivalences.py` completo antes de aplicar
el cambio. El COALESCE funciona con cualquier cobertura — las filas
sin equivalence_id usan skill_uri como fallback.

### Impacto esperado

Skills fragmentadas en 2-3 variantes se consolidan. Emergentes que
no superaban 30% individualmente pero sí combinadas empiezan a
detectarse. El Perfil Argentino muestra el nombre canónico.

---

## Parte 2 — Candidatos desde fuentes declaradas

### Lógica de detección

Un par de términos es candidato a equivalencia cuando:

```
texto_original_A y texto_original_B (de ofertas_esco_skills_detalle)
    → matchearon contra la misma URI ESCO (esco_skill_uri)
    → texto_original_A != texto_original_B (términos distintos)
    → en al menos 5 ofertas distintas
    → NO están ya en el mismo grupo de equivalencia
```

**Usa `texto_original`** (Parte 0) — no `skill_mencionado` (que es el
label ESCO y sería igual para ambos).

### Script de detección

**Archivo:** `scripts/generate_equiv_candidates.py` (nuevo)

Proceso:
1. Leer `ofertas_esco_skills_detalle` local (SQLite)
2. Filtrar skills con `texto_original IS NOT NULL`
3. Agrupar por `esco_skill_uri` — para cada URI, listar
   todos los `texto_original` distintos que matchearon
4. Para cada URI con 2+ textos originales distintos:
   - Contar co-apariciones en ofertas únicas
   - Si >= 5 ofertas → candidato
5. Filtrar candidatos ya en el mismo grupo
6. Exportar a tabla `equiv_candidates` en Supabase

### Tabla nueva: `equiv_candidates`

```sql
CREATE TABLE equiv_candidates (
    id                BIGSERIAL PRIMARY KEY,
    uri_esco          TEXT NOT NULL,
    skill_label_esco  TEXT NOT NULL,
    termino_a         TEXT NOT NULL,
    termino_b         TEXT NOT NULL,
    fuente_a          TEXT NOT NULL,
    fuente_b          TEXT NOT NULL,
    co_apariciones    INT NOT NULL,
    score_promedio_a  REAL,
    score_promedio_b  REAL,
    estado            TEXT DEFAULT 'pendiente',
    revisado_por      TEXT,
    revisado_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_candidates_uri    ON equiv_candidates(uri_esco);
CREATE INDEX idx_candidates_estado ON equiv_candidates(estado);

ALTER TABLE equiv_candidates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "platform_admin_only" ON equiv_candidates
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'platform_admin');
```

### RPCs

```sql
-- Listar candidatos (SECURITY DEFINER)
get_equiv_candidates(p_estado TEXT DEFAULT 'pendiente', limit_n INT DEFAULT 50)

-- Aprobar: crea grupo nuevo o agrega a existente (SECURITY DEFINER)
aprobar_candidato(p_candidate_id BIGINT, p_action TEXT)
    -- p_action: 'crear_grupo' | 'agregar_a_grupo'

-- Rechazar (SECURITY DEFINER)
rechazar_candidato(p_candidate_id BIGINT)
```

### UI — Tab "Candidatos"

**Ubicación:** Nueva tab en
`/admin/procesamiento/fabrica/equivalencias`

```
┌─────────────────────────────────────────────────┐
│ CANDIDATOS          47 pendientes · 12 aprobados │
├──────────────────────────────────────────────────┤
│ URI: gestionar relaciones con clientes           │
│ "CRM" ↔ "sistema CRM"    12 co-apariciones      │
│ tecnologia · 0.39    herramienta · 0.41         │
│ [Crear grupo]  [Rechazar]  [Ver ofertas]        │
├──────────────────────────────────────────────────┤
│ URI: trabajar en equipo                          │
│ "trabajo en equipo" ↔ "teamwork"  8 ofertas     │
│ [Agregar a EQ-001]  [Rechazar]                  │
└──────────────────────────────────────────────────┘
```

---

## Parte 3 — Re-clustering controlado

### Principio: Frozen Groups

```
'aprobado' → PROTEGIDO — el algoritmo no lo toca
'revisado' → PROTEGIDO — idem
'auto'     → LIBRE — el algoritmo puede modificarlo
```

### Esfuerzo estimado: medio día

El script actual tiene ~220 líneas lineales. `--partial` es un path
nuevo que no toca el comportamiento default (full-rebuild).

**Riesgo principal:** Asignación de IDs (EQ-00001, etc.) sin colisión
con grupos protegidos. Los protegidos mantienen sus IDs, los nuevos
necesitan IDs que no colisionen. Solución: obtener MAX(id) de los
protegidos y empezar a numerar desde ahí + 1.

### Flags nuevos

```
--partial  → solo re-clusteriza skills de grupos 'auto'
             protege 'aprobado' y 'revisado' como frozen
--preview  → muestra diff sin aplicar cambios
--full     → comportamiento actual (requiere confirmación)
```

### API route

```
POST /api/skill-equivalences/recluster
    body: { mode: 'preview' | 'apply' }

GET /api/skill-equivalences/recluster/status
    → estado: running | idle | error
    → último re-clustering: timestamp + stats
```

### UI — Botón con preview

**Ubicación:** Header de equivalencias page

```
┌────────────────────────────────────────────────┐
│ Vista previa del re-clustering                 │
│                                                │
│ Grupos 'auto' que cambiarían: 43              │
│   → 12 se dividirían                          │
│   → 8 se fusionarían                          │
│   → 23 sin cambio                             │
│                                                │
│ Protegidos (aprobado/revisado): 201 — INTACTOS│
│ Labels argentinos: 14 — INTACTOS              │
│                                                │
│ [Aplicar]  [Cancelar]                         │
└────────────────────────────────────────────────┘
```

---

## Cambios por archivo

```
Parte 0:
    database/match_ofertas_v3.py
        → save_skills_detalle(): agregar texto_original al INSERT
    database/skills_implicit_extractor.py
        → extract_declared_skills(): ya tiene texto_fuente, sin cambios
    ofertas_esco_skills_detalle (SQLite)
        → ALTER TABLE ADD COLUMN texto_original TEXT

Parte 1:
    Supabase RPC recalcular_emergentes()
        → cambiar GROUP BY a COALESCE(canonical_label, preferred_label)
        → cambiar comparación contra perfil a usar canonical

Parte 2:
    scripts/generate_equiv_candidates.py (nuevo)
        → detecta co-matcheo usando texto_original
    Supabase
        → tabla equiv_candidates + RLS
        → RPCs get_equiv_candidates, aprobar_candidato, rechazar_candidato
    UI
        → tab "Candidatos" en página equivalencias

Parte 3:
    scripts/generate_skill_equivalences.py
        → agregar --partial, --preview
        → lógica de frozen groups
    API
        → /api/skill-equivalences/recluster/
    UI
        → botón re-clustering con preview modal
```

---

## Secuencia de implementación

```
Paso 0: Persistir texto_original (prerequisito de Parte 2)
    0a. ALTER TABLE ofertas_esco_skills_detalle ADD COLUMN texto_original
    0b. Fix save_skills_detalle() para persistir texto_fuente
    0c. Tests unitarios de texto_original
    0d. Re-correr M-08 sobre sample → verificar texto_original poblado

Paso 1: Backfill equivalence_id (prerequisito de Parte 1)
    1a. Correr backfill_skill_equivalences.py completo
    1b. Verificar cobertura >= 80%

Paso 2: Parte 1 — recalcular_emergentes() con COALESCE
    2a. Migration SQL del RPC actualizado
    2b. Tests de variantes consolidadas
    2c. Smoke test: "analizar datos" + variantes → una emergente

Paso 3: Parte 2 — Candidatos
    3a. generate_equiv_candidates.py + tests
    3b. Tabla equiv_candidates + RPCs
    3c. UI tab Candidatos + tests React

Paso 4: Parte 3 — Re-clustering
    4a. --partial y --preview en script + tests
    4b. API route + UI modal + tests React

Paso 5: Smoke test end-to-end
    5a. Aprobar candidato → aparece en skill_equivalences
    5b. Re-clustering --partial → grupos aprobados intactos
    5c. recalcular_emergentes() → emergentes combinadas visibles
```

---

## Estrategia de Tests

### Estructura de archivos

```
tests/test_m08b_texto_original.py      ← Parte 0: persistencia texto_original
tests/test_m08b_emergentes.py          ← Parte 1: recalcular con COALESCE
tests/test_m08b_candidates.py          ← Parte 2: detección de candidatos
tests/test_m08b_recluster.py           ← Parte 3: frozen groups + partial
__tests__/component/m08b-candidates.test.tsx  ← React: tab candidatos
__tests__/component/m08b-recluster.test.tsx   ← React: modal re-clustering
```

### Fixtures compartidos

```
fixture: db_with_texto_original (Python)
    → SQLite en memoria con ofertas_esco_skills_detalle + texto_original
    → 5 ofertas con skills declaradas (texto_original poblado)
    → 3 ofertas con skills de tareas (texto_original = texto tarea)

fixture: db_with_equivalencias (Python)
    → SQLite + ofertas con equivalence_id y canonical_label
    → 2 variantes de "analizar datos" con mismo equiv_id
    → 1 skill sin equivalencia (fallback)

fixture: mockCandidatesRPC (React)
    → MSW handler para get_equiv_candidates
    → 3 candidatos: 1 para crear grupo, 1 para agregar a existente, 1 rechazado

fixture: mockReclusterStatus (React)
    → MSW handler para recluster status/preview
    → Preview con 43 cambios, 201 protegidos
```

---

### Parte 0 — Tests texto_original

```
test_save_skills_detalle_guarda_texto_original
    Tipo: integración (SQLite en memoria)
    Qué verifica:
      - Dado skill dict con texto_fuente="CRM"
      - save_skills_detalle() INSERT incluye texto_original="CRM"
      - SELECT confirma que el campo está poblado
    Datos: db_with_texto_original + skill dict mock

test_skills_tareas_tienen_texto_original
    Tipo: integración
    Qué verifica:
      - Skills de extract_from_tasks() tienen tarea como texto_original
      - "instalar cableado industrial" → texto_original = "instalar cableado industrial"
    Datos: oferta con tareas

test_skills_regla_texto_original_null
    Tipo: unitario
    Qué verifica:
      - Skills forzadas por regla no tienen texto_fuente
      - texto_original = NULL para skills de regla
    Datos: skill dict con origen="regla"

test_texto_original_truncado_200
    Tipo: unitario (caso borde)
    Qué verifica:
      - Texto de 500+ chars se trunca a 200 en texto_original
    Datos: tarea muy larga
```

---

### Parte 1 — Tests recalcular_emergentes

```
test_variantes_se_consolidan
    Tipo: integración (mock Supabase o SQL directo)
    Qué verifica:
      - "analizar datos" (25%) y "análisis de datos" (20%)
        con mismo equivalence_id
      - Después del COALESCE GROUP BY → una entrada con 45%
      - Label es canonical_label del grupo
    Datos: db_with_equivalencias con 2 variantes

test_sin_equivalencia_comportamiento_actual
    Tipo: regresión
    Qué verifica:
      - Skills sin equivalence_id → resultado idéntico al actual
      - COALESCE cae al fallback (preferred_label, skill_uri)
    Datos: skills sin equivalence_id

test_label_argentino_precedencia
    Tipo: unitario
    Qué verifica:
      - Grupo con label_argentino = "trabajo en equipo"
      - La emergente usa ese label, no el ESCO
    Datos: grupo con label_argentino asignado

test_umbral_combinado_detecta_emergente
    Tipo: integración
    Qué verifica:
      - Skill A 15% + Skill B 18% (ninguna supera 30%)
      - Mismo equivalence_id → combinadas 33% → emergente detectada
    Datos: 2 variantes con frecuencias que suman > 30%

test_on_conflict_actualiza_no_duplica
    Tipo: integración
    Qué verifica:
      - Si canonical_label + isco_code ya existe en emergentes_pendientes
      - El INSERT hace UPDATE (frecuencia actualizada), no fila duplicada
    Datos: emergente pre-existente + recálculo
```

---

### Parte 2 — Tests candidatos

```
test_candidato_detectado_por_co_matcheo
    Tipo: unitario
    Qué verifica:
      - texto_original "CRM" y "sistema CRM" matchean misma URI
        en 6 ofertas → candidato detectado
    Datos: db con 6 ofertas, 2 textos distintos, misma URI

test_candidato_no_detectado_bajo_umbral
    Tipo: unitario
    Qué verifica:
      - 4 co-apariciones (< 5) → no es candidato
    Datos: db con 4 ofertas

test_candidato_no_duplica_grupo_existente
    Tipo: unitario
    Qué verifica:
      - Par ya en el mismo equivalence_id → no es candidato
    Datos: 2 textos con mismo grupo en skill_equivalence_lookup

test_candidato_ignora_texto_original_null
    Tipo: unitario (caso borde)
    Qué verifica:
      - Skills con texto_original = NULL (pre-Parte 0) no generan candidatos
    Datos: mix de skills con y sin texto_original

test_tipo_c_failure_no_genera_candidato
    Tipo: unitario
    Qué verifica:
      - "DevOps" que falló umbral 0.40 → no está en skills_detalle
        → no puede generar candidato
    Datos: solo failures, sin matcheos exitosos

test_misma_fuente_distintos_textos
    Tipo: unitario
    Qué verifica:
      - "Excel" (tecnologia) y "Microsoft Excel" (tecnologia)
        matchean misma URI → candidato válido
      - Ambos vienen de la misma fuente (no requiere fuentes distintas)
    Datos: 2 textos de tecnologia_declarada, misma URI
```

---

### Parte 3 — Tests re-clustering

```
test_frozen_groups_protegidos
    Tipo: integración
    Qué verifica:
      - Grupos 'aprobado' y 'revisado' intactos después de --partial
      - Sus IDs, miembros y labels no cambian
    Datos: 3 grupos aprobados + 5 grupos auto

test_grupos_auto_se_reclusterizan
    Tipo: integración
    Qué verifica:
      - Grupos 'auto' sí se modifican en --partial
      - Pueden dividirse, fusionarse o mantenerse
    Datos: grupos auto con embeddings que cambiarían clustering

test_preview_no_aplica_cambios
    Tipo: unitario
    Qué verifica:
      - --preview genera diff (dict con cambios propuestos)
      - BD no se modifica (SELECT antes == SELECT después)
    Datos: cualquier set de grupos

test_ids_no_colisionan
    Tipo: unitario (caso borde)
    Qué verifica:
      - Nuevos grupos generados por --partial tienen IDs
        que no colisionan con grupos protegidos
      - Si protegidos usan EQ-00001 a EQ-00500,
        nuevos empiezan desde EQ-00501
    Datos: grupos protegidos con IDs conocidos

test_updated_at_cambia_post_recluster
    Tipo: integración
    Qué verifica:
      - Después de --partial --apply, updated_at cambia
      - Staleness check lo detecta en próximo run
    Datos: mock Supabase con updated_at anterior
```

---

### React — Tab Candidatos

```
test_candidatos_listados
    Tipo: componente React
    Qué verifica:
      - GET get_equiv_candidates retorna 3 candidatos
      - Se muestran con URI, términos, co-apariciones
    Datos: mockCandidatesRPC

test_aprobar_crear_grupo
    Tipo: componente React
    Qué verifica:
      - Click "Crear grupo" llama aprobar_candidato con action='crear_grupo'
      - Candidato desaparece de la lista de pendientes
    Datos: mockCandidatesRPC + mock de aprobar

test_aprobar_agregar_a_existente
    Tipo: componente React
    Qué verifica:
      - Candidato con grupo existente muestra "Agregar a EQ-XXX"
      - Click llama aprobar_candidato con action='agregar_a_grupo'
    Datos: mockCandidatesRPC con grupo existente

test_rechazar_candidato
    Tipo: componente React
    Qué verifica:
      - Click "Rechazar" llama rechazar_candidato
      - Candidato desaparece
    Datos: mockCandidatesRPC
```

---

### React — Modal Re-clustering

```
test_preview_muestra_diff
    Tipo: componente React
    Qué verifica:
      - Click "Re-clustering" abre modal
      - Modal muestra: grupos que cambiarían, protegidos, labels intactos
    Datos: mockReclusterStatus con preview data

test_frozen_groups_en_preview
    Tipo: componente React
    Qué verifica:
      - Preview muestra "201 protegidos — INTACTOS" claramente
      - "14 labels argentinos — INTACTOS"
    Datos: mockReclusterStatus

test_aplicar_cierra_modal_y_refresca
    Tipo: componente React
    Qué verifica:
      - Click "Aplicar" llama POST recluster con mode='apply'
      - Modal se cierra, lista se refresca
    Datos: mock de apply endpoint
```

---

### Regresión

```
test_perfil_argentino_sin_equivalencias_no_rompe
    Tipo: regresión SQL
    Qué verifica:
      - recalcular_emergentes() con 0% cobertura de equivalence_id
      - Resultado idéntico al actual (COALESCE fallback)
    Datos: ofertas_skills sin equivalence_id

test_matching_usa_grupos_actualizados
    Tipo: regresión Python
    Qué verifica:
      - Después de aprobar candidato que modifica skill_equivalences
      - Staleness check en próximo run detecta cambio
      - Matching usa lookup actualizado
    Datos: grupo aprobado + run de matching

test_save_skills_detalle_backward_compatible
    Tipo: regresión Python
    Qué verifica:
      - Skills sin texto_fuente en el dict → texto_original = NULL
      - No rompe el INSERT existente
    Datos: skill dict legacy sin texto_fuente

test_107_tests_python_en_verde
    Tipo: regresión suite
    Qué verifica: todos los tests Python existentes pasan

test_933_tests_react_en_verde
    Tipo: regresión suite
    Qué verifica: todos los tests React existentes pasan
```

---

### Casos borde

```
test_texto_original_caracteres_especiales
    Tipo: unitario
    Qué verifica:
      - texto_original con comillas, punto y coma, unicode
      - INSERT no falla, SELECT retorna correctamente
    Datos: "C++", "gestión", "résumé", "worker's comp"

test_candidato_con_3_textos_distintos
    Tipo: unitario
    Qué verifica:
      - 3 textos distintos matchean misma URI → genera 3 pares candidatos
        (A↔B, A↔C, B↔C)
      - O un solo candidato con los 3 (decisión de diseño)
    Datos: 3 textos, 1 URI, 7 ofertas

test_recluster_sin_grupos_auto
    Tipo: unitario (caso borde)
    Qué verifica:
      - Si todos los grupos son aprobados/revisados (0 auto)
      - --partial retorna "nada que re-clusterizar"
      - No modifica nada
    Datos: todos los grupos con estado != 'auto'

test_backfill_ofertas_sin_skills
    Tipo: regresión
    Qué verifica:
      - Ofertas con 0 skills en ofertas_esco_skills_detalle
      - save_skills_detalle() con lista vacía → no INSERT, no error
    Datos: oferta sin skills matcheadas
```

---

### Implementabilidad con infraestructura existente

| Aspecto | Estado |
|---------|--------|
| SQLite en memoria para tests | ✅ Usado en M-06, M-08 |
| Mock Supabase RPC (Python) | ✅ Usado en M-01 |
| MSW handlers (React) | ✅ Agregar para equiv_candidates + recluster |
| embeddings ESCO para tests clustering | ✅ Disponibles en disco |
| save_skills_detalle() accesible | ✅ Método de MatcherV3 |
| backfill_skill_equivalences.py | ✅ Existe |
| vitest + testing-library | ✅ 933+ tests existentes |

**Todos los tests son implementables** con la infraestructura existente.

---

## Criterio de done

```
Parte 0:
□ ALTER TABLE texto_original ejecutado
□ save_skills_detalle() persiste texto_fuente → texto_original
□ Re-correr M-08 sobre 10 ofertas → texto_original poblado
□ 4 tests Parte 0 pasando

Parte 1:
□ Backfill equivalence_id >= 80%
□ recalcular_emergentes() usa COALESCE
□ Emergentes combinadas se detectan
□ Label argentino tiene precedencia
□ 5 tests Parte 1 pasando
□ Smoke test: "analizar datos" + variantes → una emergente

Parte 2:
□ generate_equiv_candidates.py detecta candidatos
□ Tabla equiv_candidates creada con RLS + RPCs
□ Tab "Candidatos" visible con workflow aprobación
□ 6 tests Parte 2 pasando
□ 4 tests React Candidatos pasando
□ Smoke test: correr script → ver candidatos en UI

Parte 3:
□ --partial protege grupos aprobados/revisados
□ --preview muestra diff sin aplicar
□ IDs no colisionan con protegidos
□ Botón re-clustering con preview modal
□ 5 tests Parte 3 pasando
□ 3 tests React Re-clustering pasando
□ Smoke test: --partial → aprobados intactos

Regresión:
□ 5 tests regresión pasando
□ 4 tests casos borde pasando
□ 107+ tests Python en verde
□ 933+ tests React en verde
```

---

## Lo que NO hace este spec

- No crea skills Tipo C sin URI ESCO (M-13)
- No resuelve el sync incremental de skills reprocesadas (issue separado)
- No fine-tunea embeddings (M-17)
- No automatiza aprobación de candidatos — siempre requiere humano
- No cambia el umbral de clustering de 0.85
