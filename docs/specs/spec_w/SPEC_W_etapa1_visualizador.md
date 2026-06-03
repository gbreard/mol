# SPEC W — Etapa 1: Visualizador Estructurado

**Estado:** Diseño. Pendiente Fase 0 OK.
**Duración estimada:** 2-3 semanas calendario.
**Prerequisito:** Fase 0 con veredicto OK.

---

## 1. Objetivo

Convertir el validador actual en una herramienta que capture las auditorías de Cyn como datos estructurados, manteniendo lo que ella ya hace bien y agregando solo funcionalidad que ella pidió explícitamente.

**No es:** un rediseño del validador.
**Es:** una extensión quirúrgica que multiplica el valor de cada auditoría.

---

## 2. Alcance

### 2.1 Funcionalidad nueva (pedida por Cyn)

| # | Funcionalidad | Origen del pedido |
|---|---------------|-------------------|
| F1 | Marcar tarea individual como incorrecta | Cuestionario B4.6 |
| F2 | Marcar skill individual como incorrecta o sugerida | Cuestionario B4.6 |
| F3 | Agregar tarea/skill nueva como "sugerida" | Cuestionario B4.6 |
| F4 | Estado "Revisada" explícito al terminar oferta | Cuestionario B4.8 |
| F5 | Marcar oferta como "mal extraída en su totalidad" | Cuestionario comentario final |
| F6 | Feedback visual inmediato al guardar correcciones | Cuestionario B2.6 (prioridad máxima) |
| F7 | Filtro "datos incompletos" (sin ESCO/skills/tareas/score bajo) | Cuestionario B2.4 |
| F8 | Filtro "ocupación corregida manualmente" | Cuestionario B2.4 |
| F9 | Mostrar denominación Argentina/España de ocupación en panel detalle | Cuestionario B4.1 |

### 2.1.b Funcionalidad de infraestructura (input externo)

