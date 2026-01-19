# Sincronización con Supabase

## Descripción

Sistema de sincronización de ofertas validadas desde SQLite local hacia Supabase para alimentar el dashboard Next.js.

## Arquitectura

```
SCRAPING → NLP → MATCHING → VALIDACIÓN
                                ↓
                        estado_validacion = 'validado'
                                ↓
                    [MANUAL] sync_to_supabase.py
                                ↓
                           SUPABASE
                                ↓
                    DASHBOARD NEXT.JS (Vercel)
```

## Configuración

### 1. Credenciales

Archivo: `config/supabase_config.json`

```json
{
    "url": "https://xxx.supabase.co",
    "anon_key": "eyJ..."
}
```

**IMPORTANTE**: Este archivo está en `.gitignore`. No versionar.

### 2. Crear Schema en Supabase

1. Ir a Supabase Dashboard > SQL Editor
2. Copiar contenido de `scripts/exports/supabase_schema.sql`
3. Ejecutar

Esto crea:
- `ofertas` - Tabla principal desnormalizada
- `ofertas_skills` - Skills por oferta
- `esco_occupations` - Catálogo ocupaciones (subset)
- `esco_skills` - Catálogo skills (subset)
- Índices y vistas para el dashboard

### 3. Instalar dependencia

```bash
pip install supabase
```

## Uso

### Sync completo (todas las validadas)

```bash
python scripts/exports/sync_to_supabase.py
```

### Sync incremental (desde fecha)

```bash
python scripts/exports/sync_to_supabase.py --since 2026-01-15
```

### Sync ofertas específicas

```bash
python scripts/exports/sync_to_supabase.py --ids 123,456,789
```

### Preview sin escribir

```bash
python scripts/exports/sync_to_supabase.py --dry-run
```

### Ver estadísticas

```bash
python scripts/exports/sync_to_supabase.py --stats
```

## Flujo de Trabajo Semanal

1. **Pipeline procesa ofertas** (Scraping → NLP → Matching)
2. **Validar lote semanal** (200-500 ofertas)
   ```bash
   python scripts/validar_ofertas.py --ids X,Y,Z --estado validado
   ```
3. **Sincronizar a Supabase**
   ```bash
   python scripts/exports/sync_to_supabase.py --since [última fecha]
   ```
4. **Dashboard actualizado** automáticamente

## Datos Sincronizados

### Tabla `ofertas` (~50 campos)

| Grupo | Campos |
|-------|--------|
| **Scraping** | titulo, empresa, descripcion, localizacion, url, portal, fechas |
| **NLP** | area_funcional, seniority, modalidad, skills, salario, educacion |
| **Matching** | isco_code, esco_label, scores, método, validación |

### Tabla `ofertas_skills`

Skills extraídas con clasificación ESCO (L1, L2, es_digital).

### Catálogos ESCO

Solo el subset de ocupaciones y skills usadas en las ofertas.

## Escalabilidad

| Métrica | Valor |
|---------|-------|
| **Volumen semanal** | 200-500 ofertas |
| **Capacidad free tier** | ~50,000 ofertas |
| **Proyección** | 2-4 años en free tier |

## Troubleshooting

### Error: "Config no encontrado"

Crear `config/supabase_config.json` con URL y anon_key.

### Error: "supabase module not found"

```bash
pip install supabase
```

### Error: "relation does not exist"

Ejecutar el schema SQL en Supabase Dashboard.

### Error: "violates row-level security policy"

Verificar que las políticas RLS estén creadas (ver schema SQL).

## Vistas del Dashboard

El schema incluye vistas pre-calculadas:

- `vw_dashboard_metrics` - KPIs principales
- `vw_distribucion_isco` - Top ocupaciones
- `vw_distribucion_geografica` - Por provincia

## Seguridad

- **Lectura pública**: Dashboard puede leer sin autenticación
- **Escritura**: Solo desde script con anon_key
- **RLS activo**: Políticas de Row Level Security configuradas
