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

// GET: última acta de corrida + alertas recientes (SPEC S1C-F0.3).
// Lee el espejo que el poller sube a pipeline_local_status (fuente de verdad
// local: pipeline_run_actas / pipeline_alertas en SQLite).
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { data, error } = await client
    .from('pipeline_local_status')
    .select('ultima_acta, alertas_recientes, timestamp')
    .eq('id', 'current')
    .maybeSingle();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({
    ultimaActa: data?.ultima_acta ?? null,
    alertas: data?.alertas_recientes ?? [],
    timestamp: data?.timestamp ?? null,
  });
}
