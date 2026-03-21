"use client";

import { useState, useMemo, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, Check, X } from "lucide-react";
import { OfertaValidacion } from "@/lib/types";
import type { OcupacionCorregida } from "@/lib/wizard-types";

interface OccupationEntry {
  label: string;
  isco: string;
}

type OccupationsIndex = Record<string, OccupationEntry>;

// Module-level cache — survives component unmounts
let cachedOccupations: { uuid: string; label: string; isco: string }[] | null =
  null;
let loadingPromise: Promise<void> | null = null;

function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

interface OcupacionTabProps {
  oferta: OfertaValidacion;
  value: OcupacionCorregida | undefined;
  onChange: (correccion: OcupacionCorregida | undefined) => void;
}

export function OcupacionTab({ oferta, value, onChange }: OcupacionTabProps) {
  const [occupations, setOccupations] = useState(cachedOccupations);
  const [loading, setLoading] = useState(!cachedOccupations);
  const [searchTerm, setSearchTerm] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Load occupations index (cached at module level)
  useEffect(() => {
    if (cachedOccupations) {
      setOccupations(cachedOccupations);
      setLoading(false);
      return;
    }
    if (loadingPromise) {
      loadingPromise.then(() => {
        setOccupations(cachedOccupations);
        setLoading(false);
      });
      return;
    }
    loadingPromise = fetch("/data/occupations_index.json")
      .then((res) => res.json())
      .then((data: OccupationsIndex) => {
        cachedOccupations = Object.entries(data).map(([uuid, entry]) => ({
          uuid,
          label: entry.label,
          isco: entry.isco,
        }));
        setOccupations(cachedOccupations);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error loading occupations:", err);
        setLoading(false);
        loadingPromise = null;
      });
  }, []);

  // Auto-focus search on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Pre-fill from existing corrections
  useEffect(() => {
    if (
      !value &&
      oferta.validacion_correcciones &&
      typeof oferta.validacion_correcciones === "object"
    ) {
      const existing = oferta.validacion_correcciones as Record<string, unknown>;
      // Legacy format: { isco_correcto: "1234" }
      if (existing.isco_correcto && typeof existing.isco_correcto === "string") {
        // Try to find the occupation by ISCO code in the loaded data
        if (occupations) {
          const match = occupations.find(
            (o) => o.isco === `C${existing.isco_correcto}` || o.isco === existing.isco_correcto as string
          );
          if (match) {
            onChange({
              esco_uuid: match.uuid,
              esco_label: match.label,
              isco_code: match.isco,
            });
          }
        }
      }
      // New format: { ocupacion_corregida: {...} }
      if (existing.ocupacion_corregida) {
        onChange(existing.ocupacion_corregida as OcupacionCorregida);
      }
    }
  }, [occupations]); // eslint-disable-line react-hooks/exhaustive-deps

  const results = useMemo(() => {
    if (!occupations || !searchTerm.trim()) return [];
    const normalizedSearch = normalize(searchTerm);
    return occupations
      .filter((occ) => normalize(occ.label).includes(normalizedSearch))
      .slice(0, 15);
  }, [occupations, searchTerm]);

  const handleSelect = (occ: { uuid: string; label: string; isco: string }) => {
    onChange({
      esco_uuid: occ.uuid,
      esco_label: occ.label,
      isco_code: occ.isco,
    });
    setSearchTerm("");
  };

  const handleClear = () => {
    onChange(undefined);
  };

  return (
    <div className="space-y-4">
      {/* Current classification (read-only reference) */}
      <div className="rounded-md border bg-gray-50 p-3 space-y-1.5">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          Clasificacion actual
        </p>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-sm">
            {oferta.isco_code || "—"}
          </Badge>
          <span className="text-sm text-gray-700">
            {oferta.isco_label || "Sin clasificar"}
          </span>
        </div>
        {oferta.esco_occupation_label && (
          <p className="text-xs text-gray-500">
            ESCO: {oferta.esco_occupation_label}
          </p>
        )}
        <div className="flex items-center gap-3 text-xs text-gray-400">
          {oferta.decision_metodo && (
            <span>Metodo: {oferta.decision_metodo}</span>
          )}
          {oferta.occupation_match_score != null && (
            <span>
              Score: {(oferta.occupation_match_score * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      {/* Selected correction */}
      {value && (
        <div className="rounded-md border-2 border-blue-300 bg-blue-50 p-3 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-blue-600 uppercase tracking-wider">
              Correccion seleccionada
            </p>
            <div className="flex items-center gap-2 mt-1">
              <Badge className="font-mono text-sm bg-blue-600">
                {value.isco_code}
              </Badge>
              <span className="text-sm font-medium text-blue-900">
                {value.esco_label}
              </span>
            </div>
          </div>
          <button
            onClick={handleClear}
            className="p-1 rounded hover:bg-blue-100 text-blue-400 hover:text-blue-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          ref={inputRef}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={
            loading
              ? "Cargando ocupaciones..."
              : "Buscar ocupacion ESCO..."
          }
          disabled={loading}
          className="pl-9"
        />
      </div>

      {/* Search results */}
      {searchTerm.trim() && (
        <div className="border rounded-md max-h-[320px] overflow-y-auto divide-y">
          {results.length === 0 ? (
            <p className="text-sm text-gray-400 p-3">
              Sin resultados para &quot;{searchTerm}&quot;
            </p>
          ) : (
            results.map((occ) => {
              const isSelected = value?.esco_uuid === occ.uuid;
              return (
                <button
                  key={occ.uuid}
                  onClick={() => handleSelect(occ)}
                  className={`w-full text-left px-3 py-2 hover:bg-gray-50 flex items-center gap-2 ${
                    isSelected ? "bg-blue-50" : ""
                  }`}
                >
                  <Badge
                    variant="outline"
                    className="font-mono text-[10px] shrink-0"
                  >
                    {occ.isco}
                  </Badge>
                  <span className="text-sm text-gray-700 truncate flex-1">
                    {occ.label}
                  </span>
                  {isSelected && (
                    <Check className="w-4 h-4 text-blue-600 shrink-0" />
                  )}
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
