import { useQuery } from '@tanstack/react-query'
import { getSidebarCounts, getLocalidadesGroupedByDepartamento } from '@/lib/supabase'
import type { DashboardFilters } from '@/lib/types'

export function useSidebarCounts(filters?: DashboardFilters) {
  return useQuery({
    queryKey: ['sidebar', filters],
    queryFn: () => getSidebarCounts(filters),
  })
}

export function useLocalidadesGrouped(provinciaKey: string, filters?: DashboardFilters) {
  return useQuery({
    queryKey: ['localidades-grouped', provinciaKey, filters],
    queryFn: () => getLocalidadesGroupedByDepartamento(provinciaKey, filters),
    enabled: !!provinciaKey,
  })
}
