"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { IssueType, IssuePrioridad, ISSUE_TYPE_LABELS, ISSUE_PRIORIDAD_LABELS } from "@/lib/types";
import { createIssue } from "@/lib/supabase";
import { useIssues } from "@/contexts/IssueContext";
import { Loader2, ArrowLeft, FileText } from "lucide-react";

interface IssueFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
  compact?: boolean;
}

export function IssueForm({ onSuccess, onCancel, compact = false }: IssueFormProps) {
  const { selectedOferta, clearSelectedOferta, refreshIssues } = useIssues();

  const [titulo, setTitulo] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [tipo, setTipo] = useState<IssueType>("sugerencia");
  const [prioridad, setPrioridad] = useState<IssuePrioridad>("media");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!titulo.trim()) {
      setError("El titulo es obligatorio");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await createIssue({
        titulo: titulo.trim(),
        descripcion: descripcion.trim() || undefined,
        tipo,
        prioridad,
        id_oferta: selectedOferta?.id_oferta,
        autor_id: "00000000-0000-0000-0000-000000000000", // TODO: Get from auth
        autor_email: "admin@oede.gob.ar", // TODO: Get from auth
      });

      // Reset form
      setTitulo("");
      setDescripcion("");
      setTipo("sugerencia");
      setPrioridad("media");
      clearSelectedOferta();

      // Refresh issues list
      await refreshIssues();

      onSuccess?.();
    } catch (err) {
      console.error("Error creating issue:", err);
      setError("Error al crear el issue. Intente nuevamente.");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    clearSelectedOferta();
    onCancel?.();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Header with back button */}
      <div className="flex items-center gap-2 pb-2 border-b">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleCancel}
          className="p-1 h-8 w-8"
        >
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h3 className="font-semibold text-gray-900">
          {selectedOferta ? "Issue sobre Oferta" : "Nuevo Issue"}
        </h3>
      </div>

      {/* Oferta info (if selected) */}
      {selectedOferta && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <FileText className="w-4 h-4 text-blue-600 mt-0.5" />
            <div className="text-sm">
              <div className="font-medium text-blue-900">#{selectedOferta.id_oferta}</div>
              <div className="text-blue-700">{selectedOferta.titulo}</div>
              {selectedOferta.isco_code && (
                <div className="text-blue-600 text-xs mt-1">ISCO: {selectedOferta.isco_code}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Title */}
      <div className="space-y-2">
        <Label htmlFor="titulo">Titulo *</Label>
        <Input
          id="titulo"
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Describe brevemente el issue"
          className="bg-gray-50"
        />
      </div>

      {/* Description (optional in compact mode) */}
      {!compact && (
        <div className="space-y-2">
          <Label htmlFor="descripcion">Descripcion</Label>
          <Textarea
            id="descripcion"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            placeholder="Detalles adicionales (opcional)"
            rows={3}
            className="bg-gray-50 resize-none"
          />
        </div>
      )}

      {/* Type and Priority row */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>Tipo</Label>
          <Select value={tipo} onValueChange={(v) => setTipo(v as IssueType)}>
            <SelectTrigger className="bg-gray-50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(ISSUE_TYPE_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Prioridad</Label>
          <Select value={prioridad} onValueChange={(v) => setPrioridad(v as IssuePrioridad)}>
            <SelectTrigger className="bg-gray-50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(ISSUE_PRIORIDAD_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
          {error}
        </div>
      )}

      {/* Submit button */}
      <Button
        type="submit"
        disabled={loading || !titulo.trim()}
        className="w-full bg-blue-600 hover:bg-blue-700"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Guardando...
          </>
        ) : (
          "Guardar Issue"
        )}
      </Button>
    </form>
  );
}
