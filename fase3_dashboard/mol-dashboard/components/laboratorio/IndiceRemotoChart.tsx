"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { IndiceTrabajoRemoto } from "@/lib/supabase";

export const MODALIDAD_COLORS: Record<string, string> = {
  presencial: "#9ca3af",
  hibrido: "#3b82f6",
  remoto: "#22c55e",
};

function RemotoTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white px-4 py-3 shadow-lg rounded-lg border border-gray-200 max-w-xs">
      <p className="font-semibold text-gray-900 text-sm mb-2">{label}</p>
      <div className="space-y-1 text-sm">
        {payload.map((entry: any) => (
          <p key={entry.name}>
            <span
              className="inline-block w-3 h-3 rounded-full mr-2"
              style={{ backgroundColor: entry.color }}
            />
            {entry.name}: <span className="font-bold">{entry.value.toFixed(1)}%</span>
          </p>
        ))}
      </div>
    </div>
  );
}

interface IndiceRemotoChartProps {
  data: IndiceTrabajoRemoto[];
}

export function IndiceRemotoChart({ data }: IndiceRemotoChartProps) {
  // Solo datos globales (clae_seccion === null)
  const globalData = data.filter((d) => d.clae_seccion === null);

  return (
    <div data-testid="remoto-chart-container">
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={globalData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="mes"
            tick={{ fontSize: 11 }}
          />
          <YAxis
            tickFormatter={(v) => `${v}%`}
            domain={[0, 100]}
            label={{
              value: "% Ofertas",
              angle: -90,
              position: "insideLeft",
              offset: 10,
              style: { fill: "#6b7280", fontSize: 12 },
            }}
          />
          <Tooltip content={<RemotoTooltip />} />
          <Legend />
          <Bar
            dataKey="pct_presencial"
            stackId="a"
            name="Presencial"
            fill={MODALIDAD_COLORS.presencial}
          />
          <Bar
            dataKey="pct_hibrido"
            stackId="a"
            name="Hibrido"
            fill={MODALIDAD_COLORS.hibrido}
          />
          <Bar
            dataKey="pct_remoto"
            stackId="a"
            name="Remoto"
            fill={MODALIDAD_COLORS.remoto}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      <div
        className="flex items-center justify-center gap-6 mt-2 text-xs"
        data-testid="remoto-legend"
      >
        {Object.entries(MODALIDAD_COLORS).map(([name, color]) => {
          const lastMonth = globalData[globalData.length - 1];
          const pct = lastMonth
            ? name === "presencial" ? lastMonth.pct_presencial
            : name === "hibrido" ? lastMonth.pct_hibrido
            : lastMonth.pct_remoto
            : 0;
          return (
            <div key={name} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-gray-600 capitalize">
                {name} ({pct.toFixed(1)}% ultimo mes)
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
