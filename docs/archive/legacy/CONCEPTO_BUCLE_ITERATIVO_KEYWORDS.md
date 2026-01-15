# BUCLE ITERATIVO: KEYWORDS ↔ SCRAPING ↔ NLP

**Fecha:** 2025-10-31
**Estado:** CONCEPTO FUNDAMENTAL DEL PROYECTO
**Importante:** Este documento explica el motor de mejora continua del sistema

---

## CONCEPTO CLAVE

**El NLP NO es solo para analizar ofertas. Es el MOTOR que alimenta el bucle de mejora del scraping.**

```
┌─────────────────────────────────────────────────────────────────┐
│                   BUCLE DE RETROALIMENTACIÓN                    │
│                                                                 │
│   Keywords → Scraping → Ofertas → NLP → Nuevos Keywords → ...  │
│      ↑                                                     │     │
│      └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## EL PROBLEMA ORIGINAL

**Estado inicial:**
- Bumeran tiene ~12,000 ofertas laborales activas
- Con 56 keywords solo capturábamos ~1,500 ofertas (12.5%)
- **Brecha:** 10,500 ofertas NO capturadas (87.5%)

**¿Por qué?**
- Las ofertas usan términos/skills que NO están en nuestro diccionario
- Ejemplos de términos faltantes:
  - "Técnico en HVAC"
  - "Scrum Master"
  - "Especialista en SAP FICO"
  - "Operador de grúa torre"
  - "Desarrollador Salesforce Marketing Cloud"

---

## LA SOLUCIÓN: BUCLE ITERATIVO

### Iteración 1: Bootstrap inicial

```
Input:  56 keywords (manuales)
        ↓
Scraping: Bumeran
        ↓
Output: ~1,500 ofertas (12.5% cobertura)
        ↓
NLP:    Extraer skills de esas 1,500 ofertas
        ↓
Resultado: 144 nuevos términos encontrados
```

**Diccionario v2:** 56 + 144 = 200 keywords

---

### Iteración 2: Primera expansión

```
Input:  200 keywords
        ↓
Scraping: Bumeran
        ↓
Output: ~3,000 ofertas (25% cobertura)
        ↓
NLP:    Extraer skills de 3,000 ofertas
        ↓
Resultado: 637 nuevos términos
```

**Diccionario v3:** 200 + 637 = 837 keywords

---

### Iteración 3: Expansión acelerada

```
Input:  837 keywords
        ↓
Scraping: Bumeran
        ↓
Output: ~4,200 ofertas (35% cobertura)
        ↓
NLP:    Extraer skills de 4,200 ofertas
        ↓
Resultado: 163 nuevos términos
```

**Diccionario v3.1:** 837 + 163 = 1,000 keywords

---

### Iteración 4: Refinamiento v3.2

```
Input:  1,000 keywords + refinamiento
        ↓
Scraping: Bumeran
        ↓
Output: ~4,800 ofertas (40% cobertura)
        ↓
NLP Fase 1 (Regex): Extraer skills básicos
        ↓
Resultado: 148 nuevos términos + variaciones
```

**Diccionario v3.2:** 1,000 + 148 = 1,148 keywords

---

### Iteración 5: ACTUAL (v3.2 → v4.0)

```
Input:  1,148 keywords (ACTUAL)
        ↓
Scraping: Bumeran (automatizado Lun/Jue)
        ↓
Output: 5,479 ofertas (45.6% cobertura) ✅ COMPLETADO
        ↓
NLP Fase 2 (NER): ⏳ 55% COMPLETADO
        ├── Scripts listos (1,880 líneas) ✅
        ├── 500 ofertas seleccionadas ✅
        ├── Anotación manual PENDIENTE (8-16h)
        ├── Entrenamiento modelo PENDIENTE (~1h)
        └── Procesamiento 5,479 ofertas PENDIENTE (~20min)
        ↓
Resultado esperado: 350-500 nuevos términos (estimado)
```

**Diccionario v4.0 (proyectado):** 1,148 + 400 = 1,500-1,600 keywords

---

### Iteración 6: Objetivo final (v4.0 → v5.0)

```
Input:  1,500+ keywords
        ↓
Scraping: Bumeran
        ↓
Output ESPERADO: 8,000-10,000 ofertas (67-83% cobertura)
        ↓
Brecha restante: 2,000-4,000 ofertas
```

**Meta:** Capturar 67-83% de ofertas disponibles en Bumeran

---

## DOBLE PROPÓSITO DEL NLP

El procesamiento NLP tiene **DOS USOS SIMULTÁNEOS:**

### 1. AMPLIAR KEYWORDS (Bucle de mejora)

```python
# Ejemplo: Procesar ofertas con NER
ofertas_procesadas = nlp_ner.procesar_ofertas(5479)

