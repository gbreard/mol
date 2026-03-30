# M-06 — Registro de Tareas Fallidas (v2)

> **Estado:** ⬜ No iniciado
> **Prioridad:** CRÍTICO
> **Fase:** -1, Nivel 2
> **Prerequisito de:** M-08, M-13, M-14, M-17 (fine-tuning embeddings)
> **Supersede:** SPEC_M06_SKILLS_FAILURES.md (v1, corregida por errores en firmas y paths)

---

## Problema que resuelve

Hoy el sistema descarta silenciosamente ~60.000 tareas que intentaron matchear contra ESCO y fallaron. No queda rastro del intento, del score máximo alcanzado, ni de la skill ESCO más cercana.

Sin ese registro el sistema no puede:
- Detectar que una ocupación tiene vocabulario argentino que ESCO no cubre
- Distinguir Tipo B (vocabulario diverge, concepto existe) de Tipo C (competencias nuevas)
- Alertar que un run tuvo tasa de extracción baja
- Alimentar el Perfil Argentino con competencias que el mercado pide pero ESCO no reconoce
- Proveer datos limpios para fine-tuning de embeddings BGE-M3

**El número que justifica esto:** 1 de cada 4 ofertas con tareas reales produce 0 skills ESCO. ~9.000 de esas tienen tareas sustanciales (300+ caracteres) que el mercado argentino pide y que el sistema no puede ver.

---

## Correcciones respecto a v1

La v1 tenía 3 errores identificados al verificar contra el código real:

1. **Firmas incorrectas:** La spec asumía que `extract_skills_dual()` y `get_skills_for_offer()` recibían `oferta_id` — no lo reciben. Las firmas reales son distintas.

2. **Un solo path cubierto:** La v1 solo cubría el path NLP (`extract_from_tasks()`). Pero en producción el matching usa `extract_skills()` — un método distinto con el mismo descarte silencioso. Hay DOS puntos de descarte independientes.

3. **Persistencia en el extractor:** La v1 proponía `_persist_failures()` dentro del extractor. Pero el extractor es stateless (no tiene conexión a BD). La persistencia debe ir en el caller.

---

## Decisiones de diseño

### Los dos paths de descarte

El descarte silencioso ocurre en dos lugares independientes:

```
PATH NLP (PASO 1 del pipeline)
process_nlp_from_db_v11.py → process_oferta()
    → get_skills_for_offer(skills_declaradas, tareas_explicitas)
        → extract_from_tasks(tareas_explicitas)
            → línea 384: if score < threshold: continue  ← DESCARTE 1

PATH MATCHING (PASO 2 del pipeline)
match_ofertas_v3.py → match_and_persist(id_oferta, oferta_nlp, run_id=...)
    → extract_skills_dual(titulo_limpio, tareas_explicitas, ...)
        → extract_skills(titulo_limpio, tareas_explicitas, ...)
            → línea 581: if score < threshold: continue  ← DESCARTE 2
```

Ambos paths deben registrar los fallidos. El principio es el mismo en ambos:
**el método de extracción retorna los fallidos como lista adicional; el caller persiste.**

### Por qué el caller persiste y no el extractor

El extractor (`skills_implicit_extractor.py`) es stateless — recibe texto, retorna skills. No tiene `self.conn`, no conoce `id_oferta` ni `run_id`. Agregarle persistencia rompe su diseño.

Los callers ya tienen todo:

| Caller | Tiene id_oferta? | Tiene run_id? | Tiene conn BD? |
|--------|:---:|:---:|:---:|
| `process_oferta()` en `process_nlp_from_db_v11.py` | Sí (parámetro) | No (path NLP no tiene run_id) | Sí (`self.db_path`) |
| `match_and_persist()` en `match_ofertas_v3.py` | Sí (parámetro) | Sí (parámetro) | Sí (`self.conn`) |

### Qué pasa con run_id en el path NLP

`process_oferta()` no recibe `run_id` hoy. Dos opciones:
- **Opción A:** Agregar `run_id` como parámetro a `process_oferta()` — requiere propagarlo desde `run_validated_pipeline.py` a través de `process_batch()`.
- **Opción B:** Los registros del path NLP se guardan con `run_id=NULL`. Cuando el matching corre después (path matching), se registran con run_id.

**Decisión: Opción B.** Los fallidos del path NLP van con `run_id=NULL` y `tarea_origen='nlp'`. Los del path matching van con el `run_id` del matching y `tarea_origen='matching'`. Esto evita modificar `process_oferta()` y su cadena de llamadores.

---

## Tabla nueva: `skills_extraction_failures`

