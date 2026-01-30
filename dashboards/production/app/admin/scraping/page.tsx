"use client";

import { useState, useEffect } from "react";
import {
  Database,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Globe,
  TrendingUp,
  AlertTriangle,
  Loader2,
  Calendar
} from "lucide-react";
import { supabase } from "@/lib/supabase";

interface ScrapingStats {
  fase1_ofertas_totales: number;
  fase1_ofertas_activas: number;
  fase1_ofertas_cerradas: number;
  fase1_ultimo_scraping: string;
  fase1_dias_desde_scraping: number;
  fase1_fuentes: string;
}

interface OfertasPorPortal {
  portal: string;
  cantidad: number;
  porcentaje: number;
}

interface OfertasPorFecha {
  fecha: string;
  cantidad: number;
}

// Helper para convertir cualquier valor a string seguro para React
function safeString(value: unknown): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return value.toString();
  if (typeof value === 'object') {
    return Object.keys(value).join(', ');
  }
  return String(value);
}

export default function ScrapingPage() {
  const [stats, setStats] = useState<ScrapingStats | null>(null);
  const [porPortal, setPorPortal] = useState<OfertasPorPortal[]>([]);
  const [porFecha, setPorFecha] = useState<OfertasPorFecha[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      // Estado del sistema
      const { data: estadoData } = await supabase
        .from('sistema_estado')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(1)
        .single();

      if (estadoData) {
        // Convertir fase1_fuentes a string - SIEMPRE
        let fuentes: string = 'bumeran, zonajobs, computrabajo';
        const rawFuentes = estadoData.fase1_fuentes;
        if (rawFuentes) {
          if (typeof rawFuentes === 'string') {
            fuentes = rawFuentes;
          } else if (typeof rawFuentes === 'object' && rawFuentes !== null) {
            // Es un objeto, extraer las keys
            fuentes = Object.keys(rawFuentes).join(', ');
          }
        }

        setStats({
          fase1_ofertas_totales: estadoData.fase1_ofertas_totales || 0,
          fase1_ofertas_activas: estadoData.fase1_ofertas_activas || 0,
          fase1_ofertas_cerradas: estadoData.fase1_ofertas_cerradas || 0,
          fase1_ultimo_scraping: estadoData.fase1_ultimo_scraping || '-',
          fase1_dias_desde_scraping: estadoData.fase1_dias_desde_scraping || 0,
          fase1_fuentes: fuentes
        });
      }

      // Ofertas por portal
      const { data: ofertas } = await supabase
        .from('ofertas')
        .select('portal');

      if (ofertas) {
        const counts: Record<string, number> = {};
        ofertas.forEach(o => {
          const portal = o.portal || 'desconocido';
          counts[portal] = (counts[portal] || 0) + 1;
        });

        const total = ofertas.length;
        const portalData = Object.entries(counts)
          .map(([portal, cantidad]) => ({
            portal,
            cantidad,
            porcentaje: Math.round((cantidad / total) * 100)
          }))
          .sort((a, b) => b.cantidad - a.cantidad);

        setPorPortal(portalData);
      }

      // Ofertas por fecha (últimos 7 días)
      const { data: ofertasFecha } = await supabase
        .from('ofertas')
        .select('fecha_publicacion_iso')
        .order('fecha_publicacion_iso', { ascending: false })
        .limit(1000);

      if (ofertasFecha) {
        const countsByDate: Record<string, number> = {};
        ofertasFecha.forEach(o => {
          const fecha = o.fecha_publicacion_iso?.split('T')[0] || 'sin fecha';
          countsByDate[fecha] = (countsByDate[fecha] || 0) + 1;
        });

        const fechaData = Object.entries(countsByDate)
          .map(([fecha, cantidad]) => ({ fecha, cantidad }))
          .sort((a, b) => b.fecha.localeCompare(a.fecha))
          .slice(0, 14);

        setPorFecha(fechaData);
      }

    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  }

  const getPortalColor = (portal: string) => {
    const colors: Record<string, string> = {
      bumeran: 'bg-orange-500',
      zonajobs: 'bg-blue-500',
      computrabajo: 'bg-green-500',
      indeed: 'bg-purple-500',
      linkedin: 'bg-sky-500'
    };
    return colors[portal] || 'bg-gray-500';
  };

  const getPortalIcon = (portal: string) => {
    return <Globe className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Estado del Scraping</h1>
          <p className="text-gray-500 mt-1">Monitoreo de la adquisición de datos</p>
        </div>
        <button
          onClick={() => { setLoading(true); loadData(); }}
          className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
        >
          <RefreshCw className="w-5 h-5" />
          Actualizar
        </button>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-blue-100 p-3 rounded-lg">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
            {stats?.fase1_dias_desde_scraping === 0 ? (
              <CheckCircle className="w-5 h-5 text-green-500" />
            ) : stats && stats.fase1_dias_desde_scraping > 1 ? (
              <AlertTriangle className="w-5 h-5 text-amber-500" />
            ) : (
              <Clock className="w-5 h-5 text-gray-400" />
            )}
          </div>
          <h3 className="text-2xl font-bold text-gray-900">
            {stats?.fase1_ofertas_totales.toLocaleString() || '0'}
          </h3>
          <p className="text-sm text-gray-500">Ofertas totales</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-green-100 p-3 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-green-600">
            {stats?.fase1_ofertas_activas.toLocaleString() || '0'}
          </h3>
          <p className="text-sm text-gray-500">Ofertas activas</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-gray-100 p-3 rounded-lg">
              <XCircle className="w-6 h-6 text-gray-600" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-gray-600">
            {stats?.fase1_ofertas_cerradas.toLocaleString() || '0'}
          </h3>
          <p className="text-sm text-gray-500">Ofertas cerradas</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${stats && stats.fase1_dias_desde_scraping > 1 ? 'bg-amber-100' : 'bg-green-100'}`}>
              <Calendar className={`w-6 h-6 ${stats && stats.fase1_dias_desde_scraping > 1 ? 'text-amber-600' : 'text-green-600'}`} />
            </div>
          </div>
          <h3 className={`text-2xl font-bold ${stats && stats.fase1_dias_desde_scraping > 1 ? 'text-amber-600' : 'text-green-600'}`}>
            {stats?.fase1_dias_desde_scraping || '0'} días
          </h3>
          <p className="text-sm text-gray-500">Desde último scraping</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ofertas por Portal */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-500" />
            Ofertas por Portal
          </h2>
          <div className="space-y-4">
            {porPortal.map((item) => (
              <div key={item.portal} className="flex items-center gap-4">
                <div className={`w-10 h-10 ${getPortalColor(item.portal)} rounded-lg flex items-center justify-center text-white`}>
                  {getPortalIcon(item.portal)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900 capitalize">{item.portal}</span>
                    <span className="text-sm text-gray-500">{item.cantidad.toLocaleString()} ({item.porcentaje}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`${getPortalColor(item.portal)} h-2 rounded-full transition-all duration-500`}
                      style={{ width: `${item.porcentaje}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Ofertas por Fecha */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-500" />
            Ofertas por Fecha (últimos 14 días)
          </h2>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {porFecha.map((item, idx) => (
              <div key={item.fecha} className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className={`text-sm ${idx === 0 ? 'font-semibold text-gray-900' : 'text-gray-600'}`}>
                  {item.fecha}
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${Math.min((item.cantidad / (porFecha[0]?.cantidad || 1)) * 100, 100)}%` }}
                    />
                  </div>
                  <span className={`text-sm font-medium w-16 text-right ${idx === 0 ? 'text-green-600' : 'text-gray-600'}`}>
                    {item.cantidad}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Info del Scraping */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Información del Sistema</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">Último scraping</p>
              <p className="font-semibold text-gray-900">{stats?.fase1_ultimo_scraping || '-'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">Fuentes activas</p>
              <p className="font-semibold text-gray-900">{safeString(stats?.fase1_fuentes)}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 mb-1">Tasa de actualización</p>
              <p className="font-semibold text-gray-900">
                {porFecha[0]?.cantidad || 0} ofertas/día
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
