# Diagnóstico: ¿Por qué skills_database.json no se usa en la extracción?

**Fecha:** 2025-12-14
**Estado:** CONFIRMADO - El diccionario existe pero NO se usa para extraer skills

---

## Resumen Ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Existe el diccionario? | **SÍ** - `02.5_nlp_extraction/config/skills_database.json` (215 skills IT) |
| ¿Existe código para usarlo? | **SÍ** - `SkillsPatterns.extract_technical_skills()` en regex_patterns_v3.py |
| ¿Se ejecuta ese código? | **NO** - `extract_all()` en v4 NUNCA llama a SkillsPatterns |
| ¿El LLM usa el diccionario? | **NO** - El prompt v10 NO recibe lista de skills válidas |

**Conclusión:** El diccionario está "huérfano" - existe el código pero nunca se ejecuta.

---

## Parte 1: Inventario de Componentes

### 1.1 El Diccionario (skills_database.json)

**Ubicación:** `02.5_nlp_extraction/config/skills_database.json`

```json
{
  "categorias": {
    "lenguajes_programacion": {"skills": ["python", "javascript", "typescript", ...]},  // 27 items
    "frameworks_web": {"skills": ["react", "vue", "angular", "django", ...]},          // 24 items
    "cloud_devops": {"skills": ["aws", "azure", "docker", "kubernetes", ...]},         // 28 items
    ...
  },
  "soft_skills_expanded": {...}
}
```

**Total:** 215 skills técnicas + 60 soft skills = **275 items**

### 1.2 La Clase SkillsPatterns (regex_patterns_v3.py)

**Ubicación:** `02.5_nlp_extraction/scripts/patterns/regex_patterns_v3.py:480-763`

```python
class SkillsPatterns:
    @classmethod
    def _load_skills_database(cls):
        """Carga skills_database.json y construye patterns"""
        skills_file = config_dir / "skills_database.json"
        cls._skills_db = json.load(f)
        # Construye regex patterns para cada skill

    @classmethod
    def extract_technical_skills(cls, text: str) -> List[str]:
        """Extrae skills técnicas usando el diccionario"""
        # Busca matches de cada skill en el texto

    @classmethod
    def extract_soft_skills(cls, text: str) -> List[str]:
        """Extrae soft skills usando el diccionario"""
```

**Estado:** Código completo y funcional, pero **NUNCA INVOCADO**.

### 1.3 La Función extract_all() (regex_patterns_v4.py)

**Ubicación:** `02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py:632-756`

```python
from regex_patterns_v3 import (
    ExperienciaPatterns,
    EducacionPatterns,
    IdiomasPatterns,
    SkillsPatterns,  # <-- IMPORTA pero NO USA
    SalarioPatterns,
    JornadaPatterns
)

def extract_all(texto: str, titulo: str = "", empresa: str = "") -> Dict[str, Any]:
    # 1. Header
    header = HeaderPatterns.extraer_encabezado(texto)

    # 2. Experiencia (v3)  ✅ USA
    exp_min, exp_max = ExperienciaPatterns.extract_years(texto_completo)

    # 3. Educación (v3)  ✅ USA
    nivel_edu = EducacionPatterns.extract_nivel(texto_completo)

    # 4. Idiomas (v3)  ✅ USA
    idiomas = IdiomasPatterns.extract_idiomas(texto_completo)

    # 5. Salario (v3)  ✅ USA
    salario_min, salario_max, moneda = SalarioPatterns.extract_montos(texto_completo)

    # 6. Jornada (v3)  ✅ USA
    jornada = JornadaPatterns.extract_tipo(texto_completo)

    # ... más extracciones v4 ...

    # ❌ NUNCA LLAMA:
    # - SkillsPatterns.extract_technical_skills()
    # - SkillsPatterns.extract_soft_skills()

    return {...}  # No incluye skills_tecnicas ni tecnologias
```

### 1.4 El Prompt LLM v10 (extraction_prompt_v10.py)

**Ubicación:** `02.5_nlp_extraction/prompts/extraction_prompt_v10.py:93-100`

