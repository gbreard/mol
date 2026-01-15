# Dashboard Validacion Pipeline v3.0 - Con Trazabilidad ESCO Completa

**Fecha:** 2025-12-01
**Archivo:** `Visual--/validacion_pipeline_app_v3.R`
**Puerto:** 3853

---

## Objetivo

Dashboard de validacion campo por campo que muestra la **trazabilidad completa** del pipeline:
- **Scraping** -> datos originales de la oferta
- **NLP** -> extraccion de campos estructurados
- **ESCO** -> matching con ocupaciones ESCO v8.3

---

## Cambios Realizados (2025-12-01)

### Problema Original
La seccion ESCO solo mostraba 8 campos basicos, faltaban los campos de trazabilidad del matching v8.3:
- Scores parciales (titulo, skills, descripcion)
- Skills de la oferta y sin match
- Estado de confirmacion/revision
- Version del matching

### Solucion Implementada

**Cambio 1: Expandir CAMPOS_ESCO (linea 36-47)**

```r
# ANTES (8 campos):
CAMPOS_ESCO <- c(
  "esco_occupation_label", "isco_code", "isco_nivel1", "isco_nivel2",
  "score_final_ponderado", "skills_cobertura",
  "skills_matched_essential", "skills_matched_optional"
)

# DESPUES (17 campos con trazabilidad completa):
CAMPOS_ESCO <- c(
  # Resultado del matching
  "esco_occupation_label", "esco_occupation_uri",
  "isco_code", "isco_nivel1", "isco_nivel2",
  # Scores parciales (trazabilidad v8.3)
  "score_titulo", "score_skills", "score_descripcion", "score_final_ponderado",
  # Skills (trazabilidad)
  "skills_oferta_json", "skills_matched_essential", "skills_matched_optional",
  "skills_sin_match_json", "skills_cobertura",
  # Estado v8.3
  "match_confirmado", "requiere_revision", "matching_version"
)
```

**Cambio 2: Expandir output$tabla_esco (linea 567-598)**

Se expandio la tabla para mostrar todos los campos nuevos, usando `fmt_json()` para parsear campos JSON.

---

## Campos Mostrados por Seccion

### Seccion SCRAPING (contexto)
| Campo | Descripcion |
|-------|-------------|
| provincia_normalizada | Provincia normalizada con INDEC |
| localidad_normalizada | Localidad normalizada |
| descripcion | Texto completo de la oferta |

### Seccion NLP (18 campos)
| Campo | Descripcion |
|-------|-------------|
| experiencia_min_anios | Anos minimos de experiencia |
| experiencia_max_anios | Anos maximos de experiencia |
| experiencia_area | Area de experiencia |
| nivel_educativo | Nivel educativo requerido |
| estado_educativo | En curso, graduado, etc. |
| carrera_especifica | Carrera especifica |
| titulo_excluyente | Si el titulo es excluyente |
| idioma_principal | Idioma principal |
| nivel_idioma_principal | Nivel del idioma |
| idioma_secundario | Idioma secundario |
| nivel_idioma_secundario | Nivel del idioma secundario |
| skills_tecnicas_list | Lista de skills tecnicas (JSON) |
| soft_skills_list | Lista de soft skills (JSON) |
| certificaciones_list | Certificaciones requeridas (JSON) |
| salario_min | Salario minimo |
| salario_max | Salario maximo |
| moneda | Moneda (ARS, USD) |
| jornada_laboral | Tipo de jornada |
| horario_flexible | Si tiene horario flexible |

### Seccion ESCO (17 campos - EXPANDIDA)
| Campo | Descripcion |
|-------|-------------|
| **Resultado** | |
| esco_occupation_label | Ocupacion ESCO asignada |
| esco_occupation_uri | URI del concepto ESCO |
| isco_code | Codigo ISCO-08 |
| isco_nivel1 | Grupo mayor ISCO |
| isco_nivel2 | Subgrupo ISCO |
| **Scores parciales** | |
| score_titulo | Score de similitud titulo vs ocupacion |
| score_skills | Score de matching de skills |
| score_descripcion | Score de similitud descripcion |
| score_final_ponderado | Score final ponderado |
| **Skills** | |
| skills_oferta_json | Skills extraidos de la oferta (JSON) |
| skills_matched_essential | Skills esenciales matcheados (JSON) |
| skills_matched_optional | Skills opcionales matcheados (JSON) |
| skills_sin_match_json | Skills sin match (JSON) |
| skills_cobertura | Porcentaje de cobertura de skills |
| **Estado v8.3** | |
| match_confirmado | 1 = confirmado automaticamente |
| requiere_revision | 1 = requiere revision manual |
| matching_version | Version del algoritmo (v8.3_esco_familias_funcionales) |

