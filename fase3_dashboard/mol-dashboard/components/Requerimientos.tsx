"use client";

import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Loader2, AlertCircle, GraduationCap, Clock, TrendingUp, MapPin, Users, Briefcase, Cpu, Layers, ChevronDown } from "lucide-react";
import { ChartDownloadButton, FormattedExcelOptions } from "@/components/ExportButton";
import { SkillsFilters } from "@/lib/supabase";
import { useRequerimientos } from "@/hooks/use-requerimientos";
import { useSkills } from "@/hooks/use-skills";
import { DashboardFilters } from "@/lib/types";
import { capitalize } from "@/lib/utils";

interface RequerimientosProps {
  filters: DashboardFilters;
}

interface DistribucionItem {
  name: string;
  value: number;
  porcentaje: number;
}

interface RequerimientosData {
  total: number;
  educacion: DistribucionItem[];
  experiencia: DistribucionItem[];
  seniority: DistribucionItem[];
  modalidad: DistribucionItem[];
  genteCargo: DistribucionItem[];
  jornada: DistribucionItem[];
}

// Colores para cada categoría de valor
const CATEGORY_COLORS: Record<string, string> = {
  // Educación
  'universitario': '#3b82f6',
  'terciario': '#60a5fa',
  'secundario': '#93c5fd',
  'primario': '#bfdbfe',
  // Experiencia
  'Sin experiencia': '#10b981',
  '1-2 años': '#34d399',
  '3-4 años': '#6ee7b7',
  '5+ años': '#a7f3d0',
  // Seniority
  'trainee': '#8b5cf6',
  'junior': '#a78bfa',
  'semisenior': '#c4b5fd',
  'senior': '#ddd6fe',
  'manager': '#ede9fe',
  // Modalidad
  'presencial': '#f59e0b',
  'hibrido': '#fbbf24',
  'remoto': '#fcd34d',
  // Gente a cargo
  'Con gente a cargo': '#ec4899',
  'Sin gente a cargo': '#f9a8d4',
  // Jornada
  'full-time': '#06b6d4',
  'part-time': '#22d3ee',
  'freelance': '#67e8f9',
  // Skills digitales
  'Digitales': '#3b82f6',
  'No digitales': '#94a3b8',
  // Default
  'Sin especificar': '#d1d5db',
}

// Obtener color para un valor
function getColor(name: string): string {
  return CATEGORY_COLORS[name] || CATEGORY_COLORS['Sin especificar']
}

