export const mockRequerimientosRPC = {
  total: 16136,
  educacion: [
    { name: 'universitario', value: 8000, porcentaje: 50 },
    { name: 'terciario', value: 3000, porcentaje: 19 },
    { name: 'secundario', value: 2000, porcentaje: 12 },
    { name: 'Sin especificar', value: 3136, porcentaje: 19 },
  ],
  experiencia: [
    { name: 'Sin experiencia', value: 2000, porcentaje: 12 },
    { name: '1-2 anos', value: 5000, porcentaje: 31 },
    { name: '3-4 anos', value: 4000, porcentaje: 25 },
    { name: '5+ anos', value: 3000, porcentaje: 19 },
    { name: 'Sin especificar', value: 2136, porcentaje: 13 },
  ],
  seniority: [
    { name: 'junior', value: 4000, porcentaje: 25 },
    { name: 'semisenior', value: 5000, porcentaje: 31 },
    { name: 'senior', value: 3500, porcentaje: 22 },
    { name: 'Sin especificar', value: 3636, porcentaje: 22 },
  ],
  modalidad: [
    { name: 'presencial', value: 8000, porcentaje: 50 },
    { name: 'remoto', value: 5000, porcentaje: 31 },
    { name: 'hibrido', value: 3136, porcentaje: 19 },
  ],
  jornada: [
    { name: 'full-time', value: 13000, porcentaje: 81 },
    { name: 'part-time', value: 2000, porcentaje: 12 },
    { name: 'Sin especificar', value: 1136, porcentaje: 7 },
  ],
  gente_cargo: [
    { name: 'Sin gente a cargo', value: 14000, porcentaje: 87 },
    { name: 'Con gente a cargo', value: 2136, porcentaje: 13 },
  ],
}

export const mockSkillsResumenRPC = {
  por_l1: [
    { code: 'S', name: 'Skills', value: 25000, porcentaje: 60 },
    { code: 'K', name: 'Knowledge', value: 12000, porcentaje: 29 },
    { code: 'T', name: 'Transversal', value: 5000, porcentaje: 11 },
  ],
  digitales: {
    digitales: 20000,
    no_digitales: 22000,
    total: 42000,
  },
  top_skills: [
    { name: 'React', value: 450, categoria: 'S', categoriaNombre: 'Skills', es_digital: true },
    { name: 'Node.js', value: 380, categoria: 'S', categoriaNombre: 'Skills', es_digital: true },
    { name: 'TypeScript', value: 350, categoria: 'S', categoriaNombre: 'Skills', es_digital: true },
    { name: 'Python', value: 320, categoria: 'S', categoriaNombre: 'Skills', es_digital: true },
    { name: 'SQL', value: 290, categoria: 'S', categoriaNombre: 'Skills', es_digital: true },
  ],
}

export const mockSidebarCountsRPC = {
  total_ofertas: 16136,
  sectores: [
    { sector: 'Información y comunicaciones', count: 4500 },
    { sector: 'Actividades profesionales, científicas y técnicas', count: 3200 },
    { sector: 'Comercio al por mayor y al por menor', count: 2800 },
  ],
  ocupaciones_tree: [
    {
      major_group: '2',
      count: 5400,
      children: [
        { id: '2514', label: 'Programadores de aplicaciones', count: 1200 },
        { id: '2411', label: 'Contadores', count: 800 },
      ],
    },
    {
      major_group: '3',
      count: 3200,
      children: [
        { id: '3322', label: 'Agentes comerciales', count: 500 },
      ],
    },
  ],
}
