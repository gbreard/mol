// Mock data for config-editor preview & suggestions tests

export const mockPreviewImpact = {
  total_afectadas: 45,
  cambiarian: 12,
  ya_correctas: 33,
  distribucion_isco_actual: [
    { isco_code: '5223', cantidad: 20 },
    { isco_code: '1221', cantidad: 15 },
    { isco_code: '2431', cantidad: 10 },
  ],
  ejemplos: [
    { titulo: 'Gerente de Ventas', isco_actual: '5223', isco_nuevo: '1221', estado: 'CAMBIA' },
    { titulo: 'Gerente Comercial', isco_actual: '1221', isco_nuevo: '1221', estado: 'OK' },
    { titulo: 'Gerente de Ventas Zona Norte', isco_actual: '2431', isco_nuevo: '1221', estado: 'CAMBIA' },
  ],
}

export const mockPreviewImpactEmpty = {
  total_afectadas: 0,
  cambiarian: 0,
  ya_correctas: 0,
  distribucion_isco_actual: [],
  ejemplos: [],
}

export const mockSugerencias = [
  {
    patron_titulo: 'gerente de ventas',
    isco_sugerido: '1221',
    ofertas_afectadas: 45,
    correcciones: 8,
    corregido_por: 'cynthia@oede.gob.ar',
    tipo_sugerencia: 'correccion_titulo',
    isco_actual: '5223',
    label_actual: 'Vendedor de tiendas',
  },
  {
    patron_titulo: 'data engineer',
    isco_sugerido: '2521',
    ofertas_afectadas: 23,
    correcciones: 0,
    corregido_por: null,
    tipo_sugerencia: 'semantico_bajo',
    isco_actual: '2511',
    label_actual: 'Analista de sistemas',
  },
]

export const mockSugerenciasEmpty: any[] = []

export const mockConfigOverride = {
  config_key: 'matching_rules_business',
  json_value: {
    reglas_forzar_isco: {
      descripcion: 'Reglas que fuerzan un codigo ISCO especifico',
      R1_gerente_ventas: {
        nombre: 'Gerente de Ventas',
        prioridad: 1,
        condicion: { titulo_contiene: 'gerente de ventas' },
        forzar_isco: '1221',
        esco_label: 'director comercial/directora comercial',
      },
      R2_contador: {
        nombre: 'Contador',
        prioridad: 2,
        condicion: { titulo_contiene: 'contador' },
        forzar_isco: '2411',
        esco_label: 'contador/contadora',
      },
    },
  },
  version: 3,
  updated_by: 'admin@oede.gob.ar',
  updated_at: '2026-03-22T15:00:00Z',
  changelog: [
    { timestamp: '2026-03-20T10:00:00Z', user: 'admin@oede.gob.ar', version: 1, action: 'Creación inicial' },
    { timestamp: '2026-03-21T14:00:00Z', user: 'admin@oede.gob.ar', version: 2, action: 'Agregar regla contador' },
    { timestamp: '2026-03-22T15:00:00Z', user: 'admin@oede.gob.ar', version: 3, action: 'Editado 2 reglas' },
  ],
}

export const mockConfigUpsertResult = {
  config_key: 'matching_rules_business',
  json_value: {},
  version: 4,
  updated_by: 'admin@oede.gob.ar',
  updated_at: '2026-03-22T16:00:00Z',
  changelog: [],
}