```python
"skills": {{
    "skills_tecnicas_list": [],      # LLM extrae LIBRE
    "soft_skills_list": [],          # SIN diccionario
    "tecnologias_list": [],          # SIN validación
    ...
}}
```

**Instrucciones al LLM (línea 234):**
```
- **skills_tecnicas_list**: Skills tecnicas EXPLICITAS. Ej: "Excel", "SAP", "Python"
- **tecnologias_list**: Tecnologias (IT). Ej: "Docker", "AWS", "React"
```

**Problema:** El LLM NO recibe la lista de 215 skills válidas. Extrae "libremente".

---

## Parte 2: Flujo Actual vs Esperado

### Flujo ACTUAL (roto)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ OFERTA TEXTO                                                                │
│ "Buscamos desarrollador Python con React y AWS..."                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 0: regex_patterns_v4.extract_all()                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ Extrae: experiencia, educacion, idiomas, salario, jornada, edad, licencia│
│ ❌ NO extrae: skills_tecnicas, tecnologias, soft_skills                     │
│                                                                             │
│ ⚠️  SkillsPatterns importado pero NUNCA LLAMADO                             │
│ ⚠️  skills_database.json EXISTE pero NO SE USA                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: LLM (Qwen2.5:14b) con prompt v10                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input: texto oferta (SIN pre-extracción de skills)                          │
│ Prompt: "Extrae skills_tecnicas_list, tecnologias_list..."                  │
│                                                                             │
│ ⚠️  NO recibe diccionario de skills válidas                                 │
│ ⚠️  Extrae LIBREMENTE lo que interpreta                                     │
│ ⚠️  Puede inventar/omitir skills                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: skills_tecnicas_list = ??? (inconsistente)                          │
│         tecnologias_list = ??? (puede faltar python, react, aws)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flujo ESPERADO (corregido)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ OFERTA TEXTO                                                                │
│ "Buscamos desarrollador Python con React y AWS..."                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 0: regex_patterns_v4.extract_all() [MODIFICADO]                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ Extrae: experiencia, educacion, idiomas, salario...                      │
│ ✅ NUEVO: SkillsPatterns.extract_technical_skills(texto)                    │
│           → ["python", "react", "aws"]                                      │
│ ✅ NUEVO: SkillsPatterns.extract_soft_skills(texto)                         │
│           → ["trabajo en equipo", "proactivo"]                              │
│                                                                             │
│ ✅ skills_database.json USADO para extraer 215 skills conocidas             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: LLM (Qwen2.5:14b) con prompt v10 [OPCIONAL: VALIDACIÓN]             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input: texto oferta + skills_pre_extraidas = ["python", "react", "aws"]     │
│ Prompt: "Valida estas skills y agrega otras que veas..."                    │
│                                                                             │
│ ✅ Recibe pre-extracción de Capa 0                                          │
│ ✅ Solo VALIDA/EXPANDE (no empieza de cero)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: skills_tecnicas_list = ["Python", "React", "AWS"]                   │
│         tecnologias_list = ["Python", "React", "AWS"]                       │
│         (100% cobertura para skills conocidas)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Parte 3: El Gap Identificado

### Ubicación exacta del gap

| Archivo | Línea | Problema |
|---------|-------|----------|
| `regex_patterns_v4.py` | 27-34 | Importa SkillsPatterns pero no lo usa |
| `regex_patterns_v4.py` | 632-756 | `extract_all()` no llama a extract_technical_skills() |
| `extraction_prompt_v10.py` | 234-239 | Define campos pero no pasa diccionario |
| `process_nlp_from_db_v10.py` | N/A | No tiene referencia a SkillsPatterns |

### Por qué pasó esto

1. **SkillsPatterns fue creado** en v3 como código funcional
2. **v4 se creó encima** de v3 para agregar EdadPatterns, LicenciaPatterns, etc.
3. **Alguien olvidó** agregar la llamada a SkillsPatterns en `extract_all()`
4. **El prompt v10** asume que el LLM extraerá skills (pero sin guía)
5. **Nunca se testeó** que las skills del diccionario se extrajeran

---

## Parte 4: Solución Propuesta

### Opción A: Activar Capa 0 (Recomendada)

**Cambio en `regex_patterns_v4.py`:**

