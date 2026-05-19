# SPEC W — Etapa 3: Loop de Feedback al Validador

**Estado:** Diseño. Pendiente Etapa 1 OK + Etapa 2 al menos parcial.
**Duración estimada:** 2-3 semanas calendario.
**Prerequisito:** Etapa 1 implementada + Etapa 2 con al menos 1 patrón aprobado.

---

## 1. Objetivo

Cerrar el ciclo entre Cyn y el sistema mostrándole el impacto de sus correcciones. Que ella vea: "esta corrección que hiciste hace 2 semanas afectó a 30 ofertas nuevas similares" o "el sistema ahora clasifica como vos sugeriste".

Cyn lo pidió explícitamente en el cuestionario (Bloque 5).

---

## 2. Por qué importa

### 2.1 Beneficios operativos

- **Motivación:** ver que el trabajo tiene impacto reduce fatiga
- **Calidad:** Cyn detecta si sus correcciones se aplican bien (catch a errores de propagación)
- **Eficiencia:** ver ofertas similares ya validadas evita re-trabajo
- **Aprendizaje compartido:** los criterios consolidados se vuelven explícitos

### 2.2 Lo que Cyn pidió (Bloque 5)

| Pedido | Cita textual |
|--------|-------------|
| Ver impacto a futuro | "Me serviría poder corroborar si las ofertas similares nuevas empiezan a extraerse correctamente" |
| Ver casos similares | "Me serviría que el sistema me muestre cuando una oferta es similar a otra que ya validé" |
| Feedback explícito | "Si yo corregí una oferta como ESCO 4311.1, sería útil que el sistema me muestre que ahora la está clasificando de esa manera" |

---

## 3. Funcionalidades

### F1: Vista "Impacto de mis correcciones"

Panel separado o sección de `/admin/validacion` donde Cyn ve:
- Sus últimas 10 correcciones que generaron `candidate_rule`
- Estado de cada candidata: pendiente / aprobada / aplicada en matcher
- Si aplicada: cuántas ofertas nuevas afectó

### F2: Vista "Casos similares ya validados"

Al abrir una oferta para auditar, mostrar (si aplica):
- "Esta oferta es similar a 3 que ya validaste. Click para comparar."
- Lista de las 3 con su decisión

### F3: Notificación sutil de aplicación

Cuando una corrección de Cyn se convierte en regla aplicada al matcher:
- Toast la próxima vez que entra: "Tu corrección sobre ISCO 0110 se aplicó al matcher. Afectó 24 ofertas nuevas. Ver detalle."
- Badge en una sección "Novedades" del dashboard

### F4: Confirmar resultado de correcciones

Cyn puede recibir la pregunta: "Vos sugeriste X. El matcher ahora clasifica así. ¿Está mejor?"

Respuesta de Cyn: "Sí mejor" / "No, todavía mal" / "Parcialmente".

Esto alimenta calidad de Etapa 2 (qué reglas funcionaron, cuáles no).

---

## 4. Arquitectura

### 4.1 Cálculo de similitud entre ofertas

Para F2, necesitamos saber cuándo dos ofertas son "similares". Opciones:

#### Opción A: Embeddings sobre descripción

Generar embeddings sobre el campo descripción de cada oferta. Comparar con cosine similarity.

**Requiere:** Que existan embeddings o que se generen. Modelo BGE-M3 ya está disponible en el proyecto.

#### Opción B: Coincidencia por ISCO + sector + keywords del título

Heurística más simple. Misma ocupación + mismo sector + ≥1 keyword común en título.

**Requiere:** Solo queries SQL.

#### Opción C: Híbrido

Embeddings para ranking + filtros heurísticos para corte. Más preciso pero más costoso.

**Decisión:** A consultar en Fase 0. Para arrancar Etapa 3, la Opción B alcanza. Opción A queda como mejora.

### 4.2 Schema de datos

#### 4.2.1 Tabla nueva: `correction_impacts`

Registro de impacto observado de cada `candidate_rule` aprobada.

