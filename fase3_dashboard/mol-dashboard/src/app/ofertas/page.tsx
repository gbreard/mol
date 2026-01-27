'use client';

import { useState, useEffect } from 'react';
import Filters from '@/components/Filters';
import { getOfertas, OfertaTabla } from '@/lib/supabase';

export default function Ofertas() {
  const [searchTerm, setSearchTerm] = useState('');
  const [ofertas, setOfertas] = useState<OfertaTabla[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalOfertas, setTotalOfertas] = useState(0);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getOfertas();
        setOfertas(data);
        setTotalOfertas(data.length);
      } catch (error) {
        console.error('Error loading ofertas:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const filteredOfertas = ofertas.filter(o =>
    o.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
    o.empresa.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatModalidad = (modalidad: string) => {
    if (!modalidad) return 'Sin especificar';
    const m = modalidad.toLowerCase();
    if (m === 'remoto' || m === 'remote') return 'Remoto';
    if (m === 'hibrido' || m === 'híbrido' || m === 'hybrid') return 'Híbrido';
    if (m === 'presencial' || m === 'onsite') return 'Presencial';
    return modalidad;
  };

  const getModalidadStyle = (modalidad: string) => {
    const m = formatModalidad(modalidad);
    if (m === 'Remoto') return 'bg-green-100 text-green-800';
    if (m === 'Híbrido') return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-10 w-48 bg-gray-200 rounded mb-4"></div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-12 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Filters />

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
              {filteredOfertas.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    {searchTerm ? 'No se encontraron ofertas con ese criterio' : 'No hay ofertas disponibles'}
                  </td>
                </tr>
              ) : (
                filteredOfertas.map((oferta) => (
                  <tr key={oferta.id} className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-blue-600 hover:text-blue-800">
                        {oferta.titulo || 'Sin título'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {oferta.empresa || 'Sin empresa'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {oferta.ubicacion || 'Sin ubicación'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {oferta.ocupacion || 'Sin clasificar'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getModalidadStyle(oferta.modalidad)}`}>
                        {formatModalidad(oferta.modalidad)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {oferta.seniority || 'Sin especificar'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {oferta.fecha || 'Sin fecha'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Mostrando {filteredOfertas.length} de {totalOfertas} ofertas
          </p>
          <div className="flex gap-2">
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50" disabled>
              Anterior
            </button>
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm">
              1
            </button>
            <button className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50" disabled>
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
