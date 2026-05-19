# SPEC W — Etapa 2: Detección de Patrones

**Estado:** Diseño. Pendiente Etapa 1 OK + datos acumulados.
**Duración estimada:** 2-3 semanas calendario.
**Prerequisito:** Etapa 1 implementada + 4-6 semanas de datos en `audit_actions`.

---

## 1. Objetivo

Analizar las auditorías acumuladas de Cyn para detectar patrones generalizables: tipos de error que se repiten con misma causa raíz y son candidatos a regla nueva del matcher.

El sistema NO aplica reglas automáticamente. Genera **candidatos a regla** que pasan por revisión humana (Gerardo) antes de incorporarse al matcher.

---

## 2. Casos de uso que justifican Etapa 2

### 2.1 Caso real conocido: ISCO 0110 Fuerzas Armadas

Cyn identificó manualmente que el matcher clasifica como militar palabras ambiguas:
- "oficial" → puesto de mantenimiento
- "armador" → armado de productos
- "armado" → armado de productos
- "generalista" → puesto de RRHH
- "flota" → puesto de cobranzas

**Tiempo invertido por Cyn:** Varias correcciones a lo largo de semanas, sin ver el patrón emerger automáticamente.

**Lo que Etapa 2 hace:** Detecta automáticamente que estas correcciones comparten causa (ISCO 0110 reasignado a otros ISCOs por contexto) y propone una regla.

### 2.2 Caso real conocido: Títulos genéricos

Cyn identificó: "Técnico", "Analista", "Administrativo" llevan a clasificaciones distintas según sector y tareas. El sistema se guía por título y pierde contexto.

**Patrón candidato a detectar:** Cuando un título genérico aparece, el matcher debería pesar más las tareas y skills extraídas.

### 2.3 Casos a descubrir

Cyn no es consciente de todos los patrones. Etapa 2 puede revelar tipos de error que ni ella ni el equipo identificaron explícitamente.

---

## 3. Arquitectura propuesta

### 3.1 Flujo general

```
audit_actions (datos crudos)
    │
    ▼
[Análisis de patrones]
    │
    ▼
candidate_rules (propuestas)
    │
    ▼
[Revisión humana — Gerardo]
    │
    ▼
matcher_rules (reglas activas en matcher)
```

### 3.2 Schema de datos

#### 3.2.1 Tabla nueva: `candidate_rules`

```sql
CREATE TABLE candidate_rules (
  id BIGSERIAL PRIMARY KEY,
  detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  pattern_type TEXT NOT NULL CHECK (pattern_type IN (
    'isco_reassignment',
    'occupation_correction',
    'task_systematically_wrong',
    'skill_systematically_wrong',
    'title_keyword_ambiguous'
  )),
  
  -- Descripción del patrón
  pattern_description TEXT,
  
  -- Evidencia (cuántas ofertas, cuáles)
  evidence_count INTEGER,
  evidence_ofertas_ids TEXT[],
  
  -- ISCOs involucrados
  isco_from TEXT,
  isco_to TEXT,
  
  -- Keywords/contexto
  trigger_keywords TEXT[],
  
  -- Confianza
  confidence_score FLOAT,
  
  -- Estado de revisión
  review_status TEXT DEFAULT 'pending' CHECK (review_status IN (
    'pending', 'approved', 'rejected', 'needs_refinement'
  )),
  reviewed_by TEXT,
  reviewed_at TIMESTAMP,
  reviewer_notes TEXT,
  
  -- Regla propuesta (formato matcher)
  proposed_rule_json JSONB,
  
  -- Si fue aprobada e implementada
  implemented_in_matching_version TEXT
);

CREATE INDEX idx_candidate_rules_status ON candidate_rules(review_status);
CREATE INDEX idx_candidate_rules_type ON candidate_rules(pattern_type);
```

### 3.3 Algoritmos de detección

#### 3.3.1 Detector A: Reasignación de ISCO

Análisis: agrupar `audit_actions` por `mark_total_failure` y por `target_type = 'occupation'`. Identificar:
- ISCO origen (clasificación del matcher)
- ISCO destino (clasificación corregida por Cyn)
- Frecuencia del cambio

Si la misma reasignación ocurre ≥3 veces en N semanas → candidato a regla.

**Output:** Candidato tipo `isco_reassignment`.

#### 3.3.2 Detector B: Keywords ambiguos

Análisis: para casos `mark_total_failure`, extraer keywords del título de las ofertas. Identificar palabras que aparecen frecuentemente en ofertas mal clasificadas para un ISCO específico.

