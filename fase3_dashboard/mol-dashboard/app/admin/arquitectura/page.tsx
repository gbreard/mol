'use client';

import { useEffect, useState, useCallback } from 'react';
import { Map, GitBranch, Activity, Loader2, RefreshCw } from 'lucide-react';
import ScreenMapGraph from '@/components/admin/ScreenMapGraph';
import PipelineFlow from '@/components/admin/PipelineFlow';
import PhaseStatusCard from '@/components/admin/PhaseStatusCard';

type TabId = 'screens' | 'pipeline' | 'metrics';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const TABS: Tab[] = [
  {
    id: 'screens',
    label: 'Mapa de Pantallas',
    icon: <Map className="w-5 h-5" />,
    description: 'Ver todas las páginas del dashboard y sus conexiones'
  },
  {
    id: 'pipeline',
    label: 'Pipeline de Datos',
    icon: <GitBranch className="w-5 h-5" />,
    description: 'Ver las 3 fases del pipeline con estado en tiempo real'
  },
  {
    id: 'metrics',
    label: 'Métricas en Vivo',
    icon: <Activity className="w-5 h-5" />,
    description: 'Estado actual del sistema con auto-refresh'
  }
];

interface ArchitectureData {
  pages: Array<{
    id: string;
    path: string;
    label: string;
    type: string;
    description: string;
    components: string[];
    dataSource: string[];
  }>;
  apiRoutes: Array<{
    id: string;
    path: string;
    method: string;
    description: string;
    usedBy: string[];
  }>;
  connections: Array<{
    from: string;
    to: string;
    type: string;
    label: string;
  }>;
  pipeline: {
    phases: Array<{
      id: string;
      name: string;
      description: string;
      components: Array<{
        id: string;
        name: string;
        type: string;
        model?: string;
      }>;
      entryPoint: string;
      output: string;
    }>;
  };
}

interface ArchitectureMetrics {
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
  suggested: {
    fase: number;
    nombre: string;
    razon: string;
  };
  timestamp: string;
}

export default function AdminArchitecturePage() {
  const [activeTab, setActiveTab] = useState<TabId>('screens');
  const [architectureData, setArchitectureData] = useState<ArchitectureData | null>(null);
  const [metrics, setMetrics] = useState<ArchitectureMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Load static architecture data
  useEffect(() => {
    fetch('/data/dashboard_architecture.json')
      .then(res => res.json())
      .then(data => {
        setArchitectureData(data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Error loading architecture data:', err);
        setIsLoading(false);
      });
  }, []);

  // Load metrics from API
  const loadMetrics = useCallback(async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) setIsRefreshing(true);
    try {
      const res = await fetch('/api/admin/architecture-metrics');
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
        setLastUpdate(new Date());
      }
    } catch (err) {
      console.error('Error loading metrics:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Initial metrics load
  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  // Auto-refresh every 30 seconds when on metrics tab
  useEffect(() => {
    if (activeTab === 'metrics' || activeTab === 'pipeline') {
      const interval = setInterval(() => loadMetrics(), 30000);
      return () => clearInterval(interval);
    }
  }, [activeTab, loadMetrics]);

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        <span className="ml-3 text-gray-600">Cargando arquitectura...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Arquitectura del Sistema</h1>
          <p className="text-gray-500 mt-1">
            Visualización de pantallas, pipeline y estado del sistema MOL
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdate && (
            <span className="text-sm text-gray-500">
              Actualizado: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={() => loadMetrics(true)}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab description */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <p className="text-sm text-gray-600">
            {TABS.find(t => t.id === activeTab)?.description}
          </p>
        </div>

        {/* Tab content */}
        <div className="p-6">
          {activeTab === 'screens' && architectureData && (
            <ScreenMapGraph
              pages={architectureData.pages}
              apiRoutes={architectureData.apiRoutes}
              connections={architectureData.connections}
            />
          )}

          {activeTab === 'pipeline' && architectureData && (
            <PipelineFlow
              phases={architectureData.pipeline.phases}
              metrics={metrics}
            />
          )}

          {activeTab === 'metrics' && (
            <div className="space-y-6">
              {metrics ? (
                <>
                  {/* Suggested Action */}
                  {metrics.suggested && (
                    <div className={`p-4 rounded-lg border-l-4 ${
                      metrics.suggested.fase === 1 ? 'bg-blue-50 border-blue-500' :
                      metrics.suggested.fase === 2 ? 'bg-yellow-50 border-yellow-500' :
                      'bg-green-50 border-green-500'
                    }`}>
                      <h3 className="font-semibold text-gray-900">
                        Accion Sugerida: Fase {metrics.suggested.fase} - {metrics.suggested.nombre}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">{metrics.suggested.razon}</p>
                    </div>
                  )}

                  {/* Phase Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <PhaseStatusCard
                      phase={1}
                      name="Adquisicion"
                      metrics={{
                        total: metrics.phase1.ofertas_totales,
                        active: metrics.phase1.ofertas_activas,
                        lastRun: metrics.phase1.ultimo_scraping,
                        daysSince: metrics.phase1.dias_desde_scraping
                      }}
                      details={metrics.phase1.fuentes}
                    />
                    <PhaseStatusCard
                      phase={2}
                      name="Procesamiento"
                      metrics={{
                        conNlp: metrics.phase2.con_nlp,
                        sinNlp: metrics.phase2.sin_nlp,
                        conMatching: metrics.phase2.con_matching,
                        validadas: metrics.phase2.validadas,
                        errores: metrics.phase2.errores_sin_resolver,
                        reglas: metrics.phase2.reglas_negocio
                      }}
                    />
                    <PhaseStatusCard
                      phase={3}
                      name="Presentacion"
                      metrics={{
                        enSupabase: metrics.phase3.ofertas_supabase,
                        pendientesSync: metrics.phase3.pendientes_sync
                      }}
                    />
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
                  <span className="ml-3 text-gray-600">Cargando métricas...</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
