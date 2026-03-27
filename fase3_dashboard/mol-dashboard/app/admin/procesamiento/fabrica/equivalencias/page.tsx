"use client";

import { useState, useEffect } from "react";
import {
  Loader2, RefreshCw, Search, CheckCircle2, Eye, Edit2,
  Save, X, ChevronDown, ChevronRight,
} from "lucide-react";

interface Member {
  uri: string;
  label: string;
  frecuencia: number;
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

  useEffect(() => { loadData(); }, [estadoFilter, page]);

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

  function startEdit(eq: Equivalence) {
    setEditing(eq.id);
    setEditForm({
      label_representante: eq.label_representante,
      label_argentino: eq.label_argentino || "",
      notas: eq.notas || "",
    });
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
        <button onClick={loadData} className="flex items-center gap-2 text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {message && (
        <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm ${message.type === "ok" ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"}`}>
          {message.type === "ok" ? <CheckCircle2 className="w-4 h-4" /> : <X className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      {/* KPIs */}
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
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {eq.cantidad_miembros} equivalentes · {eq.frecuencia_total.toLocaleString("es-AR")} apariciones en ofertas
                  </div>
                </div>
                <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                  {eq.estado === "auto" && (
                    <>
                      <button onClick={() => startEdit(eq)} className="p-1.5 text-blue-500 hover:bg-blue-50 rounded" title="Editar">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => quickApprove(eq.id)} className="p-1.5 text-green-500 hover:bg-green-50 rounded" title="Aprobar">
                        <CheckCircle2 className="w-4 h-4" />
                      </button>
                    </>
                  )}
                  {eq.estado === "revisado" && (
                    <button onClick={() => quickApprove(eq.id)} className="p-1.5 text-green-500 hover:bg-green-50 rounded" title="Aprobar">
                      <CheckCircle2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Edit form */}
              {isEditing && (
                <div className="px-4 py-3 bg-blue-50 border-t border-blue-100 space-y-2">
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
                  <div className="flex gap-2">
                    <button onClick={() => saveEdit(eq.id, "revisado")} disabled={saving}
                      className="bg-amber-500 text-white px-3 py-1.5 rounded text-xs font-medium disabled:opacity-50">
                      {saving ? <Loader2 className="w-3 h-3 animate-spin inline" /> : <Eye className="w-3 h-3 inline" />} Guardar como revisado
                    </button>
                    <button onClick={() => saveEdit(eq.id, "aprobado")} disabled={saving}
                      className="bg-green-600 text-white px-3 py-1.5 rounded text-xs font-medium disabled:opacity-50">
                      <CheckCircle2 className="w-3 h-3 inline" /> Aprobar
                    </button>
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
    </div>
  );
}
