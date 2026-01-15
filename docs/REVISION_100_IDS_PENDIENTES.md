# Revisión 100 IDs - Cambios Pendientes

**Fecha inicio:** 2026-01-12
**Estado:** En revisión

## Resumen

Revisando 100 ofertas procesadas con NLP v11.3 + Matching v3.2 para detectar errores y acumular correcciones antes de aplicar nueva versión.

---

## Cambios Acumulados

### 1. Prompt NLP (extraction_prompt_lite_v1.py)

| Cambio | Descripción | ID que lo motivó |
|--------|-------------|------------------|
| Regla 3 - tareas_explicitas | Separar cada tarea con punto y coma, no concatenar | 1118105872 |
| area_funcional incorrecta | "Jefe de Producto" en Moda asignado a RRHH (debería ser Operaciones/Logística) | 1118105850 |
| area_funcional incorrecta | "Subencargado de Local" (retail) asignado a RRHH (debería ser Ventas) | 1118101812 |
| area_funcional incorrecta | "Analista de Créditos" en concesionaria asignado a Ventas (debería ser Finanzas) | 2172229 |
| sector_empresa incorrecto | "Residuos industriales" clasificado como "Salud" (debería ser Industria/Medio Ambiente) | 1118105713 |
| sector_empresa incorrecto | "FCI/Alyc" (servicios financieros) clasificado como "Comercio" (debería ser Finanzas) | 1118102067 |
| sector_empresa incorrecto | "Seguridad electrónica" (alarmas, cámaras) clasificado como "Textil/Confeccion" (GRAVE) | 1118101077 |
| sector_empresa incorrecto | "Servicios funerarios" clasificado como "Salud" (debería ser Servicios) | 2172212 |
| nivel_seniority incorrecto | "Jefe de Delegación" clasificado como semisenior (debería ser manager) | 2172211 |
| titulo_limpio no limpio | Títulos con códigos/ubicación no se limpian: "JAVA Architect - Remoto - 1729" | 2172192, 2172191 |
| skills_tecnicas_list ruido | "LEX DOCTOR" (software jurídico) genera skills médicas | 2172198 |

**Código modificado:** Líneas 78-83 - Nueva regla con ejemplo OK/MAL

**Impacto:** Requiere re-procesar NLP para todas las ofertas

---

### 2. Matcher (match_ofertas_v3.py)

| Cambio | Descripción | ID que lo motivó |
|--------|-------------|------------------|
| titulo_no_contiene_alguno | Exclusión por palabras en título | 1118105872 |
| sector_no_es | Exclusión por sector | 1118105872 |
| area_funcional_no_es | Exclusión por área | 1118105872 |
| sector_es | Filtro positivo por sector | 1118105872 |

**Impacto:** Solo requiere re-matchear (rápido)

---

### 3. Reglas de Negocio (matching_rules_business.json)

