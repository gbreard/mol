# SPEC: Motor de Conocimiento
## Gestión de Embeddings + Perfil Argentino + CLAE + M-17

**Versión:** 1.2  
**Fecha:** 2026-04-08  
**Driver:** M-17 — Base de datos limpia para fine-tuning de BGE-M3  
**Sistemas afectados:** MOL (local, Python), OE (Supabase/Next.js), VPS (FastAPI)

---

## Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.2 | 2026-04-08 | E1.1 VPS documentado + sin chromadb. E1.3 SHA via cache HF. E1.5 threshold 5%. E2.2 boosting post-matching. E3.1 sector_canonico.json agregado. E3.3 throttling Supabase. Tests por sub-etapa |
| 1.1 | 2026-04-08 | E2.4 vinculado con M-09b Comp4. E2.5 con regeneración incremental. E3 coordinación con nlp_correccion_sector. E4.3 dataset actualizado con correcciones de Cynthia |
| 1.0 | 2026-04-08 | Versión inicial |

---

## Descripción del sistema (para lectura externa)

Este spec pertenece a un sistema de inteligencia de mercado laboral argentino llamado **MOL (Monitor de Ofertas Laborales)**, desarrollado para OEDE (Observatorio de Empleo y Dinámica Empresarial). El sistema tiene dos dimensiones principales:

### MOL — Pipeline de procesamiento (local, Python)

Scrapea ofertas de empleo de 6 portales argentinos (Bumeran, ZonaJobs, ComputRabajo, Indeed, PortalEmpleo, CABA) y las procesa en tres etapas:

1. **NLP** (Qwen2.5:14b via Ollama): extrae campos estructurados del texto crudo de cada oferta (título, empresa, ubicación, tareas, skills, modalidad, etc.)
2. **Skills extractor** (BGE-M3 + embeddings): convierte las tareas extraídas en skills ESCO mediante matching semántico. Corpus: 14.247 skills ESCO europeo completo almacenadas como vectores en `.npy`
3. **Matcher de ocupaciones** (BGE-M3 + reglas): asigna cada oferta a una ocupación ESCO usando matching semántico del título contra 3.045 ocupaciones, combinado con 300 reglas de negocio

**Escala actual:** 48.532 ofertas procesadas. Precisión de matching: 81.6% sobre Gold Set de 49 casos validados manualmente.

**Stack técnico local:** Python, SQLite, NumPy (embeddings como `.npy`), Ollama, PC con 64GB RAM / 12GB VRAM GPU.

### OE — Skills Intelligence (Supabase + Next.js)

Plataforma para oficinas de empleo que permite:
- Cargar el perfil de competencias de un trabajador
- Hacer matching semántico contra ocupaciones ESCO y ofertas reales del mercado
- Detectar brechas de skills y sugerir capacitación

**Stack técnico OE:** Next.js (Vercel), Supabase (PostgreSQL + pgvector), RPCs SQL para búsqueda vectorial.

### VPS (Hostinger)

Servidor de producción que cumple dos roles:
1. **Scraping**: cron Lun/Jue 08:00 para los 3 portales activos
2. **Servidor de embeddings**: FastAPI en puerto 8082, modelo BGE-M3, usado por el dashboard OE en runtime para convertir texto libre en vectores

### Taxonomías de referencia

**ESCO (European Skills, Competences, Qualifications and Occupations):** Taxonomía europea de ocupaciones y skills. El sistema usa la versión completa: 3.045 ocupaciones, 14.247 skills/conocimientos.

**esco_argentino (Perfil Consolidado Argentino):** Subconjunto curado por analistas de OEDE. Contiene 44 ocupaciones con sus skills consolidadas para el mercado argentino. 291 asignaciones ocupación→skill, de las cuales 267 son `mol_approved` (skills que aparecen frecuentemente en ofertas argentinas pero pueden no estar en ESCO europeo) y 24 son `esco_common` (skills ESCO que el mercado argentino confirma como relevantes). Versionado con snapshots en `perfil_argentino_versiones`.

**CLAE (Clasificación de Actividades Económicas):** Estándar argentino de AFIP para clasificar empresas por sector económico. El sistema usa 950 actividades a nivel clase (6 dígitos). Se asigna a cada oferta para permitir análisis sectorial del mercado laboral.

### Modelo de embeddings

**BGE-M3** (BAAI/bge-m3): modelo multilingüe de SentenceTransformers que produce vectores de 1024 dimensiones normalizados. Se usa para:
- Matching semántico tarea→skill (MOL local)
- Matching semántico título→ocupación (MOL local)
- Búsqueda semántica skills/ocupaciones (OE Supabase)
- Extracción de skills desde texto libre (dashboard OE via VPS)

El modelo corre en dos instancias: PC local (para el pipeline NLP/matching) y VPS (para el dashboard). Ambas instancias descargan `BAAI/bge-m3` de HuggingFace sin pinear una revisión específica, lo que introduce riesgo de drift.

### Glosario de términos usados en el spec

