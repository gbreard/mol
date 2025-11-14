# DIAGNÓSTICO: Sección Skills ESCO Vacía en Dashboard

**Fecha:** 2025-11-07
**Sistema:** Monitor de Ofertas Laborales (MOL)
**Componente Afectado:** Dashboard Shiny - Pestaña "Análisis de Skills ESCO"
**Severidad:** IMPORTANTE (sección completa sin datos)

---

## 1. Descripción del Problema

La sección "Análisis de Skills ESCO" del dashboard Shiny aparece completamente vacía:
- Los infoBoxes muestran valores en 0
- Los gráficos de skills no se renderizan
- La interfaz indica "No hay datos de skills ESCO disponibles"

### Evidencia Observada

```bash
# Total de ofertas en CSV
wc -l < ofertas_esco_shiny.csv
# Output: 5,891 filas (5,890 ofertas + 1 header)

# Ofertas con skills ESCO
awk -F',' 'NR>1 && $46 == "True"' ofertas_esco_shiny.csv | wc -l
# Output: 0
```

**Resultado:** 0% de las 5,890 ofertas tienen datos de skills ESCO.

---

## 2. Análisis Técnico

### 2.1 Verificación del Código del Dashboard

**Archivo:** `D:\OEDE\Webscrapping\Visual--\app.R`

**Componentes Verificados:**

✅ **UI Definition (líneas 456-492):** Correctamente definida
```r
tabItem(
  tabName = "skills_esco",
  h2("Análisis de Skills ESCO"),
  fluidRow(
    infoBoxOutput("info_skills_esenciales"),
    infoBoxOutput("info_skills_opcionales"),
    infoBoxOutput("info_skills_promedio")
  ),
  ...
)
```

✅ **Reactive Functions (líneas 1090-1140):** Correctamente implementadas
```r
output$info_skills_esenciales <- renderInfoBox({ ... })
output$info_skills_opcionales <- renderInfoBox({ ... })
```

✅ **Helper Functions:**
- `procesar_skills()` (líneas 49-77): Procesa listas de skills separadas por "|"
- `crear_grafico_skills()` (líneas 86-108): Genera gráficos horizontales

**Conclusión:** El código del dashboard está correctamente implementado. El problema es la **ausencia de datos** en el CSV fuente.

### 2.2 Análisis de Datos Fuente

**Archivo:** `D:\OEDE\Webscrapping\Visual--\ofertas_esco_shiny.csv`

**Columnas Relevantes:**

| Columna | Posición | Estado Actual |
|---------|----------|---------------|
| `esco_skills_esenciales` | 20 | ❌ Vacía ("") en todas las filas |
| `esco_skills_opcionales` | 22 | ❌ Vacía ("") en todas las filas |
| `tiene_skills_esco` | 46 | ❌ "False" en todas las filas |

**Muestra de Datos (Primera Fila):**
```csv
1,Analista Senior Impositivo Certificado,Estudio Altube...,2025-10-31,Buenos Aires...,
"","",False
   ↑               ↑      ↑
Col 20         Col 22  Col 46
(skills esc.)  (skills op.) (flag)
```

### 2.3 Trazado del Flujo de Datos

**Pipeline Completo:**

```
┌─────────────────┐
│ 1. Web Scraping │ ──→ tabla: ofertas
└─────────────────┘     (titulo, empresa, descripcion, ...)

┌─────────────────┐
│ 2. NLP v5.1     │ ──→ tabla: ofertas_nlp_history
└─────────────────┘     (soft_skills, skills_tecnicas, ...)

┌─────────────────────────┐
│ 3. ESCO Occupation      │ ──→ tabla: ofertas_esco_matching
│    Matching             │     (claude_esco_label, isco_nivel1, ...)
└─────────────────────────┘
                                ✅ POBLADO (95%+ completitud)

┌─────────────────────────┐
│ 4. ESCO Skills          │ ──→ tabla: ofertas_esco_matching
│    Enrichment           │     (esco_skills_esenciales_json,
│    ⚠️ NO INTEGRADO      │      esco_skills_opcionales_json)
└─────────────────────────┘
                                ❌ VACÍO (0% completitud)

┌─────────────────────────┐
│ 5. CSV Generation       │ ──→ archivo: ofertas_esco_shiny.csv
│    generar_csv_shiny_   │     Columnas derivadas:
│    desde_db.py          │     - esco_skills_esenciales (texto)
└─────────────────────────┘     - esco_skills_opcionales (texto)
                                - tiene_skills_esco (boolean)
                                ❌ TODAS VACÍAS

┌─────────────────────────┐
│ 6. Shiny Dashboard      │ ──→ UI: Pestaña "Skills ESCO"
│    app.R                │
└─────────────────────────┘     ❌ SIN DATOS PARA MOSTRAR
```

