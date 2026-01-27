'use client';

interface InsightCardProps {
  title: string;
  description: string;
  icon?: string;
  color?: 'blue' | 'green' | 'purple' | 'orange';
}

const colorClasses = {
  blue: 'bg-blue-50 border-blue-200 text-blue-800',
  green: 'bg-green-50 border-green-200 text-green-800',
  purple: 'bg-purple-50 border-purple-200 text-purple-800',
  orange: 'bg-orange-50 border-orange-200 text-orange-800',
};

export default function InsightCard({ title, description, icon = '📊', color = 'blue' }: InsightCardProps) {
  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color]}`}>
      <div className="flex items-start space-x-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <h3 className="font-semibold text-sm">{title}</h3>
          <p className="text-sm mt-1 opacity-90">{description}</p>
        </div>
      </div>
    </div>
  );
}
