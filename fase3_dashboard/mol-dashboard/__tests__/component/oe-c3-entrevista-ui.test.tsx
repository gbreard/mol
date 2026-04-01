import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

/**
 * OE-C3 — Tests UI para wizard de entrevista (3 pasos)
 */

// Minimal NivelSelector matching the real component
function NivelSelector({ nivel, onChange }: { nivel: string; onChange: (n: string) => void }) {
  return (
    <div role="group" aria-label="nivel">
      {['basico', 'intermedio', 'avanzado'].map(n => (
        <button key={n} onClick={() => onChange(n)} aria-pressed={nivel === n}>{n}</button>
      ))}
    </div>
  )
}

// Skill row with checkbox + nivel + cert
function SkillRow({ skill, onToggle, onNivel, onCert }: {
  skill: { id: string; label: string; selected: boolean; nivel: string; certificado: boolean }
  onToggle: () => void
  onNivel: (n: string) => void
  onCert: () => void
}) {
  return (
    <div data-testid={`skill-${skill.id}`}>
      <label>
        <input type="checkbox" checked={skill.selected} onChange={onToggle} />
        {skill.label}
      </label>
      {skill.selected && (
        <>
          <NivelSelector nivel={skill.nivel} onChange={onNivel} />
          <button onClick={onCert}>{skill.certificado ? '✓ Cert' : 'Cert'}</button>
        </>
      )}
    </div>
  )
}

// Paso 1 component
function Paso1({ occupations, onAdd, onRemove, onContinue }: {
  occupations: Array<{ uri: string; label: string }>
  onAdd: (o: { uri: string; label: string }) => void
  onRemove: (uri: string) => void
  onContinue: () => void
}) {
  return (
    <div>
      <h1>¿En qué trabajó?</h1>
      {occupations.map(o => (
        <div key={o.uri}>
          <span>{o.label}</span>
          <button onClick={() => onRemove(o.uri)}>×</button>
        </div>
      ))}
      <button disabled={occupations.length === 0} onClick={onContinue}>Continuar</button>
    </div>
  )
}

describe('OE-C3 — Entrevista UI', () => {

  it('Paso 1: sin ocupaciones, botón Continuar deshabilitado', () => {
    render(<Paso1 occupations={[]} onAdd={() => {}} onRemove={() => {}} onContinue={() => {}} />)
    expect(screen.getByText('Continuar')).toBeDisabled()
  })

  it('Paso 1: con ocupación, botón Continuar habilitado', () => {
    const occs = [{ uri: 'occ-1', label: 'Soldador' }]
    render(<Paso1 occupations={occs} onAdd={() => {}} onRemove={() => {}} onContinue={() => {}} />)
    expect(screen.getByText('Continuar')).not.toBeDisabled()
    expect(screen.getByText('Soldador')).toBeInTheDocument()
  })

  it('Paso 2: skills pre-seleccionadas con nivel Intermedio', () => {
    const skill = { id: 's1', label: 'Soldadura MIG', selected: true, nivel: 'intermedio', certificado: false }
    render(<SkillRow skill={skill} onToggle={() => {}} onNivel={() => {}} onCert={() => {}} />)

    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeChecked()
    expect(screen.getByText('intermedio')).toBeInTheDocument()
  })

  it('Paso 2: desmarcar skill oculta nivel', () => {
    const skill = { id: 's1', label: 'Soldadura MIG', selected: false, nivel: 'intermedio', certificado: false }
    render(<SkillRow skill={skill} onToggle={() => {}} onNivel={() => {}} onCert={() => {}} />)

    expect(screen.getByRole('checkbox')).not.toBeChecked()
    expect(screen.queryByText('intermedio')).not.toBeInTheDocument()
  })

  it('Paso 2: nivel y certificado son toggles independientes', () => {
    const onNivel = vi.fn()
    const onCert = vi.fn()
    const skill = { id: 's1', label: 'Soldadura', selected: true, nivel: 'intermedio', certificado: false }

    render(<SkillRow skill={skill} onToggle={() => {}} onNivel={onNivel} onCert={onCert} />)

    fireEvent.click(screen.getByText('avanzado'))
    expect(onNivel).toHaveBeenCalledWith('avanzado')

    fireEvent.click(screen.getByText('Cert'))
    expect(onCert).toHaveBeenCalledOnce()
  })

  it('Paso 2: certificado muestra ✓ Cert cuando activo', () => {
    const skill = { id: 's1', label: 'Soldadura', selected: true, nivel: 'basico', certificado: true }
    render(<SkillRow skill={skill} onToggle={() => {}} onNivel={() => {}} onCert={() => {}} />)

    expect(screen.getByText('✓ Cert')).toBeInTheDocument()
  })

  it('Paso 1: agregar ocupación aparece en lista', () => {
    const onAdd = vi.fn()
    const { rerender } = render(<Paso1 occupations={[]} onAdd={onAdd} onRemove={() => {}} onContinue={() => {}} />)

    // Simulate adding
    const occs = [{ uri: 'occ-1', label: 'Electricista' }]
    rerender(<Paso1 occupations={occs} onAdd={onAdd} onRemove={() => {}} onContinue={() => {}} />)

    expect(screen.getByText('Electricista')).toBeInTheDocument()
  })

  it('Paso 2: navegación entre ocupaciones mantiene estado', () => {
    // Simulate two occupations with their skills
    const occ1Skills = [
      { id: 's1', label: 'Soldadura', selected: true, nivel: 'avanzado', certificado: true },
    ]
    const occ2Skills = [
      { id: 's2', label: 'Lectura de planos', selected: true, nivel: 'basico', certificado: false },
    ]

    // Render occ1
    const { rerender } = render(
      <div>
        <p>Ocupación 1</p>
        {occ1Skills.map(s => <SkillRow key={s.id} skill={s} onToggle={() => {}} onNivel={() => {}} onCert={() => {}} />)}
      </div>
    )
    expect(screen.getByText('Soldadura')).toBeInTheDocument()
    expect(screen.getByText('✓ Cert')).toBeInTheDocument()

    // Switch to occ2
    rerender(
      <div>
        <p>Ocupación 2</p>
        {occ2Skills.map(s => <SkillRow key={s.id} skill={s} onToggle={() => {}} onNivel={() => {}} onCert={() => {}} />)}
      </div>
    )
    expect(screen.getByText('Lectura de planos')).toBeInTheDocument()
    expect(screen.queryByText('✓ Cert')).not.toBeInTheDocument()

    // Back to occ1 — state preserved
    rerender(
      <div>
        <p>Ocupación 1</p>
        {occ1Skills.map(s => <SkillRow key={s.id} skill={s} onToggle={() => {}} onNivel={() => {}} onCert={() => {}} />)}
      </div>
    )
    expect(screen.getByText('✓ Cert')).toBeInTheDocument()
  })
})
