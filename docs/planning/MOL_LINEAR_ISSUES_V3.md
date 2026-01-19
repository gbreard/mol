# MOL - Issues Linear v3.0

> **Fecha:** 2025-01-03
> **Estado:** Actualizado - NLP v10, Matching v2.1.1 BGE-M3, Postprocessor v1.0
> **Propósito:** Issues detallados para implementación con Claude Code

---

## Hitos Completados

| Issue | Descripción | Estado | Fecha |
|-------|-------------|--------|-------|
| MOL-62 | NLP Schema v5 - 153 campos estructurados | ✅ Completado | 2025-12-10 |
| MOL-34 | Gold Set Matching expandido a 49 casos | ✅ Completado | 2025-12-10 |
| MOL-63 | Matching v2.1.1 BGE-M3 - 100% precisión | ✅ Completado | 2025-12-10 |
| - | NLP Pipeline v10.0 completo | ✅ Completado | 2025-12-14 |
| - | NLP Postprocessor v1.0 | ✅ Completado | 2025-12-14 |
| - | Skills fusión LLM+regex | ✅ Completado | 2025-12-14 |
| - | Gold Set NLP 49 casos validados | ✅ Completado | 2025-12-30 |

### Matching v2.1.1 BGE-M3 (Producción)
- **Modelo:** BAAI/bge-m3 (embeddings semánticos)
- **Precisión Gold Set:** 100% (49/49 correctos)
- **Archivo principal:** `database/match_ofertas_v2.py`
- **Caso crítico corregido:** ID 1117984105 "Gerente de Ventas" → Director de ventas (ISCO 1221)

### NLP v10.0 (Producción)
- **Pipeline:** `database/process_nlp_from_db_v10.py`
- **Postprocessor:** `database/nlp_postprocessor.py`
- **Precisión Gold Set:** 96-100% por campo
- **Campos:** 153 (NLP Schema v5)

---

## Resumen de Épicas

| Épica | Issues | Prioridad Alta |
|-------|--------|----------------|
| 1. Scraping | 4 | 1 |
| 2. NLP | 5 | 3 |
| 3. Matching ESCO | 5 | 4 |
| 4. Validación | 5 | 3 |
| 5. Dashboards | 5 | 2 |
| 6. Infraestructura | 6 | 1 |
| **Total** | **30** | **14** |

---

# ÉPICA 1: SCRAPING

---

## MOL-27: Dashboard Admin - Tab Scraping

### Contexto
El scraping actual tiene múltiples scripts que causan confusión. El error más común es usar `bumeran_scraper.py` directamente (trae ~20 ofertas) en lugar de `run_scheduler.py` (trae ~10,000).

**Estado actual:**
- 10,223 IDs en tracking
- 9,564 ofertas en BD
- 1,148 keywords activos
- Gap se cierra naturalmente (89% cobertura)

### Objetivo
Crear tab de Scraping en dashboard Streamlit que sea el único punto de entrada.

### Archivos a Crear/Modificar

```
dashboards/admin/
├── app.py                    # App principal Streamlit
├── tabs/
│   └── scraping_tab.py       # Este issue
├── components/
│   └── scraping_status.py    # Widget de estado
└── utils/
    └── scraping_runner.py    # Wrapper para run_scheduler
```

### Especificación UI

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TAB: SCRAPING                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⚠️ IMPORTANTE: Siempre usar este dashboard para scraping.                 │
│     NO ejecutar bumeran_scraper.py directamente.                           │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  BUMERAN (Portal Principal)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Estrategia: [ultra_exhaustiva_v3_2 ▼]                             │   │
│  │  Keywords:   1,148                                                  │   │
│  │  Páginas:    1 por keyword (workaround bug API)                    │   │
│  │                                                                     │   │
│  │  ───────────────────────────────────────────────────────────────   │   │
│  │                                                                     │   │
│  │  Última ejecución:   [fecha de BD]                                 │   │
│  │  Ofertas en tracking: [count de tracking JSON]                     │   │
│  │  Ofertas en BD:       [count de SQLite]                            │   │
│  │  Próxima automática:  [calculado según config]                     │   │
│  │                                                                     │   │
│  │  [▶️ Ejecutar Ahora]                    Estado: [spinner/listo]    │   │
│  │                                                                     │   │
│  │  ☑️ Detectar bajas automáticamente post-scraping                   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  OTROS PORTALES (Futuro)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Portal       │ Estado      │ Última    │ Ofertas │ Acción          │   │
│  │──────────────┼─────────────┼───────────┼─────────┼─────────────────│   │
│  │ ZonaJobs     │ ✅ Listo    │ -         │ 0       │ [Activar]       │   │
│  │ Computrabajo │ ⚠️ Revisar  │ -         │ 0       │ [Configurar]    │   │
│  │ LinkedIn     │ ⚠️ Limited  │ -         │ 0       │ [Configurar]    │   │
│  │ Indeed       │ ⚠️ Limited  │ -         │ 0       │ [Configurar]    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  Programación automática:                                                  │
│  ┌─────────────────┐ ┌─────────────────┐                                   │
│  │ Días: [Lun,Jue] │ │ Hora: [08:00]   │  [Guardar Config]                │
│  └─────────────────┘ └─────────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Código Referencia

```python
# dashboards/admin/utils/scraping_runner.py

import subprocess
import json
from pathlib import Path
from datetime import datetime

class ScrapingRunner:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.tracking_path = self.base_path / "data/tracking/bumeran_scraped_ids.json"
        self.db_path = self.base_path / "database/mol_database.db"
    
    def get_status(self) -> dict:
        """Obtener estado actual del scraping"""
        tracking_count = 0
        if self.tracking_path.exists():
            with open(self.tracking_path) as f:
                data = json.load(f)
                tracking_count = len(data.get("seen_ids", []))
        
        # Query SQLite para ofertas activas
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM ofertas WHERE estado_oferta = 'activa'")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "tracking_count": tracking_count,
            "db_count": db_count,
            "last_run": self._get_last_run(),
            "next_run": self._get_next_run()
        }
    
    def run_scraping(self, detect_bajas: bool = True) -> dict:
        """Ejecutar scraping con detección de bajas opcional"""
        result = subprocess.run(
            ["python", "run_scheduler.py", "--test"],
            cwd=self.base_path,
            capture_output=True,
            text=True
        )
        
        if detect_bajas and result.returncode == 0:
            subprocess.run(
                ["python", "database/detectar_bajas_integrado.py"],
                cwd=self.base_path,
                capture_output=True
            )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
```

### Criterios de Aceptación

- [ ] Tab Scraping funcional en Streamlit
- [ ] Muestra estado actual (tracking, BD, última ejecución)
- [ ] Botón ejecuta `run_scheduler.py --test`
- [ ] Checkbox para detectar bajas post-scraping
- [ ] Spinner durante ejecución
- [ ] Mensaje de éxito/error al finalizar
- [ ] Config de programación guardable

### Prioridad: 🔴 Alta

### Labels: `dashboard`, `scraping`, `feature`

### Estimación: 4h

---

## MOL-28: Activar Scraper ZonaJobs

### Contexto
ZonaJobs es el segundo portal más importante. El scraper existe y funciona pero no está integrado al scheduler.

### Objetivo
Integrar ZonaJobs al flujo de scraping semanal.

### Archivos Involucrados

```
01_sources/zonajobs/
├── zonajobs_scraper_final.py   # Scraper existente
└── config.py                   # Configuración

run_scheduler.py                # Agregar ZonaJobs
```

### Criterios de Aceptación

- [ ] ZonaJobs se ejecuta después de Bumeran
- [ ] Ofertas se insertan en misma BD
- [ ] Deduplicación cross-portal funciona
- [ ] Tab Scraping muestra estado ZonaJobs

### Prioridad: 🟡 Media

### Labels: `scraping`, `feature`

### Estimación: 3h

---

## MOL-29: Deduplicación Cross-Portal

### Contexto
Cuando se activen múltiples portales, habrá ofertas duplicadas (misma empresa publica en varios sitios).

### Objetivo
Detectar y marcar duplicados antes del procesamiento NLP.

### Algoritmo

```python
# Blocking: Provincia + semana (reduce O(n²) a O(n×k))
# Scoring: Título 40% + Descripción 35% + Empresa 15% + Salario 10%
# Threshold: >= 0.85 duplicado, 0.70-0.84 revisar
# Grupos: Union-Find para clusters de duplicados
```

### Archivos a Crear

```
database/
└── deduplicate_cross_portal.py

# Campos a agregar en BD:
# - grupo_duplicado: "DUP-00001"
# - es_duplicado: 0/1
# - es_canonico: 0/1 (cuál es la versión principal)
```

### Criterios de Aceptación

