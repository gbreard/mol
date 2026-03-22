import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

const COMANDOS_VALIDOS = [
  'lanzar_portal',
  'lanzar_todos',
  'sync_vps_local',
  'sync_local_supabase',
  'pausar_portal',
] as const;

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

// GET: listar comandos recientes
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '20');

  const { data, error } = await client.rpc('get_scraping_commands', { p_limit: limit });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data);
}

// POST: crear un comando nuevo
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { comando, params } = body;

  // Validar comando
  if (!comando || !COMANDOS_VALIDOS.includes(comando)) {
    return NextResponse.json(
      { error: `Comando invalido. Validos: ${COMANDOS_VALIDOS.join(', ')}` },
      { status: 400 }
    );
  }

  // Validar que lanzar_portal tenga params.portal
  if (comando === 'lanzar_portal' && !params?.portal) {
    return NextResponse.json({ error: 'Falta params.portal' }, { status: 400 });
  }

  // Obtener email del admin
  const adminEmail = auth.user?.email || 'admin';

  const { data, error } = await client
    .from('scraping_commands')
    .insert({
      comando,
      params: params || {},
      creado_por: adminEmail,
    })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data, { status: 201 });
}
