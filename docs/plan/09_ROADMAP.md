# 9. Roadmap de Implementación

> Última actualización: 2026-02-07

## Referencias

| Documento | Relación |
|-----------|----------|
| [06_SEGURIDAD](./06_SEGURIDAD.md) | Fase 0 completa |
| [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) | Fase 1 |
| [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md) | Fases 2-4 |
| [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md) | Métricas de negocio |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Prioridades | Este documento |
| Issues resueltos | Marcar como completado aquí |
| Nuevos issues | Agregar a fase correspondiente |

---

## Visión General

```
FASE 0          FASE 1           FASE 2           FASE 3          FASE 4
Seguridad       Escalabilidad    Valor Datos      Features        Diferenciación
─────────────────────────────────────────────────────────────────────────────────►
                                                                             TIEMPO

[BLOQUEANTE]    [1 semana]       [2-3 semanas]    [4-6 semanas]   [2-3 meses]

- Tokens        - Paginación     - Backfill NLP   - Alertas       - ML Predict
- RLS           - Cache          - Validación     - Exports       - Salarios
- Open Redirect - Vistas SQL     - Salarios       - API           - Personaliz.
- Roles Admin   - Índices        - Tendencias     - Skills Gap    - Integrac.
```

---

## Fase 0: Seguridad (BLOQUEANTE)

**Estado:** 🔴 No iniciado
**Duración estimada:** 2-3 días
**Requisito:** Completar ANTES de cualquier otra fase

### Tareas

| ID | Tarea | Prioridad | Estado |
|----|-------|-----------|--------|
| S-01 | Rotar tokens expuestos | CRÍTICO | ⬜ |
| S-02 | Fix open redirect en callback | CRÍTICO | ⬜ |
| S-03 | Implementar RLS en tablas | CRÍTICO | ⬜ |
| S-04 | Verificar rol en APIs admin | CRÍTICO | ⬜ |
| S-07 | Headers de seguridad | ALTO | ⬜ |

### Checklist Pre-Fase-1

```
□ Tokens de Supabase rotados
□ .env* en .gitignore
□ Redirect validado contra whitelist
□ RLS activo en suscripciones, pagos, alertas
□ Middleware verifica rol admin
□ Headers de seguridad en next.config.js
```

### Criterio de Éxito

- 0 vulnerabilidades críticas
- Penetration test básico sin hallazgos graves

---

## Fase 1: Escalabilidad Básica

**Estado:** 🟡 En progreso (1/7 tareas completadas)
**Duración estimada:** 1 semana

### Tareas

| ID | Tarea | Prioridad | Estado |
|----|-------|-----------|--------|
| E-01 | Reemplazar .limit(10000) | CRÍTICO | ⬜ |
| E-02 | Usar vistas SQL existentes | CRÍTICO | ⬜ |
| E-03 | Implementar React Query | CRÍTICO | ⬜ |
| **E-16** | **Insights SQL (no fetchAllPaginated)** | **CRÍTICO** | ✅ Completado 2026-02-07 |
| E-05 | Agregar índices críticos | ALTO | ⬜ |
| S-05 | Rate limiting en APIs | ALTO | ⬜ |
| S-06 | Validación con Zod | ALTO | ⬜ |

> **E-16 Resuelto:** [12_INSIGHTS_SISTEMA](./12_INSIGHTS_SISTEMA.md) - Vistas SQL + función RPC `get_insights()` implementados

### Criterio de Éxito

| Métrica | Antes | Después |
|---------|-------|---------|
| Time to First Byte | ~800ms | < 400ms |
| Queries por página | ~10 | < 5 |
| Datos truncados | Sí | No |

---

## Fase 2: Valor de Datos

**Estado:** ⬜ Pendiente
**Duración estimada:** 2-3 semanas

### Tareas

| ID | Tarea | Prioridad | Estado |
|----|-------|-----------|--------|
| V-02 | Backfill NLP (13k ofertas) | CRÍTICO | ⬜ |
| V-01 | Acelerar validación | CRÍTICO | ⬜ |
| V-04 | Habilitar análisis salarios | CRÍTICO | ⬜ |
| V-07 | Gráficos tendencias | ALTO | ⬜ |

### Metas de Datos

| Métrica | Inicio | Meta |
|---------|--------|------|
| Ofertas con NLP | 49% | 80% |
| Ofertas validadas | 1% | 10% |
| Dashboard con salarios | No | Sí |

