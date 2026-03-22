"use client";

import { useState, useEffect } from "react";
import {
  Play,
  RefreshCw,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Globe,
  AlertTriangle,
  Terminal,
  Cloud,
  Database,
  Calendar,
  Save,
} from "lucide-react";
import { supabase } from "@/lib/supabase";

interface Schedule {
  id: number;
  portal: string;
  dias_semana: number[];
  hora_utc: string;
  activo: boolean;
  updated_by: string | null;
  updated_at: string;
}

const DIAS_SEMANA = [
  { value: 1, label: 'Lun' },
  { value: 2, label: 'Mar' },
  { value: 3, label: 'Mié' },
  { value: 4, label: 'Jue' },
  { value: 5, label: 'Vie' },
  { value: 6, label: 'Sáb' },
  { value: 7, label: 'Dom' },
];

// UTC a Argentina (UTC-3)
function utcToArg(utcTime: string): string {
  const [h, m] = utcTime.split(':').map(Number);
  const argH = ((h - 3) + 24) % 24;
  return `${argH.toString().padStart(2, '0')}:${(m || 0).toString().padStart(2, '0')}`;
}

function argToUtc(argTime: string): string {
  const [h, m] = argTime.split(':').map(Number);
  const utcH = ((h + 3) % 24);
  return `${utcH.toString().padStart(2, '0')}:${(m || 0).toString().padStart(2, '0')}`;
}

interface Command {
  id: string;
  comando: string;
  params: Record<string, any>;
  estado: string;
  creado_por: string;
  log_preview: string | null;
  resultado: Record<string, any> | null;
  error_mensaje: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duracion_seg: number | null;
}

const PORTALES = ['bumeran', 'zonajobs', 'computrabajo', 'indeed', 'portalempleo', 'caba'];

const COMANDO_LABELS: Record<string, { label: string; icon: any; description: string }> = {
  lanzar_portal: { label: 'Lanzar portal', icon: Globe, description: 'Scraping de un portal específico' },
  lanzar_todos: { label: 'Lanzar todos', icon: Play, description: 'Scraping de todos los portales (~6h)' },
  sync_vps_local: { label: 'Sync VPS → Local', icon: Database, description: 'Exportar ofertas nuevas del VPS' },
};

const ESTADO_CONFIG: Record<string, { color: string; icon: any; label: string }> = {
  pendiente: { color: 'bg-amber-100 text-amber-700', icon: Clock, label: 'Pendiente' },
  ejecutando: { color: 'bg-blue-100 text-blue-700', icon: Loader2, label: 'Ejecutando' },
  completado: { color: 'bg-green-100 text-green-700', icon: CheckCircle2, label: 'Completado' },
  error: { color: 'bg-red-100 text-red-700', icon: XCircle, label: 'Error' },
  cancelado: { color: 'bg-gray-100 text-gray-700', icon: XCircle, label: 'Cancelado' },
};

