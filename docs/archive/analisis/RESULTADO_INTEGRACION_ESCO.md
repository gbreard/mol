# Resultados de Integración ZonaJobs + ESCO

**Fecha**: 2025-10-16
**Versión**: 1.0 - Prueba de Concepto

---

## 📊 Resumen Ejecutivo

Se realizó exitosamente la **integración semántica** entre las ofertas laborales scrapeadas de ZonaJobs y la ontología ESCO, utilizando algoritmos de matching semántico en español y enriquecimiento con skills y conocimientos.

### Resultados Principales

| Métrica | Valor |
|---------|-------|
| **Ofertas procesadas** | 61 |
| **Ofertas clasificadas** | 37 (60.7%) |
| **Ofertas sin clasificar** | 24 (39.3%) |
| **Promedio de similitud** | 0.496 |
| **Ocupaciones ESCO utilizadas** | 1,886 |
| **Skills disponibles** | 6,818 |
| **Ofertas enriquecidas con skills** | 34 (91.9% de clasificadas) |

---

## 🎯 Metodología

### 1. Matching Semántico

Se implementó un algoritmo de matching que combina:

- **Normalización de texto en español**: Remoción de acentos, stopwords, caracteres especiales
- **Expansión de sinónimos**: Diccionario Argentina-España (programador↔desarrollador, gerente↔director)
- **Similitud de secuencias**: SequenceMatcher de Python
- **Similitud de tokens**: Jaccard similarity
- **Score ponderado**: 30% similitud básica + 40% tokens + 30% sinónimos

**Threshold utilizado**: 0.4 (permisivo para POC)

### 2. Enriquecimiento con Skills

Para cada ocupación ESCO matcheada:
- Se extrajeron **skills esenciales** (promedio: 3.4 por oferta)
- Se extrajeron **skills opcionales**
- Se utilizaron labels en español cuando están disponibles

---

## 📈 Resultados Detallados

### Top 10 Ocupaciones ESCO Identificadas

1. **Asistente de gestión** - 3 ofertas
2. **Analista de datos** - 3 ofertas
3. **Responsable de recursos humanos** - 2 ofertas
4. **Vendedor de electrodomésticos** - 2 ofertas
5. **Responsable de eventos** - 2 ofertas
6. **Gerente de tienda** - 2 ofertas
7. **Personal de apoyo administrativo** - 2 ofertas
8. **Técnico administrativo de gestión** - 1 oferta
9. **Responsable de instalaciones** - 1 oferta
10. **Especialista en botánica** - 1 oferta

### Distribución de Calidad de Matching

| Rango de Similitud | Cantidad | Porcentaje |
|-------------------|----------|------------|
| 0.60 - 0.65 (Alta) | 3 | 8.1% |
| 0.55 - 0.60 | 5 | 13.5% |
| 0.50 - 0.55 | 11 | 29.7% |
| 0.45 - 0.50 (Media) | 12 | 32.4% |
| 0.40 - 0.45 (Baja) | 6 | 16.2% |

---

## 💡 Ejemplos de Matching

### Ejemplo 1: Alta Similitud (0.627)

**Oferta Original:**
- Título: "JEFE/A DE RECURSOS HUMANOS"
- Empresa: Piroska, Deak y Asociados

**Match ESCO:**
- Ocupación: Responsable de recursos humanos
- Similitud: 0.627

**Skills Esenciales:**
- Documentar entrevistas
- Elaborar perfiles
- Negociar los contratos laborales
- Estrategias de gestión del talento

**Skills Opcionales:**
- Favorecer la empleabilidad de las personas con discapacidad
- Elaborar programas de retención de los trabajadores
- Comunicación empresarial

---

### Ejemplo 2: Similitud Media (0.531)

**Oferta Original:**
- Título: "TECNICO ADMINISTRATIVO DE LABORATORIO"
- Empresa: Confidencial

**Match ESCO:**
- Ocupación: Técnico administrativo de gestión/técnica administrativa de gestión
- Similitud: 0.531

