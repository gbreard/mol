/**
 * Panel admin para procesar una solicitud de propagación.
 * Solo visible si rol=admin/super_admin Y issue tiene propagacion_solicitada=true
 * (o admin quiere procesar manualmente cualquier issue).
 *
 * SPEC T Fase 4. 3 estados: estructurar patrón → dry-run → aplicar.
 */
"use client";

import { useState } from "react";
import type { Issue, PropagationPattern, PropagationTipo } from "@/lib/types";
import { PROPAGATION_TIPO_LABELS } from "@/lib/types";

interface Props {
  issue: Issue;
  onApplied?: () => void;
}

type Step = "estructurar" | "dry-run" | "aplicado";

export function ProcessPropagationPanel({ issue, onApplied }: Props) {
  const [step, setStep] = useState<Step>("estructurar");
  const [patron, setPatron] = useState<PropagationPattern>(() =>
    inferPatronInicial(issue)
  );
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDryRun() {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/issues/${issue.id}/propagation/dry-run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patron }),
      });
      const j = await res.json();
      if (!res.ok) throw new Error(j.error ?? `HTTP ${res.status}`);
      setDryRunResult(j.result as DryRunResult);
      setStep("dry-run");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleApply() {
    if (!confirm(`¿Aplicar propagación a ${dryRunResult?.ofertas_identificadas} ofertas?`)) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/issues/${issue.id}/propagation/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patron }),
      });
      const j = await res.json();
      if (!res.ok) throw new Error(j.error ?? `HTTP ${res.status}`);
      setStep("aplicado");
      onApplied?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRechazar() {
    const motivo = prompt("Motivo del rechazo (opcional):");
    if (motivo === null) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/issues/${issue.id}/propagation/rechazar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ motivo }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error ?? `HTTP ${res.status}`);
      }
      onApplied?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="border rounded-lg p-4 bg-amber-50 dark:bg-amber-950/20 border-amber-300 dark:border-amber-800">
      <header className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">⚙ Procesar propagación (admin)</h3>
        <span className="text-xs text-muted-foreground">
          Paso {step === "estructurar" ? "1" : step === "dry-run" ? "2" : "3"} / 3
        </span>
      </header>

      {issue.propagacion_solicitada && (
        <div className="mb-3 text-xs bg-background rounded p-2 border">
          <p>
            <b>Solicitante:</b> {issue.propagacion_solicitada_por ?? "?"}
          </p>
          {issue.propagacion_solicitada_at && (
            <p>
              <b>Solicitada:</b>{" "}
              {new Date(issue.propagacion_solicitada_at).toLocaleString("es-AR")}
            </p>
          )}
        </div>
      )}

      {step === "estructurar" && (
        <PatronEditor patron={patron} onChange={setPatron} />
      )}

      {step === "dry-run" && dryRunResult && (
        <DryRunDisplay result={dryRunResult} />
      )}

      {step === "aplicado" && (
        <div className="bg-green-100 dark:bg-green-950/30 rounded p-3 text-sm text-green-800 dark:text-green-300">
          ✅ Propagación aplicada. La oferta del issue se actualizó con el patrón.
        </div>
      )}

      {error && (
        <div className="mt-3 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 text-sm p-2 rounded">
          {error}
        </div>
      )}

      <footer className="flex gap-2 justify-end mt-4 pt-3 border-t border-amber-200 dark:border-amber-800">
        {step === "estructurar" && (
          <>
            {issue.propagacion_solicitada && (
              <button
                type="button"
                onClick={handleRechazar}
                disabled={submitting}
                className="px-3 py-1.5 text-xs border rounded hover:bg-muted disabled:opacity-50"
              >
                ✗ Rechazar solicitud
              </button>
            )}
            <button
              type="button"
              onClick={handleDryRun}
              disabled={submitting || !patron.condicion?.tipo}
              className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? "Estimando..." : "⏵ Estimar (dry-run)"}
            </button>
          </>
        )}
        {step === "dry-run" && (
          <>
            <button
              type="button"
              onClick={() => setStep("estructurar")}
              className="px-3 py-1.5 text-xs border rounded hover:bg-muted"
            >
              ← Editar patrón
            </button>
            <button
              type="button"
              onClick={handleApply}
              disabled={submitting || !dryRunResult?.ofertas_identificadas}
              className="px-3 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
            >
              {submitting
                ? "Aplicando..."
                : `⏯ Aplicar a las ${dryRunResult?.ofertas_identificadas ?? 0}`}
            </button>
          </>
        )}
      </footer>
    </section>
  );
}

interface DryRunResult {
  tipo: string;
  ofertas_identificadas: number;
  ofertas_actualizadas: number;
  ids_tocados: number[];
  errores: string[];
  dry_run: boolean;
}