Ejemplo: "oficial" aparece en 80% de las ofertas mal clasificadas como ISCO 0110.

**Output:** Candidato tipo `title_keyword_ambiguous`.

#### 3.3.3 Detector C: Tareas sistemáticamente incorrectas

Análisis: tareas marcadas como `mark_task_incorrect` agrupadas por similitud semántica (embeddings).

Si N tareas similares fueron marcadas incorrectas → patrón.

**Output:** Candidato tipo `task_systematically_wrong`.

#### 3.3.4 Detector D: Skills sistemáticamente incorrectas

Mismo concepto que C pero para skills.

**Output:** Candidato tipo `skill_systematically_wrong`.

### 3.4 Threshold y confianza

Cada candidato tiene un `confidence_score` entre 0 y 1:

```
confidence = (evidence_count / threshold_evidence) * (consistency_factor)

donde:
- threshold_evidence = mínimo de evidencias para considerar patrón (default: 3)
- consistency_factor = qué tan consistente es el patrón (1.0 si todas las correcciones apuntan a lo mismo, baja si hay variación)
```

Solo candidatos con `confidence_score >= 0.7` se muestran como propuestas activas. Los demás quedan como observaciones de baja confianza.

---

## 4. Endpoints y UI

### 4.1 Endpoints

#### 4.1.1 `GET /api/correction-patterns`

```typescript
// Query params
{
  status?: 'pending' | 'approved' | 'rejected';
  pattern_type?: string;
  min_confidence?: number;
}

// Response
{
  candidates: CandidateRule[];
  total: number;
}
```

#### 4.1.2 `POST /api/correction-patterns/:id/review`

```typescript
// Request
{
  decision: 'approved' | 'rejected' | 'needs_refinement';
  reviewer_notes?: string;
}
```

#### 4.1.3 `POST /api/correction-patterns/run-detection`

Trigger manual del análisis. Idealmente corre como cron diario.

### 4.2 UI: nuevo dashboard en `/admin/aprendizaje`

Agregar sección "Patrones detectados" con:

- Tabla de candidatos pendientes
- Filtros por tipo, confianza, fecha
- Detalle de cada candidato: descripción, evidencia (lista de ofertas), regla propuesta
- Botones aprobar / rechazar / refinar

---

## 5. Flujo de revisión humana

### 5.1 Cuando Etapa 2 detecta un candidato

1. Cron diario corre detección, genera nuevos `candidate_rules` con `status='pending'`
2. Notificación a Gerardo (opcional, según volumen)
3. Gerardo entra a `/admin/aprendizaje` → sección Patrones
4. Lee descripción del candidato, ve evidencia (lista de ofertas)
5. Decide:
   - **Approved:** acepta como regla, se genera el JSON del matcher
   - **Rejected:** descarta, queda registro de por qué
   - **Needs refinement:** vuelve a Cyn / sistema para más datos

### 5.2 Cuando una regla es aprobada

1. Se genera entrada en `matcher_rules` con la regla nueva
2. Próximo run del matcher la incorpora
3. Se actualiza `implemented_in_matching_version`
4. Etapa 3 (loop de feedback) puede notificar a Cyn que su corrección generó una regla

---

## 6. Casos de uso

### 6.1 Caso: Detección automática de ISCO 0110

**Estado inicial:** Cyn marcó 15 ofertas como `mark_total_failure` durante el último mes, todas reasignadas de ISCO 0110 a otros ISCOs.

**Flujo:**
1. Cron corre detección
2. Detector A identifica patrón: ISCO 0110 → varios destinos
3. Detector B identifica keywords: "oficial", "armado", "armador", "generalista", "flota"
4. Genera 1 `candidate_rule` tipo `isco_reassignment + title_keyword_ambiguous`
5. Confianza: 0.85
6. Gerardo lo ve en dashboard, evidencia incluye los 15 IDs
7. Gerardo confirma: regla nueva en matcher que descalifica ISCO 0110 si aparecen estas keywords y el contexto no es militar
8. Próximo run del matcher la aplica

### 6.2 Caso: Tarea sistemáticamente mal extraída

**Estado inicial:** Cyn marcó 8 tareas similares como `mark_task_incorrect` (variantes de "responsable de inventario").

