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

// Valid state transitions
const TRANSITIONS: Record<string, string[]> = {
  nuevo: ['en_diagnostico'],
  en_diagnostico: ['perfil_completo'],
  perfil_completo: ['derivado_vacante', 'derivado_curso'],
  derivado_vacante: ['en_seguimiento'],
  derivado_curso: ['en_seguimiento'],
  en_seguimiento: ['insertado', 'perfil_completo', 'cerrado'],
  cerrado: ['nuevo'],
};

// B3 — GET /api/casos/:id
export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { id } = await params;

  // Caso + persona
  const { data: caso, error } = await client.from('casos')
    .select('*, personas(id, nombre, dni, edad, nivel_educativo, ubicacion, telefono, email)')
    .eq('id', id).maybeSingle();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  if (!caso) return NextResponse.json({ error: 'Caso no encontrado' }, { status: 404 });

  // Perfil + skills
  const { data: perfiles } = await client.from('perfiles')
    .select('*, perfil_skills(*)').eq('persona_id', caso.persona_id)
    .order('updated_at', { ascending: false }).limit(1);

  const perfil = perfiles && perfiles.length > 0 ? perfiles[0] : null;

  // Derivaciones
  const { data: derivaciones } = await client.from('derivaciones')
    .select('*').eq('caso_id', id).order('fecha_derivacion', { ascending: false });

  // Eventos
  const { data: eventos } = await client.from('eventos_caso')
    .select('*').eq('entidad_id', id).order('timestamp', { ascending: false }).limit(20);

  return NextResponse.json({
    ...caso,
    persona: caso.personas,
    personas: undefined,
    perfil: perfil ? {
      id: perfil.id,
      completitud: perfil.completitud,
      skills: perfil.perfil_skills || [],
    } : null,
    derivaciones: derivaciones || [],
    eventos: eventos || [],
  });
}

// B4 — PATCH /api/casos/:id
export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { id } = await params;
  const body = await request.json();

  // Get current case
  const { data: caso } = await client.from('casos').select('estado').eq('id', id).maybeSingle();
  if (!caso) return NextResponse.json({ error: 'Caso no encontrado' }, { status: 404 });

  const updates: Record<string, any> = {};

  // Update fields
  if (body.nota_tecnico !== undefined) updates.nota_tecnico = body.nota_tecnico;
  if (body.checkboxes_tecnico !== undefined) updates.checkboxes_tecnico = body.checkboxes_tecnico;
  if (body.prioridad !== undefined) updates.prioridad = body.prioridad;

  // State transition
  if (body.estado && body.estado !== caso.estado) {
    const allowed = TRANSITIONS[caso.estado] || [];
    if (!allowed.includes(body.estado)) {
      return NextResponse.json(
        { error: `Transicion no permitida: ${caso.estado} → ${body.estado}. Permitidas: ${allowed.join(', ')}` },
        { status: 400 }
      );
    }
    updates.estado = body.estado;
  }

  if (Object.keys(updates).length === 0) {
    return NextResponse.json({ error: 'Nada que actualizar' }, { status: 400 });
  }

  const { data, error } = await client.from('casos').update(updates).eq('id', id).select().single();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Log event
  await client.from('eventos_caso').insert({
    entidad: 'caso', entidad_id: id,
    tipo: body.estado ? `estado_${body.estado}` : 'caso_actualizado',
    payload: updates,
  });

  return NextResponse.json(data);
}
