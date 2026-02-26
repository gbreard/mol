"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import type { BrechaCalificacion } from "@/lib/supabase";

export const CATEGORIA_COLORS: Record<string, string> = {
  sobreexigente: "#ef4444",
  equilibrado: "#22c55e",
  subexigente: "#3b82f6",
};

function BrechaTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as BrechaCalificacion;
  return (
    <div className="bg-white px-4 py-3 shadow-lg rounded-lg border border-gray-200 max-w-xs">
      <p className="font-semibold text-gray-900 text-sm">{d.isco_label}</p>
      <p className="text-xs text-gray-500 mb-2">ISCO {d.isco_code}</p>
      <div className="space-y-1 text-sm">
        <p>
          Brecha: <span className="font-bold">{d.brecha}</span>
        </p>
        <p>
          Skills promedio: <span className="font-bold">{d.skills_promedio}</span>
        </p>
        <p>
          Ofertas: <span className="font-bold">{d.total_ofertas}</span>
        </p>
        <p
          className="font-semibold capitalize"
          style={{ color: CATEGORIA_COLORS[d.categoria] || "#6b7280" }}
        >
          {d.categoria}
        </p>
      </div>
    </div>
  );
}

interface BrechaCalificacionChartProps {
  data: BrechaCalificacion[];
}

export function BrechaCalificacionChart({ data }: BrechaCalificacionChartProps) {
  const top30 = data.slice(0, 30);

  const maxBrecha = Math.max(...top30.map((d) => d.brecha), 1.5);
  const minBrecha = Math.min(...top30.map((d) => d.brecha), 0.5);
  const domainMax = Math.ceil(maxBrecha * 10) / 10;
  const domainMin = Math.floor(minBrecha * 10) / 10;

  const categoriaCounts: Record<string, number> = {};
  data.forEach((d) => {
    categoriaCounts[d.categoria] = (categoriaCounts[d.categoria] || 0) + 1;
  });

  return (
    <div data-testid="brecha-chart-container">
      <ResponsiveContainer width="100%" height={Math.max(400, top30.length * 28)}>
        <BarChart
          data={top30}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 140, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            domain={[domainMin, domainMax]}
            label={{
              value: "Brecha (1.0 = promedio mercado)",
              position: "insideBottom",
              offset: -5,
              style: { fill: "#6b7280", fontSize: 12 },
            }}
          />
          <YAxis
            type="category"
            dataKey="isco_label"
            width={135}
            tick={{ fontSize: 11 }}
          />
          <ReferenceLine x={1.0} stroke="#6b7280" strokeDasharray="5 5" label={{ value: "1.0", position: "top" }} />
          <Tooltip content={<BrechaTooltip />} />
          <Bar dataKey="brecha" radius={[0, 4, 4, 0]}>
            {top30.map((entry, index) => (
              <Cell
                key={index}
                fill={CATEGORIA_COLORS[entry.categoria] || "#6b7280"}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div
        className="flex items-center justify-center gap-6 mt-2 text-xs"
        data-testid="brecha-legend"
      >
        {Object.entries(CATEGORIA_COLORS).map(([name, color]) => (
          <div key={name} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-gray-600 capitalize">
              {name} ({categoriaCounts[name] || 0})
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
