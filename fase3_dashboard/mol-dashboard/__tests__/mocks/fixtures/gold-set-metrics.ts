export const mockGoldSetMetrics = {
  total: 112,
  ok: 95,
  errores: 17,
  tasa_acierto: 84.8,
  por_validador: [
    { validador: 'cinvazquez4@gmail.com', total: 36, ok: 30, errores: 6 },
    { validador: 'migracion_inicial', total: 49, ok: 40, errores: 9 },
    { validador: 'dschlese@trabajo.gob.ar', total: 7, ok: 6, errores: 1 },
  ],
  cobertura_por_run: [
    { run_id: 'run_20260516_2052', en_gold: 5, acierto: 4, errores: 1, sin_clasificacion: 0, tasa_acierto: 80.0 },
    { run_id: 'run_20260515_0001', en_gold: 8, acierto: 7, errores: 1, sin_clasificacion: 0, tasa_acierto: 87.5 },
  ],
  casos: [
    {
      id_oferta: '7542392224',
      esco_ok_humano: true,
      isco_esperado: null,
      esco_esperado: null,
      isco_actual: '2511',
      isco_label_actual: 'analista de datos',
      agregado_por: 'cinvazquez4@gmail.com',
      agregado_at: '2026-05-06T00:00:00+00:00',
    },
    {
      id_oferta: '8085763783',
      esco_ok_humano: false,
      isco_esperado: '3323',
      esco_esperado: 'agente de compras',
      isco_actual: '3323',
      isco_label_actual: 'comprador',
      agregado_por: 'cinvazquez4@gmail.com',
      agregado_at: '2026-05-06T00:00:00+00:00',
    },
  ],
}
