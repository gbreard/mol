# Prompt para Claude Code: Corregir NLP según Validación Humana

## Contexto

Se realizó validación humana de las 49 ofertas del Gold Set. El archivo Excel `MOL_Gold_Set_49_Ofertas_Validacion__13-12__.xlsx` documenta los errores encontrados y las reglas de mejora propuestas.

**Objetivo:** Implementar las correcciones identificadas en la validación, siguiendo el mismo patrón de configs JSON que ya usamos para matching.

## Errores Identificados (del Excel - pestaña 06_Resumen_Errores)

| Campo | Correctos | Vacíos | Errores | % Gap | Prioridad |
|-------|-----------|--------|---------|-------|-----------|
| provincia | 31/49 | 16 | 2 | 36.7% | 🔴 ALTA |
| localidad | 25/49 | 22 | 2 | 49% | 🔴 ALTA |
| modalidad | 41/49 | 7 | 1 | 16.3% | 🟡 MEDIA |
| area_funcional | 47/49 | 1 | 1 | 4.1% | 🟢 BAJA |
| nivel_seniority | 43/49 | 6 | 0 | 12.2% | 🟡 MEDIA |
| experiencia_min_anios | 46/49 | 1 | 2 | 6.1% | 🟢 BAJA |

## Errores Críticos Detectados (del Excel)

1. **ID 1118027243**: Campos retornan `TRUE` en lugar de texto (provincia, localidad, modalidad)
2. **ID 1118026729**: provincia = "FALSO\nCapital Federal", localidad = FALSE
3. **ID 1117984105**: experiencia_min = 35 (confundió "edad 35-50 años" con experiencia)
4. **ID 1118023904**: experiencia_min = 20 (confundió "edad 20-45 años" con experiencia)
5. **ID 1118026700**: No lee campos estructurados (ubicación ya venía parseada del scraping)

## Reglas de Mejora (del Excel - pestaña 07_Reglas_Mejora)

### 🔴 Prioridad 1: CAMPOS ESTRUCTURADOS
**Problema:** provincia y localidad vacíos en 36-49% de casos
**Causa:** El NLP no lee el campo `ubicacion` que ya viene del scraping
**Solución:** Parsear columna "Ubicación" con formato "Localidad, Provincia" ANTES de llamar al LLM
**Regex sugerido:** `^(.+),\s*(.+)$`

### 🔴 Prioridad 2: VALORES BOOLEANOS
**Problema:** Algunos campos retornan TRUE/FALSE en lugar de texto
**Causa:** Error en parsing JSON del LLM
**Solución:** Validar tipo de dato. Si es boolean en campo texto → convertir a null

### 🔴 Prioridad 3: EXPERIENCIA vs EDAD
**Problema:** Confunde rangos de edad (35-50 años) con experiencia requerida
**Causa:** Regex extrae cualquier número + "años"
**Solución:** Regex negativo - NO extraer números precedidos de "edad", "años de edad"
**Regex sugerido:** 
- Patrón válido: `(?:experiencia|exp\.?)\s*(?:de\s+)?(?:mínima?\s+)?(?:de\s+)?(\d+)\s*(?:años?|a)`
- Excluir: `edad\s*(?:mínima?)?\s*:?\s*\d+`, `\d+\s*años\s*de\s*edad`

### 🟡 Prioridad 4: MODALIDAD INFERIDA
**Problema:** 16% de ofertas sin modalidad detectada
**Solución:** Inferir del contexto cuando no es explícita
- Si menciona: "comedor en planta", "taller", "sucursal" → presencial
- Si no menciona remoto/híbrido → default presencial

### 🟡 Prioridad 5: SENIORITY INFERIDO  
**Problema:** 12% de ofertas sin nivel de seniority
**Solución:** Inferir de indicadores contextuales
- "sin experiencia", "primer empleo" → trainee
- "experiencia comprobable", "2-4 años" → semisenior
- "gerente", "director", "a cargo de equipo" → manager

### 🟡 Prioridad 6: AREA FUNCIONAL
**Problema:** 4% de ofertas sin área funcional clasificada
**Solución:** Diccionario de palabras clave → categoría
- vendedor|ventas|comercial → Ventas/Comercial
- desarrollador|programador|IT → IT/Sistemas

### 🟢 Prioridad 7-12: DEFAULTS Y NORMALIZACIÓN
- Asignar defaults para campos booleanos (tiene_gente_cargo=0, requiere_movilidad_propia=0)
- Normalizar provincias (CABA → Capital Federal)
- "experiencia comprobable" sin número → experiencia_min=1

## Implementación

### Paso 1: Crear configs JSON para NLP (siguiendo patrón de matching)

Crear en `config/`:

```
config/
├── nlp_preprocessing.json      # Campos estructurados del scraping
├── nlp_inference_rules.json    # Reglas de inferencia (modalidad, seniority, área)
├── nlp_defaults.json           # Valores default
├── nlp_normalization.json      # CABA → Capital Federal
├── nlp_validation.json         # Validación tipos, rangos, rechazo booleans
└── nlp_extraction_patterns.json # Regex experiencia con exclusiones
```

