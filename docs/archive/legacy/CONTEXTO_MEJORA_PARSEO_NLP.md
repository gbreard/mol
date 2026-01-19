# Contexto: Mejora de Parseo NLP - Bumeran

**Fecha:** 2025-11-01
**Objetivo:** Mejorar la calidad del parseo NLP de ofertas laborales de Bumeran

## Estado Actual del Sistema

### Pipeline Completo
```
Scraping → Parseo NLP → Mapeo ESCO → Dashboard
```

### Archivos Clave

1. **Extractor NLP:** `D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts\extractors\bumeran_extractor.py`
2. **Procesador DB→DB:** `D:\OEDE\Webscrapping\database\process_nlp_from_db.py`
3. **Dashboard v4:** `D:\OEDE\Webscrapping\dashboard_scraping_v4.py` (puerto 8053)
4. **Base de datos:** `D:\OEDE\Webscrapping\database\bumeran_scraping.db`

### Métricas Actuales de Calidad

**Datos del Dashboard - Pestaña "Calidad Parseo NLP":**
- **Total ofertas:** 5,479
- **Score promedio:** 2.14/7 (30.6% efectividad)
- **Ofertas mal parseadas (score < 2):** ~1,900 (35%)
- **Ofertas bien parseadas (score >= 4):** ~841 (15%)

**Campos evaluados (0-7):**
1. Experiencia mínima en años
2. Nivel educativo
3. Soft skills
4. Skills técnicas
5. Idioma principal
6. Salario (min/max)
7. Jornada laboral

### Tablas de Base de Datos

**Tabla `ofertas`:**
- id_oferta
- titulo
- descripcion (texto completo)
- fecha_publicacion_datetime
- scrapeado_en
- ... (38 variables totales)

**Tabla `ofertas_nlp`:**
- id_oferta (FK)
- experiencia_min_anios
- experiencia_max_anios
- nivel_educativo
- estado_educativo
- carrera_especifica
- idioma_principal
- nivel_idioma_principal
- skills_tecnicas_list (JSON)
- soft_skills_list (JSON)
- certificaciones_list (JSON)
- salario_min
- salario_max
- moneda
- beneficios_list (JSON)
- requisitos_excluyentes_list (JSON)
- requisitos_deseables_list (JSON)
- jornada_laboral
- horario_flexible
- nlp_extraction_timestamp
- nlp_version
- nlp_confidence_score

## Diagnóstico Inicial

### Correlaciones Identificadas
- **Longitud de descripción vs calidad:** Descripciones muy cortas (< 500 chars) tienen peor parseo
- **Distribución temporal:** La calidad varía por fecha de scraping

### Problemas Detectados
1. **35% de ofertas con score < 2:** Parseo casi nulo
2. **Solo 15% de ofertas con score >= 4:** Parseo aceptable
3. **70% de campos están NULL o vacíos**

## Plan de Mejora

### Fase 1: Análisis de Ofertas Mal Parseadas ✓ (AHORA)
- Extraer top 20 ofertas con peor score
- Identificar patrones comunes en descripciones mal parseadas
- Analizar qué está fallando en el extractor actual

### Fase 2: Mejora del Extractor NLP
- Revisar regex y patrones de `bumeran_extractor.py`
- Agregar nuevos patrones para casos no cubiertos
- Mejorar detección de skills técnicas y soft skills
- Mejorar extracción de experiencia y educación

### Fase 3: Testing y Validación
- Probar extractor mejorado con ofertas mal parseadas
- Medir mejora en score promedio
- Validar que no empeore ofertas bien parseadas

### Fase 4: Automatización
- Actualizar `process_nlp_from_db.py` con nuevo extractor
- Integrar en pipeline de scraping automático
- Documentar cambios y versión del extractor

## Comandos Importantes

### Acceder al Dashboard
```
http://localhost:8053
```

### Re-procesar ofertas NLP
```bash
cd D:\OEDE\Webscrapping\database
python process_nlp_from_db.py
```

### Analizar calidad de parseo
```bash
cd D:\OEDE\Webscrapping\database
python analizar_calidad_parseo.py
```

## Próximos Pasos Inmediatos

1. Extraer ejemplos de ofertas mal parseadas (score 0-1)
2. Analizar manualmente qué información contienen pero no se parsea
3. Identificar patrones faltantes en el extractor
4. Implementar mejoras incrementales
5. Re-procesar y medir impacto

---
**Nota:** Este documento se actualiza conforme avanzamos en las mejoras.
