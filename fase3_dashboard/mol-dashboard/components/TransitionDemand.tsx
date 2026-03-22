import { TrendingUp } from 'lucide-react'

export interface DemandOccupation {
  ocupacion_label: string
  isco: string
  trend_pct: number
  match_score: number
  skills_gap: string[]
  estimated_months: number
}

interface Props {
  occupations: DemandOccupation[]
  onViewCourses?: (isco: string) => void
  onViewOffers?: (isco: string) => void
}

export default function TransitionDemand({ occupations, onViewCourses, onViewOffers }: Props) {
  if (occupations.length === 0) {
    return <p className="text-sm text-gray-400">No hay sugerencias de transición disponibles.</p>
  }

  // Sorted by match_score desc (accesibilidad)
  const sorted = [...occupations].sort((a, b) => b.match_score - a.match_score)

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-500">
        Ocupaciones en crecimiento cercanas a tu perfil, ordenadas por accesibilidad.
      </p>

      {/* Tabla — solo en sm+ */}
      <div className="hidden sm:block overflow-hidden rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium text-gray-600">Ocupación</th>
              <th className="px-4 py-2.5 text-left font-medium text-gray-600">Tendencia</th>
              <th className="px-4 py-2.5 text-left font-medium text-gray-600">Match</th>
              <th className="px-4 py-2.5 text-left font-medium text-gray-600">Tiempo est.</th>
              <th className="px-4 py-2.5 text-left font-medium text-gray-600">Skills faltantes</th>
              <th className="px-4 py-2.5 text-right font-medium text-gray-600">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sorted.map((occ) => (
              <tr key={occ.isco} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <p className="font-medium text-gray-900">{occ.ocupacion_label}</p>
                  <p className="text-xs text-gray-400">ISCO {occ.isco}</p>
                </td>
                <td className="px-4 py-3">
                  <span className="flex items-center gap-1 text-green-700">
                    <TrendingUp className="h-3.5 w-3.5" />
                    +{occ.trend_pct}%
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="font-semibold text-blue-700">{occ.match_score}%</span>
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {occ.estimated_months} meses
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {occ.skills_gap.slice(0, 3).map((s) => (
                      <span key={s} className="rounded bg-red-50 px-1.5 py-0.5 text-xs text-red-600">
                        {s}
                      </span>
                    ))}
                    {occ.skills_gap.length > 3 && (
                      <span className="text-xs text-gray-400">+{occ.skills_gap.length - 3}</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-2">
                    {onViewCourses && (
                      <button
                        onClick={() => onViewCourses(occ.isco)}
                        aria-label={`Ver cursos para ${occ.ocupacion_label}`}
                        className="rounded border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
                      >
                        Ver cursos
                      </button>
                    )}
                    {onViewOffers && (
                      <button
                        onClick={() => onViewOffers(occ.isco)}
                        aria-label={`Ver ofertas para ${occ.ocupacion_label}`}
                        className="rounded border border-blue-200 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50"
                      >
                        Ver ofertas
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Cards — solo en mobile */}
      <div className="space-y-3 sm:hidden">
        {sorted.map((occ) => (
          <div key={occ.isco} className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-gray-900 text-sm">{occ.ocupacion_label}</p>
                <p className="text-xs text-gray-400 mt-0.5">ISCO {occ.isco}</p>
              </div>
              <span className="shrink-0 font-semibold text-blue-700 text-base">{occ.match_score}%</span>
            </div>

            <div className="flex flex-wrap gap-3 text-sm">
              <span className="flex items-center gap-1 text-green-700">
                <TrendingUp className="h-3.5 w-3.5" />
                +{occ.trend_pct}%
              </span>
              <span className="text-gray-500">{occ.estimated_months} meses est.</span>
            </div>

            {occ.skills_gap.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {occ.skills_gap.slice(0, 3).map((s) => (
                  <span key={s} className="rounded bg-red-50 px-1.5 py-0.5 text-xs text-red-600">{s}</span>
                ))}
                {occ.skills_gap.length > 3 && (
                  <span className="text-xs text-gray-400">+{occ.skills_gap.length - 3}</span>
                )}
              </div>
            )}

            <div className="flex gap-2">
              {onViewCourses && (
                <button
                  onClick={() => onViewCourses(occ.isco)}
                  aria-label={`Ver cursos para ${occ.ocupacion_label}`}
                  className="flex-1 min-h-[44px] rounded border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
                >
                  Ver cursos
                </button>
              )}
              {onViewOffers && (
                <button
                  onClick={() => onViewOffers(occ.isco)}
                  aria-label={`Ver ofertas para ${occ.ocupacion_label}`}
                  className="flex-1 min-h-[44px] rounded border border-blue-200 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50"
                >
                  Ver ofertas
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
