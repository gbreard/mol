import { NextRequest, NextResponse } from 'next/server';
import { requireAuth, isAuthError } from '@/lib/api-auth';
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

// B5 — POST /api/casos/:id/derivar
export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { id: casoId } = await params;
  const body = await request.json();
  const { tipo, destino_id, motivo } = body;

  if (!tipo || !destino_id) {
    return NextResponse.json({ error: 'Falta tipo o destino_id' }, { status: 400 });
  }

  // Verify caso exists and is in valid state
  const { data: caso } = await client.from('casos').select('estado').eq('id', casoId).maybeSingle();
  if (!caso) return NextResponse.json({ error: 'Caso no encontrado' }, { status: 404 });

  const validStates = ['perfil_completo', 'en_seguimiento', 'derivado_vacante', 'derivado_curso'];
  if (!validStates.includes(caso.estado)) {
    return NextResponse.json(
      { error: `No se puede derivar un caso en estado "${caso.estado}". Requiere: ${validStates.join(', ')}` },
      { status: 400 }
    );
  }

  // Create derivacion
  const { data: derivacion, error } = await client.from('derivaciones').insert({
    caso_id: casoId,
    tipo,
    destino_id,
    motivo: motivo || null,
  }).select().single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Update caso estado
  const nuevoEstado = tipo === 'vacante' ? 'derivado_vacante' : 'derivado_curso';
  await client.from('casos').update({ estado: nuevoEstado }).eq('id', casoId);

  // Log event
  await client.from('eventos_caso').insert({
    entidad: 'derivacion', entidad_id: derivacion.id,
    tipo: `derivado_${tipo}`,
    payload: { caso_id: casoId, destino_id, motivo },
  });

  return NextResponse.json(derivacion, { status: 201 });
}

// B6 — PATCH /api/casos/:id/derivar — update derivacion result
export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { id: casoId } = await params;
  const body = await request.json();
  const { derivacion_id, estado } = body;

  if (!derivacion_id || !estado) {
    return NextResponse.json({ error: 'Falta derivacion_id o estado' }, { status: 400 });
  }

  const { error } = await client.from('derivaciones')
    .update({ estado, fecha_resultado: new Date().toISOString() })
    .eq('id', derivacion_id)
    .eq('caso_id', casoId);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Propagate to caso
  if (estado === 'aceptado') {
    await client.from('casos').update({ estado: 'insertado' }).eq('id', casoId);
  } else if (estado === 'rechazado' || estado === 'no_se_presento') {
    await client.from('casos').update({ estado: 'perfil_completo' }).eq('id', casoId);
  }

  // Log
  await client.from('eventos_caso').insert({
    entidad: 'derivacion', entidad_id: derivacion_id,
    tipo: `derivacion_${estado}`,
    payload: { caso_id: casoId },
  });

  return NextResponse.json({ ok: true, derivacion_id, estado });
}
