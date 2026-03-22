"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Database,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Globe,
  TrendingUp,
  AlertTriangle,
  Loader2,
  Info,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { supabase } from "@/lib/supabase";

interface PortalStats {
  portal: string;
  total: number;
  ultimos_7d: number;
  hoy: number;
  ultima_publicacion: string;
  ultimo_scraping: string;
  dias_sin_publicacion: number;
  dias_sin_scraping: number;
  porcentaje: number;
}

interface HistoryDay {
  fecha: string;
  total: number;
  por_portal: Record<string, number>;
}

interface ScrapingData {
  portales: PortalStats[];
  totales: {
    total_ofertas: number;
    total_activas: number;
    portales_activos: number;
    ultima_fecha_global: string;
    dias_sin_datos_global: number;
    ofertas_7d: number;
    ofertas_30d: number;
  };
  alertas: { nivel: string; portal: string; mensaje: string; detalle: string }[];
}

const PORTAL_COLORS: Record<string, string> = {
  bumeran: '#f97316',
  zonajobs: '#3b82f6',
  computrabajo: '#22c55e',
  indeed: '#a855f7',
  caba: '#f59e0b',
  portalempleo: '#14b8a6',
  otro: '#6b7280',
};

const ALERTA_STYLES: Record<string, string> = {
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-amber-50 border-amber-200 text-amber-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const ALERTA_ICONS: Record<string, any> = {
  error: XCircle, warning: AlertTriangle, info: Info,
};

const PERIODO_OPTIONS = [
  { value: 7, label: '7 dias' },
  { value: 14, label: '14 dias' },
  { value: 30, label: '1 mes' },
  { value: 90, label: '3 meses' },
  { value: 365, label: 'Todo' },
];

export default function ScrapingPage() {
  const [data, setData] = useState<ScrapingData | null>(null);
  const [history, setHistory] = useState<HistoryDay[]>([]);
  const [loading, setLoading] = useState(true);

  // Filtros del gráfico
  const [periodoOfertas, setPeriodoOfertas] = useState(14);
  const [fechaTipo, setFechaTipo] = useState<'publicacion' | 'scraping'>('scraping');
  const [portalesVisibles, setPortalesVisibles] = useState<Set<string>>(new Set());

  // Todos los portales disponibles (del historial)
  const allPortales = useMemo(() => {
    const set = new Set<string>();
    history.forEach(d => Object.keys(d.por_portal).forEach(p => set.add(p)));
    return Array.from(set).sort();
  }, [history]);

  // Inicializar portales visibles cuando carguen datos
  useEffect(() => {
    if (allPortales.length > 0 && portalesVisibles.size === 0) {
      setPortalesVisibles(new Set(allPortales));
    }
  }, [allPortales]);

  // Datos del gráfico filtrados
  const chartData = useMemo(() => {
    return history.map(d => {
      const row: Record<string, any> = { fecha: d.fecha.slice(5) }; // "03-12"
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

  async function loadData() {
    setLoading(true);
    try {
      if (!supabase) return;
      const { data: statsData, error: statsErr } = await supabase.rpc('get_scraping_stats');
      if (statsErr) throw statsErr;
      setData(statsData as any);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory() {
    if (!supabase) return;
    const { data: histData } = await supabase.rpc('get_scraping_history', {
      p_days: periodoOfertas,
      p_fecha_tipo: fechaTipo,
    });
    setHistory((histData as any)?.dias || []);
  }

  useEffect(() => { loadData(); }, []);
  useEffect(() => { loadHistory(); }, [periodoOfertas, fechaTipo]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando datos de scraping...</span>
      </div>
    );
  }

  if (!data) return null;
  const { portales, totales, alertas } = data;

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scraping — Portales</h1>
          <p className="text-gray-500 text-sm mt-1">
            {totales.portales_activos} fuentes — {totales.total_ofertas.toLocaleString()} ofertas totales
          </p>
        </div>
        <button onClick={loadData} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
          <RefreshCw className="w-4 h-4" /> Actualizar
        </button>
      </div>

      {/* Alertas */}
      {alertas.length > 0 && (
        <div className="space-y-2">
          {alertas.map((alerta, idx) => {
            const AlertIcon = ALERTA_ICONS[alerta.nivel] || Info;
            const style = ALERTA_STYLES[alerta.nivel] || ALERTA_STYLES.info;
            return (
              <div key={idx} className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${style}`}>
                <AlertIcon className="w-5 h-5 flex-shrink-0" />
                <div className="flex-1">
                  <span className="text-sm font-medium">{alerta.mensaje}</span>
                  {alerta.detalle && <span className="text-xs opacity-70 ml-2">{alerta.detalle}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Cards por portal */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {portales.map((portal) => {
          const color = PORTAL_COLORS[portal.portal] || PORTAL_COLORS.otro;
          const isHealthy = portal.dias_sin_scraping <= 3;
          const statusColor = isHealthy ? 'text-green-600' : portal.dias_sin_scraping > 7 ? 'text-red-600' : 'text-amber-600';
          const StatusIcon = isHealthy ? CheckCircle2 : portal.dias_sin_scraping > 7 ? XCircle : AlertTriangle;

          return (
            <div key={portal.portal} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white" style={{ backgroundColor: color }}>
                  <Globe className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 capitalize">{portal.portal}</h3>
                  <p className="text-xs text-gray-500">{portal.porcentaje}% del total</p>
                </div>
                <StatusIcon className={`w-5 h-5 ${statusColor}`} />
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="bg-gray-50 rounded-lg p-2">
                  <div className="text-lg font-bold text-gray-900">{portal.total.toLocaleString()}</div>
                  <div className="text-xs text-gray-500">Total</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-2">
                  <div className="text-lg font-bold text-gray-900">{portal.ultimos_7d.toLocaleString()}</div>
                  <div className="text-xs text-gray-500">7 dias</div>
                </div>
              </div>

              <div className="mt-3 space-y-1 text-xs text-gray-500">
                <div className="flex justify-between">
                  <span>Scraping:</span>
                  <span className={statusColor}>
                    {portal.ultimo_scraping} ({portal.dias_sin_scraping === 0 ? 'hoy' : `hace ${portal.dias_sin_scraping}d`})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Publicacion:</span>
                  <span>{portal.ultima_publicacion} ({portal.dias_sin_publicacion === 0 ? 'hoy' : `hace ${portal.dias_sin_publicacion}d`})</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Gráfico: Ofertas por dia */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        {/* Header con filtros */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Ofertas por dia</h2>
            <p className="text-sm text-gray-500">{totalPeriodo.toLocaleString()} ofertas en el periodo</p>
          </div>

          <div className="flex items-center gap-4">
            {/* Toggle fecha tipo */}
            <div className="flex items-center bg-gray-100 rounded-lg p-0.5">
              <button
                onClick={() => setFechaTipo('scraping')}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  fechaTipo === 'scraping' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'
                }`}
              >
                Fecha scraping
              </button>
              <button
                onClick={() => setFechaTipo('publicacion')}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  fechaTipo === 'publicacion' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'
                }`}
              >
                Fecha publicacion
              </button>
            </div>

            {/* Periodo */}
            <div className="flex items-center gap-1">
              {PERIODO_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setPeriodoOfertas(opt.value)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                    periodoOfertas === opt.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
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
              <button
                key={portal}
                onClick={() => {
                  const next = new Set(portalesVisibles);
                  if (active) next.delete(portal); else next.add(portal);
                  setPortalesVisibles(next);
                }}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors border ${
                  active ? 'border-transparent text-white' : 'border-gray-200 text-gray-400 bg-white'
                }`}
                style={active ? { backgroundColor: color } : {}}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: active ? 'white' : color }} />
                <span className="capitalize">{portal}</span>
              </button>
            );
          })}
        </div>

        {/* Gráfico Recharts */}
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
                <Bar
                  key={portal}
                  dataKey={portal}
                  stackId="stack"
                  fill={PORTAL_COLORS[portal] || PORTAL_COLORS.otro}
                  name={portal}
                />
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
