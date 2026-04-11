"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

interface GoldSetModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  idOferta: string;
  tituloOferta: string;
  iscoCode: string | null;
  escoLabel: string | null;
}

const TIPOS_ERROR = [
  { value: "dominio_incorrecto", label: "Dominio incorrecto" },
  { value: "nivel_incorrecto", label: "Nivel jerárquico incorrecto" },
  { value: "homonimia", label: "Homonimia (palabra ambigua)" },
  { value: "rol_incorrecto", label: "Rol primario incorrecto" },
];

export function GoldSetModal({
  open,
  onOpenChange,
  idOferta,
  tituloOferta,
  iscoCode,
  escoLabel,
}: GoldSetModalProps) {
  const [escoOk, setEscoOk] = useState<"si" | "no">("si");
  const [tipoError, setTipoError] = useState<string>("");
  const [iscoEsperado, setIscoEsperado] = useState("");
  const [comentario, setComentario] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        id_oferta: idOferta,
        esco_ok: escoOk === "si",
        comentario: comentario || null,
      };

      if (escoOk === "no") {
        body.tipo_error = tipoError || null;
        body.isco_esperado = iscoEsperado || null;
      }

      const res = await fetch("/api/gold-set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Error al guardar");
      }

      const data = await res.json();
      const total = data.total || "?";
      const action = data.is_update ? "actualizado en" : "agregado al";

      toast.success(`Gold Set: ${action} (${total}/150)`, { duration: 4000 });
      onOpenChange(false);

      // Reset form
      setEscoOk("si");
      setTipoError("");
      setIscoEsperado("");
      setComentario("");
    } catch (err) {
      toast.error(`Error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="text-amber-500">&#9733;</span>
            Agregar al Gold Set
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="text-xs text-muted-foreground">
            <strong>#{idOferta}</strong> — {tituloOferta}
            {iscoCode && (
              <span className="ml-2 text-[10px] bg-gray-100 px-1.5 py-0.5 rounded">
                ISCO {iscoCode}
              </span>
            )}
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium">
              ¿El matching es correcto?
            </Label>
            <RadioGroup
              value={escoOk}
              onValueChange={(v) => setEscoOk(v as "si" | "no")}
              className="flex gap-4"
            >
              <div className="flex items-center gap-2">
                <RadioGroupItem value="si" id="gs-si" />
                <Label htmlFor="gs-si" className="text-sm cursor-pointer">
                  Sí — buen ejemplo
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="no" id="gs-no" />
                <Label htmlFor="gs-no" className="text-sm cursor-pointer">
                  No — tiene error
                </Label>
              </div>
            </RadioGroup>
          </div>

          {escoOk === "no" && (
            <>
              <div className="space-y-1.5">
                <Label className="text-sm">Tipo de error</Label>
                <Select value={tipoError} onValueChange={setTipoError}>
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue placeholder="Seleccionar..." />
                  </SelectTrigger>
                  <SelectContent>
                    {TIPOS_ERROR.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <Label className="text-sm">ISCO correcto</Label>
                <Input
                  value={iscoEsperado}
                  onChange={(e) => setIscoEsperado(e.target.value)}
                  placeholder="Ej: 4321"
                  className="h-8 text-sm"
                />
              </div>
            </>
          )}

          <div className="space-y-1.5">
            <Label className="text-sm">Comentario</Label>
            <Textarea
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              placeholder="Descripción breve del caso..."
              className="text-sm min-h-[60px]"
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
          >
            Cancelar
          </Button>
          <Button size="sm" onClick={handleSubmit} disabled={saving}>
            {saving && <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />}
            Agregar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
