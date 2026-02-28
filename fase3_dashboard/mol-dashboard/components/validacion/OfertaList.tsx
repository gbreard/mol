"use client";

import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { OfertaValidacion } from "@/lib/types";

interface OfertaListProps {
  ofertas: OfertaValidacion[];
  selectedId: string | null;
  onSelect: (oferta: OfertaValidacion) => void;
}

function ScoreDot({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-300">-</span>;
  const color =
    score >= 0.7
      ? "text-green-600"
      : score >= 0.4
        ? "text-amber-600"
        : "text-red-600";
  return <span className={`${color} tabular-nums text-xs`}>{score.toFixed(2)}</span>;
}

function MetodoTag({ metodo }: { metodo: string | null }) {
  if (!metodo) return null;
  const short = metodo.includes("regla")
    ? "regla"
    : metodo.includes("semantic")
      ? "sem"
      : metodo.slice(0, 5);
  const color = metodo.includes("regla")
    ? "bg-purple-50 text-purple-700 border-purple-200"
    : "bg-blue-50 text-blue-700 border-blue-200";
  return (
    <Badge variant="outline" className={`text-[9px] ${color}`}>
      {short}
    </Badge>
  );
}

export function OfertaList({ ofertas, selectedId, onSelect }: OfertaListProps) {
  if (ofertas.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        No se encontraron ofertas con los filtros seleccionados
      </div>
    );
  }

  return (
    <ScrollArea className="h-[250px]">
      <table className="w-full text-xs">
        <thead className="sticky top-0 bg-white z-10">
          <tr className="border-b text-gray-500 font-medium">
            <th className="text-left py-1.5 px-2 w-[100px]">ID</th>
            <th className="text-left py-1.5 px-2">Titulo limpio</th>
            <th className="text-left py-1.5 px-2 w-[60px]">ISCO</th>
            <th className="text-right py-1.5 px-2 w-[55px]">Score</th>
            <th className="text-left py-1.5 px-2 w-[55px]">Metodo</th>
          </tr>
        </thead>
        <tbody>
          {ofertas.map((oferta) => {
            const isSelected = oferta.id_oferta === selectedId;
            return (
              <tr
                key={oferta.id_oferta}
                onClick={() => onSelect(oferta)}
                className={`cursor-pointer border-b transition-colors ${
                  isSelected
                    ? "bg-blue-50 border-blue-200"
                    : "hover:bg-gray-50"
                }`}
              >
                <td className="py-1.5 px-2 font-mono text-gray-500">
                  {oferta.id_oferta.slice(-6)}
                </td>
                <td className="py-1.5 px-2 truncate max-w-[300px]">
                  {oferta.titulo_limpio || oferta.titulo}
                </td>
                <td className="py-1.5 px-2 font-mono font-medium">
                  {oferta.isco_code || "-"}
                </td>
                <td className="py-1.5 px-2 text-right">
                  <ScoreDot score={oferta.occupation_match_score} />
                </td>
                <td className="py-1.5 px-2">
                  <MetodoTag metodo={oferta.occupation_match_method} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </ScrollArea>
  );
}
