"use client";

import { useEffect, useState } from "react";
import { Check, ChevronsUpDown, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { getRunsDisponibles } from "@/lib/supabase";
import type { RunOption } from "@/lib/types";

interface RunFilterProps {
  value: string;
  onChange: (runId: string) => void;
}

export function RunFilter({ value, onChange }: RunFilterProps) {
  const [open, setOpen] = useState(false);
  const [runs, setRuns] = useState<RunOption[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getRunsDisponibles()
      .then(setRuns)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const selected = runs.find((r) => r.run_id === value);
  const label = selected
    ? selected.fecha_legible ?? selected.run_id
    : "Run / Corrida";

  return (
    <div className="flex items-center">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            role="combobox"
            aria-expanded={open}
            className={cn(
              "h-7 px-2 text-xs justify-between gap-1 font-normal",
              value ? "w-[180px]" : "w-[150px]",
              !value && "text-muted-foreground",
            )}
          >
            <span className="truncate">{label}</span>
            <ChevronsUpDown className="w-3 h-3 opacity-50 shrink-0" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[320px] p-0" align="start">
          <Command
            filter={(itemValue, search) => {
              if (!search) return 1;
              return itemValue.toLowerCase().includes(search.toLowerCase())
                ? 1
                : 0;
            }}
          >
            <CommandInput
              placeholder={loading ? "Cargando runs..." : "Buscar run o fecha..."}
              className="h-8 text-xs"
            />
            <CommandList>
              <CommandEmpty>
                {loading ? "Cargando..." : "Sin runs."}
              </CommandEmpty>
              <CommandGroup>
                <CommandItem
                  value="__all__ todas las corridas"
                  onSelect={() => {
                    onChange("");
                    setOpen(false);
                  }}
                  className="text-xs"
                >
                  <Check
                    className={cn(
                      "mr-2 h-3 w-3",
                      !value ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <span className="text-muted-foreground">Todas las corridas</span>
                </CommandItem>
                {runs.map((r) => (
                  <CommandItem
                    key={r.run_id}
                    value={`${r.run_id} ${r.fecha_legible ?? ""}`}
                    onSelect={() => {
                      onChange(r.run_id);
                      setOpen(false);
                    }}
                    className="text-xs items-start py-1.5"
                  >
                    <Check
                      className={cn(
                        "mr-2 h-3 w-3 mt-0.5 shrink-0",
                        value === r.run_id ? "opacity-100" : "opacity-0",
                      )}
                    />
                    <div className="flex flex-col min-w-0 flex-1">
                      <span className="font-mono truncate">{r.run_id}</span>
                      <span className="text-[10px] text-muted-foreground">
                        {r.fecha_legible ? `${r.fecha_legible} · ` : ""}
                        {r.n.toLocaleString()} ofertas
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      {value && (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onChange("")}
          className="h-7 w-7 p-0 -ml-1"
          title="Limpiar filtro de run"
        >
          <X className="w-3 h-3" />
        </Button>
      )}
    </div>
  );
}
