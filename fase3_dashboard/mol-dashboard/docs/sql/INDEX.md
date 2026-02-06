# SQL Migrations para MOL Dashboard

## Instrucciones

Ejecutar estos archivos SQL en **Supabase SQL Editor** en el orden indicado.

**URL:** https://supabase.com/dashboard/project/uywzoyhjjofsvvsrrnek/sql

---

## Orden de Ejecucion

### 1. Tablas Base (ya existentes)
- `ofertas_dashboard` ✅ (creada por sync_to_supabase.py)
- `ocupaciones_esco` ✅ (creada por sync_to_supabase.py)
- `ofertas_skills` ✅ (creada por sync_to_supabase.py)

### 2. Sistema de Issues
- `issues` ✅ (ya existe)
- `add_autor_nombre.sql` ✅ - Campo autor_nombre en issues

### 3. Estado del Sistema (Scraping/Pipeline)
- `sistema_estado.sql` ✅ - Estado de las 3 fases del pipeline

### 4. Logs y Auditoria
- `audit_logs.sql` ✅ - Tablas audit_log y eventos_uso

### 5. Vistas (crear si no existen)
- `vw_distribucion_isco.sql` - Vista para distribucion por ocupaciones

### 6. Perfiles (Opcional)
- `perfiles_trabajadores.sql` - Para feature futura

---

## Archivos SQL

| Archivo | Descripcion | Pagina que lo usa | Estado |
|---------|-------------|-------------------|--------|
| `add_autor_nombre.sql` | Columna autor_nombre en issues | IssueList, IssueForm | ✅ |
| `sistema_estado.sql` | Estado del pipeline | /admin/scraping, /admin/arquitectura | ✅ |
| `audit_logs.sql` | Logs de auditoria | /admin/logs | ✅ |
| `vw_distribucion_isco.sql` | Vista distribucion ISCO | /admin/metricas | ⏳ Crear |
| `perfiles_trabajadores.sql` | Perfiles trabajadores | /perfil-argentino (futuro) | ⏳ |

---

## Vistas Necesarias

### vw_distribucion_isco

Usada por `/admin/metricas` para mostrar Top 10 ocupaciones:

```sql
-- Crear vista de distribucion por ISCO
CREATE OR REPLACE VIEW vw_distribucion_isco AS
SELECT
  isco_code,
  isco_label,
  COUNT(*) as total
FROM ofertas_dashboard
WHERE isco_code IS NOT NULL
GROUP BY isco_code, isco_label
ORDER BY total DESC;
```

---

## Verificacion Post-Ejecucion

```sql
-- Verificar tablas creadas
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Verificar sistema_estado
SELECT * FROM sistema_estado ORDER BY timestamp DESC LIMIT 1;

-- Verificar audit_log
SELECT COUNT(*) FROM audit_log;

-- Verificar eventos_uso
SELECT COUNT(*) FROM eventos_uso;

-- Verificar vista distribucion ISCO
SELECT * FROM vw_distribucion_isco LIMIT 5;
```

---

## Sincronizacion desde SQLite

El archivo `sync_to_supabase.py` (v2.1.0) actualiza:
- `ofertas_dashboard` - Ofertas validadas
- `ofertas_skills` - Skills por oferta
- `ocupaciones_esco` - Catalogo ESCO
- `sistema_estado` - Metricas de las 3 fases del pipeline

---

## Estado de Tablas (Actualizado 2026-02-06)

| Tabla | Creada | Datos | Sincronizacion |
|-------|--------|-------|----------------|
| ofertas_dashboard | ✅ | 2093+ | sync_to_supabase.py |
| ocupaciones_esco | ✅ | 3000+ | sync_to_supabase.py |
| ofertas_skills | ✅ | 34917+ | sync_to_supabase.py |
| issues | ✅ | ~5 | Dashboard (manual) |
| sistema_estado | ✅ | 165+ | sync_to_supabase.py (v2.1) |
| audit_log | ✅ | 0 | Automatico (hooks) |
| eventos_uso | ✅ | 0 | Automatico (hooks) |
| vw_distribucion_isco | ⏳ | - | Vista SQL |

**Leyenda:** ✅ Listo | ⏳ Pendiente crear

---

## Dependencias entre Paginas y Datos

```
/admin/metricas
  └── ofertas_dashboard (count)
  └── ofertas_skills (count, group by L1)
  └── sistema_estado (fase2_con_nlp, fase2_validadas, etc.)
  └── vw_distribucion_isco (top 10 ocupaciones)

/admin/scraping
  └── sistema_estado (fase1_*)
  └── ofertas_dashboard (conteos por estado)

/admin/arquitectura
  └── api/admin/architecture-metrics (lee sistema_estado)
  └── dashboard_architecture.json (estatico)

/admin/logs
  └── audit_log
  └── eventos_uso

/admin/configuracion
  └── (sin backend - solo UI)
```
