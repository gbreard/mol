import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
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

const RUN_FIELDS = [
  'run_id',
  'timestamp',
  'git_branch',
  'git_commit',
  'nlp_version',
  'matching_version',
  'ofertas_count',
  'failures_count',
  'failures_pct',
  'precision',
  'errores_detectados',
  'errores_corregidos',
  'errores_escalados',
  'reglas_nuevas',
  'sinonimos_count',
  'delta_mejoras',
  'delta_regresiones',
  'run_anterior_id',
].join(',');

// GET /api/pipeline-runs?since=&until=&matching_version=&limit=
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { searchParams } = new URL(request.url);
  const since = searchParams.get('since');
  const until = searchParams.get('until');
  const matchingVersion = searchParams.get('matching_version');
  const limit = Math.min(parseInt(searchParams.get('limit') || '100', 10), 500);

  let q = client
    .from('pipeline_runs_history')
    .select(RUN_FIELDS, { count: 'exact' })
    .order('timestamp', { ascending: false })
    .limit(limit);

  if (since) q = q.gte('timestamp', since);
  if (until) q = q.lte('timestamp', until);
  if (matchingVersion) q = q.eq('matching_version', matchingVersion);

  const { data, error, count } = await q;
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({
    runs: data || [],
    total: count || 0,
    limit,
  });
}
