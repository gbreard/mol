"use client";

import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { OfertaValidacion, METODO_LABELS } from "@/lib/types";
import { OfertaDetailSkills } from "./OfertaDetailSkills";

interface ClasificacionPanelProps {
  oferta: OfertaValidacion;
}

function ScoreBar({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-400 text-sm">-</span>;
  const pct = Math.round(score * 100);
  const color =
    score >= 0.7
      ? "bg-green-500"
      : score >= 0.4
        ? "bg-amber-500"
        : "bg-red-500";
  const textColor =
    score >= 0.7
      ? "text-green-700"
      : score >= 0.4
        ? "text-amber-700"
        : "text-red-700";
  return (
    <div className="flex items-center gap-2">
      <span className={`text-sm font-bold tabular-nums ${textColor}`}>
        {score.toFixed(2)}
      </span>
      <div className="flex-1 h-2 bg-gray-200 rounded-full max-w-[100px]">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function MetodoBadge({ metodo }: { metodo: string | null }) {
  if (!metodo) return <span className="text-gray-400">-</span>;
  const info = METODO_LABELS[metodo];
  const label = info?.label || metodo;
  const description = info?.description || metodo;

  const color = metodo.includes("regla")
    ? "bg-purple-100 text-purple-800 border-purple-200"
    : metodo.includes("dual")
      ? "bg-green-100 text-green-800 border-green-200"
      : metodo === "error"
        ? "bg-red-100 text-red-800 border-red-200"
        : "bg-blue-100 text-blue-800 border-blue-200";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`text-[11px] cursor-help ${color}`}>
            {label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-[250px]">
          <p className="text-xs">{description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function ClasificacionPanel({ oferta }: ClasificacionPanelProps) {
  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        {/* ISCO hero */}
        <div className="text-center p-4 bg-gray-50 rounded-lg border">
          <div className="font-mono text-3xl font-black text-gray-900">
            {oferta.isco_code || "-"}
          </div>
          <div className="text-sm text-gray-600 mt-1">
            {oferta.isco_label || "Sin clasificacion"}
          </div>
        </div>

        {/* Score + Metodo */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <span className="text-xs text-gray-500">Score</span>
            <div className="mt-0.5">
              <ScoreBar score={oferta.occupation_match_score} />
            </div>
          </div>
          <div>
            <span className="text-xs text-gray-500">Metodo</span>
            <div className="mt-1">
              <MetodoBadge metodo={oferta.decision_metodo} />
            </div>
          </div>
        </div>
        {/* Descripcion del metodo — siempre visible */}
        {oferta.decision_metodo && (
          <p className="text-[11px] text-gray-500 italic bg-gray-50 rounded px-2 py-1">
            {METODO_LABELS[oferta.decision_metodo]?.description || oferta.decision_metodo}
          </p>
        )}

        {/* ESCO details */}
        <div className="space-y-1 text-xs">
          {oferta.esco_occupation_label && (
            <div className="flex gap-2 py-1">
              <span className="font-medium text-gray-500 w-[80px] shrink-0">ESCO</span>
              <span className="text-gray-900">{oferta.esco_occupation_label}</span>
            </div>
          )}
          {oferta.regla_aplicada && (
            <div className="flex gap-2 py-1">
              <span className="font-medium text-gray-500 w-[80px] shrink-0">Regla</span>
              <span className="text-gray-900 font-mono text-[11px]">{oferta.regla_aplicada}</span>
            </div>
          )}
          {oferta.clae_descripcion_seccion && (
            <div className="flex gap-2 py-1">
              <span className="font-medium text-gray-500 w-[80px] shrink-0">CLAE</span>
              <span className="text-gray-900">{oferta.clae_descripcion_seccion}</span>
            </div>
          )}
          {oferta.sector_empresa && (
            <div className="flex gap-2 py-1">
              <span className="font-medium text-gray-500 w-[80px] shrink-0">Sector NLP</span>
              <span className="text-gray-500 italic">{oferta.sector_empresa}</span>
            </div>
          )}
        </div>

        {/* Skills ESCO */}
        <div>
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Skills ESCO
          </span>
          <div className="mt-2">
            <OfertaDetailSkills idOferta={oferta.id_oferta} />
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}