| Término | Significado |
|---------|-------------|
| `esco_argentino` | Tabla Supabase con el Perfil Consolidado Argentino (44 ocupaciones, 291 skills curadas) |
| `skills_embeddings` | Tabla Supabase con vectores BGE-M3 de las 14.247 skills ESCO |
| `occupations_embeddings` | Tabla Supabase con vectores BGE-M3 de las 3.045 ocupaciones ESCO |
| `.npy` | Archivos NumPy con los corpus de embeddings usados por el pipeline local |
| `corpus_manifest.json` | Archivo de registro (a crear) que documenta qué modelo generó cada corpus |
| `training_pairs` | Pares (input incorrecto, clasificación correcta) usados para fine-tuning. 602 totales: 66 validados por humanos, 536 auto-generados |
| `Gold Set` | 49 casos validados manualmente usados como benchmark de precisión |
| `mol_approved` | Skills en esco_argentino detectadas en ofertas argentinas y aprobadas por analistas |
| `esco_common` | Skills ESCO europeas que el mercado argentino confirma como relevantes |
| `emergentes_pendientes` | 431 skills detectadas automáticamente como candidatas al perfil argentino, sin procesar |
| `CLAESemanticClassifier` | Clase Python que clasifica ofertas por sector económico CLAE usando BGE-M3 |
| `recalcular_emergentes()` | RPC Supabase que detecta skills frecuentes en ofertas argentinas no cubiertas por esco_argentino |
| `pipeline_runs` | Tabla de registro de ejecuciones del pipeline con métricas agregadas |
| `M-17` | Issue en el roadmap del sistema: construir base de datos limpia para fine-tuning de BGE-M3 |

---

## Contexto y motivación

El sistema tiene cuatro usos activos de embeddings (NLP tarea→skill, matching título→ocupación, OE skills→ocupaciones, dashboard texto→skills) operando con dos instancias de BGE-M3 potencialmente distintas, sin versionado, sin coordinación entre sí, y desconectados del trabajo de curación humana que existe en `esco_argentino`.

El diagnóstico reveló:

- **Tres fuentes de embeddings no coordinadas:** `.npy` locales (regenerados Apr 7 via VPS), Supabase pgvector (generados Mar 31–Apr 1), ChromaDB (diciembre 2025, inactivo). Los `.npy` actuales difieren 2.5% de los baselines sin causa documentada.
- **Perfil Argentino desconectado del matching:** `esco_argentino` tiene 291 asignaciones curadas (44 ocupaciones, 220 skills únicas, 267 `mol_approved`) pero el pipeline de matching las ignora completamente. Solo se usa para display en la UI.
- **Ciclo de curación roto:** `recalcular_emergentes()` tiene un bug (`isco_code` es NULL en todas las filas). 431 emergentes pendientes sin procesar. Aprobar una emergente no dispara ningún downstream.
- **CLAE 84% funcional pero fuente perdida:** `clae_semantic_classifier.py` no existe en disco (solo `.pyc`). 10.084 ofertas caen a `default_seccion` (clasificación genérica). 6.777 sin CLAE porque `sector_empresa = "Otro"`.
- **Training pairs contaminados:** 536 de 602 pares son auto-generados con el 18.4% de error del sistema incorporado. Solo 66 tienen validación humana confirmada.

Este spec resuelve todo esto en cuatro etapas independientes que se pueden implementar en paralelo o en secuencia.

---

## Arquitectura objetivo

```
FUENTE DE VERDAD: PC LOCAL
├── Modelo: BAAI/bge-m3 @ revision SHA pineada
├── Genera: esco_skills_embeddings_full.npy (14,247 × 1024)
│           esco_occupations_embeddings.npy (3,045 × 1024)
│           clae_actividades_embeddings.npy (950 × 1024)
└── Sube a: Supabase (skills_embeddings, occupations_embeddings)

VPS (187.124.150.28:8082)
└── Sirve: embeddings runtime para dashboard OE
    Modelo: BAAI/bge-m3 @ MISMO revision SHA

SUPABASE (pgvector)
├── skills_embeddings (14,247 rows) ← sincronizado desde .npy local
├── occupations_embeddings (3,045 rows) ← sincronizado desde .npy local
└── RPCs que priorizan esco_argentino en resultados

CHROMADB: ELIMINADO
```

**Principio:** LOCAL genera, VPS sirve, Supabase consume. Mismo modelo pineado en ambas instancias.

---

## Etapa 1 — Infraestructura base

### E1.1 — Pinear revisión del modelo

**Problema:** `SentenceTransformer("BAAI/bge-m3")` descarga la versión más reciente de HuggingFace sin control. El VPS y la PC local pueden tener versiones distintas. Esto explica el drift del 2.5% detectado.

**Solución:** Pinear el commit SHA exacto del modelo en ambos entornos.

```python
# Obtener SHA actual del modelo en cache local:
# ~/.cache/huggingface/hub/models--BAAI--bge-m3/refs/main → leer este archivo

# Usar en código:
MODEL_NAME = "BAAI/bge-m3"
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406f efbe34"  # ← completar con SHA real

model = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION)
```

**Archivos a modificar:**
- `database/skills_implicit_extractor.py` línea 67: `DEFAULT_MODEL = "BAAI/bge-m3"` → agregar `DEFAULT_MODEL_REVISION`
- `config/matching_config.json`: agregar campo `"modelo_revision": "<SHA>"`
- VPS: actualizar `embed_server.py` con el mismo SHA (requiere SSH al servidor, modificar archivo, reiniciar servicio systemd)

