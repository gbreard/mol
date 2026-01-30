# Mapeo: Datos Validados vs Diseno Dashboard

**Fecha**: 2026-01-17
**Dashboard**: https://mol-nextjs.vercel.app/
**Datos disponibles**: 120 ofertas validadas en SQLite/Supabase

---

## 1. Estructura del Dashboard (Placeholder Actual)

### Navegacion
| Tab | Descripcion | Estado |
|-----|-------------|--------|
| Panorama general | KPIs, graficos, insights | Visible |
| Requerimientos | Skills/competencias | Placeholder |
| Ofertas laborales | Tabla detallada | Placeholder |

### Filtros Globales
| Filtro | Datos requeridos | Disponible? |
|--------|------------------|-------------|
| Territorio | provincia, localidad | SI |
| Periodo | fecha_publicacion, fecha_scraping | SI |
| Permanencia | dias_activa (calculable) | SI |
| Ocupacion | isco_code, isco_label | SI |

---

## 2. Componentes vs Datos Disponibles

### 2.1 Cards de Insights (3 cards destacados)

| Insight Placeholder | Query SQL Necesaria | Estado |
|---------------------|---------------------|--------|
| "Record historico: X ofertas en mes Y" | `SELECT strftime('%Y-%m', fecha_publicacion), COUNT(*) ... GROUP BY 1 ORDER BY 2 DESC LIMIT 1` | LISTO |
| "Sector destacado: X duplico demanda" | `SELECT isco_label, COUNT(*) ... comparar periodos` | LISTO |
| "Concentracion geografica: X% en Y" | `SELECT provincia, COUNT(*)*100.0/total ... GROUP BY 1` | LISTO |

### 2.2 KPIs Numericos (4 metricas)

| KPI | Campo/Tabla | Query | Estado |
|-----|-------------|-------|--------|
| Ofertas analizadas | `ofertas_esco_matching` | `COUNT(*) WHERE estado_validacion='validado'` | LISTO (120) |
| Ocupaciones identificadas | `ofertas_esco_matching` | `COUNT(DISTINCT isco_code)` | LISTO |
| Habilidades detectadas | `ofertas_nlp.skills_tecnicas_list` | `COUNT(DISTINCT skill)` (parsear JSON) | LISTO |
| % vs mes anterior | Calculado | Comparar conteos por periodo | LISTO |

### 2.3 Graficos

| Grafico | Datos requeridos | Campos disponibles | Estado |
|---------|------------------|-------------------|--------|
| Evolucion temporal | fecha, count por dia/semana/mes | `fecha_publicacion` en ofertas | LISTO |
| Top 10 ocupaciones | isco_code, isco_label, count | `ofertas_esco_matching` | LISTO |
| Distribucion geografica | provincia, count | `ofertas_nlp.provincia` | LISTO |

---

## 3. Datos Disponibles en BD

### 3.1 Tabla `ofertas_esco_matching` (35 campos)

Campos clave para dashboard:
- `id_oferta` - ID unico
- `isco_code` - Codigo ISCO-08 (4 digitos)
- `isco_label` - Nombre ocupacion
- `esco_occupation_label` - Nombre ESCO detallado
- `occupation_match_score` - Score de confianza (0-1)
- `occupation_match_method` - Metodo usado (regla/diccionario/semantico)
- `skills_oferta_json` - Skills extraidas (JSON array)
- `estado_validacion` - 'validado' | 'pendiente'
- `matching_version` - Version del pipeline

### 3.2 Tabla `ofertas_nlp` (161 campos)

Campos clave para dashboard:
- `id_oferta` - FK a ofertas
- `titulo` - Titulo del puesto
- `empresa` - Nombre empresa
- `provincia` - Ubicacion nivel 1
- `localidad` - Ubicacion nivel 2
- `modalidad` - remoto/hibrido/presencial
- `nivel_seniority` - junior/semisenior/senior/manager
- `area_funcional` - IT/Ventas/RRHH/etc
- `sector_empresa` - Sector del empleador
- `salario_min`, `salario_max` - Rango salarial
- `skills_tecnicas_list` - Skills tecnicas (JSON)
- `soft_skills_list` - Soft skills (JSON)
- `educacion_requerida` - Nivel educativo
- `experiencia_anios` - Anos requeridos

