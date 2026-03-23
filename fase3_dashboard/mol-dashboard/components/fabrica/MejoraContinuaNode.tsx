"use client";

import { type LucideIcon } from "lucide-react";

export interface MejoraContinuaNodeProps {
  id: string;
  label: string;
  icon: LucideIcon;
  status: "ok" | "warning" | "action-needed" | "idle";
  metric: string | number;
  metricLabel: string;
  actions: {
    label: string;
    icon?: LucideIcon;
    onClick: () => void;
  }[];
  onClick?: () => void;
}

const STATUS_STYLES = {
  ok: "border-green-200 bg-green-50/50",
  warning: "border-amber-200 bg-amber-50/50",
  "action-needed": "border-blue-200 bg-blue-50/50",
  idle: "border-gray-200 bg-gray-50/50",
};

const STATUS_DOT = {
  ok: "bg-green-400",
  warning: "bg-amber-400",
  "action-needed": "bg-blue-400 animate-pulse",
  idle: "bg-gray-300",
};

export function MejoraContinuaNode({
  id, label, icon: Icon, status, metric, metricLabel, actions, onClick,
}: MejoraContinuaNodeProps) {
  return (
    <div
      data-testid={`mejora-node-${id}`}
      className={`rounded-lg border p-3 min-w-[130px] transition-all ${STATUS_STYLES[status]} ${
        onClick ? "cursor-pointer hover:shadow-sm" : ""
      }`}
      onClick={onClick}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <div className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[status]}`} />
        <Icon className="w-3.5 h-3.5 text-gray-400" />
        <span className="text-xs font-medium text-gray-700">{label}</span>
      </div>

      <div className="mb-2">
        <div className="text-lg font-bold text-gray-800">{metric}</div>
        <div className="text-xs text-gray-400">{metricLabel}</div>
      </div>

      {actions.length > 0 && (
        <div className="flex flex-wrap gap-1" onClick={(e) => e.stopPropagation()}>
          {actions.map((action, i) => {
            const ActionIcon = action.icon;
            return (
              <button
                key={i}
                onClick={action.onClick}
                className="flex items-center gap-1 px-1.5 py-0.5 rounded text-xs text-gray-500 hover:bg-white/80 transition-colors"
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

// Arrow for mejora continua line (lighter)
export function MejoraArrow() {
  return (
    <div className="flex items-center justify-center px-0.5 self-center">
      <svg width="20" height="12" viewBox="0 0 20 12" className="text-gray-200">
        <path d="M0 6h16M13 2l4 4-4 4" fill="none" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    </div>
  );
}
