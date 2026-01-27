"use client";

import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color: string;
  change?: number;
  trend?: "up" | "down";
}

export function KPICard({ title, value, icon: Icon, color, change, trend }: KPICardProps) {
  const colorClasses = {
    blue: "from-blue-500 to-blue-600",
    green: "from-emerald-500 to-emerald-600",
    purple: "from-purple-500 to-purple-600",
    orange: "from-orange-500 to-orange-600",
  }[color] || "from-gray-500 to-gray-600";

  const bgColorClasses = {
    blue: "bg-gradient-to-br from-blue-50 to-blue-100",
    green: "bg-gradient-to-br from-emerald-50 to-emerald-100",
    purple: "bg-gradient-to-br from-purple-50 to-purple-100",
    orange: "bg-gradient-to-br from-orange-50 to-orange-100",
  }[color] || "bg-gradient-to-br from-gray-50 to-gray-100";

  // Format number consistently on server and client
  const formattedValue = typeof value === 'number'
    ? value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".")
    : value;

  return (
    <div className={`${bgColorClasses} border-0 rounded-xl p-6 flex items-start gap-4 shadow-sm hover:shadow-md transition-all duration-300 group`}>
      <div className={`bg-gradient-to-br ${colorClasses} rounded-lg p-3 shadow-md group-hover:scale-110 transition-transform duration-300`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
        <p className="text-4xl font-bold text-gray-900 tracking-tight">{formattedValue}</p>
        {change !== undefined && trend && (
          <div className={`flex items-center gap-1 mt-2 ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
            {trend === 'up' ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            <span className="text-sm font-semibold">
              {trend === 'up' ? '+' : ''}{change}% vs mes anterior
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
