"use client";

import { useState, useEffect } from "react";
import {
  Users,
  Database,
  FileText,
  Activity,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Loader2
} from "lucide-react";
import { supabase } from "@/lib/supabase";

interface AdminStats {
  totalOfertas: number;
  totalSkills: number;
  usuariosActivos: number;
  ultimoScraping: string | null;
  ofertasHoy: number;
  erroresPendientes: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [sistemaEstado, setSistemaEstado] = useState<any>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        // Obtener estadísticas de ofertas
        const { count: totalOfertas } = await supabase
          .from('ofertas')
          .select('*', { count: 'exact', head: true });

        // Obtener total de skills
        const { count: totalSkills } = await supabase
          .from('ofertas_skills')
          .select('*', { count: 'exact', head: true });

        // Obtener estado del sistema
        const { data: estadoData } = await supabase
          .from('sistema_estado')
          .select('*')
          .order('timestamp', { ascending: false })
          .limit(1)
          .single();

        // Ofertas de hoy
        const today = new Date().toISOString().split('T')[0];
        const { count: ofertasHoy } = await supabase
          .from('ofertas')
          .select('*', { count: 'exact', head: true })
          .gte('fecha_publicacion_iso', today);

        setStats({
          totalOfertas: totalOfertas || 0,
          totalSkills: totalSkills || 0,
          usuariosActivos: 1, // TODO: implementar con auth.users
          ultimoScraping: estadoData?.fase1_ultimo_scraping || null,
          ofertasHoy: ofertasHoy || 0,
          erroresPendientes: estadoData?.fase2_errores_sin_resolver || 0
        });

        setSistemaEstado(estadoData);
      } catch (error) {
        console.error('Error cargando stats:', error);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  const statCards = [
    {
      label: "Total Ofertas",
      value: stats?.totalOfertas.toLocaleString() || "0",
      icon: FileText,
      color: "bg-blue-500",
      trend: `+${stats?.ofertasHoy || 0} hoy`
    },
    {
      label: "Skills Extraídas",
      value: stats?.totalSkills.toLocaleString() || "0",
      icon: Database,
      color: "bg-green-500",
      trend: "En base de datos"
    },
    {
      label: "Usuarios Activos",
      value: stats?.usuariosActivos.toString() || "0",
      icon: Users,
      color: "bg-purple-500",
      trend: "Conectados"
    },
    {
      label: "Errores Pendientes",
      value: stats?.erroresPendientes.toString() || "0",
      icon: AlertCircle,
      color: stats?.erroresPendientes ? "bg-red-500" : "bg-gray-400",
      trend: stats?.erroresPendientes ? "Requieren atención" : "Sin errores"
    }
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Panel de Administración</h1>
        <p className="text-gray-500 mt-1">Resumen del estado del sistema MOL</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, idx) => (
          <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <span className="text-xs text-gray-500">{stat.trend}</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{stat.value}</h3>
            <p className="text-sm text-gray-500">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Estado del Sistema */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fase 1: Scraping */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-500" />
            Fase 1: Adquisición (Scraping)
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Ofertas totales</span>
              <span className="font-semibold">{sistemaEstado?.fase1_ofertas_totales?.toLocaleString() || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Ofertas activas</span>
              <span className="font-semibold text-green-600">{sistemaEstado?.fase1_ofertas_activas?.toLocaleString() || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Ofertas cerradas</span>
              <span className="font-semibold text-gray-500">{sistemaEstado?.fase1_ofertas_cerradas?.toLocaleString() || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Último scraping</span>
              <span className="font-semibold">{sistemaEstado?.fase1_ultimo_scraping || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Días desde scraping</span>
              <span className={`font-semibold ${sistemaEstado?.fase1_dias_desde_scraping > 1 ? 'text-amber-600' : 'text-green-600'}`}>
                {sistemaEstado?.fase1_dias_desde_scraping || '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Fase 2: Procesamiento */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-500" />
            Fase 2: Procesamiento (NLP + Matching)
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Con NLP</span>
              <span className="font-semibold text-green-600">{sistemaEstado?.fase2_con_nlp?.toLocaleString() || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Sin NLP</span>
              <span className="font-semibold text-amber-600">{sistemaEstado?.fase2_sin_nlp?.toLocaleString() || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Con Matching</span>
              <span className="font-semibold text-green-600">{sistemaEstado?.fase2_con_matching?.toLocaleString() || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Validadas</span>
              <span className="font-semibold text-blue-600">{sistemaEstado?.fase2_validadas?.toLocaleString() || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Reglas de negocio</span>
              <span className="font-semibold">{sistemaEstado?.fase2_reglas_negocio || '-'}</span>
            </div>
          </div>
        </div>

        {/* Fase 3: Presentación */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-purple-500" />
            Fase 3: Presentación (Dashboard)
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Ofertas en Supabase</span>
              <span className="font-semibold text-green-600">{sistemaEstado?.fase3_ofertas_supabase?.toLocaleString() || '-'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Pendientes de sync</span>
              <span className={`font-semibold ${sistemaEstado?.fase3_pendientes_sync > 0 ? 'text-amber-600' : 'text-green-600'}`}>
                {sistemaEstado?.fase3_pendientes_sync?.toLocaleString() || '-'}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Versión sync</span>
              <span className="font-semibold">{sistemaEstado?.sync_version || '-'}</span>
            </div>
          </div>
        </div>

        {/* Fase Sugerida */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-amber-500" />
            Próxima Acción Sugerida
          </h2>
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-amber-600 mt-0.5" />
              <div>
                <p className="font-semibold text-amber-900">
                  {sistemaEstado?.fase_sugerida_nombre || 'Sin sugerencia'}
                </p>
                <p className="text-sm text-amber-700 mt-1">
                  {sistemaEstado?.fase_sugerida_razon || 'Sistema actualizado'}
                </p>
              </div>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Última actualización: {sistemaEstado?.timestamp ? new Date(sistemaEstado.timestamp).toLocaleString() : '-'}
          </p>
        </div>
      </div>
    </div>
  );
}
