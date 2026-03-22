import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import AnonProfileCard, { type AnonProfile } from '@/components/AnonProfileCard'
import PoolSearch from '@/components/PoolSearch'

const mockProfile: AnonProfile = {
  id: 'uuid-4523',
  perfil_numero: 4523,
  jurisdiccion: 'CABA',
  match_score: 78,
  skills: ['Python', 'SQL', 'Git', 'Testing', 'Docker'],
  ocupaciones_previas: 3,
}

describe('AnonProfileCard', () => {
  it('no muestra nombre ni DNI del trabajador', () => {
    render(<AnonProfileCard profile={mockProfile} />)
    expect(screen.queryByText(/Juan/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/DNI/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/30\.123/)).not.toBeInTheDocument()
  })

  it('muestra número de perfil anonimizado', () => {
    render(<AnonProfileCard profile={mockProfile} />)
    expect(screen.getByText('Perfil #4523')).toBeInTheDocument()
  })

  it('muestra jurisdicción', () => {
    render(<AnonProfileCard profile={mockProfile} />)
    expect(screen.getByText('CABA')).toBeInTheDocument()
  })

  it('muestra match score', () => {
    render(<AnonProfileCard profile={mockProfile} />)
    expect(screen.getByText('Match: 78%')).toBeInTheDocument()
  })

  it('muestra todas las skills como badges', () => {
    render(<AnonProfileCard profile={mockProfile} />)
    expect(screen.getByText('Python')).toBeInTheDocument()
    expect(screen.getByText('SQL')).toBeInTheDocument()
    expect(screen.getByText('Docker')).toBeInTheDocument()
  })

  it('muestra trayectoria con cantidad de ocupaciones', () => {
    const { container } = render(<AnonProfileCard profile={mockProfile} />)
    expect(container.textContent).toContain('Trayectoria')
    expect(container.textContent).toMatch(/3 ocupacion/)
  })

  it('botón solicitar contacto tiene min touch target', () => {
    render(<AnonProfileCard profile={mockProfile} />)
    const btn = screen.getByLabelText('Solicitar contacto con Perfil #4523')
    expect(btn.className).toContain('min-h-[44px]')
  })

  it('solicitar contacto llama onSolicitarContacto con id', async () => {
    const onSolicitar = vi.fn().mockResolvedValue(undefined)
    render(<AnonProfileCard profile={mockProfile} onSolicitarContacto={onSolicitar} />)
    fireEvent.click(screen.getByLabelText('Solicitar contacto con Perfil #4523'))
    await waitFor(() => {
      expect(onSolicitar).toHaveBeenCalledWith('uuid-4523')
      expect(screen.getByText(/Solicitud enviada/)).toBeInTheDocument()
    })
  })

  it('score verde para match >= 75%', () => {
    render(<AnonProfileCard profile={mockProfile} />)
    const badge = screen.getByText('Match: 78%')
    expect(badge.className).toContain('green')
  })

  it('score amarillo para match entre 50-74%', () => {
    render(<AnonProfileCard profile={{ ...mockProfile, match_score: 60 }} />)
    const badge = screen.getByText('Match: 60%')
    expect(badge.className).toContain('yellow')
  })
})

describe('PoolSearch', () => {
  it('renderiza inputs de búsqueda', () => {
    render(<PoolSearch />)
    expect(screen.getByLabelText('Ocupación (ISCO)')).toBeInTheDocument()
    expect(screen.getByLabelText('Jurisdicción (opcional)')).toBeInTheDocument()
    expect(screen.getByLabelText('Buscar en pool')).toBeInTheDocument()
  })

  it('botón buscar deshabilitado sin ISCO', () => {
    render(<PoolSearch />)
    expect(screen.getByLabelText('Buscar en pool')).toBeDisabled()
  })

  it('muestra perfiles encontrados', async () => {
    const mockProfiles: AnonProfile[] = [
      { id: 'p1', perfil_numero: 4523, jurisdiccion: 'CABA', match_score: 78,
        skills: ['Python', 'SQL'], ocupaciones_previas: 3 },
      { id: 'p2', perfil_numero: 2891, jurisdiccion: 'Buenos Aires', match_score: 72,
        skills: ['React', 'TypeScript'], ocupaciones_previas: 2 },
    ]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ profiles: mockProfiles })
    }))

    render(<PoolSearch />)
    fireEvent.change(screen.getByLabelText('Ocupación (ISCO)'), { target: { value: '2512' } })
    fireEvent.click(screen.getByLabelText('Buscar en pool'))

    await waitFor(() => {
      expect(screen.getByText(/perfiles compatibles encontrados/)).toBeInTheDocument()
      expect(screen.getByText('Perfil #4523')).toBeInTheDocument()
      expect(screen.getByText('Perfil #2891')).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('muestra nota de anonimización', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ profiles: [
        { id: 'p1', perfil_numero: 1, jurisdiccion: 'CABA', match_score: 80, skills: [], ocupaciones_previas: 1 }
      ]})
    }))

    render(<PoolSearch />)
    fireEvent.change(screen.getByLabelText('Ocupación (ISCO)'), { target: { value: '2512' } })
    fireEvent.click(screen.getByLabelText('Buscar en pool'))

    await waitFor(() => {
      expect(screen.getByText(/anonimizados/)).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })

  it('muestra estado vacío cuando no hay perfiles', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ profiles: [] })
    }))

    render(<PoolSearch />)
    fireEvent.change(screen.getByLabelText('Ocupación (ISCO)'), { target: { value: '9999' } })
    fireEvent.click(screen.getByLabelText('Buscar en pool'))

    await waitFor(() => {
      expect(screen.getByText(/No hay perfiles disponibles/)).toBeInTheDocument()
    })

    vi.unstubAllGlobals()
  })
})
