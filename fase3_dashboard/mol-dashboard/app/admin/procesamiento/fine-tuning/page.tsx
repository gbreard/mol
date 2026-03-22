"use client";

import { useState, useEffect } from "react";
import {
  Loader2, RefreshCw, CheckCircle2, AlertTriangle, XCircle,
  TrendingUp, Database, Target, Users, Zap,
} from "lucide-react";

interface ReadinessCheck {
  label: string;
  ok: boolean;
  detail: string;
}

interface GroupDist {
  group: string;
  name: string;
  count: number;
  pct: number;
}

interface TopIsco {
  isco_code: string;
  count: number;
}

interface Gap {
  group: string;
  name: string;
  count: number;
}

interface Autor {
  name: string;
  count: number;
}

interface ReadinessData {
  total_pairs: number;
  distinct_isco: number;
  groups_covered: number;
  isco_with_min_pairs: number;
  recent_30d: number;
  readiness: {
    ready: boolean;
    level: string;
    checks: ReadinessCheck[];
    passed: number;
    total: number;
  };
  suggestions: string[];
  distribution: {
    by_group: GroupDist[];
    top_isco: TopIsco[];
    gaps: Gap[];
  };
  autores: Autor[];
  fecha_datos: string | null;
}

const LEVEL_CONFIG: Record<string, { color: string; bg: string; icon: typeof CheckCircle2; label: string }> = {
  ready: { color: "text-green-700", bg: "bg-green-50 border-green-200", icon: CheckCircle2, label: "Listo para fine-tuning" },
  almost: { color: "text-blue-700", bg: "bg-blue-50 border-blue-200", icon: TrendingUp, label: "Casi listo" },
  partial: { color: "text-amber-700", bg: "bg-amber-50 border-amber-200", icon: AlertTriangle, label: "Progreso parcial" },
  insufficient: { color: "text-red-700", bg: "bg-red-50 border-red-200", icon: XCircle, label: "Datos insuficientes" },
};

const GROUP_COLORS: Record<string, string> = {
  '1': 'bg-purple-500', '2': 'bg-blue-500', '3': 'bg-cyan-500', '4': 'bg-teal-500',
  '5': 'bg-green-500', '6': 'bg-lime-500', '7': 'bg-amber-500', '8': 'bg-orange-500',
  '9': 'bg-red-500', '0': 'bg-gray-500',
};

export default function FineTuningPage() {
  const [data, setData] = useState<ReadinessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/training-readiness");
      if (!res.ok) throw new Error((await res.json()).error || "Error cargando datos");
      setData(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Analizando datos de entrenamiento...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <XCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 text-sm">{error}</span>
          <button onClick={loadData} className="ml-auto text-red-600 hover:bg-red-100 p-1 rounded">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const levelConf = LEVEL_CONFIG[data.readiness.level] || LEVEL_CONFIG.insufficient;
  const LevelIcon = levelConf.icon;
  const maxGroupCount = Math.max(...data.distribution.by_group.map(g => g.count), 1);

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fine-Tuning Readiness</h1>
          <p className="text-gray-500 text-sm mt-1">
            Estado del dataset de entrenamiento para fine-tuning del modelo de clasificacion ESCO
          </p>
        </div>
        <button onClick={loadData} className="flex items-center gap-2 text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm">
          <RefreshCw className="w-4 h-4" /> Actualizar
        </button>
      </div>

      {/* Readiness banner */}
      <div className={`flex items-start gap-4 p-5 rounded-xl border ${levelConf.bg}`}>
        <LevelIcon className={`w-8 h-8 ${levelConf.color} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <h2 className={`text-lg font-bold ${levelConf.color}`}>{levelConf.label}</h2>
          <p className="text-sm text-gray-600 mt-1">
            {data.readiness.passed}/{data.readiness.total} criterios cumplidos
          </p>
          <div className="mt-3 space-y-1.5">
            {data.readiness.checks.map((check, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                {check.ok
                  ? <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                  : <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                }
                <span className={check.ok ? "text-gray-700" : "text-gray-500"}>{check.label}</span>
                <span className="text-xs text-gray-400">({check.detail})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KPI icon={Database} label="Pares totales" value={data.total_pairs} color="blue" />
        <KPI icon={Target} label="ISCOs distintos" value={data.distinct_isco} color="purple" />
        <KPI icon={Zap} label="Grupos cubiertos" value={`${data.groups_covered}/10`} color="green" />
        <KPI icon={TrendingUp} label="Ultimos 30 dias" value={data.recent_30d} color="amber" />
        <KPI icon={Users} label="Contribuyentes" value={data.autores.length} color="cyan" />
      </div>

      {/* Suggestions */}
      {data.suggestions.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <h3 className="font-semibold text-amber-900 text-sm mb-2">Sugerencias</h3>
          <ul className="space-y-1">
            {data.suggestions.map((s, i) => (
              <li key={i} className="text-sm text-amber-800 flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">-</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribution by group */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Distribucion por grupo ISCO</h3>
          <div className="space-y-2">
            {data.distribution.by_group.map((g) => (
              <div key={g.group} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-4 text-right font-mono">{g.group}</span>
                <span className="text-xs text-gray-700 w-28 truncate">{g.name}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${GROUP_COLORS[g.group] || 'bg-gray-400'} transition-all`}
                    style={{ width: `${Math.max(g.count / maxGroupCount * 100, 2)}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-16 text-right">{g.count} ({g.pct}%)</span>
              </div>
            ))}
          </div>

          {data.distribution.gaps.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-100">
              <p className="text-xs text-red-500 font-medium">Sub-representados ({`<`}3%):</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {data.distribution.gaps.map((g) => (
                  <span key={g.group} className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full">
                    {g.name} ({g.count})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Top ISCOs */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Top 15 ISCOs con mas pares</h3>
          <div className="space-y-1.5">
            {data.distribution.top_isco.map((isco, i) => (
              <div key={isco.isco_code} className="flex items-center gap-2 text-sm">
                <span className="text-xs text-gray-400 w-5 text-right">{i + 1}.</span>
                <span className="font-mono text-blue-700 font-bold w-12">{isco.isco_code}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${Math.max(isco.count / (data.distribution.top_isco[0]?.count || 1) * 100, 3)}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-8 text-right">{isco.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Contributors */}
      {data.autores.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-900 mb-3">Contribuyentes</h3>
          <div className="flex flex-wrap gap-3">
            {data.autores.map((a) => (
              <div key={a.name} className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
                <Users className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-700">{a.name}</span>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">{a.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer info */}
      <div className="text-xs text-gray-400 text-center">
        Datos basados en issues resueltos de Supabase
        {data.fecha_datos && ` — ultimo: ${new Date(data.fecha_datos).toLocaleDateString("es-AR")}`}
      </div>
    </div>
  );
}

function KPI({ icon: Icon, label, value, color }: { icon: any; label: string; value: string | number; color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-700",
    purple: "bg-purple-50 text-purple-700",
    green: "bg-green-50 text-green-700",
    amber: "bg-amber-50 text-amber-700",
    cyan: "bg-cyan-50 text-cyan-700",
  };
  return (
    <div className={`rounded-xl p-4 ${colors[color] || colors.blue}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 opacity-60" />
        <span className="text-xs font-medium opacity-75">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