- [ ] Script detecta duplicados con precisión >= 95%
- [ ] No marca falsos positivos
- [ ] Campos agregados a BD
- [ ] Ejecutable desde dashboard

### Prioridad: 🟡 Media

### Labels: `scraping`, `etl`, `feature`

### Estimación: 4h

---

# ÉPICA 2: NLP

---

## MOL-30: Gold Set NLP (200+ casos)

### Contexto
Actualmente no existe gold set para NLP. Se necesitan 200+ casos validados campo por campo para medir precisión del pipeline.

### Objetivo
Crear gold set con 200+ ofertas validadas manualmente.

### Estructura Propuesta

```json
{
  "version": "1.0",
  "created": "2025-12-07",
  "cases": [
    {
      "id": "1118027662",
      "raw": {
        "titulo": "Vendedor Senior B2B",
        "descripcion": "Buscamos vendedor con 3+ años...",
        "empresa": "Confidencial",
        "ubicacion": "CABA"
      },
      "expected": {
        "experiencia_min_anios": 3,
        "nivel_educativo": "secundario",
        "modalidad": "presencial",
        "area_funcional": "ventas",
        "nivel_seniority": "senior",
        "tech_skills": ["CRM"],
        "soft_skills": ["negociación", "comunicación"]
      },
      "validation_source": "manual",
      "validated_by": "gerardo",
      "validated_at": "2025-12-07"
    }
  ]
}
```

### Estrategia de Muestreo

| Criterio | Casos | % |
|----------|-------|---|
| Por familia funcional | 100 | 50% |
| Por score NLP | 50 | 25% |
| Por tipo de oferta | 30 | 15% |
| Aleatorio | 20 | 10% |

### Archivos a Crear

```
database/
├── nlp_gold_set_v1.json        # Gold set
├── test_nlp_gold_set.py        # Test automático
└── generate_nlp_sample.py      # Generador de muestra
```

### Criterios de Aceptación

- [ ] 200+ casos validados
- [ ] Distribución por familia funcional
- [ ] Test automático que mide precisión por campo
- [ ] Baseline documentado

### Prioridad: 🔴 Alta

### Labels: `nlp`, `eval-calidad`, `feature`

### Estimación: 8h (validación manual)

---

## MOL-31: Test Automático NLP

### Contexto
Se necesita script que evalúe NLP pipeline contra gold set y reporte precisión por campo.

### Objetivo
Crear `test_nlp.py` que ejecute evaluación completa.

### Output Esperado

```
=== NLP EVALUATION REPORT ===
Gold Set: nlp_gold_set_v1.json (200 cases)
Pipeline: v8.0

OVERALL METRICS:
  Precision: 91.2%
  Cases passed: 182/200

BY FIELD:
  experiencia_min_anios:  94.5% (189/200)
  nivel_educativo:        88.0% (176/200)
  area_funcional:         92.0% (184/200)
  modalidad:              96.5% (193/200)
  tech_skills:            85.0% (170/200)
  soft_skills:            82.5% (165/200)

BY FAMILY:
  comercial:    93.0% (28/30)
  tecnologia:   89.0% (27/30)
  salud:        91.0% (27/30)
  ...

FAILED CASES:
  1118027662: experiencia_min_anios expected 3, got 5
  1118028376: area_funcional expected admin, got negocios
  ...
```

### Archivos a Crear

```
database/
└── test_nlp.py
```

### Código Referencia

```python
# database/test_nlp.py

import json
from pathlib import Path
from nlp.nlp_pipeline_v8 import NLPPipeline

class NLPEvaluator:
    def __init__(self, gold_set_path: str):
        self.gold_set = self._load_gold_set(gold_set_path)
        self.pipeline = NLPPipeline()
        
    def evaluate(self) -> dict:
        results = {
            "total": len(self.gold_set["cases"]),
            "passed": 0,
            "by_field": {},
            "by_family": {},
            "failed_cases": []
        }
        
        for case in self.gold_set["cases"]:
            predicted = self.pipeline.process(case["raw"])
            case_result = self._compare(case["expected"], predicted)
            
            if case_result["passed"]:
                results["passed"] += 1
            else:
                results["failed_cases"].append({
                    "id": case["id"],
                    "errors": case_result["errors"]
                })
            
            # Agregar a métricas por campo y familia
            self._update_metrics(results, case, case_result)
        
        return results
    
    def _compare(self, expected: dict, predicted: dict) -> dict:
        errors = []
        for field, expected_value in expected.items():
            predicted_value = predicted.get(field)
            if not self._values_match(expected_value, predicted_value):
                errors.append({
                    "field": field,
                    "expected": expected_value,
                    "predicted": predicted_value
                })
        
        return {
            "passed": len(errors) == 0,
            "errors": errors
        }

if __name__ == "__main__":
    evaluator = NLPEvaluator("database/nlp_gold_set_v1.json")
    results = evaluator.evaluate()
    evaluator.print_report(results)
```

### Criterios de Aceptación

- [ ] Script ejecutable: `python database/test_nlp.py`
- [ ] Reporte por campo, familia, y casos fallidos
- [ ] Exit code 0 si >= 90%, 1 si < 90%
- [ ] Integrable en CI/CD

### Prioridad: 🔴 Alta

### Labels: `nlp`, `eval-calidad`, `feature`

### Estimación: 3h

---

## MOL-32: Export NLP a S3

### Contexto
Los datos parseados deben exportarse a S3 para validación colaborativa.

### Objetivo
Crear `export_nlp.py` que sube datos a S3/experiment/nlp/.

### Formato de Export

```json
// S3/experiment/nlp/2025-W50/parsed.json.gz
{
  "version": "nlp-v8.0",
  "exported_at": "2025-12-07T10:00:00Z",
  "total_offers": 800,
  "offers": [
    {
      "id": "1118027662",
      "titulo": "Vendedor Senior B2B",
      "parsed": {
        "experiencia_min_anios": 3,
        "nivel_educativo": "secundario",
        // ... todos los campos NLP
      },
      "nlp_score": 5,
      "nlp_version": "v8.0"
    }
  ]
}
```

### Archivos a Crear

```
exports/
└── export_nlp.py
```

### Criterios de Aceptación

- [ ] Exporta a S3/experiment/nlp/{semana}/
- [ ] Formato JSON comprimido (gzip)
- [ ] Actualiza S3/experiment/nlp/latest.json
- [ ] Ejecutable desde dashboard

### Prioridad: 🔴 Alta

### Labels: `nlp`, `infra`, `feature`

### Estimación: 2h

---

## MOL-33: Sync Validaciones NLP

### Contexto
Los validadores escriben feedback en S3. Necesitamos sincronizar esas validaciones al local.

### Objetivo
Crear `sync_validations.py` que descarga validaciones y actualiza gold set.

### Flujo

```
S3/experiment/nlp/{semana}/validations.json
                │
                ▼
sync_validations.py
                │
                ├── Descarga validaciones nuevas
                ├── Merge con gold set local
                └── Actualiza nlp_gold_set_v1.json
```

### Criterios de Aceptación

- [ ] Descarga validaciones de S3
- [ ] Merge inteligente (no duplicados)
- [ ] Actualiza gold set local
- [ ] Log de cambios

### Prioridad: 🟡 Media

### Labels: `nlp`, `infra`, `feature`

### Estimación: 2h

---

# ÉPICA 3: MATCHING ESCO

---

## MOL-5: Resolver sector_funcion (v8.4)

### Contexto
50% de errores actuales son tipo `sector_funcion`: ofertas matchean a ocupaciones ESCO de sectores completamente diferentes.

**Ejemplos:**
- "Ejecutivo de cuentas" → "Agente de empleo" (debería ser ventas)
- "Account Executive Hunter" → "Reclutador" (debería ser comercial)

**Historial:**
- v8.1: Ajustes nivel jerárquico → No resolvió
- v8.2: 6 familias funcionales → Mejoró categorización
- v8.3: +4 familias → 57.9% → 78.9%

### Objetivo
Alcanzar >= 95% precisión en matching, con <= 1 error sector_funcion.

### Archivos Involucrados

```
database/
├── matching_rules_v84.py       # CREAR (copiar de v83)
├── matching_rules_v83.py       # Referencia
├── gold_set_manual_v1.json     # 19 casos actuales
└── test_gold_set_manual.py     # Actualizar para v84
```

### Estrategia Propuesta

1. **Keywords más específicos por familia:**
   - VENTAS_B2B: "account executive", "hunter", "closer", "sales"
   - RRHH_ESCO: "agente de empleo", "reclutador interno"

2. **Reglas never_confirm:**
   - Si título contiene "ventas/sales" → nunca RRHH
   - Si título contiene "account" sin "payable/receivable" → nunca contabilidad

3. **Boost por contexto:**
   - Si descripción menciona "cuota", "comisión" → boost ventas
   - Si menciona "selección de personal" → boost RRHH