| Regla | Cambio | ID que lo motivó |
|-------|--------|------------------|
| R14_contador_auditor | Agregadas exclusiones: médico, sector Salud | 1118105872 |
| R14b_auditor_medico | NUEVA: Auditor Médico → ISCO 2212 | 1118105872 |
| R14c_auditor_medico_alt | NUEVA: Variante sin acento | 1118105872 |
| R29_modelista_textil | DIVIDIR: modelista/patronista ≠ sastre | 1118106004 |
| R29a_patronista | NUEVA: modelista, patronista, moldería → ISCO 7532 | 1118106004 |
| R29b_sastre | MODIFICAR: modista, sastre, sastrería → ISCO 7531 | 1118106004 |
| R_XX_operario_plastico | NUEVA: industria plástica, inyección, soplado → ISCO 8142 | 1118105856 |
| R_XX_mecanico_vehiculos | NUEVA: mecánico + sector Logística/Transporte → ISCO 7231 (NO barcos) | 1118105765 |
| R_XX_encargado_ganadero | NUEVA: encargado/capataz + ganadero/campo/cría → ISCO 6121 o 1311 | 1118105759 |
| R_XX_analista_qa_farma | NUEVA: analista + calidad + (farmacéutico/laboratorio) → ISCO 2145/3111 (NO osteópata) | 1118105736 |
| R_XX_operador_sim_aduanas | NUEVA: operador + (SIM/María/aduanero/despacho) → ISCO 3331 (agente aduanas) | 1118105715 |
| R40_asesor_comercial | AJUSTAR: Excluir "ambulante" - vendedor ambulante ≠ representante comercial | 1118101510 |
| R_XX_vendedor_ambulante | NUEVA: vendedor/a + ambulante → ISCO 9520 | 1118101510 |
| R42_gerente_operaciones | AJUSTAR: Debe considerar SECTOR - gastronomía ≠ fabricación | 1118091304 |
| R_XX_secretaria_admin_educacion | NUEVA: secretaria/asistente + (posgrado/universidad/académico) → ISCO 3343/4110 (NO docente) | 2172236 |
| R_XX_analista_creditos | NUEVA: analista + (crédito/préstamo/financiación) → ISCO 3312 (NO vendedor) | 2172229 |
| R_XX_admin_funeraria | NUEVA: administrativo + (cementerio/funeraria) → ISCO 4110/4226 (NO lavandería) | 2172212 |
| R_XX_jefe_delegacion_finanzas | NUEVA: jefe + (delegación/sucursal) + (finanzas/créditos) → ISCO 1221/1324 (NO ingeniero) | 2172211 |
| R_XX_arquitecto_software | NUEVA: (architect/arquitecto) + (Java/software/.NET) → ISCO 2512 (NO gestor negocio) | 2172192 |
| R_XX_devops_engineer | NUEVA: devops + (engineer/ingeniero) → ISCO 2512/2523 (NO operador centro datos) | 2172191 |

**Impacto:** Solo requiere re-matchear (rápido)

---

### 4. Skills Extractor (skills_implicit_extractor.py)

| Problema | Descripción | ID que lo motivó |
|----------|-------------|------------------|
| Falsos positivos | Skills no relacionadas pasan el umbral (0.55) | 1118106004 |
| Ejemplos ruido | "conducir tuneladoras", "controles de erosión" para Modelista textil | 1118106004 |
| Ejemplos ruido | "reparar equipo de navegación", "sistemas mecánicos de buques" para Mecánico camiones | 1118105765 |
| Skills inferidas incorrectamente | "supervisar reparación vehículos" para Mecánico operativo (no supervisor) | 1118105760 |
| Skills inferidas incorrectamente | "gestionar operaciones almacén" para Operario (no jefe) | 1118105712 |
| Skills ruido absurdo | "asistir en controles de vuelo" para Analista financiero | 1118102067 |
| Palabra polisémicas mal resueltas | "Operador SIM" (sistema aduanero) → skills de máquinas industriales | 1118105715 |
| Términos ARG no reconocidos | FCI, Alyc, Invera (finanzas) → sector "Comercio" y match retail | 1118102067 |
| Skills genéricas pesan más que específicas | "limpieza" (0.91) > "operar máquinas plástico" (0.68) → match incorrecto | 1118105856 |
| Skills genéricas pesan más que específicas | "gestionar equipo" (0.73) > "ganadería de cría" (no en top) → salón belleza | 1118105759 |
| Skills genéricas pesan más que específicas | "responder llamadas" (0.75) > "sistemas alarma" (0.67) → encuestador mercado | 1118102051 |
| Skills genéricas pesan más que específicas | "investigación académica" (0.85) > "musculoesquelético" (0.77) → psicólogo vs traumatólogo | 1118101068 |
| Colaboración ≠ Rol principal | "Colaborar con Marketing" → skills marketing altas → Responsable Marketing (pero rol es Operaciones) | 1118097995 |
| Skills operativas > gerenciales | "carga/descarga" (0.78) para Jefe Sucursal → jefe estibadores (nivel_seniority=manager ignorado) | 1118086791 |
| **SECTOR NO SE USA EN MATCHING** | Skills de gestión matchean con cualquier rol gerencial sin importar sector | 1118105850 |

