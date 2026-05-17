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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Search, RotateCcw, Download } from "lucide-react";
import { getValidacionFilterOptions, ValidacionFilterOptions } from "@/lib/supabase";
import { ValidationFiltersState, ValidationStats, METODO_LABELS, OfertaValidacion } from "@/lib/types";
import { RunFilter } from "./RunFilter";

interface ValidationFiltersProps {
  filters: ValidationFiltersState;
  onChange: (filters: ValidationFiltersState) => void;
  stats: ValidationStats | null;
  ofertas?: OfertaValidacion[];
}

const EMPTY_FILTERS: ValidationFiltersState = {
  iscoGroup: "",
  portal: "",
  provincia: "",
  metodo: "",
  search: "",
  seniority: "",
  modalidad: "",
  sector: "",
  nivelEducativo: "",
  scoreRange: "",
  estadoValidacion: "",
  runId: "",
};

const SCORE_RANGES = [
  { value: "<0.3", label: "< 0.30" },
  { value: "0.3-0.5", label: "0.30 - 0.50" },
  { value: "0.5-0.7", label: "0.50 - 0.70" },
  { value: ">0.7", label: "> 0.70" },
];

const ESTADO_OPTIONS = [
  { value: "pendiente", label: "Pendientes" },
  { value: "ok", label: "OK" },
  { value: "error", label: "Error" },
  { value: "revisar", label: "Revisar" },
  { value: "basura", label: "Basura" },
];

