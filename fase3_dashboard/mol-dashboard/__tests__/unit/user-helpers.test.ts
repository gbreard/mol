import { describe, it, expect } from 'vitest'
import {
  isTrial,
  hasTrialExpired,
  getTrialDaysRemaining,
  canAccessDashboard,
  isOficinaEmpleo,
  ROLE,
  PLAN,
  getRoleBadge,
  getPlanBadge,
} from '@/lib/user'

describe('isTrial', () => {
  it('returns true for trial plan', () => {
    expect(isTrial(PLAN.TRIAL)).toBe(true)
  })

  it('returns false for other plans', () => {
    expect(isTrial(PLAN.FREE)).toBe(false)
    expect(isTrial(PLAN.PRO)).toBe(false)
    expect(isTrial(PLAN.ENTERPRISE)).toBe(false)
  })
})

describe('hasTrialExpired', () => {
  it('returns true when no start date', () => {
    expect(hasTrialExpired()).toBe(true)
    expect(hasTrialExpired(undefined)).toBe(true)
  })

  it('returns true for invalid date string', () => {
    expect(hasTrialExpired('not-a-date')).toBe(true)
  })

  it('returns false for date within 7 days', () => {
    const now = new Date()
    const threesDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000)
    expect(hasTrialExpired(threesDaysAgo.toISOString())).toBe(false)
  })

  it('returns false for date just started (now)', () => {
    expect(hasTrialExpired(new Date().toISOString())).toBe(false)
  })

  it('returns true for date 8 days ago', () => {
    const now = new Date()
    const eightDaysAgo = new Date(now.getTime() - 8 * 24 * 60 * 60 * 1000)
    expect(hasTrialExpired(eightDaysAgo.toISOString())).toBe(true)
  })

  it('returns true for date exactly 7 days ago', () => {
    const now = new Date()
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    expect(hasTrialExpired(sevenDaysAgo.toISOString())).toBe(true)
  })
})

describe('getTrialDaysRemaining', () => {
  it('returns 0 when no start date', () => {
    expect(getTrialDaysRemaining()).toBe(0)
    expect(getTrialDaysRemaining(undefined)).toBe(0)
  })

  it('returns 7 for trial just started', () => {
    expect(getTrialDaysRemaining(new Date().toISOString())).toBe(7)
  })

  it('returns correct remaining days', () => {
    const now = new Date()
    const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000)
    expect(getTrialDaysRemaining(twoDaysAgo.toISOString())).toBe(5)
  })

  it('returns 0 for expired trial', () => {
    const now = new Date()
    const tenDaysAgo = new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000)
    expect(getTrialDaysRemaining(tenDaysAgo.toISOString())).toBe(0)
  })

  it('returns 0 for invalid date', () => {
    expect(getTrialDaysRemaining('garbage')).toBe(0)
  })
})

describe('canAccessDashboard', () => {
  it('admin always has access', () => {
    expect(canAccessDashboard(ROLE.ADMIN, PLAN.FREE)).toBe(true)
    expect(canAccessDashboard(ROLE.SUPER_ADMIN, PLAN.FREE)).toBe(true)
  })

  it('subscriber always has access', () => {
    expect(canAccessDashboard(ROLE.VIEWER, PLAN.PRO)).toBe(true)
    expect(canAccessDashboard(ROLE.ANALYST, PLAN.ENTERPRISE)).toBe(true)
  })

  it('active trial has access', () => {
    const trialStart = new Date().toISOString()
    expect(canAccessDashboard(ROLE.VIEWER, PLAN.TRIAL, trialStart)).toBe(true)
  })

  it('expired trial does NOT have access', () => {
    const eightDaysAgo = new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString()
    expect(canAccessDashboard(ROLE.VIEWER, PLAN.TRIAL, eightDaysAgo)).toBe(false)
  })

  it('trial without start date does NOT have access', () => {
    expect(canAccessDashboard(ROLE.VIEWER, PLAN.TRIAL)).toBe(false)
  })

  it('free viewer does NOT have access', () => {
    expect(canAccessDashboard(ROLE.VIEWER, PLAN.FREE)).toBe(false)
  })

  it('free analyst does NOT have access', () => {
    expect(canAccessDashboard(ROLE.ANALYST, PLAN.FREE)).toBe(false)
  })
})

describe('isOficinaEmpleo', () => {
  it('returns true for oficina_empleo role', () => {
    expect(isOficinaEmpleo(ROLE.OFICINA_EMPLEO)).toBe(true)
  })

  it('returns false for other roles', () => {
    expect(isOficinaEmpleo(ROLE.VIEWER)).toBe(false)
    expect(isOficinaEmpleo(ROLE.ADMIN)).toBe(false)
  })
})

describe('getRoleBadge', () => {
  it('returns badge for oficina_empleo', () => {
    const badge = getRoleBadge(ROLE.OFICINA_EMPLEO)
    expect(badge.label).toBe('Oficina de Empleo')
    expect(badge.className).toContain('teal')
  })
})

describe('getPlanBadge', () => {
  it('returns null for free plan', () => {
    expect(getPlanBadge(PLAN.FREE)).toBeNull()
  })

  it('returns badge for trial plan', () => {
    const badge = getPlanBadge(PLAN.TRIAL)
    expect(badge).not.toBeNull()
    expect(badge!.label).toContain('Trial')
    expect(badge!.className).toContain('orange')
  })
})
