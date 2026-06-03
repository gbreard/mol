import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Refs:
//   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 3.2.1
//   migrations/024_spec_w_audit_actions.sql

const ACTION_TYPES = [
  'mark_task_incorrect',
  'mark_skill_incorrect',
  'add_suggested_task',
  'add_suggested_skill',
  'mark_revised',
  'mark_total_failure',
  'unmark_revised',
  'unmark_total_failure',
] as const;

const TARGET_TYPES = ['task', 'skill', 'occupation', 'oferta_global'] as const;
const SOURCES = ['human', 'auto_corrector', 'rule_engine', 'import'] as const;

type ActionType = typeof ACTION_TYPES[number];
type TargetType = typeof TARGET_TYPES[number];
type Source = typeof SOURCES[number];

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

// Resetear cliente entre tests (vitest no recarga el módulo por sí solo)
export function _resetSupabaseAdminForTests() {
  supabaseAdmin = null;
}

interface PostBody {
  id_oferta?: string;
  action_type?: ActionType;
  target_type?: TargetType;
  target_id?: string;
  target_value?: string;
  note?: string;
  run_id?: string;
  matching_version?: string;
  source?: Source;
}

export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) {
    return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });
  }

  let body: PostBody;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'JSON inválido' }, { status: 400 });
  }

  const {
    id_oferta,
    action_type,
    target_type,
    target_id,
    target_value,
    note,
    run_id,
    matching_version,
    source,
  } = body;

  // Validaciones de presencia y enum
  if (!id_oferta || typeof id_oferta !== 'string') {
    return NextResponse.json({ error: 'id_oferta requerido (string)' }, { status: 400 });
  }
  if (!action_type || !ACTION_TYPES.includes(action_type)) {
    return NextResponse.json(
      { error: `action_type inválido. Válidos: ${ACTION_TYPES.join(', ')}` },
      { status: 400 },
    );
  }
  if (target_type && !TARGET_TYPES.includes(target_type)) {
    return NextResponse.json(
      { error: `target_type inválido. Válidos: ${TARGET_TYPES.join(', ')}` },
      { status: 400 },
    );
  }
  if (source && !SOURCES.includes(source)) {
    return NextResponse.json(
      { error: `source inválido. Válidos: ${SOURCES.join(', ')}` },
      { status: 400 },
    );
  }

  // Reglas cruzadas
  const ofertaGlobalActions: ActionType[] = ['mark_revised', 'mark_total_failure', 'unmark_revised', 'unmark_total_failure'];
  if (ofertaGlobalActions.includes(action_type) && target_type && target_type !== 'oferta_global') {
    return NextResponse.json(
      { error: `${action_type} requiere target_type='oferta_global' (o ausente)` },
      { status: 400 },
    );
  }

  const taskOrSkillActions: ActionType[] = [
    'mark_task_incorrect',
    'mark_skill_incorrect',
    'add_suggested_task',
    'add_suggested_skill',
  ];
  if (taskOrSkillActions.includes(action_type)) {
    if (!target_value && !target_id) {
      return NextResponse.json(
        { error: `${action_type} requiere target_value o target_id` },
        { status: 400 },
      );
    }
    if (target_type && target_type !== 'task' && target_type !== 'skill') {
      return NextResponse.json(
        { error: `${action_type} requiere target_type='task' o 'skill'` },
        { status: 400 },
      );
    }
  }

  // Verificar que la oferta exista
  const { data: oferta, error: ofertaError } = await client
    .from('ofertas_dashboard')
    .select('id_oferta')
    .eq('id_oferta', id_oferta)
    .maybeSingle();

  if (ofertaError) {
    return NextResponse.json({ error: `Error consultando oferta: ${ofertaError.message}` }, { status: 500 });
  }
  if (!oferta) {
    return NextResponse.json({ error: `id_oferta no existe: ${id_oferta}` }, { status: 404 });
  }

  const validador = auth.user?.email || 'admin';

  // Insert audit_action
  const insertPayload = {
    id_oferta,
    validador,
    action_type,
    target_type: target_type ?? (ofertaGlobalActions.includes(action_type) ? 'oferta_global' : null),
    target_id: target_id ?? null,
    target_value: target_value ?? null,
    note: note ?? null,
    run_id: run_id ?? null,
    matching_version: matching_version ?? null,
    source: source ?? 'human',
  };

  const { data: inserted, error: insertError } = await client
    .from('audit_actions')
    .insert(insertPayload)
    .select('id')
    .single();

  if (insertError || !inserted) {
    return NextResponse.json(
      { error: `Error insertando audit_action: ${insertError?.message ?? 'unknown'}` },
      { status: 500 },
    );
  }

  // Actualizar estado_revision si corresponde
  let updatedEstadoRevision: string | null | undefined;

  if (action_type === 'mark_revised') {
    updatedEstadoRevision = 'revisada';
  } else if (action_type === 'mark_total_failure') {
    updatedEstadoRevision = 'mal_extraida_total';
  } else if (action_type === 'unmark_revised' || action_type === 'unmark_total_failure') {
    updatedEstadoRevision = null;
  }

  if (updatedEstadoRevision !== undefined) {
    const { error: updateError } = await client
      .from('ofertas_dashboard')
      .update({ estado_revision: updatedEstadoRevision })
      .eq('id_oferta', id_oferta);

    if (updateError) {
      // No abortamos — la audit_action ya quedó registrada. Solo loggeamos en la respuesta.
      return NextResponse.json(
        {
          success: true,
          action_id: inserted.id,
          estado_revision_update_error: updateError.message,
        },
        { status: 201 },
      );
    }
  }

  const response: Record<string, unknown> = { success: true, action_id: inserted.id };
  if (updatedEstadoRevision !== undefined) {
    response.updated_estado_revision = updatedEstadoRevision;
  }

  return NextResponse.json(response, { status: 201 });
}
