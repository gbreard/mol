"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Timer,
  Zap,
  AlertTriangle,
  BarChart3,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { getVelocidadCobertura, VelocidadCobertura } from "@/lib/supabase";
import { ChartContainer } from "@/components/ChartContainer";
import {
  VelocidadCoberturaChart,
  VELOCIDAD_COLORS,
} from "@/components/laboratorio/VelocidadCoberturaChart";
import { InsightList, InsightItem } from "@/components/laboratorio/InsightList";

type SortKey =
  | "isco_code"
  | "isco_label"
  | "total_ofertas"
  | "mediana_dias"
  | "categoria";

export default function VelocidadCoberturaPage() {
  const [data, setData] = useState<VelocidadCobertura[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("mediana_dias");
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const result = await getVelocidadCobertura();
        setData(result);
      } catch (err) {
        console.error("Error loading velocidad data:", err);
        setError("Error al cargar datos de velocidad de cobertura.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const categoriaCounts: Record<string, number> = {};
  data.forEach((d) => {
    categoriaCounts[d.categoria] = (categoriaCounts[d.categoria] || 0) + 1;
  });

  const medianaGlobal =
    data.length > 0
      ? (() => {
          const sorted = [...data.map((d) => d.mediana_dias)].sort(
            (a, b) => a - b
          );
          const mid = Math.floor(sorted.length / 2);
          return sorted.length % 2 === 0
            ? ((sorted[mid - 1] + sorted[mid]) / 2).toFixed(1)
            : sorted[mid].toFixed(1);
        })()
      : "0";

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
          Cargando datos de velocidad...
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
      {/* Header */}
      <div>
        <Link
          href="/admin/laboratorio"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Laboratorio
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">
            Velocidad de Cobertura
          </h1>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Experimental
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Indicador I-06: Mediana de dias que tarda en cubrirse una posicion
          por ocupacion
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
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-green-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Rapidas (&lt;15d)
            </span>
          </div>
          <p className="text-3xl font-bold text-green-700">
            {categoriaCounts["rapida"] || 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Lentas (&gt;45d)
            </span>
          </div>
          <p className="text-3xl font-bold text-red-700">
            {categoriaCounts["lenta"] || 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Timer className="w-4 h-4 text-amber-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Mediana global
            </span>
          </div>
          <p className="text-3xl font-bold text-amber-700">
            {medianaGlobal}d
          </p>
        </div>
      </div>

      {/* Chart with Insights */}
      <ChartContainer
        title="Velocidad de cobertura por ocupacion"
        subtitle={`${data.length} ocupaciones — referencias 15d (rapida) y 45d (lenta)`}
        insights={
          <InsightList>
            {(categoriaCounts["lenta"] || 0) > 0 && (
              <InsightItem
                text={`${categoriaCounts["lenta"]} ocupaciones lentas (>45 dias): posiciones dificiles de cubrir`}
                highlight
              />
            )}
            {(categoriaCounts["rapida"] || 0) > 0 && (
              <InsightItem
                text={`${categoriaCounts["rapida"]} ocupaciones rapidas (<15 dias): alta rotacion o abundancia de candidatos`}
              />
            )}
            <InsightItem
              text={`${categoriaCounts["normal"] || 0} ocupaciones con cobertura normal (15-45 dias)`}
            />
            <InsightItem
              text={`Mediana global: ${medianaGlobal} dias`}
            />
          </InsightList>
        }
      >
        <VelocidadCoberturaChart data={data} />
      </ChartContainer>

      {/* Methodology */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Metodologia</h3>
        <div className="grid grid-cols-2 gap-6 text-sm text-gray-700">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Velocidad de cobertura
            </h4>
            <p>
              Se calcula la mediana de dias que cada oferta estuvo publicada
              (desde publicacion hasta baja) para cada ocupacion ISCO. Solo se
              incluyen ofertas dadas de baja (cubiertas o expiradas).
            </p>
            <p className="mt-2 font-mono text-xs bg-gray-50 p-2 rounded">
              mediana_dias = MEDIAN(dias_publicada) por ISCO
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Categorias</h4>
            <div className="space-y-2">
              {[
                {
                  name: "Rapida",
                  key: "rapida",
                  range: "< 15 dias",
                  desc: "Se cubre rapidamente — alta oferta de candidatos o rotacion",
                },
                {
                  name: "Normal",
                  key: "normal",
                  range: "15 - 45 dias",
                  desc: "Tiempo de cobertura tipico del mercado",
                },
                {
                  name: "Lenta",
                  key: "lenta",
                  range: "> 45 dias",
                  desc: "Cuesta cubrir — escasez de candidatos o requerimientos altos",
                },
              ].map((c) => (
                <div
                  key={c.key}
                  className="border rounded-lg p-2"
                  style={{
                    borderColor: VELOCIDAD_COLORS[c.key] || "#e5e7eb",
                  }}
                >
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor:
                          VELOCIDAD_COLORS[c.key] || "#6b7280",
                      }}
                    />
                    <span className="text-xs font-bold">
                      {c.name} ({c.range})
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{c.desc}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="col-span-2">
            <h4 className="font-semibold text-gray-900 mb-2">Filtros</h4>
            <p>
              Solo se incluyen ocupaciones con al menos 3 ofertas dadas de
              baja para garantizar significancia estadistica.
            </p>
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
                  { key: "total_ofertas" as SortKey, label: "Ofertas" },
                  { key: "mediana_dias" as SortKey, label: "Mediana (dias)" },
                  { key: "categoria" as SortKey, label: "Categoria" },
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
                    {row.total_ofertas}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums font-semibold">
                    {row.mediana_dias}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold capitalize"
                      style={{
                        backgroundColor: `${VELOCIDAD_COLORS[row.categoria] || "#6b7280"}15`,
                        color:
                          VELOCIDAD_COLORS[row.categoria] || "#6b7280",
                      }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          backgroundColor:
                            VELOCIDAD_COLORS[row.categoria] || "#6b7280",
                        }}
                      />
                      {row.categoria}
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
