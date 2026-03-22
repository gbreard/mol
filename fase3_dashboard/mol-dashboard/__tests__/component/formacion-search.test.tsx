import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import FormacionSearch from '@/components/FormacionSearch'

const mockResults = [
  {
    id: 'f1',
    titulo: 'Tecnicatura en Redes y Telecomunicaciones',
    institucion: 'UTN',
    nivel: 'Tecnicatura',
    resolucion: '1234/2022',
    verificado: true,
    skills_derivadas: ['Redes', 'TCP/IP', 'Cisco'],
  },
  {
    id: 'f2',
    titulo: 'Curso de Redes Básicas',
    institucion: 'CABA Digital',
    nivel: 'Curso',
    verificado: false,
    skills_derivadas: ['Redes'],
  },
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
      expect(screen.getByText('Tecnicatura en Redes y Telecomunicaciones')).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('muestra resultados con título e institución', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockResults }),
    }))

    render(<FormacionSearch />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), { target: { value: 'redes' } })
    fireEvent.click(screen.getByLabelText('Buscar formación'))

    await waitFor(() => {
      expect(screen.getByText('UTN')).toBeInTheDocument()
      expect(screen.getByText('CABA Digital')).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('badge Verificado solo en resultados con verificado=true', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockResults }),
    }))

    render(<FormacionSearch />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), { target: { value: 'redes' } })
    fireEvent.click(screen.getByLabelText('Buscar formación'))

    await waitFor(() => {
      expect(screen.getByLabelText('Título verificado con resolución oficial')).toBeInTheDocument()
      expect(screen.getAllByLabelText('Título verificado con resolución oficial').length).toBe(1)
    })
    vi.restoreAllMocks()
  })

  it('muestra skills derivadas como badges', async () => {
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
      expect(screen.getByText(/No se encontraron títulos formativos/)).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('agregar llama onAgregar y cambia botón a "Agregado"', async () => {
    const onAgregar = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockResults }),
    }))

    render(<FormacionSearch onAgregar={onAgregar} />)
    fireEvent.change(screen.getByLabelText('Buscar título formativo'), { target: { value: 'redes' } })
    fireEvent.click(screen.getByLabelText('Buscar formación'))

    await waitFor(() => screen.getByLabelText('Agregar Tecnicatura en Redes y Telecomunicaciones al perfil'))
    fireEvent.click(screen.getByLabelText('Agregar Tecnicatura en Redes y Telecomunicaciones al perfil'))

    expect(onAgregar).toHaveBeenCalledWith(mockResults[0])
    expect(screen.getByText('Agregado')).toBeInTheDocument()
    vi.restoreAllMocks()
  })

  it('botones tienen min touch target', async () => {
    render(<FormacionSearch />)
    expect(screen.getByLabelText('Buscar formación').className).toContain('min-h-[44px]')
  })
})
