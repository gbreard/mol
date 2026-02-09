"use client";

import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Loader2, AlertCircle, GraduationCap, Clock, TrendingUp, MapPin, Users, Briefcase, Cpu, Layers, ChevronDown, Download } from "lucide-react";
import { downloadFormattedExcel } from "@/components/ExportButton";
import { getDistribucionRequerimientos, getSkillsPorCategoriaL1, getSkillsDigitales, getTopSkillsConCategoria, SkillsFilters } from "@/lib/supabase";
import { DashboardFilters } from "@/lib/types";

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
            <span className="text-gray-600">{item.name}</span>
            <span className="text-gray-400">({item.porcentaje}%)</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Colores para categorías L1
const COLORS_L1 = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1', '#14b8a6', '#a855f7'];

// Opciones de cantidad de competencias
const CANTIDAD_OPTIONS = [20, 40, 60, 100];

// Opciones de tipo de visualización
const TIPO_OPTIONS = [
  { value: 'especifica', label: 'Competencias específicas' },
  { value: 'agregada', label: 'Por categoría (agregado)' }
];

export function Requerimientos({ filters }: RequerimientosProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requerimientosData, setRequerimientosData] = useState<RequerimientosData | null>(null);

  // Estados para skills clasificadas
  const [categoriasL1, setCategoriasL1] = useState<{code: string, name: string, value: number, porcentaje: number}[]>([]);
  const [skillsDigitales, setSkillsDigitales] = useState<{name: string, value: number, porcentaje: number}[]>([]);
  const [topSkillsTotal, setTopSkillsTotal] = useState<{name: string, value: number, categoria: string, categoriaNombre: string}[]>([]);

  // Selectores del gráfico de habilidades (Issue #6)
  const [cantidadCompetencias, setCantidadCompetencias] = useState<number>(20);
  const [tipoVisualizacion, setTipoVisualizacion] = useState<'especifica' | 'agregada'>('especifica');

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);

        const skillsFilters: SkillsFilters = {};

        const [requerimientos, catL1, digital, topSkills] = await Promise.all([
          getDistribucionRequerimientos(filters, {}),
          getSkillsPorCategoriaL1(skillsFilters, filters),
          getSkillsDigitales(skillsFilters, filters),
          getTopSkillsConCategoria(100, skillsFilters, filters) // Cargar más para poder filtrar
        ]);
        setRequerimientosData(requerimientos);
        setCategoriasL1(catL1);
        setSkillsDigitales(digital);
        setTopSkillsTotal(topSkills);
        setError(null);
      } catch (err) {
        console.error('Error cargando requerimientos:', err);
        setError('Error al cargar los datos de requerimientos.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [filters]);

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
    if (filters.localidad) parts.push(`Localidad: ${filters.localidad}`);
    if (filters.fechaDesde) parts.push(`Desde: ${filters.fechaDesde.toLocaleDateString('es-AR')}`);
    if (filters.fechaHasta) parts.push(`Hasta: ${filters.fechaHasta.toLocaleDateString('es-AR')}`);
    if (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0) {
      parts.push(`Ocupaciones: ${filters.ocupacionesSeleccionadas.slice(0, 3).join(', ')}${filters.ocupacionesSeleccionadas.length > 3 ? '...' : ''}`);
    }
    return parts.length > 0 ? `Filtros aplicados: ${parts.join(' | ')}` : 'Sin filtros aplicados (datos totales)';
  };

  // Handler descarga: Distribución de requerimientos
  const handleDownloadRequerimientos = () => {
    if (!requerimientosData) return;
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
    downloadFormattedExcel({
      title: 'Distribución de los requerimientos',
      subtitle: getFiltersSubtitle(),
      data,
      columns: [
        { header: 'Categoría', key: 'categoria' },
        { header: 'Valor', key: 'valor' },
        { header: 'Ofertas laborales', key: 'ofertas' },
        { header: 'Porcentaje (%)', key: 'porcentaje' }
      ],
      filename: 'distribucion_requerimientos',
      showPercentage: true
    });
  };

  // Handler descarga: Análisis de habilidades
  const handleDownloadHabilidades = () => {
    if (tipoVisualizacion === 'agregada') {
      const data = categoriasL1.slice(0, cantidadCompetencias).map(item => ({
        nombre: item.name,
        menciones: item.value,
        porcentaje: item.porcentaje
      }));
      downloadFormattedExcel({
        title: 'Distribución por categoría de habilidades',
        subtitle: getFiltersSubtitle(),
        data,
        columns: [
          { header: 'Categoría', key: 'nombre' },
          { header: 'Menciones', key: 'menciones' },
          { header: 'Porcentaje (%)', key: 'porcentaje' }
        ],
        filename: 'habilidades_por_categoria',
        showPercentage: true
      });
    } else {
      const total = topSkillsTotal.slice(0, cantidadCompetencias).reduce((s, i) => s + i.value, 0);
      const data = topSkillsTotal.slice(0, cantidadCompetencias).map(item => ({
        competencia: item.name,
        categoria: item.categoriaNombre,
        menciones: item.value,
        porcentaje: total > 0 ? Math.round((item.value / total) * 100 * 10) / 10 : 0
      }));
      downloadFormattedExcel({
        title: 'Competencias específicas más demandadas',
        subtitle: getFiltersSubtitle(),
        data,
        columns: [
          { header: 'Competencia', key: 'competencia' },
          { header: 'Categoría', key: 'categoria' },
          { header: 'Menciones', key: 'menciones' },
          { header: 'Porcentaje (%)', key: 'porcentaje' }
        ],
        filename: 'competencias_especificas',
        showPercentage: true
      });
    }
  };

  // Datos a mostrar según tipo de visualización y cantidad
  const datosGrafico = tipoVisualizacion === 'agregada'
    ? categoriasL1.slice(0, cantidadCompetencias)
    : topSkillsTotal.slice(0, cantidadCompetencias).map((skill, idx) => ({
        code: skill.categoria,
        name: skill.name,
        value: skill.value,
        porcentaje: 0, // No usado en específicas
        categoriaNombre: skill.categoriaNombre
      }));

  return (
    <div className="space-y-6">
      {/* ========== 1. ANÁLISIS DE HABILIDADES (primero según Issue #6) ========== */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            <h2 className="text-base font-semibold text-gray-800">Análisis de habilidades</h2>
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

            {/* Download formatted Excel */}
            <button
              onClick={handleDownloadHabilidades}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-gray-600 hover:text-gray-800"
              title="Descargar Excel"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Gráfico de barras horizontales */}
        <div className="h-[400px]">
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
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload;
                    const catIndex = categoriasL1.findIndex(c => c.code === d.code);
                    const color = catIndex >= 0 ? COLORS_L1[catIndex % COLORS_L1.length] : '#6b7280';
                    return (
                      <div className="bg-white px-4 py-3 shadow-xl rounded-lg border border-gray-200 text-sm">
                        <div className="flex items-center gap-2 mb-1">
                          <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                          <p className="font-semibold text-gray-800">{d.name}</p>
                        </div>
                        <p className="text-gray-600">{d.value} menciones</p>
                        {tipoVisualizacion === 'especifica' && d.categoriaNombre && (
                          <p className="text-xs text-gray-400 mt-1">Categoría: {d.categoriaNombre}</p>
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
                  const catIndex = categoriasL1.findIndex(c => c.code === item.code);
                  const color = catIndex >= 0 ? COLORS_L1[catIndex % COLORS_L1.length] : COLORS_L1[index % COLORS_L1.length];
                  return <Cell key={`cell-${index}`} fill={color} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ========== 2. DISTRIBUCIÓN DE REQUERIMIENTOS (segundo según Issue #6) ========== */}
      {requerimientosData && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-gray-800">Distribución de los requerimientos</h3>
            <button
              onClick={handleDownloadRequerimientos}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-gray-600 hover:text-gray-800"
              title="Descargar Excel"
            >
              <Download className="w-4 h-4" />
            </button>
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
