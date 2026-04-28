/**
 * POST /api/issues/[id]/solicitar-propagacion
 *
 * Analista (Cyn/Diego) solicita que la corrección de un issue se propague
 * a otras ofertas similares. NO aplica el cambio — solo entra a cola admin.
 *
 * SPEC T Fase 4. Auth: requireAuth (cualquier usuario autenticado).
 * Body: { justificacion: string, tipo_aproximado?: string }
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
  if (!issueId) {
    return NextResponse.json({ error: "issue id requerido" }, { status: 400 });
  }

  let body: { justificacion?: string; tipo_aproximado?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "JSON inválido" }, { status: 400 });
  }

  const justificacion = (body.justificacion ?? "").trim();
  if (justificacion.length < 5) {
    return NextResponse.json(
      { error: "Justificación obligatoria (≥5 caracteres)" },
      { status: 400 }
    );
  }

  const sb = getServiceClient();
  if (!sb) {
    return NextResponse.json({ error: "Service no configurado" }, { status: 503 });
  }

  // Verificar que el issue existe
  const { data: issue, error: fetchErr } = await sb
    .from("issues")
    .select("id, propagacion_solicitada, propagacion_n")
    .eq("id", issueId)
    .single();

  if (fetchErr || !issue) {
    return NextResponse.json({ error: "Issue no encontrado" }, { status: 404 });
  }

  if (issue.propagacion_solicitada) {
    return NextResponse.json(
      { error: "Esta solicitud ya existe y está pendiente." },
      { status: 409 }
    );
  }

  if (issue.propagacion_n && issue.propagacion_n > 0) {
    return NextResponse.json(
      { error: "Este issue ya tiene propagación aplicada." },
      { status: 409 }
    );
  }

  // Construir nota para descripcion (manteniendo lo previo + log de solicitud)
  const userEmail = auth.user.email ?? "desconocido";
  const tipo = body.tipo_aproximado ?? "no_especificado";
  const notaSolicitud = `\n\n---\n[SOLICITUD DE PROPAGACIÓN ${new Date().toISOString().slice(0, 16).replace("T", " ")}]\nSolicitado por: ${userEmail}\nTipo aproximado: ${tipo}\nJustificación: ${justificacion}`;

  const { error: updateErr } = await sb
    .from("issues")
    .update({
      propagacion_solicitada: true,
      propagacion_solicitada_por: userEmail,
      propagacion_solicitada_at: new Date().toISOString(),
    })
    .eq("id", issueId);

  if (updateErr) {
    return NextResponse.json({ error: updateErr.message }, { status: 500 });
  }

  // Append nota a descripción para que admin vea contexto al procesar.
  // Si la RPC no existe, ignoramos — la nota queda en log de solicitud.
  try {
    await sb.rpc("append_issue_descripcion", {
      p_issue_id: issueId,
      p_texto: notaSolicitud,
    });
  } catch {
    // Silently ignore — RPC opcional
  }

  return NextResponse.json({
    ok: true,
    issue_id: issueId,
    solicitada_por: userEmail,
    solicitada_at: new Date().toISOString(),
  });
}
