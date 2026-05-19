import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { GoldSetMetrics } from '@/components/aprendizaje/GoldSetMetrics'

describe('GoldSetMetrics', () => {
  it('renderiza el título', async () => {
    render(<GoldSetMetrics />)
    await waitFor(() => {
      expect(screen.getByText(/Gold Set real/i)).toBeInTheDocument()
    })
  })

  it('muestra KPIs del gold set', async () => {
    render(<GoldSetMetrics />)
    await waitFor(() => {
      expect(screen.getByText('112')).toBeInTheDocument() // total
      expect(screen.getByText('95')).toBeInTheDocument() // ok
      expect(screen.getByText('17')).toBeInTheDocument() // errores
      expect(screen.getByText('84.8%')).toBeInTheDocument() // tasa
    })
  })

  it('muestra distribución por validador', async () => {
    render(<GoldSetMetrics />)
    await waitFor(() => {
      expect(screen.getByText('cinvazquez4@gmail.com')).toBeInTheDocument()
      expect(screen.getByText('migracion_inicial')).toBeInTheDocument()
    })
  })

  it('muestra cobertura por run con tasa de acierto', async () => {
    render(<GoldSetMetrics />)
    await waitFor(() => {
      expect(screen.getByText('run_20260516_2052')).toBeInTheDocument()
      expect(screen.getByText('80%')).toBeInTheDocument()
      expect(screen.getByText('87.5%')).toBeInTheDocument()
    })
  })

  it('muestra tabla de casos individuales', async () => {
    render(<GoldSetMetrics />)
    await waitFor(() => {
      expect(screen.getByText('7542392224')).toBeInTheDocument()
      expect(screen.getByText('8085763783')).toBeInTheDocument()
    })
  })

  it('muestra contador de casos individuales', async () => {
    render(<GoldSetMetrics />)
    await waitFor(() => {
      expect(screen.getByText(/Casos individuales \(2 de 112\)/i)).toBeInTheDocument()
    })
  })
})
