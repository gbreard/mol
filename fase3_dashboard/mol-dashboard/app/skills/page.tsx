'use client';

import { useEffect, useState } from 'react';
import { Map, Briefcase, GitCompare, Target, Loader2, Search, X } from 'lucide-react';
import SkillsSunburst from '@/components/SkillsSunburst';
import OccupationDetail from '@/components/OccupationDetail';
import OccupationCompare from '@/components/OccupationCompare';
import MySkillsSearch from '@/components/MySkillsSearch';
import { OccupationFullDetailIndex } from '@/lib/types';

type TabId = 'taxonomy' | 'occupation' | 'compare' | 'myskills';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const TABS: Tab[] = [
  {
    id: 'taxonomy',
    label: 'Taxonomia',
    icon: <Map className="w-5 h-5" />,
    description: 'Explorar la estructura jerarquica de competencias ESCO'
  },
  {
    id: 'occupation',
    label: 'Ocupacion',
    icon: <Briefcase className="w-5 h-5" />,
    description: 'Ver skills y conocimientos de una ocupacion especifica'
  },
  {
    id: 'compare',
    label: 'Comparar',
    icon: <GitCompare className="w-5 h-5" />,
    description: 'Analizar gaps entre dos ocupaciones'
  },
  {
    id: 'myskills',
    label: 'Mis Skills',
    icon: <Target className="w-5 h-5" />,
    description: 'Encontrar ocupaciones basadas en tus competencias'
  }
];

interface HierarchyNode {
  name: string;
  label?: string;
  type?: 'skill' | 'knowledge';
  value?: number;
  children?: HierarchyNode[];
}

interface Stats {
  total: number;
  skills: number;
  knowledge: number;
}

interface OccupationBasicInfo {
  id: string;
  label: string;
  isco: string;
}

