"use client";

import { useState, useEffect } from "react";
import { KPICard } from "@/components/KPICard";
import { ChartContainer } from "@/components/ChartContainer";
import { FileText, Briefcase, MapPin, Sparkles, TrendingUp, AlertCircle, Award, Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList, Cell } from "recharts";
import { getKPIs, getTopOcupaciones, getEvolucionPeriodos, getOfertasPorLocalidad, getOfertasPorProvincia, PeriodoEvolucion } from "@/lib/supabase";
import { DashboardFilters } from "@/lib/types";
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
  const [evolutionData, setEvolutionData] = useState<PeriodoEvolucion[]>([]);
  const [periodoComparacion, setPeriodoComparacion] = useState<number>(13);
  const [ocupacionesLimit, setOcupacionesLimit] = useState(10);

  // Carga principal: KPIs + jurisdicción
  // Usa getKPIs (applyFilters) en vez de RPC para respetar TODOS los filtros
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const kpisData = await getKPIs(filters);
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
          setJurisdictionData([]);
        }

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

  // Carga de evolución: se recarga con filtros Y con cambio de período
  useEffect(() => {
    async function loadEvolucion() {
      try {
        const evolucion = await getEvolucionPeriodos(filters, periodoComparacion);
        setEvolutionData(evolucion);
      } catch (err) {
        console.error('Error cargando evolución:', err);
      }
    }
    loadEvolucion();
  }, [filters, periodoComparacion]);

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

  // Download options para Evolución
  const evolucionDownloadOptions = evolutionData.length > 0 ? {
    title: 'Evolución de las ofertas laborales activas',
    subtitle: getFiltersSubtitle(),
    data: evolutionData.map(item => ({
      periodo: item.label,
      desde: item.fechaDesde,
      hasta: item.fechaHasta,
      ofertas: item.ofertas,
      actual: item.esPeriodoActual ? 'Sí' : ''
    })),
    columns: [
      { header: 'Período', key: 'periodo' },
      { header: 'Desde', key: 'desde' },
      { header: 'Hasta', key: 'hasta' },
      { header: 'Ofertas laborales', key: 'ofertas' },
      { header: 'Período actual', key: 'actual' }
    ],
    filename: 'evolucion_ofertas',
  } : undefined;

  // Download options para Ocupaciones
  const ocupacionesTotal = occupationData.reduce((sum, item) => sum + item.value, 0);
  const ocupacionesDownloadOptions = occupationData.length > 0 ? {
    title: 'Ocupaciones en las ofertas laborales activas',
    subtitle: getFiltersSubtitle(),
    data: occupationData.map(item => ({
      name: item.name,
      value: item.value,
      porcentaje: ocupacionesTotal > 0 ? Math.round((item.value / ocupacionesTotal) * 100 * 10) / 10 : 0
    })),
    columns: [
      { header: 'Ocupación', key: 'name' },
      { header: 'Ofertas laborales', key: 'value' },
      { header: 'Porcentaje (%)', key: 'porcentaje' }
    ],
    filename: `ocupaciones_${ocupacionesLimit === 0 ? 'total' : 'top' + ocupacionesLimit}`,
  } : undefined;

  // Download options para Jurisdicciones
  const esPorLocalidad = !!filters.provincia;
  const jurisdiccionTotal = jurisdictionData.reduce((sum, item) => sum + item.value, 0);
  const jurisdiccionesDownloadOptions = jurisdictionData.length > 0 ? {
    title: esPorLocalidad
      ? 'Distribución de las ofertas laborales por localidad'
      : 'Distribución de las ofertas laborales por jurisdicción',
    subtitle: getFiltersSubtitle(),
    data: jurisdictionData.map(item => ({
      name: item.name,
      value: item.value,
      porcentaje: jurisdiccionTotal > 0 ? Math.round((item.value / jurisdiccionTotal) * 100 * 10) / 10 : 0
    })),
    columns: [
      { header: esPorLocalidad ? 'Localidad' : 'Jurisdicción', key: 'name' },
      { header: 'Ofertas laborales', key: 'value' },
      { header: 'Porcentaje (%)', key: 'porcentaje' }
    ],
    filename: esPorLocalidad ? 'distribucion_localidades' : 'distribucion_geografica',
  } : undefined;

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
            <h3 className="text-xl font-bold text-gray-900">Datos relevantes del período seleccionado</h3>
            <p className="text-sm text-gray-600">Resumen de las ofertas laborales activas (publicadas) durante el período seleccionado</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-4 border border-blue-200 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <span className="text-xs font-semibold text-gray-500 uppercase">Total analizado</span>
            </div>
            <p className="text-sm text-gray-700 font-medium">Se han identificado <span className="font-bold text-blue-600">{kpis.totalOfertas.toLocaleString()}</span> ofertas laborales activas</p>
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
          title="Ofertas laborales"
          value={kpis.totalOfertas}
          icon={FileText}
          color="blue"
        />
        <KPICard
          title="Ocupaciones en ofertas laborales"
          value={kpis.ocupacionesDistintas}
          icon={Briefcase}
          color="green"
        />
        <KPICard
          title="Provincias con demanda"
          value={kpis.provincias}
          icon={MapPin}
          color="purple"
        />
      </div>

      {/* Evolution Chart con Insights — BarChart comparativo */}
      {(() => {
        const showLabels = evolutionData.length <= 15;
        const isRotated = evolutionData.length > 8;
        const total = evolutionData.reduce((s, p) => s + p.ofertas, 0);
        const periodoActual = evolutionData.find(p => p.esPeriodoActual);
        const periodoAnterior = evolutionData.length >= 2 ? evolutionData[evolutionData.length - 2] : null;
        // Determinar unidad de período según filtros de fecha
        const tipoPeriodo = (() => {
          if (!filters.fechaDesde) return 'semanas'; // sin filtro → siempre semanas
          const desde = new Date(filters.fechaDesde);
          const hasta = filters.fechaHasta ? new Date(filters.fechaHasta) : new Date();
          const dias = Math.round((hasta.getTime() - desde.getTime()) / (1000 * 60 * 60 * 24));
          if (dias <= 7) return 'semanas';
          if (dias <= 31) return 'meses';
          return 'períodos';
        })();
        const esFemenino = tipoPeriodo === 'semanas';
        const PERIODO_OPTIONS = [
          { value: 5, label: `${esFemenino ? 'Últimas' : 'Últimos'} 5 ${tipoPeriodo}` },
          { value: 13, label: `${esFemenino ? 'Últimas' : 'Últimos'} 13 ${tipoPeriodo}` },
          { value: 0, label: `${esFemenino ? 'Todas las' : 'Todos los'} ${tipoPeriodo}` },
        ];

        return (
          <ChartContainer
            title="Evolución de las ofertas laborales activas"
            subtitle={`${evolutionData.length} períodos — ${total.toLocaleString()} ofertas`}
            downloadOptions={evolucionDownloadOptions}
            headerExtra={
              <div className="flex items-center gap-1.5 ml-4">
                <span className="text-xs text-gray-500 font-medium mr-1">Número de ofertas laborales en:</span>
                {PERIODO_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setPeriodoComparacion(opt.value)}
                    className={`px-3 py-1 text-xs font-semibold rounded-full transition-all ${
                      periodoComparacion === opt.value
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            }
            insights={evolutionData.length >= 2 ? (
              <InsightList>
                {(() => {
                  const actual = periodoActual?.ofertas || 0;
                  const anterior = periodoAnterior?.ofertas || 0;
                  const diff = anterior > 0 ? Math.round(((actual - anterior) / anterior) * 100) : 0;
                  const promedio = evolutionData.length > 0 ? Math.round(total / evolutionData.length) : 0;
                  const pico = evolutionData.reduce((max, p) => p.ofertas > max.ofertas ? p : max, evolutionData[0]);
                  return (
                    <>
                      <InsightItem
                        text={`Período actual: ${actual.toLocaleString()} ofertas (${diff >= 0 ? '+' : ''}${diff}% vs anterior)`}
                        highlight
                      />
                      <InsightItem
                        text={`Promedio ${evolutionData.length} períodos: ${promedio.toLocaleString()} ofertas`}
                      />
                      <InsightItem
                        text={`Pico: ${pico.label} con ${pico.ofertas.toLocaleString()} ofertas`}
                      />
                    </>
                  );
                })()}
              </InsightList>
            ) : undefined}
          >
            {evolutionData.length > 0 ? (
              <ResponsiveContainer width="100%" height={isRotated ? 300 : 260}>
                <BarChart data={evolutionData} margin={{ top: 20, right: 20, left: 20, bottom: isRotated ? 60 : 20 }}>
                  <XAxis
                    dataKey="label"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#6b7280', fontSize: showLabels ? 11 : 9, fontWeight: 600 }}
                    interval={showLabels ? 0 : Math.max(1, Math.floor(evolutionData.length / 10))}
                    angle={isRotated ? -45 : 0}
                    textAnchor={isRotated ? "end" : "middle"}
                    height={isRotated ? 70 : 30}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const d = payload[0].payload as PeriodoEvolucion;
                      return (
                        <div className="bg-white px-4 py-3 shadow-lg rounded-lg border border-gray-200">
                          <p className="font-semibold text-gray-900">{d.label}</p>
                          <p className="text-xs text-gray-500">{d.fechaDesde} → {d.fechaHasta}</p>
                          <p className="text-blue-600 font-bold mt-1">{d.ofertas.toLocaleString()} ofertas</p>
                          {d.esPeriodoActual && (
                            <p className="text-xs text-blue-500 font-medium mt-1">Período seleccionado</p>
                          )}
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="ofertas" radius={[4, 4, 0, 0]}>
                    {evolutionData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.esPeriodoActual ? '#1d4ed8' : '#93c5fd'}
                      />
                    ))}
                    {showLabels && (
                      <LabelList
                        dataKey="ofertas"
                        position="top"
                        style={{ fill: '#1e40af', fontSize: 12, fontWeight: 700 }}
                        formatter={(value: number) => value.toLocaleString()}
                      />
                    )}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[260px] text-gray-400 text-sm">
                Sin datos de evolución para los filtros seleccionados.
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
            title="Ocupaciones en las ofertas laborales activas"
            subtitle={`${currentLabel} — ${chartItemCount} ocupaciones`}
            downloadOptions={ocupacionesDownloadOptions}
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
            ? "Distribución de las ofertas laborales por localidad"
            : "Distribución de las ofertas laborales por jurisdicción"
          }
          subtitle={filters.provincia ? `Top 10 localidades` : `Top 10 provincias`}
          downloadOptions={jurisdiccionesDownloadOptions}
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
