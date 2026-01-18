'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DataPoint {
  periodo: string;
  ofertas: number;
}

interface EvolucionChartProps {
  data?: DataPoint[];
  title?: string;
}

// Datos de ejemplo
const defaultData: DataPoint[] = [
  { periodo: 'Ene', ofertas: 4200 },
  { periodo: 'Feb', ofertas: 4500 },
  { periodo: 'Mar', ofertas: 4800 },
  { periodo: 'Abr', ofertas: 5100 },
  { periodo: 'May', ofertas: 5400 },
  { periodo: 'Jun', ofertas: 5890 },
];

export default function EvolucionChart({ data = defaultData, title = 'Evolución de ofertas laborales' }: EvolucionChartProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <button className="text-sm text-blue-600 hover:text-blue-800">
          Descargar CSV
        </button>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="periodo"
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#e5e7eb' }}
              tickFormatter={(value) => value.toLocaleString('es-AR')}
            />
            <Tooltip
              formatter={(value) => [Number(value).toLocaleString('es-AR'), 'Ofertas']}
              contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
            />
            <Line
              type="monotone"
              dataKey="ofertas"
              stroke="#2563eb"
              strokeWidth={2}
              dot={{ fill: '#2563eb', strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="text-sm text-gray-500 mt-2">
        Crecimiento del 15.2% en los últimos 6 meses
      </p>
    </div>
  );
}
