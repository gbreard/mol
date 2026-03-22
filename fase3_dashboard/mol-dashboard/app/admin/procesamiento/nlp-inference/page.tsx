"use client";

import { useState, useEffect, useMemo } from "react";
import { Save, Plus, Trash2, X, Edit2, Loader2, RefreshCw, CheckCircle2, AlertTriangle, Search } from "lucide-react";

interface InferenceRule {
  keyword: string;
  value: string;
  section: string; // modalidad, nivel_seniority, area_funcional
}

const SECTIONS = [
  { key: 'modalidad', label: 'Modalidad', placeholder: 'remoto, hibrido, presencial' },
  { key: 'nivel_seniority', label: 'Seniority', placeholder: 'junior, semisenior, senior, manager' },
  { key: 'area_funcional', label: 'Area funcional', placeholder: 'Tecnologia, Comercial, RRHH, etc.' },
];

export default function NlpInferencePage() {
  const [rules, setRules] = useState<InferenceRule[]>([]);
  const [rawConfig, setRawConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [message, setMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeSection, setActiveSection] = useState('modalidad');
  const [newKeyword, setNewKeyword] = useState("");
  const [newValue, setNewValue] = useState("");
  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [editKw, setEditKw] = useState("");
  const [editVal, setEditVal] = useState("");

  async function loadConfig() {
    setLoading(true);
    try {
      const overrideRes = await fetch('/api/config-editor?key=nlp_inference_rules');
      const override = await overrideRes.json();
      let config: any;

      if (override.source === 'override' && override.data) {
        config = override.data;
      } else {
        const localRes = await fetch('/data/nlp_inference_rules.json');
        config = await localRes.json();
      }

      setRawConfig(config);
      parseRules(config);
    } catch (e) {
      setMessage({ type: 'error', text: 'Error cargando configuración' });
    } finally {
      setLoading(false);
    }
  }

  function parseRules(config: any) {
    const parsed: InferenceRule[] = [];
    for (const section of SECTIONS) {
      const sectionData = config[section.key];
      if (!sectionData) continue;

      // Each section has subsections with keywords
      const keywords = sectionData.keywords || {};
      for (const [value, kws] of Object.entries(keywords)) {
        if (value.startsWith('_')) continue;
        const keywordList = Array.isArray(kws) ? kws : [kws];
        for (const kw of keywordList) {
          parsed.push({ keyword: String(kw), value, section: section.key });
        }
      }

      // Also check forzar_* patterns
      const forzar = sectionData[`forzar_${section.key}`] || sectionData.forzar || {};
      for (const [kw, val] of Object.entries(forzar)) {
        if (kw.startsWith('_')) continue;
        parsed.push({ keyword: kw, value: String(val), section: section.key });
      }
    }
    setRules(parsed);
  }

  useEffect(() => { loadConfig(); }, []);

  const filteredRules = useMemo(() => {
    return rules
      .filter(r => r.section === activeSection)
      .filter(r => !searchTerm ||
        r.keyword.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.value.toLowerCase().includes(searchTerm.toLowerCase())
      );
  }, [rules, activeSection, searchTerm]);

  function addRule() {
    if (!newKeyword || !newValue) return;
    setRules(prev => [...prev, { keyword: newKeyword.toLowerCase().trim(), value: newValue.trim(), section: activeSection }]);
    setNewKeyword("");
    setNewValue("");
    setHasChanges(true);
  }

  function startEditRule(idx: number, r: InferenceRule) {
    setEditingIdx(idx);
    setEditKw(r.keyword);
    setEditVal(r.value);
  }

  function saveEditRule() {
    if (editingIdx === null) return;
    const target = filteredRules[editingIdx];
    setRules(prev => prev.map(r =>
      r.keyword === target.keyword && r.value === target.value && r.section === activeSection
        ? { ...r, keyword: editKw.toLowerCase().trim(), value: editVal.trim() }
        : r
    ));
    setEditingIdx(null);
    setHasChanges(true);
  }

  function deleteRule(keyword: string, value: string) {
    setRules(prev => prev.filter(r => !(r.keyword === keyword && r.value === value && r.section === activeSection)));
    setHasChanges(true);
  }

  async function saveConfig() {
    if (!rawConfig) return;
    setSaving(true);
    setMessage(null);
    try {
      // Rebuild keywords by section
      const newConfig = JSON.parse(JSON.stringify(rawConfig));
      for (const section of SECTIONS) {
        if (!newConfig[section.key]) newConfig[section.key] = {};
        const sectionRules = rules.filter(r => r.section === section.key);

        // Group by value
        const byValue: Record<string, string[]> = {};
        sectionRules.forEach(r => {
          if (!byValue[r.value]) byValue[r.value] = [];
          byValue[r.value].push(r.keyword);
        });

        newConfig[section.key].keywords = byValue;
      }

      const res = await fetch('/api/config-editor', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config_key: 'nlp_inference_rules',
          data: newConfig,
          action_summary: `Editado reglas NLP inference`,
        }),
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

  if (loading) {
    return <div className="flex items-center justify-center h-full"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  }

  const sectionInfo = SECTIONS.find(s => s.key === activeSection);

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">NLP Inference Rules</h1>
          <p className="text-gray-500 text-sm mt-1">Si el titulo contiene keyword → asignar {activeSection}</p>
        </div>
        <div className="flex items-center gap-2">
          {hasChanges && (
            <button onClick={saveConfig} disabled={saving}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm disabled:opacity-50">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Guardar
            </button>
          )}
          <button onClick={loadConfig} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {message && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${message.type === 'ok' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
          {message.type === 'ok' ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {/* Section tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {SECTIONS.map(s => (
          <button key={s.key} onClick={() => { setActiveSection(s.key); setSearchTerm(""); }}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeSection === s.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {s.label} ({rules.filter(r => r.section === s.key).length})
          </button>
        ))}
      </div>

      {/* Add new rule */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-xs text-blue-700 font-medium mb-2">Agregar regla: si titulo contiene keyword → {activeSection} = valor</p>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="text-xs text-gray-600 block mb-1">Keyword</label>
            <input value={newKeyword} onChange={e => setNewKeyword(e.target.value)}
              placeholder="Ej: home office" className="w-full border rounded px-3 py-2 text-sm"
              onKeyDown={e => { if (e.key === 'Enter') addRule(); }} />
          </div>
          <div className="flex-1">
            <label className="text-xs text-gray-600 block mb-1">{sectionInfo?.label}</label>
            <input value={newValue} onChange={e => setNewValue(e.target.value)}
              placeholder={sectionInfo?.placeholder} className="w-full border rounded px-3 py-2 text-sm"
              onKeyDown={e => { if (e.key === 'Enter') addRule(); }} />
          </div>
          <button onClick={addRule} className="flex items-center gap-1 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
            <Plus className="w-4 h-4" /> Agregar
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input type="text" placeholder="Buscar keyword o valor..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm" />
      </div>

      {/* Rules table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b">
              <th className="text-left py-3 px-4 text-gray-500 font-medium">Keyword</th>
              <th className="text-left py-3 px-4 text-gray-500 font-medium">{sectionInfo?.label}</th>
              <th className="text-center py-3 px-4 text-gray-500 font-medium w-20">Accion</th>
            </tr>
          </thead>
          <tbody>
            {filteredRules.map((r, i) => {
              const isEditing = editingIdx === i;
              return (
                <tr key={`${r.keyword}-${r.value}-${i}`} className={`border-b border-gray-100 ${isEditing ? 'bg-blue-50' : 'hover:bg-gray-50'}`}>
                  <td className="py-2.5 px-4">
                    {isEditing ? (
                      <input value={editKw} onChange={e => setEditKw(e.target.value)}
                        className="w-full border rounded px-2 py-1 text-sm font-mono"
                        onKeyDown={e => { if (e.key === 'Enter') saveEditRule(); if (e.key === 'Escape') setEditingIdx(null); }} />
                    ) : (
                      <span className="font-mono text-gray-900 cursor-pointer hover:underline" onClick={() => startEditRule(i, r)}>{r.keyword}</span>
                    )}
                  </td>
                  <td className="py-2.5 px-4">
                    {isEditing ? (
                      <input value={editVal} onChange={e => setEditVal(e.target.value)}
                        className="w-full border rounded px-2 py-1 text-sm"
                        onKeyDown={e => { if (e.key === 'Enter') saveEditRule(); if (e.key === 'Escape') setEditingIdx(null); }} />
                    ) : (
                      <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full cursor-pointer hover:bg-blue-200" onClick={() => startEditRule(i, r)}>{r.value}</span>
                    )}
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    {isEditing ? (
                      <div className="flex items-center gap-1 justify-center">
                        <button onClick={saveEditRule} className="p-1 text-green-600 hover:bg-green-100 rounded"><CheckCircle2 className="w-4 h-4" /></button>
                        <button onClick={() => setEditingIdx(null)} className="p-1 text-gray-400 hover:bg-gray-100 rounded"><X className="w-4 h-4" /></button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1 justify-center">
                        <button onClick={() => startEditRule(i, r)} className="p-1 text-blue-400 hover:text-blue-600 hover:bg-blue-50 rounded"><Edit2 className="w-4 h-4" /></button>
                        <button onClick={() => deleteRule(r.keyword, r.value)} className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="px-4 py-2 border-t text-xs text-gray-500">
          {filteredRules.length} reglas en {sectionInfo?.label}
        </div>
      </div>
    </div>
  );
}
