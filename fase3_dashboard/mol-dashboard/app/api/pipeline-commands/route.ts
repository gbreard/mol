import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

const COMANDOS_VALIDOS = [
  'run_pipeline',
  'run_nlp',
  'run_matching',
  'reprocess_errors',
  'revalidate_nlp',
  'revalidate_matching',
  'reapply_rules',
  'export_excel',
  'sync_supabase',
  'sync_supabase_full',
  'generate_training',
] as const;

type Comando = typeof COMANDOS_VALIDOS[number];

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
  const estado = request.nextUrl.searchParams.get('estado');

  let query = client
    .from('pipeline_commands')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(limit);

  if (estado) query = query.eq('estado', estado);

  const { data, error } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Calculate duration for each command
  const commands = (data || []).map((cmd: any) => ({
    ...cmd,
    duracion_seg: cmd.completed_at && cmd.started_at
      ? Math.round((new Date(cmd.completed_at).getTime() - new Date(cmd.started_at).getTime()) / 1000)
      : cmd.started_at
        ? Math.round((Date.now() - new Date(cmd.started_at).getTime()) / 1000)
        : null,
  }));

  return NextResponse.json({ commands, total: commands.length });
}

// POST: crear un comando nuevo
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { comando, params } = body;

  // Validate command
  if (!comando || !COMANDOS_VALIDOS.includes(comando as Comando)) {
    return NextResponse.json(
      { error: `Comando invalido. Validos: ${COMANDOS_VALIDOS.join(', ')}` },
      { status: 400 }
    );
  }

  // Validate params for commands that need them
  if ((comando === 'run_pipeline' || comando === 'run_nlp') && !params?.limit && !params?.ids) {
    return NextResponse.json(
      { error: 'Falta params.limit o params.ids' },
      { status: 400 }
    );
  }

  // Check no duplicate pending command
  const { data: pending } = await client
    .from('pipeline_commands')
    .select('id')
    .eq('comando', comando)
    .eq('estado', 'pendiente')
    .limit(1);

  if (pending && pending.length > 0) {
    return NextResponse.json(
      { error: `Ya hay un comando "${comando}" pendiente. Esperá a que termine.` },
      { status: 409 }
    );
  }

  // Also check for running commands (no parallel execution)
  const { data: running } = await client
    .from('pipeline_commands')
    .select('id, comando')
    .eq('estado', 'ejecutando')
    .limit(1);

  if (running && running.length > 0) {
    return NextResponse.json(
      { error: `Hay un comando en ejecución ("${running[0].comando}"). Esperá a que termine.` },
      { status: 409 }
    );
  }

  const adminEmail = auth.user?.email || 'admin';

  const { data, error } = await client
    .from('pipeline_commands')
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
