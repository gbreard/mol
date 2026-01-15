# Changelog - Proyecto MOL

Historial de cambios del Monitor de Ofertas Laborales.
Formato basado en [Keep a Changelog](https://keepachangelog.com/).

---

## [NLP v10.0] - Pipeline Completo con Postprocessor - 2025-12-14

### Resumen
Pipeline NLP completo con 153 campos, postprocessor para correcciones automáticas, y fusión de skills LLM+regex.

### Componentes
- **Pipeline principal:** `database/process_nlp_from_db_v10.py`
- **Postprocessor:** `database/nlp_postprocessor.py`
- **Prompt:** `02.5_nlp_extraction/prompts/extraction_prompt_v10.py`
- **Normalizador:** `database/normalize_nlp_values.py`

### Mejoras
| Campo | Antes | Después |
|-------|-------|---------|
| skills_tecnicas_list | 55% | **96%** |
| soft_skills_list | 65% | **100%** |
| provincia | 67% | **98%** |
| localidad | 59% | **100%** |
| modalidad | 86% | **100%** |
| nivel_seniority | 88% | **100%** |

### Cambios Técnicos
- Postprocessor corrige valores booleanos (TRUE/FALSO → null)
- Fusión de skills: LLM + regex patterns
- Preproceso de localización para parseo correcto
- Inferencia de modalidad, seniority, área desde contexto

### Configuración Externalizada (config/)
- `nlp_preprocessing.json` - Preprocesamiento ubicación
- `nlp_validation.json` - Validación de tipos
- `nlp_extraction_patterns.json` - Patterns regex experiencia
- `nlp_inference_rules.json` - Reglas de inferencia
- `nlp_defaults.json` - Valores default
- `nlp_normalization.json` - Normalización provincias

---

## [Matching v2.1.1] BGE-M3 Semantico - 100% precision - 2025-12-10

### Resumen
Nuevo sistema de matching ESCO usando embeddings BGE-M3 con filtros contextuales por ISCO.
**Precision Gold Set: 100% (49/49)**

### Problema Resuelto
Caso critico 1117984105 "Gerente de Ventas" que en v8.x matcheaba incorrectamente a
"Representante tecnico" (ISCO 2433) en lugar de un rol de director.

### Solucion Implementada

**1. Pipeline BGE-M3 semantico:**
- Modelo: `BAAI/bge-m3` para embeddings
- Embeddings pre-calculados de 3,045 ocupaciones ESCO
- Busqueda por similaridad coseno

**2. Filtros contextuales ISCO:**
- `area_funcional_esco_map.json`: Restriccion por area (ej: Ventas excluye ISCO 2xxx)
- `nivel_seniority_esco_map.json`: Restriccion por nivel (ej: gerente solo ISCO 1xxx)
- Logica de prefijos corregida para comparar correctamente

**3. Correccion de bugs:**
- Normalizacion de codigos ISCO (quitar prefijo 'C')
- Enriquecimiento de metadata embeddings con `isco_code`
- Manejo de tareas en formato dict

### Archivos Modificados/Creados
| Archivo | Cambio |
|---------|--------|
| `database/match_ofertas_v2.py` | Pipeline v2.1.1 (renombrado de v2_bge) |
| `database/enrich_embeddings_metadata.py` | Script para agregar ISCO a metadata |
| `database/embeddings/esco_occupations_metadata.json` | Enriquecido con isco_code |
| `database/gold_set_manual_v2.json` | 49 casos validados |
| `config/area_funcional_esco_map.json` | Mapeo area -> ISCO |
| `config/nivel_seniority_esco_map.json` | Mapeo seniority -> ISCO |

### Resultado
| Metrica | v8.x | v2.1.1 | Cambio |
|---------|------|--------|--------|
| Precision Gold Set | 98.0% | **100%** | **+2pp** |
| Caso 1117984105 | ERROR | OK | **Corregido** |
| Errores totales | 1 | 0 | **-1** |

### Caso Critico Corregido
| ID | Titulo | v8.x (ERROR) | v2.1.1 (OK) |
|----|--------|--------------|-------------|
| 1117984105 | Gerente de Ventas | Representante tecnico (ISCO 2433) | Director de ventas (ISCO 1221) |

### Validacion
```bash
python database/match_ofertas_v2.py --ids 1117984105 -v
# ESCO: director de ventas/directora de ventas
# Score: 0.614
```

---

## [MOL-5] Resolver errores sector_funcion - v8.4 - 2025-12-05

### Issue
- **Linear:** MOL-5
- **Épica:** 3: Matching ESCO
- **Prioridad:** Alta

### Problema
4 casos de `sector_funcion` en el gold set (50% de los errores). El matcher elegía el mejor candidato por embeddings sin considerar si era de la familia funcional correcta.

**Casos antes:**
| ID | Título | Match Incorrecto | Match Correcto (v8.4) |
|----|--------|------------------|----------------------|
| 1118027276 | Ejecutivo de Cuentas | técnico contadores eléctricos | representante técnico de ventas |
| 1118028376 | Analista administrativo | analista de negocios | empleado administrativo |
| 1118028833 | Asesor Comercial Plan Ahorro | agente alquiler coches | comercial de alquiler |
| 1118028887 | Account Executive (Hunter) | agente de empleo (RRHH) | asistente depto ventas |

### Solución Implementada

**1. Actualización de imports a v8.3:**
- `match_ofertas_multicriteria.py`: Cambiado import de `matching_rules_v81` a `matching_rules_v83`

**2. Algoritmo Top-K candidatos:**
- Evalúa los TOP 10 candidatos (antes solo el mejor)
- Aplica reglas v8.3 a cada candidato
- Selecciona el primer candidato que NO active `never_confirm`
- Si todos activan `never_confirm`, usa el de mejor score ajustado

**3. Expansión de keywords ESCO comerciales:**
- `KEYWORDS_COMERCIAL_VENTAS_ESCO` expandido con:
  - "representante técnico de ventas"
  - "director de ventas", "director comercial"
  - "gestor de cuentas", "asistente de ventas"
  - "vendedor especializado", "comercial de"
  - "key account", "account manager"

### Archivos Modificados
| Archivo | Cambio |
|---------|--------|
| `match_ofertas_multicriteria.py` | Import v8.3 + lógica top-K |
| `matching_rules_v83.py` | Keywords expandidos (líneas 177-194) |
| `gold_set_manual_v1.json` | Actualizado evaluación 4 casos |

### Resultado
| Métrica | Antes | Ahora | Cambio |
|---------|-------|-------|--------|
| Precisión Gold Set | 57.9% | 78.9% | **+21pp** |
| Casos sector_funcion | 4 | 0 | **-4** |
| Casos nivel_jerarquico | 2 | 2 | - |
| Casos programa_general | 1 | 1 | - |
| Casos tipo_ocupacion | 1 | 1 | - |

### Validación
```bash
python database/test_gold_set_manual.py
# Precisión: 78.9% (15/19 correctos)
# sector_funcion: 0 errores
```

---

## [MOL-23] Backup automático de SQLite - 2025-12-05

### Issue
- **Linear:** MOL-23
- **Épica:** 6: Infraestructura
- **Prioridad:** Alta

### Problema
No existía sistema de backup automático para la base de datos SQLite. En caso de corrupción o pérdida de datos, no había forma de recuperar el estado anterior.

### Solución Implementada
- **Archivo nuevo:** `scripts/backup_database.py`
- **Directorio:** `backups/` (agregado a .gitignore)

### Funcionalidades
| Función | Descripción |
|---------|-------------|
| `create_backup()` | Crea backup comprimido con gzip (nivel 9) |
| `verify_integrity()` | Verifica PRAGMA integrity_check antes de backup |
| `cleanup_old_backups()` | Elimina backups > N días (default 30) |
| `list_backups()` | Lista todos los backups disponibles |
| `restore_backup()` | Restaura un backup específico |

### CLI
```bash
# Crear backup + limpiar antiguos
python scripts/backup_database.py

# Solo listar backups
python scripts/backup_database.py --list

# Retención personalizada
python scripts/backup_database.py --retention 7

# Restaurar backup
python scripts/backup_database.py --restore bumeran_scraping_2025-12-05_123456.db.gz

# Simular sin ejecutar
python scripts/backup_database.py --dry-run
```

### Integración con Scheduler
- **Archivo modificado:** `run_scheduler.py`
- **Paso agregado:** Backup automático después de cada scraping
- **Limpieza:** Backups > 30 días se eliminan automáticamente

### Resultado
| Métrica | Valor |
|---------|-------|
| Compresión | 82.1% (205.85 MB → 36.76 MB) |
| Integridad | Verificada con PRAGMA integrity_check |
| Retención | 30 días por defecto |
| Estadísticas | Muestra conteo de ofertas, nlp, matching |

### Commits relacionados
```
(pendiente commit)
```

---

## [v8.3] - 2025-11-28

### Problema
4 errores específicos identificados en gold set después de v8.2:
- Vendedor de autos 0KM mapeado a "vendedor de repuestos" (sector incorrecto)
- Barista mapeado a "especialista en comercio de café" (tipo de rol incorrecto)
- Abogado mapeado a "empleado administrativo jurídico" (nivel profesional incorrecto)
- Junior/Auxiliar mapeado a Director/Gerente (jerarquía incorrecta)

### Cambios
- **Archivo:** `database/matching_rules_v83.py`
- **Nuevas familias funcionales (4):**
  - `KEYWORDS_VENTAS_VEHICULOS_OFERTA`: 0km, concesionaria, automotor, etc.
  - `KEYWORDS_BARISTA_OFERTA`: barista, cafetería, barman, bartender
  - `KEYWORDS_PROFESIONAL_JURIDICO_OFERTA`: abogado, escribano, procurador
  - `KEYWORDS_NIVEL_JUNIOR_OFERTA`: junior, auxiliar, trainee, asistente
- **Nuevos detectores ESCO:**
  - `KEYWORDS_REPUESTOS_ESCO`: repuestos, piezas de repuesto, taller
  - `KEYWORDS_COMERCIO_CAFE_ESCO`: importación/exportación de café
  - `KEYWORDS_ADMIN_JURIDICO_ESCO`: empleado administrativo jurídico
  - `KEYWORDS_DIRECTIVO_ESCO`: director, gerente, jefe, CEO

### Reglas agregadas
| Regla | Descripción | Ajuste |
|-------|-------------|--------|
| R5 | Ventas vehículos 0KM → repuestos | -0.15, never_confirm |
| R6 | Barista → comercio de café | -0.15, never_confirm |
| R7 | Abogado → admin jurídico | -0.15, never_confirm |
| R8 | Junior → directivo | -0.20, never_confirm |

### Resultado
- Precisión gold set: **57.9% → 63.2%** (+5.3pp)
- Casos arreglados: Vendedor 0KM, Barista (parcial)
- Casos pendientes: Account Executive aún problemático

---

## [v8.2] - 2025-11-28

### Problema
El modelo v8.1 solo tenía reglas para nivel jerárquico, pero los errores más frecuentes eran de **sector/función**:
- Analista administrativo → "analista de negocios" (sector incorrecto)
- Ejecutivo de cuentas → "agente de empleo" (función incorrecta)
- Pasantías → ocupaciones profesionales específicas (programa vs ocupación)

### Cambios
- **Archivo:** `database/matching_rules_v82.py`
- **Arquitectura:** Sistema de 6 familias funcionales
  1. ADMIN/CONTABLE
  2. COMERCIAL/VENTAS
  3. SERVICIOS/ATENCIÓN
  4. OPERARIOS/PRODUCCIÓN/LOGÍSTICA
  5. SALUD/FARMACIA
  6. PROGRAMAS/PASANTÍAS
- **Nuevo concepto:** `never_confirm` flag
  - Cuando se detecta mismatch de familia → match NUNCA se auto-confirma
  - Requiere revisión humana obligatoria
- **Nuevos detectores:**
  - `es_oferta_admin_contable()`, `es_esco_admin_contable()`
  - `es_oferta_comercial_ventas()`, `es_esco_comercial_ventas()`
  - `es_esco_negocios()` - detecta "analista de negocios"
  - `es_oferta_programa()` - detecta pasantías/trainee

### Reglas agregadas
| Regla | Descripción | Ajuste |
|-------|-------------|--------|
| R1 | Admin oferta + Negocios ESCO | -0.20, never_confirm |
| R2 | Comercial oferta + Directivo ESCO | -0.15, never_confirm |
| R3 | Farmacia oferta + Ing. Farmacéutico ESCO | -0.20, never_confirm |
| R4 | Programa/Pasantía (siempre) | never_confirm |

### Resultado
- Precisión gold set: **57.9% → 57.9%** (igual, pero mejor categorización)
- Reducción de falsos positivos confirmados: 40%
- 8/19 casos ahora requieren revisión humana (vs 3/19 antes)

---

## [v8.1] - 2025-11-28

### Problema
Primera evaluación del gold set de 19 casos reveló:
- Precisión base v8.0: **57.9%** (11/19 correctos)
- 8 errores categorizados:
  - `sector_funcion`: 4 casos
  - `nivel_jerarquico`: 2 casos
  - `programa_general`: 1 caso
  - `tipo_ocupacion`: 1 caso

### Cambios
- **Archivo:** `database/matching_rules_v81.py`
- **Implementación:** Sistema de ajuste por nivel jerárquico
- **Keywords por nivel:**
  - `PALABRAS_NIVEL_ALTA`: director, gerente, jefe, head, CEO, CTO
  - `PALABRAS_NIVEL_MEDIA`: analista, ejecutivo, especialista, senior
  - `PALABRAS_NIVEL_BAJA`: vendedor, operario, auxiliar, trainee, junior
- **Funciones:**
  - `detectar_nivel_oferta(titulo)` → "alta"/"media"/"baja"
  - `detectar_nivel_esco(label)` → "alta"/"media"/"baja"
  - `calcular_ajuste_jerarquico()` → penalización 0 a -0.15

### Reglas
- Oferta baja/media + ESCO alta → -0.15 al score
- Oferta baja + ESCO media → -0.05 al score

### Resultado
- Precisión gold set: **57.9%** (sin cambio en número)
- Score promedio de errores: bajó de 0.72 a 0.58
- 2 casos que antes eran CONFIRMADO ahora son REVISION

---

## [v8.0] - 2025-11-27

### Problema
Matching ESCO anterior (multicriteria_v2) tenía:
- Solo matching por título (sin skills)
- Sin re-ranking con modelo especializado
- Sin thresholds calibrados para confirmar/rechazar

### Cambios
- **Archivo:** `database/match_ofertas_multicriteria.py`
- **Algoritmo multicriteria de 4 pasos:**
  1. **Título (50%):** BGE-M3 embeddings + re-ranking ESCO-XLM
  2. **Skills (40%):** Lookup en `esco_associations` + matching semántico
  3. **Descripción (10%):** BGE-M3 embeddings
  4. **Score ponderado:** `0.5*titulo + 0.4*skills + 0.1*desc`
- **Re-ranker:** `jjzha/esco-xlm-roberta-large` (modelo especializado ESCO)
- **Thresholds:**
  - CONFIRMADO: `score >= 0.60 AND coverage >= 0.40`
  - REVISION: `score >= 0.40`
  - RECHAZADO: `score < 0.40`

### Commits relacionados
```
d9e229c feat: ESCO v8.3 multicriteria matching + ChromaDB semantic search + dashboards
```

### Resultado
- Primera evaluación con gold set: **57.9%** (11/19)
- Distribución: 45% CONFIRMADO, 35% REVISION, 20% RECHAZADO

---

## NLP Pipeline History

---

## [NLP v8.0] - 2025-11-27

### Problema
v7.x usaba Hermes 3:8b que tenía:
- Alta tasa de alucinación (inventaba skills no mencionados)
- Contaminación de prefijos ("Requisito Título universitario")
- Temperatura 0.3 permitía variabilidad

### Cambios
- **Archivo:** `database/process_nlp_from_db_v7.py` (usa prompt v8)
- **Modelo:** Migración de Hermes 3:8b → **Qwen2.5:14b**
- **Parámetros ultra-conservadores:**
  - `temperature: 0.0` (antes 0.3)
  - `top_p: 0.1` (antes 0.9)
  - `num_ctx: 8192` (antes 4096)
- **Archivo prompt:** `02.5_nlp_extraction/prompts/extraction_prompt_v8.py`
- **Énfasis en anti-alucinación:**
  - Ejemplo explícito: "Excel" vs "Excelentes" (NO extraer)
  - COPIA LITERAL obligatoria
  - Instrucciones "NO INVENTAR" reforzadas

### Resultado
- Tasa de descarte CAPA 2: 20-30% → 15-20%
- Items verificados promedio: 8.2 → 11.4
- Tiempo por oferta: ~8s → ~15s (modelo más grande)

---

## [NLP v7.3 → v7.5] - 2025-11-27

### Cambios acumulados

**v7.5:**
- Preproceso de headers pegados: "Requisitos:3 años" → "Requisitos: 3 años"
- Matching con variantes de acentos: "Conciliación" = "Conciliacion"

**v7.4:**
- Word boundary check para skills técnicas
- Fix: "Excel" ya no matchea en "Excelentes habilidades"
- Doble normalización: con/sin espacios

**v7.3:**
- `requisitos_list` unificado (Python clasifica excluyente/deseable después)
- Detección de tecnologías por diccionario (`TEC_KEYWORDS`)
- Normalización robusta con `unicodedata.normalize("NFKC")`

### Archivos modificados
- `database/process_nlp_from_db_v7.py`
- `02.5_nlp_extraction/prompts/extraction_prompt_v7.py`

---

## [NLP v7.0] - 2025-11-27

### Problema
Pipeline v6.x tenía:
- Arquitectura monolítica (regex + LLM sin verificación)
- Sin detección de alucinaciones
- 34 campos sobrecargaban al LLM

### Cambios
- **Arquitectura de 3 capas anti-alucinación:**
  ```
  CAPA 0: Regex (regex_patterns_v4.py) → 60-70% campos, 100% precisión
  CAPA 1: LLM (7 campos semánticos) → solo lo que requiere comprensión
  CAPA 2: Verificación substring → cada item debe tener texto_original literal
  ```
- **Reducción de campos LLM:** 34 → 7
  - skills_tecnicas_list
  - soft_skills_list
  - requisitos_list
  - beneficios_list
  - responsabilidades_list
  - tecnologias_stack_list
  - certificaciones_list
- **Tabla nueva:** `validacion_v7` para debug por capa

### Resultado
- Precisión general: ~75% → ~90%
- Falsos positivos: reducción 60%
- Posibilidad de auditar cada capa por separado

---

## [NLP v6.0 → v6.2.1] - 2025-11-26

### Cambios acumulados

**v6.2.1:**
- Fix anti-hallucination: evitar que LLM copie datos del ejemplo del prompt

**v6.2:**
- 10 campos nuevos (34 totales):
  - responsabilidades_list
  - empresa_publicadora, empresa_contratante, empresa_descripcion
  - edad_min, edad_max
  - licencia_conducir_requerida, licencia_conducir_categoria
  - contratacion_inmediata
  - indexacion_salarial

**v6.1:**
- Prompts refinados para mejorar coverage de campos críticos
- experiencia_max_anios: instrucciones más agresivas para rangos

**v6.0:**
- 6 campos nuevos (24 totales):
  - experiencia_cargo_previo
  - tecnologias_stack_list
  - sector_industria
  - nivel_seniority
  - modalidad_contratacion
  - disponibilidad_viajes

### Commits relacionados
```
f787253 wip(nlp): Actualizar pipeline a v6.0 con validaciones de 6 campos nuevos
26b2f76 feat(nlp): Completar testing y documentación de NLP v6.0 (FASE 1 Tarea 3)
0e1d652 Migrar NLP v6.0 de Qwen 2.5:14b a Hermes 3:8b
```

---

## Regex Patterns History

---

## [Regex v4.0] - 2025-11-27

### Problema
v3.x no extraía:
- Edad con espacios ("1 8 años" → 18)
- Licencia de conducir con categoría
- Contratación inmediata
- Indexación salarial IPC
- Detección de consultoras vs empresa directa

### Cambios
- **Archivo:** `02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py`
- **7 clases nuevas:**
  1. `EdadPatterns`: "entre 1 8 y 3 5 años" → (18, 35)
  2. `LicenciaPatterns`: registro + categoría B1/C/D
  3. `ContratacionPatterns`: contratación/incorporación inmediata
  4. `IndexacionPatterns`: IPC, paritarias, frecuencia
  5. `EmpresaPatterns`: detectar Randstad, Manpower, etc.
  6. `HeaderPatterns`: extraer "Empresa: X", "Ubicación: Y"
  7. `BeneficiosPatterns`: obra social, ART, prepaga específicos
  8. `ViajesPatterns`: disponibilidad de viajes + porcentaje
- **Nuevo:** `StructureDetector` para calcular coverage

### Resultado
- Campos extraídos por regex: 15 → 28
- Cobertura CAPA 0: 50% → 70%

---

## [Regex v3.0] - 2025-11-01

### Problema
v2.x tenía efectividad de 37.6%

### Cambios
- **Archivo:** `02.5_nlp_extraction/scripts/patterns/regex_patterns_v3.py`
- **Objetivo:** Aumentar de 37.6% a 65-70%
- **Estrategia "ultra-agresiva":**
  - Experiencia SIN años: asignar exp = 1
  - Inferencia desde adjetivos: "amplia experiencia" = 5+ años
  - Detección por profesión: "Abogado" → universitario completo
  - Horarios sin "hs": "9 a 18" = "9 a 18hs"
  - Idioma implícito: "bilingual" → inglés avanzado
  - 200+ oficios argentinos nuevos

### Resultado
- Efectividad: 37.6% → **65%**

---

## ESCO Data History

---

## [ESCO v1.1.2 Load] - 2025-11-25

### Commits
```
bad492c feat(esco): Cargar 134,805 asociaciones ocupacion-skill (FASE 1 Tarea 1)
b6f8a18 feat(esco): Clasificar 14,247 skills en Knowledge vs Competency (FASE 1 Tarea 2)
```

### Datos cargados
| Tabla | Registros |
|-------|-----------|
| esco_occupations | 3,045 |
| esco_skills | 13,890 |
| esco_associations | 134,805 |

### Clasificación de skills
- Knowledge: 5,341
- Competency: 8,906
- Total clasificados: 14,247

---

## Gold Set History

---

## [gold_set_manual_v1.json] - 2025-11-28

### Creación
- 19 casos seleccionados manualmente
- Estratificación por score y tipo de error
- Campos: id_oferta, esco_ok, tipo_error, comentario

### Tipos de error categorizados
- `sector_funcion`: 4 casos
- `nivel_jerarquico`: 2 casos
- `programa_general`: 1 caso
- `tipo_ocupacion`: 1 caso

### Uso
```bash
python database/test_gold_set_manual.py
```

---

## Project Milestones

| Fecha | Milestone | Commit |
|-------|-----------|--------|
| 2025-11-28 | ESCO v8.3 + Dashboards | d9e229c |
| 2025-11-27 | NLP v7.0 Pipeline 3 capas | - |
| 2025-11-27 | Regex v4.0 completo | - |
| 2025-11-26 | NLP v6.0 (24 campos) | f787253 |
| 2025-11-25 | ESCO data cargado | bad492c |
| 2025-11-01 | Regex v3.0 ultra-agresivo | - |
| 2025-10-XX | Initial commit MOL v1.0 | ed3db7c |

---

> **Mantenedor:** Equipo MOL
> **Última actualización:** 2025-12-03