# Extraer skills únicos
skills_extraidos = set()
for oferta in ofertas_procesadas:
    skills_extraidos.update(oferta['skills_tecnicas'])
    skills_extraidos.update(oferta['ocupacion_principal'])

# Filtrar nuevos términos
diccionario_actual = cargar_diccionario_v3_2()  # 1,148 keywords
nuevos_keywords = [
    skill for skill in skills_extraidos
    if skill not in diccionario_actual
]

# Resultado: 400 nuevos keywords
print(f"Nuevos keywords: {len(nuevos_keywords)}")
# Output: Nuevos keywords: 427

# Crear diccionario v4.0
diccionario_v4 = diccionario_actual + nuevos_keywords
# Total: 1,148 + 427 = 1,575 keywords
```

**Siguiente scraping (v4.0):**
- Usar 1,575 keywords
- Capturar ofertas que antes no encontrábamos
- Cerrar brecha de cobertura

---

### 2. ANÁLISIS DE OFERTAS (Downstream tasks)

Los **MISMOS DATOS** también se usan para:

```python
# Datos estructurados del NLP
oferta_procesada = {
    'titulo': 'Desarrollador Python Senior',
    'experiencia_min_anios': 5,
    'experiencia_max_anios': 7,
    'skills_tecnicas': ['Python', 'Django', 'PostgreSQL', 'Docker'],
    'skills_blandas': ['trabajo en equipo', 'comunicación'],
    'idiomas': ['inglés:avanzado'],
    'educacion_nivel': 'universitario_completo',
    'jornada_laboral': 'full-time',
    'modalidad_trabajo': 'hibrido',
    'salario_rango': '1500-2500 USD'
}

# Usado en:
# 1. Dashboard analytics (Visual--)
# 2. ESCO matching (Fase 03)
# 3. Análisis de mercado laboral
# 4. API pública (Fase 05)
# 5. Estudios de OEDE
```

---

## EVOLUCIÓN HISTÓRICA

### Tabla de iteraciones

| Versión | Keywords | Ofertas | Cobertura | Método NLP | Estado |
|---------|----------|---------|-----------|------------|--------|
| **v1** | 56 | ~1,500 | 12.5% | Manual | ✅ Completado |
| **v2** | 200 | ~3,000 | 25.0% | Regex básico | ✅ Completado |
| **v3** | 837 | ~4,200 | 35.0% | Regex + filtros | ✅ Completado |
| **v3.1** | 1,000 | ~4,800 | 40.0% | Regex avanzado | ✅ Completado |
| **v3.2** | **1,148** | **5,479** | **45.6%** | **Regex + limpieza** | ✅ **ACTUAL** |
| **v4.0** | 1,500+ | 8,000+ | 67%+ | **NER (spaCy)** | ⏳ **55% COMPLETADO** |
| **v5.0** | 1,800+ | 10,000+ | 83%+ | NER refinado | ⏳ Futuro |

### Gráfico de progreso

```
Cobertura (%)
100% ┤                                      ┌─ Meta final
 90% ┤                                  ┌───┘
 80% ┤                              ┌───┘
 70% ┤                          ┌───┘  v5.0
 60% ┤                      ┌───┘
 50% ┤                  ┌───┘  v4.0
 40% ┤              ┌───┘
 30% ┤          ┌───┘  v3.1
 20% ┤      ┌───┘  v3
 10% ┤  ┌───┘  v2
  0% ┼──┘ v1
     └──┬───┬───┬───┬───┬───┬───┬───┬──> Iteraciones
        1   2   3   4   5   6   7   8
