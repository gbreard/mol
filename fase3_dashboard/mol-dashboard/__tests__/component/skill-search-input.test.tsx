import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import SkillSearchByTask from '@/components/SkillSearchByTask'

describe('SkillSearchByTask', () => {
  it('renderiza el input de busqueda', () => {
    render(<SkillSearchByTask />)
    expect(screen.getByLabelText('Buscar skills')).toBeInTheDocument()
  })

  it('no muestra dropdown sin texto', () => {
    render(<SkillSearchByTask />)
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('muestra resultados con definicion despues del debounce', async () => {
    render(<SkillSearchByTask />)
    const input = screen.getByLabelText('Buscar skills')
    fireEvent.change(input, { target: { value: 'soldadura' } })
    fireEvent.focus(input)
    await waitFor(
      () => expect(screen.getByRole('listbox')).toBeInTheDocument(),
      { timeout: 600 }
    )
    expect(screen.getByText('soldadura MIG')).toBeInTheDocument()
    expect(screen.getByText(/soldadura por arco/)).toBeInTheDocument()
  })

  it('muestra mensaje sin resultados para query sin match', async () => {
    render(<SkillSearchByTask />)
    const input = screen.getByLabelText('Buscar skills')
    // El mock retorna vacío para query vacío — usamos un query que no matchea
    // Sobreescribimos fetch para este caso
    const originalFetch = global.fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: [] }),
    } as Response)

    fireEvent.change(input, { target: { value: 'xyzabc123' } })
    fireEvent.focus(input)
    await waitFor(
      () => expect(screen.getByRole('listbox')).toBeInTheDocument(),
      { timeout: 600 }
    )
    expect(screen.getByText(/Sin resultados/)).toBeInTheDocument()

    global.fetch = originalFetch
  })

  it('click en resultado agrega skill al perfil', async () => {
    const onSkillsChange = vi.fn()
    render(<SkillSearchByTask onSkillsChange={onSkillsChange} />)
    const input = screen.getByLabelText('Buscar skills')
    fireEvent.change(input, { target: { value: 'soldadura' } })
    fireEvent.focus(input)
    await waitFor(() => screen.getByRole('listbox'), { timeout: 600 })
    fireEvent.mouseDown(screen.getByText('soldadura MIG'))
    await waitFor(() => {
      expect(onSkillsChange).toHaveBeenCalled()
      const skills = onSkillsChange.mock.calls[0][0]
      expect(skills[0].label).toBe('soldadura MIG')
    })
  })

  it('lista de skills agregadas aparece despues de agregar', async () => {
    render(<SkillSearchByTask />)
    const input = screen.getByLabelText('Buscar skills')
    fireEvent.change(input, { target: { value: 'soldadura' } })
    fireEvent.focus(input)
    await waitFor(() => screen.getByRole('listbox'), { timeout: 600 })
    fireEvent.mouseDown(screen.getByText('soldadura MIG'))
    await waitFor(() => {
      expect(screen.getByText('Competencias agregadas (1)')).toBeInTheDocument()
    })
  })
})
