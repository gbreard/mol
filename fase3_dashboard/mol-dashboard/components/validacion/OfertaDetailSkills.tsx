"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getSkillsByOferta } from "@/lib/supabase";
import { OfertaSkillValidacion } from "@/lib/types";

interface OfertaDetailSkillsProps {
  idOferta: string;
}

export function OfertaDetailSkills({ idOferta }: OfertaDetailSkillsProps) {
  const [skills, setSkills] = useState<OfertaSkillValidacion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getSkillsByOferta(idOferta)
      .then(setSkills)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [idOferta]);

  if (loading) {
    return (
      <div className="space-y-2 p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </div>
    );
  }

  if (skills.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        Sin skills clasificadas para esta oferta
      </div>
    );
  }

  return (
    <div className="overflow-auto max-h-[400px]">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="text-xs">Skill</TableHead>
            <TableHead className="text-xs w-[120px]">Categoria L1</TableHead>
            <TableHead className="text-xs w-[80px]">Origen</TableHead>
            <TableHead className="text-xs w-[60px] text-right">Score</TableHead>
            <TableHead className="text-xs w-[70px]">Tipo</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {skills.map((skill) => (
            <TableRow key={skill.id} className="text-xs">
              <TableCell className="font-medium py-1.5">
                {skill.preferred_label}
                {skill.es_digital && (
                  <Badge
                    variant="secondary"
                    className="ml-1.5 text-[9px] bg-blue-100 text-blue-700"
                  >
                    digital
                  </Badge>
                )}
              </TableCell>
              <TableCell className="py-1.5 text-gray-600">
                {skill.l1_nombre || skill.l1 || "-"}
              </TableCell>
              <TableCell className="py-1.5">
                <Badge
                  variant="outline"
                  className="text-[10px]"
                >
                  {skill.origen || "sem"}
                </Badge>
              </TableCell>
              <TableCell className="py-1.5 text-right tabular-nums">
                {skill.score != null
                  ? skill.score.toFixed(2)
                  : "-"}
              </TableCell>
              <TableCell className="py-1.5">
                {skill.es_esencial ? (
                  <Badge className="text-[10px] bg-green-100 text-green-700 border-green-200">
                    esencial
                  </Badge>
                ) : (
                  <span className="text-gray-400">opcional</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
