# PLAN DE IMPLEMENTACIÓN - Tarea 4: Normalización Territorial

**Proyecto:** MOL v2.0 - FASE 1
**Fecha inicio:** 17/11/2025
**Status:** En progreso (10% - investigación completada)
**Responsable:** Equipo Técnico OEDE

---

## OBJETIVO

Normalizar las ubicaciones de las ofertas laborales contra códigos oficiales INDEC para:
1. Estandarizar nombres de provincias y localidades
2. Asignar códigos INDEC oficiales
3. Facilitar queries territoriales en dashboards
4. Validar >80% de ofertas con ubicación normalizada

---

## INVESTIGACIÓN COMPLETADA (10%)

### Análisis del Campo Actual

**Campo existente:** `localizacion` (columna 6 de tabla `ofertas`)

**Formato:** "Localidad, Provincia"

**Estadísticas:**
- Total ofertas: 6,521
- Ofertas con localización: 6,502 (99.7%)
- Ofertas sin localización: 19 (0.3%)

**Top 10 ubicaciones:**
```
2,836  Capital Federal, Buenos Aires
  175  Córdoba, Córdoba
  173  Pilar, Buenos Aires
  164  Rosario, Santa Fe
  133  Buenos Aires, Buenos Aires
  127  Vicente López, Buenos Aires
  120  San Martin, Buenos Aires
   92  La Plata, Buenos Aires
   89  San Isidro, Buenos Aires
   75  Martínez, Buenos Aires
```

**Observaciones:**
1. Formato consistente: "Localidad, Provincia"
2. Cobertura excelente: 99.7%
3. Alta concentración en AMBA: ~60% de ofertas
4. Nombres no normalizados (variaciones posibles)

### Hallazgos Clave

1. **Ya tenemos datos de ubicación** - No necesitamos scraping adicional
2. **Formato consistente** - Parsing simple con split(",")
3. **Alta cobertura** - Ya cumplimos objetivo de >80%
4. **Desafío principal**: Normalizar variaciones de nombres (ej: "Capital Federal" vs "CABA" vs "Ciudad de Buenos Aires")

---

## ESTRATEGIA SIMPLIFICADA

Dado que ya tenemos los datos, la tarea se simplifica a:

### PASO 1: Parsear campo `localizacion` (20%)
- Separar en `localidad_raw` y `provincia_raw`
- Limpiar espacios y normalizar casing
- Identificar casos especiales (CABA, GBA)

### PASO 2: Crear tablas de referencia INDEC (20%)
- Tabla `indec_provincias`: 24 provincias con códigos oficiales
- Tabla `indec_localidades`: Top 500-1000 localidades más frecuentes
- Fuente: Manual + datos INDEC públicos

### PASO 3: Matching directo + fuzzy (30%)
- Matching exacto por nombre normalizado (80% esperado)
- Fuzzy matching para variaciones (10% esperado)
- Manual/mapping para casos especiales (5% esperado)
- No match → mantener raw (5% esperado)

### PASO 4: Agregar columnas normalizadas (20%)
- `provincia_normalizada` - Nombre oficial INDEC
- `codigo_provincia_indec` - Código de 2 dígitos
- `localidad_normalizada` - Nombre oficial (si existe en INDEC)
- `codigo_localidad_indec` - Código de 6 dígitos (si existe)

### PASO 5: Validación (10%)
- Verificar >80% de ofertas con provincia normalizada
- Verificar >60% de ofertas con localidad normalizada
- Documentar casos no normalizados

---

## SCHEMA DE BASE DE DATOS

