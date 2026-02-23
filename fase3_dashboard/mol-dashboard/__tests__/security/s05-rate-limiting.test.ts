import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const PROJECT_ROOT = path.resolve(__dirname, '../..')
const API_DIR = path.join(PROJECT_ROOT, 'app/api')

/**
 * Recursively find all route.ts files under a directory.
 */
function findRouteFiles(dir: string): string[] {
  const results: string[] = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      results.push(...findRouteFiles(full))
    } else if (entry.name === 'route.ts') {
      results.push(full)
    }
  }
  return results
}

describe('S-05: All API routes are rate-limited', () => {
  const routeFiles = findRouteFiles(API_DIR)

  it('should find at least 10 API route files', () => {
    expect(routeFiles.length).toBeGreaterThanOrEqual(10)
  })

  routeFiles.forEach((routePath) => {
    const relative = path.relative(PROJECT_ROOT, routePath)

    it(`${relative} uses rate limiting (via api-auth guard or requireRateLimit)`, () => {
      const content = fs.readFileSync(routePath, 'utf-8')

      const hasRateLimit = content.includes('requireRateLimit')
      const hasAuth = content.includes('requireAuth')
      const hasAdmin = content.includes('requireAdmin')

      expect(
        hasRateLimit || hasAuth || hasAdmin,
        `${relative} has no rate-limiting guard (requireRateLimit, requireAuth, or requireAdmin)`,
      ).toBe(true)
    })
  })
})

describe('S-05: Rate limit module exists and exports required API', () => {
  it('lib/rate-limit.ts exports rateLimit, rateLimitResponse, getClientIp', () => {
    const rateLimitPath = path.join(PROJECT_ROOT, 'lib/rate-limit.ts')
    const content = fs.readFileSync(rateLimitPath, 'utf-8')

    expect(content).toContain('export function rateLimit')
    expect(content).toContain('export function rateLimitResponse')
    expect(content).toContain('export function getClientIp')
  })

  it('api-auth.ts imports from rate-limit and exports requireRateLimit', () => {
    const apiAuthPath = path.join(PROJECT_ROOT, 'lib/api-auth.ts')
    const content = fs.readFileSync(apiAuthPath, 'utf-8')

    expect(content).toContain("from './rate-limit'")
    expect(content).toContain('export function requireRateLimit')
    // Both requireAuth and requireAdmin should call rateLimit before auth
    expect(content).toMatch(/rateLimit\(ip.*authenticated/)
    expect(content).toMatch(/rateLimit\(ip.*admin/)
  })
})

describe('S-07: Security headers configured in next.config', () => {
  it('next.config.ts includes required security headers', () => {
    const configPath = path.join(PROJECT_ROOT, 'next.config.ts')
    const content = fs.readFileSync(configPath, 'utf-8')

    expect(content).toContain('X-Frame-Options')
    expect(content).toContain('DENY')
    expect(content).toContain('X-Content-Type-Options')
    expect(content).toContain('nosniff')
    expect(content).toContain('Referrer-Policy')
    expect(content).toContain('strict-origin-when-cross-origin')
  })
})
