"use client";

import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, ExternalLink, Filter, Loader2, AlertCircle } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect } from "react";
import { getOfertas, OfertaDashboard } from "@/lib/supabase";
import { DashboardFilters } from "@/lib/types";
import { IssueRowButton } from "@/components/issues";

interface OfertasLaboralesProps {
  filters: DashboardFilters;
}

export function OfertasLaborales({ filters }: OfertasLaboralesProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [modalidadFilter, setModalidadFilter] = useState('all');
  const [seniorityFilter, setSeniorityFilter] = useState('all');
  const [provinciaFilter, setProvinciaFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ofertas, setOfertas] = useState<OfertaDashboard[]>([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const { ofertas: data, total: count } = await getOfertas(50, 0, filters);
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
  }, [filters]);

  const filteredOfertas = ofertas.filter(oferta => {
    const matchesSearch = oferta.titulo?.toLowerCase().includes(searchTerm.toLowerCase()) || false;
    const matchesModalidad = modalidadFilter === 'all' || oferta.modalidad === modalidadFilter;
    const matchesSeniority = seniorityFilter === 'all' || oferta.nivel_seniority === seniorityFilter;
    const matchesProvincia = provinciaFilter === 'all' || oferta.provincia === provinciaFilter;
    return matchesSearch && matchesModalidad && matchesSeniority && matchesProvincia;
  });

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
      {/* Filters Row - más compacto */}
      <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm flex-shrink-0">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-semibold text-gray-900">Filtros:</span>
          </div>
          <div className="flex flex-wrap gap-3 flex-1">
          <Select value={modalidadFilter} onValueChange={setModalidadFilter}>
            <SelectTrigger className="w-[140px] bg-gray-50 hover:bg-gray-100 transition-colors h-9 text-sm">
              <SelectValue placeholder="Modalidad" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas</SelectItem>
              <SelectItem value="presencial">Presencial</SelectItem>
              <SelectItem value="remoto">Remoto</SelectItem>
              <SelectItem value="hibrido">Híbrido</SelectItem>
            </SelectContent>
          </Select>

          <Select value={seniorityFilter} onValueChange={setSeniorityFilter}>
            <SelectTrigger className="w-[140px] bg-gray-50 hover:bg-gray-100 transition-colors h-9 text-sm">
              <SelectValue placeholder="Seniority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="junior">Junior</SelectItem>
              <SelectItem value="semi-senior">Semi-Senior</SelectItem>
              <SelectItem value="senior">Senior</SelectItem>
              <SelectItem value="manager">Manager</SelectItem>
            </SelectContent>
          </Select>

          <Select value={provinciaFilter} onValueChange={setProvinciaFilter}>
            <SelectTrigger className="w-[150px] bg-gray-50 hover:bg-gray-100 transition-colors h-9 text-sm">
              <SelectValue placeholder="Provincia" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas</SelectItem>
              <SelectItem value="Capital Federal">Capital Federal</SelectItem>
              <SelectItem value="Buenos Aires">Buenos Aires</SelectItem>
              <SelectItem value="Córdoba">Córdoba</SelectItem>
              <SelectItem value="Santa Fe">Santa Fe</SelectItem>
              <SelectItem value="Mendoza">Mendoza</SelectItem>
            </SelectContent>
          </Select>

          <div className="relative min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Buscar por título"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-gray-50 hover:bg-gray-100 transition-colors"
            />
          </div>
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

      {/* Results count - compacto */}
      <div className="flex-shrink-0 text-xs text-gray-500 px-1">
        Mostrando <span className="font-semibold text-gray-700">{filteredOfertas.length}</span> de <span className="font-semibold text-gray-700">{total}</span> ofertas
      </div>
    </div>
  );
}
