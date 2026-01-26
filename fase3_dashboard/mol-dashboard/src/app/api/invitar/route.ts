import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const supabase = await createClient()

    // Verificar que el usuario esta autenticado
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json(
        { error: 'No autenticado' },
        { status: 401 }
      )
    }

    // Obtener datos del usuario actual
    const { data: currentUser, error: userError } = await supabase
      .from('usuarios')
      .select('id, rol, organizacion_id')
      .eq('auth_id', user.id)
      .single()

    if (userError || !currentUser) {
      return NextResponse.json(
        { error: 'Usuario no encontrado' },
        { status: 404 }
      )
    }

    // Verificar permisos - solo admin y platform_admin pueden invitar
    if (!['platform_admin', 'admin'].includes(currentUser.rol)) {
      return NextResponse.json(
        { error: 'Sin permisos para invitar usuarios' },
        { status: 403 }
      )
    }

    // Obtener datos de la solicitud
    const body = await request.json()
    const { email, rol } = body

    // Validar email
    if (!email || !email.includes('@')) {
      return NextResponse.json(
        { error: 'Email invalido' },
        { status: 400 }
      )
    }

    // Validar rol
    const rolesPermitidos = ['admin', 'analista', 'lector']
    if (!rol || !rolesPermitidos.includes(rol)) {
      return NextResponse.json(
        { error: 'Rol invalido. Debe ser: admin, analista o lector' },
        { status: 400 }
      )
    }

    // Un admin no puede crear otro admin (solo platform_admin puede)
    if (rol === 'admin' && currentUser.rol !== 'platform_admin') {
      return NextResponse.json(
        { error: 'Solo SuperAdmin puede crear administradores' },
        { status: 403 }
      )
    }

    // Verificar que el email no este ya registrado
    const { data: existingUser } = await supabase
      .from('usuarios')
      .select('id')
      .eq('email', email)
      .single()

    if (existingUser) {
      return NextResponse.json(
        { error: 'Este email ya tiene una cuenta' },
        { status: 409 }
      )
    }

    // Verificar invitacion pendiente para este email
    const { data: existingInvite } = await supabase
      .from('invitaciones')
      .select('id')
      .eq('email', email)
      .eq('usado', false)
      .gt('expires_at', new Date().toISOString())
      .single()

    if (existingInvite) {
      return NextResponse.json(
        { error: 'Ya existe una invitacion pendiente para este email' },
        { status: 409 }
      )
    }

    // Crear invitacion
    const { data: invitacion, error: inviteError } = await supabase
      .from('invitaciones')
      .insert({
        email,
        rol,
        organizacion_id: currentUser.organizacion_id,
        invitado_por: currentUser.id,
      })
      .select('id, token')
      .single()

    if (inviteError) {
      console.error('Error creando invitacion:', inviteError)
      return NextResponse.json(
        { error: 'Error creando invitacion' },
        { status: 500 }
      )
    }

    // Construir URL de invitacion
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || request.headers.get('origin') || ''
    const inviteUrl = `${baseUrl}/registro?token=${invitacion.token}`

    // TODO: Enviar email con el link (implementar con servicio de email)
    // Por ahora, devolver el link para copiar manualmente

    return NextResponse.json({
      success: true,
      inviteUrl,
      message: 'Invitacion creada. Comparte este link con el usuario.',
      invitacion_id: invitacion.id,
    })

  } catch (error) {
    console.error('Error en API invitar:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
}

// GET - Listar invitaciones pendientes
export async function GET() {
  try {
    const supabase = await createClient()

    // Verificar autenticacion
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json(
        { error: 'No autenticado' },
        { status: 401 }
      )
    }

    // Obtener usuario actual
    const { data: currentUser } = await supabase
      .from('usuarios')
      .select('id, rol, organizacion_id')
      .eq('auth_id', user.id)
      .single()

    if (!currentUser || !['platform_admin', 'admin'].includes(currentUser.rol)) {
      return NextResponse.json(
        { error: 'Sin permisos' },
        { status: 403 }
      )
    }

    // Obtener invitaciones de la organizacion
    const { data: invitaciones, error } = await supabase
      .from('invitaciones')
      .select('id, email, rol, created_at, expires_at, usado')
      .eq('organizacion_id', currentUser.organizacion_id)
      .order('created_at', { ascending: false })

    if (error) {
      return NextResponse.json(
        { error: 'Error obteniendo invitaciones' },
        { status: 500 }
      )
    }

    return NextResponse.json({ invitaciones })

  } catch (error) {
    console.error('Error en GET invitaciones:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
}
