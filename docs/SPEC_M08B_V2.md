# M-08b — Equivalencias: Cerrar el Loop

> **Estado:** ⬜ No iniciado  
> **Prioridad:** ALTO  
> **Prerequisito de:** M-08 ✅, SPEC_EQUIV_UI_MEJORAS_V2 ✅  
> **Versión:** 2.0 — Reescrita después de entender el objetivo real

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
1.292 grupos con scores de confianza. Pero el agrupamiento no llega
a los lugares donde se toman decisiones:

```
recalcular_emergentes()  → agrupa por label textual, ignora equivalencias
Perfil Argentino         → cuenta variantes por separado
Dashboard de analistas   → ve fragmentación, no demanda real
```

El conocimiento curado por los analistas (201 grupos aprobados,
14 con label_argentino) existe pero no circula. Es exactamente el
problema del diagnóstico sistémico — el sistema genera conocimiento
pero no lo acumula.

---

## Objetivo

Cerrar el loop de tres formas:

```
Parte 1 → El Perfil Argentino usa equivalencias para contar
           demanda real visible, emergentes que hoy no se detectan

Parte 2 → El mercado alimenta el sistema de equivalencias
           candidatos desde co-matcheo de skills declaradas

Parte 3 → El analista puede mejorar el clustering
           re-clustering controlado con frozen groups
```

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
Es el único lugar del sistema que ya resuelve este problema — M-08b
lo lleva a `recalcular_emergentes()`.

**Comparación contra el perfil consolidado:**

Opción B (sin cambiar schema de esco_argentino):
```sql
-- Hoy:
LOWER(ps.skill) = LOWER(sf.skill_label)

-- Con M-08b:
LOWER(ps.skill) = LOWER(COALESCE(sf.canonical_label, sf.skill_label))
```

Las skills con el mismo representante canónico se agrupan y la
frecuencia se suma. Sin cambiar el JSONB de esco_argentino.

### El label que se muestra

Precedencia para el label visible:
```
1. label_argentino del grupo (si existe) — vocabulario del mercado ARG
2. canonical_label del representante — label ESCO del más frecuente
3. preferred_label — label original (fallback)
```

Esta precedencia ya existe en la UI de equivalencias — M-08b la
replica en `recalcular_emergentes()`.

### Backfill de equivalence_id

**Cobertura actual:** 23.5% (83.357 de 355.019 filas en ofertas_skills)

Para que el cambio tenga impacto máximo, correr
`backfill_skill_equivalences.py` completo antes de aplicar el cambio
en el RPC. El diseño del GROUP BY con COALESCE funciona con cualquier
cobertura — las filas sin equivalence_id usan skill_uri como fallback
(comportamiento actual), sin romper nada.

**Meta de cobertura post-backfill:** 80%+

### Impacto esperado

Con los datos actuales y 23.5% de cobertura:
- Skills que hoy están fragmentadas en 2-3 variantes se consolidan
- Emergentes que no superaban el umbral de 30% individualmente
  pero sí combinadas empiezan a detectarse
- El Perfil Argentino muestra el nombre canónico (o argentino) en
  lugar de la variante que matcheó por casualidad

Con 80%+ de cobertura post-backfill el impacto se multiplica.

---

## Parte 2 — Candidatos desde fuentes declaradas

### Lógica de detección

Un par de términos es candidato a equivalencia cuando:

```
término_A y término_B
    → matchean contra la misma URI ESCO
    → en al menos 5 ofertas distintas
    → con score promedio >= 0.40
    → NO están ya en el mismo grupo de equivalencia
```

**Ejemplo real de los datos:**
```
"CRM" (tecnologia_declarada) → URI gestionar_relaciones_clientes
"sistema CRM" (herramienta_declarada) → misma URI
Co-aparición: 12 ofertas → candidato a grupo
```

### Script de detección

**Archivo:** `scripts/generate_equiv_candidates.py` (nuevo)

