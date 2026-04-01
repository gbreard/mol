"use client";

import { useState, useEffect } from "react";
import {
  Loader2, RefreshCw, Search, CheckCircle2, Eye, Edit2,
  Save, X, ChevronDown, ChevronRight, Undo2, Split, RotateCcw,
} from "lucide-react";

interface Member {
  uri: string;
  label: string;
  frecuencia: number;
}

interface ImpactoOcupacion {
  isco_code: string;
  ocupacion_label: string;
  ofertas_count: number;
  pct_de_ocupacion: number;
}

interface Equivalence {
  id: string;
  label_representante: string;
  label_argentino: string | null;
  miembros: Member[];
  cantidad_miembros: number;
  frecuencia_total: number;
  estado: string;
  revisado_por: string | null;
  notas: string | null;
  similitud_promedio: number | null;
  similitud_minima: number | null;
}

interface Stats {
  total: number;
  auto: number;
  revisado: number;
  aprobado: number;
}

const ESTADO_STYLES: Record<string, string> = {
  auto: "bg-gray-100 text-gray-700",
  revisado: "bg-amber-100 text-amber-700",
  aprobado: "bg-green-100 text-green-700",
};

export default function EquivalenciasPage() {
  const [equivalences, setEquivalences] = useState<Equivalence[]>([]);
  const [stats, setStats] = useState<Stats>({ total: 0, auto: 0, revisado: 0, aprobado: 0 });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [estadoFilter, setEstadoFilter] = useState("");
  const [sortBy, setSortBy] = useState("frecuencia");
  const [impactoCache, setImpactoCache] = useState<Record<string, ImpactoOcupacion[]>>({});
  const [activeTab, setActiveTab] = useState<"equivalencias" | "candidatos">("equivalencias");
  const [candidates, setCandidates] = useState<any[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  // M-08c: Re-clustering modal
  const [reclusterOpen, setReclusterOpen] = useState(false);
  const [reclusterThreshold, setReclusterThreshold] = useState(0.85);
  const [reclusterState, setReclusterState] = useState<"idle" | "previewing" | "preview_ready" | "applying" | "done" | "error">("idle");
  const [reclusterResult, setReclusterResult] = useState<any>(null);
  const [reclusterError, setReclusterError] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [editing, setEditing] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ label_representante: "", label_argentino: "", notas: "" });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "error"; text: string } | null>(null);
  const [page, setPage] = useState(0);
  const pageSize = 30;
  const [descriptions, setDescriptions] = useState<Record<string, string>>({});

  async function loadData() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (estadoFilter) params.set("estado", estadoFilter);
      if (search) params.set("search", search);
      if (sortBy) params.set("sort", sortBy);
      params.set("limit", String(pageSize));
      params.set("offset", String(page * pageSize));

      const res = await fetch(`/api/skill-equivalences?${params}`);
      if (res.ok) {
        const data = await res.json();
        setEquivalences(data.equivalences || []);
        setStats(data.stats || { total: 0, auto: 0, revisado: 0, aprobado: 0 });
      }
    } catch {} finally {
      setLoading(false);
    }
  }

  // Lazy load impacto en ocupaciones
  async function loadImpacto(eqId: string) {
    if (impactoCache[eqId]) return;
    try {
      const { supabase } = await import("@/lib/supabase");
      if (!supabase) return;
      const result = await supabase.rpc('get_equivalencia_impacto', { p_equivalence_id: eqId });
      if (result.data) {
        setImpactoCache(prev => ({ ...prev, [eqId]: result.data }));
      }
    } catch {}
  }

  async function loadCandidates() {
    setCandidatesLoading(true);
    try {
      const { supabase } = await import("@/lib/supabase");
      if (!supabase) return;
      const result = await supabase.rpc('get_equiv_candidates', { p_estado: 'pendiente', limit_n: 50 });
      if (result.data) setCandidates(result.data);
    } catch {} finally {
      setCandidatesLoading(false);
    }
  }

  async function handleCandidateAction(id: number, action: 'aprobar' | 'rechazar') {
    try {
      const { supabase } = await import("@/lib/supabase");
      if (!supabase) return;
      if (action === 'aprobar') {
        await supabase.rpc('aprobar_candidato', { p_candidate_id: id, p_action: 'crear_grupo' });
      } else {
        await supabase.rpc('rechazar_candidato', { p_candidate_id: id });
      }
      setCandidates(prev => prev.filter(c => c.id !== id));
      setMessage({ type: "ok", text: `Candidato ${action === 'aprobar' ? 'aprobado' : 'rechazado'}` });
    } catch (e: any) {
      setMessage({ type: "error", text: e.message || "Error" });
    }
  }

  // M-08c: Re-clustering via pipeline_commands
  async function startReclusterPreview() {
    setReclusterState("previewing");
    setReclusterResult(null);
    setReclusterError("");
    try {
      const { supabase } = await import("@/lib/supabase");
      if (!supabase) return;
      const { data } = await supabase.from("pipeline_commands").insert({
        comando: "recluster_preview",
        params: { threshold: reclusterThreshold },
        creado_por: "admin@dashboard",
      }).select("id").single();
      if (data?.id) pollReclusterCommand(data.id, "preview");
    } catch (e: any) {
      setReclusterState("error");
      setReclusterError(e.message || "Error al crear comando");
    }
  }

  async function startReclusterApply() {
    setReclusterState("applying");
    try {
      const { supabase } = await import("@/lib/supabase");
      if (!supabase) return;
      const { data } = await supabase.from("pipeline_commands").insert({
        comando: "recluster_apply",
        params: { threshold: reclusterThreshold },
        creado_por: "admin@dashboard",
      }).select("id").single();
      if (data?.id) pollReclusterCommand(data.id, "apply");
    } catch (e: any) {
      setReclusterState("error");
      setReclusterError(e.message || "Error al crear comando");
    }
  }

  async function pollReclusterCommand(cmdId: string, tipo: "preview" | "apply") {
    const { supabase } = await import("@/lib/supabase");
    if (!supabase) return;
    const interval = setInterval(async () => {
      try {
        const { data } = await supabase.from("pipeline_commands").select("estado,resultado,error_message").eq("id", cmdId).single();
        if (!data) return;
        if (data.estado === "completado") {
          clearInterval(interval);
          setReclusterResult(data.resultado);
          setReclusterState(tipo === "preview" ? "preview_ready" : "done");
        } else if (data.estado === "error") {
          clearInterval(interval);
          setReclusterError(data.error_message || "Error desconocido");
          setReclusterState("error");
        }
      } catch {}
    }, 5000);
    // Cleanup after 10 min max
    setTimeout(() => clearInterval(interval), 600000);
  }

  useEffect(() => { loadData(); }, [estadoFilter, page, sortBy]);
  useEffect(() => { if (activeTab === 'candidatos') loadCandidates(); }, [activeTab]);

  // Load descriptions from skills_searchable.json (once)
  useEffect(() => {
    fetch("/data/skills_searchable.json")
      .then(r => r.json())
      .then(data => {
        const map: Record<string, string> = {};
        for (const s of (data.skills || [])) {
          if (s.label && s.description) map[s.label.toLowerCase()] = s.description;
        }
        setDescriptions(map);
      })
      .catch(() => {});
  }, []);

  function doSearch() { setPage(0); loadData(); }

  function toggleExpand(id: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const [editMembers, setEditMembers] = useState<Member[]>([]);
  const [removedMembers, setRemovedMembers] = useState<Member[]>([]);

  function startEdit(eq: Equivalence) {
    setEditing(eq.id);
    setEditForm({
      label_representante: eq.label_representante,
      label_argentino: eq.label_argentino || "",
      notas: eq.notas || "",
    });
    setEditMembers([...eq.miembros]);
    setRemovedMembers([]);
  }

  function removeMember(member: Member) {
    setEditMembers(prev => prev.filter(m => m.uri !== member.uri));
    setRemovedMembers(prev => [...prev, member]);
  }

  function restoreMember(member: Member) {
    setRemovedMembers(prev => prev.filter(m => m.uri !== member.uri));
    setEditMembers(prev => [...prev, member]);
  }

  async function saveEdit(id: string, newEstado?: string) {
    setSaving(true);
    try {
      const res = await fetch("/api/skill-equivalences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id,
          ...editForm,
          estado: newEstado || undefined,
          miembros: editMembers.length > 0 ? editMembers : undefined,
          cantidad_miembros: editMembers.length > 0 ? editMembers.length : undefined,
          split_members: removedMembers.length > 0 ? removedMembers : undefined,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      setMessage({ type: "ok", text: "Guardado" });
      setEditing(null);
      loadData();
    } catch (e: any) {
      setMessage({ type: "error", text: e.message });
    } finally {
      setSaving(false);
    }
  }

  async function quickApprove(id: string) {
    try {
      await fetch("/api/skill-equivalences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, estado: "aprobado" }),
      });
      loadData();
    } catch {}
  }

  async function changeEstado(id: string, newEstado: string) {
    try {
      await fetch("/api/skill-equivalences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, estado: newEstado }),
      });
      loadData();
    } catch {}
  }

  if (loading && equivalences.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Equivalencias de Skills</h1>
          <p className="text-gray-500 text-sm mt-1">
            {stats.total} grupos · {stats.auto} automaticos · {stats.revisado} revisados · {stats.aprobado} aprobados
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setReclusterOpen(true)} disabled={reclusterState === "previewing" || reclusterState === "applying"}
            className="flex items-center gap-2 bg-purple-50 text-purple-700 px-3 py-2 rounded-lg hover:bg-purple-100 text-sm border border-purple-200 disabled:opacity-50">
            <RotateCcw className="w-4 h-4" /> Re-clustering
          </button>
          <button onClick={() => activeTab === 'candidatos' ? loadCandidates() : loadData()} className="flex items-center gap-2 text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* M-08c: Modal de re-clustering */}
      {reclusterOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">Re-clustering de equivalencias</h2>
              <button onClick={() => { setReclusterOpen(false); setReclusterState("idle"); }} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {reclusterState === "idle" && (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Umbral de similitud</label>
                  <div className="flex items-center gap-3 mt-1">
                    <input type="range" min="0.80" max="0.95" step="0.01" value={reclusterThreshold}
                      onChange={e => setReclusterThreshold(parseFloat(e.target.value))}
                      className="flex-1" />
                    <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">{reclusterThreshold.toFixed(2)}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Grupos mas estrictos con umbral mas alto. Default: 0.85</p>
                </div>
                <button onClick={startReclusterPreview}
                  className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 text-sm font-medium">
                  Ver cambios
                </button>
              </div>
            )}

            {reclusterState === "previewing" && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <span className="ml-2 text-gray-500">Calculando preview (umbral {reclusterThreshold})...</span>
              </div>
            )}

            {reclusterState === "preview_ready" && reclusterResult && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-green-800">Protegidos (no se tocan)</div>
                  <div className="text-xs text-green-600 mt-1">
                    {reclusterResult.grupos_protegidos || 0} grupos aprobados/revisados ·
                    {reclusterResult.labels_argentinos_protegidos || 0} labels argentinos
                  </div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-blue-800">Cambios en grupos automaticos</div>
                  <div className="text-xs text-blue-600 mt-1">
                    {reclusterResult.cambios?.total || 0} grupos cambiarían
                    {reclusterResult.cambios?.divididos > 0 && ` · ${reclusterResult.cambios.divididos} se dividirían`}
                    {reclusterResult.cambios?.fusionados > 0 && ` · ${reclusterResult.cambios.fusionados} se fusionarían`}
                  </div>
                </div>
                <div className="flex gap-3">
                  <button onClick={startReclusterApply}
                    className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 text-sm font-medium">
                    Aplicar re-clustering
                  </button>
                  <button onClick={() => { setReclusterOpen(false); setReclusterState("idle"); }}
                    className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 text-sm">
                    Cancelar
                  </button>
                </div>
              </div>
            )}

            {reclusterState === "applying" && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-green-600" />
                <span className="ml-2 text-gray-500">Actualizando grupos...</span>
              </div>
            )}

            {reclusterState === "done" && reclusterResult && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                  <CheckCircle2 className="w-8 h-8 text-green-600 mx-auto mb-2" />
                  <div className="text-sm font-medium text-green-800">Re-clustering completado</div>
                  <div className="text-xs text-green-600 mt-1">
                    {reclusterResult.grupos_procesados || reclusterResult.grupos_nuevos || 0} grupos actualizados ·
                    {reclusterResult.grupos_protegidos || 0} protegidos intactos
                  </div>
                  <p className="text-xs text-gray-500 mt-2">El matching usara el lookup actualizado en el proximo run.</p>
                </div>
                <button onClick={() => { setReclusterOpen(false); setReclusterState("idle"); loadData(); }}
                  className="w-full bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 text-sm">
                  Cerrar
                </button>
              </div>
            )}

            {reclusterState === "error" && (
              <div className="space-y-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                  <X className="w-8 h-8 text-red-600 mx-auto mb-2" />
                  <div className="text-sm font-medium text-red-800">Error</div>
                  <div className="text-xs text-red-600 mt-1">{reclusterError}</div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => setReclusterState("idle")}
                    className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 text-sm">
                    Reintentar
                  </button>
                  <button onClick={() => { setReclusterOpen(false); setReclusterState("idle"); }}
                    className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 text-sm">
                    Cerrar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        <button
          onClick={() => setActiveTab("equivalencias")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "equivalencias" ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Equivalencias
        </button>
        <button
          onClick={() => setActiveTab("candidatos")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "candidatos" ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Candidatos {candidates.length > 0 && <span className="ml-1 bg-blue-100 text-blue-700 text-xs px-1.5 py-0.5 rounded-full">{candidates.length}</span>}
        </button>
      </div>

      {message && (
        <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm ${message.type === "ok" ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"}`}>
          {message.type === "ok" ? <CheckCircle2 className="w-4 h-4" /> : <X className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      {/* KPIs */}
      {/* Candidatos Tab */}
      {activeTab === "candidatos" && (
        <div className="space-y-3">
          {candidatesLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <span className="ml-2 text-gray-500">Cargando candidatos...</span>
            </div>
          ) : candidates.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
              Sin candidatos pendientes. Correr generate_equiv_candidates.py para detectar nuevos.
            </div>
          ) : (
            candidates.map(c => (
              <div key={c.id} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs text-gray-400 mb-1">URI: {c.skill_label_esco || c.uri_esco?.slice(0, 50)}</div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">&quot;{c.termino_a}&quot;</span>
                      <span className="text-gray-400">↔</span>
                      <span className="font-medium text-gray-900">&quot;{c.termino_b}&quot;</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {c.co_apariciones} co-apariciones · {c.fuente_a} · {c.fuente_b}
                    </div>
                  </div>
                  <div className="flex gap-2" onClick={e => e.stopPropagation()}>
                    <button onClick={() => handleCandidateAction(c.id, 'aprobar')}
                      className="px-3 py-1.5 bg-green-50 text-green-700 text-xs rounded-lg hover:bg-green-100 border border-green-200">
                      Crear grupo
                    </button>
                    <button onClick={() => handleCandidateAction(c.id, 'rechazar')}
                      className="px-3 py-1.5 bg-gray-50 text-gray-600 text-xs rounded-lg hover:bg-gray-100 border border-gray-200">
                      Rechazar
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Equivalencias Tab */}
      {activeTab === "equivalencias" && <>
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xl font-bold text-gray-700">{stats.total}</div>
          <div className="text-xs text-gray-500">Total grupos</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="text-xl font-bold text-gray-500">{stats.auto}</div>
          <div className="text-xs text-gray-400">Automaticos</div>
        </div>
        <div className="bg-amber-50 rounded-lg p-3 text-center">
          <div className="text-xl font-bold text-amber-700">{stats.revisado}</div>
          <div className="text-xs text-amber-500">Revisados</div>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <div className="text-xl font-bold text-green-700">{stats.aprobado}</div>
          <div className="text-xs text-green-500">Aprobados</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="flex-1 flex gap-2">
          <input value={search} onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === "Enter" && doSearch()}
            placeholder="Buscar skill..." className="flex-1 border rounded-lg px-3 py-2 text-sm" />
          <button onClick={doSearch} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
            <Search className="w-4 h-4" />
          </button>
        </div>
        <select value={estadoFilter} onChange={e => { setEstadoFilter(e.target.value); setPage(0); }}
          className="border rounded-lg px-3 py-2 text-sm">
          <option value="">Todos</option>
          <option value="auto">Automaticos</option>
          <option value="revisado">Revisados</option>
          <option value="aprobado">Aprobados</option>
        </select>
        <select value={sortBy} onChange={e => { setSortBy(e.target.value); setPage(0); }}
          className="border rounded-lg px-3 py-2 text-sm">
          <option value="frecuencia">Frecuencia</option>
          <option value="confianza_desc">Confianza alta</option>
          <option value="confianza_asc">Revisar primero</option>
        </select>
      </div>

      {/* List */}
      <div className="space-y-2">
        {equivalences.map(eq => {
          const isExpanded = expanded.has(eq.id);
          const isEditing = editing === eq.id;

          return (
            <div key={eq.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              {/* Header */}
              <div className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50"
                onClick={() => toggleExpand(eq.id)}>
                {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{eq.label_argentino || eq.label_representante}</span>
                    {eq.label_argentino && (
                      <span className="text-xs text-gray-400">({eq.label_representante})</span>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded-full ${ESTADO_STYLES[eq.estado]}`}>{eq.estado}</span>
                    {eq.similitud_promedio != null && <ConfidenceBadge sim={eq.similitud_promedio} />}
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {eq.cantidad_miembros} equivalentes · {eq.frecuencia_total.toLocaleString("es-AR")} apariciones en ofertas
                  </div>
                </div>
                <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                  <button onClick={() => startEdit(eq)} className="p-1.5 text-blue-500 hover:bg-blue-50 rounded" title="Editar">
                    <Edit2 className="w-4 h-4" />
                  </button>
                  {eq.estado !== "aprobado" && (
                    <button onClick={() => quickApprove(eq.id)} className="p-1.5 text-green-500 hover:bg-green-50 rounded" title="Aprobar">
                      <CheckCircle2 className="w-4 h-4" />
                    </button>
                  )}
                  {eq.estado === "aprobado" && (
                    <button onClick={() => changeEstado(eq.id, "revisado")} className="p-1.5 text-amber-500 hover:bg-amber-50 rounded" title="Volver a revisado">
                      <Undo2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Edit form */}
              {isEditing && (
                <div className="px-4 py-3 bg-blue-50 border-t border-blue-100 space-y-3">
                  {/* Labels + notas */}
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-600 block mb-1">Label representante</label>
                      <input value={editForm.label_representante} onChange={e => setEditForm({ ...editForm, label_representante: e.target.value })}
                        className="w-full border rounded px-2 py-1.5 text-sm" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-600 block mb-1">Label argentino</label>
                      <input value={editForm.label_argentino} onChange={e => setEditForm({ ...editForm, label_argentino: e.target.value })}
                        placeholder="Ej: Trabajo en grupo" className="w-full border rounded px-2 py-1.5 text-sm" />
                    </div>
                  </div>
                  <input value={editForm.notas} onChange={e => setEditForm({ ...editForm, notas: e.target.value })}
                    placeholder="Notas (opcional)" className="w-full border rounded px-2 py-1.5 text-sm" />

                  {/* Members in edit mode */}
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Miembros del grupo ({editMembers.length}):</div>
                    <div className="space-y-1 max-h-64 overflow-y-auto">
                      {editMembers.map((m, i) => {
                        const desc = descriptions[m.label?.toLowerCase()];
                        const isRep = m.label === editForm.label_representante;
                        return (
                          <div key={m.uri} className="bg-white rounded-lg p-2 border border-gray-200 flex items-start gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-400 w-10 text-right flex-shrink-0">{m.frecuencia}</span>
                                <span className={`text-sm ${isRep ? "font-medium text-blue-700" : "text-gray-700"}`}>
                                  {m.label}
                                  {isRep && <span className="text-xs text-blue-400 ml-1">(rep)</span>}
                                </span>
                              </div>
                              {desc && (
                                <p className="text-xs text-gray-400 mt-0.5 ml-12 line-clamp-2">{desc}</p>
                              )}
                            </div>
                            {!isRep && (
                              <button onClick={() => removeMember(m)}
                                className="p-1 text-orange-400 hover:text-orange-600 hover:bg-orange-50 rounded flex-shrink-0" title="Separar en grupo propio">
                                <Split className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Separated members (will become own groups) */}
                  {removedMembers.length > 0 && (
                    <div>
                      <div className="text-xs text-orange-600 mb-1">Se separan en grupos propios ({removedMembers.length}):</div>
                      <div className="space-y-1">
                        {removedMembers.map(m => (
                          <div key={m.uri} className="bg-orange-50 rounded-lg p-2 border border-orange-200 flex items-center gap-2">
                            <Split className="w-3.5 h-3.5 text-orange-400 flex-shrink-0" />
                            <span className="text-xs text-orange-400 w-10 text-right flex-shrink-0">{m.frecuencia}</span>
                            <span className="text-sm text-orange-600 flex-1">{m.label}</span>
                            <button onClick={() => restoreMember(m)}
                              className="p-1 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded flex-shrink-0" title="Volver al grupo">
                              <RotateCcw className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="flex gap-2 pt-1">
                    <button onClick={() => saveEdit(eq.id, "revisado")} disabled={saving}
                      className="bg-amber-500 text-white px-3 py-1.5 rounded text-xs font-medium disabled:opacity-50 flex items-center gap-1">
                      {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Eye className="w-3 h-3" />} Guardar como revisado
                    </button>
                    <button onClick={() => saveEdit(eq.id, "aprobado")} disabled={saving}
                      className="bg-green-600 text-white px-3 py-1.5 rounded text-xs font-medium disabled:opacity-50 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Aprobar
                    </button>
                    {eq.estado !== "auto" && (
                      <button onClick={() => saveEdit(eq.id, "auto")} disabled={saving}
                        className="bg-gray-500 text-white px-3 py-1.5 rounded text-xs font-medium disabled:opacity-50 flex items-center gap-1">
                        <Undo2 className="w-3 h-3" /> Volver a auto
                      </button>
                    )}
                    <button onClick={() => setEditing(null)} className="text-gray-500 px-3 py-1.5 text-xs">Cancelar</button>
                  </div>
                </div>
              )}

              {/* Members */}
              {isExpanded && !isEditing && (
                <div className="px-4 py-3 border-t border-gray-100 bg-gray-50 space-y-2">
                  <div className="text-xs text-gray-500">Skills ESCO equivalentes:</div>
                  {eq.miembros.map((m, i) => {
                    const desc = descriptions[m.label?.toLowerCase()];
                    return (
                      <div key={i} className="bg-white rounded-lg p-2 border border-gray-100">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 w-12 text-right flex-shrink-0">{m.frecuencia}</span>
                          <span className={`text-sm ${m.label === eq.label_representante ? "font-medium text-blue-700" : "text-gray-700"}`}>
                            {m.label}
                            {m.label === eq.label_representante && <span className="text-xs text-blue-400 ml-1">(representante)</span>}
                          </span>
                        </div>
                        {desc && (
                          <p className="text-xs text-gray-400 mt-1 ml-14 line-clamp-2">{desc}</p>
                        )}
                      </div>
                    );
                  })}
                  {/* Panel de impacto en ocupaciones (lazy load) */}
                  <ImpactoPanel eqId={eq.id} impacto={impactoCache[eq.id]} onLoad={loadImpacto} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
          className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-30">
          Anterior
        </button>
        <span className="text-sm text-gray-400">Pagina {page + 1}</span>
        <button onClick={() => { setPage(p => p + 1); }} disabled={equivalences.length < pageSize}
          className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-30">
          Siguiente
        </button>
      </div>
      </>}
    </div>
  );
}

// ─── Componentes auxiliares ───────────────────────────────────────

function ConfidenceBadge({ sim }: { sim: number }) {
  let dots = 1;
  let color = 'text-red-500';
  if (sim >= 0.92) { dots = 4; color = 'text-green-500'; }
  else if (sim >= 0.88) { dots = 3; color = 'text-blue-500'; }
  else if (sim >= 0.85) { dots = 2; color = 'text-amber-500'; }

  return (
    <span className={`text-xs ${color} ml-1`} title={`Similitud promedio: ${(sim * 100).toFixed(1)}%`}>
      {'●'.repeat(dots)}{'○'.repeat(4 - dots)}
      <span className="text-gray-400 ml-1">{(sim * 100).toFixed(0)}%</span>
    </span>
  );
}

function ImpactoPanel({ eqId, impacto, onLoad }: { eqId: string; impacto?: ImpactoOcupacion[]; onLoad: (id: string) => void }) {
  useEffect(() => { if (!impacto) onLoad(eqId); }, [eqId]);

  if (!impacto) {
    return (
      <div className="text-xs text-gray-400 mt-2">
        <Loader2 className="w-3 h-3 animate-spin inline mr-1" />
        Cargando impacto en ocupaciones...
      </div>
    );
  }

  if (impacto.length === 0) {
    return (
      <div className="text-xs text-gray-400 mt-2">Sin datos de impacto en ocupaciones</div>
    );
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-200">
      <div className="text-xs text-gray-500 mb-2">Impacto en ocupaciones:</div>
      {impacto.map((o, i) => (
        <div key={i} className="flex items-center gap-2 text-xs text-gray-600 mb-1">
          <span className="text-gray-400">·</span>
          <span className="font-medium">{o.ocupacion_label}</span>
          <span className="text-gray-400">({o.isco_code})</span>
          <span className="ml-auto text-gray-500">{o.ofertas_count.toLocaleString()} ofertas</span>
          <span className="text-blue-500">({o.pct_de_ocupacion}%)</span>
        </div>
      ))}
    </div>
  );
}
