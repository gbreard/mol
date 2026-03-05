"use client";

import { useState, useCallback, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Loader2, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { OfertaValidacion, ValidacionHumana } from "@/lib/types";
import type {
  WizardCorrecciones,
  WizardTrigger,
  OcupacionCorregida,
  NlpEditado,
  TareaEditada,
  SkillAsociada,
} from "@/lib/wizard-types";
import { OcupacionTab } from "./OcupacionTab";
import { NlpTab } from "./NlpTab";

import { TareasSkillsTab } from "./TareasSkillsTab";

type TabId = "nlp" | "tareas" | "ocupacion";

const DEFAULT_TAB: Record<WizardTrigger, TabId> = {
  error: "ocupacion",
  revisar: "nlp",
  editar: "nlp",
};

interface WizardModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  oferta: OfertaValidacion;
  trigger: WizardTrigger;
  onSave: (
    resultado: ValidacionHumana | null,
    correcciones: WizardCorrecciones
  ) => void;
}

export function WizardModal({
  open,
  onOpenChange,
  oferta,
  trigger,
  onSave,
}: WizardModalProps) {
  const [activeTab, setActiveTab] = useState<TabId>(DEFAULT_TAB[trigger]);
  const [nota, setNota] = useState("");
  const [saving, setSaving] = useState(false);
  const [descExpanded, setDescExpanded] = useState(false);

  // Correction state per tab
  const [ocupacionCorregida, setOcupacionCorregida] = useState<
    OcupacionCorregida | undefined
  >(undefined);
  const [nlpEditado, setNlpEditado] = useState<NlpEditado | undefined>(
    undefined
  );
  const [tareasEditadas, setTareasEditadas] = useState<
    TareaEditada[] | undefined
  >(undefined);
  const [skillsEditadas, setSkillsEditadas] = useState<
    SkillAsociada[] | undefined
  >(undefined);

  // Track dirty tabs for dot indicators
  const dirtyTabs = new Set<TabId>();
  if (ocupacionCorregida) dirtyTabs.add("ocupacion");
  if (nlpEditado && Object.keys(nlpEditado).length > 0) dirtyTabs.add("nlp");
  if (tareasEditadas || skillsEditadas) dirtyTabs.add("tareas");

  const hasAnyCorrection = dirtyTabs.size > 0;

  // Reset state when oferta or trigger changes
  useEffect(() => {
    if (open) {
      setActiveTab(DEFAULT_TAB[trigger]);
      setNota("");
      setDescExpanded(false);
      setOcupacionCorregida(undefined);
      setNlpEditado(undefined);
      setTareasEditadas(undefined);
      setSkillsEditadas(undefined);
    }
  }, [open, oferta.id_oferta, trigger]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const correcciones: WizardCorrecciones = {};
      if (ocupacionCorregida) correcciones.ocupacion_corregida = ocupacionCorregida;
      if (nlpEditado && Object.keys(nlpEditado).length > 0)
        correcciones.nlp_editado = nlpEditado;
      if (tareasEditadas) correcciones.tareas_editadas = tareasEditadas;
      if (skillsEditadas) correcciones.skills_editadas = skillsEditadas;
      if (nota.trim()) correcciones.nota = nota.trim();

      // Determine resultado based on trigger
      let resultado: ValidacionHumana | null = null;
      if (trigger === "error") resultado = "error";
      else if (trigger === "revisar") resultado = "revisar";
      // "editar" → null (keeps current validation state)

      await onSave(resultado, correcciones);
      onOpenChange(false);
    } catch {
      // Error already handled by parent (toast) — wizard stays open
    } finally {
      setSaving(false);
    }
  }, [
    ocupacionCorregida,
    nlpEditado,
    tareasEditadas,
    skillsEditadas,
    nota,
    trigger,
    onSave,
    onOpenChange,
  ]);

  const tabLabel = (id: TabId, label: string) => (
    <span className="flex items-center gap-1.5">
      {label}
      {dirtyTabs.has(id) ? (
        <span className="w-2 h-2 rounded-full bg-blue-600" />
      ) : (
        <span className="w-2 h-2 rounded-full border border-gray-300" />
      )}
    </span>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-4xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-base">
            Corregir:{" "}
            <span className="font-normal text-gray-600">
              {oferta.titulo_limpio || oferta.titulo}
            </span>
          </DialogTitle>
        </DialogHeader>

        {/* Offer context — always visible */}
        <div className="rounded-md border bg-gray-50 px-3 py-2 space-y-1.5 shrink-0">
          <div className="flex items-center gap-2 text-xs text-gray-500 flex-wrap">
            {oferta.empresa && (
              <span className="font-medium text-gray-700">{oferta.empresa}</span>
            )}
            {oferta.portal && (
              <Badge variant="outline" className="text-[10px]">
                {oferta.portal}
              </Badge>
            )}
            {oferta.isco_code && (
              <Badge variant="outline" className="font-mono text-[10px]">
                {oferta.isco_code}
              </Badge>
            )}
            {oferta.esco_occupation_label && (
              <span className="text-gray-500 truncate max-w-[250px]">
                {oferta.esco_occupation_label}
              </span>
            )}
            {oferta.url && (
              <a
                href={oferta.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700 ml-auto shrink-0"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>

          {/* Collapsible description */}
          {oferta.descripcion && (
            <>
              <button
                onClick={() => setDescExpanded(!descExpanded)}
                className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800"
              >
                {descExpanded ? (
                  <ChevronUp className="w-3 h-3" />
                ) : (
                  <ChevronDown className="w-3 h-3" />
                )}
                {descExpanded ? "Ocultar descripcion" : "Ver descripcion"}
              </button>
              {descExpanded && (
                <div className="rounded border bg-white p-2 max-h-[180px] overflow-y-auto">
                  <p className="text-[11px] text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {oferta.descripcion}
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        <Tabs
          value={activeTab}
          onValueChange={(v) => setActiveTab(v as TabId)}
          className="flex-1 flex flex-col min-h-0"
        >
          <TabsList className="w-full justify-start">
            <TabsTrigger value="nlp">{tabLabel("nlp", "NLP")}</TabsTrigger>
            <TabsTrigger value="tareas">
              {tabLabel("tareas", "Tareas & Skills")}
            </TabsTrigger>
            <TabsTrigger value="ocupacion">
              {tabLabel("ocupacion", "Ocupacion")}
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 min-h-0 overflow-y-auto mt-4">
            <TabsContent value="nlp" className="mt-0">
              <NlpTab
                oferta={oferta}
                value={nlpEditado}
                onChange={setNlpEditado}
              />
            </TabsContent>

            <TabsContent value="tareas" className="mt-0">
              <TareasSkillsTab
                oferta={oferta}
                onTareasChange={setTareasEditadas}
                onSkillsChange={setSkillsEditadas}
              />
            </TabsContent>

            <TabsContent value="ocupacion" className="mt-0">
              <OcupacionTab
                oferta={oferta}
                value={ocupacionCorregida}
                onChange={setOcupacionCorregida}
              />
            </TabsContent>
          </div>
        </Tabs>

        {/* Footer: nota + actions */}
        <DialogFooter className="flex-col sm:flex-col gap-2 border-t pt-3">
          <Textarea
            value={nota}
            onChange={(e) => setNota(e.target.value)}
            placeholder="Nota de correccion (opcional)"
            className="text-sm resize-none"
            rows={2}
          />
          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              onClick={() => onOpenChange(false)}
              disabled={saving}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || (!hasAnyCorrection && !nota.trim())}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Guardar correccion
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
