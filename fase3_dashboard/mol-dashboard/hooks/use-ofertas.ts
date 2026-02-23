import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { getOfertas } from '@/lib/supabase'
import type { DashboardFilters } from '@/lib/types'

const PAGE_SIZE = 50

export function useOfertas(page: number, filters?: DashboardFilters) {
  const offset = (page - 1) * PAGE_SIZE

  return useQuery({
    queryKey: ['ofertas', page, filters],
    queryFn: () => getOfertas(PAGE_SIZE, offset, filters),
    placeholderData: keepPreviousData,
  })
}
