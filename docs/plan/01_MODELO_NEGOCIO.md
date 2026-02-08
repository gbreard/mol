# 1. Modelo de Negocio

> Última actualización: 2026-02-07
> Versión: 2.0 — Modelo híbrido (registro libre + acceso gated + pago dual)

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Features por nivel determinan acceso a pantallas |
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas T-planes, T-suscripciones, T-solicitudes_acceso, T-contenidos |
| [05_USER_FLOWS](./05_USER_FLOWS.md) | Flujos F-01 a F-05 |
| [09_ROADMAP](./09_ROADMAP.md) | Fases de implementación comercial |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Tipos de usuario | 02_ARQUITECTURA (permisos), 06_SEGURIDAD (RLS) |
| Features por nivel | 02_ARQUITECTURA (acceso a rutas) |
| Pricing | 09_ROADMAP, 04_MODELO (T-planes) |
| Flujo de acceso (gated) | 05_USER_FLOWS, 03_WIREFRAMES |

---

## Visión del Producto

Plataforma de **inteligencia del mercado laboral argentino** que combina acceso libre a contenido con acceso controlado al tablero de datos.

> "Inteligencia de datos para un mercado de trabajo y un sistema productivo en transformación"
> — Propuesta narrativa OEDE (2026-02-07)

| Segmento | Propuesta |
|----------|-----------|
| **Público** | Landing + registro libre |
| **Registrado** | Informes, notas y contenido generado desde datos |
| **Suscriptor tablero** | Dashboard completo (previa solicitud + aprobación MOL) |
| **Institucional** | Todo + documentos a demanda (mecanismo de pago institucional) |
| **Admin (OEDE)** | Panel admin + gestión de accesos y contenido |

---

## Flujo de Acceso (Modelo Híbrido)

```
VISITANTE ──────────────── Landing, navegar
     │
     ▼ (se registra)
REGISTRADO ─────────────── Informes, notas, contenido por email
     │                     (CMS genera y distribuye)
     │
     │ (solicita acceso al tablero)
     ▼
SOLICITUD ──────────────── MOL/OEDE revisa y aprueba
     │
     ▼ (aprobado)
FREE TRIAL (7 días) ────── Dashboard con limitaciones (TBD)
     │
     │ (quiere más)
     ▼
SUSCRIPTOR ─────────────── Dashboard completo
     │                     Pago: MercadoPago (individuos/consultoras)
     │                           o mecanismo institucional (organismos)
     ▼
INSTITUCIONAL ──────────── Todo + documentos a demanda
                           Pago: orden de compra / transferencia
```

---

## Tipos de Usuario

### U-VISITANTE
- **Acceso:** Landing, `/precios`, `/informes` (preview)
- **Auth:** No
- **Objetivo:** Convertir a U-REGISTRADO

### U-REGISTRADO
- **Acceso:** Contenido completo (informes, notas, análisis publicados)
- **Auth:** Sí (registro con email)
- **Paga:** No
- **Recibe:** Notificaciones por email de nuevo contenido (link o PDF)
- **Objetivo:** Consumir contenido + eventualmente solicitar acceso al tablero
- **Nota:** NO tiene acceso al dashboard interactivo

