import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import JobProfileForm from '@/components/JobProfileForm'

const mockSkillResults = [
  { uri: 'esco:1', label: 'Python', type: 'skill', source: 'esco' },
  { uri: 'esco:2', label: 'PostgreSQL', type: 'knowledge', source: 'esco' },
  { uri: 'arg:1', label: 'Facturación electrónica', type: 'skill', source: 'argentina_approved' },
]

// ─── S18: JobProfileForm ──────────────────────────────────────────────────────

describe('S18 — JobProfileForm', () => {
  it('renderiza input de título', () => {
    render(<JobProfileForm />)
    expect(screen.getByLabelText('Título del puesto')).toBeInTheDocument()
  })

  it('renderiza buscador de skills', () => {
    render(<JobProfileForm />)
    expect(screen.getByLabelText('Agregar skill requerida')).toBeInTheDocument()
  })

  it('botón guardar deshabilitado si título vacío', () => {
    render(<JobProfileForm />)
    const btn = screen.getByLabelText('Guardar perfil de puesto')
    expect(btn).toBeDisabled()
  })

  it('botón guardar habilitado si hay título', () => {
    render(<JobProfileForm initial={{ titulo: 'Programador', skills: [] }} />)
    expect(screen.getByLabelText('Guardar perfil de puesto')).not.toBeDisabled()
  })

  it('mostrar resultados al buscar (mock fetch)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockSkillResults }),
    }))

    render(<JobProfileForm />)
    fireEvent.change(screen.getByLabelText('Agregar skill requerida'), {
      target: { value: 'py' },
    })

    await waitFor(() => {
      expect(screen.getByText('Python')).toBeInTheDocument()
    })
    vi.restoreAllMocks()
  })

  it('agregar skill la agrega a la lista', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockSkillResults }),
    }))

    render(<JobProfileForm />)
    fireEvent.change(screen.getByLabelText('Agregar skill requerida'), {
      target: { value: 'py' },
    })

    await waitFor(() => screen.getByLabelText('Agregar skill: Python'))
    fireEvent.click(screen.getByLabelText('Agregar skill: Python'))

    expect(screen.getByText('Skills del puesto (1)')).toBeInTheDocument()
    expect(screen.getByLabelText('Quitar Python')).toBeInTheDocument()
    vi.restoreAllMocks()
  })

  it('badge ARG visible para skill argentina_approved', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockSkillResults }),
    }))

    render(<JobProfileForm />)
    fireEvent.change(screen.getByLabelText('Agregar skill requerida'), {
      target: { value: 'fa' },
    })

    await waitFor(() => screen.getByLabelText('Agregar skill: Facturación electrónica'))
    fireEvent.click(screen.getByLabelText('Agregar skill: Facturación electrónica'))

    const argBadges = screen.getAllByText('ARG')
    expect(argBadges.length).toBeGreaterThan(0)
    vi.restoreAllMocks()
  })

  it('toggle requerida/deseable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockSkillResults }),
    }))

    render(<JobProfileForm />)
    fireEvent.change(screen.getByLabelText('Agregar skill requerida'), {
      target: { value: 'py' },
    })
    await waitFor(() => screen.getByLabelText('Agregar skill: Python'))
    fireEvent.click(screen.getByLabelText('Agregar skill: Python'))

    // Por defecto es "Requerida"
    expect(screen.getByLabelText('Marcar Python como deseable')).toBeInTheDocument()

    // Toggle a deseable
    fireEvent.click(screen.getByLabelText('Marcar Python como deseable'))
    expect(screen.getByLabelText('Marcar Python como requerida')).toBeInTheDocument()
    vi.restoreAllMocks()
  })

  it('quitar skill la elimina de la lista', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: mockSkillResults }),
    }))

    render(<JobProfileForm />)
    fireEvent.change(screen.getByLabelText('Agregar skill requerida'), {
      target: { value: 'py' },
    })
    await waitFor(() => screen.getByLabelText('Agregar skill: Python'))
    fireEvent.click(screen.getByLabelText('Agregar skill: Python'))
    fireEvent.click(screen.getByLabelText('Quitar Python'))

    expect(screen.queryByText('Skills del puesto')).not.toBeInTheDocument()
    vi.restoreAllMocks()
  })

  it('guardar llama onSave con título y skills', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<JobProfileForm initial={{ titulo: 'Dev', skills: [] }} onSave={onSave} />)
    fireEvent.click(screen.getByLabelText('Guardar perfil de puesto'))
    await waitFor(() => expect(onSave).toHaveBeenCalledWith({ titulo: 'Dev', skills: [], id: undefined }))
  })

  it('sin id no muestra botón duplicar', () => {
    render(<JobProfileForm initial={{ titulo: 'Dev', skills: [] }} />)
    expect(screen.queryByLabelText('Duplicar perfil de puesto')).not.toBeInTheDocument()
  })

  it('con id muestra botón duplicar y llama onDuplicate', () => {
    const onDuplicate = vi.fn()
    render(
      <JobProfileForm
        initial={{ id: 'abc', titulo: 'Dev', skills: [] }}
        onDuplicate={onDuplicate}
      />
    )
    const btn = screen.getByLabelText('Duplicar perfil de puesto')
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    expect(onDuplicate).toHaveBeenCalledWith({ titulo: 'Dev (copia)', skills: [] })
  })

  it('botones tienen min touch target', () => {
    render(<JobProfileForm initial={{ id: 'abc', titulo: 'Dev', skills: [] }} />)
    expect(screen.getByLabelText('Guardar perfil de puesto').className).toContain('min-h-[44px]')
    expect(screen.getByLabelText('Duplicar perfil de puesto').className).toContain('min-h-[44px]')
  })
})
