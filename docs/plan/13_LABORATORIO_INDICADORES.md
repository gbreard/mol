# 13. Laboratorio de Indicadores Experimentales

> Ultima actualizacion: 2026-02-26
> Version: 1.0

## Referencias

| Documento | Relacion |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | P-31, P-31a |
| [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md) | V-16 Tension de Demanda |
| [09_ROADMAP](./09_ROADMAP.md) | Fases 2-4 |
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas calculadas |

## Proposito

El Laboratorio es un espacio admin (`/admin/laboratorio`) donde indicadores experimentales se **prueban, calibran y validan** antes de promoverlos al dashboard publico. Cada indicador pasa por un ciclo de vida:

```
EXPERIMENTAL → BETA → PRODUCCION
     ↓           ↓         ↓
  Solo admin   Admin +    Dashboard
  Datos crudos  select    publico
  Sin SLA       users    Con SLA
```

### Principios

1. **No contaminar el dashboard publico** — indicadores no validados no aparecen en `/dashboard`
2. **Datos reales, no mocks** — todo indicador usa las mismas tablas de produccion
3. **Metodologia explicita** — cada indicador documenta formula, supuestos y limitaciones
4. **Promovible** — cuando un indicador pasa a produccion, se mueve al dashboard con filtros globales

---

## Inventario de Datos Disponibles

Base: **18,259 ofertas** (ago-2025 a feb-2026), **16,130 validadas**, **350 ocupaciones ISCO**, **1,206 ESCO**, **9,449 skills unicas**, **4,062 empresas**, **23 provincias**, **15 sectores CLAE**.

| Dimension | Cobertura | Registros | Notas |
|-----------|-----------|-----------|-------|
| Ocupacion ISCO | 97% | 16,139 | 350 codigos distintos |
| Ocupacion ESCO | 75% | ~12K | 1,206 URIs |
| Skills ESCO | 99% | 297K detalle | 9,449 labels unicos |
| Seniority | 99% | 15,988 | 5 niveles: trainee→manager |
| Area funcional | 99% | 16,135 | 24 areas |
| Sector CLAE | 97% | 15,725 | 15 secciones |
| Modalidad | 100% | 16,139 | presencial/remoto/hibrido |
| Nivel educativo | 82% | 13,318 | univ/secund/terciario/etc |
| Experiencia | 89% | 14,376 | anios min/max |
| Provincia | 34% | 6,120 | 23 provincias (muchas sin geo) |
| Permanencia | 100% | 18,251 | baja/media/alta |
| Republicacion | 11% | 1,961 | grupos: 3,164 |
| Salario | 0.4% | 70 | **Inutilizable** |
| Vacantes | 100% | 18,259 | total: 35,628 posiciones |
| Jornada | 49% | 7,871 | full-time/part-time |
| Fecha publicacion | 100% | 18,259 | 7 meses de serie temporal |
| Gente a cargo | 17% | 2,808 | Solo cuando se menciona |

### Limitaciones criticas

- **Salario**: 70 ofertas de 18K — no alcanza para ningun indicador salarial
- **Provincia**: 34% cobertura — indicadores geograficos sesgados hacia ofertas geolocalizables
- **Serie temporal**: 7 meses — insuficiente para estacionalidad real, suficiente para tendencia

---

## Catalogo de Indicadores

### IMPLEMENTADO

#### I-01: Tension de Demanda (V-16) — `EXPERIMENTAL`

| Campo | Valor |
|-------|-------|
| **Pantalla** | P-31a (`/admin/laboratorio/tension-demanda`) |
| **Tabla Supabase** | `tension_ocupaciones` |
| **Fuente datos** | `ofertas` + `ofertas_esco_matching` |
| **Granularidad** | Por ocupacion ISCO (350) |
| **Visualizacion** | ScatterChart (persistencia × insistencia) + tabla ordenable |
| **Formula** | Persistencia = % posiciones con ventana >45 dias. Insistencia = % posiciones republicadas. |
| **Cuadrantes** | CRITICO (alta-alta), URGENTE (alta-baja), PASIVO (baja-alta), FLUIDO (baja-baja) |
| **Umbral** | 50% en ambos ejes |
| **Resultado actual** | 12 CRITICO, 309 URGENTE, 0 PASIVO, 29 FLUIDO |
| **Limitacion** | URGENTE sobrerepresentado: pocas republicaciones detectadas (11%), persistencia domina |
| **Siguiente paso** | Calibrar umbral de persistencia (45 dias puede ser muy bajo). Evaluar si 30d es mejor |

---

### PROPUESTOS — Prioridad ALTA

#### I-02: Indice de Concentracion Ocupacional

> ¿El mercado laboral se esta especializando o diversificando?

