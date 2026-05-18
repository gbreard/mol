"use client";

import { useState, useEffect, useMemo } from "react";

export interface PipelineRun {
  run_id: string;
  timestamp: string;
  source: string | null;
  description: string | null;
  git_branch: string | null;
  git_commit: string | null;
  nlp_version: string | null;
  matching_version: string | null;
  ofertas_count: number | null;
  failures_count: number | null;
  failures_pct: number | null;
  precision: number | null;
  errores_detectados: number | null;
  errores_corregidos: number | null;
  errores_escalados: number | null;
  reglas_nuevas: number | null;
  sinonimos_count: number | null;
  delta_mejoras: number | null;
  delta_regresiones: number | null;
  run_anterior_id: string | null;
}

interface SourceOption {
  source: string;
  n: number;
}

function fmtDate(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString("es-AR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

function fmtPct(v: number | null): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

function fmtNum(v: number | null): string {
  if (v == null) return "—";
  return v.toLocaleString("es-AR");
}

export function PipelineRunsHistory() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [sources, setSources] = useState<SourceOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");
  const [matchingVersion, setMatchingVersion] = useState("");
  const [source, setSource] = useState("");
  const [limit, setLimit] = useState(50);

  const versions = useMemo(() => {
    const set = new Set(runs.map((r) => r.matching_version).filter(Boolean) as string[]);
    return Array.from(set).sort().reverse();
  }, [runs]);

  // Cargar sources una sola vez (no depende de filtros)
  useEffect(() => {
    const loadSources = async () => {
      try {
        const res = await fetch("/api/pipeline-runs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "list_sources" }),
        });
        if (res.ok) {
          const json = await res.json();
          setSources(json.sources || []);
        }
      } catch {
        // silent: si falla, el filtro queda vacío
      }
    };
    loadSources();
  }, []);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (since) params.set("since", since);
        if (until) params.set("until", until);
        if (matchingVersion) params.set("matching_version", matchingVersion);
        if (source) params.set("source", source);
        params.set("limit", String(limit));

        const res = await fetch(`/api/pipeline-runs?${params.toString()}`);
        if (!res.ok) {
          setError(`Error ${res.status}`);
          setRuns([]);
          return;
        }
        const json = await res.json();
        setRuns(json.runs || []);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error desconocido");
        setRuns([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [since, until, matchingVersion, source, limit]);

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg lg:text-xl font-semibold text-gray-900">Historial de corridas</h2>
        <p className="text-xs lg:text-sm text-gray-500">
          Cada fila es una corrida del pipeline (manual, reapply o régimen). El régimen 15-17 mayo está en este listado.
        </p>
      </div>

      <div className="flex flex-wrap gap-2 items-end">
        <div>
          <label htmlFor="prh-since" className="block text-[10px] lg:text-xs font-medium text-gray-500 mb-1">
            Desde
          </label>
          <input
            id="prh-since"
            type="date"
            value={since}
            onChange={(e) => setSince(e.target.value)}
            className="h-8 border border-gray-300 rounded px-2 text-xs lg:text-sm"
          />
        </div>
        <div>
          <label htmlFor="prh-until" className="block text-[10px] lg:text-xs font-medium text-gray-500 mb-1">
            Hasta
          </label>
          <input
            id="prh-until"
            type="date"
            value={until}
            onChange={(e) => setUntil(e.target.value)}
            className="h-8 border border-gray-300 rounded px-2 text-xs lg:text-sm"
          />
        </div>
        <div>
          <label htmlFor="prh-matcher" className="block text-[10px] lg:text-xs font-medium text-gray-500 mb-1">
            Matcher version
          </label>
          <select
            id="prh-matcher"
            value={matchingVersion}
            onChange={(e) => setMatchingVersion(e.target.value)}
            className="h-8 border border-gray-300 rounded px-2 text-xs lg:text-sm"
          >
            <option value="">Todas</option>
            {versions.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
        {sources.length > 0 && (
          <div>
            <label htmlFor="prh-source" className="block text-[10px] lg:text-xs font-medium text-gray-500 mb-1">
              Tipo (source)
            </label>
            <select
              id="prh-source"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="h-8 border border-gray-300 rounded px-2 text-xs lg:text-sm max-w-[200px]"
            >
              <option value="">Todos</option>
              {sources.map((s) => (
                <option key={s.source} value={s.source}>
                  {s.source} ({s.n})
                </option>
              ))}
            </select>
          </div>
        )}
        <div>
          <label htmlFor="prh-limit" className="block text-[10px] lg:text-xs font-medium text-gray-500 mb-1">
            Mostrar
          </label>
          <select
            id="prh-limit"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="h-8 border border-gray-300 rounded px-2 text-xs lg:text-sm"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
            <option value={500}>500</option>
          </select>
        </div>
        {(since || until || matchingVersion || source) && (
          <button
            onClick={() => {
              setSince("");
              setUntil("");
              setMatchingVersion("");
              setSource("");
            }}
            className="h-8 px-3 text-xs lg:text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {loading ? (
        <div className="h-64 animate-pulse rounded-xl bg-gray-100" />
      ) : error ? (
        <p className="text-sm text-red-500">No se pudo cargar el historial de corridas: {error}</p>
      ) : runs.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No hay corridas para los filtros seleccionados.</p>
      ) : (
        <div className="rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs lg:text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Run ID</th>
                  <th className="px-3 py-2 text-left font-medium">Fecha</th>
                  <th className="px-3 py-2 text-left font-medium">Tipo</th>
                  <th className="px-3 py-2 text-left font-medium">Matcher</th>
                  <th className="px-3 py-2 text-right font-medium">Ofertas</th>
                  <th className="px-3 py-2 text-right font-medium">Errores</th>
                  <th className="px-3 py-2 text-right font-medium">Corregidos</th>
                  <th className="px-3 py-2 text-right font-medium">Escalados</th>
                  <th className="px-3 py-2 text-right font-medium">Precision</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {runs.map((r) => (
                  <tr key={r.run_id} className="hover:bg-gray-50">
                    <td
                      className="px-3 py-1.5 font-mono text-[10px] lg:text-xs text-gray-700"
                      title={r.description || undefined}
                    >
                      {r.run_id}
                    </td>
                    <td className="px-3 py-1.5 text-gray-700">{fmtDate(r.timestamp)}</td>
                    <td className="px-3 py-1.5">
                      {r.source ? (
                        <span className="text-[10px] lg:text-xs text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">
                          {r.source}
                        </span>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-3 py-1.5">
                      <span className="font-mono text-[10px] lg:text-xs text-gray-500">
                        {r.matching_version || "—"}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{fmtNum(r.ofertas_count)}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{fmtNum(r.errores_detectados)}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-green-700">{fmtNum(r.errores_corregidos)}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-amber-700">{fmtNum(r.errores_escalados)}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{fmtPct(r.precision)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="bg-gray-50 px-3 py-1.5 text-[10px] lg:text-xs text-gray-500 border-t">
            {runs.length} {runs.length === 1 ? "corrida" : "corridas"}
          </div>
        </div>
      )}
    </div>
  );
}
