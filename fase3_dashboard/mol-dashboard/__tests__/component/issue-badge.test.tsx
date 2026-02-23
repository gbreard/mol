import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { IssueBadge } from '../../components/issues/IssueBadge'

describe('IssueBadge', () => {
  describe('estado variant', () => {
    it.each([
      ['pendiente', 'Pendiente'],
      ['en_progreso', 'En progreso'],
      ['resuelto', 'Resuelto'],
      ['descartado', 'Descartado'],
    ])('renders estado "%s" as "%s"', (value, label) => {
      render(<IssueBadge variant="estado" value={value} />)
      expect(screen.getByText(label)).toBeInTheDocument()
    })
  })

  describe('prioridad variant', () => {
    it.each([
      ['baja', 'Baja'],
      ['media', 'Media'],
      ['alta', 'Alta'],
      ['critica', 'Critica'],
    ])('renders prioridad "%s" as "%s"', (value, label) => {
      render(<IssueBadge variant="prioridad" value={value} />)
      expect(screen.getByText(label)).toBeInTheDocument()
    })
  })

  describe('tipo variant', () => {
    it.each([
      ['error_isco', 'Error ISCO'],
      ['error_nlp', 'Error NLP'],
      ['error_skill', 'Error Skill'],
      ['sugerencia', 'Sugerencia'],
      ['bug', 'Bug'],
      ['otro', 'Otro'],
    ])('renders tipo "%s" as "%s"', (value, label) => {
      render(<IssueBadge variant="tipo" value={value} />)
      expect(screen.getByText(label)).toBeInTheDocument()
    })
  })

  it('falls back to raw value for unknown types', () => {
    render(<IssueBadge variant="estado" value="unknown_state" />)
    expect(screen.getByText('unknown_state')).toBeInTheDocument()
  })

  it('applies sm size class', () => {
    const { container } = render(
      <IssueBadge variant="estado" value="pendiente" size="sm" />
    )
    const badge = container.querySelector('.text-\\[10px\\]')
    expect(badge).toBeInTheDocument()
  })
})