---

## Fase 3: Features Comerciales

**Estado:** ⬜ Pendiente
**Duración estimada:** 4-6 semanas

### Tareas

| ID | Tarea | Prioridad | Pantalla |
|----|-------|-----------|----------|
| V-05 | Alertas por email | ALTO | P-13 |
| V-09 | Export Excel/PDF | ALTO | P-12 |
| V-08 | API pública (Enterprise) | ALTO | Nueva |
| V-10 | Skills gap analysis | ALTO | Nueva |
| - | Checkout MercadoPago | ALTO | P-06, P-07, P-08 |
| - | Gestión suscripciones | ALTO | P-15 |

### Criterio de Éxito

| Métrica | Meta |
|---------|------|
| Features PRO funcionales | 5 |
| Usuarios PRO | 10 |
| MRR | $150k ARS |

---

## Fase 4: Diferenciación

**Estado:** ⬜ Pendiente
**Duración estimada:** 2-3 meses

### Tareas

| ID | Tarea | Descripción |
|----|-------|-------------|
| V-03 | ML Predictivo | Tendencias futuras de ocupaciones |
| V-06 | Comparador salarios | Por ocupación, provincia |
| V-14 | Dashboard personalizable | Widgets drag & drop |
| - | Integración LinkedIn | Import de perfil |

---

## Dependencias entre Fases

```mermaid
graph LR
    F0[Fase 0: Seguridad] --> F1[Fase 1: Escalabilidad]
    F0 --> F2[Fase 2: Datos]
    F1 --> F3[Fase 3: Features]
    F2 --> F3
    F3 --> F4[Fase 4: Diferenciación]
```

| Dependencia | Razón |
|-------------|-------|
| F0 → F1 | No escalar un sistema inseguro |
| F0 → F2 | Datos sensibles requieren RLS |
| F1 → F3 | Features necesitan performance |
| F2 → F3 | Features necesitan datos validados |
| F3 → F4 | Diferenciación sobre base sólida |

---

## Hitos y Releases

### MVP (Fase 0 + 1 + 2 parcial)

**Meta:** Sistema funcional con datos confiables

```
✓ Seguridad básica implementada
✓ Dashboard sin problemas de performance
✓ 10% ofertas validadas
✓ Análisis de salarios básico
```

### Release 1.0 (+ Fase 3)

**Meta:** Producto comercializable

```
✓ MercadoPago integrado
✓ Planes FREE/PRO funcionando
✓ Alertas y exports
✓ 10 usuarios PRO
```

### Release 2.0 (+ Fase 4)

**Meta:** Diferenciación de mercado

```
✓ Predicciones ML
✓ API para Enterprise
✓ 100 usuarios PRO
✓ 10 clientes Enterprise
```

---

## Métricas de Seguimiento

### Técnicas

| Métrica | Fase 0 | Fase 1 | Fase 2 | Fase 3 |
|---------|--------|--------|--------|--------|
| Vulnerabilidades críticas | 4→0 | 0 | 0 | 0 |
| Time to Interactive | 4s | 2s | 2s | 1.5s |
| Ofertas validadas | 1% | 1% | 10% | 20% |
| Uptime | N/A | 99% | 99% | 99.5% |

### Negocio

| Métrica | MVP | 6 meses | 1 año |
|---------|-----|---------|-------|
| Usuarios registrados | 100 | 1,000 | 5,000 |
| Usuarios PRO | 10 | 100 | 500 |
| MRR | $150k | $1.5M | $7.5M |
| Churn | <10% | <5% | <3% |

---

## Próximos Pasos Inmediatos

**ANTES de crear pantallas nuevas:**

1. ⚠️ **URGENTE:** Rotar tokens de Supabase expuestos en Git
2. ⚠️ **URGENTE:** Agregar `.env*` a `.gitignore`
3. ⚠️ **URGENTE:** Fix open redirect en `app/auth/callback/route.ts`

**DESPUÉS de asegurar:**

1. Implementar RLS básico en tablas
2. Crear las 13 páginas placeholder
3. Integrar MercadoPago
4. Acelerar pipeline de validación

---

## Notas de Planificación

- **No hay estimaciones de tiempo exactas** - Depende de recursos disponibles
- **Fases pueden solaparse** - Especialmente 2 y 3
- **Fase 0 es BLOQUEANTE** - No proceder sin completarla
- **Revisar este documento semanalmente** - Actualizar estados
