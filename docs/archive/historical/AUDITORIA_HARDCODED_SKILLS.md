# Auditoría: Código Hardcodeado de Skills/Tecnologías

**Fecha:** 2025-12-14
**Objetivo:** Inventario completo antes de crear nuevos diccionarios

---

## Parte 1: Resumen Ejecutivo

| Categoría | Archivos | Items Hardcodeados | Estado |
|-----------|----------|-------------------|--------|
| Regex patterns (skills/oficios) | 3 | ~400+ | 🔴 Crítico |
| Clasificación skills | 2 | ~130 | 🔴 Crítico |
| Normalización valores | 2 | ~80 | 🟡 Parcial (algunos en JSON) |
| Inferencia NLP | 1 | ~100 | 🟢 Ya en JSON |
| Keywords de búsqueda | 5 | ~50 | 🟡 Parcial |

---

## Parte 2: Inventario Detallado por Archivo

### 🔴 CRÍTICO: regex_patterns_v3.py

**Ubicación:** `02.5_nlp_extraction/scripts/patterns/regex_patterns_v3.py`

| Línea | Tipo | Items | Descripción |
|-------|------|-------|-------------|
| 31-55 | ANIOS_EXPERIENCIA | 8 patterns | Regex experiencia |
| 58-73 | EXPERIENCIA_SIN_ANIOS | 5 patterns | Experiencia sin años |
| 76-84 | EXPERIENCIA_IMPLICITA | 7 patterns | Exp. implícita |
| 87-101 | EXPERIENCIA_DESCRIPTIVA | 8 items | Adjetivos → años |
| 104-111 | NIVELES_TITULO | 6 items | trainee/junior/senior |
| 186-217 | NIVELES_EDUCACION | ~25 patterns | Educación |
| 220-243 | PROFESIONES_UNIVERSITARIAS | ~15 patterns | Abogado, Ingeniero... |
| 246-251 | MATRICULA_PATTERNS | 4 patterns | Matrícula profesional |
| 254-287 | ESTADOS_EDUCATIVOS | ~20 patterns | completo/en_curso |
| 371-393 | IDIOMAS | 5 idiomas x ~3 patterns | Inglés, portugués... |
| 396-421 | NIVELES_IDIOMAS | 5 niveles x ~4 patterns | básico/avanzado |
| 424-431 | IMPLICITOS_IDIOMAS | 5 items | bilingual → inglés |
| 489-514 | SOFT_SKILLS_EXPANDED | ~25 items | Soft skills |
| 541-706 | _oficios_patterns | **~170 patterns** | 🔴 MÁS CRÍTICO |

**Total v3:** ~400+ items hardcodeados

---

### 🔴 CRÍTICO: regex_patterns_v4.py

**Ubicación:** `02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py`

| Línea | Tipo | Items | Descripción |
|-------|------|-------|-------------|
| 45-63 | EdadPatterns | 4 patterns | Edad con espacios |
| 103-122 | LicenciaPatterns | 4 patterns | Licencia conducir |
| 156-163 | PATRONES_INMEDIATA | 7 patterns | Contratación inmediata |
| 179-185 | IndexacionPatterns | 6 patterns | IPC, paritarias |

**Hereda todo de v3** (~400+ items)

---

### 🔴 CRÍTICO: clasificar_skills_esco.py

**Ubicación:** `database/clasificar_skills_esco.py`

| Línea | Tipo | Items | Descripción |
|-------|------|-------|-------------|
| 47-62 | VERBOS_COMPETENCY | ~60 verbos | gestionar, realizar... |
| 65-78 | KEYWORDS_KNOWLEDGE | ~70 keywords | anatomía, legislación... |

**Total:** ~130 items

---

### 🔴 CRÍTICO: esco_skills_extractor.py

**Ubicación:** `database/esco_skills_extractor.py`

| Línea | Tipo | Items | Descripción |
|-------|------|-------|-------------|
| 49-73 | KNOWLEDGE_PATTERNS | ~18 patterns | Detecta knowledge |
| 76-89 | SKILL_PATTERNS | ~12 patterns | Detecta skills (acción) |

**Total:** ~30 patterns

