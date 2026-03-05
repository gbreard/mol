"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, X, Search, Loader2 } from "lucide-react";
import { OfertaValidacion } from "@/lib/types";
import type { TareaEditada, SkillAsociada } from "@/lib/wizard-types";
import { useSkillsSearch } from "@/hooks/useSkillsSearch";

interface TareasSkillsTabProps {
  oferta: OfertaValidacion;
  onTareasChange: (tareas: TareaEditada[] | undefined) => void;
  onSkillsChange: (skills: SkillAsociada[] | undefined) => void;
}

function parseTareas(raw: string | null): string[] {
  if (!raw || !raw.trim()) return [];
  // Try semicolon first, then comma
  const bySemicolon = raw.split(";").map((t) => t.trim()).filter(Boolean);
  if (bySemicolon.length > 1) return bySemicolon;
  return raw.split(",").map((t) => t.trim()).filter(Boolean);
}

export function TareasSkillsTab({
  oferta,
  onTareasChange,
  onSkillsChange,
}: TareasSkillsTabProps) {
  const { search, isLoading: skillsLoading } = useSkillsSearch();

  // Initialize tareas from oferta
  const initialTareas = useMemo(() => {
    const parsed = parseTareas(oferta.tareas_explicitas);
    return parsed.map((texto) => ({ texto, skills: [] as SkillAsociada[] }));
  }, [oferta.tareas_explicitas]);

  const [tareas, setTareas] = useState<TareaEditada[]>(initialTareas);
  const [standaloneSkills, setStandaloneSkills] = useState<SkillAsociada[]>([]);

  // Skill search state — tracks which tarea (or "standalone") has search open
  const [searchTarget, setSearchTarget] = useState<number | "standalone" | null>(
    null
  );
  const [searchQuery, setSearchQuery] = useState("");
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Focus search input when target changes
  useEffect(() => {
    if (searchTarget !== null) {
      searchInputRef.current?.focus();
    }
  }, [searchTarget]);

  // Get all skill IDs currently added (for exclusion)
  const addedSkillIds = useMemo(() => {
    const ids = new Set<string>();
    for (const t of tareas) {
      for (const s of t.skills) ids.add(s.id);
    }
    for (const s of standaloneSkills) ids.add(s.id);
    return ids;
  }, [tareas, standaloneSkills]);

  const searchResults = useMemo(() => {
    if (searchTarget === null || !searchQuery.trim()) return [];
    return search(searchQuery, addedSkillIds);
  }, [search, searchQuery, addedSkillIds, searchTarget]);

  // Notify parent of changes
  const emitChanges = useCallback(
    (newTareas: TareaEditada[], newStandalone: SkillAsociada[]) => {
      // Check if tareas differ from original
      const originalParsed = parseTareas(oferta.tareas_explicitas);
      const tareasChanged =
        newTareas.length !== originalParsed.length ||
        newTareas.some(
          (t, i) => t.texto !== originalParsed[i] || t.skills.length > 0
        );
      onTareasChange(tareasChanged ? newTareas : undefined);
      onSkillsChange(newStandalone.length > 0 ? newStandalone : undefined);
    },
    [oferta.tareas_explicitas, onTareasChange, onSkillsChange]
  );

  // Tarea CRUD
  const updateTareaTexto = (idx: number, texto: string) => {
    const next = [...tareas];
    next[idx] = { ...next[idx], texto };
    setTareas(next);
    emitChanges(next, standaloneSkills);
  };

  const removeTarea = (idx: number) => {
    const next = tareas.filter((_, i) => i !== idx);
    setTareas(next);
    emitChanges(next, standaloneSkills);
  };

  const addTarea = () => {
    const next = [...tareas, { texto: "", skills: [] }];
    setTareas(next);
    emitChanges(next, standaloneSkills);
  };

  // Skill CRUD for tareas
  const addSkillToTarea = (
    tareaIdx: number,
    skill: { id: string; label: string; type: "skill" | "knowledge" }
  ) => {
    const next = [...tareas];
    next[tareaIdx] = {
      ...next[tareaIdx],
      skills: [...next[tareaIdx].skills, skill],
    };
    setTareas(next);
    setSearchTarget(null);
    setSearchQuery("");
    emitChanges(next, standaloneSkills);
  };

  const removeSkillFromTarea = (tareaIdx: number, skillId: string) => {
    const next = [...tareas];
    next[tareaIdx] = {
      ...next[tareaIdx],
      skills: next[tareaIdx].skills.filter((s) => s.id !== skillId),
    };
    setTareas(next);
    emitChanges(next, standaloneSkills);
  };

  // Standalone skills CRUD
  const addStandaloneSkill = (skill: {
    id: string;
    label: string;
    type: "skill" | "knowledge";
  }) => {
    const next = [...standaloneSkills, skill];
    setStandaloneSkills(next);
    setSearchTarget(null);
    setSearchQuery("");
    emitChanges(tareas, next);
  };

  const removeStandaloneSkill = (skillId: string) => {
    const next = standaloneSkills.filter((s) => s.id !== skillId);
    setStandaloneSkills(next);
    emitChanges(tareas, next);
  };

  const openSearch = (target: number | "standalone") => {
    setSearchTarget(target);
    setSearchQuery("");
  };

  const closeSearch = () => {
    setSearchTarget(null);
    setSearchQuery("");
  };

  return (
    <div className="space-y-4">
      {/* Tareas list */}
      <div className="space-y-3">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          Tareas ({tareas.length})
        </p>
        {tareas.map((tarea, idx) => (
          <div key={idx} className="border rounded-md p-3 space-y-2">
            <div className="flex items-center gap-2">
              <Input
                value={tarea.texto}
                onChange={(e) => updateTareaTexto(idx, e.target.value)}
                className="text-sm h-8 flex-1"
                placeholder="Descripcion de la tarea..."
              />
              <button
                onClick={() => removeTarea(idx)}
                className="p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Skills for this tarea */}
            <div className="flex flex-wrap gap-1.5 items-center">
              {tarea.skills.map((skill) => (
                <Badge
                  key={skill.id}
                  variant="secondary"
                  className="text-xs gap-1 pr-1"
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      skill.type === "skill" ? "bg-blue-500" : "bg-purple-500"
                    }`}
                  />
                  {skill.label}
                  <button
                    onClick={() => removeSkillFromTarea(idx, skill.id)}
                    className="ml-0.5 hover:text-red-500"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
              <button
                onClick={() => openSearch(idx)}
                className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-0.5"
              >
                <Plus className="w-3 h-3" />
                skill
              </button>
            </div>

            {/* Inline skill search for this tarea */}
            {searchTarget === idx && (
              <SkillSearchDropdown
                ref={searchInputRef}
                query={searchQuery}
                onQueryChange={setSearchQuery}
                results={searchResults}
                loading={skillsLoading}
                onSelect={(s) => addSkillToTarea(idx, s)}
                onClose={closeSearch}
              />
            )}
          </div>
        ))}

        <Button
          variant="outline"
          size="sm"
          onClick={addTarea}
          className="text-xs h-7"
        >
          <Plus className="w-3 h-3 mr-1" />
          Agregar tarea
        </Button>
      </div>

      {/* Standalone skills (not tied to a task) */}
      <div className="space-y-2 border-t pt-4">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          Skills sin tarea asociada
        </p>
        <div className="flex flex-wrap gap-1.5 items-center">
          {standaloneSkills.map((skill) => (
            <Badge
              key={skill.id}
              variant="secondary"
              className="text-xs gap-1 pr-1"
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  skill.type === "skill" ? "bg-blue-500" : "bg-purple-500"
                }`}
              />
              {skill.label}
              <button
                onClick={() => removeStandaloneSkill(skill.id)}
                className="ml-0.5 hover:text-red-500"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
          <button
            onClick={() => openSearch("standalone")}
            className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-0.5"
          >
            <Plus className="w-3 h-3" />
            skill
          </button>
        </div>

        {searchTarget === "standalone" && (
          <SkillSearchDropdown
            ref={searchInputRef}
            query={searchQuery}
            onQueryChange={setSearchQuery}
            results={searchResults}
            loading={skillsLoading}
            onSelect={addStandaloneSkill}
            onClose={closeSearch}
          />
        )}
      </div>
    </div>
  );
}

// ---- Inline dropdown for skill search ----

import { forwardRef } from "react";
import type { SearchableSkill } from "@/lib/types";

interface SkillSearchDropdownProps {
  query: string;
  onQueryChange: (q: string) => void;
  results: SearchableSkill[];
  loading: boolean;
  onSelect: (skill: SkillAsociada) => void;
  onClose: () => void;
}

const SkillSearchDropdown = forwardRef<
  HTMLInputElement,
  SkillSearchDropdownProps
>(function SkillSearchDropdown(
  { query, onQueryChange, results, loading, onSelect, onClose },
  ref
) {
  return (
    <div className="border rounded-md bg-white shadow-sm">
      <div className="flex items-center gap-2 p-2 border-b">
        <Search className="w-3.5 h-3.5 text-gray-400" />
        <input
          ref={ref}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") onClose();
          }}
          placeholder={loading ? "Cargando skills..." : "Buscar skill ESCO..."}
          disabled={loading}
          className="flex-1 text-sm outline-none bg-transparent"
        />
        {loading && <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-400" />}
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      {query.trim() && (
        <div className="max-h-[200px] overflow-y-auto divide-y">
          {results.length === 0 ? (
            <p className="text-xs text-gray-400 p-2">Sin resultados</p>
          ) : (
            results.map((skill) => (
              <button
                key={skill.id}
                onClick={() =>
                  onSelect({
                    id: skill.id,
                    label: skill.label,
                    type: skill.type,
                  })
                }
                className="w-full text-left px-3 py-1.5 hover:bg-gray-50 flex items-center gap-2"
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    skill.type === "skill" ? "bg-blue-500" : "bg-purple-500"
                  }`}
                />
                <span className="text-sm text-gray-700 flex-1 truncate">
                  {skill.label}
                </span>
                <span className="text-[10px] text-gray-400 uppercase shrink-0">
                  {skill.type === "skill" ? "S" : "K"}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
});
