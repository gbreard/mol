"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, Zap, Check, X, Pencil, ExternalLink, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";

interface Candidate {
  id: number;
  oferta_id: string;
  issue_ids: string[];
  tipo: string;
  propuesta: Record<string, unknown>;
  justificacion: string;
  confianza: string;
  afecta_otras: boolean;
  estado: string;
  created_at: string;
}

interface Usage {
  allowed: boolean;
  llamadas_hoy: number;
  max_daily: number;
  costo_hoy: number;
}

const TABS = [
  { id: "reglas", label: "Reglas", tipos: ["regla_nueva", "fix_regla", "fix_bug"] },
  { id: "sinonimos", label: "Sinónimos", tipos: ["sinonimo"] },
  { id: "skills", label: "Skills", tipos: ["skills_gold_set"] },
  { id: "nlp", label: "NLP", tipos: ["nlp_correccion_sector", "nlp_area_funcional", "nlp_limpieza_tareas", "nlp_fix_puntual"] },
  { id: "excepciones", label: "Excepciones", tipos: ["excepcion_aceptable", "requiere_revision"] },
];

const CONFIANZA_COLORS: Record<string, string> = {
  alta: "bg-green-100 text-green-800",
  media: "bg-amber-100 text-amber-800",
  baja: "bg-red-100 text-red-800",
};

export default function CorreccionesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [processing, setProcessing] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/admin/analizar-correcciones?estado=pendiente");
      if (res.ok) {
        const json = await res.json();
        setCandidates(json.candidatos || []);
        setUsage(json.usage || null);
      }
    } catch (err) {
      console.error("Error loading candidates:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const res = await fetch("/api/admin/analizar-correcciones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ batch_size: 15 }),
      });

      if (res.status === 429) {
        const err = await res.json();
        toast.error(err.error);
        return;
      }

      if (!res.ok) {
        const err = await res.json();
        toast.error(err.error || "Error en análisis");
        return;
      }

      const data = await res.json();
      toast.success(
        `Análisis completado: ${data.candidatos?.length || 0} candidatos, $${data.costo_estimado?.toFixed(4)}`
      );
      await loadData();
    } catch (err) {
      toast.error("Error de conexión");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAction = async (id: number, accion: "aprobar" | "rechazar") => {
    setProcessing(id);
    try {
      const res = await fetch("/api/admin/analizar-correcciones", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, accion }),
      });
      if (res.ok) {
        setCandidates(prev => prev.filter(c => c.id !== id));
        toast.success(`Candidato ${accion === "aprobar" ? "aprobado" : "rechazado"}`);
      }
    } catch (err) {
      toast.error("Error");
    } finally {
      setProcessing(null);
    }
  };

  const countByTab = (tipos: string[]) =>
    candidates.filter(c => tipos.includes(c.tipo)).length;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Correcciones de Validadores</h1>
          <p className="text-sm text-gray-500 mt-1">
            {candidates.length} candidatos pendientes de revisión
          </p>
        </div>
        <div className="flex items-center gap-4">
          {usage && (
            <span className="text-xs text-gray-500">
              API: ${usage.costo_hoy?.toFixed(2)} hoy · {usage.llamadas_hoy}/{usage.max_daily} llamadas
            </span>
          )}
          <Button onClick={handleAnalyze} disabled={analyzing}>
            {analyzing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Zap className="w-4 h-4 mr-2" />
            )}
            {analyzing ? "Analizando..." : "Analizar con Claude"}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      ) : candidates.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p>No hay candidatos pendientes.</p>
          <p className="text-xs mt-1">Clickeá "Analizar con Claude" para procesar correcciones.</p>
        </div>
      ) : (
        <Tabs defaultValue="reglas">
          <TabsList>
            {TABS.map(tab => (
              <TabsTrigger key={tab.id} value={tab.id} className="text-xs">
                {tab.label}
                {countByTab(tab.tipos) > 0 && (
                  <Badge variant="secondary" className="ml-1.5 text-[10px] px-1.5">
                    {countByTab(tab.tipos)}
                  </Badge>
                )}
              </TabsTrigger>
            ))}
          </TabsList>

          {TABS.map(tab => (
            <TabsContent key={tab.id} value={tab.id} className="space-y-3 mt-4">
              {candidates
                .filter(c => tab.tipos.includes(c.tipo))
                .map(c => (
                  <CandidateCard
                    key={c.id}
                    candidate={c}
                    processing={processing === c.id}
                    onApprove={() => handleAction(c.id, "aprobar")}
                    onReject={() => handleAction(c.id, "rechazar")}
                  />
                ))}
              {countByTab(tab.tipos) === 0 && (
                <p className="text-sm text-gray-400 text-center py-6">
                  Sin candidatos en esta categoría
                </p>
              )}
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  );
}

function CandidateCard({
  candidate,
  processing,
  onApprove,
  onReject,
}: {
  candidate: Candidate;
  processing: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  const prop = candidate.propuesta || {};

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded">
              {candidate.tipo}
            </span>
            <Badge className={`text-[10px] ${CONFIANZA_COLORS[candidate.confianza] || "bg-gray-100"}`}>
              {candidate.confianza}
            </Badge>
            {candidate.afecta_otras && (
              <span className="text-[10px] text-blue-600">Afecta otras ofertas</span>
            )}
          </div>

          <p className="text-sm font-medium text-gray-900 mb-1">
            {candidate.justificacion?.slice(0, 120)}
          </p>

          <pre className="text-[11px] text-gray-600 bg-gray-50 rounded p-2 overflow-x-auto max-h-24">
            {JSON.stringify(prop, null, 2).slice(0, 300)}
          </pre>

          {candidate.oferta_id && (
            <span className="text-[10px] text-gray-400 mt-1 inline-block">
              Oferta #{candidate.oferta_id}
              {candidate.issue_ids?.length > 0 && ` · Issue ${candidate.issue_ids[0].slice(0, 8)}`}
            </span>
          )}
        </div>

        <div className="flex flex-col gap-1.5 shrink-0">
          <Button
            size="sm"
            variant="outline"
            disabled={processing}
            onClick={onApprove}
            className="h-7 text-xs hover:bg-green-50 hover:text-green-700"
          >
            {processing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 mr-1" />}
            Aprobar
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={processing}
            onClick={onReject}
            className="h-7 text-xs hover:bg-red-50 hover:text-red-700"
          >
            <X className="w-3 h-3 mr-1" />
            Rechazar
          </Button>
        </div>
      </div>
    </div>
  );
}
