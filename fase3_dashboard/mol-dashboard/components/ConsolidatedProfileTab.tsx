'use client';

import { useState, useMemo, useEffect, useCallback } from 'react';
import { Layers, Search, ChevronDown, X, Loader2, CheckCircle, Plus, FileText, Star, TrendingUp, ChevronRight, Users, RefreshCw, Save, AlertCircle } from 'lucide-react';
import { getOfertasByEscoOccupation, OfertaConsolidado } from '@/lib/supabase';

interface OccupationInfo {
  id: string;
  label: string;
  isco: string;
  offer_count?: number;
}

interface SkillMOL {
  label_original: string;
  label_normalized: string;
  frequency: number;
  percentage: number;
  is_esco_essential: boolean;
  is_esco_optional: boolean;
  is_emerging: boolean;
  esco_uri?: string;
  description?: string;
  L1?: string;
  L2?: string;
}

interface PerfilArgentinaResponse {
  esco_uuid: string;
  esco_label: string;
  isco_code: string;
  offer_count: number;
  mol_skills: SkillMOL[];
  comparison: {
    coverage_essential: number;
    coverage_total: number;
    common_count: number;
    common_optional_count: number;
    emerging_count: number;
    missing_count: number;
    esco_essential_count: number;
    esco_optional_count: number;
    mol_unique_count: number;
    common_labels: string[];
    common_optional_labels: string[];
    emerging_labels: string[];
    missing_labels: string[];
  };
  generated_at: string;
}

interface SkillConsolidada {
  label: string;
  label_normalized: string;
  uri?: string;
  source: 'esco_common' | 'argentina_approved' | 'mol_approved';
  L1?: string;
  L2?: string;
  percentage_when_approved?: number;
  percentage?: number; // Legacy field from migration
  label_original?: string; // Legacy field from migration
  approved_at?: string;
  approved_by?: string;
}

interface EscoArgentinoEntry {
  esco_occupation_uri: string;
  esco_occupation_label: string;
  isco_code?: string;
  skills_consolidadas: SkillConsolidada[];
  total_skills: number;
  skills_from_esco: number;
  skills_from_argentina: number;
  cobertura_esco_essential?: number;
  cobertura_esco_total?: number;
  ofertas_count_snapshot?: number;
  version: number;
  updated_at: string;
  updated_by?: string;
  notas?: string;
}

interface SkillsIntelData {
  stats: { total_ofertas: number; total_ocupaciones: number };
  occupations: { esco_uri: string; esco_label: string; isco_code: string; ofertas_count: number }[];
  generated_at: string;
}

interface ConsolidatedProfileTabProps {
  occupationsData?: unknown;
  occupationsList?: OccupationInfo[];
  skillsIntelData: SkillsIntelData | null;
}