### U-TRIAL
- **Acceso:** Dashboard con limitaciones por 7 días
- **Auth:** Sí + aprobación de MOL/OEDE
- **Paga:** No
- **Limitaciones:** TBD (ver [Decisiones Pendientes](#decisiones-pendientes))
- **Flujo:** U-REGISTRADO solicita acceso → OEDE aprueba → 7 días trial
- **Objetivo:** Que valore el dashboard y decida suscribirse

### U-SUSCRIPTOR
- **Acceso:** Dashboard completo + histórico
- **Auth:** Sí + plan activo
- **Paga:** Sí
- **Features:**
  - Histórico completo
  - Exports Excel/PDF
  - Hasta 10 alertas
  - Análisis de empresas
  - Skills Intelligence completo

### U-INSTITUCIONAL
- **Acceso:** Todo de suscriptor + documentos a demanda
- **Auth:** Sí + contrato institucional
- **Paga:** Sí (mecanismo institucional: orden de compra, transferencia, etc.)
- **Features:**
  - Todo de U-SUSCRIPTOR
  - API REST
  - Documentos/reportes a demanda
  - Soporte dedicado

### U-ADMIN
- **Acceso:** Panel admin + gestión de accesos + gestión de contenido
- **Paga:** No (usuarios internos OEDE)
- **Funciones:**
  - Aprobar/rechazar solicitudes de acceso al tablero
  - Publicar contenido (informes, notas) via CMS
  - Monitorear sistema y métricas

---

## Planes y Pricing

| Plan | Precio | Facturación | Dashboard | Contenido |
|------|--------|-------------|-----------|-----------|
| **Registrado** | $0 | - | No | Sí (informes, notas) |
| **Trial** | $0 (7 días) | - | Sí (limitado) | Sí |
| **Suscriptor** | TBD | Mensual | Sí (completo) | Sí |
| **Institucional** | A consultar | Según acuerdo | Sí (completo + API) | Sí + a demanda |

### Decisiones Pendientes

- [ ] **Precio Suscriptor** — No hay benchmark de servicios comparables en Argentina
- [ ] **Limitaciones del Trial** — ¿Qué se restringe en 7 días? Opciones:
  - Solo últimos 7 días de datos (como Free original)
  - Dashboard completo pero sin exports
  - Todo abierto pero con marca de agua / límite de vistas
- [ ] **Proceso de aprobación** — ¿Quién aprueba? ¿Criterios? ¿Automático vs manual?
- [ ] **Mecanismo institucional de pago** — Orden de compra, transferencia bancaria, etc.
- [ ] **Pricing comparativo** — Investigar servicios similares (LinkedIn Talent Insights, Indeed Hiring Lab, Burning Glass)

---

## Features por Nivel (Matriz)

| Feature | Registrado | Trial | Suscriptor | Institucional |
|---------|------------|-------|------------|---------------|
| Contenido/informes | ✓ | ✓ | ✓ | ✓ |
| Email con nuevo contenido | ✓ | ✓ | ✓ | ✓ |
| Dashboard interactivo | ✗ | ✓ (TBD) | ✓ | ✓ |
| Histórico completo | ✗ | TBD | ✓ | ✓ |
| Skills Intelligence | ✗ | TBD | ✓ | ✓ |
| Análisis de empresas | ✗ | ✗ | ✓ | ✓ |
| Export Excel/PDF | ✗ | ✗ | ✓ | ✓ |
| Alertas por email | ✗ | ✗ | ✓ (10) | ✓ (∞) |
| API REST | ✗ | ✗ | ✗ | ✓ |
| Documentos a demanda | ✗ | ✗ | ✗ | ✓ |
| Soporte | - | Email | Email | Dedicado |

---

## Sistema de Contenidos (CMS) — NUEVO

### Requerimiento

Generar y distribuir contenido a usuarios registrados:
- **Fuente:** Datos del dashboard (ofertas, skills, tendencias)
- **Salida:** Documentos/notas/informes
- **Distribución:** Email con link o PDF adjunto (lo más eficiente)

### Funcionalidades CMS

| Función | Descripción | Quién |
|---------|-------------|-------|
| Crear contenido | Generar informe/nota desde datos del dashboard | Admin OEDE |
| Programar envío | Configurar frecuencia (mensual, semanal, ad-hoc) | Admin OEDE |
| Distribuir | Enviar por email a registrados (link o PDF) | Sistema |
| Gestionar | CRUD de contenidos publicados | Admin OEDE |
| Métricas | Aperturas, descargas, clicks | Admin OEDE |

### Decisiones Pendientes CMS

- [ ] ¿Email con link a web o PDF adjunto? (link es más trackeable, PDF es offline)
- [ ] ¿Generación automática desde datos o redacción manual?
- [ ] ¿Segmentación por interés? (ej: solo IT, solo CABA)
- [ ] Herramienta: ¿Custom en Next.js o servicio externo (Resend, SendGrid)?

### Tablas Relacionadas

- `T-contenidos` — Informes/notas publicados
- `T-envios_contenido` — Registro de distribución
- Ver [04_MODELO_DATOS](./04_MODELO_DATOS.md)

---

## Pasarela de Pago (Dual)

### Canal 1: MercadoPago (individuos y consultoras)

**Para:** Consultoras pequeñas, recruiters independientes, investigadores

- Tarjeta de crédito/débito
- Transferencia bancaria
- Efectivo (Pago Fácil, Rapipago)

### Canal 2: Mecanismo Institucional (organismos y gobierno)

**Para:** Ministerios, universidades, organismos internacionales, grandes consultoras

- Orden de compra
- Transferencia bancaria directa
- Facturación a 30/60 días
- Proceso manual (MOL gestiona)

### Integración

- Ver [F-04](./05_USER_FLOWS.md#f-04-webhook-mercadopago) para flujo MercadoPago
- Ver [04_MODELO_DATOS](./04_MODELO_DATOS.md#t-pagos) para tablas
- Ver [06_SEGURIDAD](./06_SEGURIDAD.md) para webhooks

---

## Métricas de Negocio Objetivo

### MVP (3 meses)

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 200 |
| Solicitudes de tablero | 50 |
| Suscriptores activos | 10 |
| Contenidos publicados | 6 |

### 6 meses

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 1,000 |
| Suscriptores activos | 50 |
| Institucionales | 3 |
| Contenidos publicados | 15 |
| Tasa apertura emails | > 30% |

### 1 año

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 5,000 |
| Suscriptores activos | 200 |
| Institucionales | 10 |
| NPS | > 50 |

---

## Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-02-05 | 1.0 | Modelo SaaS clásico (Free/Pro/Enterprise) |
| 2026-02-07 | 2.0 | Modelo híbrido: registro libre + acceso gated + CMS + pago dual. Basado en feedback colegas OEDE |