```sql
CREATE TABLE skills_extraction_failures (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Contexto
    oferta_id       TEXT NOT NULL,
    run_id          TEXT,                    -- NULL si path NLP o fuera de pipeline formal
    fecha_intento   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- La tarea que falló
    tarea_texto     TEXT NOT NULL,           -- texto crudo de la tarea
    tarea_origen    TEXT,                    -- 'nlp' | 'matching' | 'titulo' | 'skills_nlp' | 'soft_skills_nlp'

    -- El mejor match que encontró (aunque no superó el umbral)
    mejor_skill_uri   TEXT,                  -- URI ESCO de la skill más cercana
    mejor_skill_label TEXT,                  -- label legible
    mejor_score       REAL,                  -- score máximo alcanzado (< threshold)
    threshold_usado   REAL DEFAULT 0.40,     -- umbral vigente en ese momento
    gap_al_umbral     REAL,                  -- threshold - mejor_score (cuánto le faltó)

    -- Clasificación (se completa después, no en el momento del descarte)
    tipo_falla      TEXT DEFAULT 'sin_clasificar',
                    -- 'tipo_b_vocabulario'  → concepto existe en ESCO, palabras no matchean
                    -- 'tipo_c_genuino'      → competencia nueva sin equivalente ESCO
                    -- 'ruido'               → no es una tarea real
                    -- 'sin_clasificar'      → valor por defecto

    -- Índices
    FOREIGN KEY (oferta_id) REFERENCES ofertas(id_oferta)
);

-- Índices para consultas frecuentes
CREATE INDEX idx_failures_oferta    ON skills_extraction_failures(oferta_id);
CREATE INDEX idx_failures_run       ON skills_extraction_failures(run_id);
CREATE INDEX idx_failures_score     ON skills_extraction_failures(mejor_score);
CREATE INDEX idx_failures_gap       ON skills_extraction_failures(gap_al_umbral);
CREATE INDEX idx_failures_tipo      ON skills_extraction_failures(tipo_falla);
CREATE INDEX idx_failures_fecha     ON skills_extraction_failures(fecha_intento);
```

---

## Cambios en el código

### Cambio 1: `extract_from_tasks()` — retornar fallidos

**Archivo:** `database/skills_implicit_extractor.py`
**Método:** `extract_from_tasks()` (línea 318)

**Firma actual:**
```python
def extract_from_tasks(
    self,
    tareas_explicitas: str,
    top_k: int = None,
    threshold: float = None
) -> List[Dict]:
```

**Firma nueva:**
```python
def extract_from_tasks(
    self,
    tareas_explicitas: str,
    top_k: int = None,
    threshold: float = None,
    track_failures: bool = False
) -> Union[List[Dict], Tuple[List[Dict], List[Dict]]]:
```

**Lógica del cambio:**
- Si `track_failures=False` (default): comportamiento idéntico al actual, retorna `List[Dict]`. Esto preserva compatibilidad con todos los callers existentes.
- Si `track_failures=True`: acumula una lista `tareas_fallidas` además de `skills_implicitas`.

**Punto de captura (línea 384):** Cuando `score < threshold` para TODOS los top_k candidatos de una tarea, esa tarea entera es fallida. Capturar:

```python
{
    "tarea_texto":       tarea[:200],
    "mejor_skill_uri":   self.metadata[top_indices[0]].get('uri', ''),
    "mejor_skill_label": self.metadata[top_indices[0]].get('label', ''),
    "mejor_score":       float(similarities[top_indices[0]]),
    "threshold_usado":   threshold,
    "gap_al_umbral":     round(threshold - float(similarities[top_indices[0]]), 4)
}
```

**Caso borde:** Si la tarea matcheó sinónimo argentino (línea 359), NO es fallida — ya tiene resultado. Solo las tareas que pasan a embedding y fallan el umbral son fallidas.

**Caso borde:** Si `top_indices` tiene tamaño 0 (no debería pasar con 14,247 skills, pero por seguridad), registrar con `mejor_score=0.0`, `mejor_skill_uri=None`.

**Retorno con track_failures=True:**
```python
return (skills_implicitas, tareas_fallidas)
```

### Cambio 2: `extract_skills()` — retornar fallidos

**Archivo:** `database/skills_implicit_extractor.py`
**Método:** `extract_skills()` (línea 466)

**Firma actual:**
```python
def extract_skills(
    self,
    titulo_limpio: str,
    tareas_explicitas: str = None,
    skills_nlp: List[str] = None,
    soft_skills_nlp: List[str] = None,
    sector_empresa: str = None,
    nivel_seniority: str = None,
    area_funcional: str = None,
    top_k: int = None,
    threshold: float = None
) -> List[Dict]:
```

