/**
 * Component tests for Fábrica page (3 secciones: embudo, performance, controles)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import FabricaPage from '../../app/admin/procesamiento/fabrica/page'

vi.mock('@/lib/supabase', () => ({ supabase: null }))

function setupHandlers() {
  server.use(
    http.get('/api/pipeline-local-status', () => {
      return HttpResponse.json({
        id: 'current', total_ofertas: 44382, nlp_procesadas: 43862, nlp_pendientes: 520,
        nlp_aprobados: 37776, nlp_bloqueados: 0, nlp_gate_aprobado_pct: 86,
        matching_con: 37776, matching_sin: 0, validadas: 37776, errores_pendientes: 0,
        en_supabase: 37776, pendientes_sync: 0,
      })
    }),
    http.get('/api/pipeline-commands', () => {
      return HttpResponse.json({
        commands: [{
          id: 'cmd-1', comando: 'run_nlp', params: { limit: 1000 },
          estado: 'completado', resultado: { procesadas: 1000, errores: 24, exit_code: 0 },
          creado_por: 'admin@oede.gob.ar', created_at: '2026-03-25T15:00:00Z', duracion_seg: 3600,
        }],
        total: 1,
      })
    }),
    http.post('/api/pipeline-commands', () => {
      return HttpResponse.json({ id: 'cmd-new', estado: 'pendiente' }, { status: 201 })
    }),
  )
}

describe('FabricaPage', () => {
  beforeEach(() => { vi.clearAllMocks(); setupHandlers(); })

  describe('estructura', () => {
    it('muestra titulo', async () => {
      render(<FabricaPage />)
      await waitFor(() => expect(screen.getByText('Fabrica de Procesamiento')).toBeInTheDocument())
    })

    it('muestra las 3 secciones', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText(/Embudo de datos/)).toBeInTheDocument()
      })
      expect(screen.getByText(/Performance del pipeline/)).toBeInTheDocument()
      expect(screen.getByText(/Controles/)).toBeInTheDocument()
      expect(screen.getByText(/Actividad reciente/)).toBeInTheDocument()
    })
  })

  describe('embudo', () => {
    it('muestra todas las etapas del embudo', async () => {
      render(<FabricaPage />)
      await waitFor(() => expect(screen.getByText('Ofertas totales')).toBeInTheDocument())
      expect(screen.getByText('Con NLP')).toBeInTheDocument()
      expect(screen.getByText('Gate aprobado')).toBeInTheDocument()
      expect(screen.getByText('Con matching')).toBeInTheDocument()
      expect(screen.getByText('Validadas')).toBeInTheDocument()
      expect(screen.getByText('En dashboard')).toBeInTheDocument()
    })

    it('muestra verificacion que cierra', async () => {
      render(<FabricaPage />)
      await waitFor(() => expect(screen.getByText(/cierra/)).toBeInTheDocument())
    })

    it('muestra pendientes gate como cuello de botella', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText(/pendientes gate/i)).toBeInTheDocument()
      })
    })
  })

  describe('performance', () => {
    it('muestra KPIs de performance', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText(/Tasa aprobacion NLP/)).toBeInTheDocument()
      })
      expect(screen.getByText(/Errores pendientes/)).toBeInTheDocument()
    })

    it('linkea a aprendizaje', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText(/Ver detalle completo/)).toBeInTheDocument()
      })
    })
  })

  describe('controles', () => {
    it('muestra botones de accion', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('Controles')).toBeInTheDocument()
      })
      expect(screen.getByText('Matching')).toBeInTheDocument()
      expect(screen.getByText('Sync Supabase')).toBeInTheDocument()
    })

    it('muestra badge de pendientes en botones', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getAllByText(/520 pend/).length).toBeGreaterThanOrEqual(1)
      }, { timeout: 3000 })
    })
  })

  describe('timeline', () => {
    it('muestra actividad reciente', async () => {
      render(<FabricaPage />)
      await waitFor(() => {
        expect(screen.getByText('Actividad reciente')).toBeInTheDocument()
      })
      expect(screen.getAllByText(/Completado/).length).toBeGreaterThanOrEqual(1)
    })
  })
})
