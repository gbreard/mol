import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, act } from '@testing-library/react'

const { getIssuesPendientes, pathname } = vi.hoisted(() => ({
  getIssuesPendientes: vi.fn(),
  pathname: { value: '/' },
}))

vi.mock('@/lib/supabase', () => ({ getIssuesPendientes }))
vi.mock('next/navigation', () => ({ usePathname: () => pathname.value }))

import { IssueProvider, useIssues } from '@/contexts/IssueContext'

let ctx: ReturnType<typeof useIssues> | null = null
function Probe() {
  ctx = useIssues()
  return null
}

beforeEach(() => {
  vi.clearAllMocks()
  getIssuesPendientes.mockResolvedValue([])
  ctx = null
})

describe('IssueProvider — carga de issues', () => {
  it('carga al montar en rutas de admin/analistas', async () => {
    pathname.value = '/admin/validacion'
    await act(async () => { render(<IssueProvider><Probe /></IssueProvider>) })
    expect(getIssuesPendientes).toHaveBeenCalledTimes(1)
  })

  it.each(['/login', '/vip/dashboard', '/oficina-empleo/perfiles'])('no carga al montar en %s, sí al abrir el panel', async (ruta) => {
    pathname.value = ruta
    await act(async () => { render(<IssueProvider><Probe /></IssueProvider>) })
    expect(getIssuesPendientes).not.toHaveBeenCalled()

    await act(async () => { ctx!.openDrawer() })
    expect(getIssuesPendientes).toHaveBeenCalledTimes(1)
  })
})
