# Schema de Usuarios y Preferencias

**Fecha**: 2026-01-17
**Version**: 1.0

---

## 1. Modelo de Datos

```
organizaciones (tenants)
    │
    └── usuarios (profiles)
            │
            ├── busquedas_guardadas
            ├── intereses
            └── alertas
```

---

## 2. Tablas

### 2.1 Organizaciones

```sql
CREATE TABLE organizaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    tipo TEXT CHECK (tipo IN ('gobierno', 'universidad', 'empresa', 'ong', 'otro')),
    jurisdiccion TEXT,  -- 'nacional', 'CABA', 'Buenos Aires', etc.
    activa BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Ejemplos:
-- ('OEDE', 'gobierno', 'nacional')
-- ('Observatorio Córdoba', 'gobierno', 'Córdoba')
-- ('Universidad de Buenos Aires', 'universidad', 'CABA')
```

### 2.2 Usuarios (extiende auth.users de Supabase)

```sql
CREATE TABLE usuarios (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    organizacion_id UUID REFERENCES organizaciones(id),
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT NOT NULL,
    rol TEXT DEFAULT 'analista' CHECK (rol IN ('admin', 'analista', 'lector')),
    activo BOOLEAN DEFAULT true,
    ultimo_acceso TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 2.3 Busquedas Guardadas

```sql
CREATE TABLE busquedas_guardadas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,  -- "Desarrolladores en CABA"
    filtros JSONB NOT NULL,  -- {"provincia": "CABA", "isco_code": "2512", ...}
    descripcion TEXT,
    es_publica BOOLEAN DEFAULT false,  -- compartir con organizacion
    veces_usada INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Ejemplo filtros:
-- {
--   "provincia": "CABA",
--   "isco_codes": ["2512", "2511"],
--   "modalidad": "remoto",
--   "seniority": ["senior", "semisenior"],
--   "periodo": {"desde": "2026-01-01", "hasta": "2026-01-31"}
-- }
```

### 2.4 Intereses (seguimiento de ocupaciones/skills)

```sql
CREATE TABLE intereses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('ocupacion', 'skill', 'sector', 'empresa')),
    valor TEXT NOT NULL,  -- isco_code, skill_name, sector, empresa
    etiqueta TEXT,  -- nombre amigable
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Ejemplos:
-- ('ocupacion', '2512', 'Desarrolladores de software', NULL)
-- ('skill', 'python', 'Python', 'Seguir demanda de Python')
-- ('sector', 'fintech', 'Fintech', NULL)
```

### 2.5 Alertas

```sql
CREATE TABLE alertas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('nuevas_ofertas', 'cambio_tendencia', 'umbral')),
    condiciones JSONB NOT NULL,  -- criterios que disparan la alerta
    frecuencia TEXT DEFAULT 'diaria' CHECK (frecuencia IN ('inmediata', 'diaria', 'semanal')),
    canal TEXT DEFAULT 'email' CHECK (canal IN ('email', 'dashboard', 'ambos')),
    activa BOOLEAN DEFAULT true,
    ultima_ejecucion TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Ejemplo condiciones:
-- {
--   "tipo": "nuevas_ofertas",
--   "filtros": {"isco_code": "2512", "provincia": "CABA"},
--   "minimo": 5  -- alertar si hay mas de 5 nuevas
-- }
-- {
--   "tipo": "umbral",
--   "metrica": "ofertas_totales",
--   "operador": "<",
--   "valor": 100  -- alertar si bajan de 100
-- }
```

---

## 3. Row Level Security (RLS)

```sql
-- Habilitar RLS en todas las tablas
ALTER TABLE organizaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE busquedas_guardadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE intereses ENABLE ROW LEVEL SECURITY;
ALTER TABLE alertas ENABLE ROW LEVEL SECURITY;

-- Politica: usuarios ven solo su organizacion
CREATE POLICY "usuarios_misma_org" ON usuarios
    FOR SELECT USING (
        organizacion_id = (
            SELECT organizacion_id FROM usuarios WHERE id = auth.uid()
        )
    );

