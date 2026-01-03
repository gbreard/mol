# Roadmap de Implementación - NLP Extractor v2

**Fecha:** 2025-11-01
**Objetivo:** Integrar las mejoras de parseo NLP en producción
**Mejora esperada:** De 30.6% a ~50%+ de efectividad en parseo

---

## Resumen Ejecutivo

Se desarrolló y validó una **versión mejorada (v2)** del extractor NLP de ofertas laborales de Bumeran. Las pruebas con las 10 ofertas peor parseadas muestran una **mejora del +36%** en la detección de campos.

### Archivos Generados

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| `ANALISIS_PATRONES_FALLIDOS.md` | `D:\OEDE\Webscrapping\` | Análisis detallado de problemas |
| `regex_patterns_v2.py` | `D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts\patterns\` | Patrones mejorados |
| `test_patterns_v2.py` | `D:\OEDE\Webscrapping\database\` | Script de testing v1 vs v2 |
| Este archivo | `D:\OEDE\Webscrapping\` | Roadmap de implementación |

---

## Fase 1: Integración en Bumeran Extractor ⏭️ SIGUIENTE

### Objetivo
Modificar `bumeran_extractor.py` para usar los nuevos patrones de `regex_patterns_v2.py`

### Pasos

1. **Backup del archivo actual**
   ```bash
   cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts\extractors
   cp bumeran_extractor.py bumeran_extractor_v1_backup.py
   ```

2. **Modificar imports**
   ```python
   # En bumeran_extractor.py, cambiar:
   from patterns.regex_patterns import (
       ExperienciaPatterns,
       EducacionPatterns,
       # ... etc
   )

   # Por:
   from patterns.regex_patterns_v2 import (
       ExperienciaPatterns,
       EducacionPatterns,
       # ... etc
   )
   ```

3. **Agregar nuevos campos al schema de salida**

   En el método `extract()` de `BumeranExtractor`, agregar:
   ```python
   # Nuevos campos disponibles en v2:
   resultado['horario_especifico'] = JornadaPatterns.extract_horario(descripcion)
   resultado['dias_trabajo'] = JornadaPatterns.extract_dias(descripcion)
   resultado['carrera_detectada'] = EducacionPatterns.extract_carrera(descripcion)
   ```

4. **Actualizar versión del extractor**
   ```python
   # Cambiar NLP_VERSION de "1.0" a "2.0"
   NLP_VERSION = "2.0"
   ```

5. **Testing local**
   ```bash
   cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts\extractors
   python -c "
   from bumeran_extractor import BumeranExtractor
   extractor = BumeranExtractor()

   # Probar con texto que antes fallaba
   texto = 'Buscamos vendedor con experiencia mínima 2 años. Lunes a viernes de 9 a 18hs.'
   resultado = extractor.extract(texto)
   print(resultado)
   "
   ```

---

## Fase 2: Re-procesamiento de Ofertas Existentes ⏭️

### Objetivo
Re-procesar las 5,479 ofertas ya scrapeadas con el nuevo extractor v2

### Pasos

1. **Agregar columnas a la tabla `ofertas_nlp`** (opcional)
   ```sql
   ALTER TABLE ofertas_nlp ADD COLUMN horario_especifico TEXT;
   ALTER TABLE ofertas_nlp ADD COLUMN dias_trabajo TEXT;
   ALTER TABLE ofertas_nlp ADD COLUMN carrera_detectada TEXT;
   ```

2. **Ejecutar re-procesamiento**
   ```bash
   cd D:\OEDE\Webscrapping\database
   python process_nlp_from_db.py
   ```

   Esto procesará todas las ofertas con `nlp_version < 2.0` o `IS NULL`

3. **Monitorear progreso**
   - El script muestra progreso cada 100 ofertas
   - Tiempo estimado: ~5-10 minutos para 5,479 ofertas
   - Se actualizará el campo `nlp_version = '2.0'`

4. **Verificar resultados en dashboard**
   ```bash
   # El dashboard ya está corriendo en:
   http://localhost:8053

   # Ir a pestaña "Calidad Parseo NLP" y verificar:
   # - Score promedio debería subir de 2.14/7 a ~3.5/7
   # - Ofertas mal parseadas (score < 2) debería bajar de 35% a ~20%
   # - Ofertas bien parseadas (score >= 4) debería subir de 15% a ~35%
   ```

---

## Fase 3: Validación y Ajustes ⏭️

### Objetivo
Medir la mejora real en producción y ajustar si es necesario

### Métricas a Monitorear

1. **Score promedio de calidad**
   - **Actual:** 2.14/7 (30.6%)
   - **Esperado:** 3.5-4.0/7 (50-57%)
   - **Meta:** 4.5/7 (64%)

2. **Distribución de calidad**
   - **Mal parseadas (score < 2):** De 35% a ~20%
   - **Bien parseadas (score >= 4):** De 15% a ~35%

3. **Campos individuales**
   | Campo | Actual (NULL) | Esperado (NULL) |
   |-------|--------------|----------------|
   | Experiencia | ~70% | ~50% |
   | Educación | ~65% | ~45% |
   | Jornada | ~75% | ~50% |
   | Skills técnicas | ~80% | ~65% |

### Validación Manual

1. **Revisar top 20 ofertas mal parseadas**
   ```bash
   cd D:\OEDE\Webscrapping\database
   python extraer_ofertas_mal_parseadas.py
   # Analizar REPORTE_OFERTAS_MAL_PARSEADAS.txt
   ```

2. **Identificar patrones aún no cubiertos**
   - Documentar en `ANALISIS_PATRONES_FALLIDOS.md`
   - Crear issue para iteración v3

---

## Fase 4: Automatización para Futuras Ofertas ⏭️

### Objetivo
Asegurar que todas las ofertas nuevas usen el extractor v2

### Verificaciones

1. **Pipeline de scraping**
   ```bash
   # Verificar que process_nlp_from_db.py usa el extractor actualizado
   cd D:\OEDE\Webscrapping\database
   grep "BumeranExtractor" process_nlp_from_db.py
   ```

2. **Scheduler automático**
   - Verificar que el scheduler diario usa `process_nlp_from_db.py`
   - El script ya tiene lógica incremental (solo procesa ofertas sin NLP)

3. **Documentación**
   - Actualizar README con información de v2
   - Documentar cambios en changelog

---

## Rollback Plan

En caso de que v2 empeore los resultados:

1. **Revertir import en `bumeran_extractor.py`**
   ```python
   # Volver a:
   from patterns.regex_patterns import (...)
   ```

2. **Re-procesar ofertas**
   ```bash
   cd D:\OEDE\Webscrapping\database
   python process_nlp_from_db.py --force-reprocess --version=1.0
   ```

3. **Analizar qué falló**
   - Comparar resultados v1 vs v2
   - Identificar patrones que empeoraron
   - Ajustar regex_patterns_v2.py

---

## Mejoras Futuras (v3)

### Ideas para siguiente iteración

1. **Machine Learning**
   - Entrenar modelo NER para detectar skills no en el diccionario
   - Usar BERT en español para clasificación de educación

2. **Más patrones contextuales**
   - "Sin experiencia" → experiencia_min_anios = 0
   - "Estudiante avanzado" → estado_educativo = "avanzado"
   - Rangos de edad → agregar campo edad_min/max

3. **Validación semántica**
   - Verificar coherencia (ej: "Junior" con experiencia 10 años)
   - Detectar contradicciones en la descripción

4. **Integración con ESCO**
   - Mapear skills detectadas directamente a taxonomía ESCO
   - Agregar nivel de confianza en el mapeo

---

## Comandos Rápidos

```bash
# Ver dashboard
http://localhost:8053

# Re-procesar ofertas
cd D:\OEDE\Webscrapping\database && python process_nlp_from_db.py

# Analizar ofertas mal parseadas
cd D:\OEDE\Webscrapping\database && python extraer_ofertas_mal_parseadas.py

# Test de patrones
cd D:\OEDE\Webscrapping\database && python test_patterns_v2.py

# Backup de DB antes de re-procesar
cd D:\OEDE\Webscrapping\database && copy bumeran_scraping.db bumeran_scraping_backup_$(date +%Y%m%d).db
```

---

## Contacto y Preguntas

Para dudas sobre la implementación, revisar:
- `ANALISIS_PATRONES_FALLIDOS.md` - Detalles técnicos
- `CONTEXTO_MEJORA_PARSEO_NLP.md` - Contexto general
- `regex_patterns_v2.py` - Código de patrones mejorados
