'use client';

import { Database, Cpu, Cloud, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

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

const PHASE_STYLES = {
  1: { headerBg: 'bg-blue-50', headerBorder: 'border-blue-100', iconBg: 'bg-blue-100', iconText: 'text-blue-600' },
  2: { headerBg: 'bg-purple-50', headerBorder: 'border-purple-100', iconBg: 'bg-purple-100', iconText: 'text-purple-600' },
  3: { headerBg: 'bg-green-50', headerBorder: 'border-green-100', iconBg: 'bg-green-100', iconText: 'text-green-600' },
} as const;

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
    healthy: { icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-50', label: 'OK' },
    warning: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-50', label: 'Atencion' },
    error: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50', label: 'Error' }
  };
  const { icon: Icon, color, bg, label } = config[status];
  return (
    <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${bg}`}>
      <Icon className={`w-4 h-4 ${color}`} />
      <span className={`text-xs font-medium ${color}`}>{label}</span>
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
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{m.total.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Total ofertas</div>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{m.active.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Activas</div>
            </div>
          </div>
          {m.lastRun && (
            <div className="text-xs text-gray-500">
              Ultima publicacion: {new Date(m.lastRun).toLocaleDateString()}
              {m.daysSince !== null && (
                <span className={m.daysSince > 7 ? 'text-yellow-600 font-medium ml-1' : 'ml-1'}>
                  ({m.daysSince} dias)
                </span>
              )}
            </div>
          )}
          {details && Object.keys(details).length > 0 && (
            <div className="border-t pt-3 mt-3">
              <h4 className="text-xs font-semibold text-gray-500 mb-2">Por fuente</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(details).map(([source, count]) => (
                  <div key={source} className="flex justify-between">
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
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{m.conNlp.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Con NLP</div>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{m.conMatching.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Con Matching</div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-green-50 p-2 rounded-lg text-center">
              <div className="text-lg font-bold text-green-600">{m.validadas.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Validadas</div>
            </div>
            <div className={`${m.errores > 0 ? 'bg-red-50' : 'bg-gray-50'} p-2 rounded-lg text-center`}>
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
          {m.sinNlp > 0 && (
            <div className="text-xs text-yellow-600">
              {m.sinNlp.toLocaleString()} ofertas sin procesar NLP
            </div>
          )}
        </div>
      );
    }

    if (phase === 3) {
      const m = metrics as Phase3Metrics;
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{m.enSupabase.toLocaleString()}</div>
              <div className="text-xs text-gray-500">En Supabase</div>
            </div>
            <div className={`${m.pendientesSync > 0 ? 'bg-yellow-50' : 'bg-gray-50'} p-3 rounded-lg`}>
              <div className={`text-2xl font-bold ${m.pendientesSync > 0 ? 'text-yellow-600' : 'text-gray-600'}`}>
                {m.pendientesSync}
              </div>
              <div className="text-xs text-gray-500">Pend. sync</div>
            </div>
          </div>
          {m.pendientesSync > 0 && (
            <div className="text-xs text-yellow-600">
              Ejecutar sync_to_supabase.py para sincronizar
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className={`${styles.headerBg} px-4 py-3 border-b ${styles.headerBorder}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
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
