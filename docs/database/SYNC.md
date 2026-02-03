# Sincronización SQLite → Supabase

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
│  ofertas (desnormalizada)                                    │
│      ↓                                                       │
│  ofertas_skills (normalizada)                                │
│      ↓                                                       │
│  Dashboard Next.js                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Script Principal

**Ubicación:** `scripts/exports/sync_to_supabase.py`

### Uso

```bash
# Sync incremental (solo nuevas/modificadas)
python scripts/exports/sync_to_supabase.py

# Sync completo (todas las validadas)
python scripts/exports/sync_to_supabase.py --full

# Sync con tenant específico
python scripts/exports/sync_to_supabase.py --tenant oede

# Solo catálogos (skills, ocupaciones)
python scripts/exports/sync_to_supabase.py --catalogs-only
```

---

## Flujo de Sincronización

### Paso 1: Query SQLite

```sql
-- Ofertas validadas con todos sus datos
SELECT
    -- De ofertas
    o.id_oferta,
    o.titulo,
    o.empresa,
    o.localizacion,
    o.fecha_publicacion_iso,
    o.cantidad_vacantes,

    -- De ofertas_nlp
    n.titulo_limpio,
    n.provincia,
    n.localidad,
    n.modalidad,
    n.salario_min,
    n.salario_max,
    n.nivel_seniority,
    n.area_funcional,
    n.sector_empresa,
    n.experiencia_min_anios,
    n.experiencia_max_anios,
    n.nivel_educativo,

    -- De ofertas_esco_matching
    m.isco_code,
    m.esco_occupation_label as isco_label,
    m.esco_occupation_uri as esco_uri,
    m.occupation_match_score as match_score,
    m.decision_metodo as match_method,
    m.skills_oferta_json,
    m.estado_validacion,
    m.validado_timestamp

FROM ofertas o
JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
WHERE m.estado_validacion IN ('validado_claude', 'validado_humano')
```

### Paso 2: Transformación

```python
def transform_oferta(row: dict, tenant_id: str) -> dict:
    """Transforma una fila de SQLite a formato Supabase."""
    return {
        # Identificadores
        'id_oferta': row['id_oferta'],

        # Datos básicos
        'titulo': row['titulo'],
        'titulo_limpio': row['titulo_limpio'],
        'empresa': row['empresa'],

        # Ubicación
        'provincia': row['provincia'],
        'localidad': row['localidad'],
        'modalidad': row['modalidad'],

        # ESCO
        'isco_code': row['isco_code'],
        'isco_label': row['isco_label'],
        'esco_uri': row['esco_uri'],
        'match_score': row['match_score'],
        'match_method': row['match_method'],

        # Condiciones
        'salario_min': row['salario_min'],
        'salario_max': row['salario_max'],
        'nivel_seniority': row['nivel_seniority'],

        # NLP
        'experiencia_min': row['experiencia_min_anios'],
        'experiencia_max': row['experiencia_max_anios'],
        'nivel_educativo': row['nivel_educativo'],
        'area_funcional': row['area_funcional'],
        'sector': row['sector_empresa'],

        # Multi-tenant
        'tenant_id': tenant_id,
        'visibilidad': 'tenant',  # Por defecto solo visible para el tenant

        # Metadata
        'fecha_publicacion': row['fecha_publicacion_iso'],
        'validado_en': row['validado_timestamp'],
        'fecha_sync': datetime.now().isoformat()
    }
```

### Paso 3: Extracción de Skills

```python
def extract_skills(row: dict) -> list[dict]:
    """Extrae skills del JSON y los normaliza."""
    skills = []

    if row['skills_oferta_json']:
        skills_json = json.loads(row['skills_oferta_json'])

        for skill in skills_json:
            skills.append({
                'id_oferta': row['id_oferta'],
                'skill_uri': skill.get('uri'),
                'score': skill.get('score'),
                'origen': skill.get('origen', 'merged'),
                'es_esencial': skill.get('es_esencial', False)
            })

    return skills
```

### Paso 4: Upsert a Supabase

```python
def sync_to_supabase(ofertas: list, skills: list):
    """Sincroniza datos a Supabase con upsert."""

    # Upsert ofertas (on conflict id_oferta)
    supabase.table('ofertas').upsert(
        ofertas,
        on_conflict='id_oferta'
    ).execute()

    # Upsert skills (on conflict id_oferta, skill_uri)
    supabase.table('ofertas_skills').upsert(
        skills,
        on_conflict='id_oferta,skill_uri'
    ).execute()
```

---

## Mapeo de Campos

### ofertas (SQLite → Supabase)

