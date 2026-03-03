import Link from "next/link";
import { Briefcase, ArrowLeft } from "lucide-react";

export default function OfertasPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="flex items-center gap-3 mb-8">
        <Briefcase className="w-7 h-7 text-teal-600" />
        <h1 className="text-2xl font-bold text-gray-900">
          Ofertas Coincidentes
        </h1>
        <span className="bg-teal-100 text-teal-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
          Proximamente
        </span>
      </div>

      <div className="bg-white rounded-2xl border-2 border-dashed border-gray-300 p-8 text-center">
        <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500 mb-2">Selecciona un perfil primero</p>
        <p className="text-xs text-gray-400 mb-6">
          Para ver las ofertas coincidentes, primero registra o busca el perfil de un trabajador.
        </p>

        {/* Skeleton table */}
        <div className="max-w-lg mx-auto">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 flex gap-4">
              <div className="h-3 bg-gray-200 rounded w-1/3" />
              <div className="h-3 bg-gray-200 rounded w-1/4" />
              <div className="h-3 bg-gray-200 rounded w-1/4" />
            </div>
            {[1, 2, 3].map((i) => (
              <div key={i} className="px-4 py-3 border-t border-gray-100 flex gap-4">
                <div className="h-3 bg-gray-100 rounded w-1/3" />
                <div className="h-3 bg-gray-100 rounded w-1/4" />
                <div className="h-3 bg-gray-100 rounded w-1/4" />
              </div>
            ))}
          </div>
        </div>

        <Link
          href="/oficina-empleo/perfil"
          className="inline-flex items-center gap-2 mt-6 text-sm text-teal-600 hover:text-teal-700 font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          Ir a Perfil de Trabajador
        </Link>
      </div>
    </div>
  );
}
