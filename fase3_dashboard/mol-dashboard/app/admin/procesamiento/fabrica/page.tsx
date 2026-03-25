"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Loader2, RefreshCw, Globe, Cpu, Target, CheckCircle2,
  Cloud, Play, RotateCw, Settings, AlertCircle, ClipboardList,
  Download, Zap, BookOpen, Tag, TrendingDown, ArrowRight,
} from "lucide-react";
import Link from "next/link";

interface LocalStatus {
  total_ofertas: number;
  nlp_procesadas: number;
  nlp_pendientes: number;
  nlp_aprobados: number;
  nlp_bloqueados: number;
  nlp_gate_aprobado_pct: number;
  matching_con: number;
  matching_sin: number;
  validadas: number;
  errores_pendientes: number;
  en_supabase: number;
  pendientes_sync: number;
  timestamp: string;
}

interface Command {
  id: string;
  comando: string;
  params: any;
  estado: string;
  resultado: any;
  error_message?: string;
  creado_por: string;
  created_at: string;
  duracion_seg: number | null;
}

export default function FabricaPage() {
  const [status, setStatus] = useState<LocalStatus | null>(null);
  const [commands, setCommands] = useState<Command[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: "ok" | "error"; text: string } | null>(null);
  const [showLimitModal, setShowLimitModal] = useState<string | null>(null);
  const [limitInput, setLimitInput] = useState("500");

  const loadData = useCallback(async () => {
    try {
      const [statusRes, cmdsRes] = await Promise.all([
        fetch("/api/pipeline-local-status"),
        fetch("/api/pipeline-commands?limit=10"),
      ]);

      if (statusRes.ok) {
        const data = await statusRes.json();
        if (data.total_ofertas != null) setStatus(data);
      }
      if (cmdsRes.ok) {
        const data = await cmdsRes.json();
        setCommands(data.commands || []);
      }
    } catch {} finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Poll when command executing
  useEffect(() => {
    const hasRunning = commands.some((c) => c.estado === "ejecutando");
    if (!hasRunning) return;
    const interval = setInterval(() => {
      fetch("/api/pipeline-commands?limit=10")
        .then((r) => r.json())
        .then((data) => setCommands(data.commands || []))
        .catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [commands]);

  function askLimit(comando: string) {
    setShowLimitModal(comando);
    setLimitInput("500");
  }

  function confirmLimit() {
    if (!showLimitModal) return;
    setShowLimitModal(null);
    executeCommand(showLimitModal, { limit: parseInt(limitInput) || 500 });
  }

  async function executeCommand(comando: string, params: any = {}) {
    setExecuting(comando);
    setMessage(null);
    try {
      const res = await fetch("/api/pipeline-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comando, params }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setMessage({ type: "ok", text: `Comando "${formatComando(comando)}" creado${params.limit ? ` (${params.limit} ofertas)` : ''}. El poller lo ejecuta en <1 min.` });
      loadData();
    } catch (e: any) {
      setMessage({ type: "error", text: e.message });
    } finally {
      setExecuting(null);
    }
  }

  const isExec = (cmd: string) => executing === cmd;
  const hasRunning = commands.some((c) => c.estado === "ejecutando");
  const s = status;

  // Pipeline breakdown
  const sinNlp = s?.nlp_pendientes || 0;
  const conNlp = s?.nlp_procesadas || 0;
  const gateAprobado = s?.nlp_aprobados || 0;
  const gatePendiente = conNlp - gateAprobado - (s?.nlp_bloqueados || 0);
  const gateBloqueado = s?.nlp_bloqueados || 0;
  const conMatching = s?.matching_con || 0;
  const validadas = s?.validadas || 0;
  const enDashboard = s?.en_supabase || 0;
  const total = s?.total_ofertas || 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando fabrica...</span>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fabrica de Procesamiento</h1>
          <p className="text-gray-500 text-sm mt-1">Pipeline v3.3 · NLP v11.4 · Matching v3.5.4</p>
        </div>
        <button onClick={loadData} className="flex items-center gap-2 text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm">
          <RefreshCw className="w-4 h-4" /> Actualizar
        </button>
      </div>

      {message && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border text-sm ${
          message.type === "ok" ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"
        }`}>
          {message.type === "ok" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      {/* ═══ SECCIÓN 1: EMBUDO DE DATOS ═══ */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
          Embudo de datos — donde estan las ofertas
        </h2>

        {/* Funnel visualization */}
        <div className="space-y-2">
          <FunnelRow label="Ofertas totales" count={total} total={total} color="bg-gray-400" />
          <FunnelRow label="Con NLP" count={conNlp} total={total} color="bg-blue-500" sublabel={sinNlp > 0 ? `${sinNlp.toLocaleString("es-AR")} pendientes NLP` : undefined} />
          <FunnelRow label="Gate aprobado" count={gateAprobado} total={total} color="bg-teal-500"
            sublabel={gatePendiente > 0 ? `${gatePendiente.toLocaleString("es-AR")} pendientes gate (correr pipeline)` : undefined}
            sublabel2={gateBloqueado > 0 ? `${gateBloqueado.toLocaleString("es-AR")} bloqueados` : undefined} />
          <FunnelRow label="Con matching" count={conMatching} total={total} color="bg-green-500" />
          <FunnelRow label="Validadas" count={validadas} total={total} color="bg-green-600" />
          <FunnelRow label="En dashboard" count={enDashboard} total={total} color="bg-emerald-600"
            sublabel={validadas - enDashboard > 0 ? `${(validadas - enDashboard).toLocaleString("es-AR")} pendientes sync` : undefined} />
        </div>

        {/* Verificación */}
        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-400">
          Verificacion: {sinNlp.toLocaleString("es-AR")} + {gateAprobado.toLocaleString("es-AR")} + {gatePendiente.toLocaleString("es-AR")} + {gateBloqueado.toLocaleString("es-AR")} = {(sinNlp + gateAprobado + gatePendiente + gateBloqueado).toLocaleString("es-AR")}
          {sinNlp + gateAprobado + gatePendiente + gateBloqueado === total
            ? <span className="text-green-500 ml-1">✓ cierra</span>
            : <span className="text-red-500 ml-1">✗ no cierra (dif: {total - sinNlp - gateAprobado - gatePendiente - gateBloqueado})</span>}
        </div>
      </div>

      {/* ═══ SECCIÓN 2: PERFORMANCE ═══ */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
            Performance del pipeline
          </h2>
          <Link href="/admin/aprendizaje" className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
            Ver detalle completo <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KPI label="Tasa aprobacion NLP" value={`${s?.nlp_gate_aprobado_pct || 0}%`} color={s?.nlp_gate_aprobado_pct && s.nlp_gate_aprobado_pct >= 95 ? "green" : "amber"} />
          <KPI label="Errores pendientes" value={s?.errores_pendientes || 0} color={s?.errores_pendientes ? "red" : "green"} />
          <KPI label="Runs ejecutados" value={commands.filter(c => c.estado === "completado").length} color="blue" />
          <KPI label="Gate pendiente" value={gatePendiente > 0 ? `${gatePendiente.toLocaleString("es-AR")}` : "0"} color={gatePendiente > 100 ? "amber" : "green"} />
        </div>

        {/* Quick performance summary */}
        {commands.length > 0 && commands[0].estado === "completado" && commands[0].resultado && (
          <div className="mt-3 pt-3 border-t border-gray-100 text-sm text-gray-600">
            Ultimo run: {formatComando(commands[0].comando)} · {commands[0].resultado.procesadas || "?"} procesadas
            {commands[0].resultado.errores ? ` · ${commands[0].resultado.errores} errores (${commands[0].resultado.procesadas ? Math.round(commands[0].resultado.errores / commands[0].resultado.procesadas * 100) : 0}%)` : " · 0 errores"}
            {commands[0].duracion_seg != null && ` · ${formatDuration(commands[0].duracion_seg)}`}
          </div>
        )}
      </div>

      {/* ═══ SECCIÓN 3: CONTROLES ═══ */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
          Controles
        </h2>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          <ActionButton label="NLP + Validacion" icon={Cpu} onClick={() => askLimit("run_nlp")}
            disabled={hasRunning} loading={isExec("run_nlp")} badge={sinNlp > 0 ? `${sinNlp} pend.` : undefined} />
          <ActionButton label="Matching" icon={Target} onClick={() => askLimit("run_matching")}
            disabled={hasRunning} loading={isExec("run_matching")} badge={gatePendiente > 0 ? `${gatePendiente} pend.` : undefined} />
          <ActionButton label="Sync Supabase" icon={Cloud} onClick={() => executeCommand("sync_supabase")}
            disabled={hasRunning} loading={isExec("sync_supabase")} />
          <ActionButton label="Reaplicar reglas" icon={RotateCw} onClick={() => executeCommand("reapply_rules")}
            disabled={hasRunning} />
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <ActionButton label="Reprocesar errores" icon={AlertCircle} onClick={() => executeCommand("reprocess_errors")}
            disabled={hasRunning} variant="secondary" />
          <ActionButton label="Exportar Excel" icon={Download} onClick={() => executeCommand("export_excel")}
            disabled={hasRunning} variant="secondary" />
          <ActionButton label="Generar training" icon={BookOpen} onClick={() => executeCommand("generate_training")}
            disabled={hasRunning} variant="secondary" />
          <ActionButton label="Diccionarios" icon={Settings} onClick={() => window.open("/admin/procesamiento/diccionarios", "_self")}
            variant="secondary" />
        </div>
      </div>

      {/* ═══ ACTIVIDAD RECIENTE ═══ */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Actividad reciente
        </h2>

        {commands.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">Sin comandos recientes</p>
        ) : (
          <div className="space-y-2">
            {commands.slice(0, 8).map((cmd) => {
              const duration = cmd.duracion_seg != null ? formatDuration(cmd.duracion_seg) : null;
              const isTimeout = cmd.error_message?.includes("Timeout");
              return (
                <div key={cmd.id} className="flex items-start gap-3 text-sm">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${
                    cmd.estado === "completado" ? "bg-green-500" :
                    cmd.estado === "ejecutando" ? "bg-blue-500 animate-pulse" :
                    cmd.estado === "error" && isTimeout ? "bg-amber-500" :
                    cmd.estado === "error" ? "bg-red-500" :
                    cmd.estado === "pendiente" ? "bg-amber-500" : "bg-gray-300"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-xs">{formatTime(cmd.created_at)}</span>
                      <span className="font-mono text-xs text-blue-600">{formatComando(cmd.comando)}</span>
                      {cmd.params?.limit && <span className="text-xs text-gray-400">({cmd.params.limit} ofertas)</span>}
                      <span className="text-xs text-gray-400 ml-auto">{cmd.creado_por?.split("@")[0]}</span>
                    </div>
                    <div className="text-xs mt-0.5">
                      {cmd.estado === "ejecutando" && (
                        <span className="text-blue-600"><Loader2 className="w-3 h-3 animate-spin inline mr-1" />Ejecutando...{duration && ` (${duration})`}</span>
                      )}
                      {cmd.estado === "completado" && (
                        <span className="text-green-600">
                          Completado{duration && ` en ${duration}`}
                          {cmd.resultado?.procesadas && ` · ${cmd.resultado.procesadas} procesadas`}
                          {cmd.resultado?.errores ? ` · ${cmd.resultado.errores} errores` : ""}
                        </span>
                      )}
                      {cmd.estado === "pendiente" && <span className="text-amber-600">Pendiente — esperando poller</span>}
                      {cmd.estado === "error" && isTimeout && (
                        <span className="text-amber-600">Timeout ({duration}) — ofertas procesadas antes del corte se guardaron</span>
                      )}
                      {cmd.estado === "error" && !isTimeout && (
                        <span className="text-red-600">{cmd.error_message || "Error desconocido"}</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal cantidad */}
      {showLimitModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" onClick={() => setShowLimitModal(null)}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-80" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-gray-900 mb-2">{formatComando(showLimitModal)}</h3>
            <p className="text-sm text-gray-500 mb-4">Cuantas ofertas procesar?</p>
            <div className="flex gap-2 mb-4">
              {[100, 500, 1000, 2000].map(n => (
                <button key={n} onClick={() => setLimitInput(String(n))}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    limitInput === String(n) ? "bg-teal-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}>{n}</button>
              ))}
            </div>
            <input type="number" value={limitInput} onChange={(e) => setLimitInput(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm mb-4" min={1} max={10000} />
            <div className="flex gap-2">
              <button onClick={confirmLimit} className="flex-1 bg-teal-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-teal-700">
                Ejecutar {limitInput} ofertas
              </button>
              <button onClick={() => setShowLimitModal(null)} className="px-4 py-2 text-gray-500 text-sm hover:bg-gray-100 rounded-lg">Cancelar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══ Components ═══

function FunnelRow({ label, count, total, color, sublabel, sublabel2 }: {
  label: string; count: number; total: number; color: string;
  sublabel?: string; sublabel2?: string;
}) {
  const pct = total > 0 ? Math.round(count / total * 100) : 0;
  const widthPct = total > 0 ? Math.max(count / total * 100, 2) : 0;

  return (
    <div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-600 w-28 text-right flex-shrink-0">{label}</span>
        <div className="flex-1 bg-gray-100 rounded-full h-7 overflow-hidden relative">
          <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${widthPct}%` }} />
          <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white mix-blend-difference">
            {count.toLocaleString("es-AR")} ({pct}%)
          </span>
        </div>
      </div>
      {sublabel && <div className="text-xs text-amber-600 ml-32 mt-0.5">↳ {sublabel}</div>}
      {sublabel2 && <div className="text-xs text-red-500 ml-32 mt-0.5">↳ {sublabel2}</div>}
    </div>
  );
}

function KPI({ label, value, color }: { label: string; value: string | number; color: string }) {
  const colors: Record<string, string> = {
    green: "bg-green-50 text-green-700", amber: "bg-amber-50 text-amber-700",
    red: "bg-red-50 text-red-700", blue: "bg-blue-50 text-blue-700",
  };
  return (
    <div className={`rounded-xl p-4 ${colors[color] || colors.blue}`}>
      <div className="text-xs font-medium opacity-75 mb-1">{label}</div>
      <div className="text-xl font-bold">{value}</div>
    </div>
  );
}

function ActionButton({ label, icon: Icon, onClick, disabled, loading, variant, badge }: {
  label: string; icon: any; onClick: () => void; disabled?: boolean;
  loading?: boolean; variant?: "secondary"; badge?: string;
}) {
  return (
    <button onClick={onClick} disabled={disabled || loading}
      className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 w-full ${
        variant === "secondary"
          ? "bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200"
          : "bg-teal-600 text-white hover:bg-teal-700"
      }`}>
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon className="w-4 h-4" />}
      {label}
      {badge && <span className="ml-auto text-xs opacity-75">{badge}</span>}
    </button>
  );
}

// ═══ Helpers ═══

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    const diffMin = Math.round((Date.now() - d.getTime()) / 60000);
    if (diffMin < 1) return "ahora";
    if (diffMin < 60) return `hace ${diffMin}m`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `hace ${diffH}h`;
    return d.toLocaleDateString("es-AR", { day: "2-digit", month: "short" });
  } catch { return ts; }
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}min`;
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);
  return `${h}h ${m}min`;
}

const COMANDO_LABELS: Record<string, string> = {
  run_pipeline: "Pipeline completo", run_nlp: "NLP + Validacion", run_matching: "Matching",
  reprocess_errors: "Reprocesar errores", revalidate_nlp: "Re-validar NLP",
  revalidate_matching: "Re-validar Matching", reapply_rules: "Reaplicar reglas",
  export_excel: "Exportar Excel", sync_supabase: "Sync Supabase",
  sync_supabase_full: "Sync Full", generate_training: "Generar training",
};

function formatComando(cmd: string): string {
  return COMANDO_LABELS[cmd] || cmd;
}
