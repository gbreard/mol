'use client';

interface SidebarProps {
  onFilterChange?: (filters: Record<string, string>) => void;
}

export default function Sidebar({ onFilterChange }: SidebarProps) {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-120px)] p-4">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
        Filtros
      </h3>

      <div className="space-y-6">
        {/* Territorio */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Territorio
          </label>
          <select className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
            <option value="">Todos</option>
            <option value="CABA">CABA</option>
            <option value="Buenos Aires">Buenos Aires</option>
            <option value="Córdoba">Córdoba</option>
            <option value="Santa Fe">Santa Fe</option>
            <option value="Mendoza">Mendoza</option>
            <option value="Tucumán">Tucumán</option>
            <option value="Entre Ríos">Entre Ríos</option>
            <option value="Salta">Salta</option>
            <option value="Neuquén">Neuquén</option>
          </select>
        </div>

        {/* Período */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
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
          <label className="block text-sm font-medium text-gray-700 mb-2">
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
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Ocupación
          </label>
          <select className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
            <option value="">Todas</option>
            <option value="2512">Desarrollador de software</option>
            <option value="2511">Analista de sistemas</option>
            <option value="5223">Vendedor de tienda</option>
            <option value="2411">Contador</option>
            <option value="3323">Representante comercial</option>
            <option value="4226">Recepcionista</option>
            <option value="1221">Director comercial</option>
          </select>
        </div>

        {/* Modalidad */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Modalidad
          </label>
          <select className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
            <option value="">Todas</option>
            <option value="remoto">Remoto</option>
            <option value="hibrido">Híbrido</option>
            <option value="presencial">Presencial</option>
          </select>
        </div>

        {/* Seniority */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Seniority
          </label>
          <select className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm">
            <option value="">Todos</option>
            <option value="junior">Junior</option>
            <option value="semi_senior">Semi-senior</option>
            <option value="senior">Senior</option>
            <option value="manager">Manager</option>
          </select>
        </div>

        {/* Botón aplicar */}
        <div className="pt-4 border-t border-gray-200">
          <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">
            Aplicar filtros
          </button>
          <button className="w-full mt-2 text-gray-600 py-2 px-4 rounded-md text-sm hover:bg-gray-100 transition-colors">
            Limpiar filtros
          </button>
        </div>
      </div>
    </aside>
  );
}
