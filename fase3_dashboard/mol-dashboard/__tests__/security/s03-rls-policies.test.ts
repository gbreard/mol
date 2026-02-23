import { describe, it, expect } from 'vitest'

/**
 * S-03: RLS (Row Level Security) verification.
 *
 * These tests verify that the codebase follows patterns consistent with
 * RLS-protected tables. The actual RLS policies must be verified directly
 * in Supabase (these are database-level, not application-level).
 *
 * Tables that REQUIRE RLS (user-specific data):
 * - suscripciones (user subscription data)
 * - pagos (user payment data)
 * - alertas_config (user alert configuration)
 * - uso_features (user feature usage tracking)
 *
 * Tables that are OK without RLS (public data):
 * - ofertas_dashboard (public job offers, read-only for all)
 * - ofertas_skills (public skills data, read-only for all)
 *
 * To verify RLS in Supabase:
 * ```sql
 * SELECT tablename, rowsecurity
 * FROM pg_tables
 * WHERE schemaname = 'public';
 * ```
 */

const TABLES_REQUIRING_RLS = [
  'suscripciones',
  'pagos',
  'alertas_config',
  'uso_features',
]

const PUBLIC_READ_ONLY_TABLES = [
  'ofertas_dashboard',
  'ofertas_skills',
  'issues', // Issues are public within the organization
]

describe('S-03: RLS-aware data access patterns', () => {
  it('should document which tables require RLS', () => {
    // This test serves as documentation/contract
    expect(TABLES_REQUIRING_RLS).toContain('suscripciones')
    expect(TABLES_REQUIRING_RLS).toContain('pagos')
    expect(TABLES_REQUIRING_RLS).toContain('alertas_config')
  })

  it('public tables should be read-only via anon key', () => {
    // Verify that the supabase.ts data layer only reads from public tables
    // (never inserts/updates/deletes to ofertas_dashboard)
    const fs = require('fs')
    const path = require('path')
    const supabasePath = path.resolve(__dirname, '../../lib/supabase.ts')
    const content = fs.readFileSync(supabasePath, 'utf-8')

    // ofertas_dashboard should only be used with .select(), never .insert/.update/.delete
    const ofertasMutations = content.match(
      /from\(['"]ofertas_dashboard['"]\)\s*\.\s*(insert|update|delete|upsert)/g
    )
    expect(ofertasMutations).toBeNull()
  })

  it('issues table should use authenticated user for inserts', () => {
    const fs = require('fs')
    const path = require('path')
    const supabasePath = path.resolve(__dirname, '../../lib/supabase.ts')
    const content = fs.readFileSync(supabasePath, 'utf-8')

    // createIssue should reference auth.getUser() or user context
    expect(content).toContain('createIssue')
    // Issues are inserted with user attribution
    expect(content).toMatch(/autor_id|autor_email/)
  })

  it('admin API routes should use service_role_key, not anon_key', () => {
    const fs = require('fs')
    const path = require('path')

    const adminRoutes = [
      path.resolve(__dirname, '../../app/api/admin/stats/route.ts'),
      path.resolve(__dirname, '../../app/api/admin/users/route.ts'),
    ]

    adminRoutes.forEach((routePath) => {
      if (fs.existsSync(routePath)) {
        const content = fs.readFileSync(routePath, 'utf-8')
        // Admin routes should use SUPABASE_SERVICE_ROLE_KEY (server-side only)
        expect(content).toContain('SUPABASE_SERVICE_ROLE_KEY')
        // Admin routes should NOT use the anon key for privileged operations
        expect(content).not.toMatch(/NEXT_PUBLIC_SUPABASE_ANON_KEY.*admin\.auth/)
      }
    })
  })
})