-- Politica: usuarios ven solo sus propias busquedas (o publicas de su org)
CREATE POLICY "busquedas_propias_o_publicas" ON busquedas_guardadas
    FOR SELECT USING (
        usuario_id = auth.uid()
        OR (
            es_publica = true
            AND usuario_id IN (
                SELECT id FROM usuarios
                WHERE organizacion_id = (
                    SELECT organizacion_id FROM usuarios WHERE id = auth.uid()
                )
            )
        )
    );

-- Politica: usuarios solo CRUD sus propias busquedas
CREATE POLICY "busquedas_propias_insert" ON busquedas_guardadas
    FOR INSERT WITH CHECK (usuario_id = auth.uid());

CREATE POLICY "busquedas_propias_update" ON busquedas_guardadas
    FOR UPDATE USING (usuario_id = auth.uid());

CREATE POLICY "busquedas_propias_delete" ON busquedas_guardadas
    FOR DELETE USING (usuario_id = auth.uid());

-- Politica: intereses solo propios
CREATE POLICY "intereses_propios" ON intereses
    FOR ALL USING (usuario_id = auth.uid());

-- Politica: alertas solo propias
CREATE POLICY "alertas_propias" ON alertas
    FOR ALL USING (usuario_id = auth.uid());
```

---

## 4. Indices

```sql
-- Performance
CREATE INDEX idx_usuarios_org ON usuarios(organizacion_id);
CREATE INDEX idx_busquedas_usuario ON busquedas_guardadas(usuario_id);
CREATE INDEX idx_intereses_usuario ON intereses(usuario_id);
CREATE INDEX idx_alertas_usuario ON alertas(usuario_id);
CREATE INDEX idx_alertas_activas ON alertas(activa) WHERE activa = true;
```

---

## 5. Trigger para updated_at

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizaciones_updated_at
    BEFORE UPDATE ON organizaciones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_busquedas_updated_at
    BEFORE UPDATE ON busquedas_guardadas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## 6. Datos Iniciales

```sql
-- Organizacion OEDE (admin)
INSERT INTO organizaciones (id, nombre, tipo, jurisdiccion)
VALUES ('00000000-0000-0000-0000-000000000001', 'OEDE', 'gobierno', 'nacional');

-- Usuario demo (crear via Supabase Auth primero, luego INSERT aqui)
-- INSERT INTO usuarios (id, organizacion_id, nombre, apellido, email, rol)
-- VALUES ('[auth.uid del usuario]', '00000000-0000-0000-0000-000000000001',
--         'Demo', 'Administrador', 'demo@oede.gob.ar', 'admin');
```

---

## 7. Flujo de Registro

1. Usuario se registra via Supabase Auth (email/password o OAuth)
2. Trigger crea entrada basica en `usuarios`
3. Admin asigna organizacion y rol
4. Usuario puede crear busquedas, intereses, alertas

```sql
-- Trigger para crear usuario automaticamente
CREATE OR REPLACE FUNCTION create_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO usuarios (id, email, nombre, apellido)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'nombre', 'Nuevo'),
        COALESCE(NEW.raw_user_meta_data->>'apellido', 'Usuario')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_profile();
```

---

## 8. Roles y Permisos

| Rol | Organizaciones | Usuarios | Busquedas | Ofertas |
|-----|----------------|----------|-----------|---------|
| admin | CRUD todas | CRUD su org | CRUD todas | Ver todas |
| analista | Ver su org | Ver su org | CRUD propias | Ver todas |
| lector | Ver su org | Ver perfil | Ver publicas | Ver agregados |

---

## 9. Proximos Pasos

1. [ ] Crear script SQL consolidado para Supabase
2. [ ] Configurar Auth en Supabase
3. [ ] Probar RLS con usuario de prueba
4. [ ] Integrar con dashboard Next.js
