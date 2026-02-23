import { useQuery } from '@tanstack/react-query'
import { getPanoramaData, getEvolucionPeriodos, getOfertasPorLocalidad } from '@/lib/supabase'
import type { DashboardFilters } from '@/lib/types'

export function usePanorama(filters?: DashboardFilters) {
  return useQuery({
    queryKey: ['panorama', filters],
    queryFn: () => getPanoramaData(filters),
  })
}

export function useEvolucion(filters?: DashboardFilters, periodos?: number) {
  return useQuery({
    queryKey: ['evolucion', filters, periodos],
    queryFn: () => getEvolucionPeriodos(filters, periodos),
  })
}

export function useLocalidades(filters?: DashboardFilters) {
  return useQuery({
    queryKey: ['localidades', filters],
    queryFn: () => getOfertasPorLocalidad(filters),
    enabled: !!filters?.provincia,
  })
}
