# Wireframes: Cuenta

> Última actualización: 2026-02-05

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](../02_ARQUITECTURA_PANTALLAS.md) | Lista de pantallas P-14 a P-16 |
| [04_MODELO_DATOS](../04_MODELO_DATOS.md) | Tablas suscripciones, pagos |
| [01_MODELO_NEGOCIO](../01_MODELO_NEGOCIO.md) | Gestión de planes |

---

## P-14: Mi Cuenta / Perfil (`/cuenta`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │
│  │                 │  │                                             │   │
│  │   Mi Cuenta     │  │  INFORMACIÓN PERSONAL                       │   │
│  │   ─────────     │  │                                             │   │
│  │                 │  │  Nombre                                     │   │
│  │   [•] Perfil    │  │  ┌─────────────────────────────────────┐    │   │
│  │   [ ] Suscrip.  │  │  │ Juan Pérez                          │    │   │
│  │   [ ] Facturac. │  │  └─────────────────────────────────────┘    │   │
│  │                 │  │                                             │   │
│  │                 │  │  Email                                      │   │
│  │                 │  │  ┌─────────────────────────────────────┐    │   │
│  │                 │  │  │ juan@empresa.com                    │    │   │
│  │                 │  │  └─────────────────────────────────────┘    │   │
│  │                 │  │                                             │   │
│  │                 │  │  Empresa                                    │   │
│  │                 │  │  ┌─────────────────────────────────────┐    │   │
│  │                 │  │  │ Consultora ABC                      │    │   │
│  │                 │  │  └─────────────────────────────────────┘    │   │
│  │                 │  │                                             │   │
│  │                 │  │  [       Guardar cambios       ]            │   │
│  │                 │  │                                             │   │
│  │                 │  │  ─────────────────────────────────────      │   │
│  │                 │  │                                             │   │
│  │                 │  │  SEGURIDAD                                  │   │
│  │                 │  │  [ Cambiar contraseña ]                     │   │
│  │                 │  │                                             │   │
│  └─────────────────┘  └─────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Campos del Perfil

| Campo | Editable | Validación |
|-------|----------|------------|
| Nombre | ✓ | Requerido, 2-100 chars |
| Email | ✗ | Solo lectura |
| Empresa | ✓ | Opcional, 0-200 chars |
| Contraseña | Via modal | Mín 12 chars |

---

## P-15: Suscripción (`/cuenta/suscripcion`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │
│  │                 │  │                                             │   │
│  │   Mi Cuenta     │  │  MI SUSCRIPCIÓN                             │   │
│  │   ─────────     │  │                                             │   │
│  │                 │  │  ┌─────────────────────────────────────┐    │   │
│  │   [ ] Perfil    │  │  │                                     │    │   │
│  │   [•] Suscrip.  │  │  │  Plan actual: PRO                   │    │   │
│  │   [ ] Facturac. │  │  │  Estado: ● Activa                   │    │   │
│  │                 │  │  │                                     │    │   │
│  │                 │  │  │  Precio: $15,000 ARS/mes            │    │   │
│  │                 │  │  │  Próximo cobro: 05/03/2026          │    │   │
│  │                 │  │  │  Método: Visa ****4532              │    │   │
│  │                 │  │  │                                     │    │   │
│  │                 │  │  └─────────────────────────────────────┘    │   │
│  │                 │  │                                             │   │
│  │                 │  │  BENEFICIOS DE TU PLAN                      │   │
│  │                 │  │  ✓ Acceso a histórico completo              │   │
│  │                 │  │  ✓ Exports ilimitados (Excel, PDF)          │   │
│  │                 │  │  ✓ Hasta 10 alertas configuradas            │   │
│  │                 │  │  ✓ Análisis de empresas                     │   │
│  │                 │  │  ✗ Acceso API (solo Enterprise)             │   │
│  │                 │  │                                             │   │
│  │                 │  │  ─────────────────────────────────────      │   │
│  │                 │  │                                             │   │
│  │                 │  │  [Cambiar método de pago]                   │   │
│  │                 │  │  [Upgrade a Enterprise]                     │   │
│  │                 │  │  [Cancelar suscripción]                     │   │
│  │                 │  │                                             │   │
│  └─────────────────┘  └─────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Estados de Suscripción

| Estado | Descripción | Acciones Disponibles |
|--------|-------------|---------------------|
| `activa` | Pago al día | Cancelar, Upgrade |
| `trial` | Período de prueba | Convertir a pago |
| `vencida` | Pago pendiente | Renovar |
| `cancelada` | Cancelada por usuario | Reactivar |

### Flujo de Cancelación

1. Click "Cancelar suscripción"
2. Modal de confirmación con motivo
3. Opción de feedback (encuesta)
4. Confirmación final
5. Acceso hasta fin del período pagado

---

## P-16: Facturación (`/cuenta/facturacion`)

**Plan requerido:** U-PRO (U-FREE no tiene facturas)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │
│  │                 │  │                                             │   │
│  │   Mi Cuenta     │  │  HISTORIAL DE FACTURACIÓN                   │   │
│  │   ─────────     │  │                                             │   │
│  │                 │  │  Datos de facturación:                      │   │
│  │   [ ] Perfil    │  │  Razón social: Consultora ABC S.A.          │   │
│  │   [ ] Suscrip.  │  │  CUIT: 30-12345678-9                        │   │
│  │   [•] Facturac. │  │  [Editar datos de facturación]              │   │
│  │                 │  │                                             │   │
│  │                 │  │  ─────────────────────────────────────      │   │
│  │                 │  │                                             │   │
│  │                 │  │  FACTURAS                                   │   │
│  │                 │  │  ┌────────────────────────────────────┐     │   │
│  │                 │  │  │ Fecha      │ Concepto    │ Monto   │     │   │
│  │                 │  │  ├────────────┼─────────────┼─────────┤     │   │
│  │                 │  │  │ 05/02/2026 │ PRO Febrero │ $15,000 │ [⬇] │   │
│  │                 │  │  │ 05/01/2026 │ PRO Enero   │ $15,000 │ [⬇] │   │
│  │                 │  │  │ 05/12/2025 │ PRO Diciem. │ $15,000 │ [⬇] │   │
│  │                 │  │  │ 05/11/2025 │ PRO Noviem. │ $15,000 │ [⬇] │   │
│  │                 │  │  └────────────────────────────────────┘     │   │
│  │                 │  │                                             │   │
│  │                 │  │  [Ver más facturas...]                      │   │
│  │                 │  │                                             │   │
│  └─────────────────┘  └─────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Datos de Facturación

| Campo | Descripción | Validación |
|-------|-------------|------------|
| Razón social | Nombre empresa/persona | Requerido para factura |
| CUIT/CUIL | Identificador fiscal | Formato argentino |
| Condición IVA | Responsable, Monotributo, etc. | Lista desplegable |
| Dirección | Dirección fiscal | Opcional |

### Descarga de Facturas

- Formato: PDF
- Incluye: Detalle del servicio, IVA, totales
- Válida para AFIP (si se configura correctamente)
