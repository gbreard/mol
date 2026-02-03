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
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │ ofertas  │────▶│ofertas_skills│◀────│   skills     │    │
│  └────┬─────┘     └──────────────┘     └──────────────┘    │
│       │                                                     │
│       ├───────────▶ empresas                                │
│       └───────────▶ ocupaciones_esco                        │
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

### ofertas

Ofertas validadas (desnormalizadas para dashboard).

```sql
CREATE TABLE ofertas (
    -- Identificadores
    id SERIAL PRIMARY KEY,
    id_oferta INTEGER UNIQUE NOT NULL,  -- FK lógica a SQLite

    -- Datos básicos
    titulo TEXT NOT NULL,
    titulo_limpio TEXT,
    empresa TEXT,
    empresa_id INTEGER REFERENCES empresas(id),
    descripcion TEXT,

    -- Ubicación (flat)
    provincia TEXT,
    localidad TEXT,
    modalidad TEXT CHECK (modalidad IN ('presencial', 'remoto', 'hibrido')),

    -- ESCO/ISCO
    isco_code TEXT,
    isco_label TEXT,
    esco_uri TEXT REFERENCES ocupaciones_esco(esco_uri),
    match_score DECIMAL(3,2),
    match_method TEXT,  -- regla/semantico/diccionario

    -- Condiciones
    salario_min INTEGER,
    salario_max INTEGER,
    moneda TEXT DEFAULT 'ARS',
    nivel_seniority TEXT,
    tipo_contrato TEXT,
    jornada TEXT,

    -- NLP extraído
    experiencia_min INTEGER,
    experiencia_max INTEGER,
    nivel_educativo TEXT,
    area_funcional TEXT,
    sector TEXT,

    -- Multi-tenant
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    visibilidad TEXT NOT NULL DEFAULT 'tenant'
        CHECK (visibilidad IN ('publico', 'tenant', 'privado')),

    -- Metadata
    fecha_publicacion TIMESTAMPTZ,
    fecha_sync TIMESTAMPTZ DEFAULT NOW(),
    validado_en TIMESTAMPTZ,
    source TEXT DEFAULT 'bumeran'
);

-- Índices
CREATE INDEX idx_ofertas_tenant ON ofertas(tenant_id);
CREATE INDEX idx_ofertas_visibilidad ON ofertas(visibilidad);
CREATE INDEX idx_ofertas_isco ON ofertas(isco_code);
CREATE INDEX idx_ofertas_provincia ON ofertas(provincia);
CREATE INDEX idx_ofertas_fecha ON ofertas(fecha_publicacion);
CREATE INDEX idx_ofertas_seniority ON ofertas(nivel_seniority);
CREATE INDEX idx_ofertas_modalidad ON ofertas(modalidad);
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

### ofertas_skills

Relación N:M entre ofertas y skills (normalizada).

```sql
CREATE TABLE ofertas_skills (
    id SERIAL PRIMARY KEY,
    id_oferta INTEGER NOT NULL REFERENCES ofertas(id_oferta) ON DELETE CASCADE,
    skill_uri TEXT NOT NULL REFERENCES skills(skill_uri) ON DELETE RESTRICT,

    -- Metadata
    score DECIMAL(3,2),  -- Confianza 0-1
    origen TEXT CHECK (origen IN ('regla', 'semantico', 'llm', 'merged')),
    es_esencial BOOLEAN,  -- Si es esencial para la ocupación

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(id_oferta, skill_uri)
);

-- Índices
CREATE INDEX idx_ofertas_skills_oferta ON ofertas_skills(id_oferta);
CREATE INDEX idx_ofertas_skills_skill ON ofertas_skills(skill_uri);
CREATE INDEX idx_ofertas_skills_origen ON ofertas_skills(origen);
```

### empresas

Catálogo de empresas (normalizado).

```sql
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    nombre_normalizado TEXT,  -- lowercase, sin acentos

    -- Clasificación
    sector TEXT,
    tamanio TEXT CHECK (tamanio IN ('micro', 'pequena', 'mediana', 'grande')),

    -- Estadísticas
    ofertas_count INTEGER DEFAULT 0,
    ofertas_activas INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_empresas_nombre ON empresas(nombre_normalizado);
