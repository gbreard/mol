'use client';

interface KPICardProps {
  title: string;
  value: string | number;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
}

export default function KPICard({ title, value, delta, deltaType = 'positive' }: KPICardProps) {
  const deltaColors = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      <div className="mt-2 flex items-baseline">
        <p className="text-3xl font-semibold text-gray-900">
          {typeof value === 'number' ? value.toLocaleString('es-AR') : value}
        </p>
        {delta && (
          <span className={`ml-2 text-sm font-medium ${deltaColors[deltaType]}`}>
            {delta}
          </span>
        )}
      </div>
    </div>
  );
}
