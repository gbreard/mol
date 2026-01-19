'use client';

import Filters from '@/components/Filters';

export default function Requerimientos() {
  // Datos de ejemplo para skills
  const topSkills = [
    { skill: 'JavaScript', cantidad: 450, tipo: 'Técnica' },
    { skill: 'Python', cantidad: 380, tipo: 'Técnica' },
    { skill: 'Excel', cantidad: 350, tipo: 'Técnica' },
    { skill: 'Comunicación', cantidad: 320, tipo: 'Blanda' },
    { skill: 'SQL', cantidad: 280, tipo: 'Técnica' },
    { skill: 'Trabajo en equipo', cantidad: 260, tipo: 'Blanda' },
    { skill: 'React', cantidad: 220, tipo: 'Técnica' },
    { skill: 'Inglés', cantidad: 200, tipo: 'Idioma' },
    { skill: 'Liderazgo', cantidad: 180, tipo: 'Blanda' },
    { skill: 'Node.js', cantidad: 150, tipo: 'Técnica' },
  ];

  return (
    <div className="space-y-6">
      <Filters />

      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Requerimientos del mercado</h2>
        <p className="text-gray-600 mt-1">Habilidades y competencias más demandadas</p>
      </div>

      {/* KPIs de skills */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-500">Skills técnicas</h3>
          <p className="text-3xl font-semibold text-gray-900 mt-2">847</p>
          <p className="text-sm text-green-600 mt-1">+18% vs trimestre anterior</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-500">Skills blandas</h3>
          <p className="text-3xl font-semibold text-gray-900 mt-2">312</p>
          <p className="text-sm text-green-600 mt-1">+8% vs trimestre anterior</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-500">Skills digitales</h3>
          <p className="text-3xl font-semibold text-gray-900 mt-2">523</p>
          <p className="text-sm text-green-600 mt-1">+25% vs trimestre anterior</p>
        </div>
      </div>

      {/* Tabla de skills */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">Top 10 habilidades demandadas</h3>
            <button className="text-sm text-blue-600 hover:text-blue-800">
              Descargar CSV
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ranking
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Habilidad
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Menciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {topSkills.map((skill, index) => (
                <tr key={skill.skill} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {index + 1}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {skill.skill}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      skill.tipo === 'Técnica' ? 'bg-blue-100 text-blue-800' :
                      skill.tipo === 'Blanda' ? 'bg-green-100 text-green-800' :
                      'bg-purple-100 text-purple-800'
                    }`}>
                      {skill.tipo}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {skill.cantidad.toLocaleString('es-AR')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
