'use client';

import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { CheckCircle2, AlertTriangle, XCircle, Circle, ChevronDown, ChevronUp } from 'lucide-react';

interface PhaseComponent {
  id: string;
  name: string;
  type: string;
  model?: string;
}

interface Phase {
  id: string;
  name: string;
  description: string;
  components: PhaseComponent[];
  entryPoint: string;
  output: string;
}

interface MetricsData {
  phase1: {
    ofertas_totales: number;
    ofertas_activas: number;
    ultimo_scraping: string | null;
    dias_desde_scraping: number | null;
    fuentes: Record<string, number>;
  };
  phase2: {
    con_nlp: number;
    sin_nlp: number;
    con_matching: number;
    pendientes_matching: number;
    validadas: number;
    errores_sin_resolver: number;
    reglas_negocio: number;
  };
  phase3: {
    ofertas_supabase: number;
    pendientes_sync: number;
  };
}

type Metrics = MetricsData | null;

interface Props {
  phases: Phase[];
  metrics: Metrics;
}

type StatusType = 'healthy' | 'warning' | 'error' | 'inactive';

const STATUS_COLORS: Record<StatusType, { bg: string; border: string; text: string }> = {
  healthy: { bg: 'bg-green-50', border: 'border-green-500', text: 'text-green-700' },
  warning: { bg: 'bg-yellow-50', border: 'border-yellow-500', text: 'text-yellow-700' },
  error: { bg: 'bg-red-50', border: 'border-red-500', text: 'text-red-700' },
  inactive: { bg: 'bg-gray-50', border: 'border-gray-300', text: 'text-gray-500' }
};

const StatusIcon = ({ status }: { status: StatusType }) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    case 'warning':
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    case 'error':
      return <XCircle className="w-5 h-5 text-red-500" />;
    default:
      return <Circle className="w-5 h-5 text-gray-400" />;
  }
};

function getPhaseStatus(phaseId: string, metrics: Metrics): StatusType {
  if (!metrics) return 'inactive';

  switch (phaseId) {
    case 'phase1':
      if (metrics.phase1.dias_desde_scraping && metrics.phase1.dias_desde_scraping > 7) return 'warning';
      if (metrics.phase1.ofertas_activas === 0) return 'error';
      return 'healthy';
    case 'phase2':
      if (metrics.phase2.errores_sin_resolver > 10) return 'error';
      if (metrics.phase2.errores_sin_resolver > 0) return 'warning';
      if (metrics.phase2.sin_nlp > metrics.phase2.con_nlp * 0.1) return 'warning';
      return 'healthy';
    case 'phase3':
      if (metrics.phase3.pendientes_sync > metrics.phase3.ofertas_supabase * 0.2) return 'warning';
      return 'healthy';
    default:
      return 'inactive';
  }
}

function getPhaseMetricsSummary(phaseId: string, metrics: Metrics): string {
  if (!metrics) return 'Sin datos';

  switch (phaseId) {
    case 'phase1':
      return `${metrics.phase1.ofertas_activas.toLocaleString()} ofertas activas`;
    case 'phase2':
      const errores = metrics.phase2.errores_sin_resolver;
      if (errores > 0) return `${errores} errores pendientes`;
      return `${metrics.phase2.validadas.toLocaleString()} validadas`;
    case 'phase3':
      return `${metrics.phase3.ofertas_supabase.toLocaleString()} en Supabase`;
    default:
      return '';
  }
}

