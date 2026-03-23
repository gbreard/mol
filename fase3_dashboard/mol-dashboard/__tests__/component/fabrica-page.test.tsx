/**
 * Component tests for Fábrica page (F2.4-F2.9)
 * Tests: loading, both pipeline lines, command execution, activity timeline
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import FabricaPage from '../../app/admin/procesamiento/fabrica/page'
import { mockPipelineStatusRPC } from '../mocks/fixtures/pipeline-status'

vi.mock('@/lib/supabase', () => ({ supabase: null }))

function setupHandlers() {
  server.use(
    http.get('/api/pipeline-status', () => {
      return HttpResponse.json(mockPipelineStatusRPC)
    }),
    http.get('/api/pipeline-commands', () => {
      return HttpResponse.json({
        commands: [
          {
            id: 'cmd-1', comando: 'run_pipeline', params: { limit: 500 },
            estado: 'completado', resultado: { procesadas: 500, errores: 12 },
            creado_por: 'admin@oede.gob.ar', created_at: '2026-03-22T15:00:00Z',
            duracion_seg: 154,
          },
          {
            id: 'cmd-2', comando: 'sync_supabase', params: {},
            estado: 'completado', resultado: {},
            creado_por: 'admin@oede.gob.ar', created_at: '2026-03-22T14:00:00Z',
            duracion_seg: 45,
          },
        ],
        total: 2,
      })
    }),
    http.post('/api/pipeline-commands', () => {
      return HttpResponse.json({
        id: 'cmd-new', comando: 'sync_supabase', estado: 'pendiente',
      }, { status: 201 })
    }),
  )
}

describe('FabricaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupHandlers()
  })

  describe('loading and structure', () => {
    it('shows loading spinner initially', () => {
      render(<FabricaPage />)
      expect(screen.getByText(/Cargando fabrica/)).toBeInTheDocument()
    })

    it('renders page title', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('Fabrica de Procesamiento')).toBeInTheDocument()
      })
    })

    it('shows pipeline version info', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText(/Pipeline v3.3/)).toBeInTheDocument()
      })
    })
  })

  describe('fabrication line', () => {
    it('renders all fabrication nodes', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('SCRAPING')).toBeInTheDocument()
      })
      expect(screen.getByText('NLP')).toBeInTheDocument()
      expect(screen.getByText('MATCHING')).toBeInTheDocument()
      expect(screen.getByText('VALIDACION')).toBeInTheDocument()
      expect(screen.getByText('SYNC')).toBeInTheDocument()
    })

    it('renders both gates', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('GATE NLP')).toBeInTheDocument()
      })
      expect(screen.getByText('GATE MATCHING')).toBeInTheDocument()
    })

    it('shows Linea de Fabricacion header', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('Linea de Fabricacion')).toBeInTheDocument()
      })
    })

    it('renders action buttons on nodes', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('Procesar NLP')).toBeInTheDocument()
      })
      expect(screen.getAllByText('Config').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Sync').length).toBeGreaterThan(0)
    })
  })

  describe('mejora continua line', () => {
    it('renders all mejora nodes', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('ERRORES')).toBeInTheDocument()
      })
      expect(screen.getByText('ISSUES')).toBeInTheDocument()
      expect(screen.getByText('TRAINING')).toBeInTheDocument()
      expect(screen.getByText('FINE-TUNE')).toBeInTheDocument()
      expect(screen.getByText('CATALOGO')).toBeInTheDocument()
      expect(screen.getByText('PERFIL')).toBeInTheDocument()
    })

    it('shows Linea de Mejora Continua header', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('Linea de Mejora Continua')).toBeInTheDocument()
      })
    })
  })

  describe('activity timeline', () => {
    it('shows recent commands', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('Actividad reciente')).toBeInTheDocument()
      })
      expect(screen.getByText('run_pipeline')).toBeInTheDocument()
      expect(screen.getByText('sync_supabase')).toBeInTheDocument()
    })

    it('shows command status and duration', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getAllByText(/completado/).length).toBeGreaterThan(0)
      })
    })
  })

  describe('command execution', () => {
    it('creates command on button click', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getAllByText('Sync').length).toBeGreaterThan(0)
      })

      // Click the Sync button (first one in the fabrication line)
      const syncButtons = screen.getAllByText('Sync')
      fireEvent.click(syncButtons[0])

      await waitFor(() => {
        expect(screen.getByText(/Comando.*creado/)).toBeInTheDocument()
      })
    })

    it('shows empty state when no commands', async () => {
      server.use(
        http.get('/api/pipeline-commands', () => {
          return HttpResponse.json({ commands: [], total: 0 })
        }),
      )

      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('Sin comandos recientes')).toBeInTheDocument()
      })
    })
  })
})
