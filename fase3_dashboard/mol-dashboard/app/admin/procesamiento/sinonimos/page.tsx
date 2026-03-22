"use client";

import { useState, useEffect, useMemo } from "react";
import { Save, Plus, Trash2, X, Edit2, Loader2, RefreshCw, CheckCircle2, AlertTriangle, Search } from "lucide-react";
import { ConfigChangelog } from "@/components/ConfigChangelog";

interface Sinonimo {
  termino: string;
  isco: string;
  escoLabel: string;
  variantes: string[];
}

export default function SinonimosPage() {
  const [sinonimos, setSinonimos] = useState<Sinonimo[]>([]);
  const [rawConfig, setRawConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [message, setMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [showNewForm, setShowNewForm] = useState(false);
  const [newSin, setNewSin] = useState({ termino: '', isco: '', escoLabel: '', variantes: '' });
  const [editingTermino, setEditingTermino] = useState<string | null>(null);
  const [editFields, setEditFields] = useState({ isco: '', escoLabel: '', variantes: '' });
  const [configMeta, setConfigMeta] = useState<{ source: string; version: number; updated_by: string | null; updated_at: string | null; changelog: any[] }>({ source: 'local', version: 0, updated_by: null, updated_at: null, changelog: [] });

  async function loadConfig() {
    setLoading(true);
    try {
      const overrideRes = await fetch('/api/config-editor?key=sinonimos_argentinos_esco');
      const override = await overrideRes.json();
      let config: any;

      if (override.source === 'override' && override.data) {
        config = override.data;
        setConfigMeta({ source: 'override', version: override.version, updated_by: override.updated_by, updated_at: override.updated_at, changelog: override.changelog || [] });
      } else {
        const localRes = await fetch('/data/sinonimos_argentinos_esco.json');
        config = await localRes.json();
        setConfigMeta({ source: 'local', version: 0, updated_by: null, updated_at: null, changelog: [] });
      }
      setRawConfig(config);

      const ocup = config.ocupaciones_titulo || {};
      const parsed: Sinonimo[] = Object.entries(ocup)
        .filter(([k]) => !k.startsWith('_'))
        .map(([termino, data]: [string, any]) => ({
          termino,
          isco: data.isco_primario || '',
          escoLabel: data.esco_label || '',
          variantes: data.variantes || [],
        }));
      setSinonimos(parsed);
    } catch (e) {
      setMessage({ type: 'error', text: 'Error cargando' });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadConfig(); }, []);

  const filtered = useMemo(() => {
    if (!searchTerm) return sinonimos;
    const t = searchTerm.toLowerCase();
    return sinonimos.filter(s =>
      s.termino.toLowerCase().includes(t) || s.isco.includes(t) ||
      s.escoLabel.toLowerCase().includes(t) || s.variantes.some(v => v.toLowerCase().includes(t))
    );
  }, [sinonimos, searchTerm]);

  function addSinonimo() {
    if (!newSin.termino || !newSin.isco) { alert('Completá término e ISCO'); return; }
    const variantes = newSin.variantes.split(',').map(v => v.trim().toLowerCase()).filter(Boolean);
    setSinonimos(prev => [...prev, {
      termino: newSin.termino.toLowerCase().trim(),
      isco: newSin.isco.trim(),
      escoLabel: newSin.escoLabel.trim(),
      variantes: variantes.length > 0 ? variantes : [newSin.termino.toLowerCase().trim()],
    }]);
    setNewSin({ termino: '', isco: '', escoLabel: '', variantes: '' });
    setShowNewForm(false);
    setHasChanges(true);
  }

  function startEditSinonimo(s: Sinonimo) {
    setEditingTermino(s.termino);
    setEditFields({ isco: s.isco, escoLabel: s.escoLabel, variantes: s.variantes.join(', ') });
  }

  function saveEditSinonimo() {
    if (!editingTermino) return;
    const variantes = editFields.variantes.split(',').map(v => v.trim().toLowerCase()).filter(Boolean);
    setSinonimos(prev => prev.map(s => s.termino === editingTermino ? {
      ...s, isco: editFields.isco, escoLabel: editFields.escoLabel, variantes,
    } : s));
    setEditingTermino(null);
    setHasChanges(true);
  }

  function deleteSinonimo(termino: string) {
    if (!confirm(`¿Eliminar "${termino}"?`)) return;
    setSinonimos(prev => prev.filter(s => s.termino !== termino));
    setHasChanges(true);
  }

  async function saveConfig() {
    if (!rawConfig) return;
    setSaving(true);
    try {
      const newConfig = JSON.parse(JSON.stringify(rawConfig));
      const ocupaciones: Record<string, any> = { _descripcion: newConfig.ocupaciones_titulo?._descripcion || '' };
      sinonimos.forEach(s => {
        ocupaciones[s.termino] = {
          isco_primario: s.isco,
          esco_label: s.escoLabel,
          variantes: s.variantes,
        };
      });
      newConfig.ocupaciones_titulo = ocupaciones;

      const res = await fetch('/api/config-editor', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config_key: 'sinonimos_argentinos_esco', data: newConfig, action_summary: `${sinonimos.length} sinónimos` }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      const result = await res.json();
      setHasChanges(false);
      setMessage({ type: 'ok', text: `Guardado v${result.version}` });
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="flex items-center justify-center h-full"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sinónimos Argentinos → ISCO</h1>
          <p className="text-gray-500 text-sm mt-1">{sinonimos.length} términos argentinos mapeados a códigos ISCO</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowNewForm(true)} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
            <Plus className="w-4 h-4" /> Nuevo sinónimo
          </button>
          {hasChanges && (
            <button onClick={saveConfig} disabled={saving}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm disabled:opacity-50">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Guardar
            </button>
          )}
        </div>
      </div>

      {message && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${message.type === 'ok' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
          {message.type === 'ok' ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {showNewForm && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-blue-900">Nuevo sinónimo argentino</h3>
            <button onClick={() => setShowNewForm(false)}><X className="w-5 h-5 text-gray-400" /></button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Término argentino *</label>
              <input value={newSin.termino} onChange={e => setNewSin({...newSin, termino: e.target.value})}
                placeholder="Ej: cadete" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">ISCO *</label>
              <input value={newSin.isco} onChange={e => setNewSin({...newSin, isco: e.target.value})}
                placeholder="Ej: 9621" className="w-full border rounded-lg px-3 py-2 text-sm font-mono" />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Label ESCO</label>
              <input value={newSin.escoLabel} onChange={e => setNewSin({...newSin, escoLabel: e.target.value})}
                placeholder="Ej: mensajero/mensajera" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Variantes (separar con coma)</label>
              <input value={newSin.variantes} onChange={e => setNewSin({...newSin, variantes: e.target.value})}
                placeholder="Ej: cadete, cadeteria, mensajero" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <button onClick={addSinonimo} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
            <Plus className="w-4 h-4" /> Agregar
          </button>
        </div>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input type="text" placeholder="Buscar término, ISCO, variante..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm" />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b">
              <th className="text-left py-3 px-4 text-gray-500 font-medium">Término</th>
              <th className="text-left py-3 px-4 text-gray-500 font-medium w-20">ISCO</th>
              <th className="text-left py-3 px-4 text-gray-500 font-medium">Label ESCO</th>
              <th className="text-left py-3 px-4 text-gray-500 font-medium">Variantes</th>
              <th className="text-center py-3 px-4 text-gray-500 font-medium w-20">Accion</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(s => {
              const isEditing = editingTermino === s.termino;
              return (
                <tr key={s.termino} className={`border-b border-gray-100 ${isEditing ? 'bg-blue-50' : 'hover:bg-gray-50'}`}>
                  <td className="py-2.5 px-4 font-semibold text-gray-900">{s.termino}</td>
                  <td className="py-2.5 px-4">
                    {isEditing ? (
                      <input value={editFields.isco} onChange={e => setEditFields({...editFields, isco: e.target.value})}
                        className="w-20 border rounded px-2 py-1 text-sm font-mono" />
                    ) : (
                      <span className="font-mono font-bold text-blue-700 cursor-pointer hover:underline" onClick={() => startEditSinonimo(s)}>{s.isco}</span>
                    )}
                  </td>
                  <td className="py-2.5 px-4">
                    {isEditing ? (
                      <input value={editFields.escoLabel} onChange={e => setEditFields({...editFields, escoLabel: e.target.value})}
                        className="w-full border rounded px-2 py-1 text-sm" />
                    ) : (
                      <span className="text-gray-600 text-xs cursor-pointer hover:underline" onClick={() => startEditSinonimo(s)}>{s.escoLabel}</span>
                    )}
                  </td>
                  <td className="py-2.5 px-4">
                    {isEditing ? (
                      <input value={editFields.variantes} onChange={e => setEditFields({...editFields, variantes: e.target.value})}
                        className="w-full border rounded px-2 py-1 text-sm" placeholder="var1, var2, var3" />
                    ) : (
                      <div className="flex flex-wrap gap-1 cursor-pointer" onClick={() => startEditSinonimo(s)}>
                        {s.variantes.map(v => (
                          <span key={v} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{v}</span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    {isEditing ? (
                      <div className="flex items-center gap-1 justify-center">
                        <button onClick={saveEditSinonimo} className="p-1 text-green-600 hover:bg-green-100 rounded"><CheckCircle2 className="w-4 h-4" /></button>
                        <button onClick={() => setEditingTermino(null)} className="p-1 text-gray-400 hover:bg-gray-100 rounded"><X className="w-4 h-4" /></button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1 justify-center">
                        <button onClick={() => startEditSinonimo(s)} className="p-1 text-blue-400 hover:text-blue-600 hover:bg-blue-50 rounded"><Edit2 className="w-4 h-4" /></button>
                        <button onClick={() => deleteSinonimo(s.termino)} className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="px-4 py-2 border-t text-xs text-gray-500">{filtered.length} de {sinonimos.length} sinónimos</div>
      </div>

      <ConfigChangelog
        changelog={configMeta.changelog}
        version={configMeta.version}
        updatedBy={configMeta.updated_by}
        updatedAt={configMeta.updated_at}
        source={configMeta.source}
      />
    </div>
  );
}
