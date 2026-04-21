import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import FreeTextSkillExtractor from '@/components/FreeTextSkillExtractor'

describe('FreeTextSkillExtractor', () => {
  it('renderiza el textarea', () => {
    render(<FreeTextSkillExtractor />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('boton deshabilitado si texto vacio', () => {
    render(<FreeTextSkillExtractor />)
    expect(screen.getByRole('button', { name: /identificar/i })).toBeDisabled()
  })

  it('boton habilitado cuando hay texto', () => {
    render(<FreeTextSkillExtractor />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'sé soldar' } })
    expect(screen.getByRole('button', { name: /identificar/i })).not.toBeDisabled()
  })

  it('muestra loading state al procesar', async () => {
    render(<FreeTextSkillExtractor />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'sé soldar' } })
    fireEvent.click(screen.getByRole('button', { name: /identificar/i }))
    expect(screen.getByRole('status', { name: /procesando/i })).toBeInTheDocument()
  })

  it('muestra skills identificadas con definicion', async () => {
    render(<FreeTextSkillExtractor />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'sé soldar y operar tornos' } })
    fireEvent.click(screen.getByRole('button', { name: /identificar/i }))
    await waitFor(() => expect(screen.getByText('soldadura MIG')).toBeInTheDocument())
    expect(screen.getByText('operación de torno CNC')).toBeInTheDocument()
    expect(screen.getByText(/soldadura por arco/)).toBeInTheDocument()
  })

  it('agregar todas llama onSkillsAdded con skills no descartadas', async () => {
    const onSkillsAdded = vi.fn()
    render(<FreeTextSkillExtractor onSkillsAdded={onSkillsAdded} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'sé soldar' } })
    fireEvent.click(screen.getByRole('button', { name: /identificar/i }))
    await waitFor(() => screen.getByText('Agregar todas al perfil'))
    fireEvent.click(screen.getByText('Agregar todas al perfil'))
    expect(onSkillsAdded).toHaveBeenCalledOnce()
    const skills = onSkillsAdded.mock.calls[0][0]
    expect(skills.length).toBe(2)
    expect(skills[0].via).toBe('texto_libre')
  })

  it('muestra error si falla la API', async () => {
    const originalFetch = global.fetch
    global.fetch = vi.fn().mockResolvedValue({ ok: false } as Response)
    render(<FreeTextSkillExtractor />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'texto' } })
    fireEvent.click(screen.getByRole('button', { name: /identificar/i }))
    await waitFor(() =>
      expect(screen.getByText(/Error al procesar el texto/)).toBeInTheDocument()
    )
    global.fetch = originalFetch
  })
})
