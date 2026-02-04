# Sincronizacion SQLite → Supabase

## Arquitectura de Datos

```
┌─────────────────────────────────────────────────────────────┐
│                    SQLITE LOCAL                              │
│                                                              │
│  ofertas (13K+)                                              │
│      ↓                                                       │
│  ofertas_nlp (NLP v11.3)                                     │
│      ↓                                                       │
│  ofertas_esco_matching (Matching v3.4.2)                     │
│      │                                                       │
│      └── estado_validacion IN ('validado_claude',            │
│                                'validado_humano')            │
│                    ↓                                         │
│              FILTRO: ~1K ofertas                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │  sync_to_supabase.py
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE CLOUD                            │
│                                                              │
│  ofertas_dashboard (desnormalizada)                          │
│      ↓                                                       │
│  ofertas_skills (normalizada, con L1/L2)                     │
│      ↓                                                       │
│  Dashboard Next.js                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Script Principal

**Ubicación:** `scripts/exports/sync_to_supabase.py`

### Uso

```bash
# Sync todas las validadas
python scripts/exports/sync_to_supabase.py

# Sync completo (fuerza recarga)
python scripts/exports/sync_to_supabase.py --full

# Solo ofertas específicas
python scripts/exports/sync_to_supabase.py --ids 123,456

# Preview sin escribir
python scripts/exports/sync_to_supabase.py --dry-run

# Ver estadísticas actuales
python scripts/exports/sync_to_supabase.py --stats

# Solo catálogos ESCO
python scripts/exports/sync_to_supabase.py --catalogs-only
```

---

## Flujo de Sincronizacion

### Paso 1: Query SQLite (JOIN 3 tablas)

```sql
SELECT
    -- De ofertas (scraping)
    o.id_oferta,
    o.titulo,
    o.empresa,
    o.url_oferta,
    o.portal,
    o.fecha_publicacion_iso,
    o.provincia_normalizada,
    o.localidad_normalizada,
    o.estado_oferta,

    -- De ofertas_nlp (extracción NLP)
    n.titulo_limpio,
    n.provincia,
    n.localidad,
    n.modalidad,
    n.nivel_seniority,
    n.area_funcional,
    n.sector_empresa,
    n.salario_min,
    n.salario_max,
    n.experiencia_min_anios,
    n.nivel_educativo,
    n.tiene_gente_cargo,
    n.jornada_laboral,
    n.skills_tecnicas_list,
    n.soft_skills_list,

    -- De ofertas_esco_matching (matching)
    m.esco_occupation_uri,
    m.esco_occupation_label,
    m.isco_code,
    m.isco_label,
    m.occupation_match_score,
    m.occupation_match_method,
    m.estado_validacion,
    m.validado_timestamp

FROM ofertas o
INNER JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
INNER JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
WHERE m.estado_validacion IN ('validado_claude', 'validado_humano')
ORDER BY m.validado_timestamp DESC
```

### Paso 2: Transformación (transform_oferta_for_supabase)

```python
def transform_oferta_for_supabase(oferta: Dict) -> Dict:
    """Transforma una oferta de SQLite al formato de ofertas_dashboard."""
    return {
        'id_oferta': str(oferta.get('id_oferta')),
        'titulo': oferta.get('titulo'),
        'titulo_limpio': oferta.get('titulo_limpio'),
        'empresa': oferta.get('empresa'),
        'fecha_publicacion': oferta.get('fecha_publicacion_iso'),
        'url': oferta.get('url_oferta'),
        'portal': oferta.get('portal'),

        # Ubicación (prioriza NLP sobre scraping)
        'provincia': oferta.get('provincia') or oferta.get('provincia_normalizada'),
        'localidad': oferta.get('localidad') or oferta.get('localidad_normalizada'),

        # ESCO/ISCO
        'esco_occupation_uri': oferta.get('esco_occupation_uri'),
        'esco_occupation_label': oferta.get('esco_occupation_label'),
        'isco_code': oferta.get('isco_code'),
        'isco_label': oferta.get('esco_occupation_label') or oferta.get('isco_label'),
        'occupation_match_score': oferta.get('occupation_match_score'),
        'occupation_match_method': oferta.get('occupation_match_method'),

        # NLP
        'modalidad': oferta.get('modalidad'),
        'nivel_seniority': oferta.get('nivel_seniority'),
        'area_funcional': oferta.get('area_funcional'),
        'sector_empresa': oferta.get('sector_empresa'),

        # Salarios
        'salario_min': oferta.get('salario_min'),
        'salario_max': oferta.get('salario_max'),
        'moneda': oferta.get('moneda'),

        # Requerimientos
        'nivel_educativo': oferta.get('nivel_educativo'),
        'experiencia_min_anios': oferta.get('experiencia_min_anios'),
        'tiene_gente_cargo': oferta.get('tiene_gente_cargo'),
        'jornada_laboral': oferta.get('jornada_laboral'),

        # Skills (JSONB)
        'skills_tecnicas': oferta.get('skills_tecnicas_list'),
        'soft_skills': oferta.get('soft_skills_list'),

        # Estado
        'estado': oferta.get('estado_oferta', 'activa'),
        'fecha_sync': datetime.now().isoformat(),
    }
