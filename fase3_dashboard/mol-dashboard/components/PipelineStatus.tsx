'use client'

import { CheckCircle, XCircle, AlertTriangle, Loader2, ArrowRight } from 'lucide-react'

export type NodeStatus = 'ok' | 'error' | 'warning' | 'loading' | 'unknown'

export interface PipelineNode {
  id: string
  label: string
  sublabel?: string       // info adicional (ej: "16.432 ofertas")
  status: NodeStatus
  detalle?: string        // tooltip / descripción del estado
}

interface Props {
  nodes: PipelineNode[]
}

const STATUS_CONFIG: Record<NodeStatus, { icon: React.ReactNode; color: string; bg: string; border: string }> = {
  ok:      { icon: <CheckCircle className="h-5 w-5" />, color: 'text-green-600',  bg: 'bg-green-50',  border: 'border-green-200' },
  error:   { icon: <XCircle className="h-5 w-5" />,    color: 'text-red-600',    bg: 'bg-red-50',    border: 'border-red-200' },
  warning: { icon: <AlertTriangle className="h-5 w-5" />, color: 'text-amber-500', bg: 'bg-amber-50', border: 'border-amber-200' },
  loading: { icon: <Loader2 className="h-5 w-5 animate-spin" />, color: 'text-blue-500', bg: 'bg-blue-50', border: 'border-blue-200' },
  unknown: { icon: <AlertTriangle className="h-5 w-5" />, color: 'text-gray-400', bg: 'bg-gray-50',  border: 'border-gray-200' },
}

export default function PipelineStatus({ nodes }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {nodes.map((node, i) => {
        const cfg = STATUS_CONFIG[node.status]
        return (
          <div key={node.id} className="flex items-center gap-2">
            {/* Nodo */}
            <div
              aria-label={`${node.label}: ${node.status}${node.detalle ? ' — ' + node.detalle : ''}`}
              title={node.detalle}
              className={`flex min-w-[110px] flex-col items-center rounded-xl border px-4 py-3 ${cfg.bg} ${cfg.border}`}
            >
              <span className={cfg.color}>{cfg.icon}</span>
              <p className="mt-1.5 text-xs font-semibold text-gray-800">{node.label}</p>
              {node.sublabel && (
                <p className="text-[10px] text-gray-500 mt-0.5">{node.sublabel}</p>
              )}
            </div>

            {/* Flecha entre nodos */}
            {i < nodes.length - 1 && (
              <ArrowRight className="h-4 w-4 shrink-0 text-gray-300" aria-hidden />
            )}
          </div>
        )
      })}
    </div>
  )
}
