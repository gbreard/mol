import { NextRequest, NextResponse } from 'next/server';
import { requireAuth, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseAdmin: SupabaseClient | null = null;
function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  supabaseAdmin = createClient(url, key, { auth: { autoRefreshToken: false, persistSession: false } });
  return supabaseAdmin;
}

// A2 — GET /api/personas?dni=X&nombre=Y&org_id=Z
export async function GET(request: NextRequest) {
  // TODO OE-11: restore requireAuth
  // const auth = await requireAuth(request);
  // if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const dni = request.nextUrl.searchParams.get('dni');
  const nombre = request.nextUrl.searchParams.get('nombre');
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '50');

  let query = client.from('personas').select('*, casos(id, estado, organizacion_id)');

  if (dni) query = query.eq('dni', dni);
  if (nombre) query = query.ilike('nombre', `%${nombre}%`);

  const { data, error } = await query.order('created_at', { ascending: false }).limit(limit);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Flatten caso_activo
  const personas = (data || []).map((p: any) => {
    const casoActivo = (p.casos || []).find((c: any) => c.estado !== 'cerrado');
    return {
      ...p,
      casos: undefined,
      caso_activo_id: casoActivo?.id || null,
      caso_estado: casoActivo?.estado || null,
    };
  });

  return NextResponse.json(personas);
}

// A1 — POST /api/personas
export async function POST(request: NextRequest) {
  // TODO OE-11: restore requireAuth
  // const auth = await requireAuth(request);
  // if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { nombre, dni, edad, nivel_educativo, ubicacion, telefono, email, origen } = body;

  if (!nombre) return NextResponse.json({ error: 'Falta nombre' }, { status: 400 });

  // Si tiene DNI, buscar existente y actualizar campos si cambiaron
  if (dni) {
    const { data: existing } = await client.from('personas').select('*').eq('dni', dni).maybeSingle();
    if (existing) {
      const updates: Record<string, any> = {};
      if (nombre && nombre !== existing.nombre) updates.nombre = nombre;
      if (ubicacion && ubicacion !== existing.ubicacion) updates.ubicacion = ubicacion;
      if (Object.keys(updates).length > 0) {
        await client.from('personas').update(updates).eq('id', existing.id);
        Object.assign(existing, updates);
      }
      return NextResponse.json({ ...existing, es_nueva: false });
    }
  }

  const { data, error } = await client.from('personas').insert({
    nombre, dni: dni || null, edad: edad || null, nivel_educativo: nivel_educativo || null,
    ubicacion: ubicacion || null, telefono: telefono || null, email: email || null,
    origen: origen || 'S2',
  }).select().single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ...data, es_nueva: true }, { status: 201 });
}
