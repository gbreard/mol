import { createClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';

// Cliente con service_role para acceder a auth.users
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  }
);

export async function GET(request: NextRequest) {
  try {
    // Verificar que el usuario está autenticado (básico)
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json({ error: 'No autorizado' }, { status: 401 });
    }

    // Obtener todos los usuarios de auth
    const { data: { users }, error } = await supabaseAdmin.auth.admin.listUsers();

    if (error) {
      console.error('Error listando usuarios:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // Mapear a formato simplificado
    const usuariosMapeados = users.map(user => ({
      id: user.id,
      email: user.email || '',
      role: user.user_metadata?.role || 'viewer',
      display_name: user.user_metadata?.display_name || user.email?.split('@')[0] || '',
      created_at: user.created_at,
      last_sign_in_at: user.last_sign_in_at,
      email_confirmed: !!user.email_confirmed_at
    }));

    return NextResponse.json({ users: usuariosMapeados });
  } catch (err: any) {
    console.error('Error en API users:', err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password, role, display_name } = body;

    if (!email || !password) {
      return NextResponse.json({ error: 'Email y password requeridos' }, { status: 400 });
    }

    // Crear usuario con admin API
    const { data, error } = await supabaseAdmin.auth.admin.createUser({
      email,
      password,
      email_confirm: true, // Confirmar email automáticamente
      user_metadata: {
        role: role || 'viewer',
        display_name: display_name || email.split('@')[0]
      }
    });

    if (error) {
      console.error('Error creando usuario:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({
      user: {
        id: data.user.id,
        email: data.user.email,
        role: data.user.user_metadata?.role,
        display_name: data.user.user_metadata?.display_name
      }
    });
  } catch (err: any) {
    console.error('Error en API create user:', err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
