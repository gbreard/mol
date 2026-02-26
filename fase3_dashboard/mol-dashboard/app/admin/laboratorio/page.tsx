"use client";

import Link from "next/link";
import { FlaskConical, Zap, ArrowRight, Database, Calendar } from "lucide-react";

const INDICATORS = [
  {
    slug: "tension-demanda",
    title: "Tension de Demanda",
    description:
      "Persistencia x Insistencia por ocupacion ISCO. Identifica demanda critica, urgente, pasiva o fluida.",
    status: "experimental" as const,
    href: "/admin/laboratorio/tension-demanda",
    icon: Zap,
    dataSource: "tension_ocupaciones",
    addedDate: "2026-02",
  },
];

const STATUS_STYLES = {
  experimental: {
    label: "Experimental",
    bg: "bg-amber-100",
    text: "text-amber-800",
    border: "border-amber-200",
    dot: "bg-amber-500",
  },
  beta: {
    label: "Beta",
    bg: "bg-blue-100",
    text: "text-blue-800",
    border: "border-blue-200",
    dot: "bg-blue-500",
  },
  production: {
    label: "Produccion",
    bg: "bg-green-100",
    text: "text-green-800",
    border: "border-green-200",
    dot: "bg-green-500",
  },
};

export default function LaboratorioPage() {
  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-2.5 shadow-md">
            <FlaskConical className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Laboratorio de Indicadores
            </h1>
            <p className="text-sm text-gray-500">
              Indicadores experimentales en fase de prueba antes de pasar al
              dashboard publico
            </p>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mb-6 text-xs text-gray-500">
        {Object.entries(STATUS_STYLES).map(([key, style]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${style.dot}`} />
            <span>{style.label}</span>
          </div>
        ))}
      </div>

      {/* Indicator Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {INDICATORS.map((indicator) => {
          const statusStyle = STATUS_STYLES[indicator.status];
          const Icon = indicator.icon;
          return (
            <div
              key={indicator.slug}
              className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg p-2.5">
                  <Icon className="w-5 h-5 text-gray-700" />
                </div>
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border} border`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${statusStyle.dot}`}
                  />
                  {statusStyle.label}
                </span>
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {indicator.title}
              </h3>
              <p className="text-sm text-gray-600 mb-4 flex-1">
                {indicator.description}
              </p>

              <div className="flex items-center gap-4 text-xs text-gray-400 mb-4">
                <div className="flex items-center gap-1">
                  <Database className="w-3.5 h-3.5" />
                  <span>{indicator.dataSource}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>{indicator.addedDate}</span>
                </div>
              </div>

              <Link
                href={indicator.href}
                className="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
              >
                Ver indicador
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          );
        })}
      </div>

      {/* Empty state hint */}
      {INDICATORS.length === 1 && (
        <div className="mt-8 text-center text-sm text-gray-400">
          Nuevos indicadores se agregan aqui antes de promoverlos al dashboard
          publico.
        </div>
      )}
    </div>
  );
}
