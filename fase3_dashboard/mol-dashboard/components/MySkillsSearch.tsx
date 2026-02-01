'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { Search, X, Target, Loader2, ChevronRight, Star, AlertCircle, Trash2 } from 'lucide-react';
import { OccupationFullDetailIndex, SkillsSearchableIndex, SearchableSkill } from '@/lib/types';

interface OccupationBasicInfo {
  id: string;
  label: string;
  isco: string;
}

interface MySkillsSearchProps {
  occupationsData: OccupationFullDetailIndex | null;
  occupationsList: OccupationBasicInfo[];
  onNavigateToOccupation?: (occId: string) => void;
  onNavigateToCompare?: (occAId: string, occBId: string) => void;
}

interface OccupationMatch {
  id: string;
  label: string;
  isco: string;
  matchScore: number;           // 0-100, based on essential skills covered
  essentialTotal: number;
  essentialCovered: number;
  optionalCovered: number;
  gapCount: number;             // Essential skills missing
}

export default function MySkillsSearch({
  occupationsData,
  occupationsList,
  onNavigateToOccupation,
  onNavigateToCompare
}: MySkillsSearchProps) {
  // Skills data
  const [skillsData, setSkillsData] = useState<SkillsSearchableIndex | null>(null);
  const [isLoadingSkills, setIsLoadingSkills] = useState(false);

  // Selected skills
  const [selectedSkills, setSelectedSkills] = useState<SearchableSkill[]>([]);

  // Search state
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Sort options
  const [sortBy, setSortBy] = useState<'match' | 'gap' | 'alpha'>('match');

  // Load skills data
  useEffect(() => {
    if (!skillsData && !isLoadingSkills) {
      setIsLoadingSkills(true);
      fetch('/data/skills_searchable.json')
        .then(res => res.json())
        .then((data: SkillsSearchableIndex) => {
          setSkillsData(data);
          setIsLoadingSkills(false);
        })
        .catch(err => {
          console.error('Error loading skills:', err);
          setIsLoadingSkills(false);
        });
    }
  }, [skillsData, isLoadingSkills]);

  // Close search dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearchOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter skills for search
  const filteredSkills = useMemo(() => {
    if (!skillsData || !searchTerm.trim()) return [];

    const normalizedSearch = searchTerm.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    const selectedIds = new Set(selectedSkills.map(s => s.id));

    return skillsData.skills
      .filter(skill => {
        if (selectedIds.has(skill.id)) return false;
        const normalizedLabel = skill.label.toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '');
        return normalizedLabel.includes(normalizedSearch);
      })
      .slice(0, 20);
  }, [skillsData, searchTerm, selectedSkills]);

  // Calculate matching occupations
  const matchingOccupations = useMemo((): OccupationMatch[] => {
    if (!occupationsData || selectedSkills.length === 0) return [];

    const selectedSkillIds = new Set(selectedSkills.map(s => s.id));
    const matches: OccupationMatch[] = [];

    for (const [occId, occ] of Object.entries(occupationsData)) {
      const essentialIds = new Set(occ.skills.essential.map(s => s.id));
      const optionalIds = new Set(occ.skills.optional.map(s => s.id));

      let essentialCovered = 0;
      let optionalCovered = 0;

      for (const skillId of selectedSkillIds) {
        if (essentialIds.has(skillId)) essentialCovered++;
        else if (optionalIds.has(skillId)) optionalCovered++;
      }

      const essentialTotal = occ.skills.essential.length;

      // Only include if at least 1 skill matches
      if (essentialCovered + optionalCovered > 0) {
        const matchScore = essentialTotal > 0
          ? Math.round((essentialCovered / essentialTotal) * 100)
          : 0;

        matches.push({
          id: occId,
          label: occ.label,
          isco: occ.isco,
          matchScore,
          essentialTotal,
          essentialCovered,
          optionalCovered,
          gapCount: essentialTotal - essentialCovered
        });
      }
    }

    // Sort
    if (sortBy === 'match') {
      matches.sort((a, b) => b.matchScore - a.matchScore || a.gapCount - b.gapCount);
    } else if (sortBy === 'gap') {
      matches.sort((a, b) => a.gapCount - b.gapCount || b.matchScore - a.matchScore);
    } else {
      matches.sort((a, b) => a.label.localeCompare(b.label));
    }

    return matches;
  }, [occupationsData, selectedSkills, sortBy]);

  const addSkill = (skill: SearchableSkill) => {
    setSelectedSkills(prev => [...prev, skill]);
    setSearchTerm('');
    setIsSearchOpen(false);
  };

  const removeSkill = (skillId: string) => {
    setSelectedSkills(prev => prev.filter(s => s.id !== skillId));
  };

  const clearAllSkills = () => {
    setSelectedSkills([]);
  };

  if (!occupationsData || !skillsData) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">Cargando datos...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <Target className="w-7 h-7 text-green-600" />
          Mis Skills
        </h2>
        <p className="text-gray-600 mt-1">
          Ingresa tus competencias y descubri que ocupaciones son mas compatibles con tu perfil
        </p>
      </div>

      {/* Skills Input */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Tus Competencias</h3>

        {/* Search input */}
        <div ref={searchRef} className="relative mb-4">
          <div className="flex items-center gap-2 p-3 border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-green-200 focus-within:border-green-500">
            <Search className="w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setIsSearchOpen(true);
              }}
              onFocus={() => setIsSearchOpen(true)}
              placeholder={`Buscar entre ${skillsData.stats.total.toLocaleString()} competencias ESCO...`}
              className="flex-1 outline-none text-sm"
            />
          </div>

          {/* Dropdown */}
          {isSearchOpen && searchTerm && (
            <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
              {filteredSkills.length === 0 ? (
                <div className="px-4 py-8 text-center text-gray-500">
                  No se encontraron competencias
                </div>
              ) : (
                filteredSkills.map(skill => (
                  <div
                    key={skill.id}
                    onClick={() => addSkill(skill)}
                    className="px-4 py-3 hover:bg-green-50 cursor-pointer border-b border-gray-100 last:border-0"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-sm text-gray-900">{skill.label}</div>
                        <div className="text-xs text-gray-500 flex gap-2">
                          <span className={skill.type === 'knowledge' ? 'text-amber-600' : 'text-indigo-600'}>
                            {skill.type === 'knowledge' ? 'Conocimiento' : 'Skill'}
                          </span>
                          <span>•</span>
                          <span>{skill.total} ocupaciones</span>
                        </div>
                      </div>
                      <span className="text-green-500 text-sm">+ Agregar</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Selected skills */}
        {selectedSkills.length > 0 ? (
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-600">
                {selectedSkills.length} competencia{selectedSkills.length !== 1 ? 's' : ''} seleccionada{selectedSkills.length !== 1 ? 's' : ''}
              </span>
              <button
                onClick={clearAllSkills}
                className="text-sm text-red-600 hover:text-red-800 flex items-center gap-1"
              >
                <Trash2 className="w-4 h-4" />
                Limpiar
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedSkills.map(skill => (
                <div
                  key={skill.id}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                    skill.type === 'knowledge'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-green-100 text-green-800'
                  }`}
                >
                  <span className="max-w-[200px] truncate">{skill.label}</span>
                  <button
                    onClick={() => removeSkill(skill.id)}
                    className="hover:bg-white/50 rounded-full p-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>Busca y agrega tus competencias para ver ocupaciones compatibles</p>
          </div>
        )}
      </div>

      {/* Results */}
      {selectedSkills.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">
              Ocupaciones Compatibles ({matchingOccupations.length})
            </h3>

            {/* Sort options */}
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">Ordenar por:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'match' | 'gap' | 'alpha')}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value="match">Mejor match</option>
                <option value="gap">Menor gap</option>
                <option value="alpha">Alfabetico</option>
              </select>
            </div>
          </div>

          {matchingOccupations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No se encontraron ocupaciones que requieran estas competencias</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {matchingOccupations.slice(0, 50).map((occ, index) => (
                <div
                  key={occ.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 font-mono text-sm w-6">
                          {index + 1}.
                        </span>
                        <span className="font-medium text-gray-900">{occ.label}</span>
                      </div>
                      <div className="ml-8 mt-1 flex items-center gap-4 text-sm text-gray-500">
                        <span className="font-mono">ISCO: {occ.isco}</span>
                        <span>
                          <Star className="w-3 h-3 inline text-green-500 fill-green-500" /> {occ.essentialCovered}/{occ.essentialTotal} esenciales
                        </span>
                        {occ.optionalCovered > 0 && (
                          <span>+{occ.optionalCovered} opcionales</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {/* Match score */}
                      <div className="text-right">
                        <div className={`text-lg font-bold ${
                          occ.matchScore >= 70 ? 'text-green-600' :
                          occ.matchScore >= 40 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {occ.matchScore}%
                        </div>
                        <div className="text-xs text-gray-500">match</div>
                      </div>

                      {/* Gap indicator */}
                      <div className="text-right">
                        <div className={`text-lg font-bold ${
                          occ.gapCount === 0 ? 'text-green-600' :
                          occ.gapCount <= 3 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {occ.gapCount}
                        </div>
                        <div className="text-xs text-gray-500">gap</div>
                      </div>

                      {/* Action */}
                      {onNavigateToOccupation && (
                        <button
                          onClick={() => onNavigateToOccupation(occ.id)}
                          className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Ver detalle"
                        >
                          <ChevronRight className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="ml-8 mt-3">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          occ.matchScore >= 70 ? 'bg-green-500' :
                          occ.matchScore >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${occ.matchScore}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}

              {matchingOccupations.length > 50 && (
                <div className="text-center py-4 text-gray-500 text-sm">
                  Mostrando 50 de {matchingOccupations.length} ocupaciones.
                  Agrega mas skills para refinar los resultados.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {selectedSkills.length === 0 && (
        <div className="bg-gray-50 rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <Target className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">
            Ingresa tus competencias
          </h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Busca y selecciona las skills y conocimientos que tenes.
            El sistema te mostrara las ocupaciones mas compatibles con tu perfil.
          </p>
        </div>
      )}
    </div>
  );
}