function DryRunDisplay({ result }: { result: DryRunResult }) {
  const sample = result.ids_tocados.slice(0, 5);
  return (
    <div className="space-y-2 text-sm">
      <p>
        📊 <b>{result.ofertas_identificadas}</b> ofertas matchean el patrón
      </p>
      {sample.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-1">Sample (primeras 5):</p>
          <ul className="text-xs font-mono space-y-0.5">
            {sample.map((id) => (
              <li key={id}>· {id}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="text-xs text-amber-700 dark:text-amber-400 mt-2">
        ⚠ Esta acción modificará {result.ofertas_identificadas} ofertas en BD y
        dashboard. Antes de aplicar verificá que el patrón es correcto.
      </p>
    </div>
  );
}

interface PatronEditorProps {
  patron: PropagationPattern;
  onChange: (p: PropagationPattern) => void;
}

function PatronEditor({ patron, onChange }: PatronEditorProps) {
  return (
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium mb-1">Tipo</label>
          <select
            value={patron.tipo}
            onChange={(e) =>
              onChange({ ...patron, tipo: e.target.value as PropagationTipo })
            }
            className="w-full border rounded px-2 py-1 text-sm bg-background"
          >
            {(Object.keys(PROPAGATION_TIPO_LABELS) as PropagationTipo[]).map((t) => (
              <option key={t} value={t}>
                {PROPAGATION_TIPO_LABELS[t]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Campo</label>
          <input
            type="text"
            value={patron.campo}
            onChange={(e) => onChange({ ...patron, campo: e.target.value })}
            className="w-full border rounded px-2 py-1 text-sm"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium mb-1">Condición - tipo</label>
        <select
          value={patron.condicion.tipo}
          onChange={(e) =>
            onChange({
              ...patron,
              condicion: { ...patron.condicion, tipo: e.target.value as PropagationPattern["condicion"]["tipo"] },
            })
          }
          className="w-full border rounded px-2 py-1 text-sm bg-background"
        >
          <option value="titulo_contiene_alguno">titulo_contiene_alguno</option>
          <option value="regla_aplicada">regla_aplicada</option>
          <option value="titulo_esco_code">titulo_esco_code</option>
          <option value="id_oferta_lista">id_oferta_lista</option>
        </select>
      </div>

      {patron.condicion.tipo === "titulo_contiene_alguno" ? (
        <div>
          <label className="block text-xs font-medium mb-1">
            Keywords (uno por línea)
          </label>
          <textarea
            value={patron.condicion.keywords?.join("\n") ?? ""}
            onChange={(e) =>
              onChange({
                ...patron,
                condicion: {
                  ...patron.condicion,
                  keywords: e.target.value
                    .split("\n")
                    .map((k) => k.trim())
                    .filter(Boolean),
                },
              })
            }
            className="w-full border rounded px-2 py-1 text-sm font-mono min-h-[80px]"
          />
        </div>
      ) : patron.condicion.tipo === "id_oferta_lista" ? (
        <div>
          <label className="block text-xs font-medium mb-1">
            IDs de oferta (uno por línea o coma)
          </label>
          <textarea
            value={patron.condicion.valores?.join("\n") ?? ""}
            onChange={(e) =>
              onChange({
                ...patron,
                condicion: {
                  ...patron.condicion,
                  valores: e.target.value
                    .split(/[\s,]+/)
                    .map((k) => k.trim())
                    .filter(Boolean),
                },
              })
            }
            className="w-full border rounded px-2 py-1 text-sm font-mono min-h-[60px]"
          />
        </div>
      ) : (
        <div>
          <label className="block text-xs font-medium mb-1">Valor único</label>
          <input
            type="text"
            value={patron.condicion.valor_unico ?? ""}
            onChange={(e) =>
              onChange({
                ...patron,
                condicion: { ...patron.condicion, valor_unico: e.target.value },
              })
            }
            className="w-full border rounded px-2 py-1 text-sm font-mono"
            placeholder="ej: R236_analista_marketing"
          />
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium mb-1">Valor anterior</label>
          <input
            type="text"
            value={patron.valor_anterior ?? ""}
            onChange={(e) => onChange({ ...patron, valor_anterior: e.target.value })}
            className="w-full border rounded px-2 py-1 text-sm font-mono"
            placeholder="ej: 9333.3"
          />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">
            Valor nuevo {patron.tipo !== "skills_filtro" && <span className="text-red-500">*</span>}
          </label>
          <input
            type="text"
            value={patron.valor_nuevo ?? ""}
            onChange={(e) => onChange({ ...patron, valor_nuevo: e.target.value })}
            className="w-full border rounded px-2 py-1 text-sm font-mono"
            placeholder="ej: 8343.4"
          />
        </div>
      </div>
    </div>
  );
}

function inferPatronInicial(issue: Issue): PropagationPattern {
  // Si ya tiene patrón previo (re-edit), usarlo
  const prev = issue.patron_corregido as PropagationPattern | undefined;
  if (prev?.tipo) return prev;

  // Default: matching_esco con id_oferta del issue
  return {
    tipo: "matching_esco",
    campo: "esco_label",
    condicion: {
      tipo: "id_oferta_lista",
      valores: issue.id_oferta ? [issue.id_oferta] : [],
    },
    valor_anterior: "",
    valor_nuevo: "",
  };
}
