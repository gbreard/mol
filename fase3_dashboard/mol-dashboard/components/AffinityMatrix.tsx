interface ReportSkillItem {
  uri: string
  label: string
  type: 'skill' | 'knowledge' | 'transversal'
  source: 'esco' | 'argentina_approved'
  description?: string
}

interface Props {
  detected: ReportSkillItem[]
  gaps: ReportSkillItem[]
}

const TYPE_BADGE: Record<string, string> = {
  skill: 'S',
  knowledge: 'K',
  transversal: 'T',
}

const TYPE_COLOR: Record<string, string> = {
  skill: 'bg-blue-100 text-blue-700',
  knowledge: 'bg-green-100 text-green-700',
  transversal: 'bg-purple-100 text-purple-700',
}

export default function AffinityMatrix({ detected, gaps }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <h2 className="mb-4 text-base font-semibold text-gray-800">Matriz de Afinidad</h2>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Detected */}
        <div>
          <p className="mb-2 text-sm font-medium text-gray-600">
            Competencias detectadas ({detected.length})
          </p>
          <ul className="space-y-1">
            {detected.map((s) => (
              <li key={s.uri} className="flex items-center gap-2 rounded px-2 py-1 hover:bg-gray-50">
                <span className="min-w-0 flex-1 text-sm text-gray-800">{s.label}</span>
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-bold ${TYPE_COLOR[s.type]}`}
                >
                  {TYPE_BADGE[s.type]}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Gaps */}
        <div>
          <p className="mb-2 text-sm font-medium text-red-600">
            Brechas técnicas ({gaps.length})
          </p>
          {gaps.length === 0 ? (
            <p className="text-sm text-green-600">Sin brechas — perfil completo ✓</p>
          ) : (
            <ul className="space-y-1">
              {gaps.map((s) => (
                <li key={s.uri} className="flex items-center gap-2 rounded px-2 py-1 hover:bg-red-50">
                  <span className="min-w-0 flex-1 text-sm text-gray-800">{s.label}</span>
                  <span className="shrink-0 rounded bg-red-100 px-1.5 py-0.5 text-xs font-bold text-red-700">
                    E
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <p className="mt-4 text-xs text-gray-400">
        [S] Competencia &nbsp;·&nbsp; [K] Conocimiento &nbsp;·&nbsp; [T] Transversal &nbsp;·&nbsp; [E] Esencial faltante
      </p>
    </div>
  )
}
