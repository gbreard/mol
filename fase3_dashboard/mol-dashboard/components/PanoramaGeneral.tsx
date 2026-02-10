"use client";

import { useState, useEffect } from "react";
import { KPICard } from "@/components/KPICard";
import { ChartContainer } from "@/components/ChartContainer";
import { FileText, Briefcase, Lightbulb, Sparkles, TrendingUp, AlertCircle, Award, Loader2 } from "lucide-react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList, Label } from "recharts";
import { getKPIs, getTopOcupaciones, getEvolucionSemanal, getOfertasPorLocalidad, getOfertasPorProvincia, EvolucionSemanal } from "@/lib/supabase";
import { DashboardFilters } from "@/lib/types";
import { downloadFormattedExcel } from "@/components/ExportButton";
import { capitalize } from "@/lib/utils";

interface PanoramaGeneralProps {
  filters: DashboardFilters;
}

interface KPIData {
  totalOfertas: number;
  ocupacionesDistintas: number;
  empresasActivas: number;
  provincias: number;
}

interface ChartData {
  name: string;
  value: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white px-4 py-3 shadow-lg rounded-lg border border-gray-200">
        <p className="font-semibold text-gray-900">{label}</p>
        <p className="text-blue-600 font-bold">{payload[0].value.toLocaleString()} ofertas</p>
      </div>
    );
  }
  return null;
};

const InsightList = ({ children }: { children: React.ReactNode }) => (
  <ul className="space-y-3 list-none">
    {children}
  </ul>
);

const InsightItem = ({ icon: Icon, text, highlight }: { icon?: any; text: string; highlight?: boolean }) => (
  <li className={`flex items-start gap-3 transition-all duration-200 ${
    highlight ? 'font-semibold' : ''
  }`}>
    <span className={`mt-1.5 h-1.5 w-1.5 rounded-full flex-shrink-0 ${
      highlight ? 'bg-amber-600' : 'bg-gray-400'
    }`} />
    <p className={`text-sm leading-relaxed flex-1 ${
      highlight ? 'text-gray-900' : 'text-gray-700'
    }`}>
      {text}
    </p>
  </li>
);

const OCUPACIONES_LIMIT_OPTIONS = [
  { value: 10, label: 'Top 10' },
  { value: 30, label: 'Top 30' },
  { value: 50, label: 'Top 50' },
  { value: 100, label: 'Top 100' },
  { value: 0, label: 'Total' },
];

// Truncar labels largos para el eje Y
function truncateLabel(text: string, maxLen: number = 35): string {
  if (text.length <= maxLen) return text;
  return text.substring(0, maxLen - 1) + '…';
}

