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

// GET: listar emergentes (filtros: estado, isco_code)
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const estado = request.nextUrl.searchParams.get('estado') || 'pendiente';
  const isco = request.nextUrl.searchParams.get('isco_code') || null;

  const { data, error } = await client.rpc('get_emergentes', {
    p_estado: estado,
    p_isco: isco,
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

// PATCH: aprobar o rechazar emergente
// E2.4: Si se aprueba, ejecuta 4 triggers downstream via RPC
export async function PATCH(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { id, accion, notas } = body;

  if (!id || !['aprobar', 'rechazar'].includes(accion)) {
    return NextResponse.json({ error: 'Falta id o accion (aprobar/rechazar)' }, { status: 400 });
  }

  const adminEmail = auth.user?.email || 'admin';

  if (accion === 'aprobar') {
    // E2.4: Usar RPC con triggers downstream (transaccional)
    const { data, error } = await client.rpc('aprobar_emergente_con_triggers', {
      p_emergente_id: id,
      p_admin_email: adminEmail,
      p_notas: notas || null,
    });

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });

    return NextResponse.json({
      id,
      skill_label: data?.skill_label || '',
      estado: 'aprobada',
      message: `Skill "${data?.skill_label}" aprobada con triggers downstream`,
      triggers: {
        esco_argentino: data?.trigger_1_esco_argentino,
        training_pair_id: data?.trigger_2_training_pair_id,
        cache_invalidated: data?.trigger_3_cache_invalidated,
        alerta: data?.trigger_4_alerta,
        aprobadas_desde_corte: data?.aprobadas_desde_corte,
      },
    });
  }

  // Rechazar: solo UPDATE simple (sin triggers)
  const { data, error } = await client
    .from('emergentes_pendientes')
    .update({
      estado: 'rechazada',
      fecha_resolucion: new Date().toISOString(),
      resuelto_por: adminEmail,
      notas: notas || null,
    })
    .eq('id', id)
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({
    id: data.id,
    skill_label: data.skill_label,
    estado: data.estado,
    message: `Skill "${data.skill_label}" rechazada`,
  });
}

// POST: ejecutar recálculo de emergentes
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { data, error } = await client.rpc('recalcular_emergentes');
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data);
}
