'use client'

import { useState } from 'react'
import { TrendingUp, TrendingDown, Minus, BarChart3, AlertCircle } from 'lucide-react'

const SECTORES = ['Tecnología', 'Salud', 'Finanzas', 'Educación', 'Logística', 'Comercio']

const SKILLS_DEMANDA = [
  { skill: 'Inteligencia Artificial', demanda: 94, escasez: 78, tendencia: 'up', variacion: '+22%' },
  { skill: 'Cloud Computing (AWS/GCP)', demanda: 88, escasez: 65, tendencia: 'up', variacion: '+15%' },
  { skill: 'Ciberseguridad', demanda: 82, escasez: 71, tendencia: 'up', variacion: '+19%' },
  { skill: 'Data Analysis (Python/SQL)', demanda: 79, escasez: 42, tendencia: 'up', variacion: '+8%' },
  { skill: 'React / Frontend moderno', demanda: 76, escasez: 38, tendencia: 'flat', variacion: '+2%' },
  { skill: 'DevOps / CI-CD', demanda: 71, escasez: 55, tendencia: 'up', variacion: '+11%' },
  { skill: 'Product Management', demanda: 65, escasez: 30, tendencia: 'flat', variacion: '+1%' },
  { skill: 'UX / Diseño de producto', demanda: 58, escasez: 25, tendencia: 'flat', variacion: '+3%' },
  { skill: 'Java / Backend tradicional', demanda: 45, escasez: 20, tendencia: 'down', variacion: '-5%' },
  { skill: 'Excel / Ofimática', demanda: 38, escasez: 8, tendencia: 'down', variacion: '-12%' },
]

const SALARIOS = [
  { puesto: 'AI/ML Engineer', junior: 350000, senior: 750000, banda: 'alta' },
  { puesto: 'Cloud Architect', junior: 400000, senior: 900000, banda: 'alta' },
  { puesto: 'Data Scientist', junior: 280000, senior: 600000, banda: 'alta' },
  { puesto: 'Desarrollador React', junior: 250000, senior: 500000, banda: 'media' },
  { puesto: 'DevOps Engineer', junior: 300000, senior: 650000, banda: 'alta' },
  { puesto: 'Product Manager', junior: 220000, senior: 480000, banda: 'media' },
  { puesto: 'QA Automation', junior: 180000, senior: 380000, banda: 'media' },
  { puesto: 'UX Designer', junior: 160000, senior: 340000, banda: 'media' },
]

function TendenciaIcon({ t }: { t: string }) {
  if (t === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />
  if (t === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />
  return <Minus className="w-4 h-4 text-gray-400" />
}

function BarScore({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-700 tabular-nums w-8">{value}</span>
    </div>
  )
}

export default function EmpresasBenchmarkPage() {
  const [sector, setSector] = useState('Tecnología')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-5 h-5 text-indigo-500" />
            <h1 className="text-xl font-bold text-gray-900">Benchmark de mercado</h1>
          </div>
          <p className="text-sm text-gray-500">
            Tendencias de skills, escasez y bandas salariales para {sector}.
          </p>
        </div>

        {/* Selector sector */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 mb-6">
          {SECTORES.map((s) => (
            <button
              key={s}
              onClick={() => setSector(s)}
              className={`shrink-0 text-xs font-medium px-3 py-1.5 rounded-full transition-all ${
                sector === s
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-500 hover:border-gray-300'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {sector !== 'Tecnología' && (
          <div className="mb-6 flex items-start gap-2 bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
            <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700">
              Los datos para <strong>{sector}</strong> son estimaciones. La muestra completa estará disponible en la próxima actualización.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Demanda y escasez de skills */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Skills más demandadas</h2>
              <p className="text-xs text-gray-400 mt-0.5">Demanda = cuántas empresas lo buscan · Escasez = dificultad de encontrarlo</p>
            </div>
            <div className="divide-y divide-gray-50">
              {SKILLS_DEMANDA.map((s) => (
                <div key={s.skill} className="px-4 py-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <TendenciaIcon t={s.tendencia} />
                      <span className="text-sm font-medium text-gray-800">{s.skill}</span>
                    </div>
                    <span className={`text-xs font-semibold ${
                      s.variacion.startsWith('+') ? 'text-green-600' : 'text-red-500'
                    }`}>
                      {s.variacion}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-gray-400 w-14">Demanda</span>
                      <BarScore value={s.demanda} color="bg-indigo-400" />
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-gray-400 w-14">Escasez</span>
                      <BarScore
                        value={s.escasez}
                        color={s.escasez >= 60 ? 'bg-red-400' : s.escasez >= 40 ? 'bg-amber-400' : 'bg-green-400'}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bandas salariales */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Bandas salariales</h2>
              <p className="text-xs text-gray-400 mt-0.5">Rango bruto mensual en ARS · Datos de mercado {sector}</p>
            </div>
            <div className="divide-y divide-gray-50">
              {SALARIOS.map((s) => {
                const bandaColor = s.banda === 'alta' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'
                return (
                  <div key={s.puesto} className="px-4 py-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-sm font-medium text-gray-800">{s.puesto}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${bandaColor}`}>
                        {s.banda === 'alta' ? 'Alta demanda' : 'Media demanda'}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-xs text-gray-500">
                        Junior: <span className="font-semibold text-gray-800">
                          ${(s.junior / 1000).toFixed(0)}K
                        </span>
                      </div>
                      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden relative">
                        <div
                          className="absolute h-full bg-indigo-400 rounded-full"
                          style={{
                            left: `${(s.junior / 1000000) * 100}%`,
                            width: `${((s.senior - s.junior) / 1000000) * 100}%`,
                          }}
                        />
                      </div>
                      <div className="text-xs text-gray-500">
                        Senior: <span className="font-semibold text-gray-800">
                          ${(s.senior / 1000).toFixed(0)}K
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
              <p className="text-[10px] text-gray-400">
                * Datos basados en ofertas procesadas por MOL. Actualizado marzo 2026.
                No incluye beneficios adicionales.
              </p>
            </div>
          </div>
        </div>

        {/* Insight box */}
        <div className="mt-6 bg-indigo-900 text-white rounded-xl p-5">
          <div className="flex items-start gap-3">
            <TrendingUp className="w-5 h-5 text-indigo-300 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold mb-1">Insight del mes para {sector}</p>
              <p className="text-xs text-indigo-300 leading-relaxed">
                La demanda de perfiles con skills de IA creció 22% en el último trimestre.
                Sin embargo, la escasez es alta (78/100): hay más búsquedas que candidatos disponibles.
                Si tenés ese tipo de rol abierto, considerá buscar en otras ciudades o perfiles en transición.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