**Posibles fixes:**
- Subir umbral de 0.55 a 0.60-0.65
- Filtrar skills por coherencia con sector/área
- Blacklist de skills obviamente incorrectas por contexto
- Ponderar skills específicas del sector sobre genéricas (limpieza, trabajo en equipo, etc.)
- **CRÍTICO: Usar sector_empresa como filtro/peso en el matching** (Moda≠Gastronomía aunque skills sean similares)
- **CRÍTICO: Usar skills_tecnicas_list del NLP como input adicional** (actualmente solo usa tareas_explicitas + titulo)

**Impacto:** Requiere ajustar extractor y re-procesar skills

---

### 5. CRÍTICO: Skills Extractor NO usa skills_tecnicas_list del NLP

| Campo NLP | Se usa en Matching? | Impacto de no usarlo |
|-----------|---------------------|----------------------|
| titulo | Sí (embedding) | - |
| tareas_explicitas | Sí (extracción skills ESCO) | - |
| **skills_tecnicas_list** | **NO** | Info perdida (ID 1118105715) |
| **sector_empresa** | **NO** | Matches cross-sector (IDs 1118105850, 1118105759) |
| **area_funcional** | **NO** | Matches cross-área |
| **nivel_seniority** | **NO** | Operario→Jefe (ID 1118105712) |

**Evidencia (ID 1118105715):**
- NLP extrajo "técnico en despacho aduanero" en skills_tecnicas_list
- Pero tareas_explicitas = NULL (descripción corta)
- Skills extractor usó solo título → "operar limadoras"
- El matching ignoró completamente skills_tecnicas_list

**Fix propuesto:**
- Agregar skills_tecnicas_list como input al extractor de skills ESCO
- Si tareas_explicitas es NULL, usar skills_tecnicas_list como fallback

---

### 6. CRÍTICO: Matcher NO usa SECTOR

| Evidencia | Resultado |
|-----------|-----------|
| Jefe de Producto (Moda) | → Jefe de cocina (Gastronomía) |
| Operario Plástica (Industria) | → Empleado salón belleza |
| Mecánico vehículos pesados (Logística) | → Mecánico de barcos (Marítimo) |
| Encargado Campo Ganadero (Agropecuario) | → Director salón de belleza |
| Analista QA Farmacéutico (Manufactura) | → Osteópata (Atención médica) |

**El sector_empresa está disponible en NLP pero el matcher no lo considera.**

Skills de gestión genéricas (proveedores, control gastos, planificación) matchean con cualquier rol gerencial sin importar si es Moda, Gastronomía o Industria.

**Fix propuesto:**
1. Usar sector_empresa para filtrar/penalizar ocupaciones incompatibles
2. Crear mapeo sector → familias ISCO compatibles
3. Si sector=Moda y match=Gastronomía → penalizar score
4. **Subdividir sectores amplios** (ej: "Salud" → "Atención médica" vs "Industria farmacéutica" vs "Dispositivos médicos")

**Impacto:** Cambio en lógica del matcher (match_ofertas_v3.py)

---

## IDs Revisados