export function PanoramaGeneral({ filters }: PanoramaGeneralProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kpis, setKpis] = useState<KPIData>({ totalOfertas: 0, ocupacionesDistintas: 0, empresasActivas: 0, provincias: 0 });
  const [occupationData, setOccupationData] = useState<ChartData[]>([]);
  const [jurisdictionData, setJurisdictionData] = useState<ChartData[]>([]);
  const [evolutionData, setEvolutionData] = useState<EvolucionSemanal[]>([]);
  const [ocupacionesLimit, setOcupacionesLimit] = useState(10);

  // Carga principal: KPIs + jurisdicción + evolución semanal
  // Usa getKPIs (applyFilters) en vez de RPC para respetar TODOS los filtros
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [kpisData, evolucion] = await Promise.all([
          getKPIs(filters),
          getEvolucionSemanal(filters)
        ]);

        setKpis(kpisData);

        // Jurisdicción: por localidad si hay provincia, por provincia si no
        if (filters.provincia && !filters.localidad) {
          const localidades = await getOfertasPorLocalidad(filters);
          setJurisdictionData(localidades.slice(0, 10).map(l => ({
            name: l.jurisdiccion,
            value: l.cantidad
          })));
        } else if (!filters.provincia) {
          const provincias = await getOfertasPorProvincia(filters);
          setJurisdictionData(provincias.slice(0, 10).map(p => ({
            name: p.jurisdiccion,
            value: p.cantidad
          })));
        } else {
          // Localidad seleccionada → no se muestra chart
          setJurisdictionData([]);
        }

        setEvolutionData(evolucion);
        setError(null);
      } catch (err) {
        console.error('Error cargando datos:', err);
        setError('Error al cargar los datos. Verifica la conexión con Supabase.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [filters]);

  // Carga de ocupaciones: se recarga con filtros Y con cambio de límite
  useEffect(() => {
    async function loadOcupaciones() {
      try {
        const limit = ocupacionesLimit === 0 ? 9999 : ocupacionesLimit;
        const ocupaciones = await getTopOcupaciones(limit, filters);
        setOccupationData(ocupaciones.map(o => ({ name: capitalize(o.ocupacion), value: o.cantidad })));
      } catch (err) {
        console.error('Error cargando ocupaciones:', err);
      }
    }
    loadOcupaciones();
  }, [filters, ocupacionesLimit]);

  // Función para formatear los filtros aplicados como subtítulo
  const getFiltersSubtitle = (): string => {
    const parts: string[] = [];

    if (filters.territorio && filters.territorio !== 'Nacional') {
      parts.push(`Territorio: ${filters.territorio}`);
    }
    if (filters.provincia && filters.provincia !== 'Todas') {
      parts.push(`Provincia: ${filters.provincia}`);
    }
    if (filters.localidad) {
      parts.push(`Localidad: ${filters.localidad}`);
    }
    if (filters.fechaDesde) {
      parts.push(`Desde: ${filters.fechaDesde.toLocaleDateString('es-AR')}`);
    }
    if (filters.fechaHasta) {
      parts.push(`Hasta: ${filters.fechaHasta.toLocaleDateString('es-AR')}`);
    }
    if (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0) {
      parts.push(`Ocupaciones: ${filters.ocupacionesSeleccionadas.slice(0, 3).join(', ')}${filters.ocupacionesSeleccionadas.length > 3 ? '...' : ''}`);
    }

    return parts.length > 0 ? `Filtros aplicados: ${parts.join(' | ')}` : 'Sin filtros aplicados (datos totales)';
  };

  // Handler para descargar Excel de Evolución
  const handleDownloadEvolucion = () => {
    if (evolutionData.length === 0) return;

    const data = evolutionData.map(item => ({
      periodo: item.label,
      ofertas: item.ofertas
    }));

    downloadFormattedExcel({
      title: 'Evolución de las ofertas laborales',
      subtitle: getFiltersSubtitle(),
      data,
      columns: [
        { header: 'Semana (lunes - domingo)', key: 'periodo' },
        { header: 'Ofertas laborales', key: 'ofertas' }
      ],
      filename: 'evolucion_ofertas',
      showPercentage: false
    });
  };

  // Handler para descargar Excel de Ocupaciones
  const handleDownloadOcupaciones = () => {
    const total = occupationData.reduce((sum, item) => sum + item.value, 0);
    const data = occupationData.map(item => ({
      name: item.name,
      value: item.value,
      porcentaje: total > 0 ? Math.round((item.value / total) * 100 * 10) / 10 : 0
    }));

    downloadFormattedExcel({
      title: 'Distribución de las ofertas por ocupación',
      subtitle: getFiltersSubtitle(),
      data,
      columns: [
        { header: 'Ocupación', key: 'name' },
        { header: 'Ofertas laborales', key: 'value' },
        { header: 'Porcentaje (%)', key: 'porcentaje' }
      ],
      filename: `ocupaciones_${ocupacionesLimit === 0 ? 'total' : 'top' + ocupacionesLimit}`,
      showPercentage: true
    });
  };

  // Handler para descargar Excel de Jurisdicciones
  const handleDownloadJurisdicciones = () => {
    const esPorLocalidad = !!filters.provincia;
    const total = jurisdictionData.reduce((sum, item) => sum + item.value, 0);
    const data = jurisdictionData.map(item => ({
      name: item.name,
      value: item.value,
      porcentaje: total > 0 ? Math.round((item.value / total) * 100 * 10) / 10 : 0
    }));

    downloadFormattedExcel({
      title: esPorLocalidad
        ? 'Distribución de las ofertas por localidad'
        : 'Distribución de las ofertas por jurisdicción',
      subtitle: getFiltersSubtitle(),
      data,
      columns: [
        { header: esPorLocalidad ? 'Localidad' : 'Jurisdicción', key: 'name' },
        { header: 'Ofertas laborales', key: 'value' },
        { header: 'Porcentaje (%)', key: 'porcentaje' }
      ],
      filename: esPorLocalidad ? 'distribucion_localidades' : 'distribucion_geografica',
      showPercentage: true
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando datos...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hallazgos Clave */}
      <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-2 border-blue-300 rounded-2xl p-6 shadow-lg">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-blue-600 rounded-full p-2.5">
            <Award className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">Datos relevantes del período</h3>
            <p className="text-sm text-gray-600">Resumen de las ofertas laborales analizadas</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-4 border border-blue-200 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <span className="text-xs font-semibold text-gray-500 uppercase">Total analizado</span>
            </div>
            <p className="text-sm text-gray-700 font-medium">Se han procesado <span className="font-bold text-blue-600">{kpis.totalOfertas.toLocaleString()}</span> ofertas laborales</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-blue-200 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Briefcase className="w-5 h-5 text-purple-600" />
              <span className="text-xs font-semibold text-gray-500 uppercase">Ocupación destacada</span>
            </div>
            <p className="text-sm text-gray-700 font-medium">{occupationData[0]?.name || 'Cargando...'} lidera con <span className="font-bold text-purple-600">{occupationData[0]?.value || 0}</span> ofertas</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-blue-200 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-amber-600" />
              <span className="text-xs font-semibold text-gray-500 uppercase">Cobertura</span>
            </div>
            <p className="text-sm text-gray-700 font-medium">Ofertas de <span className="font-bold text-amber-600">{kpis.empresasActivas}</span> empresas en <span className="font-bold text-amber-600">{kpis.provincias}</span> provincias</p>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-6">
        <KPICard
          title="Ofertas analizadas"
          value={kpis.totalOfertas}
          icon={FileText}
          color="blue"
        />
        <KPICard
          title="Ocupaciones identificadas"
          value={kpis.ocupacionesDistintas}
          icon={Briefcase}
          color="green"
        />
        <KPICard
          title="Empresas activas"
          value={kpis.empresasActivas}
          icon={Lightbulb}
          color="purple"
        />
      </div>

      {/* Evolution Chart con Insights */}
      {(() => {
        const showLabels = evolutionData.length <= 12;
        const total = evolutionData.reduce((s, w) => s + w.ofertas, 0);
        return (
          <ChartContainer
            title="Evolución de las ofertas laborales"
            subtitle={`${evolutionData.length} semanas — ${total.toLocaleString()} ofertas`}
            onDownload={handleDownloadEvolucion}
            insights={evolutionData.length >= 2 ? (
              <InsightList>
                {(() => {
                  const last = evolutionData[evolutionData.length - 1]?.ofertas || 0;
                  const prev = evolutionData[evolutionData.length - 2]?.ofertas || 0;
                  const diff = prev > 0 ? Math.round(((last - prev) / prev) * 100) : 0;
                  return (
                    <>
                      <InsightItem
                        text={`Última semana: ${last.toLocaleString()} ofertas (${diff >= 0 ? '+' : ''}${diff}% vs semana anterior)`}
                        highlight
                      />
                      <InsightItem
                        text={`Total período: ${total.toLocaleString()} ofertas`}
                      />
                      <InsightItem
                        text={`Promedio semanal: ${Math.round(total / evolutionData.length).toLocaleString()} ofertas`}
                      />
                    </>
                  );
                })()}
              </InsightList>
            ) : undefined}
          >
            {evolutionData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={evolutionData} margin={{ top: 20, right: 20, left: 20, bottom: 20 }}>
                  <defs>
                    <linearGradient id="colorOfertas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="label"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#6b7280', fontSize: showLabels ? 11 : 9, fontWeight: 600 }}
                    interval={showLabels ? 0 : Math.max(1, Math.floor(evolutionData.length / 10))}
                    angle={evolutionData.length > 8 ? -45 : 0}
                    textAnchor={evolutionData.length > 8 ? "end" : "middle"}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="ofertas"
                    stroke="#3b82f6"
                    strokeWidth={showLabels ? 4 : 2}
                    dot={showLabels ? { fill: '#fff', stroke: '#3b82f6', strokeWidth: 3, r: 6 } : { r: 3, fill: '#3b82f6' }}
                    activeDot={{ r: 8, fill: '#3b82f6' }}
                    fill="url(#colorOfertas)"
                  >
                    {showLabels && (
                      <LabelList
                        dataKey="ofertas"
                        position="top"
                        style={{ fill: '#1e40af', fontSize: 13, fontWeight: 700 }}
                        formatter={(value: number) => value.toLocaleString()}
                      />
                    )}
                  </Line>
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[260px] text-gray-400 text-sm">
                Sin datos de evolución para los filtros seleccionados
              </div>
            )}
          </ChartContainer>
        );
      })()}

      {/* Occupation Distribution con Insights - ocultar si se filtró por 1 sola ocupación */}
      {filters.ocupacionesSeleccionadas.length !== 1 && (() => {
        const chartItemCount = occupationData.length;
        const chartHeight = Math.max(340, chartItemCount * 32);
        const needsScroll = chartItemCount > 15;
        const currentLabel = OCUPACIONES_LIMIT_OPTIONS.find(o => o.value === ocupacionesLimit)?.label || 'Top 10';

        return (
          <ChartContainer
            title="Ofertas por ocupación"
            subtitle={`${currentLabel} — ${chartItemCount} ocupaciones`}
            onDownload={handleDownloadOcupaciones}
            headerExtra={
              <select
                value={ocupacionesLimit}
                onChange={(e) => setOcupacionesLimit(Number(e.target.value))}
                className="h-8 px-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 hover:border-blue-400 transition-colors"
              >
                {OCUPACIONES_LIMIT_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            }
            insights={
              <InsightList>
                <InsightItem
                  text="Las 3 ocupaciones principales concentran el 42% del total de ofertas"
                  highlight
                />
                <InsightItem
                  text="Técnicos en informática duplicó su demanda en 3 meses"
                />
                <InsightItem
                  text="Ocupaciones comerciales representan el 35% de todas las ofertas"
                />
              </InsightList>
            }
          >
            <div className={needsScroll ? "overflow-y-auto max-h-[600px]" : ""}>
              <ResponsiveContainer width="100%" height={chartHeight}>
                <BarChart data={occupationData} layout="vertical" margin={{ top: 5, right: 50, left: 10, bottom: 5 }}>
                  <defs>
                    <linearGradient id="colorBar1" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={0.9}/>
                      <stop offset="100%" stopColor="#059669" stopOpacity={1}/>
                    </linearGradient>
                  </defs>
                  <XAxis type="number" hide={true} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={200}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#374151', fontSize: 11, fontWeight: 500 }}
                    tickFormatter={(value: string) => truncateLabel(value, 35)}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" fill="url(#colorBar1)" radius={[0, 6, 6, 0]}>
                    <LabelList
                      dataKey="value"
                      position="right"
                      style={{ fill: '#059669', fontSize: 12, fontWeight: 700 }}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartContainer>
        );
      })()}

      {/* Jurisdiction Distribution — ocultar si hay localidad seleccionada */}
      {!filters.localidad && jurisdictionData.length > 0 && (
        <ChartContainer
          title={filters.provincia
            ? "Distribución de las ofertas por localidad"
            : "Distribución de las ofertas por jurisdicción"
          }
          subtitle={filters.provincia ? `Top 10 localidades` : `Top 10 provincias`}
          onDownload={handleDownloadJurisdicciones}
          insights={
            jurisdictionData.length >= 2 ? (
              <InsightList>
                <InsightItem
                  text={`${jurisdictionData[0]?.name} lidera con ${jurisdictionData[0]?.value.toLocaleString()} ofertas`}
                  highlight
                />
                {jurisdictionData.length >= 3 && (
                  <InsightItem
                    text={`Las 3 principales concentran el ${Math.round(
                      (jurisdictionData.slice(0, 3).reduce((s, d) => s + d.value, 0) /
                        jurisdictionData.reduce((s, d) => s + d.value, 0)) * 100
                    )}% del total`}
                  />
                )}
                <InsightItem
                  text={`${jurisdictionData.length} ${filters.provincia ? 'localidades' : 'provincias'} con ofertas activas`}
                />
              </InsightList>
            ) : undefined
          }
        >
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={jurisdictionData} layout="vertical" margin={{ top: 5, right: 50, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="colorBar2" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.9}/>
                  <stop offset="100%" stopColor="#2563eb" stopOpacity={1}/>
                </linearGradient>
              </defs>
              <XAxis type="number" hide={true} />
              <YAxis
                type="category"
                dataKey="name"
                width={160}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#374151', fontSize: 11, fontWeight: 500 }}
                tickFormatter={(value: string) => truncateLabel(value, 28)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" fill="url(#colorBar2)" radius={[0, 6, 6, 0]}>
                <LabelList
                  dataKey="value"
                  position="right"
                  style={{ fill: '#2563eb', fontSize: 12, fontWeight: 700 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      )}
    </div>
  );
}
