# SPEC — Mejoras UI de Equivalencias de Skills (v2)

> **Estado:** ⬜ No iniciado
> **Prioridad:** ALTO
> **Prerequisito de:** M-08b (generación de candidatos nuevos)
> **Supersede:** SPEC_EQUIV_UI_MEJORAS.md (v1, corregida por 3 ajustes técnicos)
> **Contexto:** Antes de agregar más candidatos automáticos con M-08b,
> hay que cerrar tres gaps que hacen que la aprobación humana no tenga
> efecto real en el matching.

---

## Problema que resuelve

El sistema de equivalencias tiene tres gaps que lo hacen inefectivo:

**Gap 1 — Aprobación sin efecto real**
```
Analista aprueba grupo
    → estado = 'aprobado' en Supabase
    → extractor sigue usando cache anterior (singleton)
    → el matching NO cambia hasta proceso manual
```
Los 201 grupos "aprobados" pueden no estar activos en el matching.

**Gap 2 — Sin score de confianza**
```
799 grupos automáticos sin revisar
    → analista no sabe cuáles son más confiables
    → no puede priorizar qué revisar primero
    → revisa por frecuencia pero no por calidad
```

**Gap 3 — Sin impacto visible**
```
Analista aprueba un grupo
    → no sabe qué ocupaciones afecta
    → no sabe cuántas ofertas impacta
    → no puede evaluar si la decisión es correcta
```

---

## Correcciones respecto a v1

La v1 tenía 3 problemas identificados al verificar contra el código real:

1. **`updated_at` ya existe:** La migration para agregar la columna y
   el trigger no es necesaria — `skill_equivalences` ya tiene `updated_at`
   en Supabase. La v2 solo crea el RPC `get_latest_equiv_update()`.

2. **Staleness check en lugar incorrecto:** La v1 proponía verificar
   staleness dentro del extractor (singleton). Pero el extractor se
   inicializa una vez y se reutiliza. El check debe ir en
   `run_matching_pipeline()` (el orquestador), antes del loop de ofertas,
   donde se puede forzar una recarga sin modificar la API del extractor.

3. **RPC con CROSS JOIN inválido:** El SQL de `get_equivalencia_impacto()`
   usaba un CROSS JOIN con subconsulta que referencia la tabla externa —
   no es válido en PostgreSQL. La v2 usa CTE. Además, requiere que
   `equivalence_id` en `ofertas_skills` esté poblado (>80%), lo cual
   hay que verificar y backfillear si es necesario.

---

## Decisiones de diseño

### Alcance

Este spec cierra los tres gaps en este orden de prioridad:

1. **Regeneración automática del lookup** — el más crítico porque
   sin esto ninguna aprobación tiene efecto
2. **Score de confianza** — habilita priorización inteligente
3. **Impacto en Perfil Argentino** — habilita decisión informada

### Regeneración: cuándo y cómo

```
Momento A — Al iniciar un run de matching
    run_matching_pipeline() verifica si hubo cambios
    en skill_equivalences desde la última carga
    → si sí: recarga equiv_lookup desde Supabase
    → si no: usa cache existente
    → automático, sin intervención manual

Momento B — Post-regeneración de clustering
    generate_skill_equivalences.py reconstruye todo
    → este flujo ya existe, no cambia
```

El Momento A es el gap crítico que hay que cerrar. No se recarga por
cada aprobación individual — se recarga al iniciar el próximo run.
Esto es suficiente porque el matching no corre en tiempo real.

---

## Componente 1 — Regeneración automática del lookup

### RPC nuevo

```sql
CREATE OR REPLACE FUNCTION get_latest_equiv_update()
RETURNS TIMESTAMPTZ
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT MAX(updated_at) FROM skill_equivalences;
$$;
```

### Modificación en run_matching_pipeline()

**Archivo:** `database/match_ofertas_v3.py` — función `run_matching_pipeline()`

Antes del loop de ofertas (después de crear el matcher, línea ~1875),
agregar verificación de staleness:

