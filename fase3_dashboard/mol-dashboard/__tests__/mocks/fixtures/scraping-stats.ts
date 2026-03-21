export const mockScrapingStatsRPC = {
  portales: [
    { portal: 'computrabajo', total: 16019, ultimos_7d: 3200, hoy: 0, ultima_fecha: '2026-03-13', dias_sin_datos: 8, porcentaje: 37.8 },
    { portal: 'bumeran', total: 17530, ultimos_7d: 2800, hoy: 0, ultima_fecha: '2026-03-13', dias_sin_datos: 8, porcentaje: 41.3 },
    { portal: 'zonajobs', total: 5657, ultimos_7d: 1100, hoy: 0, ultima_fecha: '2026-03-13', dias_sin_datos: 8, porcentaje: 13.3 },
    { portal: 'indeed', total: 2735, ultimos_7d: 500, hoy: 0, ultima_fecha: '2026-03-13', dias_sin_datos: 8, porcentaje: 6.4 },
    { portal: 'portalempleo', total: 466, ultimos_7d: 80, hoy: 0, ultima_fecha: '2026-03-13', dias_sin_datos: 8, porcentaje: 1.1 },
    { portal: 'caba', total: 12, ultimos_7d: 0, hoy: 0, ultima_fecha: '2026-03-01', dias_sin_datos: 20, porcentaje: 0.0 },
  ],
  totales: {
    total_ofertas: 42419,
    total_activas: 4634,
    portales_activos: 6,
    ultima_fecha_global: '2026-03-13',
    dias_sin_datos_global: 8,
    ofertas_7d: 7680,
    ofertas_30d: 25000,
  },
  alertas: [
    { nivel: 'error', portal: 'caba', mensaje: 'caba sin ofertas hace 20 dias', detalle: 'Ultima oferta: 2026-03-01' },
    { nivel: 'warning', portal: 'computrabajo', mensaje: 'computrabajo sin ofertas hace 8 dias', detalle: 'Ultima oferta: 2026-03-13' },
  ],
  timestamp: '2026-03-21T20:00:00.000Z',
}

export const mockScrapingHistoryRPC = {
  dias: [
    { fecha: '2026-03-08', total: 450, por_portal: { bumeran: 150, zonajobs: 100, computrabajo: 150, indeed: 50 } },
    { fecha: '2026-03-09', total: 520, por_portal: { bumeran: 180, zonajobs: 120, computrabajo: 170, indeed: 50 } },
    { fecha: '2026-03-10', total: 2373, por_portal: { bumeran: 800, zonajobs: 500, computrabajo: 900, indeed: 173 } },
    { fecha: '2026-03-11', total: 1845, por_portal: { bumeran: 600, zonajobs: 400, computrabajo: 700, indeed: 145 } },
    { fecha: '2026-03-12', total: 505, por_portal: { bumeran: 200, zonajobs: 100, computrabajo: 150, indeed: 55 } },
    { fecha: '2026-03-13', total: 104, por_portal: { bumeran: 40, zonajobs: 30, computrabajo: 20, indeed: 14 } },
  ],
  periodo: { desde: '2026-03-07', hasta: '2026-03-21', dias: 14 },
}

export const mockScrapingStatsAllOK = {
  portales: [
    { portal: 'bumeran', total: 17530, ultimos_7d: 3500, hoy: 400, ultima_fecha: '2026-03-21', dias_sin_datos: 0, porcentaje: 41.3 },
    { portal: 'computrabajo', total: 16019, ultimos_7d: 3200, hoy: 350, ultima_fecha: '2026-03-21', dias_sin_datos: 0, porcentaje: 37.8 },
  ],
  totales: {
    total_ofertas: 42419,
    total_activas: 20000,
    portales_activos: 6,
    ultima_fecha_global: '2026-03-21',
    dias_sin_datos_global: 0,
    ofertas_7d: 8000,
    ofertas_30d: 30000,
  },
  alertas: [],
  timestamp: '2026-03-21T20:00:00.000Z',
}