```

### Paso 3: Extracción de Skills (ofertas_esco_skills_detalle)

```python
def transform_skill_for_supabase(skill: Dict) -> Dict:
    """Transforma un skill de SQLite al formato de ofertas_skills."""
    return {
        'id_oferta': str(skill.get('id_oferta')),
        'skill_uri': skill.get('esco_skill_uri'),
        'preferred_label': skill.get('esco_skill_label'),
        'l1': skill.get('l1'),
        'l1_nombre': skill.get('l1_nombre'),
        'l2': skill.get('l2'),
        'l2_nombre': skill.get('l2_nombre'),
        'es_digital': skill.get('es_digital', False),
        'origen': skill.get('skill_tipo_fuente', 'merged'),
        'score': skill.get('match_score'),
        'es_esencial': skill.get('es_esencial', False),
    }
```

### Paso 4: Upsert a Supabase

```python
def sync_to_supabase(ofertas: list, skills: list):
    """Sincroniza datos a Supabase con upsert."""

    # Upsert ofertas (on conflict id_oferta)
    supabase.table('ofertas_dashboard').upsert(
        ofertas,
        on_conflict='id_oferta'
    ).execute()

    # Para skills: delete + insert por oferta (evita duplicados)
    for offer_id in offer_ids:
        supabase.table('ofertas_skills').delete().eq('id_oferta', offer_id).execute()

    supabase.table('ofertas_skills').upsert(
        skills,
        on_conflict='id_oferta,skill_uri'
    ).execute()
