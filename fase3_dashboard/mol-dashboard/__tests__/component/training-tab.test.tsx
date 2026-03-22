import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import TrainingTab from '@/components/TrainingTab'

describe('TrainingTab', () => {
  it('renderiza cursos por brecha por defecto', async () => {
    render(<TrainingTab profileId="profile-1" />)
    await waitFor(() => expect(screen.getByText('Docker para principiantes')).toBeInTheDocument())
    expect(screen.getByText('Python nivel inicial')).toBeInTheDocument()
  })

  it('muestra skill de la brecha como encabezado', async () => {
    render(<TrainingTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Docker'))
    expect(screen.getByText('Python')).toBeInTheDocument()
  })

  it('card de curso muestra certificacion, duracion y modalidad', async () => {
    render(<TrainingTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Certificado CABA'))
    expect(screen.getByText('40hs')).toBeInTheDocument()
    expect(screen.getByText('virtual')).toBeInTheDocument()
  })

  it('switch a tab transicion por demanda muestra tabla', async () => {
    render(<TrainingTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Docker para principiantes'))
    fireEvent.click(screen.getByText('Transición: por demanda'))
    await waitFor(() => expect(screen.getByText('Analista DevOps')).toBeInTheDocument())
    expect(screen.getByText('Ingeniero de datos')).toBeInTheDocument()
  })

  it('switch a tab transicion por preferencia muestra input de busqueda', async () => {
    render(<TrainingTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Docker para principiantes'))
    fireEvent.click(screen.getByText('Transición: elegir destino'))
    expect(screen.getByLabelText('Buscar ocupación destino')).toBeInTheDocument()
  })

  it('muestra nota de fuente', async () => {
    render(<TrainingTab profileId="profile-1" />)
    await waitFor(() => screen.getByText(/Portal de Capacitación CABA/))
    expect(screen.getByText(/2,255 cursos/)).toBeInTheDocument()
  })
})
