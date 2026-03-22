import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import PrivacyOptIn from '@/components/PrivacyOptIn'

describe('PrivacyOptIn', () => {
  it('renderiza toggle desactivado por defecto', () => {
    render(<PrivacyOptIn />)
    const toggle = screen.getByRole('switch', { name: /activar visibilidad/i })
    expect(toggle).toHaveAttribute('aria-checked', 'false')
    expect(screen.getByText('No, mantener privado')).toBeInTheDocument()
  })

  it('activar toggle muestra opciones de alcance', () => {
    render(<PrivacyOptIn />)
    fireEvent.click(screen.getByRole('switch', { name: /activar visibilidad/i }))
    expect(screen.getByText('Solo en mi provincia')).toBeInTheDocument()
    expect(screen.getByText('En todo el país')).toBeInTheDocument()
    expect(screen.getByText('Perfil visible (anonimizado)')).toBeInTheDocument()
  })

  it('seleccionar "provincial" muestra selector de provincia', () => {
    render(<PrivacyOptIn />)
    fireEvent.click(screen.getByRole('switch', { name: /activar visibilidad/i }))
    fireEvent.click(screen.getByLabelText(/solo en mi provincia/i))
    expect(screen.getByLabelText('Seleccionar provincia')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Buenos Aires')).toBeInTheDocument()
  })

  it('seleccionar "nacional" oculta selector de provincia', () => {
    render(<PrivacyOptIn />)
    fireEvent.click(screen.getByRole('switch', { name: /activar visibilidad/i }))
    fireEvent.click(screen.getByLabelText(/solo en mi provincia/i))
    fireEvent.click(screen.getByLabelText(/en todo el país/i))
    expect(screen.queryByLabelText('Seleccionar provincia')).not.toBeInTheDocument()
  })

  it('desactivar toggle vuelve a privado y oculta alcance', () => {
    render(<PrivacyOptIn />)
    fireEvent.click(screen.getByRole('switch', { name: /activar visibilidad/i }))
    expect(screen.getByText('Solo en mi provincia')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('switch', { name: /activar visibilidad/i }))
    expect(screen.queryByText('Solo en mi provincia')).not.toBeInTheDocument()
    expect(screen.getByText('No, mantener privado')).toBeInTheDocument()
  })

  it('guardar llama onSave con alcance privado cuando toggle off', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<PrivacyOptIn onSave={onSave} />)
    fireEvent.click(screen.getByText('Guardar preferencia'))
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith({ alcance: 'privado', provincia: null })
    })
  })

  it('guardar llama onSave con alcance nacional', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<PrivacyOptIn onSave={onSave} />)
    fireEvent.click(screen.getByRole('switch', { name: /activar visibilidad/i }))
    fireEvent.click(screen.getByText('Guardar preferencia'))
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith({ alcance: 'nacional', provincia: null })
    })
  })

  it('guardar llama onSave con alcance provincial y provincia', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<PrivacyOptIn onSave={onSave} />)
    fireEvent.click(screen.getByRole('switch', { name: /activar visibilidad/i }))
    fireEvent.click(screen.getByLabelText(/solo en mi provincia/i))
    fireEvent.change(screen.getByLabelText('Seleccionar provincia'), {
      target: { value: 'Córdoba' },
    })
    fireEvent.click(screen.getByText('Guardar preferencia'))
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith({ alcance: 'provincial', provincia: 'Córdoba' })
    })
  })

  it('muestra confirmación tras guardar', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<PrivacyOptIn onSave={onSave} />)
    fireEvent.click(screen.getByText('Guardar preferencia'))
    await waitFor(() => {
      expect(screen.getByText('Preferencia guardada')).toBeInTheDocument()
    })
  })

  it('botón guardar tiene min touch target', () => {
    render(<PrivacyOptIn />)
    const btn = screen.getByText('Guardar preferencia')
    expect(btn.className).toContain('min-h-[44px]')
  })

  it('carga estado inicial visible con provincia', () => {
    render(
      <PrivacyOptIn
        initial={{ alcance: 'provincial', provincia: 'Santa Fe' }}
      />
    )
    expect(screen.getByRole('switch', { name: /activar visibilidad/i })).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByDisplayValue('Santa Fe')).toBeInTheDocument()
  })
})
