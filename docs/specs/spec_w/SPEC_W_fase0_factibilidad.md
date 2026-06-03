# SPEC W — Fase 0: Factibilidad

**Tipo:** Fase ejecutable por Claude Code antes de cualquier implementación.
**Duración estimada:** 4-8 horas activas.
**Salida:** Reporte de factibilidad con veredicto OK / BLOQUEADO / AJUSTAR.

---

## 1. Propósito

Verificar que todas las precondiciones técnicas para SPEC W están dadas. Identificar gaps que requieren resolución antes de implementar. **Sin esta fase cerrada con veredicto OK, ninguna etapa siguiente puede comenzar.**

Esta fase NO escribe código de la solución. Solo verifica, mide y reporta.

---

## 2. Reglas operativas de la fase

- Read-only sobre el sistema. Ninguna modificación a schemas, código o datos.
- Si encuentra bloqueos: PAUSAR y reportar antes de seguir.
- Si encuentra ambigüedad: NO inventar defaults. Reportar y consultar.
- Todos los hallazgos van al reporte final con evidencia (queries, paths, conteos).
- Tests propuestos para cada etapa quedan documentados aquí.

---

## 3. Bloque A — Inventario de tipos de datos existentes

### A.1 Verificar tabla `ofertas_dashboard` en Supabase

Validar que existen las siguientes columnas y su tipo:

- `id_oferta` (TEXT)
- `validacion_humana` (TEXT)
- `validacion_humana_at` (TIMESTAMP)
- `validacion_humana_por` (TEXT)
- `observaciones` (TEXT)
- `esco_occupation_uri` (TEXT)
- `esco_occupation_label` (TEXT)
- `isco_code` (TEXT)
- `run_id` (TEXT) — confirmado disponible post-Sprint 18
- `matching_version` (TEXT) — confirmado disponible post-Sprint 18

**Salida esperada:** Lista de columnas presentes/ausentes. Si falta alguna columna crítica para Etapa 1, marcar como bloqueo.

### A.2 Verificar tabla `gold_set` en Supabase

Validar estructura. Confirmar 112 casos actuales y su distribución por fuente (Excel Cyn, locales, validacion_humana, etc.).

### A.3 Verificar tabla `ofertas_skills` en Supabase

Validar que cada skill tiene asociada categoría (Correcta / Implícita fuerte / Implícita pertinente / Incorrecta) y que se puede marcar individualmente.

### A.4 Verificar tabla de tareas extraídas

Localizar dónde viven las tareas extraídas. Validar que se pueden marcar individualmente como incorrectas.

### A.5 Verificar BD local equivalente

Para cada tabla anterior, verificar correspondencia en SQLite local (`bumeran_scraping.db` u otra). Identificar si hay datos solo locales que falten en Supabase.

### A.6 Datos históricos de Cyn

Query: cuántas ofertas tienen:
- `validacion_humana_por = 'cinvazquez4@gmail.com'` (o equivalente)
- `observaciones` con texto no vacío
- `validacion_humana_at` en último año

**Salida esperada:** Conteo total, distribución temporal, % con observaciones. Esto define cuánto data histórica Etapa 2 puede analizar de entrada.

---

## 4. Bloque B — Inventario de endpoints y RPCs

### B.1 RPCs existentes en Supabase

Listar todas las RPCs disponibles. Verificar al menos:
- `get_ofertas_validacion` (filtros + paginación)
- `get_runs_disponibles` (lista de runs filtrables)
- `get_gold_set_metrics` (KPIs)
- `insertar_pipeline_run` (registro de corrida)

Para cada RPC: parámetros aceptados, valor de retorno, latencia típica.

### B.2 Endpoints Next.js disponibles

Listar todos los endpoints en `app/api/`. Verificar al menos:
- `/api/gold-set-metrics`
- `/api/pipeline-runs`
- `/api/processing-metrics`

Para cada uno: método, params, cobertura de tests.

### B.3 Endpoints faltantes (gap analysis)

Para Etapa 1, Etapa 2, Etapa 3: ¿qué endpoints nuevos son necesarios?

