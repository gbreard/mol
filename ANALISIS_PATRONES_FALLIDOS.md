# Análisis de Patrones Fallidos - NLP Extractor

**Fecha:** 2025-11-01
**Archivo analizado:** `regex_patterns.py`
**Ofertas de referencia:** `REPORTE_OFERTAS_MAL_PARSEADAS.txt`

## Problemas Identificados

### 1. EXPERIENCIA - Patrones Incompletos

**Caso fallido:** "experiencia mínima 2 años"

**Patrón actual (línea 24):**
```python
r'(?:mínimo|minimo|al menos|como mínimo|como minimo)\s*(\d+)\s*(?:años?|anios?)'
```

**Problema:**
- El patrón busca "mínimo" (masculino) pero el texto usa "mínima" (femenino)
- No captura variaciones de género: mínimo/mínima, minimo/minima

**Solución:**
```python
r'(?:mínimo?a?s?|minimo?a?s?|al menos|como mínimo?a?|como minimo?a?)\s*(\d+)\s*(?:años?|anios?)'
```

**Otros casos no cubiertos:**
- "experiencia requerida: 2 años"
- "se requieren 2 años de experiencia"
- "2+ años de experiencia"

---

### 2. EDUCACIÓN - Singular vs Plural

**Caso fallido:** "Estudios secundarios completos"

**Patrón actual (línea 96):**
```python
r'\bsecundari[oa]\s+complet[oa]\b'
```

**Problema:**
- Solo captura singular: "secundario completo" / "secundaria completa"
- No captura plural: "secundarios completos" / "secundarias completas"
- Tampoco captura cuando hay palabra intermedia: "estudios secundarios completos"

**Solución:**
```python
# Agregar variante con "estudios"
r'\bestudios?\s+secundari[oa]s?\s+complet[oa]s?\b'
# Y mantener la versión sin "estudios"
r'\bsecundari[oa]s?\s+complet[oa]s?\b'
```

**Otros casos no cubiertos:**
- "Estudiante de Administración"
- "Estudiante avanzado de [carrera]"
- "Cursando [carrera]"

---

### 3. JORNADA LABORAL - Horarios Específicos NO CAPTURADOS

**Caso fallido:** "Lunes a viernes de 9 a 18hs"

**Patrón actual:** ❌ **NO EXISTE**

**Problema:**
- Los patrones actuales solo detectan tipos genéricos (full time, part time, etc.)
- NO hay patrones para horarios específicos
- NO hay patrones para días de la semana

**Solución - Nuevos patrones:**
```python
# Días de la semana
r'lunes\s+a\s+viernes'
r'lunes\s+a\s+sábados?'
r'de\s+lunes\s+a\s+(?:viernes|sábado|domingo)'

# Horarios específicos
r'de\s+(\d{1,2}(?::\d{2})?)\s*(?:a|hasta|hs?\s+a)\s+(\d{1,2}(?::\d{2})?)\s*hs?'
r'(\d{1,2})\s*a\s*(\d{1,2})\s*hs?'
r'(\d{1,2}:\d{2})\s*a\s*(\d{1,2}:\d{2})'

# Turnos
r'turno\s+(?:mañana|tarde|noche|rotativos?)'
```

---

### 4. SKILLS TÉCNICAS - Contexto Argentino

**Casos fallidos del reporte:**
- "Refrigeración Industrial" ❌
- "Electricidad" ❌
- "Soldadura" ❌
- "Atención al cliente" ❌

**Problema:**
- El archivo `skills_database.json` no incluye oficios técnicos argentinos
- Falta categoría de "Oficios" o "Trades"
- Skills muy generales no son capturadas

**Solución:**
- Expandir `skills_database.json` con categoría de oficios
- Agregar skills de servicios (atención al cliente, ventas, etc.)

---

### 5. EDUCACIÓN - Carreras Específicas

**Caso fallido:** "Estudiante de Administración"

**Código actual (bumeran_extractor.py líneas mencionadas en lectura anterior):**
```python
# Solo 8 carreras hardcodeadas
carreras_conocidas = {
    'administracion', 'sistemas', 'contabilidad',
    'marketing', 'recursos humanos', 'economia',
    'ingenieria', 'derecho'
}
```

**Problema:**
- Lista de carreras extremadamente limitada
- No detecta "Estudiante de [carrera]"
- No detecta "Cursando [carrera]"

