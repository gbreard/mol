/**
 * Modal para que analistas (Cyn/Diego) soliciten propagación.
 * SPEC T Fase 4. Las solicitudes entran a la cola admin para revisión.
 */
"use client";

import { useState } from "react";
import type { PropagationTipo } from "@/lib/types";
import { PROPAGATION_TIPO_LABELS } from "@/lib/types";

interface Props {
  issueId: string;
  open: boolean;
  onClose: () => void;
  onSubmitted?: () => void;
}

export function RequestPropagationModal({ issueId, open, onClose, onSubmitted }: Props) {
  const [justificacion, setJustificacion] = useState("");
  const [tipo, setTipo] = useState<PropagationTipo | "">("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function handleSubmit() {
    if (!justificacion.trim()) {
      setError("La justificación es obligatoria.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/issues/${issueId}/solicitar-propagacion`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ justificacion, tipo_aproximado: tipo || null }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error ?? `HTTP ${res.status}`);
      }
      onSubmitted?.();
      onClose();
      setJustificacion("");
      setTipo("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-background rounded-lg shadow-xl max-w-lg w-full p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="space-y-1">
          <h2 className="text-lg font-semibold">Solicitar propagación</h2>
          <p className="text-sm text-muted-foreground">
            Si pensás que esta corrección debería aplicarse a otras ofertas
            similares, pedile al admin que lo revise y lo aplique.
          </p>
        </header>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">
              Justificación <span className="text-red-500">*</span>
            </label>
            <textarea
              value={justificacion}
              onChange={(e) => setJustificacion(e.target.value)}
              placeholder='ej: "todos los operarios de depósito tienen este problema"'
              className="w-full border rounded px-3 py-2 text-sm min-h-[80px]"
              maxLength={500}
            />
            <p className="text-xs text-muted-foreground mt-1">
              {justificacion.length}/500 caracteres
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Tipo aproximado <span className="text-muted-foreground">(opcional)</span>
            </label>
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value as PropagationTipo | "")}
              className="w-full border rounded px-3 py-2 text-sm bg-background"
            >
              <option value="">Selecciona... (ayuda al admin a clasificar)</option>
              {(Object.keys(PROPAGATION_TIPO_LABELS) as PropagationTipo[]).map((t) => (
                <option key={t} value={t}>
                  {PROPAGATION_TIPO_LABELS[t]}
                </option>
              ))}
            </select>
          </div>

          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded p-3 text-xs">
            ⚠ El admin va a revisar antes de aplicar. Si está mal, te avisa. Si está
            bien, lo aplica y te notifica con cuántas ofertas se modificaron.
          </div>

          {error && (
            <div className="bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 text-sm p-2 rounded">
              {error}
            </div>
          )}
        </div>

        <footer className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-sm border rounded hover:bg-muted disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !justificacion.trim()}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? "Enviando..." : "Enviar solicitud"}
          </button>
        </footer>
      </div>
    </div>
  );
}
