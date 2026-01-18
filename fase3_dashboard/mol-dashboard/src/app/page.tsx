'use client';

import InsightCard from '@/components/InsightCard';
import KPICard from '@/components/KPICard';
import EvolucionChart from '@/components/charts/EvolucionChart';
import OcupacionesChart from '@/components/charts/OcupacionesChart';
import GeografiaChart from '@/components/charts/GeografiaChart';

export default function PanoramaGeneral() {
  return (
    <div className="space-y-6">

      {/* Insights destacados */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InsightCard
          title="Récord histórico"
          description="Junio registra el máximo histórico con 5,890 ofertas publicadas"
          icon="📈"
          color="blue"
        />
        <InsightCard
          title="Sector destacado"
          description="Técnicos en informática duplicaron demanda trimestral"
          icon="💻"
          color="green"
        />
        <InsightCard
          title="Concentración geográfica"
          description="CABA y Buenos Aires concentran 60% de ofertas"
          icon="📍"
          color="purple"
        />
      </div>

      {/* KPIs principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard
          title="Ofertas analizadas"
          value={5890}
          delta="+12% vs mes anterior"
          deltaType="positive"
        />
        <KPICard
          title="Ocupaciones identificadas"
          value={907}
          delta="+8%"
          deltaType="positive"
        />
        <KPICard
          title="Habilidades detectadas"
          value={1243}
          delta="+15%"
          deltaType="positive"
        />
        <KPICard
          title="Empresas activas"
          value={2150}
          delta="+5%"
          deltaType="positive"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EvolucionChart />
        <GeografiaChart />
      </div>

      <div>
        <OcupacionesChart />
      </div>
    </div>
  );
}