```sql
CREATE TABLE correction_impacts (
  id BIGSERIAL PRIMARY KEY,
  candidate_rule_id BIGINT REFERENCES candidate_rules(id),
  validador TEXT,  -- quién hizo la corrección original
  
  -- Estadísticas de impacto
  ofertas_afectadas_count INTEGER,
  ofertas_afectadas_ids TEXT[],
  
  -- Validación humana del impacto
  feedback_status TEXT DEFAULT 'pending' CHECK (feedback_status IN (
    'pending', 'confirmed_better', 'still_wrong', 'partial'
  )),
  feedback_notes TEXT,
  feedback_at TIMESTAMP,
  feedback_by TEXT,
  
  -- Métricas
  measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  matching_version TEXT
);

CREATE INDEX idx_correction_impacts_rule ON correction_impacts(candidate_rule_id);
CREATE INDEX idx_correction_impacts_validador ON correction_impacts(validador);
```

#### 4.2.2 Tabla nueva: `oferta_similarities`

Cache de similitudes entre ofertas para acelerar F2.

```sql
CREATE TABLE oferta_similarities (
  oferta_a TEXT NOT NULL,
  oferta_b TEXT NOT NULL,
  similarity_score FLOAT,
  computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (oferta_a, oferta_b)
);

CREATE INDEX idx_oferta_similarities_a ON oferta_similarities(oferta_a);
CREATE INDEX idx_oferta_similarities_b ON oferta_similarities(oferta_b);
```

### 4.3 Endpoints

#### `GET /api/correction-impact/:validador`

Devuelve lista de impactos de correcciones del validador.

#### `GET /api/similar-validated/:id_oferta`

Devuelve ofertas similares que el validador actual (Cyn) ya validó.

#### `POST /api/correction-feedback/:impact_id`

Cyn confirma si el impacto fue mejora / sigue mal / parcial.

#### `GET /api/recent-applied-corrections/:validador`

Para mostrar notificación de correcciones aplicadas recientes.

### 4.4 Componentes UI

#### `CorrectionImpactPanel`

Panel en `/admin/validacion` con vista de impactos.

#### `SimilarValidatedBadge`

Pequeño badge en el panel detalle de una oferta: "Similar a 3 validadas".

#### `RecentImpactsToast`

Toast/notificación al entrar al sistema si hay impactos nuevos.

---

## 5. Casos de uso

### 5.1 Caso: Cyn ve impacto de su corrección sobre ISCO 0110

**Flujo:**
1. Cyn entra a `/admin/validacion`
2. Ve toast: "3 de tus correcciones se aplicaron al matcher esta semana. Ver detalle."
3. Click → panel `CorrectionImpactPanel`
4. Lista:
   - "Corrección ISCO 0110 (Fuerzas Armadas → varios). Aplicada en matcher v3.5.5. Afectó 24 ofertas nuevas."
   - "Corrección title genéricos (Técnico). Pendiente revisión."
5. Cyn click en la primera → ve las 24 ofertas afectadas
6. Para algunas, puede confirmar: "Sí mejor" / "No, sigue mal"

### 5.2 Caso: Cyn ve una oferta similar a una ya validada

**Flujo:**
1. Cyn abre oferta "Operario de mantenimiento"
2. En el panel detalle aparece badge: "Similar a 2 que ya validaste"
3. Click → modal pequeño muestra:
   - "Oferta ID #12345 validada hace 1 semana. Cyn marcó como Revisada, observación: 'Ocupación correcta'"
   - "Oferta ID #67890 validada hace 3 días. Cyn marcó como Mal extraída total"
4. Cyn aplica criterio consistente sin re-pensar desde cero

### 5.3 Caso: Pregunta retrospectiva sobre corrección

**Flujo:**
1. Sistema detecta que 5 ofertas nuevas matchean por la regla aplicada de Cyn
2. Genera entrada en `correction_impacts` con feedback pending
3. Cyn entra a `/admin/validacion`
4. Banner: "Tu corrección de hace 2 semanas se está aplicando. ¿Querés revisar 3 casos?"
5. Cyn abre, ve las 3 ofertas, confirma una por una
6. Si todas son "confirmed_better": señal positiva para Etapa 2 (esta regla funciona)

---

## 6. Criterios de aceptación

