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

// GET: list equivalences (with filters)
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const estado = request.nextUrl.searchParams.get('estado');
  const search = request.nextUrl.searchParams.get('search');
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '50');
  const offset = parseInt(request.nextUrl.searchParams.get('offset') || '0');

  let query = client.from('skill_equivalences').select('*', { count: 'exact' });

  if (estado) query = query.eq('estado', estado);
  if (search) query = query.or(`label_representante.ilike.%${search}%,label_argentino.ilike.%${search}%`);

  const { data, error, count } = await query
    .order('frecuencia_total', { ascending: false })
    .range(offset, offset + limit - 1);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Stats
  const { count: totalGroups } = await client.from('skill_equivalences').select('*', { count: 'exact', head: true });
  const { count: autoCount } = await client.from('skill_equivalences').select('*', { count: 'exact', head: true }).eq('estado', 'auto');
  const { count: revisadoCount } = await client.from('skill_equivalences').select('*', { count: 'exact', head: true }).eq('estado', 'revisado');
  const { count: aprobadoCount } = await client.from('skill_equivalences').select('*', { count: 'exact', head: true }).eq('estado', 'aprobado');

  return NextResponse.json({
    equivalences: data,
    total: count,
    stats: {
      total: totalGroups || 0,
      auto: autoCount || 0,
      revisado: revisadoCount || 0,
      aprobado: aprobadoCount || 0,
    },
  });
}

// PUT: update equivalence (label, estado, etc.)
export async function PUT(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { id, label_representante, label_argentino, estado, notas } = body;

  if (!id) return NextResponse.json({ error: 'Falta id' }, { status: 400 });

  const updates: Record<string, any> = {};
  if (label_representante !== undefined) updates.label_representante = label_representante;
  if (label_argentino !== undefined) updates.label_argentino = label_argentino;
  if (estado !== undefined) updates.estado = estado;
  if (notas !== undefined) updates.notas = notas;

  const email = auth.user?.email || 'admin';
  if (estado === 'revisado' || estado === 'aprobado') updates.revisado_por = email;

  const { data, error } = await client.from('skill_equivalences').update(updates).eq('id', id).select().single();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data);
}
