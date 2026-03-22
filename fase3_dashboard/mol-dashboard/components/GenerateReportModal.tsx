"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Download, Link, ExternalLink, Info } from "lucide-react";

interface Props {
  open: boolean;
  candidatoNombre?: string;
  tituloVacante?: string;
  onClose: () => void;
  onGenerate: (data: { nombre: string; dni: string; titulo: string }) => Promise<{ token: string; pdfUrl: string }>;
}

type Step = "form" | "loading" | "success";

export function GenerateReportModal({
  open,
  candidatoNombre = "",
  tituloVacante = "",
  onClose,
  onGenerate,
}: Props) {
  const [nombre, setNombre] = useState(candidatoNombre);
  const [dni, setDni] = useState("");
  const [titulo, setTitulo] = useState(tituloVacante);
  const [step, setStep] = useState<Step>("form");
  const [result, setResult] = useState<{ token: string; pdfUrl: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reportUrl = result ? `${window.location.origin}/reporte/${result.token}` : "";

  const handleGenerate = async () => {
    if (!nombre.trim()) {
      setError("El nombre del candidato es requerido.");
      return;
    }
    setError(null);
    setStep("loading");
    try {
      const data = await onGenerate({ nombre, dni, titulo });
      setResult(data);
      setStep("success");
    } catch {
      setError("No se pudo generar el reporte. Intentá de nuevo.");
      setStep("form");
    }
  };

  const handleCopyLink = async () => {
    await navigator.clipboard.writeText(reportUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClose = () => {
    setStep("form");
    setNombre(candidatoNombre);
    setDni("");
    setTitulo(tituloVacante);
    setResult(null);
    setError(null);
    setCopied(false);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Generar Reporte de Compatibilidad</DialogTitle>
          <DialogDescription>
            El reporte estará disponible durante 60 días.
          </DialogDescription>
        </DialogHeader>

        {step === "form" && (
          <>
            <div className="space-y-4 py-2">
              <div className="space-y-1.5">
                <Label htmlFor="nombre-candidato">Nombre del candidato *</Label>
                <Input
                  id="nombre-candidato"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Juan Pérez"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="dni-candidato">DNI (opcional)</Label>
                <Input
                  id="dni-candidato"
                  value={dni}
                  onChange={(e) => setDni(e.target.value)}
                  placeholder="12.345.678"
                  type="text"
                  inputMode="numeric"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="titulo-vacante">Título de la vacante</Label>
                <Input
                  id="titulo-vacante"
                  value={titulo}
                  onChange={(e) => setTitulo(e.target.value)}
                  placeholder="Desarrollador de software"
                />
              </div>

              <div className="flex items-start gap-2 rounded-md border border-blue-200 bg-blue-50 p-3">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
                <p className="text-sm text-blue-700">
                  El reporte estará disponible por 60 días. El DNI no se incluye en el
                  reporte visible para el reclutador.
                </p>
              </div>

              {error && <p className="text-sm text-red-500">{error}</p>}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancelar
              </Button>
              <Button onClick={handleGenerate} disabled={!nombre.trim()}>
                Generar Reporte + PDF
              </Button>
            </DialogFooter>
          </>
        )}

        {step === "loading" && (
          <div className="flex flex-col items-center gap-3 py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" aria-label="Generando reporte" />
            <p className="text-sm text-gray-500">Generando reporte y PDF...</p>
          </div>
        )}

        {step === "success" && result && (
          <>
            <div className="space-y-3 py-2">
              <p className="text-sm font-medium text-green-700">
                ✓ Reporte generado correctamente
              </p>
              <div className="space-y-2">
                <a
                  href={result.pdfUrl}
                  download
                  className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  <Download className="h-4 w-4" />
                  Descargar PDF
                </a>
                <button
                  onClick={handleCopyLink}
                  className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  <Link className="h-4 w-4" />
                  {copied ? "¡Link copiado!" : "Copiar link del reporte"}
                </button>
                <a
                  href={reportUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  <ExternalLink className="h-4 w-4" />
                  Ver reporte
                </a>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cerrar
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
