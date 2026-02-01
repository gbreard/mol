'use client';

import { ArrowRight, Users } from 'lucide-react';
import { SimilarOccupation } from '@/lib/types';

interface SimilarOccupationsProps {
  occupations: SimilarOccupation[];
  onSelect?: (occupationId: string) => void;
  onCompare?: (occupationId: string) => void;
  maxItems?: number;
}

export default function SimilarOccupations({
  occupations,
  onSelect,
  onCompare,
  maxItems = 10
}: SimilarOccupationsProps) {
  const displayed = occupations.slice(0, maxItems);

  if (displayed.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No hay ocupaciones similares</p>
      </div>
    );
  }

  return (
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

              {/* Compare button */}
              {onCompare && (
                <button
                  onClick={() => onCompare(occ.id)}
                  className="ml-7 mt-2 text-xs text-purple-600 hover:text-purple-800 hover:underline"
                >
                  Comparar con esta ocupacion
                </button>
              )}
            </li>
          );
        })}
      </ul>

      {occupations.length > maxItems && (
        <p className="text-sm text-gray-500 mt-3 text-center">
          Mostrando {maxItems} de {occupations.length} similares
        </p>
      )}
    </div>
  );
}
