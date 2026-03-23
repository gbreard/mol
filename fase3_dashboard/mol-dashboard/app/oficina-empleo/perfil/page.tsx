"use client";

import { useState, useCallback } from "react";
import { UserSearch, Save, ArrowRight, Loader2, Target, ChevronRight } from "lucide-react";
import DniSearch from "@/components/DniSearch";
import { SkillCapturePanel, SkillsPanel, type CapturedSkill } from "@/components/oficina-empleo/SkillCapturePanel";

interface WorkerData {
  nombre: string;
  dni: string;
  edad: string;
  nivel_educativo: string;
}

interface OccupationMatch {
  label: string;
  isco_code: string;
  match_score: number;
  essential_covered: number;
  essential_total: number;
  gap_count: number;
}

type Step = "datos" | "competencias" | "resultados";

export default function PerfilPage() {
  const [step, setStep] = useState<Step>("datos");
  const [worker, setWorker] = useState<WorkerData>({ nombre: "", dni: "", edad: "", nivel_educativo: "" });
  const [skills, setSkills] = useState<CapturedSkill[]>([]);
  const [matches, setMatches] = useState<OccupationMatch[]>([]);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const addSkills = useCallback((newSkills: CapturedSkill[]) => {
    setSkills(prev => {
      const existing = new Set(prev.map(s => s.uri));
      const unique = newSkills.filter(s => !existing.has(s.uri));
      return [...prev, ...unique];
    });
  }, []);

  const removeSkill = useCallback((uri: string) => {
    setSkills(prev => prev.filter(s => s.uri !== uri));
  }, []);

  const toggleConfirm = useCallback((uri: string) => {
    setSkills(prev => prev.map(s => s.uri === uri ? { ...s, confirmed: !s.confirmed } : s));
  }, []);

  async function findMatches() {
    if (skills.length === 0) return;
    setLoadingMatches(true);
    setStep("resultados");

    try {
      const skillLabels = skills.filter(s => s.confirmed).map(s => s.label);
      const res = await fetch(`/api/occupations/search?q=${encodeURIComponent(skillLabels.slice(0, 5).join(" "))}&limit=10`);
      if (res.ok) {
        const occupations = await res.json();
        // Calculate match score based on skills overlap
        const matchResults: OccupationMatch[] = await Promise.all(
          (occupations || []).slice(0, 10).map(async (occ: any) => {
            try {
              const skillsRes = await fetch(`/api/occupations/skills?isco_code=${occ.isco_code || occ.isco}`);
              const skillsData = skillsRes.ok ? await skillsRes.json() : { skills: [] };
              const occSkills = (skillsData.skills || skillsData.essential || []).map((s: any) => (s.label || s.preferred_label || "").toLowerCase());
              const workerSkillSet = new Set(skillLabels.map(s => s.toLowerCase()));
              const covered = occSkills.filter((s: string) => workerSkillSet.has(s)).length;
              const total = occSkills.length || 1;
              return {
                label: occ.label,
                isco_code: occ.isco_code || occ.isco,
                match_score: Math.round((covered / total) * 100),
                essential_covered: covered,
                essential_total: total,
                gap_count: total - covered,
              };
            } catch {
              return { label: occ.label, isco_code: occ.isco_code || occ.isco, match_score: 0, essential_covered: 0, essential_total: 0, gap_count: 0 };
            }
          })
        );
        setMatches(matchResults.sort((a, b) => b.match_score - a.match_score));
      }
    } catch {} finally {
      setLoadingMatches(false);
    }
  }

  async function saveProfile() {
    setSaving(true);
    try {
      // Save worker profile
      const res = await fetch("/api/worker-profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...worker,
          skills: skills.filter(s => s.confirmed).map(s => ({
            uri: s.uri, label: s.label, type: s.type, source: s.source,
          })),
          ocupaciones_compatibles: matches.slice(0, 5).map(m => ({
            isco_code: m.isco_code, label: m.label, match_score: m.match_score,
          })),
        }),
      });
      if (res.ok) setSaved(true);
    } catch {} finally {
      setSaving(false);
    }
  }

  const confirmedCount = skills.filter(s => s.confirmed).length;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <UserSearch className="w-7 h-7 text-teal-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Perfil de Trabajador</h1>
          <p className="text-sm text-gray-500">Registra competencias y encuentra ocupaciones compatibles</p>
        </div>
      </div>

      {/* Steps indicator */}
      <div className="flex items-center gap-2 mb-8">
        {[
          { id: "datos", label: "1. Datos", enabled: true },
          { id: "competencias", label: "2. Competencias", enabled: worker.nombre.length > 0 },
          { id: "resultados", label: "3. Resultados", enabled: confirmedCount > 0 },
        ].map((s, i) => (
          <button
            key={s.id}
            onClick={() => s.enabled && setStep(s.id as Step)}
            disabled={!s.enabled}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              step === s.id
                ? "bg-teal-600 text-white"
                : s.enabled
                  ? "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  : "bg-gray-50 text-gray-300"
            }`}
          >
            {s.label}
            {i < 2 && <ChevronRight className="w-3 h-3 ml-1" />}
          </button>
        ))}
      </div>

      {/* STEP 1: Datos del trabajador */}
      {step === "datos" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Search existing */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
            <h2 className="text-base font-semibold text-gray-800 mb-1">Buscar perfil existente</h2>
            <p className="text-sm text-gray-500 mb-4">
              Busca por DNI si el trabajador ya tiene un perfil creado.
            </p>
            <DniSearch organizacionNombre="Oficina de Empleo" />
          </div>

          {/* New profile form */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Nuevo perfil</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Nombre completo *</label>
                <input value={worker.nombre} onChange={e => setWorker({ ...worker, nombre: e.target.value })}
                  placeholder="Juan Perez" className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">DNI</label>
                  <input value={worker.dni} onChange={e => setWorker({ ...worker, dni: e.target.value })}
                    placeholder="12345678" className="w-full border rounded-lg px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Edad</label>
                  <input value={worker.edad} onChange={e => setWorker({ ...worker, edad: e.target.value })}
                    placeholder="35" className="w-full border rounded-lg px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Nivel educativo</label>
                <select value={worker.nivel_educativo} onChange={e => setWorker({ ...worker, nivel_educativo: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm">
                  <option value="">Seleccionar...</option>
                  <option value="primario">Primario</option>
                  <option value="secundario">Secundario</option>
                  <option value="terciario">Terciario</option>
                  <option value="universitario">Universitario</option>
                  <option value="posgrado">Posgrado</option>
                </select>
              </div>
              <button
                onClick={() => setStep("competencias")}
                disabled={!worker.nombre}
                className="w-full bg-teal-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-teal-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                Siguiente: Capturar competencias
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: Captura de competencias */}
      {step === "competencias" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Capture */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Capturar competencias</h2>
            <SkillCapturePanel
              skills={skills}
              onAddSkills={addSkills}
              onRemoveSkill={removeSkill}
              onToggleConfirm={toggleConfirm}
            />
          </div>

          {/* Right: Skills panel */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
            <SkillsPanel
              skills={skills}
              onRemoveSkill={removeSkill}
              onToggleConfirm={toggleConfirm}
            />

            {confirmedCount > 0 && (
              <button
                onClick={findMatches}
                className="w-full mt-4 bg-teal-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-teal-700 flex items-center justify-center gap-2"
              >
                <Target className="w-4 h-4" />
                Buscar ocupaciones compatibles ({confirmedCount} skills)
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* STEP 3: Results */}
      {step === "resultados" && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-teal-50 border border-teal-200 rounded-2xl p-5 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-teal-900">{worker.nombre}</h2>
              <p className="text-sm text-teal-700">{confirmedCount} competencias confirmadas</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setStep("competencias")} className="text-sm text-teal-600 hover:text-teal-700 px-3 py-1.5 rounded-lg hover:bg-teal-100">
                Editar competencias
              </button>
              <button onClick={saveProfile} disabled={saving || saved}
                className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-teal-700 disabled:opacity-50 flex items-center gap-2">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {saved ? "Guardado" : "Guardar perfil"}
              </button>
            </div>
          </div>

          {/* Occupation matches */}
          {loadingMatches ? (
            <div className="py-12 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-teal-600 mx-auto mb-3" />
              <p className="text-gray-500">Buscando ocupaciones compatibles...</p>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900">Ocupaciones compatibles</h3>
                <p className="text-xs text-gray-500">{matches.length} ocupaciones encontradas</p>
              </div>
              <div className="divide-y">
                {matches.map((m, i) => (
                  <div key={i} className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold ${
                      m.match_score >= 70 ? "bg-green-100 text-green-700" :
                      m.match_score >= 40 ? "bg-amber-100 text-amber-700" :
                      "bg-gray-100 text-gray-500"
                    }`}>
                      {m.match_score}%
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900">{m.label}</div>
                      <div className="text-xs text-gray-500">
                        ISCO {m.isco_code} · {m.essential_covered}/{m.essential_total} esenciales · {m.gap_count} brecha
                      </div>
                    </div>
                    <a href={`/oficina-empleo/ofertas?isco=${m.isco_code}&skills=${encodeURIComponent(skills.filter(s => s.confirmed).map(s => s.label).join(","))}`}
                      className="text-sm text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1">
                      Ver ofertas <ChevronRight className="w-4 h-4" />
                    </a>
                  </div>
                ))}

                {matches.length === 0 && !loadingMatches && (
                  <div className="px-6 py-8 text-center text-gray-400">
                    <Target className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p className="text-sm">No se encontraron ocupaciones. Intenta agregar mas competencias.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