**Firma nueva:**
```python
def extract_skills(
    self,
    titulo_limpio: str,
    tareas_explicitas: str = None,
    skills_nlp: List[str] = None,
    soft_skills_nlp: List[str] = None,
    sector_empresa: str = None,
    nivel_seniority: str = None,
    area_funcional: str = None,
    top_k: int = None,
    threshold: float = None,
    track_failures: bool = False
) -> Union[List[Dict], Tuple[List[Dict], List[Dict]]]:
```

**Lógica del cambio:** Idéntica a `extract_from_tasks()`:
- Si `track_failures=False` (default): retorna `List[Dict]`, sin cambio.
- Si `track_failures=True`: acumula fallidos por cada `(origen, texto)` en el loop de la línea 568.

**Punto de captura (línea 581):** Cuando TODOS los top_k candidatos para un texto tienen `score < threshold`, registrar:

```python
{
    "tarea_texto":       texto[:200],
    "tarea_origen":      origen,           # "titulo", "tarea", "skills_nlp", "soft_skills_nlp"
    "mejor_skill_uri":   self.metadata[top_indices[0]].get('uri', ''),
    "mejor_skill_label": self.metadata[top_indices[0]].get('label', ''),
    "mejor_score":       float(similarities[top_indices[0]]),
    "threshold_usado":   threshold,
    "gap_al_umbral":     round(threshold - float(similarities[top_indices[0]]), 4)
}
```

**Nota:** A diferencia de `extract_from_tasks()`, este método procesa múltiples tipos de texto (titulo, tareas, skills_nlp, soft_skills_nlp). El campo `tarea_origen` captura de cuál vino.

**Retorno con track_failures=True:**
```python
return (skills_extraidas, textos_fallidos)
```

### Cambio 3: `extract_skills_dual()` — propagar fallidos

**Archivo:** `database/skills_implicit_extractor.py`
**Método:** `extract_skills_dual()` (línea 690)

**Firma actual:**
```python
def extract_skills_dual(
    self,
    titulo_limpio: str,
    tareas_explicitas: str = None,
    oferta_nlp: Dict = None,
    skills_nlp: List[str] = None,
    soft_skills_nlp: List[str] = None,
    sector_empresa: str = None,
    nivel_seniority: str = None,
    area_funcional: str = None,
    top_k: int = None,
    threshold: float = None
) -> Dict:
```

**Firma nueva:** Agregar `track_failures: bool = False`:
```python
def extract_skills_dual(
    self,
    titulo_limpio: str,
    tareas_explicitas: str = None,
    oferta_nlp: Dict = None,
    skills_nlp: List[str] = None,
    soft_skills_nlp: List[str] = None,
    sector_empresa: str = None,
    nivel_seniority: str = None,
    area_funcional: str = None,
    top_k: int = None,
    threshold: float = None,
    track_failures: bool = False
) -> Dict:
```

**Cambio:** En la llamada interna a `extract_skills()` (línea 797), pasar `track_failures`:

```python
# Antes:
skills_semantico = self.extract_skills(...)

# Después:
result = self.extract_skills(..., track_failures=track_failures)
if track_failures:
    skills_semantico, failures_semantico = result
else:
    skills_semantico = result
    failures_semantico = []
```

**Agregar al dict de retorno (línea 859):**
```python
return {
    "skills_regla": skills_regla,
    "skills_semantico": skills_semantico,
    "regla_aplicada": regla_aplicada,
    "nombre_regla": nombre_regla,
    "dual_coinciden_skills": dual_coinciden_skills,
    "skills_final": skills_final,
    "metodo_primario": metodo_primario,
    "failures": failures_semantico       # NUEVO — lista vacía si track_failures=False
}
```

### Cambio 4: `match_and_persist()` — activar tracking y persistir

**Archivo:** `database/match_ofertas_v3.py`
**Método:** `match_and_persist()` (línea 1503)

**Firma:** No cambia. Ya tiene `id_oferta` y `run_id`.

**Cambio en la llamada a `extract_skills_dual()` (línea 1562):**

```python
# Antes:
skills_dual_result = self.skills_extractor.extract_skills_dual(
    titulo_limpio=titulo,
    tareas_explicitas=tareas,
    ...
)

# Después:
skills_dual_result = self.skills_extractor.extract_skills_dual(
    titulo_limpio=titulo,
    tareas_explicitas=tareas,
    ...,
    track_failures=True
)

# Persistir fallidos (después de la extracción, antes del matching)
failures = skills_dual_result.get("failures", [])
if failures:
    self._persist_skill_failures(id_oferta, run_id, failures)
```

**Método nuevo `_persist_skill_failures()` en MatcherV3:**

