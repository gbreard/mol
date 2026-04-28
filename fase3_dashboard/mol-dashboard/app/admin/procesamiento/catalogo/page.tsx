"use client";

import { Fragment, useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  Loader2, RefreshCw, Plus, Search, Edit2, Trash2, Save, X,
  CheckCircle2, AlertTriangle, XCircle, BookOpen, Briefcase,
  AlertCircle, Tag, Clock, ChevronDown, ChevronRight, Eye,
  ExternalLink,
} from "lucide-react";

// ============================================================
// Types
// ============================================================

interface CatalogoSkill {
  id: string;
  label: string;
  label_normalized: string;
  definicion: string | null;
  tipo: string;
  categoria_l1: string | null;
  categoria_l2: string | null;
  source: string;
  esco_parent_uri: string | null;
  esco_parent_label: string | null;
  relaciones: { skill: string; tipo: string }[];
  frecuencia_mercado: number;
  primera_deteccion: string | null;
  estado: string;
  aprobada_por: string | null;
  aprobada_at: string | null;
  version_catalogo: string | null;
  notas: string | null;
}

interface OfertaEjemplo {
  id_oferta: string;
  titulo: string;
  esco_actual?: string;
  regla_aplicada?: string;
  fecha_deteccion?: string;
}

interface CatalogoOcupacion {
  id: string;
  label: string;
  label_normalized: string;
  definicion: string | null;
  isco_parent: string | null;
  isco_parent_label: string | null;
  esco_parent_uri: string | null;
  esco_parent_label: string | null;
  source: string;
  skills_esenciales: string[];
  skills_opcionales: string[];
  sector: string | null;
  frecuencia_mercado: number;
  primera_deteccion: string | null;
  estado: string;
  aprobada_por: string | null;
  version_catalogo: string | null;
  notas: string | null;
  ofertas_ejemplo?: OfertaEjemplo[];
}

interface UnclassifiedItem {
  label: string;
  frecuencia: number;
  pct: number;
  avg_score?: number;
  isco_mode?: string;
}

interface CatalogoStats {
  skills: { total: number; catalogadas: number; en_revision: number; detectadas: number; descartadas: number; por_tipo: Record<string, number> };
  ocupaciones: { total: number; catalogadas: number; en_revision: number; detectadas: number; descartadas: number };
  versiones: { version: string; fecha: string; skills: number; ocupaciones: number }[];
  ultima_version: string | null;
}

interface Version {
  id: string;
  version: string;
  fecha_corte: string;
  total_skills: number;
  total_ocupaciones: number;
  skills_nuevas: number;
  ocupaciones_nuevas: number;
  skills_descartadas: number;
  nota: string | null;
  creado_por: string;
}

type Tab = "skills" | "ocupaciones" | "no-clasificados" | "versiones";

const ESTADO_COLORS: Record<string, string> = {
  detectada: "bg-gray-100 text-gray-700",
  en_revision: "bg-amber-100 text-amber-700",
  catalogada: "bg-green-100 text-green-700",
  descartada: "bg-red-100 text-red-700",
};

const TIPO_COLORS: Record<string, string> = {
  skill: "bg-blue-100 text-blue-700",
  knowledge: "bg-purple-100 text-purple-700",
  transversal: "bg-teal-100 text-teal-700",
};

// ============================================================
// Main Component
// ============================================================

