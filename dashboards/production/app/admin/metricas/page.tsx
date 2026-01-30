"use client";

import { useState, useEffect } from "react";
import {
  BarChart3,
  TrendingUp,
  Users,
  FileText,
  Activity,
  Loader2,
  RefreshCw
} from "lucide-react";
import { supabase } from "@/lib/supabase";

interface Metricas {
  totalOfertas: number;
  totalSkills: number;
  ofertasConNLP: number;
  ofertasConMatching: number;
  validadas: number;
  pendientes: number;
  skillsPromedio: number;
  ocupacionesUnicas: number;
}

export default function MetricasPage() {
  const [metricas, setMetricas] = useState<Metricas | null>(null);
  const [loading, setLoading] = useState(true);
  const [distribucionOcupaciones, setDistribucionOcupaciones] = useState<any[]>([]);
  const [distribucionSkills, setDistribucionSkills] = useState<any[]>([]);

  useEffect(() => {
    loadMetricas();
  }, []);

  async function loadMetricas() {
    try {
      // Total ofertas
      const { count: totalOfertas } = await supabase
        .from('ofertas')
        .select('*', { count: 'exact', head: true });

      // Total skills
      const { count: totalSkills } = await supabase
        .from('ofertas_skills')
        .select('*', { count: 'exact', head: true });

      // Estado del sistema
      const { data: estado } = await supabase
        .from('sistema_estado')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(1)
        .single();

      // Ocupaciones únicas
      const { data: ocupaciones } = await supabase
        .from('ofertas')
        .select('isco_code')
        .not('isco_code', 'is', null);

      const ocupacionesUnicas = new Set(ocupaciones?.map(o => o.isco_code)).size;

      // Skills promedio por oferta
      const skillsPromedio = totalOfertas && totalSkills
        ? Math.round((totalSkills / totalOfertas) * 10) / 10
        : 0;

      setMetricas({
        totalOfertas: totalOfertas || 0,
        totalSkills: totalSkills || 0,
        ofertasConNLP: estado?.fase2_con_nlp || 0,
        ofertasConMatching: estado?.fase2_con_matching || 0,
        validadas: estado?.fase2_validadas || 0,
        pendientes: estado?.fase2_pendientes_validacion || 0,
        skillsPromedio,
        ocupacionesUnicas
      });

      // Distribución por ISCO (top 10)
      const { data: distOcup } = await supabase
        .from('vw_distribucion_isco')
        .select('*')
        .limit(10);

      if (distOcup) {
        setDistribucionOcupaciones(distOcup);
      }

      // Distribución skills por L1
      const { data: distSkills } = await supabase
        .from('ofertas_skills')
        .select('l1, l1_nombre');

      if (distSkills) {
        const counts: Record<string, { nombre: string; count: number }> = {};
        distSkills.forEach(s => {
          const key = s.l1 || 'Sin categoría';
          if (!counts[key]) {
            counts[key] = { nombre: s.l1_nombre || key, count: 0 };
          }
          counts[key].count++;
        });

        const sorted = Object.entries(counts)
          .map(([l1, data]) => ({ l1, ...data }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 10);

        setDistribucionSkills(sorted);
      }

    } catch (error) {
      console.error('Error cargando métricas:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  const metricCards = [
    { label: "Total Ofertas", value: metricas?.totalOfertas.toLocaleString(), icon: FileText, color: "bg-blue-500" },
    { label: "Total Skills", value: metricas?.totalSkills.toLocaleString(), icon: Activity, color: "bg-green-500" },
    { label: "Ocupaciones ESCO", value: metricas?.ocupacionesUnicas.toString(), icon: BarChart3, color: "bg-purple-500" },
    { label: "Skills/Oferta", value: metricas?.skillsPromedio.toFixed(1), icon: TrendingUp, color: "bg-amber-500" },
  ];

  const pipelineStats = [
    { label: "Con NLP", value: metricas?.ofertasConNLP || 0, total: metricas?.totalOfertas || 1 },
    { label: "Con Matching", value: metricas?.ofertasConMatching || 0, total: metricas?.totalOfertas || 1 },
    { label: "Validadas", value: metricas?.validadas || 0, total: metricas?.totalOfertas || 1 },
  ];

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Métricas del Sistema</h1>
          <p className="text-gray-500 mt-1">Análisis del pipeline y datos procesados</p>
        </div>
        <button
          onClick={() => { setLoading(true); loadMetricas(); }}
          className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
        >
          <RefreshCw className="w-5 h-5" />
          Actualizar
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metricCards.map((metric, idx) => (
          <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`${metric.color} p-3 rounded-lg`}>
                <metric.icon className="w-6 h-6 text-white" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{metric.value}</h3>
            <p className="text-sm text-gray-500">{metric.label}</p>
          </div>
        ))}
      </div>

      {/* Pipeline Progress */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Progreso del Pipeline</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {pipelineStats.map((stat, idx) => {
            const percentage = Math.round((stat.value / stat.total) * 100);
            return (
              <div key={idx}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-700">{stat.label}</span>
                  <span className="text-sm text-gray-500">
                    {stat.value.toLocaleString()} / {stat.total.toLocaleString()} ({percentage}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-purple-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Ocupaciones */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Ocupaciones ESCO</h2>
          <div className="space-y-3">
            {distribucionOcupaciones.map((ocup, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-sm font-medium text-gray-500 w-6">{idx + 1}.</span>
                  <span className="text-sm text-gray-700 truncate" title={ocup.isco_label}>
                    {ocup.isco_label}
                  </span>
                </div>
                <span className="text-sm font-semibold text-gray-900 ml-2">
                  {ocup.total?.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Distribución Skills por L1 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Skills por Categoría (L1)</h2>
          <div className="space-y-3">
            {distribucionSkills.map((skill, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-600 w-10 text-center">
                  {skill.l1}
                </span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-700 truncate" title={skill.nombre}>
                      {skill.nombre}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {skill.count.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-green-500 h-1.5 rounded-full"
                      style={{ width: `${Math.min((skill.count / (distribucionSkills[0]?.count || 1)) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