### Paso 2: Crear módulo de postprocesamiento

Crear `database/nlp_postprocessor.py`:
- Clase que carga configs y aplica correcciones
- Flujo: preproceso → LLM → validación → regex → inferencia → normalización → defaults

### Paso 3: Integrar con process_nlp_from_db_v10.py

Modificar el pipeline existente para:
1. Extraer campos estructurados ANTES del LLM
2. Aplicar postprocesamiento DESPUÉS del LLM

### Paso 4: Test con Gold Set

Reprocesar las 49 ofertas y comparar:
- Antes (validación actual del Excel)
- Después (con correcciones)

## Especificación de Configs

### nlp_preprocessing.json

```json
{
  "_version": "1.0",
  "_descripcion": "Campos estructurados del scraping - extraer ANTES del LLM",
  "_origen": "Excel validación - Error ID 1118026700",
  
  "campos_estructurados": {
    "ubicacion": {
      "campo_origen": "ubicacion",
      "separador": ",",
      "campos_destino": ["localidad", "provincia"],
      "orden": ["localidad", "provincia"]
    }
  }
}
```

### nlp_validation.json

```json
{
  "_version": "1.0",
  "_descripcion": "Validación de tipos - corrige errores ID 1118027243, 1118026729",
  
  "rechazo_booleanos": {
    "campos_texto": ["provincia", "localidad", "modalidad", "nivel_seniority", "area_funcional", "titulo_limpio"],
    "accion": "convertir_a_null"
  }
}
```

### nlp_extraction_patterns.json

```json
{
  "_version": "1.0",
  "_descripcion": "Patrones regex - corrige errores ID 1117984105, 1118023904",
  
  "experiencia": {
    "patron_valido": "(?:experiencia|exp\\.?)\\s*(?:de\\s+)?(?:mínima?\\s+)?(?:de\\s+)?(\\d+)\\s*(?:años?|a)",
    "patrones_excluir": [
      "edad\\s*(?:mínima?|máxima?)?\\s*:?\\s*\\d+",
      "\\d+\\s*años\\s*de\\s*edad",
      "entre\\s*\\d+\\s*y\\s*\\d+\\s*años\\s*(?:de\\s*edad)?",
      "mayores?\\s*de\\s*\\d+\\s*años(?!\\s*(?:de\\s+)?experiencia)"
    ],
    "nota": "SIEMPRE verificar exclusiones ANTES de extraer"
  }
}
```

### nlp_inference_rules.json

```json
{
  "_version": "1.0",
  "_descripcion": "Reglas de inferencia cuando LLM no extrae el campo",
  
  "modalidad": {
    "reglas": [
      {"contiene": ["remoto", "home office", "100% remoto"], "resultado": "remoto"},
      {"contiene": ["híbrido", "hibrido", "semi presencial"], "resultado": "hibrido"},
      {"contiene": ["presencial", "en planta", "comedor en planta", "taller", "sucursal"], "resultado": "presencial"}
    ],
    "default": "presencial"
  },
  
  "nivel_seniority": {
    "reglas": [
      {"contiene": ["trainee", "pasante", "primer empleo", "sin experiencia"], "resultado": "trainee"},
      {"contiene": ["junior", "jr"], "resultado": "junior"},
      {"contiene": ["semi senior", "ssr", "experiencia comprobable"], "resultado": "semisenior"},
      {"contiene": ["senior", "sr", "amplia experiencia"], "resultado": "senior"},
      {"contiene": ["gerente", "manager", "director", "jefe de", "a cargo de"], "resultado": "manager"}
    ],
    "inferencia_por_experiencia": {"0": "trainee", "1": "junior", "2-4": "semisenior", "5+": "senior"}
  }
}
```

## Métricas de Éxito (comparar con Excel)

| Campo | Antes (Excel) | Objetivo |
|-------|---------------|----------|
| provincia | 63% (31/49) | >90% |
| localidad | 51% (25/49) | >85% |
| modalidad | 84% (41/49) | >95% |
| experiencia (sin errores edad) | 2 errores | 0 errores |
| nivel_seniority | 88% (43/49) | >95% |

## Output Esperado

1. ✅ 6 archivos JSON en config/ (nlp_*)
2. ✅ database/nlp_postprocessor.py
3. ✅ database/process_nlp_from_db_v10.py modificado
4. ✅ Reporte comparativo antes/después con las 49 ofertas
5. ✅ Los 5 errores críticos del Excel corregidos

## Conexión con Linear

Este trabajo corresponde a:
- **MOL-30**: Gold Set NLP - las correcciones mejoran la calidad base
- **MOL-31**: Test Automático NLP - los tests deben verificar estas correcciones

## Archivos de Referencia

- Excel de validación: `MOL_Gold_Set_49_Ofertas_Validacion__13-12__.xlsx`
- Pipeline actual: `database/process_nlp_from_db_v10.py`
- Patrón a seguir: `config/matching_config.json`, `config/area_funcional_esco_map.json`
