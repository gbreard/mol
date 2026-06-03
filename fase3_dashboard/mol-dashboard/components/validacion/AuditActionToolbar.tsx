"use client";

import { useCallback, useEffect, useImperativeHandle, useRef, useState, forwardRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
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
import { Check, AlertOctagon, Loader2 } from "lucide-react";
import { toast } from "sonner";

// SPEC W Etapa 1 sub-tarea D.1
// Refs:
//   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md F4, F5, F6
//   Endpoints: POST /api/audit-actions, DELETE /api/audit-actions/:id,
//              GET /api/oferta/:id/audit-history

type EstadoRevision = "revisada" | "mal_extraida_total" | null;

export interface AuditActionToolbarHandle {
  triggerRevisada: () => void;
  triggerMalExtraida: () => void;
}

interface AuditActionToolbarProps {
  idOferta: string;
  estadoRevisionActual: EstadoRevision;
  onAuditComplete: (newEstado: EstadoRevision) => void;
}

function extractFetchError(err: unknown, fallback: string): string {
  if (err instanceof Error) return err.message;
  return fallback;
}

async function fetchJsonOrThrow(input: RequestInfo, init?: RequestInit) {
  const response = await fetch(input, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({} as Record<string, unknown>));
    const msg = (body as { error?: string; message?: string }).error
      || (body as { error?: string; message?: string }).message
      || `HTTP ${response.status}`;
    throw new Error(String(msg));
  }
  return response.json();
}

