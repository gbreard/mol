'use client';

import { useState } from 'react';

export default function Ofertas() {
  const [searchTerm, setSearchTerm] = useState('');

  // Datos de ejemplo
  const ofertas = [
    {
      id: '1',
      titulo: 'Desarrollador Full Stack',
      empresa: 'TechCorp Argentina',
      ubicacion: 'CABA',
      ocupacion: 'Desarrollador de software',
      modalidad: 'Remoto',
      seniority: 'Senior',
      fecha: '2026-01-15',
    },
    {
      id: '2',
      titulo: 'Contador Senior',
      empresa: 'Estudio Contable García',
      ubicacion: 'Buenos Aires',
      ocupacion: 'Contador',
      modalidad: 'Híbrido',
      seniority: 'Senior',
      fecha: '2026-01-14',
    },
    {
      id: '3',
      titulo: 'Vendedor Comercial',
      empresa: 'Distribuidora Norte',
      ubicacion: 'Córdoba',
      ocupacion: 'Representante comercial',
      modalidad: 'Presencial',
      seniority: 'Semi-senior',
      fecha: '2026-01-14',
    },
    {
      id: '4',
      titulo: 'Analista de Sistemas',
      empresa: 'Banco Nacional',
      ubicacion: 'CABA',
      ocupacion: 'Analista de sistemas',
      modalidad: 'Híbrido',
      seniority: 'Semi-senior',
      fecha: '2026-01-13',
    },
    {
      id: '5',
      titulo: 'Recepcionista',
      empresa: 'Hotel Palermo',
      ubicacion: 'CABA',
      ocupacion: 'Recepcionista',
      modalidad: 'Presencial',
      seniority: 'Junior',
      fecha: '2026-01-13',
    },
  ];

  const filteredOfertas = ofertas.filter(o =>
    o.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
    o.empresa.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header con búsqueda */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Ofertas laborales</h2>
          <p className="text-gray-600 mt-1">Detalle de ofertas procesadas y validadas</p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Buscar por título o empresa..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 w-64"
          />
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Descargar CSV
          </button>
        </div>
      </div>

      {/* Tabla de ofertas */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Título
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Empresa
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ubicación
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ocupación ESCO
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Modalidad
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Seniority
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredOfertas.map((oferta) => (
                <tr key={oferta.id} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-blue-600 hover:text-blue-800">
                      {oferta.titulo}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {oferta.empresa}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {oferta.ubicacion}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {oferta.ocupacion}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      oferta.modalidad === 'Remoto' ? 'bg-green-100 text-green-800' :
                      oferta.modalidad === 'Híbrido' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {oferta.modalidad}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {oferta.seniority}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {oferta.fecha}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Mostrando {filteredOfertas.length} de 5,890 ofertas
          </p>
          <div className="flex gap-2">
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50">
              Anterior
            </button>
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm">
              1
            </button>
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50">
              2
            </button>
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50">
              3
            </button>
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50">
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