export default function ConsolidatedProfileTab({
  skillsIntelData
}: ConsolidatedProfileTabProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Derive occupations list from shared skillsIntelData (no duplicate fetch)
  const occupationsList = useMemo(() => {
    if (!skillsIntelData) return [];
    return skillsIntelData.occupations
      .map(o => ({
        id: o.esco_uri?.split('/').pop() || '',
        label: o.esco_label,
        isco: o.isco_code,
        offer_count: o.ofertas_count || 0
      }))
      .filter(o => !!o.id && (o.offer_count || 0) > 0)
      .sort((a, b) => (b.offer_count || 0) - (a.offer_count || 0));
  }, [skillsIntelData]);

  // Perfil dinámico de Argentina (desde API)
  const [perfilArgentina, setPerfilArgentina] = useState<PerfilArgentinaResponse | null>(null);
  const [isLoadingPerfil, setIsLoadingPerfil] = useState(false);
  const [perfilError, setPerfilError] = useState<string | null>(null);

  // ESCO Argentino consolidado (producto guardado)
  const [escoArgentino, setEscoArgentino] = useState<EscoArgentinoEntry | null>(null);
  const [isLoadingEscoArg, setIsLoadingEscoArg] = useState(false);

  // Filter state for candidates
  const [minFrequency, setMinFrequency] = useState(30);

  // Ofertas state
  const [ofertas, setOfertas] = useState<OfertaConsolidado[]>([]);
  const [ofertasTotal, setOfertasTotal] = useState(0);
  const [ofertasPage, setOfertasPage] = useState(0);
  const [isLoadingOfertas, setIsLoadingOfertas] = useState(false);
  const [expandedOferta, setExpandedOferta] = useState<string | null>(null);

  // Saving state
  const [isSaving, setIsSaving] = useState(false);

  // Función para cargar perfil Argentina dinámico
  const loadPerfilArgentina = useCallback(async (uuid: string) => {
    setIsLoadingPerfil(true);
    setPerfilError(null);

    try {
      const res = await fetch(`/api/perfil-argentina/${uuid}`);
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Error cargando perfil');
      }
      const data = await res.json();
      setPerfilArgentina(data);
    } catch (err) {
      console.error('Error loading perfil argentina:', err);
      setPerfilError(err instanceof Error ? err.message : 'Error desconocido');
      setPerfilArgentina(null);
    } finally {
      setIsLoadingPerfil(false);
    }
  }, []);

  // Función para cargar ESCO Argentino (producto guardado)
  const loadEscoArgentino = useCallback(async (uuid: string) => {
    setIsLoadingEscoArg(true);
    try {
      const uri = `http://data.europa.eu/esco/occupation/${uuid}`;
      const res = await fetch(`/api/esco-argentino?occupation=${encodeURIComponent(uri)}`);
      if (res.ok) {
        const data = await res.json();
        setEscoArgentino(data);
      } else if (res.status === 404) {
        // No existe aún, está bien
        setEscoArgentino(null);
      }
    } catch (err) {
      console.error('Error loading esco argentino:', err);
      setEscoArgentino(null);
    } finally {
      setIsLoadingEscoArg(false);
    }
  }, []);

  // Cargar datos cuando cambia la ocupación seleccionada
  useEffect(() => {
    if (!selectedId) {
      setPerfilArgentina(null);
      setEscoArgentino(null);
      setOfertas([]);
      setOfertasTotal(0);
      return;
    }

    // Cargar ambos en paralelo
    loadPerfilArgentina(selectedId);
    loadEscoArgentino(selectedId);

    // Cargar ofertas
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
  }, [selectedId, loadPerfilArgentina, loadEscoArgentino]);

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

  // Build consolidated skills list (from ESCO Argentino + common ESCO)
  const consolidatedSkills = useMemo(() => {
    if (!perfilArgentina) return [];

    const skills: SkillConsolidada[] = [];
    const addedLabels = new Set<string>();

    // 1. Add previously approved skills from ESCO Argentino (normalize legacy fields)
    if (escoArgentino?.skills_consolidadas) {
      escoArgentino.skills_consolidadas.forEach(skill => {
        // Normalize legacy data from migration
        const normalizedSkill: SkillConsolidada = {
          ...skill,
          label: skill.label || skill.label_original || skill.label_normalized || '',
          label_normalized: skill.label_normalized || skill.label_original?.toLowerCase() || '',
          percentage_when_approved: skill.percentage_when_approved || skill.percentage || 0,
          source: skill.source === 'mol_approved' ? 'argentina_approved' : skill.source
        };
        if (normalizedSkill.label && normalizedSkill.label_normalized) {
          skills.push(normalizedSkill);
          addedLabels.add(normalizedSkill.label_normalized);
        }
      });
    }

    // 2. Add ESCO common skills (essential + optional) that aren't already added
    const commonLabels = new Set([
      ...perfilArgentina.comparison.common_labels,
      ...perfilArgentina.comparison.common_optional_labels
    ]);

    perfilArgentina.mol_skills
      .filter(s => commonLabels.has(s.label_normalized) && !addedLabels.has(s.label_normalized))
      .forEach(s => {
        skills.push({
          label: s.label_original,
          label_normalized: s.label_normalized,
          source: 'esco_common',
          uri: s.esco_uri,
          L1: s.L1,
          L2: s.L2,
          percentage_when_approved: s.percentage
        });
        addedLabels.add(s.label_normalized);
      });

    return skills.sort((a, b) => (b.percentage_when_approved || 0) - (a.percentage_when_approved || 0));
  }, [perfilArgentina, escoArgentino]);

  // Build candidate skills list (emergent, filtered by frequency)
  const candidateSkills = useMemo(() => {
    if (!perfilArgentina) return [];

    const approvedLabels = new Set(
      consolidatedSkills.map(s => s.label_normalized)
    );

    return perfilArgentina.mol_skills
      .filter(s =>
        s.is_emerging &&
        s.percentage >= minFrequency &&
        !approvedLabels.has(s.label_normalized)
      )
      .sort((a, b) => b.percentage - a.percentage);
  }, [perfilArgentina, minFrequency, consolidatedSkills]);

  // Filter dropdown
  const filteredOccupations = useMemo(() => {
    if (!searchTerm.trim()) return occupationsList;

    const normalizedSearch = searchTerm.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    return occupationsList.filter(occ => {
      const normalizedLabel = occ.label.toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
      return normalizedLabel.includes(normalizedSearch) ||
             occ.isco.toLowerCase().includes(normalizedSearch);
    });
  }, [occupationsList, searchTerm]);

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

  // Refresh current occupation data
  const handleRefresh = () => {
    if (selectedId) {
      loadPerfilArgentina(selectedId);
      loadEscoArgentino(selectedId);
    }
  };

  // Approve a candidate skill (add to ESCO Argentino)
  const handleApprove = async (skill: SkillMOL) => {
    if (!selectedId || !perfilArgentina) return;

    setIsSaving(true);

    try {
      const uri = `http://data.europa.eu/esco/occupation/${selectedId}`;
      const res = await fetch('/api/esco-argentino', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          esco_occupation_uri: uri,
          esco_occupation_label: perfilArgentina.esco_label,
          isco_code: perfilArgentina.isco_code,
          action: 'add_skill',
          skill: {
            label: skill.label_original,
            label_normalized: skill.label_normalized,
            source: 'argentina_approved',
            uri: skill.esco_uri,
            L1: skill.L1,
            L2: skill.L2,
            percentage_when_approved: skill.percentage
          },
          updated_by: 'dashboard_user'
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Error guardando');
      }

      const result = await res.json();
      setEscoArgentino(result.data);
    } catch (err) {
      console.error('Error approving skill:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Remove an approved skill from ESCO Argentino
  const handleRemove = async (skillToRemove: SkillConsolidada) => {
    if (!selectedId || !escoArgentino) return;

    setIsSaving(true);

    try {
      const uri = `http://data.europa.eu/esco/occupation/${selectedId}`;
      const res = await fetch('/api/esco-argentino', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          esco_occupation_uri: uri,
          action: 'remove_skill',
          skill_label_normalized: skillToRemove.label_normalized,
          updated_by: 'dashboard_user'
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Error removiendo');
      }

      const result = await res.json();
      setEscoArgentino(result.data);
    } catch (err) {
      console.error('Error removing skill:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Save full profile snapshot
  const handleSaveSnapshot = async () => {
    if (!selectedId || !perfilArgentina) return;

    setIsSaving(true);

    try {
      const uri = `http://data.europa.eu/esco/occupation/${selectedId}`;
      const res = await fetch('/api/esco-argentino', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          esco_occupation_uri: uri,
          esco_occupation_label: perfilArgentina.esco_label,
          isco_code: perfilArgentina.isco_code,
          skills_consolidadas: consolidatedSkills,
          cobertura_esco_essential: perfilArgentina.comparison.coverage_essential,
          cobertura_esco_total: perfilArgentina.comparison.coverage_total,
          ofertas_count_snapshot: perfilArgentina.offer_count,
          updated_by: 'dashboard_user'
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Error guardando');
      }

      const result = await res.json();
      setEscoArgentino(result.data);
    } catch (err) {
      console.error('Error saving snapshot:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Loading state while parent fetches skills-intelligence data
  if (!skillsIntelData) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        <span className="ml-3 text-gray-600">Cargando ocupaciones...</span>
      </div>
    );
  }

  const selectedInfo = occupationsList.find(o => o.id === selectedId);
  const approvedCount = consolidatedSkills.filter(s => s.source === 'argentina_approved' || s.source === 'mol_approved').length;
  const escoCommonCount = consolidatedSkills.filter(s => s.source === 'esco_common').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Layers className="w-7 h-7 text-purple-600" />
            ESCO Argentino - Perfil Consolidado
          </h2>
          <p className="text-gray-600 mt-1">
            Construye el perfil de skills para Argentina combinando ESCO + demanda real del mercado
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {occupationsList.length} ocupaciones disponibles | Datos calculados en tiempo real desde Supabase
          </p>
        </div>
        {selectedId && (
          <button
            onClick={handleRefresh}
            disabled={isLoadingPerfil || isLoadingEscoArg}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-purple-600 hover:bg-purple-50 rounded-lg border border-purple-200 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingPerfil ? 'animate-spin' : ''}`} />
            Refrescar
          </button>
        )}
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
                ISCO: {selectedInfo.isco} |{' '}
                {perfilArgentina ? `${perfilArgentina.offer_count} ofertas` : 'Cargando...'} |{' '}
                {consolidatedSkills.length} consolidadas | {candidateSkills.length} candidatas
              </div>
              {escoArgentino && (
                <div className="text-xs text-purple-600 mt-1">
                  ESCO Argentino v{escoArgentino.version} - Actualizado: {new Date(escoArgentino.updated_at).toLocaleDateString()}
                </div>
              )}
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
                  Buscar entre {occupationsList.length} ocupaciones con datos MOL...
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
                      : `${occupationsList.length} ocupaciones con datos MOL`}
                  </div>
                  <ul className="overflow-y-auto max-h-64">
                    {filteredOccupations.length === 0 ? (
                      <li className="px-4 py-8 text-center text-gray-500">
                        No se encontraron ocupaciones
                      </li>
                    ) : (
                      filteredOccupations.slice(0, 100).map(occ => (
                        <li
                          key={occ.id}
                          onClick={() => handleSelect(occ.id)}
                          className="px-4 py-3 hover:bg-purple-50 cursor-pointer border-b border-gray-100 last:border-0"
                        >
                          <div className="flex items-center justify-between">
                            <div className="font-medium text-gray-900">
                              {occ.label}
                            </div>
                            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                              <Users className="w-3 h-3" />
                              {occ.offer_count || 0}
                            </div>
                          </div>
                          <div className="text-sm text-gray-500">
                            ISCO: {occ.isco}
                          </div>
                        </li>
                      ))
                    )}
                  </ul>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Loading/Error states */}
      {selectedId && isLoadingPerfil && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500 mx-auto mb-3" />
          <p className="text-gray-600">Calculando perfil en tiempo real desde Supabase...</p>
        </div>
      )}

      {selectedId && perfilError && (
        <div className="bg-red-50 rounded-xl border border-red-200 p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Error cargando perfil</p>
            <p className="text-sm text-red-600">{perfilError}</p>
          </div>
        </div>
      )}

      {/* Content when occupation selected */}
      {perfilArgentina && (
        <>
          {/* Frequency Filter + Save Button */}
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
              <div className="flex items-center gap-6">
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
                <button
                  onClick={handleSaveSnapshot}
                  disabled={isSaving || consolidatedSkills.length === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Guardando...' : 'Guardar ESCO Argentino'}
                </button>
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
                Skills validadas: ESCO en comun + aprobadas para Argentina
              </p>

              <div className="flex gap-2 mb-3 text-xs">
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                  ESCO: {escoCommonCount}
                </span>
                <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
                  Argentina: {approvedCount}
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
                        skill.source === 'argentina_approved' || skill.source === 'mol_approved' ? 'bg-purple-50' : 'bg-green-50'
                      }`}
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {skill.source === 'argentina_approved' || skill.source === 'mol_approved' ? (
                          <Plus className="flex-shrink-0 w-3 h-3 text-purple-500" />
                        ) : (
                          <Star className="flex-shrink-0 w-3 h-3 text-blue-500 fill-blue-500" />
                        )}
                        <span className="truncate">{skill.label || skill.label_original || skill.label_normalized}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`flex-shrink-0 font-medium ${
                          skill.source === 'argentina_approved' || skill.source === 'mol_approved' ? 'text-purple-700' : 'text-green-700'
                        }`}>
                          {skill.percentage_when_approved || skill.percentage || 0}%
                        </span>
                        {(skill.source === 'argentina_approved' || skill.source === 'mol_approved') && (
                          <button
                            onClick={() => handleRemove(skill)}
                            disabled={isSaving}
                            className="p-0.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                            title="Quitar skill"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
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
      {!selectedId && (
        <div className="bg-gray-50 rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <Layers className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">
            Selecciona una ocupacion
          </h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Usa el buscador para encontrar una ocupacion ESCO y construir su perfil
            consolidado de skills para Argentina. Los datos se calculan en tiempo real.
          </p>
        </div>
      )}
    </div>
  );
}
