# SPECs Paralelos a SPEC W

**Propósito:** Mapear los puntos identificados en análisis externo de 22 items que NO caen dentro de SPEC W (validación estructurada de Cyn) pero que merecen tratamiento estructurado en SPECs propios.

**Estado:** Inventario. Ninguno arrancado todavía.

**Fecha:** Mayo 2026

---

## Resumen

De los 22 puntos del análisis externo:

- **2 cubiertos por SPEC W:** Gold Set (#6) y Flujo de validación humana (#21)
- **5 parcialmente cubiertos por SPEC W:** #3, #4, #9, #14, #22
- **15 fuera del scope de SPEC W:** requieren SPECs separados u operaciones puntuales

Este documento agrupa los 15 puntos en 5 SPECs paralelos + 2 grupos operativos no-SPEC.

---

## SPEC X — Investigación Proactiva de Anomalías

**Estado:** Pendiente diseño completo.
**Prioridad:** Alta (complementa SPEC W).
**Duración estimada:** 2-3 semanas.

### Cubre los puntos:

- **#3 ISCO 9329 con 99% divergencia regla vs semántico**
- **#4 47 ofertas remoto+operativo (combinación anómala)**
- **#9 Regla cross-field remoto+operativo**

### Objetivo

Mientras SPEC W detecta patrones a partir de marcas humanas (reactivo), SPEC X corre análisis estadísticos sobre todo el dataset para identificar anomalías que ningún humano marcó todavía.

### Funcionalidad propuesta

- **Detector 1:** ISCOs con alta divergencia entre regla y semántico (>90%)
- **Detector 2:** Combinaciones de atributos atípicas (cross-field anomalies)
- **Detector 3:** Outliers de score dentro de un mismo ISCO
- **Detector 4:** Drift temporal (un ISCO que cambia de comportamiento entre runs)

### Arquitectura

Similar a Etapa 2 de SPEC W pero con detectores estadísticos en lugar de detectores basados en marcas:

```
ofertas_dashboard (datos crudos)
    │
    ▼
[Detectores estadísticos]
    │
    ▼
anomaly_candidates (propuestas)
    │
    ▼
[Revisión humana — Gerardo + Cyn]
    │
    ▼
candidate_rules (alimenta SPEC W Etapa 2)
```

### Tabla nueva: `anomaly_candidates`

Similar a `candidate_rules` pero con tipos específicos de anomalía estadística.

### Relación con SPEC W

SPEC X **alimenta** SPEC W. Las anomalías detectadas se proponen a Cyn para validación, y si las marca como reales, se convierten en `audit_actions` que SPEC W Etapa 2 procesa normalmente.

### Riesgos

- Falsos positivos altos (detección estadística sin contexto)
- Sobrecarga de Cyn si genera demasiados candidatos
- Sesgo: detecta anomalías estadísticas, no necesariamente errores

### Cuándo arrancar

Después de SPEC W Etapa 1 OK. Idealmente en paralelo a SPEC W Etapa 2 reactiva.

---

## SPEC Y — Mejora del AutoCorrector

**Estado:** Diagnóstico iniciado en `docs/issues/2026-05-19_diagnostico_escalados_regimen.md`.
**Prioridad:** Media-alta.
**Duración estimada:** 2-4 semanas.

### Cubre los puntos:

- **#1 Caída CLAE 14-28 pp**
- **#2 ARCOS DORADOS x 14 ofertas**
- **#5 Recálculo del baseline del AutoCorrector**
- **#7 Redefinición métrica AutoCorrector ("% corregidos sobre no-escalados")**

### Objetivo

El AutoCorrector hoy reporta ~40% de escalados, pero el diagnóstico reveló que 87.8% es ruido (errores upstream del scraping/NLP que llegan al corrector sin que pueda hacer nada). Este SPEC redefine las métricas, reclasifica severidades (R1-R5 del diagnóstico) y construye reglas nuevas para los 12.766 errores reales.

### Bloques

#### Bloque 1 — Limpieza de ruido (R1-R4 del diagnóstico)

- R1: Reclasificar categoría A (errores upstream) a severidad info, no escalar
- R2: V28 sobre-disparando → bajar severidad de warning a info
- R3: Fix bug V27 con ISCOs iguales
- R4: Categoría D (warnings informativos) → no escalar

Esfuerzo: ~1.5h.

#### Bloque 2 — Redefinición de métrica

Definir formalmente:
- **Tasa de auto-corrección:** % de errores reales auto-corregidos
- **Tasa de escalación real:** % de errores reales escalados (excluir ruido)
- **Baseline:** valor objetivo a alcanzar

Esfuerzo: ~1 día.

#### Bloque 3 — Investigación casos específicos

- #1 Caída CLAE 14-28 pp: investigar si es bug del clasificador CLAE o problema de datos
- #2 ARCOS DORADOS x 14 ofertas: caso puntual, ¿es bug o data?

Esfuerzo: ~1 semana.

#### Bloque 4 — R5: reglas nuevas para los 12K reales

Crear más reglas tipo `fix_v31_*` para los 12.766 errores reales del corrector. Cada regla nueva debe tener tests y respetar el patrón existente.

Esfuerzo: ~2-3 semanas según volumen.

### Bloqueos

R1-R4 PAUSADO esperando feedback de Cyn sobre criterios de severidad (de SPEC W).

### Cuándo arrancar

Después de SPEC W Etapa 1 OK (para tener criterios de Cyn sobre qué es ruido vs error real).

---

## SPEC Z — Enriquecimiento del Catálogo `esco_argentino`

**Estado:** Pendiente diseño.
**Prioridad:** Media.
**Duración estimada:** 1-2 semanas.

### Cubre los puntos:

- **#8 Crecimiento perfil argentino con TIC**
- **#19 Redefinir métrica perfil argentino**
- **#20 Tratamiento de mediación por consultoras**

### Objetivo

El catálogo `esco_argentino` (44 ocupaciones, 291 skills curadas) está sesgado a sectores tradicionales. Faltan ocupaciones del sector TIC y reglas claras para tratar ofertas de consultoras (que mediatizan la relación entre empresa real y postulante).

### Bloques

#### Bloque 1 — Expansión TIC

Identificar ocupaciones TIC argentinas faltantes y agregarlas al catálogo con skills curadas. Usar como referencia ofertas reales del sector.

#### Bloque 2 — Métrica del perfil argentino

Redefinir cómo se mide la calidad del catálogo:
- Cobertura: % de ofertas argentinas que matchean al catálogo
- Precisión: % de matches al catálogo confirmados por humano
- Drift: cómo cambia el catálogo entre versiones

#### Bloque 3 — Tratamiento de mediación por consultoras

Decisión de negocio + implementación: cuando una oferta es publicada por consultora ("Adecco busca para cliente del sector retail..."), ¿el sector clasificado es el de la consultora o el del cliente final?

### Cuándo arrancar

Independiente de SPEC W. Puede arrancar en paralelo si hay capacidad.

---

## SPEC Reportes — Sistema de Reportes Recurrentes

**Estado:** Pendiente diseño.
**Prioridad:** Baja-media.
**Duración estimada:** 1 semana.

### Cubre los puntos:

- **#10 Sistema de reportes semanales recurrente**

### Objetivo

Hoy no hay reporte automático a stakeholders (Diego, Gerardo, otros). El estado del sistema se conoce solo entrando al dashboard. Este SPEC define un sistema de reportes recurrentes con métricas clave.

### Funcionalidad propuesta

- Reporte semanal por mail con KPIs:
  - Ofertas procesadas
  - Tasa de errores
  - Patrones detectados (de SPEC W Etapa 2)
  - Estado del catálogo
  - Validaciones de Cyn
- Reporte mensual con tendencias
- Alertas si hay anomalías (de SPEC X)

### Cuándo arrancar

Después de SPEC W Etapa 1 OK (para tener métricas estables que reportar).

---

## SPEC Issues — Separación de Issues Automáticos vs Humanos

**Estado:** Parcialmente cubierto por SPEC W (campo `source` en `audit_actions`).
**Prioridad:** Media.
**Duración estimada:** 1 semana.

### Cubre los puntos:

- **#22 Separar issues auto vs humanos**

### Objetivo

Hoy el sistema de issues mezcla:
- Issues generados automáticamente por el AutoCorrector
- Issues generados por validadores humanos (Cyn)
- Issues generados por reglas del matcher

Sin distinguirlos, no se pueden analizar separadamente (calidad humana vs cobertura del corrector).

### Relación con SPEC W

SPEC W Etapa 1 incorpora el campo `source` en `audit_actions` (F10), que cubre parcialmente el punto. Pero el sistema de issues legado tiene su propia tabla y flujos que también requieren la separación.

### Cuándo arrancar

Después de SPEC W Etapa 1 OK. Es deuda menor pero útil para reportes y análisis.

---

## Operativos NO-SPEC (10 puntos)

Estos puntos no requieren SPEC formal, son tareas operativas o de mantenimiento.

### Pipeline operativo

| # | Punto | Esfuerzo | Cuándo |
|---|-------|----------|--------|
| #11 | Ejecutar `refresh_priorities` manualmente | 5 min | Cuando se necesite |
| #12 | Hook automático `refresh_priorities` | 2-3h | Próximo sprint |
| #14 | Hook `log_learning_event` | Cubierto por `audit_actions` en SPEC W | SPEC W Etapa 1 |

### Limpieza de código / schema

| # | Punto | Esfuerzo | Cuándo |
|---|-------|----------|--------|
| #15 | Migration 024 archivar `ofertas_skills_norm` | 1-2h | Cuando se decida hacerlo |
| #16 | Limpiar comentarios `# v11.4:` y `# v3.5.4:` | 30 min | Próxima sesión cleanup |
| #18 | Drop o doc `isco_nivel1` | 30 min | Próxima sesión cleanup |

### Documentación

| # | Punto | Esfuerzo | Cuándo |
|---|-------|----------|--------|
| #13 | Alinear doc columnas score | 30 min | Sesión cleanup |

### Comunicación

| # | Punto | Esfuerzo | Cuándo |
|---|-------|----------|--------|
| #17 | Comunicar pre-commit hook a Sergio | Conversación con Sergio | Esta semana |

---

## Mapa visual de SPECs

```
                        SPEC W (Validación humana)
                        ├── Fase 0
                        ├── Etapa 1 (Visualizador)
                        ├── Etapa 2 (Patrones reactivos)
                        └── Etapa 3 (Loop feedback)
                                  ▲
                                  │ alimenta
                                  │
                        SPEC X (Investigación proactiva)
                        ├── Detector divergencia ISCO
                        ├── Detector cross-field
                        ├── Detector outliers score
                        └── Detector drift temporal

                        SPEC Y (AutoCorrector)
                        ├── Limpieza ruido R1-R4
                        ├── Redefinición métricas
                        ├── Investigación casos
                        └── Reglas nuevas R5

                        SPEC Z (esco_argentino)
                        ├── Expansión TIC
                        ├── Métrica catálogo
                        └── Tratamiento consultoras

                        SPEC Reportes
                        └── Reportes recurrentes a stakeholders

                        SPEC Issues
                        └── Separación auto vs humanos (extensión)
```

---

## Priorización recomendada

### Inmediato (esta semana)

- Operativos: #11, #17 (puntuales rápidos)
- Resolver bugs prerequisito de SPEC W (Grupo 1 del destilado de Cyn)

### Corto plazo (próximas 4 semanas)

1. SPEC W Fase 0 (verificación de factibilidad)
2. SPEC W Etapa 1 (visualizador con #22 incorporado)
3. SPEC Y Bloque 1 (limpieza R1-R4) — paralelo a SPEC W Etapa 1

### Mediano plazo (próximas 8 semanas)

1. SPEC W Etapa 2 (reactiva)
2. SPEC X (investigación proactiva) — paralelo
3. SPEC Y Bloque 2-3 (redefinir métricas + investigaciones)

### Largo plazo (3+ meses)

1. SPEC W Etapa 3 (loop feedback)
2. SPEC Y Bloque 4 (reglas nuevas)
3. SPEC Z (catálogo argentino)
4. SPEC Reportes

---

## Decisiones pendientes

| # | Decisión | Quién decide |
|---|----------|--------------|
| 1 | ¿Empezar SPEC Y Bloque 1 en paralelo a SPEC W Etapa 1, o secuencial? | Gerardo |
| 2 | ¿SPEC X arranca antes o después de SPEC W Etapa 2? | Gerardo |
| 3 | ¿SPEC Z tiene prioridad sobre SPEC Reportes? | Gerardo + stakeholders |
| 4 | ¿#22 queda cubierto por SPEC W Etapa 1 (F10) o requiere SPEC Issues completo? | Gerardo después de Fase 0 |

---

## Notas

- **SPECs Y, Z, Reportes y Issues no están diseñados completamente todavía.** Este documento es inventario, no plan detallado.
- **Cuando se decida arrancar uno**, requerirá su propia Fase 0 + diseño completo similar a SPEC W.
- **SPEC X (investigación proactiva)** es el más urgente de los paralelos porque complementa directamente a SPEC W Etapa 2.
