'use client'

import { useState } from 'react'
import { Sidebar } from '@/components/Sidebar'
import { PanoramaGeneral } from '@/components/PanoramaGeneral'
import { Requerimientos } from '@/components/Requerimientos'
import { OfertasLaborales } from '@/components/OfertasLaborales'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { BarChart3, Target, Briefcase } from 'lucide-react'
import { ActiveFilters } from '@/components/ActiveFilters'

export default function VipDashboardPage() {
  const [activeTab, setActiveTab] = useState('panorama')
  const [filters, setFilters] = useState(() => {
    const hoy = new Date()
    const mesAtras = new Date(hoy)
    mesAtras.setDate(hoy.getDate() - 30)
    return {
      territorio: 'nacional',
      provincia: '',
      localidad: [] as string[],
      fechaDesde: mesAtras as Date | null,
      fechaHasta: hoy as Date | null,
      permanencia: [] as string[],
      searchOcupacion: '',
      ocupacionesSeleccionadas: [] as string[],
      nivelEducativo: [] as string[],
      experiencia: '' as string,
      seniority: [] as string[],
      modalidad: [] as string[],
      jornada: '' as string,
      skillsDigitales: false as boolean,
      sector: [] as string[],
    }
  })

  const handleFilterChange = (filterType: string, value: any) => {
    setFilters(prev => ({ ...prev, [filterType]: value }))
  }

  const handleRemoveFilter = (filterType: string) => {
    const resets: Record<string, any> = {
      territorio: { territorio: 'nacional', provincia: '', localidad: [] },
      provincia: { provincia: '', localidad: [] },
      localidad: { localidad: [] },
      fechas: { fechaDesde: null, fechaHasta: null },
      permanencia: { permanencia: [] },
      ocupaciones: { ocupacionesSeleccionadas: [], searchOcupacion: '' },
      nivelEducativo: { nivelEducativo: [] },
      experiencia: { experiencia: '' },
      seniority: { seniority: [] },
      modalidad: { modalidad: [] },
      jornada: { jornada: '' },
      skillsDigitales: { skillsDigitales: false },
      sector: { sector: [] },
    }
    if (resets[filterType]) setFilters(prev => ({ ...prev, ...resets[filterType] }))
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="flex-1 flex overflow-hidden">
        <Sidebar filters={filters} onFilterChange={handleFilterChange} />
        <main className="flex-1 overflow-hidden flex flex-col">
          <div className="p-4 lg:p-6 flex-1 flex flex-col min-h-0">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full flex-1 flex flex-col min-h-0">
              <TabsList className="w-full h-12 mb-4 bg-white shadow-lg border border-gray-200 p-1.5 rounded-xl grid grid-cols-3 gap-1.5 flex-shrink-0">
                <TabsTrigger value="panorama" className="h-full text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg font-semibold rounded-lg transition-all flex items-center gap-1.5">
                  <BarChart3 className="w-4 h-4" />
                  Panorama general
                </TabsTrigger>
                <TabsTrigger value="requerimientos" className="h-full text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg font-semibold rounded-lg transition-all flex items-center gap-1.5">
                  <Target className="w-4 h-4" />
                  Requerimientos
                </TabsTrigger>
                <TabsTrigger value="ofertas" className="h-full text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-lg font-semibold rounded-lg transition-all flex items-center gap-1.5">
                  <Briefcase className="w-4 h-4" />
                  Ofertas laborales
                </TabsTrigger>
              </TabsList>

              <ActiveFilters filters={filters} onRemoveFilter={handleRemoveFilter} />

              <TabsContent value="panorama" className="flex-1 overflow-auto mt-0 min-h-0">
                <PanoramaGeneral filters={filters} />
              </TabsContent>
              <TabsContent value="requerimientos" className="flex-1 overflow-auto mt-0 min-h-0">
                <Requerimientos filters={filters} />
              </TabsContent>
              <TabsContent value="ofertas" className="flex-1 overflow-auto mt-0 min-h-0">
                <OfertasLaborales filters={filters} />
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  )
}