```python
# Antes del loop:
matcher = MatcherV3(db_conn=conn, verbose=verbose)

# M-08c: Verificar si equiv_lookup está desactualizado
try:
    from supabase import create_client
    config = json.load(open('config/supabase_config.json'))
    sb = create_client(config['url'], config['anon_key'])
    latest = sb.rpc('get_latest_equiv_update').execute()
    if latest.data:
        from datetime import datetime
        latest_update = datetime.fromisoformat(latest.data.replace('Z', '+00:00'))
        # Si el extractor se inicializó antes del último cambio, recargar
        if not hasattr(SkillsImplicitExtractor, '_equiv_loaded_at') or \
           latest_update > SkillsImplicitExtractor._equiv_loaded_at:
            SkillsImplicitExtractor._equiv_lookup = None
            SkillsImplicitExtractor._equiv_groups = None
            SkillsImplicitExtractor._initialized = False
            # Re-inicializar matcher (recarga extractor)
            matcher = MatcherV3(db_conn=conn, verbose=verbose)
            if verbose:
                print(f"[EQUIV] Lookup recargado (último cambio: {latest.data})")
except Exception as e:
    if verbose:
        print(f"[EQUIV] WARN: No se pudo verificar staleness: {e}")

# Loop de ofertas continúa...
```

### Modificación en SkillsImplicitExtractor

**Archivo:** `database/skills_implicit_extractor.py`

Al final de `_initialize()`, registrar timestamp de carga:

```python
from datetime import datetime, timezone
SkillsImplicitExtractor._equiv_loaded_at = datetime.now(timezone.utc)
```

### Comportamiento

- Primer run después de aprobación: recarga automática (~2-3 seg extra por query a Supabase)
- Runs sin cambios: sin overhead (una sola query SELECT MAX)
- Si Supabase no responde: fallo silencioso, usa cache anterior
- No requiere reiniciar nada manualmente

---

## Componente 2 — Score de confianza del clustering

### Script generador

**Archivo:** `scripts/generate_skill_equivalences.py`

Al momento del clustering, los embeddings y la membresía ya están.
Agregar cálculo de similitud por grupo:

```python
from sklearn.metrics.pairwise import cosine_similarity

def calculate_group_similarity(embeddings, indices):
    """Calcula similitud promedio y mínima entre miembros del grupo."""
    if len(indices) < 2:
        return 1.0, 1.0  # grupo de 1 = confianza perfecta
    group_embs = embeddings[indices]
    sim_matrix = cosine_similarity(group_embs)
    # Excluir diagonal (similitud consigo mismo = 1.0)
    n = len(indices)
    pairwise_sims = []
    for i in range(n):
        for j in range(i+1, n):
            pairwise_sims.append(sim_matrix[i][j])
    return float(np.mean(pairwise_sims)), float(np.min(pairwise_sims))
```

Llamar en `build_equivalence_table()` para cada grupo y agregar
al dict del grupo:

```python
sim_avg, sim_min = calculate_group_similarity(embeddings, indices)
equiv_table.append({
    ...,
    'similitud_promedio': round(sim_avg, 4),
    'similitud_minima': round(sim_min, 4),
})
```

### Migration SQL

```sql
ALTER TABLE skill_equivalences
ADD COLUMN IF NOT EXISTS similitud_promedio REAL;

ALTER TABLE skill_equivalences
ADD COLUMN IF NOT EXISTS similitud_minima REAL;
```

### Backfill retroactivo de los 1,000 grupos existentes

**Archivo:** Nuevo script `scripts/backfill_equiv_similarity.py`

Los 1,000 grupos existentes no tienen score de similitud.
Los embeddings ESCO no cambiaron — se puede calcular retroactivamente:

1. Cargar embeddings de `embeddings/esco_skills_embeddings_full.npy`
2. Cargar metadata de `embeddings/esco_skills_metadata_full.json`
3. Para cada grupo en `skill_equivalences`:
   - Obtener URIs de los miembros
   - Encontrar los índices correspondientes en los embeddings
   - Calcular similitud promedio y mínima
   - UPDATE en Supabase

