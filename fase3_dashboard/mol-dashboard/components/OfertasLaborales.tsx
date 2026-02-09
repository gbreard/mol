"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, ExternalLink, Loader2, AlertCircle, ChevronLeft, ChevronRight, Download } from "lucide-react";
import { ExportButton, ExportColumn, downloadFormattedExcel } from "@/components/ExportButton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect } from "react";
import { getOfertas, OfertaDashboard } from "@/lib/supabase";
import { DashboardFilters } from "@/lib/types";
import { IssueRowButton } from "@/components/issues";

const PAGE_SIZE = 50;

interface OfertasLaboralesProps {
  filters: DashboardFilters;
}

export function OfertasLaborales({ filters }: OfertasLaboralesProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ofertas, setOfertas] = useState<OfertaDashboard[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);

  // Calcular totales de paginación
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const offset = (currentPage - 1) * PAGE_SIZE;

  // Reset a página 1 cuando cambian los filtros
  useEffect(() => {
    setCurrentPage(1);
  }, [filters]);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const { ofertas: data, total: count } = await getOfertas(PAGE_SIZE, offset, filters);
        setOfertas(data);
        setTotal(count);
        setError(null);
      } catch (err) {
        console.error('Error cargando ofertas:', err);
        setError('Error al cargar las ofertas.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [filters, currentPage, offset]);

  const filteredOfertas = ofertas.filter(oferta => {
    if (!searchTerm.trim()) return true;
    const searchLower = searchTerm.toLowerCase();
    return (oferta.titulo?.toLowerCase().includes(searchLower) ||
            oferta.titulo_limpio?.toLowerCase().includes(searchLower) ||
            false);
  });

  // Función para formatear los filtros aplicados como subtítulo
  const getFiltersSubtitle = (): string => {
    const parts: string[] = [`Fecha de extracción: ${new Date().toLocaleDateString('es-AR')}`];
    if (filters.territorio && filters.territorio !== 'Nacional') parts.push(`Territorio: ${filters.territorio}`);
    if (filters.provincia && filters.provincia !== 'Todas') parts.push(`Provincia: ${filters.provincia}`);
    if (filters.localidad) parts.push(`Localidad: ${filters.localidad}`);
    if (filters.fechaDesde) parts.push(`Desde: ${filters.fechaDesde.toLocaleDateString('es-AR')}`);
    if (filters.fechaHasta) parts.push(`Hasta: ${filters.fechaHasta.toLocaleDateString('es-AR')}`);
    if (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0) {
      parts.push(`Ocupaciones: ${filters.ocupacionesSeleccionadas.slice(0, 3).join(', ')}${filters.ocupacionesSeleccionadas.length > 3 ? '...' : ''}`);
    }
    return parts.join(' | ');
  };

  // Handler descarga Excel formateado
  const handleDownloadFormatted = () => {
    if (filteredOfertas.length === 0) return;
    const data = filteredOfertas.map(o => ({
      titulo: o.titulo_limpio || o.titulo || '',
      fecha: o.fecha_publicacion ? new Date(o.fecha_publicacion).toLocaleDateString('es-AR') : '',
      competencias: [
        ...(o.skills_tecnicas || []),
        ...(o.soft_skills || [])
      ].join('; '),
      link: o.url || ''
    }));
    downloadFormattedExcel({
      title: 'Ofertas laborales disponibles activas a la fecha según selección',
      subtitle: getFiltersSubtitle(),
      data,
      columns: [
        { header: 'Título', key: 'titulo' },
        { header: 'Fecha', key: 'fecha' },
        { header: 'Competencias', key: 'competencias' },
        { header: 'Link', key: 'link' }
      ],
      filename: 'ofertas_laborales',
      showPercentage: false
    });
  };

  // Columnas para exportación
  const exportColumns: ExportColumn[] = [
    { key: 'fecha_publicacion', header: 'Fecha', format: (v) => v ? new Date(v).toLocaleDateString('es-AR') : '' },
    { key: 'titulo_limpio', header: 'Título', format: (v) => v || '' },
    { key: 'empresa', header: 'Empresa', format: (v) => v || '' },
    { key: 'provincia', header: 'Provincia', format: (v) => v || '' },
    { key: 'localidad', header: 'Localidad', format: (v) => v || '' },
    { key: 'modalidad', header: 'Modalidad', format: (v) => v || '' },
    { key: 'nivel_seniority', header: 'Seniority', format: (v) => v || '' },
    { key: 'isco_code', header: 'ISCO', format: (v) => v || '' },
    { key: 'isco_label', header: 'Ocupación ESCO', format: (v) => v || '' },
    { key: 'skills_tecnicas', header: 'Conocimientos', format: (v) => Array.isArray(v) ? v.join('; ') : '' },
    { key: 'soft_skills', header: 'Competencias', format: (v) => Array.isArray(v) ? v.join('; ') : '' },
    { key: 'url', header: 'URL', format: (v) => v || '' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando ofertas...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0 gap-3">
      {/* Search and Export Row */}
      <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Buscar por título..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-gray-50 hover:bg-gray-100 transition-colors"
            />
          </div>
          {/* Export: Excel formateado + CSV genérico */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadFormatted}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-gray-600 hover:text-gray-800"
              title="Descargar Excel formateado"
            >
              <Download className="w-4 h-4" />
              Excel
            </button>
            <ExportButton
              data={filteredOfertas}
              columns={exportColumns}
              filename="ofertas_laborales"
              showLabel={false}
            />
          </div>
        </div>
      </div>

      {/* Table - ajustada al ancho disponible */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm flex flex-col flex-1 min-h-0">
        <div className="overflow-y-auto flex-1">
          <Table className="w-full table-fixed">
            <TableHeader className="sticky top-0 z-10">
              <TableRow className="bg-gradient-to-r from-gray-50 to-gray-100">
                <TableHead className="w-[10%] font-bold text-gray-900 bg-gray-50 text-xs">Fecha</TableHead>
                <TableHead className="w-[25%] font-bold text-gray-900 bg-gray-50 text-xs">Título</TableHead>
                <TableHead className="w-[25%] font-bold text-gray-900 bg-gray-50 text-xs">Conocimientos</TableHead>
                <TableHead className="w-[25%] font-bold text-gray-900 bg-gray-50 text-xs">Competencias</TableHead>
                <TableHead className="w-[8%] font-bold text-gray-900 bg-gray-50 text-xs">Link</TableHead>
                <TableHead className="w-[7%] bg-gray-50"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredOfertas.map((oferta) => (
                  <TableRow key={oferta.id_oferta} className="hover:bg-blue-50 transition-colors group">
                    <TableCell className="text-gray-600 text-xs py-2">
                      {oferta.fecha_publicacion
                        ? new Date(oferta.fecha_publicacion).toLocaleDateString('es-AR')
                        : '-'}
                    </TableCell>
                    <TableCell className="font-medium text-gray-900 text-xs py-2">
                      <div className="truncate" title={oferta.titulo_limpio || oferta.titulo}>
                        {oferta.titulo_limpio || oferta.titulo}
                      </div>
                    </TableCell>
                    <TableCell className="py-2">
                      <div className="flex flex-wrap gap-0.5 overflow-hidden max-h-[40px]">
                        {(oferta.skills_tecnicas || []).slice(0, 3).map((skill, idx) => (
                          <Badge key={idx} variant="secondary" className="text-[10px] px-1 py-0 bg-orange-100 text-orange-800 border-0 truncate max-w-[80px]">
                            {skill}
                          </Badge>
                        ))}
                        {(oferta.skills_tecnicas || []).length > 3 && (
                          <Badge variant="secondary" className="text-[10px] px-1 py-0 bg-gray-100 text-gray-600 border-0">
                            +{(oferta.skills_tecnicas || []).length - 3}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="py-2">
                      <div className="flex flex-wrap gap-0.5 overflow-hidden max-h-[40px]">
                        {(oferta.soft_skills || []).slice(0, 3).map((skill, idx) => (
                          <Badge key={idx} variant="secondary" className="text-[10px] px-1 py-0 bg-purple-100 text-purple-800 border-0 truncate max-w-[80px]">
                            {skill}
                          </Badge>
                        ))}
                        {(oferta.soft_skills || []).length > 3 && (
                          <Badge variant="secondary" className="text-[10px] px-1 py-0 bg-gray-100 text-gray-600 border-0">
                            +{(oferta.soft_skills || []).length - 3}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="py-2">
                      {oferta.url ? (
                        <a
                          href={oferta.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center justify-center w-6 h-6 rounded text-blue-600 hover:text-blue-800 hover:bg-blue-100 transition-all"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      ) : (
                        <span className="text-gray-400 text-xs">-</span>
                      )}
                    </TableCell>
                    <TableCell className="py-2">
                      <IssueRowButton
                        id_oferta={oferta.id_oferta}
                        titulo={oferta.titulo_limpio || oferta.titulo}
                        isco_code={oferta.isco_code || undefined}
                      />
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Pagination Controls */}
      <div className="flex-shrink-0 flex items-center justify-between px-1 py-2">
        <div className="text-xs text-gray-500">
          Mostrando <span className="font-semibold text-gray-700">{offset + 1}</span>-<span className="font-semibold text-gray-700">{Math.min(offset + PAGE_SIZE, total)}</span> de <span className="font-semibold text-gray-700">{total}</span> ofertas
        </div>

        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1 || loading}
              className="h-8 px-3"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Anterior
            </Button>

            <div className="flex items-center gap-1 text-sm">
              <span className="text-gray-500">Página</span>
              <select
                value={currentPage}
                onChange={(e) => setCurrentPage(Number(e.target.value))}
                disabled={loading}
                className="h-8 px-2 border border-gray-300 rounded-md bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <option key={page} value={page}>{page}</option>
                ))}
              </select>
              <span className="text-gray-500">de {totalPages}</span>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages || loading}
              className="h-8 px-3"
            >
              Siguiente
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
