"use client";
import { OEBreadcrumb } from "@/components/oficina-empleo/OEBreadcrumb";

import { useState, useEffect, useMemo } from "react";
import {
  Loader2,
  AlertCircle,
  GraduationCap,
  TrendingUp,
  TrendingDown,
  Scale,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { getBrechaCalificacion, BrechaCalificacion } from "@/lib/supabase";
import { ChartContainer } from "@/components/ChartContainer";
import {
  BrechaCalificacionChart,
  CATEGORIA_COLORS,
} from "@/components/laboratorio/BrechaCalificacionChart";
import { InsightList, InsightItem } from "@/components/laboratorio/InsightList";

type SortKey =
  | "isco_code"
  | "isco_label"
  | "total_ofertas"
  | "skills_promedio"
  | "brecha"
  | "categoria";

export default function BrechaCalificacionPage() {
  const [data, setData] = useState<BrechaCalificacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("brecha");
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const result = await getBrechaCalificacion();
        setData(result);
      } catch (err) {
        console.error("Error loading brecha data:", err);
        setError("Error al cargar datos de brecha de calificacion.");
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

  const avgSkills =
    data.length > 0
      ? (
          data.reduce((s, d) => s + d.skills_promedio, 0) / data.length
        ).toFixed(1)
      : "0";

  const maxBrecha = data.length > 0 ? data[0] : null;

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
          Cargando datos de brecha...
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
        <OEBreadcrumb items={[{ label: "Indicadores", href: "/vip/politicas" }, { label: "Brecha Calificacion" }]} />
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">
            Brecha de Calificacion
          </h1>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Experimental
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Indicador I-03: Skills demandadas vs promedio del mercado por
          ocupacion
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <GraduationCap className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Promedio mercado
            </span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {avgSkills} skills
          </p>
        </div>
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-red-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Sobreexigentes
            </span>
          </div>
          <p className="text-3xl font-bold text-red-700">
            {categoriaCounts["sobreexigente"] || 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Subexigentes
            </span>
          </div>
          <p className="text-3xl font-bold text-blue-700">
            {categoriaCounts["subexigente"] || 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Scale className="w-4 h-4 text-orange-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Max brecha
            </span>
          </div>
          <p className="text-3xl font-bold text-orange-700">
            {maxBrecha ? maxBrecha.brecha.toFixed(2) : "—"}
          </p>
        </div>
      </div>

      {/* Chart with Insights */}
      <ChartContainer
        title="Brecha de calificacion por ocupacion"
        subtitle={`${data.length} ocupaciones — referencia 1.0 = promedio mercado`}
        insights={
          <InsightList>
            {(categoriaCounts["sobreexigente"] || 0) > 0 && (
              <InsightItem
                text={`${categoriaCounts["sobreexigente"]} ocupaciones sobreexigentes (brecha > 1.3): piden mas skills que el promedio`}
                highlight
              />
            )}
            {(categoriaCounts["subexigente"] || 0) > 0 && (
              <InsightItem
                text={`${categoriaCounts["subexigente"]} subexigentes (brecha < 0.7): piden menos skills que el promedio`}
              />
            )}
            <InsightItem
              text={`${categoriaCounts["equilibrado"] || 0} ocupaciones equilibradas (0.7 - 1.3)`}
            />
            {maxBrecha && (
              <InsightItem
                text={`Mayor brecha: "${maxBrecha.isco_label}" con ${maxBrecha.brecha} (${maxBrecha.skills_promedio} skills)`}
              />
            )}
          </InsightList>
        }
      >
        <BrechaCalificacionChart data={data} />
      </ChartContainer>

      {/* Methodology */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Metodologia</h3>
        <div className="grid grid-cols-2 gap-6 text-sm text-gray-700">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Ratio de brecha
            </h4>
            <p>
              Se calcula el promedio de skills distintas por oferta para cada
              ocupacion ISCO, y se divide por el promedio general del mercado.
              Un valor de 1.0 indica que la ocupacion pide la misma cantidad
              de skills que el promedio.
            </p>
            <p className="mt-2 font-mono text-xs bg-gray-50 p-2 rounded">
              brecha = skills_promedio_isco / skills_promedio_mercado
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Categorias</h4>
            <div className="space-y-2">
              {[
                {
                  name: "Sobreexigente",
                  key: "sobreexigente",
                  range: "brecha > 1.3",
                  desc: "Pide significativamente mas skills que el promedio",
                },
                {
                  name: "Equilibrado",
                  key: "equilibrado",
                  range: "0.7 - 1.3",
                  desc: "Demanda de skills alineada con el mercado",
                },
                {
                  name: "Subexigente",
                  key: "subexigente",
                  range: "brecha < 0.7",
                  desc: "Pide menos skills que el promedio del mercado",
                },
              ].map((c) => (
                <div
                  key={c.key}
                  className="border rounded-lg p-2"
                  style={{
                    borderColor: CATEGORIA_COLORS[c.key] || "#e5e7eb",
                  }}
                >
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: CATEGORIA_COLORS[c.key] || "#6b7280",
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
              Solo se incluyen ocupaciones con al menos 5 ofertas validadas
              para garantizar significancia estadistica.
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
                  {
                    key: "skills_promedio" as SortKey,
                    label: "Skills prom.",
                  },
                  { key: "brecha" as SortKey, label: "Brecha" },
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
                  <td className="px-4 py-3 text-right tabular-nums">
                    {row.skills_promedio}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums font-semibold">
                    {row.brecha}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold capitalize"
                      style={{
                        backgroundColor: `${CATEGORIA_COLORS[row.categoria] || "#6b7280"}15`,
                        color:
                          CATEGORIA_COLORS[row.categoria] || "#6b7280",
                      }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          backgroundColor:
                            CATEGORIA_COLORS[row.categoria] || "#6b7280",
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
