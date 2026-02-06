'use client';

import { Database, Cpu, Cloud, CheckCircle2, AlertTriangle, XCircle, ArrowRight } from 'lucide-react';

interface Phase1Metrics {
  total: number;
  active: number;
  lastRun: string | null;
  daysSince: number | null;
}

interface Phase2Metrics {
  conNlp: number;
  sinNlp: number;
  conMatching: number;
  validadas: number;
  errores: number;
  reglas: number;
}

interface Phase3Metrics {
  enSupabase: number;
  pendientesSync: number;
}

type Metrics = Phase1Metrics | Phase2Metrics | Phase3Metrics;

interface Props {
  phase: 1 | 2 | 3;
  name: string;
  metrics: Metrics;
  details?: Record<string, number>;
}

const PHASE_ICONS = {
  1: Database,
  2: Cpu,
  3: Cloud
};

// Fix: Use static class mappings for Tailwind JIT
const PHASE_STYLES = {
  1: {
    headerBg: 'bg-blue-50',
    headerBorder: 'border-blue-100',
    iconBg: 'bg-blue-100',
    iconText: 'text-blue-600',
    accent: 'text-blue-600',
    ring: 'ring-blue-500'
  },
  2: {
    headerBg: 'bg-purple-50',
    headerBorder: 'border-purple-100',
    iconBg: 'bg-purple-100',
    iconText: 'text-purple-600',
    accent: 'text-purple-600',
    ring: 'ring-purple-500'
  },
  3: {
    headerBg: 'bg-green-50',
    headerBorder: 'border-green-100',
    iconBg: 'bg-green-100',
    iconText: 'text-green-600',
    accent: 'text-green-600',
    ring: 'ring-green-500'
  }
};

function getStatus(phase: number, metrics: Metrics): 'healthy' | 'warning' | 'error' {
  if (phase === 1) {
    const m = metrics as Phase1Metrics;
    if (m.daysSince && m.daysSince > 7) return 'warning';
    if (m.active === 0) return 'error';
    return 'healthy';
  }
  if (phase === 2) {
    const m = metrics as Phase2Metrics;
    if (m.errores > 10) return 'error';
    if (m.errores > 0 || m.sinNlp > m.conNlp * 0.1) return 'warning';
    return 'healthy';
  }
  if (phase === 3) {
    const m = metrics as Phase3Metrics;
    if (m.pendientesSync > m.enSupabase * 0.2) return 'warning';
    return 'healthy';
  }
  return 'healthy';
}

