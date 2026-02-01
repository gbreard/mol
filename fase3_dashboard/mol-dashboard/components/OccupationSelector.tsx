'use client';

import { useState, useMemo, useRef, useEffect } from 'react';
import { Search, X, ChevronDown, Loader2 } from 'lucide-react';

export interface Occupation {
  id: string;
  label: string;
  isco: string;
}

export interface OccupationSkillsData {
  e: string[];  // essential L2 codes
  o: string[];  // optional L2 codes
}

export interface OccupationsIndex {
  occupations: Occupation[];
  skills: Record<string, OccupationSkillsData>;
  stats: {
    total_occupations: number;
    occupations_with_skills: number;
  };
}

interface OccupationSelectorProps {
  value: Occupation | null;
  onChange: (occupation: Occupation | null, skills: OccupationSkillsData | null) => void;
  occupationsData: OccupationsIndex | null;
  color?: 'blue' | 'purple';
  label?: string;
  placeholder?: string;
}

export default function OccupationSelector({
  value,
  onChange,
  occupationsData,
  color = 'blue',
  label,
  placeholder = 'Seleccionar ocupacion...'
}: OccupationSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const colorClasses = {
    blue: {
      ring: 'focus:ring-blue-500',
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-700',
      badge: 'bg-blue-100 text-blue-800',
      hover: 'hover:bg-blue-50'
    },
    purple: {
      ring: 'focus:ring-purple-500',
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-700',
      badge: 'bg-purple-100 text-purple-800',
      hover: 'hover:bg-purple-50'
    }
  };

  const colors = colorClasses[color];

  // Filtrar ocupaciones
  const filteredOccupations = useMemo(() => {
    if (!occupationsData) return [];

    if (!searchTerm.trim()) {
      // Sin búsqueda, mostrar todas (virtualizadas en el scroll)
      return occupationsData.occupations;
    }

    const normalizedSearch = searchTerm.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    return occupationsData.occupations
      .filter(occ => {
        const normalizedLabel = occ.label.toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '');
        return normalizedLabel.includes(normalizedSearch) ||
               occ.isco.toLowerCase().includes(normalizedSearch);
      });
  }, [occupationsData, searchTerm]);

  // Reset highlighted index cuando cambia el filtro
  useEffect(() => {
    setHighlightedIndex(0);
  }, [searchTerm]);

  // Cerrar al hacer click fuera
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll al elemento resaltado
  useEffect(() => {
    if (isOpen && listRef.current) {
      const highlightedElement = listRef.current.children[highlightedIndex] as HTMLElement;
      if (highlightedElement) {
        highlightedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex, isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === 'ArrowDown') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(i => Math.min(i + 1, filteredOccupations.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(i => Math.max(i - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (filteredOccupations[highlightedIndex]) {
          selectOccupation(filteredOccupations[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  const selectOccupation = (occ: Occupation) => {
    const skills = occupationsData?.skills[occ.id] || null;
    onChange(occ, skills);
    setIsOpen(false);
    setSearchTerm('');
  };

  const clearSelection = () => {
    onChange(null, null);
    setSearchTerm('');
  };

  if (!occupationsData) {
    return (
      <div className="flex items-center gap-2 p-3 rounded-lg border border-gray-200 bg-gray-50">
        <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
        <span className="text-sm text-gray-500">Cargando ocupaciones...</span>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative w-full">
      {label && (
        <label className={`block text-sm font-medium mb-1 ${colors.text}`}>
          {label}
        </label>
      )}

      {/* Valor seleccionado o input de busqueda */}
      {value ? (
        <div className={`flex items-center gap-2 p-3 rounded-lg border ${colors.border} ${colors.bg}`}>
          <div className="flex-1 min-w-0">
            <div className={`font-medium text-sm truncate ${colors.text}`}>
              {value.label}
            </div>
            <div className="text-xs text-gray-500">
              ISCO: {value.isco}
            </div>
          </div>
          <button
            onClick={clearSelection}
            className="p-1 hover:bg-white rounded-full transition-colors"
            aria-label="Limpiar seleccion"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      ) : (
        <div
          className={`flex items-center gap-2 p-3 rounded-lg border border-gray-300 cursor-pointer
            hover:border-gray-400 transition-colors ${isOpen ? 'ring-2 ' + colors.ring : ''}`}
          onClick={() => {
            setIsOpen(true);
            setTimeout(() => inputRef.current?.focus(), 0);
          }}
        >
          <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
          {isOpen ? (
            <input
              ref={inputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribi para filtrar..."
              className="flex-1 bg-transparent outline-none text-sm"
              autoFocus
            />
          ) : (
            <span className="flex-1 text-sm text-gray-500">{placeholder}</span>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      )}

      {/* Dropdown */}
      {isOpen && !value && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
          {/* Header con contador */}
          <div className="px-3 py-2 bg-gray-50 border-b border-gray-100 text-xs text-gray-500">
            {searchTerm
              ? `${filteredOccupations.length} resultados`
              : `${occupationsData.stats.total_occupations} ocupaciones ESCO`}
          </div>

          {/* Lista */}
          <ul ref={listRef} className="overflow-y-auto max-h-64">
            {filteredOccupations.length === 0 ? (
              <li className="px-4 py-8 text-center text-gray-500 text-sm">
                No se encontraron ocupaciones
              </li>
            ) : (
              filteredOccupations.map((occ, index) => (
                <li
                  key={occ.id}
                  onClick={() => selectOccupation(occ)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  className={`px-4 py-2.5 cursor-pointer transition-colors border-b border-gray-50 ${
                    index === highlightedIndex ? colors.bg : colors.hover
                  }`}
                >
                  <div className="font-medium text-sm text-gray-900 truncate">
                    {occ.label}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    ISCO: {occ.isco}
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
