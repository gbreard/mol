"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Search,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  Loader2,
  RefreshCw,
  FileText,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { supabase } from "@/lib/supabase";
import { ConfigChangelog } from "@/components/ConfigChangelog";

interface Regla {
  id: string;
  nombre: string;
  prioridad: number;
  condicion: Record<string, any>;
  forzar_isco: string;
  forzar_area?: string;
  esco_label?: string;
  activa?: boolean;
}

interface ConfigData {
  source: string;
  version: number;
  updated_by: string | null;
  updated_at: string | null;
  reglas: Record<string, any>;
  changelog: any[];
}

export default function ReglasPage() {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [reglas, setReglas] = useState<Regla[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<Regla>>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [message, setMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [newRegla, setNewRegla] = useState({
    nombre: '',
    tituloContiene: '',
    forzarIsco: '',
    escoLabel: '',
    forzarArea: '',
  });
  const [preview, setPreview] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [sugerencias, setSugerencias] = useState<any[]>([]);
  const [showSugerencias, setShowSugerencias] = useState(false);
  const [loadingSugerencias, setLoadingSugerencias] = useState(false);

  async function loadConfig() {
    setLoading(true);
    try {
      // Try override from Supabase first
      const res = await fetch('/api/config-editor?key=matching_rules_business');
      const data = await res.json();

      if (data.source === 'override' && data.data) {
        setConfig({ source: 'override', version: data.version, updated_by: data.updated_by, updated_at: data.updated_at, reglas: data.data.reglas_forzar_isco || {}, changelog: data.changelog || [] });
        parseReglas(data.data.reglas_forzar_isco || {});
      } else {
        // Load from local JSON
        const localRes = await fetch('/data/matching_rules_business.json');
        if (localRes.ok) {
          const localData = await localRes.json();
          setConfig({ source: 'local', version: 0, updated_by: null, updated_at: null, reglas: localData.reglas_forzar_isco || {}, changelog: [] });
          parseReglas(localData.reglas_forzar_isco || {});
        }
      }
    } catch (e) {
      console.error('Error cargando config:', e);
    } finally {
      setLoading(false);
    }
  }

  function parseReglas(reglasDict: Record<string, any>) {
    const parsed: Regla[] = Object.entries(reglasDict)
      .filter(([key]) => key !== 'descripcion')
      .map(([id, data]: [string, any]) => ({
        id,
        nombre: data.nombre || id,
        prioridad: data.prioridad || 999,
        condicion: data.condicion || {},
        forzar_isco: data.forzar_isco || '',
        forzar_area: data.forzar_area,
        esco_label: data.esco_label,
        activa: data.activa !== false,
      }))
      .sort((a, b) => a.prioridad - b.prioridad);
    setReglas(parsed);
  }

  useEffect(() => { loadConfig(); }, []);

  const filteredReglas = useMemo(() => {
    if (!searchTerm) return reglas;
    const term = searchTerm.toLowerCase();
    return reglas.filter(r =>
      r.id.toLowerCase().includes(term) ||
      r.nombre.toLowerCase().includes(term) ||
      r.forzar_isco.includes(term) ||
      (r.esco_label || '').toLowerCase().includes(term) ||
      JSON.stringify(r.condicion).toLowerCase().includes(term)
    );
  }, [reglas, searchTerm]);

  function startEdit(regla: Regla) {
    setEditingId(regla.id);
    setEditData({ ...regla });
  }

  function cancelEdit() {
    setEditingId(null);
    setEditData({});
  }

  function saveEdit() {
    if (!editingId || !editData) return;
    setReglas(prev => prev.map(r => r.id === editingId ? { ...r, ...editData } as Regla : r));
    setEditingId(null);
    setEditData({});
    setHasChanges(true);
  }

  function deleteRegla(id: string) {
    if (!confirm(`¿Eliminar regla ${id}?`)) return;
    setReglas(prev => prev.filter(r => r.id !== id));
    setHasChanges(true);
  }

  async function loadPreview() {
    if (!newRegla.tituloContiene || !newRegla.forzarIsco) return;
    setLoadingPreview(true);
    try {
      const keywords = newRegla.tituloContiene.split(',').map(k => k.trim()).filter(Boolean);
      const body = keywords.length === 1
        ? { titulo_contiene: keywords[0], forzar_isco: newRegla.forzarIsco }
        : { titulo_contiene_alguno: keywords, forzar_isco: newRegla.forzarIsco };
      const res = await fetch('/api/config-editor/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) setPreview(await res.json());
    } catch (e) {
      console.error('Error preview:', e);
    } finally {
      setLoadingPreview(false);
    }
  }

  async function loadSugerencias() {
    setLoadingSugerencias(true);
    try {
      const res = await fetch('/api/config-editor/preview');
      if (res.ok) setSugerencias(await res.json());
    } catch (e) {
      console.error('Error sugerencias:', e);
    } finally {
      setLoadingSugerencias(false);
    }
  }

  function acceptSugerencia(s: any) {
    setNewRegla({
      nombre: s.patron_titulo?.slice(0, 40) || '',
      tituloContiene: s.patron_titulo || '',
      forzarIsco: s.isco_sugerido || '',
      escoLabel: '',
      forzarArea: '',
    });
    setShowNewForm(true);
    setShowSugerencias(false);
  }

  function addNewRegla() {
    if (!newRegla.nombre || !newRegla.tituloContiene || !newRegla.forzarIsco) {
      alert('Completá nombre, título contiene e ISCO');
      return;
    }
    const id = 'R' + (reglas.length + 1) + '_' + newRegla.nombre.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 30);
    const keywords = newRegla.tituloContiene.split(',').map(k => k.trim().toLowerCase()).filter(Boolean);
    const nueva: Regla = {
      id,
      nombre: newRegla.nombre,
      prioridad: Math.max(...reglas.map(r => r.prioridad), 0) + 1,
      condicion: keywords.length === 1
        ? { titulo_contiene: keywords[0] }
        : { titulo_contiene_alguno: keywords },
      forzar_isco: newRegla.forzarIsco,
      esco_label: newRegla.escoLabel || undefined,
      forzar_area: newRegla.forzarArea || undefined,
      activa: true,
    };
    setReglas(prev => [...prev, nueva]);
    setHasChanges(true);
    setShowNewForm(false);
    setNewRegla({ nombre: '', tituloContiene: '', forzarIsco: '', escoLabel: '', forzarArea: '' });
  }

  function toggleRegla(id: string) {
    setReglas(prev => prev.map(r => r.id === id ? { ...r, activa: !r.activa } : r));
    setHasChanges(true);
  }

  async function saveToSupabase() {
    setSaving(true);
    setMessage(null);
    try {
      // Rebuild the dict structure
      const reglasDict: Record<string, any> = {
        descripcion: "Reglas que fuerzan un codigo ISCO especifico cuando se cumplen las condiciones. Tienen prioridad sobre el matching semantico.",
      };
      reglas.forEach(r => {
        reglasDict[r.id] = {
          nombre: r.nombre,
          prioridad: r.prioridad,
          condicion: r.condicion,
          forzar_isco: r.forzar_isco,
          ...(r.forzar_area && { forzar_area: r.forzar_area }),
          ...(r.esco_label && { esco_label: r.esco_label }),
          ...(r.activa === false && { activa: false }),
        };
      });

      // Load full config to preserve other keys
      const fullRes = await fetch('/api/config-editor?key=matching_rules_business');
      const fullData = await fullRes.json();
      const fullConfig = fullData.data || {};
      fullConfig.reglas_forzar_isco = reglasDict;

      const res = await fetch('/api/config-editor', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config_key: 'matching_rules_business',
          data: fullConfig,
          action_summary: `Editado ${reglas.length} reglas`,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error);
      }

      const result = await res.json();
      setHasChanges(false);
      setMessage({ type: 'ok', text: `Guardado v${result.version} — el pipeline usará estas reglas` });
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    } finally {
      setSaving(false);
    }
  }

  function getCondicionResumen(cond: Record<string, any>): string {
    const parts: string[] = [];
    if (cond.titulo_contiene) parts.push(`titulo: "${cond.titulo_contiene}"`);
    if (cond.titulo_contiene_alguno) parts.push(`titulo∈[${cond.titulo_contiene_alguno.slice(0, 3).join(', ')}${cond.titulo_contiene_alguno.length > 3 ? '...' : ''}]`);
    if (cond.skills_contiene_alguno) parts.push(`skills∈[${cond.skills_contiene_alguno.slice(0, 3).join(', ')}${cond.skills_contiene_alguno.length > 3 ? '...' : ''}]`);
    if (cond.area_funcional) parts.push(`area: ${cond.area_funcional}`);
    if (cond.sector_empresa) parts.push(`sector: ${cond.sector_empresa}`);
    if (cond.seniority) parts.push(`seniority: ${cond.seniority}`);
    return parts.join(' + ') || JSON.stringify(cond).slice(0, 60);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando reglas...</span>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Procesamiento — Reglas de negocio</h1>
          <p className="text-gray-500 text-sm mt-1">
            {reglas.length} reglas — fuente: {config?.source || '?'}
            {config?.version ? ` v${config.version}` : ''}
            {config?.updated_by ? ` — ${config.updated_by}` : ''}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => { setShowSugerencias(!showSugerencias); if (!showSugerencias && sugerencias.length === 0) loadSugerencias(); }}
            className="flex items-center gap-2 bg-amber-500 text-white px-4 py-2 rounded-lg hover:bg-amber-600 text-sm"
          >
            {loadingSugerencias ? <Loader2 className="w-4 h-4 animate-spin" /> : <AlertTriangle className="w-4 h-4" />}
            Sugerencias
          </button>
          <button
            onClick={() => setShowNewForm(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
          >
            <Plus className="w-4 h-4" />
            Nueva regla
          </button>
          {hasChanges && (
            <button
              onClick={saveToSupabase}
              disabled={saving}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Guardar cambios
            </button>
          )}
          <button onClick={loadConfig} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
            <RefreshCw className="w-4 h-4" /> Recargar
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${
          message.type === 'ok' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          {message.type === 'ok' ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {/* Sugerencias automáticas */}
      {showSugerencias && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-amber-900">Reglas sugeridas ({sugerencias.length})</h3>
            <button onClick={() => setShowSugerencias(false)}><X className="w-5 h-5 text-gray-400" /></button>
          </div>
          <p className="text-xs text-amber-700">Basadas en correcciones de analistas y ofertas con matching semántico bajo.</p>
          {sugerencias.length === 0 ? (
            <p className="text-sm text-amber-600 py-4 text-center">{loadingSugerencias ? 'Analizando patrones...' : 'Sin sugerencias por ahora'}</p>
          ) : (
            <div className="space-y-2">
              {sugerencias.map((s: any, i: number) => (
                <div key={i} className="bg-white border border-amber-100 rounded-lg p-3 flex items-start gap-3">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">
                      SI titulo contiene <span className="font-mono bg-amber-100 px-1 rounded">"{s.patron_titulo}"</span>
                      → ISCO <span className="font-mono font-bold text-blue-700">{s.isco_sugerido}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {s.ofertas_afectadas} ofertas afectadas
                      {s.correcciones > 0 && ` · ${s.correcciones} correcciones de ${s.corregido_por || 'analista'}`}
                      {s.tipo_sugerencia === 'semantico_bajo' && ' · matching semántico <50%'}
                    </div>
                    {s.isco_actual && s.isco_actual !== s.isco_sugerido && (
                      <div className="text-xs text-red-600 mt-0.5">ISCO actual: {s.isco_actual} ({s.label_actual}) → cambiaría a {s.isco_sugerido}</div>
                    )}
                  </div>
                  <button onClick={() => acceptSugerencia(s)}
                    className="px-3 py-1.5 bg-amber-500 text-white rounded-lg text-xs hover:bg-amber-600 flex-shrink-0">
                    Usar
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* New rule form */}
      {showNewForm && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-blue-900">Nueva regla de matching</h3>
            <button onClick={() => setShowNewForm(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Nombre de la regla *</label>
              <input value={newRegla.nombre} onChange={e => setNewRegla({...newRegla, nombre: e.target.value})}
                placeholder="Ej: Gerente de Ventas" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Titulo contiene * (separar con coma para varios)</label>
              <input value={newRegla.tituloContiene} onChange={e => setNewRegla({...newRegla, tituloContiene: e.target.value})}
                placeholder="Ej: gerente de ventas, director comercial" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Forzar ISCO *</label>
              <input value={newRegla.forzarIsco} onChange={e => setNewRegla({...newRegla, forzarIsco: e.target.value})}
                placeholder="Ej: 1221" className="w-full border rounded-lg px-3 py-2 text-sm font-mono" />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Label ESCO (opcional)</label>
              <input value={newRegla.escoLabel} onChange={e => setNewRegla({...newRegla, escoLabel: e.target.value})}
                placeholder="Ej: director comercial/directora comercial" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Forzar area (opcional)</label>
              <input value={newRegla.forzarArea} onChange={e => setNewRegla({...newRegla, forzarArea: e.target.value})}
                placeholder="Ej: Comercial" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={loadPreview} disabled={loadingPreview || !newRegla.tituloContiene || !newRegla.forzarIsco}
              className="flex items-center gap-2 bg-amber-500 text-white px-4 py-2 rounded-lg hover:bg-amber-600 text-sm disabled:opacity-50">
              {loadingPreview ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              Preview impacto
            </button>
            <button onClick={addNewRegla} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
              <Plus className="w-4 h-4" /> Agregar regla
            </button>
            <button onClick={() => { setShowNewForm(false); setPreview(null); }} className="px-4 py-2 text-gray-600 text-sm hover:bg-gray-100 rounded-lg">
              Cancelar
            </button>
          </div>

          {/* Preview de impacto */}
          {preview && (
            <div className="bg-white border border-blue-200 rounded-lg p-4 space-y-3">
              <h4 className="font-semibold text-gray-900 text-sm">Impacto de la regla</h4>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-blue-50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-blue-700">{preview.total_afectadas}</div>
                  <div className="text-xs text-blue-600">Ofertas que matchean</div>
                </div>
                <div className="bg-amber-50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-amber-700">{preview.cambiarian}</div>
                  <div className="text-xs text-amber-600">Cambiarían ISCO</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <div className="text-2xl font-bold text-green-700">{preview.ya_correctas}</div>
                  <div className="text-xs text-green-600">Ya tienen ISCO correcto</div>
                </div>
              </div>

              {preview.distribucion_isco_actual?.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 font-medium mb-1">ISCO actual de estas ofertas:</p>
                  <div className="flex flex-wrap gap-2">
                    {preview.distribucion_isco_actual.map((d: any, i: number) => (
                      <span key={i} className={`text-xs px-2 py-1 rounded-full ${d.isco_code === newRegla.forzarIsco ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                        {d.isco_code} ({d.cantidad}) {d.isco_code === newRegla.forzarIsco ? '✓' : '→ cambiaría'}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {preview.ejemplos?.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 font-medium mb-1">Ejemplos (antes → después):</p>
                  <div className="overflow-x-auto max-h-48 overflow-y-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-1 pr-2 text-gray-400">Título</th>
                          <th className="text-center py-1 px-2 text-gray-400">ISCO actual</th>
                          <th className="text-center py-1 px-2 text-gray-400">→</th>
                          <th className="text-center py-1 px-2 text-gray-400">ISCO nuevo</th>
                          <th className="text-center py-1 pl-2 text-gray-400">Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {preview.ejemplos.map((e: any, i: number) => (
                          <tr key={i} className="border-b border-gray-50">
                            <td className="py-1.5 pr-2 text-gray-700 max-w-xs truncate">{e.titulo}</td>
                            <td className="py-1.5 px-2 text-center font-mono">{e.isco_actual || '—'}</td>
                            <td className="py-1.5 px-2 text-center text-gray-300">→</td>
                            <td className="py-1.5 px-2 text-center font-mono font-bold text-blue-700">{e.isco_nuevo}</td>
                            <td className="py-1.5 pl-2 text-center">
                              <span className={`px-1.5 py-0.5 rounded-full ${e.estado === 'CAMBIA' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                                {e.estado}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          <p className="text-xs text-blue-700">Usá "Preview impacto" para ver qué ofertas se afectan antes de agregar.</p>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar por ID, nombre, ISCO, condición..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 border rounded-lg text-sm bg-white"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 text-gray-500 font-medium w-8">#</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">ID / Nombre</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Condición</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium w-20">ISCO</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Label ESCO</th>
                <th className="text-center py-3 px-4 text-gray-500 font-medium w-20">Activa</th>
                <th className="text-center py-3 px-4 text-gray-500 font-medium w-24">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredReglas.map((regla) => {
                const isEditing = editingId === regla.id;

                if (isEditing) {
                  return (
                    <tr key={regla.id} className="border-b border-gray-100 bg-blue-50">
                      <td className="py-2 px-4 text-gray-400">{editData.prioridad}</td>
                      <td className="py-2 px-4">
                        <input value={editData.nombre || ''} onChange={e => setEditData({ ...editData, nombre: e.target.value })}
                          className="w-full border rounded px-2 py-1 text-sm" />
                      </td>
                      <td className="py-2 px-4 text-xs text-gray-500 font-mono">{getCondicionResumen(regla.condicion)}</td>
                      <td className="py-2 px-4">
                        <input value={editData.forzar_isco || ''} onChange={e => setEditData({ ...editData, forzar_isco: e.target.value })}
                          className="w-20 border rounded px-2 py-1 text-sm font-mono" />
                      </td>
                      <td className="py-2 px-4">
                        <input value={editData.esco_label || ''} onChange={e => setEditData({ ...editData, esco_label: e.target.value })}
                          className="w-full border rounded px-2 py-1 text-sm" />
                      </td>
                      <td className="py-2 px-4 text-center">—</td>
                      <td className="py-2 px-4 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <button onClick={saveEdit} className="p-1 text-green-600 hover:bg-green-100 rounded"><Save className="w-4 h-4" /></button>
                          <button onClick={cancelEdit} className="p-1 text-gray-400 hover:bg-gray-100 rounded"><X className="w-4 h-4" /></button>
                        </div>
                      </td>
                    </tr>
                  );
                }

                return (
                  <tr key={regla.id} className={`border-b border-gray-100 hover:bg-gray-50 ${regla.activa === false ? 'opacity-40' : ''}`}>
                    <td className="py-2 px-4 text-gray-400 text-xs">{regla.prioridad}</td>
                    <td className="py-2 px-4">
                      <div className="font-mono text-xs text-gray-400">{regla.id}</div>
                      <div className="text-gray-900">{regla.nombre}</div>
                    </td>
                    <td className="py-2 px-4 text-xs text-gray-600 font-mono max-w-xs truncate" title={JSON.stringify(regla.condicion)}>
                      {getCondicionResumen(regla.condicion)}
                    </td>
                    <td className="py-2 px-4 font-mono font-bold text-blue-700">{regla.forzar_isco}</td>
                    <td className="py-2 px-4 text-gray-700 text-xs max-w-xs truncate">{regla.esco_label || '—'}</td>
                    <td className="py-2 px-4 text-center">
                      <button onClick={() => toggleRegla(regla.id)}
                        className={`w-8 h-5 rounded-full transition-colors ${regla.activa !== false ? 'bg-green-500' : 'bg-gray-300'}`}>
                        <div className={`w-4 h-4 rounded-full bg-white shadow transition-transform ${regla.activa !== false ? 'translate-x-3.5' : 'translate-x-0.5'}`} />
                      </button>
                    </td>
                    <td className="py-2 px-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button onClick={() => startEdit(regla)} className="p-1 text-blue-600 hover:bg-blue-100 rounded"><Edit2 className="w-4 h-4" /></button>
                        <button onClick={() => deleteRegla(regla.id)} className="p-1 text-red-400 hover:bg-red-100 rounded"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 border-t border-gray-100 text-xs text-gray-500">
          Mostrando {filteredReglas.length} de {reglas.length} reglas
        </div>
      </div>

      {/* Changelog */}
      {config && (
        <ConfigChangelog
          changelog={config.changelog}
          version={config.version}
          updatedBy={config.updated_by}
          updatedAt={config.updated_at}
          source={config.source}
        />
      )}
    </div>
  );
}
