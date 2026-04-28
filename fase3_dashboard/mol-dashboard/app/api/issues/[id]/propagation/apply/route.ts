/**
 * POST /api/issues/[id]/propagation/apply
 *
 * Admin aplica una propagación tras dry-run + revisión.
 * Invoca el script Python con --apply, y este actualiza el issue con
 * patron_corregido + propagacion_n + propagacion_ids automáticamente.
 *
 * SPEC T Fase 4. Auth: requireAdmin.
 * Body: { patron: PropagationPattern }
 */
import { NextRequest, NextResponse } from "next/server";
import { requireAdmin, isAuthError } from "@/lib/api-auth";
import { runPropagate } from "../dry-run/route";

export const maxDuration = 600; // 10 min — re-rematch puede tardar para reglas grandes

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const { id: issueId } = await params;
  if (!issueId) {
    return NextResponse.json({ error: "issue id requerido" }, { status: 400 });
  }

  let body: { patron?: unknown };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "JSON inválido" }, { status: 400 });
  }
  if (!body.patron) {
    return NextResponse.json({ error: "patron requerido" }, { status: 400 });
  }

  try {
    const result = await runPropagate({
      patron: body.patron,
      apply: true,
      issueId,
    });
    return NextResponse.json({
      issue_id: issueId,
      applied_by: auth.user.email ?? "?",
      result,
    });
  } catch (e) {
    console.error("[apply] error:", e);
    return NextResponse.json({ error: (e as Error).message }, { status: 500 });
  }
}
