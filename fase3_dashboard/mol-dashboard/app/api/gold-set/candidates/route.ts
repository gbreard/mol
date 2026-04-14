import { NextRequest, NextResponse } from 'next/server';
import { requireAuth, isAuthError } from '@/lib/api-auth';
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

export async function GET(request: NextRequest) {
  const auth = await requireAuth(request);
  if (auth instanceof NextResponse) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '100');

  const { data, error } = await client.rpc('get_gold_set_candidates', {
    p_limit: Math.min(limit, 200),
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Also get gold set stats for the banner
  const { data: stats } = await client.rpc('get_gold_set_stats');

  return NextResponse.json({
    candidates: data || [],
    gold_set_stats: stats || { total: 0, correctos: 0, errores: 0 },
  });
}
