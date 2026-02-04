# Schema Supabase - Multi-Tenant

Base de datos: PostgreSQL (Supabase)
URL: `https://uywzoyhjjofsvvsrrnek.supabase.co`

---

## Principios de Diseño

1. **Desnormalizado para queries rápidas** - El dashboard necesita velocidad, no normalización perfecta
2. **Multi-tenant con RLS** - Row Level Security para aislar datos por organización
3. **Skills normalizados** - A diferencia de SQLite, aquí sí normalizamos para queries
4. **Registro abierto** - Cualquiera puede registrarse (decisión del usuario)

---

## Schema Completo

### Diagrama de Tablas

```
┌─────────────────────────────────────────────────────────────┐
│                      MULTI-TENANT                           │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │ tenants  │────▶│ tenant_users │◀────│  auth.users  │    │
│  └────┬─────┘     └──────────────┘     └──────────────┘    │
│       │                                                     │
└───────┼─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                         CORE                                │
│  ┌──────────────────┐   ┌──────────────┐   ┌──────────┐    │
│  │ ofertas_dashboard│──▶│ofertas_skills│◀──│  skills  │    │
│  └──────────────────┘   └──────────────┘   └──────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                      FEEDBACK                               │
│  ┌──────────┐                                               │
│  │  issues  │                                               │
│  └──────────┘                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Tablas Multi-Tenant

### tenants

Organizaciones que usan el sistema.

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('oede', 'empresa', 'gobierno', 'academico', 'publico')),
    config JSONB DEFAULT '{}',
    logo_url TEXT,
    dominio TEXT,  -- Para SSO futuro
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- OEDE es tenant especial que ve todo
INSERT INTO tenants (id, nombre, tipo)
VALUES ('00000000-0000-0000-0000-000000000001', 'OEDE', 'oede');

-- Índices
CREATE INDEX idx_tenants_tipo ON tenants(tipo);
CREATE INDEX idx_tenants_activo ON tenants(activo);
```

### tenant_users

Relación usuarios-organizaciones con roles.

```sql
CREATE TYPE user_role AS ENUM ('admin', 'analyst', 'viewer');

CREATE TABLE tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'viewer',
    invited_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, user_id)
);

-- Índices
CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user ON tenant_users(user_id);
```

---

## Tablas Core

### ofertas_dashboard

Ofertas validadas (desnormalizadas para dashboard).

**IMPORTANTE:** Esta tabla recibe datos JOIN de 3 tablas SQLite:
- `ofertas` (scraping)
- `ofertas_nlp` (extracción NLP)
- `ofertas_esco_matching` (matching ESCO)

```sql
CREATE TABLE ofertas_dashboard (
    -- Identificadores
    id_oferta TEXT PRIMARY KEY,

    -- Datos básicos (de scraping)
    titulo TEXT NOT NULL,
    titulo_limpio TEXT,
    empresa TEXT,
    url TEXT,
    portal TEXT,
    fecha_publicacion TIMESTAMPTZ,

    -- Ubicación (de NLP)
    provincia TEXT,
    localidad TEXT,
    modalidad TEXT,  -- presencial, remoto, hibrido

    -- ESCO/ISCO (de matching)
    esco_occupation_uri TEXT,
    esco_occupation_label TEXT,
    isco_code TEXT,
    isco_label TEXT,
    occupation_match_score DECIMAL(3,2),
    occupation_match_method TEXT,  -- regla_prioridad, semantico_default

    -- Condiciones laborales (de NLP)
    salario_min INTEGER,
    salario_max INTEGER,
    moneda TEXT DEFAULT 'ARS',
    nivel_seniority TEXT,

    -- Requerimientos (de NLP)
    experiencia_min_anios INTEGER,
    nivel_educativo TEXT,
    tiene_gente_cargo BOOLEAN,
    jornada_laboral TEXT,  -- full-time, part-time, freelance
    area_funcional TEXT,
    sector_empresa TEXT,

    -- Skills (arrays JSON para backward compatibility)
    skills_tecnicas JSONB,  -- JSON array
    soft_skills JSONB,      -- JSON array

    -- Metadata
    estado TEXT DEFAULT 'activa',
    fecha_sync TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_ofertas_dashboard_isco ON ofertas_dashboard(isco_code);
CREATE INDEX idx_ofertas_dashboard_provincia ON ofertas_dashboard(provincia);
CREATE INDEX idx_ofertas_dashboard_fecha ON ofertas_dashboard(fecha_publicacion);
CREATE INDEX idx_ofertas_dashboard_seniority ON ofertas_dashboard(nivel_seniority);
CREATE INDEX idx_ofertas_dashboard_modalidad ON ofertas_dashboard(modalidad);
```