Esto es un one-time script que corre en ~30 segundos
(1,000 grupos × cálculo de matriz pequeña).

### UI: mostrar confianza por grupo

En cada card de grupo (colapsado), agregar junto al badge de estado:

```
analizar datos  [auto]  ●●●○  92% similitud
3 equivalentes · 5.772 apariciones
```

**Código de colores:**
```
similitud >= 0.92  → ●●●●  verde   (alta confianza, aprobar con seguridad)
similitud 0.88-0.92 → ●●●○  azul   (buena confianza)
similitud 0.85-0.88 → ●●○○  amarillo (confianza media, revisar)
similitud < 0.85   → ●○○○  rojo    (baja confianza, revisar con cuidado)
```

### Priorización inteligente en filtros

Agregar opción de ordenamiento además de "por frecuencia":

```
Ordenar por:  [Frecuencia ▼]  [Confianza ▼]  [Confianza ▲ (revisar primero)]
```

"Confianza ▲" muestra primero los grupos con `similitud_minima` baja —
los que más necesitan revisión humana.

El API `/api/skill-equivalences` ya soporta `sort` — agregar
`similitud_promedio` y `similitud_minima` como opciones de ordenamiento.

---

## Componente 3 — Impacto en Perfil Argentino

### Prerequisito: verificar cobertura de equivalence_id

Antes de implementar el RPC de impacto, verificar qué proporción de
`ofertas_skills` tiene `equivalence_id` poblado.

```sql
SELECT
    COUNT(*) FILTER (WHERE equivalence_id IS NOT NULL) as con_equiv,
    COUNT(*) as total,
    ROUND(COUNT(*) FILTER (WHERE equivalence_id IS NOT NULL)::REAL / COUNT(*) * 100, 1) as pct
FROM ofertas_skills;
```

Si el porcentaje es < 80%, correr `scripts/exports/backfill_skill_equivalences.py`
antes de implementar el RPC. Sin este backfill, el impacto mostrado
será parcial y engañoso.

### RPC nuevo (corregido — usa CTE)

```sql
CREATE OR REPLACE FUNCTION get_equivalencia_impacto(p_equivalence_id TEXT)
RETURNS TABLE (
    isco_code TEXT,
    ocupacion_label TEXT,
    ofertas_count BIGINT,
    pct_de_ocupacion REAL
)
LANGUAGE sql SECURITY DEFINER
AS $$
    WITH ofertas_del_grupo AS (
        SELECT DISTINCT os.id_oferta
        FROM ofertas_skills os
        WHERE os.equivalence_id = p_equivalence_id
    ),
    totales_por_isco AS (
        SELECT d.isco_code, COUNT(DISTINCT d.id_oferta) as total_ocupacion
        FROM ofertas_dashboard d
        GROUP BY d.isco_code
    )
    SELECT
        d.isco_code,
        d.isco_label as ocupacion_label,
        COUNT(DISTINCT og.id_oferta) as ofertas_count,
        ROUND(
            COUNT(DISTINCT og.id_oferta)::REAL /
            NULLIF(t.total_ocupacion, 0) * 100, 1
        ) as pct_de_ocupacion
    FROM ofertas_del_grupo og
    JOIN ofertas_dashboard d ON og.id_oferta = d.id_oferta
    LEFT JOIN totales_por_isco t ON d.isco_code = t.isco_code
    GROUP BY d.isco_code, d.isco_label, t.total_ocupacion
    ORDER BY ofertas_count DESC
    LIMIT 5;
$$;
```

### UI: panel de impacto en modo expandido

Cuando el analista expande un grupo, agregar sección "Impacto en
ocupaciones" que se carga lazy (al expandir, no al listar):

