"use client";

import { useState, useEffect } from "react";
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
  ExternalLink,
} from "lucide-react";
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
  history: { fecha: string; total: number; por_portal: Record<string, number> }[];
}

const PORTAL_COLORS: Record<string, { bg: string; text: string }> = {
  bumeran: { bg: 'bg-orange-500', text: 'text-orange-600' },
  zonajobs: { bg: 'bg-blue-500', text: 'text-blue-600' },
  computrabajo: { bg: 'bg-green-500', text: 'text-green-600' },
  indeed: { bg: 'bg-purple-500', text: 'text-purple-600' },
  caba: { bg: 'bg-amber-500', text: 'text-amber-600' },
  portalempleo: { bg: 'bg-teal-500', text: 'text-teal-600' },
};

const ALERTA_STYLES: Record<string, string> = {
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-amber-50 border-amber-200 text-amber-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const ALERTA_ICONS: Record<string, any> = {
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

export default function ScrapingPage() {
  const [data, setData] = useState<ScrapingData | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try {
      if (!supabase) return;

      const [statsResult, historyResult] = await Promise.all([
        supabase.rpc('get_scraping_stats'),
        supabase.rpc('get_scraping_history', { p_days: 14 }),
      ]);

      if (statsResult.error) throw statsResult.error;

      setData({
        ...(statsResult.data as any),
        history: (historyResult.data as any)?.dias || [],
      });
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando datos de scraping...</span>
      </div>
    );
  }

  if (!data) return null;

  const { portales, totales, alertas, history } = data;

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scraping — Portales</h1>
          <p className="text-gray-500 text-sm mt-1">
            {totales.portales_activos} fuentes activas — {totales.total_ofertas.toLocaleString()} ofertas totales
            — ultimo dato: {totales.ultima_fecha_global || 'N/A'}
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
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
          const colors = PORTAL_COLORS[portal.portal] || { bg: 'bg-gray-500', text: 'text-gray-600' };
          const isHealthy = portal.dias_sin_scraping <= 3;
          const statusColor = isHealthy ? 'text-green-600' : portal.dias_sin_scraping > 7 ? 'text-red-600' : 'text-amber-600';
          const StatusIcon = isHealthy ? CheckCircle2 : portal.dias_sin_scraping > 7 ? XCircle : AlertTriangle;

          return (
            <div key={portal.portal} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 ${colors.bg} rounded-lg flex items-center justify-center text-white`}>
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

      {/* Historial diario */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-green-500" />
          Ofertas por dia (ultimos 14 dias)
        </h2>
        {history.length > 0 ? (
          <div className="space-y-2">
            {history.map((dia, idx) => {
              const maxTotal = Math.max(...history.map(d => d.total));
              return (
                <div key={dia.fecha} className="flex items-center gap-4">
                  <span className="text-sm text-gray-600 w-24 flex-shrink-0">{dia.fecha}</span>
                  <div className="flex-1 flex items-center gap-1 h-6">
                    {Object.entries(dia.por_portal).map(([portal, count]) => {
                      const pct = (count / maxTotal) * 100;
                      const color = PORTAL_COLORS[portal]?.bg || 'bg-gray-400';
                      return pct > 0.5 ? (
                        <div
                          key={portal}
                          className={`${color} h-5 rounded-sm`}
                          style={{ width: `${pct}%` }}
                          title={`${portal}: ${count}`}
                        />
                      ) : null;
                    })}
                  </div>
                  <span className="text-sm font-medium text-gray-900 w-16 text-right">
                    {dia.total.toLocaleString()}
                  </span>
                </div>
              );
            })}
            {/* Leyenda */}
            <div className="flex gap-4 mt-3 pt-3 border-t border-gray-100">
              {Object.entries(PORTAL_COLORS).map(([portal, colors]) => (
                <div key={portal} className="flex items-center gap-1.5">
                  <div className={`w-3 h-3 rounded-sm ${colors.bg}`} />
                  <span className="text-xs text-gray-500 capitalize">{portal}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400">Sin datos en los ultimos 14 dias</p>
        )}
      </div>
    </div>
  );
}
