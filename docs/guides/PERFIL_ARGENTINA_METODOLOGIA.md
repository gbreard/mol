# Perfil Argentina - Metodologia de Calculo

## Descripcion

El tab "Perfil Argentina" compara las skills que el mercado laboral argentino demanda (extraidas de ofertas de empleo) vs las skills que la taxonomia ESCO define para cada ocupacion.

**Objetivo:** Identificar el "perfil argentino" de cada ocupacion - diferencias entre la demanda local y el estandar europeo.

---

## Fuentes de Datos

### 1. Skills ESCO (Referencia Europea)
- **Fuente:** RDF oficial ESCO v1.2.0
- **Archivo:** `public/data/occupation_full_detail.json`
- **Contenido:** 3,045 ocupaciones con sus skills/conocimientos esenciales y opcionales
- **Estructura:**
  ```json
  {
    "uuid-ocupacion": {
      "label": "Nombre ocupacion",
      "isco": "2514",
      "skills": {
        "essential": [{ "id": "...", "label": "Python", "L1": "T4", "L2": "T4.2" }],
        "optional": [...]
      },
      "knowledge": {
        "essential": [...],
        "optional": [...]
      }
    }
  }
  ```

### 2. Skills MOL (Demanda Argentina)
- **Fuente:** Ofertas de empleo scrapeadas y procesadas
- **Tablas Supabase:**
  - `ofertas`: Contiene `esco_occupation_uri` (ocupacion asignada)
  - `ofertas_skills`: Contiene `esco_skill_label` (skills extraidas)
- **Proceso de extraccion:** NLP v11 + BGE-M3 embeddings + matching ESCO

---

## Metodologia de Comparacion

### Nivel de Agregacion

**IMPORTANTE:** La comparacion se hace a nivel de **ocupacion ESCO especifica** (URI), NO a nivel ISCO.

- **ISCO** es una categoria amplia (ej: "2514 - Programadores")
- **ESCO** es una ocupacion especifica (ej: "Desarrollador de aplicaciones web")

Agrupar por ISCO mezclaria skills de multiples ocupaciones ESCO, invalidando la comparacion.

### Normalizacion de Labels

Para comparar skills se normalizan los labels:

```python
def normalize(label: str) -> str:
    return label.strip().lower()

# Ejemplo:
# "Gestionar relaciones con clientes" -> "gestionar relaciones con clientes"
# " Python " -> "python"
```

**Nota:** No se compara por URI porque `esco_skill_uri` es NULL en muchos registros de `ofertas_skills`.

---

## Indicadores y Formulas

### 1. Cobertura Esencial

**Definicion:** Porcentaje de skills ESCO esenciales que el mercado argentino efectivamente demanda.

**Formula:**
```
Cobertura Esencial = (Skills en comun / Total skills esenciales ESCO) * 100

Donde:
- Skills en comun = MOL ∩ ESCO_essential
- Total skills esenciales ESCO = |ESCO_essential|
```

**Ejemplo:**
- ESCO define 20 skills esenciales para "Representante Comercial"
- En ofertas MOL detectamos 12 de esas 20
- Cobertura Esencial = 12/20 * 100 = **60%**

**Interpretacion:**
- **≥70%:** El mercado argentino demanda la mayoria de skills del estandar europeo
- **40-69%:** Cobertura parcial, algunas skills no se mencionan
- **<40%:** Gran brecha entre demanda local y estandar ESCO

---

### 2. Skills Emergentes

**Definicion:** Skills que el mercado argentino pide pero que NO estan definidas en ESCO para esa ocupacion.

**Formula:**
```
Skills Emergentes = MOL - (ESCO_essential ∪ ESCO_optional)

Donde:
- MOL = conjunto de skills detectadas en ofertas argentinas
- ESCO_essential ∪ ESCO_optional = todas las skills ESCO (esenciales + opcionales)
```

**Ejemplo:**
- Para "Desarrollador de Software", ESCO no incluye "Docker" ni "Kubernetes"
- Si ofertas argentinas piden Docker (45%) y Kubernetes (30%)
- Estas son skills **emergentes** - demanda local que ESCO no contempla

**Interpretacion:**
- Skills que el mercado argentino valora pero ESCO no reconoce
- Pueden ser tecnologias nuevas, herramientas locales, o especificidades del mercado
- Util para identificar tendencias locales

---

### 3. Skills Faltantes

**Definicion:** Skills que ESCO define como esenciales pero que NO detectamos en ofertas argentinas.

**Formula:**
```
Skills Faltantes = ESCO_essential - MOL
```

**Ejemplo:**
- ESCO dice que "Representante Comercial" debe saber "Analisis de mercado"
- No detectamos esa skill en las 41 ofertas analizadas
- Es una skill **faltante**

