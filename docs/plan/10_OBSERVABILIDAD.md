# 10. Observabilidad del Sistema

> Última actualización: 2026-02-06

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | P-25 Arquitectura |
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas de métricas |
| [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) | Performance del sistema |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Nueva pantalla | dashboard_architecture.json |
| Nuevo API route | dashboard_architecture.json |
| Nueva fase del pipeline | PipelineFlow.tsx, API metrics |

---

## Resumen

Sistema de visualización de arquitectura implementado en `/admin/arquitectura` que permite:
- Ver todas las pantallas del dashboard y sus conexiones
- Monitorear el estado de las 3 fases del pipeline
- Consultar métricas en tiempo real desde Supabase

---

## Arquitectura de la Solución

### Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    /admin/arquitectura                          │
│                         page.tsx                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │  Tab 1      │   │  Tab 2      │   │  Tab 3      │           │
│  │  Mapa de    │   │  Pipeline   │   │  Métricas   │           │
│  │  Pantallas  │   │  de Datos   │   │  en Vivo    │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │ScreenMap   │   │PipelineFlow │   │PhaseStatus  │           │
│  │Graph.tsx   │   │.tsx         │   │Card.tsx     │           │
│  │ (D3.js)    │   │             │   │             │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                 │                 │                   │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
   ┌─────────────┐   ┌─────────────────────────────┐
   │ JSON estático│   │  /api/admin/architecture-   │
   │ dashboard_   │   │  metrics                    │
   │ architecture │   │                             │
   │ .json        │   │  Consulta Supabase:         │
   └─────────────┘   │  - ofertas_dashboard        │
                     │  - ofertas_skills           │
                     │  - ocupaciones_esco         │
                     │  - issues                   │
                     └─────────────────────────────┘
```

### Archivos

| Archivo | Propósito |
|---------|-----------|
| `app/admin/arquitectura/page.tsx` | Página principal con 3 tabs |
| `components/admin/ScreenMapGraph.tsx` | Grafo D3.js de pantallas |
| `components/admin/PipelineFlow.tsx` | Diagrama de las 3 fases |
| `components/admin/PhaseStatusCard.tsx` | Cards de métricas por fase |
| `app/api/admin/architecture-metrics/route.ts` | API de métricas en tiempo real |
| `public/data/dashboard_architecture.json` | Definición estática de arquitectura |

---

## Tab 1: Mapa de Pantallas

### Visualización

Grafo interactivo D3.js force-directed que muestra:
- **Nodos**: Páginas del dashboard y API routes
- **Enlaces**: Conexiones de navegación y datos
- **Colores por tipo**:
  - 🔵 Azul: Páginas públicas
  - 🟣 Púrpura: Páginas admin
  - ⚫ Gris: Auth
  - 🟢 Verde: API routes

### Interacciones

| Acción | Resultado |
|--------|-----------|
| Click en nodo | Muestra detalles (path, descripción, componentes) |
| Drag | Mueve el nodo |
| Scroll | Zoom in/out |
| Click fondo | Deselecciona nodo |

### Datos (dashboard_architecture.json)

```json
{
  "pages": [
    {
      "id": "home",
      "path": "/",
      "label": "Dashboard Principal",
      "type": "public",
      "description": "Vista principal con 3 tabs",
      "components": ["PanoramaGeneral", "Requerimientos", "SkillsPanel"],
      "dataSource": ["ofertas_dashboard", "ocupaciones_esco"]
    }
    // ... más páginas
  ],
  "apiRoutes": [
    {
      "id": "api-stats",
      "path": "/api/admin/stats",
      "method": "GET",
      "description": "Estadísticas del sistema",
      "usedBy": ["/admin"]
    }
    // ... más rutas
  ],
  "connections": [
    { "from": "/admin", "to": "/api/admin/stats", "type": "data", "label": "Fetch" }
    // ... más conexiones
  ]
}
```

---

## Tab 2: Pipeline de Datos

### Las 3 Fases

```
FASE 1: ADQUISICIÓN          FASE 2: PROCESAMIENTO         FASE 3: PRESENTACIÓN
─────────────────────        ─────────────────────         ─────────────────────
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│ Scrapers:       │    →     │ NLP v11         │    →     │ sync_to_supabase│
│ - Bumeran       │          │ (Qwen2.5:7b)    │          │                 │
│ - ZonaJobs      │          │                 │          │ Dashboard       │
│ - Computrabajo  │          │ Skills BGE-M3   │          │ Next.js         │
│                 │          │                 │          │                 │
│ run_scheduler.py│          │ Matching ESCO   │          │                 │
│                 │          │ (BGE-M3)        │          │                 │
│ 🟢 OK           │          │                 │          │ 🟢 OK           │
└─────────────────┘          │ Auto-Validator  │          └─────────────────┘
                             │                 │
                             │ 🟡 3 errores    │
                             └─────────────────┘
```

### Indicadores de Estado

| Estado | Color | Condición |
|--------|-------|-----------|
| 🟢 Saludable | Verde | Sin errores, datos recientes |
| 🟡 Atención | Amarillo | Errores pendientes o datos antiguos |
| 🔴 Error | Rojo | Muchos errores o sin datos |
| ⚪ Inactivo | Gris | Sin métricas disponibles |

### Lógica de Estado

```typescript
// Fase 1: Adquisición
if (dias_desde_scraping > 7) return 'warning';
if (ofertas_activas === 0) return 'error';
return 'healthy';

