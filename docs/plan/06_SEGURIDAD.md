# 6. Análisis de Seguridad

> Última actualización: 2026-02-05

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

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| **CRÍTICO** | 4 | 🔴 Resolver ANTES de lanzar |
| **ALTO** | 6 | 🟠 Resolver en Fase 1 |
| **MEDIO** | 7 | 🟡 Resolver en Fase 2 |
| **Total** | **17** | |

**Conclusión:** El sistema NO está listo para producción. Los 4 issues críticos son **bloqueantes**.

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

### S-04: APIs Admin sin verificación de rol

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Ubicación** | `app/api/admin/*` |
| **Impacto** | Cualquier usuario autenticado puede acceder a admin |
| **Probabilidad** | Alta |

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

### S-05: Sin rate limiting en APIs

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | DDoS, brute force en login |
| **Solución** | Implementar `@upstash/ratelimit` |

```typescript
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
});

// En API route
const { success } = await ratelimit.limit(ip);
if (!success) {
  return new Response("Too many requests", { status: 429 });
}
```

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

### S-07: Sin headers de seguridad

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | Clickjacking, MIME sniffing |
| **Solución** | Configurar en `next.config.js` |

```javascript
// next.config.js
const securityHeaders = [
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-XSS-Protection', value: '1; mode=block' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
  },
];

module.exports = {
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }];
  },
};
```

---

### S-08: Sin audit logging

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | Sin trazabilidad de acciones |
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
□ S-05: Rate limiting
□ S-06: Validación Zod
□ S-07: Headers seguridad
□ S-08: Audit logging
□ S-09: Sesiones configurables
□ S-10: 2FA (opcional inicialmente)

MEDIOS (Fase 2):
□ S-11 a S-17: Mejoras incrementales
```

---

## RLS por Tabla

| Tabla | SELECT | INSERT | UPDATE | DELETE |
|-------|--------|--------|--------|--------|
| `planes` | Todos | Solo admin | Solo admin | Solo admin |
| `suscripciones` | Solo propia | Sistema | Sistema | No |
| `pagos` | Solo propios | Sistema | Sistema | No |
| `alertas_config` | Solo propias | Propias | Propias | Propias |
| `informes_publicos` | Todos | Solo admin | Solo admin | Solo admin |
| `uso_features` | Solo propios | Sistema | Sistema | No |
| `ofertas` | Todos | Sistema | Sistema | No |