Lista propuesta:
- `POST /api/audit-actions` (registrar acción de auditoría granular)
- `POST /api/oferta-status` (marcar Revisada / Mal extraída totalmente)
- `GET /api/correction-patterns` (Etapa 2)
- `GET /api/correction-impact` (Etapa 3)

Verificar si alguno ya existe parcialmente.

### B.4 Estructura de la UI actual

Identificar:
- Componente `ValidationFilters.tsx`
- Componente `PuestoPanel.tsx`
- Componente `ClasificacionPanel.tsx`
- Componente `OfertaList.tsx`

Verificar dónde se inyectarían:
- Botones nuevos (marcar Revisada, marcar como Mal extraída total)
- Marcadores por tarea/skill individual
- Display de feedback (Etapa 3)

---

## 5. Bloque C — Permisos y credenciales

### C.1 Credenciales Supabase

Verificar que existe y funciona:
- PAT (Personal Access Token) para Management API en `config/supabase_config.json` (o equivalente)
- Service role key
- Anon key

Documentar limitaciones de free tier vs Pro (statement timeouts, rate limits).

### C.2 Credenciales VPS

Verificar acceso para correr scripts de análisis sobre BD local.

### C.3 Permisos de migration

Confirmar que Claude Code puede ejecutar `ALTER TABLE` y crear RPCs nuevas en Supabase sin intervención manual.

---

## 6. Bloque D — Plan de tests por etapa

### D.1 Tests para Etapa 1 (Visualizador estructurado)

**Tests unitarios obligatorios:**
- Marcar oferta como Revisada actualiza estado en BD
- Marcar tarea individual como incorrecta persiste correctamente
- Marcar skill individual como incorrecta o sugerida persiste correctamente
- Marcar oferta como "mal extraída total" registra estado especial
- Filtro nuevo "datos incompletos" funciona
- Filtro nuevo "ocupación corregida manualmente" funciona
- Feedback visual aparece inmediatamente al guardar (test E2E o equivalente)

**Tests de regresión:**
- Las correcciones previas de Cyn (218+ validaciones) siguen visibles
- Categorías existentes (Correcta / Implícita fuerte / etc.) no se rompen
- Filtros existentes (11 + Run) siguen funcionando

**Tests de schema:**
- Migrations son reversibles
- Backfill de columnas nuevas no pierde datos

### D.2 Tests para Etapa 2 (Detección de patrones)

**Tests funcionales:**
- Detección de patrón ISCO 0110 con dataset semilla (casos confirmados por Cyn)
- Falsos positivos sobre patrones aleatorios deben ser cero
- Threshold de confianza configurable

**Tests de regresión:**
- Datos de Etapa 1 no se modifican durante análisis de Etapa 2

### D.3 Tests para Etapa 3 (Loop de feedback)

**Tests funcionales:**
- Mostrar correctamente "tu corrección de X impactó Y ofertas"
- Mostrar correctamente "esta oferta es similar a otra que validaste"
- Notificaciones no son intrusivas

### D.4 Tests transversales

**Performance:**
- Page load `/admin/validacion` < 2s con 68K ofertas
- Marcar acción < 500ms feedback visual

**Seguridad:**
- Acciones de Cyn no se pierden ni se sobreescriben
- Auditoría inmutable (no se borran registros)

---

## 7. Bloque E — Dependencias externas

### E.1 Bugs operativos prerequisito

Validar que están resueltos antes de Etapa 1:
- Bug "oferta cambia entre secciones" (reportado por Cyn, Bloque 1.4)
- Bug buscador por ID (reportado por Cyn, Bloque 1.4)
- Feedback visual al guardar (pedido máximo de Cyn, Bloque 2.6)

Si NO están resueltos: Etapa 1 está bloqueada. La UI mejorada no resuelve el problema base.

### E.2 Capacitación Alt+6 a Cyn

Validar si ya se hizo. Si no: bloqueante para que Cyn use el flujo nuevo.

### E.3 R3 del diagnóstico de escalados

Bug puro V27 (454 falsos positivos). No bloquea SPEC W pero es bueno fixearlo antes para no contaminar análisis de patrones (Etapa 2).

---

## 8. Bloque F — Riesgos técnicos a verificar

### F.1 ¿El schema actual soporta marcar tareas individuales?