### Tabla: `indec_provincias`
```sql
CREATE TABLE IF NOT EXISTS indec_provincias (
    codigo_provincia TEXT PRIMARY KEY,      -- "02", "06", etc.
    nombre_oficial TEXT NOT NULL,           -- "Ciudad Autónoma de Buenos Aires"
    nombre_comun TEXT NOT NULL,             -- "CABA"
    variantes TEXT,                         -- JSON array de variantes
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla: `indec_localidades` (opcional - solo top N)
```sql
CREATE TABLE IF NOT EXISTS indec_localidades (
    codigo_localidad TEXT PRIMARY KEY,     -- "060007" (provincia+localidad)
    codigo_provincia TEXT NOT NULL,        -- "06"
    nombre_oficial TEXT NOT NULL,          -- "La Plata"
    variantes TEXT,                         -- JSON array de variantes
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (codigo_provincia) REFERENCES indec_provincias(codigo_provincia)
);
```

### Columnas a agregar en `ofertas`:
```sql
ALTER TABLE ofertas ADD COLUMN provincia_normalizada TEXT;
ALTER TABLE ofertas ADD COLUMN codigo_provincia_indec TEXT;
ALTER TABLE ofertas ADD COLUMN localidad_normalizada TEXT;
ALTER TABLE ofertas ADD COLUMN codigo_localidad_indec TEXT;
```

---

## CÓDIGOS INDEC - 24 PROVINCIAS

```python
PROVINCIAS_INDEC = {
    "02": {
        "nombre_oficial": "Ciudad Autónoma de Buenos Aires",
        "nombre_comun": "CABA",
        "variantes": ["Capital Federal", "Ciudad de Buenos Aires", "Buenos Aires Capital"]
    },
    "06": {
        "nombre_oficial": "Buenos Aires",
        "nombre_comun": "Buenos Aires",
        "variantes": ["Provincia de Buenos Aires", "Bs. As.", "Bs As", "Pcia. Bs. As."]
    },
    "10": {
        "nombre_oficial": "Catamarca",
        "nombre_comun": "Catamarca",
        "variantes": []
    },
    "14": {
        "nombre_oficial": "Córdoba",
        "nombre_comun": "Córdoba",
        "variantes": ["Cordoba"]
    },
    "18": {
        "nombre_oficial": "Corrientes",
        "nombre_comun": "Corrientes",
        "variantes": []
    },
    "22": {
        "nombre_oficial": "Chaco",
        "nombre_comun": "Chaco",
        "variantes": []
    },
    "26": {
        "nombre_oficial": "Chubut",
        "nombre_comun": "Chubut",
        "variantes": []
    },
    "30": {
        "nombre_oficial": "Entre Ríos",
        "nombre_comun": "Entre Ríos",
        "variantes": ["Entre Rios"]
    },
    "34": {
        "nombre_oficial": "Formosa",
        "nombre_comun": "Formosa",
        "variantes": []
    },
    "38": {
        "nombre_oficial": "Jujuy",
        "nombre_comun": "Jujuy",
        "variantes": []
    },
    "42": {
        "nombre_oficial": "La Pampa",
        "nombre_comun": "La Pampa",
        "variantes": []
    },
    "46": {
        "nombre_oficial": "La Rioja",
        "nombre_comun": "La Rioja",
        "variantes": []
    },
    "50": {
        "nombre_oficial": "Mendoza",
        "nombre_comun": "Mendoza",
        "variantes": []
    },
    "54": {
        "nombre_oficial": "Misiones",
        "nombre_comun": "Misiones",
        "variantes": []
    },
    "58": {
        "nombre_oficial": "Neuquén",
        "nombre_comun": "Neuquén",
        "variantes": ["Neuquen"]
    },
    "62": {
        "nombre_oficial": "Río Negro",
        "nombre_comun": "Río Negro",
        "variantes": ["Rio Negro"]
    },
    "66": {
        "nombre_oficial": "Salta",
        "nombre_comun": "Salta",
        "variantes": []
    },
    "70": {
        "nombre_oficial": "San Juan",
        "nombre_comun": "San Juan",
        "variantes": []
    },
    "74": {
        "nombre_oficial": "San Luis",
        "nombre_comun": "San Luis",
        "variantes": []
    },
    "78": {
        "nombre_oficial": "Santa Cruz",
        "nombre_comun": "Santa Cruz",
        "variantes": []
    },
    "82": {
        "nombre_oficial": "Santa Fe",
        "nombre_comun": "Santa Fe",
        "variantes": []
    },
    "86": {
        "nombre_oficial": "Santiago del Estero",
        "nombre_comun": "Santiago del Estero",
        "variantes": []
    },
    "90": {
        "nombre_oficial": "Tucumán",
        "nombre_comun": "Tucumán",
        "variantes": ["Tucuman"]
    },
    "94": {
        "nombre_oficial": "Tierra del Fuego",
        "nombre_comun": "Tierra del Fuego",
        "variantes": ["Tierra del Fuego, Antártida e Islas del Atlántico Sur"]
    }
}
```

---

## MÉTRICAS DE ÉXITO

1. ✅ Investigación de datos existentes completada
2. ⏳ Tablas INDEC creadas y cargadas
3. ⏳ Parser de campo `localizacion` implementado
4. ⏳ Algoritmo de normalización implementado
5. ⏳ >80% de ofertas con `provincia_normalizada`
6. ⏳ >60% de ofertas con `localidad_normalizada`
7. ⏳ Columnas agregadas a tabla `ofertas`
8. ⏳ Documentación y commit realizados

**Status actual:** 1/8 completadas (12.5%)

---

## PRÓXIMOS PASOS INMEDIATOS

### Sesión siguiente (17/11/2025 - tarde):

1. Crear script `populate_indec_provincias.py`
   - Cargar 24 provincias con códigos y variantes
   - Validar carga exitosa

2. Crear script `normalizar_ubicaciones.py`
   - Parser de campo `localizacion`
   - Matching de provincias (exacto + variantes)
   - Fuzzy matching para localidades comunes
   - Actualizar columnas en `ofertas`

3. Testing y validación
   - Verificar cobertura >80% provincias
   - Verificar cobertura >60% localidades
   - Identificar casos no normalizados

4. Documentación y commit
   - Actualizar PROGRESO_FASE_1.md
   - Commit de Tarea 4 completada

---

## CRONOGRAMA ESTIMADO

| Paso | Descripción | Tiempo | Status |
|------|-------------|--------|--------|
| 1 | Investigación datos existentes | 30min | ✅ COMPLETADO |
| 2 | Crear tablas INDEC | 1h | ⏳ PENDIENTE |
| 3 | Script de normalización | 2h | ⏳ PENDIENTE |
| 4 | Testing y validación | 1h | ⏳ PENDIENTE |
| 5 | Documentación y commit | 30min | ⏳ PENDIENTE |
| **TOTAL** | **5 horas** | **10% completado** |

---

## DECISIONES TÉCNICAS

### 1. Estrategia simplificada vs completa

**Decisión:** Implementar estrategia simplificada (parsear campo existente)

**Alternativa considerada:** Scraping de APIs de INDEC para todas las localidades

**Razón:**
- Ya tenemos 99.7% de cobertura
- Formato consistente
- Más rápido y pragmático
- Suficiente para objetivos de FASE 1

### 2. Alcance de localidades INDEC

**Decisión:** Cargar solo top 100-200 localidades más frecuentes

**Razón:**
- ~80% de ofertas en top localidades
- Evita cargar ~5,000 localidades innecesarias
- Mejora performance de matching

### 3. Fuzzy matching threshold

**Decisión:** 85% similarity (Levenshtein)

**Razón:** Balance entre precisión y recall para variaciones comunes

---

## RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Variaciones de nombres no cubiertas | Media | Bajo | Logging de casos no normalizados para análisis posterior |
| Ambigüedades (múltiples matches) | Baja | Medio | Usar match más frecuente en BD |
| Performance en 6,500 ofertas | Baja | Bajo | Optimizar con índices SQL |

---

**Última actualización:** 17/11/2025 15:00
**Próxima sesión:** 17/11/2025 (tarde)
**Responsable:** Equipo Técnico OEDE + Claude Code
**Progreso Tarea 4:** 10% completado (investigación)
