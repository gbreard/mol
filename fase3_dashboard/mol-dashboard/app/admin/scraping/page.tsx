"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Database, RefreshCw, CheckCircle2, XCircle, Globe,
  TrendingUp, AlertTriangle, Loader2, Info,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { supabase } from "@/lib/supabase";

interface VpsPortalStats {
  total: number;
  ultimo_scraping: string;
  ultimos_7d: number;
  hoy: number;
}

interface VpsStats {
  total_ofertas: number;
  portales: Record<string, VpsPortalStats>;
  ultimo_scraping: string | null;
  timestamp: string;
}

interface SupabasePortalStats {
  portal: string;
  total: number;
  ultimos_7d: number;
  en_dashboard: number;
  ultimo_scraping: string;
  dias_sin_scraping: number;
}

interface HistoryDay {
  fecha: string;
  total: number;
  por_portal: Record<string, number>;
}

const PORTAL_COLORS: Record<string, string> = {
  bumeran: '#f97316', zonajobs: '#3b82f6', computrabajo: '#22c55e',
  indeed: '#a855f7', caba: '#f59e0b', portalempleo: '#14b8a6', otro: '#6b7280',
};

const PERIODO_OPTIONS = [
  { value: 7, label: '7 dias' },
  { value: 14, label: '14 dias' },
  { value: 30, label: '1 mes' },
  { value: 90, label: '3 meses' },
  { value: 365, label: 'Todo' },
];

