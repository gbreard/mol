# Plan: /admin/configuracion

## Estado Actual: Fase 1 (Solo Lectura) ✅

Implementado 2026-02-06

## Fases Planificadas

### Fase 1: Informativo (COMPLETADA)
**Solo lectura - sin backend de escritura**

| Sección | Datos mostrados |
|---------|-----------------|
| Estado Sistema | Conteos Supabase (ofertas, skills, ocupaciones) |
| Conexión Supabase | URL, estado conexión, último sync |
| Pipeline | Métricas de sistema_estado (NLP, Matching, Validación) |
| Scraping | Última ejecución, días desde scraping |
| Seguridad | Estado auth, usuarios registrados |

**Características:**
- Badge "Solo lectura" visible
- Sin botón guardar (evita confusión)
- Datos en tiempo real de Supabase
- Auto-refresh cada 30 segundos (opcional)

---

### Fase 2: Funcional Básico (PENDIENTE)
**Lectura + escritura de configs simples**

| Acción | Implementación |
|--------|----------------|
| Trigger sync manual | Botón → llama sync_to_supabase.py via API |
| Editar umbrales | Formulario → actualiza matching_config.json |
| Limpiar caché | Botón → endpoint de limpieza |

**Requiere:**
- API route `/api/admin/config` (GET/POST)
- Tabla `configuracion` en Supabase (key-value)
- Validación de permisos (solo superadmin)

**Riesgos:**
- Configs locales (JSON) vs Supabase: decidir source of truth
- Sincronización bidireccional compleja
- Posible inconsistencia entre ambientes

---

### Fase 3: Completo (FUTURO)
**Todas las operaciones administrativas**

| Sección | Operaciones |
|---------|-------------|
| BD Local | Backup, restore, vacuum |
| Supabase | Migrar datos, reset tablas |
| Scraping | Start/stop scrapers, editar schedule |
| Notificaciones | Email/Slack cuando hay errores |
| Seguridad | 2FA, API keys, audit log |
| Apariencia | Temas, logos, colores |

**Requiere:**
- Backend Python con endpoints REST
- Sistema de jobs/cron
- Integración con servicios externos
- UI compleja con formularios

---

## Recomendación

| Fase | Esfuerzo | Valor | Prioridad |
|------|----------|-------|-----------|
| 1 | Bajo | Alto | ✅ HECHO |
| 2 | Medio | Medio | Cuando se necesite editar configs |
| 3 | Alto | Variable | Solo si hay demanda real |

**Consejo:** Mantener Fase 1 mientras el equipo sea pequeño. Las configs se editan mejor directamente en los JSON + git para tener historial.

---

## Archivos Relacionados

- `app/admin/configuracion/page.tsx` - Página actual (Fase 1)
- `public/data/dashboard_architecture.json` - Documentación arquitectura
- `lib/supabase.ts` - Cliente Supabase
