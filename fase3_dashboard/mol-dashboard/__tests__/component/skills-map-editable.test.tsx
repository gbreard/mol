import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import SkillsMapEditable, { type ReportSkillItem } from '@/components/SkillsMapEditable'

const required: ReportSkillItem[] = [
  { uri: 'esco:001', label: 'JavaScript', type: 'skill', source: 'esco' },
  { uri: 'esco:002', label: 'Docker', type: 'skill', source: 'esco' },
  { uri: 'esco:003', label: 'TypeScript', type: 'skill', source: 'argentina_approved' },
]

const covered: ReportSkillItem[] = [
  { uri: 'esco:001', label: 'JavaScript', type: 'skill', source: 'esco' },
]

describe('SkillsMapEditable', () => {
  it('renderiza la tabla de competencias', () => {
    render(<SkillsMapEditable required={required} covered={covered} onChange={vi.fn()} />)
    expect(screen.getByText('JavaScript')).toBeInTheDocument()
    expect(screen.getByText('Docker')).toBeInTheDocument()
  })

  it('muestra badges de estado detectada/faltante', () => {
    render(<SkillsMapEditable required={required} covered={covered} onChange={vi.fn()} />)
    expect(screen.getByText('Detectada')).toBeInTheDocument()
    expect(screen.getAllByText('Faltante').length).toBeGreaterThan(0)
  })

  it('badge origen emergente visible para argentina_approved', () => {
    render(<SkillsMapEditable required={required} covered={covered} onChange={vi.fn()} />)
    expect(screen.getByText('emergente')).toBeInTheDocument()
  })

  it('boton quitar no visible sin modo edicion', () => {
    render(<SkillsMapEditable required={required} covered={covered} onChange={vi.fn()} />)
    expect(screen.queryByLabelText('Quitar JavaScript')).not.toBeInTheDocument()
  })

  it('quitar skill llama onChange con lista actualizada', () => {
    const onChange = vi.fn()
    render(<SkillsMapEditable required={required} covered={covered} onChange={onChange} />)
    fireEvent.click(screen.getByText('Editar'))
    fireEvent.click(screen.getByLabelText('Quitar Docker'))
    expect(onChange).toHaveBeenCalled()
    const [newRequired] = onChange.mock.calls[0]
    expect(newRequired.find((s: ReportSkillItem) => s.uri === 'esco:002')).toBeUndefined()
  })

  it('agregar skill llama onChange con nueva skill', () => {
    const onChange = vi.fn()
    render(<SkillsMapEditable required={required} covered={covered} onChange={onChange} />)
    fireEvent.click(screen.getByText('Editar'))
    fireEvent.change(screen.getByLabelText('Agregar competencia'), {
      target: { value: 'React' },
    })
    fireEvent.click(screen.getByText('+ Agregar'))
    expect(onChange).toHaveBeenCalled()
    const [newRequired] = onChange.mock.calls[0]
    expect(newRequired.some((s: ReportSkillItem) => s.label === 'React')).toBe(true)
  })
})
