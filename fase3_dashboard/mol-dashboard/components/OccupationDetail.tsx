'use client';

import { useState, useEffect, useMemo } from 'react';
import { Search, Loader2, Briefcase, ChevronDown, X, ExternalLink, BookOpen, MessageSquare } from 'lucide-react';
import SkillsList from './SkillsList';
import SimilarOccupations from './SimilarOccupations';
import OfertasOcupacionModal from './OfertasOcupacionModal';
import { OccupationDetail as OccupationDetailType, OccupationFullDetailIndex } from '@/lib/types';
import { getOfertasCountByIsco } from '@/lib/supabase';
import { capitalize } from '@/lib/utils';

function normalizeIsco(isco: string): string {
  return isco.startsWith('C') ? isco.substring(1) : isco;
}

interface OccupationInfo {
  id: string;
  label: string;
  isco: string;
}

interface OccupationDetailProps {
  occupationsData: OccupationFullDetailIndex | null;
  occupationsList: OccupationInfo[];
  onNavigateToCompare?: (occAId: string, occBId: string) => void;
  initialOccupation?: string | null;
}

export default function OccupationDetail({
  occupationsData,
  occupationsList,
  onNavigateToCompare,
  initialOccupation
}: OccupationDetailProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [ofertasCountMap, setOfertasCountMap] = useState<Record<string, number>>({});
  const [modalIsco, setModalIsco] = useState('');
  const [modalLabel, setModalLabel] = useState('');
  const [showOfertasModal, setShowOfertasModal] = useState(false);
  const [cursos, setCursos] = useState<any[]>([]);
  const [loadingCursos, setLoadingCursos] = useState(false);
  const [showAllCursos, setShowAllCursos] = useState(false);

  // Set initial occupation when prop changes
  useEffect(() => {
    if (initialOccupation) {
      setSelectedId(initialOccupation);
    }
  }, [initialOccupation]);

  // Fetch ofertas count by ISCO on mount
  useEffect(() => {
    async function fetchOfertasCount() {
      const counts = await getOfertasCountByIsco();
      setOfertasCountMap(counts);
    }
    fetchOfertasCount();
  }, []);

  // Get selected occupation detail
  const selectedOccupation = useMemo(() => {
    if (!selectedId || !occupationsData) return null;
    return occupationsData[selectedId] || null;
  }, [selectedId, occupationsData]);

  // Get selected occupation basic info
  const selectedInfo = useMemo(() => {
    return occupationsList.find(o => o.id === selectedId) || null;
  }, [selectedId, occupationsList]);

  // Filter occupations for dropdown
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
  };

  const handleClear = () => {
    setSelectedId(null);
    setSearchTerm('');
  };

  // Fetch cursos when occupation changes
  useEffect(() => {
    if (!selectedOccupation) { setCursos([]); return; }
    const essential = selectedOccupation.skills?.essential ?? [];
    if (essential.length === 0) { setCursos([]); return; }
    const uris = essential.map((s: any) => `http://data.europa.eu/esco/skill/${s.id}`);
    setLoadingCursos(true);
    setShowAllCursos(false);
    fetch('/api/perfiles/cursos-gap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gap_skill_uris: uris }),
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.cursos) setCursos(data.cursos); })
      .catch(() => {})
      .finally(() => setLoadingCursos(false));
  }, [selectedOccupation]);

  const handleViewSimilar = (similarId: string) => {
    setSelectedId(similarId);
  };

  const handleCompare = (similarId: string) => {
    if (selectedId && onNavigateToCompare) {
      onNavigateToCompare(selectedId, similarId);
    }
  };

  // AI policy recommendation
  const [recoPolicy, setRecoPolicy] = useState<string | null>(null);
  const [loadingReco, setLoadingReco] = useState(false);
  const [recoError, setRecoError] = useState(false);

  // Clear recommendation when occupation changes
  useEffect(() => {
    setRecoPolicy(null);
    setRecoError(false);
  }, [selectedId]);

  async function handlePedirAnalisis() {
    if (!selectedOccupation || !selectedInfo) return;
    setLoadingReco(true);
    setRecoError(false);
    setRecoPolicy(null);
    try {
      const isco = normalizeIsco(selectedInfo.isco);
      const ofertas = ofertasCountMap[isco] || 0;
      const essential = selectedOccupation.skills?.essential || [];
      const optional = selectedOccupation.skills?.optional || [];
      const knowledge = [...(selectedOccupation.knowledge?.essential || []), ...(selectedOccupation.knowledge?.optional || [])];
      const similar = (selectedOccupation.similar || []).slice(0, 6).map((s: any) => {
        const simIsco = normalizeIsco(s.isco || '');
        return {
          label: s.label,
          isco_code: simIsco,
          similarity: s.similarity || s.jaccard || 0,
          ofertas: ofertasCountMap[simIsco] || 0,
        };
      });

      const res = await fetch('/api/analisis-ocupacional', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ocupacion: {
            label: selectedInfo.label,
            isco_code: isco,
            ofertas_total: ofertas,
            skills_esenciales: essential.slice(0, 8).map((s: any) => s.label),
            skills_opcionales_count: optional.length,
            knowledge_esenciales: knowledge.slice(0, 5).map((k: any) => k.label),
          },
          similares: similar,
          cursos: cursos.slice(0, 5).map((c: any) => ({
            titulo: c.titulo,
            institucion: c.institucion,
            provincia: c.provincia,
            skills_cubiertas: c.skills_cubiertas,
          })),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setRecoPolicy(data.recomendacion || null);
      } else {
        setRecoError(true);
      }
    } catch {
      setRecoError(true);
    } finally {
      setLoadingReco(false);
    }
  }

  const handleViewOfertas = (isco: string, label: string) => {
    setModalIsco(isco);
    setModalLabel(label);
    setShowOfertasModal(true);
  };

  if (!occupationsData) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">Cargando datos de ocupaciones...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <Briefcase className="w-7 h-7 text-blue-600" />
          Detalle de Ocupacion
        </h2>
        <p className="text-gray-600 mt-1">
          Selecciona una ocupacion ESCO para ver todas sus competencias y ocupaciones relacionadas
        </p>
      </div>

      {/* Occupation Selector */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Ocupacion ESCO
        </label>

        {selectedInfo ? (
          // Selected state
          <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex-1">
              <div className="font-semibold text-blue-900">{capitalize(selectedInfo.label)}</div>
              <div className="text-sm text-blue-700 flex items-center gap-2">
                ISCO: {selectedInfo.isco}
                {(() => {
                  const isco = normalizeIsco(selectedInfo.isco);
                  const count = ofertasCountMap[isco] || ofertasCountMap[selectedInfo.isco] || 0;
                  if (count === 0) return null;
                  return (
                    <button
                      onClick={() => handleViewOfertas(isco, selectedInfo.label)}
                      className="inline-flex items-center gap-1 bg-green-100 hover:bg-green-200 text-green-700 text-xs px-2 py-0.5 rounded-full font-medium transition-colors"
                    >
                      <Briefcase className="w-3 h-3" />
                      {count} {count === 1 ? 'oferta' : 'ofertas'}
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  );
                })()}
              </div>
            </div>
            <button
              onClick={handleClear}
              className="p-2 hover:bg-blue-100 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-blue-600" />
            </button>
          </div>
        ) : (
          // Selector
          <div className="relative">
            <div
              className={`flex items-center gap-2 p-3 border rounded-lg cursor-pointer transition-colors ${
                isDropdownOpen ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300 hover:border-gray-400'
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
                  Buscar entre {occupationsList.length.toLocaleString()} ocupaciones...
                </span>
              )}
              <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </div>

            {/* Dropdown */}
            {isDropdownOpen && (
              <>
                {/* Backdrop */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setIsDropdownOpen(false)}
                />

                {/* List */}
                <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
                  <div className="px-3 py-2 bg-gray-50 border-b text-sm text-gray-600">
                    {searchTerm
                      ? `${filteredOccupations.length} resultados`
                      : `${occupationsList.length} ocupaciones ESCO`}
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
                          className="px-4 py-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-0"
                        >
                          <div className="font-medium text-gray-900">{capitalize(occ.label)}</div>
                          <div className="text-sm text-gray-500">ISCO: {occ.isco}</div>
                        </li>
                      ))
                    )}
                    {filteredOccupations.length > 100 && (
                      <li className="px-4 py-3 text-center text-sm text-gray-500 bg-gray-50">
                        Mostrando 100 de {filteredOccupations.length} resultados. Refina tu busqueda.
                      </li>
                    )}
                  </ul>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* AI Policy Analysis */}
      {selectedOccupation && selectedInfo && (
        <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-semibold text-blue-700">Análisis de reconversión ocupacional</h3>
          </div>

          {!recoPolicy && !loadingReco && !recoError && (
            <div className="flex items-center gap-3">
              <p className="text-xs text-gray-500 flex-1">
                Ante un escenario de crisis (cierre de empresa, caída de demanda, apertura de importaciones), qué opciones de reconversión existen para los trabajadores de esta ocupación.
              </p>
              <button
                onClick={handlePedirAnalisis}
                className="inline-flex items-center gap-1.5 bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shrink-0"
              >
                <MessageSquare className="w-3.5 h-3.5" />
                Analizar reconversión
              </button>
            </div>
          )}

          {loadingReco && (
            <div className="flex items-center justify-center gap-2 py-4 text-blue-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-xs">Analizando ocupación, skills transferibles y mercado...</span>
            </div>
          )}

          {recoError && (
            <div className="flex items-center gap-3">
              <p className="text-xs text-red-500 flex-1">No se pudo generar el análisis.</p>
              <button onClick={handlePedirAnalisis} className="text-xs text-blue-600 hover:text-blue-700 font-medium shrink-0">Reintentar</button>
            </div>
          )}

          {recoPolicy && (
            <div>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{recoPolicy}</p>
              <p className="text-[9px] text-gray-400 mt-3 leading-snug">
                Generado con IA a partir de datos del mercado laboral argentino. Orientativo para fundamentar política — no constituye dictamen técnico.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Content - only show when occupation selected */}
      {selectedOccupation && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Skills Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Skills */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <SkillsList
                essential={selectedOccupation.skills.essential}
                optional={selectedOccupation.skills.optional}
                title="Competencias (Skills)"
                type="skills"
                maxHeight="350px"
              />
            </div>

            {/* Knowledge */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <SkillsList
                essential={selectedOccupation.knowledge.essential}
                optional={selectedOccupation.knowledge.optional}
                title="Conocimientos (Knowledge)"
                type="knowledge"
                maxHeight="350px"
              />
            </div>

            {/* Cursos de formación */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-3">
                <BookOpen className="w-4 h-4 text-purple-600" />
                <h3 className="text-sm font-semibold text-gray-800">Cursos del sistema de formación continua del STEySS</h3>
              </div>
              <p className="text-xs text-gray-400 mb-3">Formación disponible para esta ocupación</p>
              {loadingCursos && (
                <div className="flex items-center gap-2 py-3 text-gray-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-xs">Buscando cursos...</span>
                </div>
              )}
              {!loadingCursos && cursos.length === 0 && (
                <p className="text-xs text-gray-400 py-2">No hay cursos registrados para esta ocupación</p>
              )}
              {!loadingCursos && cursos.length > 0 && (
                <div className="space-y-2">
                  {(showAllCursos ? cursos : cursos.slice(0, 3)).map((c: any, i: number) => (
                    <div key={`${c.curso_id}-${c.provincia}-${i}`} className="border rounded-lg p-3">
                      <p className="text-sm font-medium text-gray-900">{c.titulo}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{c.institucion} · {c.municipio}, {c.provincia}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-medium">{c.modalidad || 'Presencial'}</span>
                        {c.carga_horaria > 0 && <span className="text-[10px] text-gray-400">{c.carga_horaria}hs</span>}
                      </div>
                    </div>
                  ))}
                  {!showAllCursos && cursos.length > 3 && (
                    <button onClick={() => setShowAllCursos(true)} className="text-xs text-purple-600 hover:text-purple-700 font-medium">
                      Ver {cursos.length - 3} cursos más
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Similar Occupations Column */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-4">
              <SimilarOccupations
                occupations={selectedOccupation.similar}
                ofertasCountMap={ofertasCountMap}
                onSelect={handleViewSimilar}
                onCompare={onNavigateToCompare ? handleCompare : undefined}
                onViewOfertas={handleViewOfertas}
                maxItems={10}
                showQuantitySelector={true}
              />
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!selectedOccupation && (
        <div className="bg-gray-50 rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <Briefcase className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">
            Selecciona una ocupacion
          </h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Usa el buscador de arriba para encontrar una ocupacion ESCO y ver todas sus
            competencias, conocimientos y ocupaciones similares.
          </p>
        </div>
      )}

      {/* Modal de ofertas por ocupación */}
      <OfertasOcupacionModal
        isOpen={showOfertasModal}
        onClose={() => setShowOfertasModal(false)}
        iscoCode={modalIsco}
        iscoLabel={modalLabel}
      />
    </div>
  );
}