**Nota:** `scripts/db/create_chromadb_esco.py` NO se modifica — será eliminado en E1.4.

**Proceso VPS (manual):**
```bash
ssh root@187.124.150.28
cd /ruta/embed_server
# Editar embed_server.py: agregar revision=MODEL_REVISION_SHA al SentenceTransformer()
systemctl restart embed-server
curl http://localhost:8082/health  # verificar que levantó
```

**Centralizar en un solo lugar:**

```python
# config/embedding_config.py (NUEVO)
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_REVISION = "<SHA_A_COMPLETAR>"  # git hash de HF
EMBEDDING_DIMS = 1024
EMBEDDING_NORMALIZE = True
EMBEDDING_BATCH_SIZE = 12
```

Todos los scripts importan desde este archivo. Si cambia el modelo, se cambia en un solo lugar.

### E1.2 — Model Registry: versionado por corpus

**Problema:** Ningún embedding almacenado registra qué modelo lo generó ni cuándo. Si se regenera, no hay forma de saber si los embeddings en producción son de antes o después.

**Solución:** Archivo de manifiesto que acompaña a cada corpus.

```json
// database/embeddings/corpus_manifest.json (NUEVO)
{
  "esco_skills": {
    "file": "esco_skills_embeddings_full.npy",
    "shape": [14247, 1024],
    "model": "BAAI/bge-m3",
    "model_revision": "<SHA>",
    "generated_at": "2026-04-07T16:58:00Z",
    "generated_by": "VPS:187.124.150.28",
    "source_table": "esco_skills",
    "source_count": 14247,
    "normalize": true,
    "checksum_sha256": "<hash_del_npy>"
  },
  "esco_occupations": {
    "file": "esco_occupations_embeddings.npy",
    "shape": [3045, 1024],
    "model": "BAAI/bge-m3",
    "model_revision": "<SHA>",
    "generated_at": "2026-04-08T10:47:00Z",
    "generated_by": "VPS:187.124.150.28",
    "source_table": "esco_occupations",
    "source_count": 3045,
    "normalize": true,
    "checksum_sha256": "<hash_del_npy>"
  },
  "clae_actividades": {
    "file": "clae_actividades_embeddings.npy",
    "shape": [950, 1024],
    "model": "BAAI/bge-m3",
    "model_revision": "<SHA>",
    "generated_at": "2026-02-13T00:00:00Z",
    "generated_by": "LOCAL",
    "source_table": "clae_nomenclador",
    "source_count": 950,
    "normalize": true,
    "checksum_sha256": "<hash_del_npy>"
  }
}
```

En Supabase, agregar columna `embedding_model_version TEXT` a `skills_embeddings` y `occupations_embeddings`. Poblarla con el SHA al regenerar.

Agregar campo `embedding_model_version` a `pipeline_runs` en SQLite para cerrar el linaje oferta→embedding.

### E1.3 — Validación de compatibilidad al cargar

**Problema:** El modelo local puede diferir del que generó los `.npy`. Hoy no hay verificación.

**Solución:** Al iniciar `SkillsImplicitExtractor`, verificar que el modelo cargado coincide con el manifiesto:

```python
def _verify_corpus_compatibility(self):
    manifest = json.load(open('database/embeddings/corpus_manifest.json'))
    expected_revision = manifest['esco_skills']['model_revision']
    
    # Obtener revision del modelo cargado — leer desde cache de HuggingFace
    # Más robusto que acceder a internals de sentence-transformers
    import os
    hf_cache = os.path.expanduser(
        "~/.cache/huggingface/hub/models--BAAI--bge-m3/refs/main"
    )
    try:
        with open(hf_cache) as f:
            actual_revision = f.read().strip()
    except FileNotFoundError:
        # Fallback: intentar via huggingface_hub si está instalado
        try:
            from huggingface_hub import model_info
            info = model_info("BAAI/bge-m3")
            actual_revision = info.sha
        except Exception:
            actual_revision = "desconocido"
    
    if actual_revision != expected_revision and actual_revision != "desconocido":
        raise RuntimeError(
            f"INCOMPATIBILIDAD DE EMBEDDINGS: "
            f"Modelo cargado ({actual_revision[:8]}) difiere del que generó el corpus ({expected_revision[:8]}). "
            f"Regenerar embeddings con: python scripts/db/regenerate_all_embeddings.py"
        )
```

Esta verificación corre al iniciar el extractor. Si hay incompatibilidad, falla ruidosamente en lugar de producir scores incorrectos en silencio.

**Por qué no usar `_commit_hash`:** Es un atributo interno de sentence-transformers que puede cambiar entre versiones de la librería. Leer el archivo de refs del cache de HuggingFace es más estable y no depende de internals.

### E1.4 — Limpieza de artefactos

**Eliminar sin riesgo:**
- `database/esco_vectors/` (ChromaDB inactivo, embeddings de dic 2025)
- `database/embeddings/esco_skills_embeddings.npy` (6 vectores, obsoleto)
- `database/embeddings/esco_skills_metadata.json` (6 entradas, obsoleto)
- Dependencia `chromadb` de `requirements.txt`