```
▼ analizar datos  [auto]  ●●●●  92%

  Skills equivalentes:
  • analizar datos (representante) · 3.828 ofertas
  • realizar un análisis de datos · 987 ofertas
  • análisis de datos · 957 ofertas

  Impacto en ocupaciones:                    ← NUEVO
  • Analista de datos (2511)     · 1.842 ofertas (38%)
  • Científico de datos (2519)   · 923 ofertas  (19%)
  • Analista financiero (2413)   · 445 ofertas  (9%)

  [Aprobar ✓]  [Editar ✏]  [Revertir ↩]
```

La carga lazy se implementa con un `useEffect` condicionado al
estado de expansión del grupo. El RPC solo se llama cuando el
analista expande la card, no al cargar la lista.

---

## Cambios por archivo

```
Python (extractor):
    database/skills_implicit_extractor.py
        → _equiv_loaded_at timestamp al final de _initialize()

Python (pipeline):
    database/match_ofertas_v3.py (run_matching_pipeline)
        → staleness check antes del loop de ofertas

Python (script generador):
    scripts/generate_skill_equivalences.py
        → calculate_group_similarity() para nuevos grupos
        → guardar similitud_promedio y similitud_minima

Python (script backfill):
    scripts/backfill_equiv_similarity.py (NUEVO)
        → calcular similitud retroactiva para 1,000 grupos existentes

Supabase (migrations):
    → ADD COLUMN similitud_promedio, similitud_minima
    → RPC get_latest_equiv_update()
    → RPC get_equivalencia_impacto() (con CTE)

Next.js (UI):
    app/admin/procesamiento/fabrica/equivalencias/page.tsx
        → badge de confianza con código de colores en cards colapsadas
        → dropdown de ordenamiento (frecuencia / confianza ▼ / confianza ▲)
        → panel de impacto en ocupaciones en modo expandido (lazy)

Next.js (API):
    app/api/skill-equivalences/route.ts
        → agregar sort by similitud_promedio / similitud_minima
```

---

## Estrategia de Tests

### Estructura de archivos

```
tests/test_equiv_staleness.py             ← Python: staleness + recarga
tests/test_equiv_similarity.py            ← Python: cálculo de similitudes
__tests__/component/equiv-ui-mejoras.test.tsx  ← React: badge + impacto + sort
```

### Fixtures

```
fixture: embeddings_3_skills (Python)
    → 3 embeddings de dim 32 con similitudes controladas:
      skill_A y skill_B: similitud ~0.95 (alta)
      skill_A y skill_C: similitud ~0.86 (media)
      skill_B y skill_C: similitud ~0.87 (media)
    → similitud_promedio esperada: ~0.893
    → similitud_minima esperada: ~0.86

fixture: embeddings_2_skills_identicas (Python)
    → 2 embeddings casi idénticos: similitud ~0.99
    → similitud_promedio = similitud_minima ≈ 0.99

fixture: mock_supabase_equiv (Python)
    → Mock del Supabase client que retorna:
      get_latest_equiv_update() → timestamp configurable
      skill_equivalences → lista de grupos mock
      skill_equivalence_lookup → lista de URIs mock

fixture: mockEquivWithSimilarity (React)
    → Fixture para MSW handler:
      GET /api/skill-equivalences → grupos con similitud_promedio/minima
      POST get_equivalencia_impacto → datos de impacto por ocupación

fixture: mockEquivImpacto (React)
    → Datos de impacto para lazy load:
      [{isco_code: "2511", ocupacion_label: "Analista de datos",
        ofertas_count: 1842, pct_de_ocupacion: 38.2}, ...]
```

---

### Nivel 1 — Python: Staleness y recarga