| # | Funcionalidad | Origen |
|---|---------------|--------|
| F10 | Distinguir origen de acciones: humano vs auto_corrector vs rule_engine vs import | Análisis externo (punto #22) |

Esta funcionalidad no es directamente visible en la UI del validador, pero es base para Etapa 2 (poder analizar separadamente correcciones humanas vs automáticas) y para reportes globales del sistema.

### 2.2 Lo que NO se toca (Cyn confirmó que funciona)

- Estructura por bloque de revisión (NLP / Tareas / Skills / Ocupación)
- Notas libres en `observaciones`
- Categorías existentes de skills (Correcta / Implícita fuerte / Implícita pertinente / Incorrecta)
- Buscador por ID (excepto fix del bug)
- Edición de campos NLP
- Filtros que ella usa (ISCO, Score, ID, Limpiar)
- Filtro Run/Corrida implementado en Sprint 18

### 2.3 Bugs prerequisito (resolver antes de Etapa 1)

- B1: Oferta cambia automáticamente entre secciones
- B2: Buscador por ID inconsistente
- B3: R3 del diagnóstico (bug V27 con ISCOs iguales) — opcional, no bloqueante pero recomendado

---

## 3. Arquitectura propuesta

### 3.1 Schema de datos

#### 3.1.1 Tabla nueva: `audit_actions`

Registro granular de cada acción de auditoría que Cyn hace sobre una oferta.

```sql
CREATE TABLE audit_actions (
  id BIGSERIAL PRIMARY KEY,
  id_oferta TEXT NOT NULL,
  validador TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  action_type TEXT NOT NULL CHECK (action_type IN (
    'mark_task_incorrect',
    'mark_skill_incorrect',
    'add_suggested_task',
    'add_suggested_skill',
    'mark_revised',
    'mark_total_failure',
    'unmark_revised',
    'unmark_total_failure'
  )),
  target_type TEXT CHECK (target_type IN ('task', 'skill', 'occupation', 'oferta_global')),
  target_id TEXT,
  target_value TEXT,
  note TEXT,
  run_id TEXT,
  matching_version TEXT
);

CREATE INDEX idx_audit_actions_oferta ON audit_actions(id_oferta);
CREATE INDEX idx_audit_actions_validador ON audit_actions(validador);
CREATE INDEX idx_audit_actions_type ON audit_actions(action_type);
CREATE INDEX idx_audit_actions_timestamp ON audit_actions(timestamp);
CREATE INDEX idx_audit_actions_source ON audit_actions(source);
```

**Nota sobre `source`:** Distingue origen de la acción:
- `human`: acción de un validador (Cyn, Diego, otros)
- `auto_corrector`: acción del AutoCorrector
- `rule_engine`: acción derivada de una regla del matcher
- `import`: acción ingerida desde fuente externa (ej: Excel histórico de Cyn)

Esto resuelve el punto #22 del análisis externo: separar issues automáticos vs humanos. Permite que Etapa 2 analice solo correcciones humanas (señal de calidad) o solo automáticas (señal de cobertura del corrector), según el caso.

**Schema actualizado de `audit_actions`:**

```sql
ALTER TABLE audit_actions ADD COLUMN source TEXT NOT NULL DEFAULT 'human'
  CHECK (source IN ('human', 'auto_corrector', 'rule_engine', 'import'));
```

Si la tabla se crea desde cero, incluir `source` en el CREATE TABLE original.

**Por qué tabla separada y no columnas en `ofertas_dashboard`:**
- Permite historial: si Cyn cambia de opinión, queda registro
- Permite análisis de patrones (Etapa 2) sin tocar tabla principal
- Inmutable: no se borra, solo se invalida con acción nueva
- Permite distinguir acciones humanas vs automáticas (campo `source`)

#### 3.1.2 Columnas nuevas en `ofertas_dashboard`

```sql
ALTER TABLE ofertas_dashboard ADD COLUMN estado_revision TEXT 
  CHECK (estado_revision IN (NULL, 'revisada', 'mal_extraida_total'));

ALTER TABLE ofertas_dashboard ADD COLUMN denominacion_arg TEXT;
ALTER TABLE ofertas_dashboard ADD COLUMN denominacion_esp TEXT;
```

`estado_revision` se actualiza automáticamente desde la última `audit_action` relevante (trigger o vista materializada).

#### 3.1.3 Schema para marcas individuales de tareas/skills

Opción A — Columna JSONB en `ofertas_dashboard`:
```sql
ALTER TABLE ofertas_dashboard ADD COLUMN audit_state JSONB DEFAULT '{}';
-- audit_state = {
--   "tasks_incorrect": ["task_id_1", "task_id_2"],
--   "skills_incorrect": ["skill_id_3"],
--   "skills_suggested": [{"name": "Atención al cliente", "category": "duty"}],
--   "tasks_suggested": [...]
-- }
```

Opción B — Reconstruir desde `audit_actions` con vista materializada.

**Decisión:** A consultar en Fase 0. Opción A es más simple pero menos auditable. Opción B es más limpia pero requiere refrescos.

### 3.2 Endpoints nuevos

#### 3.2.1 `POST /api/audit-actions`

```typescript
// Request
{
  id_oferta: string;
  action_type: AuditActionType;
  target_type?: 'task' | 'skill' | 'occupation' | 'oferta_global';
  target_id?: string;
  target_value?: string;
  note?: string;
}

// Response
{
  success: boolean;
  action_id: number;
  updated_estado_revision?: string;
}
```

#### 3.2.2 `DELETE /api/audit-actions/:id`

Para deshacer (genera acción inversa, no borra).

#### 3.2.3 `GET /api/oferta/:id/audit-history`

Devuelve historial de acciones sobre la oferta, ordenado cronológicamente.

#### 3.2.4 Extensión a `getOfertasValidacion`

Agregar parámetros:
- `solo_datos_incompletos: boolean` — filtra ofertas sin ESCO / sin skills / sin tareas / score < 0.5
- `solo_correccion_manual: boolean` — filtra ofertas con al menos una `audit_action`
- `estado_revision: 'revisada' | 'mal_extraida_total' | 'pendiente'`

### 3.3 Componentes UI

#### 3.3.1 Nuevo: `AuditActionToolbar`

Barra de acciones que aparece en el panel detalle de cada oferta:

```
[ Marcar revisada ] [ Mal extraída total ] [ + Gold Set ]
```

Estados visuales:
- Si ya revisada: botón "Revisada ✓" en verde
- Si marcada como mal extraída: botón "Mal extraída ⚠️" en rojo
- Si gold set: badge dorado

#### 3.3.2 Modificación: `ClasificacionPanel.tsx`

Cada tarea y skill listada tiene:
- Botón ✕ (marcar como incorrecta)
- Botón ➕ (agregar como sugerida en otra)
- Display de marca actual si la hay

#### 3.3.3 Modificación: `PuestoPanel.tsx`

Agregar campos:
- Denominación Argentina
- Denominación España
- Badge "Mal extraída total" si aplica

#### 3.3.4 Modificación: `ValidationFilters.tsx`

Agregar:
- Toggle "Solo datos incompletos"
- Toggle "Solo ocupación corregida manualmente"
- Dropdown "Estado revisión" (Todas / Pendientes / Revisadas / Mal extraídas)

#### 3.3.5 Nuevo: `FeedbackToast`

Toast no intrusivo que aparece al guardar correcciones:
- "Tarea marcada como incorrecta ✓"
- "Oferta marcada como revisada ✓"
- "Sugerencia agregada ✓"

Resuelve F6 (feedback visual inmediato, prioridad máxima de Cyn).

---

## 4. Casos de uso

### 4.1 Caso: Cyn audita una oferta y todo está bien

**Flujo:**
1. Cyn entra a `/admin/validacion`, busca por ID
2. Lee oferta completa
3. Revisa NLP, tareas, skills, ocupación → todo OK
4. Click en "Marcar revisada"
5. Toast: "Oferta marcada como revisada ✓"
6. Oferta queda con `estado_revision = 'revisada'`

**Acciones registradas:**
- 1 acción `mark_revised`

### 4.2 Caso: Cyn detecta una tarea mal extraída y agrega otra correcta

**Flujo:**
1. Cyn entra al panel detalle
2. Ve 5 tareas extraídas, identifica que la #3 está mal
3. Click ✕ junto a tarea #3 → toast "Tarea marcada como incorrecta"
4. Cyn identifica que falta una tarea importante: "Atención al cliente en mesa"
5. Click ➕ "Agregar tarea sugerida" → modal pequeño
6. Cyn escribe la tarea, confirma
7. Marca oferta como revisada

**Acciones registradas:**
- 1 `mark_task_incorrect` con target_id de la tarea
- 1 `add_suggested_task` con target_value del texto
- 1 `mark_revised`

### 4.3 Caso: Oferta totalmente mal extraída (ISCO 0110)

**Flujo:**
1. Cyn ve oferta clasificada como Fuerzas Armadas
2. Lee el aviso: es un puesto civil de mantenimiento
3. Click "Mal extraída total"
4. Modal pide nota opcional: "Sistema interpretó 'oficial' como militar. Es operario."
5. Confirma → toast "Oferta marcada como mal extraída total ✓"
6. Cyn marca como Gold Set también (Alt+6 o botón)

**Acciones registradas:**
- 1 `mark_total_failure` con nota
- 1 acción Gold Set asociada

**Importante:** este caso es candidato directo para Etapa 2 (detección de patrones).

### 4.4 Caso: Cyn quiere ver solo ofertas con datos incompletos

**Flujo:**
1. Entra al validador
2. Activa filtro "Solo datos incompletos"
3. Lista se filtra: ofertas sin ESCO, sin skills, sin tareas, o con score < 0.5
4. Cyn las audita una por una

### 4.5 Caso: Cyn quiere ver cuáles fueron corregidas manualmente

**Flujo:**
1. Entra al validador
2. Activa filtro "Solo ocupación corregida manualmente"
3. Lista: ofertas con al menos una acción de auditoría
4. Cyn revisa si los errores se repiten en sectores específicos

---

## 5. Criterios de aceptación

| # | Criterio | Cómo se valida |
|---|----------|----------------|
| C1 | F1-F9 implementadas y testeadas | Tests unitarios verdes |
| C2 | Cero regresión sobre funcionalidad existente | Suite completa de tests verde |
| C3 | Toast aparece en <500ms tras guardar acción | Test de performance |
| C4 | Cyn puede operar el flujo sin manual escrito | Sesión de 30 min con Cyn confirmando UX |
| C5 | Acciones quedan registradas inmutables en `audit_actions` | Test que verifica no-modificación |
| C6 | Filtros nuevos devuelven resultados correctos | Tests con dataset semilla |
| C7 | Migration es reversible | Test de rollback |

---

## 6. Plan de implementación

### 6.1 Sprint 1 (semana 1): Schema + backend

- Migration 023: tabla `audit_actions` + columnas en `ofertas_dashboard`
- Endpoints `POST /api/audit-actions`, `DELETE`, `GET history`
- Backfill: ¿algunas validaciones previas de Cyn se pueden traducir a `audit_actions` retroactivamente?
- Tests unitarios sobre RPCs y endpoints

### 6.2 Sprint 2 (semana 2): UI básica

- `AuditActionToolbar` con botones Revisada / Mal extraída total
- `FeedbackToast` con feedback visual al guardar (F6)
- Modificación de `ClasificacionPanel` con botones ✕ y ➕ por tarea/skill
- Tests E2E del flujo básico

### 6.3 Sprint 3 (semana 3): Filtros + refinamientos

- Filtros nuevos (F7, F8) en `ValidationFilters`
- Denominación Argentina/España en `PuestoPanel` (F9)
- Polish de UX
- Sesión de testing con Cyn

### 6.4 Sprint 4 (semana 4): Validación con usuaria

- Cyn opera el flujo nuevo en producción
- Ajustes según feedback
- Documentación operativa
- Cierre de Etapa 1

---

## 7. Métricas de éxito de Etapa 1

| # | Métrica | Objetivo | Cuándo medir |
|---|---------|----------|--------------|
| M1 | Cyn marca al menos 10 ofertas como Revisada por día | ≥ 10 / día | 2 semanas post-lanzamiento |
| M2 | Cyn registra al menos 5 acciones granulares (tarea/skill) por semana | ≥ 5 / semana | 4 semanas post-lanzamiento |
| M3 | Tiempo promedio por oferta baja a <15 min | < 15 min | 4 semanas post-lanzamiento |
| M4 | Cyn marca al menos 5 ofertas como Gold Set por semana | ≥ 5 / semana | 4 semanas post-lanzamiento |
| M5 | Cero quejas operativas sobre la nueva UI | Cero | 2 semanas post-lanzamiento |

Si M1-M5 no se cumplen en los plazos: ajustar UX antes de avanzar a Etapa 2.

---

## 8. Riesgos específicos de Etapa 1

### 8.1 Riesgo: Cyn no adopta filtros nuevos

**Probabilidad:** Media.
**Mitigación:** Que los filtros aparezcan visibles en posición central, no escondidos. Demo en sesión de capacitación.

### 8.2 Riesgo: Botones de acción se confunden con edición de campos

**Probabilidad:** Baja.
**Mitigación:** Separación visual clara, colores distintos, ubicación consistente.

### 8.3 Riesgo: Marcas individuales generan UI sobrecargada

**Probabilidad:** Media-alta.
**Mitigación:** Marcas pequeñas y discretas, no labels grandes. Hover para detalles.

### 8.4 Riesgo: Performance degrada con muchas `audit_actions`

**Probabilidad:** Baja inicialmente, sube con el tiempo.
**Mitigación:** Índices apropiados desde el inicio. Vista materializada para agregados.

---

## 9. Decisiones pendientes (a resolver en Fase 0)

| # | Decisión | Opciones | Quién decide |
|---|----------|----------|--------------|
| D1 | Schema para marcas granulares: tabla `audit_actions` + columnas dedicadas vs JSONB | A / B (sección 3.1.3) | Gerardo en Fase 0 |
| D2 | Backfill retroactivo de validaciones previas a `audit_actions` | Sí / No / Parcial | Gerardo en Fase 0 |
| D3 | Granularidad de "mal extraída total": flag simple vs detalle por bloque | Simple / Detallado | Gerardo |
| D4 | Cómo distinguir "tarea sugerida nueva" de "edición de tarea existente" | Acción aparte / Misma con flag | Gerardo |

---

## 10. Salidas de Etapa 1

Al cerrar Etapa 1:

- 1 migration aplicada en Supabase con `audit_actions` + columnas
- 3-4 endpoints nuevos en Next.js
- 4-5 componentes UI modificados o nuevos
- Suite de tests completa
- Documentación operativa para Cyn (1-2 páginas)
- Reporte de métricas M1-M5 a 4 semanas
