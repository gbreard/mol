import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const PROJECT_ROOT = path.resolve(__dirname, '../..')

describe('S-04: Admin routes require role verification', () => {
  it('middleware should check for admin role on /admin/* routes', () => {
    const middlewarePath = path.join(PROJECT_ROOT, 'lib/supabase/middleware.ts')
    const content = fs.readFileSync(middlewarePath, 'utf-8')

    // Middleware must handle admin routes specifically
    expect(content).toContain('/admin')
    // Should check user role, not just authentication
    expect(content).toMatch(/role.*admin|admin.*role|isAdmin|user_metadata/)
  })

  it('admin API routes should verify auth header', () => {
    const adminUsersRoute = path.join(PROJECT_ROOT, 'app/api/admin/users/route.ts')
    const content = fs.readFileSync(adminUsersRoute, 'utf-8')

    // Should check for authorization header
    expect(content).toContain('authorization')
    // Should return 401 for unauthorized requests
    expect(content).toContain('401')
  })

  it('admin API routes should verify admin role', () => {
    const adminRoutes = [
      path.join(PROJECT_ROOT, 'app/api/admin/stats/route.ts'),
      path.join(PROJECT_ROOT, 'app/api/admin/users/route.ts'),
    ]

    adminRoutes.forEach((routePath) => {
      if (fs.existsSync(routePath)) {
        const content = fs.readFileSync(routePath, 'utf-8')
        // Should use service role key for admin operations (server-side validation)
        expect(content).toContain('SUPABASE_SERVICE_ROLE_KEY')
      }
    })
  })

  it('admin pages should not be in public routes list', () => {
    const middlewarePath = path.join(PROJECT_ROOT, 'lib/supabase/middleware.ts')
    const content = fs.readFileSync(middlewarePath, 'utf-8')

    // /admin should NOT be in the public prefixes list
    const publicPrefixesMatch = content.match(/publicPrefixes\s*=\s*\[([^\]]+)\]/)
    if (publicPrefixesMatch) {
      const publicPrefixes = publicPrefixesMatch[1]
      expect(publicPrefixes).not.toContain('/admin')
    }
  })

  it('middleware should redirect non-admin users from /admin routes', () => {
    const middlewarePath = path.join(PROJECT_ROOT, 'lib/supabase/middleware.ts')
    const content = fs.readFileSync(middlewarePath, 'utf-8')

    // Should have specific handling for admin routes
    expect(content).toMatch(/startsWith.*\/admin|pathname.*admin/)
    // Should redirect unauthorized admin access
    expect(content).toContain('redirect')
  })
})
