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

// A4 — POST /api/perfiles/:id/skills — agregar skills al perfil
export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  // TODO OE-11: restore requireAuth
  // const auth = await requireAuth(request);
  // if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { id: perfilId } = await params;
  const body = await request.json();
  const { skills } = body;

  if (!skills || !Array.isArray(skills) || skills.length === 0) {
    return NextResponse.json({ error: 'Falta skills[]' }, { status: 400 });
  }

  // Insert skills
  const rows = skills.map((s: any) => ({
    perfil_id: perfilId,
    skill_uri: s.skill_uri,
    skill_label: s.skill_label,
    via_captura: s.via_captura || 'tarea',
    estado: s.estado || 'sugerida',
    confianza: s.confianza || 0.5,
    nivel: s.nivel || 'intermedio',
    certificado: s.certificado || false,
    validado_por_tecnico: s.validado_por_tecnico || false,
  }));

  const { error: insertErr } = await client.from('perfil_skills').insert(rows);
  if (insertErr) return NextResponse.json({ error: insertErr.message }, { status: 500 });

  // Recalculate completitud
  const { count } = await client.from('perfil_skills')
    .select('*', { count: 'exact', head: true })
    .eq('perfil_id', perfilId)
    .eq('estado', 'confirmada');

  const completitud = count || 0;
  await client.from('perfiles').update({ completitud }).eq('id', perfilId);

  // If completitud >= 3, check if there's a caso to update
  if (completitud >= 3) {
    const { data: perfil } = await client.from('perfiles').select('persona_id').eq('id', perfilId).maybeSingle();
    if (perfil) {
      await client.from('casos')
        .update({ estado: 'perfil_completo' })
        .eq('persona_id', perfil.persona_id)
        .in('estado', ['nuevo', 'en_diagnostico']);
    }
  }

  // Return updated profile
  const { data: allSkills } = await client.from('perfil_skills')
    .select('*').eq('perfil_id', perfilId).order('created_at');

  return NextResponse.json({ perfil_id: perfilId, completitud, skills: allSkills });
}

// A5 — PATCH /api/perfiles/:id/skills — update skill estado
export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  // TODO OE-11: restore requireAuth
  // const auth = await requireAuth(request);
  // if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { id: perfilId } = await params;
  const body = await request.json();
  const { skill_id, estado } = body;

  if (!skill_id || !estado) return NextResponse.json({ error: 'Falta skill_id o estado' }, { status: 400 });

  const { error } = await client.from('perfil_skills')
    .update({ estado })
    .eq('id', skill_id)
    .eq('perfil_id', perfilId);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Recalculate completitud
  const { count } = await client.from('perfil_skills')
    .select('*', { count: 'exact', head: true })
    .eq('perfil_id', perfilId)
    .eq('estado', 'confirmada');

  const completitud = count || 0;
  await client.from('perfiles').update({ completitud }).eq('id', perfilId);

  return NextResponse.json({ perfil_id: perfilId, completitud, skill_id, estado });
}
