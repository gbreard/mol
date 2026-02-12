"use client";

import { useState } from "react";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { PanoramaGeneral } from "@/components/PanoramaGeneral";
import { Requerimientos } from "@/components/Requerimientos";
import { OfertasLaborales } from "@/components/OfertasLaborales";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart3, Target, Briefcase } from "lucide-react";
import { ActiveFilters } from "@/components/ActiveFilters";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("panorama");
  // Default: "Última semana" preseleccionada
  const [filters, setFilters] = useState(() => {
    const hoy = new Date();
    const semanaAtras = new Date(hoy);
    semanaAtras.setDate(hoy.getDate() - 7);
    return {
    territorio: "nacional",
    provincia: "",
    localidad: [] as string[],
    fechaDesde: semanaAtras as Date | null,
    fechaHasta: hoy as Date | null,
    permanencia: [] as string[],
    searchOcupacion: "",
    ocupacionesSeleccionadas: [] as string[],
    // Filtros de Requerimientos (Issue #5)
    nivelEducativo: [] as string[],
    experiencia: "" as string,
    seniority: [] as string[],
    modalidad: [] as string[],
    jornada: "" as string,
    skillsDigitales: false as boolean,
    sector: [] as string[],
  };
  });

  const handleFilterChange = (filterType: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const handleRemoveFilter = (filterType: string) => {
    switch(filterType) {
      case 'territorio':
        setFilters(prev => ({ ...prev, territorio: 'nacional', provincia: '', localidad: [] }));
        break;
      case 'provincia':
        setFilters(prev => ({ ...prev, provincia: '', localidad: [] }));
        break;
      case 'localidad':
        setFilters(prev => ({ ...prev, localidad: [] }));
        break;
      case 'fechas':
        setFilters(prev => ({ ...prev, fechaDesde: null, fechaHasta: null }));
        break;
      case 'permanencia':
        setFilters(prev => ({ ...prev, permanencia: [] }));
        break;
      case 'ocupaciones':
        setFilters(prev => ({ ...prev, ocupacionesSeleccionadas: [], searchOcupacion: '' }));
        break;
      case 'requerimientos':
        setFilters(prev => ({
          ...prev,
          nivelEducativo: [],
          experiencia: '',
          seniority: [],
          modalidad: [],
          jornada: '',
          skillsDigitales: false
        }));
        break;
      case 'nivelEducativo':
        setFilters(prev => ({ ...prev, nivelEducativo: [] }));
        break;
      case 'experiencia':
        setFilters(prev => ({ ...prev, experiencia: '' }));
        break;
      case 'seniority':
        setFilters(prev => ({ ...prev, seniority: [] }));
        break;
      case 'modalidad':
        setFilters(prev => ({ ...prev, modalidad: [] }));
        break;
      case 'jornada':
        setFilters(prev => ({ ...prev, jornada: '' }));
        break;
      case 'skillsDigitales':
        setFilters(prev => ({ ...prev, skillsDigitales: false }));
        break;
      case 'sector':
        setFilters(prev => ({ ...prev, sector: [] }));
        break;
      default:
        break;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar filters={filters} onFilterChange={handleFilterChange} />

        {/* Content */}
        <main className="flex-1 overflow-hidden flex flex-col">
          <div className="p-4 lg:p-6 flex-1 flex flex-col min-h-0">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full flex-1 flex flex-col min-h-0">
              <TabsList className="w-full h-12 mb-4 bg-white shadow-lg border border-gray-200 p-1.5 rounded-xl grid grid-cols-3 gap-1.5 flex-shrink-0">
                <TabsTrigger
                  value="panorama"
                  className="h-full text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:text-blue-600 data-[state=inactive]:hover:bg-blue-50 font-semibold rounded-lg transition-all duration-200 flex items-center gap-1.5"
                >
                  <BarChart3 className="w-4 h-4" />
                  <span className="hidden sm:inline">Panorama general</span>
                  <span className="sm:hidden">Panorama</span>
                </TabsTrigger>
                <TabsTrigger
                  value="requerimientos"
                  className="h-full text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:text-blue-600 data-[state=inactive]:hover:bg-blue-50 font-semibold rounded-lg transition-all duration-200 flex items-center gap-1.5"
                >
                  <Target className="w-4 h-4" />
                  Requerimientos
                </TabsTrigger>
                <TabsTrigger
                  value="ofertas"
                  className="h-full text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:text-blue-600 data-[state=inactive]:hover:bg-blue-50 font-semibold rounded-lg transition-all duration-200 flex items-center gap-1.5"
                >
                  <Briefcase className="w-4 h-4" />
                  <span className="hidden sm:inline">Ofertas laborales</span>
                  <span className="sm:hidden">Ofertas</span>
                </TabsTrigger>
              </TabsList>

              {/* Active Filters */}
              <div className="flex-shrink-0">
                <ActiveFilters filters={filters} onRemoveFilter={handleRemoveFilter} />
              </div>

              <TabsContent value="panorama" className="mt-0 flex-1 overflow-y-auto">
                <PanoramaGeneral filters={filters} />
              </TabsContent>

              <TabsContent value="requerimientos" className="mt-0 flex-1 overflow-y-auto">
                <Requerimientos filters={filters} />
              </TabsContent>

              <TabsContent value="ofertas" className="mt-0 flex-1 flex flex-col min-h-0">
                <OfertasLaborales filters={filters} />
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
}
