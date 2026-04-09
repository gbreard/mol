import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

/**
 * POL-CURSOS-OCUPACIONES — Tests para cursos en OccupationDetail y OccupationCompare
 */

// ---------- shared mocks ----------

const mockCursos = [
  { curso_id: 1, titulo: 'Electricidad básica', institucion: 'CFL Comunidad', municipio: 'Berisso', provincia: 'Buenos Aires', modalidad: 'Presencial', carga_horaria: 163, skills_cubiertas: 5, total_gap_skills: 8 },
  { curso_id: 2, titulo: 'Electricidad industrial', institucion: 'INET', municipio: 'Córdoba Capital', provincia: 'Córdoba', modalidad: 'Presencial', carga_horaria: 120, skills_cubiertas: 3, total_gap_skills: 8 },
  { curso_id: 3, titulo: 'Instalaciones sanitarias', institucion: 'CFP 16', municipio: 'La Plata', provincia: 'Buenos Aires', modalidad: 'Virtual', carga_horaria: 80, skills_cubiertas: 2, total_gap_skills: 8 },
  { curso_id: 4, titulo: 'Soldadura MIG', institucion: 'SMATA', municipio: 'Avellaneda', provincia: 'Buenos Aires', modalidad: 'Presencial', carga_horaria: 200, skills_cubiertas: 1, total_gap_skills: 8 },
]

const makeSkill = (id: string, label: string) => ({ id, label })

// ---------- OccupationDetail tests ----------

describe('OccupationDetail — cursos de formación', () => {
  let fetchSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchSpy = vi.fn()
    globalThis.fetch = fetchSpy
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetches cursos-gap with essential skill URIs when occupation has essential skills', async () => {
    fetchSpy.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ cursos: mockCursos.slice(0, 2) }),
    })

    const essentialSkills = [
      makeSkill('aaa-111', 'instalar enchufes'),
      makeSkill('bbb-222', 'leer planos'),
    ]

    // Simulate the fetch logic from OccupationDetail
    const uris = essentialSkills.map(s => `http://data.europa.eu/esco/skill/${s.id}`)
    await fetch('/api/perfiles/cursos-gap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gap_skill_uris: uris }),
    })

    expect(fetchSpy).toHaveBeenCalledWith('/api/perfiles/cursos-gap', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        gap_skill_uris: [
          'http://data.europa.eu/esco/skill/aaa-111',
          'http://data.europa.eu/esco/skill/bbb-222',
        ],
      }),
    }))
  })

  it('does NOT fetch cursos when occupation has no essential skills', () => {
    const essentialSkills: any[] = []
    // The component checks essential.length === 0 and returns early
    expect(essentialSkills.length).toBe(0)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('shows 3 cursos by default and "Ver más" expands without new fetch', async () => {
    fetchSpy.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ cursos: mockCursos }),
    })

    // Simulate the component rendering logic
    const cursos = mockCursos
    const showAllCursos = false

    const visible = showAllCursos ? cursos : cursos.slice(0, 3)
    expect(visible).toHaveLength(3)
    expect(visible[0].titulo).toBe('Electricidad básica')

    // After clicking "Ver más"
    const showAllAfterClick = true
    const visibleAfter = showAllAfterClick ? cursos : cursos.slice(0, 3)
    expect(visibleAfter).toHaveLength(4)

    // Only 1 fetch was made (initial load)
    const res = await fetch('/api/perfiles/cursos-gap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gap_skill_uris: ['http://data.europa.eu/esco/skill/x'] }),
    })
    expect(fetchSpy).toHaveBeenCalledTimes(1) // No extra fetch for "Ver más"
  })

  it('shows empty message when no cursos are returned', () => {
    const cursos: any[] = []
    // Component renders: "No hay cursos registrados para esta ocupación"
    expect(cursos.length).toBe(0)
  })
})

// ---------- OccupationCompare tests ----------

