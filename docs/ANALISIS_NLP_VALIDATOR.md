# Análisis NLP Validator — Variable por Variable

> Documento de trabajo. Captura las decisiones de diseño para la implementación del NLP Validator activo.
> Fecha inicio: 2026-02-14

## Contexto

El NLP extrae **164 columnas** de cada oferta. El validador actual cubre ~10.
El objetivo es recorrer cada grupo de variables, decidir:
- ¿Qué se valida?
- ¿Qué se normaliza automáticamente?
- ¿Qué genera regla nueva?
- ¿Qué se ignora (no vale la pena)?

## Decisiones ya tomadas

### Sector empresa (25 canónicos)
- **Se mantienen los 25 canónicos** (más granulares que las 20 letras CLAE)
- Relación: sector_canonico → clae_seccion (letra) → clae_code (6 dígitos)
- Colisiones: M tiene 4 sectores, N tiene 3, C tiene 3 — perder esa granularidad no conviene
- Aliases ya se normalizan en postprocessor (`_normalizar_sector_canonico`)
- **Pendiente**: 6 letras CLAE sin sector canónico (D, E, O, R, S, Z) — solo 2 ofertas hoy
- **Cobertura actual**: 92.8% con CLAE, 150 sin CLAE (79 sin sector, 71 sector "Otro")

### Reglas de exterior (V04/V05/V06)
- **ELIMINAR**. Código muerto — nunca se disparó, scrapeamos solo bumeran.ar
- Riesgo de falso positivo: "Concepción del Uruguay" (ciudad de Entre Ríos)
- Si algún día se scrapean portales regionales → crear categoría "territorio=exterior"

### Área funcional
- Es el **área de la empresa donde trabaja la persona** (no el sector de la empresa)
- 19 valores en BD, pero hay duplicados que necesitan normalización:
  - Ventas (537) + Ventas/Comercial (66) → ?
  - RRHH (61) + Recursos Humanos (16) → ?
  - IT (193) + IT/Sistemas (35) → ?
  - Finanzas (124) + Finanzas/Contabilidad (45) → ?
  - Logistica (92) + Logistica/Operaciones (1) → ?
- **Pendiente**: definir canónicos de área funcional y normalizar

---

## Análisis por grupo

### Grupo: Ubicación

**Campos vivos:**

| Campo | Cobertura | Decisión |
|-------|-----------|----------|
| provincia | 99.9% | OK, nada que tocar |
| localidad | 57.3% (217 valores) | OK, el 42.7% vacío = ofertas sin detalle de localidad |
| modalidad | 100% (3 valores: presencial/remoto/híbrido) | OK, perfecto |

**Campos muertos (0%, sacados en prompt lite v1):**

| Campo | En descripciones | Decisión |
|-------|-----------------|----------|
| tipo_lugar | 26.8% PERO ruido | **IGNORAR**. "planta"="comedor en planta", "obra"="obra social", regex no alcanza, necesitaría LLM |
| zona_residencia_req | 16.2% | **CANDIDATO a regex**. "residir en zona sur", "vivir cerca de" son frases fijas |
| requiere_viajar | 7.9% | **CANDIDATO a regex**. "disponibilidad para viajar" es frase fija |
| zonas_cobertura | 6.6% | Menor prioridad, se superpone con zona_residencia |
| requiere_movilidad_propia | 5.5% | **CANDIDATO a regex**. "movilidad propia", "vehículo propio" son claros |
| acepta_relocacion | 0.3% | **IGNORAR** |
| frecuencia_viaje | 0.1% | **IGNORAR** |
| radio_viaje_km | 0.4% | **IGNORAR** |

**Nota tipo_lugar**: Se verificó con ejemplos reales. Las keywords (planta, oficina, obra, local, depósito) aparecen en contextos ambiguos: "Obra Social" (beneficio), "comedor en planta" (beneficio), "a nivel local" (adjetivo). Regex genera más falsos positivos que detecciones útiles. Requeriría LLM para interpretar contexto, y el prompt lite ya está al límite.

**IMPLEMENTACIÓN Ubicación:**
- [x] Validar provincia: que sea provincia argentina válida (25 provincias + CABA) — regla nueva
- [x] Validar modalidad: que esté en {presencial, remoto, híbrido} — regla nueva
- [x] Eliminar V04/V05/V06 (reglas exterior Paraguay/Uruguay/Chile) de nlp_validation_rules.json
- [x] Eliminar `requiere_movilidad_propia` de la query del sync_to_supabase.py
- [ ] No hacer regex nuevos (zona_residencia, viajar, movilidad) — no vale la inversión

