/**
 * Component tests for Fábrica pipeline components (F2.1-F2.3)
 * Tests: PipelineNode, PipelineGate, MejoraContinuaNode rendering and interactions
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PipelineNode, PipelineArrow } from '../../components/fabrica/PipelineNode'
import { PipelineGate } from '../../components/fabrica/PipelineGate'
import { MejoraContinuaNode, MejoraArrow } from '../../components/fabrica/MejoraContinuaNode'
import { Database, Play, RefreshCw, Settings, AlertCircle, FileText, Zap } from 'lucide-react'

describe('PipelineNode', () => {
  const defaultProps = {
    id: 'nlp',
    label: 'NLP',
    subtitle: 'v11.4',
    icon: Database,
    status: 'ok' as const,
    metric: '16K',
    metricLabel: 'procesadas',
    actions: [],
  }

  it('renders label and metric', () => {
    render(<PipelineNode {...defaultProps} />)
    expect(screen.getByText('NLP')).toBeInTheDocument()
    expect(screen.getByText('16K')).toBeInTheDocument()
    expect(screen.getByText('procesadas')).toBeInTheDocument()
  })

  it('renders subtitle', () => {
    render(<PipelineNode {...defaultProps} />)
    expect(screen.getByText('v11.4')).toBeInTheDocument()
  })

  it('renders status-based styling', () => {
    const { container } = render(<PipelineNode {...defaultProps} status="warning" />)
    const node = container.querySelector('[data-testid="pipeline-node-nlp"]')
    expect(node?.className).toContain('amber')
  })

  it('renders error status', () => {
    const { container } = render(<PipelineNode {...defaultProps} status="error" />)
    const node = container.querySelector('[data-testid="pipeline-node-nlp"]')
    expect(node?.className).toContain('red')
  })

  it('renders action buttons', () => {
    const onClick = vi.fn()
    render(
      <PipelineNode
        {...defaultProps}
        actions={[
          { label: 'Procesar', icon: Play, onClick, variant: 'primary' },
          { label: 'Config', icon: Settings, onClick, variant: 'secondary' },
        ]}
      />
    )
    expect(screen.getByText('Procesar')).toBeInTheDocument()
    expect(screen.getByText('Config')).toBeInTheDocument()
  })

  it('calls action onClick', () => {
    const onClick = vi.fn()
    render(
      <PipelineNode
        {...defaultProps}
        actions={[{ label: 'Ejecutar', onClick }]}
      />
    )
    fireEvent.click(screen.getByText('Ejecutar'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('disables action when disabled prop', () => {
    const onClick = vi.fn()
    render(
      <PipelineNode
        {...defaultProps}
        actions={[{ label: 'Disabled', onClick, disabled: true }]}
      />
    )
    const btn = screen.getByText('Disabled')
    expect(btn.closest('button')).toBeDisabled()
  })

  it('calls node onClick when clicked', () => {
    const onClick = vi.fn()
    render(<PipelineNode {...defaultProps} onClick={onClick} />)
    fireEvent.click(screen.getByTestId('pipeline-node-nlp'))
    expect(onClick).toHaveBeenCalled()
  })

  it('does not propagate action click to node', () => {
    const nodeClick = vi.fn()
    const actionClick = vi.fn()
    render(
      <PipelineNode
        {...defaultProps}
        onClick={nodeClick}
        actions={[{ label: 'Action', onClick: actionClick }]}
      />
    )
    fireEvent.click(screen.getByText('Action'))
    expect(actionClick).toHaveBeenCalled()
    expect(nodeClick).not.toHaveBeenCalled()
  })
})

describe('PipelineArrow', () => {
  it('renders SVG arrow', () => {
    const { container } = render(<PipelineArrow />)
    expect(container.querySelector('svg')).toBeTruthy()
  })
})

describe('PipelineGate', () => {
  const defaultProps = {
    id: 'gate-nlp',
    label: 'GATE NLP',
    rulesCount: 35,
    approvedPct: 99,
    blockedCount: 1,
    errorsCount: 0,
    actions: [],
  }

  it('renders label and rules count', () => {
    render(<PipelineGate {...defaultProps} />)
    expect(screen.getByText('GATE NLP')).toBeInTheDocument()
    expect(screen.getByText('35 reglas')).toBeInTheDocument()
  })

  it('renders approved percentage', () => {
    render(<PipelineGate {...defaultProps} />)
    expect(screen.getByText('99% aprobado')).toBeInTheDocument()
  })

  it('shows blocked count when > 0', () => {
    render(<PipelineGate {...defaultProps} blockedCount={5} />)
    expect(screen.getByText('5 bloqueados')).toBeInTheDocument()
  })

  it('shows errors count when > 0', () => {
    render(<PipelineGate {...defaultProps} errorsCount={12} />)
    expect(screen.getByText('12 errores')).toBeInTheDocument()
  })

  it('uses warning style when errors > 0', () => {
    const { container } = render(<PipelineGate {...defaultProps} errorsCount={5} />)
    const gate = container.querySelector('[data-testid="pipeline-gate-gate-nlp"]')
    expect(gate?.className).toContain('amber')
  })

  it('uses ok style when no errors', () => {
    const { container } = render(<PipelineGate {...defaultProps} errorsCount={0} blockedCount={0} />)
    const gate = container.querySelector('[data-testid="pipeline-gate-gate-nlp"]')
    expect(gate?.className).toContain('green')
  })

  it('renders action buttons', () => {
    const onClick = vi.fn()
    render(
      <PipelineGate
        {...defaultProps}
        actions={[{ label: 'Ver bloqueados', icon: AlertCircle, onClick }]}
      />
    )
    expect(screen.getByText('Ver bloqueados')).toBeInTheDocument()
  })
})

describe('MejoraContinuaNode', () => {
  const defaultProps = {
    id: 'training',
    label: 'TRAINING',
    icon: FileText,
    status: 'ok' as const,
    metric: 602,
    metricLabel: 'pares',
    actions: [],
  }

  it('renders label and metric', () => {
    render(<MejoraContinuaNode {...defaultProps} />)
    expect(screen.getByText('TRAINING')).toBeInTheDocument()
    expect(screen.getByText('602')).toBeInTheDocument()
    expect(screen.getByText('pares')).toBeInTheDocument()
  })

  it('renders action-needed status with pulse', () => {
    const { container } = render(<MejoraContinuaNode {...defaultProps} status="action-needed" />)
    const node = container.querySelector('[data-testid="mejora-node-training"]')
    expect(node?.className).toContain('blue')
  })

  it('renders actions', () => {
    const onClick = vi.fn()
    render(
      <MejoraContinuaNode
        {...defaultProps}
        actions={[{ label: 'Ver stats', icon: Zap, onClick }]}
      />
    )
    expect(screen.getByText('Ver stats')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const onClick = vi.fn()
    render(<MejoraContinuaNode {...defaultProps} onClick={onClick} />)
    fireEvent.click(screen.getByTestId('mejora-node-training'))
    expect(onClick).toHaveBeenCalled()
  })
})

describe('MejoraArrow', () => {
  it('renders SVG arrow', () => {
    const { container } = render(<MejoraArrow />)
    expect(container.querySelector('svg')).toBeTruthy()
  })
})