| ID | Título | Problema | Fix aplicado | ISCO antes | ISCO después |
|----|--------|----------|--------------|------------|--------------|
| 1117941805 | Jefe de Mantenimiento | Ninguno (correcto) | - | 1219 | 1219 |
| 1118105872 | Auditor Médico | R14 lo clasificó como Contador | R14b nueva regla | 241 | 2212 |
| 1118106004 | Modelista/Tizadora | R29 asignó Sastre (7531) en vez de Patronista (7532) + skills basura | Dividir R29 + revisar umbral skills | 7531 | 7532 (pendiente) |
| 1118105856 | Operario Industria Plástica | Skills genéricas (limpieza) matchearon con Salón de belleza | Nueva regla R_XX_operario_plastico | 5142 | 8142 (pendiente) |
| 1118105850 | Jefe de Producto (Moda) | Skills gestión matchearon con Jefe de cocina + area_funcional=RRHH mal | **Usar SECTOR en matching** + revisar NLP area | 3434 | 1324 (pendiente) |
| 1118105765 | Mecánico Mendoza (vehículos pesados) | Skills mecánicas genéricas matchearon con barcos en vez de vehículos | **Usar SECTOR en matching** + regla mecánico | 7233 | 7231 (pendiente) |
| 1118105760 | Mecánico (Turno tarde) | ISCO OK pero ESCO label "supervisor" incorrecto (es mecánico operativo) + NLP concatenó tareas | Revisar selección ESCO dentro de familia ISCO | 7231 (supervisor) | 7231 (mecánico) |
| 1118105759 | Encargado Campo Ganadero | Skills genéricas (gestión, normas) dominaron sobre ganadería → Salón belleza | **Usar SECTOR** + regla ganadero + ponderar skills específicas | 1431 | 6121/1311 (pendiente) |
| 1118105736 | Analista QA Farmacéutico | Sector "Salud" confundió manufactura con atención médica → Osteópata | Distinguir sub-sectores Salud + regla QA farma | 2269 | 2145/3111 (pendiente) |
| 1118105735 | Administrativo de Ecommerce | Con 3000 opciones ESCO eligió "representante comercial" (venta activa) en vez de rol administrativo | Revisar ranking ESCO - debería ser 4311 "asistente dpto ventas" | 3322 | 4311 (pendiente) |
| 1118105715 | Operador SIM (Sistema María Aduanas) | "Operador" interpretado como máquina industrial en vez de sistema informático | Regla para despacho aduanero / Sistema María → 3331 | 8122 | 3331 (pendiente) |
| 1118105713 | Ingeniero electromecánico | Existe ESCO exacto (2151) pero eligió genérico (2144) + NLP sector "Salud" mal (es residuos industriales) | Mejorar ranking ESCO + corregir clasificación sector | 2144 | 2151 (pendiente) |
| 1118105712 | Operarios de almacén | "Operario" (trabajador) clasificado como "Jefe" (gerente) - nivel_seniority=junior ignorado | **Usar nivel_seniority** para filtrar ocupaciones gerenciales | 1324 | 9333/4321 (pendiente) |
| 1118102067 | Analista Back Office FCI (finanzas) | Términos financieros ARG (FCI, Alyc) no reconocidos → "supervisor cajas" + sector "Comercio" mal | Diccionario términos financieros ARG + corregir sector | 5222 | 3311/4312 (pendiente) |
| 1118102051 | Operador Monitoreo Alarmas | Skills genéricas (llamadas) > skills seguridad → "encuestador mercado". Sector correcto pero ignorado | **Usar sector** + ponderar skills específicas | 4227 | 5414/4222 (pendiente) |
| 1118101812 | Subencargado Local (retail ropa) | Existe "gerente tienda ropa" (1420) pero eligió "alquiler deportivo" (5249) + area_funcional=RRHH mal | Mejorar ranking ESCO + corregir area_funcional | 5249 | 1420 (pendiente) |
| 1118101510 | Vendedora ambulante (playa) | Regla R40 demasiado amplia: "vendedora" → "representante comercial". Existe ESCO exacto "vendedor ambulante" | Ajustar R40 + excluir "ambulante" | 3322 | 9520 (pendiente) |
| 1118101077 | Analista Calidad Servicios | Sector "Textil" GRAVE ERROR (es seguridad electrónica) + "Calidad" → "Director Ventas" | Corregir clasificación sector + mejorar matching calidad | 1420 | 2149/1219 (pendiente) |
| 1118101068 | Médico Traumatólogo | Skills genéricas (investigación 0.85) > específicas (musculoesquelético 0.77) → Psicólogo | Ponderar skills médicas específicas + regla médico especialista | 2634 | 2212 (pendiente) |
| 1118097995 | Supervisor Operaciones Gastronomía | "Colaborar con Marketing" → skills marketing dominan → Responsable Marketing | Distinguir "colaborar con X" vs "ser de X" | 1221 | 1412/1411 (pendiente) |
| 1118091304 | Gerente Operaciones Gastronomía | Regla R42 ignora sector: "Gerente Operaciones" → "Director Fabricación" (pero es gastronomía) | R42 debe considerar sector | 1321 | 1412/1411 (pendiente) |
| 1118086791 | Jefe de Sucursal (logística) | Skills carga/descarga (0.78) > skills gerenciales → "jefe estibadores" en vez de gerente | **Usar nivel_seniority=manager** para filtrar roles operativos | 9333 | 1324 (pendiente) |
| 1118040252 | Operario acondicionamiento (pharma) | "Manejo de equipo"=maquinaria → "gestionar equipo"=personas. ABSURDO: operario pharma → zoológico | Desambiguar "equipo" + vocabulario pharma ARG | 5164 | 8160/9329 (pendiente) |
| 2172236 | Secretaria de Posgrados | Rol ADMINISTRATIVO clasificado como "Profesor de arte". Confunde trabajar EN educación con SER docente | **Filtrar por area_funcional** (Administración ≠ Docencia) | 2330 | 3343/4110 (pendiente) |
| 2172229 | Analista de Créditos (concesionaria) | Rol FINANCIERO clasificado como "Vendedor de vehículos". Confunde trabajar en concesionaria con vender autos | area_funcional=Finanzas (no Ventas) | 5223 | 3312 (pendiente) |
| 2172222 | Coordinador Comercial B2C | Ninguno (correcto) | - | 1221 | 1221 |
| 2172220 | Auditor/a Cooperativas Jr | Ninguno (correcto) - R17 aplicó bien | - | 241 | 241 |
| 2172219 | Administrativo Almacenes (frigorífico) | ISCO OK pero ESCO "fábrica textil" cuando sector=Alimentación (frigorífico) | **Usar SECTOR** para filtrar ESCO label | 4321 (ok) | ESCO label (pendiente) |
| 2172215 | Encargado Campo Ganadero | IGUAL que 1118105759 - Skills genéricas > ganadería → Salón belleza | **Usar SECTOR** (ya documentado) | 1431 | 6121/1311 (pendiente) |
| 2172212 | Administrativa/o Cementerio | Sector "Salud" MAL (es funeraria). Rol admin → "supervisor lavandería" ABSURDO | Corregir sector + regla para servicios funerarios | 8157 | 4110/4226 (pendiente) |
| 2172211 | Jefe de Delegación (finanzas) | Jefe sucursal financiera → "Ingeniero ventas". nivel_seniority=semisenior MAL (es Jefe) | Corregir seniority + distinguir finanzas vs técnico | 2433 | 1221/1324 (pendiente) |
| 2172208 | Carpintero Aluminio / Cortador Vidriero | Parcialmente correcto - "Cristalero" captura parte del rol | - | 7125 | 7125 |
| 2172203 | Supervisor Ventas (Servicios Salud) | Skills "mejora procesos" > "gestionar ventas" → "Gestor transformación digital" en vez de ventas | Ponderar skills específicas del área | 1330 | 1221 (pendiente) |
| 2172199 | Ingeniero Industrial Equipamiento Médico | Correcto - técnico industrial para rol de gestión equipos | - | 3119 | 3119 |
| 2172198 | Abogado/a Jr Accidentes Trabajo | ISCO correcto (R17). ERROR NLP: "LEX DOCTOR" (software) → skills médicas | Corregir NLP para software jurídico | 2611 (ok) | NLP fix (pendiente) |
| 2172196 | Asistente Dental | Ninguno (correcto) | - | 3251 | 3251 |
| 2172192 | JAVA Architect | Rol técnico senior (arquitecto software) → "Gestor análisis TIC" (negocio). Título no limpio | Limpiar título + regla arquitecto software | 2511 | 2512 (pendiente) |
| 2172191 | DevOps Engineer | Ingeniero infraestructura → "Operador centro datos" (subestima nivel). Título no limpio | Limpiar título + regla DevOps | 3511 | 2512/2523 (pendiente) |
| 2172188 | Analista Técnico Funcional Medios Pagos | Analista IT bancario → "Animador actividades aire libre" ABSURDO. Título no limpio. | Limpiar título + sector Finanzas | 3423 | 2511 (pendiente) |
| 2172184 | Operador de Back office (pagos) | Rol admin → "Entrenador de vida/coach". Skills "trabajo equipo" confundieron | Regla back office → rol administrativo | 3412 | 4132/4311 (pendiente) |
| 2172183 | DevOps Engineer | Skills "fabricación" (de pipelines) → "Ingeniero materiales" (manufactura). Título no limpio | Limpiar título + regla DevOps | 2149 | 2512/2523 (pendiente) |
| 2172181 | Mecánico de Automotores Posventa | Ninguno (correcto) | - | 7231 | 7231 |
| 2172174 | Coordinador/a de Obras | Match genérico "Director operaciones" para rol de construcción. Seniority=trainee MAL | Corregir seniority + match sector | 1321 | 3123/1323 (pendiente) |
| 2172173 | Ingeniero de IA | Match parcial - "Ingeniero cloud" captura parte del rol. Título no limpio | Limpiar título | 2512 (ok) | - |
| 2172171 | Carpintero Oficial Colocador | "Colocador" → "Instalador aislante". Skills correctas (muebles) pero match incorrecto | Priorizar skills sobre palabras sueltas | 7124 | 7522 (pendiente) |
| 2172164 | Encargado Senior Gastronomía | "Encargado Senior" → "Coordinador comida rápida" (nivel bajo). Seniority=semisenior MAL | Corregir seniority + nivel jerárquico | 5246 | 1412 (pendiente) |
| 2172159 | Data Engineer Sr | Ninguno (correcto) - match exacto | - | 2511 | 2511 |
| 2172158 | Pintor Sopletista (piezas plásticas) | ISCO correcto pero ESCO "vehículos" muy específico | - | 7132 | 7132 (ok parcial) |
| 2172157 | Marketing Performance Insights Analyst | "Analyst" (analista) → "Responsable" (gerente). Nivel jerárquico inflado | Distinguir analyst vs manager | 1221 | 2431 (pendiente) |
| 2172152 | Analista funcional SAP Jr | Analista SAP → "Técnico mantenimiento BATERÍAS" ABSURDO. Título no limpio | Limpiar título + regla analista SAP | 3113 | 2511 (pendiente) |
| 2172151 | Analista Técnico Funcional Integraciones | "Integraciones" (sistemas) confundido con arquitectura edificios → "Arquitecto" | Desambiguar integraciones IT vs arquitectura | 2161 | 2511 (pendiente) |
| 2172150 | Analista de Integraciones Digitales | Analista IT fintech → "Vendedor pisos y paredes" ABSURDO. Título con "+45 años" | Limpiar título + regla integraciones IT | 5223 | 2511 (pendiente) |
| 2172144 | Diseñador/a Gráfico/a Senior | Diseñador → "Editor fotografía" (solo parte del rol). Area=IT MAL | Corregir area_funcional + match completo | 2642 | 2166 (pendiente) |

