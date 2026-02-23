import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';

let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
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
      return NextResponse.json({
        usuariosActivos24h: 0,
        usuariosActivos7d: 0,
        totalUsuarios: 0
      });
    }

    // Obtener todos los usuarios
    const { data: { users }, error } = await admin.auth.admin.listUsers();

    if (error) {
      console.error('Error listando usuarios:', error);
      return NextResponse.json({
        usuariosActivos24h: 0,
        usuariosActivos7d: 0,
        totalUsuarios: 0
      });
    }

    const now = new Date();
    const hace24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const hace7d = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    let activos24h = 0;
    let activos7d = 0;

    users.forEach(user => {
      if (user.last_sign_in_at) {
        const lastLogin = new Date(user.last_sign_in_at);
        if (lastLogin >= hace24h) {
          activos24h++;
          activos7d++;
        } else if (lastLogin >= hace7d) {
          activos7d++;
        }
      }
    });

    return NextResponse.json({
      usuariosActivos24h: activos24h,
      usuariosActivos7d: activos7d,
      totalUsuarios: users.length
    });
  } catch (err: any) {
    console.error('Error en API stats:', err);
    return NextResponse.json({
      usuariosActivos24h: 0,
      usuariosActivos7d: 0,
      totalUsuarios: 0
    });
  }
}
