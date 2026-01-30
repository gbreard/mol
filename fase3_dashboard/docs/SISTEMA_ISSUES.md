# Sistema de Issues/Feedback - Dashboard MOL

## Objetivo

Permitir que admins creen issues/comentarios sobre:
1. **Ofertas específicas** (ej: "ISCO incorrecto", "falta skill")
2. **Sistema en general** (ej: "agregar filtro X", "mejorar gráfico Y")

## Requisitos

- **Permisos:** Solo admin y super_admin pueden crear/editar
- **Campos:** título, descripción, tipo, estado, prioridad, autor, fecha
- **Relación:** Opcional con oferta específica (id_oferta nullable)
- **UX Crítico:** Acceso flotante desde cualquier página, sin perder contexto

---

## Base de Datos (Supabase)

### Tabla: `issues`

```sql
CREATE TABLE issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo TEXT NOT NULL,
  descripcion TEXT,
  tipo TEXT NOT NULL CHECK (tipo IN ('error_isco', 'error_nlp', 'error_skill', 'sugerencia', 'bug', 'otro')),
  estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_progreso', 'resuelto', 'descartado')),
  prioridad TEXT NOT NULL DEFAULT 'media' CHECK (prioridad IN ('baja', 'media', 'alta', 'critica')),
  id_oferta TEXT,  -- NULL = issue general
  autor_id UUID NOT NULL,
  autor_email TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  resuelto_at TIMESTAMPTZ,
  resuelto_por TEXT,
  -- Campos de tracking (workflow)
  agrupado_con UUID[],           -- IDs de issues similares
  solucion_aplicada TEXT,        -- Descripción de la solución implementada
  config_modificada TEXT,        -- Archivo de config modificado (ej: matching_rules_business.json)
  ofertas_afectadas INTEGER,     -- Cantidad de ofertas corregidas
  sprint TEXT                    -- Sprint/iteración asignada (ej: "2026-S05")
);

-- Índices
CREATE INDEX idx_issues_estado ON issues(estado);
CREATE INDEX idx_issues_tipo ON issues(tipo);
CREATE INDEX idx_issues_oferta ON issues(id_oferta) WHERE id_oferta IS NOT NULL;

-- RLS: Solo admin+ puede ver/crear/editar
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admin puede ver issues" ON issues
  FOR SELECT USING (
    auth.jwt() ->> 'role' IN ('admin', 'super_admin')
  );

CREATE POLICY "Admin puede crear issues" ON issues
  FOR INSERT WITH CHECK (
    auth.jwt() ->> 'role' IN ('admin', 'super_admin')
  );

CREATE POLICY "Admin puede actualizar issues" ON issues
  FOR UPDATE USING (
    auth.jwt() ->> 'role' IN ('admin', 'super_admin')
  );
```

---

## Componentes Implementados

### `components/issues/`

| Componente | Descripción |
|------------|-------------|
| `IssueBadge.tsx` | Badges de colores para tipo/estado/prioridad |
| `IssueForm.tsx` | Formulario crear/editar issue |
| `IssueList.tsx` | Lista de issues (compacta y completa) |
| `IssueFAB.tsx` | Botón flotante con contador de pendientes |
| `IssueDrawer.tsx` | Panel slide-out desde la derecha |
| `IssueRowButton.tsx` | Botón en cada fila de tabla ofertas |
| `IssueWrapper.tsx` | Wrapper client component para layout |
| `index.ts` | Barrel export |

### `contexts/IssueContext.tsx`

Estado global para el drawer:
```typescript
interface IssueContextType {
  isOpen: boolean;
  openDrawer: (oferta?: OfertaInfo) => void;
  closeDrawer: () => void;
  selectedOferta: OfertaInfo | null;
  pendingIssues: Issue[];
  pendingCount: number;
  refreshIssues: () => Promise<void>;
  isCreating: boolean;
  setIsCreating: (val: boolean) => void;
}
```

---

## Tipos TypeScript (`lib/types.ts`)

```typescript
export type IssueType = 'error_isco' | 'error_nlp' | 'error_skill' | 'sugerencia' | 'bug' | 'otro';
export type IssueEstado = 'pendiente' | 'en_progreso' | 'resuelto' | 'descartado';
export type IssuePrioridad = 'baja' | 'media' | 'alta' | 'critica';

export interface Issue {
  id: string;
  titulo: string;
  descripcion?: string;
  tipo: IssueType;
  estado: IssueEstado;
  prioridad: IssuePrioridad;
  id_oferta?: string;
  autor_id: string;
  autor_email: string;
  created_at: string;
  updated_at: string;
  resuelto_at?: string;
  resuelto_por?: string;
  // Campos de tracking (workflow)
  agrupado_con?: string[];
  solucion_aplicada?: string;
  config_modificada?: string;
  ofertas_afectadas?: number;
  sprint?: string;
}
```

---

## Flujo de Usuario

### Crear issue general (desde cualquier página)

1. Admin está en cualquier página del dashboard
2. Ve el FAB flotante en esquina inferior derecha (con badge si hay pendientes)
3. Click en FAB → se desliza el panel desde la derecha
4. Click en "+ Nuevo Issue"
5. Completa formulario (título, tipo, prioridad)
6. Guarda → issue creado, lista se actualiza

### Crear issue sobre oferta

1. Admin navega a tab "Ofertas Laborales"
2. En cada fila hay un icono de issue
3. Click → abre drawer con oferta pre-seleccionada
4. El drawer muestra: "Nuevo issue sobre: [título oferta]"
5. Completa título, tipo, prioridad
6. Guarda → issue vinculado a esa oferta

