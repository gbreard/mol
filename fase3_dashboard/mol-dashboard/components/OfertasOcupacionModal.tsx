'use client';

import { useState, useEffect, useCallback } from 'react';
import { X, Briefcase, ExternalLink, Loader2, Calendar, RefreshCw } from 'lucide-react';
import { getOfertasByIsco } from '@/lib/supabase';
import { ChartDownloadButton } from './ExportButton';

type TimePeriod = '7d' | '30d' | '90d' | 'all';

const TIME_OPTIONS: { id: TimePeriod; label: string }[] = [
  { id: '7d', label: 'Última semana' },
  { id: '30d', label: 'Último mes' },
  { id: '90d', label: 'Últimos 3 meses' },
  { id: 'all', label: 'Histórico' },
];

function getSinceDate(period: TimePeriod): string | null {
  if (period === 'all') return null;
  const d = new Date();
  d.setDate(d.getDate() - (period === '7d' ? 7 : period === '30d' ? 30 : 90));
  return d.toISOString().split('T')[0];
}

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
  const [ofertas, setOfertas] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('30d');

  const fetchOfertas = useCallback(async (period: TimePeriod) => {
    setLoading(true);
    setError(false);
    try {
      const since = getSinceDate(period);
      const { ofertas: data, total: count } = await getOfertasByIsco(iscoCode, 100, 0, null, since);
      setOfertas(data);
      setTotal(count);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [iscoCode]);

  useEffect(() => {
    if (isOpen && iscoCode) {
      fetchOfertas(timePeriod);
    }
  }, [isOpen, iscoCode, timePeriod, fetchOfertas]);

  function handlePeriodChange(period: TimePeriod) {
    setTimePeriod(period);
  }

  // Download options
  const downloadOptions = ofertas.length > 0 ? {
    title: 'Ofertas laborales disponibles según selección',
    subtitle: `Fecha de extracción: ${new Date().toLocaleDateString('es-AR')} | Ocupación: ${iscoLabel} (ISCO: ${iscoCode}) | Período: ${TIME_OPTIONS.find(t => t.id === timePeriod)?.label}`,
    data: ofertas.map((o: any) => ({
      titulo: o.titulo_limpio || o.titulo || '',
      empresa: o.empresa || '',
      fecha: o.fecha_publicacion || '',
      estado: o.estado || '',
      competencias: o.skills_tecnicas || '',
      link: o.url || ''
    })),
    columns: [
      { header: 'Título', key: 'titulo' },
      { header: 'Empresa', key: 'empresa' },
      { header: 'Fecha', key: 'fecha' },
      { header: 'Estado', key: 'estado' },
      { header: 'Competencias', key: 'competencias' },
      { header: 'Link', key: 'link' }
    ],
    filename: `ofertas_${iscoCode}_${timePeriod}`,
  } : undefined;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] m-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Ofertas laborales</h2>
            <p className="text-sm text-gray-500">{iscoLabel} · ISCO {iscoCode}</p>
          </div>
          <div className="flex items-center gap-2">
            {downloadOptions && <ChartDownloadButton {...downloadOptions} />}
            <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg">
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Time filter */}
        <div className="flex items-center gap-2 px-5 py-2.5 border-b bg-gray-50">
          <Calendar className="w-3.5 h-3.5 text-gray-400" />
          {TIME_OPTIONS.map(t => (
            <button
              key={t.id}
              onClick={() => handlePeriodChange(t.id)}
              className={`text-xs px-2.5 py-1 rounded-full transition-colors ${timePeriod === t.id ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex items-center justify-center py-12 gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
              <span className="text-sm text-gray-500">Cargando ofertas...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-sm text-gray-500 mb-3">No se pudieron cargar las ofertas.</p>
              <button
                onClick={() => fetchOfertas(timePeriod)}
                className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                <RefreshCw className="w-4 h-4" /> Reintentar
              </button>
            </div>
          ) : ofertas.length === 0 ? (
            <div className="text-center py-12">
              <Briefcase className="w-10 h-10 mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-500">
                No hay ofertas para esta ocupación en {TIME_OPTIONS.find(t => t.id === timePeriod)?.label.toLowerCase()}
              </p>
              {timePeriod !== 'all' && (
                <button
                  onClick={() => handlePeriodChange('all')}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium mt-2"
                >
                  Ver histórico completo
                </button>
              )}
            </div>
          ) : (
            <>
              <p className="text-xs text-gray-400 mb-3">
                {total} oferta{total !== 1 ? 's' : ''}
              </p>
              <div className="space-y-2">
                {ofertas.map((oferta: any, index: number) => (
                  <div key={oferta.id_oferta || index} className="bg-gray-50 hover:bg-gray-100 rounded-lg p-3 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-gray-900 truncate">{oferta.titulo_limpio || oferta.titulo}</p>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium shrink-0 ${oferta.estado === 'activa' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                            {oferta.estado === 'activa' ? 'Activa' : 'Cerrada'}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
                          {oferta.empresa && <span>{oferta.empresa}</span>}
                          {oferta.fecha_publicacion && <span>{new Date(oferta.fecha_publicacion).toLocaleDateString('es-AR')}</span>}
                        </div>
                        {oferta.skills_tecnicas && (
                          <div className="mt-1.5 flex flex-wrap gap-1">
                            {oferta.skills_tecnicas.split(/[;,]/).slice(0, 4).map((skill: string, i: number) => (
                              <span key={i} className="bg-blue-50 text-blue-600 text-[10px] px-1.5 py-0.5 rounded">
                                {skill.trim()}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      {oferta.url && (
                        <a href={oferta.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-700 shrink-0">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {total > ofertas.length && (
                <p className="text-xs text-gray-400 mt-3 text-center">
                  Mostrando {ofertas.length} de {total}
                </p>
              )}
            </>
          )}
        </div>

        <div className="border-t px-5 py-3 text-xs text-gray-400">
          Fuente: MOL, en base a portales de intermediación laboral
        </div>
      </div>
    </div>
  );
}
