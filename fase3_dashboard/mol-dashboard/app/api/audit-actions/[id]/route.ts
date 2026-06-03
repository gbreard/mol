import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Refs:
//   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 3.2.2
//   docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md (Op 3 — solo mark_revised/mark_total_failure)
//
// Op 3: NO se borra fila (trigger lo rechazaría). Se INSERTA acción inversa
// y se setea estado_revision=NULL. Solo mark_revised/mark_total_failure son
// revertibles. El resto devuelve 400 "action_not_revertible".

let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  supabaseAdmin = createClient(url, key, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  return supabaseAdmin;
}

export function _resetSupabaseAdminForTests() {
  supabaseAdmin = null;
}

const REVERSIBLE: Record<string, string> = {
  mark_revised: 'unmark_revised',
  mark_total_failure: 'unmark_total_failure',
};

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function DELETE(request: NextRequest, ctx: RouteContext) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) {
    return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });
  }

  const { id: idParam } = await ctx.params;
  const id = Number(idParam);
  if (!Number.isInteger(id) || id <= 0) {
    return NextResponse.json({ error: 'id inválido' }, { status: 400 });
  }

  // Buscar acción original
  const { data: original, error: fetchError } = await client
    .from('audit_actions')
    .select('id, id_oferta, action_type, validador, target_type')
    .eq('id', id)
    .maybeSingle();

  if (fetchError) {
    return NextResponse.json(
      { error: `Error consultando audit_action: ${fetchError.message}` },
      { status: 500 },
    );
  }
  if (!original) {
    return NextResponse.json({ error: `audit_action ${id} no existe` }, { status: 404 });
  }

  const inverseAction = REVERSIBLE[original.action_type];
  if (!inverseAction) {
    return NextResponse.json(
      {
        error: 'action_not_revertible',
        message:
          'Esta acción no es revertible. Para corregir, creá una nueva acción con criterio actualizado.',
        action_type: original.action_type,
      },
      { status: 400 },
    );
  }

  const validador = auth.user?.email || 'admin';

  // INSERT acción inversa
  const { data: inserted, error: insertError } = await client
    .from('audit_actions')
    .insert({
      id_oferta: original.id_oferta,
      validador,
      action_type: inverseAction,
      target_type: 'oferta_global',
      target_id: null,
      target_value: null,
      note: `Reversión de audit_action ${original.id}`,
      source: 'human',
    })
    .select('id')
    .single();

  if (insertError || !inserted) {
    return NextResponse.json(
      { error: `Error insertando acción inversa: ${insertError?.message ?? 'unknown'}` },
      { status: 500 },
    );
  }

  // UPDATE estado_revision = NULL
  const { error: updateError } = await client
    .from('ofertas_dashboard')
    .update({ estado_revision: null })
    .eq('id_oferta', original.id_oferta);

  if (updateError) {
    return NextResponse.json(
      {
        reverted: true,
        action_id: inserted.id,
        estado_revision_update_error: updateError.message,
      },
      { status: 200 },
    );
  }

  return NextResponse.json(
    {
      reverted: true,
      action_id: inserted.id,
    },
    { status: 200 },
  );
}
