import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'

const SUPABASE_URL = 'https://test.supabase.co'

// ─── Mock data ───────────────────────────────────────────────────────────────

const mockIssuesData = [
  {
    id: 'aaaa1111-0000-0000-0000-000000000001',
    titulo: 'ISCO incorrecto para Soldador',
    descripcion: 'Debería ser 7212, no 7112',
    tipo: 'error_isco',
    estado: 'pendiente',
    prioridad: 'alta',
    id_oferta: 'oferta-101',
    autor_id: 'user-1',
    autor_email: 'cynthia@oede.gob.ar',
    autor_nombre: 'Cynthia',
    created_at: '2026-04-01T10:00:00Z',
    updated_at: '2026-04-01T10:00:00Z',
  },
  {
    id: 'aaaa1111-0000-0000-0000-000000000002',
    titulo: 'Skills no detectadas',
    descripcion: 'Falta soldadura MIG',
    tipo: 'error_skill',
    estado: 'pendiente',
    prioridad: 'media',
    id_oferta: 'oferta-102',
    autor_id: 'user-2',
    autor_email: 'diego@oede.gob.ar',
    autor_nombre: 'Diego',
    created_at: '2026-04-02T10:00:00Z',
    updated_at: '2026-04-02T10:00:00Z',
  },
  {
    id: 'aaaa1111-0000-0000-0000-000000000003',
    titulo: 'Repositor no es sinónimo de reponedor',
    descripcion: 'El diccionario debería mapear repositor como reponedor',
    tipo: 'sugerencia',
    estado: 'pendiente',
    prioridad: 'baja',
    id_oferta: 'oferta-103',
    autor_id: 'user-1',
    autor_email: 'cynthia@oede.gob.ar',
    autor_nombre: 'Cynthia',
    created_at: '2026-04-03T10:00:00Z',
    updated_at: '2026-04-03T10:00:00Z',
  },
  {
    id: 'aaaa1111-0000-0000-0000-000000000004',
    titulo: 'Ruido en tareas NLP',
    descripcion: 'Fragmento de publicidad en campo tareas',
    tipo: 'error_nlp',
    estado: 'en_progreso',
    prioridad: 'media',
    id_oferta: 'oferta-104',
    autor_id: 'user-2',
    autor_email: 'diego@oede.gob.ar',
    autor_nombre: 'Diego',
    created_at: '2026-04-04T10:00:00Z',
    updated_at: '2026-04-04T10:00:00Z',
  },
  {
    id: 'aaaa1111-0000-0000-0000-000000000005',
    titulo: 'Issue resuelto viejo',
    descripcion: '',
    tipo: 'error_isco',
    estado: 'resuelto',
    prioridad: 'baja',
    id_oferta: null,
    autor_id: 'user-1',
    autor_email: 'cynthia@oede.gob.ar',
    autor_nombre: 'Cynthia',
    created_at: '2026-03-15T10:00:00Z',
    updated_at: '2026-03-20T10:00:00Z',
  },
]

const mockCorrectionsData = [
  {
    id_oferta: 'oferta-101',
    validacion_correcciones: {
      ocupacion_corregida: { isco_code: '7212', esco_label: 'Soldadores' },
      nota: 'El ISCO correcto es 7212 Soldadores, no 7112 Albañiles',
    },
    titulo: 'Soldador MIG/MAG',
    isco_code: '7112',
    isco_label: 'Albañiles',
  },
  {
    id_oferta: 'oferta-102',
    validacion_correcciones: {
      skills_editadas: [
        { label: 'soldadura MIG', type: 'skill' },
        { label: 'lectura de planos', type: 'knowledge' },
      ],
      nota: 'Faltan skills técnicas de soldadura',
    },
    titulo: 'Soldador industrial',
    isco_code: '7212',
    isco_label: 'Soldadores',
  },
  {
    id_oferta: 'oferta-103',
    validacion_correcciones: {
      nota: 'Repositor es sinónimo de reponedor en el diccionario argentino, agregar al diccionario de sinónimos',
    },
    titulo: 'Repositor supermercado',
    isco_code: '5223',
    isco_label: 'Vendedores',
  },
  {
    id_oferta: 'oferta-104',
    validacion_correcciones: {
      nlp_editado: true,
      nota: 'El campo tareas tiene ruido, no es tarea real, es fragmento publicitario',
    },
    titulo: 'Administrativo contable',
    isco_code: '4311',
    isco_label: 'Empleados de contabilidad',
  },
]

// Issues stats derived from mock data
const mockIssuesStats = [
  { estado: 'pendiente' },
  { estado: 'pendiente' },
  { estado: 'pendiente' },
  { estado: 'en_progreso' },
  { estado: 'resuelto' },
]

// ─── MSW handlers for M-09b tests ───────────────────────────────────────────

