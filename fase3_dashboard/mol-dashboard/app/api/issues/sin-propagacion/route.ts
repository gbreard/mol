/**
 * GET /api/issues/sin-propagacion
 *
 * Devuelve issues humanos resueltos sin patron_corregido o con patron
 * "audit-no-pattern-detected" (los 462 retrospectivos de SPEC T Fase 3).
 *
 * Visible para todos los autenticados (analistas pueden marcarlos para
 * solicitar propagación).
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

export async function GET(request: NextRequest) {
  const auth = await requireAuth(request);
  if (isAuthError(auth)) return auth;

  const sb = getServiceClient();
  if (!sb) return NextResponse.json({ error: "Service no configurado" }, { status: 503 });

  const { data, error } = await sb
    .from("issues")
    .select(
      "id, titulo, tipo, prioridad, id_oferta, autor_nombre, " +
      "autor_email, created_at, resuelto_at, patron_corregido, propagacion_solicitada"
    )
    .eq("estado", "resuelto")
    .neq("autor_email", "auto-validator@mol.gob.ar")
    .or("propagacion_n.is.null,propagacion_n.eq.0")
    .order("created_at", { ascending: false })
    .limit(500);

  if (error) {
    console.error("[sin-propagacion] error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // Filtrar los que TIENEN patron pero solo es _audit_note (los 462 retrospectivos)
  type IssueRow = {
    id: string;
    patron_corregido?: Record<string, unknown> | null;
    propagacion_solicitada?: boolean | null;
  };
  const items = ((data ?? []) as unknown as IssueRow[]).filter((i) => {
    if (!i.patron_corregido) return true;
    return !!i.patron_corregido._audit_note && !i.propagacion_solicitada;
  });

  return NextResponse.json({ items, count: items.length });
}
