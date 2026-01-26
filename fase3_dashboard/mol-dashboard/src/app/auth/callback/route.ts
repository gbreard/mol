import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const redirectTo = searchParams.get('redirectTo') || '/'
  const errorParam = searchParams.get('error')
  const errorDescription = searchParams.get('error_description')

  // Handle OAuth errors
  if (errorParam) {
    console.error('OAuth error:', errorParam, errorDescription)
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent(errorDescription || errorParam)}`
    )
  }

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)

    if (!error) {
      // Successful auth - redirect to intended destination
      return NextResponse.redirect(`${origin}${redirectTo}`)
    }

    console.error('Exchange code error:', error)
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent('Error al procesar autenticacion')}`
    )
  }

  // No code provided - redirect to login
  return NextResponse.redirect(`${origin}/login?error=auth_failed`)
}
