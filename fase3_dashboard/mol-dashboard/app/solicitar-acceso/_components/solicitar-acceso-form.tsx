"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, CheckCircle2, Send } from "lucide-react";
import { createBrowserClient } from "@/lib/supabase/browser";

interface Props {
  email: string;
  displayName: string;
}

export function SolicitarAccesoForm({ email, displayName }: Props) {
  const router = useRouter();
  const [nombre, setNombre] = useState(displayName);
  const [organizacion, setOrganizacion] = useState("");
  const [motivo, setMotivo] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const supabase = createBrowserClient();
      const { error: rpcError } = await supabase.rpc("crear_solicitud_acceso", {
        p_nombre: nombre,
        p_organizacion: organizacion || null,
        p_motivo: motivo,
      });

      if (rpcError) {
        throw new Error(rpcError.message);
      }

      setSuccess(true);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al enviar solicitud";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
        <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto mb-3" />
        <h2 className="font-semibold text-green-800 mb-2">Solicitud enviada</h2>
        <p className="text-sm text-green-700 mb-4">
          Un administrador revisara tu solicitud. Te notificaremos cuando sea
          aprobada.
        </p>
        <button
          onClick={() => router.push("/home")}
          className="text-sm text-green-700 underline hover:text-green-800"
        >
          Volver al inicio
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <input
          type="email"
          value={email}
          disabled
          className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Nombre completo *
        </label>
        <input
          type="text"
          required
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          placeholder="Tu nombre"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Organizacion
        </label>
        <input
          type="text"
          value={organizacion}
          onChange={(e) => setOrganizacion(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          placeholder="Nombre de tu organizacion (opcional)"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Motivo de la solicitud *
        </label>
        <textarea
          required
          rows={3}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
          placeholder="Contanos brevemente para que necesitas acceso al tablero..."
        />
      </div>

      <button
        type="submit"
        disabled={submitting || !nombre.trim() || !motivo.trim()}
        className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white font-medium text-sm px-6 py-3 rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {submitting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Send className="w-4 h-4" />
        )}
        Enviar solicitud
      </button>
    </form>
  );
}