---

### 🟡 PARCIAL: normalize_nlp_values.py

**Ubicación:** `database/normalize_nlp_values.py`

| Línea | Tipo | Items | Descripción |
|-------|------|-------|-------------|
| 27-41 | modalidad | 11 mapeos | hibrido, remoto... |
| 42-58 | nivel_seniority | 16 mapeos | junior, senior... |
| 59-93 | area_funcional | ~35 mapeos | IT, Ventas... |
| 94-101 | tipo_oferta | 6 mapeos | demanda_real... |
| 102-114 | jornada_laboral | 12 mapeos | full_time... |

**Total:** ~80 mapeos
**Nota:** Algunos YA están en `config/nlp_normalization.json`

---

### 🟢 YA EXTERNALIZADO: nlp_inference_rules.json

**Ubicación:** `config/nlp_inference_rules.json`

| Campo | Items | Estado |
|-------|-------|--------|
| modalidad.reglas | 5 reglas x ~5 keywords | ✅ En JSON |
| nivel_seniority.reglas | 5 reglas x ~7 keywords | ✅ En JSON |
| area_funcional.diccionario_keywords | 10 áreas x ~6 keywords | ✅ En JSON |

---

### 🟡 PARCIAL: Keywords de búsqueda (scrapers)

| Archivo | Items | Descripción |
|---------|-------|-------------|
| `01_sources/bumeran/scrapers/bumeran_explorer.py:103` | ~10 | Keywords búsqueda |
| `01_sources/zonajobs/scrapers/zonajobs_playwright_scraper.py:451` | 3 | Keywords test |
| `01_sources/computrabajo/scrapers/computrabajo_explorer.py:102` | ~10 | Keywords búsqueda |

---

## Parte 3: JSONs Existentes en config/

| Archivo | Propósito | Skills/Tech? |
|---------|-----------|--------------|
| `area_funcional_esco_map.json` | Mapeo área → ISCO | ❌ No |
| `matching_config.json` | Config matching v2 | ❌ No |
| `matching_rules.json` | Reglas matching | ❌ No |
| `niveles_jerarquicos.json` | Niveles jerárquicos | ❌ No |
| `nivel_seniority_esco_map.json` | Seniority → ISCO | ❌ No |
| `nlp_defaults.json` | Defaults NLP | ❌ No |
| `nlp_extraction_patterns.json` | Regex experiencia | ⚠️ Solo experiencia |
| `nlp_inference_rules.json` | Inferencia campos | ⚠️ Keywords modalidad/seniority |
| `nlp_normalization.json` | Normalización | ⚠️ Parcial |
| `nlp_preprocessing.json` | Preproceso | ❌ No |
| `nlp_validation.json` | Validación | ❌ No |
| `normalizacion_boost.json` | Boost matching | ❌ No |
| `sector_isco_compatibilidad.json` | Sector ↔ ISCO | ❌ No |

**JSON de Skills existente (fuera de config/):**
- `02.5_nlp_extraction/config/skills_database.json` - 215 skills técnicas IT

---

## Parte 4: Tabla Resumen - Migración Necesaria

| Archivo | Tipo | Items | ¿Migrar? | JSON Destino Sugerido |
|---------|------|-------|----------|----------------------|
| regex_patterns_v3.py | EXPERIENCIA_* | ~28 | Sí | `config/nlp_extraction_patterns.json` (expandir) |
| regex_patterns_v3.py | NIVELES_TITULO | 6 | Sí | `config/nlp_inference_rules.json` (expandir) |
| regex_patterns_v3.py | NIVELES_EDUCACION | ~25 | Sí | `config/nlp_education_patterns.json` (crear) |
| regex_patterns_v3.py | PROFESIONES_UNIV | ~15 | Sí | `config/nlp_education_patterns.json` |
| regex_patterns_v3.py | IDIOMAS + NIVELES | ~35 | Sí | `config/nlp_idiomas_patterns.json` (crear) |
| regex_patterns_v3.py | SOFT_SKILLS | ~25 | Sí | `config/skills_database.json` (mover a config/) |
| regex_patterns_v3.py | **_oficios_patterns** | **~170** | **Sí** | `config/oficios_arg.json` (crear) |
| regex_patterns_v4.py | EdadPatterns | 4 | Sí | `config/nlp_extraction_patterns.json` |
| regex_patterns_v4.py | Licencia/Inmediata | ~11 | Sí | `config/nlp_extraction_patterns.json` |
| clasificar_skills_esco.py | VERBOS_COMPETENCY | ~60 | Sí | `config/esco_classification.json` (crear) |
| clasificar_skills_esco.py | KEYWORDS_KNOWLEDGE | ~70 | Sí | `config/esco_classification.json` |
| esco_skills_extractor.py | KNOWLEDGE/SKILL_PATTERNS | ~30 | Sí | `config/esco_classification.json` |
| normalize_nlp_values.py | NORMALIZACIONES | ~80 | Parcial | Ya parcial en `nlp_normalization.json` |
| skills_database.json | skills técnicas | 215 | Mover | `config/skills_database.json` |

