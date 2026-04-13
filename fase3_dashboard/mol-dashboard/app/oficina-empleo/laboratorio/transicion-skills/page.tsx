"use client";
import { OEBreadcrumb } from "@/components/oficina-empleo/OEBreadcrumb";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Share2,
  Link2,
  GitBranch,
  BarChart3,
} from "lucide-react";
import {
  getTransicionSkills,
  TransicionSkillsOcupacion,
} from "@/lib/supabase";
import { ChartContainer } from "@/components/ChartContainer";
import {
  TransicionSkillsChart,
  TransicionNodo,
  TransicionEnlace,
} from "@/components/laboratorio/TransicionSkillsChart";
import { InsightList, InsightItem } from "@/components/laboratorio/InsightList";

export default function TransicionSkillsPage() {
  const [rawData, setRawData] = useState<TransicionSkillsOcupacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const result = await getTransicionSkills();
        setRawData(result);
      } catch (err) {
        console.error("Error loading transicion data:", err);
        setError("Error al cargar datos de transicion skills-ocupacion.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const nodes: TransicionNodo[] = rawData
    .filter((d) => d.tipo === "nodo")
    .map((d) => ({
      isco_code: d.isco_code!,
      isco_label: d.isco_label!,
      total_ofertas: d.total_ofertas!,
      total_skills: d.total_skills!,
    }));

  const links: TransicionEnlace[] = rawData
    .filter((d) => d.tipo === "enlace")
    .map((d) => ({
      source_isco: d.source_isco!,
      target_isco: d.target_isco!,
      jaccard: d.jaccard!,
      shared_skills: d.shared_skills!,
      union_skills: d.union_skills!,
      top_shared_labels: d.top_shared_labels,
    }));

  const avgJaccard =
    links.length > 0
      ? (links.reduce((s, l) => s + l.jaccard, 0) / links.length).toFixed(3)
      : "0";

  const maxShared =
    links.length > 0 ? Math.max(...links.map((l) => l.shared_skills)) : 0;

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">
          Cargando datos de transicion...
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
        <OEBreadcrumb items={[{ label: "Indicadores", href: "/oficina-empleo" }, { label: "Transicion Skills" }]} />
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
            Mapa de Transicion Skills-Ocupacion
          </h1>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Experimental
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Indicador I-04: Red de ocupaciones conectadas por similitud de skills
          (Jaccard)
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
          <p className="text-3xl font-bold text-gray-900">{nodes.length}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Link2 className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Conexiones
            </span>
          </div>
          <p className="text-3xl font-bold text-purple-700">{links.length}</p>
        </div>
        <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <GitBranch className="w-4 h-4 text-amber-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Jaccard promedio
            </span>
          </div>
          <p className="text-3xl font-bold text-amber-700">{avgJaccard}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Share2 className="w-4 h-4 text-green-600" />
            <span className="text-xs font-semibold text-gray-500 uppercase">
              Max skills compartidas
            </span>
          </div>
          <p className="text-3xl font-bold text-green-700">{maxShared}</p>
        </div>
      </div>

      {/* Chart with Insights */}
      <ChartContainer
        title="Red de transicion skills-ocupacion"
        subtitle={`${nodes.length} ocupaciones, ${links.length} conexiones — arrastra nodos, zoom con scroll`}
        insights={
          <InsightList>
            <InsightItem
              text={`${links.length} pares de ocupaciones comparten skills significativas (Jaccard >= 0.10)`}
              highlight
            />
            <InsightItem
              text={`Jaccard promedio: ${avgJaccard} — cuanto mas alto, mas transferibles son las skills`}
            />
            {maxShared > 0 && (
              <InsightItem
                text={`Maximo ${maxShared} skills compartidas entre un par de ocupaciones`}
              />
            )}
            <InsightItem
              text="Nodos mas grandes = mas ofertas. Lineas mas gruesas = mas similitud"
            />
          </InsightList>
        }
      >
        <TransicionSkillsChart nodes={nodes} links={links} />
      </ChartContainer>

      {/* Methodology */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Metodologia</h3>
        <div className="grid grid-cols-2 gap-6 text-sm text-gray-700">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Indice de Jaccard
            </h4>
            <p>
              Se calcula la similitud entre los conjuntos de skills de cada par
              de ocupaciones ISCO. El indice de Jaccard mide la proporcion de
              skills compartidas sobre el total de skills distintas de ambas.
            </p>
            <p className="mt-2 font-mono text-xs bg-gray-50 p-2 rounded">
              J(A,B) = |A ∩ B| / |A ∪ B|
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Interpretacion
            </h4>
            <div className="space-y-2 text-xs">
              <p>
                <span className="font-bold">J &gt; 0.30:</span> Ocupaciones
                muy similares — transicion laboral facil
              </p>
              <p>
                <span className="font-bold">J 0.15-0.30:</span> Similitud
                moderada — transicion posible con capacitacion
              </p>
              <p>
                <span className="font-bold">J 0.10-0.15:</span> Baja
                similitud — transicion requiere formacion significativa
              </p>
            </div>
          </div>
          <div className="col-span-2">
            <h4 className="font-semibold text-gray-900 mb-2">Filtros</h4>
            <p>
              Top 20 ocupaciones por volumen (min 5 ofertas). Se muestran
              conexiones con Jaccard &gt;= 0.10 y al menos 3 skills
              compartidas.
            </p>
          </div>
        </div>
      </div>

      {/* Table — links detail */}
      {links.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-bold text-gray-900">
              Detalle de conexiones
            </h3>
            <p className="text-sm text-gray-500">
              {links.length} pares ordenados por similitud
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                    ISCO A
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                    ISCO B
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                    Jaccard
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                    Compartidas
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                    Top skills
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {[...links]
                  .sort((a, b) => b.jaccard - a.jaccard)
                  .map((link, i) => {
                    let topLabels: string[] = [];
                    if (link.top_shared_labels) {
                      try {
                        topLabels = JSON.parse(link.top_shared_labels);
                      } catch {
                        topLabels = [];
                      }
                    }
                    const nodeA = nodes.find(
                      (n) => n.isco_code === link.source_isco
                    );
                    const nodeB = nodes.find(
                      (n) => n.isco_code === link.target_isco
                    );
                    return (
                      <tr
                        key={i}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-4 py-3 text-gray-900">
                          <span className="font-mono text-xs text-gray-500 mr-1">
                            {link.source_isco}
                          </span>
                          {nodeA?.isco_label || ""}
                        </td>
                        <td className="px-4 py-3 text-gray-900">
                          <span className="font-mono text-xs text-gray-500 mr-1">
                            {link.target_isco}
                          </span>
                          {nodeB?.isco_label || ""}
                        </td>
                        <td className="px-4 py-3 tabular-nums font-semibold">
                          {link.jaccard.toFixed(4)}
                        </td>
                        <td className="px-4 py-3 tabular-nums">
                          {link.shared_skills} / {link.union_skills}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-600">
                          {topLabels.join(", ")}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