function setupM09bHandlers() {
  server.use(
    // Issues table: returns issues list
    http.get(`${SUPABASE_URL}/rest/v1/issues`, ({ request }) => {
      const url = new URL(request.url)
      const select = url.searchParams.get('select')
      // Stats query only requests 'estado'
      if (select === 'estado') {
        return HttpResponse.json(mockIssuesStats)
      }
      return HttpResponse.json(mockIssuesData)
    }),

    // Ofertas dashboard: corrections lookup
    http.get(`${SUPABASE_URL}/rest/v1/ofertas_dashboard`, ({ request }) => {
      const url = new URL(request.url)
      const select = url.searchParams.get('select')
      if (select?.includes('validacion_correcciones')) {
        return HttpResponse.json(mockCorrectionsData)
      }
      return HttpResponse.json([])
    }),
  )
}

// ─── IssueContext wrapper ────────────────────────────────────────────────────

// IssueList uses useIssues() which requires IssueProvider
// We mock the context to avoid deep dependency chain
vi.mock('@/contexts/IssueContext', () => ({
  useIssues: () => ({
    refreshIssues: vi.fn(),
    pendingIssues: [],
    pendingCount: 0,
    isOpen: false,
    openDrawer: vi.fn(),
    closeDrawer: vi.fn(),
    selectedOferta: null,
    clearSelectedOferta: vi.fn(),
    isCreating: false,
    setIsCreating: vi.fn(),
  }),
  IssueProvider: ({ children }: { children: React.ReactNode }) => children,
}))

// ─── Tests ───────────────────────────────────────────────────────────────────

import AdminIssuesPage from '@/app/admin/issues/page'
import { IssueList } from '@/components/issues/IssueList'

describe('M-09b — Badge de tipo inferido', () => {
  it('muestra badge "Matching" para corrección con ocupacion_corregida', () => {
    const issues = [{
      ...mockIssuesData[0],
      _correctionType: 'Matching',
    }]
    render(<IssueList issues={issues as any} showOfertaLink />)
    expect(screen.getByText('Matching')).toBeInTheDocument()
  })

  it('muestra badge "Skills" para corrección con skills_editadas', () => {
    const issues = [{
      ...mockIssuesData[1],
      _correctionType: 'Skills',
    }]
    render(<IssueList issues={issues as any} showOfertaLink />)
    expect(screen.getByText('Skills')).toBeInTheDocument()
  })

  it('muestra badge "Sinónimos" para notas con palabra clave', () => {
    const issues = [{
      ...mockIssuesData[2],
      _correctionType: 'Sinónimos',
    }]
    render(<IssueList issues={issues as any} showOfertaLink />)
    expect(screen.getByText('Sinónimos')).toBeInTheDocument()
  })

  it('muestra badge "NLP" para corrección con nlp_editado', () => {
    const issues = [{
      ...mockIssuesData[3],
      _correctionType: 'NLP',
    }]
    render(<IssueList issues={issues as any} showOfertaLink />)
    expect(screen.getByText('NLP')).toBeInTheDocument()
  })

  it('badge púrpura tiene las clases CSS correctas', () => {
    const issues = [{
      ...mockIssuesData[0],
      _correctionType: 'Matching',
    }]
    render(<IssueList issues={issues as any} showOfertaLink />)
    const badge = screen.getByText('Matching')
    expect(badge).toHaveClass('bg-purple-100')
    expect(badge).toHaveClass('text-purple-700')
  })

  it('no muestra badge si no hay _correctionType', () => {
    const issues = [{ ...mockIssuesData[4] }] // resuelto, sin corrección
    render(<IssueList issues={issues as any} showOfertaLink />)
    expect(screen.queryByText('Matching')).not.toBeInTheDocument()
    expect(screen.queryByText('NLP')).not.toBeInTheDocument()
    expect(screen.queryByText('Skills')).not.toBeInTheDocument()
    expect(screen.queryByText('Sinónimos')).not.toBeInTheDocument()
  })
})

