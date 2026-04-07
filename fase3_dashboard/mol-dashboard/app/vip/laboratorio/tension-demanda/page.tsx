"use client";
import { OEBreadcrumb } from "@/components/oficina-empleo/OEBreadcrumb";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Zap,
  Users,
  AlertTriangle,
  BarChart3,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { getTensionOcupaciones, TensionOcupacion } from "@/lib/supabase";
import { ChartContainer } from "@/components/ChartContainer";
import {
  TensionDemandaChart,
  CUADRANTE_COLORS,
} from "@/components/laboratorio/TensionDemandaChart";
import { InsightList, InsightItem } from "@/components/laboratorio/InsightList";

type SortKey = "isco_code" | "isco_label" | "total_posiciones" | "total_ofertas" | "persistencia" | "insistencia" | "cuadrante";

export default function TensionDemandaPage() {
  const [data, setData] = useState<TensionOcupacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("total_posiciones");
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const result = await getTensionOcupaciones();
        setData(result);
      } catch (err) {
        console.error("Error loading tension data:", err);
        setError("Error al cargar datos de tension de demanda.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const cuadranteCounts: Record<string, number> = {};
  data.forEach((d) => {
    cuadranteCounts[d.cuadrante] = (cuadranteCounts[d.cuadrante] || 0) + 1;
  });

  const totalPosiciones = data.reduce((s, d) => s + d.total_posiciones, 0);

  const sortedData = useMemo(() => {
    const sorted = [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDesc ? bVal - aVal : aVal - bVal;
      }
      return sortDesc
        ? String(bVal).localeCompare(String(aVal))
        : String(aVal).localeCompare(String(bVal));
    });
    return sorted;
  }, [data, sortKey, sortDesc]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDesc(!sortDesc);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  };

  const SortIcon = ({ columnKey }: { columnKey: SortKey }) => {
    if (sortKey !== columnKey)
      return <ChevronDown className="w-3 h-3 text-gray-300" />;
    return sortDesc ? (
      <ChevronDown className="w-3 h-3 text-gray-700" />
    ) : (
      <ChevronUp className="w-3 h-3 text-gray-700" />
    );
  };

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Cargando datos de tension...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-6xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">Error</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
        <OEBreadcrumb items={[{ label: "Indicadores", href: "/oficina-empleo/dashboard-ejecutivo" }, { label: "Tension Demanda" }]} />
      {/* Header */}
      <div>
        <Link
          href="/vip/dashboard"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Laboratorio
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">
            Tension de Demanda
          </h1>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Experimental
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Indicador V-16: Persistencia x Insistencia por ocupacion ISCO
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Ocupaciones
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{data.length}</p>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Critico
            </span>
          </div>
          <p className="text-3xl font-bold text-red-700">
            {cuadranteCounts["CRITICO"] || 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-orange-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Urgente
            </span>
          </div>
          <p className="text-3xl font-bold text-orange-700">
            {cuadranteCounts["URGENTE"] || 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Users className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Total posiciones
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {totalPosiciones.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Chart with Insights */}
      <ChartContainer
        title="Tension de demanda por ocupacion"
        subtitle={`${data.length} ocupaciones — 4 cuadrantes`}
        insights={
          <InsightList>
            {cuadranteCounts["CRITICO"] ? (
              <InsightItem
                text={`${cuadranteCounts["CRITICO"]} ocupaciones en estado critico (alta persistencia + alta insistencia)`}
                highlight
              />
            ) : null}
            {cuadranteCounts["URGENTE"] ? (
              <InsightItem
                text={`${cuadranteCounts["URGENTE"]} urgentes: persisten pero no se republican`}
              />
            ) : null}
            <InsightItem
              text={`${cuadranteCounts["FLUIDO"] || 0} ocupaciones con demanda fluida (se cubren rapidamente)`}
            />
            <InsightItem
              text={`Umbral: 50% en ambos ejes divide los 4 cuadrantes`}
            />
          </InsightList>
        }
      >
        <TensionDemandaChart data={data} />
      </ChartContainer>

      {/* Methodology */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Metodologia</h3>
        <div className="grid grid-cols-2 gap-6 text-sm text-gray-700">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Persistencia (eje X)
            </h4>
            <p>
              Porcentaje de posiciones cuya ventana de publicacion supera los 45
              dias. Valores altos indican que las vacantes permanecen abiertas
              mucho tiempo, sugiriendo dificultad para cubrir la posicion.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Insistencia (eje Y)
            </h4>
            <p>
              Porcentaje de posiciones que fueron republicadas (mismo aviso
              publicado multiples veces). Valores altos sugieren que la empresa
              necesita re-publicar porque no encuentra candidatos.
            </p>
          </div>
          <div className="col-span-2">
            <h4 className="font-semibold text-gray-900 mb-2">Cuadrantes</h4>
            <div className="grid grid-cols-4 gap-3">
              {[
                {
                  name: "CRITICO",
                  desc: "Alta persistencia + alta insistencia. Vacantes dificiles de cubrir que se republican constantemente.",
                },
                {
                  name: "URGENTE",
                  desc: "Alta persistencia + baja insistencia. Permanecen abiertas mucho tiempo pero no se re-publican.",
                },
                {
                  name: "PASIVO",
                  desc: "Baja persistencia + alta insistencia. Se cubren rapido pero se re-publican (alta rotacion).",
                },
                {
                  name: "FLUIDO",
                  desc: "Baja persistencia + baja insistencia. Mercado funcional: se publican y cubren sin friccion.",
                },
              ].map((q) => (
                <div
                  key={q.name}
                  className="border rounded-lg p-3"
                  style={{
                    borderColor:
                      CUADRANTE_COLORS[q.name] || "#e5e7eb",
                  }}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{
                        backgroundColor:
                          CUADRANTE_COLORS[q.name] || "#6b7280",
                      }}
                    />
                    <span className="text-xs font-bold">{q.name}</span>
                  </div>
                  <p className="text-xs text-gray-600">{q.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">
            Detalle por ocupacion
          </h3>
          <p className="text-sm text-gray-500">
            {data.length} ocupaciones — click en columna para ordenar
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {[
                  { key: "isco_code" as SortKey, label: "ISCO" },
                  { key: "isco_label" as SortKey, label: "Ocupacion" },
                  { key: "total_posiciones" as SortKey, label: "Posiciones" },
                  { key: "total_ofertas" as SortKey, label: "Ofertas" },
                  { key: "persistencia" as SortKey, label: "Persistencia" },
                  { key: "insistencia" as SortKey, label: "Insistencia" },
                  { key: "cuadrante" as SortKey, label: "Cuadrante" },
                ].map((col) => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase cursor-pointer hover:bg-gray-100 transition-colors select-none"
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      <SortIcon columnKey={col.key} />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedData.map((row) => (
                <tr
                  key={row.isco_code}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">
                    {row.isco_code}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {row.isco_label}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.total_posiciones}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.total_ofertas}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.persistencia}%
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.insistencia}%
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold"
                      style={{
                        backgroundColor: `${CUADRANTE_COLORS[row.cuadrante] || "#6b7280"}15`,
                        color:
                          CUADRANTE_COLORS[row.cuadrante] || "#6b7280",
                      }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          backgroundColor:
                            CUADRANTE_COLORS[row.cuadrante] || "#6b7280",
                        }}
                      />
                      {row.cuadrante}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
