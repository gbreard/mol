/**
 * POST /api/issues/[id]/propagation/dry-run
 *
 * Admin estima cuántas ofertas matchean un patrón sin aplicar cambios.
 * Invoca scripts/correcciones/propagate_correction.py via subprocess,
 * pasando el patrón JSON via stdin (sin filesystem writes).
 *
 * SPEC T Fase 4. Auth: requireAdmin.
 * Body: { patron: PropagationPattern }
 */
import { spawn } from "node:child_process";
import { NextRequest, NextResponse } from "next/server";
import { requireAdmin, isAuthError } from "@/lib/api-auth";

const PROJECT_ROOT = process.env.MOL_PROJECT_ROOT ?? "/mnt/d/OEDE/Webscrapping";
const SCRIPT_PATH = `${PROJECT_ROOT}/scripts/correcciones/propagate_correction.py`;

export interface RunOptions {
  patron: unknown;
  apply: boolean;
  issueId?: string;
}

/**
 * Ejecuta el script Python de propagación pasando el patrón via stdin.
 * No escribe a filesystem.
 */
export async function runPropagate({ patron, apply, issueId }: RunOptions): Promise<unknown> {
  const args = [SCRIPT_PATH, "-"];
  if (apply) args.push("--apply");
  if (issueId) args.push("--issue-id", issueId);
  if (!apply || !issueId) args.push("--no-update-issue");

  return new Promise((resolve, reject) => {
    const proc = spawn("python3", args, { cwd: PROJECT_ROOT });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => (stdout += d.toString()));
    proc.stderr.on("data", (d) => (stderr += d.toString()));
    proc.on("close", (code) => {
      try {
        // El script imprime JSON al final del stdout
        const jsonStart = stdout.lastIndexOf("{\n");
        const jsonText = jsonStart >= 0 ? stdout.slice(jsonStart) : stdout;
        const parsed = JSON.parse(jsonText);
        resolve(parsed);
      } catch (e) {
        reject(
          new Error(
            `propagate_correction exit=${code}, parse failed: ${(e as Error).message}\nstdout=${stdout.slice(0, 500)}\nstderr=${stderr.slice(0, 500)}`
          )
        );
      }
    });
    proc.on("error", (e) => reject(e));

    // Pasar el patrón JSON via stdin (no filesystem)
    proc.stdin.write(JSON.stringify(patron));
    proc.stdin.end();
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const { id: issueId } = await params;
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
    const result = await runPropagate({ patron: body.patron, apply: false });
    return NextResponse.json({ issue_id: issueId, result });
  } catch (e) {
    console.error("[dry-run] error:", e);
    return NextResponse.json({ error: (e as Error).message }, { status: 500 });
  }
}