```python
def _persist_skill_failures(self, oferta_id: str, run_id: str, failures: list) -> None:
    """
    Persiste intentos fallidos de extracción de skills.
    Fallo silencioso — no interrumpe el pipeline.
    """
    if not failures:
        return
    try:
        for f in failures:
            self.conn.execute('''
                INSERT INTO skills_extraction_failures
                (oferta_id, run_id, tarea_texto, tarea_origen,
                 mejor_skill_uri, mejor_skill_label, mejor_score,
                 threshold_usado, gap_al_umbral)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                oferta_id, run_id,
                f["tarea_texto"], f.get("tarea_origen", "matching"),
                f.get("mejor_skill_uri"), f.get("mejor_skill_label"),
                f.get("mejor_score", 0.0),
                f.get("threshold_usado", 0.40),
                f.get("gap_al_umbral")
            ))
        self.conn.commit()
    except Exception as e:
        import logging
        logging.warning(f"No se pudieron registrar {len(failures)} failures para {oferta_id}: {e}")
```

### Cambio 5: `process_oferta()` — activar tracking y persistir (path NLP)

**Archivo:** `database/process_nlp_from_db_v11.py`
**Método:** `process_oferta()` (línea 342) — ya tiene `id_oferta`.

**Cambio en la llamada a `get_skills_for_offer()` (línea 453):**

`get_skills_for_offer()` llama internamente a `extract_from_tasks()`. No queremos modificar `get_skills_for_offer()` porque es un wrapper simple. En cambio, usamos `extract_from_tasks()` directamente con `track_failures=True`:

```python
# Antes (línea 453):
skills_all, skills_implicitas = self.skills_extractor.get_skills_for_offer(
    skills_declaradas=skills_declaradas,
    tareas_explicitas=tareas,
    merge=True
)

# Después:
# Extraer con tracking de fallidos
matcheadas, fallidas = self.skills_extractor.extract_from_tasks(
    tareas_explicitas=tareas,
    track_failures=True
)

# Deduplicar contra declaradas (misma lógica que get_skills_for_offer)
declaradas_norm = {s.lower().strip() for s in skills_declaradas if s}
skills_implicitas = [s for s in matcheadas if s['skill_esco'].lower() not in declaradas_norm]
skills_all = list(skills_declaradas) + [s['skill_esco'] for s in skills_implicitas]

# Persistir fallidos
if fallidas:
    try:
        conn = sqlite3.connect(self.db_path)
        for f in fallidas:
            conn.execute('''
                INSERT INTO skills_extraction_failures
                (oferta_id, run_id, tarea_texto, tarea_origen,
                 mejor_skill_uri, mejor_skill_label, mejor_score,
                 threshold_usado, gap_al_umbral)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_oferta, None,  # run_id=NULL en path NLP
                f["tarea_texto"], "nlp",
                f.get("mejor_skill_uri"), f.get("mejor_skill_label"),
                f.get("mejor_score", 0.0),
                f.get("threshold_usado", 0.40),
                f.get("gap_al_umbral")
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        if self.verbose:
            print(f"[WARN] No se pudieron registrar failures: {e}")
```

---

## Resumen de cambios por archivo

| Archivo | Método | Cambio |
|---------|--------|--------|
| `skills_implicit_extractor.py` | `extract_from_tasks()` | Agregar `track_failures` param, retornar tupla si True |
| `skills_implicit_extractor.py` | `extract_skills()` | Agregar `track_failures` param, retornar tupla si True |
| `skills_implicit_extractor.py` | `extract_skills_dual()` | Agregar `track_failures` param, propagar, incluir failures en retorno |
| `match_ofertas_v3.py` | `match_and_persist()` | Pasar `track_failures=True`, persistir failures |
| `match_ofertas_v3.py` | `_persist_skill_failures()` | **Método nuevo** — INSERT con fallo silencioso |
| `process_nlp_from_db_v11.py` | `process_oferta()` | Usar `extract_from_tasks(track_failures=True)` directo, persistir |

**Archivos que NO se modifican:** `run_validated_pipeline.py`, `nlp_validator.py`, `auto_corrector.py`, `skills_rules_matcher.py`.

**Compatibilidad hacia atrás:** `track_failures=False` por default en las 3 firmas del extractor. Cualquier caller existente que no pase el parámetro sigue funcionando exactamente igual.

---

## Consultas que habilita

Una vez implementado, estas consultas son posibles:

**¿Cuántas tareas fallaron en el último run?**
```sql
SELECT COUNT(*)
FROM skills_extraction_failures
WHERE run_id = 'run_20260329_0830';
```

**¿Qué tareas están a menos de 0.05 del umbral? (candidatas a bajar umbral)**
```sql
SELECT tarea_texto, mejor_skill_label, mejor_score, gap_al_umbral
FROM skills_extraction_failures
WHERE gap_al_umbral < 0.05
ORDER BY gap_al_umbral ASC;
```

