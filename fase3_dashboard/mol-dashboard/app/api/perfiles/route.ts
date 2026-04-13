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

// A6 — GET /api/perfiles?id=X or /api/perfiles?persona_id=X or /api/perfiles (list all)
export async function GET(request: NextRequest) {
  // TODO OE-11: restore requireAuth
  // const auth = await requireAuth(request);
  // if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const id = request.nextUrl.searchParams.get('id');
  const personaId = request.nextUrl.searchParams.get('persona_id');
  const search = request.nextUrl.searchParams.get('search');

  if (id) {
    // Get single profile with skills + persona data
    const { data: perfil, error } = await client.from('perfiles')
      .select('*, personas(id, nombre, dni, edad, nivel_educativo, ubicacion)')
      .eq('id', id).maybeSingle();
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    if (!perfil) return NextResponse.json({ error: 'Perfil no encontrado' }, { status: 404 });

    const { data: skills } = await client.from('perfil_skills')
      .select('*').eq('perfil_id', id).neq('estado', 'descartada').order('created_at');

    return NextResponse.json({ ...perfil, skills: skills || [] });
  }

  if (personaId) {
    const { data, error } = await client.from('perfiles')
      .select('*, personas(nombre, dni)')
      .eq('persona_id', personaId).order('updated_at', { ascending: false });
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json(data);
  }

  // List all perfiles with persona info (for M1 perfiles list)
  const limit = Math.max(1, Math.min(100, parseInt(request.nextUrl.searchParams.get('limit') || '100', 10) || 100));
  const offset = Math.max(0, parseInt(request.nextUrl.searchParams.get('offset') || '0', 10) || 0);

  const { data: perfiles, error } = await client.from('perfiles')
    .select('id, persona_id, origen, completitud, estado, validado_at, ocupaciones, updated_at, personas(nombre, dni)')
    .order('updated_at', { ascending: false }).range(offset, offset + limit - 1);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  let result = perfiles || [];

  // Client-side search filter by nombre or dni
  if (search) {
    const term = search.toLowerCase();
    result = result.filter((p: any) => {
      const nombre = (p.personas?.nombre || '').toLowerCase();
      const dni = p.personas?.dni || '';
      return nombre.includes(term) || dni.includes(term);
    });
  }

  return NextResponse.json(result);
}

// A3 — POST /api/perfiles
export async function POST(request: NextRequest) {
  // TODO OE-11: restore requireAuth
  // const auth = await requireAuth(request);
  // if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { persona_id, origen, ocupaciones } = body;

  if (!persona_id) return NextResponse.json({ error: 'Falta persona_id' }, { status: 400 });

  const { data, error } = await client.from('perfiles').insert({
    persona_id, origen: origen || 'S2', completitud: 0,
    ocupaciones: ocupaciones || [], estado: 'borrador',
  }).select().single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}