**Conservar (potencial uso futuro):**
- `database/embeddings/esco_descriptions_embeddings.npy` — embeddings de descripciones largas de ocupaciones, útil para matching semántico por descripción en M-17
- `database/embeddings/esco_skills_embeddings_full_baseline.npy` — baseline enero 2026, referencia para medir drift
- `database/embeddings/esco_occupations_embeddings_baseline.npy` — baseline noviembre 2025

Mover los baselines a `database/embeddings/baselines/` para distinguirlos de los activos.

### E1.5 — Pipeline de regeneración controlada

**Problema:** No existe un proceso para regenerar todos los corpus de forma coordinada, validar que son correctos, y hacer rollback si algo falla.

**Solución:** Script `scripts/db/regenerate_all_embeddings.py`:

```python
"""
Regenera todos los corpus de embeddings en orden.
Valida contra Gold Set antes de activar.
Soporta rollback automático si la validación falla.

Uso:
  python scripts/db/regenerate_all_embeddings.py --dry-run   # solo verifica
  python scripts/db/regenerate_all_embeddings.py             # regenera todo
  python scripts/db/regenerate_all_embeddings.py --corpus skills  # solo skills
"""
```

**Orden de regeneración:**
1. Backup de `.npy` activos → `database/embeddings/backups/YYYYMMDD_HHMMSS/`
2. Generar nuevo corpus (local con modelo pineado)
3. Actualizar manifiesto con SHA, timestamp, checksum
4. Correr Gold Set → si precisión < baseline - 5%, rollback automático
   (threshold conservador: con 49 casos, 2% = 1 caso, no significativo.
   Revisar a 2% cuando Gold Set llegue a 150+ casos — ver E4.4)
5. Si OK: subir a Supabase con `embedding_model_version` poblado
6. Registrar en `pipeline_runs` con `embedding_model_version`

---

## Etapa 2 — Perfil Argentino conectado al ciclo vivo

### E2.1 — Corregir bug isco_code NULL

**Problema:** `recalcular_emergentes()` cruza `ofertas_skills × esco_argentino` por `isco_code`, pero `esco_argentino.isco_code` es NULL en las 44 filas. El cruce no funciona correctamente.

**Solución:** El cruce debe hacerse por `esco_occupation_uri`, no por `isco_code`.

```sql
-- ANTES (roto):
WHERE oa.isco_code = ea.isco_code

-- DESPUÉS (correcto):
WHERE oa.occupation_uri = ea.esco_occupation_uri
```

Adicionalmente, poblar `esco_argentino.isco_code` desde la tabla `ocupaciones_esco` que sí tiene ese campo.

### E2.2 — Conectar esco_argentino al matching de MOL (boosting)

**Diseño:** El extractor re-rankea sus resultados DESPUÉS del matching
de ocupación, aplicando un bonus a las skills del Perfil Argentino.

**Problema de circularidad resuelto:**
El boosting NO puede aplicarse antes de conocer la ocupación porque
la ocupación se determina a partir de las skills. La solución es
una segunda pasada post-matching:

```
Paso 1: extract_skills() → extrae skills normalmente (sin boost)
Paso 2: match() → determina ocupación usando esas skills  
Paso 3: rerank_with_argentino_boost(occupation_uri) → re-rankea
Paso 4: Persistir skills re-rankeadas
```

**Por qué boosting y no filtrado:** El perfil cubre solo 44 ocupaciones.
Para las 3.001 restantes no hay información en esco_argentino. El boosting
degrada graciosamente: sin perfil argentino, el resultado es idéntico.

**Por qué proporcional a frecuencia:** Skills con frequency=3 deben
subir más que skills con frequency=1.

**Nueva función en skills_implicit_extractor.py:**

Agregar método `rerank_with_argentino_boost(skills, occupation_uri)`
que se llama desde `match_ofertas_v3.py` después de determinar la
ocupación. El método aplica boost_factor = 0.05 * (frequency / max_freq)
y re-ordena por score. Boost máximo: 0.05 (5 puntos porcentuales).

**Punto de integración en match_ofertas_v3.py:**
Después de determinar ocupacion_uri, llamar:
`oferta_nlp['skills_implicitas'] = extractor.rerank_with_argentino_boost(skills, ocupacion_uri)`


### E2.3 — Conectar esco_argentino a las RPCs de OE

**Problema:** Las 4 RPCs de Supabase operan sobre ESCO puro sin priorizar las skills curadas para Argentina.

**Solución:** Agregar parámetro `prioritize_argentino` a `expand_skills_semantic` y `match_occupations_by_skills`. Cuando está activo, las skills de `esco_argentino` aparecen primero en los resultados antes del ordenamiento por similitud.

```sql
-- Modificar expand_skills_semantic para aceptar occupation_uri
-- y retornar campo is_argentino en cada resultado

CREATE OR REPLACE FUNCTION expand_skills_semantic(
    skill_uris TEXT[],
    occupation_uri TEXT DEFAULT NULL,  -- NUEVO parámetro
    match_threshold FLOAT DEFAULT 0.55,
    max_results INT DEFAULT 8
)
RETURNS TABLE(
    skill_uri TEXT,
    skill_label TEXT,
    similarity FLOAT,
    is_argentino BOOLEAN  -- NUEVO campo
) AS $$
    -- ... lógica existente ...
    -- LEFT JOIN con esco_argentino para marcar is_argentino
    -- ORDER BY is_argentino DESC, similarity DESC
$$ LANGUAGE plpgsql;
```

