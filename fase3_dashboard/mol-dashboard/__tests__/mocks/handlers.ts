import { http, HttpResponse } from 'msw'
import { mockOfertas } from './fixtures/ofertas'
import { mockInsightsRPC } from './fixtures/kpis'
import { mockOfertasSkills } from './fixtures/skills'
import { mockPanoramaRPC } from './fixtures/panorama'
import { mockEvolucionRPC } from './fixtures/evolucion'
import { mockRequerimientosRPC, mockSkillsResumenRPC, mockSidebarCountsRPC } from './fixtures/requerimientos'
import { mockPipelineStatusRPC } from './fixtures/pipeline-status'
import { mockReconciliacionWarning } from './fixtures/reconciliacion'
import { mockScrapingStatsRPC, mockScrapingHistoryRPC } from './fixtures/scraping-stats'

const SUPABASE_URL = 'https://test.supabase.co'

// Wildcard handler for all PostgREST requests to ofertas_dashboard
function handleOfertasDashboard(request: Request) {
  const url = new URL(request.url)
  const select = url.searchParams.get('select')

  // Parse range header for pagination
  const range = request.headers.get('Range')
  let data: Record<string, unknown>[] = [...mockOfertas]

  if (range) {
    const match = range.match(/(\d+)-(\d+)/)
    if (match) {
      const [, startStr, endStr] = match
      data = data.slice(Number(startStr), Number(endStr) + 1)
    }
  }

  // If select only specific columns, filter the response
  if (select) {
    const columns = select.split(',').map((c) => c.trim())
    data = data.map((row) => {
      const filtered: Record<string, unknown> = {}
      columns.forEach((col) => {
        if (col in row) {
          filtered[col] = row[col]
        }
      })
      return filtered
    })
  }

  return HttpResponse.json(data, {
    headers: {
      'content-range': `0-${Math.max(0, data.length - 1)}/${mockOfertas.length}`,
    },
  })
}

export const handlers = [
  // PostgREST: ofertas_dashboard - GET (data queries)
  http.get(`${SUPABASE_URL}/rest/v1/ofertas_dashboard`, ({ request }) => {
    return handleOfertasDashboard(request)
  }),

  // PostgREST: ofertas_dashboard - HEAD (count queries)
  http.head(`${SUPABASE_URL}/rest/v1/ofertas_dashboard`, () => {
    return new HttpResponse(null, {
      status: 200,
      headers: {
        'content-range': `0-0/${mockOfertas.length}`,
      },
    })
  }),

  // PostgREST: ofertas_skills - GET
  http.get(`${SUPABASE_URL}/rest/v1/ofertas_skills`, () => {
    return HttpResponse.json(mockOfertasSkills, {
      headers: {
        'content-range': `0-${mockOfertasSkills.length - 1}/${mockOfertasSkills.length}`,
      },
    })
  }),

  // PostgREST: ofertas_skills - HEAD
  http.head(`${SUPABASE_URL}/rest/v1/ofertas_skills`, () => {
    return new HttpResponse(null, {
      status: 200,
      headers: {
        'content-range': `0-0/${mockOfertasSkills.length}`,
      },
    })
  }),

  // RPC: get_insights (legacy)
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_insights`, () => {
    return HttpResponse.json(mockInsightsRPC)
  }),

  // RPC: get_panorama
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_panorama`, () => {
    return HttpResponse.json(mockPanoramaRPC)
  }),

  // RPC: get_evolucion
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_evolucion`, () => {
    return HttpResponse.json(mockEvolucionRPC)
  }),

  // RPC: get_requerimientos
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_requerimientos`, () => {
    return HttpResponse.json(mockRequerimientosRPC)
  }),

  // RPC: get_skills_resumen
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_skills_resumen`, () => {
    return HttpResponse.json(mockSkillsResumenRPC)
  }),

  // RPC: get_sidebar_counts
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_sidebar_counts`, () => {
    return HttpResponse.json(mockSidebarCountsRPC)
  }),

  // RPC: get_pipeline_status
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_pipeline_status`, () => {
    return HttpResponse.json(mockPipelineStatusRPC)
  }),

  // RPC: reconciliar_sistemas
  http.post(`${SUPABASE_URL}/rest/v1/rpc/reconciliar_sistemas`, () => {
    return HttpResponse.json(mockReconciliacionWarning)
  }),

  // RPC: get_scraping_stats
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_scraping_stats`, () => {
    return HttpResponse.json(mockScrapingStatsRPC)
  }),

  // RPC: get_scraping_history
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_scraping_history`, () => {
    return HttpResponse.json(mockScrapingHistoryRPC)
  }),

  // Auth: get current user
  http.get(`${SUPABASE_URL}/auth/v1/user`, ({ request }) => {
    const auth = request.headers.get('Authorization')
    if (!auth || auth === 'Bearer invalid-token') {
      return HttpResponse.json({ error: 'invalid token' }, { status: 401 })
    }
    return HttpResponse.json({
      id: 'user-123',
      email: 'test@example.com',
      user_metadata: { role: 'viewer', display_name: 'Test User' },
    })
  }),

  // Auth: exchange code for session
  http.post(`${SUPABASE_URL}/auth/v1/token`, () => {
    return HttpResponse.json({
      access_token: 'test-access-token',
      refresh_token: 'test-refresh-token',
      user: { id: 'user-123', email: 'test@example.com' },
    })
  }),

  // Auth: get session (Supabase SSR checks)
  http.get(`${SUPABASE_URL}/auth/v1/token`, () => {
    return HttpResponse.json({
      access_token: 'test-access-token',
      refresh_token: 'test-refresh-token',
      user: { id: 'user-123', email: 'test@example.com' },
    })
  }),

  // Issues table
  http.get(`${SUPABASE_URL}/rest/v1/issues`, () => {
    return HttpResponse.json([])
  }),

  http.post(`${SUPABASE_URL}/rest/v1/issues`, () => {
    return HttpResponse.json({ id: 'issue-new' }, { status: 201 })
  }),

  // Eventos uso (analytics)
  http.post(`${SUPABASE_URL}/rest/v1/eventos_uso`, () => {
    return HttpResponse.json({}, { status: 201 })
  }),
]
