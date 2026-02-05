# Wireframes: Admin

> Última actualización: 2026-02-05

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](../02_ARQUITECTURA_PANTALLAS.md) | Lista de pantallas P-17 a P-24 |
| [01_MODELO_NEGOCIO](../01_MODELO_NEGOCIO.md) | Define rol U-ADMIN |
| [06_SEGURIDAD](../06_SEGURIDAD.md) | RLS y verificación de rol |

---

## P-17: Admin Dashboard (`/admin`)

**Estado:** ✅ Existe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard  ●  │  Estado del Sistema                                    │
│  Usuarios      │                                                        │
│  Issues        │  ┌─────────────────────────────────────────────────┐   │
│  Skills        │  │ FASE 1: SCRAPING                    ● Online    │   │
│  Scraping      │  │                                                 │   │
│  Métricas      │  │ Última ejecución: Hace 2 horas                  │   │
│  Logs          │  │ Ofertas nuevas hoy: 234                         │   │
│  Config        │  │ Fuentes activas: 5/5                            │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ FASE 2: PROCESAMIENTO               ● Online    │   │
│                │  │                                                 │   │
│                │  │ NLP v11.3: 100% ofertas procesadas              │   │
│                │  │ Matching v3.4.2: 538 validadas                  │   │
│                │  │ Errores pendientes: 0                           │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ FASE 3: PRESENTACIÓN                ● Online    │   │
│                │  │                                                 │   │
│                │  │ Dashboard: mol-nextjs.vercel.app                │   │
│                │  │ Último deploy: Hace 1 día                       │   │
│                │  │ Supabase sync: 538 ofertas                      │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

---

## P-18: Admin Usuarios (`/admin/usuarios`)

**Estado:** ⚠️ Básico (falta editar/eliminar)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Gestión de Usuarios                   [+ Nuevo]      │
│  Usuarios   ●  │                                                        │
│  Issues        │  Buscar: [                    ] [🔍]                   │
│  Skills        │  Filtrar: [Todos ▼] [Activos ▼]                       │
│  Scraping      │                                                        │
│  Métricas      │  ┌────────────────────────────────────────────────┐   │
│  Logs          │  │ Usuario          │ Plan   │ Estado  │ Acciones│   │
│  Config        │  ├──────────────────┼────────┼─────────┼─────────┤   │
│                │  │ juan@empresa.com │ PRO    │ ● Activo│ [✏][🗑] │   │
│                │  │ maria@consul.com │ PRO    │ ● Activo│ [✏][🗑] │   │
│                │  │ pedro@test.com   │ FREE   │ ● Activo│ [✏][🗑] │   │
│                │  │ ana@corp.com     │ ENTERP.│ ● Activo│ [✏][🗑] │   │
│                │  │ luis@demo.com    │ FREE   │ ○ Inact.│ [✏][🗑] │   │
│                │  └────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  Mostrando 5 de 156 usuarios         [< 1 2 3 ... >]  │
│                │                                                        │
│                │  ─────────────────────────────────────────────────     │
│                │                                                        │
│                │  RESUMEN                                               │
│                │  Total: 156 | Free: 89 | Pro: 52 | Enterprise: 15     │
│                │  MRR: $930,000 ARS                                     │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

---

## P-19: Admin Issues (`/admin/issues`)

**Estado:** ✅ Existe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Issues y Feedback                                     │
│  Usuarios      │                                                        │
│  Issues     ●  │  Filtrar: [Todos ▼] [Pendiente ▼] [Alta ▼]            │
│  Skills        │                                                        │
│  Scraping      │  ┌─────────────────────────────────────────────────┐   │
│  Métricas      │  │                                                 │   │
│  Logs          │  │  🔴 #45 - Error ISCO en oferta 12345            │   │
│  Config        │  │  Tipo: error_isco | Prioridad: Alta             │   │
│                │  │  Reportado: juan@empresa.com | Hace 2 horas       │   │
│                │  │  [Ver detalle] [Resolver] [Agrupar]             │   │
│                │  │                                                 │   │
│                │  ├─────────────────────────────────────────────────┤   │
│                │  │                                                 │   │
│                │  │  🟡 #44 - Sugerencia: agregar filtro por skill  │   │
│                │  │  Tipo: sugerencia | Prioridad: Media            │   │
│                │  │  Reportado: maria@test.com | Hace 1 día         │   │
│                │  │  [Ver detalle] [Resolver] [Agrupar]             │   │
│                │  │                                                 │   │
│                │  ├─────────────────────────────────────────────────┤   │
│                │  │                                                 │   │
│                │  │  🟢 #43 - Error de visualización en móvil       │   │
│                │  │  Tipo: bug | Prioridad: Baja                    │   │
│                │  │  Reportado: admin@oede.gob.ar | Hace 3 días     │   │
│                │  │  [Ver detalle] [Resolver] [Agrupar]             │   │
│                │  │                                                 │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  Pendientes: 12 | Resueltos hoy: 3 | Total: 45        │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

