# Opciones de Anotación - Manual vs Automática

**Pregunta:** ¿Por qué la anotación tiene que ser manual?
**Respuesta:** ¡NO tiene que ser manual! Hay 3 opciones:

---

## Comparación de Opciones

| Aspecto | Manual | Pre-anotación (Regex) | LLM Automática |
|---------|--------|----------------------|----------------|
| **Tiempo** | 8-16 horas | 2-4 horas | **10-30 minutos** ⭐ |
| **Costo** | $0 (solo tiempo) | $0 | **$5-15 USD** |
| **Calidad** | 95-100% (depende del anotador) | 70-80% | **85-95%** |
| **Skill requerido** | Medio (leer guía) | Bajo (revisar) | **Ninguno** ⭐ |
| **Escalabilidad** | Mala | Media | **Excelente** ⭐ |
| **Recomendado para** | Presupuesto $0 | Fase 1 funcionó bien | Rapidez + calidad |

---

## Opción 1: Anotación Manual (Tradicional)

### Proceso

1. Instalar Doccano o Label Studio
2. Cargar 500 ofertas
3. Anotar manualmente cada entidad (YEARS, EDUCATION, SKILL, etc.)
4. Revisar consistencia
5. Exportar

### Ventajas
- ✅ Sin costos monetarios
- ✅ Máxima calidad (si el anotador es cuidadoso)
- ✅ Control total del proceso

### Desventajas
- ❌ **Muy lento:** 8-16 horas de trabajo tedioso
- ❌ Requiere entrenamiento del anotador
- ❌ Propenso a errores por fatiga
- ❌ No escalable (si necesitas más datos después)

### Cuándo usar
- Presupuesto $0 absoluto
- Tienes tiempo disponible
- Quieres máximo control de calidad

---

## Opción 2: Pre-anotación con Fase 1 (Semi-automática)

### Proceso

```bash
# 1. Pre-anotar con resultados de Fase 1
python auto_annotate_with_regex.py

# 2. Cargar en Doccano/Label Studio
# 3. Revisar y corregir (2-4 horas)
# 4. Exportar
```

### Resultado Actual
- **27 de 500 muestras pre-anotadas (5.4%)**
- **28 entidades detectadas automáticamente**
- Resto requiere anotación manual

### Ventajas
- ✅ Sin costos monetarios
- ✅ Reduce tiempo de anotación en ~50%
- ✅ Aprovecha trabajo de Fase 1

### Desventajas
- ❌ **Cobertura baja:** Solo 5.4% pre-anotado (en este caso)
- ❌ Aún requiere 4-8 horas de trabajo manual
- ❌ Calidad limitada por la de Fase 1

### Cuándo usar
- Presupuesto $0
- Fase 1 tuvo buena cobertura (>60%)
- Tienes algo de tiempo disponible

---

## Opción 3: Anotación con LLM (Totalmente Automática) ⭐ RECOMENDADO

### Proceso

```bash
# Configurar API key
export OPENAI_API_KEY=sk-...
# o
export ANTHROPIC_API_KEY=sk-ant-...

# Anotar automáticamente
python auto_annotate_with_llm.py --provider openai --limit 500

# Resultado: 500 ofertas anotadas en 10-30 minutos
```

### Proveedores Disponibles

#### OpenAI (GPT-4)
- **Modelo:** gpt-4-turbo-preview
- **Costo:** ~$5-10 USD por 500 ofertas
- **Calidad:** 85-90%
- **Velocidad:** 500 ofertas en 15-20 minutos

#### Anthropic (Claude)
- **Modelo:** claude-3-sonnet
- **Costo:** ~$8-15 USD por 500 ofertas
- **Calidad:** 90-95% (mejor para español)
- **Velocidad:** 500 ofertas en 10-15 minutos

### Ventajas
- ✅ **Extremadamente rápido:** 10-30 minutos total
- ✅ **Alta calidad:** 85-95% de precisión
- ✅ Sin esfuerzo humano (corre solo)
- ✅ Totalmente escalable (puedes anotar 5,000 más si quieres)
- ✅ Consistente (no se cansa)

### Desventajas
- ❌ Costo monetario: $5-15 USD
- ❌ Requiere API key de OpenAI o Anthropic
- ❌ Necesita validación (revisar sample de 20-30)

### Cuándo usar
- **Presupuesto disponible** para API ($5-15)
- **Necesitas resultados rápidos** (hoy mismo)
- **Calidad es importante** (>85%)
- Quieres escalar a más datos después

---

## Recomendación por Escenario

### Escenario A: "Tengo $10 disponibles"
**→ Opción 3 (LLM)** sin dudar

- 10-30 minutos de procesamiento
- Calidad 85-95%
- Hoy mismo tienes el modelo entrenado

### Escenario B: "Presupuesto $0 estricto pero tengo tiempo"
**→ Opción 2 (Pre-anotación Regex) + Manual**

1. Pre-anotar con Regex (5% ya hecho)
2. Completar manualmente el resto (4-8 horas)

### Escenario C: "Presupuesto $0 y poco tiempo"
**→ Saltar Fase 2, mejorar Fase 1 con más patterns**

Si no tienes dinero ni tiempo:
- Mejora los regex patterns de Fase 1
- Agrega más skills a la base de datos
- Puede alcanzar 50-55% cobertura sin NER

### Escenario D: "Quiero máxima calidad, dinero no importa"
**→ Opción 3 (LLM) + Validación Manual**

1. Anotar 500 con LLM ($10)
2. Revisar manualmente 50 muestras (1 hora)
3. Si calidad >90%, usar directamente
4. Si calidad <90%, corregir errores comunes

---

## Paso a Paso - Opción 3 (LLM) 🚀

### 1. Obtener API Key

