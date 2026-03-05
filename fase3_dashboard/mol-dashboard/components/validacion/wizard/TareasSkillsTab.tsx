"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, X, Search, Loader2 } from "lucide-react";
import { OfertaValidacion, OfertaSkillValidacion } from "@/lib/types";
import type { TareaEditada, SkillAsociada } from "@/lib/wizard-types";
import { useSkillsSearch } from "@/hooks/useSkillsSearch";
import { getSkillsByOferta } from "@/lib/supabase";

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

/** Convert Supabase skill to SkillAsociada */
function toSkillAsociada(s: OfertaSkillValidacion): SkillAsociada {
  return {
    id: s.id,
    label: s.preferred_label,
    type: s.es_esencial ? "skill" : "knowledge",
  };
}

export function TareasSkillsTab({
  oferta,
  onTareasChange,
  onSkillsChange,
}: TareasSkillsTabProps) {
  const { search, isLoading: skillsLoading } = useSkillsSearch();

  // Skills from Supabase (existing LLM classifications)
  const [existingSkills, setExistingSkills] = useState<OfertaSkillValidacion[]>([]);
  const [loadingExisting, setLoadingExisting] = useState(true);
  // Track deleted existing skill IDs
  const [deletedExistingIds, setDeletedExistingIds] = useState<Set<string>>(new Set());

  // Load existing skills on mount
  useEffect(() => {
    setLoadingExisting(true);
    getSkillsByOferta(oferta.id_oferta)
      .then(setExistingSkills)
      .catch(console.error)
      .finally(() => setLoadingExisting(false));
  }, [oferta.id_oferta]);

  // Initialize tareas from oferta
  const initialTareas = useMemo(() => {
    const parsed = parseTareas(oferta.tareas_explicitas);
    return parsed.map((texto) => ({ texto, skills: [] as SkillAsociada[] }));
  }, [oferta.tareas_explicitas]);

  const [tareas, setTareas] = useState<TareaEditada[]>(initialTareas);
  // Skills added by the user (not from LLM)
  const [addedSkills, setAddedSkills] = useState<SkillAsociada[]>([]);

  // Skill search state
  const [searchTarget, setSearchTarget] = useState<number | "standalone" | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (searchTarget !== null) {
      searchInputRef.current?.focus();
    }
  }, [searchTarget]);

  // All skill IDs currently visible (for exclusion in search)
  const addedSkillIds = useMemo(() => {
    const ids = new Set<string>();
    for (const t of tareas) {
      for (const s of t.skills) ids.add(s.id);
    }
    for (const s of addedSkills) ids.add(s.id);
    // Include existing skills that haven't been deleted
    for (const s of existingSkills) {
      if (!deletedExistingIds.has(s.id)) ids.add(s.id);
    }
    return ids;
  }, [tareas, addedSkills, existingSkills, deletedExistingIds]);

  const searchResults = useMemo(() => {
    if (searchTarget === null || !searchQuery.trim()) return [];
    return search(searchQuery, addedSkillIds);
  }, [search, searchQuery, addedSkillIds, searchTarget]);

  // Visible existing skills (not deleted)
  const visibleExistingSkills = useMemo(
    () => existingSkills.filter((s) => !deletedExistingIds.has(s.id)),
    [existingSkills, deletedExistingIds]
  );

  // Notify parent of changes
  const emitChanges = useCallback(
    (
      newTareas: TareaEditada[],
      newAdded: SkillAsociada[],
      newDeleted: Set<string>
    ) => {
      const originalParsed = parseTareas(oferta.tareas_explicitas);
      const tareasChanged =
        newTareas.length !== originalParsed.length ||
        newTareas.some(
          (t, i) => t.texto !== originalParsed[i] || t.skills.length > 0
        );
      onTareasChange(tareasChanged ? newTareas : undefined);

      // Build skills output: added skills + info about deleted existing
      const hasSkillChanges = newAdded.length > 0 || newDeleted.size > 0;
      if (hasSkillChanges) {
        // Encode both added and deleted in the output
        const output: SkillAsociada[] = [
          ...newAdded,
          // Mark deleted as special entries so the backend knows
          ...Array.from(newDeleted).map((id) => ({
            id,
            label: `__deleted__`,
            type: "skill" as const,
          })),
        ];
        onSkillsChange(output);
      } else {
        onSkillsChange(undefined);
      }
    },
    [oferta.tareas_explicitas, onTareasChange, onSkillsChange]
  );

  // Tarea CRUD
  const updateTareaTexto = (idx: number, texto: string) => {
    const next = [...tareas];
    next[idx] = { ...next[idx], texto };
    setTareas(next);
    emitChanges(next, addedSkills, deletedExistingIds);
  };

  const removeTarea = (idx: number) => {
    const next = tareas.filter((_, i) => i !== idx);
    setTareas(next);
    emitChanges(next, addedSkills, deletedExistingIds);
  };

  const addTarea = () => {
    const next = [...tareas, { texto: "", skills: [] }];
    setTareas(next);
    emitChanges(next, addedSkills, deletedExistingIds);
  };

  // Skill CRUD for tareas
  const addSkillToTarea = (
    tareaIdx: number,
    skill: SkillAsociada
  ) => {
    const next = [...tareas];
    next[tareaIdx] = {
      ...next[tareaIdx],
      skills: [...next[tareaIdx].skills, skill],
    };
    setTareas(next);
    setSearchTarget(null);
    setSearchQuery("");
    emitChanges(next, addedSkills, deletedExistingIds);
  };

  const removeSkillFromTarea = (tareaIdx: number, skillId: string) => {
    const next = [...tareas];
    next[tareaIdx] = {
      ...next[tareaIdx],
      skills: next[tareaIdx].skills.filter((s) => s.id !== skillId),
    };
    setTareas(next);
    emitChanges(next, addedSkills, deletedExistingIds);
  };

  // Added skills CRUD (user-added, not from LLM)
  const addStandaloneSkill = (skill: SkillAsociada) => {
    const next = [...addedSkills, skill];
    setAddedSkills(next);
    setSearchTarget(null);
    setSearchQuery("");
    emitChanges(tareas, next, deletedExistingIds);
  };

  const removeAddedSkill = (skillId: string) => {
    const next = addedSkills.filter((s) => s.id !== skillId);
    setAddedSkills(next);
    emitChanges(tareas, next, deletedExistingIds);
  };

  // Delete an existing LLM skill
  const deleteExistingSkill = (skillId: string) => {
    const next = new Set(deletedExistingIds);
    next.add(skillId);
    setDeletedExistingIds(next);
    emitChanges(tareas, addedSkills, next);
  };

  // Restore a deleted existing skill
  const restoreExistingSkill = (skillId: string) => {
    const next = new Set(deletedExistingIds);
    next.delete(skillId);
    setDeletedExistingIds(next);
    emitChanges(tareas, addedSkills, next);
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
      {/* Existing skills from LLM */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Skills clasificadas por el LLM ({visibleExistingSkills.length})
          </p>
          {loadingExisting && (
            <Loader2 className="w-3 h-3 animate-spin text-gray-400" />
          )}
        </div>
        {!loadingExisting && visibleExistingSkills.length === 0 && deletedExistingIds.size === 0 && (
          <p className="text-xs text-gray-400">Sin skills clasificadas</p>
        )}
        <div className="flex flex-wrap gap-1.5 items-center">
          {visibleExistingSkills.map((skill) => (
            <Badge
              key={skill.id}
              variant="outline"
              className="text-xs gap-1 pr-1"
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  skill.es_esencial ? "bg-green-500" : "bg-gray-400"
                }`}
              />
              {skill.preferred_label}
              {skill.origen && (
                <span className="text-[9px] text-gray-400 ml-0.5">
                  {skill.origen}
                </span>
              )}
              {skill.score != null && (
                <span className="text-[9px] text-gray-400 tabular-nums">
                  {skill.score.toFixed(2)}
                </span>
              )}
              <button
                onClick={() => deleteExistingSkill(skill.id)}
                className="ml-0.5 hover:text-red-500 text-gray-400"
                title="Eliminar skill"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>

        {/* Show deleted skills with restore option */}
        {deletedExistingIds.size > 0 && (
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="text-[10px] text-red-400">Eliminadas:</span>
            {existingSkills
              .filter((s) => deletedExistingIds.has(s.id))
              .map((skill) => (
                <Badge
                  key={skill.id}
                  variant="outline"
                  className="text-xs gap-1 pr-1 opacity-50 line-through border-red-200"
                >
                  {skill.preferred_label}
                  <button
                    onClick={() => restoreExistingSkill(skill.id)}
                    className="ml-0.5 text-blue-500 hover:text-blue-700 no-underline"
                    title="Restaurar"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
          </div>
        )}
      </div>

      {/* Tareas list */}
      <div className="space-y-3 border-t pt-4">
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

      {/* User-added skills (not from LLM) */}
      <div className="space-y-2 border-t pt-4">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          Agregar skills
        </p>
        <div className="flex flex-wrap gap-1.5 items-center">
          {addedSkills.map((skill) => (
            <Badge
              key={skill.id}
              variant="secondary"
              className="text-xs gap-1 pr-1 bg-blue-50"
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  skill.type === "skill" ? "bg-blue-500" : "bg-purple-500"
                }`}
              />
              {skill.label}
              <button
                onClick={() => removeAddedSkill(skill.id)}
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
