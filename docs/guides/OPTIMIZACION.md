# Flujos de Optimización (Gold Set)

**REGLA PRINCIPAL:** Los pipelines principales (`process_nlp_from_db_v11.py`, `match_ofertas_v3.py`)
NO se tocan hasta tener las optimizaciones validadas con Gold Set.

---

## Pipeline de Validación Autónomo (v1.0)

**Principio:** El sistema valida ofertas automáticamente. Claude solo analiza PATRONES agrupados, no casos individuales.

### Arquitectura

```
LLM procesa oferta
        │
        ▼
┌──────────────────────────────────────┐
│  CAPA 1: AUTO-EVALUACIÓN             │
│  config/validation_rules.json        │
│  (10 reglas de validación)           │
└──────────────────────────────────────┘
        │
        ├── PASA ────► estado = validado (automático)
        │
        └── FALLA ───► CAPA 2: AUTO-DIAGNÓSTICO
                              │
                       config/diagnostic_patterns.json
                              │
                              ▼
                       CAPA 3: AUTO-CORRECCIÓN
                              │
                       config/auto_correction_map.json
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               Auto-corregible     No auto-corregible
                    │                   │
                    ▼                   ▼
               Corregir y          Agrupar errores
               validar              similares
                                        │
                                        ▼
                                 CAPA 4: CLAUDE
                                 (patrones agrupados)
                                        │
                                        ▼
                                 Claude propone
                                 regla en JSON
                                        │
                                        ▼
                                 Reprocesar
```

### Comandos del Sistema

```bash
# Validar ofertas (detecta errores según reglas)
python database/auto_validator.py --limit 100

# Validar + aplicar correcciones automáticas
python database/auto_corrector.py --limit 100

# Analizar patrones para Claude (errores agrupados)
python scripts/analyze_error_patterns.py --validar-primero --limit 100

# Ver patrones desde archivo existente
python scripts/analyze_error_patterns.py --desde-archivo metrics/cola_claude_*.json
```

### Configs del Sistema

| Archivo | Propósito | Reglas |
|---------|-----------|--------|
| `config/validation_rules.json` | Reglas de auto-evaluación | 10 |
| `config/diagnostic_patterns.json` | Patrones de diagnóstico | 13 |
| `config/auto_correction_map.json` | Mapeo diagnóstico → acción | 11 |

### Tipos de Corrección

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `auto_corregir` | Corrección automática sin cambiar configs | Paraguay → "Paraguay (exterior)" |
| `aplicar_config` | Buscar regla existente y reprocesar | Usar regex de limpieza existente |
| `escalar_claude` | Agrupar y presentar a Claude | Crear nueva regla de matching |

### Flujo de Trabajo

1. **Procesar ofertas** con pipeline existente
2. **Validar** con `auto_validator.py`
3. **Corregir** automáticamente lo posible con `auto_corrector.py`
4. **Analizar patrones** con `analyze_error_patterns.py`
5. **Claude crea reglas** en `config/*.json` para errores agrupados
6. **Reprocesar** ofertas afectadas
7. **Repetir** hasta sin errores

---

## Guía Rápida: Mapeo Error → Config

### Errores NLP

| Tipo de Error | Config a Editar | Sección |
|---------------|-----------------|---------|
| Provincia/Localidad mal parseada | `config/nlp_preprocessing.json` | `campos_estructurados.ubicacion` |
| Seniority incorrecto | `config/nlp_inference_rules.json` | `nivel_seniority.reglas` |
| Modalidad incorrecta | `config/nlp_inference_rules.json` | `modalidad.reglas` |
| Área funcional incorrecta | `config/nlp_inference_rules.json` | `area_funcional.reglas` |
| Sector empresa incorrecto | `config/nlp_inference_rules.json` | `correccion_sector.reglas` |
| Experiencia mal extraída | `config/nlp_extraction_patterns.json` | `experiencia.patterns` |
| Valor booleano como texto | `config/nlp_validation.json` | `rechazo_valores` |
| Normalización (CABA, etc) | `config/nlp_normalization.json` | `provincia` o `modalidad` |

### Errores Matching

| Tipo de Error | Config a Editar | Ejemplo |
|---------------|-----------------|---------|
| ISCO incorrecto para título X | `config/matching_rules_business.json` | `titulo_contiene → forzar_isco` |
| Skills mal matcheadas | `config/matching_rules_business.json` | Bypass por skills |

### Errores Skills

| Tipo de Error | Config a Editar |
|---------------|-----------------|
| Skill mal categorizada | `config/esco_skills_taxonomy.json` |
| Categoría L1/L2 incorrecta | `config/skill_categories.json` |

## Flujo de Corrección de Errores

