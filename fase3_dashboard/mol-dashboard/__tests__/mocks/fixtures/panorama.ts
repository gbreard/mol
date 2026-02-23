export const mockPanoramaRPC = {
  kpis: {
    total_ofertas: 16136,
    ocupaciones_distintas: 245,
    empresas_activas: 3200,
    provincias: 24,
  },
  top_ocupaciones: [
    { isco_code: '2514', ocupacion: 'Programadores de aplicaciones', cantidad: 1200 },
    { isco_code: '2411', ocupacion: 'Contadores', cantidad: 800 },
    { isco_code: '1221', ocupacion: 'Directores de ventas y comercialización', cantidad: 650 },
    { isco_code: '3322', ocupacion: 'Agentes comerciales', cantidad: 500 },
    { isco_code: '2431', ocupacion: 'Profesionales de publicidad y comercialización', cantidad: 450 },
  ],
  provincias: [
    { jurisdiccion: 'Capital Federal', cantidad: 8500, porcentaje: 52.7 },
    { jurisdiccion: 'Buenos Aires', cantidad: 3800, porcentaje: 23.5 },
    { jurisdiccion: 'Córdoba', cantidad: 1200, porcentaje: 7.4 },
  ],
  modalidad: [
    { modalidad: 'presencial', cantidad: 8000 },
    { modalidad: 'remoto', cantidad: 5000 },
    { modalidad: 'hibrido', cantidad: 3136 },
  ],
}