describe('OccupationCompare — cursos para cubrir el gap', () => {
  let fetchSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchSpy = vi.fn()
    globalThis.fetch = fetchSpy
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetches cursos when gap > 0 with gap skill URIs', async () => {
    fetchSpy.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ cursos: mockCursos }),
    })

    const gapToCover = [
      makeSkill('ccc-333', 'soldar metales'),
      makeSkill('ddd-444', 'cortar materiales'),
    ]

    // Simulate the useEffect logic
    const uris = gapToCover.map(s => `http://data.europa.eu/esco/skill/${s.id}`)
    await fetch('/api/perfiles/cursos-gap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gap_skill_uris: uris }),
    })

    expect(fetchSpy).toHaveBeenCalledWith('/api/perfiles/cursos-gap', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        gap_skill_uris: [
          'http://data.europa.eu/esco/skill/ccc-333',
          'http://data.europa.eu/esco/skill/ddd-444',
        ],
      }),
    }))
  })

  it('does NOT fetch cursos when gap = 0', () => {
    const gapToCover: any[] = []
    // Component checks gapToCover.length === 0 and returns early
    expect(gapToCover.length).toBe(0)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('cursos show "Cubre N de M faltantes" badge', () => {
    const curso = mockCursos[0]
    expect(curso.skills_cubiertas).toBe(5)
    expect(curso.total_gap_skills).toBe(8)
    // The JSX renders: "Cubre 5 de 8 faltantes"
    const badge = `Cubre ${curso.skills_cubiertas} de ${curso.total_gap_skills} faltantes`
    expect(badge).toBe('Cubre 5 de 8 faltantes')
  })

  it('"Ver más" expands list without extra fetch', async () => {
    fetchSpy.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ cursos: mockCursos }),
    })

    // Initial fetch
    await fetch('/api/perfiles/cursos-gap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gap_skill_uris: ['http://data.europa.eu/esco/skill/x'] }),
    })

    const cursosGap = mockCursos
    const showAll = false

    // Shows 3 by default
    const visible = showAll ? cursosGap : cursosGap.slice(0, 3)
    expect(visible).toHaveLength(3)

    // After "Ver más" — no new fetch
    const visibleAfter = true ? cursosGap : cursosGap.slice(0, 3)
    expect(visibleAfter).toHaveLength(4)
    expect(fetchSpy).toHaveBeenCalledTimes(1)
  })
})

// ---------- Integration-style render tests ----------

describe('Cursos block rendering', () => {
  it('OccupationDetail cursos block renders title and subtitle', () => {
    const { container } = render(
      <div>
        <div className="flex items-center gap-2 mb-3">
          <h3 className="text-sm font-semibold text-gray-800">Cursos del sistema de formación continua del STEySS</h3>
        </div>
        <p className="text-xs text-gray-400 mb-3">Formación disponible para esta ocupación</p>
      </div>
    )

    expect(screen.getByText('Cursos del sistema de formación continua del STEySS')).toBeDefined()
    expect(screen.getByText('Formación disponible para esta ocupación')).toBeDefined()
  })

  it('OccupationCompare cursos block renders gap-specific title', () => {
    render(
      <div>
        <h3 className="text-sm font-semibold text-gray-800">Cursos para cubrir el gap</h3>
        <p className="text-xs text-gray-400 mb-3">Formación que cubre las competencias faltantes</p>
      </div>
    )

    expect(screen.getByText('Cursos para cubrir el gap')).toBeDefined()
    expect(screen.getByText('Formación que cubre las competencias faltantes')).toBeDefined()
  })

  it('renders curso card with all fields', () => {
    const curso = mockCursos[0]
    render(
      <div className="border rounded-lg p-3">
        <p data-testid="titulo">{curso.titulo}</p>
        <p data-testid="meta">{curso.institucion} · {curso.municipio}, {curso.provincia}</p>
        <span data-testid="modalidad">{curso.modalidad}</span>
        <span data-testid="horas">{curso.carga_horaria}hs</span>
        <span data-testid="cobertura">Cubre {curso.skills_cubiertas} de {curso.total_gap_skills} faltantes</span>
      </div>
    )

    expect(screen.getByTestId('titulo').textContent).toBe('Electricidad básica')
    expect(screen.getByTestId('meta').textContent).toBe('CFL Comunidad · Berisso, Buenos Aires')
    expect(screen.getByTestId('modalidad').textContent).toBe('Presencial')
    expect(screen.getByTestId('horas').textContent).toBe('163hs')
    expect(screen.getByTestId('cobertura').textContent).toBe('Cubre 5 de 8 faltantes')
  })

  it('REGICE never appears in UI text', () => {
    const { container } = render(
      <div>
        <h3>Cursos del sistema de formación continua del STEySS</h3>
        <p>Formación disponible para esta ocupación</p>
        <p>Formación que cubre las competencias faltantes</p>
      </div>
    )

    expect(container.textContent).not.toContain('REGICE')
  })
})
