# M-06 — Registro de Tareas Fallidas

> **Estado:** ⬜ No iniciado  
> **Prioridad:** CRÍTICO  
> **Fase:** -1, Nivel 2  
> **Prerequisito de:** M-08, M-13, M-14, M-17 (fine-tuning embeddings)

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

## Decisiones de diseño

### Dónde capturar el dato

**Decisión: Opción B — capturar en get_skills_for_offer(), no en extract_from_tasks()**

```
extract_from_tasks()
    → retorna dos listas:
        skills_matcheadas  (ya existía)
        tareas_fallidas    (nueva)

get_skills_for_offer()   ← tiene id_oferta, recibe run_id
    → recibe ambas listas
    → persiste tareas_fallidas con id_oferta + run_id
```

Razón: `extract_from_tasks()` es un método de extracción pura — no debe hacer escrituras a BD ni conocer contexto de oferta. Retornar los fallidos como lista mantiene la separación de responsabilidades. El caller que ya coordina es quien persiste.

### Cómo llega run_id

**Decisión: seguir el patrón establecido — parámetro opcional `run_id: str = None`**

El patrón existe en todo el pipeline. El extractor de skills es la única excepción hoy. La propagación es:

```
match_and_persist(run_id=...)          ← ya tiene run_id
    → extract_skills_dual(run_id=...)  ← agregar parámetro
        → get_skills_for_offer(run_id=...)  ← agregar parámetro
            → extract_from_tasks()     ← NO modifica firma
            → persiste fallidos con run_id
```

Tres firmas a modificar. El patrón es idéntico al resto del pipeline.

### Dónde NO capturar

- **No en extract_from_tasks():** evitar contaminar con responsabilidades de persistencia
- **No en process_oferta():** requeriría burbujear los fallidos a través de dos niveles adicionales
- **No sin run_id:** el run_id es el dato que convierte una foto en una película — permite ver si el pipeline mejora o empeora entre runs

---

## Tabla nueva: `skills_extraction_failures`

```sql
CREATE TABLE skills_extraction_failures (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Contexto
    oferta_id       TEXT NOT NULL,
    run_id          TEXT,                    -- NULL si se corre fuera de pipeline formal
    fecha_intento   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- La tarea que falló
    tarea_texto     TEXT NOT NULL,           -- texto crudo de la tarea
    tarea_origen    TEXT,                    -- 'tareas_explicitas' | 'skills_tecnicas' | etc.
    
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

### 1. `extract_from_tasks()` — retornar fallidos además de skills

**Archivo:** `database/skills_implicit_extractor.py`

**Cambio:** Acumular los intentos fallidos en una lista local y retornarla junto con las skills matcheadas.

**Contrato actual:**
```
extract_from_tasks(tareas) → List[skill_matcheada]
```

**Contrato nuevo:**
```
extract_from_tasks(tareas) → Tuple[List[skill_matcheada], List[tarea_fallida]]
```

Cada `tarea_fallida` es un dict con:
```python
{
    "tarea_texto":      str,   # texto de la tarea
    "mejor_skill_uri":  str,   # URI ESCO del mejor candidato
    "mejor_skill_label": str,  # label del mejor candidato
    "mejor_score":      float, # score máximo alcanzado
    "threshold_usado":  float, # umbral vigente
    "gap_al_umbral":    float  # threshold - mejor_score
}
```

**Caso borde:** Si `top_indices` está vacío (ningún candidato siquiera computado), registrar con `mejor_skill_uri=None`, `mejor_score=0.0`.

### 2. `get_skills_for_offer()` — recibir run_id y persistir fallidos

**Archivo:** `database/skills_implicit_extractor.py`

**Firma actual:**
```python
def get_skills_for_offer(self, oferta_id, tareas, skills_declaradas):
```

**Firma nueva:**
```python
def get_skills_for_offer(self, oferta_id, tareas, skills_declaradas, run_id: str = None):
```

**Responsabilidad nueva:**
- Recibir la tupla `(skills_matcheadas, tareas_fallidas)` de `extract_from_tasks()`
- Llamar a `_persist_failures(oferta_id, run_id, tareas_fallidas)`
- El resto del flujo no cambia

### 3. `extract_skills_dual()` — propagar run_id

**Archivo:** `database/skills_implicit_extractor.py`

**Firma actual:**
```python
def extract_skills_dual(self, oferta_id, tareas, skills_declaradas):
```

**Firma nueva:**
```python
def extract_skills_dual(self, oferta_id, tareas, skills_declaradas, run_id: str = None):
```

Solo propagación — recibe run_id y lo pasa a `get_skills_for_offer()`.

### 4. `match_and_persist()` — pasar run_id al extractor

**Archivo:** `database/match_ofertas_v3.py`

`match_and_persist()` ya tiene `run_id`. Solo hay que pasarlo en la llamada a `extract_skills_dual()`:

**Antes:**
```python
skills = self.extractor.extract_skills_dual(oferta_id, tareas, skills_declaradas)
```

**Después:**
```python
skills = self.extractor.extract_skills_dual(oferta_id, tareas, skills_declaradas, run_id=run_id)
```

### 5. Método nuevo `_persist_failures()`

**Archivo:** `database/skills_implicit_extractor.py`

Método privado en la clase del extractor. Responsabilidades:
- Recibir lista de dicts de tareas fallidas
- Insertar en `skills_extraction_failures`
- Si la lista está vacía, no hacer nada (no es error)
- Si falla la inserción, loggear warning pero NO propagar excepción — el pipeline principal no debe romperse por un fallo en el registro

```python
def _persist_failures(self, oferta_id: str, run_id: str, failures: list) -> None:
    """
    Persiste los intentos fallidos de extracción de skills.
    Fallo silencioso — no interrumpe el pipeline principal.
    """
    if not failures:
        return
    try:
        # INSERT INTO skills_extraction_failures (...)
        # para cada item en failures
        pass
    except Exception as e:
        logger.warning(f"No se pudieron registrar {len(failures)} failures para oferta {oferta_id}: {e}")