```
test_staleness_detecta_cambio
    Tipo: unitario (mock Supabase)
    Qué verifica:
      - _equiv_loaded_at = 2026-03-30T10:00:00
      - get_latest_equiv_update() retorna 2026-03-31T14:00:00
      - El sistema detecta que hay que recargar
    Datos: mock_supabase_equiv con timestamp posterior
    Output: SkillsImplicitExtractor._initialized = False (forzar reinit)

test_staleness_sin_cambio
    Tipo: unitario (mock Supabase)
    Qué verifica:
      - _equiv_loaded_at = 2026-03-31T14:00:00
      - get_latest_equiv_update() retorna 2026-03-30T10:00:00
      - No se recarga (performance)
    Datos: mock_supabase_equiv con timestamp anterior
    Output: _initialized sigue True, no se recarga

test_staleness_supabase_falla_silencioso
    Tipo: unitario
    Qué verifica:
      - Si Supabase no responde, el pipeline continúa con cache anterior
      - No lanza excepción
    Datos: mock que lanza ConnectionError
    Output: matcher funciona normal

test_recarga_actualiza_equiv_lookup
    Tipo: integración (mock Supabase)
    Qué verifica:
      - Después de detectar cambio, _equiv_lookup tiene los datos nuevos
      - Después de detectar cambio, _equiv_groups tiene labels actualizados
    Datos: mock con grupo EQ-001 que cambió label_argentino
    Output: equiv_groups["EQ-001"]["label"] refleja el cambio

test_equiv_loaded_at_se_registra
    Tipo: unitario
    Qué verifica:
      - Después de _initialize(), _equiv_loaded_at tiene timestamp actual
      - Es de tipo datetime con timezone UTC
    Datos: extractor nuevo
    Output: _equiv_loaded_at != None, es datetime reciente
```

---

### Nivel 2 — Python: Cálculo de similitudes

```
test_similitud_3_miembros
    Tipo: unitario
    Qué verifica:
      - Dado grupo con 3 embeddings de similitudes conocidas
      - similitud_promedio = mean de los 3 pares
      - similitud_minima = min de los 3 pares
    Datos: embeddings_3_skills
    Output: valores dentro de ±0.01 del esperado

test_similitud_2_miembros_identicos
    Tipo: unitario
    Qué verifica:
      - Grupo con 2 embeddings casi iguales
      - similitud_promedio ≈ similitud_minima ≈ 0.99
    Datos: embeddings_2_skills_identicas
    Output: ambos > 0.98

test_similitud_grupo_1_miembro
    Tipo: unitario (caso borde)
    Qué verifica:
      - Grupo con 1 solo miembro (no hay pares)
      - Retorna (1.0, 1.0) — confianza perfecta por default
    Datos: 1 embedding
    Output: (1.0, 1.0)

test_similitud_se_guarda_en_dict
    Tipo: unitario
    Qué verifica:
      - build_equivalence_table() incluye similitud_promedio y
        similitud_minima en cada grupo del resultado
    Datos: embeddings mock + metadata mock + frequencies mock
    Output: cada dict en equiv_table tiene los 2 campos con float

test_backfill_calcula_retroactivo
    Tipo: integración (mock Supabase)
    Qué verifica:
      - Dado 3 grupos existentes sin similitud
      - El backfill calcula y actualiza los 3
      - Los valores son float entre 0 y 1
    Datos: embeddings reales + 3 grupos mock en Supabase
    Output: 3 UPDATEs exitosos con similitud > 0
```

---

### Nivel 3 — React: Badge de confianza

```
test_badge_confianza_verde
    Tipo: componente React
    Qué verifica:
      - Grupo con similitud_promedio = 0.95
      - Muestra 4 indicadores verdes
    Datos: mockEquivWithSimilarity con sim=0.95
    Output: 4 elementos con clase verde

test_badge_confianza_azul
    Tipo: componente React
    Qué verifica:
      - similitud_promedio = 0.90 → 3 indicadores azules
    Datos: mockEquivWithSimilarity con sim=0.90

test_badge_confianza_amarillo
    Tipo: componente React
    Qué verifica:
      - similitud_promedio = 0.86 → 2 indicadores amarillos
    Datos: mockEquivWithSimilarity con sim=0.86

test_badge_confianza_rojo
    Tipo: componente React
    Qué verifica:
      - similitud_promedio = 0.83 → 1 indicador rojo
    Datos: mockEquivWithSimilarity con sim=0.83

test_badge_sin_similitud
    Tipo: componente React (caso borde)
    Qué verifica:
      - Grupo con similitud_promedio = null (pre-backfill)
      - No muestra badge de confianza (no crashea)
    Datos: mockEquivWithSimilarity con sim=null
```