### Grupo: Experiencia

**Campos vivos (2 de 10):**

| Campo | Cobertura | Fuente | Estado |
|-------|-----------|--------|--------|
| experiencia_min_anios | 47.8% (1001) | LLM + regex | Distribución sana: 1-3 años = 83% |
| experiencia_max_anios | 4.3% (91) | LLM + regex | Muy bajo, pocas ofertas dan rango |

**Campos muertos (8 de 10, sacados en prompt lite):**
experiencia_area, experiencia_texto, experiencia_descripcion, experiencia_nivel_previo,
experiencia_sector, experiencia_areas_list, experiencia_excluyente, experiencia_valorada.
Todos 0%. **IGNORAR**.

**Gap de extracción:** 88% de las descripciones mencionan experiencia, pero solo 48% logra extraer el número. El 41% dice cosas como "experiencia comprobable" o "experiencia en el rubro" sin cifra → regex no puede sacar lo que no existe.

**Cross-validation experiencia × seniority:**

| Experiencia | Seniority coherente |
|-------------|-------------------|
| 0 | trainee, junior |
| 1-2 | junior, semisenior |
| 3-4 | semisenior, senior |
| 5+ | senior, manager, director |

- 0 inconsistencias trainee/junior con 5+ años (bien)
- **12 ofertas con 1 año + senior/manager** → el problema es seniority mal inferido del título ("Subencargado de local" → manager, pero con 1 año no es manager ESCO). Regla de cross-validation como **warning**.
- 48 ofertas con seniority NULL son todas sin experiencia → no se puede inferir seniority desde experiencia en esos casos

**Regla propuesta:** `NV_EXP_SENIORITY`: Si experiencia_min ≤ 1 AND seniority IN (senior, manager, director) → warning "Verificar seniority, experiencia baja para ese nivel"

**Llega al dash:** Solo `experiencia_min_anios`. experiencia_max_anios (4.3%) no se sincroniza.

**IMPLEMENTACIÓN Experiencia:**
- [x] Validar experiencia_min_anios: si tiene valor, numérico >= 0 y <= 30
- [x] Validar experiencia_max_anios: si tiene valor, >= experiencia_min (no invertidos)
- [x] Cross-validar NV_EXP_SENIORITY: experiencia_min ≤ 1 + seniority senior/manager/director → warning
- [ ] No hacer nada con los 8 campos muertos

### Grupo: Educación

**Campos vivos (2 de 9):**

| Campo | Cobertura | Estado |
|-------|-----------|--------|
| nivel_educativo | 70.8% (1481) | 4 valores cerrados: universitario (53%), secundario (23%), terciario (23%), primario (1%). Limpio. |
| titulo_requerido | 47.5% (994) | Texto libre (797 distintos). 19 null-like ("null", "no especificado") a limpiar. |

**Campos muertos (7 de 9):**
estado_educativo, carrera_especifica, titulo_excluyente, orientacion_estudios,
acepta_estudiantes_avanzados, estudios_valorados_list, nivel_educativo_excluyente.
Todos 0%. **IGNORAR**.

**Gap**: 62% de las descripciones mencionan educación, nivel_educativo cubre 71%. Gap real ~8% (163 ofertas dicen "valoramos estudios" sin especificar nivel). Tolerable.

**Cross-validation educación × seniority:** Sin inconsistencias (0 primario+manager, 1 secundario+manager).

**Acción:** Limpiar null-like en titulo_requerido (19 casos). `_normalize()` ya limpia null-like pero puede no cubrir este campo.

**Llega al dash:** Solo `nivel_educativo`. titulo_requerido se lee de BD pero no se envía a Supabase.

**titulo_requerido y matching:** No se usa en matching hoy. Podría ser señal fuerte (ej: "Contador Público" → ISCO 2411). Tiene 47.5% cobertura, 793 valores distintos (texto libre). Solución: normalizar con **CINE-F 2013** (UNESCO) — mismo patrón que ESCO/CLAE/ISCO. **Branch separado: `feature/cine-clasificador`**.

**IMPLEMENTACIÓN Educación:**
- [x] Validar nivel_educativo: que esté en {primario, secundario, terciario, universitario, posgrado}
- [x] Normalizar titulo_requerido: limpiar 19 null-like → NULL real
- [ ] No hacer nada con los 7 campos muertos
- [ ] FUTURO (branch separado): Clasificador CINE-F para titulo_requerido → código internacional + uso en matching