export default function SkillsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('taxonomy');
  const [stats, setStats] = useState<Stats>({ total: 0, skills: 0, knowledge: 0 });
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // Shared hierarchy data (loaded once, used by stats + sunburst)
  const [hierarchyData, setHierarchyData] = useState<HierarchyNode | null>(null);

  // Occupation data
  const [occupationsData, setOccupationsData] = useState<OccupationFullDetailIndex | null>(null);
  const [occupationsList, setOccupationsList] = useState<OccupationBasicInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // For Tab 2: Occupation Detail - pre-selected occupation
  const [selectedOccupation, setSelectedOccupation] = useState<string | null>(null);

  // For Tab 3: Compare - pre-selected occupations
  const [compareOccA, setCompareOccA] = useState<string | null>(null);
  const [compareOccB, setCompareOccB] = useState<string | null>(null);

  // Load hierarchy data ONCE — used for both stats and sunburst
  useEffect(() => {
    setStatsLoading(true);
    setStatsError(null);

    fetch('/data/esco_skills_hierarchy.json')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setHierarchyData(data);

        let skills = 0;
        let knowledge = 0;

        const countByType = (node: HierarchyNode): void => {
          if (node.type === 'skill' && node.value) {
            skills += 1;
          } else if (node.type === 'knowledge' && node.value) {
            knowledge += 1;
          }
          if (node.children) {
            node.children.forEach(countByType);
          }
        };

        if (data.children) {
          data.children.forEach(countByType);
        }

        setStats({ total: skills + knowledge, skills, knowledge });
        setStatsLoading(false);
      })
      .catch(err => {
        console.error('[SKILLS] Error loading hierarchy:', err);
        setStatsError(err.message || 'Error cargando datos');
        setStatsLoading(false);
      });
  }, []);

  // Load occupation data when switching to occupation/compare/myskills tabs
  useEffect(() => {
    if ((activeTab === 'occupation' || activeTab === 'compare' || activeTab === 'myskills') &&
        !occupationsData && !isLoading) {
      setIsLoading(true);

      fetch('/data/occupation_full_detail.json')
        .then(res => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return res.json();
        })
        .then((data: OccupationFullDetailIndex) => {
          setOccupationsData(data);

          // Build occupations list sorted alphabetically
          const list: OccupationBasicInfo[] = Object.entries(data)
            .map(([id, occ]) => ({
              id,
              label: occ.label,
              isco: occ.isco
            }))
            .sort((a, b) => a.label.localeCompare(b.label));

          setOccupationsList(list);
          setIsLoading(false);
        })
        .catch(err => {
          console.error('[SKILLS] Error loading occupations:', err);
          setIsLoading(false);
        });
    }
  }, [activeTab, occupationsData, isLoading]);

  // Handler for navigating from occupation detail to compare
  const handleNavigateToCompare = (occAId: string, occBId: string) => {
    setCompareOccA(occAId);
    setCompareOccB(occBId);
    setActiveTab('compare');
  };

  // Handler for navigating to occupation detail
  const handleNavigateToOccupation = (occId: string) => {
    setSelectedOccupation(occId);
    setActiveTab('occupation');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Skills Intelligence Dashboard
          </h1>
          <p className="mt-2 text-gray-600">
            Explora la taxonomia ESCO, analiza ocupaciones y planifica transiciones laborales
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
          <div className="flex border-b border-gray-200">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-4 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                {tab.icon}
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Tab description */}
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
            <p className="text-sm text-gray-600">
              {TABS.find(t => t.id === activeTab)?.description}
            </p>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'taxonomy' && (
          <TaxonomyTab stats={stats} statsLoading={statsLoading} statsError={statsError} hierarchyData={hierarchyData} />
        )}

        {activeTab === 'occupation' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <OccupationDetail
              occupationsData={occupationsData}
              occupationsList={occupationsList}
              onNavigateToCompare={handleNavigateToCompare}
              initialOccupation={selectedOccupation}
            />
          </div>
        )}

        {activeTab === 'compare' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <OccupationCompare
              occupationsData={occupationsData}
              occupationsList={occupationsList}
              initialOccA={compareOccA}
              initialOccB={compareOccB}
            />
          </div>
        )}

        {activeTab === 'myskills' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <MySkillsSearch
              occupationsData={occupationsData}
              occupationsList={occupationsList}
              onNavigateToOccupation={handleNavigateToOccupation}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ============= Taxonomy Tab =============

type FilterType = 'all' | 'skills' | 'knowledge';

function TaxonomyTab({ stats, statsLoading, statsError, hierarchyData }: {
  stats: Stats;
  statsLoading: boolean;
  statsError: string | null;
  hierarchyData: HierarchyNode | null;
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');

  return (
    <>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          {statsLoading ? (
            <div className="h-9 w-24 bg-gray-200 rounded animate-pulse" />
          ) : statsError ? (
            <div className="text-red-500 text-sm">{statsError}</div>
          ) : (
            <div className="text-3xl font-bold text-gray-900">
              {stats.total.toLocaleString()}
            </div>
          )}
          <div className="text-sm text-gray-500 mt-1">Total competencias ESCO</div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              {statsLoading ? (
                <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
              ) : (
                <div className="text-2xl font-bold text-indigo-600">
                  {stats.skills.toLocaleString()}
                </div>
              )}
              <div className="text-sm text-gray-500 mt-1">Skills (saber hacer)</div>
            </div>
            <div className="text-lg font-semibold text-indigo-400">
              {stats.total > 0 ? ((stats.skills / stats.total) * 100).toFixed(0) : 0}%
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              {statsLoading ? (
                <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
              ) : (
                <div className="text-2xl font-bold text-amber-600">
                  {stats.knowledge.toLocaleString()}
                </div>
              )}
              <div className="text-sm text-gray-500 mt-1">Conocimientos (saber)</div>
            </div>
            <div className="text-lg font-semibold text-amber-400">
              {stats.total > 0 ? ((stats.knowledge / stats.total) * 100).toFixed(0) : 0}%
            </div>
          </div>
        </div>
      </div>

      {/* Sunburst */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Distribucion Jerarquica de Competencias
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          <strong>Click en cualquier segmento</strong> para ver la lista completa de competencias en esa categoria.
        </p>

        {/* Search and Filter Controls */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          {/* Search */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Buscar competencia</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Ej: analisis, programacion, gestion..."
                className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-200 focus:border-blue-500 text-sm"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            {searchTerm && (
              <p className="text-xs text-gray-500 mt-1">
                Los segmentos que coinciden se resaltan en el grafico
              </p>
            )}
          </div>

          {/* Filter Toggle */}
          <div className="sm:w-64">
            <label className="block text-sm font-medium text-gray-700 mb-1">Mostrar</label>
            <div className="flex rounded-lg border border-gray-300 overflow-hidden">
              <button
                onClick={() => setFilterType('all')}
                className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
                  filterType === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                Todos
              </button>
              <button
                onClick={() => setFilterType('skills')}
                className={`flex-1 px-3 py-2 text-sm font-medium transition-colors border-l border-gray-300 ${
                  filterType === 'skills'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                Skills
              </button>
              <button
                onClick={() => setFilterType('knowledge')}
                className={`flex-1 px-3 py-2 text-sm font-medium transition-colors border-l border-gray-300 ${
                  filterType === 'knowledge'
                    ? 'bg-amber-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                Conocim.
              </button>
            </div>
          </div>
        </div>

        <SkillsSunburst
          data={hierarchyData ?? undefined}
          searchTerm={searchTerm}
          filterType={filterType}
        />
      </div>

      {/* Legend */}
      <div className="mt-8 bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Estructura de la taxonomia ESCO
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
            <div className="font-medium text-blue-900 mb-2">S - Competencias Tecnicas</div>
            <p className="text-sm text-blue-800">
              Habilidades especificas de un campo profesional (S1-S8).
            </p>
          </div>

          <div className="bg-green-50 rounded-lg p-4 border border-green-100">
            <div className="font-medium text-green-900 mb-2">T - Competencias Transversales</div>
            <p className="text-sm text-green-800">
              Capacidades aplicables a cualquier ocupacion (T1-T6).
            </p>
          </div>

          <div className="bg-violet-50 rounded-lg p-4 border border-violet-100">
            <div className="font-medium text-violet-900 mb-2">K - Conocimientos</div>
            <p className="text-sm text-violet-800">
              Informacion y conceptos teoricos organizados por area.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

// ============= Coming Soon Tab =============

function ComingSoonTab({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
      <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <Loader2 className="w-8 h-8 text-gray-400" />
      </div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">{title}</h2>
      <p className="text-gray-600 max-w-md mx-auto mb-6">{description}</p>
      <p className="text-sm text-gray-500">Proximamente disponible</p>
    </div>
  );
}
