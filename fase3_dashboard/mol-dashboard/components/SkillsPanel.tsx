'use client';

import { useState, useMemo } from 'react';
import { X, Search, ChevronRight, Star, Circle } from 'lucide-react';

interface Skill {
  name: string;
  type: 'skill' | 'knowledge';
  isEssential?: boolean;
  isOptional?: boolean;
}

interface SkillsPanelProps {
  path: string[];
  skills: Skill[];
  onClose: () => void;
  occupation?: { label: string; isco?: string };
  totalInCategory?: number;
  matchingCount?: number;
}

export default function SkillsPanel({
  path,
  skills,
  onClose,
  occupation,
  totalInCategory,
  matchingCount
}: SkillsPanelProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'essential' | 'optional'>('all');

  // Separar y filtrar skills
  const { filteredSkills, essentialCount, optionalCount } = useMemo(() => {
    const searchLower = searchTerm.toLowerCase();

    const filtered = skills.filter(s => {
      const matchesSearch = !searchTerm || s.name.toLowerCase().includes(searchLower);
      const matchesTab = activeTab === 'all' ||
        (activeTab === 'essential' && s.isEssential) ||
        (activeTab === 'optional' && s.isOptional);
      return matchesSearch && matchesTab;
    });

    // Ordenar: esenciales primero, luego por nombre
    const sorted = filtered.sort((a, b) => {
      if (a.isEssential && !b.isEssential) return -1;
      if (!a.isEssential && b.isEssential) return 1;
      return a.name.localeCompare(b.name);
    });

    return {
      filteredSkills: sorted,
      essentialCount: skills.filter(s => s.isEssential).length,
      optionalCount: skills.filter(s => s.isOptional).length
    };
  }, [skills, searchTerm, activeTab]);

  return (
    <div className="fixed right-0 top-0 h-screen w-[420px] bg-white shadow-2xl z-50 flex flex-col border-l border-gray-200">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 z-10">
        {/* Path / Contexto */}
        <div className="px-4 pt-4 pb-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-1 text-sm text-gray-600 flex-wrap">
              {path.map((item, i) => (
                <span key={i} className="flex items-center">
                  {i > 0 && <ChevronRight className="w-3 h-3 mx-1 text-gray-400" />}
                  <span className={i === path.length - 1 ? 'font-semibold text-gray-900' : ''}>
                    {item}
                  </span>
                </span>
              ))}
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded-full transition-colors flex-shrink-0"
              aria-label="Cerrar panel"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Contexto de ocupación si hay */}
        {occupation && (
          <div className="px-4 pb-2 bg-blue-50 border-b border-blue-100">
            <div className="text-xs text-blue-600 font-medium">Ocupacion seleccionada</div>
            <div className="text-sm font-semibold text-blue-900">{occupation.label}</div>
            {occupation.isco && (
              <div className="text-xs text-blue-700">ISCO: {occupation.isco}</div>
            )}
          </div>
        )}

        {/* Contador */}
        <div className="px-4 py-3">
          <div className="text-2xl font-bold text-gray-900">
            {skills.length.toLocaleString()}
          </div>
          <div className="text-sm text-gray-500">
            {occupation
              ? `competencias de esta ocupacion en la categoria`
              : 'competencias en esta categoria'}
            {totalInCategory && totalInCategory !== skills.length && (
              <span className="text-gray-400 ml-1">
                (de {totalInCategory} totales)
              </span>
            )}
          </div>
        </div>

        {/* Tabs - solo si hay ocupación */}
        {occupation && (essentialCount > 0 || optionalCount > 0) ? (
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('all')}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'all'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              Todas ({skills.length})
            </button>
            <button
              onClick={() => setActiveTab('essential')}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'essential'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              Esenciales ({essentialCount})
            </button>
            <button
              onClick={() => setActiveTab('optional')}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'optional'
                  ? 'text-blue-400 border-b-2 border-blue-300 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              Opcionales ({optionalCount})
            </button>
          </div>
        ) : (
          <div className="border-b border-gray-200"></div>
        )}

        {/* Busqueda */}
        <div className="p-3 bg-gray-50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar competencia..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Lista de skills */}
      <div className="flex-1 overflow-y-auto">
        {filteredSkills.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No se encontraron competencias</p>
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="mt-2 text-blue-600 hover:underline text-sm"
              >
                Limpiar busqueda
              </button>
            )}
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {filteredSkills.map((skill, index) => (
              <li
                key={`${skill.name}-${index}`}
                className={`px-4 py-3 hover:bg-gray-50 transition-colors ${
                  skill.isEssential ? 'bg-blue-50/50' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  {/* Indicador de esencial/opcional */}
                  {skill.isEssential ? (
                    <Star className="flex-shrink-0 w-4 h-4 mt-1 text-blue-500 fill-blue-500" />
                  ) : skill.isOptional ? (
                    <Circle className="flex-shrink-0 w-4 h-4 mt-1 text-blue-300" />
                  ) : (
                    <span
                      className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${
                        skill.type === 'skill' ? 'bg-indigo-500' : 'bg-amber-500'
                      }`}
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 leading-relaxed">
                      {skill.name}
                    </p>
                    <div className="flex gap-2 mt-0.5">
                      <span className={`text-xs ${
                        skill.type === 'skill' ? 'text-indigo-600' : 'text-amber-600'
                      }`}>
                        {skill.type === 'skill' ? 'Skill' : 'Conocimiento'}
                      </span>
                      {skill.isEssential && (
                        <span className="text-xs text-blue-600 font-medium">• Esencial</span>
                      )}
                      {skill.isOptional && (
                        <span className="text-xs text-blue-400">• Opcional</span>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer con contador de resultados filtrados */}
      {searchTerm && filteredSkills.length > 0 && (
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-4 py-2 text-sm text-gray-600">
          Mostrando {filteredSkills.length} de {skills.length} competencias
        </div>
      )}
    </div>
  );
}
