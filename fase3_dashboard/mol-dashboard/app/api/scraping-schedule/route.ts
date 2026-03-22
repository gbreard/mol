import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
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

// GET: leer schedule actual
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { data, error } = await client.rpc('get_scraping_schedule');
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data);
}

// PUT: actualizar schedule
export async function PUT(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { id, dias_semana, hora_utc, activo } = body;

  if (!id) return NextResponse.json({ error: 'Falta id' }, { status: 400 });

  const updates: Record<string, any> = { updated_at: new Date().toISOString() };
  if (dias_semana !== undefined) updates.dias_semana = dias_semana;
  if (hora_utc !== undefined) updates.hora_utc = hora_utc;
  if (activo !== undefined) updates.activo = activo;
  updates.updated_by = auth.user?.email || 'admin';

  const { data, error } = await client
    .from('scraping_schedule')
    .update(updates)
    .eq('id', id)
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data);
}

// POST: agregar nuevo schedule
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { portal, dias_semana, hora_utc } = body;

  if (!portal || !dias_semana) {
    return NextResponse.json({ error: 'Falta portal o dias_semana' }, { status: 400 });
  }

  const { data, error } = await client
    .from('scraping_schedule')
    .insert({
      portal,
      dias_semana,
      hora_utc: hora_utc || '11:00',
      activo: true,
      updated_by: auth.user?.email || 'admin',
    })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data, { status: 201 });
}