```

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
JOIN ofertas_esco_matching m ON f.oferta_id = m.oferta_id
WHERE m.isco_code = '7132'  -- pintor de vehículos
GROUP BY f.oferta_id
ORDER BY tareas_fallidas DESC;
```

---

## Tests requeridos

```
tests/test_m06_skills_failures.py

test_extract_from_tasks_retorna_fallidos()
    → tarea que no supera 0.40 aparece en la lista de fallidos
    → tarea que sí supera 0.40 NO aparece en fallidos
    → fallido contiene: tarea_texto, mejor_score, mejor_skill_uri, gap_al_umbral

test_persist_failures_inserta_correctamente()
    → dado oferta_id + run_id + lista de fallidos
    → verifica que se insertaron en skills_extraction_failures
    → verifica que los campos son correctos

test_persist_failures_fallo_silencioso()
    → si la BD no está disponible
    → el método retorna sin excepción
    → el pipeline principal no se interrumpe

test_run_id_llega_al_extractor()
    → dado un run_id en match_and_persist()
    → verificar que ese run_id aparece en skills_extraction_failures

test_caso_borde_top_indices_vacio()
    → tarea sin ningún candidato computado
    → registra con mejor_score=0.0 y mejor_skill_uri=None
    → no lanza excepción
```

---

## Criterio de done

```
□ Tabla skills_extraction_failures creada con todos sus índices
□ extract_from_tasks() retorna tupla (matcheadas, fallidas)
□ get_skills_for_offer() recibe run_id y persiste fallidos
□ extract_skills_dual() propaga run_id
□ match_and_persist() pasa run_id al extractor
□ _persist_failures() falla silenciosamente si hay error de BD
□ Tests pasando (5 tests mínimo)
□ Correr pipeline completo → verificar que skills_extraction_failures tiene registros
□ Ejecutar consulta de tasa de fallo por run → resultado coherente con el 25% conocido
□ No regresión: ofertas_esco_skills_detalle sigue funcionando igual
```

---

## Lo que NO hace este spec

- No clasifica automáticamente Tipo B vs Tipo C — eso es M-13
- No baja el umbral de 0.40 — eso requiere análisis post-implementación
- No conecta fuentes declaradas (skills_tecnicas_list, etc.) — eso es M-08
- No modifica la lógica de matching existente — solo observa y registra

---

## Notas de implementación

- **Idempotencia:** Si una oferta se reprocesa, los registros anteriores de esa oferta+run quedan. No se borran — son historia del intento.
- **Performance:** El INSERT de fallidos ocurre después del procesamiento principal de la oferta. Si genera overhead medible, considerar batch insert al final del run en lugar de por oferta.
- **Backfill:** Las 60K tareas fallidas históricas no se pueden recuperar — el embedding se computó y se descartó. Esta tabla solo captura desde la implementación en adelante.