### Grupo: Idiomas

**Campos muertos (4 de 4, sacados en prompt lite):**

| Campo | Cobertura | En descripciones | Decisión |
|-------|-----------|-----------------|----------|
| idioma_principal | 0% | 12.7% (inglés), 15.2% (cualquier idioma) | **CANDIDATO a regex** |
| nivel_idioma_principal | 0% | 6.1% con nivel explícito | **CANDIDATO a regex** |
| idioma_secundario | 0% | 6.8% portugués, 1.2% francés | Menor prioridad |
| nivel_idioma_secundario | 0% | Casi nulo | **IGNORAR** |

**Análisis de menciones de idiomas en descripciones (set NLP = 2093):**
- Inglés total: 265 (12.7%) — de esas, 127 con nivel explícito (avanzado/intermedio/básico/fluido), 14 como beneficio ("clases de inglés"), 115 mención sin nivel
- Portugués: ~30 en set NLP (1.4%)
- Francés/alemán/italiano/chino: < 1% cada uno

**Decisión:** Idioma + nivel son buenos candidatos a **regex** para los casos con nivel explícito (127 ofertas = 6.1%). Los patrones son muy fijos: "inglés avanzado (excluyente)", "nivel de inglés intermedio", "bilingüe". No tiene sentido gastar tokens LLM en esto.

**Regex propuesta:**
- `(?:inglés|ingles)\s+(?:avanzado|intermedio|básico|basico|fluido|nativo)` → idioma=inglés, nivel=X
- `(?:portugués|portugues)\s+(?:avanzado|intermedio)` → idioma=portugués, nivel=X
- `bilingüe|bilingue` → idioma=inglés, nivel=avanzado
- Contexto negativo: "clases de inglés" → IGNORAR (es beneficio, no requisito)

**Llega al dash:** Nada de idiomas hoy. Agregar al sync después de implementar regex.

**IMPLEMENTACIÓN Idiomas:**
- [x] Regex en postprocessor: extraer idioma_principal + nivel_idioma_principal de descripción
- [x] Regex inglés: `(?:inglés|ingles)\s+(?:avanzado|intermedio|básico|basico|fluido|nativo)` + contexto negativo ("clases de")
- [x] Regex portugués: `(?:portugués|portugues)\s+(?:avanzado|intermedio)`
- [x] Regex bilingüe: `bilingüe|bilingue` → inglés avanzado
- [x] Regex idioma secundario: si ya hay principal y aparece otro idioma con nivel
- [x] Agregar idioma_principal + nivel_idioma_principal al sync_to_supabase.py
- [x] Útil para análisis de mercado (% ofertas que piden idioma)

### Grupo: Skills y Tecnologías

**Importante:** Hay DOS sistemas de skills que no confundir:
1. **Skills NLP** (ofertas_nlp): Lo que el LLM extrae directo de la descripción → `skills_tecnicas_list`, `soft_skills_list`, etc.
2. **Skills Matching** (ofertas_esco_matching): Lo que `skills_implicit_extractor.py` genera mapeando contra ESCO → `skills_oferta_json`

Las skills NLP alimentan al extractor de skills, que produce las skills ESCO usadas en matching.

**Campos vivos (3 de 6):**

| Campo | Cobertura | Contenido | Estado |
|-------|-----------|-----------|--------|
| skills_tecnicas_list | 95.0% (1988) | Texto separado por `;`. Fuente principal para matching. | OK, buena cobertura |
| soft_skills_list | 64.5% (1350) | Texto libre separado por `,`. No se usa en matching ESCO. | OK, informativo |
| herramientas_list | 25.9% (542) | Herramientas específicas (Excel, Tango, SAP). | OK, complementa skills |
| tecnologias_list | 27.7% (580) | Solapamiento con herramientas: 176 tienen ambos. | Evaluar merge con herramientas |

**Campos muertos (2 de 6):**

| Campo | Cobertura | Decisión |
|-------|-----------|----------|
| certificaciones_list | 0% (2093 NULL) | **IGNORAR**. Sacado en prompt lite. |
| sistemas_list | 0% (2093 NULL) | **IGNORAR**. Sacado en prompt lite. |

