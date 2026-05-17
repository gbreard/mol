// Mock para RPC get_runs_disponibles — usado por filtro Run/Corrida en /admin/validacion.
// Ordenado por run_id DESC (lexicográfico, formato run_YYYYMMDD_HHMMSS ordena cronológicamente).
// Nota orden lexicográfico DESC: 's' > 'r' (spec_* antes que run_*); 'run_' > 'reapply_'
// porque 'u' (117) > 'e' (101) en el segundo char.
export const mockRunsDisponibles = [
  { run_id: 'spec_h_rematch_20260426T203656Z', n: 3 },
  { run_id: 'run_20260516_2052', n: 471 },
  { run_id: 'run_20260516_1745', n: 994 },
  { run_id: 'run_20260516_1141', n: 1000 },
  { run_id: 'run_20260330_1755', n: 4803 },
  { run_id: 'reapply_20260219_203452', n: 12 },
];
