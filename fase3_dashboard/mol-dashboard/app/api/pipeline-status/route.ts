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

export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) {
    return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });
  }

  // Fetch both RPCs in parallel
  const [statusResult, reconResult] = await Promise.all([
    client.rpc('get_pipeline_status'),
    client.rpc('reconciliar_sistemas'),
  ]);

  if (statusResult.error) {
    return NextResponse.json({ error: statusResult.error.message }, { status: 500 });
  }

  return NextResponse.json({
    ...statusResult.data,
    reconciliacion: reconResult.error ? null : reconResult.data,
  });
}
