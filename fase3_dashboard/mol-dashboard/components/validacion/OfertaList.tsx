"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { OfertaValidacion, ValidacionHumana } from "@/lib/types";

interface OfertaListProps {
  ofertas: OfertaValidacion[];
  selectedId: string | null;
  onSelect: (oferta: OfertaValidacion) => void;
}

const STATUS_DOT: Record<string, string> = {
  ok: "bg-green-500",
  error: "bg-red-500",
  revisar: "bg-amber-500",
  basura: "bg-gray-400",
};

function StatusDot({ validacion }: { validacion: ValidacionHumana | null }) {
  return (
    <span
      className={`w-2 h-2 rounded-full shrink-0 ${validacion ? STATUS_DOT[validacion] || "bg-gray-200" : "bg-gray-200"}`}
      title={validacion || "pendiente"}
    />
  );
}

export function OfertaList({ ofertas, selectedId, onSelect }: OfertaListProps) {
  if (ofertas.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 text-xs p-4">
        Sin ofertas
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="py-1">
        {ofertas.map((oferta) => {
          const isSelected = oferta.id_oferta === selectedId;
          const score = oferta.occupation_match_score;
          const scoreColor =
            score == null
              ? "text-gray-300"
              : score >= 0.7
                ? "text-green-600"
                : score >= 0.4
                  ? "text-amber-600"
                  : "text-red-600";

          return (
            <button
              key={oferta.id_oferta}
              onClick={() => onSelect(oferta)}
              className={`w-full text-left px-3 py-1.5 flex items-center gap-2 transition-colors text-xs border-b border-gray-50 ${
                isSelected
                  ? "bg-blue-50 border-l-2 border-l-blue-500"
                  : "hover:bg-gray-50 border-l-2 border-l-transparent"
              }`}
            >
              <StatusDot validacion={oferta.validacion_humana} />
              <span className="truncate flex-1 min-w-0">
                {oferta.titulo_limpio || oferta.titulo}
              </span>
              <span className={`tabular-nums shrink-0 ${scoreColor}`}>
                {score != null ? score.toFixed(2) : "-"}
              </span>
            </button>
          );
        })}
      </div>
    </ScrollArea>
  );
}
