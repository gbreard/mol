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

// GET: listar skills del catálogo (con filtros opcionales)
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const estado = request.nextUrl.searchParams.get('estado');
  const tipo = request.nextUrl.searchParams.get('tipo');
  const search = request.nextUrl.searchParams.get('search');
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '100');
  const offset = parseInt(request.nextUrl.searchParams.get('offset') || '0');

  let query = client.from('catalogo_mol_skills').select('*', { count: 'exact' });

  if (estado) query = query.eq('estado', estado);
  if (tipo) query = query.eq('tipo', tipo);
  if (search) query = query.ilike('label', `%${search}%`);

  query = query.order('frecuencia_mercado', { ascending: false }).range(offset, offset + limit - 1);

  const { data, error, count } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ skills: data, total: count });
}

// POST: crear nueva skill en el catálogo
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { label, definicion, tipo, categoria_l1, categoria_l2, esco_parent_uri, esco_parent_label, relaciones, estado, notas } = body;

  if (!label) return NextResponse.json({ error: 'Falta label' }, { status: 400 });

  const id = 'mol-skill-' + label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+$/, '');
  const label_normalized = label.toLowerCase().trim();

  const adminEmail = auth.user?.email || 'admin';

  const record: Record<string, any> = {
    id,
    label,
    label_normalized,
    definicion: definicion || null,
    tipo: tipo || 'skill',
    categoria_l1: categoria_l1 || null,
    categoria_l2: categoria_l2 || null,
    source: 'mol_catalogo',
    esco_parent_uri: esco_parent_uri || null,
    esco_parent_label: esco_parent_label || null,
    relaciones: relaciones || [],
    estado: estado || 'detectada',
    notas: notas || null,
    primera_deteccion: new Date().toISOString().split('T')[0],
  };

  if (estado === 'catalogada') {
    record.aprobada_por = adminEmail;
    record.aprobada_at = new Date().toISOString();
  }

  const { data, error } = await client.from('catalogo_mol_skills').upsert(record, { onConflict: 'id' }).select().single();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data, { status: 201 });
}

// PUT: actualizar skill existente
export async function PUT(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { id, ...updates } = body;

  if (!id) return NextResponse.json({ error: 'Falta id' }, { status: 400 });

  const adminEmail = auth.user?.email || 'admin';

  // Si cambia a catalogada, registrar quién aprobó
  if (updates.estado === 'catalogada') {
    updates.aprobada_por = adminEmail;
    updates.aprobada_at = new Date().toISOString();
  }

  const { data, error } = await client.from('catalogo_mol_skills').update(updates).eq('id', id).select().single();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json(data);
}

// DELETE: eliminar skill (soft delete → estado descartada)
export async function DELETE(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const id = request.nextUrl.searchParams.get('id');
  if (!id) return NextResponse.json({ error: 'Falta id' }, { status: 400 });

  const { error } = await client.from('catalogo_mol_skills').update({ estado: 'descartada' }).eq('id', id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ ok: true });
}