### E2.4 — Activar downstream post-aprobación

**Problema:** Aprobar una emergente en el panel admin no dispara nada. El ciclo está roto después de la aprobación.

**Nota de coordinación con M-09b Componente 4:**
El sistema tiene dos flujos de aprobación que deben usar el mismo
patrón pero son independientes:
- **E2.4 (este):** aprobación de emergentes del Perfil Argentino
  (skills detectadas automáticamente → analista aprueba)
- **M-09b Comp4:** aprobación de correcciones de validadores humanos
  (Cynthia corrige → Claude propone → operador aprueba)

Ambos flujos generan training pairs de alta confianza al aprobar.
Ambos usan `rule_candidates` como tabla de staging (Comp4) o
el endpoint de aprobación directa (E2.4). El patrón de generar
training pair al aprobar es idéntico en ambos casos.

**Triggers a implementar cuando se aprueba una emergente:**

1. **Actualizar `esco_argentino`:** Insertar la skill en `skills_consolidadas` de la ocupación correspondiente con `source: "mol_approved"`.

2. **Regenerar `skills_searchable.json`:** El catálogo unificado (ESCO + emergentes) usado por la búsqueda de la UI debe incluir la nueva skill. Trigger: `POST /api/admin/perfil-argentino/approve` → llamar `regenerate_skills_searchable.py`.

3. **Crear training pair:** Cada aprobación es señal supervisada de alta calidad. Generar automáticamente un training pair en `config/training_pairs.json` con `autor: "sistema_aprobacion"`, `confianza: "alta"`, y la justificación del analista si la proveyó.
   **Ver también:** M-09b Comp4 hace lo mismo al aprobar candidatos
   de tipo `regla_nueva` — ambos flujos alimentan E4.3.

4. **Notificar para corte de versión:** Cuando las aprobaciones acumuladas desde el último corte superan N (configurable, default 10), notificar al analista que hay suficientes cambios para crear una nueva versión del perfil.

### E2.5 — Corte de versión dispara regeneración de embeddings

**Problema:** Crear una nueva versión del perfil argentino no regenera los embeddings ni actualiza las RPCs de OE. La nueva versión queda solo en el snapshot JSONB.

**Decisión de diseño — Regeneración incremental vs completa:**

Regenerar los 14.247 embeddings completos cada vez que se crea una
versión es costoso. La mayoría de los cambios entre versiones afectan
solo las skills del perfil argentino (291 skills sobre 44 ocupaciones).

**Opción recomendada: Regeneración incremental**
- Solo regenerar los embeddings de las skills que cambiaron
  (nuevas aprobaciones desde el último corte)
- Threshold: si los cambios afectan > 500 skills → regeneración completa
- Si los cambios afectan ≤ 500 skills → regeneración incremental

```
Analista crea versión v2.0
    ↓
Calcular diff: skills nuevas/modificadas desde v1.0
    ↓
Si diff > 500 skills → regeneración completa (pipeline_commands)
Si diff ≤ 500 skills → regeneración incremental (solo las cambiadas)
    ↓
INSERT en perfil_argentino_versiones con activa=TRUE
UPDATE activa=FALSE en versión anterior
    ↓
[NUEVO] Encolar job: regenerar embeddings del perfil activo
    → No bloquea la UI, corre en background
    → Job actualiza skills_embeddings en Supabase solo para
      las skills afectadas (o todas si regeneración completa)
    → Notifica cuando termina
    ↓
Matching, OE y reportes usan automáticamente la nueva versión
```

**Pendiente de implementación:** El script `regenerate_all_embeddings.py`
(E1.5) debe soportar flag `--incremental` que recibe lista de URIs
a regenerar. Agregar este flag al scope de E1.5.

---

## Etapa 3 — CLAE

**Nota de coordinación con M-09b Componente 4:**
El problema de `sector_empresa = "Otro"` se ataca desde dos ángulos
complementarios que NO se contradicen:

- **E3 (CLAE):** resuelve la clasificación sectorial a nivel macro
  usando la taxonomía AFIP de 950 actividades económicas.
  Es la fuente de verdad para análisis sectorial del mercado laboral.
  
- **M-09b Comp4 (`nlp_correccion_sector`):** resuelve el campo
  `sector_empresa` en el NLP para mejorar el matching de ocupaciones.
  Usa 10-15 reglas específicas por título ("herrero" → "Metalúrgica").

**Prioridad cuando ambos están disponibles:**
CLAE tiene precedencia sobre sector_empresa para análisis sectorial.
nlp_correccion_sector mejora el matching interno pero no reemplaza CLAE.
Cuando CLAE clasifica exitosamente una oferta, ese resultado puede
usarse para corregir sector_empresa retroactivamente.

### E3.1 — Recuperar clae_semantic_classifier.py

**Problema:** El archivo fuente `.py` no existe, solo los `.pyc` compilados. El pipeline lo importa con `try/except` degradado.

**Solución:** Reconstruir el archivo desde los `.pyc` y el comportamiento observado (documentado en el diagnóstico).

El clasificador a reconstruir implementa:

