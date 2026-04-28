/**
 * POST /api/issues/[id]/cancelar-solicitud
 *
 * El solicitante (o un admin) cancela una solicitud de propagación pendiente.
 * SPEC T Fase 4.
 */
import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";
import { requireAuth, isAuthError } from "@/lib/api-auth";

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
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const { id: issueId } = await params;
  const sb = getServiceClient();
  if (!sb) return NextResponse.json({ error: "Service no configurado" }, { status: 503 });

  const { data: issue, error: fetchErr } = await sb
    .from("issues")
    .select("propagacion_solicitada, propagacion_solicitada_por, propagacion_n")
    .eq("id", issueId)
    .single();

  if (fetchErr || !issue) {
    return NextResponse.json({ error: "Issue no encontrado" }, { status: 404 });
  }

  if (!issue.propagacion_solicitada) {
    return NextResponse.json(
      { error: "No hay solicitud pendiente que cancelar" },
      { status: 409 }
    );
  }

  if (issue.propagacion_n && issue.propagacion_n > 0) {
    return NextResponse.json(
      { error: "Propagación ya aplicada — no se puede cancelar" },
      { status: 409 }
    );
  }

  // Solo el solicitante o admin pueden cancelar
  const userEmail = auth.user.email ?? "";
  const isAdmin = auth.role === "admin" || auth.role === "super_admin";
  if (!isAdmin && issue.propagacion_solicitada_por !== userEmail) {
    return NextResponse.json(
      { error: "Solo el solicitante o un admin pueden cancelar" },
      { status: 403 }
    );
  }

  const { error: updateErr } = await sb
    .from("issues")
    .update({
      propagacion_solicitada: false,
      propagacion_solicitada_por: null,
      propagacion_solicitada_at: null,
    })
    .eq("id", issueId);

  if (updateErr) {
    console.error("[cancelar-solicitud] update error:", updateErr);
    return NextResponse.json({ error: updateErr.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
