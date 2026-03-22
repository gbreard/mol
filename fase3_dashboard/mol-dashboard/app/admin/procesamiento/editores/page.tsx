"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Save,
  Search,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Edit2,
  X,
  Plus,
  Trash2,
} from "lucide-react";

const CONFIG_TABS = [
  { key: 'nlp_inference_rules', label: 'NLP Inference', description: 'Reglas de inferencia: seniority, área, modalidad' },
  { key: 'sinonimos_argentinos_esco', label: 'Sinónimos ARG', description: 'Mapeo términos argentinos a ISCO/skills ESCO' },
  { key: 'skills_rules', label: 'Skills Rules', description: 'Reglas que fuerzan skills por título' },
  { key: 'oficios_arg', label: 'Oficios ARG', description: 'Diccionario de oficios argentinos' },
  { key: 'nlp_titulo_limpieza', label: 'Limpieza Títulos', description: 'Patrones regex para limpiar títulos' },
];

// Keys internas que no se muestran en el editor
const INTERNAL_KEYS = new Set(['_version', '_descripcion', '_fecha', '_fecha_creacion', '_fecha_actualizacion',
  '_migrado_de', '_fecha_migracion', '_total_items', 'version', 'descripcion', 'fecha_creacion',
  'notas', 'documentacion', 'metadata']);

function isInternalKey(key: string): boolean {
  return INTERNAL_KEYS.has(key) || key.startsWith('_cambios') || key.startsWith('_changelog');
}

