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

// POST: preview impacto de una regla
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { titulo_contiene, titulo_contiene_alguno, forzar_isco } = body;

  if (!forzar_isco) {
    return NextResponse.json({ error: 'Falta forzar_isco' }, { status: 400 });
  }
  if (!titulo_contiene && !titulo_contiene_alguno) {
    return NextResponse.json({ error: 'Falta titulo_contiene o titulo_contiene_alguno' }, { status: 400 });
  }

  const { data, error } = await client.rpc('preview_rule_impact', {
    p_titulo_contiene: titulo_contiene || null,
    p_titulo_contiene_alguno: titulo_contiene_alguno || null,
    p_forzar_isco: forzar_isco,
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

// GET: sugerencias de reglas basadas en errores y correcciones
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { data, error } = await client.rpc('get_rule_suggestions');
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data);
}