**¿Qué tareas aparecen repetidamente sin matchear? (candidatas a sinónimos)**
```sql
SELECT tarea_texto, COUNT(*) as frecuencia, AVG(mejor_score) as score_promedio
FROM skills_extraction_failures
WHERE tipo_falla = 'sin_clasificar'
GROUP BY tarea_texto
HAVING COUNT(*) >= 10
ORDER BY frecuencia DESC;
```

**¿El pipeline mejoró entre runs?**
```sql
SELECT
    run_id,
    COUNT(*) as total_fallidos,
    AVG(mejor_score) as score_promedio,
    AVG(gap_al_umbral) as gap_promedio
FROM skills_extraction_failures
GROUP BY run_id
ORDER BY fecha_intento DESC;
```

**¿Cuántas ofertas de esta ocupación tienen tareas que no matchearon?**
```sql
SELECT f.oferta_id, COUNT(*) as tareas_fallidas
FROM skills_extraction_failures f
JOIN ofertas_esco_matching m ON f.oferta_id = m.id_oferta
WHERE m.isco_code = '7132'
GROUP BY f.oferta_id
ORDER BY tareas_fallidas DESC;
```

**Tasa de fallo por origen:**
```sql
SELECT tarea_origen, COUNT(*) as fallidos
FROM skills_extraction_failures
GROUP BY tarea_origen;
-- Permite comparar: ¿fallan más las tareas (NLP) o los títulos (matching)?
```

---

## Estrategia de Tests

### Estructura de archivos

```
tests/
  test_m06_skills_failures.py        ← unitarios + casos borde
  test_m06_integration.py            ← flujo completo ambos paths
  test_m06_regression.py             ← nada se rompió
```

### Fixtures compartidos

```
fixture: db_with_failures_table
    → SQLite en memoria con skills_extraction_failures creada
    → Se usa en todos los tests de integración y persistencia

fixture: mock_extractor
    → SkillsImplicitExtractor con embeddings reducidos (10 skills ESCO)
    → 5 skills con labels conocidos ("instalar cableado eléctrico", etc.)
    → 5 skills genéricas ("trabajar en equipo", etc.)
    → Permite controlar qué matchea y qué no

fixture: tareas_que_fallan
    → "reparar tableros eléctricos" (score esperado ~0.38, < 0.40)
    → "gestionar inventarios de repuestos" (score esperado ~0.35)
    → "actuar como embajador de la marca" (score esperado ~0.20)

fixture: tareas_que_matchean
    → "instalar cableado industrial" (score esperado ~0.82)
    → "trabajar en equipo multidisciplinario" (score esperado ~0.75)

fixture: tareas_mixtas
    → Combinación de las anteriores separadas por ";"
    → "instalar cableado industrial; reparar tableros eléctricos; trabajar en equipo"
    → Resultado esperado: 2 matcheadas, 1 fallida
```

---

### Nivel 1 — Unitarios (función aislada)

#### Path NLP: `extract_from_tasks()`

```
test_extract_from_tasks_fallidos_contiene_datos_correctos
    Tipo: unitario
    Qué verifica:
      - Tarea con score < 0.40 aparece en lista de fallidos
      - Cada fallido tiene: tarea_texto, mejor_skill_uri, mejor_skill_label,
        mejor_score, threshold_usado, gap_al_umbral
      - gap_al_umbral = threshold - mejor_score (cálculo correcto)
      - mejor_skill_label corresponde al mejor candidato real
    Input: mock_extractor + tareas_que_fallan, track_failures=True
    Output esperado: tupla ([], [3 dicts con campos completos])

test_extract_from_tasks_matcheadas_no_aparecen_en_fallidos
    Tipo: unitario
    Qué verifica:
      - Tareas que superan 0.40 aparecen en matcheadas, NO en fallidos
    Input: mock_extractor + tareas_que_matchean, track_failures=True
    Output esperado: tupla ([2 skills], [])

test_extract_from_tasks_mixto
    Tipo: unitario
    Qué verifica:
      - Con tareas mixtas, las que matchean van a matcheadas
        y las que fallan van a fallidos
      - No hay overlap entre las dos listas
    Input: mock_extractor + tareas_mixtas, track_failures=True
    Output esperado: tupla ([2 skills], [1 fallida])

test_extract_from_tasks_compatibilidad_sin_flag
    Tipo: unitario
    Qué verifica:
      - Sin track_failures (o track_failures=False), retorna List[Dict]
      - El tipo de retorno es list, no tupla
      - Comportamiento idéntico al actual
    Input: mock_extractor + tareas_mixtas, track_failures=False
    Output esperado: List con 2 skills (sin fallidos)

test_extract_from_tasks_sinonimo_no_es_fallido
    Tipo: unitario
    Qué verifica:
      - Tarea que matchea por sinónimo argentino NO aparece en fallidos
        (tiene score 0.99 por lookup directo)
    Input: mock_extractor + tarea que existe en sinonimos_skills_argentinos
    Output esperado: tupla ([1 skill con origen='sinonimo_argentino'], [])

test_extract_from_tasks_vacio
    Tipo: unitario (caso borde)
    Qué verifica:
      - Con tareas_explicitas="" o None
      - Retorna tupla ([], []) con track_failures=True
      - Retorna [] con track_failures=False
    Input: mock_extractor + ""
    Output esperado: sin errores, listas vacías
```

