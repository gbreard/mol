# MOL Dashboard - Documentación de Planificación

> Última actualización: 2026-02-05

## Mapa de Documentos

```
                           ┌─────────────────┐
                           │   INDEX.md      │
                           │   (este archivo)│
                           └────────┬────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ 01_MODELO       │      │ 02_ARQUITECTURA │      │ 03_WIREFRAMES/  │
│ _NEGOCIO        │◄────►│ _PANTALLAS      │◄────►│ (25 pantallas)  │
│                 │      │                 │      │                 │
│ U-FREE, U-PRO   │      │ P-01 a P-25     │      │ publicas.md     │
│ U-ENTERPRISE    │      │ Rutas, permisos │      │ checkout.md     │
│ U-ADMIN         │      │                 │      │ suscriptor.md   │
└────────┬────────┘      └────────┬────────┘      │ cuenta.md       │
         │                        │               │ admin.md        │
         │               ┌────────┴────────┐      └─────────────────┘
         │               │                 │
         │               ▼                 ▼
         │      ┌─────────────────┐ ┌─────────────────┐
         │      │ 04_MODELO       │ │ 05_USER_FLOWS   │
         │      │ _DATOS          │ │                 │
         │      │                 │ │ F-01 a F-04     │
         │      │ T-planes        │ │ Registro,       │
         │      │ T-suscripciones │ │ Checkout,       │
         │      │ T-pagos         │ │ Dashboard       │
         │      └────────┬────────┘ └─────────────────┘
         │               │
         │   ┌───────────┴───────────┐
         │   │                       │
         ▼   ▼                       ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ 06_SEGURIDAD    │      │ 07_ESCALABILIDAD│      │ 08_PROPUESTA    │
│                 │      │                 │      │ _VALOR          │
│ S-01 a S-17     │      │ E-01 a E-15     │      │                 │
│ 4 críticos      │      │ 3 críticos      │      │ V-01 a V-15     │
│ 6 altos         │      │ 5 altos         │      │ 4 críticos      │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │ 09_ROADMAP      │
                        │                 │
                        │ Fase 0-4        │
                        │ Prioridades     │
                        │ Dependencias    │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ 10_OBSERVA-     │
                        │ BILIDAD         │
                        │                 │
                        │ Mapa pantallas  │
                        │ Pipeline 3 fases│
                        │ Métricas vivo   │
                        └─────────────────┘
```

## Estado Actual

| Métrica | Valor |
|---------|-------|
| Pantallas existentes | 12 |
| Pantallas por crear | 13 |
| **Total pantallas** | **25** |
| Issues críticos | 11 |
| Issues altos | 17 |
| Issues medios | 19 |
| **Total issues técnicos** | **47** |
| **Issues de usuario** | **9** |

### Issues de Usuario Activos (admin@oede.gob.ar)

| Pantalla | Issues | Temas |
|----------|--------|-------|
| P-09 Dashboard | 6 | Exports, Filtros, Rediseño |
| P-10 Skills | 3 | Perfiles, Indicadores mercado |

→ Ver [ANALISIS_ISSUES_USUARIO](./ANALISIS_ISSUES_USUARIO.md) para detalle

## Quick Links

### Por Área de Trabajo

| Área | Documento | Cuándo usar |
|------|-----------|-------------|
| Modelo de negocio | [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md) | Definir usuarios, planes, pricing |
| Pantallas | [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Agregar/modificar rutas |
| Wireframes | [03_WIREFRAMES/](./03_WIREFRAMES/) | Diseñar UI |
| Base de datos | [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas, SQL |
| Flujos | [05_USER_FLOWS](./05_USER_FLOWS.md) | Journeys de usuario |
| Seguridad | [06_SEGURIDAD](./06_SEGURIDAD.md) | Vulnerabilidades, RLS |
| Performance | [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) | Cache, índices |
| Features | [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md) | Qué falta vs competidores |
| Planificación | [09_ROADMAP](./09_ROADMAP.md) | Fases, prioridades |
| Observabilidad | [10_OBSERVABILIDAD](./10_OBSERVABILIDAD.md) | Monitoreo, métricas, arquitectura visual |
| **Issues Usuario** | [ANALISIS_ISSUES_USUARIO](./ANALISIS_ISSUES_USUARIO.md) | Feedback, priorización features |

### Por Urgencia

| Prioridad | Documento | Issues |
|-----------|-----------|--------|
| **BLOQUEANTE** | [06_SEGURIDAD](./06_SEGURIDAD.md) | S-01 a S-04 |
| Alta | [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) | E-01 a E-03 |
| Alta | [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md) | V-01 a V-04 |
| Alta | [ANALISIS_ISSUES_USUARIO](./ANALISIS_ISSUES_USUARIO.md) | 9 issues de usuario |
| Media | [09_ROADMAP](./09_ROADMAP.md) | Planificar fases |

## Sistema de IDs

| Prefijo | Tipo | Rango | Documento |
|---------|------|-------|-----------|
| `P-` | Pantalla | P-01 a P-25 | [02_ARQUITECTURA](./02_ARQUITECTURA_PANTALLAS.md) |
| `U-` | Usuario | U-FREE, U-PRO, U-ENTERPRISE, U-ADMIN | [01_MODELO](./01_MODELO_NEGOCIO.md) |
| `T-` | Tabla SQL | T-planes, T-suscripciones, etc. | [04_MODELO](./04_MODELO_DATOS.md) |
| `F-` | Flujo | F-01 a F-04 | [05_USER_FLOWS](./05_USER_FLOWS.md) |
| `S-` | Seguridad | S-01 a S-17 | [06_SEGURIDAD](./06_SEGURIDAD.md) |
| `E-` | Escalabilidad | E-01 a E-15 | [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) |
| `V-` | Valor | V-01 a V-15 | [08_PROPUESTA](./08_PROPUESTA_VALOR.md) |
| `O-` | Observabilidad | O-01 a O-XX | [10_OBSERVABILIDAD](./10_OBSERVABILIDAD.md) |

## Cómo Usar Esta Documentación

### Para Agregar una Pantalla Nueva

1. Definir en [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) (asignar P-XX)
2. Verificar permisos en [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md)
3. Crear wireframe en [03_WIREFRAMES/](./03_WIREFRAMES/) correspondiente
4. Si usa tablas nuevas, agregar en [04_MODELO_DATOS](./04_MODELO_DATOS.md)
5. Si tiene flujo especial, agregar en [05_USER_FLOWS](./05_USER_FLOWS.md)

### Para Resolver un Issue de Seguridad

1. Ver issue en [06_SEGURIDAD](./06_SEGURIDAD.md)
2. Verificar pantallas afectadas (links a P-XX)
3. Verificar tablas afectadas (links a T-XX)
4. Actualizar [09_ROADMAP](./09_ROADMAP.md) cuando se resuelva

### Para Planificar Trabajo

1. Ver estado general en este INDEX
2. Revisar [09_ROADMAP](./09_ROADMAP.md) para fases
3. Elegir dimensión a trabajar (seguridad, pantallas, etc.)
4. Abrir documento específico