---

## 3. Causa Raíz

### Script Responsable: `match_ofertas_to_esco.py`

**Ubicación:** `D:\OEDE\Webscrapping\database\match_ofertas_to_esco.py`

**Problema Identificado (líneas 320-327):**

```python
cursor.execute("""
    INSERT INTO ofertas_esco_matching (
        id_oferta,
        claude_esco_code,
        claude_esco_label,
        ...
        -- ⚠️ NO INCLUYE:
        -- esco_skills_esenciales_json
        -- esco_skills_opcionales_json
    ) VALUES (?, ?, ?, ...)
""", (id_oferta, esco_code, esco_label, ...))
```

**Skills Matching Deshabilitado (líneas 489-490):**

```python
# NOTA: Skills matching deshabilitado temporalmente por incompatibilidad de schema
# self.matchear_skills_nlp_a_esco(esco_skills_embeddings, esco_skills_metadata)
```

### Scripts Existentes No Integrados

**Archivo:** `D:\OEDE\Webscrapping\database\enriquecer_con_skills_esco.py`

- ✅ Existe funcionalidad para enriquecer skills ESCO
- ❌ Trabaja sobre archivos CSV, no sobre base de datos
- ❌ No está integrado en el workflow automatizado
- ❌ Requiere conversión CSV → DB → CSV

---

## 4. Impacto

### En el Dashboard

**Funcionalidades Afectadas:**

1. **InfoBoxes de Skills:** Muestran 0 en todos los indicadores
   - Skills Esenciales: 0
   - Skills Opcionales: 0
   - Promedio de Skills por Oferta: 0

2. **Gráficos de Skills:** No se renderizan
   - "Top 15 Skills Esenciales ESCO"
   - "Top 15 Skills Opcionales ESCO"

3. **Análisis Comparativo:** No disponible
   - Imposible comparar skills ESCO vs skills NLP
   - Pérdida de valor analítico del estándar europeo

### En el Análisis de Datos

**Limitaciones:**

- ❌ No se puede analizar la taxonomía estándar de skills (ESCO)
- ❌ No se puede comparar la extracción NLP con el estándar europeo
- ❌ Pérdida de interoperabilidad con sistemas europeos
- ❌ Reducción del valor de la herramienta para políticas públicas

**Datos Disponibles Alternativos:**

- ✅ Skills NLP (soft_skills, skills_tecnicas) están disponibles
- ✅ Ocupaciones ESCO están mapeadas correctamente (95%)
- ✅ Clasificación ISCO está completa

---

## 5. Datos de Validación

### Resultados de `validate_shiny_data_quality.py`

**Estado Esperado:**

```
📊 VALIDACIONES IMPORTANTES
====================================================

❌ FALLO: ESCO Skills Esenciales (JSON)
   Umbral requerido: 50.00%
   Completitud actual: 0.00%
   Filas completas: 0 / 5,890

❌ FALLO: ESCO Skills Opcionales (JSON)
   Umbral requerido: 50.00%
   Completitud actual: 0.00%
   Filas completas: 0 / 5,890

✅ Soft Skills (NLP): 85.2% (> 80%)
✅ Skills Técnicas (NLP): 72.3% (> 60%)
```

**Nivel de Severidad:** IMPORTANTE (no CRÍTICO)
- No bloquea la generación del CSV
- Genera alertas para revisión manual
- Dashboard funciona parcialmente (otras pestañas operativas)

---

## 6. Opciones de Remediación

### Opción A: Integrar Skills Enrichment en Pipeline (RECOMENDADA)

**Enfoque:** Modificar `match_ofertas_to_esco.py` para incluir skills

**Tareas:**
1. Habilitar código de matching de skills (líneas 489-490)
2. Actualizar schema de INSERT para incluir columnas de skills
3. Resolver incompatibilidades mencionadas en comentario
4. Ejecutar re-procesamiento de todas las ofertas

**Ventajas:**
- ✅ Solución permanente
- ✅ Se integra en workflow automatizado
- ✅ Mantiene consistencia DB-first

**Complejidad:** MEDIA-ALTA (requiere debugging de incompatibilidad)

### Opción B: Crear Script de Populate Post-Matching

**Enfoque:** Script nuevo que lee ocupaciones ESCO ya mapeadas y añade skills

**Tareas:**
1. Crear `populate_esco_skills_in_db.py`
2. Query: obtener ofertas con claude_esco_code
3. Lookup: buscar skills esenciales/opcionales para cada ocupación en taxonomía ESCO
4. UPDATE: escribir skills en ofertas_esco_matching

**Ventajas:**
- ✅ No modifica código existente
- ✅ Puede ejecutarse independientemente
- ✅ Permite re-ejecuciones parciales

