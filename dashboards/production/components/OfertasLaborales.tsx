"use client";

import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, ExternalLink, Filter, Loader2, AlertCircle } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect } from "react";
import { getOfertas, OfertaDashboard } from "@/lib/supabase";
import { DashboardFilters } from "@/lib/types";

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
    <div className="space-y-6">
      {/* Filters Row */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-blue-600" />
          <h3 className="font-bold text-gray-900">Filtros de búsqueda</h3>
        </div>
        <div className="grid grid-cols-4 gap-4">
          <Select value={modalidadFilter} onValueChange={setModalidadFilter}>
            <SelectTrigger className="bg-gray-50 hover:bg-gray-100 transition-colors">
              <SelectValue placeholder="Modalidad" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas las modalidades</SelectItem>
              <SelectItem value="presencial">Presencial</SelectItem>
              <SelectItem value="remoto">Remoto</SelectItem>
              <SelectItem value="hibrido">Híbrido</SelectItem>
            </SelectContent>
          </Select>

          <Select value={seniorityFilter} onValueChange={setSeniorityFilter}>
            <SelectTrigger className="bg-gray-50 hover:bg-gray-100 transition-colors">
              <SelectValue placeholder="Nivel de experiencia" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los niveles</SelectItem>
              <SelectItem value="junior">Junior</SelectItem>
              <SelectItem value="semi-senior">Semi-Senior</SelectItem>
              <SelectItem value="senior">Senior</SelectItem>
              <SelectItem value="manager">Manager</SelectItem>
            </SelectContent>
          </Select>

          <Select value={provinciaFilter} onValueChange={setProvinciaFilter}>
            <SelectTrigger className="bg-gray-50 hover:bg-gray-100 transition-colors">
              <SelectValue placeholder="Provincia" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas las provincias</SelectItem>
              <SelectItem value="Capital Federal">Capital Federal</SelectItem>
              <SelectItem value="Buenos Aires">Buenos Aires</SelectItem>
              <SelectItem value="Córdoba">Córdoba</SelectItem>
              <SelectItem value="Santa Fe">Santa Fe</SelectItem>
              <SelectItem value="Mendoza">Mendoza</SelectItem>
            </SelectContent>
          </Select>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Buscar por título de oferta"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-gray-50 hover:bg-gray-100 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-gradient-to-r from-gray-50 to-gray-100">
                <TableHead className="w-[180px] font-bold text-gray-900">Ocupación</TableHead>
                <TableHead className="w-[250px] font-bold text-gray-900">Título de la oferta</TableHead>
                <TableHead className="w-[120px] font-bold text-gray-900">Fecha de publicación</TableHead>
                <TableHead className="w-[280px] font-bold text-gray-900">Conocimientos</TableHead>
                <TableHead className="w-[280px] font-bold text-gray-900">Competencias / Capacidades</TableHead>
                <TableHead className="w-[80px] font-bold text-gray-900">Link</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredOfertas.map((oferta) => (
                  <TableRow key={oferta.id_oferta} className="hover:bg-blue-50 transition-colors">
                    <TableCell className="font-semibold text-gray-900">{oferta.isco_label || 'Sin clasificar'}</TableCell>
                    <TableCell className="font-medium">{oferta.titulo}</TableCell>
                    <TableCell className="text-gray-600">
                      {oferta.fecha_publicacion
                        ? new Date(oferta.fecha_publicacion).toLocaleDateString('es-AR')
                        : '-'}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {(oferta.skills_tecnicas || []).slice(0, 3).map((skill, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs bg-gradient-to-r from-orange-100 to-orange-200 text-orange-800 border-0 font-medium">
                            {skill}
                          </Badge>
                        ))}
                        {(oferta.skills_tecnicas || []).length > 3 && (
                          <Badge variant="secondary" className="text-xs bg-gray-100 text-gray-600 border-0">
                            +{(oferta.skills_tecnicas || []).length - 3}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {(oferta.soft_skills || []).slice(0, 3).map((skill, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs bg-gradient-to-r from-purple-100 to-purple-200 text-purple-800 border-0 font-medium">
                            {skill}
                          </Badge>
                        ))}
                        {(oferta.soft_skills || []).length > 3 && (
                          <Badge variant="secondary" className="text-xs bg-gray-100 text-gray-600 border-0">
                            +{(oferta.soft_skills || []).length - 3}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {oferta.url ? (
                        <a
                          href={oferta.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-blue-600 hover:text-blue-800 hover:bg-blue-100 transition-all"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Results count */}
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium text-gray-600">
          Mostrando <span className="font-bold text-gray-900">{filteredOfertas.length}</span> de <span className="font-bold text-gray-900">{total}</span> ofertas laborales
        </div>
      </div>
    </div>
  );
}
