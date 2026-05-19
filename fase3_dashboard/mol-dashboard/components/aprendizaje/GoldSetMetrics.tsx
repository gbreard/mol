"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, AlertCircle } from "lucide-react";

interface ValidadorStats {
  validador: string;
  total: number;
  ok: number;
  errores: number;
}

interface CoberturaRun {
  run_id: string;
  en_gold: number;
  acierto: number;
  errores: number;
  sin_clasificacion: number;
  tasa_acierto: number;
}

interface GoldCaso {
  id_oferta: string;
  esco_ok_humano: boolean;
  isco_esperado: string | null;
  esco_esperado: string | null;
  isco_actual: string | null;
  isco_label_actual: string | null;
  agregado_por: string | null;
  agregado_at: string | null;
}

interface GoldMetrics {
  total: number;
  ok: number;
  errores: number;
  tasa_acierto: number;
  por_validador: ValidadorStats[];
  cobertura_por_run: CoberturaRun[];
  casos: GoldCaso[];
}

function fmtDate(ts: string | null): string {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleDateString("es-AR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  } catch {
    return ts;
  }
}

export function GoldSetMetrics() {
  const [data, setData] = useState<GoldMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/gold-set-metrics");
        if (!res.ok) {
          setError(`Error ${res.status}`);
          return;
        }
        const json = await res.json();
        setData(json);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error desconocido");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <div className="h-64 animate-pulse rounded-xl bg-gray-100" />;
  }
  if (error) {
    return <p className="text-sm text-red-500">No se pudo cargar gold set: {error}</p>;
  }
  if (!data || data.total === 0) {
    return (
      <p className="text-sm text-gray-400 italic">
        Sin gold set conectado todavía.
      </p>
    );
  }

  const tasaColor =
    data.tasa_acierto >= 90 ? "text-green-600" :
    data.tasa_acierto >= 70 ? "text-amber-600" :
    "text-red-600";

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg lg:text-xl font-semibold text-gray-900">Gold Set real</h2>
        <p className="text-xs lg:text-sm text-gray-500">
          Casos validados por humano. Métrica honesta de calidad del matcher.
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl border border-gray-200 bg-white p-3 text-center">
          <p className="text-2xl font-bold text-gray-900">{data.total}</p>
          <p className="text-[10px] lg:text-xs text-gray-500 mt-1">Casos totales</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-3 text-center">
          <p className="text-2xl font-bold text-green-600">{data.ok}</p>
          <p className="text-[10px] lg:text-xs text-gray-500 mt-1">Confirmados OK</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-3 text-center">
          <p className="text-2xl font-bold text-red-600">{data.errores}</p>
          <p className="text-[10px] lg:text-xs text-gray-500 mt-1">Marcados error</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-3 text-center">
          <p className={`text-2xl font-bold ${tasaColor}`}>{data.tasa_acierto}%</p>
          <p className="text-[10px] lg:text-xs text-gray-500 mt-1">Tasa acierto</p>
        </div>
      </div>

      {/* Distribución por validador */}
      {data.por_validador.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Aportes por validador</h3>
          <table className="w-full text-xs lg:text-sm">
            <thead className="text-gray-500">
              <tr>
                <th className="text-left py-1.5 font-medium">Validador</th>
                <th className="text-right py-1.5 font-medium">Casos</th>
                <th className="text-right py-1.5 font-medium">OK</th>
                <th className="text-right py-1.5 font-medium">Errores</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.por_validador.map((v) => (
                <tr key={v.validador}>
                  <td className="py-1.5 text-gray-700 font-mono text-[10px] lg:text-xs">{v.validador}</td>
                  <td className="text-right tabular-nums">{v.total}</td>
                  <td className="text-right tabular-nums text-green-700">{v.ok}</td>
                  <td className="text-right tabular-nums text-red-700">{v.errores}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Cobertura por run */}
      {data.cobertura_por_run.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">
            Acierto por corrida (runs con ≥3 casos en gold)
          </h3>
          <table className="w-full text-xs lg:text-sm">
            <thead className="text-gray-500">
              <tr>
                <th className="text-left py-1.5 font-medium">Run</th>
                <th className="text-right py-1.5 font-medium">En gold</th>
                <th className="text-right py-1.5 font-medium">Acierto</th>
                <th className="text-right py-1.5 font-medium">%</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.cobertura_por_run.map((r) => {
                const color =
                  r.tasa_acierto >= 90 ? "text-green-700" :
                  r.tasa_acierto >= 70 ? "text-amber-700" :
                  "text-red-700";
                return (
                  <tr key={r.run_id}>
                    <td className="py-1.5 font-mono text-[10px] lg:text-xs text-gray-700">{r.run_id}</td>
                    <td className="text-right tabular-nums">{r.en_gold}</td>
                    <td className="text-right tabular-nums">{r.acierto}/{r.en_gold}</td>
                    <td className={`text-right tabular-nums font-medium ${color}`}>{r.tasa_acierto}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Casos individuales */}
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-gray-800 mb-2">
          Casos individuales ({data.casos.length} de {data.total})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs lg:text-sm">
            <thead className="text-gray-500">
              <tr>
                <th className="w-8 py-1.5"></th>
                <th className="text-left py-1.5 font-medium">Oferta</th>
                <th className="text-left py-1.5 font-medium">ISCO actual</th>
                <th className="text-left py-1.5 font-medium">ISCO esperado</th>
                <th className="text-left py-1.5 font-medium">Validó</th>
                <th className="text-right py-1.5 font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.casos.map((c) => {
                const matches =
                  c.esco_ok_humano === true ? true :
                  (c.isco_esperado && c.isco_actual === c.isco_esperado) ? true :
                  c.esco_ok_humano === false && !c.isco_esperado ? null : false;
                return (
                  <tr key={c.id_oferta} className={matches === false ? "bg-red-50" : ""}>
                    <td className="py-1.5">
                      {matches === true ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : matches === false ? (
                        <XCircle className="h-4 w-4 text-red-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-amber-500" />
                      )}
                    </td>
                    <td className="py-1.5 font-mono text-[10px] lg:text-xs text-gray-700">{c.id_oferta}</td>
                    <td className="py-1.5 font-mono text-[10px] lg:text-xs">{c.isco_actual || "—"}</td>
                    <td className="py-1.5 font-mono text-[10px] lg:text-xs text-gray-500">
                      {c.isco_esperado || (c.esco_ok_humano ? "(OK)" : "?")}
                    </td>
                    <td className="py-1.5 text-[10px] lg:text-xs text-gray-600">
                      {(c.agregado_por || "—").split("@")[0]}
                    </td>
                    <td className="py-1.5 text-right text-[10px] lg:text-xs text-gray-500">
                      {fmtDate(c.agregado_at)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