export const AuditActionToolbar = forwardRef<AuditActionToolbarHandle, AuditActionToolbarProps>(
  function AuditActionToolbar({ idOferta, estadoRevisionActual, onAuditComplete }, ref) {
    const [lastActionId, setLastActionId] = useState<number | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [showMalExtraidaModal, setShowMalExtraidaModal] = useState(false);
    const [notaMalExtraida, setNotaMalExtraida] = useState("");

    // Reset lastActionId al cambiar de oferta
    const lastActionIdRef = useRef<number | null>(null);
    useEffect(() => {
      lastActionIdRef.current = null;
      setLastActionId(null);
      setNotaMalExtraida("");
    }, [idOferta]);

    // Si el componente monta con estado != null y sin lastActionId, hacer GET history
    // para conocer el id de la última acción que ese estado representa (necesario
    // para construir el DELETE).
    useEffect(() => {
      if (estadoRevisionActual === null) return;
      if (lastActionIdRef.current !== null) return;

      let cancelled = false;
      const targetAction = estadoRevisionActual === "revisada" ? "mark_revised" : "mark_total_failure";

      fetch(`/api/oferta/${encodeURIComponent(idOferta)}/audit-history`)
        .then((r) => (r.ok ? r.json() : null))
        .then((data: { actions?: Array<{ id: number; action_type: string }> } | null) => {
          if (cancelled || !data?.actions) return;
          const latest = data.actions.find((a) => a.action_type === targetAction);
          if (latest) {
            lastActionIdRef.current = latest.id;
            setLastActionId(latest.id);
          }
        })
        .catch(() => {
          // Silencioso: si falla, el DELETE va a intentar GET de fallback al click
        });

      return () => {
        cancelled = true;
      };
    }, [idOferta, estadoRevisionActual]);

    const postAuditAction = useCallback(
      async (actionType: "mark_revised" | "mark_total_failure", note?: string) => {
        const body: Record<string, unknown> = {
          id_oferta: idOferta,
          action_type: actionType,
          target_type: "oferta_global",
        };
        if (note) body.note = note;
        const data = await fetchJsonOrThrow("/api/audit-actions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        return data as { success: boolean; action_id: number };
      },
      [idOferta],
    );

    const resolveLastActionId = useCallback(
      async (targetAction: "mark_revised" | "mark_total_failure"): Promise<number | null> => {
        if (lastActionIdRef.current) return lastActionIdRef.current;
        const data = await fetchJsonOrThrow(
          `/api/oferta/${encodeURIComponent(idOferta)}/audit-history`,
        );
        const actions = (data as { actions?: Array<{ id: number; action_type: string }> })
          .actions || [];
        const latest = actions.find((a) => a.action_type === targetAction);
        return latest ? latest.id : null;
      },
      [idOferta],
    );

    const deleteAuditAction = useCallback(async (actionId: number) => {
      await fetchJsonOrThrow(`/api/audit-actions/${actionId}`, { method: "DELETE" });
    }, []);

    const handleMarcarRevisada = useCallback(async () => {
      if (isProcessing) return;
      setIsProcessing(true);
      try {
        if (estadoRevisionActual === "revisada") {
          const id = await resolveLastActionId("mark_revised");
          if (!id) {
            toast.error("No se encontró la acción a revertir");
            return;
          }
          await deleteAuditAction(id);
          lastActionIdRef.current = null;
          setLastActionId(null);
          toast.success("Revisión removida");
          onAuditComplete(null);
        } else if (estadoRevisionActual === null) {
          const result = await postAuditAction("mark_revised");
          lastActionIdRef.current = result.action_id;
          setLastActionId(result.action_id);
          toast.success("Oferta marcada como revisada");
          onAuditComplete("revisada");
        }
      } catch (err) {
        toast.error(extractFetchError(err, "Error al guardar"));
      } finally {
        setIsProcessing(false);
      }
    }, [
      isProcessing,
      estadoRevisionActual,
      resolveLastActionId,
      deleteAuditAction,
      postAuditAction,
      onAuditComplete,
    ]);

    const handleMarcarMalExtraida = useCallback(async () => {
      if (isProcessing) return;
      if (estadoRevisionActual === "mal_extraida_total") {
        // Desmarcar inmediato (sin modal)
        setIsProcessing(true);
        try {
          const id = await resolveLastActionId("mark_total_failure");
          if (!id) {
            toast.error("No se encontró la acción a revertir");
            return;
          }
          await deleteAuditAction(id);
          lastActionIdRef.current = null;
          setLastActionId(null);
          toast.success("Marca de mal extraída removida");
          onAuditComplete(null);
        } catch (err) {
          toast.error(extractFetchError(err, "Error al guardar"));
        } finally {
          setIsProcessing(false);
        }
        return;
      }
      // Marcar: abrir modal de confirmación con nota opcional
      if (estadoRevisionActual === null) {
        setNotaMalExtraida("");
        setShowMalExtraidaModal(true);
      }
    }, [
      isProcessing,
      estadoRevisionActual,
      resolveLastActionId,
      deleteAuditAction,
      onAuditComplete,
    ]);

    const handleConfirmMalExtraida = useCallback(async () => {
      setIsProcessing(true);
      try {
        const trimmed = notaMalExtraida.trim();
        const result = await postAuditAction(
          "mark_total_failure",
          trimmed.length > 0 ? trimmed : undefined,
        );
        lastActionIdRef.current = result.action_id;
        setLastActionId(result.action_id);
        toast.success("Oferta marcada como mal extraída");
        onAuditComplete("mal_extraida_total");
        setShowMalExtraidaModal(false);
        setNotaMalExtraida("");
      } catch (err) {
        toast.error(extractFetchError(err, "Error al guardar"));
      } finally {
        setIsProcessing(false);
      }
    }, [notaMalExtraida, postAuditAction, onAuditComplete]);

    // Exponer triggers a través de ref (para atajos de teclado en el padre)
    useImperativeHandle(
      ref,
      () => ({
        triggerRevisada: () => {
          void handleMarcarRevisada();
        },
        triggerMalExtraida: () => {
          void handleMarcarMalExtraida();
        },
      }),
      [handleMarcarRevisada, handleMarcarMalExtraida],
    );

    const isRevisada = estadoRevisionActual === "revisada";
    const isMalExtraida = estadoRevisionActual === "mal_extraida_total";

    return (
      <>
        <Button
          size="sm"
          variant="outline"
          disabled={isProcessing || isMalExtraida}
          onClick={handleMarcarRevisada}
          className={
            isRevisada
              ? "h-7 lg:h-8 text-xs lg:text-sm bg-green-100 text-green-800 border-green-300 hover:bg-green-200"
              : "h-7 lg:h-8 text-xs lg:text-sm hover:bg-green-50 hover:text-green-700 hover:border-green-300"
          }
          aria-pressed={isRevisada}
          data-testid="btn-marcar-revisada"
        >
          {isProcessing && isRevisada ? (
            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
          ) : (
            <Check className="w-3.5 h-3.5 mr-1" />
          )}
          {isRevisada ? "Revisada ✓" : "Revisada"}
          <kbd className="ml-1.5 text-[9px] opacity-50">Alt+7</kbd>
        </Button>

        <Button
          size="sm"
          variant="outline"
          disabled={isProcessing || isRevisada}
          onClick={handleMarcarMalExtraida}
          className={
            isMalExtraida
              ? "h-7 lg:h-8 text-xs lg:text-sm bg-purple-100 text-purple-800 border-purple-300 hover:bg-purple-200"
              : "h-7 lg:h-8 text-xs lg:text-sm hover:bg-purple-50 hover:text-purple-700 hover:border-purple-300"
          }
          aria-pressed={isMalExtraida}
          data-testid="btn-mal-extraida"
        >
          <AlertOctagon className="w-3.5 h-3.5 mr-1" />
          {isMalExtraida ? "Mal extraída ⚠" : "Mal extraída"}
          <kbd className="ml-1.5 text-[9px] opacity-50">Alt+8</kbd>
        </Button>

        <AlertDialog open={showMalExtraidaModal} onOpenChange={setShowMalExtraidaModal}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Marcar oferta como mal extraída</AlertDialogTitle>
              <AlertDialogDescription>
                Esta marca indica que el sistema extrajo la oferta incorrectamente
                en sus aspectos principales (puesto, tareas, skills u ocupación).
                Podés agregar una nota explicando qué falló para mejorar el modelo.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <div className="py-2">
              <label htmlFor="nota-mal-extraida" className="text-xs text-gray-600 mb-1 block">
                Nota (opcional)
              </label>
              <Textarea
                id="nota-mal-extraida"
                value={notaMalExtraida}
                onChange={(e) => setNotaMalExtraida(e.target.value)}
                placeholder="Ej: las tareas son títulos, no descripciones de tareas reales."
                className="text-sm min-h-[80px]"
                disabled={isProcessing}
              />
            </div>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isProcessing}>Cancelar</AlertDialogCancel>
              <AlertDialogAction onClick={handleConfirmMalExtraida} disabled={isProcessing}>
                Confirmar
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </>
    );
  },
);
