import { NextRequest, NextResponse } from 'next/server';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  supabaseAdmin = createClient(url, key, {
    auth: { autoRefreshToken: false, persistSession: false }
  });
  return supabaseAdmin;
}

export async function GET(_request: NextRequest) {
  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ count: 0 });

  // Intentar leer emergentes_pendientes si existe
  try {
    const { count, error } = await client
      .from('emergentes_pendientes')
      .select('*', { count: 'exact', head: true })
      .eq('estado', 'pendiente');

    if (!error && count !== null) {
      return NextResponse.json({ count });
    }
  } catch {
    // Tabla no existe aún
  }

  // Fallback: 0 emergentes (tabla pendiente de crear en Bloque 9°)
  return NextResponse.json({ count: 0 });
}
