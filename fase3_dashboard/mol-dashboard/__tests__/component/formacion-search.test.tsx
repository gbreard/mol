import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import FormacionSearch from '@/components/FormacionSearch'

// Mock results matching the actual API response format (skills, not formacion titles)
const mockResults = [
  { uri: 'skill-redes', label: 'Redes', type: 'skill', description: 'Redes informáticas', source: 'esco' },
  { uri: 'skill-tcp', label: 'TCP/IP', type: 'skill', description: 'Protocolo TCP/IP', source: 'esco' },
  { uri: 'skill-cisco', label: 'Cisco', type: 'skill', description: 'Equipos Cisco', source: 'esco' },
]

// ─── S20: FormacionSearch ─────────────────────────────────────────────────────

describe('S20 — FormacionSearch', () => {
  it('renderiza input de búsqueda', () => {
    render(<FormacionSearch />)
    expect(screen.getByLabelText('Buscar título formativo')).toBeInTheDocument()
  })

  it('botón buscar deshabilitado si query vacío', () => {
    render(<FormacionSearch />)
    expect(screen.getByLabelText('Buscar formación')).toBeDisabled()
  })

  it('botón habilitado con texto en input', () => {
    render(<FormacionSearch />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), {
      target: { value: 'redes' },
    })
    expect(screen.getByLabelText('Buscar formación')).not.toBeDisabled()
  })

  it('Enter en el input dispara búsqueda', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockResults }),
    }))

    render(<FormacionSearch />)
    const input = screen.getByLabelText('Buscar título formativo')
    fireEvent.change(input, { target: { value: 'redes' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('Redes')).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('muestra resultados con competencias identificadas', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockResults }),
    }))

    render(<FormacionSearch />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), { target: { value: 'redes' } })
    fireEvent.click(screen.getByLabelText('Buscar formación'))

    await waitFor(() => {
      expect(screen.getByText('3 competencias identificadas')).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('muestra skills como badges', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockResults }),
    }))

    render(<FormacionSearch />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), { target: { value: 'redes' } })
    fireEvent.click(screen.getByLabelText('Buscar formación'))

    await waitFor(() => {
      expect(screen.getByText('Redes')).toBeInTheDocument()
      expect(screen.getByText('TCP/IP')).toBeInTheDocument()
      expect(screen.getByText('Cisco')).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('muestra skills derivadas como badges individuales', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockResults }),
    }))

    render(<FormacionSearch />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), { target: { value: 'redes' } })
    fireEvent.click(screen.getByLabelText('Buscar formación'))

    await waitFor(() => {
      expect(screen.getByText('TCP/IP')).toBeInTheDocument()
      expect(screen.getByText('Cisco')).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('sin resultados muestra mensaje vacío', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: [] }),
    }))

    render(<FormacionSearch />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), { target: { value: 'xyz' } })
    fireEvent.click(screen.getByLabelText('Buscar formación'))

    await waitFor(() => {
      expect(screen.getByText(/No se encontraron competencias/)).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('agregar llama onAgregar y cambia botón a "Agregadas"', async () => {
    const onAgregar = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockResults }),
    }))

    render(<FormacionSearch onAgregar={onAgregar} />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), { target: { value: 'redes' } })
    fireEvent.click(screen.getByLabelText('Buscar formación'))

    await waitFor(() => screen.getByLabelText('Agregar competencias al perfil'))
    fireEvent.click(screen.getByLabelText('Agregar competencias al perfil'))

    expect(onAgregar).toHaveBeenCalled()
    expect(screen.getByText('Agregadas')).toBeInTheDocument()
    vi.restoreAllMocks()
  })

  it('botones tienen min touch target', async () => {
    render(<FormacionSearch />)
    expect(screen.getByLabelText('Buscar formación').className).toContain('min-h-[44px]')
  })
})
