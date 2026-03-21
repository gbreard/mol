"use client";

import { useState, useEffect } from "react";
import {
  BarChart3,
  TrendingUp,
  FileText,
  Activity,
  Loader2,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Info,
  ArrowRight,
  Database,
  Brain,
  GitMerge,
  Cloud,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import { supabase } from "@/lib/supabase";

// --- Types ---

interface FaseStatus {
  estado: 'ok' | 'warning' | 'error';
  [key: string]: any;
}

interface Alerta {
  nivel: 'ok' | 'warning' | 'error' | 'info';
  mensaje: string;
  accion: string | null;
  detalle: string | null;
}

interface Inconsistencia {
  tipo: string;
  severidad: 'ok' | 'warning' | 'error';
  mensaje: string;
  esperado: number;
  actual: number;
  diferencia: number;
  accion: string | null;
}

interface Reconciliacion {
  conteos: {
    local_total: number;
    local_con_nlp: number;
    local_validadas: number;
    supabase_ofertas: number;
    supabase_skills: number;
    supabase_ofertas_con_skills: number;
    supabase_sin_isco: number;
    supabase_sin_skills: number;
  };
  inconsistencias: Inconsistencia[];
  estado: 'ok' | 'warning' | 'error';
}

interface PipelineData {
  fases: {
    scraping: FaseStatus;
    nlp: FaseStatus;
    matching: FaseStatus;
    sync: FaseStatus;
  };
  alertas: Alerta[];
  resumen: {
    total_ofertas: number;
    en_supabase: number;
    issues_humanos_pendientes: number;
    issues_auto_pendientes: number;
    fase_sugerida: string;
    fase_sugerida_razon: string;
  };
  ultimo_update: string;
  reconciliacion: Reconciliacion | null;
}

// --- Constants ---

const FASE_CONFIG = [
  { key: 'scraping', label: 'Scraping', sublabel: 'VPS', icon: Database },
  { key: 'nlp', label: 'NLP', sublabel: 'Local', icon: Brain },
  { key: 'matching', label: 'Matching', sublabel: 'Local', icon: GitMerge },
  { key: 'sync', label: 'Sync', sublabel: 'Supabase', icon: Cloud },
] as const;

const ESTADO_COLORS = {
  ok: { bg: 'bg-green-100', border: 'border-green-400', text: 'text-green-700', dot: 'bg-green-500' },
  warning: { bg: 'bg-amber-100', border: 'border-amber-400', text: 'text-amber-700', dot: 'bg-amber-500' },
  error: { bg: 'bg-red-100', border: 'border-red-400', text: 'text-red-700', dot: 'bg-red-500' },
};

const ALERTA_ICONS: Record<string, any> = {
  ok: CheckCircle2, info: Info, warning: AlertTriangle, error: XCircle,
};

const ALERTA_STYLES: Record<string, string> = {
  ok: 'bg-green-50 border-green-200 text-green-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  warning: 'bg-amber-50 border-amber-200 text-amber-800',
  error: 'bg-red-50 border-red-200 text-red-800',
};

const ACCION_LINKS: Record<string, { label: string; href: string }> = {
  lanzar_scraping: { label: 'Ver scraping', href: '/admin/scraping' },
  procesar_nlp: { label: 'Ver pipeline', href: '/admin/metricas' },
  procesar_matching: { label: 'Ver pipeline', href: '/admin/metricas' },
  sync_supabase: { label: 'Ver sync', href: '/admin/metricas' },
  ver_errores: { label: 'Ver errores', href: '/admin/validacion' },
  ver_issues: { label: 'Ver issues', href: '/admin/issues' },
  backfill_skills: { label: 'Ver skills', href: '/admin/skills' },
  reprocesar_matching: { label: 'Ver matching', href: '/admin/metricas' },
};

const QUICK_LINKS = [
  { label: 'Issues', href: '/admin/issues', icon: AlertTriangle },
  { label: 'Validacion', href: '/admin/validacion', icon: CheckCircle2 },
  { label: 'Skills', href: '/admin/skills', icon: Activity },
  { label: 'Scraping', href: '/admin/scraping', icon: Database },
  { label: 'Arquitectura', href: '/admin/arquitectura', icon: GitMerge },
  { label: 'Configuracion', href: '/admin/configuracion', icon: BarChart3 },
];

// --- Page ---

export default function MetricasPage() {
  const [pipeline, setPipeline] = useState<PipelineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      if (!supabase) throw new Error('Supabase no configurado');

      const [statusResult, reconResult] = await Promise.all([
        supabase.rpc('get_pipeline_status'),
        supabase.rpc('reconciliar_sistemas'),
      ]);

      if (statusResult.error) throw statusResult.error;

      setPipeline({
        ...(statusResult.data as any),
        reconciliacion: reconResult.error ? null : (reconResult.data as Reconciliacion),
      });
    } catch (err: any) {
      console.error('Error cargando datos:', err);
      setError(err.message || 'Error al cargar datos');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando estado del pipeline...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 font-medium">{error}</p>
          <button onClick={loadData} className="mt-4 text-blue-600 hover:underline">Reintentar</button>
        </div>
      </div>
    );
  }

  const fases = pipeline?.fases;
  const alertas = pipeline?.alertas || [];
  const resumen = pipeline?.resumen;
  const recon = pipeline?.reconciliacion;

  const tiempoDesdeUpdate = pipeline?.ultimo_update
    ? formatTimeAgo(new Date(pipeline.ultimo_update))
    : '—';

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Centro de Control</h1>
          <p className="text-gray-500 text-sm mt-1">
            Actualizado {tiempoDesdeUpdate}
            {resumen?.fase_sugerida && (
              <span className="ml-2 text-blue-600 font-medium">
                — Fase sugerida: {resumen.fase_sugerida}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={() => loadData()}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </div>

      {/* Seccion 1: Pipeline Visual con Semaforos */}
      {fases && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-5">Pipeline</h2>
          <div className="flex items-center justify-between gap-2">
            {FASE_CONFIG.map((fase, idx) => {
              const status = fases[fase.key];
              const colors = ESTADO_COLORS[status.estado];
              const Icon = fase.icon;
              return (
                <div key={fase.key} className="flex items-center flex-1">
                  <div className={`flex-1 rounded-xl border-2 p-4 ${colors.bg} ${colors.border} transition-all`}>
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`p-2 rounded-lg ${colors.dot} bg-opacity-20`}>
                        <Icon className={`w-5 h-5 ${colors.text}`} />
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900 text-sm">{fase.label}</div>
                        <div className="text-xs text-gray-500">{fase.sublabel}</div>
                      </div>
                      <div className={`ml-auto w-3 h-3 rounded-full ${colors.dot} animate-pulse`} />
                    </div>
                    <div className="text-xs text-gray-600 space-y-0.5">
                      {fase.key === 'scraping' && (
                        <>
                          <div>{status.ofertas_totales?.toLocaleString()} ofertas</div>
                          <div>Hace {status.dias_desde_scraping} dias</div>
                        </>
                      )}
                      {fase.key === 'nlp' && (
                        <>
                          <div>{status.procesadas?.toLocaleString()} procesadas</div>
                          {status.pendientes > 0 && <div className="text-amber-700 font-medium">{status.pendientes} pendientes</div>}
                        </>
                      )}
                      {fase.key === 'matching' && (
                        <>
                          <div>{status.con_matching?.toLocaleString()} matcheadas</div>
                          <div>{status.validadas?.toLocaleString()} validadas</div>
                          {status.errores_sin_resolver > 0 && <div className="text-amber-700 font-medium">{status.errores_sin_resolver} errores</div>}
                        </>
                      )}
                      {fase.key === 'sync' && (
                        <>
                          <div>{status.en_supabase?.toLocaleString()} en Supabase</div>
                          {status.pendientes > 0 && <div className="text-amber-700 font-medium">{status.pendientes} pendientes</div>}
                        </>
                      )}
                    </div>
                  </div>
                  {idx < FASE_CONFIG.length - 1 && (
                    <ArrowRight className="w-5 h-5 text-gray-300 mx-1 flex-shrink-0" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Seccion 2: Alertas con acciones */}
      {alertas.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Alertas</h2>
          <div className="space-y-2">
            {alertas.map((alerta, idx) => {
              const AlertIcon = ALERTA_ICONS[alerta.nivel] || Info;
              const style = ALERTA_STYLES[alerta.nivel] || ALERTA_STYLES.info;
              const link = alerta.accion ? ACCION_LINKS[alerta.accion] : null;
              return (
                <div key={idx} className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${style}`}>
                  <AlertIcon className="w-5 h-5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium">{alerta.mensaje}</span>
                    {alerta.detalle && (
                      <span className="text-xs opacity-70 ml-2">{alerta.detalle}</span>
                    )}
                  </div>
                  {link && (
                    <a href={link.href} className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-md bg-white bg-opacity-60 hover:bg-opacity-100 transition-colors flex-shrink-0">
                      {link.label} <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Seccion 3: KPIs */}
      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Ofertas totales" value={resumen.total_ofertas} icon={FileText} color="blue" />
          <KPICard label="En Supabase" value={resumen.en_supabase} icon={Cloud} color="green" />
          <KPICard label="Issues usuarios" value={resumen.issues_humanos_pendientes} icon={AlertTriangle} color={resumen.issues_humanos_pendientes > 0 ? 'amber' : 'green'} />
          <KPICard label="Sin procesar" value={(resumen.total_ofertas - resumen.en_supabase)} icon={TrendingUp} color={(resumen.total_ofertas - resumen.en_supabase) > 0 ? 'red' : 'green'} />
        </div>
      )}

      {/* Seccion 4: Reconciliacion */}
      {recon && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className={`w-5 h-5 ${recon.estado === 'ok' ? 'text-green-600' : recon.estado === 'error' ? 'text-red-600' : 'text-amber-600'}`} />
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Reconciliacion de sistemas</h2>
            <span className={`ml-auto text-xs font-medium px-2 py-1 rounded-full ${
              recon.estado === 'ok' ? 'bg-green-100 text-green-700' :
              recon.estado === 'error' ? 'bg-red-100 text-red-700' :
              'bg-amber-100 text-amber-700'
            }`}>
              {recon.estado === 'ok' ? 'Consistente' : recon.inconsistencias.length + ' diferencias'}
            </span>
          </div>

          {/* Conteos comparativos */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <ConteoCard label="Local total" value={recon.conteos.local_total} />
            <ConteoCard label="Local con NLP" value={recon.conteos.local_con_nlp} />
            <ConteoCard label="Supabase ofertas" value={recon.conteos.supabase_ofertas} />
            <ConteoCard label="Supabase skills" value={recon.conteos.supabase_skills} />
          </div>

          {/* Inconsistencias */}
          {recon.inconsistencias.length > 0 && (
            <div className="space-y-2">
              {recon.inconsistencias.map((inc, idx) => {
                const style = ALERTA_STYLES[inc.severidad] || ALERTA_STYLES.info;
                const Icon = ALERTA_ICONS[inc.severidad] || Info;
                const link = inc.accion ? ACCION_LINKS[inc.accion] : null;
                return (
                  <div key={idx} className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${style}`}>
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-medium">{inc.mensaje}</span>
                      {inc.diferencia > 0 && (
                        <span className="text-xs opacity-70 ml-2">
                          ({inc.diferencia.toLocaleString()} diferencia)
                        </span>
                      )}
                    </div>
                    {link && (
                      <a href={link.href} className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-md bg-white bg-opacity-60 hover:bg-opacity-100 transition-colors flex-shrink-0">
                        {link.label} <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Seccion 5: Links rapidos */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Acceso rapido</h2>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {QUICK_LINKS.map(link => (
            <a key={link.href} href={link.href} className="flex flex-col items-center gap-2 p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-center">
              <link.icon className="w-5 h-5 text-gray-500" />
              <span className="text-xs font-medium text-gray-700">{link.label}</span>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Helper components ---

function KPICard({ label, value, icon: Icon, color }: { label: string; value: number | string; icon: any; color: string }) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600', green: 'bg-green-100 text-green-600',
    amber: 'bg-amber-100 text-amber-600', purple: 'bg-purple-100 text-purple-600',
    red: 'bg-red-100 text-red-600',
  };
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg ${colorMap[color] || colorMap.blue}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="text-xs text-gray-500 font-medium">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
    </div>
  );
}

function ConteoCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <div className="text-lg font-bold text-gray-900">{value.toLocaleString()}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHours / 24);
  if (diffMin < 1) return 'ahora';
  if (diffMin < 60) return `hace ${diffMin} min`;
  if (diffHours < 24) return `hace ${diffHours}h`;
  return `hace ${diffDays}d`;
}