const StatusBadge = ({ status }: { status: 'healthy' | 'warning' | 'error' }) => {
  const config = {
    healthy: { icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-50 border-green-200', label: 'OK' },
    warning: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-50 border-yellow-200', label: 'Atencion' },
    error: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50 border-red-200', label: 'Error' }
  };
  const { icon: Icon, color, bg, label } = config[status];
  return (
    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${bg}`}>
      <Icon className={`w-4 h-4 ${color}`} />
      <span className={`text-xs font-medium ${color}`}>{label}</span>
    </div>
  );
};

// Progress bar component
const ProgressBar = ({ value, max, color = 'blue' }: { value: number; max: number; color?: string }) => {
  const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  };
  return (
    <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${colorClasses[color] || 'bg-blue-500'}`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

export default function PhaseStatusCard({ phase, name, metrics, details }: Props) {
  const Icon = PHASE_ICONS[phase];
  const styles = PHASE_STYLES[phase];
  const status = getStatus(phase, metrics);

  const renderMetrics = () => {
    if (phase === 1) {
      const m = metrics as Phase1Metrics;
      const activePercentage = m.total > 0 ? ((m.active / m.total) * 100).toFixed(0) : 0;
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{m.total.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Total ofertas</div>
            </div>
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
              <div className="text-2xl font-bold text-blue-600">{m.active.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Activas ({activePercentage}%)</div>
            </div>
          </div>

          {m.total > 0 && (
            <div>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Activas vs Total</span>
                <span>{activePercentage}%</span>
              </div>
              <ProgressBar value={m.active} max={m.total} color="blue" />
            </div>
          )}

          {m.lastRun && (
            <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-50 p-2 rounded-lg">
              <span>Ultimo scraping:</span>
              <span className="font-medium">{new Date(m.lastRun).toLocaleDateString()}</span>
              {m.daysSince !== null && (
                <span className={`px-1.5 py-0.5 rounded ${m.daysSince > 7 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100'}`}>
                  {m.daysSince}d
                </span>
              )}
            </div>
          )}

          {details && Object.keys(details).length > 0 && (
            <div className="border-t pt-3">
              <h4 className="text-xs font-semibold text-gray-500 mb-2">Por fuente</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(details).map(([source, count]) => (
                  <div key={source} className="flex justify-between bg-gray-50 px-2 py-1.5 rounded">
                    <span className="text-gray-600 capitalize">{source}</span>
                    <span className="font-medium">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    if (phase === 2) {
      const m = metrics as Phase2Metrics;
      const nlpPercentage = m.conNlp > 0 ? ((m.validadas / m.conNlp) * 100).toFixed(0) : 0;
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{m.conNlp.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Con NLP</div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg border border-purple-100">
              <div className="text-2xl font-bold text-purple-600">{m.conMatching.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Con Matching</div>
            </div>
          </div>

          {/* Pipeline flow mini visualization */}
          <div className="flex items-center justify-between text-xs bg-gray-50 p-2 rounded-lg">
            <div className="text-center">
              <div className="font-bold text-gray-700">{m.conNlp.toLocaleString()}</div>
              <div className="text-gray-400">NLP</div>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300" />
            <div className="text-center">
              <div className="font-bold text-gray-700">{m.conMatching.toLocaleString()}</div>
              <div className="text-gray-400">Match</div>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300" />
            <div className="text-center">
              <div className="font-bold text-green-600">{m.validadas.toLocaleString()}</div>
              <div className="text-gray-400">Valid</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="bg-green-50 border border-green-100 p-2 rounded-lg text-center">
              <div className="text-lg font-bold text-green-600">{m.validadas.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Validadas</div>
            </div>
            <div className={`${m.errores > 0 ? 'bg-red-50 border border-red-100' : 'bg-gray-50'} p-2 rounded-lg text-center`}>
              <div className={`text-lg font-bold ${m.errores > 0 ? 'text-red-600' : 'text-gray-600'}`}>
                {m.errores}
              </div>
              <div className="text-xs text-gray-500">Errores</div>
            </div>
            <div className="bg-gray-50 p-2 rounded-lg text-center">
              <div className="text-lg font-bold text-gray-600">{m.reglas}</div>
              <div className="text-xs text-gray-500">Reglas</div>
            </div>
          </div>

          {m.conNlp > 0 && (
            <div>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Validadas de NLP</span>
                <span>{nlpPercentage}%</span>
              </div>
              <ProgressBar value={m.validadas} max={m.conNlp} color="purple" />
            </div>
          )}

          {m.sinNlp > 0 && (
            <div className="flex items-center gap-2 text-xs text-yellow-700 bg-yellow-50 border border-yellow-100 p-2 rounded-lg">
              <AlertTriangle className="w-4 h-4" />
              <span>{m.sinNlp.toLocaleString()} ofertas sin procesar NLP</span>
            </div>
          )}
        </div>
      );
    }

    if (phase === 3) {
      const m = metrics as Phase3Metrics;
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-green-50 p-3 rounded-lg border border-green-100">
              <div className="text-2xl font-bold text-green-600">{m.enSupabase.toLocaleString()}</div>
              <div className="text-xs text-gray-500">En Supabase</div>
            </div>
            <div className={`${m.pendientesSync > 0 ? 'bg-yellow-50 border border-yellow-100' : 'bg-gray-50'} p-3 rounded-lg`}>
              <div className={`text-2xl font-bold ${m.pendientesSync > 0 ? 'text-yellow-600' : 'text-gray-600'}`}>
                {m.pendientesSync}
              </div>
              <div className="text-xs text-gray-500">Pend. sync</div>
            </div>
          </div>

          {m.enSupabase > 0 && (
            <div>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Sincronizadas</span>
                <span>100%</span>
              </div>
              <ProgressBar value={m.enSupabase} max={m.enSupabase} color="green" />
            </div>
          )}

          {m.pendientesSync > 0 && (
            <div className="flex items-center gap-2 text-xs text-yellow-700 bg-yellow-50 border border-yellow-100 p-2 rounded-lg">
              <AlertTriangle className="w-4 h-4" />
              <span>Ejecutar <code className="bg-yellow-100 px-1 rounded">sync_to_supabase.py</code></span>
            </div>
          )}

          {m.pendientesSync === 0 && m.enSupabase > 0 && (
            <div className="flex items-center gap-2 text-xs text-green-700 bg-green-50 border border-green-100 p-2 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
              <span>Todo sincronizado con Supabase</span>
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow`}>
      {/* Header */}
      <div className={`${styles.headerBg} px-4 py-3 border-b ${styles.headerBorder}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 ${styles.iconBg} rounded-lg`}>
              <Icon className={`w-5 h-5 ${styles.iconText}`} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Fase {phase}</h3>
              <p className="text-xs text-gray-500">{name}</p>
            </div>
          </div>
          <StatusBadge status={status} />
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {renderMetrics()}
      </div>
    </div>
  );
}