```python
class CLAESemanticClassifier:
    """
    Clasifica ofertas por código CLAE (6 dígitos) usando cascada jerárquica:
    1. sector_empresa → sección CLAE (letra A-S)
    2. Dentro de la sección: BGE-M3 cosine search → código 6 dígitos
    
    Reutiliza el modelo BGE-M3 del SkillsImplicitExtractor (no carga dos veces).
    """
    
    def __init__(self, extractor: SkillsImplicitExtractor):
        self.model = extractor.model  # reutilizar modelo cargado
        self.embeddings = np.load('database/embeddings/clae_actividades_embeddings.npy')
        self.metadata = json.load(open('database/embeddings/clae_actividades_metadata.json'))
        self._build_section_index()  # índice por sección para búsqueda eficiente
    
    def classify(self, sector_empresa: str, titulo: str, empresa: str = None,
                 id_area_portal: str = None) -> dict:
        """
        Retorna: {clae_code, clae_grupo, clae_seccion, clae_score, clae_metodo}
        """
```

**Algoritmo completo (incluyendo mejoras respecto al original):**

```
ENTRADA: sector_empresa, titulo, empresa, id_area_portal

Paso 0: id_area_portal disponible?
    SÍ → buscar en portal_area_to_clae.json (mapeo curado)
        → si hay match: return {método: "portal_directo", score: 1.0}
    NO → continuar

Paso 1: sector_empresa → SECCIÓN CLAE
    usar _sector_to_seccion (mapeo canónico)
    si sector = "Otro" o None:
        Fallback A: intentar inferir sección desde titulo_limpio
                    query = titulo
                    buscar en TODO el corpus CLAE (no filtrar por sección)
                    si score >= 0.45: usar sección del resultado
                    si score < 0.45: return {método: "sin_clasificar"}
    
Paso 2: dentro de la sección → código 6 dígitos
    query = sector_empresa + " " + titulo[:500]
    embeddings_seccion = self._section_index[seccion]
    scores = np.dot(embeddings_seccion, model.encode(query))
    top = argmax(scores)
    
    si scores[top] >= threshold (0.45):
        return {método: "semantico_seccion", score: scores[top]}
    else:
        return {método: "default_seccion", score: scores[top],
                code: DEFAULT_CODE[seccion]}
```

### E3.2 — Mapeo portal_area_to_clae

**Oportunidad:** El 51.9% de las ofertas tiene `id_area/id_subarea` del portal. Estos campos son clasificaciones ya hechas por el portal (Bumeran, ZonaJobs, ComputRabajo). Mapearlos a CLAE es trabajo de una vez que mejora permanentemente la cobertura.

**Implementación:**

```json
// config/portal_area_to_clae.json (NUEVO — completar manualmente o con LLM)
{
  "bumeran": {
    "tecnologia": { "clae_seccion": "J", "clae_code": "620100", "confianza": "alta" },
    "comercio": { "clae_seccion": "G", "clae_code": "471000", "confianza": "alta" },
    "salud": { "clae_seccion": "Q", "clae_code": "861000", "confianza": "alta" }
  },
  "zonajobs": { ... },
  "computrabajo": { ... }
}
```

**Prioridad en la cascada:** portal_directo > semantico_seccion > default_seccion > sin_clasificar.

### E3.3 — Reprocesar las 7.026 ofertas sin CLAE

Una vez implementadas E3.1 y E3.2, reprocesar las ofertas sin CLAE:

```bash
python scripts/db/reprocesar_clae.py --only-missing --batch-size 500
```

Meta: bajar de 7.026 sin CLAE a menos de 2.000.

**Throttling obligatorio para Supabase:**
7.026 UPDATEs en batch pueden saturar el free tier (~15 req/s).
El script debe incluir:
```python
import time
# Por cada batch de 500: actualizar + sleep(2)
# Rate efectivo: ~250 updates/seg → completa en ~30 segundos
# Sin throttling: posible rate limiting o timeout
```

---

## Etapa 4 — Training pairs limpios para M-17

### E4.1 — Separación por confianza

**Acción:** Agregar campo `confianza` a `config/training_pairs.json` para cada par existente.

```json
{
  "pares": [
    {
      "input": "...",
      "clasificacion_incorrecta": "...",
      "clasificacion_correcta": "...",
      "justificacion": "...",
      "autor": "Cynthia",
      "confianza": "alta",       // ← NUEVO: "alta" para humanos
      "split": "train"           // ← NUEVO: "train" | "validation"
    },
    {
      "autor": "sistema",
      "confianza": "baja",       // ← auto-generados
      "split": "validation"      // ← nunca al entrenamiento
    }
  ]
}
```

**Regla de asignación:**
- `autor` en ["Cynthia", "Diego Javier Schleser", "Gerardo Breard"] → `confianza: "alta"`, `split: "train"`
- `autor` = "sistema" o similar → `confianza: "baja"`, `split: "validation"`

**Resultado:** 66 pares de entrenamiento (señal limpia), 536 de validación (para detectar regresiones).

### E4.2 — Convertir asignaciones de esco_argentino en training pairs

**Las 291 asignaciones en `esco_argentino` son señal supervisada de alta calidad** (humanos aprobaron que esa skill pertenece a esa ocupación en el mercado argentino). Convertirlas a training pairs para BGE-M3.

**Formato de par para fine-tuning de embeddings (contrastivo):**

