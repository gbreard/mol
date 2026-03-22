'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import {
  Search, X, Target, Loader2, ChevronRight, Star, AlertCircle,
  Trash2, User, Briefcase, Plus, Save, FolderOpen, Check, ChevronDown
} from 'lucide-react';
import { OccupationFullDetailIndex, SkillsSearchableIndex, SearchableSkill } from '@/lib/types';
import { usePerfilArgentino, getSkillsConsolidadas } from '@/lib/use-perfil-argentino';

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

interface WorkerProfile {
  id?: string;
  nombre: string;
  ocupaciones_trayectoria: string[];
  skills_seleccionadas: string[];
  skills_eliminadas: string[];
  skills_agregadas: string[];
  created_at?: string;
  updated_at?: string;
}

interface OccupationMatch {
  id: string;
  label: string;
  isco: string;
  matchScore: number;
  essentialTotal: number;
  essentialCovered: number;
  optionalCovered: number;
  gapCount: number;
  /** 'argentino' si usó perfil consolidado, 'esco' si usó ESCO puro */
  matchSource: 'argentino' | 'esco';
}

type Step = 'registro' | 'perfil' | 'matching';

export default function MySkillsSearch({
  occupationsData,
  occupationsList,
  onNavigateToOccupation,
  onNavigateToCompare
}: MySkillsSearchProps) {
  // Perfil Consolidado Argentino (si hay versión activa, se usa para matching)
  const perfilArgentino = usePerfilArgentino();

  // Current step
  const [currentStep, setCurrentStep] = useState<Step>('registro');

  // Profile data
  const [nombreTrabajador, setNombreTrabajador] = useState('');
  const [selectedOccupations, setSelectedOccupations] = useState<OccupationBasicInfo[]>([]);
  const [removedSkillIds, setRemovedSkillIds] = useState<Set<string>>(new Set());
  const [addedSkills, setAddedSkills] = useState<SearchableSkill[]>([]);

  // Skills data
  const [skillsData, setSkillsData] = useState<SkillsSearchableIndex | null>(null);
  const [isLoadingSkills, setIsLoadingSkills] = useState(false);

  // Search states
  const [occSearchTerm, setOccSearchTerm] = useState('');
  const [skillSearchTerm, setSkillSearchTerm] = useState('');
  const [isOccSearchOpen, setIsOccSearchOpen] = useState(false);
  const [isSkillSearchOpen, setIsSkillSearchOpen] = useState(false);
  const occSearchRef = useRef<HTMLDivElement>(null);
  const skillSearchRef = useRef<HTMLDivElement>(null);

  // Saved profiles
  const [savedProfiles, setSavedProfiles] = useState<WorkerProfile[]>([]);
  const [isLoadingProfiles, setIsLoadingProfiles] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [currentProfileId, setCurrentProfileId] = useState<string | null>(null);
  const [showProfilesDropdown, setShowProfilesDropdown] = useState(false);

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

  // Load saved profiles
  useEffect(() => {
    loadProfiles();
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (occSearchRef.current && !occSearchRef.current.contains(event.target as Node)) {
        setIsOccSearchOpen(false);
      }
      if (skillSearchRef.current && !skillSearchRef.current.contains(event.target as Node)) {
        setIsSkillSearchOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load profiles from API
  const loadProfiles = async () => {
    setIsLoadingProfiles(true);
    try {
      const res = await fetch('/api/worker-profiles');
      const data = await res.json();
      setSavedProfiles(data.profiles || []);
    } catch (err) {
      console.error('Error loading profiles:', err);
    } finally {
      setIsLoadingProfiles(false);
    }
  };

  // Save current profile
  const saveProfile = async () => {
    if (!nombreTrabajador.trim()) return;

    setIsSaving(true);
    try {
      const profileData: Partial<WorkerProfile> = {
        nombre: nombreTrabajador,
        ocupaciones_trayectoria: selectedOccupations.map(o => o.id),
        skills_seleccionadas: derivedSkills.map(s => s.id),
        skills_eliminadas: Array.from(removedSkillIds),
        skills_agregadas: addedSkills.map(s => s.id)
      };

      if (currentProfileId) {
        profileData.id = currentProfileId;
        await fetch('/api/worker-profiles', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(profileData)
        });
      } else {
        const res = await fetch('/api/worker-profiles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(profileData)
        });
        const data = await res.json();
        setCurrentProfileId(data.profile?.id);
      }

      await loadProfiles();
    } catch (err) {
      console.error('Error saving profile:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Load a specific profile
  const loadProfile = (profile: WorkerProfile) => {
    setNombreTrabajador(profile.nombre);
    setCurrentProfileId(profile.id || null);

    // Restore occupations
    const occs = profile.ocupaciones_trayectoria
      .map(id => occupationsList.find(o => o.id === id))
      .filter(Boolean) as OccupationBasicInfo[];
    setSelectedOccupations(occs);

    // Restore removed skills
    setRemovedSkillIds(new Set(profile.skills_eliminadas || []));

    // Restore added skills
    if (skillsData && profile.skills_agregadas) {
      const added = profile.skills_agregadas
        .map(id => skillsData.skills.find(s => s.id === id))
        .filter(Boolean) as SearchableSkill[];
      setAddedSkills(added);
    }

    setShowProfilesDropdown(false);
    setCurrentStep('perfil');
  };

  // New profile
  const newProfile = () => {
    setNombreTrabajador('');
    setSelectedOccupations([]);
    setRemovedSkillIds(new Set());
    setAddedSkills([]);
    setCurrentProfileId(null);
    setCurrentStep('registro');
  };

  // Filter occupations for search
  const filteredOccupations = useMemo(() => {
    if (!occSearchTerm.trim()) return [];

    const normalizedSearch = occSearchTerm.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    const selectedIds = new Set(selectedOccupations.map(o => o.id));

    return occupationsList
      .filter(occ => {
        if (selectedIds.has(occ.id)) return false;
        const normalizedLabel = occ.label.toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '');
        return normalizedLabel.includes(normalizedSearch);
      })
      .slice(0, 15);
  }, [occupationsList, occSearchTerm, selectedOccupations]);

  // Filter skills for search
  const filteredSkills = useMemo(() => {
    if (!skillsData || !skillSearchTerm.trim()) return [];

    const normalizedSearch = skillSearchTerm.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    const addedIds = new Set(addedSkills.map(s => s.id));

    return skillsData.skills
      .filter(skill => {
        if (addedIds.has(skill.id)) return false;
        const normalizedLabel = skill.label.toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '');
        return normalizedLabel.includes(normalizedSearch);
      })
      .slice(0, 20);
  }, [skillsData, skillSearchTerm, addedSkills]);

  // Derive skills from selected occupations
  const derivedSkills = useMemo(() => {
    if (!occupationsData || selectedOccupations.length === 0) return [];

    const skillsMap = new Map<string, { skill: SearchableSkill; count: number; isEssential: boolean }>();

    for (const occ of selectedOccupations) {
      const occData = occupationsData[occ.id];
      if (!occData) continue;

      // Process essential skills
      [...occData.skills.essential, ...occData.knowledge.essential].forEach(s => {
        if (removedSkillIds.has(s.id)) return;
        const existing = skillsMap.get(s.id);
        if (existing) {
          existing.count++;
          existing.isEssential = true;
        } else {
          skillsMap.set(s.id, {
            skill: {
              id: s.id,
              label: s.label,
              type: s.L1.startsWith('K') ? 'knowledge' : 'skill',
              L1: s.L1,
              L2: s.L2,
              essential: 1,
              optional: 0,
              total: 1,
              description: s.description
            },
            count: 1,
            isEssential: true
          });
        }
      });

      // Process optional skills
      [...occData.skills.optional, ...occData.knowledge.optional].forEach(s => {
        if (removedSkillIds.has(s.id)) return;
        const existing = skillsMap.get(s.id);
        if (existing) {
          existing.count++;
        } else {
          skillsMap.set(s.id, {
            skill: {
              id: s.id,
              label: s.label,
              type: s.L1.startsWith('K') ? 'knowledge' : 'skill',
              L1: s.L1,
              L2: s.L2,
              essential: 0,
              optional: 1,
              total: 1,
              description: s.description
            },
            count: 1,
            isEssential: false
          });
        }
      });
    }

    // Add manually added skills
    for (const skill of addedSkills) {
      if (!skillsMap.has(skill.id)) {
        skillsMap.set(skill.id, { skill, count: 1, isEssential: false });
      }
    }

    return Array.from(skillsMap.values())
      .sort((a, b) => b.count - a.count || (a.isEssential ? -1 : 1))
      .map(v => v.skill);
  }, [occupationsData, selectedOccupations, removedSkillIds, addedSkills]);

  // Calculate matching occupations
  // Si hay perfil argentino activo, usa skills_consolidadas (ESCO + emergentes).
  // Si no hay perfil argentino para una ocupación, usa ESCO puro como fallback.
  const matchingOccupations = useMemo((): OccupationMatch[] => {
    if (!occupationsData || derivedSkills.length === 0) return [];

    const selectedSkillIds = new Set(derivedSkills.map(s => s.id));
    // También matchear por label normalizado (para emergentes que no tienen URI ESCO)
    const selectedSkillLabels = new Set(
      derivedSkills.map(s => s.label.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''))
    );
    const matches: OccupationMatch[] = [];

    for (const [occId, occ] of Object.entries(occupationsData)) {
      // Intentar usar perfil argentino primero
      const skillsArgentinas = getSkillsConsolidadas(
        perfilArgentino.snapshot,
        occId  // occId es el URI ESCO de la ocupación
      );

      let essentialCovered = 0;
      let optionalCovered = 0;
      let essentialTotal = 0;
      let matchSource: 'argentino' | 'esco' = 'esco';

      if (skillsArgentinas) {
        // --- PERFIL ARGENTINO: usa skills_consolidadas ---
        matchSource = 'argentino';
        // En el perfil argentino, todas las skills consolidadas se tratan como "requeridas"
        // (tanto las ESCO comunes como las emergentes aprobadas)
        essentialTotal = skillsArgentinas.length;

        for (const skillArg of skillsArgentinas) {
          // Matchear por URI si existe, sino por label normalizado
          const labelNorm = skillArg.label_normalized ||
            skillArg.label.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

          if ((skillArg.uri && selectedSkillIds.has(skillArg.uri)) ||
              selectedSkillLabels.has(labelNorm)) {
            essentialCovered++;
          }
        }
      } else {
        // --- FALLBACK ESCO PURO ---
        matchSource = 'esco';
        const essentialIds = new Set([
          ...occ.skills.essential.map(s => s.id),
          ...occ.knowledge.essential.map(s => s.id)
        ]);
        const optionalIds = new Set([
          ...occ.skills.optional.map(s => s.id),
          ...occ.knowledge.optional.map(s => s.id)
        ]);

        essentialTotal = occ.skills.essential.length + occ.knowledge.essential.length;

        for (const skillId of selectedSkillIds) {
          if (essentialIds.has(skillId)) essentialCovered++;
          else if (optionalIds.has(skillId)) optionalCovered++;
        }
      }

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
          gapCount: essentialTotal - essentialCovered,
          matchSource,
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
  }, [occupationsData, derivedSkills, sortBy, perfilArgentino.snapshot]);

  const addOccupation = (occ: OccupationBasicInfo) => {
    setSelectedOccupations(prev => [...prev, occ]);
    setOccSearchTerm('');
    setIsOccSearchOpen(false);
  };

  const removeOccupation = (occId: string) => {
    setSelectedOccupations(prev => prev.filter(o => o.id !== occId));
  };

  const removeSkill = (skillId: string) => {
    setRemovedSkillIds(prev => new Set([...prev, skillId]));
    setAddedSkills(prev => prev.filter(s => s.id !== skillId));
  };

  const restoreSkill = (skillId: string) => {
    setRemovedSkillIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(skillId);
      return newSet;
    });
  };

  const addSkill = (skill: SearchableSkill) => {
    setAddedSkills(prev => [...prev, skill]);
    setSkillSearchTerm('');
    setIsSkillSearchOpen(false);
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
      {/* Header with Actions */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Target className="w-7 h-7 text-green-600" />
            Perfiles de Trabajadores
          </h2>
          <p className="text-gray-600 mt-1">
            Sistema de apoyo para oficina de empleo - Construye perfiles y encuentra ocupaciones compatibles
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Load profile dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowProfilesDropdown(!showProfilesDropdown)}
              className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <FolderOpen className="w-4 h-4" />
              Cargar perfil
              <ChevronDown className="w-4 h-4" />
            </button>

            {showProfilesDropdown && (
              <div className="absolute right-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-64 overflow-y-auto">
                {isLoadingProfiles ? (
                  <div className="p-4 text-center text-gray-500">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                  </div>
                ) : savedProfiles.length === 0 ? (
                  <div className="p-4 text-center text-gray-500 text-sm">
                    No hay perfiles guardados
                  </div>
                ) : (
                  savedProfiles.map(profile => (
                    <button
                      key={profile.id}
                      onClick={() => loadProfile(profile)}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-0"
                    >
                      <div className="font-medium text-sm">{profile.nombre}</div>
                      <div className="text-xs text-gray-500">
                        {profile.ocupaciones_trayectoria?.length || 0} ocupaciones
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>

          <button
            onClick={newProfile}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Plus className="w-4 h-4" />
            Nuevo perfil
          </button>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-4 bg-white rounded-xl p-4 border border-gray-200">
        {[
          { key: 'registro', label: '1. Registro', icon: User },
          { key: 'perfil', label: '2. Construir Perfil', icon: Briefcase },
          { key: 'matching', label: '3. Ocupaciones', icon: Target }
        ].map((step, idx) => (
          <button
            key={step.key}
            onClick={() => {
              if (step.key === 'registro' || nombreTrabajador) {
                setCurrentStep(step.key as Step);
              }
            }}
            disabled={step.key !== 'registro' && !nombreTrabajador}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              currentStep === step.key
                ? 'bg-green-600 text-white'
                : nombreTrabajador || step.key === 'registro'
                  ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  : 'bg-gray-50 text-gray-400 cursor-not-allowed'
            }`}
          >
            <step.icon className="w-4 h-4" />
            {step.label}
            {step.key === 'registro' && nombreTrabajador && (
              <Check className="w-4 h-4 ml-1" />
            )}
          </button>
        ))}
      </div>

      {/* STEP 1: Registro */}
      {currentStep === 'registro' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <User className="w-5 h-5 text-green-600" />
            Datos del Trabajador/a
          </h3>

          <div className="max-w-md">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nombre completo
            </label>
            <input
              type="text"
              value={nombreTrabajador}
              onChange={(e) => setNombreTrabajador(e.target.value)}
              placeholder="Ej: Juan Pérez"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-200 focus:border-green-500"
            />

            <button
              onClick={() => nombreTrabajador.trim() && setCurrentStep('perfil')}
              disabled={!nombreTrabajador.trim()}
              className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Continuar
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Construcción del Perfil */}
      {currentStep === 'perfil' && (
        <div className="space-y-6">
          {/* 2a: Ingresar ocupaciones de trayectoria */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-blue-600" />
              Trayectoria Laboral de {nombreTrabajador}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Ingresa las ocupaciones que ha tenido el trabajador. El sistema calculará las competencias asociadas.
            </p>

            {/* Occupation search */}
            <div ref={occSearchRef} className="relative mb-4">
              <div className="flex items-center gap-2 p-3 border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-blue-200 focus-within:border-blue-500">
                <Search className="w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={occSearchTerm}
                  onChange={(e) => {
                    setOccSearchTerm(e.target.value);
                    setIsOccSearchOpen(true);
                  }}
                  onFocus={() => setIsOccSearchOpen(true)}
                  placeholder="Buscar ocupación (ej: Vendedor, Contador, Electricista...)"
                  className="flex-1 outline-none text-sm"
                />
              </div>

              {isOccSearchOpen && occSearchTerm && (
                <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                  {filteredOccupations.length === 0 ? (
                    <div className="px-4 py-8 text-center text-gray-500">
                      No se encontraron ocupaciones
                    </div>
                  ) : (
                    filteredOccupations.map(occ => (
                      <div
                        key={occ.id}
                        onClick={() => addOccupation(occ)}
                        className="px-4 py-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-0"
                      >
                        <div className="font-medium text-sm text-gray-900">{occ.label}</div>
                        <div className="text-xs text-gray-500">ISCO: {occ.isco}</div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Selected occupations */}
            {selectedOccupations.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {selectedOccupations.map(occ => (
                  <div
                    key={occ.id}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    <Briefcase className="w-3 h-3" />
                    <span className="max-w-[200px] truncate">{occ.label}</span>
                    <button
                      onClick={() => removeOccupation(occ.id)}
                      className="hover:bg-blue-200 rounded-full p-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500 text-sm">
                Agrega ocupaciones de la trayectoria laboral
              </div>
            )}
          </div>

          {/* 2b/2c/2d: Skills derivadas y gestión */}
          {selectedOccupations.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">
                  Competencias del Perfil ({derivedSkills.length})
                </h3>
                <button
                  onClick={saveProfile}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
                >
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Guardar perfil
                </button>
              </div>

              <p className="text-sm text-gray-600 mb-4">
                Estas son las competencias derivadas de las ocupaciones.
                <strong className="text-red-600"> Elimina</strong> las que el trabajador NO tiene,
                o <strong className="text-green-600">agrega</strong> otras manualmente.
              </p>

              {/* Add skill search */}
              <div ref={skillSearchRef} className="relative mb-4">
                <div className="flex items-center gap-2 p-2 border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-green-200 focus-within:border-green-500 bg-gray-50">
                  <Plus className="w-4 h-4 text-green-600" />
                  <input
                    type="text"
                    value={skillSearchTerm}
                    onChange={(e) => {
                      setSkillSearchTerm(e.target.value);
                      setIsSkillSearchOpen(true);
                    }}
                    onFocus={() => setIsSkillSearchOpen(true)}
                    placeholder="Agregar competencia manualmente..."
                    className="flex-1 outline-none text-sm bg-transparent"
                  />
                </div>

                {isSkillSearchOpen && skillSearchTerm && (
                  <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                    {filteredSkills.length === 0 ? (
                      <div className="px-4 py-6 text-center text-gray-500 text-sm">
                        No se encontraron competencias
                      </div>
                    ) : (
                      filteredSkills.map(skill => (
                        <div
                          key={skill.id}
                          onClick={() => addSkill(skill)}
                          className="px-4 py-2 hover:bg-green-50 cursor-pointer border-b border-gray-100 last:border-0"
                        >
                          <div className="font-medium text-sm text-gray-900">{skill.label}</div>
                          <div className="text-xs text-gray-500">
                            <span className={skill.type === 'knowledge' ? 'text-amber-600' : 'text-indigo-600'}>
                              {skill.type === 'knowledge' ? 'Conocimiento' : 'Skill'}
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Skills grid */}
              <div className="flex flex-wrap gap-2 max-h-[300px] overflow-y-auto">
                {derivedSkills.map(skill => (
                  <div
                    key={skill.id}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                      skill.type === 'knowledge'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    <span className="max-w-[180px] truncate">{skill.label}</span>
                    <button
                      onClick={() => removeSkill(skill.id)}
                      className="hover:bg-white/50 rounded-full p-0.5"
                      title="Eliminar (el trabajador NO tiene esta competencia)"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Removed skills (can restore) */}
              {removedSkillIds.size > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-500 mb-2">
                    Competencias eliminadas ({removedSkillIds.size}):
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {Array.from(removedSkillIds).slice(0, 10).map(skillId => {
                      const skill = skillsData.skills.find(s => s.id === skillId);
                      if (!skill) return null;
                      return (
                        <button
                          key={skillId}
                          onClick={() => restoreSkill(skillId)}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded-full hover:bg-gray-200"
                          title="Click para restaurar"
                        >
                          <Plus className="w-3 h-3" />
                          {skill.label}
                        </button>
                      );
                    })}
                    {removedSkillIds.size > 10 && (
                      <span className="text-xs text-gray-400">
                        +{removedSkillIds.size - 10} más
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Continue button */}
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setCurrentStep('matching')}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Ver ocupaciones compatibles
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* STEP 3: Matching con ocupaciones */}
      {currentStep === 'matching' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-gray-900">
                Ocupaciones Compatibles para {nombreTrabajador}
              </h3>
              <p className="text-sm text-gray-500">
                Basado en {derivedSkills.length} competencias del perfil
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500">Ordenar:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'match' | 'gap' | 'alpha')}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  <option value="match">Mejor match</option>
                  <option value="gap">Menor gap</option>
                  <option value="alpha">Alfabético</option>
                </select>
              </div>

              <button
                onClick={() => setCurrentStep('perfil')}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Editar perfil
              </button>
            </div>
          </div>

          {matchingOccupations.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No se encontraron ocupaciones compatibles</p>
              <button
                onClick={() => setCurrentStep('perfil')}
                className="mt-4 text-blue-600 hover:text-blue-800"
              >
                Volver a editar el perfil
              </button>
            </div>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {matchingOccupations.slice(0, 50).map((occ, index) => (
                <div
                  key={occ.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 font-mono text-sm w-6 shrink-0">
                          {index + 1}.
                        </span>
                        <span className="font-medium text-gray-900">{occ.label}</span>
                      </div>
                      <div className="ml-8 mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
                        <span className="font-mono">ISCO: {occ.isco}</span>
                        <span>
                          <Star className="w-3 h-3 inline text-green-500 fill-green-500" /> {occ.essentialCovered}/{occ.essentialTotal} esenciales
                        </span>
                        {occ.optionalCovered > 0 && (
                          <span>+{occ.optionalCovered} opcionales</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-4 ml-8 sm:ml-0">
                      <div className="text-right">
                        <div className={`text-lg font-bold ${
                          occ.matchScore >= 70 ? 'text-green-600' :
                          occ.matchScore >= 40 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {occ.matchScore}%
                        </div>
                        <div className="text-xs text-gray-500">match</div>
                      </div>

                      <div className="text-right">
                        <div className={`text-lg font-bold ${
                          occ.gapCount === 0 ? 'text-green-600' :
                          occ.gapCount <= 3 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {occ.gapCount}
                        </div>
                        <div className="text-xs text-gray-500">gap</div>
                      </div>

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
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
