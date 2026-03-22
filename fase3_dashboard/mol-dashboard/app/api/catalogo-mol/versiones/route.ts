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

// GET: listar versiones del catálogo
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const { data, error } = await client
    .from('catalogo_mol_versiones')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ versiones: data });
}

// POST: crear nueva versión (corte del catálogo)
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { version, nota } = body;

  if (!version) return NextResponse.json({ error: 'Falta version' }, { status: 400 });

  const adminEmail = auth.user?.email || 'admin';

  // Count current catalogadas
  const { count: skillsCount } = await client
    .from('catalogo_mol_skills')
    .select('*', { count: 'exact', head: true })
    .eq('estado', 'catalogada');

  const { count: ocupCount } = await client
    .from('catalogo_mol_ocupaciones')
    .select('*', { count: 'exact', head: true })
    .eq('estado', 'catalogada');

  // Get previous version to calculate deltas
  const { data: prevVersion } = await client
    .from('catalogo_mol_versiones')
    .select('total_skills, total_ocupaciones')
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();

  const prevSkills = prevVersion?.total_skills || 0;
  const prevOcup = prevVersion?.total_ocupaciones || 0;

  // Count descartadas since last version
  const { count: descartadasCount } = await client
    .from('catalogo_mol_skills')
    .select('*', { count: 'exact', head: true })
    .eq('estado', 'descartada');

  const { data, error } = await client.from('catalogo_mol_versiones').insert({
    version,
    total_skills: skillsCount || 0,
    total_ocupaciones: ocupCount || 0,
    skills_nuevas: (skillsCount || 0) - prevSkills,
    ocupaciones_nuevas: (ocupCount || 0) - prevOcup,
    skills_descartadas: descartadasCount || 0,
    nota: nota || null,
    creado_por: adminEmail,
  }).select().single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Update version_catalogo on all catalogadas that don't have one
  await client.from('catalogo_mol_skills')
    .update({ version_catalogo: version })
    .eq('estado', 'catalogada')
    .is('version_catalogo', null);

  await client.from('catalogo_mol_ocupaciones')
    .update({ version_catalogo: version })
    .eq('estado', 'catalogada')
    .is('version_catalogo', null);

  return NextResponse.json(data, { status: 201 });
}