**Overlap herramientas vs tecnologías:** 176 ambos, 367 solo herramientas, 404 solo tecnologías, 1146 ninguno. Los campos se solapan ("Excel" aparece en ambos según el contexto). Podrían mergearse pero no es prioritario — el extractor de skills los unifica al mapear contra ESCO.

**Flujo skills: NLP → Matching:**
- skills_tecnicas_list (95%) → skills_implicit_extractor → skills_oferta_json (98.7%)
- Solo 10 ofertas tienen skills NLP pero no skills matching → gap mínimo
- Skills matching promedio: 16.4 por oferta (mediana 16), rango 3-34

**Validación propuesta:** El 5% sin skills_tecnicas es el mismo grupo sin tareas (datos_insuficientes). No necesita regla nueva, V11/NV08 ya lo cubre.

**PROBLEMA CRÍTICO: Duplicados de skills ESCO en dashboard**

El dashboard muestra skills duplicadas que fragmentan conteos y generan desconfianza del usuario.
Ejemplo: "trabajo en equipo" (50 ofertas) y "trabajo en equipos" (30 ofertas) aparecen como 2 skills separadas.

**3 tipos de duplicados encontrados:**

| Tipo | Cantidad | Ejemplo | Causa |
|------|----------|---------|-------|
| Acento/plural | 15 pares | "trabajo en equipo" vs "trabajo en equipos" | Variantes tipográficas ESCO |
| Mismo label, distinta URI | 63 grupos | skill con URI_A y URI_B | ESCO tiene skills en distintos contextos |
| URI = None | Muchas | Skills de rules engine sin URI | `skills_rules_matcher.py` no asigna URI |

**`normalize()` actual** (en API perfil-argentina y script batch): solo hace `trim().toLowerCase()` — NO normaliza acentos ni plurales. Esto causa:
- `coverage_essential` **deflateada** (skills ESCO "faltantes" que están con variante)
- `emerging_count` **inflateado** (falsos emergentes que son variantes de ESCO)
- `frequency` por skill **fragmentada** (conteo partido en 2+)

**Impacto en Perfil Consolidado:**
- Admin aprueba como "emergentes argentinas" skills que son variantes tipográficas de ESCO
- La cobertura real de ESCO es MAYOR de lo que se muestra
- El % de frecuencia está fragmentado → decisiones de aprobación basadas en datos incorrectos

**Solución propuesta (3 capas, en sync layer):**
1. **Normalización de texto:** Quitar acentos, normalizar plurales en `preferred_label` al sincronizar a Supabase
2. **Mapeo canónico de URIs:** JSON `config/esco_skill_canonical.json` que mapea URI duplicadas → URI canónica
3. **Resolver NULL URIs:** Buscar URI correcta para skills del rules engine que llegan sin URI

**Punto de aplicación:** En `sync_to_supabase.py` al armar `ofertas_skills` — así ambas tabs se benefician sin tocar API ni componentes React.

**Branch separado:** `feature/skills-dedup` — es un concern independiente del NLP validator.

**IMPLEMENTACIÓN Skills (NLP validator):**
- [x] No crear reglas nuevas de validación para skills NLP — V11/NV08 ya cubre los sin tareas/skills
- [x] Validar skills_count (migrar V03 existente): < 3 skills → medio
- [ ] BRANCH SEPARADO `feature/skills-dedup`: Deduplicación 3 capas en sync layer
- [ ] PENDIENTE: Definir canónicos de área funcional (5 pares duplicados, ver grupo Clasificación)

### Grupo: Salario

**Campos muertos (4 de 4):**

| Campo | Cobertura | Decisión |
|-------|-----------|----------|
| salario_min | 0.4% (9) | **IGNORAR** |
| salario_max | 0.2% (4) | **IGNORAR** |
| moneda | 0.7% (14, todas ARS) | **IGNORAR** |
| salario_periodo | 0% | **IGNORAR** |

**Realidad:** 21.5% de las descripciones mencionan "salario/sueldo/remuneración" pero casi nunca con cifra (0.8% tiene `$`, 0.2% "pesos"). Las empresas argentinas no publican el número — dicen "remuneración acorde" o "sueldo competitivo".

**Fuente alternativa:** `salario_obligatorio` (INTEGER) viene del campo estructurado del formulario de Bumeran (scraping), no del NLP. Es la única fuente real de salario.

**Decisión:** No vale la pena extraer salario de la descripción. **IGNORAR** los 4 campos NLP.