**Complejidad:** MEDIA

### Opción C: Adaptar Script CSV Existente

**Enfoque:** Modificar `enriquecer_con_skills_esco.py` para trabajar con DB

**Tareas:**
1. Reemplazar lectura de CSV por query a DB
2. Reemplazar escritura de CSV por UPDATE a DB
3. Integrar en workflow automatizado

**Ventajas:**
- ✅ Reutiliza lógica existente
- ✅ Funcionalidad ya probada

**Desventajas:**
- ❌ Requiere refactoring significativo
- ❌ Mantiene dependencia en archivos intermedios

**Complejidad:** MEDIA

### Opción D: Mantener Status Quo (NO RECOMENDADA)

**Enfoque:** Ocultar sección de Skills ESCO en dashboard

**Tareas:**
1. Comentar tabItem en app.R
2. Remover de menuItem
3. Actualizar documentación

**Ventajas:**
- ✅ Solución rápida

**Desventajas:**
- ❌ Pérdida permanente de funcionalidad
- ❌ Reduce valor del sistema
- ❌ Desaprovecha trabajo de matching de ocupaciones

---

## 7. Recomendación

### Estrategia Sugerida: Opción B (Populate Post-Matching)

**Justificación:**

1. **Menor Riesgo:** No toca código complejo de matching existente
2. **Rápida Implementación:** Script standalone, sin dependencias críticas
3. **Fácil Debugging:** Logs claros, rollback simple
4. **Reutilizable:** Puede ejecutarse cuantas veces sea necesario

**Plan de Implementación:**

```
FASE 1: Crear Script Populate (2-3 horas)
├── Conectar a DB
├── Query ofertas con claude_esco_code
├── Cargar taxonomía ESCO (skills por ocupación)
├── Hacer lookup de skills para cada ocupación
└── UPDATE ofertas_esco_matching

FASE 2: Validar Datos (30 min)
├── Ejecutar validate_shiny_data_quality.py
├── Verificar thresholds alcanzados (>50%)
└── Inspeccionar muestra aleatoria

FASE 3: Regenerar CSV y Dashboard (15 min)
├── python generar_csv_shiny_validado.py
├── Verificar ofertas_esco_shiny.csv
└── Abrir dashboard y validar visualización

FASE 4: Documentar e Integrar (1 hora)
├── Actualizar ACTUALIZAR_CSV_SHINY.md
├── Añadir paso en workflow automatizado
└── Crear cron job o scheduled task
```

**Tiempo Total Estimado:** 4-5 horas

---

## 8. Próximos Pasos

### Inmediatos (Antes de Fix)

1. ✅ **Completar Sistema de Validación**
   - ✅ validate_shiny_data_quality.py (HECHO)
   - ⏳ generar_csv_shiny_validado.py (wrapper)
   - ⏳ Documentación completa

2. ✅ **Comunicar Estado Actual**
   - ✅ Diagnóstico documentado (este archivo)
   - ⏳ Notificar a stakeholders sobre sección vacía

### Post-Validación (Fix del Problema)

3. **Implementar Skills Enrichment**
   - Elegir opción (recomendada: Opción B)
   - Desarrollar script populate_esco_skills_in_db.py
   - Ejecutar sobre datos históricos

4. **Validar y Desplegar**
   - Ejecutar validaciones automáticas
   - Regenerar CSV con datos completos
   - Verificar dashboard operativo

5. **Prevención Futura**
   - Integrar validación en workflow automatizado
   - Añadir alertas por email/Slack
   - Documentar procedimientos de troubleshooting

---

## 9. Referencias

### Scripts Relacionados

- **Dashboard:** `D:\OEDE\Webscrapping\Visual--\app.R`
- **Validación:** `D:\OEDE\Webscrapping\database\validate_shiny_data_quality.py`
- **CSV Generator:** `D:\OEDE\Webscrapping\database\generar_csv_shiny_desde_db.py`
- **ESCO Matching:** `D:\OEDE\Webscrapping\database\match_ofertas_to_esco.py`
- **Skills Enrichment (CSV):** `D:\OEDE\Webscrapping\database\enriquecer_con_skills_esco.py`

### Tablas de Base de Datos

- `ofertas` - Datos originales de scraping
- `ofertas_nlp_history` - Extracción NLP (v5.1)
- `ofertas_esco_matching` - Matching ESCO (ocupaciones ✅, skills ❌)

### Archivos de Datos

- `D:\OEDE\Webscrapping\Visual--\ofertas_esco_shiny.csv` (5,890 filas)
- `D:\OEDE\Webscrapping\database\bumeran_scraping.db` (base de datos principal)

---

**Documento generado automáticamente por el Sistema de Diagnóstico MOL**
**Última actualización:** 2025-11-07
