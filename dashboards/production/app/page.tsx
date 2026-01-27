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

export default function Home() {
  const [activeTab, setActiveTab] = useState("panorama");
  const [filters, setFilters] = useState({
    territorio: "nacional",
    provincia: "",
    localidad: "",
    fechaDesde: null as Date | null,
    fechaHasta: null as Date | null,
    permanencia: [] as string[],
    searchOcupacion: "",
    ocupacionesSeleccionadas: [] as string[],
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
        setFilters(prev => ({ ...prev, territorio: 'nacional', provincia: '', localidad: '' }));
        break;
      case 'provincia':
        setFilters(prev => ({ ...prev, provincia: '' }));
        break;
      case 'localidad':
        setFilters(prev => ({ ...prev, localidad: '' }));
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
        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="w-full h-14 mb-6 bg-white shadow-lg border border-gray-200 p-2 rounded-xl grid grid-cols-3 gap-2">
                <TabsTrigger
                  value="panorama"
                  className="h-full text-base data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:text-blue-600 data-[state=inactive]:hover:bg-blue-50 font-semibold rounded-lg transition-all duration-200 flex items-center gap-2"
                >
                  <BarChart3 className="w-5 h-5" />
                  Panorama general
                </TabsTrigger>
                <TabsTrigger
                  value="requerimientos"
                  className="h-full text-base data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:text-blue-600 data-[state=inactive]:hover:bg-blue-50 font-semibold rounded-lg transition-all duration-200 flex items-center gap-2"
                >
                  <Target className="w-5 h-5" />
                  Requerimientos
                </TabsTrigger>
                <TabsTrigger
                  value="ofertas"
                  className="h-full text-base data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=inactive]:text-gray-600 data-[state=inactive]:hover:text-blue-600 data-[state=inactive]:hover:bg-blue-50 font-semibold rounded-lg transition-all duration-200 flex items-center gap-2"
                >
                  <Briefcase className="w-5 h-5" />
                  Ofertas laborales
                </TabsTrigger>
              </TabsList>

              {/* Active Filters */}
              <ActiveFilters filters={filters} onRemoveFilter={handleRemoveFilter} />

              <TabsContent value="panorama" className="mt-0">
                <PanoramaGeneral filters={filters} />
              </TabsContent>

              <TabsContent value="requerimientos" className="mt-0">
                <Requerimientos filters={filters} />
              </TabsContent>

              <TabsContent value="ofertas" className="mt-0">
                <OfertasLaborales filters={filters} />
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
}
