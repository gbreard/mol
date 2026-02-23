import { describe, it, expect } from 'vitest'
import * as fs from 'fs'
import * as path from 'path'

/**
 * S-03: RLS + API Route Auth verification.
 *
 * Tables WITH correct RLS (verified in migration):
 * - ofertas_dashboard, ofertas_skills, skills, ocupaciones_esco (public read, service_role write)
 * - usuarios, busquedas_guardadas, intereses, alertas (user/org-scoped)
 * - issues, issue_comments, issue_attachments (author+admin scoped)
 * - esco_argentino (public read, admin/service_role write — fixed in 014)
 * - sistema_estado (public read, admin/service_role write — fixed in 014)
 *
 * API routes requiring auth:
 * - /api/esco-argentino POST/PATCH/DELETE → requireAdmin
 * - /api/admin/* → requireAdmin
 * - /api/worker-profiles → requireAuth
 * - /api/consolidated-profiles POST → requireAdmin
 */

const TABLES_WITH_RLS = [
  'esco_argentino',
  'sistema_estado',
  'usuarios',
  'busquedas_guardadas',
  'intereses',
  'alertas',
  'issues',
  'issue_comments',
  'issue_attachments',
]

const PUBLIC_READ_ONLY_TABLES = [
  'ofertas_dashboard',
  'ofertas_skills',
  'skills',
  'ocupaciones_esco',
]

describe('S-03: RLS-aware data access patterns', () => {
  it('should document which tables have RLS', () => {
    expect(TABLES_WITH_RLS).toContain('esco_argentino')
    expect(TABLES_WITH_RLS).toContain('sistema_estado')
    expect(TABLES_WITH_RLS).toContain('usuarios')
    expect(TABLES_WITH_RLS).toContain('issues')
  })

  it('public tables should be read-only via anon key', () => {
    const supabasePath = path.resolve(__dirname, '../../lib/supabase.ts')
    const content = fs.readFileSync(supabasePath, 'utf-8')

    // ofertas_dashboard should only be used with .select(), never .insert/.update/.delete
    const ofertasMutations = content.match(
      /from\(['"]ofertas_dashboard['"]\)\s*\.\s*(insert|update|delete|upsert)/g
    )
    expect(ofertasMutations).toBeNull()
  })

  it('issues table should use authenticated user for inserts', () => {
    const supabasePath = path.resolve(__dirname, '../../lib/supabase.ts')
    const content = fs.readFileSync(supabasePath, 'utf-8')

    expect(content).toContain('createIssue')
    expect(content).toMatch(/autor_id|autor_email/)
  })

  it('admin API routes should use service_role_key', () => {
    const adminRoutes = [
      path.resolve(__dirname, '../../app/api/admin/stats/route.ts'),
      path.resolve(__dirname, '../../app/api/admin/users/route.ts'),
    ]

    adminRoutes.forEach((routePath) => {
      if (fs.existsSync(routePath)) {
        const content = fs.readFileSync(routePath, 'utf-8')
        expect(content).toContain('SUPABASE_SERVICE_ROLE_KEY')
        expect(content).not.toMatch(/NEXT_PUBLIC_SUPABASE_ANON_KEY.*admin\.auth/)
      }
    })
  })

  it('lib/api-auth.ts should exist with requireAuth and requireAdmin', () => {
    const authPath = path.resolve(__dirname, '../../lib/api-auth.ts')
    expect(fs.existsSync(authPath)).toBe(true)

    const content = fs.readFileSync(authPath, 'utf-8')
    expect(content).toContain('export async function requireAuth')
    expect(content).toContain('export async function requireAdmin')
    expect(content).toContain('export function isAuthError')
  })

  it('write API routes should use requireAdmin or requireAuth', () => {
    const routeChecks: { path: string; guard: string }[] = [
      { path: '../../app/api/esco-argentino/route.ts', guard: 'requireAdmin' },
      { path: '../../app/api/admin/users/route.ts', guard: 'requireAdmin' },
      { path: '../../app/api/admin/stats/route.ts', guard: 'requireAdmin' },
      { path: '../../app/api/admin/architecture-metrics/route.ts', guard: 'requireAdmin' },
      { path: '../../app/api/worker-profiles/route.ts', guard: 'requireAuth' },
      { path: '../../app/api/consolidated-profiles/route.ts', guard: 'requireAdmin' },
    ]

    routeChecks.forEach(({ path: routeRelPath, guard }) => {
      const routePath = path.resolve(__dirname, routeRelPath)
      if (fs.existsSync(routePath)) {
        const content = fs.readFileSync(routePath, 'utf-8')
        expect(content).toContain(guard)
        expect(content).toContain('isAuthError')
      }
    })
  })

  it('SQL migration 014 should fix esco_argentino and sistema_estado RLS', () => {
    const migrationPath = path.resolve(__dirname, '../../../sql/014_rls_data_tables.sql')
    expect(fs.existsSync(migrationPath)).toBe(true)

    const content = fs.readFileSync(migrationPath, 'utf-8')
    expect(content).toContain('esco_argentino')
    expect(content).toContain('sistema_estado')
    expect(content).toContain('is_platform_admin')
    expect(content).toContain('ENABLE ROW LEVEL SECURITY')
  })
})
