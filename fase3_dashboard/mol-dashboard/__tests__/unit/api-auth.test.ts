import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

// Mock @supabase/ssr before importing the module under test
const mockGetUser = vi.fn()

vi.mock('@supabase/ssr', () => ({
  createServerClient: () => ({
    auth: {
      getUser: mockGetUser,
    },
  }),
}))

// Import AFTER mocks are set up
import { requireAuth, requireAdmin, isAuthError } from '../../lib/api-auth'

function makeRequest(url = 'http://localhost:3000/api/test'): NextRequest {
  return new NextRequest(url)
}

describe('api-auth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('requireAuth', () => {
    it('returns 401 when no session', async () => {
      mockGetUser.mockResolvedValue({ data: { user: null }, error: null })

      const result = await requireAuth(makeRequest())
      expect(isAuthError(result)).toBe(true)
      // Cast to get status
      const response = result as Response
      expect(response.status).toBe(401)
    })

    it('returns 401 on auth error', async () => {
      mockGetUser.mockResolvedValue({
        data: { user: null },
        error: { message: 'invalid token' },
      })

      const result = await requireAuth(makeRequest())
      expect(isAuthError(result)).toBe(true)
      const response = result as Response
      expect(response.status).toBe(401)
    })

    it('returns AuthResult with user on valid session', async () => {
      const fakeUser = {
        id: 'user-123',
        email: 'test@example.com',
        user_metadata: { role: 'analyst' },
      }
      mockGetUser.mockResolvedValue({ data: { user: fakeUser }, error: null })

      const result = await requireAuth(makeRequest())
      expect(isAuthError(result)).toBe(false)
      if (!isAuthError(result)) {
        expect(result.user.id).toBe('user-123')
        expect(result.role).toBe('analyst')
      }
    })

    it('defaults role to viewer when not set', async () => {
      const fakeUser = {
        id: 'user-456',
        email: 'noob@example.com',
        user_metadata: {},
      }
      mockGetUser.mockResolvedValue({ data: { user: fakeUser }, error: null })

      const result = await requireAuth(makeRequest())
      expect(isAuthError(result)).toBe(false)
      if (!isAuthError(result)) {
        expect(result.role).toBe('viewer')
      }
    })
  })

  describe('requireAdmin', () => {
    it('returns 401 when not authenticated', async () => {
      mockGetUser.mockResolvedValue({ data: { user: null }, error: null })

      const result = await requireAdmin(makeRequest())
      expect(isAuthError(result)).toBe(true)
      const response = result as Response
      expect(response.status).toBe(401)
    })

    it('returns 403 for non-admin user', async () => {
      const fakeUser = {
        id: 'user-789',
        email: 'viewer@example.com',
        user_metadata: { role: 'viewer' },
      }
      mockGetUser.mockResolvedValue({ data: { user: fakeUser }, error: null })

      const result = await requireAdmin(makeRequest())
      expect(isAuthError(result)).toBe(true)
      const response = result as Response
      expect(response.status).toBe(403)
    })

    it('returns 403 for analyst role', async () => {
      const fakeUser = {
        id: 'user-101',
        email: 'analyst@example.com',
        user_metadata: { role: 'analyst' },
      }
      mockGetUser.mockResolvedValue({ data: { user: fakeUser }, error: null })

      const result = await requireAdmin(makeRequest())
      expect(isAuthError(result)).toBe(true)
      const response = result as Response
      expect(response.status).toBe(403)
    })

    it('returns AuthResult for admin role', async () => {
      const fakeUser = {
        id: 'admin-1',
        email: 'admin@example.com',
        user_metadata: { role: 'admin' },
      }
      mockGetUser.mockResolvedValue({ data: { user: fakeUser }, error: null })

      const result = await requireAdmin(makeRequest())
      expect(isAuthError(result)).toBe(false)
      if (!isAuthError(result)) {
        expect(result.user.id).toBe('admin-1')
        expect(result.role).toBe('admin')
      }
    })

    it('returns AuthResult for super_admin role', async () => {
      const fakeUser = {
        id: 'sadmin-1',
        email: 'superadmin@example.com',
        user_metadata: { role: 'super_admin' },
      }
      mockGetUser.mockResolvedValue({ data: { user: fakeUser }, error: null })

      const result = await requireAdmin(makeRequest())
      expect(isAuthError(result)).toBe(false)
      if (!isAuthError(result)) {
        expect(result.role).toBe('super_admin')
      }
    })
  })

  describe('isAuthError', () => {
    it('returns true for NextResponse', async () => {
      mockGetUser.mockResolvedValue({ data: { user: null }, error: null })
      const result = await requireAuth(makeRequest())
      expect(isAuthError(result)).toBe(true)
    })

    it('returns false for AuthResult', async () => {
      const fakeUser = {
        id: 'u1',
        email: 'a@b.com',
        user_metadata: { role: 'admin' },
      }
      mockGetUser.mockResolvedValue({ data: { user: fakeUser }, error: null })
      const result = await requireAuth(makeRequest())
      expect(isAuthError(result)).toBe(false)
    })
  })
})
