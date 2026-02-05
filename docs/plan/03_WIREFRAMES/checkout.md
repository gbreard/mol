# Wireframes: Checkout

> Última actualización: 2026-02-05

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](../02_ARQUITECTURA_PANTALLAS.md) | Lista de pantallas P-06 a P-08 |
| [01_MODELO_NEGOCIO](../01_MODELO_NEGOCIO.md) | Define pasarela MercadoPago |
| [05_USER_FLOWS](../05_USER_FLOWS.md) | Flujo F-02: Checkout |

---

## P-06: Checkout (`/checkout`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                               Pago seguro 🔒                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐       │
│  │                             │  │                             │       │
│  │   RESUMEN DE TU PEDIDO      │  │      MÉTODO DE PAGO         │       │
│  │                             │  │                             │       │
│  │   Plan: PRO                 │  │  ┌───────────────────────┐  │       │
│  │   Período: Mensual          │  │  │                       │  │       │
│  │                             │  │  │    [MercadoPago]      │  │       │
│  │   ───────────────────       │  │  │                       │  │       │
│  │   Subtotal:    $XX.XXX      │  │  │   Tarjeta de crédito  │  │       │
│  │   IVA (21%):   $X.XXX       │  │  │   Tarjeta de débito   │  │       │
│  │   ───────────────────       │  │  │   Transferencia       │  │       │
│  │   TOTAL:       $XX.XXX      │  │  │   Efectivo            │  │       │
│  │                             │  │  │                       │  │       │
│  │                             │  │  └───────────────────────┘  │       │
│  │   Incluye:                  │  │                             │       │
│  │   ✓ Histórico completo      │  │  Al continuar serás        │       │
│  │   ✓ Exports ilimitados      │  │  redirigido a MercadoPago  │       │
│  │   ✓ Alertas por email       │  │  para completar el pago.   │       │
│  │   ✓ Análisis de empresas    │  │                             │       │
│  │                             │  │                             │       │
│  │   Renovación automática     │  │  [    Pagar $XX.XXX    ]   │       │
│  │   Cancelá cuando quieras    │  │                             │       │
│  │                             │  │                             │       │
│  └─────────────────────────────┘  └─────────────────────────────┘       │
│                                                                          │
│  🔒 Pago procesado por MercadoPago. No almacenamos datos de tarjeta.    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Notas de Implementación

- **Integración:** SDK MercadoPago para Argentina
- **Métodos:** Tarjeta crédito/débito, transferencia bancaria, efectivo (Pago Fácil, Rapipago)
- **Seguridad:** PCI DSS compliance via MercadoPago
- **Moneda:** ARS (pesos argentinos)

---

## P-07: Checkout Éxito (`/checkout/exito`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                                                                          │
│                                                                          │
│         ┌─────────────────────────────────────────────┐                 │
│         │                                             │                 │
│         │              ✓                              │                 │
│         │           (verde)                           │                 │
│         │                                             │                 │
│         │      ¡Pago completado con éxito!            │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  Plan: PRO                                  │                 │
│         │  Monto: $15,000 ARS                         │                 │
│         │  Próximo cobro: 05/03/2026                  │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  Tu cuenta ya está activa con acceso        │                 │
│         │  completo al histórico de datos.            │                 │
│         │                                             │                 │
│         │  Te enviamos un email de confirmación       │                 │
│         │  a usuario@empresa.com                      │                 │
│         │                                             │                 │
│         │  [      Ir al Dashboard      ]              │                 │
│         │                                             │                 │
│         │  [    Descargar comprobante    ]            │                 │
│         │                                             │                 │
│         └─────────────────────────────────────────────┘                 │
│                                                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Acciones Post-Éxito

1. Actualizar `suscripciones` en BD (estado = 'activa')
2. Enviar email de confirmación
3. Registrar pago en tabla `pagos`
4. Redirect a `/dashboard`

---

## P-08: Checkout Cancelado (`/checkout/cancelado`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                                                                          │
│                                                                          │
│         ┌─────────────────────────────────────────────┐                 │
│         │                                             │                 │
│         │              ✗                              │                 │
│         │           (rojo)                            │                 │
│         │                                             │                 │
│         │      El pago no pudo completarse            │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  Motivo: Fondos insuficientes               │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  No te preocupes, podés intentar            │                 │
│         │  nuevamente con otro método de pago.        │                 │
│         │                                             │                 │
│         │  [    Reintentar pago    ]                  │                 │
│         │                                             │                 │
│         │  [    Elegir otro plan    ]                 │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  ¿Problemas? Contactanos:                   │                 │
│         │  soporte@mol.gob.ar                         │                 │
│         │                                             │                 │
│         └─────────────────────────────────────────────┘                 │
│                                                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Motivos de Rechazo Comunes

| Código MP | Motivo | Mensaje Usuario |
|-----------|--------|-----------------|
| `cc_rejected_insufficient_amount` | Fondos insuficientes | "Fondos insuficientes" |
| `cc_rejected_bad_filled_card_number` | Número incorrecto | "Verificá el número de tarjeta" |
| `cc_rejected_call_for_authorize` | Llamar al banco | "Contactá a tu banco para autorizar" |
| `cc_rejected_high_risk` | Rechazado por riesgo | "Pago rechazado. Probá otro método" |