```

---

## Mapeo de Campos

### ofertas_dashboard (SQLite → Supabase)

| SQLite | Supabase | Notas |
|--------|----------|-------|
| `ofertas.id_oferta` | `id_oferta` | Convertido a TEXT |
| `ofertas.titulo` | `titulo` | Directo |
| `ofertas_nlp.titulo_limpio` | `titulo_limpio` | Directo |
| `ofertas.empresa` | `empresa` | Directo |
| `ofertas.url_oferta` | `url` | Renombrado |
| `ofertas.portal` | `portal` | Directo |
| `ofertas.fecha_publicacion_iso` | `fecha_publicacion` | Renombrado |
| `ofertas_nlp.provincia` | `provincia` | Prioriza NLP |
| `ofertas_nlp.localidad` | `localidad` | Prioriza NLP |
| `ofertas_nlp.modalidad` | `modalidad` | Directo |
| `ofertas_esco_matching.esco_occupation_uri` | `esco_occupation_uri` | Directo |
| `ofertas_esco_matching.esco_occupation_label` | `esco_occupation_label` | Directo |
| `ofertas_esco_matching.isco_code` | `isco_code` | Directo |
| `ofertas_esco_matching.esco_occupation_label` | `isco_label` | Usa esco_label |
| `ofertas_esco_matching.occupation_match_score` | `occupation_match_score` | Directo |
| `ofertas_esco_matching.occupation_match_method` | `occupation_match_method` | Directo |
| `ofertas_nlp.salario_min` | `salario_min` | Directo |
| `ofertas_nlp.salario_max` | `salario_max` | Directo |
| - | `moneda` | Hardcoded 'ARS' |
| `ofertas_nlp.nivel_seniority` | `nivel_seniority` | Directo |
| `ofertas_nlp.experiencia_min_anios` | `experiencia_min_anios` | Directo |
| `ofertas_nlp.nivel_educativo` | `nivel_educativo` | Directo |
| `ofertas_nlp.tiene_gente_cargo` | `tiene_gente_cargo` | Boolean |
| `ofertas_nlp.jornada_laboral` | `jornada_laboral` | Directo |
| `ofertas_nlp.area_funcional` | `area_funcional` | Directo |
| `ofertas_nlp.sector_empresa` | `sector_empresa` | Directo |
| `ofertas_nlp.skills_tecnicas_list` | `skills_tecnicas` | JSON array |
| `ofertas_nlp.soft_skills_list` | `soft_skills` | JSON array |
| `ofertas.estado_oferta` | `estado` | Default 'activa' |
| - | `fecha_sync` | NOW() |

### ofertas_skills (Extracción de ofertas_esco_skills_detalle)

| SQLite | Supabase | Notas |
|--------|----------|-------|
| `id_oferta` | `id_oferta` | TEXT |
| `esco_skill_uri` | `skill_uri` | URI ESCO |
| `esco_skill_label` | `preferred_label` | **IMPORTANTE: columna renombrada** |
| `source_classification.L1` | `l1` | Extraido de JSON |
| `source_classification.L1_nombre` | `l1_nombre` | Extraido de JSON |
| `source_classification.L2` | `l2` | Extraido de JSON |
| `source_classification.L2_nombre` | `l2_nombre` | Extraido de JSON |
| `source_classification.es_digital` | `es_digital` | Boolean |
| `skill_tipo_fuente` | `origen` | titulo/tareas/semantico/etc |
| `match_score` | `score` | Decimal 0-1 |
| - | `es_esencial` | Default false |

---

## Paginacion en el Dashboard

**IMPORTANTE:** Supabase tiene un límite de 1000 filas por query.

El dashboard (`lib/supabase.ts`) usa paginación automática:

```typescript
async function fetchAllPaginated<T>(
  client: any,
  table: string,
  selectFields: string,
  buildQuery: (query: any) => any
): Promise<T[]> {
  const PAGE_SIZE = 1000
  let allData: T[] = []
  let offset = 0
  let hasMore = true

  while (hasMore) {
    let query = client.from(table).select(selectFields)
    query = buildQuery(query)
    query = query.range(offset, offset + PAGE_SIZE - 1)

    const { data, error } = await query
    if (error) throw error

    if (data && data.length > 0) {
      allData = allData.concat(data)
      if (data.length < PAGE_SIZE) {
        hasMore = false
      } else {
        offset += PAGE_SIZE
      }
    } else {
      hasMore = false
    }
  }

  return allData
}
```

---

## Validación Post-Sync

```python
def validate_sync():
    """Valida que el sync fue exitoso."""

    # Contar en SQLite
    sqlite_count = sqlite.query("""
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE estado_validacion IN ('validado_claude', 'validado_humano')
    """)[0][0]

    # Contar en Supabase
    supabase_count = supabase.table('ofertas_dashboard').select('count').execute().data[0]['count']

    return {
        'ofertas_sqlite': sqlite_count,
        'ofertas_supabase': supabase_count,
        'match': sqlite_count == supabase_count
    }
```

---

## Manejo de Errores

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `duplicate key value` | Oferta ya existe | Usar upsert en lugar de insert |
| `foreign key violation` | skill_uri no existe | Sync catálogos primero |
| `null value in column` | Campo requerido vacío | Agregar defaults o filtrar |
| `row level security` | Sin permisos | Verificar service_role key |
| `limit 1000 rows` | Límite por defecto | Usar paginación |

### Reintentos

```python
@retry(max_attempts=3, delay=5)
def sync_batch(ofertas: list):
    """Sincroniza un batch con reintentos."""
    try:
        supabase.table('ofertas_dashboard').upsert(ofertas).execute()
    except Exception as e:
        log.error(f"Error en sync: {e}")
        raise
```

---

## Programacion

### Sync Manual

```bash
# Después de validar ofertas
python scripts/run_validated_pipeline.py --limit 100
python scripts/exports/sync_to_supabase.py
```

### Sync Automático (futuro)

```bash
# Cron job cada 6 horas
0 */6 * * * cd /path/to/project && python scripts/exports/sync_to_supabase.py >> /var/log/sync.log 2>&1
```

---

## Logs

El script genera logs en:
- `config/supabase_sync_log.json` - Historial de syncs
- `stdout` - Progreso en tiempo real

Ejemplo de log:

```json
{
    "timestamp": "2026-02-04T15:30:00",
    "ofertas_synced": 1026,
    "skills_synced": 15309,
    "duration_seconds": 45.2,
    "errors": []
}
```

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-02-04 | Agregar columnas requerimientos, paginación dashboard, actualizar mapeo real |
| 2026-02-03 | Documentación inicial |
