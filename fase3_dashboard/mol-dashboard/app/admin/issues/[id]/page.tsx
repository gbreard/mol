/**
 * /admin/issues/[id]
 *
 * Página detalle de un issue. Muestra info + paneles de propagación
 * (read-only para analistas, panel admin para gerardo).
 *
 * SPEC T Fase 4 — pantalla nueva.
 */
"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2, ArrowLeft } from "lucide-react";

import { createBrowserClient } from "@/lib/supabase/browser";
import {
  PropagationInfoPanel,
  ProcessPropagationPanel,
  RequestPropagationModal,
} from "@/components/issues";
import type { Issue } from "@/lib/types";
import { isAdmin, type Role } from "@/lib/user";

export default function IssueDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;

  const [issue, setIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<Role>("viewer");
  const [showSolicitarModal, setShowSolicitarModal] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const sb = createBrowserClient();
      const [{ data: userData }, issueRes] = await Promise.all([
        sb.auth.getUser(),
        sb.from("issues").select("*").eq("id", id).single(),
      ]);
      if (issueRes.error) throw issueRes.error;
      setIssue(issueRes.data as Issue);
      const r = (userData.user?.user_metadata?.role as Role) || "viewer";
      setRole(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleCancelarSolicitud() {
    if (!issue) return;
    if (!confirm("¿Cancelar la solicitud de propagación?")) return;
    const res = await fetch(`/api/issues/${issue.id}/cancelar-solicitud`, {
      method: "POST",
    });
    if (res.ok) {
      load();
    } else {
      alert("Error al cancelar");
    }
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center gap-2 text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" /> Cargando...
      </div>
    );
  }

  if (error || !issue) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded p-4">
          <p className="text-sm text-red-700 dark:text-red-400">
            Error: {error ?? "Issue no encontrado"}
          </p>
          <button
            type="button"
            onClick={() => router.push("/admin/issues")}
            className="mt-2 text-sm text-blue-600 hover:underline"
          >
            ← Volver a Issues
          </button>
        </div>
      </div>
    );
  }

  const admin = isAdmin(role);
  const isResolved = issue.estado === "resuelto";
  const showProcessPanel = admin && (issue.propagacion_solicitada || isResolved);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-4">
      <Link
        href="/admin/issues"
        className="text-sm text-blue-600 hover:underline inline-flex items-center gap-1"
      >
        <ArrowLeft className="w-4 h-4" /> Volver a Issues
      </Link>

      <header className="space-y-2">
        <h1 className="text-2xl font-bold">{issue.titulo}</h1>
        <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
          <span>ID: {issue.id.slice(0, 8)}</span>
          <span>·</span>
          <span>Tipo: {issue.tipo}</span>
          <span>·</span>
          <span>Estado: {issue.estado}</span>
          <span>·</span>
          <span>Prioridad: {issue.prioridad}</span>
          {issue.id_oferta && (
            <>
              <span>·</span>
              <Link
                href={`/admin/validacion?id=${issue.id_oferta}`}
                className="text-blue-600 hover:underline"
              >
                Oferta: {issue.id_oferta}
              </Link>
            </>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          Por <b>{issue.autor_nombre ?? issue.autor_email}</b> el{" "}
          {new Date(issue.created_at).toLocaleString("es-AR")}
        </p>
      </header>

      {issue.descripcion && (
        <section className="border rounded p-4 bg-card">
          <h3 className="text-sm font-semibold mb-2">Descripción</h3>
          <p className="text-sm whitespace-pre-wrap">{issue.descripcion}</p>
        </section>
      )}

      {issue.solucion_aplicada && (
        <section className="border rounded p-4 bg-card">
          <h3 className="text-sm font-semibold mb-2">Solución aplicada</h3>
          <p className="text-sm whitespace-pre-wrap">{issue.solucion_aplicada}</p>
          {issue.config_modificada && (
            <p className="text-xs text-muted-foreground mt-2">
              Config modificada: <code className="bg-muted px-1 rounded">{issue.config_modificada}</code>
            </p>
          )}
        </section>
      )}

      <PropagationInfoPanel
        issue={issue}
        isAdmin={admin}
        onSolicitar={() => setShowSolicitarModal(true)}
        onCancelarSolicitud={handleCancelarSolicitud}
      />

      {showProcessPanel && (
        <div id="propagacion">
          <ProcessPropagationPanel issue={issue} onApplied={load} />
        </div>
      )}

      <RequestPropagationModal
        issueId={issue.id}
        open={showSolicitarModal}
        onClose={() => setShowSolicitarModal(false)}
        onSubmitted={() => {
          setShowSolicitarModal(false);
          load();
        }}
      />
    </div>
  );
}
