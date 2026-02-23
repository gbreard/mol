import { describe, it, expect, beforeEach } from 'vitest'
import { rateLimit, rateLimitResponse, getClientIp, _resetStore } from '@/lib/rate-limit'
import { NextRequest } from 'next/server'

beforeEach(() => {
  _resetStore()
})

describe('rateLimit()', () => {
  it('allows requests within the limit', () => {
    for (let i = 0; i < 30; i++) {
      const result = rateLimit('test-ip', 'public')
      expect(result.success).toBe(true)
    }
  })

  it('blocks when limit is exceeded', () => {
    // Exhaust the 30-request public limit
    for (let i = 0; i < 30; i++) {
      rateLimit('test-ip', 'public')
    }

    const blocked = rateLimit('test-ip', 'public')
    expect(blocked.success).toBe(false)
    expect(blocked.remaining).toBe(0)
  })

  it('tracks keys independently', () => {
    for (let i = 0; i < 30; i++) {
      rateLimit('ip-a', 'public')
    }

    const blockedA = rateLimit('ip-a', 'public')
    const allowedB = rateLimit('ip-b', 'public')

    expect(blockedA.success).toBe(false)
    expect(allowedB.success).toBe(true)
  })

  it('respects tier limits: public=30, authenticated=60, admin=120', () => {
    // Public: 30
    for (let i = 0; i < 30; i++) rateLimit('pub', 'public')
    expect(rateLimit('pub', 'public').success).toBe(false)

    // Authenticated: 60
    for (let i = 0; i < 60; i++) rateLimit('auth', 'authenticated')
    expect(rateLimit('auth', 'authenticated').success).toBe(false)

    // Admin: 120
    for (let i = 0; i < 120; i++) rateLimit('adm', 'admin')
    expect(rateLimit('adm', 'admin').success).toBe(false)
  })

  it('returns correct remaining count', () => {
    const first = rateLimit('ip', 'public')
    expect(first.remaining).toBe(29)

    const second = rateLimit('ip', 'public')
    expect(second.remaining).toBe(28)
  })

  it('returns a reset timestamp in the future', () => {
    const result = rateLimit('ip', 'public')
    expect(result.reset).toBeGreaterThan(Date.now())
  })
})

describe('rateLimitResponse()', () => {
  it('returns 429 with correct headers', () => {
    const result = {
      success: false,
      limit: 30,
      remaining: 0,
      reset: Date.now() + 60_000,
    }

    const response = rateLimitResponse(result)

    expect(response.status).toBe(429)
    expect(response.headers.get('X-RateLimit-Limit')).toBe('30')
    expect(response.headers.get('X-RateLimit-Remaining')).toBe('0')
    expect(response.headers.get('X-RateLimit-Reset')).toBeTruthy()
    expect(response.headers.get('Retry-After')).toBeTruthy()
  })
})

describe('getClientIp()', () => {
  it('extracts IP from X-Forwarded-For', () => {
    const request = new NextRequest('http://localhost/api/test', {
      headers: { 'x-forwarded-for': '1.2.3.4, 5.6.7.8' },
    })
    expect(getClientIp(request)).toBe('1.2.3.4')
  })

  it('falls back to X-Real-IP', () => {
    const request = new NextRequest('http://localhost/api/test', {
      headers: { 'x-real-ip': '9.8.7.6' },
    })
    expect(getClientIp(request)).toBe('9.8.7.6')
  })

  it('defaults to 127.0.0.1 when no header', () => {
    const request = new NextRequest('http://localhost/api/test')
    expect(getClientIp(request)).toBe('127.0.0.1')
  })
})
