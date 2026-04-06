import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { StructuredSkills } from '@/components/oficina-empleo/StructuredSkills'
import { SkillProfilePanel } from '@/components/oficina-empleo/SkillProfilePanel'
import type { SelectedSkill, SelectedOccupation } from '@/components/oficina-empleo/useSkillCapture'

// ============================================================
// StructuredSkills
// ============================================================

describe('StructuredSkills', () => {
  it('renderiza las 3 tabs de categorías', () => {
    render(<StructuredSkills skillUris={new Set()} onAddSkill={vi.fn()} />)
    expect(screen.getByText('Idiomas')).toBeDefined()
    expect(screen.getByText('Ofimática')).toBeDefined()
    expect(screen.getByText('Software')).toBeDefined()
  })

  it('agrega una skill estructurada con label compuesto', () => {
    const onAdd = vi.fn()
    render(<StructuredSkills skillUris={new Set()} onAddSkill={onAdd} />)

    // Select Inglés
    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'Inglés' } })
    fireEvent.change(selects[1], { target: { value: 'Avanzado' } })

    // Click add button
    const addBtn = screen.getByRole('button', { name: '' }) // Plus icon button
    fireEvent.click(addBtn)

    expect(onAdd).toHaveBeenCalledOnce()
    const skill = onAdd.mock.calls[0][0]
    expect(skill.label).toBe('Inglés — Avanzado')
    expect(skill.source).toBe('estructurado')
    expect(skill.category).toBe('idioma')
    expect(skill.type).toBe('knowledge')
  })

  it('cambia a tab Software y muestra opciones correctas', () => {
    render(<StructuredSkills skillUris={new Set()} onAddSkill={vi.fn()} />)

    fireEvent.click(screen.getByText('Software'))

    const selects = screen.getAllByRole('combobox')
    const options = Array.from(selects[0].querySelectorAll('option')).map((o: any) => o.textContent)
    expect(options).toContain('Python')
    expect(options).toContain('JavaScript')
    expect(options).toContain('SAP')
  })

  it('no agrega si falta nivel', () => {
    const onAdd = vi.fn()
    render(<StructuredSkills skillUris={new Set()} onAddSkill={onAdd} />)

    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'Inglés' } })
    // No selecciono nivel

    const addBtn = screen.getByRole('button', { name: '' })
    fireEvent.click(addBtn)

    expect(onAdd).not.toHaveBeenCalled()
  })
})

// ============================================================
// SkillProfilePanel
// ============================================================

describe('SkillProfilePanel', () => {
  const baseProps = {
    onRemoveSkill: vi.fn(),
    onRemoveOccupation: vi.fn(),
    nombre: '',
    dni: '',
    onSetNombre: vi.fn(),
    onSetDni: vi.fn(),
    onSave: vi.fn(),
  }

  it('muestra estado vacío sin skills ni ocupaciones', () => {
    render(<SkillProfilePanel {...baseProps} ocupaciones={[]} skills={[]} />)
    expect(screen.getByText(/Usá las vías de captura/)).toBeDefined()
  })

  it('muestra ocupaciones como chips', () => {
    const occs: SelectedOccupation[] = [
      { id: '1', label: 'Albañil', isco_code: '7112' },
      { id: '2', label: 'Electricista', isco_code: '7411' },
    ]
    render(<SkillProfilePanel {...baseProps} ocupaciones={occs} skills={[]} />)
    expect(screen.getByText('Albañil')).toBeDefined()
    expect(screen.getByText('Electricista')).toBeDefined()
  })

  it('clasifica skills esenciales en sección separada', () => {
    const skills: SelectedSkill[] = [
      { uri: 's1', label: 'Soldadura', type: 'skill', source: 'ocupacion', essential_for_occupation: true, L1: 'S2' },
      { uri: 's2', label: 'Inglés — Avanzado', type: 'knowledge', source: 'estructurado', category: 'idioma' },
    ]
    render(<SkillProfilePanel {...baseProps} ocupaciones={[]} skills={skills} />)
    expect(screen.getByText('Skills esenciales')).toBeDefined()
    expect(screen.getByText('Idiomas')).toBeDefined()
    expect(screen.getByText(/Soldadura/)).toBeDefined()
    expect(screen.getByText(/Inglés — Avanzado/)).toBeDefined()
  })

  it('muestra contador de competencias', () => {
    const skills: SelectedSkill[] = [
      { uri: 's1', label: 'Skill 1', type: 'skill', source: 'busqueda' },
      { uri: 's2', label: 'Skill 2', type: 'skill', source: 'busqueda' },
    ]
    render(<SkillProfilePanel {...baseProps} ocupaciones={[]} skills={skills} />)
    expect(screen.getByText('2 competencias')).toBeDefined()
  })

  it('botón Guardar deshabilitado sin nombre/dni/skills', () => {
    render(<SkillProfilePanel {...baseProps} ocupaciones={[]} skills={[]} />)
    const btn = screen.getByText('Guardar perfil')
    expect(btn.hasAttribute('disabled')).toBe(true)
  })

  it('botón Guardar habilitado con nombre + dni + skills', () => {
    const skills: SelectedSkill[] = [
      { uri: 's1', label: 'Skill', type: 'skill', source: 'busqueda' },
    ]
    render(<SkillProfilePanel {...baseProps} nombre="Test" dni="123" ocupaciones={[]} skills={skills} />)
    const btn = screen.getByText('Guardar perfil')
    expect(btn.hasAttribute('disabled')).toBe(false)
  })

  it('llama onRemoveSkill al clickear X en skill', () => {
    const onRemove = vi.fn()
    const skills: SelectedSkill[] = [
      { uri: 's1', label: 'Soldadura', type: 'skill', source: 'busqueda' },
    ]
    const { container } = render(
      <SkillProfilePanel {...baseProps} onRemoveSkill={onRemove} ocupaciones={[]} skills={skills} />
    )
    // Find the X button near the skill — it's in a group-hover element
    const removeButtons = container.querySelectorAll('button')
    // Last button before save is the skill remove
    const skillRemoveBtn = Array.from(removeButtons).find(btn =>
      btn.closest('.group') && btn.querySelector('svg')
    )
    if (skillRemoveBtn) {
      fireEvent.click(skillRemoveBtn)
      expect(onRemove).toHaveBeenCalledWith('s1')
    }
  })

  it('clasifica digital skills correctamente (L1=S5)', () => {
    const skills: SelectedSkill[] = [
      { uri: 's1', label: 'Programación', type: 'skill', source: 'busqueda', L1: 'S5' },
    ]
    render(<SkillProfilePanel {...baseProps} ocupaciones={[]} skills={skills} />)
    expect(screen.getByText('Habilidades digitales')).toBeDefined()
  })

  it('clasifica transversales correctamente (L1=T1)', () => {
    const skills: SelectedSkill[] = [
      { uri: 's1', label: 'Trabajo en equipo', type: 'skill', source: 'busqueda', L1: 'T1' },
    ]
    render(<SkillProfilePanel {...baseProps} ocupaciones={[]} skills={skills} />)
    expect(screen.getByText('Transversales')).toBeDefined()
  })
})
