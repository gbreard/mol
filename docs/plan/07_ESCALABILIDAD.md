# 7. Análisis de Escalabilidad

> Última actualización: 2026-02-07

## Referencias

| Documento | Relación |
|-----------|----------|
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Índices y vistas |
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Pantallas con problemas |
| [09_ROADMAP](./09_ROADMAP.md) | Fase 1 escalabilidad |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Paginación | API routes, componentes frontend |
| Índices | 04_MODELO_DATOS |
| Cache | Componentes que consumen datos |

---

## Resumen Ejecutivo

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| **CRÍTICO** | 4 (1 resuelto) | 🟢 E-16 resuelto, 3 pendientes |
| **ALTO** | 5 | 🟠 Resolver en Fase 2 |
| **MEDIO** | 7 | 🟡 Mejoras futuras |
| **Total** | **16** | |

---

## Issues CRÍTICOS (E-01 a E-03)

### E-01: Límite hardcodeado de 10,000 registros

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Ubicación** | `lib/supabase.ts:136,174,214` |
| **Impacto** | Trunca datos sin aviso al usuario |
| **Datos actuales** | ~13,000 ofertas (ya excede límite) |

**Código problemático:**
```typescript
// lib/supabase.ts - PROBLEMÁTICO
export async function getOfertas() {
  const { data } = await supabase
    .from('ofertas')
    .select('*')
    .limit(10000)  // ⚠️ Si hay 50k ofertas, se pierden 40k
    .order('fecha_publicacion', { ascending: false })
  return data
}
```

**Solución - Paginación cursor-based:**
```typescript
// FIX: Paginación cursor-based
export async function getOfertas(cursor?: string, pageSize = 50) {
  let query = supabase
    .from('ofertas')
    .select('*')
    .order('fecha_publicacion', { ascending: false })
    .limit(pageSize)

  if (cursor) {
    query = query.lt('fecha_publicacion', cursor)
  }

  const { data } = await query
  return {
    data,
    nextCursor: data?.[data.length - 1]?.fecha_publicacion
  }
}
```

---

### E-02: Agregaciones en JavaScript

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Ubicación** | `lib/supabase.ts` (varias funciones) |
| **Impacto** | O(n) en cliente, lento con muchos datos |
| **Problema** | Trae todos los datos y procesa en browser |

**Vistas SQL existentes pero NO usadas:**
```sql
-- Estas vistas YA EXISTEN en Supabase pero el código no las usa
v_kpis_dashboard        -- KPIs agregados
v_ofertas_por_provincia -- Distribución geográfica
v_top_ocupaciones       -- Ocupaciones más demandadas
v_ofertas_por_modalidad -- Presencial/Remoto/Híbrido
v_skills_demanda        -- Skills más pedidas
v_skills_por_l1         -- Skills por categoría L1
```

**Solución:**
```typescript
// En lugar de:
const ofertas = await getOfertas();
const kpis = {
  total: ofertas.length,
  porProvincia: ofertas.reduce(...), // ⚠️ Lento
};

// Usar:
const kpis = await supabase.from('v_kpis_dashboard').select('*').single();
```

---

### E-03: Sin cache del lado cliente

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🔴 CRÍTICO |
| **Ubicación** | Todo el dashboard |
| **Impacto** | Requests innecesarios, latencia perceptible |
| **Problema** | Cada navegación = nueva request |

**Solución - React Query:**
```typescript
import { useQuery } from '@tanstack/react-query';

// Con cache automático
export function useOfertas(filters) {
  return useQuery({
    queryKey: ['ofertas', filters],
    queryFn: () => fetchOfertas(filters),
    staleTime: 5 * 60 * 1000, // 5 minutos
    cacheTime: 30 * 60 * 1000, // 30 minutos
  });
}
```

---

### E-16: Insights calculados en cliente (fetchAllPaginated) ✅ RESUELTO

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟢 RESUELTO (2026-02-07) |
| **Ubicación** | `lib/supabase.ts` (múltiples funciones) |
| **Impacto** | Browser congela con >10k ofertas |
| **Detalle completo** | [12_INSIGHTS_SISTEMA](./12_INSIGHTS_SISTEMA.md) |

**Problema original:** Se traían TODAS las ofertas al cliente y se procesaban con `forEach()` en JavaScript.

**Solución implementada:**
1. **5 vistas SQL** creadas en Supabase:
   - `vw_insights_kpis` - KPIs agregados
   - `vw_insights_isco_grupos` - Distribución por grupo ISCO
   - `vw_insights_tendencia` - Tendencia mensual
   - `vw_insights_empresas` - Top empresas
   - `vw_insights_provincias` - Distribución geográfica

