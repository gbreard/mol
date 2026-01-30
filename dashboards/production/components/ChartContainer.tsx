"use client";

import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ReactNode } from "react";

interface ChartContainerProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  onDownload?: () => void;
  insights?: ReactNode;
}

export function ChartContainer({ title, subtitle, children, onDownload, insights }: ChartContainerProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow duration-300">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          {subtitle && <p className="text-sm text-gray-500 mt-1 font-medium">{subtitle}</p>}
        </div>
        {onDownload && (
          <Button
            variant="outline"
            size="sm"
            className="gap-2 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-all"
            onClick={onDownload}
          >
            <Download className="w-4 h-4" />
            <span className="font-medium">CSV</span>
          </Button>
        )}
      </div>
      {insights ? (
        <div className="grid grid-cols-[1.2fr_1fr] gap-6 items-start">
          <div className="min-w-0 overflow-hidden">
            {children}
          </div>
          <div className="bg-gradient-to-br from-amber-50/80 via-orange-50/60 to-amber-50/80 border border-amber-200 rounded-xl p-6 min-w-0 shadow-sm hover:shadow-md transition-shadow duration-300">
            {insights}
          </div>
        </div>
      ) : (
        <div>{children}</div>
      )}
    </div>
  );
}