// Componente de barra horizontal apilada al 100% con leyenda
function StackedBar({
  label,
  data,
  icon: Icon
}: {
  label: string;
  data: DistribucionItem[];
  icon: any;
}) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  // Filtrar "Sin especificar" si es muy pequeño
  const filteredData = data.filter(d => d.porcentaje >= 3 || d.name !== 'Sin especificar')

  return (
    <div className="py-2 border-b border-gray-100 last:border-0">
      <div className="flex items-center gap-3">
        {/* Label con icono */}
        <div className="flex items-center gap-2 w-32 lg:w-40 flex-shrink-0">
          <div className="p-1 bg-gray-100 rounded-lg">
            <Icon className="w-3.5 h-3.5 text-gray-600" />
          </div>
          <span className="text-xs lg:text-sm font-medium text-gray-700 truncate">{label}</span>
        </div>

        {/* Barra apilada */}
        <div className="flex-1 flex h-6 rounded-lg overflow-hidden bg-gray-100 relative">
          {filteredData.map((item, index) => (
            <div
              key={item.name}
              className="h-full flex items-center justify-center transition-all duration-200 cursor-pointer relative"
              style={{
                width: `${item.porcentaje}%`,
                backgroundColor: getColor(item.name),
                opacity: hoveredIndex !== null && hoveredIndex !== index ? 0.6 : 1
              }}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              {item.porcentaje >= 10 && (
                <span className="text-xs font-semibold text-white drop-shadow-sm truncate px-1">
                  {item.porcentaje}%
                </span>
              )}

              {/* Tooltip on hover */}
              {hoveredIndex === index && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-10">
                  <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
                    <p className="font-semibold">{item.name}</p>
                    <p>{item.value.toLocaleString()} ofertas ({item.porcentaje}%)</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Leyenda debajo de la barra - oculta en móvil para ahorrar espacio */}
      <div className="hidden lg:flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 ml-[140px] lg:ml-[168px]">
        {filteredData.map((item) => (
          <div key={item.name} className="flex items-center gap-1 text-[10px]">
            <div
              className="w-2 h-2 rounded-sm flex-shrink-0"
              style={{ backgroundColor: getColor(item.name) }}
            />
            <span className="text-gray-600">{capitalize(item.name)}</span>
            <span className="text-gray-400">({item.porcentaje}%)</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Colores para categorías L1 (modo agregado)
const COLORS_L1 = ['#2563eb', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d', '#ea580c', '#4f46e5', '#0d9488', '#c026d3'];

// Paleta ampliada para skills individuales (modo específica) — 20 colores distintos
const COLORS_SKILLS = [
  '#2563eb', '#059669', '#d97706', '#7c3aed', '#db2777',
  '#0891b2', '#65a30d', '#ea580c', '#4f46e5', '#0d9488',
  '#c026d3', '#dc2626', '#2dd4bf', '#a3e635', '#fb923c',
  '#818cf8', '#f472b6', '#38bdf8', '#a78bfa', '#34d399',
];

// Opciones de cantidad de competencias
const CANTIDAD_OPTIONS = [20, 40, 60, 100];

// Opciones de tipo de visualización
const TIPO_OPTIONS = [
  { value: 'especifica', label: 'Competencias específicas' },
  { value: 'agregada', label: 'Por categoría (agregado)' }
];

export function Requerimientos({ filters }: RequerimientosProps) {
  // Selectores del gráfico de habilidades (Issue #6)
  const [cantidadCompetencias, setCantidadCompetencias] = useState<number>(20);
  const [tipoVisualizacion, setTipoVisualizacion] = useState<'especifica' | 'agregada'>('especifica');

  // React Query hooks — replace 1 useEffect + Promise.all(4) + 5 useState
  const { data: requerimientosData, isLoading: loadingReq, error: reqError } = useRequerimientos(filters);
  const { data: skillsData, isLoading: loadingSkills } = useSkills(filters);

  const loading = loadingReq || loadingSkills;
  const error = reqError ? 'Error al cargar los datos de requerimientos.' : null;

  // Derive skills state from skillsData
  const categoriasL1 = skillsData?.por_l1 || [];
  const skillsDigitales = (() => {
    if (!skillsData) return [];
    const { digitales, no_digitales, total } = skillsData.digitales;
    if (total === 0) return [];
    return [
      { name: 'Digitales', value: digitales, porcentaje: Math.round(digitales * 100 / total) },
      { name: 'No digitales', value: no_digitales, porcentaje: Math.round(no_digitales * 100 / total) }
    ];
  })();
  const topSkillsTotal = skillsData?.top_skills || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando requerimientos...</span>
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

  // Función para formatear los filtros aplicados como subtítulo
  const getFiltersSubtitle = (): string => {
    const parts: string[] = [];
    if (filters.territorio && filters.territorio !== 'Nacional') parts.push(`Territorio: ${filters.territorio}`);
    if (filters.provincia && filters.provincia !== 'Todas') parts.push(`Provincia: ${filters.provincia}`);
    if (filters.localidad?.length > 0) parts.push(`Localidad: ${filters.localidad.length === 1 ? filters.localidad[0] : `${filters.localidad.length} seleccionadas`}`);
    if (filters.fechaDesde) parts.push(`Desde: ${filters.fechaDesde.toLocaleDateString('es-AR')}`);
    if (filters.fechaHasta) parts.push(`Hasta: ${filters.fechaHasta.toLocaleDateString('es-AR')}`);
    if (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0) {
      parts.push(`Ocupaciones: ${filters.ocupacionesSeleccionadas.slice(0, 3).join(', ')}${filters.ocupacionesSeleccionadas.length > 3 ? '...' : ''}`);
    }
    return parts.length > 0 ? `Filtros aplicados: ${parts.join(' | ')}` : 'Sin filtros aplicados (datos totales)';
  };

  // Download options: Distribución de requerimientos
  const requerimientosDownloadOptions: FormattedExcelOptions | undefined = (() => {
    if (!requerimientosData) return undefined;
    const data: { categoria: string; valor: string; ofertas: number; porcentaje: number }[] = [];
    const sections: [string, DistribucionItem[]][] = [
      ['Nivel educativo', requerimientosData.educacion],
      ['Experiencia', requerimientosData.experiencia],
      ['Seniority', requerimientosData.seniority],
      ['Modalidad', requerimientosData.modalidad],
      ['Personal a cargo', requerimientosData.genteCargo],
      ['Jornada', requerimientosData.jornada],
    ];
    if (skillsDigitales.length > 0) {
      sections.push(['Skills digitales', skillsDigitales.map(s => ({ name: s.name, value: s.value, porcentaje: s.porcentaje }))]);
    }
    for (const [cat, items] of sections) {
      for (const item of items) {
        data.push({ categoria: cat, valor: item.name, ofertas: item.value, porcentaje: item.porcentaje });
      }
    }
    return {
      title: 'Otros requerimientos solicitados en las ofertas laborales activas',
      subtitle: getFiltersSubtitle(),
      data,
      columns: [
        { header: 'Categoría', key: 'categoria' },
        { header: 'Valor', key: 'valor' },
        { header: 'Ofertas laborales', key: 'ofertas' },
        { header: 'Porcentaje (%)', key: 'porcentaje' }
      ],
      filename: 'distribucion_requerimientos',
    };
  })();

  // Download options: Competencias solicitadas en las ofertas laborales activas
  const habilidadesDownloadOptions: FormattedExcelOptions = (() => {
    if (tipoVisualizacion === 'agregada') {
      return {
        title: 'Distribución por categoría de habilidades',
        subtitle: getFiltersSubtitle(),
        data: categoriasL1.slice(0, cantidadCompetencias).map(item => ({
          nombre: item.name,
          menciones: item.value,
          porcentaje: item.porcentaje
        })),
        columns: [
          { header: 'Categoría', key: 'nombre' },
          { header: 'Menciones', key: 'menciones' },
          { header: 'Porcentaje (%)', key: 'porcentaje' }
        ],
        filename: 'habilidades_por_categoria',
      };
    } else {
      const total = topSkillsTotal.slice(0, cantidadCompetencias).reduce((s, i) => s + i.value, 0);
      return {
        title: 'Competencias específicas más demandadas',
        subtitle: getFiltersSubtitle(),
        data: topSkillsTotal.slice(0, cantidadCompetencias).map(item => ({
          competencia: item.name,
          categoria: item.categoriaNombre,
          menciones: item.value,
          porcentaje: total > 0 ? Math.round((item.value / total) * 100 * 10) / 10 : 0
        })),
        columns: [
          { header: 'Competencia', key: 'competencia' },
          { header: 'Categoría', key: 'categoria' },
          { header: 'Menciones', key: 'menciones' },
          { header: 'Porcentaje (%)', key: 'porcentaje' }
        ],
        filename: 'competencias_especificas',
      };
    }
  })();

  // Datos a mostrar según tipo de visualización y cantidad
  const datosGrafico = tipoVisualizacion === 'agregada'
    ? categoriasL1.slice(0, cantidadCompetencias).map(c => ({ ...c, name: capitalize(c.name) }))
    : topSkillsTotal.slice(0, cantidadCompetencias).map((skill) => ({
        code: skill.categoria,
        name: capitalize(skill.name),
        value: skill.value,
        porcentaje: 0,
        categoriaNombre: skill.categoriaNombre
      }));

  return (
    <div className="space-y-6">
      {/* ========== 1. ANÁLISIS DE HABILIDADES (primero según Issue #6) ========== */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            <h2 className="text-base font-semibold text-gray-800">Competencias solicitadas en las ofertas laborales activas</h2>
          </div>

          {/* Selectores (Issue #6) */}
          <div className="flex items-center gap-4">
            {/* Selector cantidad */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Mostrar:</span>
              <div className="relative">
                <select
                  value={cantidadCompetencias}
                  onChange={(e) => setCantidadCompetencias(Number(e.target.value))}
                  className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
                >
                  {CANTIDAD_OPTIONS.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Selector tipo */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Tipo:</span>
              <div className="relative">
                <select
                  value={tipoVisualizacion}
                  onChange={(e) => setTipoVisualizacion(e.target.value as 'especifica' | 'agregada')}
                  className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
                >
                  {TIPO_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>

            <ChartDownloadButton {...habilidadesDownloadOptions} />
          </div>
        </div>

        {/* Gráfico de barras horizontales — altura dinámica */}
        {(() => {
          const chartHeight = tipoVisualizacion === 'agregada'
            ? Math.max(400, datosGrafico.length * 35)
            : Math.max(400, datosGrafico.length * 24);
          const needsScroll = chartHeight > 600;

          return (
            <div className={needsScroll ? "overflow-y-auto max-h-[600px]" : ""}>
              <div style={{ height: chartHeight }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={datosGrafico}
                    layout="vertical"
                    margin={{ left: 10, right: 30 }}
                    barSize={tipoVisualizacion === 'agregada' ? 20 : 14}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
                    <XAxis type="number" stroke="#6b7280" style={{ fontSize: '11px' }} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={tipoVisualizacion === 'agregada' ? 220 : 280}
                      stroke="#6b7280"
                      tick={{ fontSize: 11, fontWeight: 500 }}
                      tickFormatter={(value: string) => value.length > 42 ? value.substring(0, 41) + '…' : value}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          const idx = datosGrafico.findIndex(g => g.name === d.name);
                          let color: string;
                          if (tipoVisualizacion === 'agregada') {
                            const catIndex = categoriasL1.findIndex(c => c.code === d.code);
                            color = catIndex >= 0 ? COLORS_L1[catIndex % COLORS_L1.length] : '#6b7280';
                          } else {
                            color = COLORS_SKILLS[idx >= 0 ? idx % COLORS_SKILLS.length : 0];
                          }
                          return (
                            <div className="bg-white px-4 py-3 shadow-xl rounded-lg border border-gray-200 text-sm">
                              <div className="flex items-center gap-2 mb-1">
                                <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                                <p className="font-semibold text-gray-800">{capitalize(d.name)}</p>
                              </div>
                              <p className="text-gray-600">{d.value} menciones</p>
                              {tipoVisualizacion === 'especifica' && d.categoriaNombre && (
                                <p className="text-xs text-gray-400 mt-1">Categoría: {capitalize(d.categoriaNombre)}</p>
                              )}
                              {tipoVisualizacion === 'agregada' && d.porcentaje > 0 && (
                                <p className="text-xs text-gray-400 mt-1">{d.porcentaje}% del total</p>
                              )}
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {datosGrafico.map((item, index) => {
                        let color: string;
                        if (tipoVisualizacion === 'agregada') {
                          const catIndex = categoriasL1.findIndex(c => c.code === item.code);
                          color = catIndex >= 0 ? COLORS_L1[catIndex % COLORS_L1.length] : COLORS_L1[index % COLORS_L1.length];
                        } else {
                          color = COLORS_SKILLS[index % COLORS_SKILLS.length];
                        }
                        return <Cell key={`cell-${index}`} fill={color} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })()}
      </div>

      {/* ========== 2. DISTRIBUCIÓN DE REQUERIMIENTOS (segundo según Issue #6) ========== */}
      {requerimientosData && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-gray-800">Otros requerimientos solicitados en las ofertas laborales activas</h3>
            {requerimientosDownloadOptions && <ChartDownloadButton {...requerimientosDownloadOptions} />}
          </div>

          <div className="space-y-0">
            <StackedBar
              label="Nivel educativo"
              data={requerimientosData.educacion}
              icon={GraduationCap}
            />
            <StackedBar
              label="Experiencia"
              data={requerimientosData.experiencia}
              icon={Clock}
            />
            <StackedBar
              label="Seniority"
              data={requerimientosData.seniority}
              icon={TrendingUp}
            />
            <StackedBar
              label="Modalidad"
              data={requerimientosData.modalidad}
              icon={MapPin}
            />
            <StackedBar
              label="Personal a cargo"
              data={requerimientosData.genteCargo}
              icon={Users}
            />
            <StackedBar
              label="Jornada"
              data={requerimientosData.jornada}
              icon={Briefcase}
            />
            {skillsDigitales.length > 0 && (
              <StackedBar
                label="Skills digitales"
                data={skillsDigitales.map(s => ({ name: s.name, value: s.value, porcentaje: s.porcentaje }))}
                icon={Cpu}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
