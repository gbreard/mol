'use client';

import { useState, useEffect, useMemo } from 'react';
import { Search, Loader2, GitCompare, ChevronDown, X, Check, AlertCircle, Star, Circle, Briefcase, ExternalLink } from 'lucide-react';
import { OccupationDetail, OccupationFullDetailIndex, SkillItem } from '@/lib/types';
import { getOfertasCountByIsco } from '@/lib/supabase';
import OfertasOcupacionModal from './OfertasOcupacionModal';

// Helper to normalize ISCO code (remove 'C' prefix if present)
function normalizeIsco(isco: string): string {
  return isco.startsWith('C') ? isco.substring(1) : isco;
}

// Helper to get ofertas count with normalized ISCO
function getOfertasCount(isco: string, countMap: Record<string, number>): number {
  return countMap[isco] || countMap[normalizeIsco(isco)] || 0;
}

interface OccupationBasicInfo {
  id: string;
  label: string;
  isco: string;
}

interface OccupationCompareProps {
  occupationsData: OccupationFullDetailIndex | null;
  occupationsList: OccupationBasicInfo[];
  initialOccA?: string | null;
  initialOccB?: string | null;
}

interface GapAnalysis {
  shared: SkillItem[];
  sharedEssentialBoth: SkillItem[];
  sharedOptionalAny: SkillItem[];
  gapToCover: SkillItem[];           // In B but not in A
  gapEssential: SkillItem[];         // Essential in B, not in A
  gapOptional: SkillItem[];          // Optional in B, not in A
  transferable: SkillItem[];         // In A but not in B
  compatibility: number;              // 0-100
  sharedKnowledge: SkillItem[];
  gapKnowledge: SkillItem[];
}

