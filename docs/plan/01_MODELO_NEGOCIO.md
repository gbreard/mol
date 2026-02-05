# 1. Modelo de Negocio

> Última actualización: 2026-02-05

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Features por plan determinan acceso a pantallas |
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas T-planes, T-suscripciones |
| [09_ROADMAP](./09_ROADMAP.md) | Fases de implementación comercial |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Tipos de usuario | 02_ARQUITECTURA (permisos), 06_SEGURIDAD (RLS) |
| Features por plan | 02_ARQUITECTURA (acceso a rutas) |
| Pricing | 09_ROADMAP (MercadoPago), 04_MODELO (T-planes) |

---

## Visión del Producto

Plataforma SaaS que **vende acceso** a inteligencia del mercado laboral argentino.

| Segmento | Propuesta |
|----------|-----------|
| **Público** | Landing + informes PDF gratuitos |
| **Suscriptores** | Dashboard completo (empresas, consultoras, recruiters) |
| **Admin (OEDE)** | Solo visualización del sistema (no paga) |

---

## Tipos de Usuario

### U-VISITANTE
- **Acceso:** Landing, `/precios`, `/informes`, `/skills` (limitado)
- **Paga:** No
- **Objetivo:** Convertir a U-FREE o U-PRO

### U-FREE
- **Acceso:** Dashboard con datos de últimos 7 días
- **Paga:** No (registro con email)
- **Limitaciones:**
  - Sin exports
  - Sin alertas
  - Sin análisis de empresas
  - Sin histórico

### U-PRO
- **Acceso:** Dashboard completo + histórico
- **Paga:** Sí (mensual)
- **Precio:** $XX.XXX ARS/mes (definir)
- **Features:**
  - Histórico completo
  - Exports Excel/PDF
  - Hasta 10 alertas
  - Análisis de empresas

### U-ENTERPRISE
- **Acceso:** Todo + API + reportes custom
- **Paga:** Sí (anual, precio custom)
- **Features:**
  - Todo de PRO
  - API REST
  - Webhooks
  - Soporte dedicado
  - Reportes personalizados
  - SLA 99.9%

### U-ADMIN
- **Acceso:** Panel admin (solo lectura)
- **Paga:** No (usuarios internos OEDE)
- **Objetivo:** Monitorear sistema, ver métricas

---

## Planes y Pricing

| Plan | Precio | Facturación | Días Histórico |
|------|--------|-------------|----------------|
| **Free** | $0 | - | 7 días |
| **Pro** | $XX.XXX | Mensual | Ilimitado |
| **Enterprise** | Contactar | Anual | Ilimitado |

### Decisiones Pendientes

- [ ] Definir precio PRO en ARS
- [ ] Definir precio ENTERPRISE (¿por usuario? ¿por empresa?)
- [ ] ¿Trial de PRO por X días?
- [ ] ¿Descuento anual para PRO?

---

## Features por Plan (Matriz)

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Dashboard con filtros | ✓ | ✓ | ✓ |
| Datos últimos 7 días | ✓ | ✓ | ✓ |
| Histórico completo | ✗ | ✓ | ✓ |
| Skills Intelligence básico | ✓ | ✓ | ✓ |
| Skills Intelligence completo | ✗ | ✓ | ✓ |
| Análisis de empresas | ✗ | ✓ | ✓ |
| Export Excel | ✗ | ✓ | ✓ |
| Export PDF | ✗ | ✓ | ✓ |
| Alertas por email | ✗ | ✓ (10) | ✓ (∞) |
| API REST | ✗ | ✗ | ✓ |
| Webhooks | ✗ | ✗ | ✓ |
| Reportes custom | ✗ | ✗ | ✓ |
| Soporte | Email | Email | Dedicado |
| SLA | - | - | 99.9% |

---

## Métricas de Negocio Objetivo

### MVP (3 meses)

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 100 |
| Usuarios Pro | 10 |
| MRR | $150k ARS |

### 6 meses

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 1,000 |
| Usuarios Pro | 100 |
| MRR | $1.5M ARS |
| Churn mensual | < 5% |

### 1 año

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 5,000 |
| Usuarios Pro | 500 |
| Enterprise | 10 |
| MRR | $7.5M ARS |
| NPS | > 50 |

---

## Pasarela de Pago

**Decisión:** MercadoPago (Argentina, pesos)

### Métodos Aceptados
- Tarjeta de crédito
- Tarjeta de débito
- Transferencia bancaria
- Efectivo (Pago Fácil, Rapipago)

### Integración
- Ver [F-02](./05_USER_FLOWS.md#f-02-checkout) para flujo
- Ver [04_MODELO_DATOS](./04_MODELO_DATOS.md#t-pagos) para tablas
- Ver [06_SEGURIDAD](./06_SEGURIDAD.md) para webhooks
