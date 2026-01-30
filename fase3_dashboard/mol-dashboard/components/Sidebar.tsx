"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Search, ChevronRight, ChevronDown, MapPin, Calendar as CalendarIcon, Timer, Briefcase, Filter, X, Loader2 } from "lucide-react";
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
import { getTotalOfertas, getOcupacionesTree, OcupacionTreeNode } from "@/lib/supabase";

interface SidebarProps {
  filters: {
    territorio: string;
    provincia: string;
    localidad: string;
    fechaDesde: Date | null;
    fechaHasta: Date | null;
    permanencia: string[];
    searchOcupacion: string;
    ocupacionesSeleccionadas: string[];
  };
  onFilterChange: (filterType: string, value: any) => void;
}

export function Sidebar({ filters, onFilterChange }: SidebarProps) {
  const [expandedNodes, setExpandedNodes] = useState<string[]>([]);
  const [ocupacionesTree, setOcupacionesTree] = useState<OcupacionTreeNode[]>([]);
  const [totalOfertas, setTotalOfertas] = useState<number | null>(null);
  const [loadingTree, setLoadingTree] = useState(true);

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev =>
      prev.includes(nodeId)
        ? prev.filter(id => id !== nodeId)
        : [...prev, nodeId]
    );
  };

  // Cargar total y árbol de ocupaciones cuando cambian filtros relevantes
  // (excluimos ocupacionesSeleccionadas para no re-cargar el árbol al seleccionar)
  useEffect(() => {
    async function loadSidebarData() {
      try {
        setLoadingTree(true);
        const [total, tree] = await Promise.all([
          getTotalOfertas(filters),
          getOcupacionesTree(filters)
        ]);
        setTotalOfertas(total);
        setOcupacionesTree(tree);

        // Auto-expandir el primer grupo si hay datos
        if (tree.length > 0 && expandedNodes.length === 0) {
          setExpandedNodes([tree[0].id]);
        }
      } catch (err) {
        console.error('Error cargando datos sidebar:', err);
      } finally {
        setLoadingTree(false);
      }
    }
    loadSidebarData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.territorio, filters.provincia, filters.localidad, filters.fechaDesde, filters.fechaHasta, filters.permanencia]);

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
    (filters.localidad ? 1 : 0) +
    (filters.fechaDesde || filters.fechaHasta ? 1 : 0) +
    filters.permanencia.length +
    filters.ocupacionesSeleccionadas.length;

  const clearAllFilters = () => {
    onFilterChange('territorio', 'nacional');
    onFilterChange('provincia', '');
    onFilterChange('localidad', '');
    onFilterChange('fechaDesde', null);
    onFilterChange('fechaHasta', null);
    onFilterChange('permanencia', []);
    onFilterChange('searchOcupacion', '');
    onFilterChange('ocupacionesSeleccionadas', []);
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
        <Accordion type="multiple" defaultValue={[]} className="w-full">

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
              <RadioGroup value={filters.territorio} onValueChange={(value) => onFilterChange('territorio', value)}>
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
                        onChange={(e) => onFilterChange('provincia', e.target.value)}
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
              {/* Opciones rápidas */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-gray-700">Opciones rápidas</Label>
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
                    Semana
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
                    Mes
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
                    Año
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
                            <span className="font-medium flex-1 text-left text-xs leading-tight">{category.label}</span>
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
                                  {child.label}
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