---

## P-20: Admin Skills Intelligence (`/admin/skills`)

**Estado:** ✅ Existe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Skills Intelligence (Interno)                         │
│  Usuarios      │                                                        │
│  Issues        │  [Taxonomía] [Ocupación] [Comparar] [Mis Skills]       │
│  Skills     ●  │  [Perfil Argentina] [Consolidado]                      │
│  Scraping      │  ═══════════════════                                   │
│  Métricas      │                                                        │
│  Logs          │  PERFIL ARGENTINA (tab activo)                         │
│  Config        │                                                        │
│                │  Skills más demandadas en Argentina (MOL data)         │
│                │                                                        │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ # │ Skill              │ Ofertas │ Tendencia   │   │
│                │  ├───┼────────────────────┼─────────┼─────────────┤   │
│                │  │ 1 │ Microsoft Excel    │   2,345 │ ↑ +12%      │   │
│                │  │ 2 │ Comunicación       │   1,890 │ ↑ +8%       │   │
│                │  │ 3 │ Inglés             │   1,567 │ → 0%        │   │
│                │  │ 4 │ Python             │   1,234 │ ↑ +25%      │   │
│                │  │ 5 │ SAP                │     987 │ ↓ -5%       │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  ┌──────────────────┐ ┌──────────────────┐             │
│                │  │ POR CATEGORÍA L1 │ │ SKILLS EMERGENTES│             │
│                │  │ S: Soft    45%   │ │ 1. IA Gen.  +150%│             │
│                │  │ T: Tech    30%   │ │ 2. LLMs     +120%│             │
│                │  │ K: Conocim.15%   │ │ 3. Next.js   +80%│             │
│                │  │ A: Actitud.10%   │ │ 4. Rust      +60%│             │
│                │  └──────────────────┘ └──────────────────┘             │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

---

## P-21: Admin Scraping (`/admin/scraping`)

**Estado:** ⚠️ Solo lectura (no ejecuta)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Estado de Scraping                                    │
│  Usuarios      │                                                        │
│  Issues        │  Última actualización: 05/02/2026 14:30                │
│  Skills        │                                                        │
│  Scraping   ●  │  ┌─────────────────────────────────────────────────┐   │
│  Métricas      │  │ Fuente      │ Estado  │ Última    │ Ofertas    │   │
│  Logs          │  │             │         │ ejecución │ hoy        │   │
│  Config        │  ├─────────────┼─────────┼───────────┼────────────┤   │
│                │  │ Bumeran     │ ● OK    │ Hace 2h   │ 89         │   │
│                │  │ ZonaJobs    │ ● OK    │ Hace 2h   │ 67         │   │
│                │  │ Computrabajo│ ● OK    │ Hace 2h   │ 45         │   │
│                │  │ Indeed      │ ● OK    │ Hace 2h   │ 23         │   │
│                │  │ LinkedIn    │ ○ WARN  │ Hace 4h   │ 10         │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │         OFERTAS SCRAPEADAS (últimos 7 días)     │   │
│                │  │   300 ┤                              ██         │   │
│                │  │   250 ┤                    ██        ██         │   │
│                │  │   200 ┤          ██        ██   ██   ██         │   │
│                │  │   150 ┤     ██   ██   ██   ██   ██   ██         │   │
│                │  │   100 ┼─────────────────────────────────        │   │
│                │  │        Lun  Mar  Mié  Jue  Vie  Sáb  Dom        │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  Bajas detectadas hoy: 34 | Duplicados: 12             │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

---

## P-22: Admin Métricas (`/admin/metricas`)

