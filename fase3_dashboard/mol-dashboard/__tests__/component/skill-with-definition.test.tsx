import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import SkillWithDefinition, { type SkillItem } from '@/components/SkillWithDefinition'

const mockSkill: SkillItem = {
  uri: 'http://data.europa.eu/esco/skill/001',
  label: 'soldadura MIG',
  type: 'skill',
  description: 'Capacidad para realizar soldadura por arco metálico con gas inerte.',
  source: 'esco',
  frequency: 12,
  confidence: 'confirmed',
  via: 'busqueda',
}

describe('SkillWithDefinition', () => {
  it('muestra label y definicion', () => {
    render(<SkillWithDefinition skill={mockSkill} onConfidenceChange={vi.fn()} onRemove={vi.fn()} />)
    expect(screen.getByText('soldadura MIG')).toBeInTheDocument()
    expect(screen.getByText(/soldadura por arco/)).toBeInTheDocument()
  })

  it('muestra badge de tipo y origen', () => {
    render(<SkillWithDefinition skill={mockSkill} onConfidenceChange={vi.fn()} onRemove={vi.fn()} />)
    expect(screen.getByText('competencia')).toBeInTheDocument()
    expect(screen.getByText('ESCO')).toBeInTheDocument()
  })

  it('muestra badge de via', () => {
    render(<SkillWithDefinition skill={mockSkill} onConfidenceChange={vi.fn()} onRemove={vi.fn()} />)
    expect(screen.getByText('vía búsqueda')).toBeInTheDocument()
  })

  it('checkbox cambia a unsure', () => {
    const onConfidenceChange = vi.fn()
    render(<SkillWithDefinition skill={mockSkill} onConfidenceChange={onConfidenceChange} onRemove={vi.fn()} />)
    fireEvent.click(screen.getByLabelText('No estoy seguro'))
    expect(onConfidenceChange).toHaveBeenCalledWith(mockSkill.uri, 'unsure')
  })

  it('checkbox cambia a discarded', () => {
    const onConfidenceChange = vi.fn()
    render(<SkillWithDefinition skill={mockSkill} onConfidenceChange={onConfidenceChange} onRemove={vi.fn()} />)
    fireEvent.click(screen.getByLabelText('Descartar'))
    expect(onConfidenceChange).toHaveBeenCalledWith(mockSkill.uri, 'discarded')
  })

  it('click quitar dispara onRemove', () => {
    const onRemove = vi.fn()
    render(<SkillWithDefinition skill={mockSkill} onConfidenceChange={vi.fn()} onRemove={onRemove} />)
    fireEvent.click(screen.getByLabelText('Quitar skill'))
    expect(onRemove).toHaveBeenCalledWith(mockSkill.uri)
  })

  it('badge emergente para source argentina_approved', () => {
    const emergente: SkillItem = { ...mockSkill, source: 'argentina_approved' }
    render(<SkillWithDefinition skill={emergente} onConfidenceChange={vi.fn()} onRemove={vi.fn()} />)
    expect(screen.getByText('emergente')).toBeInTheDocument()
  })

  it('descripcion larga muestra boton ver mas', () => {
    const longDesc: SkillItem = {
      ...mockSkill,
      description: 'A'.repeat(200),
    }
    render(<SkillWithDefinition skill={longDesc} onConfidenceChange={vi.fn()} onRemove={vi.fn()} />)
    expect(screen.getByText('ver más')).toBeInTheDocument()
  })
})
