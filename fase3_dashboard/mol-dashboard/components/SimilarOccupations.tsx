'use client';

import { useState } from 'react';
import { ArrowRight, Users, Briefcase, ExternalLink, ChevronDown } from 'lucide-react';
import { SimilarOccupation } from '@/lib/types';

interface SimilarOccupationsProps {
  occupations: SimilarOccupation[];
  ofertasCountMap?: Record<string, number>;
  onSelect?: (occupationId: string) => void;
  onCompare?: (occupationId: string) => void;
  maxItems?: number;
  showQuantitySelector?: boolean;
}

// Helper to normalize ISCO code (remove 'C' prefix if present)
function normalizeIsco(isco: string): string {
  return isco.startsWith('C') ? isco.substring(1) : isco;
}

// Helper to get ofertas count with normalized ISCO
function getOfertasCount(isco: string, countMap: Record<string, number>): number {
  // Try original format first, then normalized
  return countMap[isco] || countMap[normalizeIsco(isco)] || 0;
}

export default function SimilarOccupations({
  occupations,
  ofertasCountMap = {},
  onSelect,
  onCompare,
  maxItems = 10,
  showQuantitySelector = false
}: SimilarOccupationsProps) {
  const [displayCount, setDisplayCount] = useState(maxItems);

  const displayed = occupations.slice(0, displayCount);

  // Separate occupations with and without offers
  const withOffers = displayed.filter(occ => getOfertasCount(occ.isco, ofertasCountMap) > 0);
  const hasOfertasData = Object.keys(ofertasCountMap).length > 0;

  if (displayed.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No hay ocupaciones similares</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Quantity Selector */}
      {showQuantitySelector && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-600">Mostrar:</span>
          <select
            value={displayCount}
            onChange={(e) => setDisplayCount(Number(e.target.value))}
            className="border border-gray-300 rounded-md px-2 py-1 text-sm bg-white focus:ring-2 focus:ring-purple-200 focus:border-purple-400"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={30}>30</option>
          </select>
          <span className="text-gray-500">ocupaciones</span>
        </div>
      )}

      {/* Main list: All similar occupations */}
      <div>
        <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
          <Users className="w-5 h-5 text-purple-600" />
          Ocupaciones Similares
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          Por skills esenciales compartidas (Jaccard similarity)
        </p>

        <ul className="space-y-2">
          {displayed.map((occ, index) => {
            const percentMatch = Math.round(occ.jaccard * 100);
            const ofertasCount = getOfertasCount(occ.isco, ofertasCountMap);

            return (
              <li
                key={occ.id}
                className="bg-gray-50 hover:bg-gray-100 rounded-lg p-3 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-sm font-mono w-5">
                        {index + 1}.
                      </span>
                      <span className="font-medium text-gray-900 truncate">
                        {occ.label}
                      </span>
                      {/* Badge de ofertas */}
                      {hasOfertasData && ofertasCount > 0 && (
                        <span className="inline-flex items-center gap-1 bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full font-medium">
                          <Briefcase className="w-3 h-3" />
                          {ofertasCount}
                        </span>
                      )}
                    </div>
                    <div className="ml-7 mt-1 flex items-center gap-3 text-xs text-gray-500">
                      <span className="font-mono">ISCO: {occ.isco}</span>
                      <span>{occ.shared} skills compartidas</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-3">
                    {/* Similarity bar */}
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-purple-500 rounded-full transition-all"
                          style={{ width: `${percentMatch}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold text-purple-700 w-10 text-right">
                        {percentMatch}%
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-1">
                      {onSelect && (
                        <button
                          onClick={() => onSelect(occ.id)}
                          className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="Ver detalle"
                        >
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions row */}
                <div className="ml-7 mt-2 flex items-center gap-3">
                  {/* Compare button */}
                  {onCompare && (
                    <button
                      onClick={() => onCompare(occ.id)}
                      className="text-xs text-purple-600 hover:text-purple-800 hover:underline"
                    >
                      Comparar con esta ocupacion
                    </button>
                  )}

                  {/* Link to offers */}
                  {hasOfertasData && ofertasCount > 0 && (
                    <a
                      href={`/?tab=ofertas&isco=${normalizeIsco(occ.isco)}`}
                      className="text-xs text-green-600 hover:text-green-800 hover:underline flex items-center gap-1"
                    >
                      Ver {ofertasCount} {ofertasCount === 1 ? 'oferta' : 'ofertas'}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </li>
            );
          })}
        </ul>

        {occupations.length > displayCount && (
          <p className="text-sm text-gray-500 mt-3 text-center">
            Mostrando {displayCount} de {occupations.length} similares
          </p>
        )}
      </div>

      {/* Second column: Only occupations WITH offers */}
      {hasOfertasData && withOffers.length > 0 && (
        <div className="border-t pt-6">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
            <Briefcase className="w-5 h-5 text-green-600" />
            Ocupaciones Similares con Ofertas Activas
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            {withOffers.length} ocupaciones similares tienen ofertas laborales activas
          </p>

          <ul className="space-y-2">
            {withOffers.slice(0, displayCount).map((occ, index) => {
              const ofertasCount = getOfertasCount(occ.isco, ofertasCountMap);
              const percentMatch = Math.round(occ.jaccard * 100);

              return (
                <li
                  key={`with-offers-${occ.id}`}
                  className="bg-green-50 hover:bg-green-100 rounded-lg p-3 transition-colors border border-green-100"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900 truncate">
                          {occ.label}
                        </span>
                        <span className="inline-flex items-center gap-1 bg-green-200 text-green-800 text-xs px-2 py-0.5 rounded-full font-semibold">
                          <Briefcase className="w-3 h-3" />
                          {ofertasCount} {ofertasCount === 1 ? 'oferta' : 'ofertas'}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                        <span className="font-mono">ISCO: {occ.isco}</span>
                        <span>{percentMatch}% similar</span>
                      </div>
                    </div>

                    <a
                      href={`/?tab=ofertas&isco=${normalizeIsco(occ.isco)}`}
                      className="flex items-center gap-1 bg-green-600 hover:bg-green-700 text-white text-xs px-3 py-1.5 rounded-lg font-medium transition-colors"
                    >
                      Ver ofertas
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </li>
              );
            })}
          </ul>

          {withOffers.length > displayCount && (
            <p className="text-sm text-gray-500 mt-3 text-center">
              Mostrando {displayCount} de {withOffers.length} ocupaciones con ofertas
            </p>
          )}
        </div>
      )}
    </div>
  );
}