**Estado:** ✅ Existe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Métricas del Pipeline                                 │
│  Usuarios      │                                                        │
│  Issues        │  Período: [Última semana ▼]                           │
│  Skills        │                                                        │
│  Scraping      │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  Métricas   ●  │  │ 2,345  │ │ 99.2%  │ │ 95.8%  │ │  538   │          │
│  Logs          │  │ofertas │ │NLP OK  │ │Match OK│ │validado│          │
│  Config        │  │ proces.│ │        │ │        │ │        │          │
│                │  └────────┘ └────────┘ └────────┘ └────────┘          │
│                │                                                        │
│                │  NLP PIPELINE v11.3                                    │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ Campo           │ Precision │ Trend            │   │
│                │  ├─────────────────┼───────────┼──────────────────┤   │
│                │  │ titulo_limpio   │ 99.5%     │ ↑ +0.3%          │   │
│                │  │ provincia       │ 98.2%     │ → 0%             │   │
│                │  │ skills_tecnicas │ 96.1%     │ ↑ +2.1%          │   │
│                │  │ nivel_seniority │ 94.5%     │ ↑ +1.2%          │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  MATCHING v3.4.2                                       │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ Por regla: 81% | Por diccionario: 4%            │   │
│                │  │ Por semántico: 15%                              │   │
│                │  │ Reglas de negocio: 132 | Convergencia: 100%     │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

---

## P-23: Admin Logs (`/admin/logs`)

**Estado:** ⚠️ Datos de prueba

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Audit Logs                                            │
│  Usuarios      │                                                        │
│  Issues        │  Filtrar: [Todos ▼] [Hoy ▼] [Buscar...]              │
│  Skills        │                                                        │
│  Scraping      │  ┌─────────────────────────────────────────────────┐   │
│  Métricas      │  │                                                 │   │
│  Logs       ●  │  │  14:32:15 │ INFO  │ Scraping completado        │   │
│  Config        │  │           │       │ bumeran: 89 ofertas nuevas │   │
│                │  │                                                 │   │
│                │  │  14:30:00 │ INFO  │ Scraping iniciado          │   │
│                │  │           │       │ Fuentes: 5                  │   │
│                │  │                                                 │   │
│                │  │  12:15:43 │ WARN  │ LinkedIn rate limit        │   │
│                │  │           │       │ Retry en 5 minutos          │   │
│                │  │                                                 │   │
│                │  │  10:00:00 │ INFO  │ Pipeline NLP completado    │   │
│                │  │           │       │ 234 ofertas procesadas      │   │
│                │  │                                                 │   │
│                │  │  09:45:22 │ INFO  │ Usuario login              │   │
│                │  │           │       │ juan@empresa.com            │   │
│                │  │                                                 │   │
│                │  │  09:30:00 │ INFO  │ Backup BD completado       │   │
│                │  │           │       │ ofertas_backup_20260205.db  │   │
│                │  │                                                 │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  [Cargar más...]        Exportar: [JSON] [CSV]        │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

---

## P-24: Admin Configuración (`/admin/configuracion`)

**Estado:** ⚠️ UI sin backend real

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Configuración del Sistema                             │
│  Usuarios      │                                                        │
│  Issues        │  [General] [Scraping] [NLP] [Matching] [Email] [API]  │
│  Skills        │  ════════                                              │
│  Scraping      │                                                        │
│  Métricas      │  GENERAL (tab activo)                                  │
│  Logs          │                                                        │
│  Config     ●  │  ┌─────────────────────────────────────────────────┐   │
│                │  │                                                 │   │
│                │  │  Nombre del sitio                               │   │
│                │  │  ┌───────────────────────────────────────────┐  │   │
│                │  │  │ MOL - Monitor de Ofertas Laborales        │  │   │
│                │  │  └───────────────────────────────────────────┘  │   │
│                │  │                                                 │   │
│                │  │  URL base                                       │   │
│                │  │  ┌───────────────────────────────────────────┐  │   │
│                │  │  │ https://mol-nextjs.vercel.app             │  │   │
│                │  │  └───────────────────────────────────────────┘  │   │
│                │  │                                                 │   │
│                │  │  Modo mantenimiento                             │   │
│                │  │  [ ] Activar modo mantenimiento                 │   │
│                │  │                                                 │   │
│                │  │  Registro de usuarios                           │   │
│                │  │  [●] Abierto  [ ] Solo invitación  [ ] Cerrado │   │
│                │  │                                                 │   │
│                │  │  [         Guardar cambios         ]            │   │
│                │  │                                                 │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

### Tabs de Configuración

| Tab | Descripción | Estado |
|-----|-------------|--------|
| General | Nombre, URL, mantenimiento | ⚠️ UI only |
| Scraping | Frecuencia, fuentes activas | ⚠️ UI only |
| NLP | Modelo, prompt version | ⚠️ UI only |
| Matching | Pesos, umbrales | ⚠️ UI only |
| Email | SMTP, templates | ⚠️ UI only |
| API | Rate limits, keys | ⚠️ UI only |
