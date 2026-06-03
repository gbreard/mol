# SPEC W — Sistema de Validación Estructurada para Cyn

**Estado:** Diseño completo. Pendiente ejecución de Fase 0.
**Fecha:** Mayo 2026
**Autor:** Gerardo (con destilado de cuestionario a Cyn)
**Versión:** 1.0

---

## 1. Resumen ejecutivo

SPEC W define el sistema de captura, análisis y feedback de las auditorías de Cyn al pipeline MOL. Su objetivo a mediano plazo es que el sistema aprenda de las correcciones de validadores humanos y reduzca progresivamente su carga de trabajo manual.

El SPEC se ejecuta en **4 fases secuenciales** con dependencias estrictas: ninguna fase comienza sin que la anterior haya cerrado satisfactoriamente.

| Fase | Nombre | Objetivo | Duración estimada |
|------|--------|----------|-------------------|
| 0 | Factibilidad | Verificar tipos de datos, endpoints, dependencias antes de implementar nada | 4-8h |
| 1 | Visualizador estructurado | Capturar auditorías de Cyn como datos estructurados explotables | 2-3 semanas |
| 2 | Detección de patrones (reactiva) | Identificar correcciones generalizables a partir de marcas humanas | 2-3 semanas |
| 3 | Loop de feedback | Mostrar a Cyn el impacto de sus correcciones | 2-3 semanas |

**Total estimado:** 6-10 semanas calendario.

**Importante sobre el alcance:** SPEC W es **reactivo** — el sistema aprende a partir de lo que Cyn marca. La investigación **proactiva** (detección automática de anomalías estadísticas sin esperar marca humana, ej: "ISCO 9329 tiene 99% divergencia regla vs semántico") queda fuera de SPEC W y se trata en un SPEC separado (ver `SPECs_PARALELOS.md`).

---

## 2. Origen y justificación

### 2.1 Diagnóstico previo

Durante el período enero-mayo 2026, Cyn produjo aproximadamente 218 validaciones humanas en el sistema MOL. Estas validaciones tienen valor analítico significativo pero presentan problemas estructurales:

- **162 de 218 quedaron huérfanas** cuando el matcher fue actualizado en SPEC U-1 (las URIs ESCO cambiaron y sus correcciones quedaron sin referencia)
- **El sistema no aprende automáticamente** de las correcciones; cada error se corrige caso por caso sin propagación
- **Los criterios de validación** no estaban formalmente documentados ni compartidos
- **El loop de feedback** entre Cyn y el sistema era inexistente: ella corregía sin saber qué pasaba después

### 2.2 Input de Cyn (cuestionario mayo 2026)

Cyn respondió un cuestionario de 39 preguntas en 6 bloques que sirvió de input para este SPEC. Hallazgos críticos:

1. **Nunca usó Alt+6 para marcar Gold Set** (las 49 ofertas iniciales no vinieron de ella; aporta 36 casos de los 112 actuales pero vía ingesta de Excel histórico, no marcado en vivo)
2. **Pidió funcionalidad nueva específica:** marcar tareas/skills individuales como incorrectas o sugeridas
3. **Pidió estado "Revisada" explícito** al terminar una oferta
4. **Pidió poder marcar oferta como "mal extraída en su totalidad"** (no solo errores parciales)
5. **Confirmó patrones generalizables existentes:** ISCO 0110 Fuerzas Armadas, títulos genéricos (Técnico/Analista/Administrativo)
6. **Quiere ver impacto de sus correcciones** a futuro y casos similares ya validados

### 2.3 Lo que SPEC W no es

- **No es un re-diseño del matcher.** El matcher se mejora por separado (fine-tuning M-17, reglas nuevas, etc.).
- **No es Gold Set.** Gold Set es el conjunto de referencia para evaluar el matcher; SPEC W es la infraestructura para capturar y propagar las auditorías de Cyn que alimentan el Gold Set y otras correcciones.
- **No es validación masiva.** Cyn valida ~30 ofertas/día. SPEC W respeta esa capacidad y maximiza el valor de cada validación.

---

## 3. Decisiones clave de diseño

### 3.1 Aprovechar datos existentes en Supabase

Las correcciones previas de Cyn ya están en `ofertas_dashboard` con campos como:
- `validacion_humana` (categoría asignada)
- `validacion_humana_at` (timestamp)
- `validacion_humana_por` (autor)
- `observaciones` (texto libre)
- Otros campos de corrección estructurada

**SPEC W lee de aquí**, no espera a que Cyn empiece a marcar cosas desde cero.

### 3.2 Estructura por bloque de revisión

Cyn ya organiza sus auditorías por bloques (atributos NLP / tareas / skills / ocupación). SPEC W respeta esta estructura en lugar de imponer una nueva.

### 3.3 Notas libres + categorías cerradas (híbrido)

Cyn confirmó que prefiere notas libres en "observaciones" sobre formularios estructurados. El SPEC mantiene esto y agrega solo categorías cerradas mínimas donde aportan valor (estado Revisada, marcar tarea como incorrecta).

### 3.4 Fase 0 obligatoria antes de implementar

Por experiencia operativa (sesiones anteriores con estimaciones desfasadas y descubrimientos tardíos), ninguna fase de implementación comienza sin Fase 0 cerrada. Detalles en `SPEC_W_fase0_factibilidad.md`.

### 3.5 Aprendizaje incremental, no automático

