"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Loader2, RefreshCw, Globe, Cpu, Target, Shield, CheckCircle2,
  Cloud, Play, RotateCw, Settings, FileText, AlertCircle, ClipboardList,
  Download, Zap, BookOpen, Tag, Users, Clock,
} from "lucide-react";
import { PipelineNode, PipelineArrow } from "@/components/fabrica/PipelineNode";
import { PipelineGate } from "@/components/fabrica/PipelineGate";
import { MejoraContinuaNode, MejoraArrow } from "@/components/fabrica/MejoraContinuaNode";

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
  log_preview?: string;
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
  const [scrapingStats, setScrapingStats] = useState<{ total_ofertas: number; portales: Record<string, any>; ultimo_scraping?: string } | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [statusRes, cmdsRes, scrapingRes] = await Promise.all([
        fetch("/api/pipeline-local-status"),
        fetch("/api/pipeline-commands?limit=10"),
        fetch("/api/scraping-live-stats"),
      ]);

      if (statusRes.ok) {
        const data = await statusRes.json();
        if (data.status) setStatus(data.status);
        else if (data.total_ofertas != null) setStatus(data);
      }
      if (cmdsRes.ok) {
        const data = await cmdsRes.json();
        setCommands(data.commands || []);
      }
      if (scrapingRes.ok) {
        setScrapingStats(await scrapingRes.json());
      }
    } catch {} finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Poll for updates when a command is executing
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
    const limit = parseInt(limitInput) || 500;
    setShowLimitModal(null);
    executeCommand(showLimitModal, { limit });
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
      setMessage({ type: "ok", text: `Comando "${comando}" creado (${params.limit ? params.limit + ' ofertas' : ''}). El poller lo ejecutara en <1 min.` });
      loadData();
    } catch (e: any) {
      setMessage({ type: "error", text: e.message });
    } finally {
      setExecuting(null);
    }
  }

  const isExecuting = (cmd: string) => executing === cmd;
  const hasRunning = commands.some((c) => c.estado === "ejecutando");

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando fabrica...</span>
      </div>
    );
  }

  const s = status; // LocalStatus directly

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fabrica de Procesamiento</h1>
          <p className="text-gray-500 text-sm mt-1">
            Pipeline v3.3 · NLP v11.4 · Matching v3.5.4
          </p>
        </div>
        <button onClick={loadData} className="flex items-center gap-2 text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm">
          <RefreshCw className="w-4 h-4" /> Actualizar
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border text-sm ${
          message.type === "ok" ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"
        }`}>
          {message.type === "ok" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      {/* === LÍNEA DE FABRICACIÓN === */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
          Linea de Fabricacion
        </h2>

        {/* Pipeline nodes */}
        <div className="flex items-start gap-1 overflow-x-auto pb-4">
          <PipelineNode
            id="scraping" label="SCRAPING" subtitle={`${Object.keys(scrapingStats?.portales || {}).length} portales`} icon={Globe}
            status={scrapingStats?.total_ofertas ? "ok" : "idle"}
            metric={scrapingStats?.total_ofertas?.toLocaleString("es-AR") || s?.total_ofertas?.toLocaleString("es-AR") || "—"}
            metricLabel="ofertas VPS"
            actions={[
              { label: "Lanzar", icon: Play, onClick: () => window.open("/admin/scraping/comandos", "_self"), variant: "primary" },
              { label: "Estado", icon: Settings, onClick: () => window.open("/admin/scraping", "_self") },
            ]}
          />
          <PipelineArrow />

          <div className="flex flex-col gap-2">
            <PipelineNode
              id="nlp" label="NLP" subtitle="v11.4" icon={Cpu}
              status={s?.nlp_pendientes && s.nlp_pendientes > 100 ? "warning" : "ok"}
              metric={s?.nlp_pendientes?.toLocaleString("es-AR") || "0"}
              metricLabel="pendientes"
              actions={[
                { label: "Procesar NLP", icon: Play, onClick: () => askLimit("run_nlp"),
                  variant: "primary", loading: isExecuting("run_nlp"), disabled: hasRunning },
                { label: "Re-NLP", icon: RotateCw, onClick: () => executeCommand("reprocess_errors"),
                  disabled: hasRunning },
                { label: "Config", icon: Settings, onClick: () => window.open("/admin/procesamiento/diccionarios", "_self") },
              ]}
            />
            <PipelineGate
              id="gate-nlp" label="GATE NLP"
              rulesCount={35} approvedPct={s?.nlp_gate_aprobado_pct || 99} blockedCount={s?.nlp_bloqueados || 0} errorsCount={0}
              actions={[
                { label: "Bloq.", icon: ClipboardList, onClick: () => {} },
                { label: "Re-val", icon: RotateCw, onClick: () => executeCommand("revalidate_nlp") },
                { label: "Reglas", icon: Settings, onClick: () => window.open("/admin/procesamiento/diccionarios", "_self") },
              ]}
            />
          </div>
          <PipelineArrow />

          <div className="flex flex-col gap-2">
            <PipelineNode
              id="matching" label="MATCHING" subtitle="v3.5.4" icon={Target}
              status={s?.errores_pendientes ? "warning" : "ok"}
              metric={s?.matching_con?.toLocaleString("es-AR") || "0"}
              metricLabel="matcheadas"
              actions={[
                { label: "Match", icon: Play, onClick: () => askLimit("run_matching"),
                  variant: "primary", loading: isExecuting("run_matching"), disabled: hasRunning },
                { label: "Re-M", icon: RotateCw, onClick: () => executeCommand("reapply_rules"),
                  disabled: hasRunning },
                { label: "Config", icon: Settings, onClick: () => window.open("/admin/procesamiento/diccionarios", "_self") },
              ]}
            />
            <PipelineGate
              id="gate-matching" label="GATE MATCHING"
              rulesCount={22} approvedPct={s?.matching_con && s?.errores_pendientes
                ? Math.round((1 - s.errores_pendientes / s.matching_con) * 100) : 99}
              blockedCount={0}
              errorsCount={s?.errores_pendientes || 0}
              actions={[
                { label: "Errs", icon: ClipboardList, onClick: () => {} },
                { label: "Re-val", icon: RotateCw, onClick: () => executeCommand("revalidate_matching") },
                { label: "Reglas", icon: Settings, onClick: () => window.open("/admin/procesamiento/diccionarios", "_self") },
              ]}
            />
          </div>
          <PipelineArrow />

          <PipelineNode
            id="validacion" label="VALIDACION" subtitle="humana" icon={CheckCircle2}
            status="ok"
            metric={s?.validadas?.toLocaleString("es-AR") || "0"}
            metricLabel="validadas"
            actions={[
              { label: "Validar", icon: Play, onClick: () => window.open("/admin/validacion", "_self"), variant: "primary" },
              { label: "Export", icon: Download, onClick: () => executeCommand("export_excel"), disabled: hasRunning },
              { label: "Issues", icon: ClipboardList, onClick: () => window.open("/admin/issues", "_self") },
            ]}
          />
          <PipelineArrow />

          <PipelineNode
            id="sync" label="SYNC" subtitle="Supabase" icon={Cloud}
            status={s?.pendientes_sync ? "warning" : "ok"}
            metric={s?.en_supabase?.toLocaleString("es-AR") || "0"}
            metricLabel="en Supabase"
            actions={[
              { label: "Sync", icon: Play, onClick: () => executeCommand("sync_supabase"),
                variant: "primary", loading: isExecuting("sync_supabase"), disabled: hasRunning },
              { label: "Full", icon: RotateCw, onClick: () => executeCommand("sync_supabase_full"), disabled: hasRunning },
            ]}
          />
        </div>
      </div>

      {/* === LÍNEA DE MEJORA CONTINUA === */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
          Linea de Mejora Continua
        </h2>

        <div className="flex items-start gap-1 overflow-x-auto pb-2">
          <MejoraContinuaNode
            id="errores" label="ERRORES" icon={AlertCircle}
            status={s?.errores_pendientes ? "warning" : "ok"}
            metric={s?.errores_pendientes || 0}
            metricLabel="escalados"
            actions={[
              { label: "Ver", icon: ClipboardList, onClick: () => {} },
              { label: "Repro.", icon: RotateCw, onClick: () => executeCommand("reprocess_errors") },
            ]}
          />
          <MejoraArrow />

          <MejoraContinuaNode
            id="issues" label="ISSUES" icon={FileText}
            status={(0) > 0 ? "action-needed" : "ok"}
            metric={0}
            metricLabel="pendientes"
            actions={[
              { label: "Ver", icon: ClipboardList, onClick: () => window.open("/admin/issues", "_self") },
            ]}
            onClick={() => window.open("/admin/issues", "_self")}
          />
          <MejoraArrow />

          <MejoraContinuaNode
            id="training" label="TRAINING" icon={FileText}
            status="ok"
            metric="602+"
            metricLabel="pares"
            actions={[
              { label: "Stats", icon: Zap, onClick: () => window.open("/admin/procesamiento/fine-tuning", "_self") },
              { label: "Regen.", icon: RotateCw, onClick: () => executeCommand("generate_training") },
            ]}
          />
          <MejoraArrow />

          <MejoraContinuaNode
            id="finetune" label="FINE-TUNE" icon={Zap}
            status="idle"
            metric="almost"
            metricLabel="ready"
            actions={[
              { label: "Dash", icon: Zap, onClick: () => window.open("/admin/procesamiento/fine-tuning", "_self") },
            ]}
            onClick={() => window.open("/admin/procesamiento/fine-tuning", "_self")}
          />
          <MejoraArrow />

          <MejoraContinuaNode
            id="catalogo" label="CATALOGO" icon={BookOpen}
            status="idle"
            metric={0}
            metricLabel="nuevas"
            actions={[
              { label: "Ver", icon: BookOpen, onClick: () => window.open("/admin/procesamiento/catalogo", "_self") },
            ]}
            onClick={() => window.open("/admin/procesamiento/catalogo", "_self")}
          />
          <MejoraArrow />

          <MejoraContinuaNode
            id="perfil" label="PERFIL" icon={Tag}
            status="ok"
            metric="v1.0"
            metricLabel="actual"
            actions={[
              { label: "Corte", icon: Tag, onClick: () => window.open("/admin/perfil-argentino", "_self") },
            ]}
            onClick={() => window.open("/admin/perfil-argentino", "_self")}
          />
        </div>
      </div>

      {/* === ÚLTIMA ACTIVIDAD === */}
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
                      {cmd.estado === "pendiente" && (
                        <span className="text-amber-600">Pendiente — esperando poller</span>
                      )}
                      {cmd.estado === "error" && isTimeout && (
                        <span className="text-amber-600">Timeout ({duration}) — las ofertas procesadas antes del corte se guardaron en BD</span>
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

      {/* Modal: cuántas ofertas procesar */}
      {showLimitModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" onClick={() => setShowLimitModal(null)}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-80" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-gray-900 mb-2">
              {showLimitModal === "run_nlp" ? "Procesar NLP" : showLimitModal === "run_matching" ? "Ejecutar Matching" : showLimitModal}
            </h3>
            <p className="text-sm text-gray-500 mb-4">Cuantas ofertas procesar?</p>
            <div className="flex gap-2 mb-4">
              {[100, 500, 1000, 2000].map(n => (
                <button key={n} onClick={() => setLimitInput(String(n))}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    limitInput === String(n) ? "bg-teal-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}>
                  {n}
                </button>
              ))}
            </div>
            <input
              type="number"
              value={limitInput}
              onChange={(e) => setLimitInput(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm mb-4"
              placeholder="Cantidad personalizada"
              min={1}
              max={10000}
            />
            <div className="flex gap-2">
              <button onClick={confirmLimit}
                className="flex-1 bg-teal-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-teal-700">
                Ejecutar {limitInput} ofertas
              </button>
              <button onClick={() => setShowLimitModal(null)}
                className="px-4 py-2 text-gray-500 text-sm hover:bg-gray-100 rounded-lg">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.round(diffMs / 60000);
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
  run_pipeline: "Pipeline completo",
  run_nlp: "Procesar NLP",
  run_matching: "Matching",
  reprocess_errors: "Reprocesar errores",
  revalidate_nlp: "Re-validar NLP",
  revalidate_matching: "Re-validar Matching",
  reapply_rules: "Reaplicar reglas",
  export_excel: "Exportar Excel",
  sync_supabase: "Sync Supabase",
  sync_supabase_full: "Sync Full",
  generate_training: "Generar training",
};

function formatComando(cmd: string): string {
  return COMANDO_LABELS[cmd] || cmd;
}
