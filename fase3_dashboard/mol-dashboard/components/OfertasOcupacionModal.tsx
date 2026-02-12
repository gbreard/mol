'use client';

import { useState, useEffect } from 'react';
import { X, Briefcase, ExternalLink, Loader2 } from 'lucide-react';
import { getOfertasByIsco, OfertaPorOcupacion } from '@/lib/supabase';
import { ChartDownloadButton } from './ExportButton';

interface OfertasOcupacionModalProps {
  isOpen: boolean;
  onClose: () => void;
  iscoCode: string;
  iscoLabel: string;
}

export default function OfertasOcupacionModal({
  isOpen,
  onClose,
  iscoCode,
  iscoLabel
}: OfertasOcupacionModalProps) {
  const [ofertas, setOfertas] = useState<OfertaPorOcupacion[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && iscoCode) {
      fetchOfertas();
    }
  }, [isOpen, iscoCode]);

  async function fetchOfertas() {
    setLoading(true);
    try {
      const { ofertas: data, total: count } = await getOfertasByIsco(iscoCode, 100);
      setOfertas(data);
      setTotal(count);
    } catch (error) {
      console.error('Error fetching ofertas:', error);
    } finally {
      setLoading(false);
    }
  }

  // Download options unificado
  const downloadOptions = ofertas.length > 0 ? {
    title: 'Ofertas laborales disponibles activas a la fecha según selección',
    subtitle: `Fecha de extracción: ${new Date().toLocaleDateString('es-AR')} | Ocupación: ${iscoLabel} (ISCO: ${iscoCode})`,
    data: ofertas.map(o => ({
      titulo: o.titulo_limpio || o.titulo || '',
      fecha: o.fecha_publicacion || '',
      competencias: o.skills_tecnicas || '',
      link: o.url || ''
    })),
    columns: [
      { header: 'Título', key: 'titulo' },
      { header: 'Fecha', key: 'fecha' },
      { header: 'Competencias', key: 'competencias' },
      { header: 'Link', key: 'link' }
    ],
    filename: `ofertas_${iscoCode}`,
  } : undefined;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] m-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="bg-green-100 p-2 rounded-full">
              <Briefcase className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Ofertas Laborales Activas
              </h2>
              <p className="text-sm text-gray-500">
                {iscoLabel} (ISCO: {iscoCode})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {downloadOptions && <ChartDownloadButton {...downloadOptions} />}

            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors ml-2"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <span className="ml-3 text-gray-600">Cargando ofertas...</span>
            </div>
          ) : ofertas.length === 0 ? (
            <div className="text-center py-12">
              <Briefcase className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500">No hay ofertas activas para esta ocupación</p>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-600 mb-4">
                {total} {total === 1 ? 'oferta encontrada' : 'ofertas encontradas'}
              </p>

              <div className="space-y-3">
                {ofertas.map((oferta, index) => (
                  <div
                    key={oferta.id_oferta}
                    className="bg-gray-50 hover:bg-gray-100 rounded-lg p-4 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 truncate">
                          {oferta.titulo_limpio || oferta.titulo}
                        </h3>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                          {oferta.empresa && (
                            <span>{oferta.empresa}</span>
                          )}
                          {oferta.fecha_publicacion && (
                            <span>{new Date(oferta.fecha_publicacion).toLocaleDateString('es-AR')}</span>
                          )}
                        </div>
                        {oferta.skills_tecnicas && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {oferta.skills_tecnicas.split(/[;,]/).slice(0, 5).map((skill, i) => (
                              <span
                                key={i}
                                className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded"
                              >
                                {skill.trim()}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {oferta.url && (
                        <a
                          href={oferta.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 whitespace-nowrap"
                        >
                          Ver oferta
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {total > ofertas.length && (
                <p className="text-sm text-gray-500 mt-4 text-center">
                  Mostrando {ofertas.length} de {total} ofertas
                </p>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t p-4 bg-gray-50 text-sm text-gray-500 rounded-b-xl">
          Fuente: MOL, en base a portales de intermediación laboral
        </div>
      </div>
    </div>
  );
}