El sistema NO aplicará automáticamente las correcciones de Cyn como reglas. Cada candidato a regla pasa por revisión humana antes de incorporarse al matcher. Esto preserva el control de calidad y previene propagación de errores.

---

## 4. Dependencias entre fases

```
Fase 0 (Factibilidad)
    │
    ▼
Etapa 1 (Visualizador estructurado)
    │  ← requiere Fase 0 OK
    │
    ▼
Etapa 2 (Detección de patrones)
    │  ← requiere Etapa 1 OK + 4-6 semanas de datos
    │
    ▼
Etapa 3 (Loop de feedback)
    ← requiere Etapa 1 OK + Etapa 2 parcial
```

### 4.1 Dependencias externas (no controladas por SPEC W)

- **Bugs operativos resueltos:** "oferta cambia entre secciones", buscador por ID, feedback visual al guardar. Sin estos, Etapa 1 no es operable.
- **Capacitación Alt+6 a Cyn:** 15 min + documento. Sin esto, Cyn no marca Gold Set sistemáticamente.
- **R3 del diagnóstico de escalados** (bug V27 con ISCOs iguales): bug puro de 454 casos.

Estos puntos están en el **Grupo 1 de prioridades** del destilado del cuestionario y son prerequisitos operativos (no técnicos) de Etapa 1.

---

## 5. Criterios de éxito globales

SPEC W se considera exitoso cuando:

| # | Criterio | Cómo se mide |
|---|----------|--------------|
| 1 | Cyn registra ≥5 ofertas como Gold Set por semana usando el flujo nuevo | Métrica en `/admin/aprendizaje` |
| 2 | El sistema detecta ≥1 patrón nuevo de error por mes | Reporte de candidatos a regla |
| 3 | El loop de feedback muestra impacto medible de correcciones | KPI en validador |
| 4 | Cyn reduce tiempo promedio por oferta de 20 min a 10 min | Encuesta + métricas internas |
| 5 | Gold Set alcanza 150+ casos | Conteo en `gold_set` |
| 6 | Tasa de errores escalados baja de ~40% a ~10% | Métrica de pipeline |

---

## 6. Riesgos identificados

### 6.1 Riesgo: Cyn no adopta el nuevo flujo

**Mitigación:** Capacitación previa, criterios documentados, no cambiar lo que ella confirmó que funciona (estructura por bloques, notas libres en observaciones).

### 6.2 Riesgo: Detección de patrones genera falsos positivos

**Mitigación:** Cada candidato a regla pasa por revisión humana (Gerardo) antes de aplicarse al matcher. Threshold de confianza alto antes de proponer.

### 6.3 Riesgo: Sobre-ingeniería con baja adopción

**Mitigación:** Etapas se cierran solo cuando demuestran valor medible. Etapa 2 y 3 son opcionales hasta que Etapa 1 muestre adopción.

### 6.4 Riesgo: Cambios al schema rompen datos históricos

**Mitigación:** Migrations con backfill, no modificación destructiva. Tests de regresión sobre validaciones previas.

---

## 7. Archivos del SPEC

| Archivo | Contenido |
|---------|-----------|
| `SPEC_W_overview.md` | Este documento |
| `SPEC_W_fase0_factibilidad.md` | Verificaciones técnicas previas (ejecutable) |
| `SPEC_W_etapa1_visualizador.md` | Visualizador estructurado |
| `SPEC_W_etapa2_patrones.md` | Detección de patrones |
| `SPEC_W_etapa3_feedback.md` | Loop de feedback |

---

## 8. Glosario

- **Validador:** UI en `/admin/validacion` donde Cyn audita ofertas
- **Gold Set:** Conjunto de ofertas de referencia para evaluar mejoras del matcher (112 casos actuales)
- **Matcher:** Sistema que asigna ESCO a una oferta (versión actual 3.5.2)
- **Auditoría:** Revisión completa de una oferta por Cyn (NLP + tareas + skills + ocupación)
- **Patrón generalizable:** Tipo de error que aparece repetidamente con misma causa (ej: ISCO 0110)
- **Candidato a regla:** Patrón detectado por Etapa 2 que se propone como regla nueva (pendiente revisión humana)
- **SPEC W:** Este sistema. "W" por nombre interno asignado en sesión del 11/05.

---

## 9. Próximos pasos

1. **Antes de implementar nada:** Ejecutar Fase 0 (`SPEC_W_fase0_factibilidad.md`) y obtener veredicto "OK para avanzar"
2. **Si Fase 0 detecta bloqueos:** Resolver bloqueos o ajustar SPEC W antes de continuar
3. **Si Fase 0 OK:** Implementar Etapa 1 con sus criterios de aceptación
4. **Etapa 2 y 3 quedan en backlog** hasta que Etapa 1 muestre valor medible

---

## 10. Decisiones tomadas durante el diseño

| Fecha | Decisión | Razón |
|-------|----------|-------|
| 2026-05-?? | Fase 0 ejecutable por Claude Code como primer paso | Patrón spec-driven puro, máxima trazabilidad |
| 2026-05-?? | Archivos separados por fase | Facilita lectura selectiva y mantenimiento |
| 2026-05-?? | Leer correcciones previas de Supabase | No esperar a Cyn marcando desde cero |
| 2026-05-?? | Estructura por bloque de revisión | Cyn confirmó que le funciona |
| 2026-05-?? | Notas libres + categorías cerradas | Híbrido pedido por Cyn |
| 2026-05-?? | Aprendizaje con revisión humana | Prevenir propagación de errores |
