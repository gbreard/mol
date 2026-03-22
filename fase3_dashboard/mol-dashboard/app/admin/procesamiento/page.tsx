"use client";

import { useState, useEffect } from "react";
import {
  Brain,
  GitMerge,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  RefreshCw,
  TrendingUp,
  Cloud,
} from "lucide-react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { supabase } from "@/lib/supabase";

interface ProcessingKPIs {
  nlp: { procesadas: number; pendientes: number; total: number; porcentaje: number };
  matching: { con_matching: number; pendientes: number; validadas: number };
  sync: { en_supabase: number; pendientes: number };
  ultimo_run: string;
}

interface ErrorByType {
  error_tipo: string;
  total: number;
  resueltos: number;
  pendientes: number;
  severidad_predominante: string;
}

const PIE_COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

const SEV_COLORS: Record<string, string> = {
  error: 'bg-red-100 text-red-700',
  alto: 'bg-red-100 text-red-700',
  medio: 'bg-amber-100 text-amber-700',
  warning: 'bg-amber-100 text-amber-700',
  bajo: 'bg-blue-100 text-blue-700',
  info: 'bg-gray-100 text-gray-600',
};

export default function ProcesamientoPage() {
  const [kpis, setKpis] = useState<ProcessingKPIs | null>(null);
  const [errores, setErrores] = useState<ErrorByType[]>([]);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try {
      if (!supabase) return;
      const { data, error } = await supabase.rpc('get_processing_metrics', { p_days: 90 });
      if (error) throw error;
      setKpis((data as any)?.kpis || null);
      setErrores((data as any)?.errores_por_tipo || []);
      setTimeline((data as any)?.timeline || []);
    } catch (e) {
      console.error('Error:', e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando métricas de procesamiento...</span>
      </div>
    );
  }

  // Matching method distribution for pie chart
  const lastRun = timeline.length > 0 ? timeline[timeline.length - 1] : null;
  const matchingPie = lastRun ? [
    { name: 'Por regla', value: lastRun.matching_por_regla || 0 },
    { name: 'Por semántico', value: lastRun.matching_por_semantico || 0 },
  ].filter(d => d.value > 0) : [];

  // Errors for bar chart
  const errorChart = errores.slice(0, 10).map(e => ({
    tipo: e.error_tipo.replace('error_', '').replace(/_/g, ' ').slice(0, 25),
    Pendientes: e.pendientes,
    Resueltos: e.resueltos,
  }));

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Procesamiento</h1>
          <p className="text-gray-500 text-sm mt-1">
            NLP + Matching + Validación — último run: {kpis?.ultimo_run || '—'}
          </p>
        </div>
        <button onClick={loadData} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
          <RefreshCw className="w-4 h-4" /> Actualizar
        </button>
      </div>

      {/* Pipeline progress bars */}
      {kpis && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Estado del pipeline</h2>
          <div className="space-y-4">
            <ProgressRow
              icon={Brain} label="NLP" color="blue"
              current={kpis.nlp.procesadas} total={kpis.nlp.total}
              detail={kpis.nlp.pendientes > 0 ? `${kpis.nlp.pendientes.toLocaleString()} pendientes` : 'Completo'}
              alert={kpis.nlp.pendientes > 0}
            />
            <ProgressRow
              icon={GitMerge} label="Matching" color="green"
              current={kpis.matching.con_matching} total={kpis.nlp.procesadas}
              detail={kpis.matching.pendientes > 0 ? `${kpis.matching.pendientes.toLocaleString()} pendientes` : 'Completo'}
              alert={kpis.matching.pendientes > 0}
            />
            <ProgressRow
              icon={CheckCircle2} label="Validadas" color="purple"
              current={kpis.matching.validadas} total={kpis.matching.con_matching}
              detail={`${kpis.matching.validadas.toLocaleString()} ofertas validadas`}
            />
            <ProgressRow
              icon={Cloud} label="En Supabase" color="teal"
              current={kpis.sync.en_supabase} total={kpis.matching.validadas}
              detail={kpis.sync.pendientes > 0 ? `${kpis.sync.pendientes.toLocaleString()} pendientes sync` : 'Sincronizado'}
              alert={kpis.sync.pendientes > 0}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Matching method pie */}
        {matchingPie.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Método de matching</h2>
            <div className="flex items-center gap-6">
              <ResponsiveContainer width="50%" height={200}>
                <PieChart>
                  <Pie data={matchingPie} dataKey="value" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}>
                    {matchingPie.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => v.toLocaleString()} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-3">
                {matchingPie.map((d, i) => (
                  <div key={d.name} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PIE_COLORS[i] }} />
                    <span className="text-sm text-gray-700">{d.name}</span>
                    <span className="text-sm font-bold text-gray-900">{d.value.toLocaleString()}</span>
                  </div>
                ))}
                {lastRun && (
                  <div className="pt-2 border-t border-gray-100">
                    <div className="text-xs text-gray-500">
                      Dual coinciden: {lastRun.matching_dual_coinciden?.toLocaleString() || 0}
                    </div>
                    <div className="text-xs text-gray-500">
                      Dual difieren: {lastRun.matching_dual_difieren?.toLocaleString() || 0}
                    </div>
                    <div className="text-xs text-gray-500">
                      Score promedio: {lastRun.matching_score_promedio?.toFixed(3) || '—'}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Errors by type */}
        {errores.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Errores por tipo</h2>
            {errorChart.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={errorChart} layout="vertical" margin={{ left: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="tipo" tick={{ fontSize: 10 }} width={100} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Resueltos" stackId="a" fill="#22c55e" />
                  <Bar dataKey="Pendientes" stackId="a" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            ) : null}
          </div>
        )}
      </div>

      {/* Error detail table */}
      {errores.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Detalle de errores</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 pr-4 text-gray-500 font-medium">Tipo</th>
                  <th className="text-right py-2 px-3 text-gray-500 font-medium">Total</th>
                  <th className="text-right py-2 px-3 text-gray-500 font-medium">Resueltos</th>
                  <th className="text-right py-2 px-3 text-gray-500 font-medium">Pendientes</th>
                  <th className="text-center py-2 px-3 text-gray-500 font-medium">Severidad</th>
                </tr>
              </thead>
              <tbody>
                {errores.map(e => (
                  <tr key={e.error_tipo} className="border-b border-gray-100">
                    <td className="py-2 pr-4 text-gray-900 font-mono text-xs">{e.error_tipo}</td>
                    <td className="py-2 px-3 text-right">{e.total.toLocaleString()}</td>
                    <td className="py-2 px-3 text-right text-green-600">{e.resueltos.toLocaleString()}</td>
                    <td className="py-2 px-3 text-right font-medium text-red-600">{e.pendientes.toLocaleString()}</td>
                    <td className="py-2 px-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${SEV_COLORS[e.severidad_predominante] || SEV_COLORS.info}`}>
                        {e.severidad_predominante}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function ProgressRow({ icon: Icon, label, color, current, total, detail, alert = false }: {
  icon: any; label: string; color: string; current: number; total: number; detail: string; alert?: boolean;
}) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-600', green: 'bg-green-600', purple: 'bg-purple-600', teal: 'bg-teal-600',
  };
  const iconColorMap: Record<string, string> = {
    blue: 'text-blue-600', green: 'text-green-600', purple: 'text-purple-600', teal: 'text-teal-600',
  };

  return (
    <div className="flex items-center gap-4">
      <Icon className={`w-5 h-5 ${iconColorMap[color]} flex-shrink-0`} />
      <div className="w-24 text-sm font-medium text-gray-700">{label}</div>
      <div className="flex-1">
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div className={`${colorMap[color]} h-3 rounded-full transition-all`} style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="w-16 text-right text-sm font-bold text-gray-900">{pct}%</div>
      <div className={`w-48 text-xs text-right ${alert ? 'text-amber-600 font-medium' : 'text-gray-500'}`}>
        {current.toLocaleString()} / {total.toLocaleString()} — {detail}
      </div>
    </div>
  );
}
