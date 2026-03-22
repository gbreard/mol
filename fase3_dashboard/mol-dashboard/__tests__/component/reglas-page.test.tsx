/**
 * Component tests for ReglasPage (I2 — reglas de negocio editor)
 * Tests: loading, display, search, new rule form, preview, sugerencias
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import ReglasPage from '../../app/admin/procesamiento/reglas/page'
import { mockConfigOverride, mockPreviewImpact, mockSugerencias } from '../mocks/fixtures/config-editor'

// Mock supabase import (page imports it but doesn't use it directly for config-editor)
vi.mock('@/lib/supabase', () => ({
  supabase: null,
}))

function setupApiHandlers() {
  server.use(
    // GET /api/config-editor?key=matching_rules_business
    http.get('/api/config-editor', ({ request }) => {
      const url = new URL(request.url)
      const key = url.searchParams.get('key')
      if (key === 'matching_rules_business') {
        return HttpResponse.json({
          config_key: 'matching_rules_business',
          source: 'override',
          data: mockConfigOverride.json_value,
          version: mockConfigOverride.version,
          updated_by: mockConfigOverride.updated_by,
          updated_at: mockConfigOverride.updated_at,
          changelog: mockConfigOverride.changelog,
        })
      }
      return HttpResponse.json({ source: 'local', data: null, version: 0 })
    }),

    // POST /api/config-editor/preview (preview impacto)
    http.post('/api/config-editor/preview', () => {
      return HttpResponse.json(mockPreviewImpact)
    }),

    // GET /api/config-editor/preview (sugerencias)
    http.get('/api/config-editor/preview', () => {
      return HttpResponse.json(mockSugerencias)
    }),

    // PUT /api/config-editor (save)
    http.put('/api/config-editor', () => {
      return HttpResponse.json({
        config_key: 'matching_rules_business',
        version: 4,
        updated_by: 'admin@oede.gob.ar',
        message: 'Config guardado. El pipeline usará este override.',
      })
    }),
  )
}

describe('ReglasPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupApiHandlers()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.spyOn(window, 'alert').mockImplementation(() => {})
  })

  describe('loading and initial render', () => {
    it('shows loading spinner initially', () => {
      render(<ReglasPage />)
      expect(screen.getByText('Cargando reglas...')).toBeInTheDocument()
    })

    it('loads and displays rules from config', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Procesamiento — Reglas de negocio')).toBeInTheDocument()
      })

      // Header and footer both show rule count
      expect(screen.getAllByText(/2 reglas/).length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText(/override/).length).toBeGreaterThanOrEqual(1)
    })

    it('displays rule names from config', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Gerente de Ventas')).toBeInTheDocument()
      })
      expect(screen.getByText('Contador')).toBeInTheDocument()
    })

    it('displays ISCO codes', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('1221')).toBeInTheDocument()
      })
      expect(screen.getByText('2411')).toBeInTheDocument()
    })
  })

  describe('search', () => {
    it('filters rules by name', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Gerente de Ventas')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/Buscar por ID/i)
      fireEvent.change(searchInput, { target: { value: 'contador' } })

      expect(screen.queryByText('Gerente de Ventas')).not.toBeInTheDocument()
      expect(screen.getByText('Contador')).toBeInTheDocument()
    })

    it('filters rules by ISCO code', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Gerente de Ventas')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/Buscar por ID/i)
      fireEvent.change(searchInput, { target: { value: '2411' } })

      expect(screen.queryByText('Gerente de Ventas')).not.toBeInTheDocument()
      expect(screen.getByText('Contador')).toBeInTheDocument()
    })

    it('shows count of filtered results', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText(/2 de 2 reglas/)).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/Buscar por ID/i)
      fireEvent.change(searchInput, { target: { value: 'gerente' } })

      expect(screen.getByText(/1 de 2 reglas/)).toBeInTheDocument()
    })
  })

  describe('new rule form', () => {
    it('opens form when clicking "Nueva regla"', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Nueva regla')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Nueva regla'))

      expect(screen.getByText('Nueva regla de matching')).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/Ej: Gerente de Ventas/)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/Ej: 1221/)).toBeInTheDocument()
    })

    it('closes form when clicking "Cancelar"', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Nueva regla'))
      })

      expect(screen.getByText('Nueva regla de matching')).toBeInTheDocument()

      fireEvent.click(screen.getByText('Cancelar'))

      expect(screen.queryByText('Nueva regla de matching')).not.toBeInTheDocument()
    })

    it('adds a new rule to the list', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Nueva regla'))
      })

      fireEvent.change(screen.getByPlaceholderText(/Ej: Gerente de Ventas/), { target: { value: 'Analista de Datos' } })
      fireEvent.change(screen.getByPlaceholderText(/gerente de ventas, director/), { target: { value: 'analista de datos' } })
      fireEvent.change(screen.getByPlaceholderText(/Ej: 1221/), { target: { value: '2511' } })

      fireEvent.click(screen.getByText('Agregar regla'))

      await waitFor(() => {
        expect(screen.getByText('Analista de Datos')).toBeInTheDocument()
      })
      expect(screen.getAllByText(/3 reglas/).length).toBeGreaterThanOrEqual(1)
    })

    it('shows validation alert for incomplete form', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Nueva regla'))
      })

      fireEvent.change(screen.getByPlaceholderText(/Ej: Gerente de Ventas/), { target: { value: 'Test' } })

      fireEvent.click(screen.getByText('Agregar regla'))

      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining('nombre'))
    })
  })

  describe('preview impacto', () => {
    it('loads preview when clicking "Preview impacto"', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Nueva regla'))
      })

      fireEvent.change(screen.getByPlaceholderText(/gerente de ventas, director/), { target: { value: 'gerente' } })
      fireEvent.change(screen.getByPlaceholderText(/Ej: 1221/), { target: { value: '1221' } })

      fireEvent.click(screen.getByText('Preview impacto'))

      await waitFor(() => {
        expect(screen.getByText('Impacto de la regla')).toBeInTheDocument()
      })

      // KPI cards
      expect(screen.getByText('45')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument()
      expect(screen.getByText('33')).toBeInTheDocument()
      expect(screen.getByText('Ofertas que matchean')).toBeInTheDocument()
      expect(screen.getByText('Cambiarían ISCO')).toBeInTheDocument()
    })

    it('shows examples table in preview', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Nueva regla'))
      })

      fireEvent.change(screen.getByPlaceholderText(/gerente de ventas, director/), { target: { value: 'gerente' } })
      fireEvent.change(screen.getByPlaceholderText(/Ej: 1221/), { target: { value: '1221' } })

      fireEvent.click(screen.getByText('Preview impacto'))

      await waitFor(() => {
        // "Gerente de Ventas" appears both as rule name and as example — check examples section
        expect(screen.getByText('Gerente Comercial')).toBeInTheDocument()
      })
    })

    it('shows distribution badges', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Nueva regla'))
      })

      fireEvent.change(screen.getByPlaceholderText(/gerente de ventas, director/), { target: { value: 'gerente' } })
      fireEvent.change(screen.getByPlaceholderText(/Ej: 1221/), { target: { value: '1221' } })

      fireEvent.click(screen.getByText('Preview impacto'))

      await waitFor(() => {
        expect(screen.getByText(/5223 \(20\)/)).toBeInTheDocument()
      })
    })

    it('disables preview button when fields are empty', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Nueva regla'))
      })

      const previewBtn = screen.getByText('Preview impacto').closest('button')
      expect(previewBtn).toBeDisabled()
    })
  })

  describe('sugerencias', () => {
    it('loads and shows sugerencias panel', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Sugerencias')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Sugerencias'))

      await waitFor(() => {
        expect(screen.getByText(/Reglas sugeridas/)).toBeInTheDocument()
      })
    })

    it('displays suggestion details', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Sugerencias'))
      })

      await waitFor(() => {
        // Multiple elements match "gerente de ventas" (suggestion + rule table)
        expect(screen.getAllByText(/gerente de ventas/i).length).toBeGreaterThanOrEqual(1)
      })
      expect(screen.getByText(/45 ofertas afectadas/)).toBeInTheDocument()
    })

    it('pre-fills form when clicking "Usar"', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        fireEvent.click(screen.getByText('Sugerencias'))
      })

      await waitFor(() => {
        expect(screen.getAllByText('Usar').length).toBeGreaterThan(0)
      })

      fireEvent.click(screen.getAllByText('Usar')[0])

      await waitFor(() => {
        expect(screen.getByText('Nueva regla de matching')).toBeInTheDocument()
      })

      const iscoInput = screen.getByPlaceholderText(/Ej: 1221/) as HTMLInputElement
      expect(iscoInput.value).toBe('1221')
    })
  })

  describe('save to Supabase', () => {
    it('shows "Guardar cambios" button after adding a rule', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Gerente de Ventas')).toBeInTheDocument()
      })

      expect(screen.queryByText('Guardar cambios')).not.toBeInTheDocument()

      // Add a rule to trigger hasChanges
      fireEvent.click(screen.getByText('Nueva regla'))
      fireEvent.change(screen.getByPlaceholderText(/Ej: Gerente de Ventas/), { target: { value: 'Test Rule' } })
      fireEvent.change(screen.getByPlaceholderText(/gerente de ventas, director/), { target: { value: 'test' } })
      fireEvent.change(screen.getByPlaceholderText(/Ej: 1221/), { target: { value: '9999' } })
      fireEvent.click(screen.getByText('Agregar regla'))

      expect(screen.getByText('Guardar cambios')).toBeInTheDocument()
    })

    it('saves and shows success message', async () => {
      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Gerente de Ventas')).toBeInTheDocument()
      })

      // Add a rule to trigger hasChanges
      fireEvent.click(screen.getByText('Nueva regla'))
      fireEvent.change(screen.getByPlaceholderText(/Ej: Gerente de Ventas/), { target: { value: 'Test Rule' } })
      fireEvent.change(screen.getByPlaceholderText(/gerente de ventas, director/), { target: { value: 'test' } })
      fireEvent.change(screen.getByPlaceholderText(/Ej: 1221/), { target: { value: '9999' } })
      fireEvent.click(screen.getByText('Agregar regla'))

      await waitFor(() => {
        expect(screen.getByText('Guardar cambios')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Guardar cambios'))

      await waitFor(() => {
        expect(screen.getByText(/Guardado v4/)).toBeInTheDocument()
      })
    })
  })

  describe('local fallback', () => {
    it('handles local source config', async () => {
      // Override with local-only response
      server.use(
        http.get('/api/config-editor', () => {
          return HttpResponse.json({
            config_key: 'matching_rules_business',
            source: 'local',
            data: null,
            version: 0,
          })
        }),
        http.get('/data/matching_rules_business.json', () => {
          return HttpResponse.json({
            reglas_forzar_isco: {
              R1_test: {
                nombre: 'Test Local',
                prioridad: 1,
                condicion: { titulo_contiene: 'test' },
                forzar_isco: '1111',
              },
            },
          })
        }),
      )

      render(<ReglasPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Local')).toBeInTheDocument()
      })
      expect(screen.getAllByText(/local/).length).toBeGreaterThanOrEqual(1)
    })
  })
})