---

## Como Ejecutar

```bash
# Matar procesos R existentes
cmd.exe /c "taskkill /F /IM Rscript.exe"

# Lanzar dashboard
"C:/Program Files/R/R-4.4.0/bin/Rscript.exe" -e "shiny::runApp('D:/OEDE/Webscrapping/Visual--/validacion_pipeline_app_v3.R', port = 3853, host = '0.0.0.0', launch.browser = FALSE)"

# Abrir en navegador
start http://localhost:3853
```

---

## Estructura del Dashboard

```
+------------------------------------------------------------------+
| Validacion Pipeline v3.0                                          |
+------------------------------------------------------------------+
| Sidebar:                                                          |
|   - Tu nombre (validador)                                         |
|   - Ir a oferta #                                                 |
|   - Progreso de validacion                                        |
+------------------------------------------------------------------+
| [Anterior] [GUARDAR] [Siguiente]  Oferta N de TOTAL               |
+------------------------------------------------------------------+
| BOX: DATOS SCRAPING - Descripcion                                 |
|   - Info basica (titulo, empresa, ubicacion, modalidad, fecha)    |
|   - Descripcion completa (scroll)                                 |
|   - Tabla campos ubicacion (checkbox + correccion)                |
+------------------------------------------------------------------+
| BOX: EXTRACCION NLP - Campos a evaluar                            |
|   - 18 campos con checkbox error + campo correccion               |
+------------------------------------------------------------------+
| BOX: MATCHING ESCO - Campos a evaluar  <-- EXPANDIDO              |
|   - 17 campos con checkbox error + campo correccion               |
|   - Incluye scores parciales, skills, estado v8.3                 |
+------------------------------------------------------------------+
| Comentario General: [textarea]                                    |
+------------------------------------------------------------------+
```

---

## Base de Datos

**Archivo:** `database/bumeran_scraping.db`

**Tablas utilizadas:**
- `ofertas` - Datos originales del scraping
- `ofertas_nlp` - Campos extraidos por NLP
- `ofertas_esco_matching` - Matching con ESCO v8.3
- `validacion_pipeline` - Scores y comentarios de validacion
- `validacion_campos` - Errores por campo con correcciones

---

## Archivos Relacionados

| Archivo | Descripcion |
|---------|-------------|
| `Visual--/validacion_pipeline_app_v3.R` | Dashboard principal (MODIFICADO) |
| `Visual--/validacion_pipeline_app_v2.R` | Version anterior |
| `Visual--/validacion_nlp_v7_app.R` | Dashboard solo NLP |
| `database/matching_rules_v83.py` | Reglas de ajuste v8.3 |
| `database/apply_v82_rules_batch.py` | Aplicar reglas a batch |
| `database/apply_v82_rules_gold19.py` | Aplicar reglas a gold set |

---

## Notas Tecnicas

1. **El query `get_oferta_completa()` ya traia todos los campos ESCO** (lineas 85-95), solo habia que agregarlos a CAMPOS_ESCO y a la tabla de visualizacion.

2. **Campos JSON** se parsean con `fmt_json()` para mostrar como lista separada por comas.

3. **Sistema de errores** usa checkbox + campo texto para cada campo. Se guarda en `validacion_campos`.

4. **Navegacion** permite ir a oferta especifica por numero.

---

## Proximos Pasos Sugeridos

1. Agregar filtro por estado (CONFIRMADOS/REVISION/RECHAZADOS)
2. Agregar link clickeable a `esco_occupation_uri`
3. Exportar validaciones a CSV
4. Agregar metricas de precision/recall basadas en validaciones