---

## IDs Pendientes de Revisar

Total: 44 restantes

---

## Resumen Estadístico (56/100 revisados)

| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| CORRECTOS | 7 | 12.5% |
| CORRECTOS PARCIALES | 6 | 10.7% |
| **ERRORES** | **43** | **76.8%** |

**Precisión actual:**
- Estricta: ~12%
- Flexible (incluyendo parciales): ~23%

### Causas Principales de Error (agrupadas)

| Causa | Frecuencia | Ejemplos |
|-------|------------|----------|
| **Títulos no limpios** | ~15 casos | DevOps Engineer - Remoto - 1729, Analista SAP - Rosario - 1779 |
| **SECTOR ignorado** | ~12 casos | Gastronomía→Fabricación, Moda→Cocina, Finanzas→Retail |
| **Skills genéricas dominan** | ~10 casos | "trabajo equipo"→coach, "gestión"→cualquier gerente |
| **Palabras polisémicas** | ~8 casos | "operador" (SIM/máquina), "integraciones" (IT/arquitectura) |
| **Seniority ignorado** | ~6 casos | trainee→jefe, junior→gerente |
| **Área funcional incorrecta** | ~5 casos | Finanzas→Ventas, Marketing→IT |
| **Roles IT no reconocidos** | ~5 casos | DevOps, SAP, Data Engineer, IA |
| **Matches absurdos** | ~5 casos | Analista IT→Baterías, Admin cementerio→Lavandería |

