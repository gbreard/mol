import type { RecomendacionTrayectoria } from '@/lib/recomendacion-ia'
// DEMO: recomendaciones fijadas (ya validadas) para los perfiles DEMO, por "perfil_id|ocupacion_uri"
import recomendacionesDemo from './recomendaciones-demo.json'

const CACHE_DEMO = recomendacionesDemo as Record<string, RecomendacionTrayectoria>

/** Busca perfil_id|ocupación y, si no hay, la recomendación a nivel perfil (perfil_id|). */
export function recomendacionFijada(perfilId?: string | null, ocupacionUri?: string | null): RecomendacionTrayectoria | null {
  if (!perfilId) return null
  return CACHE_DEMO[`${perfilId}|${ocupacionUri || ''}`] ?? CACHE_DEMO[`${perfilId}|`] ?? null
}