| Campo | Valor |
|-------|-------|
| **Metrica** | HHI (Herfindahl-Hirschman Index) de ofertas por ocupacion ISCO |
| **Formula** | HHI = Σ (share_i)^2, donde share_i = ofertas_isco_i / total_ofertas |
| **Interpretacion** | HHI < 0.15 = diversificado, 0.15-0.25 = moderado, > 0.25 = concentrado |
| **Visualizacion** | Gauge + trend line mensual + top 5 ocupaciones concentradoras |
| **Granularidad** | Global, por provincia, por sector CLAE |
| **Datos necesarios** | `ofertas_esco_matching.isco_code` + `ofertas.fecha_publicacion_iso` |
| **Cobertura** | 97% — excelente |
| **Valor analitico** | ALTO — responde "¿pocas ocupaciones acaparan la demanda?" |
| **Complejidad** | BAJA — SQL puro, sin dependencias nuevas |

#### I-03: Brecha de Calificacion por Ocupacion

> ¿Que ocupaciones piden mas skills de las que el promedio del mercado puede ofrecer?

| Campo | Valor |
|-------|-------|
| **Metrica** | Skills demandadas por ocupacion vs promedio general |
| **Formula** | brecha = skills_promedio_isco / skills_promedio_mercado. >1 = sobreexigente, <1 = subexigente |
| **Visualizacion** | BarChart horizontal divergente (centro=1.0) por ocupacion ISCO |
| **Granularidad** | Por ocupacion ISCO (top 30) |
| **Datos necesarios** | `ofertas_esco_skills_detalle` + `ofertas_esco_matching.isco_code` |
| **Cobertura** | 99% en skills — excelente |
| **Valor analitico** | ALTO — muestra desbalances entre lo que se pide y lo que es razonable |
| **Complejidad** | BAJA — SQL agregado |

#### I-04: Mapa de Transicion Skills-Ocupacion

> ¿Que skills son puente entre ocupaciones? Si aprendo X, ¿a que otras ocupaciones puedo saltar?

| Campo | Valor |
|-------|-------|
| **Metrica** | Skills compartidas entre pares de ocupaciones ISCO |
| **Formula** | jaccard(skills_A, skills_B) = |A ∩ B| / |A ∪ B| por par de ISCO |
| **Visualizacion** | Network graph / chord diagram (top 20 ocupaciones) |
| **Granularidad** | Par de ocupaciones ISCO |
| **Datos necesarios** | `ofertas_esco_skills_detalle` + `ofertas_esco_matching.isco_code` |
| **Cobertura** | 99% skills, 350 ISCO |
| **Valor analitico** | MUY ALTO — propuesta de valor diferenciadora para politica publica |
| **Complejidad** | MEDIA — requiere calculo de pares (350² = ~60K pares, filtrar por threshold) |
| **Nota** | Ya tenemos propuesta tecnica en `docs/PROPUESTA_MODULO_BRECHAS_TECNICO.md` |

#### I-05: Indice de Digitalizacion por Sector

> ¿Que sectores estan demandando mas skills digitales?

| Campo | Valor |
|-------|-------|
| **Metrica** | % de skills digitales sobre total de skills por sector CLAE |
| **Formula** | idx_digital = skills_digitales_sector / skills_total_sector |
| **Visualizacion** | BarChart por sector CLAE + trend mensual |
| **Granularidad** | Por sector CLAE (15 secciones) |
| **Datos necesarios** | `ofertas_esco_skills_detalle.es_digital` (via Supabase `ofertas_skills`) + `ofertas_nlp.clae_seccion` |
| **Cobertura** | 97% sector + 99% skills |
| **Valor analitico** | ALTO — politica publica de transformacion digital |
| **Complejidad** | BAJA — SQL con JOIN y GROUP BY |

---

### PROPUESTOS — Prioridad MEDIA

#### I-06: Velocidad de Cobertura

> ¿Cuanto tardan en cubrirse las ofertas por ocupacion?

| Campo | Valor |
|-------|-------|
| **Metrica** | Mediana de `dias_publicada` por ocupacion ISCO |
| **Formula** | mediana(dias_publicada) por ISCO, solo ofertas con `estado_oferta = 'baja'` |
| **Visualizacion** | BoxPlot o violin por ISCO (top 20 mas lentas vs 20 mas rapidas) |
| **Granularidad** | Por ocupacion ISCO |
| **Datos necesarios** | `ofertas.dias_publicada` + `ofertas_esco_matching.isco_code` |
| **Cobertura** | 100% dias_publicada |
| **Valor analitico** | MEDIO — complementa I-01 (tension) con dato temporal |
| **Complejidad** | BAJA — SQL con Window Functions |

#### I-07: Perfil de Exigencia por Ocupacion (Radar)

