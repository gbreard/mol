/**
 * Regression test: /admin/skills must NOT fetch the 59MB mol_skills_profile.json.
 * Stats + occupations come from a single /api/skills-intelligence call at mount.
 * Tabs receive the data as props — no duplicate fetches.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AdminSkillsPage from '../../app/admin/skills/page'

// Minimal mock responses for the fetches the page makes on mount
const MOCK_HIERARCHY = { children: [] }
const MOCK_OCCUPATIONS_INDEX = {
  'abc-123': { label: 'Software developer', isco: '2512' }
}
const MOCK_SKILLS_INTELLIGENCE = {
  stats: { total_ofertas: 500, total_ocupaciones: 42, total_skills: 1200, avg_skills_por_oferta: 4.2 },
  occupations: [
    { esco_uri: 'http://data.europa.eu/esco/occupation/abc-123', esco_label: 'Software developer', isco_code: '2512', ofertas_count: 35 }
  ],
  generated_at: '2026-02-25T00:00:00Z'
}
const MOCK_FULL_DETAIL = {
  'abc-123': {
    label: 'Software developer',
    isco: '2512',
    skills: { essential: [], optional: [] },
    knowledge: { essential: [], optional: [] },
    similar: [],
    counts: { skills_essential: 0, skills_optional: 0, knowledge_essential: 0, knowledge_optional: 0, total_skills: 0, total_knowledge: 0, similar: 0 }
  }
}

let fetchSpy: ReturnType<typeof vi.spyOn>

beforeEach(() => {
  fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const url = typeof input === 'string' ? input : (input as Request).url

    if (url.includes('esco_skills_hierarchy.json')) {
      return Response.json(MOCK_HIERARCHY)
    }
    if (url.includes('occupations_index.json')) {
      return Response.json(MOCK_OCCUPATIONS_INDEX)
    }
    if (url.includes('occupation_full_detail.json')) {
      return Response.json(MOCK_FULL_DETAIL)
    }
    if (url.includes('/api/skills-intelligence')) {
      return Response.json(MOCK_SKILLS_INTELLIGENCE)
    }

    // Fallback: return empty JSON (catch sub-component fetches)
    return Response.json({})
  })
})

afterEach(() => {
  fetchSpy.mockRestore()
})

describe('AdminSkillsPage – no 59MB fetch', () => {
  it('never fetches mol_skills_profile.json on any tab', async () => {
    const user = userEvent.setup()

    await act(async () => {
      render(<AdminSkillsPage />)
    })

    // Click "Perfil Argentina" tab
    const argTab = screen.getByRole('button', { name: /perfil argentina/i })
    await user.click(argTab)

    // Click "Consolidado" tab
    const conTab = screen.getByRole('button', { name: /consolidado/i })
    await user.click(conTab)

    // Collect all fetched URLs
    const fetchedUrls = fetchSpy.mock.calls.map(([input]) =>
      typeof input === 'string' ? input : (input as Request).url
    )

    expect(fetchedUrls.some(u => u.includes('mol_skills_profile.json'))).toBe(false)
  })

  it('calls /api/skills-intelligence exactly once (shared across tabs)', async () => {
    const user = userEvent.setup()

    await act(async () => {
      render(<AdminSkillsPage />)
    })

    // Navigate to both tabs that previously made their own fetch
    const argTab = screen.getByRole('button', { name: /perfil argentina/i })
    await user.click(argTab)

    const conTab = screen.getByRole('button', { name: /consolidado/i })
    await user.click(conTab)

    const skillsIntelCalls = fetchSpy.mock.calls.filter(([input]) => {
      const url = typeof input === 'string' ? input : (input as Request).url
      return url.includes('/api/skills-intelligence')
    })

    expect(skillsIntelCalls).toHaveLength(1)
  })

  it('renders stats from the API in the header', async () => {
    await act(async () => {
      render(<AdminSkillsPage />)
    })

    // Wait for stats to render
    expect(await screen.findByText(/500/)).toBeInTheDocument()
    expect(await screen.findByText(/42/)).toBeInTheDocument()
  })
})
