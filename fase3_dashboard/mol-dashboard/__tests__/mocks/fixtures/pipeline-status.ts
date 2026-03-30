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
  // M-01: Campos de último run
  ultimo_run_id: 'run_20260330_1358',
  ultimo_run_timestamp: '2026-03-30T13:58:52',
  ultimo_run_branch: 'feature/m06-skills-failures',
  ultimo_run_nlp_version: '11.3.0',
  ultimo_run_matching_version: '3.5.2',
  ultimo_run_ofertas: 500,
  ultimo_run_skills: 96,
  ultimo_run_failures: 312,
  ultimo_run_failures_pct: 0.243,
  ultimo_run_errores: 12,
  ultimo_run_corregidos: 10,
  ultimo_run_escalados: 2,
  ultimo_run_precision: 0.976,
  ultimo_run_delta_precision: 0.002,
  ultimo_run_delta_regresiones: 0,
  ultimo_run_delta_mejoras: 15,
  ultimo_run_reglas_nuevas: 38,
  ultimo_run_top_failures: JSON.stringify([
    { tarea: 'Controlar políticas de mermas, decomisos y vencimientos', oferta: 'Gerente de sucursal', score: 0.3945, gap: 0.0055, mejor_skill: 'administrar' },
    { tarea: 'Elaborar plan maestro de producción (MPS)', oferta: 'Responsable planificación', score: 0.3809, gap: 0.0191, mejor_skill: 'planificar inventario' },
    { tarea: 'Especialista confiabilidad metalúrgico', oferta: 'Técnico metalúrgico', score: 0.3304, gap: 0.0696, mejor_skill: 'garantizar especificaciones' },
  ]),
}

// M-01: Sin datos de último run (migration no ejecutada o primer uso)
export const mockPipelineStatusNoRun = {
  ...mockPipelineStatusRPC,
  ultimo_run_id: null,
  ultimo_run_timestamp: null,
  ultimo_run_branch: null,
  ultimo_run_ofertas: null,
  ultimo_run_failures: null,
  ultimo_run_failures_pct: null,
  ultimo_run_top_failures: null,
}

// M-01: Run con failures altos (>30% = rojo)
export const mockPipelineStatusHighFailures = {
  ...mockPipelineStatusRPC,
  ultimo_run_failures_pct: 0.35,
  ultimo_run_delta_regresiones: 5,
}

// M-01: Historial de runs
export const mockRunsHistory = [
  { run_id: 'run_20260330_1358', timestamp: '2026-03-30T13:58:52', git_branch: 'feature/m06', ofertas_count: 500, failures_pct: 0.243, precision: 0.976, delta_precision: 0.002, delta_regresiones: 0, errores_escalados: 2 },
  { run_id: 'run_20260329_1000', timestamp: '2026-03-29T10:00:00', git_branch: 'main', ofertas_count: 487, failures_pct: 0.231, precision: 0.974, delta_precision: 0.011, delta_regresiones: 0, errores_escalados: 0 },
  { run_id: 'run_20260322_0830', timestamp: '2026-03-22T08:30:00', git_branch: 'main', ofertas_count: 512, failures_pct: 0.312, precision: 0.963, delta_precision: -0.005, delta_regresiones: 3, errores_escalados: 1 },
]

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
