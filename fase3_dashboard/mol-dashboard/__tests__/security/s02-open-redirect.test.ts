import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { isAllowedRedirectPath } from '../../lib/auth-utils'

const PROJECT_ROOT = path.resolve(__dirname, '../..')

describe('S-02: Open redirect protection in auth callback', () => {
  it('should validate the next parameter against allowed paths', () => {
    const callbackPath = path.join(PROJECT_ROOT, 'app/auth/callback/route.ts')
    const content = fs.readFileSync(callbackPath, 'utf-8')

    // The file should contain validation logic for the redirect path
    expect(content).toContain('ALLOWED_REDIRECT_PATHS')
  })

  it('should not blindly redirect to user-supplied next parameter', () => {
    const callbackPath = path.join(PROJECT_ROOT, 'app/auth/callback/route.ts')
    const content = fs.readFileSync(callbackPath, 'utf-8')

    const hasValidation = content.includes('ALLOWED_REDIRECT_PATHS') ||
      content.includes('isAllowedPath') ||
      content.includes('safePath')

    expect(hasValidation).toBe(true)
  })

  it('rejects absolute URLs', () => {
    expect(isAllowedRedirectPath('https://evil.com')).toBe(false)
    expect(isAllowedRedirectPath('http://evil.com')).toBe(false)
    expect(isAllowedRedirectPath('//evil.com')).toBe(false)
    expect(isAllowedRedirectPath('javascript:alert(1)')).toBe(false)
  })

  it('rejects protocol-relative URLs', () => {
    expect(isAllowedRedirectPath('//evil.com')).toBe(false)
    expect(isAllowedRedirectPath('///evil.com')).toBe(false)
    expect(isAllowedRedirectPath('/\\evil.com')).toBe(false)
  })

  it('accepts valid internal paths', () => {
    expect(isAllowedRedirectPath('/home')).toBe(true)
    expect(isAllowedRedirectPath('/dashboard')).toBe(true)
    expect(isAllowedRedirectPath('/admin')).toBe(true)
    expect(isAllowedRedirectPath('/cuenta')).toBe(true)
    expect(isAllowedRedirectPath('/skills')).toBe(true)
    expect(isAllowedRedirectPath('/dashboard/alertas')).toBe(true)
  })

  it('rejects paths not in whitelist', () => {
    expect(isAllowedRedirectPath('/unknown-path')).toBe(false)
    expect(isAllowedRedirectPath('/api/admin/users')).toBe(false)
  })

  it('handles edge cases', () => {
    expect(isAllowedRedirectPath('')).toBe(false)
    expect(isAllowedRedirectPath('   ')).toBe(false)
    expect(isAllowedRedirectPath(null as unknown as string)).toBe(false)
    expect(isAllowedRedirectPath(undefined as unknown as string)).toBe(false)
  })
})
