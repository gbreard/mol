/**
 * POST /api/issues/[id]/propagation/rechazar
 *
 * Admin rechaza una solicitud de propagación (decide que no aplica).
 * Marca propagacion_solicitada=false y deja propagacion_n=0.
 *
 * SPEC T Fase 4. Auth: requireAdmin.
 * Body: { motivo?: string }
 */
import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";
import { requireAdmin, isAuthError } from "@/lib/api-auth";

function getServiceClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  return createClient(url, key, { auth: { autoRefreshToken: false, persistSession: false } });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const { id: issueId } = await params;
  let body: { motivo?: string };
  try {
    body = await request.json();
  } catch {
    body = {};
  }
  const motivo = (body.motivo ?? "").trim();

  const sb = getServiceClient();
  if (!sb) return NextResponse.json({ error: "Service no configurado" }, { status: 503 });

  const adminEmail = auth.user.email ?? "admin";
  const ahora = new Date().toISOString();

  const { error: updateErr } = await sb
    .from("issues")
    .update({
      propagacion_solicitada: false,
      propagacion_n: 0,
      patron_corregido: {
        _audit_note: `SPEC T Fase 4 — solicitud rechazada por ${adminEmail} el ${ahora.slice(0, 16)}.${motivo ? " Motivo: " + motivo : ""}`,
        _audit_at: ahora,
        rechazada_por: adminEmail,
        rechazada_motivo: motivo || null,
      },
    })
    .eq("id", issueId);

  if (updateErr) {
    console.error("[rechazar] update error:", updateErr);
    return NextResponse.json({ error: updateErr.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true, rechazada_por: adminEmail });
}
