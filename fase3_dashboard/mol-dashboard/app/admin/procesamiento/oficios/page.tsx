"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Save, Plus, Trash2, X, Loader2, RefreshCw, CheckCircle2,
  AlertTriangle, Search, ChevronDown, ChevronRight,
} from "lucide-react";
import { ConfigChangelog } from "@/components/ConfigChangelog";

interface Categoria {
  id: string;
  descripcion: string;
  items: string[];
}

export default function OficiosPage() {
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [rawConfig, setRawConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "error"; text: string } | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedCats, setExpandedCats] = useState<Set<string>>(new Set());
  const [showNewCatForm, setShowNewCatForm] = useState(false);
  const [newCat, setNewCat] = useState({ id: "", descripcion: "" });
  const [addingItemTo, setAddingItemTo] = useState<string | null>(null);
  const [newItem, setNewItem] = useState("");
  const [configMeta, setConfigMeta] = useState<{ source: string; version: number; updated_by: string | null; updated_at: string | null; changelog: any[] }>({ source: "local", version: 0, updated_by: null, updated_at: null, changelog: [] });

  async function loadConfig() {
    setLoading(true);
    try {
      const overrideRes = await fetch("/api/config-editor?key=oficios_arg");
      const override = await overrideRes.json();
      let config: any;

      if (override.source === "override" && override.data) {
        config = override.data;
        setConfigMeta({ source: "override", version: override.version, updated_by: override.updated_by, updated_at: override.updated_at, changelog: override.changelog || [] });
      } else {
        const localRes = await fetch("/data/oficios_arg.json");
        config = await localRes.json();
        setConfigMeta({ source: "local", version: 0, updated_by: null, updated_at: null, changelog: [] });
      }
      setRawConfig(config);

      const oficios = config.oficios || {};
      const parsed: Categoria[] = Object.entries(oficios).map(
        ([id, data]: [string, any]) => ({
          id,
          descripcion: data._descripcion || "",
          items: [...(data.items || [])],
        })
      );
      setCategorias(parsed);
      setExpandedCats(new Set(parsed.map((c) => c.id)));
    } catch (e) {
      setMessage({ type: "error", text: "Error cargando oficios" });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadConfig(); }, []);

  const totalItems = useMemo(() => categorias.reduce((sum, c) => sum + c.items.length, 0), [categorias]);

  const filtered = useMemo(() => {
    if (!searchTerm) return categorias;
    const t = searchTerm.toLowerCase();
    return categorias
      .map((c) => ({
        ...c,
        items: c.items.filter((i) => i.toLowerCase().includes(t)),
      }))
      .filter(
        (c) =>
          c.items.length > 0 ||
          c.id.toLowerCase().includes(t) ||
          c.descripcion.toLowerCase().includes(t)
      );
  }, [categorias, searchTerm]);

  function toggleCat(id: string) {
    setExpandedCats((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function addCategoria() {
    if (!newCat.id) { alert("Completar ID de categoría"); return; }
    const id = newCat.id.toLowerCase().replace(/[^a-z0-9_]/g, "_");
    if (categorias.some((c) => c.id === id)) { alert("Ya existe esa categoría"); return; }
    setCategorias((prev) => [...prev, { id, descripcion: newCat.descripcion, items: [] }]);
    setExpandedCats((prev) => new Set([...prev, id]));
    setNewCat({ id: "", descripcion: "" });
    setShowNewCatForm(false);
    setHasChanges(true);
  }

  function deleteCategoria(id: string) {
    if (!confirm(`¿Eliminar categoría "${id}" con todos sus items?`)) return;
    setCategorias((prev) => prev.filter((c) => c.id !== id));
    setHasChanges(true);
  }

  function addItem(catId: string) {
    if (!newItem.trim()) return;
    const items = newItem.split(",").map((i) => i.trim().toLowerCase()).filter(Boolean);
    setCategorias((prev) =>
      prev.map((c) =>
        c.id === catId
          ? { ...c, items: [...c.items, ...items.filter((i) => !c.items.includes(i))] }
          : c
      )
    );
    setNewItem("");
    setAddingItemTo(null);
    setHasChanges(true);
  }

  function deleteItem(catId: string, item: string) {
    setCategorias((prev) =>
      prev.map((c) =>
        c.id === catId ? { ...c, items: c.items.filter((i) => i !== item) } : c
      )
    );
    setHasChanges(true);
  }

  async function saveConfig() {
    if (!rawConfig) return;
    setSaving(true);
    try {
      const newConfig = JSON.parse(JSON.stringify(rawConfig));
      const oficios: Record<string, any> = {};
      categorias.forEach((c) => {
        oficios[c.id] = {
          _descripcion: c.descripcion,
          items: c.items,
        };
      });
      newConfig.oficios = oficios;
      newConfig._total_items = categorias.reduce((sum, c) => sum + c.items.length, 0);

      const res = await fetch("/api/config-editor", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          config_key: "oficios_arg",
          data: newConfig,
          action_summary: `${categorias.length} categorías, ${newConfig._total_items} items`,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error);
      const result = await res.json();
      setHasChanges(false);
      setMessage({ type: "ok", text: `Guardado v${result.version}` });
    } catch (e: any) {
      setMessage({ type: "error", text: e.message });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Oficios Argentinos</h1>
          <p className="text-gray-500 text-sm mt-1">
            {categorias.length} categorías, {totalItems} oficios
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNewCatForm(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
          >
            <Plus className="w-4 h-4" /> Nueva categoría
          </button>
          {hasChanges && (
            <button
              onClick={saveConfig}
              disabled={saving}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Guardar
            </button>
          )}
          <button
            onClick={loadConfig}
            className="flex items-center gap-2 text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${
            message.type === "ok"
              ? "bg-green-50 border-green-200 text-green-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          {message.type === "ok" ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {/* New category form */}
      {showNewCatForm && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-blue-900">Nueva categoría</h3>
            <button onClick={() => setShowNewCatForm(false)}>
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">ID (snake_case) *</label>
              <input
                value={newCat.id}
                onChange={(e) => setNewCat({ ...newCat, id: e.target.value })}
                placeholder="Ej: comercio_exterior"
                className="w-full border rounded-lg px-3 py-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium block mb-1">Descripción</label>
              <input
                value={newCat.descripcion}
                onChange={(e) => setNewCat({ ...newCat, descripcion: e.target.value })}
                placeholder="Ej: Oficios de comercio exterior y aduanas"
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>
          <button
            onClick={addCategoria}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm"
          >
            <Plus className="w-4 h-4" /> Crear
          </button>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar oficio..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm"
        />
      </div>

      {/* Categories */}
      <div className="space-y-3">
        {filtered.map((cat) => {
          const isExpanded = expandedCats.has(cat.id);
          const isAddingItem = addingItemTo === cat.id;

          return (
            <div key={cat.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              {/* Category header */}
              <div
                className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50"
                onClick={() => toggleCat(cat.id)}
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <span className="font-semibold text-gray-900">{cat.id.replace(/_/g, " ")}</span>
                  <span className="text-xs text-gray-400 ml-2">({cat.items.length})</span>
                  {cat.descripcion && (
                    <span className="text-xs text-gray-500 ml-2">— {cat.descripcion}</span>
                  )}
                </div>
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => { setAddingItemTo(isAddingItem ? null : cat.id); setNewItem(""); }}
                    className="p-1 text-blue-500 hover:bg-blue-50 rounded"
                    title="Agregar items"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteCategoria(cat.id)}
                    className="p-1 text-red-400 hover:bg-red-50 rounded"
                    title="Eliminar categoría"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Add item inline */}
              {isAddingItem && (
                <div className="px-4 py-2 bg-blue-50 border-t border-blue-100 flex gap-2">
                  <input
                    value={newItem}
                    onChange={(e) => setNewItem(e.target.value)}
                    placeholder="Nuevo oficio (separar con coma para varios)"
                    className="flex-1 border rounded-lg px-3 py-1.5 text-sm"
                    onKeyDown={(e) => e.key === "Enter" && addItem(cat.id)}
                    autoFocus
                  />
                  <button
                    onClick={() => addItem(cat.id)}
                    className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    Agregar
                  </button>
                  <button
                    onClick={() => setAddingItemTo(null)}
                    className="px-2 py-1.5 text-gray-400 hover:bg-gray-100 rounded-lg"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Items */}
              {isExpanded && (
                <div className="px-4 pb-3 pt-1 flex flex-wrap gap-1.5">
                  {cat.items.map((item) => (
                    <span
                      key={item}
                      className="group inline-flex items-center gap-1 text-xs bg-gray-100 text-gray-700 pl-2.5 pr-1 py-1 rounded-full hover:bg-gray-200"
                    >
                      {item}
                      <button
                        onClick={() => deleteItem(cat.id, item)}
                        className="text-gray-400 hover:text-red-500 p-0.5 rounded-full"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                  {cat.items.length === 0 && (
                    <span className="text-xs text-gray-400 italic">Sin items — usá + para agregar</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="text-xs text-gray-400 text-center">
        {filtered.reduce((s, c) => s + c.items.length, 0)} items en {filtered.length} categorías
        {searchTerm && ` (filtrado de ${totalItems} total)`}
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
