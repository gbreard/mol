export interface MockPipelineRun {
  run_id: string
  timestamp: string
  source: string | null
  description: string | null
  git_branch: string | null
  git_commit: string | null
  nlp_version: string | null
  matching_version: string | null
  ofertas_count: number | null
  failures_count: number | null
  failures_pct: number | null
  precision: number | null
  errores_detectados: number | null
  errores_corregidos: number | null
  errores_escalados: number | null
  reglas_nuevas: number | null
  sinonimos_count: number | null
  delta_mejoras: number | null
  delta_regresiones: number | null
  run_anterior_id: string | null
}

export const mockPipelineRuns: MockPipelineRun[] = [
  {
    run_id: 'run_20260516_2052',
    timestamp: '2026-05-16T20:52:48.614930',
    source: 'manual',
    description: 'Lote 471 ofertas',
    git_branch: 'feature/spec-e-embeddings-enriquecidos',
    git_commit: 'bc1b13f6',
    nlp_version: '11.3.1',
    matching_version: '3.5.5',
    ofertas_count: 471,
    failures_count: 0,
    failures_pct: 0,
    precision: 1.0,
    errores_detectados: 232,
    errores_corregidos: 0,
    errores_escalados: 213,
    reglas_nuevas: 0,
    sinonimos_count: 23,
    delta_mejoras: null,
    delta_regresiones: null,
    run_anterior_id: null,
  },
  {
    run_id: 'run_20260515_0001',
    timestamp: '2026-05-15T00:01:12.000000',
    source: 'manual',
    description: null,
    git_branch: 'feature/spec-e-embeddings-enriquecidos',
    git_commit: 'bc1b13f6',
    nlp_version: '11.3.1',
    matching_version: '3.5.5',
    ofertas_count: 1010,
    failures_count: 0,
    failures_pct: 0,
    precision: 1.0,
    errores_detectados: 142,
    errores_corregidos: 12,
    errores_escalados: 130,
    reglas_nuevas: 0,
    sinonimos_count: 23,
    delta_mejoras: null,
    delta_regresiones: null,
    run_anterior_id: 'run_20260514_1759',
  },
  {
    run_id: 'reapply_20260422_185810',
    timestamp: '2026-04-22T18:58:10.000000',
    source: 'reapply_rules',
    description: 'Reapply tras crear regla R321',
    git_branch: 'main',
    git_commit: '0873fd61',
    nlp_version: '11.3.0',
    matching_version: '3.5.4',
    ofertas_count: 1,
    failures_count: 0,
    failures_pct: 0,
    precision: 1.0,
    errores_detectados: 0,
    errores_corregidos: 0,
    errores_escalados: 0,
    reglas_nuevas: 0,
    sinonimos_count: 22,
    delta_mejoras: null,
    delta_regresiones: null,
    run_anterior_id: null,
  },
]