```

---

## POR QUÉ FASE 02.5 ES CRÍTICA

**Fase 02.5 NLP Extraction** NO es solo análisis de datos.
**Es el motor que permite cerrar el bucle y capturar las 6,521 ofertas faltantes.**

### Sin completar Fase 02.5:

```
❌ No podemos generar diccionario v4.0
❌ No podemos scrapear con nuevos keywords
❌ Cobertura estancada en 45.6%
❌ 6,521 ofertas quedan sin capturar (54.4%)
```

### Completando Fase 02.5:

```
✅ Diccionario v4.0 con ~1,500 keywords
✅ Siguiente scraping captura +2,500-4,500 ofertas nuevas
✅ Cobertura sube a 67-83%
✅ Brecha se reduce a 2,000-4,000 ofertas (17-33%)
```

---

## ESTADO ACTUAL DE FASE 02.5

### Fase 1: Regex (COMPLETADA) ✅

- **Método:** Patrones regex para 23 campos
- **Cobertura:** 40%
- **Confianza:** 0.26
- **Output:** `all_sources_nlp_20251025_141134.csv`
- **Nuevos keywords extraídos:** 148 términos

### Fase 2: NER (55% COMPLETADA) ⏳

**✅ Completado:**
- Scripts de entrenamiento (1,880 líneas)
- Scripts de procesamiento
- Selección de 500 ofertas para anotación
- Dataset en formato JSONL

**⏳ Pendiente:**
1. **Anotación manual** (8-16 horas trabajo humano)
   - Herramienta: Doccano o Label Studio
   - Dataset: `ner_samples_500_ofertas.jsonl`
   - Formato: IOB tagging para 23 entidades

2. **Entrenamiento** (~30-60 minutos)
   - Framework: spaCy 3.x
   - Arquitectura: Transformer-based NER
   - Validación cruzada 80/20

3. **Procesamiento** (~20 minutos)
   - Input: 5,479 ofertas de DB
   - Output: CSV con 23 campos NER
   - Guardado en DB

4. **Generación diccionario v4.0** (~5 minutos)
   - Extraer skills únicos
   - Filtrar ya existentes en v3.2
   - Agregar ~400 nuevos términos
   - Guardar `diccionario_keywords_v4_0.json`

---

## MÉTRICAS DE MEJORA ESPERADA

### Comparación Regex (Fase 1) vs NER (Fase 2)

| Métrica | Regex (Actual) | NER (Esperado) | Mejora |
|---------|----------------|----------------|--------|
| Cobertura | 40% | 70-90% | +75-125% |
| Precisión | 0.26 | 0.75-0.85 | +188-227% |
| Recall | 0.35 | 0.65-0.80 | +86-129% |
| F1-Score | 0.30 | 0.70-0.82 | +133-173% |

### Impacto en scraping v4.0

```
Situación actual (v3.2):
- Keywords: 1,148
- Ofertas capturadas: 5,479 (45.6%)
- Ofertas no capturadas: 6,521 (54.4%)

Proyección con v4.0:
- Keywords: 1,500-1,600 (+31-39%)
- Ofertas esperadas: 8,000-10,000 (+46-83%)
- Cobertura esperada: 67-83% (+47-82% mejora)
- Brecha restante: 2,000-4,000 (17-33%)
```

---

## ROADMAP PARA COMPLETAR FASE 02.5

### Paso 1: Preparar herramienta de anotación

```bash
# Opción A: Doccano (más simple)
pip install doccano
doccano init
doccano createuser --username admin --password admin
doccano webserver --port 8000

# Opción B: Label Studio (más potente)
pip install label-studio
label-studio start
```

### Paso 2: Importar dataset para anotar

```python
# Cargar 500 ofertas seleccionadas
import json

with open('02.5_nlp_extraction/data/ner_samples_500_ofertas.jsonl') as f:
    ofertas = [json.loads(line) for line in f]

# Importar a herramienta de anotación
# (interfaz web de Doccano/Label Studio)
```

### Paso 3: Anotar entidades (8-16 horas)

**Entidades a anotar (23 tipos):**

1. `EXPERIENCIA_MIN` - Años mínimos de experiencia
2. `EXPERIENCIA_MAX` - Años máximos de experiencia
3. `SKILL_TECNICA` - Habilidad técnica (Python, Excel, etc.)
4. `SKILL_BLANDA` - Habilidad blanda (liderazgo, comunicación)
5. `IDIOMA` - Idioma y nivel (inglés avanzado)
6. `EDUCACION_NIVEL` - Nivel educativo (universitario, secundario)
7. `EDUCACION_AREA` - Área de estudio (ingeniería, contabilidad)
8. `CERTIFICACION` - Certificaciones (PMP, CPA, etc.)
9. `JORNADA` - Full-time, part-time, por proyecto
10. `MODALIDAD` - Presencial, remoto, híbrido
11. `SALARIO_MIN` - Salario mínimo ofrecido
12. `SALARIO_MAX` - Salario máximo ofrecido
13. `MONEDA` - ARS, USD, EUR
14. `BENEFICIO` - Beneficios adicionales
15. `VACANTES` - Cantidad de vacantes
16. `UBICACION` - Localización geográfica
17. `AREA_TRABAJO` - Área/departamento
18. `SECTOR` - Sector industrial
19. `RESPONSABILIDAD` - Responsabilidades clave
20. `REQUISITO` - Requisitos obligatorios
21. `DESEABLE` - Requisitos deseables
22. `HORARIO` - Horario laboral
23. `OCUPACION` - Título de la ocupación

**Ejemplo de anotación:**

```
Texto original:
"Buscamos contador con 3-5 años de experiencia en IFRS,
inglés intermedio, disponibilidad full-time."

Anotado (formato IOB):
Buscamos      O
contador      B-OCUPACION
con           O
3             B-EXPERIENCIA_MIN
-             I-EXPERIENCIA_MIN
5             B-EXPERIENCIA_MAX
años          O
de            O
experiencia   O
en            O
IFRS          B-SKILL_TECNICA
,             O
inglés        B-IDIOMA
intermedio    I-IDIOMA
,             O
disponibilidad O
full-time     B-JORNADA
.             O
```

### Paso 4: Entrenar modelo NER

```bash
cd D:\OEDE\Webscrapping\02.5_nlp_extraction

