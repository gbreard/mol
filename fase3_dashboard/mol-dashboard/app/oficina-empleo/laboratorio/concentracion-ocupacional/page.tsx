"use client";
import { OEBreadcrumb } from "@/components/oficina-empleo/OEBreadcrumb";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  PieChart,
  BarChart3,
  Hash,
  TrendingUp,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import {
  getConcentracionOcupacional,
  ConcentracionOcupacional,
} from "@/lib/supabase";
import { ChartContainer } from "@/components/ChartContainer";
import {
  ConcentracionOcupacionalChart,
  CLASIFICACION_COLORS,
} from "@/components/laboratorio/ConcentracionOcupacionalChart";
import { InsightList, InsightItem } from "@/components/laboratorio/InsightList";

type SortKey = "isco_code" | "isco_label" | "ofertas" | "share_pct";

export default function ConcentracionOcupacionalPage() {
  const [data, setData] = useState<ConcentracionOcupacional[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("share_pct");
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const result = await getConcentracionOcupacional();
        setData(result);
      } catch (err) {
        console.error("Error loading concentracion data:", err);
        setError("Error al cargar datos de concentracion ocupacional.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const ocupaciones = data.filter((d) => d.tipo === "ocupacion");
  const globalRow = data.find((d) => d.tipo === "global");
  const hhiGlobal = globalRow?.hhi ?? 0;
  const clasificacion = globalRow?.clasificacion ?? "desconocido";

  const sortedOcupaciones = useMemo(() => {
    return [...ocupaciones].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDesc ? bVal - aVal : aVal - bVal;
      }
      return sortDesc
        ? String(bVal).localeCompare(String(aVal))
        : String(aVal).localeCompare(String(bVal));
    });
  }, [ocupaciones, sortKey, sortDesc]);

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
        <span className="ml-3 text-gray-600">
          Cargando datos de concentracion...
        </span>
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

  const top1 = ocupaciones[0];

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
        <OEBreadcrumb items={[{ label: "Indicadores", href: "/oficina-empleo/dashboard-ejecutivo" }, { label: "Concentracion Ocupacional" }]} />
      {/* Header */}
      <div>
        <Link
          href="/oficina-empleo"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Laboratorio
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">
            Concentracion Ocupacional
          </h1>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Experimental
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Indicador I-02: Indice HHI de concentracion de ofertas por ocupacion
          ISCO
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <PieChart className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              HHI Global
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {hhiGlobal.toFixed(4)}
          </p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-4 h-4 text-green-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Clasificacion
            </span>
          </div>
          <p
            className="text-2xl font-bold capitalize"
            style={{
              color: CLASIFICACION_COLORS[clasificacion] || "#6b7280",
            }}
          >
            {clasificacion}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Hash className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Ocupaciones
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {ocupaciones.length}
          </p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-orange-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Top 1 Share
            </span>
          </div>
          <p className="text-3xl font-bold text-orange-700">
            {top1 ? `${top1.share_pct}%` : "—"}
          </p>
        </div>
      </div>

      {/* Chart with Insights */}
      <ChartContainer
        title="Top 10 ocupaciones por concentracion"
        subtitle={`${ocupaciones.length} ocupaciones analizadas — HHI ${hhiGlobal.toFixed(4)}`}
        insights={
          <InsightList>
            <InsightItem
              text={`Mercado ${clasificacion}: HHI de ${hhiGlobal.toFixed(4)}`}
              highlight={clasificacion === "concentrado"}
            />
            {top1 && (
              <InsightItem
                text={`"${top1.isco_label}" lidera con ${top1.share_pct}% del total`}
                highlight
              />
            )}
            <InsightItem
              text="HHI < 0.15 = diversificado, 0.15-0.25 = moderado, > 0.25 = concentrado"
            />
            <InsightItem
              text="Un mercado concentrado indica que pocas ocupaciones acaparan la mayor parte de la demanda"
            />
          </InsightList>
        }
      >
        <ConcentracionOcupacionalChart
          topOcupaciones={ocupaciones}
          hhiGlobal={hhiGlobal}
          clasificacion={clasificacion}
        />
      </ChartContainer>

      {/* Methodology */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Metodologia</h3>
        <div className="grid grid-cols-2 gap-6 text-sm text-gray-700">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Indice Herfindahl-Hirschman (HHI)
            </h4>
            <p>
              Suma de los cuadrados de las participaciones (share) de cada
              ocupacion en el total de ofertas. Mide la concentracion del
              mercado: cuanto mayor el HHI, mas concentrada la demanda en
              pocas ocupaciones.
            </p>
            <p className="mt-2 font-mono text-xs bg-gray-50 p-2 rounded">
              HHI = Sum(share_i^2) donde share_i = ofertas_i / total
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Umbrales</h4>
            <div className="space-y-2">
              {[
                { name: "Diversificado", range: "HHI < 0.15", desc: "Demanda distribuida entre muchas ocupaciones" },
                { name: "Moderado", range: "0.15 - 0.25", desc: "Concentracion moderada en algunas ocupaciones" },
                { name: "Concentrado", range: "HHI > 0.25", desc: "Pocas ocupaciones dominan la demanda" },
              ].map((u) => (
                <div
                  key={u.name}
                  className="border rounded-lg p-2"
                  style={{
                    borderColor:
                      CLASIFICACION_COLORS[u.name.toLowerCase()] || "#e5e7eb",
                  }}
                >
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor:
                          CLASIFICACION_COLORS[u.name.toLowerCase()] || "#6b7280",
                      }}
                    />
                    <span className="text-xs font-bold">
                      {u.name} ({u.range})
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{u.desc}</p>
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
            Top 15 ocupaciones
          </h3>
          <p className="text-sm text-gray-500">
            {ocupaciones.length} ocupaciones — click en columna para ordenar
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {[
                  { key: "isco_code" as SortKey, label: "ISCO" },
                  { key: "isco_label" as SortKey, label: "Ocupacion" },
                  { key: "ofertas" as SortKey, label: "Ofertas" },
                  { key: "share_pct" as SortKey, label: "Share %" },
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
              {sortedOcupaciones.map((row) => (
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
                    {row.ofertas}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.share_pct}%
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