### ofertas_skills

Relación N:M entre ofertas y skills (normalizada para queries).

```sql
CREATE TABLE ofertas_skills (
    id SERIAL PRIMARY KEY,
    id_oferta TEXT NOT NULL REFERENCES ofertas_dashboard(id_oferta) ON DELETE CASCADE,
    skill_uri TEXT NOT NULL,

    -- Datos del skill (desnormalizados para evitar JOINs)
    preferred_label TEXT,

    -- Categorización ESCO
    l1 TEXT,             -- Código L1 (ej: "S1")
    l1_nombre TEXT,      -- Nombre L1 (ej: "Communication")
    l2 TEXT,             -- Código L2
    l2_nombre TEXT,      -- Nombre L2
    es_digital BOOLEAN DEFAULT false,

    -- Metadata matching
    score DECIMAL(3,2),  -- Confianza 0-1
    origen TEXT CHECK (origen IN ('titulo', 'tareas', 'descripcion', 'semantico', 'regla', 'llm', 'merged')),
    es_esencial BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(id_oferta, skill_uri)
);

-- Índices
CREATE INDEX idx_ofertas_skills_oferta ON ofertas_skills(id_oferta);
CREATE INDEX idx_ofertas_skills_skill ON ofertas_skills(skill_uri);
CREATE INDEX idx_ofertas_skills_l1 ON ofertas_skills(l1);
CREATE INDEX idx_ofertas_skills_digital ON ofertas_skills(es_digital);
```

### skills

Catálogo de skills (copia de ESCO + custom).

```sql
CREATE TABLE skills (
    skill_uri TEXT PRIMARY KEY,
    preferred_label_es TEXT NOT NULL,
    description_es TEXT,

    -- Categorización ESCO
    L1 TEXT,           -- Código L1 (ej: "S1")
    L1_nombre TEXT,    -- Nombre L1 (ej: "Communication")
    L2 TEXT,           -- Código L2
    L2_nombre TEXT,    -- Nombre L2

    -- Clasificación
    skill_type TEXT CHECK (skill_type IN ('skill', 'knowledge', 'attitude')),
    es_digital BOOLEAN DEFAULT false,

    -- Metadata
    source TEXT DEFAULT 'esco',  -- esco/custom
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_skills_l1 ON skills(L1);
CREATE INDEX idx_skills_l2 ON skills(L2);
CREATE INDEX idx_skills_digital ON skills(es_digital);
CREATE INDEX idx_skills_label ON skills(preferred_label_es);
```

### ocupaciones_esco

Catálogo de ocupaciones ESCO (copia de SQLite).

```sql
CREATE TABLE ocupaciones_esco (
    esco_uri TEXT PRIMARY KEY,
    isco_code TEXT NOT NULL,
    preferred_label_es TEXT NOT NULL,
    description_es TEXT,

    -- Jerarquía
    broader_uri TEXT REFERENCES ocupaciones_esco(esco_uri),
    hierarchy_level INTEGER,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_ocupaciones_isco ON ocupaciones_esco(isco_code);
```

---

## Tablas de Feedback

### issues

Feedback de usuarios del dashboard.

```sql
CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Contexto
    id_oferta TEXT REFERENCES ofertas_dashboard(id_oferta),
    tenant_id UUID REFERENCES tenants(id),

    -- Contenido
    titulo TEXT NOT NULL,
    descripcion TEXT,
    tipo TEXT NOT NULL CHECK (tipo IN (
        'error_isco', 'error_nlp', 'error_skill',
        'sugerencia', 'bug', 'otro'
    )),

    -- Estado
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN (
        'pendiente', 'en_revision', 'resuelto', 'rechazado'
    )),
    prioridad TEXT DEFAULT 'media' CHECK (prioridad IN (
        'baja', 'media', 'alta', 'critica'
    )),

    -- Tracking
    autor_id UUID REFERENCES auth.users(id),
    autor_email TEXT,
    resuelto_por TEXT,
    resuelto_at TIMESTAMPTZ,
    solucion_aplicada TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_issues_estado ON issues(estado);
CREATE INDEX idx_issues_tipo ON issues(tipo);
CREATE INDEX idx_issues_oferta ON issues(id_oferta);
```

