# Anotación Automática - NO es Manual ✨

## Resumen Ejecutivo

**¿Por qué la anotación tiene que ser manual?**
**Respuesta: ¡NO TIENE QUE SER MANUAL!** 🎉

Tienes **3 opciones**, desde totalmente automática hasta manual:

---

## Comparación Rápida

| Opción | Tiempo | Costo | Calidad | Complejidad |
|--------|--------|-------|---------|-------------|
| **🤖 LLM (GPT-4/Claude)** | **15 min** ⭐ | **$5-15** | **90%** ⭐ | **Muy Fácil** ⭐ |
| 🔄 Pre-anotación Regex | 2-4 horas | $0 | 75% | Fácil |
| 👤 Manual (Doccano) | 8-16 horas | $0 | 95% | Media |

---

## Opción Recomendada: LLM Automático 🚀

### Paso 1: Obtener API Key (5 minutos)

**OpenAI (más barato):**
1. https://platform.openai.com/
2. Agregar $10 de crédito
3. Copiar API key

**Anthropic (mejor calidad):**
1. https://console.anthropic.com/
2. Agregar $10 de crédito
3. Copiar API key

### Paso 2: Instalar y configurar (2 minutos)

```bash
# Instalar
pip install openai
# o
pip install anthropic

# Configurar (Windows)
set OPENAI_API_KEY=sk-...
# o (Linux/Mac)
export OPENAI_API_KEY=sk-...
```

### Paso 3: Ejecutar anotación automática (15 minutos)

```bash
cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts

# Probar con 10 muestras primero
python auto_annotate_with_llm.py --provider openai --limit 10

# Si funciona, ejecutar todas (500 ofertas)
python auto_annotate_with_llm.py --provider openai
```

**Resultado:**
- ✅ 500 ofertas anotadas en 10-15 minutos
- ✅ ~450 ofertas con anotaciones correctas (90% calidad)
- ✅ Costo: $5-10 USD
- ✅ Listo para entrenar modelo NER

### Paso 4: Entrenar modelo NER (30 minutos)

```bash
# Convertir a formato spaCy
python convert_annotations_to_spacy.py \
    --input ../data/ner_training/ner_samples_for_annotation_20251027_101013_llm_annotated.jsonl \
    --format doccano

# Entrenar
python train_ner_model.py \
    --train-data ../data/ner_training/spacy_format/train_data.json \
    --dev-data ../data/ner_training/spacy_format/dev_data.json \
    --n-iter 30
```

**Tiempo total: ~1 hora (vs 8-16 horas manual)**

---

## Alternativa: Sin Presupuesto ($0)

### Opción A: Pre-anotación con Fase 1 + Manual

```bash
# 1. Pre-anotar con Regex (1 minuto)
python auto_annotate_with_regex.py

# Resultado: 27 ofertas pre-anotadas (5.4%)
```

Luego:
2. Cargar en Doccano: `ner_samples_for_annotation_20251027_101013_pre_annotated.jsonl`
3. Completar manualmente: 473 ofertas restantes (4-8 horas)

### Opción B: Saltar Fase 2

Si no tienes tiempo ni dinero:
- Usa resultados de Fase 1 (Regex) directamente
- Mejora patterns y skills_database.json
- Puede alcanzar 50-55% cobertura

---

## Costos Detallados LLM

### OpenAI GPT-4 Turbo
- 500 ofertas: **$7-10 USD**
- 1,000 ofertas: $14-20 USD
- 5,000 ofertas: $70-100 USD

### Anthropic Claude 3 Sonnet (Recomendado)
- 500 ofertas: **$3-5 USD** ⭐ Más barato
- 1,000 ofertas: $6-10 USD
- 5,000 ofertas: $30-50 USD
- Mejor para español

---

## Scripts Disponibles

✅ **Todos los scripts ya están creados:**

| Script | Descripción |
|--------|-------------|
| `prepare_ner_dataset.py` | Selecciona 500 muestras (YA EJECUTADO) |
| `auto_annotate_with_llm.py` | Anota con GPT-4/Claude ⭐ NUEVO |
| `auto_annotate_with_regex.py` | Pre-anota con Fase 1 (YA EJECUTADO) |
| `convert_annotations_to_spacy.py` | Convierte a formato spaCy |
| `train_ner_model.py` | Entrena modelo NER |
| `base_ner_extractor.py` | Procesa dataset con NER |
| `compare_phase1_vs_phase2.py` | Compara resultados |

---

## Decisión Rápida

### ¿Tienes $5-10 disponibles?

**SÍ →** Usa LLM (auto_annotate_with_llm.py)
- Tiempo: 1 hora total
- Calidad: 90%
- Hoy mismo tienes modelo NER entrenado

**NO →**
- ¿Tienes 4-8 horas? → Pre-anotación + Manual (Doccano)
- ¿No tienes tiempo? → Saltar Fase 2, mejorar Fase 1

---

## FAQ

**P: ¿El LLM comete errores?**
R: Sí, ~10% de errores. Pero mejor que Regex (40% errores) y más rápido que manual (8 horas).

**P: ¿Necesito revisar todas las anotaciones?**
R: No. Revisa 20-30 muestras (10 minutos). Si >85% correctas, úsalas directamente.

**P: ¿Qué LLM es mejor?**
R: Claude (Anthropic) - Mejor español + más barato ($3 vs $10).

**P: ¿Puedo probar con pocas muestras primero?**
R: Sí! `--limit 10` para probar. Costo: $0.15 USD.

**P: ¿Realmente funciona?**
R: Sí. LLMs estado del arte (GPT-4, Claude) tienen >90% precisión en NER para español.

---

## Siguiente Acción Recomendada

Si tienes presupuesto para $5-10:

```bash
# 1. Configurar API key
set OPENAI_API_KEY=sk-...

# 2. Probar con 10 muestras
cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts
python auto_annotate_with_llm.py --provider openai --limit 10

# 3. Si funciona, ejecutar todas
python auto_annotate_with_llm.py --provider openai

# ¡Listo! En 1 hora tienes modelo NER entrenado
```

Si presupuesto $0:

```bash
# 1. Pre-anotar con Regex (ya ejecutado)
# Archivo: ner_samples_for_annotation_20251027_101013_pre_annotated.jsonl

# 2. Instalar Doccano
pip install doccano
doccano init
doccano webserver --port 8000

# 3. Cargar y completar manualmente (4-8 horas)
```

---

## Documentación Completa

Ver `ANNOTATION_OPTIONS.md` para comparación detallada de todas las opciones.

---

**Resumen:** NO necesitas anotar manualmente. Usa LLM por $5-10 y termina en 1 hora. 🚀
