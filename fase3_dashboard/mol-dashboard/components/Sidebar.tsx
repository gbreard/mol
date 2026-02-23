"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Search, ChevronRight, ChevronDown, MapPin, Calendar as CalendarIcon, Timer, Briefcase, Filter, X, Loader2, GraduationCap, Clock, Laptop, Building2 } from "lucide-react";
import { useState, useEffect, useMemo } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { OcupacionTreeNode, DepartamentoGroup, SectorCount } from "@/lib/supabase";
import { useSidebarCounts, useLocalidadesGrouped } from "@/hooks/use-sidebar";
import { capitalize } from "@/lib/utils";

interface SidebarProps {
  filters: {
    territorio: string;
    provincia: string;
    localidad: string[];
    fechaDesde: Date | null;
    fechaHasta: Date | null;
    permanencia: string[];
    searchOcupacion: string;
    ocupacionesSeleccionadas: string[];
    // Filtros de Requerimientos
    nivelEducativo: string[];
    experiencia: string;
    seniority: string[];
    modalidad: string[];
    jornada: string;
    skillsDigitales: boolean;
    sector: string[];
  };
  onFilterChange: (filterType: string, value: any) => void;
}

export function Sidebar({ filters, onFilterChange }: SidebarProps) {
  const [expandedNodes, setExpandedNodes] = useState<string[]>([]);
  const [expandedDepts, setExpandedDepts] = useState<string[]>([]);

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev =>
      prev.includes(nodeId)
        ? prev.filter(id => id !== nodeId)
        : [...prev, nodeId]
    );
  };

  // React Query hooks — replace 3 useEffects + 6 useState
  const { data: sidebarData, isLoading: loadingTree } = useSidebarCounts(filters);
  const { data: localidadesData, isLoading: loadingLocalidades } = useLocalidadesGrouped(filters.provincia, filters);

  // Derive state from query data
  const totalOfertas = sidebarData?.total_ofertas ?? null;
  const sectores = sidebarData?.sectores || [];
  const loadingSectores = loadingTree;

  // Map RPC ocupaciones_tree to OcupacionTreeNode format
  const ISCO_MAJOR_GROUPS: Record<string, string> = {
    '1': 'Directores y gerentes',
    '2': 'Profesionales científicos e intelectuales',
    '3': 'Técnicos y profesionales de nivel medio',
    '4': 'Personal de apoyo administrativo',
    '5': 'Trabajadores de servicios y vendedores',
    '6': 'Agricultores y trabajadores agropecuarios',
    '7': 'Oficiales, operarios y artesanos',
    '8': 'Operadores de instalaciones y máquinas',
    '9': 'Ocupaciones elementales',
    '0': 'Ocupaciones militares',
  };

  const ocupacionesTree: OcupacionTreeNode[] = useMemo(() => {
    if (!sidebarData?.ocupaciones_tree) return [];
    return sidebarData.ocupaciones_tree.map(g => {
      // Aggregate children by ISCO code (multiple ESCO labels share the same ISCO)
      // RPC returns children ordered by count DESC, so first label per ISCO is the most representative
      const byIsco = new Map<string, { label: string; count: number }>();
      for (const c of g.children || []) {
        const existing = byIsco.get(c.id);
        if (existing) {
          existing.count += c.count;
        } else {
          byIsco.set(c.id, { label: c.label, count: c.count });
        }
      }
      return {
        id: `isco-${g.major_group}`,
        label: ISCO_MAJOR_GROUPS[g.major_group] || `Grupo ${g.major_group}`,
        count: g.count,
        children: Array.from(byIsco.entries())
          .map(([id, { label, count }]) => ({ id, label, count }))
          .sort((a, b) => b.count - a.count),
      };
    });
  }, [sidebarData?.ocupaciones_tree]);

  const departamentoGroups: DepartamentoGroup[] = useMemo(() => {
    return localidadesData || [];
  }, [localidadesData]);

  // Filtrar el árbol por búsqueda de texto
  const filteredTree = useMemo(() => {
    const search = filters.searchOcupacion.toLowerCase().trim();
    if (!search) return ocupacionesTree;

    return ocupacionesTree
      .map(group => {
        const matchingChildren = group.children.filter(
          child => child.label.toLowerCase().includes(search) || child.id.includes(search)
        );
        const groupMatches = group.label.toLowerCase().includes(search);

        if (groupMatches) return group; // Mostrar todo el grupo
        if (matchingChildren.length > 0) {
          return { ...group, children: matchingChildren, count: matchingChildren.reduce((s, c) => s + c.count, 0) };
        }
        return null;
      })
      .filter((g): g is OcupacionTreeNode => g !== null);
  }, [ocupacionesTree, filters.searchOcupacion]);

  // Calcular cantidad de filtros activos
  const activeFiltersCount =
    (filters.territorio !== 'nacional' ? 1 : 0) +
    (filters.provincia ? 1 : 0) +
    (filters.localidad.length > 0 ? 1 : 0) +
    (filters.fechaDesde || filters.fechaHasta ? 1 : 0) +
    filters.permanencia.length +
    filters.ocupacionesSeleccionadas.length +
    filters.nivelEducativo.length +
    (filters.experiencia ? 1 : 0) +
    filters.seniority.length +
    filters.modalidad.length +
    (filters.jornada ? 1 : 0) +
    (filters.skillsDigitales ? 1 : 0);

  // Contar filtros de requerimientos activos
  const requerimientosCount =
    filters.nivelEducativo.length +
    (filters.experiencia ? 1 : 0) +
    filters.seniority.length +
    filters.modalidad.length +
    (filters.jornada ? 1 : 0) +
    (filters.skillsDigitales ? 1 : 0);

  const clearAllFilters = () => {
    onFilterChange('territorio', 'nacional');
    onFilterChange('provincia', '');
    onFilterChange('localidad', []);
    onFilterChange('fechaDesde', null);
    onFilterChange('fechaHasta', null);
    onFilterChange('permanencia', []);
    onFilterChange('searchOcupacion', '');
    onFilterChange('ocupacionesSeleccionadas', []);
    // Limpiar filtros de requerimientos
    onFilterChange('nivelEducativo', []);
    onFilterChange('experiencia', '');
    onFilterChange('seniority', []);
    onFilterChange('modalidad', []);
    onFilterChange('jornada', '');
    onFilterChange('skillsDigitales', false);
  };

  const toggleOcupacion = (id: string) => {
    const current = filters.ocupacionesSeleccionadas;
    const newSelection = current.includes(id)
      ? current.filter(i => i !== id)
      : [...current, id];

    onFilterChange('ocupacionesSeleccionadas', newSelection);
  };

  const selectAllInCategory = (categoryId: string) => {
    const category = ocupacionesTree.find(c => c.id === categoryId);
    if (!category) return;

    const childIds = category.children.map(c => c.id);
    const current = filters.ocupacionesSeleccionadas;
    const allSelected = childIds.every(id => current.includes(id));

    const newSelection = allSelected
      ? current.filter(id => !childIds.includes(id))
      : [...new Set([...current, ...childIds])];

    onFilterChange('ocupacionesSeleccionadas', newSelection);
  };

  return (
    <aside className="w-[320px] border-r border-gray-200 bg-gradient-to-b from-white to-gray-50 flex flex-col h-full shadow-sm">
      {/* Header del Sidebar */}
      <div className="border-b border-gray-200 p-4 bg-white">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-bold text-gray-900">Filtros</h2>
            {activeFiltersCount > 0 && (
              <Badge
                variant="default"
                className="bg-blue-600 text-white px-2 py-0.5 text-xs animate-in fade-in zoom-in duration-300"
              >
                {activeFiltersCount}
              </Badge>
            )}
          </div>
          {activeFiltersCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}
              className="h-7 px-2 text-xs text-gray-600 hover:text-red-600 hover:bg-red-50 transition-all animate-in fade-in slide-in-from-right duration-300"
            >
              <X className="w-3 h-3 mr-1" />
              Limpiar
            </Button>
          )}
        </div>
        <p className="text-xs text-gray-500">
          Mostrando{' '}
          <span className="font-semibold text-blue-600">
            {totalOfertas !== null ? totalOfertas.toLocaleString() : '...'}
          </span>{' '}
          ofertas
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <Accordion type="multiple" defaultValue={["periodo"]} className="w-full">

          {/* Territorio */}
          <AccordionItem value="territorio" className="border-b border-gray-200">
            <AccordionTrigger className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-bold text-gray-900">Territorio</span>
                {filters.territorio !== 'nacional' && (
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4 space-y-3">
              <RadioGroup value={filters.territorio} onValueChange={(value) => {
                onFilterChange('territorio', value);
                if (value === 'nacional') {
                  onFilterChange('provincia', '');
                  onFilterChange('localidad', []);
                }
              }}>
                {/* Nacional */}
                <div className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                  filters.territorio === 'nacional' ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                }`}>
                  <RadioGroupItem value="nacional" id="nacional" />
                  <Label htmlFor="nacional" className="text-sm font-semibold cursor-pointer flex-1">Nacional</Label>
                </div>

                {/* Provincia */}
                <div className="space-y-2">
                  <div className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                    filters.territorio === 'provincia' ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                  }`}>
                    <RadioGroupItem value="provincia" id="provincia" />
                    <Label htmlFor="provincia" className="text-sm font-semibold cursor-pointer flex-1">Provincia</Label>
                  </div>

                  {filters.territorio === 'provincia' && (
                    <div className="ml-6 space-y-1.5 animate-in fade-in slide-in-from-top duration-300">
                      <Label className="text-xs text-gray-600">Seleccionar provincia</Label>
                      <select
                        value={filters.provincia}
                        onChange={(e) => {
                          onFilterChange('provincia', e.target.value);
                          onFilterChange('localidad', []);
                        }}
                        className="w-full p-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white hover:border-blue-400 transition-colors"
                      >
                        <option value="">Todas las provincias</option>
                        <option value="caba">Ciudad Autónoma de Buenos Aires</option>
                        <option value="buenosaires">Buenos Aires</option>
                        <option value="cordoba">Córdoba</option>
                        <option value="santafe">Santa Fe</option>
                        <option value="mendoza">Mendoza</option>
                        <option value="tucuman">Tucumán</option>
                        <option value="entrerios">Entre Ríos</option>
                        <option value="salta">Salta</option>
                        <option value="chaco">Chaco</option>
                        <option value="corrientes">Corrientes</option>
                        <option value="misiones">Misiones</option>
                        <option value="formosa">Formosa</option>
                        <option value="jujuy">Jujuy</option>
                        <option value="catamarca">Catamarca</option>
                        <option value="larioja">La Rioja</option>
                        <option value="sanjuan">San Juan</option>
                        <option value="sanluis">San Luis</option>
                        <option value="neuquen">Neuquén</option>
                        <option value="rionegro">Río Negro</option>
                        <option value="chubut">Chubut</option>
                        <option value="santacruz">Santa Cruz</option>
                        <option value="tierradelfuego">Tierra del Fuego</option>
                        <option value="lapampa">La Pampa</option>
                        <option value="santiago">Santiago del Estero</option>
                      </select>

                      {/* Localidad multi-select agrupada por departamento */}
                      {filters.provincia && (
                        <div className="mt-3 space-y-1.5 animate-in fade-in slide-in-from-top duration-300">
                          <div className="flex items-center justify-between">
                            <Label className="text-xs text-gray-600">
                              Localidad
                              {filters.localidad.length > 0 && (
                                <Badge variant="secondary" className="ml-1.5 text-xs px-1.5 py-0 bg-blue-100 text-blue-700">
                                  {filters.localidad.length}
                                </Badge>
                              )}
                            </Label>
                            {filters.localidad.length > 0 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onFilterChange('localidad', [])}
                                className="h-5 px-1.5 text-xs text-gray-500 hover:text-red-600"
                              >
                                Limpiar
                              </Button>
                            )}
                          </div>
                          {loadingLocalidades ? (
                            <div className="flex items-center gap-2 p-2 text-xs text-gray-500">
                              <Loader2 className="w-3 h-3 animate-spin" />
                              Cargando localidades...
                            </div>
                          ) : (
                            <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg bg-white">
                              {departamentoGroups.map((group) => {
                                const deptLocalidades = group.localidades.map(l => l.localidad);
                                const selectedInDept = deptLocalidades.filter(l => filters.localidad.includes(l)).length;
                                const allSelectedInDept = selectedInDept === deptLocalidades.length;
                                const isExpanded = expandedDepts.includes(group.departamento);

                                return (
                                  <div key={group.departamento} className="border-b border-gray-100 last:border-b-0">
                                    {/* Departamento header */}
                                    <div className="flex items-center gap-1 px-2 py-1.5 bg-gray-50 hover:bg-gray-100 transition-colors">
                                      <button
                                        onClick={() => setExpandedDepts(prev =>
                                          prev.includes(group.departamento)
                                            ? prev.filter(d => d !== group.departamento)
                                            : [...prev, group.departamento]
                                        )}
                                        className="flex items-center gap-1 flex-1 text-left"
                                      >
                                        {isExpanded ? (
                                          <ChevronDown className="w-3 h-3 text-gray-500 flex-shrink-0" />
                                        ) : (
                                          <ChevronRight className="w-3 h-3 text-gray-500 flex-shrink-0" />
                                        )}
                                        <span className="text-xs font-semibold text-gray-700 truncate">{group.departamento}</span>
                                        <span className="text-xs text-gray-400 flex-shrink-0">({group.totalCount})</span>
                                      </button>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => {
                                          const current = filters.localidad;
                                          const newSelection = allSelectedInDept
                                            ? current.filter(l => !deptLocalidades.includes(l))
                                            : [...new Set([...current, ...deptLocalidades])];
                                          onFilterChange('localidad', newSelection);
                                        }}
                                        className="h-5 px-1.5 text-xs text-blue-600 hover:bg-blue-50 flex-shrink-0"
                                      >
                                        {allSelectedInDept ? 'Quitar' : 'Todas'}
                                      </Button>
                                    </div>
                                    {/* Localidades */}
                                    {isExpanded && (
                                      <div className="px-1 py-0.5">
                                        {group.localidades.map(({ localidad, count }) => (
                                          <div
                                            key={localidad}
                                            className={`flex items-center gap-2 px-2 py-1 rounded transition-all ${
                                              filters.localidad.includes(localidad)
                                                ? 'bg-blue-50'
                                                : 'hover:bg-gray-50'
                                            }`}
                                          >
                                            <Checkbox
                                              id={`loc-${localidad}`}
                                              checked={filters.localidad.includes(localidad)}
                                              onCheckedChange={(checked) => {
                                                const newValue = checked
                                                  ? [...filters.localidad, localidad]
                                                  : filters.localidad.filter(l => l !== localidad);
                                                onFilterChange('localidad', newValue);
                                              }}
                                              className="h-3.5 w-3.5"
                                            />
                                            <Label htmlFor={`loc-${localidad}`} className="text-xs text-gray-600 cursor-pointer flex-1 truncate">
                                              {localidad}
                                            </Label>
                                            <span className="text-xs text-gray-400 flex-shrink-0">{count}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                              {departamentoGroups.length === 0 && (
                                <p className="text-xs text-gray-500 text-center py-3">Sin localidades</p>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </RadioGroup>
            </AccordionContent>
          </AccordionItem>

          {/* Período - Rango de Fechas */}
          <AccordionItem value="periodo" className="border-b border-gray-200">
            <AccordionTrigger className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-2">
                <CalendarIcon className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-bold text-gray-900">Período</span>
                {(filters.fechaDesde || filters.fechaHasta) && (
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4 space-y-4">
              <div className="space-y-2">
                <div className="grid grid-cols-3 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300"
                    onClick={() => {
                      const hoy = new Date();
                      const semanaAtras = new Date(hoy);
                      semanaAtras.setDate(hoy.getDate() - 7);
                      onFilterChange('fechaDesde', semanaAtras);
                      onFilterChange('fechaHasta', hoy);
                    }}
                  >
                    Última semana
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300"
                    onClick={() => {
                      const hoy = new Date();
                      const mesAtras = new Date(hoy);
                      mesAtras.setMonth(hoy.getMonth() - 1);
                      onFilterChange('fechaDesde', mesAtras);
                      onFilterChange('fechaHasta', hoy);
                    }}
                  >
                    Último mes
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300"
                    onClick={() => {
                      const hoy = new Date();
                      const añoAtras = new Date(hoy);
                      añoAtras.setFullYear(hoy.getFullYear() - 1);
                      onFilterChange('fechaDesde', añoAtras);
                      onFilterChange('fechaHasta', hoy);
                    }}
                  >
                    Último año
                  </Button>
                </div>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="bg-white px-2 text-gray-500">o seleccione fechas personalizadas</span>
                </div>
              </div>

              {/* Fecha Desde */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-gray-700">Desde</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-full justify-start text-left font-normal text-sm"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {filters.fechaDesde ? format(filters.fechaDesde, "PPP", { locale: es }) : "Seleccionar fecha"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.fechaDesde || undefined}
                      onSelect={(date) => onFilterChange('fechaDesde', date)}
                      initialFocus
                      locale={es}
                    />
                  </PopoverContent>
                </Popover>
              </div>

              {/* Fecha Hasta */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-gray-700">Hasta</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-full justify-start text-left font-normal text-sm"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {filters.fechaHasta ? format(filters.fechaHasta, "PPP", { locale: es }) : "Seleccionar fecha"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.fechaHasta || undefined}
                      onSelect={(date) => onFilterChange('fechaHasta', date)}
                      initialFocus
                      locale={es}
                      disabled={(date) => filters.fechaDesde ? date < filters.fechaDesde : false}
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Permanencia */}
          <AccordionItem value="permanencia" className="border-b border-gray-200">
            <AccordionTrigger className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-2">
                <Timer className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-bold text-gray-900">Permanencia</span>
                {filters.permanencia.length > 0 && (
                  <Badge variant="secondary" className="text-xs px-1.5 py-0 bg-blue-100 text-blue-700">
                    {filters.permanencia.length}
                  </Badge>
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-2">
                <div className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                  filters.permanencia.includes('baja') ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                }`}>
                  <Checkbox
                    id="perm-baja"
                    checked={filters.permanencia.includes('baja')}
                    onCheckedChange={(checked) => {
                      const newValue = checked
                        ? [...filters.permanencia, 'baja']
                        : filters.permanencia.filter(p => p !== 'baja');
                      onFilterChange('permanencia', newValue);
                    }}
                  />
                  <Label htmlFor="perm-baja" className="text-sm font-normal cursor-pointer flex-1">Baja (1-7 días)</Label>
                </div>
                <div className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                  filters.permanencia.includes('media') ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                }`}>
                  <Checkbox
                    id="perm-media"
                    checked={filters.permanencia.includes('media')}
                    onCheckedChange={(checked) => {
                      const newValue = checked
                        ? [...filters.permanencia, 'media']
                        : filters.permanencia.filter(p => p !== 'media');
                      onFilterChange('permanencia', newValue);
                    }}
                  />
                  <Label htmlFor="perm-media" className="text-sm font-normal cursor-pointer flex-1">Media (8-30 días)</Label>
                </div>
                <div className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                  filters.permanencia.includes('alta') ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                }`}>
                  <Checkbox
                    id="perm-alta"
                    checked={filters.permanencia.includes('alta')}
                    onCheckedChange={(checked) => {
                      const newValue = checked
                        ? [...filters.permanencia, 'alta']
                        : filters.permanencia.filter(p => p !== 'alta');
                      onFilterChange('permanencia', newValue);
                    }}
                  />
                  <Label htmlFor="perm-alta" className="text-sm font-normal cursor-pointer flex-1">Alta (+30 días)</Label>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Sector CLAE */}
          <AccordionItem value="sector" className="border-b border-gray-200">
            <AccordionTrigger className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-bold text-gray-900">Sector</span>
                {filters.sector.length > 0 && (
                  <Badge variant="secondary" className="text-xs px-1.5 py-0 bg-blue-100 text-blue-700">
                    {filters.sector.length}
                  </Badge>
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              {loadingSectores ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="ml-2 text-xs text-gray-500">Cargando...</span>
                </div>
              ) : sectores.length === 0 ? (
                <p className="text-xs text-gray-500 py-2">Sin datos de sector</p>
              ) : (
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {sectores.map((s) => (
                    <div
                      key={s.sector}
                      className={`flex items-center space-x-2 p-2 rounded-lg transition-all duration-200 ${
                        filters.sector.includes(s.sector) ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                      }`}
                    >
                      <Checkbox
                        id={`sector-${s.sector}`}
                        checked={filters.sector.includes(s.sector)}
                        onCheckedChange={(checked) => {
                          const newValue = checked
                            ? [...filters.sector, s.sector]
                            : filters.sector.filter(v => v !== s.sector);
                          onFilterChange('sector', newValue);
                        }}
                      />
                      <Label htmlFor={`sector-${s.sector}`} className="text-xs font-normal cursor-pointer flex-1 truncate">
                        {s.sector}
                      </Label>
                      <span className="text-[10px] text-gray-400 font-medium">{s.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </AccordionContent>
          </AccordionItem>

          {/* Requerimientos */}
          <AccordionItem value="requerimientos" className="border-b border-gray-200">
            <AccordionTrigger className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-bold text-gray-900">Requerimientos</span>
                {requerimientosCount > 0 && (
                  <Badge variant="secondary" className="text-xs px-1.5 py-0 bg-blue-100 text-blue-700">
                    {requerimientosCount}
                  </Badge>
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4 space-y-4">
              {/* Nivel Educativo */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-gray-700">Nivel Educativo</Label>
                {[
                  { id: 'edu-primario', value: 'primario', label: 'Primario' },
                  { id: 'edu-secundario', value: 'secundario', label: 'Secundario' },
                  { id: 'edu-terciario', value: 'terciario', label: 'Terciario' },
                  { id: 'edu-universitario', value: 'universitario', label: 'Universitario' },
                  { id: 'edu-posgrado', value: 'posgrado', label: 'Posgrado' },
                ].map(opt => (
                  <div key={opt.id} className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                    filters.nivelEducativo.includes(opt.value) ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                  }`}>
                    <Checkbox
                      id={opt.id}
                      checked={filters.nivelEducativo.includes(opt.value)}
                      onCheckedChange={(checked) => {
                        const newValue = checked
                          ? [...filters.nivelEducativo, opt.value]
                          : filters.nivelEducativo.filter(v => v !== opt.value);
                        onFilterChange('nivelEducativo', newValue);
                      }}
                    />
                    <Label htmlFor={opt.id} className="text-sm font-normal cursor-pointer flex-1">{opt.label}</Label>
                  </div>
                ))}
              </div>

              {/* Experiencia */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-gray-700">Experiencia</Label>
                <select
                  value={filters.experiencia}
                  onChange={(e) => onFilterChange('experiencia', e.target.value)}
                  className="w-full p-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white hover:border-blue-400 transition-colors"
                >
                  <option value="">Todas</option>
                  <option value="sin_experiencia">Sin experiencia</option>
                  <option value="1_2_anios">1-2 años</option>
                  <option value="3_5_anios">3-5 años</option>
                  <option value="5_mas">Más de 5 años</option>
                </select>
              </div>

              {/* Seniority */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-gray-700">Seniority</Label>
                {[
                  { id: 'sen-trainee', value: 'trainee', label: 'Trainee' },
                  { id: 'sen-junior', value: 'junior', label: 'Junior' },
                  { id: 'sen-semisenior', value: 'semi-senior', label: 'Semi-Senior' },
                  { id: 'sen-senior', value: 'senior', label: 'Senior' },
                  { id: 'sen-manager', value: 'manager', label: 'Manager' },
                ].map(opt => (
                  <div key={opt.id} className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                    filters.seniority.includes(opt.value) ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                  }`}>
                    <Checkbox
                      id={opt.id}
                      checked={filters.seniority.includes(opt.value)}
                      onCheckedChange={(checked) => {
                        const newValue = checked
                          ? [...filters.seniority, opt.value]
                          : filters.seniority.filter(v => v !== opt.value);
                        onFilterChange('seniority', newValue);
                      }}
                    />
                    <Label htmlFor={opt.id} className="text-sm font-normal cursor-pointer flex-1">{opt.label}</Label>
                  </div>
                ))}
              </div>

              {/* Modalidad */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-gray-700">Modalidad</Label>
                {[
                  { id: 'mod-presencial', value: 'presencial', label: 'Presencial' },
                  { id: 'mod-remoto', value: 'remoto', label: 'Remoto' },
                  { id: 'mod-hibrido', value: 'hibrido', label: 'Híbrido' },
                ].map(opt => (
                  <div key={opt.id} className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                    filters.modalidad.includes(opt.value) ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
                  }`}>
                    <Checkbox
                      id={opt.id}
                      checked={filters.modalidad.includes(opt.value)}
                      onCheckedChange={(checked) => {
                        const newValue = checked
                          ? [...filters.modalidad, opt.value]
                          : filters.modalidad.filter(v => v !== opt.value);
                        onFilterChange('modalidad', newValue);
                      }}
                    />
                    <Label htmlFor={opt.id} className="text-sm font-normal cursor-pointer flex-1">{opt.label}</Label>
                  </div>
                ))}
              </div>

              {/* Jornada */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-gray-700">Jornada</Label>
                <select
                  value={filters.jornada}
                  onChange={(e) => onFilterChange('jornada', e.target.value)}
                  className="w-full p-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white hover:border-blue-400 transition-colors"
                >
                  <option value="">Todas</option>
                  <option value="full_time">Full-time</option>
                  <option value="part_time">Part-time</option>
                  <option value="por_horas">Por horas</option>
                </select>
              </div>

              {/* Skills Digitales */}
              <div className={`flex items-center space-x-2 p-2.5 rounded-lg transition-all duration-200 ${
                filters.skillsDigitales ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-100'
              }`}>
                <Checkbox
                  id="skills-digitales"
                  checked={filters.skillsDigitales}
                  onCheckedChange={(checked) => onFilterChange('skillsDigitales', checked)}
                />
                <div className="flex items-center gap-2 flex-1">
                  <Laptop className="w-4 h-4 text-blue-600" />
                  <Label htmlFor="skills-digitales" className="text-sm font-normal cursor-pointer">
                    Requiere skills digitales
                  </Label>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Ocupación */}
          <AccordionItem value="ocupacion" className="border-b-0">
            <AccordionTrigger className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-bold text-gray-900">Ocupación</span>
                {filters.ocupacionesSeleccionadas.length > 0 && (
                  <Badge variant="secondary" className="text-xs px-1.5 py-0 bg-blue-100 text-blue-700">
                    {filters.ocupacionesSeleccionadas.length}
                  </Badge>
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              {/* Búsqueda */}
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Buscar ocupación..."
                  value={filters.searchOcupacion}
                  onChange={(e) => onFilterChange('searchOcupacion', e.target.value)}
                  className="pl-9 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500 transition-all"
                />
              </div>

              {/* Árbol de Ocupaciones */}
              {loadingTree ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600 mr-2" />
                  <span className="text-xs text-gray-500">Cargando ocupaciones...</span>
                </div>
              ) : filteredTree.length === 0 ? (
                <p className="text-xs text-gray-500 text-center py-4">
                  {filters.searchOcupacion ? 'Sin resultados para la búsqueda' : 'No hay ocupaciones disponibles'}
                </p>
              ) : (
                <div className="space-y-2">
                  {filteredTree.map((category) => {
                    const childIds = category.children.map(c => c.id);
                    const selectedCount = childIds.filter(id => filters.ocupacionesSeleccionadas.includes(id)).length;
                    const allSelected = selectedCount === childIds.length && childIds.length > 0;

                    return (
                      <div key={category.id} className="space-y-1">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => toggleNode(category.id)}
                            className="flex-1 flex items-center gap-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-blue-50 py-2 px-2 rounded-md transition-all"
                          >
                            {expandedNodes.includes(category.id) ? (
                              <ChevronDown className="w-4 h-4 transition-transform" />
                            ) : (
                              <ChevronRight className="w-4 h-4 transition-transform" />
                            )}
                            <span className="font-medium flex-1 text-left text-xs leading-tight">{capitalize(category.label)}</span>
                            <Badge variant="outline" className="text-xs px-1.5 py-0 flex-shrink-0">
                              {category.count}
                            </Badge>
                          </button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => selectAllInCategory(category.id)}
                            className="h-7 px-2 text-xs text-blue-600 hover:bg-blue-50 flex-shrink-0"
                          >
                            {allSelected ? 'Quitar' : 'Todas'}
                          </Button>
                        </div>
                        {expandedNodes.includes(category.id) && (
                          <div className="ml-6 space-y-1 animate-in slide-in-from-top-2 duration-200">
                            {category.children.map((child) => (
                              <div
                                key={child.id}
                                className={`flex items-center gap-2 p-2 rounded-md transition-all duration-200 ${
                                  filters.ocupacionesSeleccionadas.includes(child.id)
                                    ? 'bg-blue-50 border border-blue-200'
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Checkbox
                                  id={`ocup-${child.id}`}
                                  checked={filters.ocupacionesSeleccionadas.includes(child.id)}
                                  onCheckedChange={() => toggleOcupacion(child.id)}
                                />
                                <Label
                                  htmlFor={`ocup-${child.id}`}
                                  className="text-xs text-gray-600 cursor-pointer flex-1 leading-tight"
                                >
                                  {capitalize(child.label)}
                                </Label>
                                <span className="text-xs text-gray-400 flex-shrink-0">{child.count}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </aside>
  );
}
