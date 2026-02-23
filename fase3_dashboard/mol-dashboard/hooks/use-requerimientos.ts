import { useQuery } from '@tanstack/react-query'
import { getDistribucionRequerimientos } from '@/lib/supabase'
import type { DashboardFilters } from '@/lib/types'

export function useRequerimientos(filters?: DashboardFilters) {
  return useQuery({
    queryKey: ['requerimientos', filters],
    queryFn: () => getDistribucionRequerimientos(filters),
  })
}
