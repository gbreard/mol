# 8. Propuesta de Valor

> Última actualización: 2026-02-11

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
| **CRÍTICO** | 5 | Gaps que impiden lanzamiento (incluye V-19 pools OE) |
| **ALTO** | 10 | Features que esperan los usuarios |
| **MEDIO** | 6 | Mejoras de UX + S3 v2 |
| **Total** | **21** | |

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

### V-09: Exportación a formatos múltiples ✅ PARCIAL

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Formatos** | Excel, PDF, CSV |
| **Plan** | PRO y Enterprise |
| **Estado** | ✅ CSV/Excel implementado (2026-02-06) |
| **Pendiente** | PDF |

**Implementado en:**
- Panorama General: CSV por gráfico
- Ofertas Laborales: CSV/Excel (12 columnas)
- Requerimientos: CSV/Excel (distribución + skills)

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

### V-16: Indicador de Tensión de Demanda

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Descripción** | Indicador compuesto que mide qué ocupaciones cuestan más llenar, combinando persistencia (duración) e insistencia (republicación) |
| **Componentes** | Persistencia (% posiciones >45d) + Insistencia (% posiciones republicadas) |
| **Pantalla** | [P-09](./03_WIREFRAMES/suscriptor.md#p-09-dashboard) — Scatter plot en Panorama + Filtro en sidebar |
| **Tabla** | `tension_ocupaciones` — [04_MODELO_DATOS](./04_MODELO_DATOS.md#t-tension_ocupaciones-nueva--indicador-tensión-de-demanda) |
| **Diferenciador** | Ningún competidor tiene un indicador que combine permanencia + republicación a nivel ocupación |
| **Estado** | ⚠️ Parcial — datos disponibles (permanencia + republicación en Supabase), UI pendiente |

**Cuadrantes y su impacto para usuarios:**

| Cuadrante | Significado para analista | Significado para buscador de empleo |
|-----------|--------------------------|-------------------------------------|
| CRÍTICO | Ocupaciones donde hay escasez real de candidatos | Alta probabilidad de conseguir empleo |
| URGENTE | Alta rotación, empleadores necesitan cubrir rápido | Empleos disponibles pero posiblemente inestables |
| PASIVO | Búsquedas largas sin urgencia, posiblemente perfiles muy específicos | Competencia alta, proceso largo |
| FLUIDO | Mercado equilibrado, oferta y demanda balanceadas | Condiciones normales de búsqueda |

---

### V-17: Reporte de Compatibilidad Laboral para Empresas

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Descripción** | Genera un reporte de compatibilidad entre un trabajador y una vacante, dirigido al reclutador de la empresa contratante. Incluye carta PDF con QR + reporte web interactivo |
| **Componentes** | 1) Carta PDF (logo MOL + datos candidato + QR) 2) Reporte web interactivo (mapa competencias + matriz afinidad + edición en tiempo real) |
| **Pantallas** | Modificación P-10 (botón en "Mis Skills"), P-35 (reporte público `/reporte/[token]`) |
| **Dependencias** | Motor de matching (MySkillsSearch.tsx), ESCO Argentino (perfiles consolidados), perfiles_trabajadores (Supabase) |
| **Taxonomía** | Usa el Perfil Consolidado Argentino (ESCO + emergentes aprobadas), no ESCO genérico. El reporte registra la versión del perfil usada |
| **Captura de competencias** | 3 vías combinables: por ocupación (existe), por tarea/habilidad (nuevo), texto libre (nuevo). Cada skill muestra su definición ESCO para confirmar/descartar |
| **Diferenciador** | Ningún competidor ofrece un reporte de compatibilidad basado en taxonomía ESCO adaptada al mercado argentino. Transparenta el matching y difunde el MOL entre empresas |
| **Estado** | ⬜ Pendiente |

**Resultados en 3 tabs (paso 3):**

1. **Ocupaciones compatibles:** Ranking de ocupaciones ESCO ordenadas por % de afinidad con el perfil del trabajador.
2. **Ofertas laborales:** Ofertas reales del mercado argentino (de `ofertas_dashboard`) filtradas por las ocupaciones compatibles, con gap personalizado por oferta.
3. **Capacitación sugerida:** Cursos que cubren las brechas técnicas, con dos modos de transición laboral: (A) por preferencia del trabajador ("quiero ser X") y (B) por demanda del mercado (ocupaciones en crecimiento accesibles desde el perfil actual, usando tendencia temporal de ofertas). Fuente inicial: Portal de Capacitación CABA (2,255 cursos).

**Dos entregables (reporte):**

1. **Carta de presentación (PDF):**
   - Logo MOL + fecha + presentación institucional
   - Datos del candidato (nombre, DNI) y vacante analizada
   - Código QR dinámico que apunta al reporte web
   - Contacto para consultas técnicas

2. **Reporte web interactivo (página pública por token):**
   - Datos del perfil y título de la vacante
   - Mapa de competencias requeridas (estándar ESCO)
   - Matriz de afinidad: competencias detectadas + brechas técnicas (skills gap)
   - **Interactividad:** reclutador puede eliminar/agregar competencias al mapa y el sistema recalcula en tiempo real
   - Link a landing page del MOL (difusión)

**Impacto esperado:**
- Difusión del MOL entre empresas (cada reporte es una puerta de entrada)
- Los trabajadores obtienen un documento profesional para entrevistas
- Las empresas acceden a la plataforma para ver el reporte completo

---

### V-18: Vía 4 — Captura de skills por formación/título

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Descripción** | El trabajador carga su título, certificación o curso completado. El sistema mapea esa formación a skills ESCO usando base de resoluciones oficiales argentinas + catálogo de cursos de academias/plataformas |
| **Dependencia** | Requiere scraping y análisis de resoluciones oficiales de carreras (pre, grado, posgrado) + catálogos de instituciones de formación |
| **Servicios** | S1 (trabajador), S2 (técnico OE) |
| **Estado** | ⬜ Pendiente (requiere base de resoluciones) |

---

### V-19: Gestión de pools para Oficinas de Empleo

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO (habilitante para lanzamiento) |
| **Descripción** | Las OEs cargan sus bases existentes (personas, vacantes locales, cursos del territorio) via Excel/CSV. El sistema mapea internamente a ESCO sin que la OE necesite conocer la taxonomía |
| **Impacto** | Permite lanzamiento inmediato: la OE ya tiene datos, el MOL aporta el motor |
| **Servicios** | S2 |
| **Estado** | ⬜ Pendiente |

---

### V-20: Matching bidireccional (vacante → candidatos)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Descripción** | Empresa trae una vacante a la OE → sistema la traduce a skills ESCO → rankea automáticamente la cartera de la OE por match → técnico preselecciona |
| **Servicios** | S2, S3 |
| **Estado** | ⬜ Pendiente |

---

### V-21: Servicio Empresas (S3) — nivel registrado

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 MEDIO (v2) |
| **Descripción** | Cuenta empresa con: publicar búsquedas, perfiles de puesto reutilizables, historial de candidatos, comparar side-by-side, benchmark del mercado, buscar en pool, reskilling de plantilla, inteligencia sectorial |
| **Pantallas** | S3-4 a S3-12 (9 pantallas) |
| **Estado** | ⬜ Futuro (Etapa 3-4 del roadmap) |

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
| Tensión de demanda | ✓ | ✗ | ✗ | ✗ |
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
⚠️ V-16: Tensión de demanda (datos disponibles, UI pendiente)
```

### Fase 3: Features Comerciales (4-6 semanas)

```
□ V-05: Sistema de alertas por email
✅ V-09: Exportación Excel/CSV (PDF pendiente)
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