---

## Parte 5: Plan de Migración Priorizado

### Prioridad 1: ALTA (afecta matching y extracción)

1. **Crear `config/oficios_arg.json`** (~170 items)
   - Mover `_oficios_patterns` de regex_patterns_v3.py
   - Estructura: `{"oficios": [{"pattern": "...", "categoria": "...", "esco_hint": "..."}]}`
   - Impacto: Mejora matching de ofertas operativas

2. **Mover `skills_database.json` a `config/`** (215 items)
   - Ya existe, solo mover ubicación
   - Actualizar imports en regex_patterns_v*.py

3. **Crear `config/esco_classification.json`** (~160 items)
   - Unificar VERBOS_COMPETENCY + KEYWORDS_KNOWLEDGE
   - Usado por clasificar_skills_esco.py y esco_skills_extractor.py

### Prioridad 2: MEDIA (mejora NLP)

4. **Expandir `config/nlp_extraction_patterns.json`**
   - Agregar: edad, licencia, contratación inmediata
   - Ya tiene experiencia

5. **Crear `config/nlp_education_patterns.json`** (~40 items)
   - NIVELES_EDUCACION + PROFESIONES_UNIVERSITARIAS + MATRICULA

6. **Crear `config/nlp_idiomas_patterns.json`** (~35 items)
   - IDIOMAS + NIVELES + IMPLICITOS

### Prioridad 3: BAJA (ya funciona)

7. **Completar `config/nlp_normalization.json`**
   - Sincronizar con normalize_nlp_values.py

---

## Parte 6: Estimación de Trabajo

| Tarea | Archivos | Items | Esfuerzo |
|-------|----------|-------|----------|
| Crear oficios_arg.json | 1 | 170 | 2-3 horas |
| Mover skills_database.json | 2 | 215 | 30 min |
| Crear esco_classification.json | 3 | 160 | 2 horas |
| Expandir nlp_extraction_patterns | 2 | 25 | 1 hora |
| Crear nlp_education_patterns | 2 | 40 | 1 hora |
| Crear nlp_idiomas_patterns | 2 | 35 | 1 hora |
| Sincronizar normalize | 2 | 80 | 1 hora |

**Total estimado:** 8-10 horas

---

## Anexo: Archivos Completos con Hardcoded

```
02.5_nlp_extraction/scripts/patterns/regex_patterns_v3.py   [~400 items] 🔴
02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py   [hereda v3]  🔴
02.5_nlp_extraction/scripts/patterns/regex_patterns_v2.py   [obsoleto]
02.5_nlp_extraction/scripts/patterns/regex_patterns.py      [obsoleto]
database/clasificar_skills_esco.py                          [~130 items] 🔴
database/esco_skills_extractor.py                           [~30 items]  🔴
database/normalize_nlp_values.py                            [~80 items]  🟡
02.5_nlp_extraction/config/skills_database.json             [215 items]  🟡
config/nlp_inference_rules.json                             [~100 items] 🟢
```

---

**Conclusión:** Hay ~700+ items hardcodeados que deberían externalizarse a JSON. La prioridad es `oficios_arg.json` (170 items) porque afecta directamente el matching de ofertas operativas/técnicas.
