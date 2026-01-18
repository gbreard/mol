'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DataPoint {
  jurisdiccion: string;
  cantidad: number;
  porcentaje: number;
}

interface GeografiaChartProps {
  data?: DataPoint[];
  title?: string;
}

// Datos de ejemplo
const defaultData: DataPoint[] = [
  { jurisdiccion: 'CABA', cantidad: 2100, porcentaje: 35.7 },
  { jurisdiccion: 'Buenos Aires', cantidad: 1450, porcentaje: 24.6 },
  { jurisdiccion: 'Córdoba', cantidad: 580, porcentaje: 9.8 },
  { jurisdiccion: 'Santa Fe', cantidad: 420, porcentaje: 7.1 },
  { jurisdiccion: 'Mendoza', cantidad: 310, porcentaje: 5.3 },
  { jurisdiccion: 'Tucumán', cantidad: 180, porcentaje: 3.1 },
  { jurisdiccion: 'Otras', cantidad: 850, porcentaje: 14.4 },
];

export default function GeografiaChart({ data = defaultData, title = 'Distribución por jurisdicción' }: GeografiaChartProps) {
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
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="jurisdiccion"
              tick={{ fontSize: 11 }}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              axisLine={{ stroke: '#e5e7eb' }}
              tickFormatter={(value) => value.toLocaleString('es-AR')}
            />
            <Tooltip
              formatter={(value, name) => {
                if (name === 'cantidad') return [Number(value).toLocaleString('es-AR'), 'Ofertas'];
                return [value + '%', 'Porcentaje'];
              }}
              contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
            />
            <Bar
              dataKey="cantidad"
              fill="#10b981"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-sm text-gray-500 mt-2">
        CABA y Buenos Aires concentran el 60% de las ofertas
      </p>
    </div>
  );
}
