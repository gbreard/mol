import { NextRequest, NextResponse } from 'next/server';
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

// PATCH /api/perfiles/[id] — cambiar estado (borrador/validado)
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { estado } = body;

  if (!estado || !['borrador', 'validado'].includes(estado)) {
    return NextResponse.json({ error: 'estado debe ser borrador o validado' }, { status: 400 });
  }

  const update: Record<string, any> = { estado };
  if (estado === 'validado') {
    update.validado_at = new Date().toISOString();
  } else {
    update.validado_at = null;
  }

  const { data, error } = await client
    .from('perfiles')
    .update(update)
    .eq('id', id)
    .select('id, estado, validado_at')
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

// DELETE /api/perfiles/[id] — eliminar perfil y sus skills
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  // Check perfil exists before deleting
  const { data: existing } = await client.from('perfiles').select('id').eq('id', id).maybeSingle();
  if (!existing) return NextResponse.json({ error: 'Perfil no encontrado' }, { status: 404 });

  // Delete skills first (FK dependency)
  await client.from('perfil_skills').delete().eq('perfil_id', id);

  const { error } = await client.from('perfiles').delete().eq('id', id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ deleted: true });
}

// PUT /api/perfiles/[id] — editar perfil completo (persona + ocupaciones + skills)
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { nombre, dni, ocupaciones, skills, edad, nivel_educativo, ubicacion } = body;

  // Get perfil to find persona_id
  const { data: perfil } = await client
    .from('perfiles')
    .select('persona_id')
    .eq('id', id)
    .maybeSingle();

  if (!perfil) return NextResponse.json({ error: 'Perfil no encontrado' }, { status: 404 });

  // Update persona fields if provided
  if (nombre || dni) {
    const personaUpdate: Record<string, any> = {};
    if (nombre) personaUpdate.nombre = nombre;
    if (dni) personaUpdate.dni = dni;
    if (edad !== undefined) personaUpdate.edad = edad;
    if (nivel_educativo !== undefined) personaUpdate.nivel_educativo = nivel_educativo;
    if (ubicacion !== undefined) personaUpdate.ubicacion = ubicacion;
    await client.from('personas').update(personaUpdate).eq('id', perfil.persona_id);
  }

  // Update perfil (ocupaciones, reset to borrador on edit)
  const perfilUpdate: Record<string, any> = { estado: 'borrador', validado_at: null };
  if (ocupaciones) perfilUpdate.ocupaciones = ocupaciones;
  if (skills) perfilUpdate.completitud = skills.length;

  await client.from('perfiles').update(perfilUpdate).eq('id', id);

  // Replace skills: delete old + insert new
  if (skills && Array.isArray(skills)) {
    await client.from('perfil_skills').delete().eq('perfil_id', id);

    const skillRows = skills.map((s: any) => ({
      perfil_id: id,
      skill_uri: s.skill_uri || s.uri || '',
      skill_label: s.skill_label || s.label,
      via_captura: s.via_captura || (
        s.source === 'ocupacion' ? 'ocupacion'
        : s.source === 'busqueda' ? 'tarea'
        : s.source === 'texto' ? 'texto'
        : s.source === 'estructurado' ? 'estructurado'
        : 'tarea'
      ),
      estado: s.estado || 'confirmada',
      confianza: s.confianza ?? 0.8,
      nivel: s.nivel || 'intermedio',
      certificado: s.certificado || false,
    }));

    const { error: skErr } = await client.from('perfil_skills').insert(skillRows);
    if (skErr) return NextResponse.json({ error: skErr.message }, { status: 500 });
  }

  return NextResponse.json({ id, estado: 'borrador' });
}
