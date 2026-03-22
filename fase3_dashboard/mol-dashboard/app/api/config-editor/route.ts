import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

const VALID_CONFIGS = [
  'matching_rules_business',
  'nlp_inference_rules',
  'sinonimos_argentinos_esco',
  'skills_rules',
  'oficios_arg',
  'nlp_titulo_limpieza',
];

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

// GET: leer config (override de Supabase o JSON local via fetch)
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const key = request.nextUrl.searchParams.get('key');
  if (!key || !VALID_CONFIGS.includes(key)) {
    return NextResponse.json({ error: `Config inválido. Válidos: ${VALID_CONFIGS.join(', ')}` }, { status: 400 });
  }

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  // Buscar override en Supabase
  const { data: override } = await client
    .from('config_overrides')
    .select('*')
    .eq('config_key', key)
    .maybeSingle();

  if (override) {
    return NextResponse.json({
      config_key: key,
      source: 'override',
      data: override.json_value,
      version: override.version,
      updated_by: override.updated_by,
      updated_at: override.updated_at,
      changelog: override.changelog,
    });
  }

  // Sin override — el frontend deberá cargar el JSON local
  return NextResponse.json({
    config_key: key,
    source: 'local',
    data: null,
    version: 0,
    message: 'Sin override. El pipeline usa el JSON local.',
  });
}

// PUT: guardar override
export async function PUT(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { config_key, data, action_summary } = body;

  if (!config_key || !VALID_CONFIGS.includes(config_key)) {
    return NextResponse.json({ error: 'config_key inválido' }, { status: 400 });
  }
  if (!data) {
    return NextResponse.json({ error: 'Falta data' }, { status: 400 });
  }

  const adminEmail = auth.user?.email || 'admin';

  // Leer override existente para incrementar version y changelog
  const { data: existing } = await client
    .from('config_overrides')
    .select('version, changelog')
    .eq('config_key', config_key)
    .maybeSingle();

  const newVersion = (existing?.version || 0) + 1;
  const changelog = existing?.changelog || [];
  changelog.push({
    timestamp: new Date().toISOString(),
    user: adminEmail,
    version: newVersion,
    action: action_summary || 'Actualización',
  });

  // Upsert
  const { data: result, error } = await client
    .from('config_overrides')
    .upsert({
      config_key,
      json_value: data,
      version: newVersion,
      updated_by: adminEmail,
      updated_at: new Date().toISOString(),
      changelog,
    }, { onConflict: 'config_key' })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({
    config_key,
    version: newVersion,
    updated_by: adminEmail,
    message: 'Config guardado. El pipeline usará este override.',
  });
}
