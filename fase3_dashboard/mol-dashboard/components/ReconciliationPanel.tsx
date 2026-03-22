'use client'

import { CheckCircle, AlertTriangle, RefreshCw } from 'lucide-react'

export interface ReconciliationRow {
  sistema: string
  conteo_local: number
  conteo_remoto: number
  diferencia: number    // local - remoto
  estado: 'ok' | 'diff'
}

interface Props {
  rows: ReconciliationRow[]
  onSyncFaltantes?: () => void
  syncing?: boolean
}

export default function ReconciliationPanel({ rows, onSyncFaltantes, syncing }: Props) {
  const hayDiffs = rows.some((r) => r.estado === 'diff')

  return (
    <div className="space-y-4">
      {/* Tabla comparación */}
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Sistema</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Local (SQLite)</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Remoto (Supabase)</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Diferencia</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row) => (
              <tr key={row.sistema} className={row.estado === 'diff' ? 'bg-amber-50' : ''}>
                <td className="px-4 py-3 font-medium text-gray-800">{row.sistema}</td>
                <td className="px-4 py-3 text-right text-gray-700">
                  {row.conteo_local.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right text-gray-700">
                  {row.conteo_remoto.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right">
                  {row.diferencia === 0 ? (
                    <span className="text-gray-400">—</span>
                  ) : (
                    <span
                      aria-label={`Diferencia en ${row.sistema}: ${row.diferencia > 0 ? '+' : ''}${row.diferencia}`}
                      className="font-semibold text-amber-600"
                    >
                      {row.diferencia > 0 ? '+' : ''}{row.diferencia.toLocaleString()}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {row.estado === 'ok' ? (
                    <span aria-label={`${row.sistema}: sincronizado`}>
                      <CheckCircle className="mx-auto h-4 w-4 text-green-500" />
                    </span>
                  ) : (
                    <span aria-label={`${row.sistema}: diferencia detectada`}>
                      <AlertTriangle className="mx-auto h-4 w-4 text-amber-500" />
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Botón sync */}
      {hayDiffs && (
        <button
          onClick={onSyncFaltantes}
          disabled={syncing}
          aria-label="Sincronizar faltantes"
          className="flex min-h-[44px] items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Sincronizando...' : 'Sincronizar faltantes'}
        </button>
      )}

      {!hayDiffs && (
        <div className="flex items-center gap-2 rounded-xl border border-green-200 bg-green-50 px-4 py-3">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <p className="text-sm text-green-700">Todos los sistemas están sincronizados.</p>
        </div>
      )}
    </div>
  )
}