### Prioridades de Fix

1. **CRÍTICO:** Limpiar títulos (regex para códigos, ubicaciones, modalidades)
2. **CRÍTICO:** Usar sector_empresa en matching
3. **ALTO:** Agregar reglas de negocio para roles IT
4. **ALTO:** Ponderar skills específicas sobre genéricas
5. **MEDIO:** Corregir clasificación area_funcional en NLP
6. **MEDIO:** Usar nivel_seniority para filtrar ocupaciones

---

## Versiones Objetivo (post-revisión)

| Componente | Actual | Nueva |
|------------|--------|-------|
| NLP Pipeline | v11.3.0 | v11.4.0 |
| Prompt | v1.1 | v1.2 |
| Matching | v3.2.0 | v3.3.0 |

---

## Plan de Aplicación

1. [ ] Terminar revisión de 100 IDs
2. [ ] Consolidar todos los cambios
3. [ ] Bumpar versiones
4. [ ] Re-procesar NLP (100 ofertas, ~40 min)
5. [ ] Re-procesar Matching (100 ofertas, ~10 min)
6. [ ] Exportar Excel comparativo (antes vs después)
7. [ ] Medir mejoras en Gold Set

---

## DIAGNÓSTICO ARQUITECTÓNICO: Pipeline Desconectado

