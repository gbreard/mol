export const mockTopOcupaciones = [
  { ocupacion: 'Programadores de aplicaciones', cantidad: 450 },
  { ocupacion: 'Contadores', cantidad: 380 },
  { ocupacion: 'Directores de ventas y comercialización', cantidad: 320 },
  { ocupacion: 'Analistas de sistemas', cantidad: 290 },
  { ocupacion: 'Especialistas en recursos humanos', cantidad: 250 },
]

export const mockOcupacionesTree = [
  {
    id: 'isco-2',
    label: 'Profesionales científicos e intelectuales',
    count: 5400,
    children: [
      { id: '2514', label: 'Programadores de aplicaciones', count: 450 },
      { id: '2411', label: 'Contadores', count: 380 },
      { id: '2511', label: 'Analistas de sistemas', count: 290 },
    ],
  },
  {
    id: 'isco-1',
    label: 'Directores y gerentes',
    count: 2200,
    children: [
      { id: '1221', label: 'Directores de ventas y comercialización', count: 320 },
      { id: '1211', label: 'Directores financieros', count: 200 },
    ],
  },
]
