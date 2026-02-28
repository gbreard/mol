"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Check, X, AlertTriangle, Loader2, Send } from "lucide-react";
import { createIssue, getIssuesByOferta } from "@/lib/supabase";
import { Issue, ISSUE_ESTADO_LABELS } from "@/lib/types";
import { createBrowserClient } from "@/lib/supabase/browser";
import { toast } from "sonner";

interface ValidationActionsProps {
  idOferta: string;
  tituloOferta: string;
  iscoCode: string | null;
  onEvaluated?: () => void;
}

type Evaluation = "correcto" | "incorrecto" | "revisar" | null;

export function ValidationActions({
  idOferta,
  tituloOferta,
  iscoCode,
  onEvaluated,
}: ValidationActionsProps) {
  const [evaluation, setEvaluation] = useState<Evaluation>(null);
  const [escoSugerido, setEscoSugerido] = useState("");
  const [justificacion, setJustificacion] = useState("");
  const [sending, setSending] = useState(false);
  const [existingIssues, setExistingIssues] = useState<Issue[]>([]);

  // Load existing issues for this oferta
  useEffect(() => {
    getIssuesByOferta(idOferta).then(setExistingIssues).catch(console.error);
  }, [idOferta]);

  // Reset state when oferta changes
  useEffect(() => {
    setEvaluation(null);
    setEscoSugerido("");
    setJustificacion("");
  }, [idOferta]);

  const handleEvaluation = useCallback((ev: Evaluation) => {
    setEvaluation(ev);
    if (ev === "correcto") {
      toast.success("Marcada como correcta");
      onEvaluated?.();
    }
  }, [onEvaluated]);

  // Keyboard shortcuts
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === "1") {
        e.preventDefault();
        handleEvaluation("correcto");
      } else if (e.ctrlKey && e.key === "2") {
        e.preventDefault();
        handleEvaluation("incorrecto");
      } else if (e.ctrlKey && e.key === "3") {
        e.preventDefault();
        handleEvaluation("revisar");
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [handleEvaluation]);

  const handleSubmitIssue = async () => {
    if (!justificacion.trim()) {
      toast.error("La justificacion es obligatoria");
      return;
    }

    setSending(true);
    try {
      const supabase = createBrowserClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) {
        toast.error("Debes estar autenticado");
        return;
      }

      const tipo = evaluation === "incorrecto" ? "error_isco" : "sugerencia";
      const titulo = evaluation === "incorrecto"
        ? `ISCO incorrecto: ${iscoCode || "?"} en #${idOferta}`
        : `Revisar: #${idOferta} - ${tituloOferta.slice(0, 50)}`;

      const descripcionIssue = [
        justificacion,
        escoSugerido ? `ESCO sugerido: ${escoSugerido}` : null,
        `Oferta: ${tituloOferta}`,
        `ISCO actual: ${iscoCode || "sin asignar"}`,
      ]
        .filter(Boolean)
        .join("\n");

      await createIssue({
        titulo,
        descripcion: descripcionIssue,
        tipo,
        prioridad: evaluation === "incorrecto" ? "alta" : "media",
        id_oferta: idOferta,
        autor_id: user.id,
        autor_email: user.email || "",
        autor_nombre:
          user.user_metadata?.display_name ||
          user.user_metadata?.full_name ||
          user.email?.split("@")[0] ||
          "Validador",
      });

      toast.success("Issue creado");
      setEvaluation(null);
      setEscoSugerido("");
      setJustificacion("");

      // Refresh existing issues
      const updated = await getIssuesByOferta(idOferta);
      setExistingIssues(updated);

      onEvaluated?.();
    } catch (err) {
      console.error("Error creating issue:", err);
      toast.error("Error al crear el issue");
    } finally {
      setSending(false);
    }
  };

  const estadoColor: Record<string, string> = {
    pendiente: "bg-yellow-100 text-yellow-800",
    en_progreso: "bg-blue-100 text-blue-800",
    resuelto: "bg-green-100 text-green-800",
    descartado: "bg-gray-100 text-gray-800",
  };

  return (
    <div className="space-y-3">
      {/* Action buttons */}
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant={evaluation === "correcto" ? "default" : "outline"}
          className={
            evaluation === "correcto"
              ? "bg-green-600 hover:bg-green-700"
              : "hover:bg-green-50 hover:text-green-700 hover:border-green-300"
          }
          onClick={() => handleEvaluation("correcto")}
        >
          <Check className="w-4 h-4 mr-1" />
          Correcto
          <kbd className="ml-2 text-[10px] opacity-60">Ctrl+1</kbd>
        </Button>
        <Button
          size="sm"
          variant={evaluation === "incorrecto" ? "default" : "outline"}
          className={
            evaluation === "incorrecto"
              ? "bg-red-600 hover:bg-red-700"
              : "hover:bg-red-50 hover:text-red-700 hover:border-red-300"
          }
          onClick={() => handleEvaluation("incorrecto")}
        >
          <X className="w-4 h-4 mr-1" />
          Incorrecto
          <kbd className="ml-2 text-[10px] opacity-60">Ctrl+2</kbd>
        </Button>
        <Button
          size="sm"
          variant={evaluation === "revisar" ? "default" : "outline"}
          className={
            evaluation === "revisar"
              ? "bg-amber-600 hover:bg-amber-700"
              : "hover:bg-amber-50 hover:text-amber-700 hover:border-amber-300"
          }
          onClick={() => handleEvaluation("revisar")}
        >
          <AlertTriangle className="w-4 h-4 mr-1" />
          Revisar
          <kbd className="ml-2 text-[10px] opacity-60">Ctrl+3</kbd>
        </Button>
      </div>

      {/* Issue form (shown for incorrecto/revisar) */}
      {(evaluation === "incorrecto" || evaluation === "revisar") && (
        <div className="bg-gray-50 rounded-lg p-3 space-y-3 border">
          {evaluation === "incorrecto" && (
            <div>
              <label className="text-xs font-medium text-gray-600">
                ESCO sugerido (opcional)
              </label>
              <Input
                value={escoSugerido}
                onChange={(e) => setEscoSugerido(e.target.value)}
                placeholder="Ej: 1221, accountant, etc."
                className="mt-1 h-8 text-sm"
              />
            </div>
          )}
          <div>
            <label className="text-xs font-medium text-gray-600">
              Justificacion *
            </label>
            <Textarea
              value={justificacion}
              onChange={(e) => setJustificacion(e.target.value)}
              placeholder={
                evaluation === "incorrecto"
                  ? "Por que el ISCO es incorrecto?"
                  : "Que hay que revisar?"
              }
              rows={2}
              className="mt-1 text-sm resize-none"
            />
          </div>
          <Button
            size="sm"
            onClick={handleSubmitIssue}
            disabled={sending || !justificacion.trim()}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {sending ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Send className="w-4 h-4 mr-1" />
            )}
            Enviar
          </Button>
        </div>
      )}

      {/* Existing issues */}
      {existingIssues.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-gray-500">
            Issues existentes ({existingIssues.length})
          </p>
          {existingIssues.map((issue) => (
            <div
              key={issue.id}
              className="flex items-center gap-2 text-xs p-1.5 bg-white rounded border"
            >
              <Badge
                variant="secondary"
                className={`text-[10px] ${estadoColor[issue.estado] || ""}`}
              >
                {ISSUE_ESTADO_LABELS[issue.estado]}
              </Badge>
              <span className="truncate flex-1">{issue.titulo}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