**Matches Alternativos:**
- Técnico de laboratorio físico (0.495)
- Fisiólogo/fisióloga (0.482)

---

## 📁 Archivos Generados

### Ubicación
```
D:\OEDE\Webscrapping\data\processed\
```

### Archivos

1. **zonajobs_esco_enriquecida_[timestamp].csv**
   - Formato: CSV plano
   - Columnas: 26 campos
   - Uso: Importación a bases de datos, análisis en Excel

2. **zonajobs_esco_enriquecida_[timestamp].json**
   - Formato: JSON
   - Uso: APIs, procesamiento con Python/JavaScript

3. **zonajobs_esco_analisis_[timestamp].xlsx**
   - Formato: Excel con 4 hojas
   - Hojas:
     - Ofertas Enriquecidas
     - Top Ocupaciones ESCO
     - Distribución ISCO
     - Estadísticas de Similitud

---

## 🔧 Estructura de Datos

### Campos Disponibles en CSV/JSON

**Datos Originales:**
- `id_oferta`, `titulo_original`, `empresa`, `localizacion`
- `modalidad_trabajo`, `tipo_trabajo`, `fecha_publicacion`, `url_oferta`

**Matching ESCO:**
- `esco_match_1_id`: ID de la ocupación ESCO
- `esco_match_1_label`: Nombre de la ocupación en español
- `esco_match_1_isco_4d`: Código ISCO de 4 dígitos
- `esco_match_1_isco_2d`: Código ISCO de 2 dígitos (grupo)
- `esco_match_1_similitud`: Score de similitud (0-1)

**Matches Alternativos:**
- `esco_match_2_label`, `esco_match_2_similitud`
- `esco_match_3_label`, `esco_match_3_similitud`

**Skills:**
- `skills_esenciales_top5`: Top 5 skills esenciales (separadas por `;`)
- `skills_esenciales_count`: Cantidad total de skills esenciales
- `skills_opcionales_top5`: Top 5 skills opcionales
- `skills_opcionales_count`: Cantidad total de skills opcionales

**Metadata:**
- `fecha_clasificacion`: Timestamp de la clasificación
- `clasificada`: Boolean (True/False)

---

## ⚠️ Limitaciones Conocidas

### 1. Códigos ISCO Incompletos

**Problema:** De las 1,886 ocupaciones ESCO cargadas, solo 2 tienen códigos ISCO de 4 dígitos.

**Causa:** Los archivos JSON procesados (`esco_consolidado_con_isco.json`) no extrajeron todos los códigos ISCO del RDF original.

**Impacto:** No se pueden hacer análisis por grupos ISCO (CIUO) de forma completa.

**Solución propuesta:**
- Opción A: Extraer directamente del RDF usando `rdflib` en Python
- Opción B: Consultar el endpoint SPARQL de Fuseki (si está corriendo)
- Opción C: Usar archivos RDF más pequeños o CSV pre-procesados

### 2. Threshold Permisivo

**Configuración actual:** 0.4 (40% de similitud mínima)

**Razón:** Para esta prueba de concepto, se utilizó un threshold permisivo para maximizar matches.

**Resultado:** Algunos matches tienen similitud baja (40-45%), lo que puede indicar clasificaciones menos precisas.

**Recomendación:** Para producción, usar threshold de 0.6 (60%).

### 3. Skills sin Contexto

**Situación:** Las skills se presentan como listas sin jerarquía ni agrupación.

**Mejora posible:** Agrupar skills por categorías (técnicas, blandas, conocimientos).

---

## 🚀 Próximos Pasos

### Para Mejorar el Matching

1. **Implementar embeddings semánticos**
   - Usar `sentence-transformers` con modelo multilingüe
   - Modelos recomendados: `paraphrase-multilingual-MiniLM-L12-v2`

2. **Entrenar modelo específico**
   - Crear dataset de matching manual (ground truth)
   - Fine-tuning de modelo de similitud

3. **Análisis de descripciones**
   - Actualmente solo se usa el título
   - Incorporar análisis de la descripción completa de la oferta

