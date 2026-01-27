'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DataPoint {
  ocupacion: string;
  cantidad: number;
}

interface OcupacionesChartProps {
  data?: DataPoint[];
  title?: string;
}

// Datos de ejemplo
const defaultData: DataPoint[] = [
  { ocupacion: 'Desarrollador de software', cantidad: 850 },
  { ocupacion: 'Vendedor de tienda', cantidad: 720 },
  { ocupacion: 'Analista de sistemas', cantidad: 680 },
  { ocupacion: 'Contador', cantidad: 520 },
  { ocupacion: 'Representante comercial', cantidad: 480 },
  { ocupacion: 'Recepcionista', cantidad: 420 },
  { ocupacion: 'Director comercial', cantidad: 380 },
  { ocupacion: 'Mecánico automotor', cantidad: 350 },
  { ocupacion: 'Empleado administrativo', cantidad: 320 },
  { ocupacion: 'Técnico en informática', cantidad: 290 },
];

export default function OcupacionesChart({ data = defaultData, title = 'Top 10 ocupaciones' }: OcupacionesChartProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <button className="text-sm text-blue-600 hover:text-blue-800">
          Descargar CSV
        </button>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ left: 20, right: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={true} vertical={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 11 }}
              axisLine={{ stroke: '#e5e7eb' }}
              tickFormatter={(value) => value.toLocaleString('es-AR')}
            />
            <YAxis
              type="category"
              dataKey="ocupacion"
              tick={{ fontSize: 11 }}
              axisLine={{ stroke: '#e5e7eb' }}
              width={150}
            />
            <Tooltip
              formatter={(value) => [Number(value).toLocaleString('es-AR'), 'Ofertas']}
              contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
            />
            <Bar
              dataKey="cantidad"
              fill="#3b82f6"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