**Solución:**
```python
# Patrón para detectar cualquier carrera
r'estudiante\s+(?:de|en)\s+([A-Z][a-zá-ú]+(?:\s+[A-Z][a-zá-ú]+){0,3})'
r'cursando\s+(?:la\s+carrera\s+de\s+)?([A-Z][a-zá-ú]+(?:\s+[A-Z][a-zá-ú]+){0,3})'

# Expandir lista de carreras a ~50 carreras comunes
```

---

### 6. IDIOMAS - Patrones Funcionales ✓

**Estado:** Los patrones de idiomas parecen correctos.

**Patrones actuales:**
- Detectan inglés, portugués, alemán, francés, italiano
- Detectan niveles: básico, intermedio, avanzado, nativo, bilingüe

**No requiere cambios inmediatos.**

---

### 7. SALARIO - NO IMPLEMENTADO

**Código actual (línea 326):**
```python
def extract_montos(text: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    # Por ahora retornamos None, a implementar en próxima iteración
    return (None, None, None)
```

**Problema:**
- La función está definida pero no implementada
- Hay patrones definidos pero no se usan

**Solución:**
- Implementar la lógica de extracción usando los patrones ya definidos

---

## Resumen de Mejoras Requeridas

| Campo | Problema | Prioridad | Impacto Estimado |
|-------|----------|-----------|------------------|
| Experiencia | Género (mínima vs mínimo) | 🔴 ALTA | +20% capturas |
| Educación | Plural (secundarios vs secundario) | 🔴 ALTA | +25% capturas |
| Educación | "Estudiante de [carrera]" | 🔴 ALTA | +15% capturas |
| Jornada | Horarios específicos (9 a 18hs) | 🔴 ALTA | +30% capturas |
| Jornada | Días de semana (Lunes a viernes) | 🟡 MEDIA | +15% capturas |
| Skills | Oficios técnicos argentinos | 🟡 MEDIA | +10% capturas |
| Salario | Implementar función existente | 🟢 BAJA | +5% capturas |

**Mejora total estimada:** De 2.14/7 (30.6%) a ~4.5/7 (64%)

---

## Resultados del Testing

**Archivo:** `test_patterns_v2.py`
**Fecha test:** 2025-11-01

### Métricas Comparativas (10 ofertas peor parseadas)

| Métrica | V1 (Original) | V2 (Mejorado) | Mejora |
|---------|--------------|---------------|--------|
| Score promedio | 0.00/4 (0%) | 1.80/5 (36%) | +36.0% |
| Ofertas mejoradas | 0/10 | 7/10 | 70% |

### Ejemplos de Mejoras Exitosas

1. **VENDEDOR CONSUMO MASIVO (ID: 1117868779)**
   - V1: 0/4 campos → V2: 4/5 campos
   - **Detectado:** experiencia (2 años), jornada (full_time), horario (7:30-17:00), días (lunes a viernes), skills (ventas)

2. **Coordinador de Mantenimiento (ID: 2165546)**
   - V1: 0/4 campos → V2: 2/5 campos
   - **Detectado:** educación (secundario), skills técnicas (refrigeración industrial, electricidad)

3. **Representante Mesa de Ayuda ERP (ID: 1117978366)**
   - V1: 0/4 campos → V2: 2/5 campos
   - **Detectado:** carrera (Administración de Empresas), jornada (full_time), horario (9-18hs), días (lunes a viernes)

### Patrones que Ahora Funcionan

- ✅ "experiencia mínima 2 años" (género femenino)
- ✅ "Estudios secundarios completos" (plural)
- ✅ "Lunes a viernes de 9 a 18hs" (horarios específicos)
- ✅ "Refrigeración Industrial" (oficios técnicos)
- ✅ "Estudiante de Administración" (extracción de carrera)

---

## Próximos Pasos

1. ✅ Análisis completado
2. ✅ Crear `regex_patterns_v2.py` con mejoras
3. ✅ Probar en ofertas mal parseadas → **+36% mejora confirmada**
4. ⏭️ Integrar v2 en `bumeran_extractor.py`
5. ⏭️ Re-procesar todas las ofertas de la DB
6. ⏭️ Medir mejora en dashboard
7. ⏭️ Automatizar para futuras ofertas