#### Path Matching: `extract_skills()`

```
test_extract_skills_fallidos_por_origen
    Tipo: unitario
    Qué verifica:
      - Cada fallido tiene tarea_origen correcto:
        "titulo" si vino del título,
        "tarea" si vino de tareas_explicitas,
        "skills_nlp" si vino de skills NLP,
        "soft_skills_nlp" si vino de soft skills
    Input: mock_extractor + titulo="gerente de innovation" +
           tareas="diseñar agentes de IA" +
           skills_nlp=["prompt engineering"]
           track_failures=True
    Output esperado: fallidos con tarea_origen variados

test_extract_skills_fallidos_datos_correctos
    Tipo: unitario
    Qué verifica:
      - Misma estructura que extract_from_tasks: tarea_texto,
        mejor_skill_uri, mejor_skill_label, mejor_score,
        threshold_usado, gap_al_umbral
      - tarea_texto truncado a 200 chars máximo
    Input: mock_extractor + tareas_que_fallan, track_failures=True
    Output esperado: tupla (skills, [fallidos con campos completos])

test_extract_skills_compatibilidad_sin_flag
    Tipo: unitario
    Qué verifica:
      - Sin track_failures, retorna List[Dict] (no tupla)
      - Idéntico al comportamiento actual
    Input: mock_extractor + tareas_mixtas, track_failures=False
    Output esperado: List de skills

test_extract_skills_terminologia_no_es_fallido
    Tipo: unitario
    Qué verifica:
      - Skills encontradas por terminología argentina (capa 0)
        no aparecen como fallidas
    Input: mock_extractor + tarea con término en terminologia_argentina_skills.json
    Output esperado: terminología en matcheadas, no en fallidas
```

#### Propagación: `extract_skills_dual()`

```
test_extract_skills_dual_failures_en_retorno
    Tipo: unitario
    Qué verifica:
      - El dict de retorno incluye key "failures"
      - "failures" contiene los fallidos del semántico
      - Los fallidos de reglas NO se registran (reglas siempre tienen score 0.99)
    Input: mock_extractor + tareas_mixtas, track_failures=True
    Output esperado: dict con "failures" = lista de fallidos

test_extract_skills_dual_failures_vacio_sin_flag
    Tipo: unitario
    Qué verifica:
      - Con track_failures=False, "failures" es lista vacía en el retorno
    Input: mock_extractor + tareas_mixtas, track_failures=False
    Output esperado: dict con "failures" = []

test_extract_skills_dual_failures_vacio_todo_matchea
    Tipo: unitario
    Qué verifica:
      - Si todas las tareas matchean, "failures" es lista vacía
    Input: mock_extractor + tareas_que_matchean, track_failures=True
    Output esperado: dict con "failures" = [], "skills_final" con datos
```

#### Casos borde

```
test_caso_borde_score_exacto_en_umbral
    Tipo: unitario
    Qué verifica:
      - Score == 0.40 exacto: ¿es matcheada o fallida?
      - Según el código actual (score < threshold → continue),
        score == threshold PASA. Verificar que no aparece como fallida.
    Input: mock_extractor configurado para dar score 0.40 exacto
    Output esperado: aparece en matcheadas, no en fallidos

test_caso_borde_tarea_muy_larga
    Tipo: unitario
    Qué verifica:
      - Tarea de 500+ caracteres se trunca a 200 en tarea_texto
      - No lanza error
    Input: "x" * 500 como tarea
    Output esperado: tarea_texto tiene len ≤ 200

test_caso_borde_embeddings_vacios
    Tipo: unitario
    Qué verifica:
      - Si el extractor no tiene embeddings cargados (self.embeddings.size == 0)
      - Retorna ([], []) con track_failures=True
      - No lanza excepción
    Input: extractor sin embeddings + cualquier tarea
    Output esperado: tuplas vacías
```

---

### Nivel 2 — Integración (flujo completo)