export default function ComandosPage() {
  const [commands, setCommands] = useState<Command[]>([]);
  const [schedule, setSchedule] = useState<Schedule[]>([]);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);
  const [savingSchedule, setSavingSchedule] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState<string | null>(null);
  const [expandedLog, setExpandedLog] = useState<string | null>(null);

  async function loadSchedule() {
    if (!supabase) return;
    const { data } = await supabase.rpc('get_scraping_schedule');
    if (data) setSchedule(data as Schedule[]);
  }

  async function saveSchedule(sched: Schedule) {
    setSavingSchedule(true);
    try {
      const res = await fetch('/api/scraping-schedule', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: sched.id,
          dias_semana: sched.dias_semana,
          hora_utc: sched.hora_utc,
          activo: sched.activo,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        alert(`Error: ${err.error}`);
        return;
      }
      await loadSchedule();
      setEditingSchedule(null);
    } finally {
      setSavingSchedule(false);
    }
  }

  async function loadCommands() {
    if (!supabase) return;
    const { data, error } = await supabase.rpc('get_scraping_commands', { p_limit: 20 });
    if (!error && data) setCommands(data as Command[]);
    setLoading(false);
  }

  useEffect(() => {
    loadSchedule();
    loadCommands();
    // Auto-refresh cada 30s si hay comandos ejecutando
    const interval = setInterval(() => {
      if (commands.some(c => c.estado === 'pendiente' || c.estado === 'ejecutando')) {
        loadCommands();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  async function sendCommand(comando: string, params?: Record<string, any>) {
    if (!supabase) return;
    setSending(comando);

    try {
      const res = await fetch('/api/scraping-commands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comando, params }),
      });

      if (!res.ok) {
        const err = await res.json();
        alert(`Error: ${err.error}`);
        return;
      }

      await loadCommands();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    } finally {
      setSending(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando comandos...</span>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scraping — Comandos</h1>
          <p className="text-gray-500 text-sm mt-1">Control remoto del VPS de scraping</p>
        </div>
        <button
          onClick={loadCommands}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </div>

      {/* Calendario de scraping */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-blue-600" />
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Calendario de scraping</h2>
        </div>

        {schedule.length === 0 ? (
          <p className="text-sm text-gray-400">Sin calendario configurado</p>
        ) : (
          <div className="space-y-3">
            {schedule.map(sched => {
              const isEditing = editingSchedule?.id === sched.id;
              const current = isEditing ? editingSchedule! : sched;
              const argHora = utcToArg(current.hora_utc);

              return (
                <div key={sched.id} className={`border rounded-lg p-4 ${sched.activo ? 'border-gray-200' : 'border-gray-100 bg-gray-50 opacity-60'}`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 capitalize">{sched.portal}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${sched.activo ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-500'}`}>
                        {sched.activo ? 'Activo' : 'Pausado'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {isEditing ? (
                        <>
                          <button
                            onClick={() => saveSchedule(current)}
                            disabled={savingSchedule}
                            className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs hover:bg-blue-700 disabled:opacity-50"
                          >
                            {savingSchedule ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                            Guardar
                          </button>
                          <button onClick={() => setEditingSchedule(null)} className="text-xs text-gray-500 hover:text-gray-700">
                            Cancelar
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setEditingSchedule({ ...sched })}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Editar
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Días de la semana */}
                  <div className="flex items-center gap-1 mb-2">
                    <span className="text-xs text-gray-500 mr-2">Dias:</span>
                    {DIAS_SEMANA.map(dia => {
                      const selected = current.dias_semana.includes(dia.value);
                      return (
                        <button
                          key={dia.value}
                          disabled={!isEditing}
                          onClick={() => {
                            if (!isEditing) return;
                            const next = selected
                              ? current.dias_semana.filter(d => d !== dia.value)
                              : [...current.dias_semana, dia.value].sort();
                            setEditingSchedule({ ...current, dias_semana: next });
                          }}
                          className={`w-9 h-9 rounded-lg text-xs font-medium transition-colors ${
                            selected
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-400'
                          } ${isEditing ? 'cursor-pointer hover:opacity-80' : 'cursor-default'}`}
                        >
                          {dia.label}
                        </button>
                      );
                    })}
                  </div>

                  {/* Hora */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Hora (ARG):</span>
                    {isEditing ? (
                      <input
                        type="time"
                        value={argHora}
                        onChange={(e) => setEditingSchedule({ ...current, hora_utc: argToUtc(e.target.value) })}
                        className="text-sm border rounded px-2 py-1"
                      />
                    ) : (
                      <span className="text-sm font-medium text-gray-900">{argHora}hs</span>
                    )}

                    {/* Toggle activo */}
                    {isEditing && (
                      <label className="flex items-center gap-1.5 ml-4 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={current.activo}
                          onChange={(e) => setEditingSchedule({ ...current, activo: e.target.checked })}
                          className="rounded"
                        />
                        <span className="text-xs text-gray-600">Activo</span>
                      </label>
                    )}
                  </div>

                  {sched.updated_by && (
                    <p className="text-xs text-gray-400 mt-2">
                      Editado por {sched.updated_by?.split('@')[0]} — {new Date(sched.updated_at).toLocaleDateString('es-AR')}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Acciones rápidas */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Acciones</h2>

        {/* Lanzar por portal */}
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">Lanzar scraping por portal:</p>
          <div className="flex flex-wrap gap-2">
            {PORTALES.map(portal => (
              <button
                key={portal}
                onClick={() => sendCommand('lanzar_portal', { portal })}
                disabled={sending !== null}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50 text-sm transition-colors disabled:opacity-50"
              >
                {sending === 'lanzar_portal' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4 text-gray-500" />}
                <span className="capitalize">{portal}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Otros comandos */}
        <div className="flex flex-wrap gap-3">
          {Object.entries(COMANDO_LABELS)
            .filter(([cmd]) => cmd !== 'lanzar_portal')
            .map(([cmd, config]) => {
              const Icon = config.icon;
              return (
                <button
                  key={cmd}
                  onClick={() => {
                    if (cmd === 'lanzar_todos' && !confirm('Esto lanza scraping de todos los portales (~6h). ¿Continuar?')) return;
                    sendCommand(cmd);
                  }}
                  disabled={sending !== null}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50 text-sm transition-colors disabled:opacity-50"
                >
                  {sending === cmd ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon className="w-4 h-4 text-gray-500" />}
                  <div className="text-left">
                    <div className="font-medium">{config.label}</div>
                    <div className="text-xs text-gray-400">{config.description}</div>
                  </div>
                </button>
              );
            })}
        </div>
      </div>

      {/* Historial de comandos */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Historial ({commands.length})
        </h2>

        {commands.length === 0 ? (
          <p className="text-sm text-gray-400">No hay comandos registrados</p>
        ) : (
          <div className="space-y-3">
            {commands.map(cmd => {
              const estadoCfg = ESTADO_CONFIG[cmd.estado] || ESTADO_CONFIG.pendiente;
              const EstadoIcon = estadoCfg.icon;
              const cmdLabel = COMANDO_LABELS[cmd.comando]?.label || cmd.comando;
              const portalParam = cmd.params?.portal;
              const isExpanded = expandedLog === cmd.id;

              return (
                <div key={cmd.id} className="border border-gray-100 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    {/* Estado */}
                    <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${estadoCfg.color}`}>
                      <EstadoIcon className={`w-3.5 h-3.5 ${cmd.estado === 'ejecutando' ? 'animate-spin' : ''}`} />
                      {estadoCfg.label}
                    </span>

                    {/* Comando */}
                    <span className="text-sm font-medium text-gray-900">
                      {cmdLabel}{portalParam ? `: ${portalParam}` : ''}
                    </span>

                    {/* Duración */}
                    {cmd.duracion_seg !== null && (
                      <span className="text-xs text-gray-400">
                        {cmd.duracion_seg < 60 ? `${cmd.duracion_seg}s` : `${Math.round(cmd.duracion_seg / 60)}min`}
                      </span>
                    )}

                    {/* Timestamp */}
                    <span className="ml-auto text-xs text-gray-400">
                      {new Date(cmd.created_at).toLocaleString('es-AR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                    </span>

                    {/* Por quién */}
                    <span className="text-xs text-gray-400">{cmd.creado_por?.split('@')[0]}</span>
                  </div>

                  {/* Error */}
                  {cmd.error_mensaje && (
                    <div className="mt-2 text-xs text-red-600 bg-red-50 px-3 py-2 rounded">
                      {cmd.error_mensaje}
                    </div>
                  )}

                  {/* Resultado */}
                  {cmd.resultado && Object.keys(cmd.resultado).length > 0 && (
                    <div className="mt-2 flex gap-3">
                      {Object.entries(cmd.resultado).map(([k, v]) => (
                        <span key={k} className="text-xs text-gray-500">
                          {k}: <strong className="text-gray-700">{String(v)}</strong>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Log expandible */}
                  {cmd.log_preview && (
                    <button
                      onClick={() => setExpandedLog(isExpanded ? null : cmd.id)}
                      className="mt-2 flex items-center gap-1 text-xs text-blue-600 hover:underline"
                    >
                      <Terminal className="w-3 h-3" />
                      {isExpanded ? 'Ocultar log' : 'Ver log'}
                    </button>
                  )}
                  {isExpanded && cmd.log_preview && (
                    <pre className="mt-2 text-xs bg-gray-900 text-gray-300 p-3 rounded-lg overflow-x-auto max-h-48 overflow-y-auto">
                      {cmd.log_preview}
                    </pre>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
