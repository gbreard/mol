export const mockPipelineStatusRPC = {
  fases: {
    scraping: {
      estado: 'warning',
      ultimo_scraping: '2026-03-13',
      dias_desde_scraping: 7,
      ofertas_totales: 37785,
      ofertas_activas: 18316,
      fuentes: {
        caba: 12,
        indeed: 1697,
        bumeran: 691,
        zonajobs: 1773,
        computrabajo: 13716,
        portalempleo: 427,
      },
    },
    nlp: {
      estado: 'warning',
      procesadas: 37776,
      pendientes: 19,
      ultimo_run: 'run_20260320_1855',
    },
    matching: {
      estado: 'ok',
      con_matching: 37776,
      pendientes: 0,
      validadas: 37776,
      errores_sin_resolver: 0,
      reglas_negocio: 0,
    },
    sync: {
      estado: 'ok',
      en_supabase: 37776,
      pendientes: 0,
    },
  },
  alertas: [
    {
      nivel: 'warning',
      mensaje: 'Scraping sin ejecutar hace 7 días',
      accion: 'lanzar_scraping',
      detalle: 'Último scraping: 2026-03-13',
    },
    {
      nivel: 'warning',
      mensaje: '19 ofertas sin procesar NLP',
      accion: 'procesar_nlp',
      detalle: 'Procesadas: 37776/37785',
    },
    {
      nivel: 'info',
      mensaje: '70 issues de usuarios pendientes',
      accion: 'ver_issues',
      detalle: null,
    },
  ],
  resumen: {
    total_ofertas: 37785,
    en_supabase: 37776,
    issues_humanos_pendientes: 70,
    issues_auto_pendientes: 50864,
    fase_sugerida: 'Adquisición',
    fase_sugerida_razon: 'Último scraping hace 7 días',
  },
  ultimo_update: '2026-03-21T18:07:54.406878+00:00',
}

// Variante: todo OK (sin alertas)
export const mockPipelineStatusAllOK = {
  fases: {
    scraping: { estado: 'ok', ultimo_scraping: '2026-03-21', dias_desde_scraping: 0, ofertas_totales: 37785, ofertas_activas: 18316, fuentes: {} },
    nlp: { estado: 'ok', procesadas: 37785, pendientes: 0, ultimo_run: 'run_20260321_1000' },
    matching: { estado: 'ok', con_matching: 37785, pendientes: 0, validadas: 37785, errores_sin_resolver: 0, reglas_negocio: 124 },
    sync: { estado: 'ok', en_supabase: 37785, pendientes: 0 },
  },
  alertas: [
    { nivel: 'ok', mensaje: 'Pipeline operativo — sin alertas', accion: null, detalle: null },
  ],
  resumen: {
    total_ofertas: 37785,
    en_supabase: 37785,
    issues_humanos_pendientes: 0,
    issues_auto_pendientes: 0,
    fase_sugerida: 'Adquisición',
    fase_sugerida_razon: 'Todo al día',
  },
  ultimo_update: '2026-03-21T20:00:00.000000+00:00',
}

// Variante: errores críticos
export const mockPipelineStatusError = {
  fases: {
    scraping: { estado: 'error', ultimo_scraping: '2026-03-01', dias_desde_scraping: 20, ofertas_totales: 37785, ofertas_activas: 18316, fuentes: {} },
    nlp: { estado: 'error', procesadas: 30000, pendientes: 7785, ultimo_run: 'run_20260301_1000' },
    matching: { estado: 'ok', con_matching: 30000, pendientes: 0, validadas: 30000, errores_sin_resolver: 15, reglas_negocio: 124 },
    sync: { estado: 'warning', en_supabase: 29000, pendientes: 1000 },
  },
  alertas: [
    { nivel: 'error', mensaje: 'Scraping sin ejecutar hace 20 días', accion: 'lanzar_scraping', detalle: 'Último scraping: 2026-03-01' },
    { nivel: 'error', mensaje: '7785 ofertas sin procesar NLP', accion: 'procesar_nlp', detalle: 'Procesadas: 30000/37785' },
    { nivel: 'warning', mensaje: '15 errores de validación sin resolver', accion: 'ver_errores', detalle: null },
    { nivel: 'warning', mensaje: '1000 ofertas pendientes de sync a Supabase', accion: 'sync_supabase', detalle: 'En Supabase: 29000' },
  ],
  resumen: {
    total_ofertas: 37785,
    en_supabase: 29000,
    issues_humanos_pendientes: 0,
    issues_auto_pendientes: 0,
    fase_sugerida: 'Adquisición',
    fase_sugerida_razon: 'Scraping atrasado 20 días',
  },
  ultimo_update: '2026-03-01T10:00:00.000000+00:00',
}
