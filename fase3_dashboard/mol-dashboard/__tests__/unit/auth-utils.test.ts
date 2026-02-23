import { describe, it, expect } from 'vitest'
import {
  isAllowedRedirectPath,
  getSafeRedirectPath,
  ALLOWED_REDIRECT_PATHS,
} from '../../lib/auth-utils'

describe('auth-utils', () => {
  describe('ALLOWED_REDIRECT_PATHS', () => {
    it('contains expected routes', () => {
      expect(ALLOWED_REDIRECT_PATHS).toContain('/home')
      expect(ALLOWED_REDIRECT_PATHS).toContain('/dashboard')
      expect(ALLOWED_REDIRECT_PATHS).toContain('/admin')
      expect(ALLOWED_REDIRECT_PATHS).toContain('/cuenta')
    })

    it('does not contain API routes', () => {
      const hasApi = ALLOWED_REDIRECT_PATHS.some((p) => p.startsWith('/api'))
      expect(hasApi).toBe(false)
    })
  })

  describe('isAllowedRedirectPath', () => {
    it('accepts all defined allowed paths', () => {
      ALLOWED_REDIRECT_PATHS.forEach((path) => {
        expect(isAllowedRedirectPath(path)).toBe(true)
      })
    })

    it('accepts sub-paths of allowed paths', () => {
      expect(isAllowedRedirectPath('/dashboard/alertas')).toBe(true)
      expect(isAllowedRedirectPath('/admin/configuracion')).toBe(true)
      expect(isAllowedRedirectPath('/cuenta/facturacion')).toBe(true)
    })

    it('rejects dangerous schemes', () => {
      expect(isAllowedRedirectPath('javascript:alert(1)')).toBe(false)
      expect(isAllowedRedirectPath('data:text/html,<h1>XSS</h1>')).toBe(false)
      expect(isAllowedRedirectPath('vbscript:msgbox')).toBe(false)
    })

    it('rejects external URLs', () => {
      expect(isAllowedRedirectPath('https://evil.com/dashboard')).toBe(false)
      expect(isAllowedRedirectPath('http://evil.com')).toBe(false)
      expect(isAllowedRedirectPath('ftp://evil.com')).toBe(false)
    })

    it('rejects protocol-relative URLs', () => {
      expect(isAllowedRedirectPath('//evil.com')).toBe(false)
      expect(isAllowedRedirectPath('//evil.com/dashboard')).toBe(false)
      expect(isAllowedRedirectPath('///evil.com')).toBe(false)
    })

    it('rejects backslash tricks', () => {
      expect(isAllowedRedirectPath('/\\evil.com')).toBe(false)
    })

    it('rejects paths without leading slash', () => {
      expect(isAllowedRedirectPath('dashboard')).toBe(false)
      expect(isAllowedRedirectPath('home')).toBe(false)
    })
  })

  describe('getSafeRedirectPath', () => {
    it('returns path if valid', () => {
      expect(getSafeRedirectPath('/dashboard')).toBe('/dashboard')
      expect(getSafeRedirectPath('/admin')).toBe('/admin')
    })

    it('defaults to /home for invalid paths', () => {
      expect(getSafeRedirectPath('https://evil.com')).toBe('/home')
      expect(getSafeRedirectPath(null)).toBe('/home')
      expect(getSafeRedirectPath(undefined)).toBe('/home')
      expect(getSafeRedirectPath('')).toBe('/home')
    })

    it('trims whitespace', () => {
      expect(getSafeRedirectPath('  /dashboard  ')).toBe('/dashboard')
    })
  })
})
