import { createServerClient as createSupabaseServerClient, type CookieOptions } from '@supabase/ssr'
import { NextRequest, NextResponse } from 'next/server'
import { type User } from '@supabase/supabase-js'

export interface AuthResult {
  user: User
  role: string
}

/**
 * Authenticate a request by reading Supabase session cookies.
 * Returns AuthResult on success, or a NextResponse(401) on failure.
 */
export async function requireAuth(
  request: NextRequest
): Promise<AuthResult | NextResponse> {
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
 * Returns AuthResult on success, NextResponse(401) if not authenticated,
 * or NextResponse(403) if not admin.
 */
export async function requireAdmin(
  request: NextRequest
): Promise<AuthResult | NextResponse> {
  const result = await requireAuth(request)
  if (isAuthError(result)) return result

  if (result.role !== 'admin' && result.role !== 'super_admin') {
    return NextResponse.json({ error: 'Acceso denegado: se requiere rol admin' }, { status: 403 })
  }

  return result
}

/**
 * Type guard: true when the auth result is an error response.
 */
export function isAuthError(result: AuthResult | NextResponse): result is NextResponse {
  return result instanceof NextResponse
}