```
test_integration_path_matching_registra_en_bd
    Tipo: integración
    Qué verifica:
      - Flujo completo: match_and_persist() → extract_skills_dual(track_failures=True)
        → _persist_skill_failures() → INSERT en skills_extraction_failures
      - La tabla tiene registros con oferta_id y run_id correctos
      - tarea_origen refleja el origen real ("tarea", "titulo", etc.)
    Datos: db_with_failures_table + mock_extractor + oferta con tareas mixtas
    Setup:
      - Crear MatcherV3 con conexión a BD en memoria
      - Insertar oferta mock en ofertas_nlp
      - Llamar match_and_persist(id_oferta="TEST_001", run_id="run_test_001")
    Verificación:
      - SELECT * FROM skills_extraction_failures WHERE oferta_id = 'TEST_001'
      - Hay al menos 1 registro
      - run_id = 'run_test_001'
      - mejor_score < 0.40
      - gap_al_umbral > 0

test_integration_path_nlp_registra_en_bd
    Tipo: integración
    Qué verifica:
      - Flujo completo: process_oferta() → extract_from_tasks(track_failures=True)
        → INSERT en skills_extraction_failures
      - run_id = NULL (path NLP no tiene run_id)
      - tarea_origen = 'nlp'
    Datos: db_with_failures_table + mock_extractor + oferta con tareas que fallan
    Setup:
      - Crear NLPProcessor con skills_extractor mockeado
      - Llamar process_oferta(id_oferta="TEST_002", ...)
    Verificación:
      - SELECT * FROM skills_extraction_failures WHERE oferta_id = 'TEST_002'
      - run_id IS NULL
      - tarea_origen = 'nlp'

test_integration_ambos_paths_misma_oferta
    Tipo: integración
    Qué verifica:
      - Una oferta procesada por AMBOS paths genera registros
        en ambos con tarea_origen distinto
      - Los registros del path NLP tienen run_id=NULL
      - Los del matching tienen run_id con valor
    Datos: misma oferta procesada primero por NLP, luego por matching
    Verificación:
      - SELECT tarea_origen, run_id FROM skills_extraction_failures
        WHERE oferta_id = 'TEST_003'
      - Hay registros con tarea_origen='nlp' AND run_id IS NULL
      - Hay registros con tarea_origen IN ('tarea','titulo') AND run_id IS NOT NULL

test_integration_persist_fallo_silencioso_matching
    Tipo: integración
    Qué verifica:
      - Si la tabla skills_extraction_failures no existe (o está corrupta),
        match_and_persist() completa sin excepción
      - Las skills que SÍ matchearon se guardaron en ofertas_esco_skills_detalle
      - El MatchResult es correcto
    Datos: BD sin tabla skills_extraction_failures + oferta con tareas mixtas
    Verificación:
      - match_and_persist() no lanza excepción
      - ofertas_esco_matching tiene registro
      - ofertas_esco_skills_detalle tiene skills matcheadas

test_integration_persist_fallo_silencioso_nlp
    Tipo: integración
    Qué verifica:
      - Si la tabla no existe, process_oferta() completa sin excepción
      - Los campos NLP (skills_tecnicas_list, tareas_explicitas) se guardaron
    Datos: BD sin tabla skills_extraction_failures + oferta con tareas mixtas
    Verificación:
      - process_oferta() retorna resultado válido
      - ofertas_nlp tiene la oferta con skills_tecnicas_list poblado

test_integration_run_id_consistente_en_pipeline
    Tipo: integración
    Qué verifica:
      - Cuando run_matching_pipeline() crea un run_id,
        ese mismo run_id aparece en skills_extraction_failures
      - Es el mismo run_id que aparece en ofertas_esco_matching
    Datos: 3 ofertas con tareas que fallan procesadas via run_matching_pipeline()
    Verificación:
      - SELECT DISTINCT run_id FROM skills_extraction_failures → 1 solo run_id
      - SELECT DISTINCT run_id FROM ofertas_esco_matching → mismo run_id
```

---

### Nivel 3 — Regresión (nada se rompió)

