# SPEC J — Pendientes de curación manual

**Generado:** 2026-04-25T15:15:51.122995
**Total pendientes:** 18

Para cada regla, agregar el campo `esco_code` correcto en `config/matching_rules_business.json`.

---

## A) Reglas ambiguas (9) — múltiples esco_codes para el mismo label

Hay que decidir cuál esco_code corresponde para cada regla.

### Label: `mozo de almacén/moza de almacén`

Opciones (mismo label aparece en varios esco_codes):
- **`9333.4`**: mozo de almacén/moza de almacén ([http://data.europa.eu/esco/occupation/c84a055d-00fe-4789-a054-f4a62914ff6e])
- **`9333.8`**: mozo de almacén/moza de almacén ([http://data.europa.eu/esco/occupation/bea705fe-06ac-4147-b8e0-6e8ac1208d8f])

Reglas afectadas (7):
- `R32_operario_picking` (forzar_isco actual: 9333)
- `R36_operario_almacen` (forzar_isco actual: 9333)
- `R136_personal_deposito` (forzar_isco actual: 9333)
- `R137_tareas_picking_crossdocking` (forzar_isco actual: 9333)
- `R141_peon_deposito` (forzar_isco actual: 9333)
- `R142_bodeguero` (forzar_isco actual: 9333)
- `R350_operario_deposito_logistica` (forzar_isco actual: 9333)

### Label: `inspector de control de calidad/inspectora de control de calidad`

Opciones (mismo label aparece en varios esco_codes):
- **`7543.10`**: inspector de control de calidad/inspectora de control de calidad ([http://data.europa.eu/esco/occupation/61d9270c-491d-438d-8d41-77ba2e0ef023])
- **`7543.7.2`**: inspector de control de calidad/inspectora de control de calidad ([http://data.europa.eu/esco/occupation/68ad860f-c5cd-420f-840f-993e3e813508])

Reglas afectadas (1):
- `R221_analista_calidad_general` (forzar_isco actual: 7543)

### Label: `herrero/herrera`

Opciones (mismo label aparece en varios esco_codes):
- **`7221.1`**: herrero/herrera ([http://data.europa.eu/esco/occupation/fccecd5d-ad90-41a8-bb89-96d7595abca3])
- **`7221.1.1`**: herrero/herrera ([http://data.europa.eu/esco/occupation/bcffa133-c499-4db4-8e4f-b2d95da3b0fc])

Reglas afectadas (1):
- `R287_herrero` (forzar_isco actual: 7221)

## B) Reglas sin match (9) — label no existe en metadata

El `esco_label` actual no aparece en `esco_occupations_metadata.json`. Buscar variante correcta.

### `R193_supervisor_operaciones`
- esco_label actual: `"supervisor de construcción/supervisora de construcción"`
- forzar_isco actual: `3123`
- Sugerencias posibles:
  - `3123.1.13` — supervisor de instalaciones de aislamiento/supervisora de instalaciones de aislamiento
  - `3123.1.13` — supervisor de instalaciones de aislamiento/supervisora de instalaciones de aislamiento
  - `3315.3` — supervisor de seguros/supervisora de seguros
  - `3315.3` — supervisor de seguros/supervisora de seguros
  - `3122.3.2` — supervisor de montaje de equipamiento de contenedores/supervisora de montaje de equipamiento de contenedores

### `R207_peon_cocina`
- esco_label actual: `"ayudante/ayudanta de cocina"`
- forzar_isco actual: `9412`

### `R209_personal_maestranza`
- esco_label actual: `"limpiador de oficinas/limpiadora de oficinas"`
- forzar_isco actual: `9112`
- Sugerencias posibles:
  - `8160.10` — limpiador de granos de cacao/limpiadora de granos de cacao
  - `8160.10` — limpiador de granos de cacao/limpiadora de granos de cacao
  - `7511.3` — limpiador de pescado/limpiadora de pescado
  - `7511.3` — limpiador de pescado/limpiadora de pescado
  - `9111.1` — limpiador doméstico/limpiadora doméstica

### `R210_telefonista_ventas`
- esco_label actual: `"vendedor en centro de contacto/vendedora en centro de contacto"`
- forzar_isco actual: `5244`
- Sugerencias posibles:
  - `5223.7.21` — vendedor especializado en ferretería y pintura/vendedora especializada en ferretería y pintura
  - `5223.7.21` — vendedor especializado en ferretería y pintura/vendedora especializada en ferretería y pintura
  - `5223.7.16` — vendedor especializado en pescado y mariscos/vendedora especializada en pescado y mariscos
  - `5223.7.16` — vendedor especializado en pescado y mariscos/vendedora especializada en pescado y mariscos
  - `5223.2` — vendedor de piezas de repuesto de automóviles/vendedora de piezas de repuesto de automóviles

### `R212_personal_limpieza`
- esco_label actual: `"limpiador de oficinas/limpiadora de oficinas"`
- forzar_isco actual: `9112`
- Sugerencias posibles:
  - `8160.10` — limpiador de granos de cacao/limpiadora de granos de cacao
  - `8160.10` — limpiador de granos de cacao/limpiadora de granos de cacao
  - `7511.3` — limpiador de pescado/limpiadora de pescado
  - `7511.3` — limpiador de pescado/limpiadora de pescado
  - `9111.1` — limpiador doméstico/limpiadora doméstica

### `R213_asistente_comercial`
- esco_label actual: `"empleado del centro de contacto de información/empleada del centro de contacto de información"`
- forzar_isco actual: `4222`
- Sugerencias posibles:
  - `3342.2` — empleado administrativo en el ámbito jurídico-legal/empleada administrativo en el ámbito jurídico-legal
  - `3342.2` — empleado administrativo en el ámbito jurídico-legal/empleada administrativo en el ámbito jurídico-legal
  - `3343.1` — empleado administrativo/empleada administrativa
  - `3343.1` — empleado administrativo/empleada administrativa
  - `7516.1` — empleado de la sala de curado/empleada de la sala de curado

### `R214_analista_comercial`
- esco_label actual: `"profesional de la publicidad y la comercialización"`
- forzar_isco actual: `2431`
- Sugerencias posibles:
  - `3421.1` — atleta profesional
  - `2320.1.15` — profesor de formación profesional en hostelería/profesora de formación profesional en hostelería
  - `2320.1.15` — profesor de formación profesional en hostelería/profesora de formación profesional en hostelería
  - `3412.4.6` — profesional de apoyo en acogimiento familiar
  - `2320.1.13` — profesor de formación profesional en cocina y gastronomía/profesora de formación profesional en cocina y gastronomía

### `R302_supervisor_obra`
- esco_label actual: `"supervisor de obras/supervisora de obras"`
- forzar_isco actual: `3123`
- Sugerencias posibles:
  - `3123.1.13` — supervisor de instalaciones de aislamiento/supervisora de instalaciones de aislamiento
  - `3123.1.13` — supervisor de instalaciones de aislamiento/supervisora de instalaciones de aislamiento
  - `3315.3` — supervisor de seguros/supervisora de seguros
  - `3315.3` — supervisor de seguros/supervisora de seguros
  - `3122.3.2` — supervisor de montaje de equipamiento de contenedores/supervisora de montaje de equipamiento de contenedores

### `R332_talentos_discapacidad`
- esco_label actual: `"asistente social/asistenta social"`
- forzar_isco actual: `3435`

