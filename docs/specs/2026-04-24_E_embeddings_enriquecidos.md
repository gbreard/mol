# SPEC E — Reconstrucción de embeddings ESCO enriquecidos

**Fecha:** 2026-04-24
**Autor:** Claude + Gerardo
**Estado:** Draft — pendiente análisis de factibilidad
**Scope:** Regeneración de `esco_skills_embeddings_full.npy` + `esco_occupations_embeddings.npy` + sus metadatos. Ajuste downstream en `skills_implicit_extractor.py` y `match_by_skills.py`.
**Reemplaza intentos anteriores:** Spec B (filtro post-hoc invalidado por Fase 0), Spec D (filtro por coherencia invalidado por Fase 0).
**Basado en:** `2026-04-24_E_FASE0_prototipo.md` (evidencia empírica sobre caso Cyn).

---

## 1. Contexto y motivación

### 1.1 Historia del problema

En varios ciclos (Spec B, Spec D, issues reportados por Cyn) se detectó que el matching de skills asigna skills de dominios ajenos: "operario metalúrgico" recibe `producir diseños textiles`, `equipos de acuicultura`, `animación de partículas`. El ruido no es aleatorio, es sistemático.

Los approaches de filtrado post-hoc (Spec B trust-source, Spec D coherencia ESCO) mitigan casos específicos pero no resuelven el root cause: **BGE-M3 genera el ruido en la fase de extracción porque los embeddings no discriminan dominios**.

### 1.2 Descubrimiento del root cause (Fase 0)

Los embeddings ESCO vigentes (`esco_skills_embeddings_full.npy`, 14,247 × 1024) se generaron usando exclusivamente el campo `label` de cada skill. El metadata (`esco_skills_metadata_full.json`) tiene:
```json
{"uri": "...", "label": "gestionar tareas en relación con los músicos", "description": ""}
```

El campo `description` está vacío. Sin embargo, **toda la información rica del RDF ESCO ya fue extraída** y reside en:
- `esco_skills_full.json` (14,257 skills con description + L1/L2 + broader + type — 100% completitud)
- `esco_skill_to_occupations.json` (relación skill→ocupaciones con esco_code para 13,492 skills)
- `esco_occupations_full.json` (3,047 ocupaciones con jerarquía ESCO)

**Los datos existen. Solo no se usaron al vectorizar.**

### 1.3 Prototipo validado

Sobre 575 skills (ver `2026-04-24_E_FASE0_prototipo.md`), embeddings enriquecidos con `label + categoría L1/L2 + broader + top-3 ocupaciones con esco_code + description` muestran discriminación semántica por dominio:

- Viejo: `Conocimiento de soldadura` → enfermería, animación de partículas, radioterapia.
- Nuevo: `Conocimiento de soldadura` → manejar equipos de soldadura, emplear técnicas de soldadura, conductividad térmica de los metales.

---

## 2. Objetivo

Reemplazar los embeddings y metadatos actuales por versiones enriquecidas, respetando los códigos ESCO como identificador principal (no ISCO), y propagar la mejora a las 49,117 ofertas validadas.

---

## 3. Diseño técnico

### 3.1 Texto enriquecido por skill

**Entrada:** registro de `esco_skills_full.json` + lookup a `esco_skill_to_occupations.json`.

**Estructura del texto que recibe BGE-M3:**
```
{label}
Categoría: {L1}.{L2} {category_label}
Tipo general: {broader_label}
Típica en: {top 3 ocupaciones essential_for, formato "label (esco_code)"}
{description truncada a 500 chars}
```

**Reglas:**
- Si no hay `description` no agregar esa línea.
- Si no hay ocupaciones `essential_for` usar `optional_for`.
- Si la skill no tiene ninguna ocupación (orfanas), omitir esa línea.
- Normalización: lowercase opcional (preservar ESCO por default para casos como "AutoCAD"). Decisión por validar.

**Output:** string UTF-8 de 200-1000 caracteres aprox.

### 3.2 Texto enriquecido por ocupación

**Entrada:** registro de `esco_occupations_full.json`.

**Estructura:**
```
{label} [ESCO {esco_code}]
Jerarquía ISCO: {isco_1d} > {isco_2d} > {isco_3d} > {isco_4d}
Skills esenciales: {top 5 skills essential_for, labels solamente}
{description}
```

