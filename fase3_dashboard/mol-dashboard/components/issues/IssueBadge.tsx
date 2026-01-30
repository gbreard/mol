"use client";

import { Badge } from "@/components/ui/badge";
import { IssueType, IssueEstado, IssuePrioridad, ISSUE_TYPE_LABELS, ISSUE_ESTADO_LABELS, ISSUE_PRIORIDAD_LABELS } from "@/lib/types";
import { AlertCircle, FileText, Zap, Lightbulb, Bug, HelpCircle } from "lucide-react";

// Colores para estado
const estadoColors: Record<IssueEstado, string> = {
  pendiente: "bg-yellow-100 text-yellow-800 border-yellow-200",
  en_progreso: "bg-blue-100 text-blue-800 border-blue-200",
  resuelto: "bg-green-100 text-green-800 border-green-200",
  descartado: "bg-gray-100 text-gray-600 border-gray-200",
};

// Colores para prioridad
const prioridadColors: Record<IssuePrioridad, string> = {
  baja: "bg-gray-100 text-gray-600 border-gray-200",
  media: "bg-blue-100 text-blue-700 border-blue-200",
  alta: "bg-orange-100 text-orange-800 border-orange-200",
  critica: "bg-red-100 text-red-800 border-red-200",
};

// Colores para tipo
const tipoColors: Record<IssueType, string> = {
  error_isco: "bg-red-50 text-red-700 border-red-200",
  error_nlp: "bg-purple-50 text-purple-700 border-purple-200",
  error_skill: "bg-orange-50 text-orange-700 border-orange-200",
  sugerencia: "bg-blue-50 text-blue-700 border-blue-200",
  bug: "bg-pink-50 text-pink-700 border-pink-200",
  otro: "bg-gray-50 text-gray-700 border-gray-200",
};

// Iconos para tipo
const tipoIcons: Record<IssueType, React.ReactNode> = {
  error_isco: <AlertCircle className="w-3 h-3" />,
  error_nlp: <FileText className="w-3 h-3" />,
  error_skill: <Zap className="w-3 h-3" />,
  sugerencia: <Lightbulb className="w-3 h-3" />,
  bug: <Bug className="w-3 h-3" />,
  otro: <HelpCircle className="w-3 h-3" />,
};

interface IssueBadgeProps {
  variant: "estado" | "prioridad" | "tipo";
  value: string;
  showIcon?: boolean;
  size?: "sm" | "default";
}

export function IssueBadge({ variant, value, showIcon = true, size = "default" }: IssueBadgeProps) {
  let colorClass = "";
  let label = value;
  let icon: React.ReactNode = null;

  if (variant === "estado") {
    colorClass = estadoColors[value as IssueEstado] || estadoColors.pendiente;
    label = ISSUE_ESTADO_LABELS[value as IssueEstado] || value;
  } else if (variant === "prioridad") {
    colorClass = prioridadColors[value as IssuePrioridad] || prioridadColors.media;
    label = ISSUE_PRIORIDAD_LABELS[value as IssuePrioridad] || value;
  } else if (variant === "tipo") {
    colorClass = tipoColors[value as IssueType] || tipoColors.otro;
    label = ISSUE_TYPE_LABELS[value as IssueType] || value;
    icon = tipoIcons[value as IssueType] || tipoIcons.otro;
  }

  const sizeClass = size === "sm" ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-1";

  return (
    <Badge
      variant="outline"
      className={`${colorClass} ${sizeClass} font-medium border inline-flex items-center gap-1`}
    >
      {showIcon && icon}
      {label}
    </Badge>
  );
}