### Grupo: Condiciones laborales

**Campos vivos (2 de 5):**

| Campo | Cobertura | Valores | Estado |
|-------|-----------|---------|--------|
| jornada_laboral | 48.1% (1006) | full-time (899), part-time (69), freelance (38) | **REDUNDANTE** con scraping `tipo_trabajo` (100%, más confiable) |
| tipo_contrato | 18.8% (393) | monotributo (161), contrato (117), efectivo (98), pasantia (17) | Valor propio, Bumeran no tiene este campo estructurado |

**Campos muertos (3 de 5):**

| Campo | Cobertura | En descripciones | Decisión |
|-------|-----------|-----------------|----------|
| horario_flexible | 0% | 2.2% (46) | **IGNORAR** — muy bajo |
| trabajo_nocturno | 0% | 1.5% (32) | **IGNORAR** — muy bajo |
| trabajo_turnos_rotativos | 0% | 4.3% (91) | **IGNORAR** — candidato menor, no prioritario |

**Hallazgo clave jornada_laboral:** El scraping trae `tipo_trabajo` al 100% con más detalle (Full-time, Part-time, Por Horas, Pasantia, Temporario, Nocturno, Fines de Semana). El NLP extrae lo mismo pero peor: 48% cobertura y con errores (34 NLP=full-time vs scraping=Part-time, 32 NLP=freelance vs scraping=Full-time). **Decisión:** Usar `tipo_trabajo` del scraping, jornada_laboral NLP es redundante y menos confiable.

**tipo_contrato (18.8%):** Aporta valor propio. "Monotributo" (0.9% en desc), "relación de dependencia" (7.8%), "pasantía" (0.6%). Cobertura baja pero dato que no existe en scraping.

**Llega al dash:** `jornada_laboral` SÍ (payload línea 593). `tipo_contrato` NO (se lee de BD pero no entra al payload de Supabase).

**IMPLEMENTACIÓN Condiciones Laborales:**
- [x] Validar jornada_laboral: si tiene valor, que esté en {full-time, part-time, freelance} — regla nueva
- [x] Validar tipo_contrato: si tiene valor, que esté en {monotributo, contrato, efectivo, pasantia} — regla nueva
- [ ] No hacer nada con los 3 campos muertos (horario_flexible, trabajo_nocturno, trabajo_turnos_rotativos)
- [ ] EVALUAR: Agregar `tipo_contrato` al sync (18.8% cobertura, dato único no disponible en scraping)
- [x] **CAMBIO DASH**: Reemplazar `jornada_laboral` (NLP, 48%) por `tipo_trabajo` (scraping, 100%) en sync + filtro + gráfico Requerimientos. El filtro actual pierde la mitad de las ofertas porque el NLP no extrajo jornada.
- [ ] FUTURO: Mejorar extracción `tipo_contrato` (regex: "relación de dependencia", "monotributo", "contrato temporal"). Cobertura actual 18.8%.
- [ ] FUTURO: Inferir tipo de contratación por combinatoria de variables para el 81% sin dato: tipo_oferta (freelance→monotributo), es_intermediario (consultora→contrato tercerizado), empresa conocida+full-time→efectivo. Objetivo: eliminar "Sin especificar" en el dash.

### Grupo: Empresa

**Campos vivos (4 de 5):**

| Campo | Cobertura | Contenido | Estado |
|-------|-----------|-----------|--------|
| sector_empresa | 93.5% (1957) | 25 canónicos. Top: Comercio (565), Salud (229), Industria (215), Tecnologia (207). 103 "Otro", 136 sin sector | OK, 6.5% sin dato = limitación LLM |
| sector_confianza | 93.3% (1952) | media (1636, 84%), alta (316, 16%) | Eslabón débil: 84% confianza media |
| sector_fuente | 93.3% (1952) | llm (1636), frase_explicita (191), empresa_conocida (124), catalogo (1) | OK, metadata útil |
| es_intermediario | 100% (2093) | No (1487, 71%), Sí (606, 29%). Top: Grupo Gestión, Manpower, CONA, Adecco | OK, dato valioso |

**Campos muertos (1 de 5):**

| Campo | Cobertura | En descripciones | Decisión |
|-------|-----------|-----------------|----------|
| empresa_tamanio | 0% | multinacional 4.2%, empresa líder 4.8%, pyme 2.7%, startup 0.7% | **IGNORAR** — texto marketing ambiguo, no extraíble |

