'use client';

import { useEffect, useState } from 'react';
import InsightCard from '@/components/InsightCard';
import KPICard from '@/components/KPICard';
import OcupacionesChart from '@/components/charts/OcupacionesChart';
import GeografiaChart from '@/components/charts/GeografiaChart';
import { getKPIs, getOfertasPorProvincia, getTopOcupaciones } from '@/lib/supabase';

interface KPIs {
  totalOfertas: number;
  ocupacionesDistintas: number;
  empresasActivas: number;
  provincias: number;
}

export default function PanoramaGeneral() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [geografiaData, setGeografiaData] = useState<{ jurisdiccion: string; cantidad: number; porcentaje: number }[]>([]);
  const [ocupacionesData, setOcupacionesData] = useState<{ ocupacion: string; cantidad: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [kpisData, geoData, ocupData] = await Promise.all([
          getKPIs(),
          getOfertasPorProvincia(),
          getTopOcupaciones(10)
        ]);
        setKpis(kpisData);
        setGeografiaData(geoData);
        setOcupacionesData(ocupData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al cargar datos');
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando datos...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  // Calcular insights dinámicos
  const topProvincia = geografiaData[0];
  const topOcupacion = ocupacionesData[0];
  const concentracion = geografiaData.slice(0, 2).reduce((sum, p) => sum + p.porcentaje, 0);

  return (
    <div className="space-y-6">
      {/* Insights destacados */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InsightCard
          title="Total de ofertas"
          description={`${kpis?.totalOfertas || 0} ofertas laborales validadas y clasificadas`}
          icon="📊"
          color="blue"
        />
        <InsightCard
          title="Ocupación destacada"
          description={`${topOcupacion?.ocupacion || 'N/A'} con ${topOcupacion?.cantidad || 0} ofertas`}
          icon="💼"
          color="green"
        />
        <InsightCard
          title="Concentración geográfica"
          description={`${topProvincia?.jurisdiccion || 'N/A'} y alrededores concentran ${concentracion.toFixed(0)}% de ofertas`}
          icon="📍"
          color="purple"
        />
      </div>

      {/* KPIs principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard
          title="Ofertas analizadas"
          value={kpis?.totalOfertas || 0}
          delta="validadas"
          deltaType="neutral"
        />
        <KPICard
          title="Ocupaciones ESCO"
          value={kpis?.ocupacionesDistintas || 0}
          delta="distintas"
          deltaType="neutral"
        />
        <KPICard
          title="Empresas"
          value={kpis?.empresasActivas || 0}
          delta="únicas"
          deltaType="neutral"
        />
        <KPICard
          title="Provincias"
          value={kpis?.provincias || 0}
          delta="con ofertas"
          deltaType="neutral"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GeografiaChart data={geografiaData} title="Distribución por provincia" />
        <OcupacionesChart data={ocupacionesData} title="Top 10 ocupaciones ESCO" />
      </div>
    </div>
  );
}
