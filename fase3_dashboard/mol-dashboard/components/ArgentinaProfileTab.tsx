'use client';

import { useState, useMemo } from 'react';
import { Globe, Search, ChevronDown, X, Loader2, Star, Circle, TrendingUp, AlertCircle, Briefcase, Users, AlertTriangle, CheckCircle } from 'lucide-react';
import { MOLSkillsProfileIndex, OccupationFullDetailIndex, OccupationMOLProfile, SkillItem, MOLSkillItem } from '@/lib/types';

interface OccupationInfo {
  id: string;
  label: string;
  isco: string;
}

interface ArgentinaProfileTabProps {
  molProfileData: MOLSkillsProfileIndex | null;
  occupationsData: OccupationFullDetailIndex | null;
  occupationsList: OccupationInfo[];
}

export default function ArgentinaProfileTab({
  molProfileData,
  occupationsData,
  occupationsList
}: ArgentinaProfileTabProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Filter to only occupations with MOL data, sorted by offer count (descending)
  const occupationsWithMOL = useMemo(() => {
    if (!molProfileData) {
      console.log('[ARG TAB DEBUG] molProfileData is null');
      return [];
    }

    if (occupationsList.length === 0) {
      console.log('[ARG TAB DEBUG] occupationsList is empty');
      return [];
    }

    // DEBUG: Check data
    const molOccupationKeys = Object.keys(molProfileData.occupations);
    const occupationsListIds = occupationsList.map(o => o.id);
    const matchingIds = occupationsListIds.filter(id => molProfileData.occupations[id]);

    // DEBUG: Specific UUID comparison
    const molFirst = molOccupationKeys[0];
    const occFirst = occupationsListIds[0];
    const crossCheck = {
      molFirstKey: molFirst,
      molFirstInOccList: occupationsListIds.includes(molFirst),
      occFirstKey: occFirst,
      occFirstInMolData: !!molProfileData.occupations[occFirst],
      molKeyCharCodes: molFirst?.split('').slice(0, 10).map(c => c.charCodeAt(0)),
      occKeyCharCodes: occFirst?.split('').slice(0, 10).map(c => c.charCodeAt(0))
    };

    console.log('[ARG TAB DEBUG] Data check:', {
      molOccupationKeys_count: molOccupationKeys.length,
      molOccupationKeys_first5: molOccupationKeys.slice(0, 5),
      occupationsList_count: occupationsList.length,
      occupationsList_first5: occupationsListIds.slice(0, 5),
      matchingIds_count: matchingIds.length,
      matchingIds_first5: matchingIds.slice(0, 5),
      crossCheck,
      first5OfferCounts: matchingIds.slice(0, 5).map(id => ({
        id,
        offer_count: molProfileData.occupations[id]?.offer_count,
        type: typeof molProfileData.occupations[id]?.offer_count
      }))
    });

    const result = occupationsList
      .filter(o => molProfileData.occupations[o.id])
      .sort((a, b) => {
        const countA = molProfileData.occupations[a.id]?.offer_count || 0;
        const countB = molProfileData.occupations[b.id]?.offer_count || 0;
        return countB - countA; // Mayor cantidad primero
      });

    console.log('[ARG TAB DEBUG] Final result:', {
      count: result.length,
      first5: result.slice(0, 5).map(o => ({
        id: o.id,
        label: o.label,
        offer_count: molProfileData.occupations[o.id]?.offer_count
      }))
    });

    return result;
  }, [occupationsList, molProfileData]);

  // Get selected occupation profile
  const selectedProfile = useMemo(() => {
    if (!selectedId || !molProfileData) return null;
    return molProfileData.occupations[selectedId] || null;
  }, [selectedId, molProfileData]);

  // Get ESCO data for selected occupation
  const selectedEsco = useMemo(() => {
    if (!selectedId || !occupationsData) return null;
    return occupationsData[selectedId] || null;
  }, [selectedId, occupationsData]);

  // Filter occupations for dropdown
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
  };

  const handleClear = () => {
    setSelectedId(null);
    setSearchTerm('');
  };

  // Loading state - wait for both molProfileData AND occupationsList
  if (!molProfileData || occupationsList.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-teal-500" />
        <span className="ml-3 text-gray-600">
          {!molProfileData
            ? 'Cargando datos de perfil argentino...'
            : 'Cargando lista de ocupaciones...'}
        </span>
      </div>
    );
  }

  const stats = molProfileData.stats;
  const selectedInfo = occupationsList.find(o => o.id === selectedId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <Globe className="w-7 h-7 text-teal-600" />
          Perfil Argentina
        </h2>
        <p className="text-gray-600 mt-1">
          Compara las skills que pide el mercado argentino vs lo que define ESCO para cada ocupacion
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="text-3xl font-bold text-gray-900">
            {stats.total_offers.toLocaleString()}
          </div>
          <div className="text-sm text-gray-500 mt-1">Ofertas analizadas</div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="text-3xl font-bold text-teal-600">
            {stats.total_occupations_with_mol}
          </div>
          <div className="text-sm text-gray-500 mt-1">Ocupaciones con datos MOL</div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="text-3xl font-bold text-purple-600">
            {stats.avg_skills_per_offer}
          </div>
          <div className="text-sm text-gray-500 mt-1">Skills promedio por oferta</div>
        </div>
      </div>

      {/* Occupation Selector */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Ocupacion ESCO (solo ocupaciones con ofertas MOL)
        </label>

        {selectedInfo ? (
          <div className="flex items-center gap-3 p-4 bg-teal-50 border border-teal-200 rounded-lg">
            <div className="flex-1">
              <div className="font-semibold text-teal-900">{selectedInfo.label}</div>
              <div className="text-sm text-teal-700">
                ISCO: {selectedInfo.isco} | {selectedProfile?.offer_count || 0} ofertas MOL
              </div>
            </div>
            <button
              onClick={handleClear}
              className="p-2 hover:bg-teal-100 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-teal-600" />
            </button>
          </div>
        ) : (
          <div className="relative">
            <div
              className={`flex items-center gap-2 p-3 border rounded-lg cursor-pointer transition-colors ${
                isDropdownOpen ? 'border-teal-500 ring-2 ring-teal-200' : 'border-gray-300 hover:border-gray-400'
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
                        const offerCount = profile?.offer_count || 0;
                        const isSmallSample = offerCount < 10;
                        return (
                          <li
                            key={occ.id}
                            onClick={() => handleSelect(occ.id)}
                            className="px-4 py-3 hover:bg-teal-50 cursor-pointer border-b border-gray-100 last:border-0"
                          >
                            <div className="flex items-center justify-between">
                              <div className="font-medium text-gray-900">{occ.label}</div>
                              <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                                isSmallSample ? 'bg-amber-100 text-amber-700' : 'bg-teal-100 text-teal-700'
                              }`}>
                                <Users className="w-3 h-3" />
                                {offerCount}
                              </div>
                            </div>
                            <div className="text-sm text-gray-500 flex items-center gap-2">
                              <span>ISCO: {occ.isco}</span>
                              <span>|</span>
                              <span>{profile?.comparison.coverage_essential || 0}% cobertura</span>
                              {isSmallSample && (
                                <span className="text-amber-600 text-xs">(muestra chica)</span>
                              )}
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
      {selectedProfile && !selectedEsco && (
        <div className="flex items-center justify-center h-32 bg-gray-50 rounded-xl border border-gray-200">
          <Loader2 className="w-6 h-6 animate-spin text-teal-500 mr-3" />
          <span className="text-gray-600">Cargando detalles ESCO de la ocupación...</span>
        </div>
      )}
      {selectedProfile && selectedEsco && (
        <>
          {/* Metrics Cards */}
          <MetricsCards profile={selectedProfile} />

          {/* Three Column Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* ESCO Skills Column */}
            <EscoSkillsColumn
              escoData={selectedEsco}
              commonLabels={new Set(selectedProfile.comparison.common_labels)}
              missingLabels={new Set(selectedProfile.comparison.missing_labels)}
            />

            {/* Common Skills Column */}
            <CommonSkillsColumn
              molSkills={selectedProfile.mol_skills}
              commonEssentialLabels={new Set(selectedProfile.comparison.common_labels)}
              commonOptionalLabels={new Set(selectedProfile.comparison.common_optional_labels || [])}
            />

            {/* MOL Skills Column */}
            <MOLSkillsColumn
              molSkills={selectedProfile.mol_skills}
              emergingLabels={new Set(selectedProfile.comparison.emerging_labels)}
            />
          </div>

          {/* Legend */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex flex-wrap gap-6 text-sm">
              <div className="flex items-center gap-2">
                <Star className="w-4 h-4 text-blue-500 fill-blue-500" />
                <span>Esencial ESCO</span>
              </div>
              <div className="flex items-center gap-2">
                <Circle className="w-4 h-4 text-gray-400" />
                <span>Opcional ESCO</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 h-4 bg-green-500 rounded-full"></span>
                <span>Detectada en MOL</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-500" />
                <span>Faltante (ESCO no en MOL)</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-teal-500" />
                <span>Emergente (MOL no en ESCO)</span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Empty state */}
      {!selectedProfile && (
        <div className="bg-gray-50 rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <Globe className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">
            Selecciona una ocupacion
          </h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Usa el buscador de arriba para encontrar una ocupacion ESCO y comparar
            las skills que pide el mercado argentino vs las definidas por ESCO.
          </p>
        </div>
      )}
    </div>
  );
}

// ============= Helper Components =============

function MetricsCards({ profile }: { profile: OccupationMOLProfile }) {
  const { comparison, offer_count } = profile;

  const getColorClass = (value: number): string => {
    if (value >= 70) return 'text-green-600';
    if (value >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getBgClass = (value: number): string => {
    if (value >= 70) return 'bg-green-500';
    if (value >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getSampleQuality = (count: number): { label: string; color: string; bgColor: string } => {
    if (count >= 30) return { label: 'Muestra representativa', color: 'text-green-600', bgColor: 'bg-green-100' };
    if (count >= 10) return { label: 'Muestra moderada', color: 'text-yellow-600', bgColor: 'bg-yellow-100' };
    return { label: 'Muestra chica - interpretar con cuidado', color: 'text-amber-600', bgColor: 'bg-amber-100' };
  };

  const sampleQuality = getSampleQuality(offer_count);

  return (
    <div className="space-y-4">
      {/* Sample Size Alert */}
      <div className={`flex items-center gap-3 p-4 rounded-xl ${sampleQuality.bgColor}`}>
        <Users className={`w-6 h-6 ${sampleQuality.color}`} />
        <div>
          <div className={`font-bold text-2xl ${sampleQuality.color}`}>{offer_count} ofertas</div>
          <div className={`text-sm ${sampleQuality.color}`}>{sampleQuality.label}</div>
        </div>
        {offer_count < 10 && (
          <AlertTriangle className="w-5 h-5 text-amber-500 ml-auto" />
        )}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Cobertura Esencial */}
      <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <div className={`text-3xl font-bold ${getColorClass(comparison.coverage_essential)}`}>
          {comparison.coverage_essential}%
        </div>
        <div className="text-sm text-gray-600 mt-1">Cobertura Esencial</div>
        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getBgClass(comparison.coverage_essential)} rounded-full`}
            style={{ width: `${Math.min(comparison.coverage_essential, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {comparison.common_count} de {comparison.esco_essential_count} esenciales
        </div>
      </div>

      {/* Emergentes */}
      <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <div className="text-3xl font-bold text-teal-600">
          {comparison.emerging_count}
        </div>
        <div className="text-sm text-gray-600 mt-1">Skills Emergentes</div>
        <div className="flex items-center gap-1 mt-2 text-teal-600">
          <TrendingUp className="w-4 h-4" />
          <span className="text-xs">Solo en MOL</span>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Skills que pide Argentina pero no estan en ESCO
        </div>
      </div>

      {/* Faltantes */}
      <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <div className="text-3xl font-bold text-amber-600">
          {comparison.missing_count}
        </div>
        <div className="text-sm text-gray-600 mt-1">Skills Faltantes</div>
        <div className="flex items-center gap-1 mt-2 text-amber-600">
          <AlertCircle className="w-4 h-4" />
          <span className="text-xs">ESCO no en MOL</span>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Skills esenciales ESCO no detectadas en ofertas
        </div>
      </div>

      {/* Cobertura Total */}
      <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <div className={`text-3xl font-bold ${getColorClass(comparison.coverage_total)}`}>
          {comparison.coverage_total}%
        </div>
        <div className="text-sm text-gray-600 mt-1">Cobertura Total</div>
        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getBgClass(comparison.coverage_total)} rounded-full`}
            style={{ width: `${Math.min(comparison.coverage_total, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Incluye esenciales + opcionales
        </div>
      </div>
      </div>
    </div>
  );
}

function EscoSkillsColumn({
  escoData,
  commonLabels,
  missingLabels
}: {
  escoData: { skills: { essential: SkillItem[]; optional: SkillItem[] }; knowledge: { essential: SkillItem[]; optional: SkillItem[] } };
  commonLabels: Set<string>;
  missingLabels: Set<string>;
}) {
  const [showOptional, setShowOptional] = useState(false);

  // Combine skills and knowledge
  const essential = [
    ...escoData.skills.essential,
    ...escoData.knowledge.essential
  ];
  const optional = [
    ...escoData.skills.optional,
    ...escoData.knowledge.optional
  ];

  const normalize = (s: string) => s.trim().toLowerCase();

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-fit">
      <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
        <Briefcase className="w-5 h-5 text-blue-600" />
        Skills ESCO
      </h3>

      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setShowOptional(false)}
          className={`px-3 py-1 text-sm rounded-lg transition-colors ${
            !showOptional ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          Esenciales ({essential.length})
        </button>
        <button
          onClick={() => setShowOptional(true)}
          className={`px-3 py-1 text-sm rounded-lg transition-colors ${
            showOptional ? 'bg-gray-200 text-gray-700' : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          Opcionales ({optional.length})
        </button>
      </div>

      <ul className="space-y-1 max-h-96 overflow-y-auto">
        {(showOptional ? optional : essential).map((skill, idx) => {
          const labelNorm = normalize(skill.label);
          const isDetected = commonLabels.has(labelNorm);
          const isMissing = missingLabels.has(labelNorm);

          return (
            <li
              key={`${skill.id}-${idx}`}
              className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm ${
                isDetected ? 'bg-green-50' : isMissing ? 'bg-amber-50' : 'bg-gray-50'
              }`}
            >
              {showOptional ? (
                <Circle className="flex-shrink-0 w-3 h-3 text-gray-400" />
              ) : (
                <Star className="flex-shrink-0 w-3 h-3 text-blue-500 fill-blue-500" />
              )}
              <span className="flex-1 truncate">{skill.label}</span>
              {isDetected && (
                <span className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full" />
              )}
              {isMissing && !showOptional && (
                <AlertCircle className="flex-shrink-0 w-3 h-3 text-amber-500" />
              )}
            </li>
          );
        })}
      </ul>

      <div className="mt-3 pt-3 border-t text-xs text-gray-500">
        {essential.length} esenciales | {optional.length} opcionales
      </div>
    </div>
  );
}

function CommonSkillsColumn({
  molSkills,
  commonEssentialLabels,
  commonOptionalLabels
}: {
  molSkills: { label_original: string; label_normalized: string; frequency: number; percentage: number }[];
  commonEssentialLabels: Set<string>;
  commonOptionalLabels: Set<string>;
}) {
  const [showOptional, setShowOptional] = useState(false);

  const allCommonLabels = new Set([...commonEssentialLabels, ...commonOptionalLabels]);
  const commonSkills = molSkills
    .filter(s => allCommonLabels.has(s.label_normalized))
    .map(s => ({
      ...s,
      isEssential: commonEssentialLabels.has(s.label_normalized),
      isOptional: commonOptionalLabels.has(s.label_normalized)
    }));

  const essentialSkills = commonSkills.filter(s => s.isEssential);
  const optionalSkills = commonSkills.filter(s => s.isOptional && !s.isEssential);
  const displaySkills = showOptional ? optionalSkills : essentialSkills;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-green-200 p-4 h-fit">
      <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
        <span className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">
          =
        </span>
        En Comun (ESCO y MOL)
      </h3>

      <p className="text-sm text-gray-600 mb-3">
        Skills que ESCO define Y el mercado argentino pide
      </p>

      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setShowOptional(false)}
          className={`px-3 py-1 text-sm rounded-lg transition-colors ${
            !showOptional ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          Esenciales ({essentialSkills.length})
        </button>
        <button
          onClick={() => setShowOptional(true)}
          className={`px-3 py-1 text-sm rounded-lg transition-colors ${
            showOptional ? 'bg-gray-200 text-gray-700' : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          Opcionales ({optionalSkills.length})
        </button>
      </div>

      <ul className="space-y-1 max-h-96 overflow-y-auto">
        {displaySkills.length === 0 ? (
          <li className="text-sm text-gray-500 py-4 text-center">
            No hay skills {showOptional ? 'opcionales' : 'esenciales'} en comun
          </li>
        ) : (
          displaySkills.map((skill, idx) => (
            <li
              key={`${skill.label_normalized}-${idx}`}
              className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-sm ${
                skill.isEssential ? 'bg-green-50' : 'bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                {skill.isEssential ? (
                  <Star className="flex-shrink-0 w-3 h-3 text-blue-500 fill-blue-500" />
                ) : (
                  <Circle className="flex-shrink-0 w-3 h-3 text-gray-400" />
                )}
                <span className="truncate">{skill.label_original}</span>
              </div>
              <span className="flex-shrink-0 text-green-700 font-medium">
                {skill.percentage}%
              </span>
            </li>
          ))
        )}
      </ul>

      <div className="mt-3 pt-3 border-t text-xs text-gray-500">
        {commonSkills.length} skills compartidas
      </div>
    </div>
  );
}

function MOLSkillsColumn({
  molSkills,
  emergingLabels
}: {
  molSkills: MOLSkillItem[];
  emergingLabels: Set<string>;
}) {
  const [showOnlyEmerging, setShowOnlyEmerging] = useState(false);
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);

  const displaySkills = showOnlyEmerging
    ? molSkills.filter(s => s.is_emerging)
    : molSkills.slice(0, 50);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-teal-200 p-4 h-fit">
      <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
        <TrendingUp className="w-5 h-5 text-teal-600" />
        Skills MOL (Argentina)
      </h3>

      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setShowOnlyEmerging(false)}
          className={`px-3 py-1 text-sm rounded-lg transition-colors ${
            !showOnlyEmerging ? 'bg-teal-100 text-teal-700' : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          Top 50
        </button>
        <button
          onClick={() => setShowOnlyEmerging(true)}
          className={`px-3 py-1 text-sm rounded-lg transition-colors ${
            showOnlyEmerging ? 'bg-teal-100 text-teal-700' : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          Solo Emergentes ({emergingLabels.size})
        </button>
      </div>

      <ul className="space-y-1 max-h-96 overflow-y-auto">
        {displaySkills.map((skill, idx) => (
          <li key={`${skill.label_normalized}-${idx}`}>
            <div
              onClick={() => setExpandedSkill(
                expandedSkill === skill.label_normalized ? null : skill.label_normalized
              )}
              className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded text-sm cursor-pointer ${
                skill.is_emerging ? 'bg-teal-50 hover:bg-teal-100' : 'bg-gray-50 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                {skill.is_emerging && (
                  <TrendingUp className="flex-shrink-0 w-3 h-3 text-teal-500" />
                )}
                {skill.esco_uri && !skill.is_emerging && (
                  <CheckCircle className="flex-shrink-0 w-3 h-3 text-blue-400" />
                )}
                <span className="truncate">{skill.label_original}</span>
              </div>
              <div className="flex-shrink-0 text-right">
                <span className="text-gray-700 font-medium">{skill.frequency}</span>
                <span className="text-gray-400 text-xs ml-1">({skill.percentage}%)</span>
              </div>
            </div>
            {/* Descripcion expandible */}
            {expandedSkill === skill.label_normalized && skill.description && (
              <div className="mt-1 mx-2 p-2 bg-gray-100 rounded text-xs text-gray-600 border-l-2 border-teal-400">
                {skill.L1 && (
                  <span className="inline-block px-1.5 py-0.5 bg-teal-100 text-teal-700 rounded text-xs mr-2 mb-1">
                    {skill.L1}
                  </span>
                )}
                {skill.description}
              </div>
            )}
            {expandedSkill === skill.label_normalized && !skill.description && (
              <div className="mt-1 mx-2 p-2 bg-amber-50 rounded text-xs text-amber-600 border-l-2 border-amber-400">
                Sin descripcion ESCO disponible
              </div>
            )}
          </li>
        ))}
      </ul>

      <div className="mt-3 pt-3 border-t text-xs text-gray-500">
        {molSkills.length} skills unicas | {emergingLabels.size} emergentes
        <div className="text-xs text-gray-400 mt-1">
          Click en una skill para ver descripcion ESCO
        </div>
      </div>
    </div>
  );
}
