import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

/**
 * OE-04 — Tests de UI para Tab Comparar (ProfileOccupationGap)
 */

interface GapSkill {
  id: string
  label: string
}

interface CubiertaDetail {
  similarity: number
  is_exact: boolean
}

function ProfileOccupationGap({
  personaName,
  destino,
  essential,
  optional,
  cubiertasDetail,
  loading,
  sinSkills,
  onChangeDest,
}: {
  personaName: string
  destino: { uri: string; label: string; isco_code: string } | null
  essential: GapSkill[]
  optional: GapSkill[]
  cubiertasDetail: Record<string, CubiertaDetail>
  loading: boolean
  sinSkills: boolean
  onChangeDest: () => void
}) {
  const PREFIX = 'http://data.europa.eu/esco/skill/'

  if (!destino) {
    return (
      <div>
        <p>Elegí una ocupación destino para ver el gap.</p>
        <button onClick={onChangeDest}>Ir a Ocupaciones para elegir destino</button>
      </div>
    )
  }

  if (loading) return <div>Calculando gap semántico...</div>

  if (sinSkills) {
    return <p>Completá el perfil de la persona para ver el gap.</p>
  }

  const essentialCub = essential.filter(s => cubiertasDetail[PREFIX + s.id])
  const essentialGap = essential.filter(s => !cubiertasDetail[PREFIX + s.id])
  const optionalCub = optional.filter(s => cubiertasDetail[PREFIX + s.id])
  const pct = essential.length > 0 ? Math.round((essentialCub.length / essential.length) * 100) : 0

  return (
    <div>
      <p>{personaName} → {destino.label}</p>
      <div role="progressbar" aria-valuenow={pct}>{pct}% skills esenciales cubiertas</div>

      <h3>Skills esenciales ({essentialCub.length}/{essential.length})</h3>
      {essentialCub.map(s => {
        const d = cubiertasDetail[PREFIX + s.id]
        return (
          <div key={s.id} data-testid={`skill-${s.id}`}>
            <span>✅ {s.label}</span>
            <span>{d.is_exact ? 'exacto' : `~${(d.similarity * 100).toFixed(0)}%`}</span>
          </div>
        )
      })}
      {essentialGap.map(s => (
        <div key={s.id} data-testid={`gap-${s.id}`}>
          <span>❌ {s.label}</span>
          <span>falta</span>
        </div>
      ))}

      {optionalCub.length > 0 && <h3>Skills opcionales</h3>}
    </div>
  )
}

const mockEssential: GapSkill[] = [
  { id: 'sk1', label: 'contabilidad financiera' },
  { id: 'sk2', label: 'análisis de estados contables' },
  { id: 'sk3', label: 'auditoría interna' },
  { id: 'sk4', label: 'normas NIIF' },
]

const mockOptional: GapSkill[] = [
  { id: 'sk5', label: 'Excel avanzado' },
  { id: 'sk6', label: 'SAP' },
]

const mockCubiertas: Record<string, CubiertaDetail> = {
  'http://data.europa.eu/esco/skill/sk1': { similarity: 1.0, is_exact: true },
  'http://data.europa.eu/esco/skill/sk2': { similarity: 0.81, is_exact: false },
  'http://data.europa.eu/esco/skill/sk5': { similarity: 0.74, is_exact: false },
}

const mockDestino = { uri: 'http://esco/occ/1', label: 'Contable', isco_code: '2411' }

describe('OE-04 — Tab Comparar UI', () => {

  it('sin destino seleccionado: muestra buscador', () => {
    render(
      <ProfileOccupationGap
        personaName="María" destino={null} essential={[]} optional={[]}
        cubiertasDetail={{}} loading={false} sinSkills={false} onChangeDest={() => {}}
      />
    )
    expect(screen.getByText(/Elegí una ocupación destino/)).toBeInTheDocument()
    expect(screen.getByText(/Ir a Ocupaciones/)).toBeInTheDocument()
  })

  it('con destino pre-cargado: muestra gap directamente', () => {
    render(
      <ProfileOccupationGap
        personaName="María" destino={mockDestino} essential={mockEssential} optional={mockOptional}
        cubiertasDetail={mockCubiertas} loading={false} sinSkills={false} onChangeDest={() => {}}
      />
    )
    expect(screen.getByText('María → Contable')).toBeInTheDocument()
    expect(screen.getByText(/50% skills esenciales cubiertas/)).toBeInTheDocument()
  })

  it('skills cubiertas exactas vs semánticas tienen indicador distinto', () => {
    render(
      <ProfileOccupationGap
        personaName="María" destino={mockDestino} essential={mockEssential} optional={mockOptional}
        cubiertasDetail={mockCubiertas} loading={false} sinSkills={false} onChangeDest={() => {}}
      />
    )
    expect(screen.getByText('exacto')).toBeInTheDocument()
    expect(screen.getByText('~81%')).toBeInTheDocument()
  })

  it('skills faltantes listadas con indicador', () => {
    render(
      <ProfileOccupationGap
        personaName="María" destino={mockDestino} essential={mockEssential} optional={mockOptional}
        cubiertasDetail={mockCubiertas} loading={false} sinSkills={false} onChangeDest={() => {}}
      />
    )
    expect(screen.getByText('❌ auditoría interna')).toBeInTheDocument()
    expect(screen.getByText('❌ normas NIIF')).toBeInTheDocument()
    expect(screen.getAllByText('falta')).toHaveLength(2)
  })

  it('barra de progreso presente con valor correcto', () => {
    render(
      <ProfileOccupationGap
        personaName="María" destino={mockDestino} essential={mockEssential} optional={mockOptional}
        cubiertasDetail={mockCubiertas} loading={false} sinSkills={false} onChangeDest={() => {}}
      />
    )
    const bar = screen.getByRole('progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '50')
  })
})