**Notas:**
- 84% del sector viene del LLM con confianza media — es lo menos confiable del grupo
- 136 sin sector: 29 intermediarios (consultoras no dicen sector del cliente), resto descripciones genéricas
- 103 "Otro": LLM no pudo clasificar en 25 canónicos
- 29% intermediarios (606): para esas ofertas el sector es del cliente, no de la consultora
- Validaciones V20/V21 ya filtran cross-sector solo cuando `confianza=alta` (fix sprint 6)

**Llega al dash:** Solo `sector_empresa`. `sector_confianza`, `sector_fuente`, `es_intermediario` NO se sincronizan a Supabase.

**IMPLEMENTACIÓN Empresa:**
- [x] Validar sector_empresa: que esté en 25 canónicos (ya existe como NV02 en plan) — **alto** gate
- [x] Validar null-like en sector_empresa (ya existe como NV11): "null", "None", "sin dato" → NULL real
- [x] Migrar V18 (sector = area_funcional coinciden) → warning
- [x] Migrar V19 (sector=Seguridad + area no vigilancia) → warning
- [x] Migrar V20/V21 (cross sector-area con confianza alta) → info
- [x] Migrar V22 (empresa confidencial + sector) → info
- [ ] No hacer nada con empresa_tamanio (0%)
- [ ] EVALUAR: Agregar `es_intermediario` al sync (100% cobertura, dato valioso para filtrar consultoras)

### Grupo: Clasificación

**Campos vivos (4 de 4):**

| Campo | Cobertura | Valores | Estado |
|-------|-----------|---------|--------|
| area_funcional | 100% (2093) | 19 valores, 5 pares duplicados | **Normalizar duplicados** (163 ofertas) |
| nivel_seniority | 97.7% (2045) | semisenior (907), trainee (468), junior (366), senior (190), manager (114) | OK, 48 sin dato |
| tipo_oferta | 100% (2093) | demanda_real (2006), freelance (53), pasantia (31), becario (3) | OK, limpio |
| tiene_gente_cargo | 100% (2093) | No (1753, 84%), Sí (340, 16%) | OK |

**Duplicados area_funcional (163 ofertas afectadas):**
- Ventas (537) + Ventas/Comercial (66) → unificar
- IT (193) + IT/Sistemas (35) → unificar
- Finanzas (124) + Finanzas/Contabilidad (45) → unificar
- RRHH (61) + Recursos Humanos (16) → unificar
- Logistica (92) + Logistica/Operaciones (1) → unificar

**Cross-validation tiene_gente_cargo × seniority:**
- **19 junior con gente a cargo** — sospechoso
- **35 trainee con gente a cargo** — sospechoso
- 13 manager SIN gente a cargo — posible (project manager sin equipo directo)
- manager+gente (101), senior+gente (84) — coherente
- **Regla propuesta NV_CROSS:** trainee/junior + tiene_gente_cargo=1 → warning

**48 sin seniority:** Solo 1 tiene gente a cargo. Ofertas donde LLM no pudo inferir nivel.

**Llega al dash:** `area_funcional`, `nivel_seniority`, `tiene_gente_cargo` SÍ. `tipo_oferta` NO (se lee de BD pero no entra al payload Supabase).

**IMPLEMENTACIÓN Clasificación:**
- [x] Validar area_funcional: que esté en valores válidos (ya existe como NV03 en plan) — **alto** gate
- [x] Normalizar 5 pares duplicados de area_funcional en postprocessor: Ventas/Comercial→Ventas, IT/Sistemas→IT, Finanzas/Contabilidad→Finanzas, Recursos Humanos→RRHH, Logistica/Operaciones→Logistica
- [x] Validar nivel_seniority: que esté en 7 valores (ya existe como NV04 en plan) — **alto** gate
- [x] Validar tipo_oferta: que esté en {demanda_real, freelance, pasantia, becario} (ya existe como NV06 en plan) — medio
- [x] Cross-validar NV_CROSS: trainee/junior + tiene_gente_cargo=1 → warning (bajo)
- [x] **CAMBIO MATCHING**: Reincorporar `tiene_gente_cargo` como penalización en matching v3 (como estaba en v2: tiene_gente=0 → penalizar ISCO 1xxx directivos; tiene_gente=1 + ISCO 1xxx → boost)
- [ ] `tipo_oferta`: NO agregar al dash. "demanda_real" (96%) no aporta al usuario. freelance/pasantia/becario ya cubiertos por `tipo_trabajo` del scraping. Se mantiene como campo interno para validación.

