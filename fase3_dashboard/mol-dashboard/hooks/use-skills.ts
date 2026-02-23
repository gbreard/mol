import { useQuery } from '@tanstack/react-query'
import { getSkillsResumen } from '@/lib/supabase'
import type { DashboardFilters } from '@/lib/types'

export function useSkills(filters?: DashboardFilters) {
  return useQuery({
    queryKey: ['skills', filters],
    queryFn: () => getSkillsResumen(filters),
  })
}
