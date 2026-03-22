import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import DniSearch from '@/components/DniSearch'

describe('DniSearch', () => {
  it('renderiza input DNI y botón buscar', () => {
    render(<DniSearch />)
    expect(screen.getByLabelText('DNI del trabajador/a')).toBeInTheDocument()
    expect(screen.getByLabelText('Buscar perfil por DNI')).toBeInTheDocument()
  })

  it('botón buscar deshabilitado con DNI vacío', () => {
    render(<DniSearch />)
    expect(screen.getByLabelText('Buscar perfil por DNI')).toBeDisabled()
  })

  it('botón buscar habilitado con DNI válido (7+ dígitos)', () => {
    render(<DniSearch />)
    fireEvent.change(screen.getByLabelText('DNI del trabajador/a'), {
      target: { value: '30123456' },
    })
    expect(screen.getByLabelText('Buscar perfil por DNI')).not.toBeDisabled()
  })

  it('botón buscar deshabilitado con DNI corto (< 7 dígitos)', () => {
    render(<DniSearch />)
    fireEvent.change(screen.getByLabelText('DNI del trabajador/a'), {
      target: { value: '123456' },
    })
    expect(screen.getByLabelText('Buscar perfil por DNI')).toBeDisabled()
  })

  it('muestra perfil encontrado con datos correctos', async () => {
    const mockProfile = {
      id: 'uuid-1',
      nombre: 'Juan Pérez',
      dni: '30123456',
      creado_at: '2026-03-15T00:00:00Z',
      skills_count: 12,
      ocupaciones_count: 3,
      reportes_count: 1,
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockProfile,
    }))

    render(<DniSearch />)
    fireEvent.change(screen.getByLabelText('DNI del trabajador/a'), {
      target: { value: '30123456' },
    })
    fireEvent.click(screen.getByLabelText('Buscar perfil por DNI'))

    await waitFor(() => {
      expect(screen.getByText('Perfil encontrado')).toBeInTheDocument()
      expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
      expect(screen.getByText('30.123.456')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('muestra "no encontrado" cuando API retorna 404', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({}),
    }))

    render(<DniSearch />)
    fireEvent.change(screen.getByLabelText('DNI del trabajador/a'), {
      target: { value: '30999999' },
    })
    fireEvent.click(screen.getByLabelText('Buscar perfil por DNI'))

    await waitFor(() => {
      expect(screen.getByText(/No se encontró perfil/)).toBeInTheDocument()
      expect(screen.getByLabelText('Crear nuevo perfil')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('botón crear nuevo llama onCrearNuevo', async () => {
    const onCrearNuevo = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 404, json: async () => ({})
    }))

    render(<DniSearch onCrearNuevo={onCrearNuevo} />)
    fireEvent.change(screen.getByLabelText('DNI del trabajador/a'), { target: { value: '30999999' } })
    fireEvent.click(screen.getByLabelText('Buscar perfil por DNI'))

    await waitFor(() => screen.getByLabelText('Crear nuevo perfil'))
    fireEvent.click(screen.getByLabelText('Crear nuevo perfil'))
    expect(onCrearNuevo).toHaveBeenCalled()

    vi.unstubAllGlobals()
  })

  it('vincular llama onVincular con el perfil', async () => {
    const mockProfile = {
      id: 'uuid-1', nombre: 'Ana López', dni: '28000001',
      creado_at: '2026-01-01T00:00:00Z', skills_count: 5, ocupaciones_count: 2, reportes_count: 0,
    }
    const onVincular = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => mockProfile
    }))

    render(<DniSearch onVincular={onVincular} organizacionNombre="OE Test" />)
    fireEvent.change(screen.getByLabelText('DNI del trabajador/a'), { target: { value: '28000001' } })
    fireEvent.click(screen.getByLabelText('Buscar perfil por DNI'))

    await waitFor(() => screen.getByLabelText('Vincular a OE Test'))
    fireEvent.click(screen.getByLabelText('Vincular a OE Test'))

    await waitFor(() => {
      expect(onVincular).toHaveBeenCalledWith(mockProfile)
      expect(screen.getByText(/Perfil vinculado a OE Test/)).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('botón buscar tiene min touch target', () => {
    render(<DniSearch />)
    const btn = screen.getByLabelText('Buscar perfil por DNI')
    expect(btn.className).toContain('min-h-[44px]')
  })

  it('Enter en input dispara búsqueda', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false, status: 404, json: async () => ({})
    })
    vi.stubGlobal('fetch', mockFetch)

    render(<DniSearch />)
    const input = screen.getByLabelText('DNI del trabajador/a')
    fireEvent.change(input, { target: { value: '30123456' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    vi.unstubAllGlobals()
  })
})
