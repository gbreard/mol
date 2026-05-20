"use client";

import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";
import { ValidationFiltersState } from "@/lib/types";

interface EmptyResultsWithFiltersProps {
  filters: ValidationFiltersState;
  onClearFiltersKeepSearch: () => void;
  onClearAll: () => void;
}

/**
 * Empty state que distingue 3 casos:
 *  1. Búsqueda + otros filtros activos → posiblemente el ID/término no
 *     cumple con los filtros. Sugerencia: limpiar filtros manteniendo
 *     la búsqueda.
 *  2. Sólo búsqueda activa → mensaje simple "sin resultados".
 *  3. Sólo filtros activos (sin búsqueda) → mensaje genérico.
 *
 * Reportado en B2: docs/issues/2026-05-19_B2_buscador_id_inconsistente.md
 */

// Mapa de campo de filtro → label legible para el banner.
// Excluye search (es lo que el usuario está buscando).
const FILTER_LABELS: Record<keyof ValidationFiltersState, string> = {
  iscoGroup: "ISCO",
  portal: "Portal",
  provincia: "Provincia",
  metodo: "Método",
  search: "Búsqueda",
  seniority: "Seniority",
  modalidad: "Modalidad",
  sector: "Sector",
  nivelEducativo: "Nivel educativo",
  scoreRange: "Score",
  estadoValidacion: "Estado",
  runId: "Corrida",
};

function getActiveOtherFilters(filters: ValidationFiltersState): { key: string; label: string; value: string }[] {
  return (Object.keys(filters) as (keyof ValidationFiltersState)[])
    .filter((k) => k !== "search" && filters[k] !== "")
    .map((k) => ({ key: k, label: FILTER_LABELS[k], value: filters[k] }));
}

export function EmptyResultsWithFilters({
  filters,
  onClearFiltersKeepSearch,
  onClearAll,
}: EmptyResultsWithFiltersProps) {
  const hasSearch = filters.search !== "";
  const otherFilters = getActiveOtherFilters(filters);
  const hasOtherFilters = otherFilters.length > 0;

  // Caso 1: búsqueda + otros filtros — sugerencia útil
  if (hasSearch && hasOtherFilters) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 py-8 text-center">
        <Search className="w-8 h-8 text-gray-300 mb-3" />
        <p className="text-sm text-gray-700 font-medium mb-1">
          Sin resultados para &ldquo;{filters.search}&rdquo;
        </p>
        <p className="text-xs text-gray-500 mb-4 max-w-md">
          Probablemente el término o ID no cumple con los filtros activos:{" "}
          {otherFilters.map((f, i) => (
            <span key={f.key}>
              <span className="font-medium text-gray-700">{f.label}</span>={" "}
              <span className="text-gray-600">{f.value}</span>
              {i < otherFilters.length - 1 ? ", " : ""}
            </span>
          ))}
        </p>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="default"
            onClick={onClearFiltersKeepSearch}
            className="h-8 text-xs"
          >
            <X className="w-3.5 h-3.5 mr-1" />
            Limpiar filtros (mantener búsqueda)
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={onClearAll}
            className="h-8 text-xs text-gray-500"
          >
            Limpiar todo
          </Button>
        </div>
      </div>
    );
  }

  // Caso 2: solo búsqueda
  if (hasSearch) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 py-8 text-center text-gray-500">
        <Search className="w-8 h-8 text-gray-300 mb-2" />
        <p className="text-sm">Sin resultados para &ldquo;{filters.search}&rdquo;</p>
      </div>
    );
  }

  // Caso 3: genérico (filtros sin búsqueda, o nada)
  return (
    <div className="flex items-center justify-center flex-1 text-gray-500 text-sm">
      No se encontraron ofertas con los filtros seleccionados
    </div>
  );
}