**Interpretacion:**
- Puede indicar que:
  1. El mercado argentino no valora esa skill (diferencia cultural)
  2. La skill se asume implicita y no se menciona en ofertas
  3. El NLP no la esta detectando correctamente
- Requiere analisis caso por caso

---

### 4. Cobertura Total

**Definicion:** Porcentaje de TODAS las skills ESCO (esenciales + opcionales) detectadas en MOL.

**Formula:**
```
Cobertura Total = (MOL ∩ ESCO_all / |ESCO_all|) * 100

Donde:
- ESCO_all = ESCO_essential ∪ ESCO_optional
```

**Ejemplo:**
- ESCO define 20 esenciales + 15 opcionales = 35 totales
- Detectamos 15 de esas 35
- Cobertura Total = 15/35 * 100 = **43%**

**Interpretacion:**
- Metrica mas laxa que incluye opcionales
- Util para ver el overlap general

---

### 5. Tamano de Muestra (Ofertas)

**Definicion:** Cantidad de ofertas de empleo usadas para construir el perfil de cada ocupacion.

**Umbrales de confiabilidad:**

| Ofertas | Calificacion | Color | Interpretacion |
|---------|--------------|-------|----------------|
| ≥30 | Muestra representativa | Verde | Alta confianza estadistica |
| 10-29 | Muestra moderada | Amarillo | Interpretable con precaucion |
| <10 | Muestra chica | Naranja | Solo indicativo, no tomar decisiones |

**Justificacion estadistica:**
- 30+ ofertas: Teorema del limite central, distribucion tiende a normal
- 10-29: Suficiente para detectar tendencias, pero con varianza alta
- <10: Muy susceptible a outliers, un solo caso puede distorsionar

---

## Proceso de Generacion de Datos

### Script: `generate_mol_skills_profile.py`

```
1. Cargar occupation_full_detail.json (ESCO)

2. Consultar Supabase (con paginacion):
   SELECT o.esco_occupation_uri, o.esco_occupation_label,
          s.esco_skill_label, COUNT(*) as freq
   FROM ofertas o
   JOIN ofertas_skills s ON o.id_oferta = s.id_oferta
   WHERE o.esco_occupation_uri IS NOT NULL
     AND s.esco_skill_label IS NOT NULL
   GROUP BY 1, 2, 3

3. Por cada ocupacion ESCO:
   a. Extraer UUID de URI (para matchear con JSON)
   b. Normalizar labels de skills
   c. Crear sets: mol_set, esco_essential_set, esco_optional_set
   d. Calcular: common, emerging, missing
   e. Calcular porcentajes

4. Guardar mol_skills_profile.json
```

### Output: `mol_skills_profile.json`

```json
{
  "version": "1.0.0",
  "generated_at": "2026-02-03T...",
  "stats": {
    "total_offers": 838,
    "total_occupations_with_mol": 254,
    "avg_skills_per_offer": 10.5
  },
  "occupations": {
    "uuid-ocupacion": {
      "esco_uuid": "uuid-ocupacion",
      "esco_label": "Representante comercial",
      "offer_count": 41,
      "mol_skills": [
        {
          "label_original": "Gestion de clientes",
          "label_normalized": "gestion de clientes",
          "frequency": 35,
          "percentage": 85.4,
          "is_esco_essential": true,
          "is_esco_optional": false,
          "is_emerging": false
        }
      ],
      "comparison": {
        "coverage_essential": 50.0,
        "coverage_total": 38.5,
        "common_count": 14,
        "emerging_count": 180,
        "missing_count": 14,
        "esco_essential_count": 28,
        "esco_optional_count": 15,
        "common_labels": ["gestion de clientes", ...],
        "emerging_labels": ["crm", "excel", ...],
        "missing_labels": ["analisis de mercado", ...]
      }
    }
  }
}
```

---

## Limitaciones Conocidas

1. **Calidad del NLP:** Si el NLP no extrae bien una skill, no aparecera en MOL
2. **Sinonimos:** "Python" y "Programacion en Python" se cuentan como diferentes
3. **Ofertas sesgadas:** Solo incluye ofertas scrapeadas (portales especificos)
4. **Skills implicitas:** Algunas skills basicas no se mencionan por obvias
5. **Temporalidad:** El perfil refleja un momento especifico, no tendencias

---

## Casos de Uso

### 1. Identificar brechas de formacion
- Skills faltantes = temas que las instituciones educativas deberian reforzar

### 2. Validar curriculas
- Cobertura esencial alta = curricula alineada con mercado

### 3. Detectar tendencias locales
- Skills emergentes = tecnologias/herramientas que Argentina adopta antes que ESCO actualice

### 4. Orientacion laboral
- Mostrar a candidatos que skills priorizar segun mercado local

---

## Regenerar Datos

```bash
cd fase3_dashboard/mol-dashboard/scripts
python generate_mol_skills_profile.py
```

Ejecutar periodicamente (semanal/mensual) para mantener actualizado.
