import { type NextRequest, NextResponse } from 'next/server'
import { updateSession } from '@/lib/supabase/middleware'

// Rutas publicas que no requieren autenticacion
const publicRoutes = ['/login', '/auth/callback', '/registro']

// Rutas que requieren rol especifico
const adminRoutes = ['/admin']
const superAdminRoutes = ['/superadmin']

export async function middleware(request: NextRequest) {
  const { response, user, supabase } = await updateSession(request)
  const { pathname } = request.nextUrl

  // Rutas publicas - permitir acceso
  if (publicRoutes.some(route => pathname.startsWith(route))) {
    // Si ya esta logueado y va a /login, redirigir a home
    if (user && pathname === '/login') {
      return NextResponse.redirect(new URL('/', request.url))
    }
    return response
  }

  // Rutas protegidas - requieren autenticacion
  if (!user) {
    const redirectUrl = new URL('/login', request.url)
    redirectUrl.searchParams.set('redirectTo', pathname)
    return NextResponse.redirect(redirectUrl)
  }

  // Verificar permisos para rutas admin/superadmin
  if (adminRoutes.some(route => pathname.startsWith(route)) ||
      superAdminRoutes.some(route => pathname.startsWith(route))) {

    // Obtener rol del usuario
    const { data: usuario } = await supabase
      .from('usuarios')
      .select('rol')
      .eq('auth_id', user.id)
      .single()

    if (!usuario) {
      // Usuario autenticado pero sin perfil - redirigir a home
      return NextResponse.redirect(new URL('/', request.url))
    }

    // Verificar acceso a rutas superadmin
    if (superAdminRoutes.some(route => pathname.startsWith(route))) {
      if (usuario.rol !== 'platform_admin') {
        return NextResponse.redirect(new URL('/', request.url))
      }
    }

    // Verificar acceso a rutas admin
    if (adminRoutes.some(route => pathname.startsWith(route))) {
      if (!['platform_admin', 'admin'].includes(usuario.rol)) {
        return NextResponse.redirect(new URL('/', request.url))
      }
    }
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, etc)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
