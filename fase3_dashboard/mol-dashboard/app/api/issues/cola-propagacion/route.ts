/**
 * GET /api/issues/cola-propagacion
 *
 * Devuelve issues con propagacion_solicitada=true y aún no aplicada.
 * Solo accesible por admin.
 *
 * SPEC T Fase 4.
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

export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const sb = getServiceClient();
  if (!sb) return NextResponse.json({ error: "Service no configurado" }, { status: 503 });

  const { data, error } = await sb
    .from("issues")
    .select(
      "id, titulo, descripcion, tipo, estado, prioridad, id_oferta, autor_nombre, " +
      "autor_email, created_at, resuelto_at, propagacion_solicitada_por, " +
      "propagacion_solicitada_at, patron_corregido"
    )
    .eq("propagacion_solicitada", true)
    .or("propagacion_n.is.null,propagacion_n.eq.0")
    .order("propagacion_solicitada_at", { ascending: true });

  if (error) {
    console.error("[cola-propagacion] error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ items: data ?? [], count: (data ?? []).length });
}
