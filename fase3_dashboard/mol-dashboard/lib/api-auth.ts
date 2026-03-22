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

// Dev bypass: usuario admin mock sin Supabase real
const DEV_MOCK_USER = {
  id: 'dev-mock-user-id',
  email: 'dev@mol.local',
  user_metadata: { role: 'admin', plan: 'enterprise' },
  app_metadata: {},
  aud: 'authenticated',
  created_at: new Date().toISOString(),
} as unknown as User

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
  if (process.env.DEV_MOCK_AUTH === 'true') {
    return { user: DEV_MOCK_USER, role: 'admin' }
  }

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
  if (process.env.DEV_MOCK_AUTH === 'true') {
    return { user: DEV_MOCK_USER, role: 'admin' }
  }

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
 * Authenticate + verify dashboard access (admin, subscriber, or active trial).
 * Rate-limited at the `authenticated` tier.
 * Returns AuthResult on success, NextResponse(401/403/429) on failure.
 */
export async function requireSubscriber(
  request: NextRequest
): Promise<AuthResult | NextResponse> {
  if (process.env.DEV_MOCK_AUTH === 'true') {
    return { user: DEV_MOCK_USER, role: 'admin' }
  }

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
          // API routes don't need to refresh cookies
        },
      },
    }
  )

  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    return NextResponse.json({ error: 'No autorizado' }, { status: 401 })
  }

  const role = (user.user_metadata?.role as string) || 'viewer'
  const plan = (user.user_metadata?.plan as string) || 'free'
  const trialStartDate = user.user_metadata?.trial_start_date as string | undefined

  // Admins always pass
  if (role === 'admin' || role === 'super_admin') {
    return { user, role }
  }

  // Paid subscribers pass
  if (plan === 'pro' || plan === 'enterprise') {
    return { user, role }
  }

  // Active trial passes
  if (plan === 'trial' && trialStartDate) {
    const start = new Date(trialStartDate)
    const diffDays = (Date.now() - start.getTime()) / (1000 * 60 * 60 * 24)
    if (diffDays < 7) {
      return { user, role }
    }
  }

  return NextResponse.json(
    { error: 'Acceso denegado: se requiere suscripcion activa o trial vigente' },
    { status: 403 }
  )
}

/**
 * Type guard: true when the auth result is an error response.
 */
export function isAuthError(result: AuthResult | NextResponse): result is NextResponse {
  return result instanceof NextResponse
}
