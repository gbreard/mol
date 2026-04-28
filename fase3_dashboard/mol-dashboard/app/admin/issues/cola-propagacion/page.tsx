/**
 * /admin/issues/cola-propagacion
 *
 * Pantalla admin con la cola de solicitudes de propagación pendientes.
 * Solo accesible por usuarios con rol admin/super_admin (chequeo en API).
 *
 * SPEC T Fase 4.
 */
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";

interface ColaItem {
  id: string;
  titulo: string;
  descripcion?: string;
  tipo: string;
  estado: string;
  prioridad: string;
  id_oferta?: string;
  autor_nombre?: string;
  autor_email?: string;
  created_at: string;
  resuelto_at?: string;
  propagacion_solicitada_por?: string;
  propagacion_solicitada_at?: string;
  patron_corregido?: unknown;
}

export default function ColaPropagacionPage() {
  const [items, setItems] = useState<ColaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch("/api/issues/cola-propagacion");
        if (!res.ok) {
          if (res.status === 401 || res.status === 403) {
            throw new Error(
              "Esta sección es solo para admin. Vos podés solicitar propagaciones, pero quien las aplica es el admin."
            );
          }
          const j = await res.json().catch(() => ({}));
          throw new Error(j.error ?? `HTTP ${res.status}`);
        }
        const j = await res.json();
        if (!cancelled) setItems(j.items ?? []);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="p-6 flex items-center gap-2 text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        Cargando cola...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-800 rounded p-4 max-w-2xl">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
            <div>
              <h2 className="font-semibold mb-1">🔒 Acceso restringido</h2>
              <p className="text-sm">{error}</p>
              <Link
                href="/admin/issues"
                className="mt-3 inline-block text-sm text-blue-600 hover:underline"
              >
                ← Volver a Issues
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Cola de propagación</h1>
        <p className="text-sm text-muted-foreground mt-1">
          🟡 {items.length} solicitudes pendientes — analistas piden que la
          corrección se aplique a otras ofertas similares.
        </p>
      </header>

      {items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          ✅ No hay solicitudes pendientes.
        </div>
      ) : (
        <div className="border rounded-lg overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-left">
              <tr>
                <th className="px-4 py-2 font-medium">Solicitada</th>
                <th className="px-4 py-2 font-medium">Issue</th>
                <th className="px-4 py-2 font-medium">Solicitante</th>
                <th className="px-4 py-2 font-medium">Tipo issue</th>
                <th className="px-4 py-2 font-medium">Acción</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t hover:bg-muted/50">
                  <td className="px-4 py-2 text-xs text-muted-foreground whitespace-nowrap">
                    {item.propagacion_solicitada_at
                      ? new Date(item.propagacion_solicitada_at).toLocaleString("es-AR", {
                          dateStyle: "short",
                          timeStyle: "short",
                        })
                      : "—"}
                  </td>
                  <td className="px-4 py-2">
                    <Link
                      href={`/admin/issues/${item.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      {item.titulo.slice(0, 70)}
                      {item.titulo.length > 70 && "..."}
                    </Link>
                    {item.id_oferta && (
                      <span className="block text-xs text-muted-foreground mt-0.5">
                        Oferta: {item.id_oferta}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-xs">
                    {item.propagacion_solicitada_por ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-xs">{item.tipo}</td>
                  <td className="px-4 py-2">
                    <Link
                      href={`/admin/issues/${item.id}#propagacion`}
                      className="px-3 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700 inline-block"
                    >
                      Procesar →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