```python
def extract_all(texto: str, titulo: str = "", empresa: str = "") -> Dict[str, Any]:
    texto_completo = f"{titulo}\n{texto}"

    # ... código existente ...

    # NUEVO: Extraer skills usando diccionario
    skills_tecnicas = SkillsPatterns.extract_technical_skills(texto_completo)
    soft_skills = SkillsPatterns.extract_soft_skills(texto_completo)

    return {
        # ... campos existentes ...

        # NUEVO: Skills pre-extraídas
        "skills_tecnicas_pre": skills_tecnicas,
        "soft_skills_pre": soft_skills,
    }
```

**Ventajas:**
- Rápido (regex)
- Determinístico
- 100% precisión para skills conocidas
- No aumenta costo de LLM

### Opción B: Inyectar diccionario en prompt LLM

**Cambio en `extraction_prompt_v10.py`:**

```python
EXTRACTION_PROMPT_V10 = """...

## DICCIONARIO DE SKILLS VÁLIDAS

Usa esta lista como referencia para normalizar skills:

**Lenguajes:** python, javascript, typescript, java, c#, go, rust, php, ruby, scala, kotlin, swift...
**Frameworks:** react, vue, angular, django, flask, spring, .net, rails, laravel, express...
**Cloud/DevOps:** aws, azure, gcp, docker, kubernetes, terraform, ansible, jenkins, gitlab-ci...
...

Si encuentras una skill en el texto que coincide con esta lista, ÚSALA tal cual está escrita aquí.

..."""
```

**Desventajas:**
- Aumenta tokens del prompt
- LLM puede ignorarlo
- Más lento

### Opción C: Híbrido (Mejor opción)

1. **Capa 0:** Extraer skills conocidas con regex (rápido, 100% precisión)
2. **Capa 1:** LLM valida y agrega skills NO conocidas
3. **Postproceso:** Normalizar todo contra diccionario

---

## Parte 5: Plan de Implementación

### Paso 1: Modificar extract_all() (30 min)

```python
# En regex_patterns_v4.py, agregar al final de extract_all():

    # 15. Skills técnicas (v3) - ACTIVAR
    skills_tecnicas = SkillsPatterns.extract_technical_skills(texto_completo)
    soft_skills = SkillsPatterns.extract_soft_skills(texto_completo)

    return {
        # ... campos existentes ...
        "skills_tecnicas_pre": skills_tecnicas,
        "soft_skills_pre": soft_skills,
    }
```

### Paso 2: Integrar en process_nlp_from_db_v10.py (30 min)

```python
# Usar skills pre-extraídas de Capa 0
resultado_regex = extract_all(descripcion, titulo, empresa)
skills_pre = resultado_regex.get("skills_tecnicas_pre", [])

# Pasar a postprocesador para merge con resultado LLM
```

### Paso 3: Testear con Gold Set (1 hora)

```bash
python database/test_gold_set_v211.py --verbose
# Verificar que ahora extrae python, react, aws, etc.
```

### Paso 4: Expandir diccionario (2 horas)

- Agregar skills LATAM (MercadoLibre, Rappi, AFIP...)
- Agregar skills logística (picking, WMS...)
- Agregar skills contables (AFIP, liquidación, Tango...)

---

## Anexo: Archivos Involucrados

| Archivo | Rol | Necesita cambio |
|---------|-----|-----------------|
| `02.5_nlp_extraction/config/skills_database.json` | Diccionario | ⚠️ Expandir |
| `02.5_nlp_extraction/scripts/patterns/regex_patterns_v3.py` | SkillsPatterns | ✅ OK |
| `02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py` | extract_all() | ⚠️ Activar llamada |
| `02.5_nlp_extraction/prompts/extraction_prompt_v10.py` | Prompt LLM | 🔄 Opcional |
| `database/process_nlp_from_db_v10.py` | Pipeline | ⚠️ Integrar |
| `database/nlp_postprocessor.py` | Postproceso | ⚠️ Merge skills |

---

**Conclusión:** El problema es que `extract_all()` importa pero NO LLAMA a `SkillsPatterns`.
El fix es agregar 2 líneas de código + integrar en el pipeline.

Esfuerzo estimado: **2-3 horas**