---

## Row Level Security (RLS)

### Políticas para ofertas_dashboard

```sql
-- Habilitar RLS
ALTER TABLE ofertas_dashboard ENABLE ROW LEVEL SECURITY;

-- Política de lectura: todos pueden leer (datos públicos)
CREATE POLICY "ofertas_select" ON ofertas_dashboard
    FOR SELECT USING (true);

-- Política de inserción: solo service_role puede insertar
CREATE POLICY "ofertas_insert" ON ofertas_dashboard
    FOR INSERT WITH CHECK (
        auth.role() = 'service_role'
    );

-- Política de update: solo service_role puede actualizar
CREATE POLICY "ofertas_update" ON ofertas_dashboard
    FOR UPDATE USING (
        auth.role() = 'service_role'
    );
```

### Políticas para ofertas_skills

```sql
ALTER TABLE ofertas_skills ENABLE ROW LEVEL SECURITY;

-- Lectura pública
CREATE POLICY "ofertas_skills_select" ON ofertas_skills
    FOR SELECT USING (true);

-- Escritura solo service_role
CREATE POLICY "ofertas_skills_insert" ON ofertas_skills
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
```

---

## Vistas Materializadas

Para queries frecuentes del dashboard.

### vw_kpis

```sql
CREATE MATERIALIZED VIEW vw_kpis AS
SELECT
    COUNT(*) as total_ofertas,
    COUNT(DISTINCT empresa) as total_empresas,
    COUNT(DISTINCT isco_code) as total_ocupaciones,
    AVG(salario_min) as salario_promedio_min,
    AVG(salario_max) as salario_promedio_max,
    COUNT(*) FILTER (WHERE modalidad = 'remoto') as ofertas_remotas,
    COUNT(*) FILTER (WHERE fecha_publicacion > NOW() - INTERVAL '7 days') as ofertas_semana
FROM ofertas_dashboard;
```

### vw_skills_demanda

```sql
CREATE MATERIALIZED VIEW vw_skills_demanda AS
SELECT
    os.preferred_label as skill,
    os.l1,
    os.l1_nombre,
    os.es_digital,
    COUNT(*) as ofertas_count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ofertas_dashboard) as porcentaje
FROM ofertas_skills os
GROUP BY os.preferred_label, os.l1, os.l1_nombre, os.es_digital
ORDER BY ofertas_count DESC;
```

### vw_distribucion_geografica

```sql
CREATE MATERIALIZED VIEW vw_distribucion_geografica AS
SELECT
    provincia,
    COUNT(*) as ofertas_count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ofertas_dashboard) as porcentaje
FROM ofertas_dashboard
WHERE provincia IS NOT NULL
GROUP BY provincia
ORDER BY ofertas_count DESC;
```

---

## Funciones Auxiliares

### get_user_tenant()

```sql
CREATE OR REPLACE FUNCTION get_user_tenant()
RETURNS UUID AS $$
    SELECT tenant_id FROM tenant_users
    WHERE user_id = auth.uid()
    LIMIT 1;
$$ LANGUAGE SQL SECURITY DEFINER;
```

### is_oede_user()

```sql
CREATE OR REPLACE FUNCTION is_oede_user()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM tenant_users tu
        JOIN tenants t ON tu.tenant_id = t.id
        WHERE tu.user_id = auth.uid()
        AND t.tipo = 'oede'
    );
$$ LANGUAGE SQL SECURITY DEFINER;
```

---

## Migración desde SQLite

Script de migración en `scripts/exports/sync_to_supabase.py`:

1. **ofertas_dashboard** ← JOIN de ofertas + ofertas_nlp + ofertas_esco_matching (solo validadas)
2. **ofertas_skills** ← Extracción de ofertas_esco_skills_detalle (normalizado)
3. **skills** (opcional) ← esco_skills (catálogo completo)
4. **ocupaciones_esco** (opcional) ← esco_occupations

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-02-04 | Actualizar schema a implementación real (ofertas_dashboard, ofertas_skills con preferred_label) |
| 2026-02-03 | Versión inicial con multi-tenant |
