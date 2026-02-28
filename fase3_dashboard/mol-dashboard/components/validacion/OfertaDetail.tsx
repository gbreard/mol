"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ExternalLink } from "lucide-react";
import { OfertaValidacion } from "@/lib/types";
import { OfertaDetailSkills } from "./OfertaDetailSkills";
import { ValidationActions } from "./ValidationActions";

interface OfertaDetailProps {
  oferta: OfertaValidacion;
  onEvaluated?: () => void;
}

function FieldRow({
  label,
  value,
}: {
  label: string;
  value: string | number | null | undefined;
}) {
  if (value == null || value === "") return null;
  return (
    <div className="flex gap-2 py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-xs font-medium text-gray-500 w-[140px] shrink-0">
        {label}
      </span>
      <span className="text-sm text-gray-900 break-words">{String(value)}</span>
    </div>
  );
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-400">-</span>;
  const color =
    score >= 0.7
      ? "bg-green-100 text-green-800"
      : score >= 0.4
        ? "bg-amber-100 text-amber-800"
        : "bg-red-100 text-red-800";
  return (
    <Badge variant="secondary" className={`${color} text-xs tabular-nums`}>
      {score.toFixed(2)}
    </Badge>
  );
}

function MetodoBadge({ metodo }: { metodo: string | null }) {
  if (!metodo) return <span className="text-gray-400">-</span>;
  const color = metodo.includes("regla")
    ? "bg-purple-100 text-purple-800"
    : metodo.includes("semantic")
      ? "bg-blue-100 text-blue-800"
      : "bg-gray-100 text-gray-800";
  return (
    <Badge variant="secondary" className={`${color} text-xs`}>
      {metodo}
    </Badge>
  );
}

export function OfertaDetail({ oferta, onEvaluated }: OfertaDetailProps) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">
            {oferta.titulo_limpio || oferta.titulo}
          </h3>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            <span>#{oferta.id_oferta}</span>
            {oferta.empresa && (
              <>
                <span className="text-gray-300">|</span>
                <span>{oferta.empresa}</span>
              </>
            )}
            {oferta.portal && (
              <>
                <span className="text-gray-300">|</span>
                <Badge variant="outline" className="text-[10px]">
                  {oferta.portal}
                </Badge>
              </>
            )}
          </div>
        </div>
        {oferta.url && (
          <a
            href={oferta.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 shrink-0"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="original" className="w-full">
        <TabsList className="w-full grid grid-cols-4">
          <TabsTrigger value="original" className="text-xs">
            Original
          </TabsTrigger>
          <TabsTrigger value="nlp" className="text-xs">
            NLP
          </TabsTrigger>
          <TabsTrigger value="matching" className="text-xs">
            Matching
          </TabsTrigger>
          <TabsTrigger value="skills" className="text-xs">
            Skills
          </TabsTrigger>
        </TabsList>

        <TabsContent value="original" className="mt-3">
          <div className="space-y-1">
            <FieldRow label="Titulo original" value={oferta.titulo} />
            <FieldRow label="Empresa" value={oferta.empresa} />
            <FieldRow label="Fecha publicacion" value={oferta.fecha_publicacion} />
            <FieldRow label="Portal" value={oferta.portal} />
            <FieldRow label="Provincia" value={oferta.provincia} />
            <FieldRow label="Localidad" value={oferta.localidad} />
            {oferta.descripcion && (
              <div className="pt-2">
                <span className="text-xs font-medium text-gray-500">
                  Descripcion
                </span>
                <ScrollArea className="mt-1 h-[200px] rounded border bg-gray-50 p-3">
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">
                    {oferta.descripcion}
                  </p>
                </ScrollArea>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="nlp" className="mt-3">
          <div className="space-y-1">
            <FieldRow label="Titulo limpio" value={oferta.titulo_limpio} />
            <FieldRow label="Area funcional" value={oferta.area_funcional} />
            <FieldRow label="Seniority" value={oferta.nivel_seniority} />
            <FieldRow label="Sector empresa" value={oferta.sector_empresa} />
            <FieldRow label="Modalidad" value={oferta.modalidad} />
            <FieldRow label="Nivel educativo" value={oferta.nivel_educativo} />
            <FieldRow
              label="Experiencia min"
              value={
                oferta.experiencia_min_anios != null
                  ? `${oferta.experiencia_min_anios} anios`
                  : null
              }
            />
            <FieldRow label="Mision del rol" value={oferta.mision_rol} />
            {oferta.tareas_explicitas && (
              <div className="pt-2">
                <span className="text-xs font-medium text-gray-500">
                  Tareas explicitas
                </span>
                <ScrollArea className="mt-1 h-[150px] rounded border bg-gray-50 p-3">
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">
                    {oferta.tareas_explicitas}
                  </p>
                </ScrollArea>
              </div>
            )}
            {oferta.salario_min != null && (
              <FieldRow
                label="Salario"
                value={`$${oferta.salario_min.toLocaleString()}${oferta.salario_max ? ` - $${oferta.salario_max.toLocaleString()}` : ""}`}
              />
            )}
          </div>
        </TabsContent>

        <TabsContent value="matching" className="mt-3">
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 rounded-lg border">
              <div>
                <span className="text-xs text-gray-500">ISCO</span>
                <div className="font-mono text-lg font-bold text-gray-900">
                  {oferta.isco_code || "-"}
                </div>
                <div className="text-sm text-gray-600">
                  {oferta.isco_label || "-"}
                </div>
              </div>
              <div>
                <span className="text-xs text-gray-500">Score</span>
                <div className="mt-0.5">
                  <ScoreBadge score={oferta.occupation_match_score} />
                </div>
              </div>
            </div>

            <div className="space-y-1">
              <FieldRow label="ESCO URI" value={oferta.esco_occupation_uri} />
              <FieldRow
                label="ESCO label"
                value={oferta.esco_occupation_label}
              />
              <div className="flex gap-2 py-1.5 border-b border-gray-100">
                <span className="text-xs font-medium text-gray-500 w-[140px] shrink-0">
                  Metodo
                </span>
                <MetodoBadge metodo={oferta.occupation_match_method} />
              </div>
              <div className="flex gap-2 py-1.5 border-b border-gray-100">
                <span className="text-xs font-medium text-gray-500 w-[140px] shrink-0">
                  Decision
                </span>
                <MetodoBadge metodo={oferta.decision_metodo} />
              </div>
              <FieldRow label="Regla aplicada" value={oferta.regla_aplicada} />
            </div>

            {/* Skills from arrays */}
            {oferta.skills_tecnicas && (
              <div>
                <span className="text-xs font-medium text-gray-500">
                  Skills tecnicas (NLP)
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {(Array.isArray(oferta.skills_tecnicas)
                    ? oferta.skills_tecnicas
                    : String(oferta.skills_tecnicas).split(/[;,]\s*/).filter(Boolean)
                  ).map((s, i) => (
                    <Badge key={i} variant="secondary" className="text-[10px]">
                      {s}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="skills" className="mt-3">
          <OfertaDetailSkills idOferta={oferta.id_oferta} />
        </TabsContent>
      </Tabs>

      {/* Validation actions */}
      <div className="border-t pt-3">
        <ValidationActions
          idOferta={oferta.id_oferta}
          tituloOferta={oferta.titulo_limpio || oferta.titulo}
          iscoCode={oferta.isco_code}
          onEvaluated={onEvaluated}
        />
      </div>
    </div>
  );
}