### Criterios de Aceptación

- [ ] Precisión gold set >= 95% (actual: 78.9%)
- [ ] Errores sector_funcion <= 1 (actual: 4)
- [ ] Sin regresiones en casos correctos
- [ ] Documentado en CHANGELOG.md

### Prioridad: 🔴 Alta

### Labels: `matching`, `esco`, `feature`

### Estimación: 6h

---

## MOL-34: Expandir Gold Set Matching (200+ casos)

### Contexto
El gold set actual tiene solo 19 casos. Se necesitan 200+ para evaluación confiable.

### Estrategia de Muestreo

| Familia | Casos | % |
|---------|-------|---|
| comercial | 30 | 15% |
| tecnologia | 25 | 12.5% |
| administracion | 25 | 12.5% |
| salud | 20 | 10% |
| manufactura | 20 | 10% |
| logistica | 20 | 10% |
| educacion | 15 | 7.5% |
| gastronomia | 15 | 7.5% |
| construccion | 15 | 7.5% |
| servicios | 15 | 7.5% |

**Dentro de cada familia:**
- 50% casos score alto (>= 0.70)
- 30% casos score medio (0.50-0.70)
- 20% casos score bajo (< 0.50)

### Archivos a Crear

```
database/
├── matching_gold_set_v2.json   # Gold set expandido
└── generate_matching_sample.py # Generador de muestra
```

### Criterios de Aceptación

- [ ] 200+ casos validados
- [ ] Distribución por familia
- [ ] Distribución por score
- [ ] Formato compatible con test existente

### Prioridad: 🔴 Alta

### Labels: `matching`, `eval-calidad`, `feature`

### Estimación: 8h (validación manual)

---

## MOL-35: Export Matching a S3

### Contexto
Los datos matcheados deben exportarse a S3 para validación.

### Formato de Export

```json
// S3/experiment/matching/2025-W50/matched.json.gz
{
  "version": "matching-v8.3",
  "exported_at": "2025-12-07T10:00:00Z",
  "offers": [
    {
      "id": "1118027662",
      "titulo": "Vendedor Senior B2B",
      "esco_uri": "http://data.europa.eu/esco/occupation/abc123",
      "esco_label": "representante técnico de ventas",
      "isco_code": "3322",
      "match_score": 0.72,
      "familia_funcional": "comercial_ventas",
      "candidates": [
        {"uri": "...", "label": "...", "score": 0.72},
        {"uri": "...", "label": "...", "score": 0.68},
        {"uri": "...", "label": "...", "score": 0.65}
      ]
    }
  ]
}
```

### Criterios de Aceptación

- [ ] Exporta a S3/experiment/matching/{semana}/
- [ ] Incluye top 3 candidatos
- [ ] Formato JSON comprimido
- [ ] Ejecutable desde dashboard

### Prioridad: 🔴 Alta

### Labels: `matching`, `infra`, `feature`

### Estimación: 2h

---

# ÉPICA 4: VALIDACIÓN

---

## MOL-36: Dashboard Admin - Tab Tests

### Contexto
Necesitamos tab para ejecutar tests contra gold sets y ver resultados.

### UI Propuesta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TAB: TESTS                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NLP PIPELINE (v8.0)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Gold Set: nlp_gold_set_v1.json (200 casos)                        │   │
│  │                                                                     │   │
│  │  Última ejecución: 2025-12-07 10:00                                │   │
│  │  Precisión: 91.2% ✅ (umbral: 90%)                                 │   │
│  │                                                                     │   │
│  │  [▶️ Ejecutar Test]  [📊 Ver Detalle]                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MATCHING (v8.3)                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Gold Set: matching_gold_set_v2.json (200 casos)                   │   │
│  │                                                                     │   │
│  │  Última ejecución: 2025-12-07 10:00                                │   │
│  │  Precisión: 78.9% ❌ (umbral: 95%)                                 │   │
│  │                                                                     │   │
│  │  [▶️ Ejecutar Test]  [📊 Ver Detalle]                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  DETALLE (expandible)                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Por Campo:                     Por Familia:                        │   │
│  │  experiencia: 94.5% ████████    comercial:    93.0% ████████        │   │
│  │  educacion:   88.0% ███████     tecnologia:   89.0% ████████        │   │
│  │  modalidad:   96.5% █████████   salud:        91.0% ████████        │   │
│  │  ...                            ...                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CASOS FALLIDOS                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ID          │ Campo/Match      │ Esperado    │ Obtenido           │   │
│  │──────────────┼──────────────────┼─────────────┼────────────────────│   │
│  │ 1118027662   │ experiencia      │ 3 años      │ 5 años             │   │
│  │ 1118028376   │ area_funcional   │ admin       │ negocios           │   │
│  │ ...          │ ...              │ ...         │ ...                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Criterios de Aceptación

- [ ] Muestra estado de ambos tests
- [ ] Indicador visual pass/fail
- [ ] Botón para ejecutar
- [ ] Detalle expandible por campo/familia
- [ ] Lista de casos fallidos

### Prioridad: 🔴 Alta

### Labels: `dashboard`, `eval-calidad`, `feature`

### Estimación: 4h

---

## MOL-37: Dashboard Admin - Tab S3 Sync

### Contexto
Necesitamos tab para exportar datos a S3 y sincronizar validaciones.

### UI Propuesta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TAB: S3 SYNC                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EXPORTAR A S3                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Semana: [2025-W50 ▼]                                              │   │
│  │                                                                     │   │
│  │  ☑️ Exportar NLP (800 ofertas parseadas)                           │   │
│  │  ☑️ Exportar Matching (800 ofertas matcheadas)                     │   │
│  │  ☐ Exportar a Producción (requiere tests pasados)                  │   │
│  │                                                                     │   │
│  │  [▶️ Exportar]                           Estado: Listo             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SINCRONIZAR VALIDACIONES                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Validaciones pendientes en S3: 45                                 │   │
│  │  Última sincronización: 2025-12-06 18:00                           │   │
│  │                                                                     │   │
│  │  [▶️ Sincronizar]                        [📊 Ver Validaciones]     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ESTADO S3                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Bucket: mol-validation-data                                       │   │
│  │  Región: sa-east-1                                                 │   │
│  │                                                                     │   │
│  │  /experiment/nlp/      12 semanas, 9,600 ofertas                   │   │
│  │  /experiment/matching/ 12 semanas, 9,600 ofertas                   │   │
│  │  /production/          48 semanas, 38,400 ofertas                  │   │
│  │  /goldset/             2 archivos                                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Criterios de Aceptación

- [ ] Exportar NLP y Matching a S3
- [ ] Sincronizar validaciones de S3
- [ ] Mostrar estado del bucket
- [ ] Bloquear export producción si tests no pasan

### Prioridad: 🔴 Alta

### Labels: `dashboard`, `infra`, `feature`

### Estimación: 4h

---

## MOL-38: Generate Sample (Muestra Estratificada)

### Contexto
Para validación humana, necesitamos generar muestras estratificadas.

### Especificación

```python
# generate_sample.py

def generate_sample(
    n: int = 90,
    by_family: bool = True,
    by_score: bool = True,
    include_random: float = 0.10
) -> pd.DataFrame:
    """
    Genera muestra estratificada para validación.
    
    Args:
        n: Total de casos
        by_family: Estratificar por familia funcional
        by_score: Estratificar por score
        include_random: Porcentaje aleatorio (control)
    
    Returns:
        DataFrame con ofertas seleccionadas
    """
```

### Distribución (90 casos)

| Estrato | Casos | % |
|---------|-------|---|
| Por familia (10 familias × 5) | 50 | 56% |
| Score bajo (< 0.50) | 15 | 17% |
| Score medio (0.50-0.70) | 15 | 17% |
| Aleatorio (control) | 10 | 11% |

### Criterios de Aceptación

- [ ] Genera muestra con distribución correcta
- [ ] Exporta a JSON para validación
- [ ] No incluye casos ya validados
- [ ] Reproducible con seed

### Prioridad: 🟡 Media

### Labels: `eval-calidad`, `feature`

### Estimación: 2h

---

## MOL-39: Dashboard Validación (Vercel)

### Contexto
Dashboard web para que los 3 admins validen ofertas remotamente.

### Stack

- Next.js 14
- TypeScript
- Tailwind CSS
- AWS SDK (S3)

### Funcionalidades

1. **Login simple** (3 usuarios predefinidos)
2. **Lista de ofertas** pendientes de validación
3. **Vista de validación NLP** (campo por campo)
4. **Vista de validación Matching** (ocupación correcta)
5. **Submit** → escribe a S3

