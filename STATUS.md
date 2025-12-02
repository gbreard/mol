# STATUS.md - MOL Monitor Ofertas Laborales

> **Ultima actualizacion:** 2025-12-02
> **Branch activo:** feature/fase1-fundamentos-datos
> **Linear:** https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f

---

## ESTADO ACTUAL DEL PROYECTO

### Versiones Activas

| Componente | Version | Archivo Principal |
|------------|---------|-------------------|
| **Matching Rules** | v8.3 | database/matching_rules_v83.py |
| **NLP Pipeline** | v8.0 | database/process_nlp_from_db_v7.py |
| **Regex Patterns** | v4.0 | 02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py |
| **Prompts LLM** | v8.0 | 02.5_nlp_extraction/prompts/extraction_prompt_v8.py |

### Metricas Actuales

| Metrica | Valor | Meta | Medicion |
|---------|-------|------|----------|
| **Precision ESCO** | ~80% | >85% | python database/test_gold_set_manual.py |
| **Gold Set** | 19 casos | 50+ | database/gold_set_manual_v1.json |
| **Cobertura NLP** | 60-70% | >75% | regex v4 capa 0 |

### Errores Conocidos (Gold Set 19)

Total: 8 errores de 19 casos (42.1%)

Por tipo:
- sector_funcion:     4 casos (50%) <- PRIORIDAD
- nivel_jerarquico:   2 casos (25%)
- tipo_ocupacion:     1 caso
- programa_general:   1 caso

---

## ESTRUCTURA DEL PROYECTO

D:\OEDE\Webscrapping- 01_sources/          # Scrapers (Bumeran, ZonaJobs, Indeed, LinkedIn, ComputRabajo)
- 02_consolidation/    # Normalizacion y deduplicacion
- 02.5_nlp_extraction/ # Pipeline NLP (prompts, patterns, extractors)
- 03_esco_matching/    # Matching semantico ESCO/ISCO
- 04_analysis/         # Analisis estadistico
- 05_products/         # Productos finales
- Visual--/            # Dashboard Shiny (produccion)
- database/            # SQLite + ChromaDB + scripts de matching
- shared/              # Schema unificado y utilidades

---

## PIPELINE DE MATCHING ESCO (v8.3)

Oferta -> match_ofertas_multicriteria.py
         - Titulo (50%): BGE-M3 + ESCO-XLM
         - Skills (40%): SQL lookup esco_associations
         - Descripcion (10%): BGE-M3 embeddings
         - Ajustes v8.3: matching_rules_v83.py
           - 6 familias funcionales
           - never_confirm para casos problematicos
           - Reglas especificas (vehiculos, barista, abogados, jerarquia)

### Sistema never_confirm

Casos que NUNCA se auto-confirman:
- Admin -> Analista de negocios
- Comercial -> No-comercial
- Farmaceutico -> Ingeniero
- Pasantias -> Cualquier ocupacion especifica
- Servicios/Vendedor -> Director
- Operario -> Negocios
- Ventas vehiculos -> Repuestos
- Barista -> Comercio internacional cafe
- Abogado -> Administrativo juridico
- Junior -> Director/Gerente

---

## PIPELINE NLP (v8.0)

Descripcion -> Capa 0: regex_patterns_v4.py (60-70% precision 100%)
            -> Capa 1: extraction_prompt_v8.py + Qwen2.5:14b
            -> Capa 2: process_nlp_from_db_v7.py (post-validacion anti-alucinacion)

---

## BACKLOG LINEAR (Prioridades)

### Alta Prioridad
- **MOL-5:** [v8.4] Resolver errores sector_funcion (4 casos)
- **MOL-6:** Expandir Gold Set de 19 a 50+ casos

### Media Prioridad
- **MOL-7:** Agregar metricas de Recall al benchmark
- **MOL-8:** Resolver casos bilingues
- **MOL-10:** Regex v4.1: Abreviaciones argentinas
- **MOL-11:** Mejorar deteccion niveles jerarquicos

### Baja Prioridad
- **MOL-9:** CI/CD test automatico gold set
- **MOL-12:** Consolidar pipeline NLP v6+v7
- **MOL-15:** Limpieza JSONs duplicados

---

## COMANDOS UTILES

# Correr test de gold set
python database/test_gold_set_manual.py

# Test de regresion completo
python database/test_esco_matching_regression.py --gold19

# Aplicar reglas v8.3 a gold set
python database/apply_v82_rules_gold19.py

# Batch de matching
python database/run_batch_pilot_v8.py --rules v8.3 --limit 100

---

## ARCHIVOS CLAVE

| Proposito | Archivo |
|-----------|---------|
| Gold Set | database/gold_set_manual_v1.json |
| Reglas Matching | database/matching_rules_v83.py |
| Matcher Principal | database/match_ofertas_multicriteria.py |
| NLP Pipeline | database/process_nlp_from_db_v7.py |
| Test Benchmark | database/test_gold_set_manual.py |
| Prompts LLM | 02.5_nlp_extraction/prompts/extraction_prompt_v8.py |
| Regex Patterns | 02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py |
| Dashboard | Visual--/app.R |

---

## NOTAS PARA PROXIMA SESION

1. **Prioridad 1:** Resolver MOL-5 (errores sector_funcion) creando matching_rules_v84.py
2. **Prioridad 2:** Expandir gold set a 50+ casos (MOL-6)
3. **Pendiente:** Auditoria detallada de Infraestructura Base y Dashboard v3