export default function PipelineFlow({ phases, metrics }: Props) {
  const [expandedPhase, setExpandedPhase] = useState<string | null>(null);

  const togglePhase = (phaseId: string) => {
    setExpandedPhase(expandedPhase === phaseId ? null : phaseId);
  };

  return (
    <div className="space-y-4">
      {/* Flow Diagram */}
      <div className="flex items-center justify-center gap-4 py-8">
        {phases.map((phase, index) => {
          const status = getPhaseStatus(phase.id, metrics);
          const colors = STATUS_COLORS[status];
          const isExpanded = expandedPhase === phase.id;

          return (
            <div key={phase.id} className="flex items-center gap-4">
              {/* Phase Card */}
              <div
                className={`relative w-64 rounded-lg border-2 ${colors.border} ${colors.bg} p-4 cursor-pointer transition-all hover:shadow-md`}
                onClick={() => togglePhase(phase.id)}
              >
                {/* Status Badge */}
                <div className="absolute -top-3 -right-3">
                  <div className="bg-white rounded-full p-1 shadow">
                    <StatusIcon status={status} />
                  </div>
                </div>

                {/* Phase Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${colors.text} bg-white/50`}>
                      FASE {index + 1}
                    </span>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-500" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  )}
                </div>

                {/* Phase Name */}
                <h3 className="font-bold text-gray-900 text-lg">{phase.name}</h3>
                <p className="text-xs text-gray-500 mt-1">{phase.description}</p>

                {/* Quick Metrics */}
                <div className={`mt-3 pt-3 border-t ${colors.border} border-opacity-30`}>
                  <p className={`text-sm font-medium ${colors.text}`}>
                    {getPhaseMetricsSummary(phase.id, metrics)}
                  </p>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                    {/* Components */}
                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 mb-2">COMPONENTES</h4>
                      <div className="space-y-1">
                        {phase.components.map(comp => (
                          <div key={comp.id} className="flex items-center gap-2 text-sm">
                            <div className="w-2 h-2 rounded-full bg-gray-400" />
                            <span>{comp.name}</span>
                            {comp.model && (
                              <span className="text-xs text-gray-400">({comp.model})</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Entry Point */}
                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 mb-1">ENTRY POINT</h4>
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {phase.entryPoint}
                      </code>
                    </div>

                    {/* Output */}
                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 mb-1">OUTPUT</h4>
                      <span className="text-xs text-gray-600">{phase.output}</span>
                    </div>

                    {/* Detailed Metrics */}
                    {metrics && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 mb-2">METRICAS</h4>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {phase.id === 'phase1' && (
                            <>
                              <div className="bg-white/50 p-2 rounded">
                                <div className="font-bold">{metrics.phase1.ofertas_totales.toLocaleString()}</div>
                                <div className="text-gray-500">Total ofertas</div>
                              </div>
                              <div className="bg-white/50 p-2 rounded">
                                <div className="font-bold">{metrics.phase1.ofertas_activas.toLocaleString()}</div>
                                <div className="text-gray-500">Activas</div>
                              </div>
                              {metrics.phase1.dias_desde_scraping !== null && (
                                <div className="bg-white/50 p-2 rounded col-span-2">
                                  <div className="font-bold">{metrics.phase1.dias_desde_scraping} dias</div>
                                  <div className="text-gray-500">Desde ultimo scraping</div>
                                </div>
                              )}
                            </>
                          )}
                          {phase.id === 'phase2' && (
                            <>
                              <div className="bg-white/50 p-2 rounded">
                                <div className="font-bold">{metrics.phase2.con_nlp.toLocaleString()}</div>
                                <div className="text-gray-500">Con NLP</div>
                              </div>
                              <div className="bg-white/50 p-2 rounded">
                                <div className="font-bold">{metrics.phase2.con_matching.toLocaleString()}</div>
                                <div className="text-gray-500">Con Matching</div>
                              </div>
                              <div className="bg-white/50 p-2 rounded">
                                <div className="font-bold">{metrics.phase2.validadas.toLocaleString()}</div>
                                <div className="text-gray-500">Validadas</div>
                              </div>
                              <div className="bg-white/50 p-2 rounded">
                                <div className={`font-bold ${metrics.phase2.errores_sin_resolver > 0 ? 'text-red-600' : ''}`}>
                                  {metrics.phase2.errores_sin_resolver}
                                </div>
                                <div className="text-gray-500">Errores</div>
                              </div>
                            </>
                          )}
                          {phase.id === 'phase3' && (
                            <>
                              <div className="bg-white/50 p-2 rounded">
                                <div className="font-bold">{metrics.phase3.ofertas_supabase.toLocaleString()}</div>
                                <div className="text-gray-500">En Supabase</div>
                              </div>
                              <div className="bg-white/50 p-2 rounded">
                                <div className={`font-bold ${metrics.phase3.pendientes_sync > 0 ? 'text-yellow-600' : ''}`}>
                                  {metrics.phase3.pendientes_sync}
                                </div>
                                <div className="text-gray-500">Pend. sync</div>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Arrow between phases */}
              {index < phases.length - 1 && (
                <div className="flex items-center">
                  <div className="w-8 h-0.5 bg-gray-300" />
                  <div className="w-0 h-0 border-t-4 border-b-4 border-l-6 border-transparent border-l-gray-300" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-green-500" />
          <span>Saludable</span>
        </div>
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
          <span>Atencion</span>
        </div>
        <div className="flex items-center gap-2">
          <XCircle className="w-4 h-4 text-red-500" />
          <span>Error</span>
        </div>
        <div className="flex items-center gap-2">
          <Circle className="w-4 h-4 text-gray-400" />
          <span>Sin datos</span>
        </div>
      </div>

      {/* Tip */}
      <p className="text-center text-xs text-gray-500 mt-4">
        Click en una fase para ver detalles y metricas
      </p>
    </div>
  );
}