Si `ofertas_dashboard` no tiene granularidad por tarea, hay que diseñar nueva tabla o JSONB. Reportar opciones.

### F.2 ¿El schema actual soporta múltiples categorías por skill?

Verificar si una skill puede tener varias marcas (Correcta + sugerida, por ejemplo) o si es exclusivo.

### F.3 ¿Hay race conditions conocidas en validación?

Si Cyn marca una oferta y el sync con local corre simultáneamente, ¿qué pasa? Verificar locks o timestamps.

### F.4 ¿La búsqueda de "ofertas similares" (Etapa 3) es viable?

Verificar si hay embeddings ya generados sobre ofertas que permitan calcular similitud. Si no, ¿hay que generar?

---

## 9. Salida esperada de Fase 0

### 9.1 Reporte de factibilidad

Archivo `FASE_0_RESULTADO.md` con:

```
# Fase 0 — Resultado

## Veredicto global
[OK PARA AVANZAR | BLOQUEADO | OK CON AJUSTES]

## Bloque A — Tipos de datos
- Estado: [OK | Faltan columnas X, Y]
- Acción requerida: ...

## Bloque B — Endpoints
- Estado: ...
- Endpoints nuevos requeridos: ...

## Bloque C — Permisos
- Estado: ...

## Bloque D — Plan de tests
- Tests por etapa: [definidos / pendientes]
- Cobertura objetivo: ...

## Bloque E — Dependencias externas
- Bugs prerequisito: [resueltos / pendientes]
- Lista de bloqueos: ...

## Bloque F — Riesgos técnicos
- Riesgos verificados: ...
- Decisiones pendientes: ...

## Estimación final
- Etapa 1: X-Y horas
- Etapa 2: X-Y horas
- Etapa 3: X-Y horas
- Total: X-Y semanas

## Próximo paso recomendado
[Avanzar a Etapa 1 | Resolver bloqueos | Ajustar SPEC]
```

### 9.2 Decisiones pendientes a consultar

Lista de decisiones de diseño que Claude Code NO debe tomar por su cuenta y que requieren input de Gerardo. Ejemplos posibles:

- Schema para marcar tareas individuales: tabla nueva vs JSONB vs columna múltiple
- Granularidad de "mal extraída total": estado simple vs estado + detalle por bloque
- Threshold de confianza para Etapa 2: empezar bajo (más candidatos, más ruido) o alto (menos candidatos, mejor precisión)
- Cómo mostrar feedback de Etapa 3: notificación, panel separado, badge

---

## 10. Criterios de "Fase 0 OK"

Para que Fase 0 cierre con veredicto OK:

| # | Criterio | Sin esto, NO se avanza |
|---|----------|------------------------|
| 1 | Todos los tipos de datos críticos están presentes o el plan de migration es claro | Sí |
| 2 | Los endpoints existentes están documentados y los faltantes identificados | Sí |
| 3 | Plan de tests por etapa está completo y reviewable | Sí |
| 4 | Bugs operativos prerequisito están resueltos o tienen plan claro | Sí |
| 5 | Riesgos técnicos están verificados o tienen mitigación documentada | Sí |
| 6 | Decisiones pendientes están listadas para que Gerardo apruebe | Sí |
| 7 | Estimación final es realista (basada en evidencia, no en optimismo) | Sí |

Si alguno falla: veredicto BLOQUEADO o OK CON AJUSTES, según severidad.

---

## 11. Tiempo estimado de Fase 0

- Bloque A (Tipos de datos): 1-2h
- Bloque B (Endpoints): 1h
- Bloque C (Permisos): 30 min
- Bloque D (Plan de tests): 1-2h
- Bloque E (Dependencias): 30 min
- Bloque F (Riesgos): 1-2h
- Reporte final: 30 min-1h

**Total:** 5-9 horas activas.

---

## 12. Comando para arrancar

Cuando Gerardo dé OK para arrancar Fase 0, prompt para Claude Code:

```
Arrancar Fase 0 de SPEC W. Leer SPEC_W_fase0_factibilidad.md como guía. 
Ejecutar los 6 bloques en orden, generar FASE_0_RESULTADO.md al final 
con veredicto claro. PAUSAR ante bloqueos. NO implementar nada todavía.
```
