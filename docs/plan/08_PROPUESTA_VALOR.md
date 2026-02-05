# 8. Propuesta de Valor

> Última actualización: 2026-02-05

## Referencias

| Documento | Relación |
|-----------|----------|
| [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md) | Features por plan |
| [09_ROADMAP](./09_ROADMAP.md) | Fases 2-4 features |
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Pantallas de features |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Features de plan | 01_MODELO_NEGOCIO, 02_ARQUITECTURA |
| Nuevos diferenciadores | 09_ROADMAP |
| Métricas de datos | Estado de pipeline |

---

## Resumen Ejecutivo

| Severidad | Cantidad | Descripción |
|-----------|----------|-------------|
| **CRÍTICO** | 4 | Gaps que impiden lanzamiento comercial |
| **ALTO** | 6 | Features que esperan los usuarios |
| **MEDIO** | 5 | Mejoras de UX |
| **Total** | **15** | |

---

## Métricas Actuales de Datos

```
OFERTAS EN BD:
├── Total:           13,170
├── Con NLP:          6,512 (49%)
├── Sin NLP:         13,658 (52%) ⚠️
├── Validadas:          119 (1%)  ⚠️ CRÍTICO
└── En Supabase:        538 (4%)

MATCHING:
├── Por reglas:        81%
├── Por diccionario:    4%
└── Por semántico:     15%
```

---

## Issues CRÍTICOS (V-01 a V-04)

### V-01: Solo 1% de ofertas validadas

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Datos** | 119 de 13,170 ofertas (0.9%) |
| **Impacto** | Datos poco confiables para usuarios que pagan |
| **Meta** | 40% validadas para lanzamiento |

**Plan de acción:**
1. Acelerar pipeline de validación
2. Priorizar ofertas recientes
3. Automatizar validación para casos claros
4. Meta: 1,000 ofertas/semana

---

### V-02: 52% de ofertas sin NLP

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Datos** | 13,658 ofertas sin procesar |
| **Impacto** | Mitad de datos sin skills, seniority, etc. |
| **Meta** | 100% procesado |

**Plan de acción:**
1. Backfill masivo con priorización
2. Procesar más recientes primero
3. Cron job para nuevas ofertas

---

### V-03: Sin análisis predictivo

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Impacto** | No hay diferenciación vs competidores |
| **Competidores** | Indeed Hiring Lab tiene predicciones |

**Features propuestas:**
- Tendencias de ocupaciones (siguiente trimestre)
- Predicción de demanda por skill
- Alertas de ocupaciones emergentes

---

### V-04: Sin análisis de salarios

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Datos** | Campo `salario` existe pero no se usa |
| **Impacto** | Feature clave desperdiciada |
| **Competidores** | Glassdoor es el líder en salarios |

**Features propuestas:**
- Rangos salariales por ocupación
- Comparador de salarios por provincia
- Tendencias salariales históricas

---

## Issues ALTOS (V-05 a V-10)

### V-05: Alertas de nuevas ofertas

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Competidores** | LinkedIn, Indeed lo tienen |
| **Pantalla** | [P-13](./03_WIREFRAMES/suscriptor.md#p-13-alertas) |

**Implementación:**
- Cron job diario que revisa nuevas ofertas
- Match contra criterios de alertas
- Envío de email con resumen

---

### V-06: Comparador de salarios por ocupación

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Competidores** | Glassdoor |
| **Datos necesarios** | 30%+ ofertas con salario |

---

### V-07: Tendencias históricas (gráficos de evolución)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Competidores** | Indeed Hiring Lab |
| **Implementación** | Gráficos de línea por ocupación/skill |

---

### V-08: API pública para desarrolladores

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Plan** | Solo Enterprise |
| **Implementación** | REST API con rate limiting |

---

### V-09: Exportación a formatos múltiples

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Formatos** | Excel, PDF, CSV |
| **Plan** | PRO y Enterprise |

---

### V-10: Análisis de skills gap

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Descripción** | Comparar skills del usuario vs demanda |
| **Diferenciador** | Pocos competidores lo tienen |

---

## Issues MEDIOS (V-11 a V-15)

| ID | Feature | Descripción |
|----|---------|-------------|
| V-11 | Onboarding guiado | Tour interactivo para nuevos usuarios |
| V-12 | Tooltips explicativos | Explicaciones en métricas y gráficos |
| V-13 | Comparación temporal | Selector "vs período anterior" |
| V-14 | Dashboard personalizable | Widgets arrastrables |
| V-15 | Modo offline | PWA con cache de datos recientes |

---

## Análisis Competitivo

### Competidores Principales

| Feature | MOL | LinkedIn | Indeed | Glassdoor |
|---------|-----|----------|--------|-----------|
| Ofertas Argentina | ✓ | ✓ | ✓ | Parcial |
| Clasificación ESCO | ✓ | ✗ | ✗ | ✗ |
| Skills Intelligence | ✓ | Parcial | ✗ | ✗ |
| Salarios | ⚠️ | ✓ | ✓ | ✓ |
| Tendencias | ⚠️ | ✓ | ✓ | ✓ |
| Alertas | ⚠️ | ✓ | ✓ | ✓ |
| API | ⚠️ | ✓ | ✓ | ✗ |
| Datos oficiales OEDE | ✓ | ✗ | ✗ | ✗ |

### Diferenciadores Únicos de MOL

1. **Taxonomía ESCO oficial** - Único en Argentina
2. **Datos de OEDE** - Fuente oficial gubernamental
3. **Skills Intelligence** - Análisis profundo de competencias
4. **Enfoque Argentina** - Localización completa

---

## Features por Fase

### Fase 2: Valor de Datos (2-3 semanas)

```
□ V-01: Backfill NLP (meta: 10,000 ofertas)
□ V-02: Acelerar validación (meta: 1,000/semana)
□ V-04: Habilitar análisis de salarios
□ V-07: Gráficos de tendencias históricas
```

### Fase 3: Features Comerciales (4-6 semanas)

```
□ V-05: Sistema de alertas por email
□ V-09: Exportación Excel/PDF
□ V-08: API pública (Enterprise)
□ V-10: Análisis de skills gap
```

### Fase 4: Diferenciación (2-3 meses)

```
□ V-03: Análisis predictivo con ML
□ V-06: Comparador de salarios
□ V-11: Onboarding guiado
□ V-14: Dashboard personalizable
```

---

## Métricas de Éxito

### Datos

| Métrica | Actual | Meta MVP | Meta 6 meses |
|---------|--------|----------|--------------|
| Ofertas validadas | 1% | 10% | 40% |
| Ofertas con NLP | 49% | 80% | 100% |
| Ofertas con salario | ~20% | 30% | 40% |

### Producto

| Métrica | Actual | Meta MVP | Meta 6 meses |
|---------|--------|----------|--------------|
| Features PRO | 2 | 5 | 8 |
| NPS | N/A | > 30 | > 50 |
| Churn mensual | N/A | < 10% | < 5% |
