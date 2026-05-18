'use client'

import { TrendingDown, BookOpen, CheckCircle, XCircle } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

export interface RuleEvent {
  fecha: string
  regla_id: string
  tipo: 'creada' | 'modificada' | 'desactivada'
  descripcion: string
}

export interface ErrorRatePoint {
  fecha: string
  tasa_error: number   // %
  total_procesadas: number
}

export interface GoldSetResult {
  oferta_id: number
  titulo: string
  isco_esperado: string
  isco_obtenido: string
  correcto: boolean
  score: number
}

export interface LearningData {
  total_reglas_activas: number
  total_reglas_creadas: number
  tasa_error_actual: number
  tasa_error_inicial: number
  timeline_errores: ErrorRatePoint[]
  timeline_reglas: RuleEvent[]
  gold_set: GoldSetResult[]
}

interface Props {
  data: LearningData
}

export default function LearningDashboard({ data }: Props) {
  const goldOk = data.gold_set.filter((r) => r.correcto).length
  const goldTotal = data.gold_set.length
  const goldPct = goldTotal > 0 ? Math.round((goldOk / goldTotal) * 100) : 0
  const mejora = data.tasa_error_inicial - data.tasa_error_actual

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-2xl font-bold text-blue-600">{data.total_reglas_activas}</p>
          <p className="text-xs text-gray-500 mt-1">Reglas activas</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-2xl font-bold text-gray-700">{data.total_reglas_creadas}</p>
          <p className="text-xs text-gray-500 mt-1">Reglas creadas (total)</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{data.tasa_error_actual}%</p>
          <p className="text-xs text-gray-500 mt-1">Tasa error actual</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <p className="text-2xl font-bold text-emerald-600">−{mejora.toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">Mejora desde inicio</p>
        </div>
      </div>

      {/* Gráfico evolución tasa de error */}
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <h3 className="mb-4 text-sm font-semibold text-gray-800">Evolución tasa de error</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data.timeline_errores}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
            <YAxis unit="%" tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: number) => [`${v}%`, 'Tasa error']} />
            <Line
              type="monotone"
              dataKey="tasa_error"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="Tasa error"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Timeline de reglas */}
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-800">
          Timeline de reglas ({data.timeline_reglas.length})
        </h3>
        {data.timeline_reglas.length === 0 ? (
          <p className="text-sm text-gray-400 italic">
            Sin historial de reglas registrado. Se mostrarán eventos cuando se versionen los cambios en config_overrides.
          </p>
        ) : (
          <ul className="space-y-2 max-h-48 overflow-y-auto">
            {data.timeline_reglas.map((e, i) => (
              <li key={i} className="flex items-center gap-3 text-sm">
                <span className="text-xs text-gray-400 shrink-0 w-20">{e.fecha}</span>
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${
                    e.tipo === 'creada'
                      ? 'bg-green-100 text-green-700'
                      : e.tipo === 'modificada'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {e.tipo}
                </span>
                <span className="text-gray-700 truncate">{e.descripcion}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Gold Set */}
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-800">
            Gold Set <span className="font-normal text-gray-400">({goldTotal} casos)</span>
          </h3>
          {goldTotal > 0 && (
            <span
              aria-label={`Gold Set: ${goldPct}% correctos`}
              className={`rounded-full px-3 py-1 text-sm font-bold ${
                goldPct >= 95
                  ? 'bg-green-100 text-green-700'
                  : goldPct >= 80
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-red-100 text-red-700'
              }`}
            >
              {goldPct}% correctos
            </span>
          )}
        </div>

        {goldTotal === 0 ? (
          <p className="text-sm text-gray-400 italic">
            Sin gold set conectado. Se mostrarán casos cuando se persistan validaciones humanas como referencia.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Título</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Esperado</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Obtenido</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-600">OK</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.gold_set.map((r) => (
                  <tr key={r.oferta_id} className={r.correcto ? '' : 'bg-red-50'}>
                    <td className="px-3 py-2 text-gray-800 max-w-[180px] truncate">{r.titulo}</td>
                    <td className="px-3 py-2 text-gray-600">{r.isco_esperado}</td>
                    <td className="px-3 py-2 text-gray-600">{r.isco_obtenido}</td>
                    <td className="px-3 py-2 text-center">
                      {r.correcto
                        ? <CheckCircle className="h-4 w-4 text-green-500 mx-auto" />
                        : <XCircle className="h-4 w-4 text-red-500 mx-auto" />
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
