'use client';

interface FiltersProps {
  onFilterChange?: (filters: Record<string, string>) => void;
}

export default function Filters({ onFilterChange }: FiltersProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Territorio */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Territorio
          </label>
          <select className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
            <option value="">Todos</option>
            <option value="CABA">CABA</option>
            <option value="Buenos Aires">Buenos Aires</option>
            <option value="Córdoba">Córdoba</option>
            <option value="Santa Fe">Santa Fe</option>
            <option value="Mendoza">Mendoza</option>
          </select>
        </div>

        {/* Período */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Período
          </label>
          <select className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
            <option value="ultimo_mes">Último mes</option>
            <option value="ultimo_trimestre">Último trimestre</option>
            <option value="ultimo_semestre">Último semestre</option>
            <option value="ultimo_anio">Último año</option>
          </select>
        </div>

        {/* Permanencia */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Permanencia
          </label>
          <select className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
            <option value="">Todas</option>
            <option value="activas">Solo activas</option>
            <option value="cerradas">Solo cerradas</option>
          </select>
        </div>

        {/* Ocupación */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ocupación
          </label>
          <select className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
            <option value="">Todas</option>
            <option value="2512">Desarrollador de software</option>
            <option value="2511">Analista de sistemas</option>
            <option value="5223">Vendedor de tienda</option>
            <option value="2411">Contador</option>
          </select>
        </div>
      </div>
    </div>
  );
}