> ¿Que tan exigente es cada ocupacion en las 5 dimensiones?

| Campo | Valor |
|-------|-------|
| **Metrica** | Score normalizado (0-100) en: experiencia, educacion, skills, seniority, idioma |
| **Formula** | Por ISCO: exp_score = avg(exp_min_anios)/max * 100, edu_score = nivel_ponderado, etc. |
| **Visualizacion** | RadarChart por ocupacion, comparar 2-3 en overlay |
| **Granularidad** | Por ocupacion ISCO |
| **Datos necesarios** | `ofertas_nlp` (experiencia, educacion, seniority) + skills count |
| **Cobertura** | 82-99% segun dimension |
| **Valor analitico** | MEDIO — util para orientacion laboral |
| **Complejidad** | MEDIA — requiere normalizar 5 escalas diferentes |

#### I-08: Concentracion Empresarial

> ¿Pocas empresas dominan la demanda de ciertas ocupaciones?

| Campo | Valor |
|-------|-------|
| **Metrica** | Top 3 empresas como % del total de ofertas por ISCO |
| **Formula** | concentracion_top3 = (ofertas_emp1 + emp2 + emp3) / total_isco |
| **Visualizacion** | TreeMap por ISCO, tamanio=ofertas, color=concentracion |
| **Granularidad** | Por ocupacion ISCO |
| **Datos necesarios** | `ofertas.empresa` + `ofertas_esco_matching.isco_code` |
| **Cobertura** | 100% empresa (4,062 distintas) |
| **Valor analitico** | MEDIO — detecta monopsonio por ocupacion |
| **Complejidad** | BAJA — SQL con RANK() |

#### I-09: Gap Formativo (Seniority vs Educacion)

> ¿Se pide titulo universitario para puestos junior? ¿Hay mismatch formativo?

| Campo | Valor |
|-------|-------|
| **Metrica** | Distribucion de nivel_educativo cruzada por nivel_seniority |
| **Formula** | Heatmap: eje X = seniority (5 niveles), eje Y = educacion (4 niveles), color = count |
| **Visualizacion** | Heatmap + drill-down por celda para ver ocupaciones |
| **Granularidad** | Global, filtrable por sector |
| **Datos necesarios** | `ofertas_nlp.nivel_seniority` + `ofertas_nlp.nivel_educativo` |
| **Cobertura** | 82% educacion, 99% seniority |
| **Valor analitico** | MEDIO — politica educativa |
| **Complejidad** | BAJA — Crosstab SQL |

#### I-10: Indice de Trabajo Remoto

> ¿Como evoluciona la oferta de trabajo remoto/hibrido por sector y ocupacion?

| Campo | Valor |
|-------|-------|
| **Metrica** | % de ofertas remoto+hibrido sobre total, evolucion mensual |
| **Formula** | idx_remoto = (remoto + hibrido) / total * 100 por mes × sector |
| **Visualizacion** | LineChart mensual por sector (stacked area: presencial/hibrido/remoto) |
| **Granularidad** | Por mes × sector CLAE |
| **Datos necesarios** | `ofertas_nlp.modalidad` + `ofertas_nlp.clae_seccion` + `ofertas.fecha_publicacion_iso` |
| **Cobertura** | 100% modalidad, 97% sector |
| **Valor analitico** | MEDIO — tendencia post-pandemia |
| **Complejidad** | BAJA — SQL temporal con GROUP BY |

---

### PROPUESTOS — Prioridad BAJA (requieren mas datos o desarrollo)

#### I-11: Indice de Diversidad Ocupacional por Empresa

> ¿Las empresas grandes buscan perfiles mas diversos que las chicas?

| Campo | Valor |
|-------|-------|
| **Metrica** | Cantidad de ISCO distintos por empresa |
| **Formula** | diversidad = COUNT(DISTINCT isco_code) WHERE empresa = X |
| **Visualizacion** | ScatterChart (ofertas vs diversidad) con outliers etiquetados |
| **Cobertura** | 100% |
| **Complejidad** | BAJA |
| **Valor analitico** | BAJO — exploratorio |

#### I-12: Estacionalidad de Ocupaciones

> ¿Hay ocupaciones que se demandan mas en ciertos meses?

| Campo | Valor |
|-------|-------|
| **Metrica** | Coeficiente de variacion mensual por ISCO |
| **Formula** | CV = stddev(ofertas_mensuales) / mean(ofertas_mensuales) |
| **Visualizacion** | Heatmap mes × ocupacion (top 20 mas estacionales) |
| **Cobertura** | 100% |
| **Limitacion** | Solo 7 meses de datos — necesitamos 12+ para validar estacionalidad real |
| **Complejidad** | BAJA — SQL |
| **Valor analitico** | BAJO (ahora) / ALTO (cuando tengamos 1+ anio) |

