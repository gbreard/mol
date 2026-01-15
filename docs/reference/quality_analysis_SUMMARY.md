# Quality Analysis Report - NLP v6.0
**Fecha:** 2025-11-23 22:04:12
**Base de datos:** `bumeran_scraping.db`
**Modelo:** Hermes 3:8b

---

## RESUMEN EJECUTIVO

### Estadísticas Generales
- **Total ofertas en BD:** 6,521
- **Procesadas con v6.0:** 6,521 (100.0%)
- **Quality Score Promedio:** 13.4/24 (55.7%)
- **Quality Score Mediana:** 13/24
- **Rango:** 3.0 - 22.0

### Criterios de Calidad Evaluados

| Criterio | Target | Resultado | Status |
|----------|--------|-----------|--------|
| Quality Score Promedio | >60% | 55.7% | [X] NO CUMPLE |
| Campos CORE >60% coverage | 5/5 | 3/5 | [X] NO CUMPLE |
| Campos v6.0 cumpliendo target | 4/6 | 4/6 | [OK] CUMPLE |
| Arrays JSON válidos | 100% | 100% | [OK] CUMPLE |

---

## RECOMENDACIÓN FINAL

### ESCENARIO C - CALIDAD ACEPTABLE (Necesita mejora)

**DECISIÓN:** [!] REFINAR PROMPT v6.1, reprocesar ofertas con quality score <12, LUEGO FASE 2

**Detalles:** La calidad es aceptable pero mejorable. Se recomienda refinamiento antes de FASE 2.

---

## ANÁLISIS DETALLADO

### 1. Coverage por Categoría de Campo

| Categoría | Promedio Coverage | Campos | Target General |
|-----------|-------------------|--------|----------------|
| CORE | 62.5% | 5 | >60% |
| IMPORTANT | 68.1% | 6 | >40% |
| CONTEXTUAL | 20.8% | 7 | >20% |
| OPTIONAL | 16.4% | 6 | >10% |

### 2. Campos Nuevos v6.0

| Campo | Coverage | Target | Status |
|-------|----------|--------|--------|
| `experiencia_cargo_previo` | 6.1% | 20% | LOW |
| `tecnologias_stack_list` | 24.0% | 20% | OK |
| `sector_industria` | 95.4% | 40% | OK |
| `nivel_seniority` | 83.4% | 60% | OK |
| `modalidad_contratacion` | 93.0% | 40% | OK |
| `disponibilidad_viajes` | 15.5% | 20% | LOW |

### 3. Distribución de Quality Score

| Rango | Cantidad | Porcentaje |
|-------|----------|------------|
| Excelente (>17) | 150 | 2.3% |
| Bueno (14-17) | 3,043 | 46.7% |
| Aceptable (10-13) | 3,044 | 46.7% |
| Bajo (<10) | 294 | 4.5% |

### 5. Validación de Arrays JSON

[OK] **Todos los arrays JSON son válidos** (0 errores)

---

## PRÓXIMOS PASOS


1. [!] **REFINAR PROMPTS** antes de FASE 2:
   - Identificar campos con coverage <target
   - Revisar y mejorar prompts específicos
   - Crear v6.1 con mejoras
2. **REPROCESAR ofertas con quality score <12**
   - Identificar ~{sum(1 for s in self.stats['quality_score_distribution'] if s < 12)} ofertas
   - Aplicar prompts mejorados
3. **RE-ANALIZAR calidad** post-mejoras
4. **ENTONCES proceder a FASE 2** (si mejora es suficiente)

---

**Reporte generado automáticamente por:** `quality_analysis_v6.py`  
**Timestamp:** 2025-11-23T22:04:12.779026  
