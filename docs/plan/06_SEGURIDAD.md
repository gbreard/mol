# 6. Análisis de Seguridad

> Última actualización: 2026-03-20
> Versión: 2.0 — Ampliado con issues Skills Intelligence (S-18 a S-25)

## Referencias

| Documento | Relación |
|-----------|----------|
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas que necesitan RLS |
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Rutas a proteger |
| [09_ROADMAP](./09_ROADMAP.md) | Fase 0 es seguridad |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Políticas RLS | 04_MODELO_DATOS |
| Rutas protegidas | 02_ARQUITECTURA (middleware) |
| Autenticación | 05_USER_FLOWS |

---

## Resumen Ejecutivo

| Severidad | Cantidad | Resueltos | Estado |
|-----------|----------|-----------|--------|
| **CRÍTICO** | 6 | 4 | 🟠 2 nuevos (S-19, S-22 multi-tenancy OE) |
| **ALTO** | 10 | 3 | 🟠 4 nuevos (S-18, S-20, S-23, S-25) |
| **MEDIO** | 9 | 0 | 🟡 2 nuevos (S-21, S-24) |
| **Total** | **25** | **7** | |

**Fase 0 completada.** Los 4 issues críticos están resueltos:
- S-01: Tokens limpiados del código (commit `9f904093`) — **pendiente rotar key en Supabase Dashboard**
- S-02: Open redirect fix con whitelist (`lib/auth-utils.ts`)
- S-03: RLS + API route auth guards (`lib/api-auth.ts`, migration `014`)
- S-04: Admin role verification (middleware + `requireAdmin` en API routes)

---

## Issues CRÍTICOS (S-01 a S-04)

### S-01: Tokens expuestos en Git

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Ubicación** | `.env.local`, `.env.vercel` (en historial Git) |
| **Impacto** | Compromiso total de Supabase, acceso a todos los datos |
| **Probabilidad** | Alta (repositorio puede ser público o filtrado) |

**Solución:**
1. Rotar TODOS los tokens de Supabase inmediatamente
2. Agregar `.env*` a `.gitignore`
3. Usar variables de entorno de Vercel (no archivos)
4. Revisar historial de Git y limpiar si es necesario

**Verificación:**
```bash
# Buscar tokens en Git
git log -p --all -S 'supabase' -- '*.env*'
git log -p --all -S 'SUPABASE'
```

---

### S-02: Open Redirect en Auth Callback

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Ubicación** | `app/auth/callback/route.ts` |
| **Impacto** | Phishing, robo de sesiones |
| **CVSS** | 6.1 (Medium-High) |

**Código vulnerable:**
```typescript
// VULNERABLE
const next = searchParams.get("next") ?? "/";
return NextResponse.redirect(`${origin}${next}`);
// Atacante puede usar: /auth/callback?next=//malicious.com
```

**Solución:**
```typescript
// FIX
const allowedPaths = ['/dashboard', '/admin', '/skills', '/cuenta'];
const next = searchParams.get("next") ?? "/";
const safePath = allowedPaths.some(p => next.startsWith(p)) ? next : "/dashboard";
return NextResponse.redirect(`${origin}${safePath}`);
```

---

### S-03: Sin RLS (Row Level Security)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Ubicación** | Todas las tablas Supabase |
| **Impacto** | Usuarios pueden ver/modificar datos de otros |
| **Probabilidad** | Alta (cualquier usuario autenticado) |

**Tablas afectadas:**
- `ofertas` - Datos públicos, OK sin RLS
- `suscripciones` - ⚠️ Requiere RLS
- `pagos` - ⚠️ Requiere RLS
- `alertas_config` - ⚠️ Requiere RLS
- `uso_features` - ⚠️ Requiere RLS

**Solución - Políticas RLS:**
```sql
-- Habilitar RLS
ALTER TABLE suscripciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagos ENABLE ROW LEVEL SECURITY;
ALTER TABLE alertas_config ENABLE ROW LEVEL SECURITY;

-- Política: usuario solo ve su data
CREATE POLICY "Users can view own subscription"
ON suscripciones FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can view own payments"
ON pagos FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own alerts"
ON alertas_config FOR ALL
USING (auth.uid() = user_id);
```

---

### S-04: APIs Admin sin verificación de rol — ✅ RESUELTO

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Estado** | ✅ Resuelto (2026-02-23) |
| **Ubicación** | `app/api/admin/*` |
| **Impacto** | Cualquier usuario autenticado puede acceder a admin |
| **Solución aplicada** | Middleware verifica rol en páginas `/admin/*`, `requireAdmin()` en todas las API routes admin |