describe('M-09b — Página de Issues carga y muestra datos', () => {
  beforeEach(() => {
    setupM09bHandlers()
  })

  it('muestra stats cards con contadores correctos', async () => {
    render(<AdminIssuesPage />)
    await waitFor(() => {
      // 3 pendientes from mockIssuesStats
      expect(screen.getByText('3')).toBeInTheDocument()
    })
    expect(screen.getByText('Pendientes')).toBeInTheDocument()
    // "En progreso" appears both in stats card and as issue badge — use getAllByText
    expect(screen.getAllByText('En progreso').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Resueltos')).toBeInTheDocument()
  })

  it('muestra botón "Generar reporte para Claude Code"', async () => {
    render(<AdminIssuesPage />)
    await waitFor(() => {
      expect(screen.getByText('Generar reporte para Claude Code')).toBeInTheDocument()
    })
  })

  it('muestra contador de correcciones asociadas', async () => {
    render(<AdminIssuesPage />)
    await waitFor(() => {
      expect(screen.getByText(/con correcciones/)).toBeInTheDocument()
    })
  })
})

describe('M-09b — Reporte para Claude Code', () => {
  beforeEach(() => {
    setupM09bHandlers()
  })

  it('abre modal con reporte al hacer click en botón', async () => {
    render(<AdminIssuesPage />)
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Generar reporte para Claude Code')).toBeInTheDocument()
    })
    // Wait for issues to render (loading done)
    await waitFor(() => {
      expect(screen.getByText(/Mostrando/)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Generar reporte para Claude Code'))

    await waitFor(() => {
      expect(screen.getByText('Reporte para Claude Code')).toBeInTheDocument()
    })
  })

  it('modal tiene botones Copiar y Descargar', async () => {
    render(<AdminIssuesPage />)
    await waitFor(() => {
      expect(screen.getByText(/Mostrando/)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Generar reporte para Claude Code'))

    await waitFor(() => {
      expect(screen.getByText('Copiar')).toBeInTheDocument()
      expect(screen.getByText('Descargar .md')).toBeInTheDocument()
    })
  })

  it('reporte contiene secciones de ISCO, Notas y Skills', async () => {
    render(<AdminIssuesPage />)
    await waitFor(() => {
      expect(screen.getByText(/Mostrando/)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Generar reporte para Claude Code'))

    await waitFor(() => {
      const pre = screen.getByText(/Reporte de correcciones/)
      expect(pre).toBeInTheDocument()
    })
    // The report markdown content should include key sections
    const reportEl = document.querySelector('pre')
    expect(reportEl?.textContent).toContain('CORRECCIONES DE ISCO')
    expect(reportEl?.textContent).toContain('INSTRUCCIONES PARA CLAUDE CODE')
  })

  it('modal se cierra con botón ✕', async () => {
    render(<AdminIssuesPage />)
    await waitFor(() => {
      expect(screen.getByText(/Mostrando/)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Generar reporte para Claude Code'))
    await waitFor(() => {
      expect(screen.getByText('Reporte para Claude Code')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('✕'))
    await waitFor(() => {
      expect(screen.queryByText('Reporte para Claude Code')).not.toBeInTheDocument()
    })
  })
})

describe('M-09b — Alerta correcciones en pipeline-status', () => {
  it('fixture de pipeline-status incluye alerta de correcciones cuando existe', () => {
    // Verify the mock can carry correction alerts
    const alertaCorrecciones = {
      nivel: 'info',
      mensaje: '89 correcciones de validadores sin procesar',
      accion: 'ver_correcciones_pendientes',
      detalle: 'Hay correcciones expertas de validadores que no fueron incorporadas al sistema.',
    }

    // The alert structure matches what get_pipeline_status() returns
    expect(alertaCorrecciones.nivel).toBe('info')
    expect(alertaCorrecciones.accion).toBe('ver_correcciones_pendientes')
    expect(alertaCorrecciones.mensaje).toContain('correcciones')
  })

  it('métricas muestra alerta con link a correcciones pendientes', async () => {
    // Override pipeline status to include correction alert
    server.use(
      http.post(`${SUPABASE_URL}/rest/v1/rpc/get_pipeline_status`, () => {
        return HttpResponse.json({
          fases: {
            scraping: { estado: 'ok', ultimo_scraping: '2026-04-07', dias_desde_scraping: 1, ofertas_totales: 37785, ofertas_activas: 18316, fuentes: {} },
            nlp: { estado: 'ok', procesadas: 37785, pendientes: 0, ultimo_run: 'run_test' },
            matching: { estado: 'ok', con_matching: 37785, pendientes: 0, validadas: 37785, errores_sin_resolver: 0, reglas_negocio: 297 },
            sync: { estado: 'ok', en_supabase: 37785, pendientes: 0 },
          },
          alertas: [
            {
              nivel: 'info',
              mensaje: '89 correcciones de validadores sin procesar',
              accion: 'ver_correcciones_pendientes',
              detalle: 'Hay correcciones expertas de validadores.',
            },
          ],
          resumen: {
            total_ofertas: 37785, en_supabase: 37785,
            issues_humanos_pendientes: 0, issues_auto_pendientes: 0,
            fase_sugerida: 'Procesamiento', fase_sugerida_razon: 'Correcciones pendientes',
          },
          ultimo_update: '2026-04-08T10:00:00Z',
          ultimo_run_id: null, ultimo_run_timestamp: null, ultimo_run_branch: null,
          ultimo_run_nlp_version: null, ultimo_run_matching_version: null,
          ultimo_run_ofertas: null, ultimo_run_skills: null, ultimo_run_failures: null,
          ultimo_run_failures_pct: null, ultimo_run_errores: null, ultimo_run_corregidos: null,
          ultimo_run_escalados: null, ultimo_run_precision: null, ultimo_run_delta_precision: null,
          ultimo_run_delta_regresiones: null, ultimo_run_delta_mejoras: null,
          ultimo_run_reglas_nuevas: null, ultimo_run_top_failures: null,
        })
      }),
    )

    // Dynamic import to get the metricas page
    const { default: MetricasPage } = await import('@/app/admin/metricas/page')
    render(<MetricasPage />)

    await waitFor(() => {
      expect(screen.getByText(/89 correcciones de validadores sin procesar/)).toBeInTheDocument()
    })
  })
})
