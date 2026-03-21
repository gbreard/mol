"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Check, X, AlertTriangle, Trash2, Loader2, Pencil } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { saveValidacion, createIssue } from "@/lib/supabase";
import { createBrowserClient } from "@/lib/supabase/browser";
import { OfertaValidacion, ValidacionHumana } from "@/lib/types";
import type { WizardCorrecciones, WizardTrigger } from "@/lib/wizard-types";
import { toast } from "sonner";
import { WizardModal } from "./wizard/WizardModal";

function extractErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "object" && err !== null) {
    const obj = err as Record<string, unknown>;
    // Supabase errors: { message, code, details, hint }
    if (typeof obj.message === "string") return obj.message;
    // PostgrestError
    if (typeof obj.code === "string" && typeof obj.details === "string")
      return `${obj.code}: ${obj.details}`;
    return JSON.stringify(err);
  }
  return String(err);
}

interface ValidationActionsProps {
  idOferta: string;
  tituloOferta: string;
  iscoCode: string | null;
  currentValidacion: ValidacionHumana | null;
  oferta: OfertaValidacion;
  onEvaluated: (resultado: ValidacionHumana) => void;
}

export function ValidationActions({
  idOferta,
  tituloOferta,
  iscoCode,
  currentValidacion,
  oferta,
  onEvaluated,
}: ValidationActionsProps) {
  const [saving, setSaving] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardTrigger, setWizardTrigger] = useState<WizardTrigger>("editar");
  const [confirmAction, setConfirmAction] = useState<ValidacionHumana | null>(null);

  // Close wizard when oferta changes
  useEffect(() => {
    setWizardOpen(false);
  }, [idOferta]);

  /** Returns true on success, false on error */
  const doSave = useCallback(
    async (
      resultado: ValidacionHumana,
      correcciones?: Record<string, unknown>
    ): Promise<boolean> => {
      setSaving(true);
      try {
        await saveValidacion(idOferta, resultado, correcciones);

        // Create issue for error/revisar/editar corrections
        if (resultado === "error" || resultado === "revisar") {
          try {
            const supabase = createBrowserClient();
            const {
              data: { user },
            } = await supabase.auth.getUser();
            if (!user) {
              toast.error("Issue no creado: usuario no autenticado", { duration: 6000 });
            }
            if (user) {
              const hasCorrecciones = correcciones && Object.keys(correcciones).length > 0;
              const tipo =
                resultado === "error" ? "error_isco" : "sugerencia";
              const titulo =
                resultado === "error"
                  ? `ISCO incorrecto: ${iscoCode || "?"} en #${idOferta}`
                  : hasCorrecciones
                    ? `Correccion: #${idOferta} - ${tituloOferta.slice(0, 50)}`
                    : `Revisar: #${idOferta} - ${tituloOferta.slice(0, 50)}`;
              const nota =
                typeof correcciones?.nota === "string"
                  ? correcciones.nota
                  : "";
              const iscoCorr =
                typeof correcciones?.isco_correcto === "string"
                  ? correcciones.isco_correcto
                  : undefined;
              const ocupCorr = correcciones?.ocupacion_corregida as
                | { isco_code?: string; esco_label?: string }
                | undefined;
              const nlpEdit = correcciones?.nlp_editado as
                | Record<string, unknown>
                | undefined;
              const parts: string[] = [
                nota,
                iscoCorr ? `ISCO correcto: ${iscoCorr}` : null,
                ocupCorr
                  ? `ESCO corregido: ${ocupCorr.esco_label} (${ocupCorr.isco_code})`
                  : null,
                // NLP changes
                ...(nlpEdit
                  ? Object.entries(nlpEdit).map(
                      ([k, v]) => `${k}: ${String(v)}`
                    )
                  : []),
                `Oferta: ${tituloOferta}`,
                `ISCO actual: ${iscoCode || "sin asignar"}`,
              ].filter(Boolean) as string[];

              await createIssue({
                titulo,
                descripcion: parts.join("\n"),
                tipo,
                prioridad: resultado === "error" ? "alta" : "media",
                id_oferta: idOferta,
                autor_id: user.id,
                autor_email: user.email || "",
                autor_nombre:
                  user.user_metadata?.display_name ||
                  user.email?.split("@")[0] ||
                  "Validador",
              });
              toast.success("Issue creado", { duration: 3000 });
            }
          } catch (issueErr: unknown) {
            const issueMsg = extractErrorMessage(issueErr);
            console.error("Could not create issue:", issueMsg, issueErr);
            toast.error(`Issue no creado: ${issueMsg}`, { duration: 6000 });
          }
        }

        const labels: Record<ValidacionHumana, string> = {
          ok: "OK",
          error: "Error",
          revisar: "Revisar",
          basura: "Basura",
        };
        toast.success(`Marcada: ${labels[resultado]}`);
        onEvaluated(resultado);
        return true;
      } catch (err: unknown) {
        const msg = extractErrorMessage(err);
        console.error("Error saving validation:", msg, err);
        toast.error(`Error al guardar: ${msg}`, { duration: 8000 });
        return false;
      } finally {
        setSaving(false);
      }
    },
    [idOferta, tituloOferta, iscoCode, onEvaluated]
  );

  const executeAction = useCallback(
    (action: ValidacionHumana) => {
      if (action === "ok" || action === "basura") {
        doSave(action);
      } else {
        // Error/Revisar open the wizard
        setWizardTrigger(action as WizardTrigger);
        setWizardOpen(true);
      }
    },
    [doSave]
  );

  const handleQuickAction = useCallback(
    (action: ValidacionHumana) => {
      // If already validated, confirm before changing
      if (currentValidacion && currentValidacion !== action) {
        setConfirmAction(action);
        return;
      }
      executeAction(action);
    },
    [currentValidacion, executeAction]
  );

  const handleConfirm = useCallback(() => {
    if (confirmAction) {
      executeAction(confirmAction);
      setConfirmAction(null);
    }
  }, [confirmAction, executeAction]);

  const handleOpenEditar = useCallback(() => {
    setWizardTrigger("editar");
    setWizardOpen(true);
  }, []);

  // Wizard save handler
  const handleWizardSave = useCallback(
    async (
      resultado: ValidacionHumana | null,
      correcciones: WizardCorrecciones
    ) => {
      // Build the flat correcciones object for Supabase
      const flatCorrecciones: Record<string, unknown> = {};

      if (correcciones.ocupacion_corregida) {
        flatCorrecciones.ocupacion_corregida = correcciones.ocupacion_corregida;
        // Also set isco_correcto for backward compat
        flatCorrecciones.isco_correcto =
          correcciones.ocupacion_corregida.isco_code;
      }
      if (correcciones.nlp_editado) {
        flatCorrecciones.nlp_editado = correcciones.nlp_editado;
      }
      if (correcciones.tareas_editadas) {
        flatCorrecciones.tareas_editadas = correcciones.tareas_editadas;
      }
      if (correcciones.skills_editadas) {
        flatCorrecciones.skills_editadas = correcciones.skills_editadas;
      }
      if (correcciones.nota) {
        flatCorrecciones.nota = correcciones.nota;
      }

      // "editar" trigger has no resultado — use current state or default to "revisar"
      const finalResultado = resultado || currentValidacion || "revisar";
      const ok = await doSave(finalResultado as ValidacionHumana, flatCorrecciones);
      if (!ok) throw new Error("save failed");
    },
    [doSave, currentValidacion, idOferta, onEvaluated]
  );

  // Keyboard shortcuts: Alt+1/2/3/4/5
  // Suppressed when wizard is open
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (saving || wizardOpen) return;
      if (!e.altKey) return;

      if (e.key === "1") {
        e.preventDefault();
        handleQuickAction("ok");
      } else if (e.key === "2") {
        e.preventDefault();
        handleQuickAction("error");
      } else if (e.key === "3") {
        e.preventDefault();
        handleQuickAction("revisar");
      } else if (e.key === "4") {
        e.preventDefault();
        handleQuickAction("basura");
      } else if (e.key === "5") {
        e.preventDefault();
        handleOpenEditar();
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [saving, wizardOpen, handleQuickAction, handleOpenEditar]);

  const validacionColor: Record<ValidacionHumana, string> = {
    ok: "bg-green-100 text-green-800",
    error: "bg-red-100 text-red-800",
    revisar: "bg-amber-100 text-amber-800",
    basura: "bg-gray-200 text-gray-600",
  };

  return (
    <>
      <div className="border-t bg-white px-4 py-2 flex items-center gap-2 flex-wrap">
        {saving && (
          <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
        )}

        {/* Already validated indicator */}
        {currentValidacion && (
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded ${validacionColor[currentValidacion]}`}
          >
            {currentValidacion.toUpperCase()}
          </span>
        )}

        {/* Quick action buttons */}
        <Button
          size="sm"
          variant="outline"
          disabled={saving}
          onClick={() => handleQuickAction("ok")}
          className="h-7 text-xs hover:bg-green-50 hover:text-green-700 hover:border-green-300"
        >
          <Check className="w-3.5 h-3.5 mr-1" />
          OK
          <kbd className="ml-1.5 text-[9px] opacity-50">Alt+1</kbd>
        </Button>

        <Button
          size="sm"
          variant="outline"
          disabled={saving}
          onClick={() => handleQuickAction("error")}
          className="h-7 text-xs hover:bg-red-50 hover:text-red-700 hover:border-red-300"
        >
          <X className="w-3.5 h-3.5 mr-1" />
          Error
          <kbd className="ml-1.5 text-[9px] opacity-50">Alt+2</kbd>
        </Button>

        <Button
          size="sm"
          variant="outline"
          disabled={saving}
          onClick={() => handleQuickAction("revisar")}
          className="h-7 text-xs hover:bg-amber-50 hover:text-amber-700 hover:border-amber-300"
        >
          <AlertTriangle className="w-3.5 h-3.5 mr-1" />
          Revisar
          <kbd className="ml-1.5 text-[9px] opacity-50">Alt+3</kbd>
        </Button>

        <Button
          size="sm"
          variant="outline"
          disabled={saving}
          onClick={() => handleQuickAction("basura")}
          className="h-7 text-xs hover:bg-gray-100 hover:text-gray-700"
        >
          <Trash2 className="w-3.5 h-3.5 mr-1" />
          Basura
          <kbd className="ml-1.5 text-[9px] opacity-50">Alt+4</kbd>
        </Button>

        <div className="h-5 w-px bg-gray-200 mx-1" />

        <Button
          size="sm"
          variant="outline"
          disabled={saving}
          onClick={handleOpenEditar}
          className="h-7 text-xs hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300"
        >
          <Pencil className="w-3.5 h-3.5 mr-1" />
          Editar
          <kbd className="ml-1.5 text-[9px] opacity-50">Alt+5</kbd>
        </Button>
      </div>

      {/* Wizard modal */}
      <WizardModal
        open={wizardOpen}
        onOpenChange={setWizardOpen}
        oferta={oferta}
        trigger={wizardTrigger}
        onSave={handleWizardSave}
      />

      {/* Re-validation confirmation */}
      <AlertDialog
        open={confirmAction !== null}
        onOpenChange={(open) => !open && setConfirmAction(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cambiar evaluacion</AlertDialogTitle>
            <AlertDialogDescription>
              Esta oferta ya fue evaluada como{" "}
              <strong>{currentValidacion?.toUpperCase()}</strong>
              {oferta.validacion_humana_por && (
                <> por {oferta.validacion_humana_por}</>
              )}
              . ¿Cambiar a <strong>{confirmAction?.toUpperCase()}</strong>?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirm}>
              Cambiar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
