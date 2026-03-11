# MOL Dashboard - Documentación de Planificación

> Ultima actualizacion: 2026-02-11

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
│ _NEGOCIO v2.0   │◄────►│ _PANTALLAS v2.0 │◄────►│ (30 pantallas)  │
│                 │      │                 │      │                 │
│ U-VISITANTE     │      │ P-01 a P-30     │      │ publicas.md     │
│ U-REGISTRADO    │      │ 4 niveles:      │      │ contenido.md    │
│ U-TRIAL         │      │ público,        │      │ checkout.md     │
│ U-SUSCRIPTOR    │      │ registrado,     │      │ suscriptor.md   │
│ U-INSTITUCIONAL │      │ gated, admin    │      │ cuenta.md       │
│ U-ADMIN         │      │                 │      │ admin.md        │
└────────┬────────┘      └────────┬────────┘      └─────────────────┘
         │                        │
         │               ┌────────┴────────┐
         │               │                 │
         │               ▼                 ▼
         │      ┌─────────────────┐ ┌─────────────────┐
         │      │ 04_MODELO       │ │ 05_USER_FLOWS   │
         │      │ _DATOS v2.2     │ │ v2.0            │
         │      │                 │ │                 │
         │      │ T-planes        │ │ F-01 a F-05     │
         │      │ T-suscripciones │ │ Registro libre, │
         │      │ T-solicitudes   │ │ Acceso gated,   │
         │      │ T-contenidos    │ │ Checkout dual,  │
         │      │ T-envios        │ │ Webhook MP,     │
         │      │ T-pagos         │ │ CMS             │
         │      └────────┬────────┘ └─────────────────┘
         │               │
         │   ┌───────────┴───────────┐
         │   │                       │
         ▼   ▼                       ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ 06_SEGURIDAD    │      │ 07_ESCALABILIDAD│      │ 08_PROPUESTA    │
│                 │      │                 │      │ _VALOR          │
│ S-01 a S-17     │      │ E-01 a E-15     │      │                 │
│ 4 críticos      │      │ 3 críticos      │      │ V-01 a V-16     │
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
                        │ + CMS           │
                        │ + Aprobación    │
                        │ + Pago dual     │
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
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ 13_LABORATORIO  │
                        │ _INDICADORES    │
                        │                 │
                        │ I-01 a I-13     │
                        │ Ciclo de vida   │
                        │ Priorizacion    │
                        └─────────────────┘
