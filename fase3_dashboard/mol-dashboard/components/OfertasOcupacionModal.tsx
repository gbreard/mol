'use client';

import { useState, useEffect } from 'react';
import { X, Briefcase, ExternalLink, Download, FileSpreadsheet, FileText, Loader2 } from 'lucide-react';
import { getOfertasByIsco, OfertaPorOcupacion } from '@/lib/supabase';
import { downloadFormattedExcel } from './ExportButton';

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
  const [exporting, setExporting] = useState(false);

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

  const handleExportCSV = () => {
    if (ofertas.length === 0) return;

    const headers = ['Titulo', 'Fecha', 'Link'];
    const rows = ofertas.map(o => [
      o.titulo_limpio || o.titulo || '',
      o.fecha_publicacion || '',
      o.url || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => {
        const str = String(cell);
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      }).join(','))
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ofertas_${iscoCode}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportExcel = async () => {
    if (ofertas.length === 0) return;

    setExporting(true);
    try {
      const XLSX = await import('xlsx');

      // Preparar datos
      const dataRows = ofertas.map(o => ({
        'Título': o.titulo_limpio || o.titulo || '',
        'Fecha': o.fecha_publicacion || '',
        'Competencias': o.skills_tecnicas || '',
        'Link': o.url || ''
      }));

      // Crear worksheet vacío
      const ws = XLSX.utils.aoa_to_sheet([]);

      // Fila 1: Título
      const title = 'Ofertas laborales disponibles activas a la fecha según selección';
      XLSX.utils.sheet_add_aoa(ws, [[title]], { origin: 'A1' });

      // Fila 2: Subtítulo (fecha + ocupación)
      const subtitle = `Fecha de extracción: ${new Date().toLocaleDateString('es-AR')} | Ocupación: ${iscoLabel} (ISCO: ${iscoCode})`;
      XLSX.utils.sheet_add_aoa(ws, [[subtitle]], { origin: 'A2' });

      // Fila 3: vacía
      XLSX.utils.sheet_add_aoa(ws, [['']], { origin: 'A3' });

      // Fila 4: Headers
      const headers = ['Título', 'Fecha', 'Competencias', 'Link'];
      XLSX.utils.sheet_add_aoa(ws, [headers], { origin: 'A4' });

      // Filas de datos
      dataRows.forEach((row, idx) => {
        const rowData = headers.map(h => row[h as keyof typeof row] ?? '');
        XLSX.utils.sheet_add_aoa(ws, [rowData], { origin: `A${5 + idx}` });
      });

      // Fuente
      const lastDataRow = 5 + dataRows.length;
      XLSX.utils.sheet_add_aoa(ws, [['']], { origin: `A${lastDataRow}` });
      XLSX.utils.sheet_add_aoa(ws, [['Fuente: MOL, en base a portales de intermediación laboral']], { origin: `A${lastDataRow + 1}` });

      // Ajustar ancho de columnas
      ws['!cols'] = [
        { wch: 50 }, // Título
        { wch: 12 }, // Fecha
        { wch: 40 }, // Competencias
        { wch: 60 }  // Link
      ];

      // Fusionar celdas para título y subtítulo
      ws['!merges'] = [
        { s: { r: 0, c: 0 }, e: { r: 0, c: 3 } },
        { s: { r: 1, c: 0 }, e: { r: 1, c: 3 } },
        { s: { r: lastDataRow, c: 0 }, e: { r: lastDataRow, c: 3 } }
      ];

      // Crear workbook y descargar
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Ofertas');
      XLSX.writeFile(wb, `ofertas_${iscoCode}_${new Date().toISOString().split('T')[0]}.xlsx`);
    } catch (error) {
      console.error('Error exporting Excel:', error);
      alert('Error al exportar. Intente nuevamente.');
    } finally {
      setExporting(false);
    }
  };

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
            {/* Export buttons */}
            {ofertas.length > 0 && (
              <>
                <button
                  onClick={handleExportCSV}
                  className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <FileText className="w-4 h-4 text-green-600" />
                  CSV
                </button>
                <button
                  onClick={handleExportExcel}
                  disabled={exporting}
                  className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  {exporting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <FileSpreadsheet className="w-4 h-4 text-blue-600" />
                  )}
                  Excel
                </button>
              </>
            )}

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