```
1. Detectar error (Excel/revisión manual)
        ↓
2. Clasificar: ¿NLP? ¿Matching? ¿Skills?
        ↓
3. Buscar en tabla → editar JSON correcto
        ↓
4. Reprocesar Gold Set:
   - NLP: python database/process_nlp_from_db_v11.py --ids <IDS>
   - Matching: pytest tests/matching/test_gold_set_manual.py -v
        ↓
5. Verificar que el error se corrigió
        ↓
6. Commit: git add config/*.json && git commit -m "fix: corregir X"
```

---

## 1. Optimización NLP

**Pipeline Principal (NO TOCAR):** `database/process_nlp_from_db_v11.py`

**Componentes que SÍ se modifican:**

| Archivo | Qué hace |
|---------|----------|
| `database/nlp_postprocessor.py` | Aplica reglas de config/ |
| `database/limpiar_titulos.py` | Limpia títulos |
| `config/nlp_preprocessing.json` | Parsing ubicación |
| `config/nlp_inference_rules.json` | Inferencia área/seniority/modalidad |
| `config/nlp_validation.json` | Validación tipos |
| `config/nlp_extraction_patterns.json` | Regex experiencia |

**Scripts de optimización (`scripts/nlp/gold_set/`):**

| Script | Qué hace |
|--------|----------|
| `expandir_gold_set_nlp.py` | Selecciona ofertas nuevas para Gold Set |
| `completar_nlp_gold_set_100.py` | Completa campos NLP vacíos |
| `reprocesar_gold_set_nlp.py` | Reprocesa con nuevas reglas |
| `export_gold_set_*.py` | Exporta Excel para validación manual |

**Flujo:**
```
1. Modificar config/nlp_*.json
        ↓
2. Ejecutar scripts/nlp/gold_set/*.py
        ↓
3. Revisar Excel, detectar errores
        ↓
4. Corregir config/nlp_*.json
        ↓
5. Repetir hasta métricas OK
        ↓
6. Aplicar al pipeline principal
```

---

## 2. Optimización Matching

**Pipeline Principal (NO TOCAR):** `database/match_ofertas_v3.py`

**Componentes que SÍ se modifican:**

| Archivo | Qué hace |
|---------|----------|
| `database/match_by_skills.py` | Matching por skills |
| `config/matching_config.json` | Pesos y umbrales |
| `config/matching_rules_business.json` | 52 reglas de negocio |
| `config/area_funcional_esco_map.json` | Mapeo área → ISCO |
| `config/nivel_seniority_esco_map.json` | Mapeo seniority → ISCO |

**Scripts de optimización:**

| Script | Ubicación |
|--------|-----------|
| `test_gold_set_manual.py` | `tests/matching/` |
| `analyze_gold_set_errors.py` | `scripts/matching/gold_set/` |
| `run_matching_gold_set_100.py` | `scripts/matching/gold_set/` |

**Gold Set:** `database/gold_set_manual_v2.json` (49 casos)

**Flujo:**
```
1. Modificar config/matching_*.json
        ↓
2. Ejecutar pytest tests/matching/test_gold_set_manual.py -v
        ↓
3. Analizar errores
        ↓
4. Agregar reglas a matching_rules_business.json
        ↓
5. Repetir hasta 100% Gold Set
        ↓
6. Expandir Gold Set y repetir
```

---

## 3. Optimización Skills

**Pipeline Principal (NO TOCAR):**
- `database/skills_implicit_extractor.py`
- `database/skill_categorizer.py`

**Componentes que SÍ se modifican:**

| Archivo | Qué hace |
|---------|----------|
| `config/skills_database.json` | ~320 skills por categoría |
| `config/skill_categories.json` | Categorías L1/L2 |

**Scripts de optimización:**

| Script | Qué hace |
|--------|----------|
| `scripts/test_skills_extraction.py` | Prueba extracción |
| `scripts/test_skill_categorizer.py` | Prueba categorización |

**Flujo:**
```
1. Agregar skills a config/skills_database.json
        ↓
2. Ejecutar scripts/test_skills_extraction.py
        ↓
3. Verificar cobertura y precisión
        ↓
4. Ajustar categorías en config/skill_categories.json
        ↓
5. Repetir hasta cobertura OK
```

---

## Carpetas de Scripts de Optimización

```
scripts/
├── nlp/
│   └── gold_set/              ← Scripts optimización NLP
│
└── matching/
    └── gold_set/              ← Scripts optimización Matching

tests/
├── nlp/                       ← Tests NLP (pytest)
│   ├── test_extraction.py
│   └── test_postprocessor_gold_set.py
│
└── matching/                  ← Tests Matching (pytest)
    ├── test_gold_set_manual.py
    └── test_precision.py
```
