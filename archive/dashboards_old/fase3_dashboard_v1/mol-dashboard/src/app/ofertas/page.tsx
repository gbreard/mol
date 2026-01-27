'use client';

import { useEffect, useState } from 'react';
import { getOfertas, OfertaDashboard } from '@/lib/supabase';

export default function Ofertas() {
  const [searchTerm, setSearchTerm] = useState('');
  const [ofertas, setOfertas] = useState<OfertaDashboard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const { ofertas: data, total: count } = await getOfertas(pageSize, page * pageSize);
        setOfertas(data);
        setTotal(count);
      } catch (err) {
        console.error('Error fetching ofertas:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [page]);

  const filteredOfertas = ofertas.filter(o =>
    o.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (o.empresa?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(total / pageSize);

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
        </div>
      </div>

      {/* Tabla de ofertas */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Cargando ofertas...</div>
        ) : (
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
                  <tr key={oferta.id_oferta} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      {oferta.url ? (
                        <a
                          href={oferta.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                          {oferta.titulo}
                        </a>
                      ) : (
                        <div className="text-sm font-medium text-gray-900">
                          {oferta.titulo}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {oferta.empresa || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {[oferta.localidad, oferta.provincia].filter(Boolean).join(', ') || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span title={`ISCO: ${oferta.isco_code}`}>
                        {oferta.isco_label || '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {oferta.modalidad ? (
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          oferta.modalidad === 'remoto' ? 'bg-green-100 text-green-800' :
                          oferta.modalidad === 'hibrido' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {oferta.modalidad}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {oferta.nivel_seniority || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {oferta.fecha_publicacion || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Paginación */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Mostrando {page * pageSize + 1}-{Math.min((page + 1) * pageSize, total)} de {total} ofertas
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              Anterior
            </button>
            <span className="px-3 py-1 text-sm">
              Página {page + 1} de {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