Proceso:
1. Leer `ofertas_esco_skills_detalle` local (SQLite)
2. Filtrar skills de fuentes declaradas (M-08):
   `skill_tipo_fuente IN ('skills_nlp_declarada',
   'tecnologia_declarada', 'herramienta_declarada',
   'soft_skill_declarada')`
3. Agrupar por `skill_uri` — para cada URI, listar
   todos los términos declarados que matchearon
4. Para cada URI con 2+ términos distintos:
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

CREATE INDEX idx_candidates_uri        ON equiv_candidates(uri_esco);
CREATE INDEX idx_candidates_estado     ON equiv_candidates(estado);
CREATE INDEX idx_candidates_coapar     ON equiv_candidates(co_apariciones DESC);

ALTER TABLE equiv_candidates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "platform_admin_only" ON equiv_candidates
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'platform_admin');
```

### RPCs

```sql
-- Listar candidatos con filtros
get_equiv_candidates(estado TEXT, limit_n INT)

-- Aprobar: crea grupo nuevo o agrega a existente
aprobar_candidato(candidate_id BIGINT, action TEXT)
    -- action: 'crear_grupo' | 'agregar_a_grupo'
    -- si crear_grupo: INSERT en skill_equivalences con estado='aprobado'
    -- si agregar_a_grupo: INSERT en skill_equivalence_lookup

-- Rechazar
rechazar_candidato(candidate_id BIGINT)
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
│ [Aprobar → crear grupo]  [Rechazar]  [Ver ofertas]│
├──────────────────────────────────────────────────┤
│ URI: trabajar en equipo                          │
│ "trabajo en equipo" ↔ "teamwork"  8 ofertas     │
│ [Aprobar → agregar a EQ-001]  [Rechazar]        │
└──────────────────────────────────────────────────┘
```

**Dos tipos de aprobación:**
- Sin grupo existente → "Crear grupo" → grupo nuevo con
  estado='aprobado' directamente
- Con grupo existente → "Agregar a grupo EQ-XXX" → nuevo
  miembro en skill_equivalence_lookup

---

## Parte 3 — Re-clustering controlado

### Principio: Frozen Groups

```
'aprobado' → PROTEGIDO — el algoritmo no lo toca
'revisado' → PROTEGIDO — idem
'auto'     → LIBRE — el algoritmo puede modificarlo
```

### Botón en la UI

**Ubicación:** Header de
`/admin/procesamiento/fabrica/equivalencias`

Al clickear → modal de preview:

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

### Script modificado

**Archivo:** `scripts/generate_skill_equivalences.py`

Agregar flags:
```
--partial  → solo re-clusteriza grupos 'auto'
             respeta 'aprobado' y 'revisado' como frozen
--preview  → muestra diff sin aplicar cambios
--full     → comportamiento actual (requiere confirmación)
```

### API route

**Archivo:** `app/api/skill-equivalences/recluster/route.ts` (nuevo)

```
POST /api/skill-equivalences/recluster
    body: { mode: 'preview' | 'apply' }

GET /api/skill-equivalences/recluster/status
    → estado: running | idle | error
    → último re-clustering: timestamp + stats
```

El proceso corre en background — la UI hace polling al status.

---

## Secuencia de implementación

```
1. Backfill completo de equivalence_id (operativo, pre-requisito)
   → correr backfill_skill_equivalences.py
   → verificar cobertura >= 80%

2. Parte 1: cambio en recalcular_emergentes()
   → migration SQL con el nuevo GROUP BY
   → tests de que emergentes combinadas se detectan
   → verificar con ejemplo concreto:
     "analizar datos" + variantes → una emergente con frecuencia real

3. Parte 2: generate_equiv_candidates.py + tabla equiv_candidates
   → tests del script de detección
   → RPCs de aprobación/rechazo

4. Parte 2 UI: tab "Candidatos"
   → tests React de la tab
   → smoke test: aprobar candidato → aparece en skill_equivalences