### UI Validación NLP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VALIDACIÓN NLP - Oferta 1118027662                    [Anterior] [Siguiente]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OFERTA ORIGINAL                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Título: Vendedor Senior B2B                                        │   │
│  │  Empresa: Confidencial                                              │   │
│  │                                                                     │   │
│  │  Descripción:                                                       │   │
│  │  Buscamos vendedor con 3+ años de experiencia en ventas B2B.       │   │
│  │  Requisitos: Secundario completo, manejo de CRM...                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CAMPOS EXTRAÍDOS                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Campo              │ Valor extraído  │ Validación                 │   │
│  │─────────────────────┼─────────────────┼────────────────────────────│   │
│  │  experiencia_anios  │ 3               │ ✅ Correcto  ❌ Incorrecto │   │
│  │  nivel_educativo    │ secundario      │ ✅ Correcto  ❌ Incorrecto │   │
│  │  area_funcional     │ ventas          │ ✅ Correcto  ❌ Incorrecto │   │
│  │  tech_skills        │ [CRM]           │ ✅ Correcto  ❌ Incorrecto │   │
│  │  ...                │ ...             │                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Comentario (opcional): [________________________________]                 │
│                                                                             │
│  [💾 Guardar y Siguiente]                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Criterios de Aceptación

- [ ] Deploy en Vercel
- [ ] Login funcional (3 usuarios)
- [ ] Validación NLP campo por campo
- [ ] Validación Matching con candidatos
- [ ] Escribe a S3 correctamente
- [ ] Responsive (mobile friendly)

### Prioridad: 🟡 Media

### Labels: `dashboard`, `feature`

### Estimación: 12h

---

## MOL-40: Export Producción

### Contexto
Cuando NLP >= 90% y Matching >= 95%, exportar a S3/production/.

### Formato Parquet

```python
# Columnas principales
columns = [
    "id", "titulo", "empresa", "provincia", "localidad",
    "fecha_publicacion", "url_fuente", "portal",
    
    # NLP
    "experiencia_min_anios", "nivel_educativo", "modalidad",
    "area_funcional", "nivel_seniority", "tech_skills", "soft_skills",
    
    # Matching
    "esco_uri", "esco_label", "isco_code", "match_score",
    "familia_funcional",
    
    # ESCO Skills
    "esco_essential_skills", "esco_optional_skills",
    "esco_essential_knowledge", "esco_optional_knowledge",
    
    # Permanencia
    "estado_oferta", "dias_publicada", "categoria_permanencia"
]
```

### Estructura S3

```
S3/production/
├── current/
│   └── ofertas.parquet          # Lambda lee esto
├── history/
│   └── year=2025/
│       ├── week=49/ofertas.parquet
│       └── week=50/ofertas.parquet
└── metadata.json
```

### Criterios de Aceptación

- [ ] Solo exporta si tests pasan
- [ ] Formato Parquet particionado
- [ ] Actualiza /current/ y /history/
- [ ] Actualiza metadata.json
- [ ] Log de export

### Prioridad: 🔴 Alta

### Labels: `infra`, `feature`

### Estimación: 3h

---

# ÉPICA 5: DASHBOARDS

---

## MOL-41: Dashboard Admin - App Principal

### Contexto
App Streamlit principal que integra todos los tabs.

### Estructura

```python
# dashboards/admin/app.py

import streamlit as st
from tabs import scraping_tab, pipeline_tab, tests_tab, s3_tab, logs_tab

st.set_page_config(
    page_title="MOL Admin",
    page_icon="📊",
    layout="wide"
)

# Sidebar con navegación
tab = st.sidebar.radio(
    "Navegación",
    ["Scraping", "Pipeline", "Tests", "S3 Sync", "Logs"]
)

# Render tab seleccionado
if tab == "Scraping":
    scraping_tab.render()
elif tab == "Pipeline":
    pipeline_tab.render()
# ...
```

### Criterios de Aceptación

- [ ] App funcional con 5 tabs
- [ ] Navegación por sidebar
- [ ] Persistencia de estado entre tabs
- [ ] Ejecutable: `streamlit run dashboards/admin/app.py`

### Prioridad: 🔴 Alta

### Labels: `dashboard`, `feature`

### Estimación: 2h

---

## MOL-42: Dashboard Admin - Tab Pipeline

### Contexto
Tab para ejecutar NLP y Matching sobre ofertas.

### UI Propuesta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TAB: PIPELINE                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OFERTAS PENDIENTES                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Sin procesar NLP:     847                                          │   │
│  │  Sin procesar Matching: 123                                         │   │
│  │  Listas para producción: 9,441                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  EJECUTAR PIPELINE                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Batch size: [100 ▼]                                               │   │
│  │                                                                     │   │
│  │  ☑️ Ejecutar NLP                                                   │   │
│  │  ☑️ Ejecutar Matching                                              │   │
│  │  ☐ Solo ofertas nuevas                                             │   │
│  │                                                                     │   │
│  │  [▶️ Ejecutar]                                                     │   │
│  │                                                                     │   │
│  │  Progreso: ████████████░░░░░░░░ 60% (60/100)                       │   │
│  │  Tiempo estimado: 2:30 restantes                                   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ÚLTIMAS EJECUCIONES                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Fecha       │ Tipo     │ Ofertas │ Tiempo  │ Estado              │   │
│  │──────────────┼──────────┼─────────┼─────────┼─────────────────────│   │
│  │  07/12 10:00 │ NLP      │ 100     │ 4:32    │ ✅ Completado       │   │
│  │  07/12 10:05 │ Matching │ 100     │ 1:15    │ ✅ Completado       │   │
│  │  06/12 18:00 │ Full     │ 800     │ 45:00   │ ✅ Completado       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Criterios de Aceptación

- [ ] Muestra ofertas pendientes
- [ ] Ejecuta NLP y/o Matching
- [ ] Barra de progreso
- [ ] Historial de ejecuciones
- [ ] Manejo de errores

### Prioridad: 🟡 Media

### Labels: `dashboard`, `feature`

### Estimación: 4h

---

## MOL-43: Dashboard Producción (Vercel)

### Contexto
Dashboard para analistas OEDE con datos limpios.

### Stack

- Next.js 14
- TypeScript
- Tailwind CSS
- Recharts (gráficos)
- AWS Lambda (backend)

### 3 Pestañas

Ver DASHBOARD_WIREFRAMES.md para wireframes completos.

| Tab | Contenido |
|-----|-----------|
| Panorama General | KPIs + Evolución + Top 10 ocupaciones |
| Requerimientos | 4 tortas + Top 20 skills |
| Ofertas Laborales | Tabla explorable |

### Criterios de Aceptación

- [ ] Deploy en Vercel
- [ ] 3 tabs funcionales
- [ ] Filtros globales operativos
- [ ] Gráficos con descarga Excel/CSV
- [ ] Responsive
- [ ] Sin siglas técnicas (CIUO, ESCO)

### Prioridad: 🟡 Media

### Labels: `dashboard`, `feature`

### Estimación: 16h

---

## MOL-44: Lambda API Backend

### Contexto
API serverless para dashboard de producción.

### Endpoints

```
GET /ofertas
  ?territorio=nacional|provincial|localidad
  &periodo=semana|mes|año
  &permanencia=todas|baja|media|alta
  &familia=comercial|tecnologia|...
  &page=1&limit=20

GET /metricas/panorama
  → KPIs, evolución, top 10

GET /metricas/requerimientos
  → Distribuciones edad, género, educación, skills

GET /ocupaciones/arbol
  → Árbol jerárquico de ocupaciones

GET /export
  ?format=csv|xlsx
  → Descarga de datos filtrados
```

### Stack

- Python 3.11
- PyArrow (leer Parquet)
- Pandas (filtros)
- API Gateway + Lambda

### Criterios de Aceptación

- [ ] 4 endpoints funcionales
- [ ] Lee de S3/production/current/ofertas.parquet
- [ ] Responde en < 500ms
- [ ] Free tier AWS
- [ ] CORS configurado

### Prioridad: 🟡 Media

### Labels: `api`, `infra`, `feature`

### Estimación: 6h

---

# ÉPICA 6: INFRAESTRUCTURA

---

## MOL-23: Backup Automático SQLite

### Estado: ✅ Completado

Script de backup ya implementado.

---

## MOL-45: Dashboard Admin - Tab Logs

### Contexto
Tab para ver logs de ejecuciones.

### UI Propuesta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TAB: LOGS                                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Filtros: [Todos ▼] [Últimas 24h ▼] [🔍 Buscar...]                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  2025-12-07 10:05:32 [INFO] Matching completado: 100 ofertas        │   │
│  │  2025-12-07 10:00:15 [INFO] NLP completado: 100 ofertas             │   │
│  │  2025-12-07 08:00:00 [INFO] Scraping iniciado                       │   │
│  │  2025-12-07 08:45:23 [INFO] Scraping completado: 701 nuevas         │   │
│  │  2025-12-07 08:46:00 [INFO] Detección bajas: 0 bajas                │   │
│  │  2025-12-06 18:00:00 [WARN] S3 sync: timeout, reintentando          │   │
│  │  2025-12-06 18:00:15 [INFO] S3 sync completado                      │   │
│  │  ...                                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [Exportar Logs]  [Limpiar Logs Antiguos]                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Criterios de Aceptación