---

### Nivel 4 — React: Ordenamiento

```
test_ordenamiento_por_frecuencia_default
    Tipo: componente React
    Qué verifica:
      - Por default, grupos ordenados por frecuencia_total DESC
      - El primer grupo tiene mayor frecuencia
    Datos: mockEquivWithSimilarity con 3 grupos de distintas frecuencias

test_ordenamiento_confianza_descendente
    Tipo: componente React
    Qué verifica:
      - Al seleccionar "Confianza ▼"
      - El primer grupo tiene mayor similitud_promedio
    Datos: 3 grupos con similitudes distintas

test_ordenamiento_confianza_ascendente
    Tipo: componente React
    Qué verifica:
      - Al seleccionar "Confianza ▲ (revisar primero)"
      - El primer grupo tiene menor similitud_minima
    Datos: 3 grupos con similitudes distintas
```

---

### Nivel 5 — React: Impacto en ocupaciones

```
test_impacto_carga_lazy
    Tipo: componente React
    Qué verifica:
      - Al expandir grupo → llama a get_equivalencia_impacto RPC
      - Colapsado → no llama al RPC
    Datos: mockEquivImpacto
    Verificación: mock RPC handler llamado solo después de click

test_impacto_muestra_ocupaciones
    Tipo: componente React
    Qué verifica:
      - Después de expandir, muestra tabla de ocupaciones
      - ISCO code, label, ofertas count, porcentaje visibles
    Datos: mockEquivImpacto con 3 ocupaciones
    Output: 3 filas en sección "Impacto en ocupaciones"

test_impacto_sin_datos
    Tipo: componente React
    Qué verifica:
      - Si el RPC retorna [] (grupo sin ofertas con equivalence_id)
      - Muestra "Sin datos de impacto" o equivalente
      - No crashea
    Datos: mockEquivImpacto vacío

test_impacto_rpc_falla_gracefully
    Tipo: componente React
    Qué verifica:
      - Si el RPC falla (network error)
      - Muestra mensaje de error, no rompe la card
      - Las otras secciones del grupo expandido siguen visibles
    Datos: MSW handler que retorna error
```

---

### Nivel 6 — Regresión

```
test_aprobacion_no_rompe_matching
    Tipo: integración Python
    Qué verifica:
      - Aprobar un grupo (via mock) + recargar lookup
      - Matching produce mismo resultado para grupos no cambiados
      - Skills que usaban el grupo siguen funcionando
    Datos: extractor con equiv_lookup, run matching sobre 1 oferta

test_ui_equivalencias_existentes_intactas
    Tipo: componente React
    Qué verifica:
      - Las cards existentes (label, miembros, frecuencia, estado)
        siguen mostrándose igual
      - Filtros por estado y búsqueda siguen funcionando
    Datos: mockEquivWithSimilarity (superset de mock actual)

test_sorting_por_frecuencia_sigue_default
    Tipo: componente React
    Qué verifica:
      - Sin cambiar el dropdown de sort, el orden es por frecuencia
      - Mismo comportamiento que antes de la mejora
    Datos: mock estándar
```

---

### Casos borde