5. Parte 3: flags --partial y --preview en script
   → tests de frozen groups
   → API route de re-clustering

6. Parte 3 UI: botón con preview y polling
   → tests React del modal
   → smoke test end-to-end
```

---

## Tests requeridos

```
Python — Parte 1 (recalcular_emergentes):
test_variantes_se_consolidan()
    → dado "analizar datos" (25%) y "análisis de datos" (20%)
    → con mismo equivalence_id
    → recalcular_emergentes() devuelve una sola entrada con 45%
    → label es el canonical_label del grupo

test_sin_equivalencia_comportamiento_actual()
    → dado skills sin equivalence_id
    → recalcular_emergentes() devuelve resultado idéntico al actual
    → sin regresión

test_label_argentino_tiene_precedencia()
    → dado grupo con label_argentino = "trabajo en equipo"
    → la emergente detectada usa ese label, no el ESCO

test_umbral_combinado_detecta_emergente()
    → skill A en 15%, skill B en 18% (ninguna supera 30%)
    → combinadas 33% → se detecta como emergente

Python — Parte 2 (candidatos):
test_candidato_detectado_por_co_matcheo()
    → dos términos que matchean misma URI en 6 ofertas → candidato

test_candidato_no_detectado_bajo_umbral()
    → 4 co-apariciones (< 5) → no es candidato

test_candidato_no_duplica_grupo_existente()
    → par ya en el mismo grupo → no es candidato

test_tipo_c_no_genera_candidato()
    → "DevOps" que falló umbral 0.40 → no es candidato

Python — Parte 3 (re-clustering):
test_frozen_groups_protegidos()
    → grupos 'aprobado' y 'revisado' intactos después de --partial

test_grupos_auto_se_reclusterizan()
    → grupos 'auto' sí se modifican en --partial

test_preview_no_aplica_cambios()
    → --preview genera diff sin modificar BD

test_updated_at_cambia_post_recluster()
    → staleness check lo detecta en próximo run

React — Tab candidatos:
test_candidatos_listados()
test_aprobar_crea_grupo()
test_aprobar_agrega_a_grupo_existente()
test_rechazar_candidato()

React — Botón re-clustering:
test_preview_muestra_diff()
test_frozen_groups_en_preview()
test_polling_durante_proceso()

Regresión:
test_perfil_argentino_no_rompe_sin_equivalencias()
test_matching_usa_grupos_actualizados()
test_97_tests_python_en_verde()
test_933_tests_react_en_verde()
```

---

## Criterio de done

```
□ Backfill equivalence_id >= 80% de cobertura
□ recalcular_emergentes() usa COALESCE(canonical_label, preferred_label)
□ Emergentes combinadas se detectan correctamente
□ Label argentino tiene precedencia en el label visible
□ generate_equiv_candidates.py detecta candidatos
□ tabla equiv_candidates creada con RLS y RPCs
□ Tab "Candidatos" visible con workflow de aprobación
□ Aprobar candidato → aparece en skill_equivalences
□ Script --partial protege grupos aprobados/revisados
□ Botón re-clustering muestra preview con diff
□ Re-clustering --apply actualiza updated_at
□ Staleness check detecta cambio en próximo run
□ 23 tests pasando
□ Smoke test Parte 1:
  "analizar datos" + variantes → una emergente con frecuencia real
□ Smoke test Parte 2:
  Correr generate_equiv_candidates.py → ver candidatos en UI
□ Smoke test Parte 3:
  Re-clustering --partial → grupos aprobados intactos
□ No regresión: 97 tests Python en verde
□ No regresión: 933 tests React en verde
```

---

## Lo que NO hace este spec

- No crea skills Tipo C sin URI ESCO (M-13)
- No resuelve el sync de skills de M-08 a Supabase (issue separado)
- No fine-tunea embeddings (M-17)
- No automatiza aprobación de candidatos — siempre requiere humano
- No cambia el umbral de clustering de 0.85
