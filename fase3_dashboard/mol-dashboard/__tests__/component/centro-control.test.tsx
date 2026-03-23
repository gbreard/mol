import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import PipelineStatus, { type PipelineNode } from '@/components/PipelineStatus'
import AlertActionList, { type SystemAlert } from '@/components/AlertActionList'
import ReconciliationPanel, { type ReconciliationRow } from '@/components/ReconciliationPanel'

// ─── S31: PipelineStatus ──────────────────────────────────────────────────────

const mockNodes: PipelineNode[] = [
  { id: 'vps',      label: 'VPS',      sublabel: '5 portales', status: 'ok' },
  { id: 'local',    label: 'Local',    sublabel: '16.432',     status: 'ok' },
  { id: 'supabase', label: 'Supabase', sublabel: '16.100',     status: 'warning', detalle: '332 pendientes' },
  { id: 'vercel',   label: 'Vercel',   status: 'error', detalle: 'Build fallido' },
]

describe('S31 — PipelineStatus', () => {
  it('renderiza todos los nodos', () => {
    render(<PipelineStatus nodes={mockNodes} />)
    expect(screen.getByLabelText(/VPS: ok/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Local: ok/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Supabase: warning/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Vercel: error/)).toBeInTheDocument()
  })

  it('muestra sublabels de cada nodo', () => {
    render(<PipelineStatus nodes={mockNodes} />)
    expect(screen.getByText('5 portales')).toBeInTheDocument()
    expect(screen.getByText('16.432')).toBeInTheDocument()
  })

  it('nodo error incluye detalle en aria-label', () => {
    render(<PipelineStatus nodes={mockNodes} />)
    expect(screen.getByLabelText(/Build fallido/)).toBeInTheDocument()
  })
})

// ─── S32: AlertActionList ─────────────────────────────────────────────────────

const mockAlerts: SystemAlert[] = [
  {
    id: 'a1',
    nivel: 'error',
    titulo: 'VPS no responde',
    detalle: 'Sin conexión hace 2 horas',
    accion: { label: 'Reiniciar scraper', comando: 'restart_scraper' },
  },
  {
    id: 'a2',
    nivel: 'warning',
    titulo: 'Supabase con retraso',
    detalle: '332 ofertas pendientes de sync',
    accion: { label: 'Sync ahora', comando: 'sync_supabase' },
  },
  {
    id: 'a3',
    nivel: 'info',
    titulo: 'NLP procesando',
    detalle: '45 ofertas en cola',
  },
]

describe('S32 — AlertActionList', () => {
  it('renderiza alertas con aria-label', () => {
    render(<AlertActionList alerts={mockAlerts} />)
    expect(screen.getByLabelText('Alerta error: VPS no responde')).toBeInTheDocument()
    expect(screen.getByLabelText('Alerta warning: Supabase con retraso')).toBeInTheDocument()
  })

  it('muestra detalles de cada alerta', () => {
    render(<AlertActionList alerts={mockAlerts} />)
    expect(screen.getByText('Sin conexión hace 2 horas')).toBeInTheDocument()
  })

  it('botón acción llama onAccion con la alerta', () => {
    const onAccion = vi.fn()
    render(<AlertActionList alerts={mockAlerts} onAccion={onAccion} />)
    fireEvent.click(screen.getByLabelText('Acción: Reiniciar scraper'))
    expect(onAccion).toHaveBeenCalledWith(mockAlerts[0])
  })

  it('alertas sin acción no muestran botón', () => {
    render(<AlertActionList alerts={mockAlerts} />)
    const btns = screen.getAllByRole('button')
    expect(btns.length).toBe(2) // solo a1 y a2 tienen acción
  })

  it('sin alertas muestra mensaje de sistemas OK', () => {
    render(<AlertActionList alerts={[]} />)
    expect(screen.getByText('Todos los sistemas operativos.')).toBeInTheDocument()
  })

  it('botones acción tienen min touch target', () => {
    render(<AlertActionList alerts={mockAlerts} />)
    expect(screen.getByLabelText('Acción: Reiniciar scraper').className).toContain('min-h-[44px]')
  })
})

// ─── S33: ReconciliationPanel ─────────────────────────────────────────────────

const mockRows: ReconciliationRow[] = [
  { sistema: 'Ofertas',   conteo_local: 16432, conteo_remoto: 16100, diferencia: 332, estado: 'diff' },
  { sistema: 'Skills',    conteo_local: 98450, conteo_remoto: 98450, diferencia: 0,   estado: 'ok' },
  { sistema: 'NLP',       conteo_local: 15800, conteo_remoto: 15600, diferencia: 200, estado: 'diff' },
]

const syncedRows: ReconciliationRow[] = mockRows.map((r) => ({ ...r, diferencia: 0, estado: 'ok' as const }))

describe('S33 — ReconciliationPanel', () => {
  it('muestra tabla con sistemas', () => {
    render(<ReconciliationPanel rows={mockRows} />)
    expect(screen.getByText('Ofertas')).toBeInTheDocument()
    expect(screen.getByText('Skills')).toBeInTheDocument()
  })

  it('muestra diferencia con signo + para diffs positivas', () => {
    render(<ReconciliationPanel rows={mockRows} />)
    expect(screen.getByLabelText('Diferencia en Ofertas: +332')).toBeInTheDocument()
  })

  it('ícono OK en sistemas sincronizados', () => {
    render(<ReconciliationPanel rows={mockRows} />)
    expect(screen.getByLabelText('Skills: sincronizado')).toBeInTheDocument()
  })

  it('ícono warning en sistemas con diferencia', () => {
    render(<ReconciliationPanel rows={mockRows} />)
    expect(screen.getByLabelText('Ofertas: diferencia detectada')).toBeInTheDocument()
  })

  it('muestra botón sincronizar cuando hay diffs', () => {
    render(<ReconciliationPanel rows={mockRows} />)
    expect(screen.getByLabelText('Sincronizar faltantes')).toBeInTheDocument()
  })

  it('sin diffs no muestra botón sync y muestra mensaje OK', () => {
    render(<ReconciliationPanel rows={syncedRows} />)
    expect(screen.queryByLabelText('Sincronizar faltantes')).not.toBeInTheDocument()
    expect(screen.getByText('Todos los sistemas están sincronizados.')).toBeInTheDocument()
  })

  it('botón sync llama onSyncFaltantes', () => {
    const onSync = vi.fn()
    render(<ReconciliationPanel rows={mockRows} onSyncFaltantes={onSync} />)
    fireEvent.click(screen.getByLabelText('Sincronizar faltantes'))
    expect(onSync).toHaveBeenCalled()
  })

  it('botón sync tiene min touch target', () => {
    render(<ReconciliationPanel rows={mockRows} />)
    expect(screen.getByLabelText('Sincronizar faltantes').className).toContain('min-h-[44px]')
  })
})
