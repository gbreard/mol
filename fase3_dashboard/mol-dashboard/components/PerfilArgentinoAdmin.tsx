"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, RefreshCw, AlertCircle, CheckCircle2, XCircle, Search, ChevronDown } from "lucide-react";
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
  emergentes_nuevas?: number;
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
  const [showEmergentes, setShowEmergentes] = useState(false);
  const [emergentes, setEmergentes] = useState<any[]>([]);
  const [loadingEmergentes, setLoadingEmergentes] = useState(false);
  const [emergentesFilter, setEmergentesFilter] = useState("");
  const [procesando, setProcesando] = useState<string | null>(null);

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

  const loadEmergentes = useCallback(async () => {
    setLoadingEmergentes(true);
    try {
      const res = await fetch("/api/emergentes-pendientes?estado=pendiente");
      if (res.ok) {
        const json = await res.json();
        setEmergentes(Array.isArray(json) ? json : []);
      }
    } catch (e) {
      console.error("Error cargando emergentes:", e);
    } finally {
      setLoadingEmergentes(false);
    }
  }, []);

  const handleEmergente = async (id: number, accion: "aprobar" | "rechazar") => {
    setProcesando(`${id}-${accion}`);
    try {
      const res = await fetch("/api/emergentes-pendientes", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, accion }),
      });
      if (res.ok) {
        setEmergentes(prev => prev.filter(e => e.id !== id));
      }
    } catch (e) {
      console.error("Error:", e);
    } finally {
      setProcesando(null);
    }
  };

  const toggleEmergentes = () => {
    if (!showEmergentes && emergentes.length === 0) {
      loadEmergentes();
    }
    setShowEmergentes(!showEmergentes);
  };

  const filteredEmergentes = emergentes.filter(e => {
    if (!emergentesFilter) return true;
    const term = emergentesFilter.toLowerCase();
    return e.skill_label?.toLowerCase().includes(term) ||
      e.isco_code?.includes(term) ||
      e.ocupacion_label?.toLowerCase().includes(term);
  });

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

  // Sin versiones aún — estado inicial
  if (!activa) {
    return (
      <div className="space-y-4">
        <div className="rounded-md border border-blue-200 bg-blue-50 p-4 text-sm text-blue-700">
          No hay ninguna versión del Perfil Consolidado Argentino todavía.
          Creá la primera versión para comenzar.
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          Crear primera versión
        </Button>
        <CreateVersionModal
          open={showCreateModal}
          versionPropuesta="v1.0"
          emergentesPendientes={0}
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreate}
        />
      </div>
    );
  }

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
          <Button variant="outline" size="sm" className="relative" onClick={toggleEmergentes}>
            {showEmergentes ? 'Ocultar' : 'Revisar'} emergentes
            {estado_actual.emergentes_pendientes > 0 && (
              <Badge className="ml-2 bg-red-500 text-white hover:bg-red-500 text-xs px-1.5 py-0">
                {emergentes.length || estado_actual.emergentes_pendientes}
              </Badge>
            )}
          </Button>
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
          <span className="font-medium">{estado_actual.emergentes_nuevas ?? 0}</span>
          <span className="text-gray-500">Emergentes pendientes de revisión</span>
          <span className={`font-medium ${estado_actual.emergentes_pendientes > 0 ? "text-amber-600" : ""}`}>
            {estado_actual.emergentes_pendientes}
          </span>
          <span className="text-gray-500">Skills aprobadas desde último corte</span>
          <span className="font-medium">{estado_actual.skills_aprobadas_desde_corte}</span>
        </div>
      </div>

      {/* Emergentes pendientes */}
      {showEmergentes && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-amber-800">
              Skills emergentes pendientes ({emergentes.length})
            </h3>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Filtrar..."
                  value={emergentesFilter}
                  onChange={e => setEmergentesFilter(e.target.value)}
                  className="pl-7 pr-3 py-1.5 text-xs border rounded-md w-48"
                />
              </div>
              <Button variant="ghost" size="sm" onClick={loadEmergentes} disabled={loadingEmergentes}>
                <RefreshCw className={`h-3.5 w-3.5 ${loadingEmergentes ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          {loadingEmergentes ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-amber-600" />
            </div>
          ) : filteredEmergentes.length === 0 ? (
            <p className="text-sm text-amber-700 py-4 text-center">
              {emergentes.length === 0 ? 'No hay emergentes pendientes' : 'Sin resultados para el filtro'}
            </p>
          ) : (
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-amber-50">
                  <tr className="border-b border-amber-200">
                    <th className="text-left py-2 pr-3 text-amber-700 font-medium">Skill</th>
                    <th className="text-left py-2 px-3 text-amber-700 font-medium">ISCO</th>
                    <th className="text-left py-2 px-3 text-amber-700 font-medium">Ocupacion</th>
                    <th className="text-right py-2 px-3 text-amber-700 font-medium">Freq.</th>
                    <th className="text-right py-2 px-3 text-amber-700 font-medium">Ofertas</th>
                    <th className="text-center py-2 pl-3 text-amber-700 font-medium">Accion</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEmergentes.map(e => (
                    <tr key={e.id} className="border-b border-amber-100 hover:bg-amber-100/50">
                      <td className="py-2 pr-3 text-gray-900 font-medium">{e.skill_label}</td>
                      <td className="py-2 px-3 font-mono text-xs text-blue-700">{e.isco_code}</td>
                      <td className="py-2 px-3 text-gray-600 text-xs max-w-xs truncate">{e.ocupacion_label}</td>
                      <td className="py-2 px-3 text-right font-bold text-amber-700">{e.frecuencia_pct}%</td>
                      <td className="py-2 px-3 text-right text-gray-600">{e.ofertas_count}/{e.total_ofertas_isco}</td>
                      <td className="py-2 pl-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => handleEmergente(e.id, 'aprobar')}
                            disabled={procesando !== null}
                            className="p-1.5 text-green-600 hover:bg-green-100 rounded-md disabled:opacity-30"
                            title="Aprobar"
                          >
                            {procesando === `${e.id}-aprobar` ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                          </button>
                          <button
                            onClick={() => handleEmergente(e.id, 'rechazar')}
                            disabled={procesando !== null}
                            className="p-1.5 text-red-400 hover:bg-red-100 rounded-md disabled:opacity-30"
                            title="Rechazar"
                          >
                            {procesando === `${e.id}-rechazar` ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

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