### Para Completar Códigos ISCO

1. **Extracción directa del RDF**
   ```python
   import rdflib
   g = rdflib.Graph()
   g.parse("esco-v1.2.0.rdf", format="xml")
   # Query SPARQL para extraer occupations con ISCO
   ```

2. **Mapeo manual para ocupaciones más comunes**
   - Identificar top 50 ocupaciones sin ISCO
   - Asignar códigos CIUO manualmente basado en documentación

### Para Producción

1. **Automatización**
   - Script scheduled para scraping diario
   - Clasificación automática de nuevas ofertas
   - Alertas por ocupaciones de interés

2. **Base de datos**
   - Migrar a PostgreSQL o MongoDB
   - Indexar por ISCO, skills, ubicación
   - API REST para consultas

3. **Dashboard de análisis**
   - Visualización de tendencias
   - Skills más demandadas por sector
   - Distribución geográfica de ocupaciones

---

## 📚 Uso del Sistema

### Cargar Últimos Resultados

```python
import pandas as pd
from pathlib import Path

# Cargar CSV enriquecido
output_dir = Path(r"D:\OEDE\Webscrapping\data\processed")
archivos = list(output_dir.glob("zonajobs_esco_enriquecida_*.csv"))
ultimo = max(archivos, key=lambda x: x.stat().st_mtime)

df = pd.read_csv(ultimo)

# Filtrar solo ofertas clasificadas
clasificadas = df[df['clasificada'] == True]

# Análisis por ocupación
por_ocupacion = clasificadas.groupby('esco_match_1_label').size()
print(por_ocupacion)
```

### Re-ejecutar Clasificación

```bash
cd D:\OEDE\Webscrapping\scripts
python integracion_esco_semantica.py
```

### Ajustar Threshold

Editar en `integracion_esco_semantica.py`:
```python
# Línea final del archivo
integrador.ejecutar_pipeline_completo(threshold=0.6)  # Cambiar de 0.4 a 0.6
```

---

## 📊 Scripts Disponibles

### Principal
- **`integracion_esco_semantica.py`**: Pipeline completo de integración

### Utilidades
- **`mostrar_resultados_muestra.py`**: Muestra ejemplos de ofertas clasificadas
- **`check_isco_codes.py`**: Verifica cobertura de códigos ISCO
- **`find_best_esco_source.py`**: Identifica mejor fuente de datos ESCO

---

## 🎓 Conclusiones

### Éxitos

✅ **Matching funcional**: 60.7% de ofertas clasificadas con similitud promedio de 0.496
✅ **Enriquecimiento con skills**: 34 ofertas (91.9% de clasificadas) tienen skills asociadas
✅ **Pipeline automatizado**: Script reutilizable para futuras scrapeadas
✅ **Múltiples formatos**: CSV, JSON, Excel para diferentes usos
✅ **Documentación completa**: Código comentado y documentación técnica

### Aprendizajes

📌 **Normalización es clave**: La expansión de sinónimos Argentina-España mejora significativamente el matching
📌 **Threshold crítico**: Balance entre cobertura (más matches) y precisión (mejor similitud)
📌 **Skills valiosas**: La información de skills es el verdadero valor agregado de ESCO
📌 **Datos estructurados**: RDF es potente pero requiere procesamiento cuidadoso

### Valor para OEDE

🎯 **Clasificación automática** de ofertas laborales según estándar internacional (ESCO)
🎯 **Identificación de skills** demandadas por el mercado laboral argentino
🎯 **Base para estadísticas** laborales comparables internacionalmente
🎯 **Fundamento para políticas** de formación y capacitación

---

## 📞 Soporte Técnico

**Scripts ubicados en:**
```
D:\OEDE\Webscrapping\scripts\
```

**Datos procesados en:**
```
D:\OEDE\Webscrapping\data\processed\
```

**Documentación completa en:**
```
D:\OEDE\Webscrapping\docs\
```

---

**Desarrollado para OEDE**
**Fecha**: 2025-10-16
**Versión**: 1.0 - Prueba de Concepto
