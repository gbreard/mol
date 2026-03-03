"use client";

import { useState, useEffect } from "react";
import {
  UserPlus,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Building2,
  MessageSquare,
} from "lucide-react";
import { createBrowserClient } from "@/lib/supabase/browser";
import type { SolicitudAcceso, SolicitudEstado } from "@/lib/types";

const TABS: { key: SolicitudEstado | "todas"; label: string }[] = [
  { key: "pendiente", label: "Pendientes" },
  { key: "aprobada", label: "Aprobadas" },
  { key: "rechazada", label: "Rechazadas" },
  { key: "todas", label: "Todas" },
];

export default function SolicitudesPage() {
  const [solicitudes, setSolicitudes] = useState<SolicitudAcceso[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<SolicitudEstado | "todas">("pendiente");
  const [processing, setProcessing] = useState<string | null>(null);
  const [notasModal, setNotasModal] = useState<{
    solicitudId: string;
    action: "aprobar" | "rechazar";
  } | null>(null);
  const [notas, setNotas] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createBrowserClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.access_token) {
        loadSolicitudes(session.access_token);
      } else {
        setLoading(false);
      }
    });
  }, []);

  async function loadSolicitudes(accessToken: string) {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("/api/admin/solicitudes", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Error al cargar solicitudes");
      }
      const data = await response.json();
      setSolicitudes(data.solicitudes || []);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(solicitudId: string, action: "aprobar" | "rechazar") {
    setProcessing(solicitudId);
    setError(null);
    setSuccess(null);

    try {
      const supabase = createBrowserClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) throw new Error("No autenticado");

      const response = await fetch("/api/admin/solicitudes", {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ solicitudId, action, notas: notas || undefined }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Error al procesar solicitud");
      }

      const sol = solicitudes.find((s) => s.id === solicitudId);
      if (action === "aprobar") {
        setSuccess(`Trial de 7 dias activado para ${sol?.email || "usuario"}`);
      } else {
        setSuccess(`Solicitud de ${sol?.email || "usuario"} rechazada`);
      }

      setNotasModal(null);
      setNotas("");

      // Reload
      loadSolicitudes(session.access_token);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      setError(message);
    } finally {
      setProcessing(null);
    }
  }

  const filtered =
    activeTab === "todas"
      ? solicitudes
      : solicitudes.filter((s) => s.estado === activeTab);

  const pendingCount = solicitudes.filter((s) => s.estado === "pendiente").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center gap-3 mb-8">
        <UserPlus className="w-8 h-8 text-purple-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Solicitudes de Acceso</h1>
          <p className="text-gray-500 mt-1">
            {pendingCount > 0
              ? `${pendingCount} solicitud${pendingCount > 1 ? "es" : ""} pendiente${pendingCount > 1 ? "s" : ""}`
              : "No hay solicitudes pendientes"}
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          {success}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
            {tab.key === "pendiente" && pendingCount > 0 && (
              <span className="ml-1.5 bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded-full">
                {pendingCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                Solicitante
              </th>
              <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                Organizacion
              </th>
              <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                Motivo
              </th>
              <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                Fecha
              </th>
              <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                Estado
              </th>
              <th className="text-right px-6 py-4 text-sm font-semibold text-gray-900">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filtered.map((sol) => (
              <tr key={sol.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <p className="font-medium text-gray-900 text-sm">{sol.nombre}</p>
                  <p className="text-xs text-gray-500">{sol.email}</p>
                </td>
                <td className="px-6 py-4">
                  {sol.organizacion ? (
                    <span className="flex items-center gap-1.5 text-sm text-gray-700">
                      <Building2 className="w-3.5 h-3.5 text-gray-400" />
                      {sol.organizacion}
                    </span>
                  ) : (
                    <span className="text-xs text-gray-400">-</span>
                  )}
                </td>
                <td className="px-6 py-4 max-w-xs">
                  <p className="text-sm text-gray-700 truncate">{sol.motivo}</p>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {new Date(sol.created_at).toLocaleDateString("es-AR")}
                </td>
                <td className="px-6 py-4">
                  <EstadoBadge estado={sol.estado} />
                </td>
                <td className="px-6 py-4 text-right">
                  {sol.estado === "pendiente" ? (
                    <div className="flex items-center gap-2 justify-end">
                      <button
                        onClick={() =>
                          setNotasModal({ solicitudId: sol.id, action: "aprobar" })
                        }
                        disabled={processing === sol.id}
                        className="flex items-center gap-1 px-3 py-1.5 bg-green-50 text-green-700 text-xs font-medium rounded-lg hover:bg-green-100 transition-colors disabled:opacity-50"
                      >
                        {processing === sol.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <CheckCircle2 className="w-3 h-3" />
                        )}
                        Aprobar
                      </button>
                      <button
                        onClick={() =>
                          setNotasModal({ solicitudId: sol.id, action: "rechazar" })
                        }
                        disabled={processing === sol.id}
                        className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-700 text-xs font-medium rounded-lg hover:bg-red-100 transition-colors disabled:opacity-50"
                      >
                        <XCircle className="w-3 h-3" />
                        Rechazar
                      </button>
                    </div>
                  ) : (
                    sol.notas_admin && (
                      <span className="flex items-center gap-1 text-xs text-gray-400 justify-end">
                        <MessageSquare className="w-3 h-3" />
                        {sol.revisado_por}
                      </span>
                    )
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-500 text-sm">
            No hay solicitudes en esta categoria
          </div>
        )}
      </div>

      {/* Modal notas */}
      {notasModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              {notasModal.action === "aprobar"
                ? "Aprobar solicitud"
                : "Rechazar solicitud"}
            </h2>
            <p className="text-sm text-gray-500 mb-4">
              {notasModal.action === "aprobar"
                ? "Se activara un trial de 7 dias para el usuario."
                : "El usuario sera notificado del rechazo."}
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notas (opcional)
              </label>
              <textarea
                rows={3}
                value={notas}
                onChange={(e) => setNotas(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 resize-none"
                placeholder="Notas internas..."
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setNotasModal(null);
                  setNotas("");
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() =>
                  handleAction(notasModal.solicitudId, notasModal.action)
                }
                disabled={!!processing}
                className={`flex-1 px-4 py-2 text-white text-sm rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 ${
                  notasModal.action === "aprobar"
                    ? "bg-green-600 hover:bg-green-700"
                    : "bg-red-600 hover:bg-red-700"
                }`}
              >
                {processing && <Loader2 className="w-4 h-4 animate-spin" />}
                {notasModal.action === "aprobar" ? "Aprobar" : "Rechazar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EstadoBadge({ estado }: { estado: string }) {
  const config: Record<string, { icon: typeof Clock; className: string; label: string }> = {
    pendiente: {
      icon: Clock,
      className: "bg-orange-100 text-orange-700",
      label: "Pendiente",
    },
    aprobada: {
      icon: CheckCircle2,
      className: "bg-green-100 text-green-700",
      label: "Aprobada",
    },
    rechazada: {
      icon: XCircle,
      className: "bg-red-100 text-red-700",
      label: "Rechazada",
    },
  };

  const c = config[estado] || config.pendiente;
  const Icon = c.icon;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${c.className}`}
    >
      <Icon className="w-3 h-3" />
      {c.label}
    </span>
  );
}