export default function OccupationCompare({
  occupationsData,
  occupationsList,
  initialOccA,
  initialOccB
}: OccupationCompareProps) {
  const [selectedAId, setSelectedAId] = useState<string | null>(initialOccA || null);
  const [selectedBId, setSelectedBId] = useState<string | null>(initialOccB || null);
  const [ofertasCountMap, setOfertasCountMap] = useState<Record<string, number>>({});
  const [showOfertasModal, setShowOfertasModal] = useState(false);
  const [modalIsco, setModalIsco] = useState('');
  const [modalLabel, setModalLabel] = useState('');

  // Update when initial values change
  useEffect(() => {
    if (initialOccA) setSelectedAId(initialOccA);
    if (initialOccB) setSelectedBId(initialOccB);
  }, [initialOccA, initialOccB]);

  // Fetch ofertas count by ISCO on mount
  useEffect(() => {
    async function fetchOfertasCount() {
      const counts = await getOfertasCountByIsco();
      setOfertasCountMap(counts);
    }
    fetchOfertasCount();
  }, []);

  // Get occupation details
  const occA = useMemo(() => {
    if (!selectedAId || !occupationsData) return null;
    const detail = occupationsData[selectedAId];
    if (!detail) return null;
    return { id: selectedAId, ...detail };
  }, [selectedAId, occupationsData]);

  const occB = useMemo(() => {
    if (!selectedBId || !occupationsData) return null;
    const detail = occupationsData[selectedBId];
    if (!detail) return null;
    return { id: selectedBId, ...detail };
  }, [selectedBId, occupationsData]);

  // Calculate gap analysis
  const gapAnalysis = useMemo((): GapAnalysis | null => {
    if (!occA || !occB) return null;

    // Get all skills from A and B
    const allSkillsA = [...occA.skills.essential, ...occA.skills.optional];
    const allSkillsB = [...occB.skills.essential, ...occB.skills.optional];

    const skillIdsA = new Set(allSkillsA.map(s => s.id));
    const skillIdsB = new Set(allSkillsB.map(s => s.id));
    const essentialIdsA = new Set(occA.skills.essential.map(s => s.id));
    const essentialIdsB = new Set(occB.skills.essential.map(s => s.id));

    // Shared skills
    const shared = allSkillsB.filter(s => skillIdsA.has(s.id));
    const sharedEssentialBoth = shared.filter(s => essentialIdsA.has(s.id) && essentialIdsB.has(s.id));
    const sharedOptionalAny = shared.filter(s => !essentialIdsA.has(s.id) || !essentialIdsB.has(s.id));

    // Gap to cover (in B but not in A)
    const gapToCover = allSkillsB.filter(s => !skillIdsA.has(s.id));
    const gapEssential = gapToCover.filter(s => essentialIdsB.has(s.id));
    const gapOptional = gapToCover.filter(s => !essentialIdsB.has(s.id));

    // Transferable (in A but not in B)
    const transferable = allSkillsA.filter(s => !skillIdsB.has(s.id));

    // Compatibility: % of B's essential skills that A has
    const essentialBCount = occB.skills.essential.length;
    const essentialBCoveredCount = occB.skills.essential.filter(s => skillIdsA.has(s.id)).length;
    const compatibility = essentialBCount > 0
      ? Math.round((essentialBCoveredCount / essentialBCount) * 100)
      : 0;

    // Knowledge gap
    const allKnowledgeA = [...occA.knowledge.essential, ...occA.knowledge.optional];
    const allKnowledgeB = [...occB.knowledge.essential, ...occB.knowledge.optional];
    const knowledgeIdsA = new Set(allKnowledgeA.map(k => k.id));

    const sharedKnowledge = allKnowledgeB.filter(k => knowledgeIdsA.has(k.id));
    const gapKnowledge = allKnowledgeB.filter(k => !knowledgeIdsA.has(k.id));

    return {
      shared,
      sharedEssentialBoth,
      sharedOptionalAny,
      gapToCover,
      gapEssential,
      gapOptional,
      transferable,
      compatibility,
      sharedKnowledge,
      gapKnowledge
    };
  }, [occA, occB]);

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
          <GitCompare className="w-7 h-7 text-purple-600" />
          Comparar Ocupaciones
        </h2>
        <p className="text-gray-600 mt-1">
          Analiza el gap de skills entre dos ocupaciones y planifica tu transicion laboral
        </p>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <OccupationSelectorCard
          label="Ocupacion A (Actual)"
          color="blue"
          occupationsList={occupationsList}
          selectedId={selectedAId}
          excludeId={selectedBId}
          onSelect={setSelectedAId}
          occupationsData={occupationsData}
        />

        <OccupationSelectorCard
          label="Ocupacion B (Objetivo)"
          color="purple"
          occupationsList={occupationsList}
          selectedId={selectedBId}
          excludeId={selectedAId}
          onSelect={setSelectedBId}
          occupationsData={occupationsData}
        />
      </div>

      {/* Results */}
      {occA && occB && gapAnalysis && (
        <>
          {/* Banner: Ofertas activas para ocupación objetivo */}
          {(() => {
            const occBInfo = occupationsList.find(o => o.id === selectedBId);
            const ofertasCount = occBInfo ? getOfertasCount(occBInfo.isco, ofertasCountMap) : 0;
            if (ofertasCount === 0) return null;

            return (
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="bg-green-100 p-2 rounded-full">
                    <Briefcase className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-green-800">
                      Ofertas laborales activas en esta ocupacion
                    </p>
                    <p className="text-sm text-green-600">
                      Hay {ofertasCount} {ofertasCount === 1 ? 'oferta activa' : 'ofertas activas'} para "{occB.label}"
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (occBInfo) {
                      setModalIsco(normalizeIsco(occBInfo.isco));
                      setModalLabel(occB!.label);
                      setShowOfertasModal(true);
                    }
                  }}
                  className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Ver ofertas
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            );
          })()}

          {/* Compatibility Score */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Analisis de Transicion: {occA.label} → {occB.label}
            </h3>

            <div className="flex items-center gap-6">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Compatibilidad</span>
                  <span className={`text-2xl font-bold ${
                    gapAnalysis.compatibility >= 70 ? 'text-green-600' :
                    gapAnalysis.compatibility >= 40 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {gapAnalysis.compatibility}%
                  </span>
                </div>
                <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      gapAnalysis.compatibility >= 70 ? 'bg-green-500' :
                      gapAnalysis.compatibility >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${gapAnalysis.compatibility}%` }}
                  />
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Basado en skills esenciales de {occB.label} que ya tenes
                </p>
              </div>

              <div className="text-center px-6 border-l border-gray-200">
                <div className="text-3xl font-bold text-red-600">{gapAnalysis.gapEssential.length}</div>
                <div className="text-sm text-gray-500">Skills esenciales a cubrir</div>
              </div>
            </div>
          </div>

          {/* Gap Details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Shared Skills */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h4 className="font-semibold text-green-700 flex items-center gap-2 mb-4">
                <Check className="w-5 h-5" />
                Skills Compartidas ({gapAnalysis.shared.length})
              </h4>
              <p className="text-sm text-gray-500 mb-4">
                Estas skills ya las tenes y son requeridas en la ocupacion objetivo.
              </p>
              <SkillsListCompact
                skills={gapAnalysis.sharedEssentialBoth}
                label="Esenciales en ambas"
                emptyMessage="Ninguna"
                icon={<Star className="w-3 h-3 text-green-500 fill-green-500" />}
              />
              {gapAnalysis.sharedOptionalAny.length > 0 && (
                <SkillsListCompact
                  skills={gapAnalysis.sharedOptionalAny}
                  label="Compartidas (alguna opcional)"
                  emptyMessage=""
                  icon={<Circle className="w-3 h-3 text-green-400" />}
                  className="mt-4"
                />
              )}
            </div>

            {/* Gap to Cover */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h4 className="font-semibold text-red-700 flex items-center gap-2 mb-4">
                <AlertCircle className="w-5 h-5" />
                Gap a Cubrir ({gapAnalysis.gapToCover.length})
              </h4>
              <p className="text-sm text-gray-500 mb-4">
                Estas skills necesitas adquirir para la transicion.
              </p>
              <SkillsListCompact
                skills={gapAnalysis.gapEssential}
                label="Esenciales (prioridad alta)"
                emptyMessage="Ninguna"
                icon={<Star className="w-3 h-3 text-red-500 fill-red-500" />}
                highlight="red"
              />
              {gapAnalysis.gapOptional.length > 0 && (
                <SkillsListCompact
                  skills={gapAnalysis.gapOptional}
                  label="Opcionales"
                  emptyMessage=""
                  icon={<Circle className="w-3 h-3 text-orange-400" />}
                  className="mt-4"
                />
              )}
            </div>
          </div>

          {/* Knowledge Gap */}
          {(gapAnalysis.sharedKnowledge.length > 0 || gapAnalysis.gapKnowledge.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h4 className="font-semibold text-amber-700 flex items-center gap-2 mb-4">
                  Conocimientos Compartidos ({gapAnalysis.sharedKnowledge.length})
                </h4>
                <SkillsListCompact
                  skills={gapAnalysis.sharedKnowledge}
                  label=""
                  emptyMessage="Ninguno"
                />
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h4 className="font-semibold text-amber-700 flex items-center gap-2 mb-4">
                  Conocimientos a Adquirir ({gapAnalysis.gapKnowledge.length})
                </h4>
                <SkillsListCompact
                  skills={gapAnalysis.gapKnowledge}
                  label=""
                  emptyMessage="Ninguno"
                  highlight="amber"
                />
              </div>
            </div>
          )}

          {/* Transferable Skills */}
          {gapAnalysis.transferable.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h4 className="font-semibold text-blue-700 flex items-center gap-2 mb-4">
                Skills Transferibles ({gapAnalysis.transferable.length})
              </h4>
              <p className="text-sm text-gray-500 mb-4">
                Estas skills tenes de la ocupacion actual pero no son requeridas en la objetivo.
                Pueden ser valiosas para otras ocupaciones.
              </p>
              <SkillsListCompact
                skills={gapAnalysis.transferable.slice(0, 10)}
                label=""
                emptyMessage=""
              />
              {gapAnalysis.transferable.length > 10 && (
                <p className="text-sm text-gray-500 mt-2">
                  +{gapAnalysis.transferable.length - 10} mas...
                </p>
              )}
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {(!occA || !occB) && (
        <div className="bg-gray-50 rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <GitCompare className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">
            Selecciona dos ocupaciones
          </h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Elige una ocupacion actual (A) y una ocupacion objetivo (B) para ver el analisis
            de gap y planificar tu transicion laboral.
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

// ============= Helper Components =============

interface OccupationSelectorCardProps {
  label: string;
  color: 'blue' | 'purple';
  occupationsList: OccupationBasicInfo[];
  selectedId: string | null;
  excludeId: string | null;
  onSelect: (id: string | null) => void;
  occupationsData: OccupationFullDetailIndex;
}

function OccupationSelectorCard({
  label,
  color,
  occupationsList,
  selectedId,
  excludeId,
  onSelect,
  occupationsData
}: OccupationSelectorCardProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const colorClasses = {
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-900',
      light: 'text-blue-700'
    },
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-900',
      light: 'text-purple-700'
    }
  };

  const colors = colorClasses[color];

  const selectedOcc = selectedId ? occupationsData[selectedId] : null;
  const selectedInfo = occupationsList.find(o => o.id === selectedId);

  const filteredList = useMemo(() => {
    let list = occupationsList;

    // Exclude the other selected occupation
    if (excludeId) {
      list = list.filter(o => o.id !== excludeId);
    }

    if (!searchTerm.trim()) return list;

    const normalizedSearch = searchTerm.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    return list.filter(occ => {
      const normalizedLabel = occ.label.toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
      return normalizedLabel.includes(normalizedSearch) ||
             occ.isco.toLowerCase().includes(normalizedSearch);
    });
  }, [occupationsList, excludeId, searchTerm]);

  return (
    <div className={`rounded-xl shadow-sm border ${colors.border} p-4 ${colors.bg}`}>
      <label className={`block text-sm font-semibold ${colors.text} mb-3`}>
        {label}
      </label>

      {selectedInfo && selectedOcc ? (
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-start justify-between">
            <div>
              <div className={`font-semibold ${colors.text}`}>{selectedInfo.label}</div>
              <div className="text-sm text-gray-500">ISCO: {selectedInfo.isco}</div>
              <div className="text-xs text-gray-400 mt-1">
                {selectedOcc.counts.skills_essential} esenciales / {selectedOcc.counts.skills_optional} opcionales
              </div>
            </div>
            <button
              onClick={() => onSelect(null)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
      ) : (
        <div className="relative">
          <div
            className={`flex items-center gap-2 p-3 bg-white border border-gray-300 rounded-lg cursor-pointer ${
              isOpen ? 'ring-2 ring-blue-200' : ''
            }`}
            onClick={() => setIsOpen(true)}
          >
            <Search className="w-4 h-4 text-gray-400" />
            {isOpen ? (
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar ocupacion..."
                className="flex-1 outline-none text-sm"
                autoFocus
              />
            ) : (
              <span className="flex-1 text-sm text-gray-500">Seleccionar ocupacion...</span>
            )}
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </div>

          {isOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
              <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                {filteredList.slice(0, 50).map(occ => (
                  <div
                    key={occ.id}
                    onClick={() => {
                      onSelect(occ.id);
                      setIsOpen(false);
                      setSearchTerm('');
                    }}
                    className="px-4 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0"
                  >
                    <div className="font-medium text-sm text-gray-900">{occ.label}</div>
                    <div className="text-xs text-gray-500">ISCO: {occ.isco}</div>
                  </div>
                ))}
                {filteredList.length > 50 && (
                  <div className="px-4 py-2 text-center text-xs text-gray-500 bg-gray-50">
                    Refina tu busqueda ({filteredList.length} resultados)
                  </div>
                )}
                {filteredList.length === 0 && (
                  <div className="px-4 py-8 text-center text-gray-500">
                    No se encontraron ocupaciones
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

interface SkillsListCompactProps {
  skills: SkillItem[];
  label: string;
  emptyMessage: string;
  icon?: React.ReactNode;
  highlight?: 'red' | 'amber' | 'green';
  className?: string;
}

function SkillsListCompact({
  skills,
  label,
  emptyMessage,
  icon,
  highlight,
  className = ''
}: SkillsListCompactProps) {
  const highlightClasses = {
    red: 'bg-red-50',
    amber: 'bg-amber-50',
    green: 'bg-green-50'
  };

  if (skills.length === 0 && !emptyMessage) return null;

  return (
    <div className={className}>
      {label && (
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
          {label}
        </div>
      )}
      {skills.length === 0 ? (
        <p className="text-sm text-gray-400 italic">{emptyMessage}</p>
      ) : (
        <ul className="space-y-1 max-h-48 overflow-y-auto">
          {skills.map((skill, i) => (
            <li
              key={skill.id}
              className={`text-sm py-1 px-2 rounded flex items-center gap-2 ${
                highlight ? highlightClasses[highlight] : 'hover:bg-gray-50'
              }`}
            >
              {icon}
              <span className="text-gray-800">{skill.label}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