### 3.3 Tabla `ofertas` (datos crudos scraping)

- `fecha_publicacion` - Para series temporales
- `fecha_scraping` - Para frescura de datos
- `url` - Link original
- `portal` - Fuente (bumeran, zonajobs, etc)
- `estado` - activa/cerrada

---

## 4. Gaps Identificados

### 4.1 Datos que FALTAN

| Dato requerido | Para que | Solucion |
|----------------|----------|----------|
| Historico mensual largo | Graficos temporales | Solo tenemos ~2 meses de datos validados |
| Skills ESCO categorizadas | Tab Requerimientos | Tenemos `skills_oferta_json` pero sin L1/L2 |
| Comparativa vs periodo anterior | Deltas en KPIs | Calcular sobre datos existentes |

### 4.2 Datos que SOBRAN (podemos agregar al dash)

| Dato disponible | Uso potencial |
|-----------------|---------------|
| `modalidad` | Filtro/grafico remoto vs presencial |
| `nivel_seniority` | Filtro/grafico por nivel |
| `sector_empresa` | Grafico por sector |
| `salario_min/max` | Rangos salariales por ocupacion |
| `match_method` | % reglas vs semantico (calidad) |
| `area_funcional` | Distribucion por area |

---

## 5. Propuesta de Adaptacion

### Fase A: Replicar diseño actual con datos reales

1. **KPIs**: Conectar a queries SQL sobre ofertas validadas
2. **Graficos**: Usar misma estructura, datos de nuestra BD
3. **Filtros**: Implementar sobre campos existentes

### Fase B: Enriquecer con datos adicionales

1. Agregar filtro por `modalidad` (remoto/hibrido/presencial)
2. Agregar filtro por `seniority`
3. Agregar grafico de sectores
4. Agregar rangos salariales

### Fase C: Tab Requerimientos (Skills)

1. Top skills tecnicas demandadas
2. Skills por ocupacion
3. Skills digitales vs no digitales
4. Evolucion de skills en el tiempo

### Fase D: Tab Ofertas (Tabla detallada)

1. Tabla con busqueda y filtros
2. Columnas: titulo, empresa, ubicacion, ISCO, skills, salario
3. Link a oferta original
4. Export CSV

---

## 6. Queries SQL Listas para Dashboard

```sql
-- KPI: Total ofertas validadas
SELECT COUNT(*) FROM ofertas_esco_matching
WHERE estado_validacion = 'validado';

-- KPI: Ocupaciones distintas
SELECT COUNT(DISTINCT isco_code) FROM ofertas_esco_matching
WHERE estado_validacion = 'validado';

-- Top 10 ocupaciones
SELECT isco_code, isco_label, COUNT(*) as ofertas
FROM ofertas_esco_matching
WHERE estado_validacion = 'validado'
GROUP BY isco_code, isco_label
ORDER BY ofertas DESC
LIMIT 10;

-- Distribucion geografica
SELECT n.provincia, COUNT(*) as ofertas
FROM ofertas_nlp n
JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
WHERE m.estado_validacion = 'validado'
GROUP BY n.provincia
ORDER BY ofertas DESC;

-- Evolucion temporal (por semana)
SELECT strftime('%Y-%W', o.fecha_publicacion) as semana, COUNT(*) as ofertas
FROM ofertas o
JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
WHERE m.estado_validacion = 'validado'
GROUP BY semana
ORDER BY semana;

-- Distribucion por modalidad
SELECT n.modalidad, COUNT(*) as ofertas
FROM ofertas_nlp n
JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
WHERE m.estado_validacion = 'validado'
GROUP BY n.modalidad;

-- Distribucion por seniority
SELECT n.nivel_seniority, COUNT(*) as ofertas
FROM ofertas_nlp n
JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
WHERE m.estado_validacion = 'validado'
GROUP BY n.nivel_seniority;
```

---

## 7. Proximos Pasos

1. [ ] Obtener acceso a Supabase para ver schema actual
2. [ ] Verificar que sync_to_supabase.py sube todos los campos necesarios
3. [ ] Definir API/views en Supabase para el dashboard
4. [ ] Conectar dashboard Next.js a datos reales
