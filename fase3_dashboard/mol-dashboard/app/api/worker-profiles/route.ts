import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';
import { requireAuth, isAuthError } from '@/lib/api-auth';

// Cliente con service_role para acceder a tablas (lazy initialization)
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

// Type definitions
interface WorkerProfile {
  id?: string;
  nombre: string;
  ocupaciones_trayectoria: string[]; // UUIDs de ocupaciones ESCO
  skills_seleccionadas: string[];    // URIs de skills ESCO
  skills_eliminadas: string[];       // URIs de skills que el trabajador NO tiene
  skills_agregadas: string[];        // URIs de skills agregadas manualmente
  created_at?: string;
  updated_at?: string;
  created_by?: string;               // user_id del gestor de empleo
}

// GET - Listar perfiles o obtener uno específico
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'API no configurada' }, { status: 503 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const search = searchParams.get('search');

    if (id) {
      // Obtener perfil específico
      const { data, error } = await admin
        .from('perfiles_trabajadores')
        .select('*')
        .eq('id', id)
        .single();

      if (error) {
        console.error('Error obteniendo perfil:', error);
        return NextResponse.json({ error: error.message }, { status: 404 });
      }

      return NextResponse.json({ profile: data });
    }

    // Listar perfiles (con búsqueda opcional)
    let query = admin
      .from('perfiles_trabajadores')
      .select('*')
      .order('updated_at', { ascending: false });

    if (search) {
      query = query.ilike('nombre', `%${search}%`);
    }

    const { data, error } = await query.limit(50);

    if (error) {
      console.error('Error listando perfiles:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ profiles: data || [] });
  } catch (err: any) {
    console.error('Error en API perfiles:', err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

// POST - Crear nuevo perfil
export async function POST(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'API no configurada' }, { status: 503 });
    }

    const body: Partial<WorkerProfile> = await request.json();

    if (!body.nombre?.trim()) {
      return NextResponse.json({ error: 'Nombre del trabajador requerido' }, { status: 400 });
    }

    const perfil = {
      nombre: body.nombre.trim(),
      ocupaciones_trayectoria: body.ocupaciones_trayectoria || [],
      skills_seleccionadas: body.skills_seleccionadas || [],
      skills_eliminadas: body.skills_eliminadas || [],
      skills_agregadas: body.skills_agregadas || [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const { data, error } = await admin
      .from('perfiles_trabajadores')
      .insert(perfil)
      .select()
      .single();

    if (error) {
      console.error('Error creando perfil:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ profile: data }, { status: 201 });
  } catch (err: any) {
    console.error('Error en API crear perfil:', err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

// PUT - Actualizar perfil existente
export async function PUT(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'API no configurada' }, { status: 503 });
    }

    const body: Partial<WorkerProfile> = await request.json();

    if (!body.id) {
      return NextResponse.json({ error: 'ID del perfil requerido' }, { status: 400 });
    }

    const updates: any = {
      updated_at: new Date().toISOString()
    };

    if (body.nombre !== undefined) updates.nombre = body.nombre.trim();
    if (body.ocupaciones_trayectoria !== undefined) updates.ocupaciones_trayectoria = body.ocupaciones_trayectoria;
    if (body.skills_seleccionadas !== undefined) updates.skills_seleccionadas = body.skills_seleccionadas;
    if (body.skills_eliminadas !== undefined) updates.skills_eliminadas = body.skills_eliminadas;
    if (body.skills_agregadas !== undefined) updates.skills_agregadas = body.skills_agregadas;

    const { data, error } = await admin
      .from('perfiles_trabajadores')
      .update(updates)
      .eq('id', body.id)
      .select()
      .single();

    if (error) {
      console.error('Error actualizando perfil:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ profile: data });
  } catch (err: any) {
    console.error('Error en API actualizar perfil:', err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

// DELETE - Eliminar perfil
export async function DELETE(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'API no configurada' }, { status: 503 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json({ error: 'ID del perfil requerido' }, { status: 400 });
    }

    const { error } = await admin
      .from('perfiles_trabajadores')
      .delete()
      .eq('id', id);

    if (error) {
      console.error('Error eliminando perfil:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch (err: any) {
    console.error('Error en API eliminar perfil:', err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