2. **Función RPC `get_insights()`** que acepta filtros y devuelve todo en 1 query

3. **Código refactorizado:**
   - `lib/supabase.ts`: Nuevas funciones `getInsightsRPC()`, `getKPIsOptimized()`, `getOfertasPorProvinciaOptimized()`
   - `components/PanoramaGeneral.tsx`: Usa `getInsightsRPC()` en lugar de múltiples fetches

**Resultado:**
| Métrica | Antes | Después |
|---------|-------|---------|
| Queries a Supabase | 3+ (paginadas) | 1 RPC |
| Datos transferidos | ~200KB | ~2KB |
| Tiempo carga | ~500ms | <50ms |

---

## Issues ALTOS (E-04 a E-08)

### E-04: Offset pagination

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | O(n) en queries con offset alto |
| **Solución** | Cursor pagination (ver E-01) |

**Problema:** `OFFSET 10000` requiere que Postgres escanee 10,000 filas antes de devolver resultados.

---

### E-05: Sin índices en columnas de filtro

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Ubicación** | Tablas principales |
| **Impacto** | Queries lentas con filtros |

**Índices necesarios:**
```sql
-- ofertas
CREATE INDEX idx_ofertas_fecha ON ofertas(fecha_publicacion DESC);
CREATE INDEX idx_ofertas_provincia ON ofertas(provincia);
CREATE INDEX idx_ofertas_isco ON ofertas_esco_matching(isco);

-- suscripciones
CREATE INDEX idx_suscripciones_estado ON suscripciones(estado);
CREATE INDEX idx_suscripciones_fecha_fin ON suscripciones(fecha_fin);
```

---

### E-06: Sync SQLite→Supabase es full replace

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | Ineficiente con muchos datos |
| **Solución** | Sync incremental con timestamps |

```python
# En lugar de DELETE + INSERT ALL
# Usar UPSERT con updated_at
def sync_incremental(last_sync: datetime):
    nuevas = db.query(
        "SELECT * FROM ofertas WHERE updated_at > ?",
        [last_sync]
    )
    supabase.upsert(nuevas, on_conflict='id')
```

---

### E-07: Sin connection pooling

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | Límite de conexiones a Postgres |
| **Solución** | Usar Supabase pooler (ya disponible) |

---

### E-08: Imágenes sin CDN/optimización

| Atributo | Valor |
|----------|-------|
| **Severidad** | 🟠 ALTO |
| **Impacto** | Carga lenta |
| **Solución** | Next.js Image + Vercel CDN |

---

## Issues MEDIOS (E-09 a E-15)

| ID | Problema | Solución |
|----|----------|----------|
| E-09 | Sin lazy loading de componentes | `dynamic()` imports |
| E-10 | Bundle size sin analizar | `@next/bundle-analyzer` |
| E-11 | Sin service worker | Workbox para offline |
| E-12 | Sin compresión de responses | Brotli/gzip (Vercel lo hace) |
| E-13 | Sin database replicas | Read replicas para queries pesadas |
| E-14 | Gráficos renderizan todo | Virtualización para datasets grandes |
| E-15 | Sin health checks | Endpoint `/api/health` |

---

## Métricas de Performance

### Objetivos

| Métrica | Actual | Meta Fase 1 | Meta Producción |
|---------|--------|-------------|-----------------|
| Time to First Byte | ~800ms | < 400ms | < 200ms |
| First Contentful Paint | ~2.5s | < 1.5s | < 1s |
| Time to Interactive | ~4s | < 2s | < 1.5s |
| Largest Contentful Paint | ~3s | < 2s | < 1.5s |

### Cómo Medir

```bash
# Lighthouse CLI
npx lighthouse https://mol-nextjs.vercel.app --output=json

# Web Vitals en código
import { getCLS, getFID, getLCP } from 'web-vitals';
getCLS(console.log);
getFID(console.log);
getLCP(console.log);
```

---

## Plan de Optimización

### Fase 1 (Inmediato)

```
□ E-01: Reemplazar .limit(10000) por paginación cursor
□ E-02: Usar vistas SQL existentes
□ E-03: Implementar React Query con cache
□ E-05: Agregar índices críticos
```

### Fase 2 (1 mes)

```
□ E-04: Migrar toda paginación a cursor-based
□ E-06: Sync incremental
□ E-09: Lazy loading de componentes pesados
□ E-10: Analizar y reducir bundle
```

### Fase 3 (3 meses)

```
□ E-07: Configurar pooler correctamente
□ E-11: Service worker para offline
□ E-14: Virtualización de listas largas
□ E-15: Health checks y monitoreo
```