export default function CatalogoPage() {
  const [tab, setTab] = useState<Tab>("no-clasificados");
  const [stats, setStats] = useState<CatalogoStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: "ok" | "error"; text: string } | null>(null);

  async function loadStats() {
    try {
      const res = await fetch("/api/catalogo-mol/stats");
      if (res.ok) setStats(await res.json());
    } catch {}
  }

  useEffect(() => {
    loadStats().finally(() => setLoading(false));
  }, []);

  function showMessage(type: "ok" | "error", text: string) {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando Catalogo MOL...</span>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: typeof BookOpen; count?: number }[] = [
    { id: "no-clasificados", label: "No clasificados", icon: AlertCircle },
    { id: "skills", label: "Skills MOL", icon: BookOpen, count: stats?.skills.total },
    { id: "ocupaciones", label: "Ocupaciones MOL", icon: Briefcase, count: stats?.ocupaciones.total },
    { id: "versiones", label: "Versiones", icon: Tag, count: stats?.versiones.length },
  ];

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Catalogo MOL</h1>
          <p className="text-gray-500 text-sm mt-1">
            Taxonomia propia argentina — skills y ocupaciones que ESCO no cubre
            {stats?.ultima_version && <span className="ml-2 text-blue-600 font-medium">({stats.ultima_version})</span>}
          </p>
        </div>
        <button onClick={() => { setLoading(true); loadStats().finally(() => setLoading(false)); }}
          className="flex items-center gap-2 text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Stats KPIs */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <KPI label="Skills catalogadas" value={stats.skills.catalogadas} color="blue" />
          <KPI label="Ocupaciones catalogadas" value={stats.ocupaciones.catalogadas} color="purple" />
          <KPI label="En revision" value={stats.skills.en_revision + stats.ocupaciones.en_revision} color="amber" />
          <KPI label="Detectadas (nuevas)" value={stats.skills.detectadas + stats.ocupaciones.detectadas} color="gray" />
          <KPI label="Versiones" value={stats.versiones.length} color="green" />
        </div>
      )}

      {/* Message */}
      {message && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${message.type === "ok" ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"}`}>
          {message.type === "ok" ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <Icon className="w-4 h-4" />
              {t.label}
              {t.count !== undefined && (
                <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">{t.count}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {tab === "no-clasificados" && <UnclassifiedTab onCatalog={() => { setTab("skills"); loadStats(); }} showMessage={showMessage} />}
      {tab === "skills" && <SkillsTab onRefresh={loadStats} showMessage={showMessage} />}
      {tab === "ocupaciones" && <OcupacionesTab onRefresh={loadStats} showMessage={showMessage} />}
      {tab === "versiones" && <VersionesTab onRefresh={loadStats} showMessage={showMessage} />}
    </div>
  );
}

// ============================================================
// Tab: No clasificados (G5)
// ============================================================

function UnclassifiedTab({ onCatalog, showMessage }: { onCatalog: () => void; showMessage: (t: "ok" | "error", m: string) => void }) {
  const [data, setData] = useState<{ unclassified_skills: UnclassifiedItem[]; unclassified_titles: UnclassifiedItem[]; total_ofertas: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [minFreq, setMinFreq] = useState(3);
  const [cataloging, setCataloging] = useState<string | null>(null);
  const [catalogForm, setCatalogForm] = useState({ label: "", definicion: "", tipo: "skill", isco_parent: "" });

  async function load() {
    setLoading(true);
    try {
      const res = await fetch(`/api/catalogo-mol/unclassified?min_frecuencia=${minFreq}`);
      if (res.ok) setData(await res.json());
    } catch {} finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [minFreq]);

  async function catalogSkill(label: string) {
    try {
      const res = await fetch("/api/catalogo-mol/skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label: catalogForm.label || label,
          definicion: catalogForm.definicion || null,
          tipo: catalogForm.tipo,
          estado: "en_revision",
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      showMessage("ok", `"${label}" agregada al catalogo como en_revision`);
      setCataloging(null);
      setCatalogForm({ label: "", definicion: "", tipo: "skill", isco_parent: "" });
      load();
    } catch (e: any) {
      showMessage("error", e.message);
    }
  }

  async function catalogOcupacion(label: string) {
    try {
      const res = await fetch("/api/catalogo-mol/ocupaciones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label: catalogForm.label || label,
          definicion: catalogForm.definicion || null,
          isco_parent: catalogForm.isco_parent || null,
          estado: "en_revision",
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      showMessage("ok", `"${label}" agregada como ocupacion en_revision`);
      setCataloging(null);
      setCatalogForm({ label: "", definicion: "", tipo: "skill", isco_parent: "" });
      load();
    } catch (e: any) {
      showMessage("error", e.message);
    }
  }

  if (loading) return <div className="py-8 text-center text-gray-500"><Loader2 className="w-6 h-6 animate-spin inline mr-2" />Analizando ofertas...</div>;

  return (
    <div className="space-y-6">
      {/* Min frequency filter */}
      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-600">Frecuencia minima:</label>
        <select value={minFreq} onChange={(e) => setMinFreq(parseInt(e.target.value))}
          className="border rounded-lg px-3 py-1.5 text-sm">
          <option value={2}>2+ ofertas</option>
          <option value={3}>3+ ofertas</option>
          <option value={5}>5+ ofertas</option>
          <option value={10}>10+ ofertas</option>
          <option value={20}>20+ ofertas</option>
        </select>
        <span className="text-xs text-gray-400">de {data?.total_ofertas?.toLocaleString("es-AR")} ofertas totales</span>
      </div>

      {/* Skills no clasificadas */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-blue-500" />
          <h3 className="font-semibold text-gray-900">Skills no clasificadas</h3>
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{data?.unclassified_skills?.length || 0}</span>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {(!data?.unclassified_skills || data.unclassified_skills.length === 0) ? (
            <div className="px-4 py-6 text-center text-gray-400 text-sm">Sin skills no clasificadas con esta frecuencia</div>
          ) : (
            <table className="w-full text-sm">
              <thead><tr className="bg-gray-50 text-gray-500 text-xs">
                <th className="text-left px-4 py-2">Skill</th>
                <th className="text-right px-4 py-2">Ofertas</th>
                <th className="text-right px-4 py-2">%</th>
                <th className="text-center px-4 py-2 w-24">Accion</th>
              </tr></thead>
              <tbody>
                {data.unclassified_skills.map((s) => (
                  <tr key={s.label} className="border-t border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium text-gray-900">{s.label}</td>
                    <td className="px-4 py-2 text-right text-gray-600">{s.frecuencia}</td>
                    <td className="px-4 py-2 text-right text-gray-400">{s.pct}%</td>
                    <td className="px-4 py-2 text-center">
                      {cataloging === `skill:${s.label}` ? (
                        <div className="space-y-1">
                          <input value={catalogForm.definicion} onChange={(e) => setCatalogForm({ ...catalogForm, definicion: e.target.value })}
                            placeholder="Definicion (opcional)" className="w-full border rounded px-2 py-1 text-xs" />
                          <select value={catalogForm.tipo} onChange={(e) => setCatalogForm({ ...catalogForm, tipo: e.target.value })}
                            className="w-full border rounded px-2 py-1 text-xs">
                            <option value="skill">Skill</option>
                            <option value="knowledge">Knowledge</option>
                            <option value="transversal">Transversal</option>
                          </select>
                          <div className="flex gap-1">
                            <button onClick={() => catalogSkill(s.label)} className="flex-1 bg-green-600 text-white px-2 py-1 rounded text-xs">Catalogar</button>
                            <button onClick={() => setCataloging(null)} className="px-2 py-1 text-gray-400 text-xs">X</button>
                          </div>
                        </div>
                      ) : (
                        <button onClick={() => { setCataloging(`skill:${s.label}`); setCatalogForm({ ...catalogForm, label: s.label }); }}
                          className="text-xs text-blue-600 hover:bg-blue-50 px-2 py-1 rounded">
                          + Catalogar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Titulos no clasificados */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
          <Briefcase className="w-4 h-4 text-purple-500" />
          <h3 className="font-semibold text-gray-900">Titulos sin ocupacion ESCO clara</h3>
          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{data?.unclassified_titles?.length || 0}</span>
          <span className="text-xs text-gray-400 ml-2">(score semantico &lt; 0.6)</span>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {(!data?.unclassified_titles || data.unclassified_titles.length === 0) ? (
            <div className="px-4 py-6 text-center text-gray-400 text-sm">Sin titulos no clasificados con esta frecuencia</div>
          ) : (
            <table className="w-full text-sm">
              <thead><tr className="bg-gray-50 text-gray-500 text-xs">
                <th className="text-left px-4 py-2">Titulo</th>
                <th className="text-right px-4 py-2">Ofertas</th>
                <th className="text-right px-4 py-2">Score</th>
                <th className="text-center px-4 py-2">ISCO actual</th>
                <th className="text-center px-4 py-2 w-24">Accion</th>
              </tr></thead>
              <tbody>
                {data.unclassified_titles.map((t) => (
                  <tr key={t.label} className="border-t border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium text-gray-900">{t.label}</td>
                    <td className="px-4 py-2 text-right text-gray-600">{t.frecuencia}</td>
                    <td className="px-4 py-2 text-right">
                      <span className={`text-xs font-mono ${(t.avg_score || 0) < 0.4 ? 'text-red-500' : 'text-amber-500'}`}>
                        {t.avg_score || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-center font-mono text-xs text-gray-500">{t.isco_mode || '—'}</td>
                    <td className="px-4 py-2 text-center">
                      {cataloging === `occ:${t.label}` ? (
                        <div className="space-y-1">
                          <input value={catalogForm.definicion} onChange={(e) => setCatalogForm({ ...catalogForm, definicion: e.target.value })}
                            placeholder="Definicion" className="w-full border rounded px-2 py-1 text-xs" />
                          <input value={catalogForm.isco_parent} onChange={(e) => setCatalogForm({ ...catalogForm, isco_parent: e.target.value })}
                            placeholder="ISCO parent (4 dig)" className="w-full border rounded px-2 py-1 text-xs font-mono" />
                          <div className="flex gap-1">
                            <button onClick={() => catalogOcupacion(t.label)} className="flex-1 bg-purple-600 text-white px-2 py-1 rounded text-xs">Catalogar</button>
                            <button onClick={() => setCataloging(null)} className="px-2 py-1 text-gray-400 text-xs">X</button>
                          </div>
                        </div>
                      ) : (
                        <button onClick={() => { setCataloging(`occ:${t.label}`); setCatalogForm({ ...catalogForm, label: t.label }); }}
                          className="text-xs text-purple-600 hover:bg-purple-50 px-2 py-1 rounded">
                          + Catalogar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Tab: Skills MOL (G6)
// ============================================================

function SkillsTab({ onRefresh, showMessage }: { onRefresh: () => void; showMessage: (t: "ok" | "error", m: string) => void }) {
  const [skills, setSkills] = useState<CatalogoSkill[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [estadoFilter, setEstadoFilter] = useState("");
  const [tipoFilter, setTipoFilter] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<CatalogoSkill>>({});
  const [showNewForm, setShowNewForm] = useState(false);
  const [newForm, setNewForm] = useState({ label: "", definicion: "", tipo: "skill", categoria_l1: "", esco_parent_label: "" });

  async function load() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (estadoFilter) params.set("estado", estadoFilter);
      if (tipoFilter) params.set("tipo", tipoFilter);
      if (search) params.set("search", search);
      params.set("limit", "200");
      const res = await fetch(`/api/catalogo-mol/skills?${params}`);
      if (res.ok) {
        const data = await res.json();
        setSkills(data.skills);
        setTotal(data.total);
      }
    } catch {} finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [estadoFilter, tipoFilter]);

  const filtered = useMemo(() => {
    if (!search) return skills;
    const t = search.toLowerCase();
    return skills.filter(s => s.label.toLowerCase().includes(t) || s.definicion?.toLowerCase().includes(t));
  }, [skills, search]);

  async function updateSkill(id: string, updates: Record<string, any>) {
    try {
      const res = await fetch("/api/catalogo-mol/skills", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, ...updates }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      showMessage("ok", "Skill actualizada");
      setEditing(null);
      load();
      onRefresh();
    } catch (e: any) {
      showMessage("error", e.message);
    }
  }

  async function createSkill() {
    if (!newForm.label) { alert("Falta label"); return; }
    try {
      const res = await fetch("/api/catalogo-mol/skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label: newForm.label,
          definicion: newForm.definicion || null,
          tipo: newForm.tipo,
          categoria_l1: newForm.categoria_l1 || null,
          esco_parent_label: newForm.esco_parent_label || null,
          estado: "en_revision",
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      showMessage("ok", `Skill "${newForm.label}" creada`);
      setShowNewForm(false);
      setNewForm({ label: "", definicion: "", tipo: "skill", categoria_l1: "", esco_parent_label: "" });
      load();
      onRefresh();
    } catch (e: any) {
      showMessage("error", e.message);
    }
  }

  async function changeEstado(id: string, estado: string) {
    await updateSkill(id, { estado });
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar skill..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm" />
        </div>
        <select value={estadoFilter} onChange={(e) => setEstadoFilter(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
          <option value="">Todos los estados</option>
          <option value="detectada">Detectadas</option>
          <option value="en_revision">En revision</option>
          <option value="catalogada">Catalogadas</option>
          <option value="descartada">Descartadas</option>
        </select>
        <select value={tipoFilter} onChange={(e) => setTipoFilter(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
          <option value="">Todos los tipos</option>
          <option value="skill">Skill</option>
          <option value="knowledge">Knowledge</option>
          <option value="transversal">Transversal</option>
        </select>
        <button onClick={() => setShowNewForm(true)} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
          <Plus className="w-4 h-4" /> Nueva skill
        </button>
      </div>

      {/* New form */}
      {showNewForm && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-blue-900">Nueva skill MOL</h3>
            <button onClick={() => setShowNewForm(false)}><X className="w-5 h-5 text-gray-400" /></button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input value={newForm.label} onChange={(e) => setNewForm({ ...newForm, label: e.target.value })} placeholder="Label *" className="border rounded-lg px-3 py-2 text-sm" />
            <select value={newForm.tipo} onChange={(e) => setNewForm({ ...newForm, tipo: e.target.value })} className="border rounded-lg px-3 py-2 text-sm">
              <option value="skill">Skill</option>
              <option value="knowledge">Knowledge</option>
              <option value="transversal">Transversal</option>
            </select>
            <input value={newForm.categoria_l1} onChange={(e) => setNewForm({ ...newForm, categoria_l1: e.target.value })} placeholder="Categoria L1" className="border rounded-lg px-3 py-2 text-sm" />
            <input value={newForm.esco_parent_label} onChange={(e) => setNewForm({ ...newForm, esco_parent_label: e.target.value })} placeholder="Skill ESCO parent (label)" className="border rounded-lg px-3 py-2 text-sm" />
            <textarea value={newForm.definicion} onChange={(e) => setNewForm({ ...newForm, definicion: e.target.value })} placeholder="Definicion completa" className="col-span-2 border rounded-lg px-3 py-2 text-sm" rows={2} />
          </div>
          <button onClick={createSkill} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">Crear skill</button>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="py-8 text-center text-gray-500"><Loader2 className="w-6 h-6 animate-spin inline" /></div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="bg-gray-50 border-b text-gray-500 text-xs">
                <th className="text-left px-4 py-2.5">Label</th>
                <th className="text-left px-4 py-2.5 w-24">Tipo</th>
                <th className="text-left px-4 py-2.5 w-24">Estado</th>
                <th className="text-right px-4 py-2.5 w-16">Freq</th>
                <th className="text-left px-4 py-2.5">ESCO parent</th>
                <th className="text-center px-4 py-2.5 w-32">Acciones</th>
              </tr></thead>
              <tbody>
                {filtered.map((s) => (
                  <tr key={s.id} className="border-t border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-2">
                      <div className="font-medium text-gray-900">{s.label}</div>
                      {s.definicion && <div className="text-xs text-gray-400 truncate max-w-xs">{s.definicion}</div>}
                    </td>
                    <td className="px-4 py-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${TIPO_COLORS[s.tipo] || ""}`}>{s.tipo}</span>
                    </td>
                    <td className="px-4 py-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${ESTADO_COLORS[s.estado] || ""}`}>{s.estado}</span>
                    </td>
                    <td className="px-4 py-2 text-right text-gray-600">{s.frecuencia_mercado}</td>
                    <td className="px-4 py-2 text-xs text-gray-500 truncate max-w-32">{s.esco_parent_label || "—"}</td>
                    <td className="px-4 py-2 text-center">
                      <div className="flex items-center gap-1 justify-center">
                        {s.estado === "detectada" && (
                          <button onClick={() => changeEstado(s.id, "en_revision")} className="text-xs text-amber-600 hover:bg-amber-50 px-2 py-1 rounded" title="Iniciar revision">
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {s.estado === "en_revision" && (
                          <>
                            <button onClick={() => changeEstado(s.id, "catalogada")} className="text-xs text-green-600 hover:bg-green-50 px-2 py-1 rounded" title="Aprobar">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={() => changeEstado(s.id, "descartada")} className="text-xs text-red-400 hover:bg-red-50 px-2 py-1 rounded" title="Descartar">
                              <XCircle className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                        {s.estado === "catalogada" && (
                          <span className="text-xs text-green-500">v{s.version_catalogo || "?"}</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-2 border-t text-xs text-gray-500">{filtered.length} de {total} skills</div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// Tab: Ocupaciones MOL (G6)
// ============================================================

function OcupacionesTab({ onRefresh, showMessage }: { onRefresh: () => void; showMessage: (t: "ok" | "error", m: string) => void }) {
  const [ocupaciones, setOcupaciones] = useState<CatalogoOcupacion[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [estadoFilter, setEstadoFilter] = useState("");
  const [showNewForm, setShowNewForm] = useState(false);
  const [newForm, setNewForm] = useState({ label: "", definicion: "", isco_parent: "", skills_esenciales: "", sector: "" });
  // SPEC catálogo MOL: row expansion para mostrar ofertas_ejemplo
  const [expandedId, setExpandedId] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (estadoFilter) params.set("estado", estadoFilter);
      if (search) params.set("search", search);
      params.set("limit", "200");
      const res = await fetch(`/api/catalogo-mol/ocupaciones?${params}`);
      if (res.ok) {
        const data = await res.json();
        setOcupaciones(data.ocupaciones);
        setTotal(data.total);
      }
    } catch {} finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [estadoFilter]);

  const filtered = useMemo(() => {
    if (!search) return ocupaciones;
    const t = search.toLowerCase();
    return ocupaciones.filter(o => o.label.toLowerCase().includes(t) || o.definicion?.toLowerCase().includes(t));
  }, [ocupaciones, search]);

  async function changeEstado(id: string, estado: string) {
    try {
      const res = await fetch("/api/catalogo-mol/ocupaciones", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, estado }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      showMessage("ok", "Ocupacion actualizada");
      load();
      onRefresh();
    } catch (e: any) {
      showMessage("error", e.message);
    }
  }

  async function createOcupacion() {
    if (!newForm.label) { alert("Falta label"); return; }
    try {
      const skills = newForm.skills_esenciales.split(",").map(s => s.trim()).filter(Boolean);
      const res = await fetch("/api/catalogo-mol/ocupaciones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label: newForm.label,
          definicion: newForm.definicion || null,
          isco_parent: newForm.isco_parent || null,
          skills_esenciales: skills,
          sector: newForm.sector || null,
          estado: "en_revision",
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      showMessage("ok", `Ocupacion "${newForm.label}" creada`);
      setShowNewForm(false);
      setNewForm({ label: "", definicion: "", isco_parent: "", skills_esenciales: "", sector: "" });
      load();
      onRefresh();
    } catch (e: any) {
      showMessage("error", e.message);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar ocupacion..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm" />
        </div>
        <select value={estadoFilter} onChange={(e) => setEstadoFilter(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
          <option value="">Todos los estados</option>
          <option value="detectada">Detectadas</option>
          <option value="en_revision">En revision</option>
          <option value="catalogada">Catalogadas</option>
        </select>
        <button onClick={() => setShowNewForm(true)} className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-700">
          <Plus className="w-4 h-4" /> Nueva ocupacion
        </button>
      </div>

      {showNewForm && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-purple-900">Nueva ocupacion MOL</h3>
            <button onClick={() => setShowNewForm(false)}><X className="w-5 h-5 text-gray-400" /></button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input value={newForm.label} onChange={(e) => setNewForm({ ...newForm, label: e.target.value })} placeholder="Label (ej: Community Manager) *" className="border rounded-lg px-3 py-2 text-sm" />
            <input value={newForm.isco_parent} onChange={(e) => setNewForm({ ...newForm, isco_parent: e.target.value })} placeholder="ISCO parent (4 dig)" className="border rounded-lg px-3 py-2 text-sm font-mono" />
            <input value={newForm.sector} onChange={(e) => setNewForm({ ...newForm, sector: e.target.value })} placeholder="Sector (ej: Marketing)" className="border rounded-lg px-3 py-2 text-sm" />
            <input value={newForm.skills_esenciales} onChange={(e) => setNewForm({ ...newForm, skills_esenciales: e.target.value })} placeholder="Skills esenciales (coma separadas)" className="border rounded-lg px-3 py-2 text-sm" />
            <textarea value={newForm.definicion} onChange={(e) => setNewForm({ ...newForm, definicion: e.target.value })} placeholder="Definicion completa" className="col-span-2 border rounded-lg px-3 py-2 text-sm" rows={2} />
          </div>
          <button onClick={createOcupacion} className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm">Crear ocupacion</button>
        </div>
      )}

      {loading ? (
        <div className="py-8 text-center text-gray-500"><Loader2 className="w-6 h-6 animate-spin inline" /></div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="bg-gray-50 border-b text-gray-500 text-xs">
              <th className="w-8 px-2 py-2.5"></th>
              <th className="text-left px-4 py-2.5">Ocupacion</th>
              <th className="text-center px-4 py-2.5 w-20">ISCO</th>
              <th className="text-left px-4 py-2.5 w-24">Estado</th>
              <th className="text-right px-4 py-2.5 w-16">Freq</th>
              <th className="text-left px-4 py-2.5">Skills esenciales</th>
              <th className="text-center px-4 py-2.5 w-28">Acciones</th>
            </tr></thead>
            <tbody>
              {filtered.map((o) => {
                const expandable = (o.ofertas_ejemplo?.length ?? 0) > 0;
                const isExpanded = expandedId === o.id;
                return (
                  <Fragment key={o.id}>
                    <tr className="border-t border-gray-50 hover:bg-gray-50">
                      <td className="px-2 py-2 text-center">
                        {expandable ? (
                          <button
                            onClick={() => setExpandedId(isExpanded ? null : o.id)}
                            className="text-gray-400 hover:text-gray-700"
                            title={isExpanded ? "Ocultar ofertas" : `Ver ${o.ofertas_ejemplo!.length} ofertas`}
                          >
                            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                          </button>
                        ) : (
                          <span className="text-gray-200">—</span>
                        )}
                      </td>
                      <td className="px-4 py-2">
                        <div className="font-medium text-gray-900">{o.label}</div>
                        {o.definicion && <div className="text-xs text-gray-400 truncate max-w-xs">{o.definicion}</div>}
                      </td>
                      <td className="px-4 py-2 text-center font-mono text-blue-700 font-bold">{o.isco_parent || "—"}</td>
                      <td className="px-4 py-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${ESTADO_COLORS[o.estado] || ""}`}>{o.estado}</span>
                      </td>
                      <td className="px-4 py-2 text-right text-gray-600">{o.frecuencia_mercado}</td>
                      <td className="px-4 py-2">
                        <div className="flex flex-wrap gap-1">
                          {(o.skills_esenciales || []).slice(0, 3).map((s) => (
                            <span key={s} className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">{s}</span>
                          ))}
                          {(o.skills_esenciales || []).length > 3 && (
                            <span className="text-xs text-gray-400">+{o.skills_esenciales.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <div className="flex items-center gap-1 justify-center">
                          {o.estado === "detectada" && (
                            <button onClick={() => changeEstado(o.id, "en_revision")} className="text-xs text-amber-600 hover:bg-amber-50 px-2 py-1 rounded">
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {o.estado === "en_revision" && (
                            <>
                              <button onClick={() => changeEstado(o.id, "catalogada")} className="text-xs text-green-600 hover:bg-green-50 px-2 py-1 rounded">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                              </button>
                              <button onClick={() => changeEstado(o.id, "descartada")} className="text-xs text-red-400 hover:bg-red-50 px-2 py-1 rounded">
                                <XCircle className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                    {isExpanded && expandable && (
                      <tr className="bg-purple-50/30 border-t border-purple-100">
                        <td></td>
                        <td colSpan={6} className="px-4 py-3">
                          <OfertasEjemploTable ocupacion={o} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
          <div className="px-4 py-2 border-t text-xs text-gray-500">{filtered.length} de {total} ocupaciones</div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// Tab: Versiones (G7)
// ============================================================

function VersionesTab({ onRefresh, showMessage }: { onRefresh: () => void; showMessage: (t: "ok" | "error", m: string) => void }) {
  const [versiones, setVersiones] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewForm, setShowNewForm] = useState(false);
  const [newVersion, setNewVersion] = useState({ version: "", nota: "" });
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch("/api/catalogo-mol/versiones");
      if (res.ok) {
        const data = await res.json();
        setVersiones(data.versiones || []);
      }
    } catch {} finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function createVersion() {
    if (!newVersion.version) { alert("Falta version (ej: v1.0)"); return; }
    setCreating(true);
    try {
      const res = await fetch("/api/catalogo-mol/versiones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newVersion),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      showMessage("ok", `Version ${newVersion.version} creada`);
      setShowNewForm(false);
      setNewVersion({ version: "", nota: "" });
      load();
      onRefresh();
    } catch (e: any) {
      showMessage("error", e.message);
    } finally { setCreating(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">Cada version es un corte del catalogo — snapshot de skills y ocupaciones catalogadas en ese momento.</p>
        <button onClick={() => setShowNewForm(true)} className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700">
          <Tag className="w-4 h-4" /> Crear version
        </button>
      </div>

      {showNewForm && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-green-900">Nuevo corte de version</h3>
            <button onClick={() => setShowNewForm(false)}><X className="w-5 h-5 text-gray-400" /></button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input value={newVersion.version} onChange={(e) => setNewVersion({ ...newVersion, version: e.target.value })}
              placeholder="Version (ej: v1.0)" className="border rounded-lg px-3 py-2 text-sm font-mono" />
            <input value={newVersion.nota} onChange={(e) => setNewVersion({ ...newVersion, nota: e.target.value })}
              placeholder="Nota (ej: Primera version con skills IT)" className="border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button onClick={createVersion} disabled={creating}
            className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">
            {creating ? <Loader2 className="w-4 h-4 animate-spin inline mr-1" /> : <Tag className="w-4 h-4 inline mr-1" />}
            Crear corte
          </button>
        </div>
      )}

      {loading ? (
        <div className="py-8 text-center text-gray-500"><Loader2 className="w-6 h-6 animate-spin inline" /></div>
      ) : versiones.length === 0 ? (
        <div className="py-12 text-center text-gray-400">
          <Tag className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No hay versiones todavia. Cataloga skills y ocupaciones, luego crea el primer corte.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {versiones.map((v, i) => (
            <div key={v.id} className={`bg-white rounded-xl shadow-sm border p-5 ${i === 0 ? "border-green-200" : "border-gray-200"}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`text-lg font-bold font-mono ${i === 0 ? "text-green-700" : "text-gray-700"}`}>{v.version}</span>
                  {i === 0 && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Ultima</span>}
                  <span className="text-xs text-gray-400">{new Date(v.fecha_corte).toLocaleDateString("es-AR")}</span>
                </div>
                <span className="text-xs text-gray-400">por {v.creado_por}</span>
              </div>
              {v.nota && <p className="text-sm text-gray-600 mt-2">{v.nota}</p>}
              <div className="flex gap-4 mt-3 text-sm">
                <span className="text-blue-600">{v.total_skills} skills</span>
                <span className="text-purple-600">{v.total_ocupaciones} ocupaciones</span>
                {v.skills_nuevas > 0 && <span className="text-green-600">+{v.skills_nuevas} nuevas</span>}
                {v.ocupaciones_nuevas > 0 && <span className="text-green-600">+{v.ocupaciones_nuevas} ocup nuevas</span>}
                {v.skills_descartadas > 0 && <span className="text-red-400">{v.skills_descartadas} descartadas</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================
// KPI Component
// ============================================================

function KPI({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-700",
    purple: "bg-purple-50 text-purple-700",
    green: "bg-green-50 text-green-700",
    amber: "bg-amber-50 text-amber-700",
    gray: "bg-gray-50 text-gray-700",
  };
  return (
    <div className={`rounded-xl p-3 ${colors[color] || colors.gray}`}>
      <div className="text-xs font-medium opacity-75">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

// ============================================================
// Tabla anidada: ofertas que motivaron una entrada del catálogo
// ============================================================

function OfertasEjemploTable({ ocupacion }: { ocupacion: CatalogoOcupacion }) {
  const ofertas = ocupacion.ofertas_ejemplo ?? [];
  const total = ocupacion.frecuencia_mercado ?? 0;
  const showingAll = ofertas.length >= total;

  if (ofertas.length === 0) {
    return (
      <div className="text-xs text-gray-500 py-2">
        Sin ofertas de ejemplo cargadas para esta entrada.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <h4 className="font-semibold text-purple-900">
          Ofertas que motivaron esta entrada
          <span className="ml-2 text-gray-500 font-normal">
            ({ofertas.length}{showingAll ? "" : ` de ${total}`} mostradas)
          </span>
        </h4>
        {!showingAll && (
          <span className="text-gray-500 italic">
            Sample representativo — el catálogo MOL guarda solo una muestra.
          </span>
        )}
      </div>

      <div className="bg-white rounded border border-gray-200 overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 text-gray-500">
            <tr>
              <th className="text-left px-3 py-1.5 w-32">ID Oferta</th>
              <th className="text-left px-3 py-1.5">Título</th>
              <th className="text-left px-3 py-1.5">ESCO actual (incorrecto)</th>
              <th className="text-left px-3 py-1.5 w-44">Regla aplicada</th>
              <th className="text-center px-3 py-1.5 w-16">Ver</th>
            </tr>
          </thead>
          <tbody>
            {ofertas.map((o) => (
              <tr key={o.id_oferta} className="border-t border-gray-100">
                <td className="px-3 py-1.5 font-mono text-blue-700">{o.id_oferta}</td>
                <td className="px-3 py-1.5 text-gray-800">{o.titulo}</td>
                <td className="px-3 py-1.5 text-gray-600 italic">
                  {o.esco_actual || "—"}
                </td>
                <td className="px-3 py-1.5 text-gray-500 font-mono text-[10px]">
                  {o.regla_aplicada || "—"}
                </td>
                <td className="px-3 py-1.5 text-center">
                  <Link
                    href={`/admin/validacion?id=${o.id_oferta}`}
                    className="inline-flex items-center gap-1 text-blue-600 hover:underline"
                    title="Abrir oferta en validación"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-500">
        Estas ofertas fueron clasificadas mal por el sistema (ESCO oficial no
        tiene targets adecuados). Forman parte del fundamento para crear esta
        entrada en el Catálogo MOL Argentino.
      </p>
    </div>
  );
}
