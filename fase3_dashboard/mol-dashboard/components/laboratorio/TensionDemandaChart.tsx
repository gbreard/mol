"use client";

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import type { TensionOcupacion } from "@/lib/supabase";

export const CUADRANTE_COLORS: Record<string, string> = {
  CRITICO: "#ef4444",
  URGENTE: "#f97316",
  PASIVO: "#eab308",
  FLUIDO: "#22c55e",
};

function TensionTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as TensionOcupacion;
  return (
    <div className="bg-white px-4 py-3 shadow-lg rounded-lg border border-gray-200 max-w-xs">
      <p className="font-semibold text-gray-900 text-sm">{d.isco_label}</p>
      <p className="text-xs text-gray-500 mb-2">ISCO {d.isco_code}</p>
      <div className="space-y-1 text-sm">
        <p>
          Persistencia: <span className="font-bold">{d.persistencia}%</span>
        </p>
        <p>
          Insistencia: <span className="font-bold">{d.insistencia}%</span>
        </p>
        <p>
          Posiciones: <span className="font-bold">{d.total_posiciones}</span>
        </p>
        <p>
          Ofertas: <span className="font-bold">{d.total_ofertas}</span>
        </p>
        <p
          className="font-semibold"
          style={{ color: CUADRANTE_COLORS[d.cuadrante] || "#6b7280" }}
        >
          {d.cuadrante}
        </p>
      </div>
    </div>
  );
}

interface TensionDemandaChartProps {
  data: TensionOcupacion[];
}

export function TensionDemandaChart({ data }: TensionDemandaChartProps) {
  const cuadranteCounts: Record<string, number> = {};
  data.forEach((d) => {
    cuadranteCounts[d.cuadrante] = (cuadranteCounts[d.cuadrante] || 0) + 1;
  });

  return (
    <div data-testid="tension-chart-container">
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            dataKey="persistencia"
            name="Persistencia"
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
            label={{
              value: "Persistencia (%)",
              position: "insideBottom",
              offset: -10,
              style: { fill: "#6b7280", fontSize: 12 },
            }}
          />
          <YAxis
            type="number"
            dataKey="insistencia"
            name="Insistencia"
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
            label={{
              value: "Insistencia (%)",
              angle: -90,
              position: "insideLeft",
              offset: 10,
              style: { fill: "#6b7280", fontSize: 12 },
            }}
          />
          <ZAxis
            type="number"
            dataKey="total_posiciones"
            range={[40, 400]}
            name="Posiciones"
          />
          <ReferenceLine x={50} stroke="#9ca3af" strokeDasharray="5 5" />
          <ReferenceLine y={50} stroke="#9ca3af" strokeDasharray="5 5" />
          <Tooltip content={<TensionTooltip />} />
          <Scatter data={data} fill="#8884d8">
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={CUADRANTE_COLORS[entry.cuadrante] || "#6b7280"}
                fillOpacity={0.7}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div
        className="flex items-center justify-center gap-6 mt-2 text-xs"
        data-testid="tension-legend"
      >
        {Object.entries(CUADRANTE_COLORS).map(([name, color]) => (
          <div key={name} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-gray-600">
              {name} ({cuadranteCounts[name] || 0})
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
