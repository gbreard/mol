"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, RotateCcw } from "lucide-react";
import { getValidacionFilterOptions } from "@/lib/supabase";
import { ValidationFiltersState } from "@/lib/types";

interface ValidationFiltersProps {
  filters: ValidationFiltersState;
  onChange: (filters: ValidationFiltersState) => void;
}

const EMPTY_FILTERS: ValidationFiltersState = {
  iscoGroup: "",
  portal: "",
  provincia: "",
  metodo: "",
  search: "",
};

export function ValidationFilters({
  filters,
  onChange,
}: ValidationFiltersProps) {
  const [options, setOptions] = useState<{
    portales: string[];
    provincias: string[];
    metodos: string[];
    iscoGroups: { code: string; label: string }[];
  }>({ portales: [], provincias: [], metodos: [], iscoGroups: [] });

  const [searchInput, setSearchInput] = useState(filters.search);

  useEffect(() => {
    getValidacionFilterOptions().then(setOptions).catch(console.error);
  }, []);

  const handleChange = (key: keyof ValidationFiltersState, value: string) => {
    onChange({ ...filters, [key]: value });
  };

  const handleSearchSubmit = () => {
    onChange({ ...filters, search: searchInput });
  };

  const handleReset = () => {
    setSearchInput("");
    onChange(EMPTY_FILTERS);
  };

  const hasFilters = Object.values(filters).some((v) => v !== "");

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Select
        value={filters.iscoGroup || "__all__"}
        onValueChange={(v) => handleChange("iscoGroup", v === "__all__" ? "" : v)}
      >
        <SelectTrigger className="w-[200px] h-8 text-xs">
          <SelectValue placeholder="Grupo ISCO" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">Todos los ISCO</SelectItem>
          {options.iscoGroups.map((g) => (
            <SelectItem key={g.code} value={g.code}>
              {g.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.portal || "__all__"}
        onValueChange={(v) => handleChange("portal", v === "__all__" ? "" : v)}
      >
        <SelectTrigger className="w-[140px] h-8 text-xs">
          <SelectValue placeholder="Portal" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">Todos los portales</SelectItem>
          {options.portales.map((p) => (
            <SelectItem key={p} value={p}>
              {p}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.provincia || "__all__"}
        onValueChange={(v) => handleChange("provincia", v === "__all__" ? "" : v)}
      >
        <SelectTrigger className="w-[160px] h-8 text-xs">
          <SelectValue placeholder="Provincia" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">Todas las provincias</SelectItem>
          {options.provincias.map((p) => (
            <SelectItem key={p} value={p}>
              {p}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.metodo || "__all__"}
        onValueChange={(v) => handleChange("metodo", v === "__all__" ? "" : v)}
      >
        <SelectTrigger className="w-[140px] h-8 text-xs">
          <SelectValue placeholder="Metodo" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">Todos los metodos</SelectItem>
          {options.metodos.map((m) => (
            <SelectItem key={m} value={m}>
              {m}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Search box */}
      <div className="flex items-center gap-1">
        <Input
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearchSubmit()}
          placeholder="Buscar titulo o ID..."
          className="w-[180px] h-8 text-xs"
        />
        <Button
          size="sm"
          variant="ghost"
          onClick={handleSearchSubmit}
          className="h-8 w-8 p-0"
        >
          <Search className="w-3.5 h-3.5" />
        </Button>
      </div>

      {hasFilters && (
        <Button
          size="sm"
          variant="ghost"
          onClick={handleReset}
          className="h-8 text-xs text-gray-500 hover:text-gray-700"
        >
          <RotateCcw className="w-3 h-3 mr-1" />
          Limpiar
        </Button>
      )}
    </div>
  );
}
