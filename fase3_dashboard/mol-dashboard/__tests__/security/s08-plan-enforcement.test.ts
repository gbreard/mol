import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const PROJECT_ROOT = path.resolve(__dirname, '../..')

describe('S-08: Plan enforcement on dashboard routes', () => {
  it('middleware should check plan on /dashboard routes', () => {
    const middlewarePath = path.join(PROJECT_ROOT, 'lib/supabase/middleware.ts')
    const content = fs.readFileSync(middlewarePath, 'utf-8')

    // Must handle dashboard routes specifically
    expect(content).toContain('/dashboard')
    // Should check plan
    expect(content).toMatch(/plan/)
    // Should check trial
    expect(content).toContain('trial')
  })

  it('middleware should redirect free users from /dashboard', () => {
    const middlewarePath = path.join(PROJECT_ROOT, 'lib/supabase/middleware.ts')
    const content = fs.readFileSync(middlewarePath, 'utf-8')

    // Should have redirect for non-authorized dashboard access
    expect(content).toContain('no_access')
    expect(content).toContain('trial_expired')
  })

  it('middleware should gate /oficina-empleo routes', () => {
    const middlewarePath = path.join(PROJECT_ROOT, 'lib/supabase/middleware.ts')
    const content = fs.readFileSync(middlewarePath, 'utf-8')

    expect(content).toContain('oficina-empleo')
    expect(content).toContain('oficina_empleo')
  })

  it('dashboard layout should have defense-in-depth canAccessDashboard check', () => {
    const layoutPath = path.join(PROJECT_ROOT, 'app/dashboard/layout.tsx')
    const content = fs.readFileSync(layoutPath, 'utf-8')

    expect(content).toContain('canAccessDashboard')
    expect(content).toContain('no_access')
  })

  it('user.ts should export trial helper functions', () => {
    const userPath = path.join(PROJECT_ROOT, 'lib/user.ts')
    const content = fs.readFileSync(userPath, 'utf-8')

    expect(content).toContain('export function isTrial')
    expect(content).toContain('export function hasTrialExpired')
    expect(content).toContain('export function getTrialDaysRemaining')
    expect(content).toContain('export function canAccessDashboard')
    expect(content).toContain('export function isOficinaEmpleo')
  })

  it('ROLE should include oficina_empleo', () => {
    const userPath = path.join(PROJECT_ROOT, 'lib/user.ts')
    const content = fs.readFileSync(userPath, 'utf-8')

    expect(content).toContain('OFICINA_EMPLEO')
    expect(content).toContain('"oficina_empleo"')
  })

  it('PLAN should include trial', () => {
    const userPath = path.join(PROJECT_ROOT, 'lib/user.ts')
    const content = fs.readFileSync(userPath, 'utf-8')

    expect(content).toContain('TRIAL')
    expect(content).toMatch(/TRIAL.*trial/)
  })

  it('api-auth.ts should export requireSubscriber', () => {
    const apiAuthPath = path.join(PROJECT_ROOT, 'lib/api-auth.ts')
    const content = fs.readFileSync(apiAuthPath, 'utf-8')

    expect(content).toContain('export async function requireSubscriber')
    expect(content).toContain('trial')
    expect(content).toContain('403')
  })

  it('admin users API should accept oficina_empleo role', () => {
    const routePath = path.join(PROJECT_ROOT, 'app/api/admin/users/route.ts')
    const content = fs.readFileSync(routePath, 'utf-8')

    expect(content).toContain('oficina_empleo')
  })

  it('admin users API should accept plan field', () => {
    const routePath = path.join(PROJECT_ROOT, 'app/api/admin/users/route.ts')
    const content = fs.readFileSync(routePath, 'utf-8')

    expect(content).toContain('validPlans')
    expect(content).toContain('trial')
    expect(content).toContain('trial_start_date')
  })

  it('admin solicitudes API should exist', () => {
    const routePath = path.join(PROJECT_ROOT, 'app/api/admin/solicitudes/route.ts')
    expect(fs.existsSync(routePath)).toBe(true)

    const content = fs.readFileSync(routePath, 'utf-8')
    expect(content).toContain('requireAdmin')
    expect(content).toContain('aprobar')
    expect(content).toContain('rechazar')
  })

  it('auth-utils should allow new redirect paths', () => {
    const authUtilsPath = path.join(PROJECT_ROOT, 'lib/auth-utils.ts')
    const content = fs.readFileSync(authUtilsPath, 'utf-8')

    expect(content).toContain('/solicitar-acceso')
    expect(content).toContain('/contenido')
    expect(content).toContain('/oficina-empleo')
  })

  it('solicitar-acceso page should exist', () => {
    const pagePath = path.join(PROJECT_ROOT, 'app/solicitar-acceso/page.tsx')
    expect(fs.existsSync(pagePath)).toBe(true)
  })

  it('oficina-empleo layout should check role', () => {
    const layoutPath = path.join(PROJECT_ROOT, 'app/oficina-empleo/layout.tsx')
    const content = fs.readFileSync(layoutPath, 'utf-8')

    expect(content).toContain('isAdmin')
    expect(content).toContain('isOficinaEmpleo')
    expect(content).toContain('redirect')
  })
})
