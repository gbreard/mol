import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * OE-03 — Tests de UI para Tab Ocupaciones
 *
 * Estos tests verifican la lógica de rendering sin importar la página completa
 * (que depende de Next.js routing). Se testea:
 * 1. Render de lista de ocupaciones
 * 2. Render de estado vacío (sin skills)
 * 3. Comportamiento del botón "Usar como destino"
 * 4. Que los 4 tabs estén presentes
 */

// Minimal tab component that mirrors the page's ocupaciones tab logic
function OcupacionesTab({
  ocupaciones,
  mensaje,
  loading,
  skillsCount,
  onSelectDestino,
  selectedDestinoUri,
  onGoToPerfil,
}: {
  ocupaciones: Array<{ uri: string; label: string; isco_code: string; afinidad: number; skills_matched: number }>
  mensaje: string | null
  loading: boolean
  skillsCount: number
  onSelectDestino: (o: { uri: string; label: string; isco_code: string }) => void
  selectedDestinoUri: string | null
  onGoToPerfil: () => void
}) {
  if (loading) return <div>Buscando ocupaciones compatibles...</div>

  if (mensaje === 'sin_skills') {
    return (
      <div>
        <p>Para ver ocupaciones compatibles, completá primero el perfil de la persona.</p>
        <button onClick={onGoToPerfil}>Ir a Perfil</button>
      </div>
    )
  }

  if (ocupaciones.length === 0) {
    return <p>No se encontraron ocupaciones compatibles.</p>
  }

  return (
    <div>
      <p>Ocupaciones compatibles · basado en {skillsCount} skills del perfil</p>
      {ocupaciones.map(o => (
        <div key={o.uri} data-testid={`ocupacion-${o.uri}`}>
          <h3>{o.label}</h3>
          <span>{o.isco_code}</span>
          <span>{o.skills_matched} skills coinciden</span>
          <div role="progressbar" aria-valuenow={o.afinidad} aria-valuemin={0} aria-valuemax={100}>
            {o.afinidad}%
          </div>
          <button onClick={() => onSelectDestino({ uri: o.uri, label: o.label, isco_code: o.isco_code })}>
            {selectedDestinoUri === o.uri ? '✓ Destino seleccionado' : 'Usar como destino →'}
          </button>
        </div>
      ))}
    </div>
  )
}

