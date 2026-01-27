'use client';

import { useState, useEffect } from 'react';
import Filters from '@/components/Filters';
import InsightCard from '@/components/InsightCard';
import KPICard from '@/components/KPICard';
import EvolucionChart from '@/components/charts/EvolucionChart';
import OcupacionesChart from '@/components/charts/OcupacionesChart';
import GeografiaChart from '@/components/charts/GeografiaChart';
import {
  getKPIs,
  getEvolucion,
  getDistribucionGeografica,
  getTopOcupaciones,
  DashboardKPIs,
  EvolucionData,
  GeografiaData,
  OcupacionData
} from '@/lib/supabase';

export default function PanoramaGeneral() {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [evolucion, setEvolucion] = useState<EvolucionData[]>([]);
  const [geografia, setGeografia] = useState<GeografiaData[]>([]);
  const [ocupaciones, setOcupaciones] = useState<OcupacionData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [kpisData, evolucionData, geografiaData, ocupacionesData] = await Promise.all([
          getKPIs(),
          getEvolucion(),
          getDistribucionGeografica(),
          getTopOcupaciones()
        ]);

        setKpis(kpisData);
        setEvolucion(evolucionData);
        setGeografia(geografiaData);
        setOcupaciones(ocupacionesData);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // Generar insights dinámicos basados en los datos
  const getInsights = () => {
    if (!kpis || geografia.length === 0) {
      return {
        totalText: 'Cargando datos...',
        topJurisdiccion: 'Cargando...',
        modalidadText: 'Cargando...'
      };
    }

    const topDos = geografia.slice(0, 2);
    const porcentajeTopDos = topDos.reduce((sum, g) => sum + g.porcentaje, 0);

    return {
      totalText: `${kpis.total_ofertas.toLocaleString('es-AR')} ofertas analizadas en el sistema`,
      topJurisdiccion: topDos.length >= 2
        ? `${topDos[0].jurisdiccion} y ${topDos[1].jurisdiccion} concentran ${porcentajeTopDos.toFixed(0)}% de ofertas`
        : 'Datos insuficientes',
      modalidadText: `${kpis.ofertas_remotas} remotas, ${kpis.ofertas_hibridas} híbridas, ${kpis.ofertas_presenciales} presenciales`
    };
  };

  const insights = getInsights();

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-10 w-64 bg-gray-200 rounded mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-28 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-80 bg-gray-200 rounded-lg"></div>
            <div className="h-80 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filtros */}
      <Filters />

      {/* Insights destacados */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InsightCard
          title="Total ofertas"
          description={insights.totalText}
          icon="📊"
          color="blue"
        />
        <InsightCard
          title="Modalidad de trabajo"
          description={insights.modalidadText}
          icon="💼"
          color="green"
        />
        <InsightCard
          title="Concentración geográfica"
          description={insights.topJurisdiccion}
          icon="📍"
          color="purple"
        />
      </div>

      {/* KPIs principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard
          title="Ofertas analizadas"
          value={kpis?.total_ofertas || 0}
        />
        <KPICard
          title="Ocupaciones identificadas"
          value={kpis?.ocupaciones_distintas || 0}
        />
        <KPICard
          title="Skills promedio"
          value={kpis?.skills_promedio || 0}
        />
        <KPICard
          title="Empresas activas"
          value={kpis?.empresas_distintas || 0}
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EvolucionChart data={evolucion.length > 0 ? evolucion : undefined} />
        <GeografiaChart data={geografia.length > 0 ? geografia : undefined} />
      </div>

      <div>
        <OcupacionesChart data={ocupaciones.length > 0 ? ocupaciones : undefined} />
      </div>
    </div>
  );
}