```
test_regression_skills_detalle_sin_cambios
    Tipo: regresión
    Qué verifica:
      - Las skills que SÍ matchean se guardan en ofertas_esco_skills_detalle
        exactamente igual que antes
      - Misma cantidad, mismos scores, mismos URIs
    Datos: oferta conocida con skills esperadas (fixture golden)
    Verificación:
      - Procesar oferta con track_failures=True
      - SELECT * FROM ofertas_esco_skills_detalle WHERE id_oferta = X
      - Comparar contra snapshot esperado: misma cantidad, mismos labels

test_regression_extract_from_tasks_sin_flag_identico
    Tipo: regresión
    Qué verifica:
      - Llamar extract_from_tasks() sin track_failures (o con False)
        produce exactamente el mismo resultado que el código original
      - Mismo tipo de retorno (List, no Tuple)
      - Mismos skills, mismos scores
    Datos: tareas_mixtas
    Verificación:
      - resultado_nuevo = extract_from_tasks(tareas, track_failures=False)
      - isinstance(resultado_nuevo, list) == True
      - len(resultado_nuevo) == len(resultado_esperado)
      - Cada skill tiene mismos campos y valores

test_regression_extract_skills_sin_flag_identico
    Tipo: regresión
    Qué verifica:
      - extract_skills() sin track_failures retorna List idéntica a antes
    Datos: titulo + tareas + skills_nlp
    Verificación: mismo patrón que test anterior

test_regression_matching_result_no_cambia
    Tipo: regresión
    Qué verifica:
      - El MatchResult de match_and_persist() es idéntico con y sin tracking
      - Mismo isco_code, mismo score, mismas skills_extracted
    Datos: oferta conocida con resultado esperado
    Verificación:
      - result_con = match_and_persist(track_failures=True en extract)
      - result_sin = match_and_persist(track_failures=False)
      - result_con.isco_code == result_sin.isco_code
      - result_con.occupation_match_score == result_sin.occupation_match_score

test_regression_dual_coinciden_no_cambia
    Tipo: regresión
    Qué verifica:
      - El campo dual_coinciden_skills en extract_skills_dual() no se
        ve afectado por track_failures
      - El merge de skills (regla + semántico) produce el mismo resultado
    Datos: oferta que matchea una skills_rule
    Verificación:
      - dual_coinciden_skills es el mismo con y sin track_failures

test_regression_callers_existentes_no_rotos
    Tipo: regresión
    Qué verifica:
      - Todos los callers que NO pasan track_failures siguen funcionando
      - Buscar todos los callers de extract_from_tasks, extract_skills,
        extract_skills_dual en el codebase
      - Verificar que ninguno rompe
    Datos: grep del codebase por llamadas a estos métodos
    Verificación:
      - import del módulo no falla
      - Cada caller existente produce el mismo resultado
```

---

## Criterio de done

```
□ Tabla skills_extraction_failures creada con todos sus índices
□ extract_from_tasks() retorna tupla con track_failures=True
□ extract_from_tasks() retorna List con track_failures=False (compatibilidad)
□ extract_skills() retorna tupla con track_failures=True
□ extract_skills() retorna List con track_failures=False (compatibilidad)
□ extract_skills_dual() propaga track_failures y retorna failures en dict
□ match_and_persist() pasa track_failures=True y persiste failures
□ process_oferta() usa extract_from_tasks(track_failures=True) y persiste failures
□ Ambos paths persisten con fallo silencioso (no rompen pipeline)
□ Tests pasando (8 tests mínimo)
□ Correr pipeline completo → verificar registros en skills_extraction_failures
□ Verificar que hay registros con tarea_origen='nlp' Y con tarea_origen='matching'/'tarea'/'titulo'
□ Ejecutar consulta de tasa de fallo por run → resultado coherente con el 25% conocido
□ No regresión: ofertas_esco_skills_detalle sigue funcionando igual
□ No regresión: callers que no pasan track_failures siguen funcionando igual
```

---

## Lo que NO hace esta spec

- No clasifica automáticamente Tipo B vs Tipo C — eso es M-13
- No baja el umbral de 0.40 — eso requiere análisis post-implementación
- No conecta fuentes declaradas (skills_tecnicas_list, etc.) — eso es M-08
- No modifica la lógica de matching existente — solo observa y registra
- No propaga run_id al path NLP — las failures del NLP van con run_id=NULL

---

## Notas de implementación

- **Compatibilidad:** `track_failures=False` por default en las 3 firmas. Ningún caller existente necesita cambios salvo los dos que activan el tracking.
- **Idempotencia:** Si una oferta se reprocesa, los registros anteriores de esa oferta+run quedan. No se borran — son historia del intento.
- **Performance:** El overhead es mínimo — solo se agrega un dict a una lista en memoria para tareas que fallan. El INSERT se hace en batch después. Si genera overhead medible, considerar batch insert al final del run en lugar de por oferta.
- **Backfill:** Las ~60K tareas fallidas históricas no se pueden recuperar — el embedding se computó y se descartó. Esta tabla solo captura desde la implementación en adelante.
- **Duplicados path NLP + matching:** Una misma tarea puede fallar en AMBOS paths (primero en NLP, luego en matching). Esto es correcto y deseable — permite comparar si el mismo texto falla distinto en cada contexto. El campo `tarea_origen` los distingue.
