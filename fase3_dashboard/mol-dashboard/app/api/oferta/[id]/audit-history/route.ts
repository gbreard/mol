import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Refs:
//   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 3.2.3

let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  supabaseAdmin = createClient(url, key, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  return supabaseAdmin;
}

export function _resetSupabaseAdminForTests() {
  supabaseAdmin = null;
}

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(request: NextRequest, ctx: RouteContext) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) {
    return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });
  }

  const { id: idOferta } = await ctx.params;
  if (!idOferta) {
    return NextResponse.json({ error: 'id_oferta requerido' }, { status: 400 });
  }

  const { data, error } = await client
    .from('audit_actions')
    .select('*')
    .eq('id_oferta', idOferta)
    .order('timestamp', { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const actions = data || [];
  return NextResponse.json({ actions, total: actions.length });
}