### Grupo: Tareas

**Campos:**

| Campo | Cobertura | Estado |
|-------|-----------|--------|
| tareas_explicitas | 93.9% (1965) | Principal fuente de tareas, formateado con `;` |
| tareas_inferidas | 0.2% (4) | **Prácticamente muerto** — solo 4 ofertas, no vale mantener |

**Desglose cobertura:**
- Solo explícitas: 1965 (93.9%)
- Solo inferidas: 4 (0.2%)
- Ambas vacías: 124 (5.9%) — de esas, 101 tienen skills (extractor infiere del título), 23 nada

**Longitud tareas_explicitas:**
- < 50 chars: 73 — tareas muy cortas ("Manejo de lex doctor", "Armado de pedidos"). Son los V29 conocidos.
- 50-99: 155
- 100-199: 389
- 200-499: 960 (grueso)
- 500+: 388

**Formato:** 1871 usan `;` como separador, 0 usan solo `,`. Limpio.

**Notas:**
- Las 73 tareas < 50 chars = LLM extrae parcial cuando desc tiene bullet lists (limitación LLM, no config)
- Las 124 sin tareas = datos_insuficientes (ya cubierto por V11/NV08)
- 101 sin tareas pero con skills = extractor infiere del título como fallback
- tareas_inferidas casi muerto: solo 4 inferencias del título. No justifica campo separado.

**Llega al dash:** NO. `tareas_explicitas` se lee de BD pero no entra al payload de Supabase. Es insumo interno para el extractor de skills.

**IMPLEMENTACIÓN Tareas:**
- [x] Migrar V11 (tareas ambas vacías) → **alto** gate
- [x] Migrar V25 (tareas vacías + skills presentes) → medio
- [x] Migrar V26 (formato comas en vez de `;`) → medio
- [x] Migrar V29 (tareas < 50 chars) → bajo
- [x] **ELIMINAR `tareas_inferidas`**: Campo muerto (4 ofertas), no útil. Sacar del prompt/postprocessor/BD.
- [ ] No necesita reglas nuevas — las existentes cubren los casos

### Grupo: CLAE

**Campos:**

| Campo | Cobertura | Contenido | Estado |
|-------|-----------|-----------|--------|
| clae_code | 92.8% (1943) | 6 dígitos | OK, 150 sin CLAE = limitación datos |
| clae_grupo | 92.8% (1943) | 3 dígitos, derivado mecánico de clae_code | OK, no es campo independiente |
| clae_seccion | 92.8% (1943) | Letra (A-R). Top: G/Comercio (575), J/Info-Comm (307), C/Industria (253), Q/Salud (233) | OK |
| clae_score | 5.2% (109) | Solo para clasificaciones semánticas | OK, 1834 usan mapeo directo (sin score) |
| clae_metodo | 5.5% (115) | semantico_seccion (72), semantico (19), default_seccion (18), sector_directo (6) | OK |

**150 sin CLAE:**
- 79 sin sector (LLM no pudo determinar)
- 71 con sector "Otro" (no entró en canónicos)
- 0 con sector válido sin CLAE — todo lo que tiene sector ya tiene CLAE

**Cross sector→sección:** Coherente. Comercio→G, Salud→Q, Tecnologia→J, Industria→C. Combinaciones "raras" (J+Industria=15, J+Marketing=12) son empresas de esos sectores publicando puestos IT/marketing — normal.

**Nota score/método:** 94.5% clasificado por mapeo directo (sector→sección→código semántico dentro de sección), sin score ni método. Solo 109 pasaron por clasificación semántica pura.

**Llega al dash:** `clae_code`, `clae_grupo`, `clae_seccion`, `clae_score`, `clae_metodo` + `clae_descripcion_seccion` (derivada). Todo llega.

**IMPLEMENTACIÓN CLAE:**
- [x] Migrar V17 (sección CLAE inválida, no es letra A-R) → **alto** gate
- [x] Migrar V16 (sector sin CLAE) → info
- [ ] 150 sin CLAE = limitación de datos (79 sin sector + 71 sector "Otro"), no se puede hacer más
- [ ] ~~NV_CLAE cross sector-sección~~: DESCARTADO — sección CLAE se deriva mecánicamente del sector canónico, no puede haber incoherencia

### Grupo: Títulos

**Campos vivos (1 de 6):**