```json
{
  "query": "nombre de la tarea o skill en español argentino",
  "positive": "uri_skill_esco_correcta + label",
  "negatives": ["uri_skill_parecida_1", "uri_skill_parecida_2"],
  "occupation_context": "uri_ocupacion",
  "source": "esco_argentino_v1.0",
  "confianza": "alta"
}
```

**Script:** `scripts/ml/generate_training_pairs_from_argentino.py`

```python
"""
Genera training pairs para fine-tuning de BGE-M3 desde esco_argentino.

Por cada asignación (ocupación, skill):
1. La skill curada = positive
2. Top-5 skills semánticamente similares que NO están en el perfil = hard negatives
3. Guardar en formato compatible con sentence-transformers

Output: data/fine_tuning/training_pairs_argentino.json
"""
```

### E4.3 — Dataset final para M-17

**Composición:**

| Dataset | Fuente | Tamaño | Uso |
|---------|--------|--------|-----|
| `train_human.json` | 66 pares humanos validados (Cynthia, Diego, Gerardo) | 66 | Entrenamiento |
| `train_correcciones.json` | Correcciones de Cynthia aprobadas via M-09b Comp4 | ~31 actuales + crecimiento continuo | Entrenamiento |
| `train_argentino.json` | 291 asignaciones esco_argentino convertidas | ~291 | Entrenamiento |
| `validation_auto.json` | 536 pares auto-generados (baja confianza) | 536 | Validación / detección regresiones |
| `validation_gold.json` | Gold Set 49 casos | 49 | Benchmark principal |

**Total entrenamiento estimado: ~388 pares de alta confianza** (66 humanos + 31 correcciones + 291 argentino).
Cada aprobación desde M-09b Comp4 agrega un par nuevo automáticamente.
Con el flujo activo de Cynthia (~10 correcciones/semana), se estima
llegar a 500+ pares en 4-6 semanas de uso normal.

**Fuente `train_correcciones.json` — cómo se genera:**
Cada vez que el operador aprueba un candidato de tipo `regla_nueva`
o `fix_regla` en `/admin/procesamiento/correcciones` (M-09b Comp4),
el sistema genera automáticamente un training pair:
```json
{
  "query": "gerente administración",
  "clasificacion_incorrecta": "4110",
  "clasificacion_correcta": "1211",
  "justificacion": "Gerente de administración clasificado como empleado de oficina",
  "autor": "cynthia+operador",
  "confianza": "alta",
  "split": "train",
  "issue_id": "#7006539054",
  "oferta_ejemplo": "7006539054"
}
```

**Meta intermedia antes de fine-tuning:** Expandir Gold Set a 150+ casos (M-10) y mantener el flujo activo de M-09b Comp4 para llegar a 500+ pares de entrenamiento.

### E4.4 — Criterio go/no-go para fine-tuning

No arrancar fine-tuning hasta cumplir:

| Criterio | Valor mínimo | Estado actual |
|----------|-------------|---------------|
| Pares de entrenamiento alta confianza | 500 | ~388 (con E4.2 + correcciones Cynthia), creciendo via M-09b Comp4 |
| Gold Set casos | 150 | 49 |
| Precisión baseline Gold Set | conocida y estable | 81.6% (Feb 2026) |
| Model Registry implementado | sí | No (E1 lo resuelve) |
| Linaje embedding→oferta | sí | No (E1 lo resuelve) |

---

## Dependencias entre etapas

```
E1 (Infraestructura)
├── E1.1 Pinear modelo ──────────────────────────────┐
├── E1.2 Model Registry ────────────────────────────┐│
├── E1.3 Validación compatibilidad ───── depende E1.1││
├── E1.4 Limpieza ──────────────── independiente     ││
└── E1.5 Pipeline regeneración ──── depende E1.1+E1.2││
                                                     ││
E2 (Perfil Argentino)                                ││
├── E2.1 Fix isco_code ──── independiente            ││
├── E2.2 Boosting MOL ───── depende E2.1             ││
├── E2.3 RPCs OE ────────── depende E2.1             ││
├── E2.4 Downstream aprobación ─── depende E2.1      ││
└── E2.5 Corte → regeneración ── depende E1.5 + E2.4 ││
                                                     ││
E3 (CLAE)                                            ││
├── E3.1 Recuperar classifier ── independiente       ││
├── E3.2 Mapeo portal_area ───── independiente       ││
└── E3.3 Reprocesar sin CLAE ─── depende E3.1+E3.2  ││
                                                     ││
E4 (Training pairs / M-17)                           ││
├── E4.1 Separar confianza ──── independiente        ││
├── E4.2 Pares desde argentino ─ depende E2.1        ││
├── E4.3 Dataset final ──────── depende E4.1+E4.2    ││
└── E4.4 Go/no-go fine-tuning ── depende E1 completo ││
                                          ←──────────┘│
                                          ←───────────┘
```

**Secuencia recomendada:**
1. E1.4 (limpieza) — sin riesgo, libera espacio mental y de disco
2. E2.1 (fix isco_code) — pequeño, desbloquea E2.2 y E2.3
3. E4.1 (separar training pairs) — pequeño, sin dependencias
4. E1.1 + E1.2 (pinear modelo + manifiesto) — base de todo
5. E3.1 + E3.2 (CLAE) — independiente, alto valor
6. E2.2 + E2.3 (boosting + RPCs) — después de E2.1
7. E1.5 (pipeline regeneración) — después de E1.1 + E1.2
8. E2.4 + E2.5 (downstream aprobación) — después de E1.5
9. E4.2 + E4.3 (dataset M-17) — después de E2.4
10. E4.4 fine-tuning — cuando se cumplan los criterios go/no-go

