# Skills Intelligence Dashboard

## Descripcion

Dashboard interactivo para explorar la taxonomia ESCO de competencias (skills y conocimientos), analizar ocupaciones y planificar transiciones laborales.

**Acceso:** Admin Panel > Skills Intelligence
**URL:** https://mol-nextjs.vercel.app/admin/skills

## Funcionalidades (4 Tabs)

### 1. Taxonomia (Sunburst)

Visualizacion jerarquica de las ~14,000 competencias ESCO en formato sunburst.

**Caracteristicas:**
- Grafico interactivo con drill-down por categorias
- Busqueda de competencias con highlight
- Filtro por tipo: Skills / Conocimientos / Todos
- Click en segmento muestra lista de competencias

**Categorias principales:**
| Codigo | Nombre | Descripcion |
|--------|--------|-------------|
| S1-S8 | Competencias Tecnicas | Habilidades especificas de un campo profesional |
| T1-T6 | Competencias Transversales | Capacidades aplicables a cualquier ocupacion |
| K | Conocimientos | Informacion y conceptos teoricos |

### 2. Ocupacion (Detalle)

Muestra skills y conocimientos requeridos para una ocupacion especifica.

**Incluye:**
- Skills esenciales y opcionales
- Conocimientos esenciales y opcionales
- **Descripciones ESCO** de cada competencia (click para expandir)
- Ocupaciones similares (por Jaccard similarity)
- Link para comparar con otra ocupacion

### 3. Comparar (Gap Analysis)

Compara dos ocupaciones para analizar:
- Skills compartidas
- Skills exclusivas de A
- Skills exclusivas de B
- **Gap de competencias** para transicion laboral

**Caso de uso:** Planificar transiciones de carrera identificando que competencias faltan.

### 4. Mis Skills (Matching)

El usuario ingresa sus competencias y el sistema encuentra ocupaciones compatibles.

**Algoritmo:**
1. Usuario busca y selecciona skills del catalogo ESCO
2. Sistema calcula match con cada ocupacion
3. Ordena por % de skills esenciales cubiertas
4. Muestra gap (competencias faltantes)

**Metricas:**
- `matchScore`: % de skills esenciales que el usuario tiene
- `gapCount`: Cantidad de skills esenciales faltantes

---

## Datos (JSONs)

Los datos se generan desde el RDF de ESCO y se guardan en `public/data/`:

| Archivo | Tamano | Contenido |
|---------|--------|-----------|
| `esco_skills_hierarchy.json` | 3.2 MB | Arbol jerarquico para Sunburst |
| `occupation_full_detail.json` | 45 MB | Detalle completo de 3,045 ocupaciones |
| `skills_searchable.json` | 5 MB | 14,257 skills con descripciones |
| `occupation_similarity.json` | 4.1 MB | Similitud entre ocupaciones |

### Regenerar Datos

Si se actualiza ESCO o se agregan descripciones:

```bash
cd fase3_dashboard/mol-dashboard/scripts

# 1. Generar similitud entre ocupaciones
python generate_occupation_similarity.py

# 2. Generar detalle completo (requiere paso 1)
python generate_occupation_full_detail.py

# 3. Generar indice de skills buscables
python generate_skills_searchable.py

# 4. (Opcional) Extraer descripciones del RDF
python ../../scripts/extract_esco_descriptions.py
```

---

## Componentes React

| Componente | Ubicacion | Funcion |
|------------|-----------|---------|
| `SkillsSunburst.tsx` | `components/` | Grafico sunburst D3.js |
| `OccupationDetail.tsx` | `components/` | Tab de detalle de ocupacion |
| `OccupationCompare.tsx` | `components/` | Tab de comparacion |
| `MySkillsSearch.tsx` | `components/` | Tab de matching por skills |
| `SkillsList.tsx` | `components/` | Lista de skills con descripciones |
| `OccupationSelector.tsx` | `components/` | Dropdown de seleccion |
| `SimilarOccupations.tsx` | `components/` | Lista de ocupaciones similares |

---

## Tipos TypeScript

```typescript
// lib/types.ts

interface SkillItem {
  id: string;
  label: string;
  L1: string;           // Categoria nivel 1 (ej: "S1")
  L2: string;           // Categoria nivel 2 (ej: "S1.1")
  description?: string; // Definicion ESCO en espanol
}

interface OccupationDetail {
  label: string;
  isco: string;
  skills: {
    essential: SkillItem[];
    optional: SkillItem[];
  };
  knowledge: {
    essential: SkillItem[];
    optional: SkillItem[];
  };
  similar: SimilarOccupation[];
}

interface SearchableSkill {
  id: string;
  label: string;
  type: 'skill' | 'knowledge';
  L1: string;
  L2: string;
  essential: number;    // Ocupaciones que la requieren como esencial
  optional: number;     // Ocupaciones que la requieren como opcional
  total: number;
  description?: string;
}
```

---

## Fuente de Datos

Los datos provienen del RDF oficial de ESCO v1.2.0:

```
/mnt/d/Trabajos en PY/EPH-ESCO/01_datos_originales/Tablas_esco/Data/esco-v1.2.0.rdf
```

- **Tamano:** 1.35 GB
- **Skills:** 14,257 (skills + conocimientos)
- **Ocupaciones:** 3,045
- **Descripciones:** Extraidas del namespace `dct:description` con `xml:lang="es"`

---

## Historial de Versiones

| Fecha | Version | Cambios |
|-------|---------|---------|
| 2026-02-02 | v1.1 | Acceso via Admin Panel (auth protegido) |
| 2026-02-01 | v1.0 | 4 tabs completas + descripciones ESCO |
| 2026-01-31 | v0.9 | Sunburst + Ocupacion + Comparar |
| 2026-01-30 | v0.1 | Sunburst inicial |
