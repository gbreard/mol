'use client';

import { useState, useMemo } from 'react';
import { Search, Star, Circle, BookOpen, Wrench } from 'lucide-react';
import { SkillItem } from '@/lib/types';

interface SkillsListProps {
  essential: SkillItem[];
  optional: SkillItem[];
  title?: string;
  showSearch?: boolean;
  maxHeight?: string;
  type?: 'skills' | 'knowledge';
}

export default function SkillsList({
  essential,
  optional,
  title,
  showSearch = true,
  maxHeight = '400px',
  type = 'skills'
}: SkillsListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'essential' | 'optional'>('all');

  const { filteredItems, essentialCount, optionalCount } = useMemo(() => {
    const searchLower = searchTerm.toLowerCase();

    const allItems = [
      ...essential.map(s => ({ ...s, isEssential: true, isOptional: false })),
      ...optional.map(s => ({ ...s, isEssential: false, isOptional: true }))
    ];

    const filtered = allItems.filter(item => {
      const matchesSearch = !searchTerm || item.label.toLowerCase().includes(searchLower);
      const matchesTab = activeTab === 'all' ||
        (activeTab === 'essential' && item.isEssential) ||
        (activeTab === 'optional' && item.isOptional);
      return matchesSearch && matchesTab;
    });

    // Sort: essential first, then alphabetically
    filtered.sort((a, b) => {
      if (a.isEssential && !b.isEssential) return -1;
      if (!a.isEssential && b.isEssential) return 1;
      return a.label.localeCompare(b.label);
    });

    return {
      filteredItems: filtered,
      essentialCount: essential.length,
      optionalCount: optional.length
    };
  }, [essential, optional, searchTerm, activeTab]);

  const total = essentialCount + optionalCount;
  const Icon = type === 'knowledge' ? BookOpen : Wrench;
  const colorClass = type === 'knowledge' ? 'amber' : 'indigo';

  if (total === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Icon className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No hay {type === 'knowledge' ? 'conocimientos' : 'skills'} registradas</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      {title && (
        <div className="mb-3">
          <h3 className={`font-semibold text-${colorClass}-900 flex items-center gap-2`}>
            <Icon className={`w-5 h-5 text-${colorClass}-600`} />
            {title}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {total} {type === 'knowledge' ? 'conocimientos' : 'competencias'} ({essentialCount} esenciales, {optionalCount} opcionales)
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-3">
        <button
          onClick={() => setActiveTab('all')}
          className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
            activeTab === 'all'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Todas ({total})
        </button>
        <button
          onClick={() => setActiveTab('essential')}
          className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
            activeTab === 'essential'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Esenciales ({essentialCount})
        </button>
        <button
          onClick={() => setActiveTab('optional')}
          className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
            activeTab === 'optional'
              ? 'text-gray-600 border-b-2 border-gray-400 bg-gray-50'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          Opcionales ({optionalCount})
        </button>
      </div>

      {/* Search */}
      {showSearch && (
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder={`Buscar ${type === 'knowledge' ? 'conocimiento' : 'competencia'}...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      )}

      {/* List */}
      <div className="flex-1 overflow-y-auto" style={{ maxHeight }}>
        {filteredItems.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No se encontraron resultados</p>
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
          <ul className="space-y-1">
            {filteredItems.map((item, index) => (
              <li
                key={`${item.id}-${index}`}
                className={`px-3 py-2 rounded-lg transition-colors ${
                  item.isEssential ? 'bg-blue-50 hover:bg-blue-100' : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-start gap-2">
                  {item.isEssential ? (
                    <Star className="flex-shrink-0 w-4 h-4 mt-0.5 text-blue-500 fill-blue-500" />
                  ) : (
                    <Circle className="flex-shrink-0 w-4 h-4 mt-0.5 text-gray-400" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{item.label}</p>
                    <div className="flex gap-2 mt-0.5 text-xs text-gray-500">
                      <span className="font-mono">{item.L2 || item.L1}</span>
                      {item.isEssential && (
                        <span className="text-blue-600 font-medium">Esencial</span>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      {searchTerm && filteredItems.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-200 text-sm text-gray-600">
          Mostrando {filteredItems.length} de {total}
        </div>
      )}
    </div>
  );
}