#### I-13: Indice Salarial (BLOQUEADO)

> ¿Cuanto se paga por ocupacion/sector?

| Campo | Valor |
|-------|-------|
| **Metrica** | Mediana salarial por ISCO |
| **Estado** | **BLOQUEADO** — solo 70 ofertas con salario (0.4%). Inutilizable. |
| **Desbloqueo** | Scraping de portales que publican salario (LinkedIn, Glassdoor) o fuentes externas (INDEC) |

---

## Matriz de Priorizacion

| ID | Indicador | Valor | Complejidad | Cobertura | Prioridad |
|----|-----------|-------|-------------|-----------|-----------|
| I-01 | Tension de Demanda | ALTO | BAJA | 100% | ✅ HECHO |
| I-02 | Concentracion Ocupacional | ALTO | BAJA | 97% | **P1** |
| I-05 | Digitalizacion por Sector | ALTO | BAJA | 97% | **P1** |
| I-03 | Brecha de Calificacion | ALTO | BAJA | 99% | **P1** |
| I-04 | Transicion Skills-Ocupacion | MUY ALTO | MEDIA | 99% | **P2** |
| I-10 | Indice Trabajo Remoto | MEDIO | BAJA | 100% | **P2** |
| I-06 | Velocidad de Cobertura | MEDIO | BAJA | 100% | **P2** |
| I-09 | Gap Formativo | MEDIO | BAJA | 82% | **P3** |
| I-08 | Concentracion Empresarial | MEDIO | BAJA | 100% | **P3** |
| I-07 | Perfil Exigencia (Radar) | MEDIO | MEDIA | 82% | **P3** |
| I-11 | Diversidad Empresarial | BAJO | BAJA | 100% | P4 |
| I-12 | Estacionalidad | BAJO | BAJA | 100% | P4 (necesita 12+ meses) |
| I-13 | Indice Salarial | ALTO | ALTA | 0.4% | **BLOQUEADO** |

### Criterios de priorizacion

- **P1** = Alto valor + baja complejidad + alta cobertura → implementar ya
- **P2** = Alto/medio valor + complejidad media → siguiente sprint
- **P3** = Medio valor → cuando haya tiempo
- **P4** = Bajo valor o datos insuficientes → backlog
- **BLOQUEADO** = datos insuficientes, no implementable

---

## Ciclo de Vida de un Indicador

```
1. PROPUESTA (este documento)
   - Definir formula, datos, visualizacion
   - Validar cobertura de datos
   - Asignar ID (I-XX)

2. EXPERIMENTAL (/admin/laboratorio)
   - Implementar calculo en sync_to_supabase.py
   - Crear tabla Supabase
   - Crear pagina en /admin/laboratorio/<slug>
   - Badge: "Experimental" (amber)
   - Acceso: solo admin

3. BETA (/admin/laboratorio con badge azul)
   - Calibrar umbrales y parametros
   - Validar con analistas (OEDE)
   - Documentar metodologia final
   - Opcional: dar acceso a usuarios seleccionados

4. PRODUCCION (/dashboard)
   - Promover al dashboard publico
   - Integrar con filtros globales (Sidebar)
   - Remover de laboratorio
   - Agregar a documentacion publica
```

---

## Arquitectura Tecnica

### Patron para cada indicador

```
Backend (Python):
  scripts/exports/sync_to_supabase.py
    → calcular_<indicador>(conn) → List[Dict]     # CTE SQL
    → sync_<indicador>(client, conn) → int         # Truncate + insert

Supabase:
  scripts/exports/supabase_schema.sql
    → CREATE TABLE <indicador> (...)               # DDL + RLS + index

Frontend (Next.js):
  lib/supabase.ts
    → interface <Indicador>                         # Tipos
    → get<Indicador>(): Promise<T[]>                # Query

  components/laboratorio/<Indicador>Chart.tsx       # Componente presentacional
  app/admin/laboratorio/<slug>/page.tsx             # Pagina detalle

  app/admin/laboratorio/page.tsx                    # Agregar card a INDICATORS[]
```

### Registro de indicador en landing

Agregar a `INDICATORS[]` en `app/admin/laboratorio/page.tsx`:

```typescript
{
  slug: '<slug>',
  title: '<Titulo>',
  description: '<Descripcion corta>',
  status: 'experimental',           // 'experimental' | 'beta' | 'production'
  href: '/admin/laboratorio/<slug>',
  icon: <LucideIcon>,
  dataSource: '<tabla_supabase>',
  addedDate: 'YYYY-MM',
}
```

---

## Historial de Cambios

| Fecha | Version | Cambio |
|-------|---------|--------|
| 2026-02-26 | 1.0 | Documento inicial. I-01 implementado. 12 indicadores propuestos. |
