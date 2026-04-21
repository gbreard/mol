"use client";
import { OEBreadcrumb } from "@/components/oficina-empleo/OEBreadcrumb";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Cpu,
  BarChart3,
  TrendingUp,
  TrendingDown,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { getDigitalizacionSector, DigitalizacionSector } from "@/lib/supabase";
import { ChartContainer } from "@/components/ChartContainer";
import {
  DigitalizacionSectorChart,
  NIVEL_COLORS,
} from "@/components/laboratorio/DigitalizacionSectorChart";
import { InsightList, InsightItem } from "@/components/laboratorio/InsightList";

type SortKey =
  | "clae_seccion"
  | "total_skills"
  | "skills_digitales"
  | "total_ofertas"
  | "idx_digital"
  | "nivel_digital";

export default function DigitalizacionSectorPage() {
  const [data, setData] = useState<DigitalizacionSector[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("idx_digital");
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const result = await getDigitalizacionSector();
        setData(result);
      } catch (err) {
        console.error("Error loading digitalizacion data:", err);
        setError("Error al cargar datos de digitalizacion por sector.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const nivelCounts: Record<string, number> = {};
  data.forEach((d) => {
    nivelCounts[d.nivel_digital] = (nivelCounts[d.nivel_digital] || 0) + 1;
  });

  const avgDigital =
    data.length > 0
      ? (data.reduce((s, d) => s + d.idx_digital, 0) / data.length).toFixed(1)
      : "0";

  const topSector = data.length > 0 ? data[0] : null;
  const bottomSector = data.length > 0 ? data[data.length - 1] : null;

  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDesc ? bVal - aVal : aVal - bVal;
      }
      return sortDesc
        ? String(bVal).localeCompare(String(aVal))
        : String(aVal).localeCompare(String(bVal));
    });
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
        <span className="ml-3 text-gray-600">
          Cargando datos de digitalizacion...
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

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
        <OEBreadcrumb items={[{ label: "Indicadores", href: "/oficina-empleo" }, { label: "Digitalizacion Sector" }]} />
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
            Digitalizacion por Sector
          </h1>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Experimental
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Indicador I-05: % de skills digitales sobre total por sector CLAE
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Sectores
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{data.length}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-4 h-4 text-green-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Promedio digital
            </span>
          </div>
          <p className="text-3xl font-bold text-green-700">{avgDigital}%</p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Mas digital
            </span>
          </div>
          <p className="text-lg font-bold text-purple-700 truncate" title={topSector?.clae_seccion}>
            {topSector ? `${topSector.idx_digital}%` : "—"}
          </p>
          <p className="text-xs text-gray-500 truncate">
            {topSector?.clae_seccion || ""}
          </p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown className="w-4 h-4 text-orange-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Menos digital
            </span>
          </div>
          <p className="text-lg font-bold text-orange-700 truncate" title={bottomSector?.clae_seccion}>
            {bottomSector ? `${bottomSector.idx_digital}%` : "—"}
          </p>
          <p className="text-xs text-gray-500 truncate">
            {bottomSector?.clae_seccion || ""}
          </p>
        </div>
      </div>

      {/* Chart with Insights */}
      <ChartContainer
        title="Indice de digitalizacion por sector CLAE"
        subtitle={`${data.length} sectores — promedio ${avgDigital}%`}
        insights={
          <InsightList>
            {topSector && (
              <InsightItem
                text={`"${topSector.clae_seccion}" lidera con ${topSector.idx_digital}% de skills digitales`}
                highlight
              />
            )}
            <InsightItem
              text={`${nivelCounts["alto"] || 0} sectores con digitalizacion alta (>40%)`}
            />
            <InsightItem
              text={`${nivelCounts["bajo"] || 0} sectores con digitalizacion baja (<20%)`}
            />
            <InsightItem
              text={`Promedio general del mercado: ${avgDigital}% de skills digitales`}
            />
          </InsightList>
        }
      >
        <DigitalizacionSectorChart data={data} />
      </ChartContainer>

      {/* Methodology */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Metodologia</h3>
        <div className="grid grid-cols-2 gap-6 text-sm text-gray-700">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Indice de digitalizacion
            </h4>
            <p>
              Porcentaje de skills clasificadas como "digitales" sobre el total
              de skills extraidas por sector CLAE. Las skills se clasifican
              automaticamente durante la extraccion usando la taxonomia ESCO.
            </p>
            <p className="mt-2 font-mono text-xs bg-gray-50 p-2 rounded">
              idx_digital = (skills_digitales / total_skills) * 100
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Niveles de digitalizacion
            </h4>
            <div className="space-y-2">
              {[
                {
                  name: "Alto",
                  key: "alto",
                  range: "> 40%",
                  desc: "Alta demanda de competencias digitales",
                },
                {
                  name: "Medio",
                  key: "medio",
                  range: "20% - 40%",
                  desc: "Demanda moderada de skills digitales",
                },
                {
                  name: "Bajo",
                  key: "bajo",
                  range: "< 20%",
                  desc: "Baja penetracion de skills digitales",
                },
              ].map((n) => (
                <div
                  key={n.key}
                  className="border rounded-lg p-2"
                  style={{
                    borderColor: NIVEL_COLORS[n.key] || "#e5e7eb",
                  }}
                >
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: NIVEL_COLORS[n.key] || "#6b7280",
                      }}
                    />
                    <span className="text-xs font-bold">
                      {n.name} ({n.range})
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{n.desc}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="col-span-2">
            <h4 className="font-semibold text-gray-900 mb-2">Filtros</h4>
            <p>
              Solo se incluyen sectores con al menos 10 skills clasificadas
              para garantizar significancia estadistica.
            </p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">
            Detalle por sector
          </h3>
          <p className="text-sm text-gray-500">
            {data.length} sectores — click en columna para ordenar
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {[
                  { key: "clae_seccion" as SortKey, label: "Sector CLAE" },
                  { key: "total_ofertas" as SortKey, label: "Ofertas" },
                  { key: "total_skills" as SortKey, label: "Total Skills" },
                  {
                    key: "skills_digitales" as SortKey,
                    label: "Skills Digitales",
                  },
                  { key: "idx_digital" as SortKey, label: "% Digital" },
                  { key: "nivel_digital" as SortKey, label: "Nivel" },
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
                  key={row.clae_seccion}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {row.clae_seccion}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.total_ofertas}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.total_skills}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.skills_digitales}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums font-semibold">
                    {row.idx_digital}%
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold capitalize"
                      style={{
                        backgroundColor: `${NIVEL_COLORS[row.nivel_digital] || "#6b7280"}15`,
                        color:
                          NIVEL_COLORS[row.nivel_digital] || "#6b7280",
                      }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          backgroundColor:
                            NIVEL_COLORS[row.nivel_digital] || "#6b7280",
                        }}
                      />
                      {row.nivel_digital}
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
