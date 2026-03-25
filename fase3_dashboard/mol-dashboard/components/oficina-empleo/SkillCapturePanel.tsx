"use client";

import { useState } from "react";
import {
  Search, Briefcase, MessageSquare, GraduationCap,
  Loader2, Plus, X, CheckCircle2, HelpCircle,
} from "lucide-react";

export interface CapturedSkill {
  uri: string;
  label: string;
  type: "skill" | "knowledge" | "transversal";
  description?: string;
  source: string; // "ocupacion" | "busqueda" | "texto_libre" | "formacion"
  confirmed: boolean;
}

interface SkillCapturePanelProps {
  skills: CapturedSkill[];
  onAddSkills: (skills: CapturedSkill[]) => void;
  onRemoveSkill: (uri: string) => void;
  onToggleConfirm: (uri: string) => void;
}

type Via = "ocupacion" | "busqueda" | "texto" | "formacion";

const VIA_CONFIG: { id: Via; label: string; icon: typeof Search; placeholder: string; description: string }[] = [
  { id: "ocupacion", label: "Por ocupacion", icon: Briefcase, placeholder: "albanil, electricista, vendedor...", description: "En que trabajaste? Selecciona una ocupacion y el sistema asigna skills." },
  { id: "busqueda", label: "Por habilidad", icon: Search, placeholder: "soldar, programar, atender clientes...", description: "Que sabes hacer? Busca skills sueltas." },
  { id: "texto", label: "Texto libre", icon: MessageSquare, placeholder: "Trabaje 5 anos en una fabrica haciendo soldadura y mantenimiento...", description: "Conta con tus palabras tu experiencia. El sistema extrae skills automaticamente." },
  { id: "formacion", label: "Por formacion", icon: GraduationCap, placeholder: "Tecnicatura en Redes, Curso de Soldadura...", description: "Que estudiaste? Buscamos skills derivadas de tu formacion." },
];

