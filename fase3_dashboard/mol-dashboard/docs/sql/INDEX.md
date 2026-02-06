# SQL Migrations para MOL Dashboard

## Instrucciones

Ejecutar estos archivos SQL en **Supabase SQL Editor** en el orden indicado.

**URL:** https://supabase.com/dashboard/project/uywzoyhjjofsvvsrrnek/sql

---

## Orden de Ejecución

### 1. Tablas Base (ya existentes)
- `ofertas_dashboard` ✅ (creada por sync_to_supabase.py)
- `ocupaciones_esco` ✅ (creada por sync_to_supabase.py)
- `ofertas_skills` ✅ (creada por sync_to_supabase.py)

### 2. Sistema de Issues
- `issues` ✅ (ya existe)
- `add_autor_nombre.sql` - Agregar campo autor_nombre a issues

### 3. Estado del Sistema (Scraping/Pipeline)
- `sistema_estado.sql` - Estado de las 3 fases del pipeline

### 4. Logs y Auditoría
- `audit_logs.sql` - Tablas audit_log y eventos_uso

### 5. Perfiles (Opcional)
- `perfiles_trabajadores.sql` - Para feature futura

---

## Archivos SQL

| Archivo | Descripción | Página que lo usa |
|---------|-------------|-------------------|
| `add_autor_nombre.sql` | Columna autor_nombre en issues | IssueList, IssueForm |
| `sistema_estado.sql` | Estado del pipeline | /admin/scraping |
| `audit_logs.sql` | Logs de auditoría | /admin/logs |
| `perfiles_trabajadores.sql` | Perfiles trabajadores | /perfil-argentino (futuro) |

---

## Verificación Post-Ejecución

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
```

---

## Sincronización desde SQLite

El archivo `sync_to_supabase.py` actualiza:
- `ofertas_dashboard` - Ofertas validadas
- `ofertas_skills` - Skills por oferta
- `ocupaciones_esco` - Catálogo ESCO

Para actualizar `sistema_estado`, agregar la función en sync_to_supabase.py:
```python
def sync_sistema_estado():
    # Calcular métricas desde SQLite local
    # Insertar en Supabase sistema_estado
    pass
```

---

## Estado de Tablas

| Tabla | Creada | Datos | Sincronización |
|-------|--------|-------|----------------|
| ofertas_dashboard | ✅ | 538+ | sync_to_supabase.py |
| ocupaciones_esco | ✅ | 3000+ | sync_to_supabase.py |
| ofertas_skills | ✅ | 4000+ | sync_to_supabase.py |
| issues | ✅ | ~5 | Dashboard (manual) |
| sistema_estado | ⏳ | 0 | sync_to_supabase.py (pendiente) |
| audit_log | ⏳ | 0 | Automático (hooks) |
| eventos_uso | ⏳ | 0 | Automático (hooks) |

**Leyenda:** ✅ Listo | ⏳ Pendiente ejecutar SQL
