"use client";

import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ExternalLink } from "lucide-react";
import { OfertaValidacion } from "@/lib/types";

interface PuestoPanelProps {
  oferta: OfertaValidacion;
}

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value == null || value === "") return null;
  return (
    <div className="flex gap-2 py-1 text-xs lg:text-sm">
      <span className="font-medium text-gray-500 w-[100px] lg:w-[120px] shrink-0">{label}</span>
      <span className="text-gray-900 break-words min-w-0">{String(value)}</span>
    </div>
  );
}

export function PuestoPanel({ oferta }: PuestoPanelProps) {
  const salario =
    oferta.salario_min != null
      ? `$${oferta.salario_min.toLocaleString()}${oferta.salario_max ? ` - $${oferta.salario_max.toLocaleString()}` : ""}`
      : null;

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        {/* Title */}
        <div>
          <div className="flex items-start justify-between gap-2">
            <h2 className="text-lg font-bold text-gray-900 leading-tight">
              {oferta.titulo_limpio || oferta.titulo}
            </h2>
            {oferta.url && (
              <a
                href={oferta.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 shrink-0 mt-0.5"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1 text-xs lg:text-sm text-gray-500 flex-wrap">
            {oferta.empresa && <span>{oferta.empresa}</span>}
            {oferta.portal && (
              <Badge variant="outline" className="text-[10px] lg:text-xs">
                {oferta.portal}
              </Badge>
            )}
            {oferta.matching_version && (
              <Badge
                variant="outline"
                className="text-[10px] lg:text-xs font-mono text-gray-400 border-gray-200"
                title={oferta.run_id ? `Run: ${oferta.run_id}` : undefined}
              >
                Matcher: {oferta.matching_version}
              </Badge>
            )}
            {oferta.fecha_publicacion && (
              <span className="text-gray-400">{oferta.fecha_publicacion}</span>
            )}
          </div>
        </div>

        {/* Description */}
        {oferta.descripcion && (
          <div>
            <span className="text-xs lg:text-sm font-medium text-gray-500">Descripcion</span>
            <div className="mt-1 rounded border bg-gray-50 p-3 max-h-[250px] overflow-y-auto">
              <p className="text-xs lg:text-sm text-gray-800 whitespace-pre-wrap leading-relaxed break-words">
                {oferta.descripcion}
              </p>
            </div>
          </div>
        )}

        {/* NLP Fields */}
        <div className="space-y-0.5">
          <span className="text-xs lg:text-sm font-medium text-gray-400 uppercase tracking-wider">NLP</span>
          <Field label="Area" value={oferta.area_funcional} />
          <Field label="Seniority" value={oferta.nivel_seniority} />
          <Field label="Modalidad" value={oferta.modalidad} />
          <Field label="Sector" value={oferta.sector_empresa} />
          <Field label="Educacion" value={oferta.nivel_educativo} />
          <Field label="Experiencia" value={oferta.experiencia_min_anios != null ? `${oferta.experiencia_min_anios} anios` : null} />
          <Field label="Salario" value={salario} />
          <Field label="Provincia" value={oferta.provincia} />
          <Field label="Localidad" value={oferta.localidad} />
          <Field label="Mision" value={oferta.mision_rol} />
        </div>

        {/* Tasks */}
        {oferta.tareas_explicitas && (
          <div>
            <span className="text-xs lg:text-sm font-medium text-gray-500">Tareas</span>
            <div className="mt-1 rounded border bg-gray-50 p-2 max-h-[150px] overflow-y-auto">
              <p className="text-xs lg:text-sm text-gray-800 whitespace-pre-wrap break-words">
                {oferta.tareas_explicitas}
              </p>
            </div>
          </div>
        )}

        {/* Skills tecnicas from NLP */}
        {oferta.skills_tecnicas && oferta.skills_tecnicas.length > 0 && (
          <div>
            <span className="text-xs lg:text-sm font-medium text-gray-500">Skills tecnicas (NLP)</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {(Array.isArray(oferta.skills_tecnicas)
                ? oferta.skills_tecnicas
                : String(oferta.skills_tecnicas).split(/[;,]\s*/).filter(Boolean)
              ).map((s, i) => (
                <Badge key={i} variant="secondary" className="text-[10px] lg:text-xs">
                  {s}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* ID */}
        <div className="text-[10px] lg:text-xs text-gray-400 font-mono pt-2 border-t">
          #{oferta.id_oferta}
        </div>
      </div>
    </ScrollArea>
  );
}
