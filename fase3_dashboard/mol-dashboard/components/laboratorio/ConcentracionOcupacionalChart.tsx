"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ConcentracionOcupacional } from "@/lib/supabase";

export const CLASIFICACION_COLORS: Record<string, string> = {
  diversificado: "#22c55e",
  moderado: "#f59e0b",
  concentrado: "#ef4444",
};

function ConcentracionTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as ConcentracionOcupacional;
  return (
    <div className="bg-white px-4 py-3 shadow-lg rounded-lg border border-gray-200 max-w-xs">
      <p className="font-semibold text-gray-900 text-sm">{d.isco_label}</p>
      <p className="text-xs text-gray-500 mb-2">ISCO {d.isco_code}</p>
      <div className="space-y-1 text-sm">
        <p>
          Share: <span className="font-bold">{d.share_pct}%</span>
        </p>
        <p>
          Ofertas: <span className="font-bold">{d.ofertas}</span>
        </p>
      </div>
    </div>
  );
}

interface ConcentracionOcupacionalChartProps {
  topOcupaciones: ConcentracionOcupacional[];
  hhiGlobal: number;
  clasificacion: string;
}

function shortLabel(label: string | null, max = 30): string {
  if (!label) return "";
  // ESCO inclusive labels: "vendedor de X/vendedora de X" → take first part
  const slash = label.indexOf("/");
  const clean = slash > 0 ? label.slice(0, slash) : label;
  return clean.length > max ? clean.slice(0, max - 1) + "…" : clean;
}

export function ConcentracionOcupacionalChart({
  topOcupaciones,
  hhiGlobal,
  clasificacion,
}: ConcentracionOcupacionalChartProps) {
  const top10 = topOcupaciones.slice(0, 10).map((d) => ({
    ...d,
    short_label: shortLabel(d.isco_label),
  }));
  const color = CLASIFICACION_COLORS[clasificacion] || "#6b7280";

  return (
    <div data-testid="concentracion-chart-container">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm font-semibold text-gray-700">
          HHI Global:
        </span>
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold"
          style={{ backgroundColor: `${color}15`, color }}
          data-testid="hhi-badge"
        >
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: color }}
          />
          {hhiGlobal.toFixed(4)} — {clasificacion}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={380}>
        <BarChart
          data={top10}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            tickFormatter={(v) => `${v}%`}
            label={{
              value: "% del total de ofertas",
              position: "insideBottom",
              offset: -5,
              style: { fill: "#6b7280", fontSize: 12 },
            }}
          />
          <YAxis
            type="category"
            dataKey="short_label"
            width={150}
            tick={{ fontSize: 11 }}
          />
          <Tooltip content={<ConcentracionTooltip />} />
          <Bar dataKey="share_pct" radius={[0, 4, 4, 0]}>
            {top10.map((_, index) => (
              <Cell
                key={index}
                fill={index === 0 ? "#3b82f6" : index < 3 ? "#60a5fa" : "#93c5fd"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div
        className="flex items-center justify-center gap-6 mt-2 text-xs"
        data-testid="concentracion-legend"
      >
        {Object.entries(CLASIFICACION_COLORS).map(([name, c]) => (
          <div key={name} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: c }}
            />
            <span className="text-gray-600 capitalize">{name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