**Solución - Middleware:**
```typescript
// middleware.ts
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })

  const { data: { session } } = await supabase.auth.getSession()

  // Rutas admin requieren rol
  if (req.nextUrl.pathname.startsWith('/admin')) {
    if (!session) {
      return NextResponse.redirect(new URL('/login', req.url))
    }

    // Verificar rol admin
    const { data: profile } = await supabase
      .from('user_profiles')
      .select('role')
      .eq('id', session.user.id)
      .single()

    if (profile?.role !== 'admin') {
      return NextResponse.redirect(new URL('/dashboard', req.url))
    }
  }

  return res
}
```

---

## Issues ALTOS (S-05 a S-10)

### S-05: Sin rate limiting en APIs — ✅ RESUELTO

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Estado** | ✅ Resuelto (2026-02-23) |
| **Impacto** | DDoS, brute force en login |
| **Solución aplicada** | In-memory sliding-window rate limiter (`lib/rate-limit.ts`) integrado en `lib/api-auth.ts`. Las 11 API routes están protegidas. |

**Tiers:**

| Tier | Ventana | Max req | Aplica a |
|------|---------|---------|----------|
| `public` | 60s | 30 | GET públicos (search, skills-intelligence, perfil-argentina) |
| `authenticated` | 60s | 60 | Rutas con `requireAuth` |
| `admin` | 60s | 120 | Rutas con `requireAdmin` |

**Limitación conocida:** In-memory pierde estado en cold starts de Vercel y no se comparte entre instancias. Suficiente para uso interno OEDE.

**Para escalar:** Migrar a `@upstash/ratelimit` + Redis. Cambio localizado en `lib/rate-limit.ts`, las API routes no cambian.

---

### S-06: Sin validación de input

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | SQL injection, XSS |
| **Solución** | Usar Zod para validación |

```typescript
import { z } from 'zod';

const AlertaSchema = z.object({
  nombre: z.string().min(1).max(100),
  tipo: z.enum(['ocupacion', 'skill', 'empresa', 'provincia']),
  criterios: z.object({}).passthrough(),
  frecuencia: z.enum(['inmediata', 'diaria', 'semanal']),
});

// En API
const result = AlertaSchema.safeParse(body);
if (!result.success) {
  return Response.json({ error: result.error }, { status: 400 });
}
```

---

### S-07: Sin headers de seguridad — ✅ RESUELTO

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Estado** | ✅ Resuelto (2026-02-23) |
| **Impacto** | Clickjacking, MIME sniffing |
| **Solución aplicada** | Headers configurados en `next.config.ts` vía `async headers()` |

**Headers aplicados a todas las rutas (`/:path*`):**
- `X-Frame-Options: DENY` — previene clickjacking
- `X-Content-Type-Options: nosniff` — previene MIME sniffing
- `Referrer-Policy: strict-origin-when-cross-origin` — controla info de referrer

**Pendiente para futuro:** CSP (Content-Security-Policy) requiere auditar todos los scripts/estilos inline primero.

---

### S-08: Sin audit logging — 🟡 PARCIAL

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Estado** | 🟡 Parcial (2026-03-03) |
| **Impacto** | Sin trazabilidad de acciones |
| **Avance** | Validación humana registra `validacion_humana_por` (email) + `validacion_humana_at` (timestamp). Solicitudes de acceso registran `revisado_por` + `revisado_at`. Falta tabla `audit_logs` general. |
| **Solución** | Tabla `audit_logs` con triggers |

```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  action VARCHAR(50) NOT NULL,
  table_name VARCHAR(50),
  record_id UUID,
  old_data JSONB,
  new_data JSONB,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
```

---

### S-09: Sesiones sin expiración configurable

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | Sesiones eternas, riesgo en dispositivos compartidos |
| **Solución** | Configurar expiración en Supabase |

---

### S-10: Sin 2FA

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | Cuentas vulnerables a phishing |
| **Solución** | Implementar TOTP con Supabase Auth |

---

## Issues MEDIOS (S-11 a S-17)

| ID | Problema | Solución |
|----|----------|----------|
| S-11 | Sin política de contraseñas | Mínimo 12 chars, complejidad |
| S-12 | Emails sin verificar pueden acceder | Forzar verificación |
| S-13 | Sin protección CSRF en forms | Tokens CSRF |
| S-14 | Logs con datos sensibles | Sanitizar logs |
| S-15 | Sin backup automático | Cron backup diario |
| S-16 | Secrets en código | Mover a env vars |
| S-17 | Sin monitoreo de seguridad | Integrar Sentry |

