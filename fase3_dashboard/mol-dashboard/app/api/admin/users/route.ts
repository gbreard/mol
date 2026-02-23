import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';

// Cliente con service_role para acceder a auth.users (lazy initialization)
let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    console.warn('Supabase admin credentials not configured');
    return null;
  }

  supabaseAdmin = createClient(url, key, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  });

  return supabaseAdmin;
}

export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'Admin API no configurada' }, { status: 503 });
    }

    // Obtener todos los usuarios de auth
    const { data: { users }, error } = await admin.auth.admin.listUsers();

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

export async function PATCH(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'Admin API no configurada' }, { status: 503 });
    }

    const body = await request.json();
    const { userId, role, display_name } = body;

    if (!userId) {
      return NextResponse.json({ error: 'userId requerido' }, { status: 400 });
    }

    const validRoles = ['viewer', 'analyst', 'admin', 'super_admin'];
    if (role && !validRoles.includes(role)) {
      return NextResponse.json({ error: `Rol inválido. Válidos: ${validRoles.join(', ')}` }, { status: 400 });
    }

    // Build metadata update — updateUserById MERGES metadata (doesn't overwrite unset fields)
    const metadata: Record<string, string> = {};
    if (role) metadata.role = role;
    if (display_name !== undefined) metadata.display_name = display_name;

    if (Object.keys(metadata).length === 0) {
      return NextResponse.json({ error: 'Nada que actualizar (enviar role y/o display_name)' }, { status: 400 });
    }

    const { data, error } = await admin.auth.admin.updateUserById(userId, {
      user_metadata: metadata
    });

    if (error) {
      console.error('Error actualizando usuario:', error);
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
    console.error('Error en API update user:', err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'Admin API no configurada' }, { status: 503 });
    }

    const body = await request.json();
    const { email, password, role, display_name } = body;

    if (!email || !password) {
      return NextResponse.json({ error: 'Email y password requeridos' }, { status: 400 });
    }

    // Crear usuario con admin API
    const { data, error } = await admin.auth.admin.createUser({
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