**Flujo:**
1. Cron corre detección
2. Detector C agrupa por similitud semántica
3. Genera candidato tipo `task_systematically_wrong` con la descripción "El NLP extrae 'inventario' como tarea aislada cuando es complemento de otra tarea"
4. Confianza: 0.65 (bajo threshold)
5. Queda como observación, no propuesta activa
6. Si vuelven a aparecer más casos similares en próximas semanas, sube de confianza

---

## 7. Criterios de aceptación

| # | Criterio | Cómo se valida |
|---|----------|----------------|
| C1 | Detector A detecta el patrón ISCO 0110 con dataset semilla | Test funcional |
| C2 | Cero falsos positivos sobre dataset de control aleatorio | Test funcional |
| C3 | Candidatos con `confidence < 0.7` no se muestran como propuestas activas | Test unitario |
| C4 | Aprobación de regla genera JSON aplicable al matcher | Test E2E |
| C5 | Cron diario corre sin intervención manual | Test de scheduler |
| C6 | UI permite revisar candidato y decidir | Test E2E + sesión con Gerardo |

---

## 8. Plan de implementación

### 8.1 Sprint 1 (semana 1): Schema + detectores básicos

- Migration 024: tabla `candidate_rules`
- Implementación Detector A (reasignación ISCO)
- Implementación Detector B (keywords ambiguos)
- Tests unitarios

### 8.2 Sprint 2 (semana 2): Detectores avanzados + endpoints

- Detector C (tareas)
- Detector D (skills)
- Endpoints `/api/correction-patterns`
- Cron diario

### 8.3 Sprint 3 (semana 3): UI + flujo de revisión

- Componente nuevo en `/admin/aprendizaje`
- Flujo de aprobación/rechazo
- Generación de JSON de regla
- Tests E2E

---

## 9. Métricas de éxito de Etapa 2

| # | Métrica | Objetivo | Cuándo medir |
|---|---------|----------|--------------|
| M1 | Etapa 2 detecta al menos 1 patrón generalizable por mes | ≥ 1 / mes | 8 semanas post-lanzamiento |
| M2 | ≥70% de candidatos aprobados son útiles (reducen errores reales) | ≥ 70% | 12 semanas post-lanzamiento |
| M3 | Falsos positivos (candidatos rechazados sin valor) < 30% | < 30% | 8 semanas post-lanzamiento |
| M4 | Patrones aplicados al matcher generan mejora medible en Gold Set | Mejora ≥ 5% | 12 semanas post-lanzamiento |

---

## 10. Riesgos específicos de Etapa 2

### 10.1 Riesgo: Falsos positivos excesivos

**Probabilidad:** Media-alta inicial, baja con tuning.
**Mitigación:** Threshold conservador. Revisión humana obligatoria. Logs de rechazos para ajustar detectores.

### 10.2 Riesgo: Datos insuficientes para detectar patrones

**Probabilidad:** Alta los primeros meses.
**Mitigación:** Etapa 2 solo arranca tras 4-6 semanas de datos acumulados en `audit_actions`. Si no hay suficiente, posponer.

### 10.3 Riesgo: Reglas generadas son demasiado específicas o demasiado amplias

**Probabilidad:** Media.
**Mitigación:** Iteración con Gerardo en revisión. Posibilidad de refinar antes de aprobar.

### 10.4 Riesgo: Aprobación automática se convierte en sello de goma

**Probabilidad:** Baja si la UI obliga a ver evidencia.
**Mitigación:** UI muestra siempre lista de ofertas afectadas. No se puede aprobar sin verlas.

---

## 11. Decisiones pendientes (a resolver durante implementación)

| # | Decisión | Opciones | Cuándo |
|---|----------|----------|--------|
| D1 | Threshold de confianza para mostrar candidatos | 0.5 / 0.7 / 0.85 | Sprint 1 con datos reales |
| D2 | Mínimo de evidencias para considerar patrón | 3 / 5 / 10 | Sprint 1 |
| D3 | Ventana temporal para análisis | 30 días / 60 días / sin límite | Sprint 1 |
| D4 | Cron frecuencia | Diario / semanal | Sprint 2 |
| D5 | Quién recibe notificación de candidatos nuevos | Solo Gerardo / Gerardo + Cyn | Sprint 3 |

---

## 12. Salidas de Etapa 2

Al cerrar Etapa 2:

- 1 migration aplicada con `candidate_rules`
- 4 detectores funcionando
- Cron diario activo
- 3-4 endpoints nuevos
- 1 sección nueva en `/admin/aprendizaje`
- Suite de tests completa
- Reporte de patrones detectados en primeras 8 semanas
