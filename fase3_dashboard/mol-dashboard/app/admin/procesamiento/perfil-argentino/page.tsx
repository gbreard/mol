"use client";

// Re-export the existing Perfil Argentino component
// Original is at /admin/perfil-argentino but now also accessible from /admin/procesamiento/perfil-argentino
import { PerfilArgentinoAdmin } from "@/components/PerfilArgentinoAdmin";

export default function PerfilArgentinoPage() {
  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <PerfilArgentinoAdmin />
    </div>
  );
}