- [ ] Muestra logs de todas las operaciones
- [ ] Filtros por tipo y fecha
- [ ] Búsqueda de texto
- [ ] Exportar a archivo
- [ ] Colores por nivel (INFO/WARN/ERROR)

### Prioridad: ⚪ Baja

### Labels: `dashboard`, `infra`, `feature`

### Estimación: 2h

---

## MOL-46: Alertas Email/Slack

### Contexto
Notificaciones cuando algo falla o requiere atención.

### Eventos a Notificar

| Evento | Canal | Prioridad |
|--------|-------|-----------|
| Scraping fallido | Email + Slack | Alta |
| Precisión < umbral | Email | Alta |
| Export S3 fallido | Email | Alta |
| Nuevas validaciones | Slack | Baja |

### Criterios de Aceptación

- [ ] Integración con SendGrid (email)
- [ ] Integración con Slack webhook
- [ ] Configurable desde dashboard
- [ ] No spam (rate limit)

### Prioridad: ⚪ Baja

### Labels: `infra`, `feature`

### Estimación: 3h

---

## MOL-47: CI/CD GitHub Actions

### Contexto
Automatizar tests en cada PR.

### Workflow

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python database/test_nlp.py
      - run: python database/test_gold_set_manual.py
```

### Criterios de Aceptación

- [ ] Workflow ejecuta en cada PR
- [ ] Falla si precisión < umbral
- [ ] Badge en README

### Prioridad: ⚪ Baja

### Labels: `infra`, `feature`

### Estimación: 2h

---

## MOL-48: Sistema de Métricas y Logging para Experimentos

### Contexto
Actualmente no hay forma de comparar versiones del pipeline ni medir el impacto de cambios. Los resultados están dispersos:
- Scores en `ofertas_esco_matching` (SQLite) - solo score final
- NLP en `validacion_v7` (SQLite) - sin timestamps
- Gold set en consola - no persiste
- Sin timing por componente

**Problema:** No podemos saber si ESCO-XLM reranker aporta valor, ni comparar v8.2 vs v8.3.

### Objetivo
Crear sistema centralizado para persistir y comparar resultados de experimentos.

### Archivos a Crear

```
metrics/
├── experiments.json          # Resultados de experimentos
├── gold_set_history.json     # Histórico de runs del gold set
└── timing_logs.jsonl         # Tiempos por componente (append)

database/
└── experiment_logger.py      # Clase para logging
```

### Especificación

```python
# database/experiment_logger.py

import json
from datetime import datetime
from pathlib import Path
import time
from contextlib import contextmanager