### Problema Principal

El pipeline NLP extrae información valiosa que el pipeline de Matching **ignora completamente**.

### Flujo ACTUAL (con pérdida de información)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PIPELINE NLP v11.3                           │
│                                                                     │
│  Descripción ──► LLM Qwen2.5 ──► ofertas_nlp                       │
│                                    │                                │
│                                    ├── titulo_limpio        ✓ USADO │
│                                    ├── tareas_explicitas    ✓ USADO │
│                                    ├── skills_tecnicas_list ✗ IGNORADO
│                                    ├── soft_skills_list     ✗ IGNORADO
│                                    ├── sector_empresa       ✗ IGNORADO
│                                    ├── area_funcional       ✗ IGNORADO
│                                    └── nivel_seniority      ✗ IGNORADO
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE MATCHING v3.2                           │
│                                                                     │
│  INPUT ACTUAL:                                                      │
│  ┌─────────────────────────────────────────┐                       │
│  │ titulo_limpio + tareas_explicitas       │                       │
│  └─────────────────────────────────────────┘                       │
│                      │                                              │
│                      ▼                                              │
│              Skills Extractor (BGE-M3)                              │
│                      │                                              │
│                      ▼                                              │
│              Match vs 3000 ESCO ocupaciones                         │
│                      │                                              │
│                      ▼                                              │
│              Reglas de Negocio (bypass)                             │
│                      │                                              │
│                      ▼                                              │
│              ISCO final                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Caso Ejemplo: ID 1118105715 "Operador SIM"

