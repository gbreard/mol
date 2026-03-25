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

// B1 — GET /api/casos?org_id=X&estado=Y&q=nombre_o_dni
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const orgId = request.nextUrl.searchParams.get('org_id');
  const estado = request.nextUrl.searchParams.get('estado');
  const q = request.nextUrl.searchParams.get('q');
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '50');

  let query = client.from('casos').select('*, personas(nombre, dni)');

  if (orgId) query = query.eq('organizacion_id', orgId);
  if (estado) query = query.eq('estado', estado);

  const { data, error } = await query.order('updated_at', { ascending: false }).limit(limit);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  let casos = (data || []).map((c: any) => ({
    id: c.id,
    persona_nombre: c.personas?.nombre || '',
    persona_dni: c.personas?.dni || '',
    estado: c.estado,
    prioridad: c.prioridad,
    objetivo: c.objetivo,
    ultima_atencion: c.updated_at,
    created_at: c.created_at,
  }));

  // Filter by text if q provided
  if (q) {
    const term = q.toLowerCase();
    casos = casos.filter((c: any) =>
      c.persona_nombre.toLowerCase().includes(term) || (c.persona_dni || '').includes(term)
    );
  }

  return NextResponse.json(casos);
}

// B2 — POST /api/casos
export async function POST(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { persona_id, organizacion_id, objetivo } = body;

  if (!persona_id || !organizacion_id) {
    return NextResponse.json({ error: 'Falta persona_id o organizacion_id' }, { status: 400 });
  }

  // Check no active case for this persona in this org
  const { data: existing } = await client.from('casos')
    .select('id, estado')
    .eq('persona_id', persona_id)
    .eq('organizacion_id', organizacion_id)
    .neq('estado', 'cerrado')
    .limit(1);

  if (existing && existing.length > 0) {
    return NextResponse.json(
      { error: 'Ya existe un caso activo para esta persona en esta organizacion', caso_existente_id: existing[0].id },
      { status: 409 }
    );
  }

  const { data, error } = await client.from('casos').insert({
    persona_id, organizacion_id, objetivo: objetivo || 'empleo',
  }).select().single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Log event
  await client.from('eventos_caso').insert({
    entidad: 'caso', entidad_id: data.id, tipo: 'caso_creado',
    payload: { organizacion_id, objetivo },
  });

  return NextResponse.json(data, { status: 201 });
}