| SQLite | Supabase | Transformación |
|--------|----------|----------------|
| `ofertas.id_oferta` | `id_oferta` | Directo |
| `ofertas.titulo` | `titulo` | Directo |
| `ofertas_nlp.titulo_limpio` | `titulo_limpio` | Directo |
| `ofertas.empresa` | `empresa` | Directo |
| `ofertas_nlp.provincia` | `provincia` | Directo |
| `ofertas_nlp.localidad` | `localidad` | Directo |
| `ofertas_nlp.modalidad` | `modalidad` | Normalizar a minúsculas |
| `ofertas_esco_matching.isco_code` | `isco_code` | Directo |
| `ofertas_esco_matching.esco_occupation_label` | `isco_label` | Directo |
| `ofertas_esco_matching.esco_occupation_uri` | `esco_uri` | Directo |
| `ofertas_esco_matching.occupation_match_score` | `match_score` | Directo |
| `ofertas_esco_matching.decision_metodo` | `match_method` | Directo |
| `ofertas_nlp.salario_min` | `salario_min` | Directo |
| `ofertas_nlp.salario_max` | `salario_max` | Directo |
| `ofertas_nlp.nivel_seniority` | `nivel_seniority` | Directo |
| `ofertas_nlp.experiencia_min_anios` | `experiencia_min` | Directo |
| `ofertas_nlp.experiencia_max_anios` | `experiencia_max` | Directo |
| `ofertas_nlp.nivel_educativo` | `nivel_educativo` | Directo |
| `ofertas_nlp.area_funcional` | `area_funcional` | Directo |
| `ofertas_nlp.sector_empresa` | `sector` | Directo |
| - | `tenant_id` | Parámetro de sync |
| - | `visibilidad` | Default 'tenant' |
| `ofertas.fecha_publicacion_iso` | `fecha_publicacion` | Directo |
| `ofertas_esco_matching.validado_timestamp` | `validado_en` | Directo |
| - | `fecha_sync` | NOW() |

### ofertas_skills (Extracción de JSON)

| SQLite JSON | Supabase | Transformación |
|-------------|----------|----------------|
| `skills_oferta_json[].uri` | `skill_uri` | Directo |
| `skills_oferta_json[].score` | `score` | Directo |
| `skills_oferta_json[].origen` | `origen` | Default 'merged' |
| `skills_oferta_json[].es_esencial` | `es_esencial` | Default false |

---

## Sincronización de Catálogos

### skills (esco_skills → skills)

```python
def sync_skills_catalog():
    """Sincroniza catálogo de skills de ESCO."""

    skills = sqlite.query("""
        SELECT
            skill_uri,
            preferred_label_es,
            description_es,
            -- Agregar L1/L2 si están disponibles
            skill_type
        FROM esco_skills
    """)

    supabase.table('skills').upsert(
        skills,
        on_conflict='skill_uri'
    ).execute()
```

### ocupaciones_esco (esco_occupations → ocupaciones_esco)

```python
def sync_occupations_catalog():
    """Sincroniza catálogo de ocupaciones ESCO."""

    ocupaciones = sqlite.query("""
        SELECT
            occupation_uri as esco_uri,
            isco_code,
            preferred_label_es,
            description_es,
            broader_occupation_uri as broader_uri,
            hierarchy_level
        FROM esco_occupations
    """)

    supabase.table('ocupaciones_esco').upsert(
        ocupaciones,
        on_conflict='esco_uri'
    ).execute()
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
    supabase_count = supabase.table('ofertas').select('count').execute().data[0]['count']

    if sqlite_count != supabase_count:
        raise ValueError(f"Mismatch: SQLite={sqlite_count}, Supabase={supabase_count}")

    # Validar skills
    sqlite_skills = sqlite.query("""
        SELECT COUNT(*) FROM ofertas_esco_skills_detalle
    """)[0][0]

    supabase_skills = supabase.table('ofertas_skills').select('count').execute().data[0]['count']

    return {
        'ofertas_sqlite': sqlite_count,
        'ofertas_supabase': supabase_count,
        'skills_sqlite': sqlite_skills,
        'skills_supabase': supabase_skills,
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
| `row level security` | Sin permisos | Verificar rol del usuario |

### Reintentos

```python
@retry(max_attempts=3, delay=5)
def sync_batch(ofertas: list):
    """Sincroniza un batch con reintentos."""
    try:
        supabase.table('ofertas').upsert(ofertas).execute()
    except Exception as e:
        log.error(f"Error en sync: {e}")
        raise
```

---

## Programación

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
- `metrics/sync_supabase_YYYYMMDD_HHMM.json` - Estadísticas
- `stdout` - Progreso en tiempo real

```json
{
    "timestamp": "2026-02-03T15:30:00",
    "ofertas_synced": 538,
    "skills_synced": 4338,
    "duration_seconds": 12.5,
    "errors": []
}
```

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-02-03 | Documentación inicial |
