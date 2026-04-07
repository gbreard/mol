import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SkillProfilePanel } from '@/components/oficina-empleo/SkillProfilePanel'
import type { SelectedSkill } from '@/components/oficina-empleo/useSkillCapture'

const baseProps = {
  ocupaciones: [],
  onRemoveSkill: vi.fn(),
  onRemoveOccupation: vi.fn(),
  nombre: 'Test',
  dni: '123',
  localidad: '',
  provincia: '',
  onSetNombre: vi.fn(),
  onSetDni: vi.fn(),
  onSetLocalidad: vi.fn(),
  onSetProvincia: vi.fn(),
  onSave: vi.fn(),
}

function makeSkill(overrides: Partial<SelectedSkill> = {}): SelectedSkill {
  return {
    uri: 'http://data.europa.eu/esco/skill/test-1',
    label: 'Soldadura MIG/MAG',
    type: 'skill',
    source: 'ocupacion',
    nivel: 'intermedio',
    certificado: false,
    ...overrides,
  }
}

describe('M1 Nivel de Maestría — SkillProfilePanel', () => {
  it('muestra 4 botones de nivel por skill', () => {
    render(<SkillProfilePanel {...baseProps} skills={[makeSkill()]} />)
    expect(screen.getByText('Básico')).toBeDefined()
    expect(screen.getByText('Interm.')).toBeDefined()
    expect(screen.getByText('Avanz.')).toBeDefined()
    expect(screen.getByText('Experto')).toBeDefined()
  })

  it('nivel intermedio activo por default', () => {
    render(<SkillProfilePanel {...baseProps} skills={[makeSkill()]} />)
    const btn = screen.getByText('Interm.')
    expect(btn.className).toContain('bg-teal-100')
  })

  it('click en Avanzado llama onUpdateNivel', () => {
    const onUpdate = vi.fn()
    render(<SkillProfilePanel {...baseProps} skills={[makeSkill()]} onUpdateNivel={onUpdate} />)
    fireEvent.click(screen.getByText('Avanz.'))
    expect(onUpdate).toHaveBeenCalledWith('http://data.europa.eu/esco/skill/test-1', 'avanzado')
  })

  it('skill con nivel experto muestra Experto activo', () => {
    render(<SkillProfilePanel {...baseProps} skills={[makeSkill({ nivel: 'experto' })]} />)
    const btn = screen.getByText('Experto')
    expect(btn.className).toContain('bg-purple-100')
  })

  it('click en Cert llama onToggleCertificado', () => {
    const onToggle = vi.fn()
    render(<SkillProfilePanel {...baseProps} skills={[makeSkill()]} onToggleCertificado={onToggle} />)
    fireEvent.click(screen.getByText('Cert'))
    expect(onToggle).toHaveBeenCalledWith('http://data.europa.eu/esco/skill/test-1')
  })

  it('certificado=true muestra badge verde', () => {
    render(<SkillProfilePanel {...baseProps} skills={[makeSkill({ certificado: true })]} />)
    const btn = screen.getByText('Cert')
    expect(btn.className).toContain('bg-green-100')
  })

  it('certificado=false muestra badge gris', () => {
    render(<SkillProfilePanel {...baseProps} skills={[makeSkill({ certificado: false })]} />)
    const btn = screen.getByText('Cert')
    expect(btn.className).toContain('text-gray-400')
    expect(btn.className).not.toContain('bg-green-100')
  })

  it('DemandBar y badge esencial siguen funcionando', () => {
    render(<SkillProfilePanel {...baseProps} skills={[makeSkill({ essential_for_occupation: true, market_frequency: 150 })]} />)
    expect(screen.getByText('esencial')).toBeDefined()
  })
})
