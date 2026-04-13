"use client";
import { OEBreadcrumb } from "@/components/oficina-empleo/OEBreadcrumb";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Wifi,
  Calendar,
  Building2,
  BarChart3,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { getIndiceRemoto, IndiceTrabajoRemoto } from "@/lib/supabase";
import { ChartContainer } from "@/components/ChartContainer";
import {
  IndiceRemotoChart,
  MODALIDAD_COLORS,
} from "@/components/laboratorio/IndiceRemotoChart";
import { InsightList, InsightItem } from "@/components/laboratorio/InsightList";

type SortKey =
  | "mes"
  | "clae_seccion"
  | "total_ofertas"
  | "pct_remoto"
  | "pct_hibrido"
  | "pct_presencial";

export default function IndiceRemotoPage() {
  const [data, setData] = useState<IndiceTrabajoRemoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("mes");
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const result = await getIndiceRemoto();
        setData(result);
      } catch (err) {
        console.error("Error loading indice remoto data:", err);
        setError("Error al cargar datos de indice de trabajo remoto.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const globalData = data.filter((d) => d.clae_seccion === null);
  const sectorData = data.filter((d) => d.clae_seccion !== null);
  const distinctMonths = [...new Set(globalData.map((d) => d.mes))];
  const distinctSectors = [
    ...new Set(sectorData.map((d) => d.clae_seccion).filter(Boolean)),
  ];

  const lastMonth = globalData.length > 0 ? globalData[globalData.length - 1] : null;

  const sortedSectorData = useMemo(() => {
    return [...sectorData].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDesc ? bVal - aVal : aVal - bVal;
      }
      return sortDesc
        ? String(bVal ?? "").localeCompare(String(aVal ?? ""))
        : String(aVal ?? "").localeCompare(String(bVal ?? ""));
    });
  }, [sectorData, sortKey, sortDesc]);

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
          Cargando datos de trabajo remoto...
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
        <OEBreadcrumb items={[{ label: "Indicadores", href: "/oficina-empleo" }, { label: "Indice Remoto" }]} />
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
            Indice de Trabajo Remoto
          </h1>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Experimental
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Indicador I-10: Evolucion mensual de modalidades de trabajo
          (presencial, hibrido, remoto)
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Calendar className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Meses
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {distinctMonths.length}
          </p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Wifi className="w-4 h-4 text-green-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              % Remoto actual
            </span>
          </div>
          <p className="text-3xl font-bold text-green-700">
            {lastMonth ? `${lastMonth.pct_remoto}%` : "—"}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              % Hibrido actual
            </span>
          </div>
          <p className="text-3xl font-bold text-purple-700">
            {lastMonth ? `${lastMonth.pct_hibrido}%` : "—"}
          </p>
        </div>
        <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Building2 className="w-4 h-4 text-amber-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Sectores
            </span>
          </div>
          <p className="text-3xl font-bold text-amber-700">
            {distinctSectors.length}
          </p>
        </div>
      </div>

      {/* Chart with Insights */}
      <ChartContainer
        title="Evolucion mensual de modalidades de trabajo"
        subtitle={`${distinctMonths.length} meses — datos globales`}
        insights={
          <InsightList>
            {lastMonth && (
              <InsightItem
                text={`Ultimo mes (${lastMonth.mes}): ${lastMonth.pct_remoto}% remoto, ${lastMonth.pct_hibrido}% hibrido, ${lastMonth.pct_presencial}% presencial`}
                highlight
              />
            )}
            {lastMonth && globalData.length >= 2 && (
              <InsightItem
                text={`Remoto ${lastMonth.pct_remoto > globalData[0].pct_remoto ? "en aumento" : "en descenso"} respecto al primer mes registrado`}
              />
            )}
            <InsightItem
              text={`${distinctSectors.length} sectores con datos desglosados (min 5 ofertas/mes)`}
            />
          </InsightList>
        }
      >
        <IndiceRemotoChart data={data} />
      </ChartContainer>

      {/* Methodology */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Metodologia</h3>
        <div className="grid grid-cols-2 gap-6 text-sm text-gray-700">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Indice de trabajo remoto
            </h4>
            <p>
              Porcentaje de ofertas por modalidad (presencial, hibrido, remoto)
              agrupadas por mes de publicacion. Se calcula tanto a nivel global
              como por sector CLAE.
            </p>
            <p className="mt-2 font-mono text-xs bg-gray-50 p-2 rounded">
              pct_remoto = (ofertas_remoto / total_ofertas) * 100
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Modalidades</h4>
            <div className="space-y-2">
              {[
                {
                  name: "Presencial",
                  key: "presencial",
                  desc: "Trabajo 100% en oficina o lugar fisico",
                },
                {
                  name: "Hibrido",
                  key: "hibrido",
                  desc: "Combinacion de presencial y remoto",
                },
                {
                  name: "Remoto",
                  key: "remoto",
                  desc: "Trabajo 100% a distancia",
                },
              ].map((m) => (
                <div
                  key={m.key}
                  className="border rounded-lg p-2"
                  style={{
                    borderColor: MODALIDAD_COLORS[m.key] || "#e5e7eb",
                  }}
                >
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor:
                          MODALIDAD_COLORS[m.key] || "#6b7280",
                      }}
                    />
                    <span className="text-xs font-bold">{m.name}</span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{m.desc}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="col-span-2">
            <h4 className="font-semibold text-gray-900 mb-2">Filtros</h4>
            <p>
              Datos globales incluyen todas las ofertas validadas con modalidad
              conocida. Datos por sector requieren al menos 5 ofertas por
              mes-sector.
            </p>
          </div>
        </div>
      </div>

      {/* Table — sector data */}
      {sectorData.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-bold text-gray-900">
              Detalle por sector y mes
            </h3>
            <p className="text-sm text-gray-500">
              {sectorData.length} registros — click en columna para ordenar
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {[
                    { key: "mes" as SortKey, label: "Mes" },
                    { key: "clae_seccion" as SortKey, label: "Sector" },
                    { key: "total_ofertas" as SortKey, label: "Ofertas" },
                    { key: "pct_presencial" as SortKey, label: "% Presencial" },
                    { key: "pct_hibrido" as SortKey, label: "% Hibrido" },
                    { key: "pct_remoto" as SortKey, label: "% Remoto" },
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
                {sortedSectorData.map((row, i) => (
                  <tr
                    key={`${row.mes}-${row.clae_seccion}-${i}`}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">
                      {row.mes}
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {row.clae_seccion}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {row.total_ofertas}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {row.pct_presencial}%
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {row.pct_hibrido}%
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums font-semibold">
                      {row.pct_remoto}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