---

## Checklist Pre-Launch

```
CRÍTICOS (Fase 0):
□ S-01: Rotar tokens expuestos
□ S-02: Fix open redirect
□ S-03: Implementar RLS básico
□ S-04: Verificar rol en APIs admin

ALTOS (Fase 1):
☑ S-05: Rate limiting (in-memory sliding window)
□ S-06: Validación Zod
☑ S-07: Headers seguridad (X-Frame-Options, nosniff, Referrer-Policy)
□ S-08: Audit logging
□ S-09: Sesiones configurables
□ S-10: 2FA (opcional inicialmente)

MEDIOS (Fase 2):
□ S-11 a S-17: Mejoras incrementales
```

---

## Issues Skills Intelligence (S-18 a S-25)

> Nuevos issues de seguridad derivados de la arquitectura de 3 servicios.
> Referencia: [01_MODELO_NEGOCIO v3.0](./01_MODELO_NEGOCIO.md#roles-skills-intelligence-v5)

### S-18: Token QR no adivinable + expiración

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Servicio** | S3 (Empresas) |
| **Impacto** | Si el token es predecible, cualquiera puede acceder a reportes con datos personales |

**Solución:**
- Token: UUID v4 (128 bits de entropía) sin guiones → 32 chars hex
- Expiración: 60 días por defecto, configurable
- Revocación: quien generó puede revocar en cualquier momento
- Audit: registrar cada acceso (IP, timestamp, user-agent)

---

### S-19: RLS multi-tenancy OE (aislamiento entre oficinas)

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Servicio** | S2 (Oficina de Empleo) |
| **Impacto** | Una OE podría ver datos de trabajadores de otra jurisdicción |

**Solución:**
```sql
-- Tabla organizaciones con jurisdicción
-- RLS: técnico solo ve registros donde organizacion_id = su org

CREATE POLICY "OE solo ve su cartera"
ON perfiles_trabajadores FOR SELECT
USING (
  organizacion_id = (
    SELECT organizacion_id FROM user_organizaciones
    WHERE user_id = auth.uid()
  )
);

-- Misma lógica para vacantes_oe, cursos_oe, etc.
```

---

### S-20: Consentimiento opt-in del trabajador

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Servicio** | S1 → S2, S3 |
| **Impacto** | Sin consentimiento explícito, compartir datos del trabajador con OEs/empresas viola privacidad |

**Solución:**
- Campo `opt_in_pool` en `perfiles_trabajadores` (boolean, default FALSE)
- Checkbox claro: "Acepto que mi perfil sea visible en búsquedas de oficinas de empleo y empresas"
- El trabajador puede revocar en cualquier momento
- Sin opt-in: perfil invisible para S2 y S3, solo el trabajador lo ve

---

### S-21: Datos personales (DNI) solo en PDF

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 MEDIO |
| **Servicio** | S1, S3 |
| **Impacto** | El DNI no debería ser visible en una URL accesible por token |

**Solución:**
- El DNI se incluye en el PDF descargable (documento físico)
- El reporte web (acceso por QR) muestra nombre pero NO DNI
- Campo `candidato_dni` no se expone en la API pública del reporte

---

### S-22: Aislamiento de pools por jurisdicción

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Servicio** | S2 |
| **Impacto** | Sin aislamiento, una OE de CABA podría ver la cartera de una OE de Córdoba |

**Solución:**
- Cada OE tiene `jurisdiccion` (provincia/municipio) en tabla `organizaciones`
- Pool propio: solo datos cargados por la OE (aislamiento total)
- Pool amplio MOL: ofertas del mercado general filtradas por jurisdicción (lectura)
- Trabajadores con opt-in: visibles solo si están en la misma jurisdicción (o nacional si el trabajador lo elige)

---

### S-23: Rate limiting APIs públicas S1

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Servicio** | S1 |
| **Impacto** | Sin rate limit, scraping masivo de ofertas y datos de matching |

**Solución:**
- Tier `s1_public`: 20 req/min (matching), 10 req/min (generar reporte)
- Tier `s1_auth`: 60 req/min (usuario registrado)
- Extender el rate limiter existente (`lib/rate-limit.ts`) con nuevos tiers
- CAPTCHA opcional en generación de reportes si se detecta abuso

---

### S-24: Audit log de reportes generados

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟡 MEDIO |
| **Servicio** | S1, S2 |
| **Impacto** | Sin trazabilidad de quién generó qué reporte para quién |

**Solución:**
- Tabla `reportes_compatibilidad` ya tiene `created_by`, `origen`, `created_at`
- Agregar: log de cada acceso al reporte (tabla `reporte_accesos`: token, ip, timestamp, user_agent)
- Dashboard admin: métricas de reportes generados por servicio (S1 vs S2)

---

### S-25: Validación input en importación Excel/CSV

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Servicio** | S2 |
| **Impacto** | Inyección de datos maliciosos via archivos de la OE (fórmulas Excel, HTML, SQL) |

**Solución:**
- Sanitizar todas las celdas: strip fórmulas (=, +, -, @), HTML tags, caracteres de control
- Validar schema: columnas esperadas, tipos de dato, longitudes máximas
- Límite de filas por importación (ej: 10,000)
- Preview antes de confirmar: mostrar primeras 10 filas parseadas
- Log de importación: quién, cuándo, cuántas filas, errores

---

## Checklist Skills Intelligence

```
CRÍTICOS:
□ S-19: RLS multi-tenancy OE (aislamiento entre oficinas)
□ S-22: Aislamiento de pools por jurisdicción

ALTOS:
□ S-18: Token QR seguro (UUID v4 + expiración + revocación)
□ S-20: Consentimiento opt-in del trabajador para pool
□ S-23: Rate limiting APIs públicas S1
□ S-25: Validación input importación Excel/CSV

MEDIOS:
□ S-21: DNI solo en PDF, no en reporte web
□ S-24: Audit log de reportes generados
```

---

## RLS por Tabla

| Tabla | SELECT | INSERT | UPDATE | DELETE | Estado |
|-------|--------|--------|--------|--------|--------|
| `planes` | Todos | Solo admin | Solo admin | Solo admin | ⬜ Pendiente |
| `suscripciones` | Solo propia | Sistema | Sistema | No | ⬜ Pendiente |
| `pagos` | Solo propios | Sistema | Sistema | No | ⬜ Pendiente |
| `alertas_config` | Solo propias | Propias | Propias | Propias | ⬜ Pendiente |
| `informes_publicos` | Todos | Solo admin | Solo admin | Solo admin | ⬜ Pendiente |
| `uso_features` | Solo propios | Sistema | Sistema | No | ⬜ Pendiente |
| `ofertas` | Todos | Sistema | Sistema | No | ⬜ Pendiente |
| `solicitudes_acceso` | Propias (user) / Todas (admin) | Propias (via RPC) | Solo admin (via RPC) | No | ✅ Implementado (2026-03-03) |
| `ofertas_dashboard` | Todos (anon read) | Sistema | Sistema + RPC validación | No | ✅ Parcial (RPC guardar_validacion_humana) |

> **2026-03-03:** Tabla `solicitudes_acceso` implementada con RLS completo (4 políticas) + 3 RPCs SECURITY DEFINER. Ver migration `017_solicitudes_acceso.sql`.

### RLS — Tablas Skills Intelligence (nuevas)

| Tabla | Trabajador S1 | Técnico OE S2 | Empresa libre S3 | Empresa reg. S3 | Admin | Estado |
|-------|--------------|---------------|-------------------|-----------------|-------|--------|
| `perfiles_trabajadores` | Solo propios (created_by) | Su cartera (org_id) | ✗ | ✗ | Todos | ⬜ Ampliar RLS |
| `reportes_compatibilidad` | Sus reportes | Reportes de su OE | Solo por token (activo) | Sus candidatos | Todos | ⬜ Crear RLS |
| `organizaciones` | ✗ | Solo su org | ✗ | Solo su org | CRUD | ⬜ Crear |
| `user_organizaciones` | ✗ | Su org | ✗ | Su org | CRUD | ⬜ Crear |
| `vacantes_oe` | ✗ | CRUD (su OE) | ✗ | ✗ | Todos | ⬜ Crear |
| `cursos_oe` | ✗ | CRUD (su OE) | ✗ | ✗ | Todos | ⬜ Crear |
| `vacantes_empresa` | ✗ | Lectura (pool jurisd.) | ✗ | CRUD (su empresa) | Todos | ⬜ Crear |
| `esco_argentino` | Lectura | Lectura | Lectura (via reporte) | Lectura | CRUD | ✅ Existe |
| `reporte_accesos` | ✗ | ✗ | ✗ | ✗ | Lectura | ⬜ Crear |

> **Principio:** La RLS es la primera línea de defensa. Incluso si un usuario construye una query manual contra Supabase, solo ve lo que le corresponde.
