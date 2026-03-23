"use client";

import { Shield, type LucideIcon } from "lucide-react";

export interface PipelineGateProps {
  id: string;
  label: string;
  rulesCount: number;
  approvedPct: number;
  blockedCount: number;
  errorsCount: number;
  actions: {
    label: string;
    icon?: LucideIcon;
    onClick: () => void;
  }[];
}

export function PipelineGate({
  id, label, rulesCount, approvedPct, blockedCount, errorsCount, actions,
}: PipelineGateProps) {
  const status = errorsCount > 0 || blockedCount > 10 ? "warning" : "ok";

  return (
    <div
      data-testid={`pipeline-gate-${id}`}
      className={`rounded-lg border-2 border-dashed p-3 min-w-[140px] ${
        status === "warning"
          ? "border-amber-300 bg-amber-50/50"
          : "border-green-300 bg-green-50/50"
      }`}
    >
      <div className="flex items-center gap-1.5 mb-1.5">
        <Shield className={`w-3.5 h-3.5 ${status === "warning" ? "text-amber-500" : "text-green-500"}`} />
        <span className="text-xs font-semibold text-gray-700">{label}</span>
      </div>

      <div className="space-y-0.5 text-xs mb-2">
        <div className="text-gray-500">{rulesCount} reglas</div>
        <div className={approvedPct >= 95 ? "text-green-600" : "text-amber-600"}>
          {approvedPct}% aprobado
        </div>
        {blockedCount > 0 && (
          <div className="text-red-500">{blockedCount} bloqueados</div>
        )}
        {errorsCount > 0 && (
          <div className="text-amber-600">{errorsCount} errores</div>
        )}
      </div>

      {actions.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {actions.map((action, i) => {
            const ActionIcon = action.icon;
            return (
              <button
                key={i}
                onClick={action.onClick}
                className="flex items-center gap-1 px-1.5 py-0.5 rounded text-xs text-gray-600 hover:bg-white/80 transition-colors"
                title={action.label}
              >
                {ActionIcon && <ActionIcon className="w-3 h-3" />}
                {action.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
