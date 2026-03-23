'use client'

import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react'

export type DifficultyLevel = 'alta' | 'media' | 'baja'

export interface SkillBenchmark {
  uri: string
  label: string
  demanda_pct: number       // % de ofertas que piden esta skill
  disponibilidad_pct: number // % de perfiles que tienen esta skill
  brecha: number             // demanda - disponibilidad
  dificultad: DifficultyLevel
  tendencia: 'subiendo' | 'bajando' | 'estable'
}

export interface MarketBenchmarkData {
  jurisdiccion: string
  total_ofertas: number
  total_perfiles: number
  skills: SkillBenchmark[]
}

interface Props {
  data: MarketBenchmarkData
}

const difficultyColor: Record<DifficultyLevel, string> = {
  alta: 'bg-red-100 text-red-700',
  media: 'bg-amber-100 text-amber-700',
  baja: 'bg-green-100 text-green-700',
}

const TrendIcon = ({ t }: { t: SkillBenchmark['tendencia'] }) => {
  if (t === 'subiendo') return <TrendingUp className="h-4 w-4 text-red-500" />
  if (t === 'bajando') return <TrendingDown className="h-4 w-4 text-green-500" />
  return <Minus className="h-4 w-4 text-gray-400" />
}

export default function MarketBenchmark({ data }: Props) {
  const escasas = data.skills.filter((s) => s.dificultad === 'alta')

  return (
    <div className="space-y-6">
      {/* Alertas escasez */}
      {escasas.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <p className="text-sm font-semibold text-red-900">
              {escasas.length} skill{escasas.length !== 1 ? 's' : ''} con escasez crítica en {data.jurisdiccion}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {escasas.map((s) => (
              <span
                key={s.uri}
                aria-label={`Escasez crítica: ${s.label}`}
                className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700"
              >
                {s.label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Encabezado */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{data.total_ofertas.toLocaleString()} ofertas analizadas</span>
        <span>{data.total_perfiles.toLocaleString()} perfiles en la zona</span>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Skill</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Demanda</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Disponibilidad</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Brecha</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600">Dificultad</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600">Tendencia</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.skills.map((s) => (
              <tr key={s.uri} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{s.label}</td>
                <td className="px-4 py-3 text-right text-gray-700">{s.demanda_pct}%</td>
                <td className="px-4 py-3 text-right text-gray-700">{s.disponibilidad_pct}%</td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={s.brecha > 0 ? 'font-semibold text-red-600' : 'text-green-600'}
                    aria-label={`Brecha de ${s.label}: ${s.brecha > 0 ? '+' : ''}${s.brecha}%`}
                  >
                    {s.brecha > 0 ? '+' : ''}{s.brecha}%
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${difficultyColor[s.dificultad]}`}>
                    {s.dificultad}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="inline-flex justify-center" aria-label={`Tendencia: ${s.tendencia}`}>
                    <TrendIcon t={s.tendencia} />
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
