'use client'

import { AlertTriangle, XCircle, Info, CheckCircle } from 'lucide-react'

export type AlertLevel = 'error' | 'warning' | 'info' | 'ok'

export interface AlertAction {
  label: string
  comando: string   // comando a enviar via POST /api/scraping-commands
}

export interface SystemAlert {
  id: string
  nivel: AlertLevel
  titulo: string
  detalle?: string
  accion?: AlertAction
}

interface Props {
  alerts: SystemAlert[]
  onAccion?: (alerta: SystemAlert) => void
}

const LEVEL_CONFIG: Record<AlertLevel, { icon: React.ReactNode; bg: string; border: string; text: string }> = {
  error:   { icon: <XCircle className="h-4 w-4 shrink-0" />,       bg: 'bg-red-50',    border: 'border-red-200',   text: 'text-red-700' },
  warning: { icon: <AlertTriangle className="h-4 w-4 shrink-0" />, bg: 'bg-amber-50',  border: 'border-amber-200', text: 'text-amber-700' },
  info:    { icon: <Info className="h-4 w-4 shrink-0" />,          bg: 'bg-blue-50',   border: 'border-blue-200',  text: 'text-blue-700' },
  ok:      { icon: <CheckCircle className="h-4 w-4 shrink-0" />,   bg: 'bg-green-50',  border: 'border-green-200', text: 'text-green-700' },
}

export default function AlertActionList({ alerts, onAccion }: Props) {
  if (alerts.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-green-200 bg-green-50 px-4 py-3">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <p className="text-sm text-green-700">Todos los sistemas operativos.</p>
      </div>
    )
  }

  return (
    <ul className="space-y-2">
      {alerts.map((alert) => {
        const cfg = LEVEL_CONFIG[alert.nivel]
        return (
          <li
            key={alert.id}
            aria-label={`Alerta ${alert.nivel}: ${alert.titulo}`}
            className={`flex items-start justify-between gap-3 rounded-xl border px-4 py-3 ${cfg.bg} ${cfg.border}`}
          >
            <div className="flex min-w-0 flex-1 items-start gap-2">
              <span className={cfg.text}>{cfg.icon}</span>
              <div className="min-w-0">
                <p className={`text-sm font-medium ${cfg.text}`}>{alert.titulo}</p>
                {alert.detalle && (
                  <p className="text-xs text-gray-500 mt-0.5">{alert.detalle}</p>
                )}
              </div>
            </div>

            {alert.accion && (
              <button
                onClick={() => onAccion?.(alert)}
                aria-label={`Acción: ${alert.accion.label}`}
                className="flex min-h-[44px] shrink-0 items-center rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
              >
                {alert.accion.label}
              </button>
            )}
          </li>
        )
      })}
    </ul>
  )
}
