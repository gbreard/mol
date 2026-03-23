/**
 * Component tests for P-33 (Perfil Trabajador) and P-34 (Ofertas Coincidentes)
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SkillCapturePanel, SkillsPanel, type CapturedSkill } from '../../components/oficina-empleo/SkillCapturePanel'

// Mock next/navigation for ofertas page
vi.mock('next/navigation', async () => {
  const actual = await vi.importActual('next/navigation')
  return {
    ...actual,
    useSearchParams: () => new URLSearchParams('isco=2512&skills=Python,SQL'),
    useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
    usePathname: () => '/oficina-empleo/ofertas',
  }
})

describe('SkillCapturePanel', () => {
  const defaultProps = {
    skills: [] as CapturedSkill[],
    onAddSkills: vi.fn(),
    onRemoveSkill: vi.fn(),
    onToggleConfirm: vi.fn(),
  }

  it('renders 4 vias de captura', () => {
    render(<SkillCapturePanel {...defaultProps} />)
    expect(screen.getByText('Por ocupacion')).toBeInTheDocument()
    expect(screen.getByText('Por habilidad')).toBeInTheDocument()
    expect(screen.getByText('Texto libre')).toBeInTheDocument()
    expect(screen.getByText('Por formacion')).toBeInTheDocument()
  })

  it('shows search input', () => {
    render(<SkillCapturePanel {...defaultProps} />)
    expect(screen.getByPlaceholderText(/albanil, electricista/)).toBeInTheDocument()
  })

  it('switches via on click', () => {
    render(<SkillCapturePanel {...defaultProps} />)
    fireEvent.click(screen.getByText('Texto libre'))
    expect(screen.getByPlaceholderText(/Trabaje 5 anos/)).toBeInTheDocument()
  })

  it('shows textarea for texto libre via', () => {
    render(<SkillCapturePanel {...defaultProps} />)
    fireEvent.click(screen.getByText('Texto libre'))
    const textarea = screen.getByPlaceholderText(/Trabaje 5 anos/)
    expect(textarea.tagName).toBe('TEXTAREA')
  })

  it('has search button', () => {
    render(<SkillCapturePanel {...defaultProps} />)
    expect(screen.getByText('Buscar')).toBeInTheDocument()
  })

  it('disables search when empty', () => {
    render(<SkillCapturePanel {...defaultProps} />)
    const btn = screen.getByText('Buscar').closest('button')
    expect(btn).toBeDisabled()
  })
})

describe('SkillsPanel', () => {
  const mockSkills: CapturedSkill[] = [
    { uri: 's1', label: 'Soldadura', type: 'skill', description: 'Tecnicas de soldeo', source: 'ocupacion', confirmed: true },
    { uri: 's2', label: 'Electricidad', type: 'knowledge', description: 'Principios electricos', source: 'busqueda', confirmed: false },
  ]

  it('renders skill count', () => {
    render(<SkillsPanel skills={mockSkills} onRemoveSkill={vi.fn()} onToggleConfirm={vi.fn()} />)
    expect(screen.getByText(/Competencias identificadas \(2\)/)).toBeInTheDocument()
  })

  it('renders skill labels', () => {
    render(<SkillsPanel skills={mockSkills} onRemoveSkill={vi.fn()} onToggleConfirm={vi.fn()} />)
    expect(screen.getByText('Soldadura')).toBeInTheDocument()
    expect(screen.getByText('Electricidad')).toBeInTheDocument()
  })

  it('renders descriptions', () => {
    render(<SkillsPanel skills={mockSkills} onRemoveSkill={vi.fn()} onToggleConfirm={vi.fn()} />)
    expect(screen.getByText('Tecnicas de soldeo')).toBeInTheDocument()
  })

  it('renders source labels', () => {
    render(<SkillsPanel skills={mockSkills} onRemoveSkill={vi.fn()} onToggleConfirm={vi.fn()} />)
    expect(screen.getByText('via ocupacion')).toBeInTheDocument()
    expect(screen.getByText('via busqueda')).toBeInTheDocument()
  })

  it('shows unconfirmed count', () => {
    render(<SkillsPanel skills={mockSkills} onRemoveSkill={vi.fn()} onToggleConfirm={vi.fn()} />)
    expect(screen.getByText(/1 por confirmar/)).toBeInTheDocument()
  })

  it('calls onRemoveSkill when X clicked', () => {
    const onRemove = vi.fn()
    render(<SkillsPanel skills={mockSkills} onRemoveSkill={onRemove} onToggleConfirm={vi.fn()} />)
    // Find X buttons (there are 2, one per skill)
    const removeButtons = screen.getAllByRole('button').filter(b => b.querySelector('.lucide-x'))
    expect(removeButtons.length).toBe(2)
  })

  it('shows empty state when no skills', () => {
    render(<SkillsPanel skills={[]} onRemoveSkill={vi.fn()} onToggleConfirm={vi.fn()} />)
    expect(screen.getByText(/Usa las vias de captura/)).toBeInTheDocument()
  })

  it('shows type badges', () => {
    render(<SkillsPanel skills={mockSkills} onRemoveSkill={vi.fn()} onToggleConfirm={vi.fn()} />)
    expect(screen.getByText('skill')).toBeInTheDocument()
    expect(screen.getByText('knowledge')).toBeInTheDocument()
  })
})
