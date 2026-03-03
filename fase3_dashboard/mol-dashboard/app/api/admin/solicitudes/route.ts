import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';

let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    console.warn('Supabase admin credentials not configured');
    return null;
  }

  supabaseAdmin = createClient(url, key, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });

  return supabaseAdmin;
}

export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'Admin API no configurada' }, { status: 503 });
    }

    const { searchParams } = new URL(request.url);
    const estado = searchParams.get('estado');

    let query = admin.from('solicitudes_acceso').select('*').order('created_at', { ascending: false });

    if (estado) {
      query = query.eq('estado', estado);
    }

    const { data, error } = await query;

    if (error) {
      console.error('Error listando solicitudes:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ solicitudes: data });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Error desconocido';
    console.error('Error en API solicitudes:', message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  try {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return NextResponse.json({ error: 'Admin API no configurada' }, { status: 503 });
    }

    const body = await request.json();
    const { solicitudId, action, notas } = body;

    if (!solicitudId || !action) {
      return NextResponse.json({ error: 'solicitudId y action requeridos' }, { status: 400 });
    }

    if (action !== 'aprobar' && action !== 'rechazar') {
      return NextResponse.json({ error: 'action debe ser "aprobar" o "rechazar"' }, { status: 400 });
    }

    // Get the solicitud first to find user_id
    const { data: solicitud, error: fetchError } = await admin
      .from('solicitudes_acceso')
      .select('*')
      .eq('id', solicitudId)
      .single();

    if (fetchError || !solicitud) {
      return NextResponse.json({ error: 'Solicitud no encontrada' }, { status: 404 });
    }

    if (solicitud.estado !== 'pendiente') {
      return NextResponse.json({ error: 'Solicitud ya procesada' }, { status: 400 });
    }

    const adminEmail = auth.user.email || 'admin';

    // Update solicitud status
    const newEstado = action === 'aprobar' ? 'aprobada' : 'rechazada';
    const { error: updateError } = await admin
      .from('solicitudes_acceso')
      .update({
        estado: newEstado,
        revisado_por: adminEmail,
        revisado_at: new Date().toISOString(),
        notas_admin: notas || null,
      })
      .eq('id', solicitudId);

    if (updateError) {
      console.error('Error actualizando solicitud:', updateError);
      return NextResponse.json({ error: updateError.message }, { status: 500 });
    }

    // If approved, activate trial via Admin API (update user_metadata)
    if (action === 'aprobar') {
      const { error: userError } = await admin.auth.admin.updateUserById(
        solicitud.user_id,
        {
          user_metadata: {
            plan: 'trial',
            trial_start_date: new Date().toISOString(),
          },
        }
      );

      if (userError) {
        console.error('Error activando trial:', userError);
        return NextResponse.json(
          { error: `Solicitud aprobada pero error activando trial: ${userError.message}` },
          { status: 500 }
        );
      }
    }

    return NextResponse.json({
      solicitud: { id: solicitudId, estado: newEstado },
      trial_activated: action === 'aprobar',
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Error desconocido';
    console.error('Error en API solicitudes PATCH:', message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
