import { Building2, Construction } from "lucide-react";

export default function EmpresasPage() {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Building2 className="w-8 h-8 text-blue-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Análisis por empresa</h1>

        <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-700 border border-amber-200 px-4 py-2 rounded-lg text-sm font-medium mb-4">
          <Construction className="w-4 h-4" />
          En desarrollo
        </div>

        <p className="text-gray-500">
          Acá vas a poder explorar qué empresas publican más ofertas, en qué sectores y qué perfiles buscan.
        </p>
      </div>
    </div>
  );
}
