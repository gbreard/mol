/**
 * /admin/issues/sin-propagacion
 *
 * Pantalla con los 462 issues retrospectivos sin patrón estructurado.
 * Cualquier analista puede marcar los que considere propagables.
 *
 * SPEC T Fase 4.
 */
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { RequestPropagationModal } from "@/components/issues/RequestPropagationModal";

interface Item {
  id: string;
  titulo: string;
  tipo: string;
  prioridad: string;
  id_oferta?: string;
  autor_nombre?: string;
  autor_email?: string;
  created_at: string;
  resuelto_at?: string;
  patron_corregido?: { _audit_note?: string } | null;
  propagacion_solicitada?: boolean;
}

export default function SinPropagacionPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalIssue, setModalIssue] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch("/api/issues/sin-propagacion");
      const j = await res.json();
      if (res.ok) setItems(j.items ?? []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="p-6 flex items-center gap-2 text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        Cargando...
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Issues sin propagación</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {items.length} issues resueltos sin patrón de propagación auditado.
        </p>
      </header>

      <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded p-4 text-sm space-y-2">
        <p className="font-medium">ℹ️ Issues resueltos antes del sistema SPEC T</p>
        <p>
          Estos issues fueron resueltos antes que existiera la propagación automática.
          Algunos pueden tener correcciones que aplican a muchas otras ofertas, pero
          nunca se propagaron.
        </p>
        <p>
          Si entrás a uno y pensás que la corrección debería aplicarse a otras
          ofertas similares, click en <b>"Solicitar"</b>. El admin lo revisa.
        </p>
        <p className="text-muted-foreground italic">
          Si fue puntual (una sola oferta con problema único), no hace falta hacer
          nada — quedan así.
        </p>
      </div>

      <div className="border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted text-left">
            <tr>
              <th className="px-4 py-2 font-medium">Fecha</th>
              <th className="px-4 py-2 font-medium">Título</th>
              <th className="px-4 py-2 font-medium">Autor</th>
              <th className="px-4 py-2 font-medium">Tipo</th>
              <th className="px-4 py-2 font-medium">Acción</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t hover:bg-muted/50">
                <td className="px-4 py-2 text-xs text-muted-foreground whitespace-nowrap">
                  {new Date(item.created_at).toLocaleDateString("es-AR")}
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
                <td className="px-4 py-2 text-xs">{item.autor_nombre ?? item.autor_email}</td>
                <td className="px-4 py-2 text-xs">{item.tipo}</td>
                <td className="px-4 py-2">
                  {item.propagacion_solicitada ? (
                    <span className="text-xs text-amber-700">🟡 Ya solicitada</span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setModalIssue(item.id)}
                      className="px-3 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700"
                    >
                      Solicitar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalIssue && (
        <RequestPropagationModal
          issueId={modalIssue}
          open
          onClose={() => setModalIssue(null)}
          onSubmitted={() => {
            setModalIssue(null);
            load();
          }}
        />
      )}
    </div>
  );
}