export default function EditoresPage() {
  const [activeTab, setActiveTab] = useState(CONFIG_TABS[0].key);
  const [configData, setConfigData] = useState<Record<string, any> | null>(null);
  const [originalData, setOriginalData] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [editingPath, setEditingPath] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const hasChanges = JSON.stringify(configData) !== JSON.stringify(originalData);

  async function loadConfig(key: string) {
    setLoading(true);
    setMessage(null);
    setSearchTerm("");
    setExpandedSections(new Set());
    try {
      // Check override first
      const overrideRes = await fetch(`/api/config-editor?key=${key}`);
      const override = await overrideRes.json();

      if (override.source === 'override' && override.data) {
        setConfigData(override.data);
        setOriginalData(JSON.parse(JSON.stringify(override.data)));
      } else {
        // Load from local JSON
        const localRes = await fetch(`/data/${key}.json`);
        const localData = await localRes.json();
        setConfigData(localData);
        setOriginalData(JSON.parse(JSON.stringify(localData)));
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Error cargando configuración' });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadConfig(activeTab); }, [activeTab]);

  async function saveConfig() {
    if (!configData) return;
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch('/api/config-editor', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config_key: activeTab,
          data: configData,
          action_summary: `Editado desde editores UI`,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      const result = await res.json();
      setOriginalData(JSON.parse(JSON.stringify(configData)));
      setMessage({ type: 'ok', text: `Guardado v${result.version} — el pipeline usará esta config` });
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    } finally {
      setSaving(false);
    }
  }

  function toggleSection(path: string) {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path); else next.add(path);
      return next;
    });
  }

  function updateValue(path: string, value: any) {
    if (!configData) return;
    const keys = path.split('.');
    const newData = JSON.parse(JSON.stringify(configData));
    let obj = newData;
    for (let i = 0; i < keys.length - 1; i++) {
      obj = obj[keys[i]];
    }
    obj[keys[keys.length - 1]] = value;
    setConfigData(newData);
  }

  function deleteKey(path: string) {
    if (!confirm(`¿Eliminar "${path}"?`)) return;
    if (!configData) return;
    const keys = path.split('.');
    const newData = JSON.parse(JSON.stringify(configData));
    let obj = newData;
    for (let i = 0; i < keys.length - 1; i++) {
      obj = obj[keys[i]];
    }
    if (Array.isArray(obj)) {
      obj.splice(parseInt(keys[keys.length - 1]), 1);
    } else {
      delete obj[keys[keys.length - 1]];
    }
    setConfigData(newData);
  }

  function startEdit(path: string, currentValue: any) {
    setEditingPath(path);
    setEditValue(typeof currentValue === 'string' ? currentValue : JSON.stringify(currentValue));
  }

  function saveEdit() {
    if (!editingPath) return;
    try {
      const parsed = editValue.startsWith('{') || editValue.startsWith('[')
        ? JSON.parse(editValue)
        : editValue;
      updateValue(editingPath, parsed);
    } catch {
      updateValue(editingPath, editValue);
    }
    setEditingPath(null);
  }

  // Render a config tree recursively
  function renderNode(obj: any, path: string, depth: number): React.ReactNode[] {
    if (obj === null || obj === undefined) return [];

    if (typeof obj !== 'object') {
      // Leaf value
      const isEditing = editingPath === path;
      const matchesSearch = searchTerm && path.toLowerCase().includes(searchTerm.toLowerCase());

      return [(
        <div key={path} className={`flex items-center gap-2 py-1.5 pl-${Math.min(depth * 4, 16)} ${matchesSearch ? 'bg-yellow-50' : ''}`}>
          <span className="text-xs text-gray-400 font-mono truncate max-w-48">{path.split('.').pop()}</span>
          <span className="text-gray-300">:</span>
          {isEditing ? (
            <div className="flex items-center gap-1 flex-1">
              <input value={editValue} onChange={e => setEditValue(e.target.value)}
                className="flex-1 text-xs border rounded px-2 py-1 font-mono" autoFocus
                onKeyDown={e => { if (e.key === 'Enter') saveEdit(); if (e.key === 'Escape') setEditingPath(null); }} />
              <button onClick={saveEdit} className="p-1 text-green-600 hover:bg-green-100 rounded"><CheckCircle2 className="w-3.5 h-3.5" /></button>
              <button onClick={() => setEditingPath(null)} className="p-1 text-gray-400 hover:bg-gray-100 rounded"><X className="w-3.5 h-3.5" /></button>
            </div>
          ) : (
            <div className="flex items-center gap-1 flex-1 min-w-0">
              <span className="text-xs text-gray-700 font-mono truncate cursor-pointer hover:text-blue-600"
                onClick={() => startEdit(path, obj)} title="Click para editar">
                {typeof obj === 'string' ? `"${obj}"` : String(obj)}
              </span>
              <button onClick={() => deleteKey(path)} className="p-0.5 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100"><Trash2 className="w-3 h-3" /></button>
            </div>
          )}
        </div>
      )];
    }

    if (Array.isArray(obj)) {
      const isExpanded = expandedSections.has(path);
      const matchesSearch = !searchTerm || JSON.stringify(obj).toLowerCase().includes(searchTerm.toLowerCase());
      if (!matchesSearch) return [];

      return [(
        <div key={path} className="group">
          <div className={`flex items-center gap-1 py-1.5 cursor-pointer hover:bg-gray-50 rounded`}
            style={{ paddingLeft: `${depth * 16}px` }}
            onClick={() => toggleSection(path)}>
            {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />}
            <span className="text-xs font-medium text-gray-700">{path.split('.').pop()}</span>
            <span className="text-xs text-gray-400">[{obj.length} items]</span>
          </div>
          {isExpanded && obj.map((item, i) => renderNode(item, `${path}.${i}`, depth + 1)).flat()}
        </div>
      )];
    }

    // Object
    const entries = Object.entries(obj).filter(([k]) => !isInternalKey(k));
    const isExpanded = expandedSections.has(path) || depth === 0;
    const matchesSearch = !searchTerm || JSON.stringify(obj).toLowerCase().includes(searchTerm.toLowerCase());
    if (!matchesSearch && depth > 0) return [];

    if (depth === 0) {
      // Top level — always show
      return entries.map(([key, value]) => renderNode(value, key, 1)).flat();
    }

    return [(
      <div key={path} className="group">
        <div className={`flex items-center gap-1 py-1.5 cursor-pointer hover:bg-gray-50 rounded`}
          style={{ paddingLeft: `${depth * 16}px` }}
          onClick={() => toggleSection(path)}>
          {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />}
          <span className="text-xs font-semibold text-gray-800">{path.split('.').pop()}</span>
          <span className="text-xs text-gray-400">({entries.length > 0 ? `${Object.keys(obj).length} keys` : 'vacío'})</span>
          <button onClick={(e) => { e.stopPropagation(); deleteKey(path); }}
            className="ml-auto p-0.5 text-gray-300 hover:text-red-500"><Trash2 className="w-3 h-3" /></button>
        </div>
        {isExpanded && entries.map(([key, value]) => renderNode(value, `${path}.${key}`, depth + 1)).flat()}
      </div>
    )];
  }

  const tabInfo = CONFIG_TABS.find(t => t.key === activeTab);

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Procesamiento — Editores</h1>
          <p className="text-gray-500 text-sm mt-1">{tabInfo?.description}</p>
        </div>
        <div className="flex items-center gap-2">
          {hasChanges && (
            <button onClick={saveConfig} disabled={saving}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm disabled:opacity-50">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Guardar cambios
            </button>
          )}
          <button onClick={() => loadConfig(activeTab)} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
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

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 overflow-x-auto">
        {CONFIG_TABS.map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input type="text" placeholder="Buscar clave o valor..."
          value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm" />
      </div>

      {/* Editor */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 max-h-[600px] overflow-y-auto">
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : configData ? (
          <div className="font-mono text-sm">
            {renderNode(configData, '', 0)}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-8">Sin datos</p>
        )}
      </div>
    </div>
  );
}