```
PASO 1 - NLP extrae correctamente:
┌────────────────────────────────────────────┐
│ titulo_limpio: "Operador SIM"              │
│ tareas_explicitas: NULL (desc muy corta)   │
│ skills_tecnicas_list: "técnico despacho    │
│                        aduanero" ✓ CORRECTO│
│ sector_empresa: "Logistica" ✓ CORRECTO     │
└────────────────────────────────────────────┘

PASO 2 - Matching IGNORA contexto:
┌────────────────────────────────────────────┐
│ Input usado: solo "Operador SIM"           │
│ Input ignorado: "despacho aduanero",       │
│                 "Logistica"                │
│                                            │
│ Embedding "Operador SIM" ──► similitud     │
│   con "operar limadoras" (0.60)            │
│                                            │
│ Resultado: ISCO 8122 (máquina industrial)  │
│ Correcto:  ISCO 3331 (agente aduanas)      │
└────────────────────────────────────────────┘
```

### Archivos Involucrados

| Archivo | Rol | Problema |
|---------|-----|----------|
| `database/process_nlp_from_db_v11.py` | Extrae 20 campos NLP | Funciona bien |
| `database/skills_implicit_extractor.py` | Extrae skills ESCO de texto | Solo usa titulo + tareas |
| `database/match_ofertas_v3.py` | Matching final ESCO | No usa sector/area/skills_NLP |
| `database/match_by_skills.py` | Matching por skills | No recibe contexto NLP |

### Código Específico a Modificar

**1. skills_implicit_extractor.py** (~línea 45-60)

```python
# ACTUAL:
def extract_skills(titulo: str, tareas: str) -> list:
    text = f"{titulo}. {tareas or ''}"
    # ... embedding y matching

# PROPUESTO:
def extract_skills(titulo: str, tareas: str,
                   skills_nlp: list = None,
                   sector: str = None) -> list:
    text = f"{titulo}. {tareas or ''}"
    if skills_nlp:
        text += ". " + ". ".join(skills_nlp)
    # ... embedding y matching
    # ... filtrar por coherencia con sector
```

**2. match_ofertas_v3.py** (~línea 120-150)

```python
# ACTUAL:
def match_oferta(id_oferta, titulo, tareas):
    skills = extract_skills(titulo, tareas)
    # ... matching

# PROPUESTO:
def match_oferta(id_oferta, titulo, tareas,
                 skills_nlp=None, sector=None, area=None):
    skills = extract_skills(titulo, tareas, skills_nlp, sector)
    # ... matching con penalización por sector incompatible
```

### Flujo PROPUESTO (usando toda la información)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE MATCHING v3.3 (PROPUESTO)               │
│                                                                     │
│  INPUT COMPLETO:                                                    │
│  ┌─────────────────────────────────────────┐                       │
│  │ titulo_limpio                           │                       │
│  │ + tareas_explicitas                     │                       │
│  │ + skills_tecnicas_list    ◄── NUEVO     │                       │
│  │ + soft_skills_list        ◄── NUEVO     │                       │
│  │ + sector_empresa          ◄── NUEVO     │                       │
│  │ + area_funcional          ◄── NUEVO     │                       │
│  └─────────────────────────────────────────┘                       │
│                      │                                              │
│                      ▼                                              │
│              Skills Extractor (BGE-M3)                              │
│              + Filtro por sector/área                               │
│                      │                                              │
│                      ▼                                              │
│              Match vs 3000 ESCO ocupaciones                         │
│              + Penalización sector incompatible                     │
│                      │                                              │
│                      ▼                                              │
│              Reglas de Negocio (bypass)                             │
│                      │                                              │
│                      ▼                                              │
│              ISCO final (más preciso)                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Impacto Esperado

| Métrica | Actual | Esperado |
|---------|--------|----------|
| Errores por sector incompatible | ~40% de errores | ~5% |
| Errores por palabra polisémica | ~20% de errores | ~10% |
| Errores por falta de contexto | ~30% de errores | ~5% |
| Precisión Gold Set | ~70% estimado | ~90%+ |

### Prioridad de Implementación

1. **ALTA**: Usar sector_empresa como filtro/penalización
2. **ALTA**: Usar skills_tecnicas_list como input adicional
3. **MEDIA**: Usar area_funcional para filtrar familias ISCO
4. **BAJA**: Usar nivel_seniority para ajustar ocupación dentro de familia