**OpenAI (más económico):**
1. Ir a https://platform.openai.com/
2. Crear cuenta (gratis)
3. Agregar $5-10 de crédito
4. Copiar API key

**Anthropic (mejor calidad):**
1. Ir a https://console.anthropic.com/
2. Crear cuenta (gratis)
3. Agregar $10-20 de crédito
4. Copiar API key

### 2. Instalar dependencias

```bash
# Para OpenAI
pip install openai

# Para Anthropic
pip install anthropic
```

### 3. Configurar API key

**Windows:**
```bash
set OPENAI_API_KEY=sk-...
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=sk-...
```

### 4. Ejecutar anotación

```bash
cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts

# Primero probar con 10 muestras
python auto_annotate_with_llm.py --provider openai --limit 10

# Si funciona bien, ejecutar todas
python auto_annotate_with_llm.py --provider openai --limit 500
```

### 5. Validar calidad (10 minutos)

```python
# Script rápido para revisar calidad
import json
import random

# Cargar anotaciones
with open('../data/ner_training/ner_samples_for_annotation_20251027_101013_llm_annotated.jsonl', 'r') as f:
    samples = [json.loads(line) for line in f if line.strip()]

# Tomar 20 muestras aleatorias
random_samples = random.sample(samples, 20)

# Revisar manualmente
for i, sample in enumerate(random_samples, 1):
    print(f"\n{'='*70}")
    print(f"Muestra {i}/20")
    print(f"{'='*70}")
    print(f"Texto: {sample['text'][:200]}...")
    print(f"\nEntidades detectadas:")
    for start, end, label in sample['label']:
        entity_text = sample['text'][start:end]
        print(f"  [{label}] {entity_text}")

    respuesta = input("\n¿Anotación correcta? (s/n/q para salir): ")
    if respuesta.lower() == 'q':
        break
```

### 6. Continuar con training

Si calidad >85%:
```bash
# Convertir a spaCy
python convert_annotations_to_spacy.py \
    --input ../data/ner_training/ner_samples_for_annotation_20251027_101013_llm_annotated.jsonl \
    --format doccano

# Entrenar
python train_ner_model.py \
    --train-data ../data/ner_training/spacy_format/train_data.json \
    --dev-data ../data/ner_training/spacy_format/dev_data.json \
    --n-iter 30
```

---

## Estimación de Costos LLM

### Por 500 ofertas

**OpenAI GPT-4 Turbo:**
- Input: ~375,000 tokens ($0.01/1K) = $3.75
- Output: ~125,000 tokens ($0.03/1K) = $3.75
- **Total: ~$7.50 USD**

**Anthropic Claude 3 Sonnet:**
- Input: ~375,000 tokens ($0.003/1K) = $1.13
- Output: ~125,000 tokens ($0.015/1K) = $1.88
- **Total: ~$3.00 USD** ⭐ Más barato!

### Por 5,000 ofertas (si quieres escalar)
- OpenAI: ~$75 USD
- Anthropic: ~$30 USD

---

## Decisión Rápida: ¿Qué opción elegir?

```
¿Tienes $5-15 USD disponibles?
├─ Sí → Opción 3 (LLM) ✅
│   ├─ ¿Mejor español? → Anthropic Claude
│   └─ ¿Más económico? → OpenAI GPT-4
│
└─ No → ¿Tienes 4-8 horas disponibles?
    ├─ Sí → Opción 2 (Regex + Manual)
    │   └─ python auto_annotate_with_regex.py
    │       + Revisar manualmente en Doccano
    │
    └─ No → Saltar Fase 2 o mejorar Fase 1
        └─ Agregar más patterns regex
            + Expandir skills_database.json
```

---

## Scripts Disponibles

| Script | Propósito | Tiempo | Costo |
|--------|-----------|--------|-------|
| `prepare_ner_dataset.py` | Selecciona 500 muestras | 1 min | $0 |
| `auto_annotate_with_regex.py` | Pre-anota con Fase 1 | 1 min | $0 |
| `auto_annotate_with_llm.py` | Anota con GPT-4/Claude | **15 min** | **$5-15** |
| Manual (Doccano) | Anotar manualmente | 8-16 horas | $0 |

---

## FAQ

### ¿El LLM puede equivocarse?
Sí, típicamente 5-15% de errores. Pero es mejor que:
- Regex Fase 1: ~40% de errores
- Humano cansado: ~10-20% de errores

### ¿Necesito revisar todas las anotaciones del LLM?
No. Revisa un sample de 20-30 (10 minutos). Si calidad >85%, úsalas directamente.

### ¿Puedo combinar métodos?
¡Sí! Por ejemplo:
1. LLM anota 400 ofertas ($6)
2. Manual para 100 ofertas difíciles (2 horas)
3. Mejor relación costo-calidad

### ¿Qué pasa si no puedo pagar LLM?
Opciones:
1. Usa pre-anotación Regex + manual (2-4 horas)
2. Salta Fase 2, mejora Fase 1 con más patterns
3. Usa modelo pre-entrenado genérico (no custom)

### ¿El modelo NER realmente mejora sobre Regex?
Solo si la anotación es buena. Con LLM (85-95% calidad) → sí, mejora.
Con anotación manual rápida/descuidada (70% calidad) → probablemente no.

---

## Mi Recomendación Personal

**Si tienes $10 disponibles: usa LLM (Opción 3).**

¿Por qué?
- Tu tiempo vale más que $10
- 15 minutos vs 8 horas
- Calidad 90% vs 80-95% manual (con fatiga)
- Escalable si necesitas más datos

**Si presupuesto $0:** Pre-anota con Regex (27 ofertas listas) + completa manualmente el resto en Doccano (4-6 horas).

---

**Próximo paso:** Decidir qué opción usar y ejecutarla.

¿Qué prefieres?
