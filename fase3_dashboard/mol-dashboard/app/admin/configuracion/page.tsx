"use client";

import { useState, useEffect } from "react";
import {
  Database,
  Cloud,
  RefreshCw,
  Shield,
  Info,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Loader2,
  Server,
  HardDrive,
  Users,
  FileText,
  Zap
} from "lucide-react";
import { supabase } from "@/lib/supabase";

interface SystemStatus {
  supabaseConnected: boolean;
  ofertas: number;
  skills: number;
  ocupaciones: number;
  usuarios: number;
  issues: number;
  lastSync: string | null;
  fase1: {
    ofertas_totales: number;
    ofertas_activas: number;
    ultimo_scraping: string | null;
  };
  fase2: {
    con_nlp: number;
    con_matching: number;
    validadas: number;
  };
  fase3: {
    ofertas_supabase: number;
    pendientes_sync: number;
  };
}

interface ConfigSection {
  id: string;
  title: string;
  icon: React.ElementType;
  description: string;
}

export default function ConfiguracionPage() {
  const [activeSection, setActiveSection] = useState('estado');
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const sections: ConfigSection[] = [
    { id: 'estado', title: 'Estado del Sistema', icon: Server, description: 'Vista general en tiempo real' },
    { id: 'supabase', title: 'Supabase', icon: Cloud, description: 'Conexion y datos' },
    { id: 'pipeline', title: 'Pipeline', icon: Zap, description: 'Estado de las 3 fases' },
    { id: 'scraping', title: 'Scraping', icon: RefreshCw, description: 'Fuentes configuradas' },
    { id: 'seguridad', title: 'Seguridad', icon: Shield, description: 'Autenticacion activa' },
  ];

  async function loadStatus() {
    try {
      if (!supabase) {
        setStatus(null);
        setLoading(false);
        return;
      }

      // Test connection + get counts
      const [
        { count: ofertas },
        { count: skills },
        { count: ocupaciones },
        { count: issues },
        { data: estadoData },
      ] = await Promise.all([
        supabase.from('ofertas_dashboard').select('*', { count: 'exact', head: true }),
        supabase.from('ofertas_skills').select('*', { count: 'exact', head: true }),
        supabase.from('ocupaciones_esco').select('*', { count: 'exact', head: true }),
        supabase.from('issues').select('*', { count: 'exact', head: true }),
        supabase.from('sistema_estado').select('*').order('timestamp', { ascending: false }).limit(1),
      ]);

      const estado = estadoData?.[0];

      setStatus({
        supabaseConnected: true,
        ofertas: ofertas || 0,
        skills: skills || 0,
        ocupaciones: ocupaciones || 0,
        usuarios: 0, // Would need admin API
        issues: issues || 0,
        lastSync: estado?.timestamp || null,
        fase1: {
          ofertas_totales: estado?.fase1_ofertas_totales || 0,
          ofertas_activas: estado?.fase1_ofertas_activas || 0,
          ultimo_scraping: estado?.fase1_ultimo_scraping || null,
        },
        fase2: {
          con_nlp: estado?.fase2_con_nlp || 0,
          con_matching: estado?.fase2_con_matching || 0,
          validadas: estado?.fase2_validadas || 0,
        },
        fase3: {
          ofertas_supabase: estado?.fase3_ofertas_supabase || 0,
          pendientes_sync: estado?.fase3_pendientes_sync || 0,
        },
      });
    } catch (error) {
      console.error('Error loading status:', error);
      setStatus({
        supabaseConnected: false,
        ofertas: 0,
        skills: 0,
        ocupaciones: 0,
        usuarios: 0,
        issues: 0,
        lastSync: null,
        fase1: { ofertas_totales: 0, ofertas_activas: 0, ultimo_scraping: null },
        fase2: { con_nlp: 0, con_matching: 0, validadas: 0 },
        fase3: { ofertas_supabase: 0, pendientes_sync: 0 },
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadStatus();
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        <span className="ml-3 text-gray-600">Cargando estado del sistema...</span>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">Configuracion</h1>
            <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full flex items-center gap-1">
              <Info className="w-3 h-3" />
              Solo lectura
            </span>
          </div>
          <p className="text-gray-500 mt-1">Estado actual del sistema MOL</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      <div className="flex gap-6">
        {/* Sidebar de secciones */}
        <div className="w-64 flex-shrink-0">
          <nav className="space-y-1">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                  activeSection === section.id
                    ? 'bg-purple-100 text-purple-700'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                <section.icon className="w-5 h-5" />
                <div>
                  <p className="font-medium">{section.title}</p>
                  <p className="text-xs text-gray-500">{section.description}</p>
                </div>
              </button>
            ))}
          </nav>

          {/* Links utiles */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs font-medium text-gray-500 uppercase mb-3">Links Utiles</p>
            <div className="space-y-2">
              <a
                href="https://supabase.com/dashboard/project/uywzoyhjjofsvvsrrnek"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-purple-600"
              >
                <ExternalLink className="w-4 h-4" />
                Supabase Dashboard
              </a>
              <a
                href="https://github.com/gbreard/mol"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-purple-600"
              >
                <ExternalLink className="w-4 h-4" />
                GitHub Repo
              </a>
            </div>
          </div>
        </div>

        {/* Contenido */}
        <div className="flex-1">
          {activeSection === 'estado' && (
            <div className="space-y-6">
              {/* Connection Status */}
              <div className={`p-4 rounded-lg border ${
                status?.supabaseConnected
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {status?.supabaseConnected ? (
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    ) : (
                      <AlertCircle className="w-6 h-6 text-red-600" />
                    )}
                    <div>
                      <p className="font-semibold text-gray-900">
                        {status?.supabaseConnected ? 'Sistema Operativo' : 'Error de Conexion'}
                      </p>
                      <p className="text-sm text-gray-600">
                        {status?.lastSync
                          ? `Ultima sincronizacion: ${new Date(status.lastSync).toLocaleString()}`
                          : 'Sin datos de sincronizacion'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <FileText className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{status?.ofertas.toLocaleString()}</p>
                      <p className="text-sm text-gray-500">Ofertas en Supabase</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <Zap className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{status?.skills.toLocaleString()}</p>
                      <p className="text-sm text-gray-500">Skills</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Database className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{status?.ocupaciones.toLocaleString()}</p>
                      <p className="text-sm text-gray-500">Ocupaciones ESCO</p>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-100 rounded-lg">
                      <AlertCircle className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{status?.issues}</p>
                      <p className="text-sm text-gray-500">Issues</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Info Banner */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-900">Modo Solo Lectura</p>
                    <p className="text-sm text-blue-700 mt-1">
                      Esta pagina muestra el estado actual del sistema. Para modificar la configuracion
                      del pipeline (scraping, NLP, matching), editar los archivos JSON en el repositorio.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'supabase' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Conexion Supabase</h2>

              <div className="space-y-6">
                <div className={`flex items-center justify-between p-4 rounded-lg border ${
                  status?.supabaseConnected
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div>
                    <p className="font-medium text-gray-900">Estado de conexion</p>
                    <p className="text-sm text-gray-500">uywzoyhjjofsvvsrrnek.supabase.co</p>
                  </div>
                  <span className={`flex items-center gap-2 ${
                    status?.supabaseConnected ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {status?.supabaseConnected ? (
                      <><CheckCircle className="w-4 h-4" /> Conectado</>
                    ) : (
                      <><AlertCircle className="w-4 h-4" /> Desconectado</>
                    )}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      URL del proyecto
                    </label>
                    <input
                      type="text"
                      value={process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://...supabase.co'}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
                      readOnly
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Region
                    </label>
                    <input
                      type="text"
                      value="South America (Sao Paulo)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
                      readOnly
                    />
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Tablas en uso</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { name: 'ofertas_dashboard', count: status?.ofertas || 0 },
                      { name: 'ofertas_skills', count: status?.skills || 0 },
                      { name: 'ocupaciones_esco', count: status?.ocupaciones || 0 },
                      { name: 'issues', count: status?.issues || 0 },
                      { name: 'sistema_estado', count: '~165' },
                      { name: 'audit_log', count: 'Activo' },
                    ].map((table) => (
                      <div key={table.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <code className="text-sm text-gray-700">{table.name}</code>
                        <span className="text-sm font-medium text-gray-900">
                          {typeof table.count === 'number' ? table.count.toLocaleString() : table.count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <a
                  href="https://supabase.com/dashboard/project/uywzoyhjjofsvvsrrnek"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-purple-600 hover:text-purple-700"
                >
                  Abrir Dashboard de Supabase
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          )}

          {activeSection === 'pipeline' && (
            <div className="space-y-6">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Estado del Pipeline</h2>

                <div className="space-y-4">
                  {/* Fase 1 */}
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-blue-900">Fase 1: Adquisicion</h3>
                      <span className="text-sm text-blue-600">
                        {status?.fase1.ultimo_scraping
                          ? `Ultimo: ${status.fase1.ultimo_scraping}`
                          : 'Sin datos'
                        }
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div>
                        <p className="text-sm text-gray-600">Ofertas totales (SQLite)</p>
                        <p className="text-xl font-bold text-gray-900">{status?.fase1.ofertas_totales.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Ofertas activas</p>
                        <p className="text-xl font-bold text-gray-900">{status?.fase1.ofertas_activas.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>

                  {/* Fase 2 */}
                  <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <h3 className="font-medium text-yellow-900 mb-2">Fase 2: Procesamiento</h3>
                    <div className="grid grid-cols-3 gap-4 mt-3">
                      <div>
                        <p className="text-sm text-gray-600">Con NLP</p>
                        <p className="text-xl font-bold text-gray-900">{status?.fase2.con_nlp.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Con Matching</p>
                        <p className="text-xl font-bold text-gray-900">{status?.fase2.con_matching.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Validadas</p>
                        <p className="text-xl font-bold text-gray-900">{status?.fase2.validadas.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>

                  {/* Fase 3 */}
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <h3 className="font-medium text-green-900 mb-2">Fase 3: Presentacion</h3>
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div>
                        <p className="text-sm text-gray-600">En Supabase</p>
                        <p className="text-xl font-bold text-gray-900">{status?.fase3.ofertas_supabase.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Pendientes sync</p>
                        <p className="text-xl font-bold text-gray-900">{status?.fase3.pendientes_sync.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-sm text-gray-600">
                  <strong>Nota:</strong> Estos datos provienen de <code>sistema_estado</code> que se actualiza
                  cada vez que se ejecuta <code>sync_to_supabase.py</code>.
                </p>
              </div>
            </div>
          )}

          {activeSection === 'scraping' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Fuentes de Scraping</h2>

              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Fuentes Activas</h3>
                  <div className="space-y-2">
                    {[
                      { name: 'Bumeran', status: 'activo', url: 'bumeran.com.ar' },
                      { name: 'ZonaJobs', status: 'activo', url: 'zonajobs.com.ar' },
                      { name: 'Computrabajo', status: 'activo', url: 'computrabajo.com.ar' },
                      { name: 'Indeed', status: 'inactivo', url: 'ar.indeed.com' },
                      { name: 'LinkedIn', status: 'inactivo', url: 'linkedin.com' },
                    ].map((source) => (
                      <div key={source.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            source.status === 'activo' ? 'bg-green-500' : 'bg-gray-300'
                          }`} />
                          <div>
                            <p className="font-medium text-gray-900">{source.name}</p>
                            <p className="text-xs text-gray-500">{source.url}</p>
                          </div>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          source.status === 'activo'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-500'
                        }`}>
                          {source.status === 'activo' ? 'Activo' : 'Inactivo'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Entry Point
                    </label>
                    <input
                      type="text"
                      value="run_scheduler.py"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600 font-mono text-sm"
                      readOnly
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Modo
                    </label>
                    <input
                      type="text"
                      value="Manual (sin scheduler automatico)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
                      readOnly
                    />
                  </div>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-amber-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-amber-900">Configuracion en Python</p>
                      <p className="text-sm text-amber-700 mt-1">
                        Para activar/desactivar fuentes o cambiar frecuencia, editar <code>run_scheduler.py</code>
                        y los configs en <code>01_sources/</code>.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'seguridad' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Seguridad y Autenticacion</h2>

              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                  <div>
                    <p className="font-medium text-gray-900">Supabase Auth</p>
                    <p className="text-sm text-gray-500">Email/Password authentication</p>
                  </div>
                  <span className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    Activo
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Caracteristicas de Seguridad</h3>
                  <div className="space-y-2">
                    {[
                      { feature: 'Autenticacion por email', enabled: true },
                      { feature: 'Sesiones con JWT', enabled: true },
                      { feature: 'Row Level Security (RLS)', enabled: true },
                      { feature: 'Audit Log', enabled: true },
                      { feature: 'Autenticacion 2FA', enabled: false },
                      { feature: 'OAuth (Google, GitHub)', enabled: false },
                    ].map((item) => (
                      <div key={item.feature} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span className="text-gray-700">{item.feature}</span>
                        <span className={`flex items-center gap-1 text-sm ${
                          item.enabled ? 'text-green-600' : 'text-gray-400'
                        }`}>
                          {item.enabled ? (
                            <><CheckCircle className="w-4 h-4" /> Activo</>
                          ) : (
                            <><AlertCircle className="w-4 h-4" /> No configurado</>
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-blue-900">Gestion en Supabase</p>
                      <p className="text-sm text-blue-700 mt-1">
                        Para configurar 2FA, OAuth u otras opciones de seguridad, usar el
                        <a
                          href="https://supabase.com/dashboard/project/uywzoyhjjofsvvsrrnek/auth/providers"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="underline ml-1"
                        >
                          Dashboard de Supabase Auth
                        </a>.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
