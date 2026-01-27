"use client";

import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Filter, Loader2, AlertCircle, GraduationCap, Clock, TrendingUp, MapPin, Users, Briefcase, Cpu, Layers, ChevronDown } from "lucide-react";
import { getDistribucionRequerimientos, getSkillsPorCategoriaL1, getSkillsDigitales, getTopSkillsConCategoria, getTopSkillsPorCategoria, SkillsFilters, RequerimientosFilters } from "@/lib/supabase";
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
    <div className="py-3 border-b border-gray-100 last:border-0">
      <div className="flex items-center gap-4">
        {/* Label con icono */}
        <div className="flex items-center gap-2 w-40 flex-shrink-0">
          <div className="p-1.5 bg-gray-100 rounded-lg">
            <Icon className="w-4 h-4 text-gray-600" />
          </div>
          <span className="text-sm font-medium text-gray-700">{label}</span>
        </div>

        {/* Barra apilada */}
        <div className="flex-1 flex h-7 rounded-lg overflow-hidden bg-gray-100 relative">
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

      {/* Leyenda debajo de la barra */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 ml-44">
        {filteredData.map((item) => (
          <div key={item.name} className="flex items-center gap-1.5 text-xs">
            <div
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
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

// Opciones para filtros locales del tab
const EDUCACION_OPTIONS = ['Todos', 'universitario', 'terciario', 'secundario', 'primario', 'Sin especificar'];
const MODALIDAD_OPTIONS = ['Todos', 'presencial', 'hibrido', 'remoto', 'Sin especificar'];
const DIGITAL_OPTIONS = ['Todos', 'Digitales', 'No digitales'];

export function Requerimientos({ filters }: RequerimientosProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requerimientosData, setRequerimientosData] = useState<RequerimientosData | null>(null);

  // Estados para skills clasificadas
  const [categoriasL1, setCategoriasL1] = useState<{code: string, name: string, value: number, porcentaje: number}[]>([]);
  const [allCategoriasL1, setAllCategoriasL1] = useState<{code: string, name: string, value: number, porcentaje: number}[]>([]);
  const [skillsDigitales, setSkillsDigitales] = useState<{name: string, value: number, porcentaje: number}[]>([]);
  const [topSkillsTotal, setTopSkillsTotal] = useState<{name: string, value: number, categoria: string, categoriaNombre: string}[]>([]);
  const [topPorCategoria, setTopPorCategoria] = useState<Record<string, {nombre: string, skills: {name: string, value: number}[]}>>({});

  // Filtros locales del tab
  const [filtroCategoria, setFiltroCategoria] = useState<string>('Todos');
  const [filtroEducacion, setFiltroEducacion] = useState<string>('Todos');
  const [filtroModalidad, setFiltroModalidad] = useState<string>('Todos');
  const [filtroDigital, setFiltroDigital] = useState<string>('Todos');

  // Cargar todas las categorías cuando cambian filtros globales (para el dropdown)
  useEffect(() => {
    async function loadAllCategories() {
      try {
        const allCats = await getSkillsPorCategoriaL1(undefined, filters);
        setAllCategoriasL1(allCats);
      } catch (err) {
        console.error('Error cargando categorías:', err);
      }
    }
    loadAllCategories();
  }, [filters]);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);

        // Construir filtros locales para requerimientos (distribución)
        const localFilters: RequerimientosFilters = {
          educacion: filtroEducacion,
          modalidad: filtroModalidad
        };

        // Construir filtros para skills
        const skillsFilters: SkillsFilters = {
          categoria: filtroCategoria,
          esDigital: filtroDigital === 'Todos' ? null : filtroDigital === 'Digitales'
        };

        const [requerimientos, catL1, digital, topSkills, topCat] = await Promise.all([
          getDistribucionRequerimientos(filters, localFilters),
          getSkillsPorCategoriaL1(skillsFilters, filters),
          getSkillsDigitales(skillsFilters, filters),
          getTopSkillsConCategoria(10, skillsFilters, filters),
          getTopSkillsPorCategoria(5, skillsFilters, filters)
        ]);
        setRequerimientosData(requerimientos);
        setCategoriasL1(catL1);
        setSkillsDigitales(digital);
        setTopSkillsTotal(topSkills);
        setTopPorCategoria(topCat);
        setError(null);
      } catch (err) {
        console.error('Error cargando requerimientos:', err);
        setError('Error al cargar los datos de requerimientos.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [filters, filtroCategoria, filtroEducacion, filtroModalidad, filtroDigital]);

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

  // Opciones de categoría desde los datos cargados (todas las categorías, no filtradas)
  const categoriaOptions = ['Todos', ...allCategoriasL1.map(c => c.name)];

  return (
    <div className="space-y-6">
      {/* Filtros del tab */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <div className="flex items-center gap-6 flex-wrap">
          <div className="flex items-center gap-2 text-gray-500">
            <Filter className="w-4 h-4" />
            <span className="text-sm font-medium">Filtros:</span>
          </div>

          {/* Filtro Categoría */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Categoría skill</label>
            <div className="relative">
              <select
                value={filtroCategoria}
                onChange={(e) => setFiltroCategoria(e.target.value)}
                className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
              >
                {categoriaOptions.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Filtro Educación */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Educación</label>
            <div className="relative">
              <select
                value={filtroEducacion}
                onChange={(e) => setFiltroEducacion(e.target.value)}
                className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
              >
                {EDUCACION_OPTIONS.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Filtro Modalidad */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Modalidad</label>
            <div className="relative">
              <select
                value={filtroModalidad}
                onChange={(e) => setFiltroModalidad(e.target.value)}
                className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
              >
                {MODALIDAD_OPTIONS.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Filtro Skills Digitales */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Skills digitales</label>
            <div className="relative">
              <select
                value={filtroDigital}
                onChange={(e) => setFiltroDigital(e.target.value)}
                className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 pr-8 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
              >
                {DIGITAL_OPTIONS.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Botón limpiar filtros */}
          {(filtroCategoria !== 'Todos' || filtroEducacion !== 'Todos' || filtroModalidad !== 'Todos' || filtroDigital !== 'Todos') && (
            <button
              onClick={() => {
                setFiltroCategoria('Todos');
                setFiltroEducacion('Todos');
                setFiltroModalidad('Todos');
                setFiltroDigital('Todos');
              }}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium mt-4"
            >
              Limpiar filtros
            </button>
          )}
        </div>
      </div>

      {/* Requerimientos - Barras horizontales apiladas al 100% */}
      {requerimientosData && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Distribución de requerimientos</h3>

          <div className="space-y-1">
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

      {/* ========== SKILLS CLASIFICADAS (ESCO) ========== */}
      <div className="border-t border-gray-200 pt-6 mt-6">
        <div className="flex items-center gap-2 mb-6">
          <Layers className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-800">Análisis de habilidades</h2>
        </div>

        {/* Grid: Categorías L1 (3/4) + Top 10 Skills tabla (1/4) */}
        <div className="grid grid-cols-4 gap-6 mb-6" style={{ minHeight: '480px' }}>
          {/* Distribución por Categoría L1 - 3/4 del ancho */}
          <div className="col-span-3 bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex flex-col">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Distribución por categoría de habilidades</h3>
            <ResponsiveContainer width="100%" height={420} className="flex-1">
              <BarChart data={categoriasL1} layout="vertical" margin={{ left: 10, right: 30 }} barSize={20}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
                <XAxis type="number" stroke="#6b7280" style={{ fontSize: '11px' }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={220}
                  stroke="#6b7280"
                  tick={{ fontSize: 11, fontWeight: 500 }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      const catData = topPorCategoria[d.code];
                      const catIndex = categoriasL1.findIndex(c => c.code === d.code);
                      const color = catIndex >= 0 ? COLORS_L1[catIndex % COLORS_L1.length] : '#6b7280';
                      return (
                        <div className="bg-white px-4 py-3 shadow-xl rounded-lg border border-gray-200 text-sm min-w-[200px]">
                          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-100">
                            <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                            <p className="font-semibold text-gray-800">{d.name}</p>
                          </div>
                          <p className="text-gray-600 mb-3">{d.value} skills ({d.porcentaje}%)</p>
                          {catData && catData.skills.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-gray-500 mb-1.5">Top 5 habilidades:</p>
                              <div className="space-y-1">
                                {catData.skills.slice(0, 5).map((skill, idx) => (
                                  <div key={idx} className="flex items-center gap-2">
                                    <span className="text-xs text-gray-400 w-3">{idx + 1}.</span>
                                    <span className="text-xs text-gray-700 flex-1 truncate">{skill.name}</span>
                                    <span className="text-xs text-gray-400">{skill.value}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {categoriasL1.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS_L1[index % COLORS_L1.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top 10 Skills - Tabla */}
          <div className="col-span-1 bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex flex-col">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Top 10 habilidades</h3>
            <div className="flex-1 flex flex-col justify-between">
              {topSkillsTotal.map((skill, index) => {
                const catIndex = categoriasL1.findIndex(c => c.code === skill.categoria);
                const color = catIndex >= 0 ? COLORS_L1[catIndex % COLORS_L1.length] : '#6b7280';
                const total = topSkillsTotal.reduce((sum, s) => sum + s.value, 0);
                const porcentaje = Math.round(skill.value * 100 / total);
                return (
                  <div key={index} className="flex items-center gap-2 py-2 border-b border-gray-50 last:border-0">
                    <div
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 truncate" title={skill.name}>
                        {skill.name}
                      </p>
                      <p className="text-xs text-gray-400 truncate" title={skill.categoriaNombre}>
                        {skill.categoriaNombre}
                      </p>
                    </div>
                    <span className="text-sm font-medium text-gray-600 flex-shrink-0">
                      {porcentaje}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