---

## Requisito de tests por sub-etapa

Cada sub-etapa requiere tests antes de commit. Tests mínimos:

| Sub-etapa | Tests requeridos |
|-----------|-----------------|
| E1.1 Pinear modelo | test que el modelo carga con SHA correcto; test que falla si SHA no coincide |
| E1.2 Manifiesto | test que corpus_manifest.json existe y tiene checksum válido |
| E1.3 Validación | test que lanza RuntimeError con modelo incorrecto |
| E1.4 Limpieza | verificar que archivos eliminados no son importados en ningún módulo |
| E1.5 Regeneración | test dry-run completa sin errores; test rollback si Gold Set falla |
| E2.1 Fix isco_code | test que recalcular_emergentes() retorna filas con isco_code no-null |
| E2.2 Boosting | test que skill del perfil argentino sube en ranking post-boost |
| E2.3 RPCs OE | test que expand_skills_semantic retorna campo is_argentino |
| E2.4 Downstream | test que aprobar emergente genera training pair |
| E3.1 CLAE | test classify("Tecnologia", "desarrollador python") → sección J |
| E3.2 Mapeo portal | test que oferta con id_area conocido retorna método "portal_directo" |
| E3.3 Reprocesar | test que script no rompe ofertas ya clasificadas |
| E4.1 Confianza | test que todos los pares tienen campo confianza y split |
| E4.2 Pares argentino | test que pares generados tienen formato correcto para sentence-transformers |

---

## Criterios de aceptación por etapa

### Etapa 1
- [ ] `config/embedding_config.py` centraliza modelo y revisión SHA
- [ ] `corpus_manifest.json` existe y tiene checksum verificable
- [ ] Al iniciar el extractor con modelo incorrecto, falla con error claro
- [ ] `database/esco_vectors/` eliminado
- [ ] `scripts/db/regenerate_all_embeddings.py` corre end-to-end con rollback

### Etapa 2
- [ ] `recalcular_emergentes()` cruza por `esco_occupation_uri` (no `isco_code`)
- [ ] Aprobar una emergente genera training pair automáticamente
- [ ] El extractor de skills aplica boost cuando hay perfil argentino disponible
- [ ] `expand_skills_semantic` retorna campo `is_argentino` en cada resultado
- [ ] Crear versión del perfil encola regeneración de embeddings

### Etapa 3
- [ ] `database/clae_semantic_classifier.py` existe como archivo fuente editable
- [ ] `config/portal_area_to_clae.json` tiene los 3 portales principales mapeados
- [ ] Ofertas sin CLAE bajan de 7.026 a menos de 2.000
- [ ] `clae_metodo` muestra el nuevo valor `"portal_directo"` en las clasificadas por portal

### Etapa 4
- [ ] Todos los training pairs tienen campos `confianza` y `split`
- [ ] `data/fine_tuning/training_pairs_argentino.json` generado con pares desde esco_argentino
- [ ] `data/fine_tuning/train_human.json` tiene exactamente 66 pares
- [ ] Tabla resumen del dataset final con conteos por fuente y split

---

## Archivos nuevos a crear

| Archivo | Etapa | Propósito |
|---------|-------|-----------|
| `config/embedding_config.py` | E1.1 | Configuración centralizada del modelo |
| `database/embeddings/corpus_manifest.json` | E1.2 | Registro de versión por corpus |
| `scripts/db/regenerate_all_embeddings.py` | E1.5 | Regeneración controlada con rollback |
| `database/clae_semantic_classifier.py` | E3.1 | Reconstrucción del clasificador CLAE |
| `config/sector_canonico.json` | E3.1 | Mapeo sector_empresa → sección CLAE (A-S) |
| `config/portal_area_to_clae.json` | E3.2 | Mapeo área de portal → CLAE |
| `scripts/db/reprocesar_clae.py` | E3.3 | Reprocesar ofertas sin CLAE |
| `scripts/ml/generate_training_pairs_from_argentino.py` | E4.2 | Pares desde esco_argentino |
| `data/fine_tuning/` | E4.3 | Directorio datasets fine-tuning |
| `data/fine_tuning/train_correcciones.json` | E4.3 | Pares desde correcciones de Cynthia aprobadas via M-09b Comp4 |

## Archivos a modificar

| Archivo | Etapa | Cambio |
|---------|-------|--------|
| `database/skills_implicit_extractor.py` | E1.1 + E2.2 | Pinear modelo + boosting argentino |
| `scripts/db/create_chromadb_esco.py` | E1.1 | Pinear modelo (o deprecar) |
| `config/matching_config.json` | E1.1 | Agregar `modelo_revision` |
| `config/training_pairs.json` | E4.1 | Agregar `confianza` y `split` |
| RPCs Supabase | E2.3 | `expand_skills_semantic` con `is_argentino` |
| `sync_to_supabase.py` | E2.5 | Llamar `recalcular_emergentes()` al final |
