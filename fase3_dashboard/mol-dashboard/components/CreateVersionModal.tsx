"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { AlertTriangle, Loader2 } from "lucide-react";

type Props = {
  open: boolean;
  versionPropuesta: string;
  emergentesPendientes: number;
  onClose: () => void;
  onCreate: (nota: string) => Promise<void>;
};

export function CreateVersionModal({
  open,
  versionPropuesta,
  emergentesPendientes,
  onClose,
  onCreate,
}: Props) {
  const [nota, setNota] = useState("");
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onCreate(nota);
      setNota("");
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Crear nueva versión {versionPropuesta}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <p className="text-sm text-gray-500">
            Se creará un snapshot completo del estado actual del perfil. Los
            reportes generados a partir de ahora usarán esta versión. Los
            reportes existentes mantienen su versión original.
          </p>

          <div className="space-y-1">
            <label className="text-sm font-medium">Nota del corte</label>
            <Textarea
              placeholder="Ej: Incorpora Docker, Kubernetes, Scrum..."
              value={nota}
              onChange={(e) => setNota(e.target.value)}
              rows={3}
            />
          </div>

          {emergentesPendientes > 0 && (
            <div className="flex items-start gap-2 rounded-md bg-amber-50 border border-amber-200 p-3">
              <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
              <p className="text-sm text-amber-700">
                Hay {emergentesPendientes} emergente
                {emergentesPendientes > 1 ? "s" : ""} pendiente
                {emergentesPendientes > 1 ? "s" : ""} de revisión. Se
                recomienda revisarlas antes de crear el corte.
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button onClick={handleConfirm} disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Confirmar corte {versionPropuesta}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
