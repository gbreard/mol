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

interface PipelineStatus {
  fases: {
    scraping: { estado: string; ofertas_totales: number; ofertas_activas: number; dias_desde_scraping: number };
    nlp: { estado: string; procesadas: number; pendientes: number };
    matching: { estado: string; con_matching: number; pendientes: number; validadas: number; errores_sin_resolver: number; reglas_negocio: number };
    sync: { estado: string; en_supabase: number; pendientes: number };
  };
  resumen: { total_ofertas: number; en_supabase: number; issues_humanos_pendientes: number };
}

interface Command {
  id: string;
  comando: string;
  params: any;
  estado: string;
  log_preview?: string;
  resultado: any;
  creado_por: string;
  created_at: string;
  duracion_seg: number | null;
}

export default function FabricaPage() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [commands, setCommands] = useState<Command[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: "ok" | "error"; text: string } | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [statusRes, cmdsRes] = await Promise.all([
        fetch("/api/pipeline-status"),
        fetch("/api/pipeline-commands?limit=10"),
      ]);

      if (statusRes.ok) setStatus(await statusRes.json());
      if (cmdsRes.ok) {
        const data = await cmdsRes.json();
        setCommands(data.commands || []);
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
      setMessage({ type: "ok", text: `Comando "${comando}" creado. El poller lo ejecutara en <1 min.` });
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

  const s = status?.fases;
  const r = status?.resumen;

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
            id="scraping" label="SCRAPING" subtitle="6 portales" icon={Globe}
            status={s?.scraping.estado === "ok" ? "ok" : s?.scraping.estado === "warning" ? "warning" : "error"}
            metric={s?.scraping.ofertas_totales?.toLocaleString("es-AR") || "—"}
            metricLabel="ofertas"
            actions={[
              { label: "Lanzar", icon: Play, onClick: () => window.open("/admin/scraping/comandos", "_self"), variant: "primary" },
              { label: "Estado", icon: Settings, onClick: () => window.open("/admin/scraping", "_self") },
            ]}
          />
          <PipelineArrow />

          <div className="flex flex-col gap-2">
            <PipelineNode
              id="nlp" label="NLP" subtitle="v11.4" icon={Cpu}
              status={s?.nlp.pendientes && s.nlp.pendientes > 100 ? "warning" : "ok"}
              metric={s?.nlp.pendientes?.toLocaleString("es-AR") || "0"}
              metricLabel="pendientes"
              actions={[
                { label: "NLP 500", icon: Play, onClick: () => executeCommand("run_nlp", { limit: 500 }),
                  variant: "primary", loading: isExecuting("run_nlp"), disabled: hasRunning },
                { label: "Re-NLP", icon: RotateCw, onClick: () => executeCommand("reprocess_errors"),
                  disabled: hasRunning },
                { label: "Config", icon: Settings, onClick: () => window.open("/admin/procesamiento/diccionarios", "_self") },
              ]}
            />
            <PipelineGate
              id="gate-nlp" label="GATE NLP"
              rulesCount={35} approvedPct={99} blockedCount={s?.nlp.pendientes ? 1 : 0} errorsCount={0}
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
              status={s?.matching.errores_sin_resolver ? "warning" : "ok"}
              metric={s?.matching.con_matching?.toLocaleString("es-AR") || "0"}
              metricLabel="matcheadas"
              actions={[
                { label: "Match", icon: Play, onClick: () => executeCommand("run_matching", { limit: 500 }),
                  variant: "primary", loading: isExecuting("run_matching"), disabled: hasRunning },
                { label: "Re-M", icon: RotateCw, onClick: () => executeCommand("reapply_rules"),
                  disabled: hasRunning },
                { label: "Config", icon: Settings, onClick: () => window.open("/admin/procesamiento/diccionarios", "_self") },
              ]}
            />
            <PipelineGate
              id="gate-matching" label="GATE MATCHING"
              rulesCount={22} approvedPct={s?.matching.con_matching && s?.matching.errores_sin_resolver
                ? Math.round((1 - s.matching.errores_sin_resolver / s.matching.con_matching) * 100) : 99}
              blockedCount={0}
              errorsCount={s?.matching.errores_sin_resolver || 0}
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
            metric={s?.matching.validadas?.toLocaleString("es-AR") || "0"}
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
            status={s?.sync.pendientes ? "warning" : "ok"}
            metric={s?.sync.en_supabase?.toLocaleString("es-AR") || "0"}
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
            status={s?.matching.errores_sin_resolver ? "warning" : "ok"}
            metric={s?.matching.errores_sin_resolver || 0}
            metricLabel="escalados"
            actions={[
              { label: "Ver", icon: ClipboardList, onClick: () => {} },
              { label: "Repro.", icon: RotateCw, onClick: () => executeCommand("reprocess_errors") },
            ]}
          />
          <MejoraArrow />

          <MejoraContinuaNode
            id="issues" label="ISSUES" icon={FileText}
            status={(r?.issues_humanos_pendientes || 0) > 0 ? "action-needed" : "ok"}
            metric={r?.issues_humanos_pendientes || 0}
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
            {commands.slice(0, 8).map((cmd) => (
              <div key={cmd.id} className="flex items-center gap-3 text-sm">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  cmd.estado === "completado" ? "bg-green-500" :
                  cmd.estado === "ejecutando" ? "bg-blue-500 animate-pulse" :
                  cmd.estado === "error" ? "bg-red-500" :
                  cmd.estado === "pendiente" ? "bg-amber-500" : "bg-gray-300"
                }`} />
                <span className="text-gray-400 text-xs w-20 flex-shrink-0">
                  {formatTime(cmd.created_at)}
                </span>
                <span className="font-mono text-xs text-blue-600 w-36 flex-shrink-0">{cmd.comando}</span>
                <span className="text-gray-600 flex-1 truncate">
                  {cmd.estado === "ejecutando" && <Loader2 className="w-3 h-3 animate-spin inline mr-1" />}
                  {cmd.estado}
                  {cmd.duracion_seg != null && ` · ${cmd.duracion_seg}s`}
                  {cmd.resultado?.procesadas && ` · ${cmd.resultado.procesadas} procesadas`}
                  {cmd.resultado?.errores && ` · ${cmd.resultado.errores} errores`}
                </span>
                <span className="text-xs text-gray-400 flex-shrink-0">{cmd.creado_por?.split("@")[0]}</span>
              </div>
            ))}
          </div>
        )}
      </div>
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
