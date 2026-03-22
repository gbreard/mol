import { UserSearch } from "lucide-react";
import DniSearch from "@/components/DniSearch";

export default function PerfilPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-16">
      <div className="flex items-center gap-3 mb-8">
        <UserSearch className="w-7 h-7 text-teal-600" />
        <h1 className="text-2xl font-bold text-gray-900">
          Perfil de Trabajador
        </h1>
      </div>

      {/* S10: Búsqueda por DNI */}
      <div className="mb-8 max-w-lg rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-1 text-base font-semibold text-gray-800">
          Buscar perfil existente
        </h2>
        <p className="mb-4 text-sm text-gray-500">
          Ingresá el DNI del trabajador para ver si ya tiene un perfil creado en Mi Futuro Laboral.
        </p>
        <DniSearch organizacionNombre="OE CABA Sur" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Form wireframe */}
        <div className="bg-white rounded-2xl border-2 border-dashed border-gray-300 p-6">
          <h2 className="font-semibold text-gray-700 text-sm mb-4">
            Datos del trabajador
          </h2>
          <div className="space-y-4">
            {["Nombre completo", "DNI", "Edad", "Nivel educativo"].map(
              (label) => (
                <div key={label}>
                  <label className="block text-xs font-medium text-gray-400 mb-1">
                    {label}
                  </label>
                  <div className="h-10 bg-gray-100 rounded-lg border border-gray-200" />
                </div>
              )
            )}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">
                Experiencia laboral
              </label>
              <div className="h-24 bg-gray-100 rounded-lg border border-gray-200" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">
                Skills / Competencias
              </label>
              <div className="h-10 bg-gray-100 rounded-lg border border-gray-200" />
              <div className="flex gap-2 mt-2">
                {["Excel", "Atencion al cliente", "Logistica"].map((s) => (
                  <span
                    key={s}
                    className="px-2 py-1 bg-gray-200 rounded text-xs text-gray-500"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Results wireframe */}
        <div className="bg-white rounded-2xl border-2 border-dashed border-gray-300 p-6">
          <h2 className="font-semibold text-gray-700 text-sm mb-4">
            Ocupaciones coincidentes
          </h2>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100"
              >
                <div className="w-8 h-8 bg-gray-200 rounded animate-pulse" />
                <div className="flex-1">
                  <div className="h-3 bg-gray-200 rounded w-3/4 mb-2" />
                  <div className="h-2 bg-gray-100 rounded w-1/2" />
                </div>
                <div className="h-6 w-12 bg-gray-200 rounded" />
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-4 text-center">
            Las ocupaciones se calcularan automaticamente en base al perfil
          </p>
        </div>
      </div>
    </div>
  );
}