CREATE INDEX idx_empresas_sector ON empresas(sector);
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
    id_oferta INTEGER REFERENCES ofertas(id_oferta),
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

### Políticas para ofertas

```sql
-- Habilitar RLS
ALTER TABLE ofertas ENABLE ROW LEVEL SECURITY;

-- Política de lectura: tenant ve lo suyo + públicos + OEDE ve todo
CREATE POLICY "ofertas_select" ON ofertas
    FOR SELECT USING (
        -- Mis datos (mismo tenant)
        tenant_id IN (
            SELECT tenant_id FROM tenant_users
            WHERE user_id = auth.uid()
        )
        -- O datos públicos
        OR visibilidad = 'publico'
        -- O soy OEDE (veo todo)
        OR EXISTS (
            SELECT 1 FROM tenant_users tu
            JOIN tenants t ON tu.tenant_id = t.id
            WHERE tu.user_id = auth.uid()
            AND t.tipo = 'oede'
        )
    );

-- Política de inserción: solo OEDE puede insertar
CREATE POLICY "ofertas_insert" ON ofertas
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM tenant_users tu
            JOIN tenants t ON tu.tenant_id = t.id
            WHERE tu.user_id = auth.uid()
            AND t.tipo = 'oede'
        )
    );

-- Política de update: solo OEDE puede actualizar
CREATE POLICY "ofertas_update" ON ofertas
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM tenant_users tu
            JOIN tenants t ON tu.tenant_id = t.id
            WHERE tu.user_id = auth.uid()
            AND t.tipo = 'oede'
        )
    );
```

### Políticas para ofertas_skills

```sql
ALTER TABLE ofertas_skills ENABLE ROW LEVEL SECURITY;

-- Hereda permisos de ofertas (si puedo ver la oferta, puedo ver sus skills)
CREATE POLICY "ofertas_skills_select" ON ofertas_skills
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM ofertas o
            WHERE o.id_oferta = ofertas_skills.id_oferta
        )
    );
```

### Políticas para tenants

```sql
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Usuarios ven solo su tenant (excepto OEDE)
CREATE POLICY "tenants_select" ON tenants
    FOR SELECT USING (
        id IN (
            SELECT tenant_id FROM tenant_users
            WHERE user_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1 FROM tenant_users tu
            JOIN tenants t ON tu.tenant_id = t.id
            WHERE tu.user_id = auth.uid()
            AND t.tipo = 'oede'
        )
    );
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
FROM ofertas
WHERE visibilidad IN ('publico', 'tenant');

-- Refrescar diariamente
-- SELECT cron.schedule('refresh_kpis', '0 6 * * *', 'REFRESH MATERIALIZED VIEW vw_kpis');
```

### vw_skills_demanda

```sql
CREATE MATERIALIZED VIEW vw_skills_demanda AS
SELECT
    s.preferred_label_es as skill,
    s.L1,
    s.L1_nombre,
    s.es_digital,
    COUNT(*) as ofertas_count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ofertas) as porcentaje
FROM ofertas_skills os
JOIN skills s ON os.skill_uri = s.skill_uri
GROUP BY s.skill_uri, s.preferred_label_es, s.L1, s.L1_nombre, s.es_digital
ORDER BY ofertas_count DESC;
```

### vw_distribucion_geografica

```sql
CREATE MATERIALIZED VIEW vw_distribucion_geografica AS
SELECT
    provincia,
    COUNT(*) as ofertas_count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ofertas) as porcentaje
FROM ofertas
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

1. **ofertas** ← JOIN de ofertas + ofertas_nlp + ofertas_esco_matching (solo validadas)
2. **skills** ← esco_skills (catálogo completo)
3. **ofertas_skills** ← Extraer de skills_oferta_json (JSON → filas)
4. **empresas** ← SELECT DISTINCT empresa FROM ofertas
5. **ocupaciones_esco** ← esco_occupations

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-02-03 | Versión inicial con multi-tenant |