**Output:** string de 300-1500 caracteres.

### 3.3 Metadata nuevo — skills

**Formato (reemplaza `esco_skills_metadata_full.json`):**
```json
{
  "uri": "http://data.europa.eu/esco/skill/...",
  "label": "ocuparse de remachadoras",
  "description": "Manejar máquinas diseñadas para unir piezas metálicas...",
  "type": "skill",
  "L1": "S8",
  "L2": "S8.5",
  "category_code": "S8.5",
  "category_label": "manejar equipos de producción de material impreso y fotográfico",
  "broader_uri": "...",
  "broader_label": "manejar herramientas mecánicas",
  "esco_codes_aplicable": ["7214.3.1", "7214.3", "8189.5"],
  "n_occupations": 3,
  "texto_indexado": "ocuparse de remachadoras\\nCategoría: S8.5 manejar equipos...\\nTípica en: ..."
}
```

**Novedad vs actual:** todos los campos excepto `uri`, `label`, `description`. El campo `esco_codes_aplicable` es el puente crítico con el sistema de reglas matching (que ya apuntan a ocupaciones ESCO vía `esco_label`).

### 3.4 Metadata nuevo — ocupaciones

**Formato (reemplaza `esco_occupations_metadata.json`):**
```json
{
  "uri": "http://data.europa.eu/esco/occupation/...",
  "label": "remachador/remachadora",
  "esco_code": "7214.3.1",
  "isco_4dig": "7214",
  "isco_3dig": "721",
  "isco_2dig": "72",
  "isco_1dig": "7",
  "description": "...",
  "broader_uri": "...",
  "broader_label": "ferrallista",
  "skills_esenciales": ["uri1", "uri2", ...],
  "skills_optativas": ["uri3", "uri4", ...],
  "texto_indexado": "..."
}
```

**Novedad crítica:** `esco_code` existe (hoy solo hay `isco_code` con prefijo `C`). ISCO queda como derivado jerárquico para navegabilidad, no como identificador primario.

### 3.5 Generación de embeddings

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')