| # | Criterio | Cómo se valida |
|---|----------|----------------|
| C1 | Cyn puede ver lista de sus correcciones aplicadas | Test E2E |
| C2 | Lista de ofertas similares devuelve resultados correctos | Test funcional |
| C3 | Feedback de Cyn se persiste y alimenta Etapa 2 | Test funcional |
| C4 | Notificación es no intrusiva (puede dismiss) | Test UX con Cyn |
| C5 | Performance: query "similares" responde en <1s | Test de performance |
| C6 | Cero regresión sobre Etapas 1 y 2 | Suite completa verde |

---

## 7. Plan de implementación

### 7.1 Sprint 1 (semana 1): Backend impactos

- Migration 025: `correction_impacts`
- Endpoint `GET /api/correction-impact`
- Job que calcula impactos automáticamente cuando una regla se aplica
- Tests

### 7.2 Sprint 2 (semana 2): Similitud + UI impactos

- Migration: `oferta_similarities`
- Algoritmo de similitud (Opción B inicial)
- Endpoint `GET /api/similar-validated`
- `CorrectionImpactPanel` UI
- Tests

### 7.3 Sprint 3 (semana 3): Notificaciones + feedback

- `RecentImpactsToast`
- `SimilarValidatedBadge`
- Flujo de feedback retrospectivo
- Polish y testing con Cyn

---

## 8. Métricas de éxito

| # | Métrica | Objetivo | Cuándo medir |
|---|---------|----------|--------------|
| M1 | Cyn entra a panel de impactos al menos 1 vez por semana | ≥ 1 / semana | 4 semanas post-lanzamiento |
| M2 | Cyn da feedback sobre al menos 50% de los impactos | ≥ 50% | 8 semanas post-lanzamiento |
| M3 | Casos donde Cyn confirma "mejor" superan a "todavía mal" | Ratio ≥ 3:1 | 12 semanas post-lanzamiento |
| M4 | Tiempo de validación de ofertas similares baja vs validación inicial | -30% | 8 semanas post-lanzamiento |

---

## 9. Riesgos específicos

### 9.1 Riesgo: Notificaciones se vuelven ruido

**Probabilidad:** Alta si no se calibra.
**Mitigación:** Toast solo si hay 3+ correcciones nuevas. Banner solo si hay caso urgente para revisar. Permitir dismiss.

### 9.2 Riesgo: Similitud devuelve falsos positivos

**Probabilidad:** Media con Opción B (heurística).
**Mitigación:** Score visible para Cyn ("similar al 80%"). Mejora con Opción A si es necesario.

### 9.3 Riesgo: Cyn no quiere ver impactos retrospectivos

**Probabilidad:** Baja, lo pidió explícitamente.
**Mitigación:** Permitir desactivar las notificaciones si no las quiere.

---

## 10. Decisiones pendientes

| # | Decisión | Opciones | Cuándo |
|---|----------|----------|--------|
| D1 | Algoritmo de similitud | A (embeddings) / B (heurística) / C (híbrido) | Sprint 1 con feedback |
| D2 | Threshold de similitud para mostrar | 0.6 / 0.75 / 0.85 | Sprint 2 con datos reales |
| D3 | Frecuencia de notificaciones | Cada login / diaria / semanal | Sprint 3 con feedback Cyn |
| D4 | Tipo de feedback estructurado vs libre | Solo categorías / categorías + nota | Sprint 3 |

---

## 11. Salidas de Etapa 3

Al cerrar Etapa 3:

- 2 migrations aplicadas
- 4 endpoints nuevos
- 3 componentes UI nuevos
- Job de cálculo automático de impactos
- Suite de tests completa
- Reporte de feedback de Cyn en primeras 4 semanas
- Documentación operativa

---

## 12. Cierre del SPEC W

Cuando Etapa 3 esté funcionando y mostrando valor medible (M1-M4), SPEC W se considera cerrado. A partir de ese momento:

- El sistema captura auditorías estructuradas (Etapa 1)
- Detecta patrones generalizables (Etapa 2)
- Muestra impacto a quien las hace (Etapa 3)

**Próximo nivel (fuera de SPEC W):** Aplicación automática de correcciones con threshold alto, integración con fine-tuning M-17, expansión a otros validadores.
