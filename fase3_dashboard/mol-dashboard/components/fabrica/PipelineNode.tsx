"use client";

import { Loader2 } from "lucide-react";
import { type LucideIcon } from "lucide-react";

export interface PipelineNodeAction {
  label: string;
  icon?: LucideIcon;
  onClick: () => void;
  variant?: "primary" | "secondary" | "warning";
  disabled?: boolean;
  loading?: boolean;
}

export interface PipelineNodeProps {
  id: string;
  label: string;
  subtitle?: string;
  icon: LucideIcon;
  status: "ok" | "warning" | "error" | "idle";
  metric: string | number;
  metricLabel: string;
  actions: PipelineNodeAction[];
  onClick?: () => void;
  highlight?: boolean;
}

const STATUS_STYLES = {
  ok: "border-green-300 bg-green-50",
  warning: "border-amber-300 bg-amber-50",
  error: "border-red-300 bg-red-50",
  idle: "border-gray-200 bg-gray-50",
};

const STATUS_DOT = {
  ok: "bg-green-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
  idle: "bg-gray-400",
};

const ACTION_STYLES = {
  primary: "bg-blue-600 text-white hover:bg-blue-700",
  secondary: "bg-gray-100 text-gray-700 hover:bg-gray-200",
  warning: "bg-amber-500 text-white hover:bg-amber-600",
};

export function PipelineNode({
  id, label, subtitle, icon: Icon, status, metric, metricLabel,
  actions, onClick, highlight,
}: PipelineNodeProps) {
  return (
    <div
      data-testid={`pipeline-node-${id}`}
      className={`rounded-xl border-2 p-4 min-w-[160px] transition-all ${STATUS_STYLES[status]} ${
        highlight ? "ring-2 ring-blue-400 ring-offset-2" : ""
      } ${onClick ? "cursor-pointer hover:shadow-md" : ""}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${STATUS_DOT[status]}`} />
        <Icon className="w-4 h-4 text-gray-500" />
        <span className="text-sm font-semibold text-gray-900">{label}</span>
      </div>

      {/* Subtitle */}
      {subtitle && (
        <div className="text-xs text-gray-500 mb-2">{subtitle}</div>
      )}

      {/* Metric */}
      <div className="mb-3">
        <div className="text-2xl font-bold text-gray-900">{metric}</div>
        <div className="text-xs text-gray-500">{metricLabel}</div>
      </div>

      {/* Actions */}
      {actions.length > 0 && (
        <div className="flex flex-wrap gap-1" onClick={(e) => e.stopPropagation()}>
          {actions.map((action, i) => {
            const ActionIcon = action.icon;
            return (
              <button
                key={i}
                onClick={action.onClick}
                disabled={action.disabled || action.loading}
                className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors disabled:opacity-50 ${
                  ACTION_STYLES[action.variant || "secondary"]
                }`}
                title={action.label}
              >
                {action.loading ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : ActionIcon ? (
                  <ActionIcon className="w-3 h-3" />
                ) : null}
                {action.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Arrow connector between nodes
export function PipelineArrow() {
  return (
    <div className="flex items-center justify-center px-1 self-center">
      <svg width="24" height="16" viewBox="0 0 24 16" className="text-gray-300">
        <path d="M0 8h20M16 3l5 5-5 5" fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
    </div>
  );
}
