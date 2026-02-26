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
import type { DigitalizacionSector } from "@/lib/supabase";

export const NIVEL_COLORS: Record<string, string> = {
  alto: "#22c55e",
  medio: "#f59e0b",
  bajo: "#9ca3af",
};

function DigitalizacionTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as DigitalizacionSector;
  return (
    <div className="bg-white px-4 py-3 shadow-lg rounded-lg border border-gray-200 max-w-xs">
      <p className="font-semibold text-gray-900 text-sm">{d.clae_seccion}</p>
      <div className="space-y-1 text-sm mt-2">
        <p>
          Indice digital: <span className="font-bold">{d.idx_digital}%</span>
        </p>
        <p>
          Skills digitales: <span className="font-bold">{d.skills_digitales}</span> / {d.total_skills}
        </p>
        <p>
          Ofertas: <span className="font-bold">{d.total_ofertas}</span>
        </p>
        <p
          className="font-semibold capitalize"
          style={{ color: NIVEL_COLORS[d.nivel_digital] || "#6b7280" }}
        >
          Nivel: {d.nivel_digital}
        </p>
      </div>
    </div>
  );
}

interface DigitalizacionSectorChartProps {
  data: DigitalizacionSector[];
}

export function DigitalizacionSectorChart({ data }: DigitalizacionSectorChartProps) {
  const avgDigital = data.length > 0
    ? data.reduce((s, d) => s + d.idx_digital, 0) / data.length
    : 0;

  const nivelCounts: Record<string, number> = {};
  data.forEach((d) => {
    nivelCounts[d.nivel_digital] = (nivelCounts[d.nivel_digital] || 0) + 1;
  });

  return (
    <div data-testid="digitalizacion-chart-container">
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="clae_seccion"
            angle={-35}
            textAnchor="end"
            tick={{ fontSize: 10 }}
            interval={0}
            height={80}
          />
          <YAxis
            tickFormatter={(v) => `${v}%`}
            label={{
              value: "% Skills Digitales",
              angle: -90,
              position: "insideLeft",
              offset: 10,
              style: { fill: "#6b7280", fontSize: 12 },
            }}
          />
          <ReferenceLine
            y={avgDigital}
            stroke="#6b7280"
            strokeDasharray="5 5"
            label={{ value: `Promedio ${avgDigital.toFixed(1)}%`, position: "right", fill: "#6b7280", fontSize: 11 }}
          />
          <Tooltip content={<DigitalizacionTooltip />} />
          <Bar dataKey="idx_digital" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={NIVEL_COLORS[entry.nivel_digital] || "#6b7280"}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div
        className="flex items-center justify-center gap-6 mt-2 text-xs"
        data-testid="digitalizacion-legend"
      >
        {Object.entries(NIVEL_COLORS).map(([name, color]) => (
          <div key={name} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-gray-600 capitalize">
              {name} ({nivelCounts[name] || 0})
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