export default function ScrapingPage() {
  const [vps, setVps] = useState<VpsStats | null>(null);
  const [supabasePortales, setSupabasePortales] = useState<SupabasePortalStats[]>([]);
  const [supabaseTotals, setSupabaseTotals] = useState<{ en_dashboard: number; sin_procesar: number }>({ en_dashboard: 0, sin_procesar: 0 });
  const [history, setHistory] = useState<HistoryDay[]>([]);
  const [loading, setLoading] = useState(true);

  const [periodoOfertas, setPeriodoOfertas] = useState(365);
  const [fechaTipo, setFechaTipo] = useState<'scraping' | 'publicacion'>('scraping');
  const [portalesVisibles, setPortalesVisibles] = useState<Set<string>>(new Set());

  const [localStatus, setLocalStatus] = useState<{
    total_ofertas: number; nlp_procesadas: number; nlp_pendientes: number;
    matching_con: number; validadas: number; en_supabase: number; pendientes_sync: number;
  } | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      if (!supabase) return;
      const [vpsResult, statsResult, localResult] = await Promise.all([
        supabase.from('scraping_live_stats').select('*').eq('id', 'current').maybeSingle(),
        supabase.rpc('get_scraping_stats'),
        supabase.from('pipeline_local_status').select('*').eq('id', 'current').maybeSingle(),
      ]);

      if (!vpsResult.error && vpsResult.data) setVps(vpsResult.data);
      if (!localResult.error && localResult.data) setLocalStatus(localResult.data);
      if (!statsResult.error && statsResult.data) {
        const d = statsResult.data as any;
        setSupabasePortales(d.portales || []);
        setSupabaseTotals({
          en_dashboard: d.totales?.en_dashboard || 0,
          sin_procesar: d.totales?.sin_procesar || 0,
        });
      }
    } catch (e) {
      console.error('Error:', e);
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory() {
    if (!supabase) return;
    const { data: dailyData } = await supabase.rpc('get_scraping_daily', {
      p_days: periodoOfertas,
      p_fecha_tipo: fechaTipo,
    });
    setHistory((dailyData as any)?.dias || []);
  }

  useEffect(() => { loadData(); }, []);
  useEffect(() => { loadHistory(); }, [periodoOfertas, fechaTipo]);

  // VPS health check
  const vpsStale = vps?.timestamp
    ? (Date.now() - new Date(vps.timestamp).getTime()) > 24 * 3600000
    : true;
  const vpsOffline = !vps || !vps.total_ofertas;

  // Merge VPS + Supabase data per portal
  const mergedPortales = useMemo(() => {
    if (!vps || !vps.portales || Object.keys(vps.portales).length === 0) {
      // Fallback to Supabase data if VPS unavailable
      return supabasePortales.map(p => ({
        portal: p.portal,
        total_vps: p.total,
        ultimo_scraping: p.ultimo_scraping,
        dias_sin_scraping: p.dias_sin_scraping,
        procesadas: p.en_dashboard,
        ultimos_7d: p.ultimos_7d,
        hoy: 0,
      }));
    }
    return Object.entries(vps.portales)
      .sort(([, a], [, b]) => b.total - a.total)
      .map(([portal, stats]) => {
        const sbData = supabasePortales.find(p => p.portal === portal);
        const daysSinceScraping = stats.ultimo_scraping
          ? Math.round((Date.now() - new Date(stats.ultimo_scraping).getTime()) / 86400000)
          : 99;
        return {
          portal,
          total_vps: stats.total,
          ultimo_scraping: stats.ultimo_scraping,
          dias_sin_scraping: daysSinceScraping,
          procesadas: sbData?.en_dashboard || 0,
          ultimos_7d: stats.ultimos_7d || 0,
          hoy: stats.hoy || 0,
        };
      });
  }, [vps, supabasePortales]);

  // Chart
  const allPortales = useMemo(() => {
    const set = new Set<string>();
    history.forEach(d => Object.keys(d.por_portal).forEach(p => set.add(p)));
    return Array.from(set).sort();
  }, [history]);

  useEffect(() => {
    if (allPortales.length > 0 && portalesVisibles.size === 0) {
      setPortalesVisibles(new Set(allPortales));
    }
  }, [allPortales]);

  const chartData = useMemo(() => {
    return history.map(d => {
      const row: Record<string, any> = { fecha: d.fecha.slice(5) };
      let total = 0;
      allPortales.forEach(p => {
        const val = portalesVisibles.has(p) ? (d.por_portal[p] || 0) : 0;
        row[p] = val;
        total += val;
      });
      row.total = total;
      return row;
    });
  }, [history, portalesVisibles, allPortales]);

  const totalPeriodo = chartData.reduce((s, d) => s + (d.total || 0), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando datos de scraping...</span>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scraping — Portales</h1>
          <p className="text-gray-500 text-sm mt-1">{mergedPortales.length} fuentes activas</p>
        </div>
        <button onClick={loadData} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
          <RefreshCw className="w-4 h-4" /> Actualizar
        </button>
      </div>

      {/* Pipeline de datos — cadena completa */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-700">Cadena de datos</h3>
          <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${vpsOffline ? 'bg-red-500' : vpsStale ? 'bg-amber-500' : 'bg-green-500'}`} />
            <span className="text-xs text-gray-500">
              VPS {vpsOffline ? 'sin datos' : vpsStale ? 'desactualizado' : 'online'}
              {vps?.timestamp && !vpsOffline && (
                <span className="text-gray-400 ml-1">
                  ({new Date(vps.timestamp).toLocaleString("es-AR")})
                </span>
              )}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 overflow-x-auto">
          <div className="bg-blue-50 rounded-lg p-3 text-center min-w-[120px]">
            <div className="text-lg font-bold text-blue-700">{vps?.total_ofertas?.toLocaleString("es-AR") || "?"}</div>
            <div className="text-xs text-blue-500">VPS (scrapeadas)</div>
          </div>
          <div className="text-gray-300 text-lg">→</div>
          <div className="bg-purple-50 rounded-lg p-3 text-center min-w-[120px]">
            <div className="text-lg font-bold text-purple-700">{localStatus?.total_ofertas?.toLocaleString("es-AR") || "?"}</div>
            <div className="text-xs text-purple-500">Local (importadas)</div>
          </div>
          <div className="text-gray-300 text-lg">→</div>
          <div className="bg-teal-50 rounded-lg p-3 text-center min-w-[120px]">
            <div className="text-lg font-bold text-teal-700">{localStatus?.nlp_procesadas?.toLocaleString("es-AR") || "?"}</div>
            <div className="text-xs text-teal-500">Con NLP</div>
          </div>
          <div className="text-gray-300 text-lg">→</div>
          <div className="bg-green-50 rounded-lg p-3 text-center min-w-[120px]">
            <div className="text-lg font-bold text-green-700">{localStatus?.validadas?.toLocaleString("es-AR") || "?"}</div>
            <div className="text-xs text-green-500">Validadas</div>
          </div>
          <div className="text-gray-300 text-lg">→</div>
          <div className="bg-gray-50 rounded-lg p-3 text-center min-w-[120px]">
            <div className="text-lg font-bold text-gray-700">{localStatus?.en_supabase?.toLocaleString("es-AR") || supabaseTotals.en_dashboard.toLocaleString("es-AR")}</div>
            <div className="text-xs text-gray-500">En Dashboard</div>
          </div>
        </div>
        {(localStatus?.nlp_pendientes || 0) > 0 && (
          <div className="mt-2 text-xs text-amber-600">
            {localStatus?.nlp_pendientes?.toLocaleString("es-AR")} ofertas pendientes de NLP
            {(localStatus?.pendientes_sync || 0) > 0 && ` · ${localStatus?.pendientes_sync?.toLocaleString("es-AR")} pendientes de sync`}
          </div>
        )}
      </div>

      {/* Alertas portales */}
      {mergedPortales.some(p => p.dias_sin_scraping > 3) && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg border bg-amber-50 border-amber-200 text-amber-800">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm">
            {mergedPortales.filter(p => p.dias_sin_scraping > 3).map(p => p.portal).join(', ')} sin scraping hace mas de 3 dias
          </span>
        </div>
      )}

      {/* Cards por portal — datos del VPS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mergedPortales.map((portal) => {
          const color = PORTAL_COLORS[portal.portal] || PORTAL_COLORS.otro;
          const isHealthy = portal.dias_sin_scraping <= 3;
          const statusColor = isHealthy ? 'text-green-600' : portal.dias_sin_scraping > 7 ? 'text-red-600' : 'text-amber-600';
          const StatusIcon = isHealthy ? CheckCircle2 : portal.dias_sin_scraping > 7 ? XCircle : AlertTriangle;
          const pct = vps?.total_ofertas ? Math.round(portal.total_vps / vps.total_ofertas * 100 * 10) / 10 : 0;

          return (
            <div key={portal.portal} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white" style={{ backgroundColor: color }}>
                  <Globe className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 capitalize">{portal.portal}</h3>
                  <p className="text-xs text-gray-500">{pct}% del total</p>
                </div>
                <StatusIcon className={`w-5 h-5 ${statusColor}`} />
              </div>

              <div className="grid grid-cols-4 gap-2 text-center">
                <div className="bg-blue-50 rounded-lg p-2">
                  <div className="text-lg font-bold text-blue-700">{portal.total_vps.toLocaleString("es-AR")}</div>
                  <div className="text-xs text-blue-500">Total VPS</div>
                </div>
                <div className="bg-green-50 rounded-lg p-2">
                  <div className="text-lg font-bold text-green-700">{portal.ultimos_7d.toLocaleString("es-AR")}</div>
                  <div className="text-xs text-green-500">7 dias</div>
                </div>
                <div className="bg-amber-50 rounded-lg p-2">
                  <div className="text-lg font-bold text-amber-700">{portal.hoy.toLocaleString("es-AR")}</div>
                  <div className="text-xs text-amber-500">Hoy</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-2">
                  <div className="text-lg font-bold text-gray-600">{portal.procesadas.toLocaleString("es-AR")}</div>
                  <div className="text-xs text-gray-400">En Dashboard</div>
                </div>
              </div>

              <div className="mt-3 text-xs text-gray-500">
                <div className="flex justify-between">
                  <span>Ultimo scraping:</span>
                  <span className={statusColor}>
                    {portal.ultimo_scraping
                      ? `${new Date(portal.ultimo_scraping).toLocaleDateString("es-AR")} (${portal.dias_sin_scraping === 0 ? 'hoy' : `hace ${portal.dias_sin_scraping}d`})`
                      : 'Sin datos'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Grafico: Ofertas por dia */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Ofertas por dia</h2>
            <p className="text-sm text-gray-500">{totalPeriodo.toLocaleString("es-AR")} ofertas en el periodo (datos procesados)</p>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center bg-gray-100 rounded-lg p-0.5">
              <button onClick={() => setFechaTipo('scraping')}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${fechaTipo === 'scraping' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'}`}>
                Fecha scraping
              </button>
              <button onClick={() => setFechaTipo('publicacion')}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${fechaTipo === 'publicacion' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'}`}>
                Fecha publicacion
              </button>
            </div>

            <div className="flex items-center gap-1">
              {PERIODO_OPTIONS.map(opt => (
                <button key={opt.value} onClick={() => setPeriodoOfertas(opt.value)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                    periodoOfertas === opt.value ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}>
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Filtro de portales */}
        <div className="flex flex-wrap gap-2 mb-4">
          {allPortales.map(portal => {
            const active = portalesVisibles.has(portal);
            const color = PORTAL_COLORS[portal] || PORTAL_COLORS.otro;
            return (
              <button key={portal} onClick={() => {
                const next = new Set(portalesVisibles);
                if (active) next.delete(portal); else next.add(portal);
                setPortalesVisibles(next);
              }}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors border ${
                  active ? 'border-transparent text-white' : 'border-gray-200 text-gray-400 bg-white'
                }`}
                style={active ? { backgroundColor: color } : {}}>
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: active ? 'white' : color }} />
                <span className="capitalize">{portal}</span>
              </button>
            );
          })}
        </div>

        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="fecha" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '12px' }}
                formatter={(value: number, name: string) => [value.toLocaleString(), name]}
                labelFormatter={(label) => `Fecha: ${label}`}
              />
              {allPortales.filter(p => portalesVisibles.has(p)).map(portal => (
                <Bar key={portal} dataKey={portal} stackId="stack"
                  fill={PORTAL_COLORS[portal] || PORTAL_COLORS.otro} name={portal} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
            Sin datos en el periodo seleccionado
          </div>
        )}
      </div>
    </div>
  );
}
