"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, RefreshCw, AlertCircle } from "lucide-react";
import { VersionHistoryTable, PerfilVersion } from "./VersionHistoryTable";
import { CreateVersionModal } from "./CreateVersionModal";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

type EstadoActual = {
  ofertas_desde_ultimo_corte: number;
  emergentes_nuevas: number;
  emergentes_pendientes: number;
  skills_aprobadas_desde_corte: number;
};

type ApiResponse = {
  activa: PerfilVersion;
  versiones: PerfilVersion[];
  estado_actual: EstadoActual;
};

function calcularVersionPropuesta(versiones: PerfilVersion[]): string {
  if (versiones.length === 0) return "v1.0";
  const activa = versiones.find((v) => v.activa);
  if (!activa) return "v1.0";
  const match = activa.version.match(/^v(\d+)\.(\d+)$/);
  if (!match) return "v1.0";
  const minor = parseInt(match[2]) + 1;
  return `v${match[1]}.${minor}`;
}

export function PerfilArgentinoAdmin() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [rollbackTarget, setRollbackTarget] = useState<PerfilVersion | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/perfil-argentino-versiones");
      if (!res.ok) throw new Error("Error al cargar versiones");
      const json: ApiResponse = await res.json();
      setData(json);
    } catch (e) {
      setError("No se pudieron cargar las versiones.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreate = async (nota: string) => {
    const res = await fetch("/api/perfil-argentino-versiones", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nota }),
    });
    if (!res.ok) throw new Error("Error al crear versión");
    await loadData();
  };

  const handleRollback = async () => {
    if (!rollbackTarget) return;
    const res = await fetch("/api/perfil-argentino-versiones", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version_id: rollbackTarget.id, action: "rollback" }),
    });
    if (!res.ok) throw new Error("Error al hacer rollback");
    setRollbackTarget(null);
    await loadData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-md bg-red-50 border border-red-200 p-4 text-red-700">
        <AlertCircle className="h-4 w-4 shrink-0" />
        <span className="text-sm">{error}</span>
        <Button variant="ghost" size="sm" onClick={loadData} className="ml-auto">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  if (!data) return null;

  const { activa, versiones, estado_actual } = data;
  const versionPropuesta = calcularVersionPropuesta(versiones);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500">
            Versión activa:{" "}
            <span className="font-semibold text-gray-900">
              {activa.version}
            </span>{" "}
            <span className="text-gray-400">
              ({new Date(activa.created_at).toLocaleDateString("es-AR")})
            </span>
          </p>
        </div>
        <div className="flex gap-2">
          {estado_actual.emergentes_pendientes > 0 && (
            <Button variant="outline" size="sm" className="relative">
              Revisar emergentes
              <Badge className="ml-2 bg-red-500 text-white hover:bg-red-500 text-xs px-1.5 py-0">
                {estado_actual.emergentes_pendientes}
              </Badge>
            </Button>
          )}
          <Button size="sm" onClick={() => setShowCreateModal(true)}>
            Crear nueva versión
          </Button>
        </div>
      </div>

      {/* Estado actual */}
      <div className="rounded-md border bg-gray-50 p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">
          Estado actual — cambios desde {activa.version}
        </h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm">
          <span className="text-gray-500">Ofertas procesadas desde último corte</span>
          <span className="font-medium">
            {estado_actual.ofertas_desde_ultimo_corte.toLocaleString("es-AR")}
          </span>
          <span className="text-gray-500">Emergentes nuevas detectadas (≥30%)</span>
          <span className="font-medium">{estado_actual.emergentes_nuevas}</span>
          <span className="text-gray-500">Emergentes pendientes de revisión</span>
          <span className={`font-medium ${estado_actual.emergentes_pendientes > 0 ? "text-amber-600" : ""}`}>
            {estado_actual.emergentes_pendientes}
          </span>
          <span className="text-gray-500">Skills aprobadas desde último corte</span>
          <span className="font-medium">{estado_actual.skills_aprobadas_desde_corte}</span>
        </div>
      </div>

      {/* Historial */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-700">Historial de versiones</h3>
        <VersionHistoryTable
          versiones={versiones}
          onRollback={(v) => setRollbackTarget(v)}
        />
      </div>

      {/* Modal crear versión */}
      <CreateVersionModal
        open={showCreateModal}
        versionPropuesta={versionPropuesta}
        emergentesPendientes={estado_actual.emergentes_pendientes}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
      />

      {/* Confirmación rollback */}
      <AlertDialog
        open={!!rollbackTarget}
        onOpenChange={(v) => !v && setRollbackTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              ¿Hacer rollback a {rollbackTarget?.version}?
            </AlertDialogTitle>
            <AlertDialogDescription>
              El sistema volverá a usar la versión {rollbackTarget?.version} para
              matching, búsquedas y nuevos reportes. Los reportes existentes no
              se modifican.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleRollback}>
              Confirmar rollback
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
