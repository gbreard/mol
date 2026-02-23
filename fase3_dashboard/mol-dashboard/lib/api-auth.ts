import { createServerClient as createSupabaseServerClient, type CookieOptions } from '@supabase/ssr'
import { NextRequest, NextResponse } from 'next/server'
import { type User } from '@supabase/supabase-js'
import {
  rateLimit,
  rateLimitResponse,
  getClientIp,
  type RateLimitTier,
} from './rate-limit'

export interface AuthResult {
  user: User
  role: string
}

/**
 * Apply rate limit to a public route (no auth required).
 * Returns `null` when the request is allowed, or a 429 NextResponse to return
 * immediately.
 */
export function requireRateLimit(
  request: NextRequest,
  tier: RateLimitTier = 'public',
): NextResponse | null {
  const ip = getClientIp(request)
  const result = rateLimit(ip, tier)
  if (!result.success) return rateLimitResponse(result)
  return null
}

/**
 * Authenticate a request by reading Supabase session cookies.
 * Rate-limited BEFORE touching Supabase (blocks floods early).
 * Returns AuthResult on success, or a NextResponse(401/429) on failure.
 */
export async function requireAuth(
  request: NextRequest
): Promise<AuthResult | NextResponse> {
  // Rate limit first — before any Supabase call
  const ip = getClientIp(request)
  const rl = rateLimit(ip, 'authenticated')
  if (!rl.success) return rateLimitResponse(rl)

  const supabase = createSupabaseServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(_cookiesToSet: { name: string; value: string; options: CookieOptions }[]) {
          // API routes don't need to refresh cookies — middleware handles that
        },
      },
    }
  )

  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 401 })
  }

  const role = (user.user_metadata?.role as string) || 'viewer'
  return { user, role }
}

/**
 * Authenticate + verify admin role (admin or super_admin).
 * Rate-limited at the `admin` tier BEFORE auth check.
 * Returns AuthResult on success, NextResponse(401/403/429) on failure.
 */
export async function requireAdmin(
  request: NextRequest
): Promise<AuthResult | NextResponse> {
  // Rate limit at admin tier first
  const ip = getClientIp(request)
  const rl = rateLimit(ip, 'admin')
  if (!rl.success) return rateLimitResponse(rl)

  // Auth check (skips the authenticated-tier limit since we already checked admin tier)
  const supabase = createSupabaseServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(_cookiesToSet: { name: string; value: string; options: CookieOptions }[]) {
          // API routes don't need to refresh cookies — middleware handles that
        },
      },
    }
  )

  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 401 })
  }

  const role = (user.user_metadata?.role as string) || 'viewer'

  if (role !== 'admin' && role !== 'super_admin') {
    return NextResponse.json({ error: 'Acceso denegado: se requiere rol admin' }, { status: 403 })
  }

  return { user, role }
}

/**
 * Type guard: true when the auth result is an error response.
 */
export function isAuthError(result: AuthResult | NextResponse): result is NextResponse {
  return result instanceof NextResponse
}