class ExperimentLogger:
    def __init__(self, metrics_dir="metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(exist_ok=True)
        self.experiments_file = self.metrics_dir / "experiments.json"
        self.timing_file = self.metrics_dir / "timing_logs.jsonl"
    
    def log_experiment(self, name: str, config: dict, results: dict):
        """Guarda resultado de un experimento"""
        experiments = self._load_experiments()
        
        key = f"{datetime.now().strftime('%Y-%m-%d_%H%M')}_{name}"
        experiments[key] = {
            "config": config,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        self._save_experiments(experiments)
        return key
    
    @contextmanager
    def timer(self, component: str):
        """Context manager para medir tiempo de un componente"""
        start = time.perf_counter()
        yield
        duration_ms = (time.perf_counter() - start) * 1000
        self.log_timing(component, duration_ms)
    
    def log_timing(self, component: str, duration_ms: float):
        """Guarda timing de un componente"""
        with open(self.timing_file, "a") as f:
            f.write(json.dumps({
                "component": component,
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now().isoformat()
            }) + "\n")
    
    def get_timing_summary(self, last_n: int = 100) -> dict:
        """Obtiene resumen de tiempos por componente"""
        timings = {}
        if not self.timing_file.exists():
            return timings
        
        lines = self.timing_file.read_text().strip().split("\n")[-last_n:]
        for line in lines:
            entry = json.loads(line)
            comp = entry["component"]
            if comp not in timings:
                timings[comp] = []
            timings[comp].append(entry["duration_ms"])
        
        return {
            comp: {
                "avg_ms": sum(vals) / len(vals),
                "min_ms": min(vals),
                "max_ms": max(vals),
                "count": len(vals)
            }
            for comp, vals in timings.items()
        }
    
    def compare_experiments(self, exp1_key: str, exp2_key: str) -> dict:
        """Compara dos experimentos"""
        experiments = self._load_experiments()
        e1 = experiments.get(exp1_key, {})
        e2 = experiments.get(exp2_key, {})
        
        if not e1 or not e2:
            return {"error": "Experimento no encontrado"}
        
        r1 = e1.get("results", {})
        r2 = e2.get("results", {})
        
        return {
            "exp1": exp1_key,
            "exp2": exp2_key,
            "precision_diff": r2.get("precision", 0) - r1.get("precision", 0),
            "exp1_precision": r1.get("precision"),
            "exp2_precision": r2.get("precision"),
            "exp1_config": e1.get("config"),
            "exp2_config": e2.get("config")
        }
    
    def _load_experiments(self) -> dict:
        if self.experiments_file.exists():
            return json.loads(self.experiments_file.read_text())
        return {}
    
    def _save_experiments(self, data: dict):
        self.experiments_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
```

### Ejemplo de Uso

```python
# En test_gold_set_manual.py
from database.experiment_logger import ExperimentLogger

logger = ExperimentLogger()

# Al final del test:
logger.log_experiment(
    name="gold_set_matching_v83",
    config={
        "matching_version": "v8.3",
        "gold_set_version": "v1",
        "gold_set_size": 19,
        "use_reranker": True
    },
    results={
        "precision": 0.789,
        "errores_por_tipo": {
            "sector_funcion": 4,
            "nivel_jerarquico": 2
        },
        "casos_fallidos": ["1118027276", "1118028887"]
    }
)

# En match_ofertas_multicriteria.py
with logger.timer("bge_m3_embedding"):
    embeddings = model.encode(texto)

with logger.timer("esco_xlm_rerank"):
    reranked = reranker.rerank(candidates)
```

### Formato experiments.json

```json
{
  "2025-12-07_1430_gold_set_matching_v83": {
    "config": {
      "matching_version": "v8.3",
      "gold_set_version": "v1",
      "gold_set_size": 19,
      "use_reranker": true
    },
    "results": {
      "precision": 0.789,
      "errores_por_tipo": {
        "sector_funcion": 4,
        "nivel_jerarquico": 2
      }
    },
    "timestamp": "2025-12-07T14:30:00"
  },
  "2025-12-07_1445_gold_set_matching_v83_sin_reranker": {
    "config": {
      "matching_version": "v8.3",
      "gold_set_version": "v1", 
      "gold_set_size": 19,
      "use_reranker": false
    },
    "results": {
      "precision": 0.785,
      "errores_por_tipo": {
        "sector_funcion": 4,
        "nivel_jerarquico": 2
      }
    },
    "timestamp": "2025-12-07T14:45:00"
  }
}
```

### Criterios de Aceptación

- [ ] `database/experiment_logger.py` creado
- [ ] `metrics/` directorio con .gitkeep
- [ ] `test_gold_set_manual.py` usa logger automáticamente
- [ ] Timing integrado en `match_ofertas_multicriteria.py`
- [ ] Script `compare_experiments.py` para comparar 2 runs
- [ ] Documentación de uso en CLAUDE.md

### Prioridad: 🔴 Alta (prerequisito para experimentos)

### Labels: `infra`, `eval-calidad`, `feature`

### Estimación: 3h

---

## MOL-49: Spike - Evaluar si ESCO-XLM Reranker Aporta Valor

### Contexto
El pipeline actual usa ESCO-XLM-RoBERTa-Large como re-ranker, pero hay evidencia de que podría ser subóptimo:

**Hallazgos del análisis:**
1. El modelo se usa con **mean pooling para embeddings**, pero fue diseñado para **clasificación**
2. En StackOverflow reportan que este approach "no funciona bien"
3. Solo aporta 30% al score final (70% BGE-M3 + 30% rerank)
4. Agrega ~480ms por oferta (10 candidatos × ~50ms)

**Uso actual (match_ofertas_multicriteria.py:163-167):**
```python
hidden_states = outputs.last_hidden_state
mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
sum_embeddings = torch.sum(hidden_states * mask_expanded, dim=1)
embedding = sum_embeddings / sum_mask  # Mean pooling ← POSIBLEMENTE SUBÓPTIMO
```

### Objetivo
Determinar si remover ESCO-XLM reranker mantiene precisión similar con menos complejidad.

### Experimento

**Test A:** Pipeline actual (baseline)
- BGE-M3 → Top 10 → ESCO-XLM rerank → Top 3 → Rules

**Test B:** Pipeline sin reranker
- BGE-M3 → Top 3 directo → Rules

### Metodología

1. Ejecutar gold set con pipeline A (ya tenemos baseline: 78.9%)
2. Modificar temporalmente para deshabilitar reranker
3. Ejecutar gold set con pipeline B
4. Comparar: precisión, errores por tipo, timing

### Código de Modificación

```python
# match_ofertas_multicriteria.py

# Agregar flag:
USE_RERANKER = True  # Cambiar a False para experimento

# En la función de matching:
if USE_RERANKER:
    candidatos = self.rerank_con_esco_xlm(candidatos_bge, oferta_texto)
else:
    candidatos = candidatos_bge[:3]  # Top 3 directo de BGE-M3
```

### Criterios de Éxito

| Escenario | Decisión |
|-----------|----------|
| B precision >= A - 2% | Remover reranker (simplificar) |
| B precision < A - 2% | Mantener reranker |
| B precision > A | Definitivamente remover |

### Resultados a Documentar

- [ ] Precisión A vs B
- [ ] Errores por tipo A vs B
- [ ] Timing A vs B
- [ ] Casos específicos que cambian
- [ ] Decisión Go/NoGo

### Criterios de Aceptación

- [ ] Experimento ejecutado con ambas configuraciones
- [ ] Resultados guardados en `metrics/experiments.json`
- [ ] Documentación de decisión
- [ ] Si NoGo: cerrar issue
- [ ] Si Go: crear MOL-XX para implementar cambio

### Dependencias

- MOL-48 (Sistema de métricas) debe estar completado

### Prioridad: 🔴 Alta

### Labels: `spike`, `matching`, `eval-calidad`

### Estimación: 2h

---

## MOL-50: Spike - Evaluar BGE-M3 Hybrid Retrieval

### Contexto
BGE-M3 actualmente solo usa **dense retrieval**, pero soporta 3 modos:
- Dense: Embeddings semánticos (actual)
- Sparse: Lexical matching (tipo BM25 mejorado)
- Multi-vector: ColBERT-style

**Oportunidad:** Hybrid (dense + sparse) podría mejorar precisión en términos técnicos exactos como "Excel", "SAP", "Python".

### Estado Actual

```python
# Solo dense:
embeddings = model.encode(texts)
similarity = cosine_similarity(query_emb, doc_emb)
```

### Propuesta

```python
# Hybrid:
output = model.encode(texts, return_dense=True, return_sparse=True)
dense_score = cosine_similarity(query_dense, doc_dense)
sparse_score = compute_sparse_score(query_sparse, doc_sparse)
final_score = 0.7 * dense_score + 0.3 * sparse_score
```

### Experimento

1. Modificar embedding para retornar dense + sparse
2. Implementar scoring híbrido
3. Evaluar contra gold set
4. Comparar precisión y timing

### Criterios de Éxito

| Métrica | Baseline | Objetivo |
|---------|----------|----------|
| Precisión | 78.9% | >= 82% |
| Timing | ~100ms | <= 150ms |

### Criterios de Aceptación

- [ ] Implementar hybrid retrieval
- [ ] Evaluar con gold set
- [ ] Documentar resultados
- [ ] Decisión Go/NoGo
- [ ] Si Go: crear issue para integrar

### Dependencias

- MOL-48 (Sistema de métricas)

### Prioridad: 🟡 Media

### Labels: `spike`, `matching`, `embeddings`

### Estimación: 4h

---

## MOL-51: Spike - Evaluar GLiNER para Extracción de Skills

### Contexto
Qwen2.5:14b tarda 2-5 segundos por oferta para extraer 8 campos semánticos. GLiNER es un modelo compacto (~200M params) que:
- Supera a ChatGPT en zero-shot NER
- Soporta español, francés, alemán, italiano, portugués
- Procesa en ~100ms

**Papers relevantes:**
- "GLiNER: Generalist Model for Named Entity Recognition" (NAACL 2024)
- Skill-LLM alcanzó 64.8% F1 en SkillSpan dataset

### Riesgo
GLiNER no está entrenado específicamente en job market español. Hay que validar.

### Experimento

```python
from gliner import GLiNER

model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

# Labels para job postings
labels = [
    "skill técnico", 
    "skill blanda", 
    "tecnología", 
    "certificación",
    "beneficio",
    "requisito"
]

# Extraer entidades
entities = model.predict_entities(descripcion_oferta, labels, threshold=0.5)
```

### Metodología

1. Seleccionar 50 ofertas con skills validados manualmente
2. Extraer skills con GLiNER
3. Extraer skills con Qwen2.5 (baseline)
4. Comparar: precision, recall, F1
5. Comparar timing

### Criterios de Éxito

| Métrica | Qwen2.5 (baseline) | GLiNER objetivo |
|---------|-------------------|-----------------|
| F1 skills | ~90% | >= 85% |
| Timing/oferta | 2-5s | < 500ms |

**Trade-off aceptable:** -5% F1 si ganamos 10x velocidad.

### Criterios de Aceptación

- [ ] Dataset de 50 ofertas con skills anotados
- [ ] Benchmark Qwen2.5 vs GLiNER
- [ ] Métricas: precision, recall, F1 por tipo de skill
- [ ] Timing comparativo
- [ ] Análisis de errores
- [ ] Decisión Go/NoGo

### Dependencias

- MOL-48 (Sistema de métricas)
- Anotar 50 ofertas con skills (puede ser subset del gold set NLP)

### Prioridad: 🟡 Media

### Labels: `spike`, `nlp`, `eval-calidad`

### Estimación: 6h

---

## MOL-55: Agregar Funciones Ejecutables al Dashboard Admin

### Contexto
El Dashboard Admin (MOL-41) actualmente muestra datos pero no permite ejecutar acciones. El objetivo es convertirlo en un **centro de control** donde el administrador pueda operar el sistema sin usar terminal.

### Objetivo
Agregar botones y controles que ejecuten las funciones principales del sistema.

---

### FASE 1: Funciones Críticas (Prioridad Alta)

#### Tab Scraping
| Acción | UI | Comando |
|--------|-----|---------|
| Iniciar scraping | 🟢 Botón "Iniciar Scraping" | `run_scheduler.py --test` |
| Detectar bajas | 🔵 Botón "Detectar Bajas" | `detectar_bajas_integrado.py` |
| Ver últimas ofertas | Tabla expandible | Query SQLite últimas 50 |

#### Tab Pipeline
| Acción | UI | Comando |
|--------|-----|---------|
| Procesar lote NLP | 🟢 Botón "Procesar 100" | `process_nlp_from_db_v7.py --limit 100` |
| Ver progreso | Barra de progreso | Query ofertas por versión |
| Detener proceso | 🔴 Botón "Detener" | Kill subprocess |

#### Tab Tests
| Acción | UI | Comando |
|--------|-----|---------|
| Ejecutar Gold Set | 🟢 Botón "Correr Test" | `test_gold_set_manual.py` |
| Ver resultados | Tabla con casos | Lee gold_set_history.json |

**Estimación Fase 1:** 4h

---

### FASE 2: Validación y Exploración (Prioridad Media)

#### Tab Pipeline
| Acción | UI | Comando |
|--------|-----|---------|
| Ver oferta específica | Input ID + 🔍 "Ver" | Query SQLite + mostrar JSON |
| Reprocesar oferta | Input ID + 🔄 "Reprocesar" | NLP en 1 oferta |
| Procesar todo | 🟠 Botón (con confirmación) | Sin límite |

#### Tab Tests
| Acción | UI | Comando |
|--------|-----|---------|
| Probar oferta individual | Input ID + 🧪 "Testear" | Matching de 1 oferta |
| Ver caso fallido | Select dropdown + "Detalles" | Muestra expected vs actual |
| Agregar al Gold Set | Input ID + ocupación + ➕ | Agrega a JSON |
| Comparar experimentos | 2 dropdowns + 📊 "Comparar" | Diff de métricas |

**Estimación Fase 2:** 6h

---

### FASE 3: S3 y Sistema (Prioridad Baja)

#### Tab S3 Sync
| Acción | UI | Comando |
|--------|-----|---------|
| Export NLP a S3 | 📤 Botón "Exportar NLP" | Upload parsed.json.gz |
| Export Matching a S3 | 📤 Botón "Exportar Matching" | Upload matched.json.gz |
| Export Producción | 📤 Botón (bloqueado si tests < 90%) | Upload parquet |
| Sync validaciones | 📥 Botón "Descargar" | Download de S3 |
| Ver estado bucket | 🔄 Botón "Refresh" | Lista S3 |

#### Tab Logs
| Acción | UI | Comando |
|--------|-----|---------|
| Filtrar por componente | Dropdown | Filtra timing_logs |
| Exportar métricas | 📥 Botón "Descargar CSV" | Genera CSV |
| Limpiar logs viejos | 🗑️ Botón "Limpiar > 30d" | Borra archivos |

#### Sidebar Global
| Acción | UI | Función |
|--------|-----|---------|
| Estado del sistema | Indicador 🟢/🔴 | Verifica servicios |
| Proceso en background | Texto + spinner | Muestra qué corre |
| Backup BD | 💾 Botón "Backup" | Copia SQLite |
| Detener todo | 🔴 Botón emergencia | Kill all |

**Estimación Fase 3:** 6h

---

### Implementación Técnica

```python
# Patrón para ejecutar comandos
import subprocess
import streamlit as st

def ejecutar_comando(comando: list, descripcion: str):
    """Ejecuta comando y muestra resultado en Streamlit"""
    with st.spinner(f"Ejecutando {descripcion}..."):
        try:
            result = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            if result.returncode == 0:
                st.success(f"✅ {descripcion} completado")
                with st.expander("Ver output"):
                    st.code(result.stdout[-2000:])
            else:
                st.error(f"❌ Error en {descripcion}")
                st.code(result.stderr)
        except subprocess.TimeoutExpired:
            st.warning("⏱️ Proceso tomando mucho tiempo, corre en background")
```

```python
# Para procesos largos (background)
import threading

def run_in_background(comando, log_file):
    """Ejecuta en background sin bloquear UI"""
    def _run():
        with open(log_file, 'w') as f:
            subprocess.run(comando, stdout=f, stderr=f)
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    st.session_state['background_process'] = {
        'comando': comando,
        'log_file': log_file,
        'thread': thread
    }
```

---

### Criterios de Aceptación

**Fase 1:**
- [ ] Botón scraping ejecuta y muestra resultado
- [ ] Botón NLP procesa 100 ofertas
- [ ] Botón test corre gold set y muestra precisión
- [ ] Indicador de proceso en background

**Fase 2:**
- [ ] Input para ver/reprocesar oferta específica
- [ ] Probar matching de 1 oferta
- [ ] Agregar caso al gold set desde UI
- [ ] Comparar 2 experimentos

**Fase 3:**
- [ ] Exports a S3 funcionando
- [ ] Filtros en logs
- [ ] Backup de BD
- [ ] Botón emergencia

---

### Prioridad: 🔴 Alta (Fase 1), 🟡 Media (Fase 2), ⚪ Baja (Fase 3)

### Labels: `dashboard`, `feature`, `admin`

### Estimación Total: 16h (4h + 6h + 6h)

### Dependencias
- MOL-41 ✅ (Dashboard base creado)

---

## MOL-56: Sistema de Optimización de Keywords

### Contexto
El scraping usa 1,148 keywords pero:
- 478 (41%) no traen resultados
- 6 son muy genéricos (traen >9,000 ofertas sin filtrar)
- No hay forma de medir el impacto de cambios
- No hay versionado ni trazabilidad

### Objetivo
Crear sistema completo para analizar, proponer, versionar y medir mejoras en keywords.

---

### Componentes

#### 1. Estructura de Versionado (1h)

```
data/config/
├── master_keywords.json           # Versión activa
├── keywords_history/
│   ├── v3.2_2025-11-15.json      # Versiones anteriores
│   ├── v3.3_2025-12-08.json
│   └── changelog.json             # Registro de cambios
└── keywords_proposals/
    └── v3.3_proposal.json         # Propuestas pendientes
```

#### 2. Clase KeywordOptimizer (3h)

```python
# database/keyword_optimizer.py

class KeywordOptimizer:
    def analyze(self) -> dict:
        """Analiza keywords_performance y retorna métricas"""
        pass
    
    def propose_changes(self, analysis: dict) -> dict:
        """Genera propuesta de cambios con justificación"""
        pass
    
    def apply_version(self, version: str, author: str):
        """Aplica propuesta: backup + cambios + changelog"""
        pass
    
    def compare_versions(self, v1: str, v2: str) -> dict:
        """Compara métricas entre versiones"""
        pass
```

#### 3. Tab Dashboard Keywords (3h)

Mostrar:
- Resumen: total keywords, sin uso, genéricos, tasa novedad
- Tabla keywords problemáticos
- Top 10 eficientes
- Historial de versiones con métricas
- Comparador de versiones

#### 4. CLI del Optimizer (1h)

```bash
python -m database.keyword_optimizer analyze
python -m database.keyword_optimizer propose --output v3.3
python -m database.keyword_optimizer apply v3.3 --author "gerardo"
python -m database.keyword_optimizer compare v3.1 v3.2
```

---

### Ciclo de Uso

```
1. ANALIZAR (Dashboard) → Ver métricas, identificar problemas
2. PROPONER (Claude Code) → "Analiza keywords y propone v3.3"
3. REVISAR (Admin) → Aprobar o ajustar propuesta
4. APLICAR (Script) → Backup automático + changelog
5. MEDIR (Dashboard) → Comparar versiones post-scraping
```

---

### Criterios de Aceptación

- [ ] Estructura de versionado creada
- [ ] KeywordOptimizer con analyze/propose/apply/compare
- [ ] CLI funcional
- [ ] Tab en dashboard con métricas + historial
- [ ] Documentación del proceso
- [ ] Al menos una optimización v3.3 aplicada y medida

### Prioridad: 🟡 Media

### Labels: `scraping`, `optimization`, `dashboard`

### Estimación: 8h

### Dependencias
- MOL-41 ✅ (Dashboard base)
- keywords_performance en BD ✅

---

## MOL-52: Documentar Arquitectura de Modelos LLM/ML

### Contexto
No existe documentación clara de cómo funcionan los modelos y cómo interactúan.

### Objetivo
Crear documento técnico que explique la arquitectura actual.

### Contenido a Documentar

```markdown
# Arquitectura de Modelos LLM/ML - MOL

## 1. Inventario de Modelos

| Modelo | Tipo | Parámetros | Uso | Timing |
|--------|------|------------|-----|--------|
| Qwen2.5:14b | LLM | 14B | NLP extraction | 2-5s/oferta |
| BGE-M3 | Embeddings | ~560M | Retrieval semántico | ~100ms/batch |
| ChromaDB | Vector DB | - | Storage ESCO | Disk-based |

## 2. Pipeline NLP (3 capas)

- Capa 0: Regex (70% campos, 100% precisión)
- Capa 1: Qwen2.5 (30% campos, temp=0.0, top_p=0.1)
- Capa 2: Anti-alucinación (substring matching)

## 3. Pipeline Matching (3 pasos) - ACTUALIZADO

- Paso 1: BGE-M3 → Top 3 candidatos (sin reranker)
- Paso 2: Score skills (threshold 0.50)
- Paso 3: Pesos dinámicos + rules v8.3

Nota: ESCO-XLM reranker REMOVIDO (MOL-49 demostró que perjudicaba precisión)

## 4. Pesos Dinámicos

| Coverage | Título | Skills | Descripción |
|----------|--------|--------|-------------|
| >= 80% | 50% | 40% | 10% |
| 40-80% | 60% | 30% | 10% |
| < 40% | 85% | 0% | 15% |
```

### Archivos a Crear

- `docs/ARQUITECTURA_MODELOS.md`

### Criterios de Aceptación

- [ ] Documento completo con diagramas
- [ ] Thresholds y configuración documentados
- [ ] Documentar decisión de remover ESCO-XLM (spike MOL-49)
- [ ] Referencias a archivos de código
- [ ] Integrado en CLAUDE.md

### Prioridad: ⚪ Baja

### Labels: `docs`, `nlp`, `matching`

### Estimación: 2h

---

# RESUMEN DE PRIORIDADES

## 🔴 Alta Prioridad (Implementar Primero)

| Issue | Título | Épica | Estimación |
|-------|--------|-------|------------|
| MOL-48 | Sistema de Métricas y Logging | Infra | 3h |
| MOL-27 | Dashboard Admin - Tab Scraping | Scraping | 4h |
| MOL-30 | Gold Set NLP (200+ casos) | NLP | 8h |
| MOL-31 | Test Automático NLP | NLP | 3h |
| MOL-32 | Export NLP a S3 | NLP | 2h |
| MOL-5 | Resolver sector_funcion (v8.4) | Matching | 6h |
| MOL-34 | Expandir Gold Set Matching | Matching | 8h |
| MOL-35 | Export Matching a S3 | Matching | 2h |
| MOL-49 | Spike - Evaluar ESCO-XLM Reranker | Matching | 2h |
| MOL-36 | Dashboard Admin - Tab Tests | Validación | 4h |
| MOL-37 | Dashboard Admin - Tab S3 Sync | Validación | 4h |
| MOL-40 | Export Producción | Validación | 3h |
| MOL-41 | Dashboard Admin - App Principal | Dashboards | 2h |
| MOL-55 | Funciones Ejecutables Dashboard (Fase 1) | Dashboards | 4h |

**Total Alta Prioridad:** 55h

## 🟡 Media Prioridad

| Issue | Título | Épica | Estimación |
|-------|--------|-------|------------|
| MOL-28 | Activar Scraper ZonaJobs | Scraping | 3h |
| MOL-29 | Deduplicación Cross-Portal | Scraping | 4h |
| MOL-33 | Sync Validaciones NLP | NLP | 2h |
| MOL-38 | Generate Sample | Validación | 2h |
| MOL-39 | Dashboard Validación (Vercel) | Validación | 12h |
| MOL-42 | Dashboard Admin - Tab Pipeline | Dashboards | 4h |
| MOL-43 | Dashboard Producción (Vercel) | Dashboards | 16h |
| MOL-44 | Lambda API Backend | Dashboards | 6h |
| MOL-56 | Sistema Optimización Keywords | Scraping | 8h |

**Total Media Prioridad:** 57h

## ⚪ Baja Prioridad

| Issue | Título | Épica | Estimación |
|-------|--------|-------|------------|
| MOL-45 | Dashboard Admin - Tab Logs | Infra | 2h |
| MOL-46 | Alertas Email/Slack | Infra | 3h |
| MOL-47 | CI/CD GitHub Actions | Infra | 2h |
| MOL-50 | Spike - BGE-M3 Hybrid Retrieval | Matching | 4h |
| MOL-51 | Spike - GLiNER para Skills | NLP | 6h |
| MOL-52 | Documentar Arquitectura Modelos | Docs | 2h |

**Total Baja Prioridad:** 19h

---

**Total General:** ~144h

---

# RESUMEN POR ÉPICA

## Épica 1: Scraping (4 issues)
- MOL-27: Dashboard Admin - Tab Scraping 🔴
- MOL-28: Activar Scraper ZonaJobs 🟡
- MOL-29: Deduplicación Cross-Portal 🟡
- MOL-56: Sistema Optimización Keywords 🟡

## Épica 2: NLP (5 issues)
- MOL-30: Gold Set NLP (200+ casos) 🔴
- MOL-31: Test Automático NLP 🔴
- MOL-32: Export NLP a S3 🔴
- MOL-33: Sync Validaciones NLP 🟡
- MOL-51: Spike - GLiNER para Skills ⚪

## Épica 3: Matching ESCO (5 issues)
- MOL-5: Resolver sector_funcion (v8.4) 🔴
- MOL-34: Expandir Gold Set Matching 🔴
- MOL-35: Export Matching a S3 🔴
- MOL-49: Spike - Evaluar ESCO-XLM Reranker 🔴
- MOL-50: Spike - BGE-M3 Hybrid Retrieval ⚪

## Épica 4: Validación (5 issues)
- MOL-36: Dashboard Admin - Tab Tests 🔴
- MOL-37: Dashboard Admin - Tab S3 Sync 🔴
- MOL-38: Generate Sample 🟡
- MOL-39: Dashboard Validación (Vercel) 🟡
- MOL-40: Export Producción 🔴

## Épica 5: Dashboards (5 issues)
- MOL-41: Dashboard Admin - App Principal 🔴 ✅
- MOL-42: Dashboard Admin - Tab Pipeline 🟡
- MOL-43: Dashboard Producción (Vercel) 🟡
- MOL-44: Lambda API Backend 🟡
- MOL-55: Funciones Ejecutables Dashboard 🔴 (Fase 1)

## Épica 6: Infraestructura (6 issues)
- MOL-48: Sistema de Métricas y Logging 🔴
- MOL-45: Dashboard Admin - Tab Logs ⚪
- MOL-46: Alertas Email/Slack ⚪
- MOL-47: CI/CD GitHub Actions ⚪
- MOL-52: Documentar Arquitectura Modelos ⚪

---

# ORDEN DE IMPLEMENTACIÓN SUGERIDO

## Fase 1: Fundamentos (Semana 1) - EN PROGRESO
1. **MOL-48**: Sistema de Métricas ✅ COMPLETADO
2. **MOL-49**: Spike ESCO-XLM ✅ COMPLETADO (Decisión: REMOVER reranker)
3. **MOL-41**: Dashboard Admin - App Principal ✅ COMPLETADO
4. **MOL-54**: Validar NLP v8.0 ✅ COMPLETADO (78.9% precisión)
5. **MOL-55**: Funciones Ejecutables Dashboard (Fase 1) ← SIGUIENTE

## Fase 2: NLP Completo (Semana 2)
6. Procesar 9,443 ofertas con NLP v8.0 (en background)
7. **MOL-30**: Gold Set NLP (200+ casos)
8. **MOL-31**: Test Automático NLP
9. **MOL-27**: Dashboard Admin - Tab Scraping

## Fase 3: Tests y Matching (Semana 3)
10. **MOL-34**: Expandir Gold Set Matching
11. **MOL-36**: Dashboard Admin - Tab Tests
12. **MOL-32**: Export NLP a S3
13. **MOL-35**: Export Matching a S3

## Fase 4: Mejoras Matching (Semana 4)
14. **MOL-5**: Resolver sector_funcion v8.4
15. **MOL-37**: Dashboard Admin - Tab S3 Sync
16. **MOL-40**: Export Producción

## Fase 5: Optimización (Semana 5+)
17. MOL-50: Spike - BGE-M3 Hybrid
18. MOL-51: Spike - GLiNER
19. MOL-55: Funciones Dashboard (Fases 2 y 3)
20. Resto de issues según prioridad

---

---

## MOL-62: Implementar NLP Schema v5 - Campos Críticos

### Contexto
Gap Analysis reveló:
- Schema diseñado (NLP_SCHEMA_V5.md): 147 campos en 16 bloques
- Implementado actual: 12 campos (8.2%)
- Campos críticos faltantes impactan directamente el matching ESCO

**Campos más críticos faltantes:**
| Campo | Bloque | Impacto Matching |
|-------|--------|------------------|
| tareas[] | Rol y Tareas | ★★★★★ Confirma ocupación |
| area_funcional | Condiciones | ★★★★★ Contexto sector |
| nivel_seniority | Condiciones | ★★★★★ Nivel jerárquico |
| tiene_gente_cargo | Rol y Tareas | ★★★★☆ Jefe vs IC |
| tipo_oferta | Metadatos NLP | ★★★☆☆ Filtrar basura |

### Objetivo
Implementar extracción de campos críticos según NLP_SCHEMA_V5.md para mejorar matching.

### Fases de Implementación

#### Fase 1: Campos Críticos para Matching (Este Issue)
| Campo | Bloque | Tipo |
|-------|--------|------|
| tareas_explicitas | Rol y Tareas | [string] |
| tareas_inferidas | Rol y Tareas | [string] |
| tiene_gente_cargo | Rol y Tareas | boolean |
| area_funcional | Condiciones | string |
| nivel_seniority | Condiciones | string |
| sector_empresa | Empresa | string |
| tecnologias_list | Skills | [string] |
| tipo_oferta | Metadatos | string |
| licencia_conducir | Licencias | boolean |

#### Fase 2: Campos Importantes
- experiencia_nivel_previo
- producto_servicio
- titulo_requerido
- conocimientos_especificos[]
- tipo_contrato

#### Fase 3: Calidad y Flags
- tiene_requisitos_discriminatorios
- calidad_redaccion
- requisito_edad_min/max

#### Fase 4: Resto de Bloques
- Compensación completa
- Beneficios detallados
- Ubicación/Movilidad
- Certificaciones

### Archivos a Crear/Modificar

```
database/migrations/
└── 002_add_nlp_schema_v5_columns.sql   # CREAR

02.5_nlp_extraction/prompts/
└── extraction_prompt_v9.py              # CREAR (expandir v8)

database/
├── process_nlp_from_db_v7.py           # ACTUALIZAR schema
└── ofertas_nlp                         # MIGRAR tabla
```

### Criterios de Aceptación

- [ ] Migración ejecutada (9 columnas nuevas)
- [ ] Prompt v9 creado con campos nuevos
- [ ] process_nlp actualizado para v9
- [ ] Test con 5 ofertas muestra extracción correcta
- [ ] Gold Set verificado post-migración

### Prioridad: 🔴 Alta

### Labels: `nlp`, `schema`, `feature`

### Estimación: 8h

### Dependencias
- Gap Analysis completado ✅

---

*Documento generado: 2025-12-07*
*Última actualización: 2025-12-09*
*Para Linear: Copiar cada issue con su contexto completo*