function FilterSelect({
  value,
  onValueChange,
  placeholder,
  options,
  allLabel,
  className = "w-[140px]",
}: {
  value: string;
  onValueChange: (v: string) => void;
  placeholder: string;
  options: { value: string; label: string }[];
  allLabel: string;
  className?: string;
}) {
  return (
    <Select value={value || "__all__"} onValueChange={(v) => onValueChange(v === "__all__" ? "" : v)}>
      <SelectTrigger className={`h-7 text-xs ${className}`}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="__all__">{allLabel}</SelectItem>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function downloadBlob(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function exportCSV(ofertas: OfertaValidacion[]) {
  const headers = [
    "id_oferta", "titulo", "titulo_limpio", "empresa", "portal",
    "isco_code", "isco_label", "esco_occupation_label", "occupation_match_score",
    "decision_metodo", "area_funcional", "nivel_seniority", "modalidad",
    "provincia", "localidad", "validacion_humana",
  ];
  const escape = (v: unknown) => {
    const s = v == null ? "" : String(v);
    return s.includes(",") || s.includes('"') || s.includes("\n")
      ? `"${s.replace(/"/g, '""')}"`
      : s;
  };
  const rows = ofertas.map((o) =>
    headers.map((h) => escape((o as unknown as Record<string, unknown>)[h])).join(",")
  );
  downloadBlob([headers.join(","), ...rows].join("\n"), "validacion_export.csv", "text/csv");
}

function exportJSON(ofertas: OfertaValidacion[]) {
  downloadBlob(JSON.stringify(ofertas, null, 2), "validacion_export.json", "application/json");
}

export function ValidationFilters({ filters, onChange, stats, ofertas }: ValidationFiltersProps) {
  const [options, setOptions] = useState<ValidacionFilterOptions>({
    portales: [], provincias: [], metodos: [], iscoGroups: [],
    seniorities: [], modalidades: [], sectores: [], nivelesEducativos: [],
  });
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

  // Build metodo options with readable labels
  const metodoOptions = options.metodos.map((m) => ({
    value: m,
    label: METODO_LABELS[m]?.label || m,
  }));

  return (
    <div className="space-y-2">
      {/* Row 1: Domain filters */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <FilterSelect
          value={filters.iscoGroup}
          onValueChange={(v) => handleChange("iscoGroup", v)}
          placeholder="ISCO"
          allLabel="Todos ISCO"
          className="w-[200px]"
          options={options.iscoGroups.map((g) => ({ value: g.code, label: g.label }))}
        />
        <FilterSelect
          value={filters.seniority}
          onValueChange={(v) => handleChange("seniority", v)}
          placeholder="Seniority"
          allLabel="Todo seniority"
          options={options.seniorities.map((s) => ({ value: s, label: s }))}
        />
        <FilterSelect
          value={filters.sector}
          onValueChange={(v) => handleChange("sector", v)}
          placeholder="Sector"
          allLabel="Todos sectores"
          className="w-[160px]"
          options={options.sectores.map((s) => ({ value: s, label: s }))}
        />
        <FilterSelect
          value={filters.modalidad}
          onValueChange={(v) => handleChange("modalidad", v)}
          placeholder="Modalidad"
          allLabel="Toda modalidad"
          options={options.modalidades.map((m) => ({ value: m, label: m }))}
        />
        <FilterSelect
          value={filters.provincia}
          onValueChange={(v) => handleChange("provincia", v)}
          placeholder="Provincia"
          allLabel="Todas provincias"
          className="w-[160px]"
          options={options.provincias.map((p) => ({ value: p, label: p }))}
        />
        <FilterSelect
          value={filters.portal}
          onValueChange={(v) => handleChange("portal", v)}
          placeholder="Portal"
          allLabel="Todos portales"
          className="w-[120px]"
          options={options.portales.map((p) => ({ value: p, label: p }))}
        />
      </div>

      {/* Row 2: Validation filters + search + progress */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <FilterSelect
          value={filters.scoreRange}
          onValueChange={(v) => handleChange("scoreRange", v)}
          placeholder="Score"
          allLabel="Todo score"
          className="w-[120px]"
          options={SCORE_RANGES}
        />
        <FilterSelect
          value={filters.estadoValidacion}
          onValueChange={(v) => handleChange("estadoValidacion", v)}
          placeholder="Estado"
          allLabel="Todos estados"
          className="w-[130px]"
          options={ESTADO_OPTIONS}
        />
        <FilterSelect
          value={filters.metodo}
          onValueChange={(v) => handleChange("metodo", v)}
          placeholder="Metodo"
          allLabel="Todos metodos"
          className="w-[160px]"
          options={metodoOptions}
        />
        <FilterSelect
          value={filters.nivelEducativo}
          onValueChange={(v) => handleChange("nivelEducativo", v)}
          placeholder="Educacion"
          allLabel="Todo nivel"
          options={options.nivelesEducativos.map((n) => ({ value: n, label: n }))}
        />

        <RunFilter
          value={filters.runId}
          onChange={(v) => handleChange("runId", v)}
        />

        {/* Search */}
        <div className="flex items-center gap-1">
          <Input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearchSubmit()}
            placeholder="Titulo, ID o lista IDs..."
            className="w-[200px] h-7 text-xs"
            title="Un término = búsqueda parcial en título e ID. Múltiples IDs separados por coma, espacio o salto de línea = filtro exacto por lista."
          />
          <Button size="sm" variant="ghost" onClick={handleSearchSubmit} className="h-7 w-7 p-0">
            <Search className="w-3.5 h-3.5" />
          </Button>
        </div>

        {hasFilters && (
          <Button
            size="sm"
            variant="ghost"
            onClick={handleReset}
            className="h-7 text-xs text-gray-500 hover:text-gray-700"
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Limpiar
          </Button>
        )}

        {ofertas && ofertas.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" variant="ghost" className="h-7 text-xs text-gray-500 hover:text-gray-700">
                <Download className="w-3 h-3 mr-1" />
                Exportar
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem onClick={() => exportCSV(ofertas)}>
                CSV ({ofertas.length} ofertas)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportJSON(ofertas)}>
                JSON ({ofertas.length} ofertas)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Progress bar */}
        {stats && stats.total > 0 && (
          <div className="flex items-center gap-2 ml-auto">
            <div className="flex gap-1 text-[10px] tabular-nums">
              <span className="text-green-600">{stats.ok}</span>
              <span className="text-gray-300">/</span>
              <span className="text-gray-600">{stats.total}</span>
            </div>
            <div className="w-[80px] h-2 bg-gray-200 rounded-full overflow-hidden flex">
              {stats.ok > 0 && (
                <div className="bg-green-500 h-full" style={{ width: `${(stats.ok / stats.total) * 100}%` }} />
              )}
              {stats.error > 0 && (
                <div className="bg-red-500 h-full" style={{ width: `${(stats.error / stats.total) * 100}%` }} />
              )}
              {stats.revisar > 0 && (
                <div className="bg-amber-500 h-full" style={{ width: `${(stats.revisar / stats.total) * 100}%` }} />
              )}
              {stats.basura > 0 && (
                <div className="bg-gray-400 h-full" style={{ width: `${(stats.basura / stats.total) * 100}%` }} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