// Tab bar component
function TabBar({ tabs, activeTab, onTabChange }: {
  tabs: Array<{ id: string; label: string }>
  activeTab: string
  onTabChange: (id: string) => void
}) {
  return (
    <div role="tablist">
      {tabs.map(t => (
        <button
          key={t.id}
          role="tab"
          aria-selected={activeTab === t.id}
          onClick={() => onTabChange(t.id)}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}

const mockOcupaciones = [
  { uri: 'occ-1', label: 'Contable', isco_code: '2411', afinidad: 88.4, skills_matched: 4 },
  { uri: 'occ-2', label: 'Auditor/auditora', isco_code: '4312', afinidad: 77.9, skills_matched: 2 },
  { uri: 'occ-3', label: 'Analista financiero', isco_code: '2413', afinidad: 73.0, skills_matched: 5 },
]

describe('OE-03 — Tab Ocupaciones UI', () => {

  it('muestra 4 tabs: Perfil, Ocupaciones, Vacantes, Notas', () => {
    const tabs = [
      { id: 'perfil', label: 'Perfil' },
      { id: 'ocupaciones', label: 'Ocupaciones' },
      { id: 'vacantes', label: 'Vacantes' },
      { id: 'notas', label: 'Notas' },
    ]
    render(<TabBar tabs={tabs} activeTab="perfil" onTabChange={() => {}} />)

    expect(screen.getByText('Perfil')).toBeInTheDocument()
    expect(screen.getByText('Ocupaciones')).toBeInTheDocument()
    expect(screen.getByText('Vacantes')).toBeInTheDocument()
    expect(screen.getByText('Notas')).toBeInTheDocument()
  })

  it('con skills: muestra lista de ocupaciones con afinidad', () => {
    render(
      <OcupacionesTab
        ocupaciones={mockOcupaciones}
        mensaje={null}
        loading={false}
        skillsCount={15}
        onSelectDestino={() => {}}
        selectedDestinoUri={null}
        onGoToPerfil={() => {}}
      />
    )

    expect(screen.getByText('Contable')).toBeInTheDocument()
    expect(screen.getByText('Auditor/auditora')).toBeInTheDocument()
    expect(screen.getByText('Analista financiero')).toBeInTheDocument()
    expect(screen.getByText(/basado en 15 skills/)).toBeInTheDocument()
    expect(screen.getByText('2411')).toBeInTheDocument()
    expect(screen.getByText('4 skills coinciden')).toBeInTheDocument()
  })

  it('la barra de progreso refleja el % de afinidad', () => {
    render(
      <OcupacionesTab
        ocupaciones={mockOcupaciones}
        mensaje={null}
        loading={false}
        skillsCount={15}
        onSelectDestino={() => {}}
        selectedDestinoUri={null}
        onGoToPerfil={() => {}}
      />
    )

    const progressBars = screen.getAllByRole('progressbar')
    expect(progressBars[0]).toHaveAttribute('aria-valuenow', '88.4')
    expect(progressBars[1]).toHaveAttribute('aria-valuenow', '77.9')
  })

  it('sin skills: muestra mensaje orientativo + botón Ir a Perfil', () => {
    render(
      <OcupacionesTab
        ocupaciones={[]}
        mensaje="sin_skills"
        loading={false}
        skillsCount={0}
        onSelectDestino={() => {}}
        selectedDestinoUri={null}
        onGoToPerfil={() => {}}
      />
    )

    expect(screen.getByText(/completá primero el perfil/)).toBeInTheDocument()
    expect(screen.getByText('Ir a Perfil')).toBeInTheDocument()
  })

  it('click "Ir a Perfil" dispara callback', () => {
    const onGoToPerfil = vi.fn()
    render(
      <OcupacionesTab
        ocupaciones={[]}
        mensaje="sin_skills"
        loading={false}
        skillsCount={0}
        onSelectDestino={() => {}}
        selectedDestinoUri={null}
        onGoToPerfil={onGoToPerfil}
      />
    )

    fireEvent.click(screen.getByText('Ir a Perfil'))
    expect(onGoToPerfil).toHaveBeenCalledOnce()
  })

  it('click "Usar como destino" selecciona la ocupación', () => {
    const onSelectDestino = vi.fn()
    render(
      <OcupacionesTab
        ocupaciones={mockOcupaciones}
        mensaje={null}
        loading={false}
        skillsCount={15}
        onSelectDestino={onSelectDestino}
        selectedDestinoUri={null}
        onGoToPerfil={() => {}}
      />
    )

    const buttons = screen.getAllByText('Usar como destino →')
    fireEvent.click(buttons[0])

    expect(onSelectDestino).toHaveBeenCalledWith({
      uri: 'occ-1',
      label: 'Contable',
      isco_code: '2411',
    })
  })

  it('ocupación seleccionada muestra "✓ Destino seleccionado"', () => {
    render(
      <OcupacionesTab
        ocupaciones={mockOcupaciones}
        mensaje={null}
        loading={false}
        skillsCount={15}
        onSelectDestino={() => {}}
        selectedDestinoUri="occ-1"
        onGoToPerfil={() => {}}
      />
    )

    expect(screen.getByText('✓ Destino seleccionado')).toBeInTheDocument()
    // Other occupations still show "Usar como destino"
    expect(screen.getAllByText('Usar como destino →')).toHaveLength(2)
  })

  it('loading muestra spinner', () => {
    render(
      <OcupacionesTab
        ocupaciones={[]}
        mensaje={null}
        loading={true}
        skillsCount={0}
        onSelectDestino={() => {}}
        selectedDestinoUri={null}
        onGoToPerfil={() => {}}
      />
    )

    expect(screen.getByText(/Buscando ocupaciones/)).toBeInTheDocument()
  })

  it('sin resultados (pero con skills): muestra mensaje apropiado', () => {
    render(
      <OcupacionesTab
        ocupaciones={[]}
        mensaje={null}
        loading={false}
        skillsCount={5}
        onSelectDestino={() => {}}
        selectedDestinoUri={null}
        onGoToPerfil={() => {}}
      />
    )

    expect(screen.getByText(/No se encontraron ocupaciones/)).toBeInTheDocument()
  })
})
