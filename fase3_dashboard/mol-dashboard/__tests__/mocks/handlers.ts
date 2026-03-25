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
import { mockPreviewImpact, mockSugerencias, mockConfigOverride, mockConfigUpsertResult } from './fixtures/config-editor'

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

  // RPC: get_scraping_daily (usado por /admin/scraping)
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_scraping_daily`, () => {
    return HttpResponse.json(mockScrapingHistoryRPC)
  }),

  // RPC: get_scraping_commands
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_scraping_commands`, () => {
    return HttpResponse.json([
      {
        id: 'cmd-1', comando: 'lanzar_portal', params: { portal: 'bumeran' },
        estado: 'completado', creado_por: 'admin@oede.gob.ar',
        log_preview: 'Scraping finalizado. 1240 ofertas.', resultado: { nuevas: 1240, duplicadas: 80 },
        error_mensaje: null, created_at: '2026-03-21T10:00:00Z',
        started_at: '2026-03-21T10:00:05Z', completed_at: '2026-03-21T11:30:00Z', duracion_seg: 5395,
      },
      {
        id: 'cmd-2', comando: 'sync_vps_local', params: {},
        estado: 'error', creado_por: 'admin@oede.gob.ar',
        log_preview: null, resultado: null,
        error_mensaje: 'Connection refused (VPS offline)', created_at: '2026-03-20T08:00:00Z',
        started_at: '2026-03-20T08:00:02Z', completed_at: null, duracion_seg: null,
      },
    ])
  }),

  // RPC: get_scraping_schedule
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_scraping_schedule`, () => {
    return HttpResponse.json([
      {
        id: 1, portal: 'bumeran', dias_semana: [1, 4], hora_utc: '11:00',
        activo: true, updated_by: 'admin@oede.gob.ar', updated_at: '2026-03-15T00:00:00Z',
      },
      {
        id: 2, portal: 'computrabajo', dias_semana: [1, 4], hora_utc: '11:00',
        activo: false, updated_by: null, updated_at: '2026-03-10T00:00:00Z',
      },
    ])
  }),

  // API: scraping-commands
  http.post('/api/scraping-commands', () => {
    return HttpResponse.json({ id: 'cmd-new', estado: 'pendiente' }, { status: 201 })
  }),

  // API: scraping-schedule
  http.put('/api/scraping-schedule', () => {
    return HttpResponse.json({ ok: true })
  }),

  // API: config-editor (usado por /admin/procesamiento/reglas)
  http.get('/api/config-editor', () => {
    return HttpResponse.json({
      source: 'override',
      version: 12,
      updated_by: 'admin@oede.gob.ar',
      updated_at: '2026-03-20T10:00:00Z',
      data: {
        reglas_forzar_isco: {
          R_GERENTE_VENTAS: {
            nombre: 'Gerente de Ventas', prioridad: 1,
            condicion: { titulo_contiene_alguno: ['gerente de ventas', 'jefe de ventas'] },
            forzar_isco: '1221', esco_label: 'Directores de ventas y comercialización', activa: true,
          },
          R_CONTADOR: {
            nombre: 'Contador Público', prioridad: 2,
            condicion: { titulo_contiene: 'contador' },
            forzar_isco: '2411', esco_label: 'Contadores', activa: true,
          },
          R_ALBANIL: {
            nombre: 'Albañil', prioridad: 3,
            condicion: { titulo_contiene_alguno: ['albañil', 'albanil'] },
            forzar_isco: '7112', esco_label: 'Albañiles', activa: false,
          },
        },
      },
    })
  }),

  http.put('/api/config-editor', () => {
    return HttpResponse.json({ version: 13, ok: true })
  }),

  // RPC: get_processing_metrics (usado por /admin/procesamiento)
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_processing_metrics`, () => {
    return HttpResponse.json({
      kpis: {
        nlp: { procesadas: 16146, pendientes: 19007, total: 35153, porcentaje: 46 },
        matching: { con_matching: 15968, pendientes: 178, validadas: 15968 },
        sync: { en_supabase: 15800, pendientes: 168 },
        ultimo_run: '2026-03-21',
      },
      errores_por_tipo: [
        { error_tipo: 'error_isco_incorrecto', total: 320, resueltos: 280, pendientes: 40, severidad_predominante: 'alto' },
        { error_tipo: 'error_ubicacion_vacia', total: 150, resueltos: 140, pendientes: 10, severidad_predominante: 'medio' },
        { error_tipo: 'error_seniority_invalido', total: 85, resueltos: 70, pendientes: 15, severidad_predominante: 'bajo' },
      ],
      timeline: [
        {
          fecha: '2026-03-15', nlp_procesadas: 15000, matching_procesadas: 14000,
          matching_por_regla: 5600, matching_por_semantico: 8400,
          matching_dual_coinciden: 7200, matching_dual_difieren: 1200,
          matching_score_promedio: 0.823,
        },
        {
          fecha: '2026-03-21', nlp_procesadas: 16146, matching_procesadas: 15968,
          matching_por_regla: 6300, matching_por_semantico: 9668,
          matching_dual_coinciden: 8100, matching_dual_difieren: 1560,
          matching_score_promedio: 0.851,
        },
      ],
    })
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

  // Personas
  http.get(`${SUPABASE_URL}/rest/v1/personas`, () => {
    return HttpResponse.json([
      { id: 'p1', nombre: 'María García', dni: '32456789', created_at: '2026-03-25T10:00:00Z',
        casos: [{ id: 'c1', estado: 'perfil_completo', organizacion_id: 'org1' }] },
    ])
  }),
  http.post(`${SUPABASE_URL}/rest/v1/personas`, () => {
    return HttpResponse.json({ id: 'p-new', nombre: 'Test', es_nueva: true }, { status: 201 })
  }),

  // Perfiles
  http.get(`${SUPABASE_URL}/rest/v1/perfiles`, () => {
    return HttpResponse.json([{ id: 'pf1', persona_id: 'p1', completitud: 5 }])
  }),
  http.post(`${SUPABASE_URL}/rest/v1/perfiles`, () => {
    return HttpResponse.json({ id: 'pf-new', persona_id: 'p1', completitud: 0 }, { status: 201 })
  }),
  http.patch(`${SUPABASE_URL}/rest/v1/perfiles`, () => {
    return HttpResponse.json({ id: 'pf1', completitud: 5 })
  }),

  // Perfil_skills
  http.get(`${SUPABASE_URL}/rest/v1/perfil_skills`, () => {
    return HttpResponse.json([])
  }),
  http.post(`${SUPABASE_URL}/rest/v1/perfil_skills`, () => {
    return HttpResponse.json({}, { status: 201 })
  }),
  http.patch(`${SUPABASE_URL}/rest/v1/perfil_skills`, () => {
    return HttpResponse.json({})
  }),

  // Casos
  http.get(`${SUPABASE_URL}/rest/v1/casos`, () => {
    return HttpResponse.json([
      { id: 'c1', estado: 'perfil_completo', persona_id: 'p1', organizacion_id: 'org1',
        personas: { nombre: 'María García', dni: '32456789' }, updated_at: '2026-03-25T10:00:00Z' },
    ])
  }),
  http.post(`${SUPABASE_URL}/rest/v1/casos`, () => {
    return HttpResponse.json({ id: 'c-new', estado: 'nuevo' }, { status: 201 })
  }),
  http.patch(`${SUPABASE_URL}/rest/v1/casos`, () => {
    return HttpResponse.json({ id: 'c1', estado: 'en_diagnostico' })
  }),

  // Derivaciones
  http.get(`${SUPABASE_URL}/rest/v1/derivaciones`, () => {
    return HttpResponse.json([])
  }),
  http.post(`${SUPABASE_URL}/rest/v1/derivaciones`, () => {
    return HttpResponse.json({ id: 'd-new', tipo: 'vacante', estado: 'derivado' }, { status: 201 })
  }),
  http.patch(`${SUPABASE_URL}/rest/v1/derivaciones`, () => {
    return HttpResponse.json({})
  }),

  // Eventos_caso
  http.get(`${SUPABASE_URL}/rest/v1/eventos_caso`, () => {
    return HttpResponse.json([])
  }),
  http.post(`${SUPABASE_URL}/rest/v1/eventos_caso`, () => {
    return HttpResponse.json({}, { status: 201 })
  }),

  // Vacantes_oe
  http.get(`${SUPABASE_URL}/rest/v1/vacantes_oe`, () => {
    return HttpResponse.json([])
  }),

  // Scraping live stats
  http.get(`${SUPABASE_URL}/rest/v1/scraping_live_stats`, () => {
    return HttpResponse.json({
      id: 'current', total_ofertas: 29154,
      portales: { bumeran: { total: 5516 }, computrabajo: { total: 16993 }, zonajobs: { total: 3404 } },
      ultimo_scraping: '2026-03-23T11:28:18Z',
    })
  }),

  // Pipeline local status
  http.get(`${SUPABASE_URL}/rest/v1/pipeline_local_status`, () => {
    return HttpResponse.json({
      id: 'current', total_ofertas: 42485, nlp_procesadas: 38025, nlp_pendientes: 4460,
      nlp_aprobados: 37776, nlp_bloqueados: 0, nlp_gate_aprobado_pct: 100,
      matching_con: 37776, matching_sin: 0, validadas: 37776, errores_pendientes: 0,
      en_supabase: 37776, pendientes_sync: 0,
    })
  }),

  // Pipeline commands table
  http.get(`${SUPABASE_URL}/rest/v1/pipeline_commands`, () => {
    return HttpResponse.json([
      {
        id: 'cmd-1', comando: 'run_pipeline', params: { limit: 500 },
        estado: 'completado', log: 'Procesadas 500 ofertas',
        resultado: { procesadas: 500, errores: 12 },
        creado_por: 'admin@oede.gob.ar',
        created_at: '2026-03-22T15:00:00Z',
        started_at: '2026-03-22T15:00:05Z',
        completed_at: '2026-03-22T15:02:34Z',
      },
    ])
  }),

  http.post(`${SUPABASE_URL}/rest/v1/pipeline_commands`, () => {
    return HttpResponse.json({
      id: 'cmd-new', comando: 'run_pipeline', estado: 'pendiente',
      creado_por: 'admin@oede.gob.ar', created_at: '2026-03-22T16:00:00Z',
    }, { status: 201 })
  }),

  // Catálogo MOL tables
  http.get(`${SUPABASE_URL}/rest/v1/catalogo_mol_skills`, () => {
    return HttpResponse.json([], { headers: { 'content-range': '0-0/0' } })
  }),

  http.post(`${SUPABASE_URL}/rest/v1/catalogo_mol_skills`, () => {
    return HttpResponse.json({ id: 'mol-skill-test', label: 'Test', estado: 'detectada' }, { status: 201 })
  }),

  http.patch(`${SUPABASE_URL}/rest/v1/catalogo_mol_skills`, () => {
    return HttpResponse.json({ id: 'mol-skill-test', estado: 'catalogada' })
  }),

  http.get(`${SUPABASE_URL}/rest/v1/catalogo_mol_ocupaciones`, () => {
    return HttpResponse.json([], { headers: { 'content-range': '0-0/0' } })
  }),

  http.post(`${SUPABASE_URL}/rest/v1/catalogo_mol_ocupaciones`, () => {
    return HttpResponse.json({ id: 'mol-occ-test', label: 'Test', estado: 'detectada' }, { status: 201 })
  }),

  http.patch(`${SUPABASE_URL}/rest/v1/catalogo_mol_ocupaciones`, () => {
    return HttpResponse.json({ id: 'mol-occ-test', estado: 'catalogada' })
  }),

  http.get(`${SUPABASE_URL}/rest/v1/catalogo_mol_versiones`, () => {
    return HttpResponse.json([])
  }),

  http.post(`${SUPABASE_URL}/rest/v1/catalogo_mol_versiones`, () => {
    return HttpResponse.json({ id: 'uuid-v1', version: 'v1.0', total_skills: 0, total_ocupaciones: 0 }, { status: 201 })
  }),

  // RPC: get_unclassified_items
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_unclassified_items`, () => {
    return HttpResponse.json({
      total_ofertas: 15968,
      unclassified_skills: [
        { label: 'Docker Compose', frecuencia: 45, pct: 0.28 },
        { label: 'Terraform', frecuencia: 12, pct: 0.08 },
      ],
      unclassified_skills_count: 2,
      unclassified_titles: [
        { label: 'Community Manager', frecuencia: 30, pct: 0.19, avg_score: 0.35, isco_mode: '2431' },
      ],
      unclassified_titles_count: 1,
      min_frecuencia: 3,
    })
  }),

  // RPC: get_catalogo_stats
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_catalogo_stats`, () => {
    return HttpResponse.json({
      skills: { total: 0, catalogadas: 0, en_revision: 0, detectadas: 0, descartadas: 0, por_tipo: {} },
      ocupaciones: { total: 0, catalogadas: 0, en_revision: 0, detectadas: 0, descartadas: 0 },
      versiones: [],
      ultima_version: null,
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

  // Perfil Argentino Versiones
  http.get('/api/perfil-argentino-versiones', () => {
    return HttpResponse.json({
      activa: {
        id: 'uuid-1', version: 'v1.0', total_skills: 14257,
        total_emergentes_aprobadas: 0, total_ocupaciones: 3046,
        nota: 'Version base ESCO', creado_por: 'admin@oede.gob.ar',
        activa: true, created_at: '2026-01-15T00:00:00Z',
      },
      versiones: [
        {
          id: 'uuid-1', version: 'v1.0', total_skills: 14257,
          total_emergentes_aprobadas: 0, total_ocupaciones: 3046,
          nota: 'Version base ESCO', creado_por: 'admin@oede.gob.ar',
          activa: true, created_at: '2026-01-15T00:00:00Z',
        },
      ],
      estado_actual: {
        ofertas_desde_ultimo_corte: 2132,
        emergentes_nuevas: 8,
        emergentes_pendientes: 3,
        skills_aprobadas_desde_corte: 5,
      },
    })
  }),

  http.post('/api/perfil-argentino-versiones', () => {
    return HttpResponse.json({
      version: {
        id: 'uuid-2', version: 'v1.1', total_skills: 14262,
        total_emergentes_aprobadas: 5, total_ocupaciones: 3046,
        nota: 'Nueva version', creado_por: 'admin@oede.gob.ar',
        activa: true, created_at: '2026-03-21T00:00:00Z',
      },
    }, { status: 201 })
  }),

  http.patch('/api/perfil-argentino-versiones', () => {
    return HttpResponse.json({ ok: true })
  }),

  // Training suggestions
  http.get('/api/training-suggestions', () => {
    return HttpResponse.json({
      by_gap: [
        {
          skill_label: 'Docker',
          courses: [
            {
              id: 1, name: 'Docker para principiantes', certificacion: 'Certificado CABA',
              duracion: '40hs', modalidad: 'virtual', covers_skills: ['Docker', 'containers'],
              url: 'https://capacitacion.example.com/1',
            },
          ],
        },
        {
          skill_label: 'Python',
          courses: [
            {
              id: 2, name: 'Python nivel inicial', certificacion: '',
              duracion: '60hs', modalidad: 'presencial', covers_skills: ['Python'],
            },
          ],
        },
      ],
      transition_demand: [
        {
          ocupacion_label: 'Analista DevOps',
          isco: '2511',
          trend_pct: 35,
          match_score: 72,
          skills_gap: ['Kubernetes', 'CI/CD'],
          estimated_months: 6,
        },
        {
          ocupacion_label: 'Ingeniero de datos',
          isco: '2529',
          trend_pct: 28,
          match_score: 65,
          skills_gap: ['Spark', 'Airflow', 'dbt'],
          estimated_months: 9,
        },
      ],
    })
  }),

  // Matching offers
  http.get('/api/matching-offers', ({ request }) => {
    const url = new URL(request.url)
    const page = Number(url.searchParams.get('page') ?? '1')
    const provincia = url.searchParams.get('provincia') ?? ''
    const modalidad = url.searchParams.get('modalidad') ?? ''

    const allOffers = [
      {
        id_oferta: 1, titulo: 'Desarrollador React', empresa: 'TechCorp',
        provincia: 'CABA', localidad: 'Palermo', modalidad: 'remoto',
        fecha_publicacion: '2026-03-15T00:00:00Z', url_oferta: 'https://example.com/1',
        match_score: 85, skills_cubiertas: ['JavaScript', 'React'], skills_gap: ['Docker'],
      },
      {
        id_oferta: 2, titulo: 'Analista de Datos', empresa: 'DataCo',
        provincia: 'Buenos Aires', localidad: 'La Plata', modalidad: 'presencial',
        fecha_publicacion: '2026-03-10T00:00:00Z', url_oferta: 'https://example.com/2',
        match_score: 60, skills_cubiertas: ['SQL'], skills_gap: ['Python', 'Power BI'],
      },
    ]

    let filtered = allOffers
    if (provincia) filtered = filtered.filter((o) => o.provincia === provincia)
    if (modalidad) filtered = filtered.filter((o) => o.modalidad === modalidad)

    const pageSize = 10
    const start = (page - 1) * pageSize
    return HttpResponse.json({ offers: filtered.slice(start, start + pageSize), total: filtered.length })
  }),

  // Compatibility report generate (POST)
  http.post('/api/compatibility-report', () => {
    return HttpResponse.json(
      { token: 'mock-token-abc123', pdfUrl: '/mock/reporte.pdf' },
      { status: 201 }
    )
  }),

  // Compatibility report
  http.get('/api/compatibility-report', ({ request }) => {
    const url = new URL(request.url)
    const token = url.searchParams.get('token')
    if (token === 'expired-token') {
      return HttpResponse.json({
        estado: 'expirado',
        candidato_nombre: 'Juan Perez',
        ocupacion_label: '',
        ocupacion_isco: '',
        match_score: 0,
        perfil_consolidado_version: 'v1.0',
        skills_candidato: [],
        skills_requeridas: [],
        skills_cubiertas: [],
        skills_gap: [],
        created_at: '2026-01-01T00:00:00Z',
        expira_at: '2026-02-01T00:00:00Z',
      })
    }
    if (!token || token === 'invalid') {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json({
      candidato_nombre: 'Juan Perez',
      ocupacion_label: 'Desarrollador de software',
      ocupacion_isco: '2512',
      match_score: 78,
      perfil_consolidado_version: 'v1.0',
      estado: 'activo',
      created_at: '2026-03-18T00:00:00Z',
      expira_at: '2026-05-18T00:00:00Z',
      skills_candidato: [],
      skills_requeridas: [
        { uri: 'esco:001', label: 'JavaScript', type: 'skill', source: 'esco' },
        { uri: 'esco:002', label: 'Python', type: 'skill', source: 'esco' },
        { uri: 'esco:003', label: 'Docker', type: 'skill', source: 'esco' },
      ],
      skills_cubiertas: [
        { uri: 'esco:001', label: 'JavaScript', type: 'skill', source: 'esco' },
        { uri: 'esco:002', label: 'Python', type: 'skill', source: 'esco' },
      ],
      skills_gap: [
        { uri: 'esco:003', label: 'Docker', type: 'skill', source: 'esco' },
      ],
    })
  }),

  // Skills extract from text
  http.post('/api/skills-extract-from-text', () => {
    return HttpResponse.json({
      skills: [
        {
          uri: 'http://data.europa.eu/esco/skill/001',
          label: 'soldadura MIG',
          type: 'skill',
          description: 'Capacidad para realizar soldadura por arco metálico con gas inerte.',
          source: 'esco',
          frequency: 12,
        },
        {
          uri: 'http://data.europa.eu/esco/skill/003',
          label: 'operación de torno CNC',
          type: 'skill',
          description: 'Manejo y programación de tornos de control numérico computarizado.',
          source: 'esco',
          frequency: 7,
        },
      ],
    })
  }),

  // RPC: preview_rule_impact
  http.post(`${SUPABASE_URL}/rest/v1/rpc/preview_rule_impact`, () => {
    return HttpResponse.json(mockPreviewImpact)
  }),

  // RPC: get_rule_suggestions
  http.post(`${SUPABASE_URL}/rest/v1/rpc/get_rule_suggestions`, () => {
    return HttpResponse.json(mockSugerencias)
  }),

  // PostgREST: config_overrides - GET (read override)
  http.get(`${SUPABASE_URL}/rest/v1/config_overrides`, ({ request }) => {
    const url = new URL(request.url)
    const configKeyFilter = url.searchParams.get('config_key')
    if (configKeyFilter && configKeyFilter.includes('matching_rules_business')) {
      return HttpResponse.json(mockConfigOverride)
    }
    // No override found
    return HttpResponse.json(null)
  }),

  // PostgREST: config_overrides - POST/PATCH (upsert)
  http.post(`${SUPABASE_URL}/rest/v1/config_overrides`, () => {
    return HttpResponse.json(mockConfigUpsertResult, { status: 201 })
  }),

  // Skills search
  http.get('/api/skills-search', ({ request }) => {
    const url = new URL(request.url)
    const q = url.searchParams.get('q') ?? ''
    const results = q
      ? [
          {
            uri: 'http://data.europa.eu/esco/skill/001',
            label: 'soldadura MIG',
            type: 'skill',
            description: 'Capacidad para realizar soldadura por arco metálico con gas inerte.',
            source: 'esco',
            frequency: 12,
          },
          {
            uri: 'http://data.europa.eu/esco/skill/002',
            label: 'lectura de planos técnicos',
            type: 'knowledge',
            description: 'Interpretación de planos de ingeniería y diagramas técnicos.',
            source: 'esco',
            frequency: 8,
          },
        ]
      : []
    return HttpResponse.json({ results })
  }),
]