// Fase 2: Procesamiento
if (errores_sin_resolver > 10) return 'error';
if (errores_sin_resolver > 0) return 'warning';
if (sin_nlp > con_nlp * 0.1) return 'warning';
return 'healthy';

// Fase 3: Presentación
if (pendientes_sync > ofertas_supabase * 0.2) return 'warning';
return 'healthy';
```

---

## Tab 3: Métricas en Vivo

### Cards por Fase

| Fase | Métricas |
|------|----------|
| **Fase 1** | Total ofertas, Activas, Último scraping, Días desde, Por fuente |
| **Fase 2** | Con NLP, Con Matching, Validadas, Errores, Reglas negocio |
| **Fase 3** | En Supabase, Pendientes sync, Skills count, Ocupaciones count |

### Acción Sugerida

El sistema analiza las métricas y sugiere en qué fase trabajar:

| Condición | Sugerencia |
|-----------|------------|
| Errores > 0 | Fase 2 - Procesamiento |
| Días desde scraping > 7 | Fase 1 - Adquisición |
| Todo OK | Fase 3 - Presentación |

### Auto-Refresh

- Cada 30 segundos cuando está en tab Métricas o Pipeline
- Botón manual "Actualizar" siempre disponible

---

## API: architecture-metrics

### Endpoint

```
GET /api/admin/architecture-metrics
```

### Response

```typescript
interface ArchitectureMetrics {
  phase1: {
    ofertas_totales: number;      // Count exacto de ofertas_dashboard
    ofertas_activas: number;      // Count donde estado = 'activa'
    ultimo_scraping: string;      // Fecha más reciente
    dias_desde_scraping: number;  // Días desde última publicación
    fuentes: Record<string, number>; // Count por portal
  };
  phase2: {
    con_nlp: number;              // = ofertas_totales (en Supabase todo tiene NLP)
    sin_nlp: number;              // = 0 (en Supabase)
    con_matching: number;         // Count donde isco_code != null
    pendientes_matching: number;  // = 0 (en Supabase)
    validadas: number;            // = ofertas_totales (en Supabase)
    errores_sin_resolver: number; // Count issues estado='abierto'
    reglas_negocio: number;       // De sistema_estado o default 140
  };
  phase3: {
    ofertas_supabase: number;     // = ofertas_totales
    pendientes_sync: number;      // = 0 (no se puede saber desde Supabase)
    skills_count: number;         // Count ofertas_skills
    ocupaciones_count: number;    // Count ocupaciones_esco
  };
  suggested: {
    fase: number;
    nombre: string;
    razon: string;
  };
  timestamp: string;
}
```

### Tablas Consultadas

| Tabla Supabase | Uso |
|----------------|-----|
| `ofertas_dashboard` | Conteos de ofertas, fechas, portales |
| `ofertas_skills` | Count total de skills |
| `ocupaciones_esco` | Count de ocupaciones |
| `issues` | Errores sin resolver |
| `sistema_estado` | Reglas de negocio (opcional) |

### Nota sobre Paginación

Supabase tiene límite de 1000 registros por query. El API usa `{ count: 'exact', head: true }` para obtener conteos totales sin descargar datos.

---

## Cómo Mantener

### Agregar Nueva Pantalla

1. Editar `public/data/dashboard_architecture.json`
2. Agregar entrada en `pages[]`:
   ```json
   {
     "id": "nueva-pantalla",
     "path": "/ruta/nueva",
     "label": "Nombre Display",
     "type": "public|admin|auth",
     "description": "Qué hace esta pantalla",
     "components": ["ComponenteUsado"],
     "dataSource": ["tabla_o_api"]
   }
   ```
3. Agregar conexiones en `connections[]` si aplica

### Agregar Nuevo API Route

1. Editar `public/data/dashboard_architecture.json`
2. Agregar entrada en `apiRoutes[]`:
   ```json
   {
     "id": "api-nuevo",
     "path": "/api/nuevo/endpoint",
     "method": "GET|POST",
     "description": "Qué retorna",
     "usedBy": ["/pantallas/que/lo/usan"]
   }
   ```

### Modificar Lógica de Estado

Editar `components/admin/PipelineFlow.tsx`:
- Función `getPhaseStatus()` para cambiar condiciones
- Función `getPhaseMetricsSummary()` para cambiar texto mostrado

---

## Dependencias

| Dependencia | Versión | Uso |
|-------------|---------|-----|
| d3 | ^7.x | Grafos force-directed |
| lucide-react | ^0.x | Iconos |
| @supabase/supabase-js | ^2.x | Queries a BD |

---

## Issues Conocidos

| ID | Descripción | Estado |
|----|-------------|--------|
| O-01 | Paginación Supabase (límite 1000) | ✅ Resuelto con count exact |
| O-02 | Archivos no persistían en filesystem | ✅ Resuelto |

---

## Roadmap

| Fase | Feature | Prioridad |
|------|---------|-----------|
| Actual | 3 tabs funcionando | ✅ Completado |
| Siguiente | Historial de métricas | Media |
| Futuro | Alertas automáticas | Baja |
| Futuro | Export de métricas | Baja |