textos = [texto_enriquecido(uri) for uri in skill_uris]
embeddings = model.encode(textos, normalize_embeddings=True, batch_size=32)
# Shape: (14247, 1024)
np.save('esco_skills_embeddings_full.npy', embeddings)
```

**Revisión del modelo:** seguimos con `BAAI/bge-m3` revision `5617a9f61b028005a4858fdac845db406aefb181` (la del `corpus_manifest.json` actual). No se cambia modelo en este spec.

### 3.6 Corpus manifest actualizado

Se genera nuevo `corpus_manifest.json` con:
- Nuevo timestamp `generated_at`
- Nuevo `checksum_sha256` de cada .npy
- Campo nuevo `source_enriched: true` para marcar la versión
- Se guarda el anterior como `corpus_manifest.baseline_{fecha}.json`

### 3.7 Backups

Antes de escribir los nuevos `.npy`/`.json`:
- Copiar actuales a `database/embeddings/baselines/esco_*_pre_spec_e_{timestamp}.*`
- Ya existen baselines en la carpeta, agregamos los previos a SPEC E para rollback específico.

### 3.8 Ajustes downstream en el pipeline

**Archivos a tocar:**
- `database/skills_implicit_extractor.py`
  - Leer nuevo metadata con `esco_codes_aplicable`
  - Exponer método `extract_skills_by_esco(tareas, esco_code_target)` que filtra embeddings por `esco_codes_aplicable` antes del top-K (aprovecha la precisión nueva)
  - Ajustar umbral default (0.40 → evaluar 0.30-0.35 tras medición)
- `database/match_by_skills.py`
  - Consumir nuevo metadata de ocupaciones con `esco_code`
  - Derivar ISCO desde `esco_code` (primeros 4 dígitos) cuando se requiera compatibilidad
- `database/skill_categorizer.py`
  - Ya usa L1/L2 — verificar compatibilidad con nuevo formato
- `config/embedding_config.py`
  - Actualizar metadata paths si cambian

### 3.9 Retropropagación a BD

- Corrida única de `match_ofertas_v3.py` o equivalente sobre las 49,117 ofertas validadas, reemplazando `skills_semantico_json` con el output nuevo.
- El `estado_validacion` no cambia (no requerimos revalidación humana — el ISCO ya fue validado; cambian las skills enriquecidas).
- Trust metadata (SPEC B v2) se recalcula automáticamente porque es derivada.
- Tiempo estimado: ~60-90 min (BGE-M3 en CPU + persistir JSON). Corrible en background.

---

## 4. Plan por fases

### Fase 1 — Regeneración (~3 h)

1. Script `scripts/embeddings/build_enriched_embeddings.py`:
   - Lee `esco_skills_full.json` + `esco_skill_to_occupations.json`
   - Genera textos enriquecidos
   - Genera embeddings (14,247 skills)
   - Escribe `.npy` + metadata nuevo a `database/embeddings/enriched/` (no sobreescribe aún)
2. Script `scripts/embeddings/build_enriched_occupations.py`:
   - Análogo para las 3,045 ocupaciones
3. Verificaciones:
   - Shape correcto (14247 × 1024 y 3045 × 1024)
   - Norma unitaria (normalize_embeddings=True)
   - Todos los `esco_codes_aplicable` son válidos (presentes en metadata ocupaciones)
   - Checksum SHA-256 calculado

### Fase 2 — A/B test (~2 h)

1. Script `scripts/embeddings/ab_test_embeddings.py`:
   - Toma muestra de 100 ofertas validadas cubriendo 20+ reglas distintas
   - Corre matching con embeddings viejos (baseline) y nuevos (enriched)
   - Reporta por oferta: top-5 skills viejo vs nuevo, scores, Jaccard entre ambos sets
   - Reporta agregados: % skills con diferencia, distribución de scores, ISCOs con cambios dramáticos
2. Sampling manual:
   - 10 ofertas "gold" (casos Cyn + otros conocidos) para evaluación cualitativa
   - Documentar: ¿cuántas skills del top-5 son del dominio correcto?
3. Criterio de promoción:
   - Regresión gold set v2 pasa (47/48 mantenidos)
   - Sobre 10 ofertas gold, ≥80% de skills top-5 son del dominio correcto con embeddings nuevos
   - Ningún caso catastrófico detectado

### Fase 3 — Promoción a producción (~1 h)

1. Backup de embeddings + metadata actuales a `baselines/pre_spec_e_{fecha}.*`
2. Mover `enriched/*` a los paths de producción (sobreescribir)
3. Actualizar `corpus_manifest.json`
4. Sanity check: cargar el extractor y correr 5 ofertas de prueba. Verificar no crashea, no devuelve vacío, scores razonables.
5. Actualizar `.claude/learnings.yaml` y `CLAUDE.md` con nueva versión.

### Fase 4 — Retropropagación (~2-3 h ejecución real, ~1 h desarrollo)

1. Script `scripts/rerun_skills_all_validated.py`:
   - Lista ofertas validadas
   - Por oferta: reconstruye input NLP (titulo_limpio + tareas + skills_tecnicas + soft_skills) → llama a `extract_skills()` → escribe `skills_semantico_json` actualizado
   - Respeta `filtrar_por_trust=False` (no cambia lógica de trust, solo los vectores)
   - Batch de 500 con commit incremental (resumible si falla)
   - Correr en background
2. Post-proceso:
   - Corrida de `backfill_skills_trust.py` (actualiza trust_motivo con los nuevos embeddings)
   - Sync Supabase (incremental) de `skills_semantico_json`
3. Validación:
   - Muestreo 20 ofertas canónicas, comparar skills BD con salida esperada
   - Gold set v2 sigue pasando

---

## 5. Tests

### 5.1 Tests unit (pytest)

**`tests/embeddings/test_enriched_text_builder.py`:**
- Dado skill con todos los campos → texto enriquecido contiene label, L1/L2, broader, ocupaciones, description.
- Skill sin broader → texto omite esa línea sin crashear.
- Skill sin ocupaciones → texto omite esa línea.
- Description > 500 chars → se trunca.
- Unicode/caracteres especiales preservados.

**`tests/embeddings/test_new_metadata_schema.py`:**
- Metadata de skill nueva tiene todos los campos requeridos.
- `esco_codes_aplicable` es lista de strings no vacía para skills con ocupaciones.
- Metadata de ocupación tiene `esco_code` válido (regex `^\d{4}(\.\d+)*$` aprox).
- `isco_4dig` derivado correcto de `esco_code`.

**`tests/embeddings/test_enriched_pipeline_integration.py`:**
- Cargar extractor con nuevos embeddings → procesa 3 ofertas sample sin error.
- Skills devueltas tienen campo `esco_codes_aplicable` disponible vía metadata.
- Top-K para caso Cyn canónico (oferta 7907119232) incluye skills de dominio metalúrgico.

### 5.2 Test de regresión

- `tests/matching/test_gold_set_v2_verified.py`: 47/48 passed debe mantenerse.
- `tests/matching/test_skills_trust.py`: 17 passed.
- Nuevos tests: 3 casos gold (Cyn metalúrgico, Cyn plástico, enfermera buena existente) con assertions sobre dominio.

### 5.3 A/B test cuantitativo

Ver Fase 2. Métricas:
- Jaccard promedio top-5 viejo vs nuevo (esperado: bajo, la mayoría cambia).
- % ofertas con al menos 1 skill "claramente mejor" (evaluación manual sobre 50 casos).
- Regresión en distribución de scores: viejo 0.4-0.9 → nuevo 0.3-0.7 (esperado).

---

## 6. Criterios de éxito

### 6.1 Cualitativos sobre casos canónicos

- **Oferta 7907119232 (operario metalúrgico):** skills top-5 ≥4 del dominio soldadura/montaje/metal (hoy: 0/5).
- **Oferta 9255109063 (operario plástico flex blow):** skills top-5 ≥3 del dominio plástico/moldeo (hoy: 0/5).
- **Oferta 1118173872 (enfermera profesional, control positivo):** skills del dominio sanitario se mantienen o mejoran.

### 6.2 Cuantitativos sobre corpus

- Gold set v2: 47/48 pasa.
- Sobre 100 ofertas random validadas con regla matching aplicada: ≥70% skills del top-5 están en `esco_codes_aplicable` ∋ `esco_code` de la ocupación target (vs ~5% hoy).
- Distribución L1 de skills por ISCO: mejora de coherencia medible (varianza de L1 debería bajar).

### 6.3 Operacionales

- Sin regresión en tiempos: extract_skills mantiene latencia <100 ms por oferta.
- Sync Supabase completo en <90 min.
- Rollback posible en <5 min (restaurar baseline + reiniciar pipeline).

---

## 7. Riesgos y mitigaciones

### 7.1 Embeddings peores para casos hoy aceptables
**Riesgo:** skills actualmente buenas (ofertas de roles donde el label por sí solo era suficiente) podrían empeorar.
**Mitigación:** A/B test Fase 2 detecta esto sobre 100 ofertas. Si se detecta regresión, evaluar texto enriquecido más corto o híbrido.

### 7.2 Descripciones ESCO en español inconsistentes
**Riesgo:** algunas descripciones en `esco_skills_full.json` son muy técnicas o con anglicismos. Podrían introducir ruido semántico diferente al actual.
**Mitigación:** muestrear 50 descripciones y auditar. Si hay casos problemáticos, aplicar limpieza mínima (pasar a lowercase, remover URLs).

### 7.3 Cambio masivo invalida calibraciones downstream
**Riesgo:** thresholds de `skills_implicit_extractor` (0.40 default), reglas de `validation_rules.json` (V24-V30 sobre skills) fueron calibradas contra embeddings viejos.
**Mitigación:** tras Fase 3, re-medir distribución de scores y ajustar thresholds. Nuevos umbrales quedan documentados en el commit.

### 7.4 Dashboard/UI muestra skills muy distintas
**Riesgo:** usuarios del dashboard notan cambio abrupto de skills en sus ofertas.
**Mitigación:** comunicar cambio como "mejora de precisión". La mayoría de usuarios reportaba skills ruidosas — el cambio debería percibirse como mejora.

### 7.5 Skills "huérfanas" (sin ocupaciones ESCO)
**Riesgo:** ~764 skills (5%) no aparecen en `esco_skill_to_occupations.json`. Su texto enriquecido será más pobre.
**Mitigación:** para estas skills, texto enriquecido usa solo label + L1/L2 + description. Aceptable — son casos marginales y la descripción compensa.

### 7.6 Tiempo de retropropagación
**Riesgo:** 49K ofertas × BGE-M3 + escribir JSON a BD de 2GB en /mnt/d puede ser lento (I/O WSL).
**Mitigación:** correr en background, batches de 500 con commits, resumible. Estimado 60-120 min.

---

## 8. Decisiones pendientes

1. **Modelo de embeddings:** seguir con BGE-M3 base o aprovechar el cambio para evaluar LoRA fine-tuned existente en `data/finetuning/matching/model_lora`? Actualmente `skills_implicit_extractor` ya preferiría LoRA si existe (según `CLAUDE.md` no está disponible pero el código lo detecta).
   - **Recomendado:** mantener BGE-M3 base en esta fase. LoRA en spec separado futuro.

2. **Lowercase en texto enriquecido:** ESCO viene mayormente en lowercase pero hay excepciones (acrónimos). 
   - **Recomendado:** preservar mayúsculas/minúsculas originales. BGE-M3 es case-insensitive a nivel de tokenizer.

3. **Largo máximo de texto enriquecido:** BGE-M3 context window es 8192 tokens. Nuestros textos son ~200-1000 chars ≈ 60-300 tokens. No hay problema, pero ¿truncar description a 500 chars sigue teniendo sentido?
   - **Recomendado:** sí, para homogeneizar señal. Evitar que skills con description larga tengan peso desproporcionado.

4. **Persistir `texto_indexado` en metadata?** Útil para debugging y reproducibilidad. Pero agrega peso (~2-5 MB al JSON).
   - **Recomendado:** sí. Facilita auditoría.

5. **Cuándo hacer la retropropagación:**
   - Opción A — todas las 49K ofertas inmediatamente tras Fase 3.
   - Opción B — gradual (10% inicial + monitoreo + resto).
   - **Recomendado:** Opción A. El cambio es global, la gradualidad no aporta (dashboard no compara versiones).

6. **Activar `filtrar_por_trust=True` aprovechando el refactor?**
   - **Recomendado:** NO. Cambio independiente. Mantener default `False` para no confundir causa/efecto.

---

## 9. Cosas que este spec NO hace

- No cambia el modelo (sigue BGE-M3 base).
- No toca el RDF ESCO. Los datos ya están extraídos.
- No curación humana de skills.
- No ampliación de `skills_rules.json`.
- No fine-tuning ni re-entrenamiento.
- No cambios en reglas de matching (`matching_rules_business.json`).
- No cambios en NLP.

---

## 10. Comparación con intentos previos

| Spec | Approach | Estado | Por qué |
|---|---|---|---|
| B original | Threshold dinámico por contexto | ❌ Descartado | Scores no discriminan |
| B v2 | Trust por origen | ✅ Implementado, limitado | No detecta tareas sustantivas mal matcheadas |
| D | Filtro ESCO / coherencia | ❌ Descartado | BGE-M3 no discrimina dominios cercanos con label solo |
| **E (este)** | **Reconstruir embeddings con contexto** | **Propuesto** | **Arregla root cause: los embeddings ignoraban el contexto RDF** |

---

## 11. Anexos

- Fase 0 prototipo: `2026-04-24_E_FASE0_prototipo.md`
- Prototipo código: `scripts/embeddings/prototipo_embeddings_enriquecidos.py`
- Fuentes RDF ya extraídas:
  - `database/embeddings/esco_skills_full.json`
  - `database/embeddings/esco_skill_to_occupations.json`
  - `database/embeddings/esco_occupations_full.json`
- Embeddings actuales (para backup):
  - `database/embeddings/esco_skills_embeddings_full.npy`
  - `database/embeddings/esco_skills_metadata_full.json`
  - `database/embeddings/esco_occupations_embeddings.npy`
  - `database/embeddings/esco_occupations_metadata.json`
- Issues que motivan este spec: `#0cf1bf8d`, `#41571c84` (Cyn 2026-04-24, pendientes).
