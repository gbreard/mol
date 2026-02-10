'use client';

import { useState, useEffect, useMemo } from 'react';
import { Search, Loader2, Briefcase, ChevronDown, X, ExternalLink } from 'lucide-react';
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

  const handleViewSimilar = (similarId: string) => {
    setSelectedId(similarId);
  };

  const handleCompare = (similarId: string) => {
    if (selectedId && onNavigateToCompare) {
      onNavigateToCompare(selectedId, similarId);
    }
  };

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
