"use client";

import { useState, useEffect, useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Loader2,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  RotateCcw,
  Clock,
  Activity,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from "recharts";
import { supabase } from "@/lib/supabase";

interface DinamicaDay {
  fecha: string;
  ofertas_nuevas: number;
  ofertas_bajas: number;
  ofertas_republicadas: number;
  ofertas_activas: number;
  flujo_neto: number;
  vida_media_dias: number | null;
  tasa_rotacion: number;
  tasa_republicacion: number;
}

interface DinamicaKPIs {
  total_nuevas: number;
  total_bajas: number;
  total_republicadas: number;
  flujo_neto_periodo: number;
  activas_actual: number;
  tasa_rotacion_promedio: number;
  tasa_republicacion_promedio: number;
  vida_media_promedio: number;
  dias_con_datos: number;
}

const PERIODO_OPTIONS = [
  { value: 7, label: '7 dias' },
  { value: 14, label: '14 dias' },
  { value: 30, label: '1 mes' },
  { value: 90, label: '3 meses' },
  { value: 365, label: 'Todo' },
];

export default function DinamicaPage() {
  const [dias, setDias] = useState<DinamicaDay[]>([]);
  const [kpis, setKpis] = useState<DinamicaKPIs | null>(null);
  const [periodo, setPeriodo] = useState(365);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try {
      if (!supabase) return;
      const { data, error } = await supabase.rpc('get_scraping_dinamica', { p_days: periodo });
      if (error) throw error;
      setDias((data as any)?.dias || []);
      setKpis((data as any)?.kpis || null);
    } catch (e) {
      console.error('Error:', e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, [periodo]);

  const chartData = useMemo(() => {
    return dias.map(d => ({
      fecha: d.fecha.slice(5),
      Nuevas: d.ofertas_nuevas,
      Bajas: -d.ofertas_bajas, // negativo para mostrar abajo
      Republicadas: d.ofertas_republicadas,
      flujo_neto: d.flujo_neto,
    }));
  }, [dias]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando dinámica del mercado...</span>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scraping — Dinámica del mercado</h1>
          <p className="text-gray-500 text-sm mt-1">
            Flujo de ofertas: nuevas, bajas, republicaciones
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            {PERIODO_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setPeriodo(opt.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                  periodo === opt.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <button onClick={loadData} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
            <RefreshCw className="w-4 h-4" /> Actualizar
          </button>
        </div>
      </div>

      {/* KPIs */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            label="Nuevas en periodo"
            value={kpis.total_nuevas}
            icon={ArrowUpRight}
            color="green"
          />
          <KPICard
            label="Bajas en periodo"
            value={kpis.total_bajas}
            icon={ArrowDownRight}
            color="red"
          />
          <KPICard
            label="Flujo neto"
            value={kpis.flujo_neto_periodo}
            icon={kpis.flujo_neto_periodo >= 0 ? TrendingUp : TrendingDown}
            color={kpis.flujo_neto_periodo >= 0 ? 'green' : 'red'}
            prefix={kpis.flujo_neto_periodo > 0 ? '+' : ''}
          />
          <KPICard
            label="Activas actual"
            value={kpis.activas_actual || 0}
            icon={Activity}
            color="blue"
          />
        </div>
      )}

      {/* Gráfico principal: Nuevas vs Bajas */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Flujo de ofertas</h2>
        <p className="text-sm text-gray-500 mb-4">Barras arriba = nuevas, barras abajo = bajas</p>

        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }} stackOffset="sign">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '12px' }}
                formatter={(value: number, name: string) => [Math.abs(value).toLocaleString(), name]}
                labelFormatter={(label) => `Fecha: ${label}`}
              />
              <ReferenceLine y={0} stroke="#9ca3af" strokeWidth={1} />
              <Legend />
              <Bar dataKey="Nuevas" stackId="flow" fill="#22c55e" />
              <Bar dataKey="Bajas" stackId="flow" fill="#ef4444" />
              <Bar dataKey="Republicadas" fill="#f59e0b" opacity={0.7} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
            Sin datos en el periodo seleccionado
          </div>
        )}
      </div>

      {/* Indicadores secundarios */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center gap-2 mb-2">
              <RotateCcw className="w-4 h-4 text-amber-600" />
              <span className="text-sm font-medium text-gray-700">Tasa de rotacion</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {(kpis.tasa_rotacion_promedio * 100).toFixed(0)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Bajas / activas (promedio del periodo)
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {kpis.tasa_rotacion_promedio > 0.4 ? 'Alta rotacion — mercado dinámico' :
               kpis.tasa_rotacion_promedio > 0.15 ? 'Rotacion moderada' :
               'Baja rotacion — ofertas permanecen'}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center gap-2 mb-2">
              <Minus className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">Tasa de republicacion</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {(kpis.tasa_republicacion_promedio * 100).toFixed(0)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Republicadas / total (promedio del periodo)
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {kpis.tasa_republicacion_promedio > 0.15 ? 'Alta — puestos dificiles de cubrir' :
               kpis.tasa_republicacion_promedio > 0.05 ? 'Normal — algunas repiten' :
               'Baja — pocas se republicaron'}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Vida media oferta</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {kpis.vida_media_promedio > 0 ? `${kpis.vida_media_promedio} dias` : '—'}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Mediana de dias activa antes de baja
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {kpis.vida_media_promedio > 30 ? 'Larga permanencia — baja demanda o nicho' :
               kpis.vida_media_promedio > 14 ? 'Duración normal' :
               kpis.vida_media_promedio > 0 ? 'Corta — alta demanda, se cubren rápido' : ''}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function KPICard({ label, value, icon: Icon, color, prefix = '' }: {
  label: string; value: number; icon: any; color: string; prefix?: string;
}) {
  const colorMap: Record<string, string> = {
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    blue: 'bg-blue-100 text-blue-600',
    amber: 'bg-amber-100 text-amber-600',
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
        {prefix}{value.toLocaleString()}
      </div>
    </div>
  );
}
