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
import type { VelocidadCobertura } from "@/lib/supabase";

export const VELOCIDAD_COLORS: Record<string, string> = {
  rapida: "#22c55e",
  normal: "#f59e0b",
  lenta: "#ef4444",
};

function VelocidadTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as VelocidadCobertura & { short_label: string };
  return (
    <div className="bg-white px-4 py-3 shadow-lg rounded-lg border border-gray-200 max-w-xs">
      <p className="font-semibold text-gray-900 text-sm">{d.isco_label}</p>
      <p className="text-xs text-gray-500 mb-2">ISCO {d.isco_code}</p>
      <div className="space-y-1 text-sm">
        <p>
          Mediana: <span className="font-bold">{d.mediana_dias} dias</span>
        </p>
        <p>
          Rango: <span className="font-bold">{d.min_dias} - {d.max_dias} dias</span>
        </p>
        <p>
          Q1-Q3: <span className="font-bold">{d.q1_dias} - {d.q3_dias}</span>
        </p>
        <p>
          Ofertas: <span className="font-bold">{d.total_ofertas}</span>
        </p>
        <p
          className="font-semibold capitalize"
          style={{ color: VELOCIDAD_COLORS[d.categoria] || "#6b7280" }}
        >
          {d.categoria}
        </p>
      </div>
    </div>
  );
}

interface VelocidadCoberturaChartProps {
  data: VelocidadCobertura[];
}

function shortLabel(label: string, max = 30): string {
  const slash = label.indexOf("/");
  const clean = slash > 0 ? label.slice(0, slash) : label;
  return clean.length > max ? clean.slice(0, max - 1) + "..." : clean;
}

export function VelocidadCoberturaChart({ data }: VelocidadCoberturaChartProps) {
  const top30 = data.slice(0, 30).map((d) => ({
    ...d,
    short_label: shortLabel(d.isco_label),
  }));

  const categoriaCounts: Record<string, number> = {};
  data.forEach((d) => {
    categoriaCounts[d.categoria] = (categoriaCounts[d.categoria] || 0) + 1;
  });

  return (
    <div data-testid="velocidad-chart-container">
      <ResponsiveContainer width="100%" height={Math.max(400, top30.length * 28)}>
        <BarChart
          data={top30}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 140, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            label={{
              value: "Mediana dias publicada",
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
          <ReferenceLine x={15} stroke="#22c55e" strokeDasharray="5 5" label={{ value: "15d", position: "top" }} />
          <ReferenceLine x={45} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "45d", position: "top" }} />
          <Tooltip content={<VelocidadTooltip />} />
          <Bar dataKey="mediana_dias" radius={[0, 4, 4, 0]}>
            {top30.map((entry, index) => (
              <Cell
                key={index}
                fill={VELOCIDAD_COLORS[entry.categoria] || "#6b7280"}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div
        className="flex items-center justify-center gap-6 mt-2 text-xs"
        data-testid="velocidad-legend"
      >
        {Object.entries(VELOCIDAD_COLORS).map(([name, color]) => (
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
