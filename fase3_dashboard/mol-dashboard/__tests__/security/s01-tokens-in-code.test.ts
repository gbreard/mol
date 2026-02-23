import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

const PROJECT_ROOT = path.resolve(__dirname, '../..')

// Patterns that indicate hardcoded secrets
const SECRET_PATTERNS = [
  /eyJhbGciOi/, // JWT token prefix (base64 of {"alg":)
  /supabase_service_role_key\s*[:=]\s*["'][^"']+["']/i,
  /SUPABASE_SERVICE_ROLE_KEY\s*[:=]\s*["'][^"']+["']/i,
  /sk_live_[a-zA-Z0-9]+/, // Stripe live key
  /sk_test_[a-zA-Z0-9]+/, // Stripe test key
]

// Patterns for env var values (actual keys, not references)
const HARDCODED_KEY_PATTERNS = [
  // Supabase anon key pattern: starts with eyJ (base64 JWT)
  /['"]eyJ[A-Za-z0-9_-]{20,}['"]/,
  // Supabase URL with actual project ref hardcoded (not env var reference)
  /['"]https:\/\/[a-z]{20}\.supabase\.co['"]/,
]

function getSourceFiles(dir: string): string[] {
  const files: string[] = []
  const entries = fs.readdirSync(dir, { withFileTypes: true })

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    // Skip non-source directories
    if (entry.isDirectory()) {
      if (['node_modules', '.next', '.git', 'coverage', '__tests__', 'e2e'].includes(entry.name)) continue
      files.push(...getSourceFiles(fullPath))
    } else if (/\.(ts|tsx|js|jsx|mjs)$/.test(entry.name) && !entry.name.endsWith('.d.ts')) {
      files.push(fullPath)
    }
  }
  return files
}

describe('S-01: No hardcoded tokens in source code', () => {
  const sourceFiles = getSourceFiles(PROJECT_ROOT)

  it('should have source files to scan', () => {
    expect(sourceFiles.length).toBeGreaterThan(0)
  })

  it('should not contain JWT tokens in source files', () => {
    const violations: { file: string; line: number; pattern: string }[] = []

    for (const file of sourceFiles) {
      const content = fs.readFileSync(file, 'utf-8')
      const lines = content.split('\n')

      lines.forEach((line, idx) => {
        // Skip comments and imports
        if (line.trim().startsWith('//') || line.trim().startsWith('*')) return
        // Skip test files
        if (file.includes('__tests__') || file.includes('.test.')) return

        for (const pattern of SECRET_PATTERNS) {
          if (pattern.test(line)) {
            violations.push({
              file: path.relative(PROJECT_ROOT, file),
              line: idx + 1,
              pattern: pattern.source,
            })
          }
        }
      })
    }

    expect(violations).toEqual([])
  })

  it('should not have hardcoded Supabase keys in source files', () => {
    const violations: { file: string; line: number }[] = []

    for (const file of sourceFiles) {
      const content = fs.readFileSync(file, 'utf-8')
      const lines = content.split('\n')

      lines.forEach((line, idx) => {
        if (line.trim().startsWith('//') || line.trim().startsWith('*')) return
        if (file.includes('__tests__') || file.includes('.test.')) return

        for (const pattern of HARDCODED_KEY_PATTERNS) {
          if (pattern.test(line)) {
            // Allow process.env references — those are fine
            if (line.includes('process.env')) continue
            violations.push({
              file: path.relative(PROJECT_ROOT, file),
              line: idx + 1,
            })
          }
        }
      })
    }

    expect(violations).toEqual([])
  })

  it('should use process.env for Supabase credentials', () => {
    // Check that lib/supabase.ts uses env vars, not hardcoded values
    const supabasePath = path.join(PROJECT_ROOT, 'lib/supabase.ts')
    const content = fs.readFileSync(supabasePath, 'utf-8')

    expect(content).toContain('process.env.NEXT_PUBLIC_SUPABASE_URL')
    expect(content).toContain('process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY')
  })

  it('.gitignore should exclude .env files', () => {
    const gitignorePath = path.join(PROJECT_ROOT, '.gitignore')
    const content = fs.readFileSync(gitignorePath, 'utf-8')

    expect(content).toMatch(/\.env\*/)
  })
})
