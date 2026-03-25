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

// A6 — GET /api/perfiles?id=X or /api/perfiles?persona_id=X
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const id = request.nextUrl.searchParams.get('id');
  const personaId = request.nextUrl.searchParams.get('persona_id');

  if (id) {
    // Get single profile with skills
    const { data: perfil, error } = await client.from('perfiles').select('*').eq('id', id).maybeSingle();
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    if (!perfil) return NextResponse.json({ error: 'Perfil no encontrado' }, { status: 404 });

    const { data: skills } = await client.from('perfil_skills')
      .select('*').eq('perfil_id', id).order('created_at');

    return NextResponse.json({ ...perfil, skills: skills || [] });
  }

  if (personaId) {
    const { data, error } = await client.from('perfiles').select('*')
      .eq('persona_id', personaId).order('updated_at', { ascending: false });
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json(data);
  }

  return NextResponse.json({ error: 'Falta id o persona_id' }, { status: 400 });
}

// A3 — POST /api/perfiles
export async function POST(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { persona_id, origen } = body;

  if (!persona_id) return NextResponse.json({ error: 'Falta persona_id' }, { status: 400 });

  const { data, error } = await client.from('perfiles').insert({
    persona_id, origen: origen || 'S2', completitud: 0,
  }).select().single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}