### Gestión avanzada

1. Desde el drawer, click en "Ver todos"
2. Navega a /admin/issues
3. Tabla completa con filtros avanzados
4. Estadísticas: pendientes, en progreso, resueltos

---

## Workflow de Procesamiento de Issues

### Ciclo de Vida

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CREACIÓN   │ --> │   TRIAGE    │ --> │  EJECUCIÓN  │ --> │   CIERRE    │
│  (Usuario)  │     │  (Semanal)  │     │  (Claude)   │     │ (Validación)│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Fase 1: Creación (Usuarios/Admins)

- Cualquier admin puede crear issues desde el dashboard
- Issues sobre ofertas específicas (error ISCO, NLP, skill)
- Issues generales (sugerencias, bugs, mejoras)
- **Campos obligatorios:** título, tipo, prioridad

### Fase 2: Triage (Reunión Semanal)

**Objetivo:** Revisar issues pendientes, agrupar similares, priorizar

| Paso | Acción | Responsable |
|------|--------|-------------|
| 1 | Listar issues pendientes | Automático |
| 2 | Identificar duplicados/similares | Equipo |
| 3 | Agrupar por tipo (ISCO, NLP, Skill) | Equipo |
| 4 | Decidir prioridad final | Equipo |
| 5 | Asignar a sprint/iteración | Equipo |

**Criterios de agrupación:**
- Mismo tipo de error (ej: varios errores ISCO en sector "IT")
- Misma causa raíz (ej: falta regla para "Gerente de X")
- Mismo patrón (ej: ubicaciones mal parseadas)

### Fase 3: Ejecución (Claude + Pipeline)

```
Issues Agrupados          Acción                    Resultado
─────────────────         ──────                    ─────────
5 errores ISCO     -->    Crear regla negocio  --> config/matching_rules_business.json
   en sector IT

3 errores NLP      -->    Ajustar inference    --> config/nlp_inference_rules.json
   seniority              rules

2 sugerencias      -->    Evaluar y diseñar    --> Plan de implementación
   filtros                (si se aprueba)
```

**Flujo de ejecución:**
1. **Análisis:** Claude revisa el grupo de issues similares
2. **Propuesta:** Claude propone solución (regla, config, código)
3. **Aprobación:** Equipo revisa y aprueba propuesta
4. **Implementación:** Claude ejecuta cambios
5. **Validación:** Reprocesar ofertas afectadas
6. **Verificación:** Confirmar que issues se resolvieron

### Fase 4: Cierre

- Marcar issues como "resueltos"
- Documentar solución aplicada
- Registrar config modificada
- Contar ofertas afectadas
- Actualizar métricas

---

## Campos de Tracking

| Campo | Tipo | Uso |
|-------|------|-----|
| `agrupado_con` | UUID[] | IDs de issues similares agrupados |
| `solucion_aplicada` | TEXT | Descripción de qué se hizo |
| `config_modificada` | TEXT | Qué archivo se cambió |
| `ofertas_afectadas` | INTEGER | Cuántas ofertas se corrigieron |
| `sprint` | TEXT | A qué iteración pertenece (ej: "2026-S05") |

---

## Mockups de Referencia

### Estado Normal (FAB visible)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  MOL Dashboard                                    [Usuario: admin@oede.gob]  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   [contenido del dashboard]                                                  │
│                                                                              │
│                                                                         ┌───┐│
│                                                                         │ 3 ││
│                                                                         └───┘│
└──────────────────────────────────────────────────────────────────────────────┘
                                                            FAB: bottom-6 right-6
```

### Drawer Abierto

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  MOL Dashboard                                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                          ┌──────────────────┐│
│   [contenido con overlay]                                │ X  Issues        ││
│                                                          ├──────────────────┤│
│                                                          │ [+ Nuevo Issue]  ││
│                                                          │                  ││
│                                                          │ -- Pendientes -- ││
│                                                          │ o Error ISCO     ││
│                                                          │   ofertas IT     ││
│                                                          │   alta  2h       ││
│                                                          │                  ││
│                                                          │ [Ver todos]      ││
│                                                          └──────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
```

### Badges de Colores

```
PRIORIDAD                    ESTADO
─────────                    ──────
Crítica (red-500)           Pendiente (yellow-500)
Alta (orange-500)           En progreso (blue-500)
Media (blue-400)            Resuelto (green-500)
Baja (gray-400)             Descartado (gray-400)

TIPOS (iconos)
──────────────
error_isco    → AlertCircle
error_nlp     → FileText
error_skill   → Zap
sugerencia    → Lightbulb
bug           → Bug
otro          → HelpCircle
```

---

## SQL Pendiente (Tracking Fields)

Ejecutar en Supabase para agregar campos de tracking:

```sql
ALTER TABLE issues ADD COLUMN agrupado_con UUID[];
ALTER TABLE issues ADD COLUMN solucion_aplicada TEXT;
ALTER TABLE issues ADD COLUMN config_modificada TEXT;
ALTER TABLE issues ADD COLUMN ofertas_afectadas INTEGER;
ALTER TABLE issues ADD COLUMN sprint TEXT;
```

---

## Archivos del Sistema

| Archivo | Propósito |
|---------|-----------|
| `lib/types.ts` | Tipos TypeScript para Issue |
| `lib/supabase.ts` | Funciones CRUD de issues |
| `contexts/IssueContext.tsx` | Estado global del drawer |
| `components/issues/*` | Componentes UI |
| `app/admin/issues/page.tsx` | Página de gestión completa |
| `app/layout.tsx` | Integración FAB + Drawer |