```

## Estado Actual

| Métrica | Valor |
|---------|-------|
| Pantallas existentes | 10 |
| Pantallas por crear | 20 |
| **Total pantallas** | **30** |
| Issues críticos | 11 |
| Issues altos | 17 |
| Issues medios | 19 |
| **Total issues técnicos** | **47** |
| **Issues de usuario** | **12** |

### Modelo de Negocio v2.0

| Componente | Estado |
|------------|--------|
| Registro libre | Definido |
| Acceso gated (solicitud + aprobación) | Definido |
| Pago dual (MercadoPago + institucional) | Definido |
| CMS (contenidos + distribución) | Definido |
| Pricing suscriptor | TBD |
| Limitaciones trial | TBD |

### Issues de Usuario (admin@oede.gob.ar)

| Estado | Cantidad | Detalle |
|--------|----------|---------|
| ✅ Resueltos | 7 | Sprint 1 + Sprint 2 + Sprint 5 |
| 🔨 En desarrollo | 1 | Sprint 5 |
| ⏳ Pendientes | 4 | Sprint 3 + Sprint 4 |

| Pantalla | Resueltos | Pendientes |
|----------|-----------|------------|
| P-09 Dashboard | 4 (#1,#2,#4,#11) | 4 (#3,#5,#6,#12) |
| P-10 Skills | 3 (#8,#9,#10) | 1 (#7) |

### Sprints

| Sprint | Issues | Estado |
|--------|--------|--------|
| 1 | #1, #2, #4 | ✅ Completado |
| 2 | #8, #9, #10 | ✅ Completado |
| 3 | #3, #5 | ⏳ Pendiente validación |
| 4 | #6, #7 | ⏳ Pendiente validación |
| 5 | #11, #12 | 🔨 En progreso (#11 resuelto, #12 en desarrollo) |

> Ver [ANALISIS_ISSUES_USUARIO](./ANALISIS_ISSUES_USUARIO.md) para detalle

## Quick Links

### Por Área de Trabajo

| Área | Documento | Cuándo usar |
|------|-----------|-------------|
| Modelo de negocio | [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md) | Definir usuarios, niveles, pricing |
| Pantallas | [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Agregar/modificar rutas |
| Wireframes | [03_WIREFRAMES/](./03_WIREFRAMES/) | Diseñar UI |
| Base de datos | [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas, SQL |
| Flujos | [05_USER_FLOWS](./05_USER_FLOWS.md) | Journeys de usuario |
| Seguridad | [06_SEGURIDAD](./06_SEGURIDAD.md) | Vulnerabilidades, RLS |
| Performance | [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) | Cache, índices |
| Features | [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md) | Qué falta vs competidores |
| Planificación | [09_ROADMAP](./09_ROADMAP.md) | Fases, prioridades |
| Observabilidad | [10_OBSERVABILIDAD](./10_OBSERVABILIDAD.md) | Monitoreo, métricas, arquitectura visual |
| Configuración Admin | [11_CONFIGURACION_ADMIN](./11_CONFIGURACION_ADMIN.md) | /admin/configuracion - Fases 1-3 |
| **Insights Sistema** | [12_INSIGHTS_SISTEMA](./12_INSIGHTS_SISTEMA.md) | Performance + ubicación insights |
| **Issues Usuario** | [ANALISIS_ISSUES_USUARIO](./ANALISIS_ISSUES_USUARIO.md) | Feedback, priorización features |
| **Lab. Indicadores** | [13_LABORATORIO_INDICADORES](./13_LABORATORIO_INDICADORES.md) | Indicadores experimentales |
| **Skills Emergentes** | [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md#v-17-skills-emergentes-escomol) | V-17: ESCO+MOL, skills no cubiertas |

### Por Urgencia

| Prioridad | Documento | Issues |
|-----------|-----------|--------|
| **BLOQUEANTE** | [06_SEGURIDAD](./06_SEGURIDAD.md) | S-01 a S-04 |
| Alta | [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) | E-01 a E-03 |
| Alta | [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md) | V-01 a V-04 |
| Alta | [ANALISIS_ISSUES_USUARIO](./ANALISIS_ISSUES_USUARIO.md) | 12 issues de usuario |
| Media | [09_ROADMAP](./09_ROADMAP.md) | Planificar fases |

## Sistema de IDs

| Prefijo | Tipo | Rango | Documento |
|---------|------|-------|-----------|
| `P-` | Pantalla | P-01 a P-30 | [02_ARQUITECTURA](./02_ARQUITECTURA_PANTALLAS.md) |
| `U-` | Usuario | U-VISITANTE, U-REGISTRADO, U-TRIAL, U-SUSCRIPTOR, U-INSTITUCIONAL, U-ADMIN | [01_MODELO](./01_MODELO_NEGOCIO.md) |
| `T-` | Tabla SQL | T-planes, T-suscripciones, T-solicitudes_acceso, T-contenidos, T-envios_contenido, T-tension_ocupaciones, etc. | [04_MODELO](./04_MODELO_DATOS.md) |
| `F-` | Flujo | F-01 a F-05 | [05_USER_FLOWS](./05_USER_FLOWS.md) |
| `S-` | Seguridad | S-01 a S-17 | [06_SEGURIDAD](./06_SEGURIDAD.md) |
| `E-` | Escalabilidad | E-01 a E-15 | [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) |
| `V-` | Valor | V-01 a V-16 | [08_PROPUESTA](./08_PROPUESTA_VALOR.md) |
| `O-` | Observabilidad | O-01 a O-XX | [10_OBSERVABILIDAD](./10_OBSERVABILIDAD.md) |

## Cómo Usar Esta Documentación

### Para Agregar una Pantalla Nueva

1. Definir en [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) (asignar P-XX)
2. Verificar nivel de acceso en [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md)
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