# Entrenar modelo con datos anotados
python scripts/train_ner_model.py \
    --input data/ner_samples_500_anotadas.jsonl \
    --output models/ner_model_v1 \
    --epochs 20 \
    --batch_size 8

# Tiempo estimado: 30-60 minutos
```

### Paso 5: Procesar ofertas completas

```bash
# Procesar las 5,479 ofertas con modelo entrenado
python scripts/process_all_offers_ner.py \
    --model models/ner_model_v1 \
    --input database/bumeran_scraping.db \
    --output data/all_sources_ner_20251031.csv

# Tiempo estimado: 20 minutos
```

### Paso 6: Generar diccionario v4.0

```bash
# Extraer keywords únicos del procesamiento NER
python scripts/generate_keywords_v4.py \
    --input data/all_sources_ner_20251031.csv \
    --current_dict 01_sources/bumeran/scrapers/diccionario_keywords_v3_2.json \
    --output 01_sources/bumeran/scrapers/diccionario_keywords_v4_0.json \
    --min_frequency 2

# Output esperado:
# - Keywords v3.2: 1,148
# - Nuevos keywords extraídos: 427
# - Keywords v4.0: 1,575
```

### Paso 7: Ejecutar scraping v4.0

```bash
# Actualizar estrategia en scrapear_con_diccionario.py
# Agregar estrategia 'ultra_exhaustiva_v4_0'

cd 01_sources/bumeran/scrapers
python run_scraping_completo.py --estrategia ultra_exhaustiva_v4_0

# Tiempo estimado: ~52 minutos (1,575 keywords)
# Ofertas esperadas: 8,000-10,000
# Nuevas capturas: 2,500-4,500
```

---

## MÉTRICAS DE VALIDACIÓN

### Validar que el bucle funciona:

```python
# Verificar mejora de cobertura
metricas = {
    'v3.2': {
        'keywords': 1148,
        'ofertas_capturadas': 5479,
        'cobertura': 45.6,
        'brecha': 6521
    },
    'v4.0': {
        'keywords': 1575,  # esperado
        'ofertas_capturadas': 9000,  # esperado
        'cobertura': 75.0,  # esperado
        'brecha': 3000  # esperado
    }
}

mejora = {
    'keywords_incremento_pct': (1575/1148 - 1) * 100,  # +37.2%
    'ofertas_incremento_pct': (9000/5479 - 1) * 100,   # +64.3%
    'cobertura_incremento_pts': 75.0 - 45.6,           # +29.4 pts
    'brecha_reduccion_pct': (1 - 3000/6521) * 100      # -54.0%
}

print("Mejoras con v4.0:")
print(f"  Keywords: +{mejora['keywords_incremento_pct']:.1f}%")
print(f"  Ofertas: +{mejora['ofertas_incremento_pct']:.1f}%")
print(f"  Cobertura: +{mejora['cobertura_incremento_pts']:.1f} puntos")
print(f"  Brecha reducida: {mejora['brecha_reduccion_pct']:.1f}%")
```

---

## CONCLUSIÓN

**El bucle iterativo keywords-scraping-NLP es el CORE del sistema.**

No es un proceso lineal de:
```
❌ Scrapear → Analizar → Fin
```

Es un proceso **CÍCLICO** de mejora continua:
```
✅ Scrapear → Analizar → Extraer keywords → Scrapear mejor → Repetir
```

**Cada iteración:**
- ✅ Aumenta cobertura de ofertas capturadas
- ✅ Descubre nuevos términos del mercado laboral
- ✅ Mejora precisión del análisis NLP
- ✅ Reduce la brecha con ofertas disponibles

**Estado actual:**
- Iteración 5 (v3.2): 45.6% cobertura
- Fase 02.5: 55% completada
- **Objetivo:** Completar Fase 02.5 → Lanzar v4.0 → 67-83% cobertura

**Próximos pasos:**
1. Anotar 500 ofertas (8-16h humano)
2. Entrenar NER (~1h máquina)
3. Procesar 5,479 ofertas (~20min)
4. Generar diccionario v4.0 (~5min)
5. Scrapear con v4.0 (~52min)
6. Capturar 2,500-4,500 ofertas nuevas
7. Cerrar brecha de 54.4% → 17-33%

---

**Fecha de creación:** 2025-10-31
**Autor:** Sistema MOL (Monitor de Ofertas Laborales)
**Versión:** 1.0
**Revisión requerida:** Cada nueva iteración de keywords

**IMPORTANTE:** Este documento debe consultarse cada vez que se trabaje con NLP o keywords para recordar que son dos caras de la misma moneda - el bucle de mejora continua.
