/**
 * Badge de estado de propagación. SPEC T Fase 4.
 * Aparece en lista y detalle de issues. Read-only — no aplica acciones.
 */
"use client";

import type { Issue, PropagationEstado } from "@/lib/types";

interface Props {
  issue: Pick<Issue, "estado" | "patron_corregido" | "propagacion_n" | "propagacion_solicitada">;
  size?: "sm" | "md";
}

export function getPropagationEstado(
  issue: Pick<Issue, "estado" | "patron_corregido" | "propagacion_n" | "propagacion_solicitada">
): PropagationEstado | null {
  // Solo aplica a resueltos
  if (issue.estado !== "resuelto") {
    if (issue.propagacion_solicitada) return "solicitada";
    return null;
  }

  if (issue.propagacion_solicitada && (!issue.propagacion_n || issue.propagacion_n === 0)) {
    return "solicitada";
  }
  if (issue.propagacion_n && issue.propagacion_n > 0) {
    return "aplicada";
  }
  if (issue.patron_corregido) {
    // Tiene patrón pero N=0 → puntual
    const audit = issue.patron_corregido as { _audit_note?: string };
    if (audit._audit_note) return "sin_auditar";
    return "excepcion";
  }
  return "sin_auditar";
}

const STYLES: Record<PropagationEstado, { icon: string; label: string; cls: string; tooltip: string }> = {
  aplicada: {
    icon: "✅",
    label: "+",
    cls: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    tooltip: "Esta corrección ya se propagó a otras ofertas similares.",
  },
  excepcion: {
    icon: "➡",
    label: "Excepción",
    cls: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
    tooltip: "Caso puntual: la corrección NO aplica a otras ofertas similares.",
  },
  solicitada: {
    icon: "🟡",
    label: "Solicitada",
    cls: "bg-amber-100 text-amber-900 dark:bg-amber-900 dark:text-amber-100",
    tooltip: "Pediste que se propague pero el admin todavía no lo procesó.",
  },
  sin_auditar: {
    icon: "⚠",
    label: "Sin auditar",
    cls: "bg-orange-100 text-orange-900 dark:bg-orange-900 dark:text-orange-100",
    tooltip:
      "Issue cerrado antes del sistema de propagación. Si creés que aplica a otras ofertas, podés solicitarlo.",
  },
};

export function PropagationBadge({ issue, size = "sm" }: Props) {
  const estado = getPropagationEstado(issue);
  if (!estado) return null;

  const style = STYLES[estado];
  const padding = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";

  const label =
    estado === "aplicada"
      ? `+${issue.propagacion_n ?? 0}`
      : style.label;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${padding} ${style.cls}`}
      title={style.tooltip}
    >
      <span>{style.icon}</span>
      <span>{label}</span>
    </span>
  );
}
