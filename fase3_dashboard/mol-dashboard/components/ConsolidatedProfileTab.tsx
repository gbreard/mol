'use client';

import { useState, useMemo, useEffect } from 'react';
import { Layers, Search, ChevronDown, X, Loader2, CheckCircle, Plus, FileText, Star, TrendingUp, ChevronRight, ExternalLink, Users } from 'lucide-react';
import { MOLSkillsProfileIndex, OccupationFullDetailIndex, ConsolidatedProfilesIndex, ConsolidatedProfile, ConsolidatedSkill } from '@/lib/types';
import { getOfertasByEscoOccupation, OfertaConsolidado } from '@/lib/supabase';

interface OccupationInfo {
  id: string;
  label: string;
  isco: string;
}

interface ConsolidatedProfileTabProps {
  molProfileData: MOLSkillsProfileIndex | null;
  occupationsData: OccupationFullDetailIndex | null;
  occupationsList: OccupationInfo[];
}

export default function ConsolidatedProfileTab({
  molProfileData,
  occupationsData,
  occupationsList
}: ConsolidatedProfileTabProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Filter state for candidates
  const [minFrequency, setMinFrequency] = useState(30);

  // Consolidated profiles (loaded from API)
  const [consolidatedData, setConsolidatedData] = useState<ConsolidatedProfilesIndex | null>(null);
  const [isLoadingConsolidated, setIsLoadingConsolidated] = useState(false);

  // Ofertas state
  const [ofertas, setOfertas] = useState<OfertaConsolidado[]>([]);
  const [ofertasTotal, setOfertasTotal] = useState(0);
  const [ofertasPage, setOfertasPage] = useState(0);
  const [isLoadingOfertas, setIsLoadingOfertas] = useState(false);
  const [expandedOferta, setExpandedOferta] = useState<string | null>(null);

  // Saving state
  const [isSaving, setIsSaving] = useState(false);

  // Load consolidated profiles on mount
  useEffect(() => {
    setIsLoadingConsolidated(true);
    fetch('/api/consolidated-profiles')
      .then(res => res.json())
      .then(data => {
        setConsolidatedData(data);
        setIsLoadingConsolidated(false);
      })
      .catch(err => {
        console.error('Error loading consolidated profiles:', err);
        setIsLoadingConsolidated(false);
      });
  }, []);

  // Load ofertas when occupation changes
  useEffect(() => {
    if (!selectedId) {
      setOfertas([]);
      setOfertasTotal(0);
      return;
    }

    setIsLoadingOfertas(true);
    setOfertasPage(0);

    getOfertasByEscoOccupation(selectedId, 10, 0)
      .then(result => {
        setOfertas(result.ofertas);
        setOfertasTotal(result.total);
        setIsLoadingOfertas(false);
      })
      .catch(err => {
        console.error('Error loading ofertas:', err);
        setIsLoadingOfertas(false);
      });
  }, [selectedId]);

  // Load more ofertas
  const loadMoreOfertas = async () => {
    if (!selectedId || isLoadingOfertas) return;

    setIsLoadingOfertas(true);
    const newPage = ofertasPage + 1;

    try {
      const result = await getOfertasByEscoOccupation(selectedId, 10, newPage * 10);
      setOfertas(prev => [...prev, ...result.ofertas]);
      setOfertasPage(newPage);
    } catch (err) {
      console.error('Error loading more ofertas:', err);
    } finally {
      setIsLoadingOfertas(false);
    }
  };

  // Filter occupations with MOL data
  const occupationsWithMOL = useMemo(() => {
    if (!molProfileData) return [];
    return occupationsList
      .filter(o => molProfileData.occupations[o.id])
      .sort((a, b) => {
        const countA = molProfileData.occupations[a.id]?.offer_count || 0;
        const countB = molProfileData.occupations[b.id]?.offer_count || 0;
        return countB - countA;
      });
  }, [occupationsList, molProfileData]);

  // Get selected MOL profile
  const selectedMolProfile = useMemo(() => {
    if (!selectedId || !molProfileData) return null;
    return molProfileData.occupations[selectedId] || null;
  }, [selectedId, molProfileData]);

  // Get current consolidated profile for selected occupation
  const currentConsolidated = useMemo(() => {
    if (!selectedId || !consolidatedData) return null;
    return consolidatedData.profiles[selectedId] || null;
  }, [selectedId, consolidatedData]);

  // Build consolidated skills list
  const consolidatedSkills = useMemo(() => {
    if (!selectedMolProfile) return [];

    const skills: ConsolidatedSkill[] = [];
    const addedLabels = new Set<string>();

    // 1. Add previously approved skills
    if (currentConsolidated) {
      currentConsolidated.consolidated_skills.forEach(skill => {
        if (skill.source === 'mol_approved') {
          skills.push(skill);
          addedLabels.add(skill.label_normalized);
        }
      });
    }

    // 2. Add ESCO common skills (essential + optional)
    const commonLabels = new Set([
      ...selectedMolProfile.comparison.common_labels,
      ...(selectedMolProfile.comparison.common_optional_labels || [])
    ]);

    selectedMolProfile.mol_skills
      .filter(s => commonLabels.has(s.label_normalized) && !addedLabels.has(s.label_normalized))
      .forEach(s => {
        skills.push({
          label_normalized: s.label_normalized,
          label_original: s.label_original,
          source: 'esco_common',
          frequency: s.frequency,
          percentage: s.percentage,
          esco_uri: s.esco_uri,
          description: s.description,
          L1: s.L1,
          L2: s.L2
        });
        addedLabels.add(s.label_normalized);
      });

    return skills.sort((a, b) => (b.percentage || 0) - (a.percentage || 0));
  }, [selectedMolProfile, currentConsolidated]);

  // Build candidate skills list (emergent, filtered by frequency)
  const candidateSkills = useMemo(() => {
    if (!selectedMolProfile) return [];

    const approvedLabels = new Set(
      consolidatedSkills
        .filter(s => s.source === 'mol_approved')
        .map(s => s.label_normalized)
    );

    return selectedMolProfile.mol_skills
      .filter(s =>
        s.is_emerging &&
        s.percentage >= minFrequency &&
        !approvedLabels.has(s.label_normalized)
      )
      .sort((a, b) => b.percentage - a.percentage);
  }, [selectedMolProfile, minFrequency, consolidatedSkills]);

  // Filter dropdown
  const filteredOccupations = useMemo(() => {
    if (!searchTerm.trim()) return occupationsWithMOL;

    const normalizedSearch = searchTerm.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    return occupationsWithMOL.filter(occ => {
      const normalizedLabel = occ.label.toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
      return normalizedLabel.includes(normalizedSearch) ||
             occ.isco.toLowerCase().includes(normalizedSearch);
    });
  }, [occupationsWithMOL, searchTerm]);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setIsDropdownOpen(false);
    setSearchTerm('');
    setExpandedOferta(null);
  };

  const handleClear = () => {
    setSelectedId(null);
    setSearchTerm('');
    setOfertas([]);
    setOfertasTotal(0);
    setExpandedOferta(null);
  };

  // Approve a candidate skill
  const handleApprove = async (skill: typeof candidateSkills[0]) => {
    if (!selectedId || !selectedMolProfile) return;

    setIsSaving(true);

    const newSkill: ConsolidatedSkill = {
      label_normalized: skill.label_normalized,
      label_original: skill.label_original,
      source: 'mol_approved',
      frequency: skill.frequency,
      percentage: skill.percentage,
      esco_uri: skill.esco_uri,
      description: skill.description,
      L1: skill.L1,
      L2: skill.L2,
      approved_at: new Date().toISOString()
    };

    // Build new profile
    const existingProfile = currentConsolidated || {
      esco_uuid: selectedId,
      esco_label: selectedMolProfile.esco_label,
      last_updated: '',
      consolidated_skills: [],
      stats: {
        total_consolidated: 0,
        from_esco_common: 0,
        from_mol_approved: 0,
        pending_candidates: 0
      }
    };

    const updatedProfile: ConsolidatedProfile = {
      ...existingProfile,
      last_updated: new Date().toISOString(),
      consolidated_skills: [...existingProfile.consolidated_skills, newSkill],
      stats: {
        ...existingProfile.stats,
        from_mol_approved: existingProfile.stats.from_mol_approved + 1,
        total_consolidated: existingProfile.stats.total_consolidated + 1
      }
    };

    try {
      const response = await fetch('/api/consolidated-profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          esco_uuid: selectedId,
          profile: updatedProfile
        })
      });

      if (response.ok) {
        const data = await response.json();
        setConsolidatedData(data);
      }
    } catch (err) {
      console.error('Error saving profile:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Loading state
  if (!molProfileData || isLoadingConsolidated) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        <span className="ml-3 text-gray-600">Cargando datos...</span>
      </div>
    );
  }

  const selectedInfo = occupationsList.find(o => o.id === selectedId);
  const approvedCount = consolidatedSkills.filter(s => s.source === 'mol_approved').length;
  const escoCommonCount = consolidatedSkills.filter(s => s.source === 'esco_common').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <Layers className="w-7 h-7 text-purple-600" />
          Perfil Consolidado
        </h2>
        <p className="text-gray-600 mt-1">
          Construye el perfil de skills Argentina para cada ocupacion combinando ESCO + demanda real
        </p>
      </div>

      {/* Occupation Selector */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Ocupacion ESCO
        </label>

        {selectedInfo ? (
          <div className="flex items-center gap-3 p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="flex-1">
              <div className="font-semibold text-purple-900">{selectedInfo.label}</div>
              <div className="text-sm text-purple-700">
                ISCO: {selectedInfo.isco} | {selectedMolProfile?.offer_count || 0} ofertas |{' '}
                {consolidatedSkills.length} consolidadas | {candidateSkills.length} candidatas
              </div>
            </div>
            <button
              onClick={handleClear}
              className="p-2 hover:bg-purple-100 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-purple-600" />
            </button>
          </div>
        ) : (
          <div className="relative">
            <div
              className={`flex items-center gap-2 p-3 border rounded-lg cursor-pointer transition-colors ${
                isDropdownOpen ? 'border-purple-500 ring-2 ring-purple-200' : 'border-gray-300 hover:border-gray-400'
              }`}
              onClick={() => setIsDropdownOpen(true)}
            >
              <Search className="w-5 h-5 text-gray-400" />
              {isDropdownOpen ? (
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Escribi para filtrar..."
                  className="flex-1 outline-none bg-transparent"
                  autoFocus
                />
              ) : (
                <span className="flex-1 text-gray-500">
                  Buscar entre {occupationsWithMOL.length} ocupaciones con datos MOL...
                </span>
              )}
              <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </div>

            {isDropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setIsDropdownOpen(false)}
                />
                <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
                  <div className="px-3 py-2 bg-gray-50 border-b text-sm text-gray-600">
                    {searchTerm
                      ? `${filteredOccupations.length} resultados`
                      : `${occupationsWithMOL.length} ocupaciones con datos MOL`}
                  </div>
                  <ul className="overflow-y-auto max-h-64">
                    {filteredOccupations.length === 0 ? (
                      <li className="px-4 py-8 text-center text-gray-500">
                        No se encontraron ocupaciones
                      </li>
                    ) : (
                      filteredOccupations.slice(0, 100).map(occ => {
                        const profile = molProfileData.occupations[occ.id];
                        const hasConsolidated = consolidatedData?.profiles[occ.id];
                        return (
                          <li
                            key={occ.id}
                            onClick={() => handleSelect(occ.id)}
                            className="px-4 py-3 hover:bg-purple-50 cursor-pointer border-b border-gray-100 last:border-0"
                          >
                            <div className="flex items-center justify-between">
                              <div className="font-medium text-gray-900 flex items-center gap-2">
                                {occ.label}
                                {hasConsolidated && (
                                  <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">
                                    Consolidado
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                                <Users className="w-3 h-3" />
                                {profile?.offer_count || 0}
                              </div>
                            </div>
                            <div className="text-sm text-gray-500">
                              ISCO: {occ.isco}
                            </div>
                          </li>
                        );
                      })
                    )}
                  </ul>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Content when occupation selected */}
      {selectedMolProfile && (
        <>
          {/* Frequency Filter */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Filtro de frecuencia para candidatas
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Solo mostrar skills emergentes que aparecen en al menos este % de ofertas
                </p>
              </div>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="5"
                  max="50"
                  step="5"
                  value={minFrequency}
                  onChange={(e) => setMinFrequency(Number(e.target.value))}
                  className="w-32"
                />
                <span className="text-lg font-bold text-purple-600 w-12 text-right">{minFrequency}%</span>
              </div>
            </div>
          </div>

          {/* Two Column Layout: Consolidadas + Candidatas */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Panel 1: Skills Consolidadas */}
            <div className="bg-white rounded-xl shadow-sm border border-green-200 p-4">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Skills Consolidadas ({consolidatedSkills.length})
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Skills validadas: ESCO en comun + aprobadas manualmente
              </p>

              <div className="flex gap-2 mb-3 text-xs">
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                  ESCO: {escoCommonCount}
                </span>
                <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
                  Aprobadas: {approvedCount}
                </span>
              </div>

              <ul className="space-y-1 max-h-80 overflow-y-auto">
                {consolidatedSkills.length === 0 ? (
                  <li className="text-sm text-gray-500 py-4 text-center">
                    No hay skills consolidadas aun
                  </li>
                ) : (
                  consolidatedSkills.map((skill, idx) => (
                    <li
                      key={`${skill.label_normalized}-${idx}`}
                      className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-sm ${
                        skill.source === 'mol_approved' ? 'bg-purple-50' : 'bg-green-50'
                      }`}
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {skill.source === 'mol_approved' ? (
                          <Plus className="flex-shrink-0 w-3 h-3 text-purple-500" />
                        ) : (
                          <Star className="flex-shrink-0 w-3 h-3 text-blue-500 fill-blue-500" />
                        )}
                        <span className="truncate">{skill.label_original}</span>
                      </div>
                      <span className={`flex-shrink-0 font-medium ${
                        skill.source === 'mol_approved' ? 'text-purple-700' : 'text-green-700'
                      }`}>
                        {skill.percentage}%
                      </span>
                    </li>
                  ))
                )}
              </ul>
            </div>

            {/* Panel 2: Skills Candidatas */}
            <div className="bg-white rounded-xl shadow-sm border border-amber-200 p-4">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <TrendingUp className="w-5 h-5 text-amber-600" />
                Skills Candidatas ({candidateSkills.length})
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Skills emergentes MOL ({`>=${minFrequency}%`}) - click para aprobar
              </p>

              <ul className="space-y-1 max-h-80 overflow-y-auto">
                {candidateSkills.length === 0 ? (
                  <li className="text-sm text-gray-500 py-4 text-center">
                    No hay candidatas con {`>=${minFrequency}%`} de frecuencia
                  </li>
                ) : (
                  candidateSkills.map((skill, idx) => (
                    <li
                      key={`${skill.label_normalized}-${idx}`}
                      className="flex items-center justify-between gap-2 px-2 py-1.5 rounded text-sm bg-amber-50 hover:bg-amber-100"
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <TrendingUp className="flex-shrink-0 w-3 h-3 text-amber-500" />
                        <span className="truncate">{skill.label_original}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-amber-700 font-medium">
                          {skill.percentage}%
                        </span>
                        <button
                          onClick={() => handleApprove(skill)}
                          disabled={isSaving}
                          className="px-2 py-0.5 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 disabled:opacity-50"
                        >
                          {isSaving ? '...' : 'Aprobar'}
                        </button>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>

          {/* Panel 3: Ofertas */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-gray-600" />
              Ofertas de esta ocupacion ({ofertasTotal})
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              Verifica las skills in situ revisando las ofertas originales
            </p>

            {isLoadingOfertas && ofertas.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-500">Cargando ofertas...</span>
              </div>
            ) : ofertas.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No se encontraron ofertas para esta ocupacion
              </div>
            ) : (
              <>
                <ul className="space-y-2">
                  {ofertas.map(oferta => (
                    <li key={oferta.id_oferta} className="border border-gray-200 rounded-lg overflow-hidden">
                      <div
                        onClick={() => setExpandedOferta(
                          expandedOferta === oferta.id_oferta ? null : oferta.id_oferta
                        )}
                        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50"
                      >
                        <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${
                          expandedOferta === oferta.id_oferta ? 'rotate-90' : ''
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-900 truncate">
                            {oferta.titulo_limpio || oferta.titulo}
                          </div>
                          <div className="text-sm text-gray-500">
                            {oferta.empresa || 'Empresa no especificada'}
                          </div>
                        </div>
                      </div>

                      {expandedOferta === oferta.id_oferta && (
                        <div className="px-4 pb-3 bg-gray-50 border-t">
                          <div className="py-2">
                            <div className="text-xs font-medium text-gray-500 mb-1">Skills tecnicas:</div>
                            <div className="text-sm text-gray-700">
                              {oferta.skills_tecnicas || 'No especificadas'}
                            </div>
                          </div>
                          <div className="py-2">
                            <div className="text-xs font-medium text-gray-500 mb-1">Soft skills:</div>
                            <div className="text-sm text-gray-700">
                              {oferta.soft_skills || 'No especificadas'}
                            </div>
                          </div>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>

                {ofertas.length < ofertasTotal && (
                  <button
                    onClick={loadMoreOfertas}
                    disabled={isLoadingOfertas}
                    className="mt-4 w-full py-2 text-sm text-purple-600 hover:bg-purple-50 rounded-lg border border-purple-200 disabled:opacity-50"
                  >
                    {isLoadingOfertas ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Cargando...
                      </span>
                    ) : (
                      `Cargar mas (${ofertas.length} de ${ofertasTotal})`
                    )}
                  </button>
                )}
              </>
            )}
          </div>
        </>
      )}

      {/* Empty state */}
      {!selectedMolProfile && (
        <div className="bg-gray-50 rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <Layers className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">
            Selecciona una ocupacion
          </h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Usa el buscador para encontrar una ocupacion ESCO y construir su perfil
            consolidado de skills para Argentina.
          </p>
        </div>
      )}
    </div>
  );
}
