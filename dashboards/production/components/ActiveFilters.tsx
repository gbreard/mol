"use client";

import { X, MapPin, Calendar, Timer, Briefcase } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface ActiveFiltersProps {
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
  onRemoveFilter: (filterType: string) => void;
}

export function ActiveFilters({ filters, onRemoveFilter }: ActiveFiltersProps) {
  const activeFilters = [];

  // Territorio
  if (filters.territorio !== 'nacional' || filters.provincia || filters.localidad) {
    let label = '';
    if (filters.localidad) {
      label = `Localidad: ${filters.localidad}`;
    } else if (filters.provincia) {
      label = `Provincia: ${filters.provincia}`;
    } else {
      label = `Territorio: ${filters.territorio}`;
    }
    activeFilters.push({
      key: 'territorio',
      label,
      icon: MapPin,
      onRemove: () => onRemoveFilter('territorio')
    });
  }

  // Fechas
  if (filters.fechaDesde || filters.fechaHasta) {
    const desde = filters.fechaDesde ? filters.fechaDesde.toLocaleDateString('es-AR') : '...';
    const hasta = filters.fechaHasta ? filters.fechaHasta.toLocaleDateString('es-AR') : '...';
    activeFilters.push({
      key: 'fechas',
      label: `Período: ${desde} - ${hasta}`,
      icon: Calendar,
      onRemove: () => onRemoveFilter('fechas')
    });
  }

  // Permanencia
  if (filters.permanencia.length > 0) {
    activeFilters.push({
      key: 'permanencia',
      label: `Permanencia: ${filters.permanencia.length} seleccionada${filters.permanencia.length > 1 ? 's' : ''}`,
      icon: Timer,
      onRemove: () => onRemoveFilter('permanencia')
    });
  }

  // Ocupaciones
  if (filters.ocupacionesSeleccionadas.length > 0) {
    activeFilters.push({
      key: 'ocupaciones',
      label: `Ocupaciones: ${filters.ocupacionesSeleccionadas.length} seleccionada${filters.ocupacionesSeleccionadas.length > 1 ? 's' : ''}`,
      icon: Briefcase,
      onRemove: () => onRemoveFilter('ocupaciones')
    });
  }

  if (activeFilters.length === 0) {
    return null;
  }

  return (
    <div className="mb-6 bg-white border border-gray-200 rounded-xl p-4 shadow-sm animate-in fade-in slide-in-from-top duration-300">
      <div className="flex items-center flex-wrap gap-2">
        <span className="text-sm font-semibold text-gray-700 mr-2">Filtros activos:</span>
        {activeFilters.map((filter) => {
          const Icon = filter.icon;
          return (
            <Badge
              key={filter.key}
              variant="secondary"
              className="bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1.5 text-sm font-medium hover:bg-blue-100 transition-colors flex items-center gap-2 animate-in fade-in zoom-in duration-200"
            >
              <Icon className="w-3.5 h-3.5" />
              {filter.label}
              <button
                onClick={filter.onRemove}
                className="ml-1 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                aria-label={`Remover filtro ${filter.label}`}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </Badge>
          );
        })}
      </div>
    </div>
  );
}
