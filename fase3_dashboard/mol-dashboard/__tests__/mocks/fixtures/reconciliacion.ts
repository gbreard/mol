// Reconciliacion: todo consistente
export const mockReconciliacionOK = {
  conteos: {
    local_total: 37776,
    local_con_nlp: 37776,
    local_validadas: 37776,
    supabase_ofertas: 37776,
    supabase_skills: 318720,
    supabase_ofertas_con_skills: 37776,
    supabase_sin_isco: 0,
    supabase_sin_skills: 0,
  },
  inconsistencias: [
    { tipo: 'ok', severidad: 'ok', mensaje: 'Sistemas consistentes — sin diferencias', esperado: 37776, actual: 37776, diferencia: 0, accion: null },
  ],
  estado: 'ok',
  timestamp: '2026-03-21T20:00:00.000Z',
}

// Reconciliacion: con diferencias
export const mockReconciliacionWarning = {
  conteos: {
    local_total: 42419,
    local_con_nlp: 37776,
    local_validadas: 37776,
    supabase_ofertas: 37776,
    supabase_skills: 318720,
    supabase_ofertas_con_skills: 35000,
    supabase_sin_isco: 50,
    supabase_sin_skills: 2776,
  },
  inconsistencias: [
    { tipo: 'ofertas_faltantes', severidad: 'error', mensaje: 'Ofertas en local sin subir a Supabase', esperado: 42419, actual: 37776, diferencia: 4643, accion: 'sync_supabase' },
    { tipo: 'sin_skills', severidad: 'warning', mensaje: 'Ofertas en Supabase sin skills asociadas', esperado: 37776, actual: 35000, diferencia: 2776, accion: 'backfill_skills' },
    { tipo: 'sin_isco', severidad: 'warning', mensaje: 'Ofertas sin clasificacion ISCO', esperado: 37776, actual: 37726, diferencia: 50, accion: 'reprocesar_matching' },
  ],
  estado: 'error',
  timestamp: '2026-03-21T20:00:00.000Z',
}
