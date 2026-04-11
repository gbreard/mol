import { NextRequest, NextResponse } from 'next/server';
import { requireAuth, requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  supabaseAdmin = createClient(url, key, {
    auth: { autoRefreshToken: false, persistSession: false }
  });
  return supabaseAdmin;
}

// GET: estadísticas del Gold Set
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request);
  if (auth instanceof NextResponse) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { data, error } = await client.rpc('get_gold_set_stats');
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data);
}

// POST: agregar caso al Gold Set (UPSERT)
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { id_oferta, esco_ok, isco_esperado, esco_esperado, tipo_error, comentario } = body;

  if (!id_oferta || typeof esco_ok !== 'boolean') {
    return NextResponse.json({ error: 'id_oferta y esco_ok requeridos' }, { status: 400 });
  }

  const adminEmail = auth.user?.email || 'admin';

  const { data, error } = await client.rpc('agregar_a_gold_set', {
    p_id_oferta: id_oferta,
    p_esco_ok: esco_ok,
    p_isco_esperado: isco_esperado || null,
    p_esco_esperado: esco_esperado || null,
    p_tipo_error: tipo_error || null,
    p_comentario: comentario || null,
    p_agregado_por: adminEmail,
    p_version_reglas: 'v5.16',
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data, { status: 201 });
}

// DELETE: desactivar caso del Gold Set
export async function DELETE(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { id_oferta } = await request.json();
  if (!id_oferta) return NextResponse.json({ error: 'id_oferta requerido' }, { status: 400 });

  const { error } = await client
    .from('gold_set')
    .update({ activo: false })
    .eq('id_oferta', id_oferta);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ message: 'Desactivado' });
}