```
test_grupo_grande_similitud_baja
    Tipo: unitario Python
    Qué verifica:
      - Grupo con 10+ miembros puede tener similitud_minima << 0.85
        (el umbral del clustering es promedio, no mínimo)
      - El cálculo no falla con matrices grandes
    Datos: 10 embeddings con similitudes variadas

test_staleness_timezone_handling
    Tipo: unitario Python
    Qué verifica:
      - Supabase retorna timestamps con timezone (+00:00)
      - Python compara correctamente con datetime UTC local
      - No falla por mismatch naive vs aware datetime
    Datos: timestamp "2026-03-31T14:00:00+00:00" vs datetime.now(UTC)

test_backfill_grupo_sin_miembros_en_embeddings
    Tipo: unitario Python
    Qué verifica:
      - Si un grupo tiene URIs que no están en los embeddings
        (datos inconsistentes), el backfill no crashea
      - Registra warning y pone similitud = NULL
    Datos: grupo con URI inventada

test_impacto_equiv_id_no_poblado
    Tipo: componente React
    Qué verifica:
      - Si ofertas_skills.equivalence_id no está poblado para este grupo
      - El RPC retorna 0 filas
      - UI muestra "Sin datos — ejecutar backfill" o similar
    Datos: grupo existente sin ofertas_skills asociadas
```

---

### Implementabilidad con infraestructura existente

| Aspecto | Estado |
|---------|--------|
| Mock Supabase RPC (Python) | ⚠️ Nuevo — usar unittest.mock para client.rpc() |
| Embeddings ESCO en disco | ✅ `embeddings/esco_skills_embeddings_full.npy` disponible |
| cosine_similarity (sklearn) | ✅ Ya importado en generate_skill_equivalences.py |
| MSW handlers (React) | ✅ Agregar handler para get_equivalencia_impacto RPC |
| Fixture pipeline-status (React) | ✅ Reusar mockPipelineStatusRPC existente |
| SQLite en memoria (Python) | ✅ No necesario — solo mocks de Supabase |
| vitest + testing-library | ✅ 933+ tests existentes |

**Todos los tests son implementables** con la infraestructura existente.
Los tests Python usan mocks de Supabase client (mismo patrón que
test_m01_sync_learnings.py). Los tests React agregan un handler MSW
para el nuevo RPC de impacto.

---

## Secuencia de implementación sugerida

```
1. Migration SQL: similitud_promedio + similitud_minima + 2 RPCs
2. Backfill retroactivo: calcular similitudes para 1,000 grupos
3. Staleness check en run_matching_pipeline() + _equiv_loaded_at
4. Tests Python (staleness + similitud)
5. calculate_group_similarity() en generate_skill_equivalences.py
6. UI: badge confianza + dropdown ordenamiento
7. UI: panel impacto lazy
8. Tests React
9. Verificar cobertura equivalence_id → backfill si < 80%
10. Smoke test: aprobar grupo → correr matching → verificar recarga
11. Commit
```

---

## Criterio de done

```
□ RPC get_latest_equiv_update() creado
□ RPC get_equivalencia_impacto() creado (con CTE)
□ Columnas similitud_promedio y similitud_minima en skill_equivalences
□ Backfill retroactivo ejecutado sobre 1,000 grupos
□ generate_skill_equivalences.py calcula similitudes en nuevos runs
□ run_matching_pipeline() verifica staleness antes del loop
□ _equiv_loaded_at registrado en extractor
□ Badge de confianza visible en cards colapsadas
□ Ordenamiento por confianza disponible en dropdown
□ Panel de impacto visible al expandir grupo (lazy)
□ 5 tests Python staleness pasando
□ 5 tests Python similitud pasando
□ 5 tests React badge pasando
□ 3 tests React ordenamiento pasando
□ 4 tests React impacto pasando
□ 3 tests regresión pasando
□ 4 tests casos borde pasando
□ Aprobar grupo → próximo run recarga lookup automáticamente
□ No regresión: 97+ tests Python en verde
□ No regresión: 933+ tests React en verde
```

---

## Lo que NO hace este spec

- No regenera los grupos de clustering (eso es M-08b)
- No agrega nuevos candidatos de equivalencias
- No cambia el umbral de similitud del clustering (0.85)
- No automatiza la revisión — siempre requiere aprobación humana
- No recarga el lookup en tiempo real (solo al iniciar run)
