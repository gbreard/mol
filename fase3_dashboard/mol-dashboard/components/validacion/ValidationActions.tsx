"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Check, X, AlertTriangle, Trash2, Loader2 } from "lucide-react";
import { saveValidacion, createIssue } from "@/lib/supabase";
import { createBrowserClient } from "@/lib/supabase/browser";
import { ValidacionHumana } from "@/lib/types";
import { toast } from "sonner";

interface ValidationActionsProps {
  idOferta: string;
  tituloOferta: string;
  iscoCode: string | null;
  currentValidacion: ValidacionHumana | null;
  onEvaluated: (resultado: ValidacionHumana) => void;
}

export function ValidationActions({
  idOferta,
  tituloOferta,
  iscoCode,
  currentValidacion,
  onEvaluated,
}: ValidationActionsProps) {
  const [expandedAction, setExpandedAction] = useState<"error" | "revisar" | null>(null);
  const [iscoInput, setIscoInput] = useState("");
  const [notaInput, setNotaInput] = useState("");
  const [saving, setSaving] = useState(false);
  const iscoRef = useRef<HTMLInputElement>(null);

  // Reset when oferta changes
  useEffect(() => {
    setExpandedAction(null);
    setIscoInput("");
    setNotaInput("");
  }, [idOferta]);

  // Focus ISCO input when error expanded
  useEffect(() => {
    if (expandedAction === "error" && iscoRef.current) {
      iscoRef.current.focus();
    }
  }, [expandedAction]);

  const doSave = useCallback(async (resultado: ValidacionHumana, correcciones?: Record<string, string>) => {
    setSaving(true);
    try {
      await saveValidacion(idOferta, resultado, correcciones);

      // Create issue for error/revisar
      if (resultado === "error" || resultado === "revisar") {
        try {
          const supabase = createBrowserClient();
          const { data: { user } } = await supabase.auth.getUser();
          if (user) {
            const tipo = resultado === "error" ? "error_isco" : "sugerencia";
            const titulo = resultado === "error"
              ? `ISCO incorrecto: ${iscoCode || "?"} en #${idOferta}`
              : `Revisar: #${idOferta} - ${tituloOferta.slice(0, 50)}`;
            const parts = [
              correcciones?.nota || "",
              correcciones?.isco_correcto ? `ISCO correcto: ${correcciones.isco_correcto}` : null,
              `Oferta: ${tituloOferta}`,
              `ISCO actual: ${iscoCode || "sin asignar"}`,
            ].filter(Boolean);

            await createIssue({
              titulo,
              descripcion: parts.join("\n"),
              tipo,
              prioridad: resultado === "error" ? "alta" : "media",
              id_oferta: idOferta,
              autor_id: user.id,
              autor_email: user.email || "",
              autor_nombre: user.user_metadata?.display_name || user.email?.split("@")[0] || "Validador",
            });
          }
        } catch {
          // Issue creation is best-effort
          console.error("Could not create issue");
        }
      }

      const labels: Record<ValidacionHumana, string> = {
        ok: "OK", error: "Error", revisar: "Revisar", basura: "Basura",
      };
      toast.success(`Marcada: ${labels[resultado]}`);
      setExpandedAction(null);
      setIscoInput("");
      setNotaInput("");
      onEvaluated(resultado);
    } catch (err) {
      console.error("Error saving validation:", err);
      toast.error("Error al guardar validacion");
    } finally {
      setSaving(false);
    }
  }, [idOferta, tituloOferta, iscoCode, onEvaluated]);

  const handleQuickAction = useCallback((action: ValidacionHumana) => {
    if (action === "ok" || action === "basura") {
      doSave(action);
    } else {
      setExpandedAction(action === "error" ? "error" : "revisar");
    }
  }, [doSave]);

  const handleSubmitExpanded = useCallback(() => {
    if (!expandedAction) return;
    const correcciones: Record<string, string> = {};
    if (iscoInput.trim()) correcciones.isco_correcto = iscoInput.trim();
    if (notaInput.trim()) correcciones.nota = notaInput.trim();
    doSave(expandedAction, Object.keys(correcciones).length > 0 ? correcciones : undefined);
  }, [expandedAction, iscoInput, notaInput, doSave]);

  // Keyboard shortcuts: Alt+1/2/3/4
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (saving) return;
      if (!e.altKey) return;
      const target = e.target as HTMLElement;
      const isTyping = target.tagName === "INPUT" || target.tagName === "TEXTAREA";

      if (e.key === "1") {
        e.preventDefault();
        handleQuickAction("ok");
      } else if (e.key === "2") {
        e.preventDefault();
        if (expandedAction === "error" && !isTyping) {
          handleSubmitExpanded();
        } else if (!expandedAction) {
          handleQuickAction("error");
        }
      } else if (e.key === "3") {
        e.preventDefault();
        if (expandedAction === "revisar" && !isTyping) {
          handleSubmitExpanded();
        } else if (!expandedAction) {
          handleQuickAction("revisar");
        }
      } else if (e.key === "4") {
        e.preventDefault();
        handleQuickAction("basura");
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [saving, expandedAction, handleQuickAction, handleSubmitExpanded]);

  const validacionColor: Record<ValidacionHumana, string> = {
    ok: "bg-green-100 text-green-800",
    error: "bg-red-100 text-red-800",
    revisar: "bg-amber-100 text-amber-800",
    basura: "bg-gray-200 text-gray-600",
  };

  return (
    <div className="border-t bg-white px-4 py-2 flex items-center gap-2 flex-wrap">
      {saving && <Loader2 className="w-4 h-4 animate-spin text-blue-600" />}

      {/* Already validated indicator */}
      {currentValidacion && (
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${validacionColor[currentValidacion]}`}>
          {currentValidacion.toUpperCase()}
        </span>
      )}

      {/* Action buttons */}
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
        variant={expandedAction === "error" ? "default" : "outline"}
        disabled={saving}
        onClick={() => handleQuickAction("error")}
        className={`h-7 text-xs ${expandedAction === "error" ? "bg-red-600 hover:bg-red-700" : "hover:bg-red-50 hover:text-red-700 hover:border-red-300"}`}
      >
        <X className="w-3.5 h-3.5 mr-1" />
        Error
        <kbd className="ml-1.5 text-[9px] opacity-50">Alt+2</kbd>
      </Button>

      <Button
        size="sm"
        variant={expandedAction === "revisar" ? "default" : "outline"}
        disabled={saving}
        onClick={() => handleQuickAction("revisar")}
        className={`h-7 text-xs ${expandedAction === "revisar" ? "bg-amber-600 hover:bg-amber-700" : "hover:bg-amber-50 hover:text-amber-700 hover:border-amber-300"}`}
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

      {/* Inline form for error/revisar */}
      {expandedAction && (
        <>
          <div className="h-5 w-px bg-gray-200 mx-1" />
          {expandedAction === "error" && (
            <Input
              ref={iscoRef}
              value={iscoInput}
              onChange={(e) => setIscoInput(e.target.value)}
              placeholder="ISCO correcto"
              className="w-[100px] h-7 text-xs"
              onKeyDown={(e) => e.key === "Enter" && handleSubmitExpanded()}
            />
          )}
          <Input
            value={notaInput}
            onChange={(e) => setNotaInput(e.target.value)}
            placeholder="Nota (opcional)"
            className="w-[180px] h-7 text-xs"
            onKeyDown={(e) => e.key === "Enter" && handleSubmitExpanded()}
          />
          <Button
            size="sm"
            onClick={handleSubmitExpanded}
            disabled={saving}
            className="h-7 text-xs bg-blue-600 hover:bg-blue-700"
          >
            Enviar
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setExpandedAction(null)}
            className="h-7 text-xs text-gray-400"
          >
            Cancelar
          </Button>
        </>
      )}
    </div>
  );
}