| Campo | Cobertura | Estado |
|-------|-----------|--------|
| titulo_limpio | 100% (2093) | Principal. 89.6% difiere del original (limpieza funciona). |

**Campos muertos (5 de 6):**

| Campo | Cobertura | Decisión |
|-------|-----------|----------|
| titulo_excluyente | 0% | **IGNORAR** |
| titulo_repetido_en_descripcion | 0% | **IGNORAR** |
| titulo_genero_especifico | 0% | **IGNORAR** |
| titulo_normalizado | 0% | **IGNORAR** |
| titulo_requerido | 46.5% (974) | Ya analizado en Educación (título académico, no de la oferta) |

**Longitud titulo_limpio:**
- < 10 chars: 85 — títulos que perdieron contexto en limpieza ("Personal para Depósito en Villa Soldati" → "Personal")
- 10-19: 434
- 20-39: 1066 (grueso)
- 40-59: 377
- 60-79: 103
- 80+: 28

**Nota:** Los 85 títulos < 10 chars quedaron genéricos post-limpieza. La limpieza hizo bien en sacar ubicación/empresa, pero el título queda débil para matching.

**Llega al dash:** `titulo` (original) y `titulo_limpio` SÍ.

**IMPLEMENTACIÓN Títulos:**
- [x] Migrar V01 (titulo_limpio vacío) → **critico** gate
- [x] Migrar V07 (código interno no limpiado en título) → medio
- [ ] 85 títulos < 10 chars = warning informativo, no bloqueante
- [ ] No hacer nada con los 5 campos muertos

### Grupo: Otros campos vivos

**mision_rol** — 91.0% (1905):
- Texto libre, una oración con el objetivo principal del puesto
- Longitud: <50 (54), 50-99 (708), 100-199 (864), 200+ (279)
- Resumen del rol generado por el LLM. No se usa en matching, útil para dashboard.

**requerimiento_edad** — 93.2% (1950, pero 80% es "0"):
- Categorías del prompt: 0=sin requisito, 1=18-25, 2=25-35, 3=35-45, 4=45+, 5=ambiguo
- Distribución: 0 (1565), 5/ambiguo (258), 3 (50), 2 (38), 1 (24), 4 (15), NULL (143)
- El 258 "ambiguo" es ruido — LLM pone 5 cuando no sabe
- **Variable sensible** (discriminación laboral). Útil para análisis de mercado.

**requerimiento_sexo** — 93.2% (1950, pero 91% es "0"):
- Categorías: 0=sin requisito, 1=masculino, 2=femenino
- Distribución: 0 (1909), 1/masculino (34), 2/femenino (7), NULL (143)
- Masculino: repositores, soldadores, operarios, choferes
- Femenino: subencargada, enfermera, vendedoras indumentaria femenina
- **Variable sensible** (discriminación laboral).

**es_republica** — 15.8% (330):
- Flag: 1=oferta aplica a nivel nacional, NULL=no
- Las 330 tienen provincia asignada igual. Se infiere de "a nivel república" o "todo el país".

**calidad_texto** — 1.5% (32):
- Solo valor: "baja_sin_tareas". Flag del postprocessor cuando no hay tareas extraíbles.
- Subconjunto de los 124 sin tareas.

**IMPLEMENTACIÓN Otros campos vivos:**
- [x] **ELIMINAR `calidad_texto`**: Campo huérfano, no se genera en NLP v11, columna siempre vacía. Sacar de BD.
- [ ] FUTURO DASH: `mision_rol` → descripción corta del puesto (cosmético)
- [ ] FUTURO DASH: `requerimiento_edad` + `requerimiento_sexo` → análisis de discriminación laboral (variables sensibles, alta importancia para análisis de mercado)
- [ ] `es_republica` → dato complementario de ubicación, evaluar si agregar al dash

### Campos muertos no listados (89 columnas)

89 columnas adicionales en ofertas_nlp con 0% de cobertura. Todas sacadas en prompt lite v1. Incluyen: beneficios (beneficios_list, prepaga, obra_social, tiene_comedor, etc.), licencias (licencia_conducir, licencia_autoelevador), condiciones físicas (trabajo_en_altura, carga_peso_kg, requiere_esfuerzo_fisico), horarios detallados (hora_entrada, hora_salida, dias_laborales), y metadata sin uso (nlp_confidence_score, campos_con_fuente_json, errores_detectados_list). **IGNORAR** todas.
