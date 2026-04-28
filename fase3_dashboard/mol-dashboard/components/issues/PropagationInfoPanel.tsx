/**
 * Panel informativo del estado de propagación de un issue.
 * Read-only — visible para todos los roles.
 * SPEC T Fase 4.
 */
"use client";

import { useState } from "react";
import type { Issue, PropagationPattern } from "@/lib/types";
import { PROPAGATION_TIPO_LABELS } from "@/lib/types";
import { PropagationBadge, getPropagationEstado } from "./PropagationBadge";

interface Props {
  issue: Issue;
  isAdmin?: boolean;
  onSolicitar?: () => void;
  onCancelarSolicitud?: () => void;
}

export function PropagationInfoPanel({
  issue,
  isAdmin = false,
  onSolicitar,
  onCancelarSolicitud,
}: Props) {
  const [showHelp, setShowHelp] = useState(false);
  const estado = getPropagationEstado(issue);
  const patron = issue.patron_corregido as PropagationPattern | undefined;

  return (
    <section className="border rounded-lg p-4 bg-card">
      <header className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          Propagación
          <PropagationBadge issue={issue} size="sm" />
        </h3>
        <button
          type="button"
          onClick={() => setShowHelp((v) => !v)}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          ¿Qué es esto?
        </button>
      </header>

      {showHelp && (
        <div className="mb-3 p-3 rounded bg-muted text-xs space-y-2">
          <p className="font-medium">¿Qué es la propagación?</p>
          <p>
            Cuando reportás un error, hay que arreglarlo en la oferta que viste, pero
            puede ser que el mismo error esté en muchas otras ofertas similares. La
            "propagación" busca esas ofertas y aplica la misma corrección a todas.
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>✅ Podés <b>ver</b> si una corrección ya se propagó</li>
            <li>✅ Podés <b>solicitar</b> que se propague (si creés que hay similares)</li>
            {!isAdmin && <li>❌ NO aplicás la propagación directamente</li>}
            {isAdmin && <li>✅ Como admin, <b>aplicás</b> la propagación tras controles previos</li>}
          </ul>
          {!isAdmin && (
            <p className="text-muted-foreground italic">
              Quien aplica: el admin (Gerardo) hace controles previos antes de modificar
              cientos de ofertas.
            </p>
          )}
        </div>
      )}

      {estado === "aplicada" && patron && (
        <div className="space-y-2 text-sm">
          <p className="text-green-700 dark:text-green-400">
            ✅ Esta corrección se propagó a <b>{issue.propagacion_n}</b> ofertas similares.
          </p>
          <DetallePatron patron={patron} />
        </div>
      )}

      {estado === "solicitada" && (
        <div className="space-y-2 text-sm">
          <p className="text-amber-700 dark:text-amber-400">
            🟡 Solicitada por <b>{issue.propagacion_solicitada_por ?? "?"}</b>
            {issue.propagacion_solicitada_at &&
              ` el ${new Date(issue.propagacion_solicitada_at).toLocaleString("es-AR", {
                dateStyle: "short",
                timeStyle: "short",
              })}`}
            — pendiente revisión admin.
          </p>
          <p className="text-xs text-muted-foreground italic">
            ⏳ El admin va a hacer dry-run + controles antes de aplicar.
          </p>
          {onCancelarSolicitud && (
            <button
              type="button"
              onClick={onCancelarSolicitud}
              className="text-xs text-red-600 hover:underline"
            >
              Cancelar solicitud
            </button>
          )}
        </div>
      )}

      {estado === "excepcion" && patron && (
        <div className="space-y-2 text-sm">
          <p className="text-muted-foreground">
            ➡ Caso puntual: la corrección NO aplica a otras ofertas similares.
          </p>
          <DetallePatron patron={patron} />
        </div>
      )}

      {estado === "sin_auditar" && (
        <div className="space-y-3 text-sm">
          <p className="text-orange-700 dark:text-orange-400">
            ⚠ Este issue se cerró antes del sistema de propagación SPEC T. No hay
            registro de si la corrección se aplicó a ofertas similares.
          </p>
          {issue.estado === "resuelto" && onSolicitar && (
            <div className="pt-2 border-t">
              <p className="text-xs mb-2">
                ¿Considerás que esta corrección debería aplicarse a otras ofertas
                similares?
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={onSolicitar}
                  className="px-3 py-1.5 text-xs rounded bg-blue-600 text-white hover:bg-blue-700"
                >
                  Sí, solicitar propagación
                </button>
                <button
                  type="button"
                  className="px-3 py-1.5 text-xs rounded border hover:bg-muted"
                  disabled
                  title="(no requiere acción)"
                >
                  No, fue puntual
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function DetallePatron({ patron }: { patron: PropagationPattern }) {
  return (
    <dl className="text-xs grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 mt-2 p-2 bg-muted rounded">
      <dt className="text-muted-foreground">Tipo:</dt>
      <dd>{PROPAGATION_TIPO_LABELS[patron.tipo] ?? patron.tipo}</dd>
      <dt className="text-muted-foreground">Condición:</dt>
      <dd className="font-mono">
        {patron.condicion?.tipo}
        {patron.condicion?.valor_unico && ` = ${patron.condicion.valor_unico}`}
        {patron.condicion?.keywords && ` (${patron.condicion.keywords.length} keywords)`}
      </dd>
      {patron.valor_anterior && (
        <>
          <dt className="text-muted-foreground">Anterior:</dt>
          <dd className="font-mono">{patron.valor_anterior}</dd>
        </>
      )}
      {patron.valor_nuevo && (
        <>
          <dt className="text-muted-foreground">Nuevo:</dt>
          <dd className="font-mono">{patron.valor_nuevo}</dd>
        </>
      )}
    </dl>
  );
}
