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
  'source',
  'description',
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

// GET /api/pipeline-runs?since=&until=&matching_version=&source=&limit=
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { searchParams } = new URL(request.url);
  const since = searchParams.get('since');
  const until = searchParams.get('until');
  const matchingVersion = searchParams.get('matching_version');
  const source = searchParams.get('source');
  const limit = Math.min(parseInt(searchParams.get('limit') || '100', 10), 500);

  let q = client
    .from('pipeline_runs_history')
    .select(RUN_FIELDS, { count: 'exact' })
    .order('timestamp', { ascending: false })
    .limit(limit);

  if (since) q = q.gte('timestamp', since);
  if (until) q = q.lte('timestamp', until);
  if (matchingVersion) q = q.eq('matching_version', matchingVersion);
  if (source) q = q.eq('source', source);

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

// GET sources únicos para el selector
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json().catch(() => ({}));
  if (body.action !== 'list_sources') {
    return NextResponse.json({ error: 'Acción no soportada' }, { status: 400 });
  }

  // Distinct sources (PostgREST no soporta DISTINCT, hacemos en cliente)
  const { data, error } = await client
    .from('pipeline_runs_history')
    .select('source')
    .not('source', 'is', null)
    .limit(10000);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const counts = new Map<string, number>();
  for (const row of data || []) {
    const s = (row as { source: string | null }).source;
    if (s) counts.set(s, (counts.get(s) || 0) + 1);
  }
  const sources = Array.from(counts.entries())
    .map(([source, n]) => ({ source, n }))
    .sort((a, b) => b.n - a.n);

  return NextResponse.json({ sources });
}
