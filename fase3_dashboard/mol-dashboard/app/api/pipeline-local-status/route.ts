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

// GET: lee pipeline_local_status (snapshot que el poller sube cada minuto)
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { data, error } = await client
    .from('pipeline_local_status')
    .select('*')
    .eq('id', 'current')
    .maybeSingle();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  if (!data || !data.total_ofertas) {
    return NextResponse.json({
      source: 'no_data',
      message: 'Sin datos locales. El poller los sube cada minuto si cron esta activo.',
      total_ofertas: 0,
      nlp_procesadas: 0, nlp_pendientes: 0, nlp_aprobados: 0, nlp_bloqueados: 0, nlp_gate_aprobado_pct: 100,
      matching_con: 0, matching_sin: 0,
      validadas: 0, errores_pendientes: 0,
      en_supabase: 0, pendientes_sync: 0,
    });
  }

  return NextResponse.json(data);
}