export function SkillCapturePanel({ skills, onAddSkills, onRemoveSkill, onToggleConfirm }: SkillCapturePanelProps) {
  const [activeVia, setActiveVia] = useState<Via>("ocupacion");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setResults([]);

    try {
      if (activeVia === "ocupacion") {
        const res = await fetch(`/api/occupations/search?q=${encodeURIComponent(query)}&limit=10`);
        if (res.ok) setResults(await res.json());
      } else if (activeVia === "busqueda") {
        const res = await fetch(`/api/skills-search?q=${encodeURIComponent(query)}&limit=20`);
        if (res.ok) {
          const data = await res.json();
          setResults(data.results || data);
        }
      } else if (activeVia === "texto") {
        const res = await fetch("/api/skills-extract-from-text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: query }),
        });
        if (res.ok) {
          const data = await res.json();
          setResults(data.skills || data.results || []);
        }
      } else if (activeVia === "formacion") {
        // Search skills by training/education title
        const res = await fetch(`/api/skills-search?q=${encodeURIComponent(query)}&limit=20`);
        if (res.ok) {
          const data = await res.json();
          setResults(data.results || data);
        }
      }
    } catch {} finally {
      setLoading(false);
    }
  }

  function addOccupationSkills(occupation: any) {
    // Fetch skills for this occupation
    fetch(`/api/occupations/skills?isco_code=${occupation.isco_code || occupation.isco}`)
      .then(r => r.json())
      .then(data => {
        const skills: CapturedSkill[] = (data.skills || data.essential || []).map((s: any) => ({
          uri: s.uri || s.id || s.label,
          label: s.label || s.preferred_label,
          type: s.type || "skill",
          description: s.description || "",
          source: "ocupacion",
          confirmed: true,
        }));
        onAddSkills(skills);
        setResults([]);
        setQuery("");
      })
      .catch(() => {});
  }

  function addSkillFromResult(result: any) {
    const skill: CapturedSkill = {
      uri: result.uri || result.id || result.label,
      label: result.label || result.preferred_label,
      type: result.type || "skill",
      description: result.description || "",
      source: activeVia === "texto" ? "texto_libre" : activeVia === "formacion" ? "formacion" : "busqueda",
      confirmed: true,
    };
    onAddSkills([skill]);
  }

  function addAllExtracted() {
    const newSkills: CapturedSkill[] = results.map((r: any) => ({
      uri: r.uri || r.id || r.label,
      label: r.label || r.preferred_label,
      type: r.type || "skill",
      description: r.description || "",
      source: activeVia === "texto" ? "texto_libre" : "formacion",
      confirmed: false, // User should confirm extracted skills
    }));
    onAddSkills(newSkills);
    setResults([]);
    setQuery("");
  }

  const existingUris = new Set(skills.map(s => s.uri));
  const config = VIA_CONFIG.find(v => v.id === activeVia)!;

  return (
    <div className="space-y-4">
      {/* Via selector */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {VIA_CONFIG.map(via => {
          const Icon = via.icon;
          return (
            <button
              key={via.id}
              onClick={() => { setActiveVia(via.id); setResults([]); setQuery(""); }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors flex-1 justify-center ${
                activeVia === via.id
                  ? "bg-white text-teal-700 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{via.label}</span>
            </button>
          );
        })}
      </div>

      {/* Description */}
      <p className="text-sm text-gray-500">{config.description}</p>

      {/* Search input */}
      <div className="flex gap-2">
        {activeVia === "texto" ? (
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={config.placeholder}
            className="flex-1 border rounded-lg px-3 py-2 text-sm min-h-[80px] resize-y"
          />
        ) : (
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            placeholder={config.placeholder}
            className="flex-1 border rounded-lg px-3 py-2 text-sm"
          />
        )}
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-teal-700 disabled:opacity-50 flex items-center gap-1"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          Buscar
        </button>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="border rounded-lg divide-y max-h-64 overflow-y-auto">
          {activeVia === "ocupacion" ? (
            // Occupation results — click to add all skills of that occupation
            results.map((occ: any, i: number) => (
              <button
                key={i}
                onClick={() => addOccupationSkills(occ)}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-teal-50 text-left transition-colors"
              >
                <Briefcase className="w-4 h-4 text-teal-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900">{occ.label}</div>
                  <div className="text-xs text-gray-400">ISCO {occ.isco_code || occ.isco}</div>
                </div>
                <Plus className="w-4 h-4 text-teal-500" />
              </button>
            ))
          ) : activeVia === "texto" ? (
            // Text extraction results — add all button
            <>
              <div className="px-4 py-2 bg-gray-50 flex items-center justify-between">
                <span className="text-xs text-gray-500">{results.length} skills identificadas</span>
                <button onClick={addAllExtracted} className="text-xs text-teal-600 hover:text-teal-700 font-medium">
                  Agregar todas
                </button>
              </div>
              {results.map((skill: any, i: number) => {
                const alreadyAdded = existingUris.has(skill.uri || skill.label);
                return (
                  <div key={i} className={`flex items-center gap-3 px-4 py-2 ${alreadyAdded ? "opacity-40" : ""}`}>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-gray-900">{skill.label || skill.preferred_label}</div>
                      {skill.description && <div className="text-xs text-gray-400 truncate">{skill.description}</div>}
                    </div>
                    {!alreadyAdded && (
                      <button onClick={() => addSkillFromResult(skill)} className="text-teal-500 hover:text-teal-600">
                        <Plus className="w-4 h-4" />
                      </button>
                    )}
                    {alreadyAdded && <CheckCircle2 className="w-4 h-4 text-green-400" />}
                  </div>
                );
              })}
            </>
          ) : (
            // Skill search results — click to add individual
            results.map((skill: any, i: number) => {
              const alreadyAdded = existingUris.has(skill.uri || skill.label);
              return (
                <button
                  key={i}
                  onClick={() => !alreadyAdded && addSkillFromResult(skill)}
                  disabled={alreadyAdded}
                  className={`w-full flex items-center gap-3 px-4 py-2 text-left transition-colors ${
                    alreadyAdded ? "opacity-40" : "hover:bg-teal-50"
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-900">{skill.label || skill.preferred_label}</div>
                    {skill.description && <div className="text-xs text-gray-400 line-clamp-1">{skill.description}</div>}
                  </div>
                  <span className="text-xs text-gray-400 px-1.5 py-0.5 bg-gray-100 rounded">{skill.type || "skill"}</span>
                  {alreadyAdded ? <CheckCircle2 className="w-4 h-4 text-green-400" /> : <Plus className="w-4 h-4 text-teal-500" />}
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

// Panel showing all captured skills with confirm/remove
export function SkillsPanel({ skills, onRemoveSkill, onToggleConfirm }: {
  skills: CapturedSkill[];
  onRemoveSkill: (uri: string) => void;
  onToggleConfirm: (uri: string) => void;
}) {
  if (skills.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <Search className="w-8 h-8 mx-auto mb-2 opacity-30" />
        <p className="text-sm">Usa las vias de captura para agregar competencias</p>
      </div>
    );
  }

  const sourceLabel: Record<string, string> = {
    ocupacion: "via ocupacion",
    busqueda: "via busqueda",
    texto_libre: "via texto libre",
    formacion: "via formacion",
  };

  const confirmed = skills.filter(s => s.confirmed);
  const unconfirmed = skills.filter(s => !s.confirmed);

  return (
    <div className="space-y-1">
      <div className="text-sm font-medium text-gray-700 mb-2">
        Competencias identificadas ({skills.length})
        {unconfirmed.length > 0 && (
          <span className="text-xs text-amber-600 ml-2">
            {unconfirmed.length} por confirmar
          </span>
        )}
      </div>

      {/* Unconfirmed first */}
      {unconfirmed.map(skill => (
        <SkillRow key={skill.uri} skill={skill} sourceLabel={sourceLabel} onRemove={onRemoveSkill} onToggle={onToggleConfirm} />
      ))}

      {/* Confirmed */}
      {confirmed.map(skill => (
        <SkillRow key={skill.uri} skill={skill} sourceLabel={sourceLabel} onRemove={onRemoveSkill} onToggle={onToggleConfirm} />
      ))}
    </div>
  );
}

function SkillRow({ skill, sourceLabel, onRemove, onToggle }: {
  skill: CapturedSkill;
  sourceLabel: Record<string, string>;
  onRemove: (uri: string) => void;
  onToggle: (uri: string) => void;
}) {
  return (
    <div className={`flex items-start gap-2 px-3 py-2 rounded-lg border transition-colors ${
      skill.confirmed ? "border-green-200 bg-green-50/50" : "border-amber-200 bg-amber-50/50"
    }`}>
      <button onClick={() => onToggle(skill.uri)} className="mt-0.5 flex-shrink-0">
        {skill.confirmed ? (
          <CheckCircle2 className="w-4 h-4 text-green-500" />
        ) : (
          <HelpCircle className="w-4 h-4 text-amber-500" />
        )}
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">{skill.label}</span>
          <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{skill.type}</span>
        </div>
        {skill.description && (
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{skill.description}</p>
        )}
        <span className="text-xs text-gray-400">{sourceLabel[skill.source] || skill.source}</span>
      </div>
      <button onClick={() => onRemove(skill.uri)} className="text-gray-300 hover:text-red-400 mt-0.5 flex-shrink-0">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
