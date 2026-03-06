"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, AlertTriangle } from "lucide-react";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { getOfertasValidacion, getValidacionStats } from "@/lib/supabase";
import { OfertaValidacion, ValidationFiltersState, ValidationStats, ValidacionHumana } from "@/lib/types";
import { ValidationFilters } from "@/components/validacion/ValidationFilters";
import { OfertaList } from "@/components/validacion/OfertaList";
import { PuestoPanel } from "@/components/validacion/PuestoPanel";
import { ClasificacionPanel } from "@/components/validacion/ClasificacionPanel";
import { ValidationActions } from "@/components/validacion/ValidationActions";
import { ListPagination } from "@/components/validacion/ListPagination";
import { createBrowserClient } from "@/lib/supabase/browser";

const PAGE_SIZE = 50;

const EMPTY_FILTERS: ValidationFiltersState = {
  iscoGroup: "",
  portal: "",
  provincia: "",
  metodo: "",
  search: "",
  seniority: "",
  modalidad: "",
  sector: "",
  nivelEducativo: "",
  scoreRange: "",
  estadoValidacion: "",
};

export default function ValidacionPage() {
  const [filters, setFilters] = useState<ValidationFiltersState>(EMPTY_FILTERS);
  const [ofertas, setOfertas] = useState<OfertaValidacion[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedOferta, setSelectedOferta] = useState<OfertaValidacion | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [offset, setOffset] = useState(0);
  const [stats, setStats] = useState<ValidationStats | null>(null);
  const [currentUserEmail, setCurrentUserEmail] = useState<string | null>(null);

  // Get current user email
  useEffect(() => {
    createBrowserClient()
      .auth.getUser()
      .then(({ data: { user } }) => {
        setCurrentUserEmail(user?.email ?? null);
      });
  }, []);

  // Fetch ofertas
  const fetchOfertas = useCallback(async () => {
    setLoading(true);
    try {
      const [result, statsResult] = await Promise.all([
        getOfertasValidacion(filters, PAGE_SIZE, offset),
        getValidacionStats(),
      ]);
      setOfertas(result.ofertas);
      setTotal(result.total);
      setStats(statsResult);
      // Auto-select first if nothing selected
      if (result.ofertas.length > 0 && !selectedOferta) {
        setSelectedOferta(result.ofertas[0]);
        setCurrentIndex(0);
      }
    } catch (err) {
      console.error("Error loading ofertas:", err);
    } finally {
      setLoading(false);
    }
  }, [filters, offset]);

  useEffect(() => {
    fetchOfertas();
  }, [fetchOfertas]);

  // Reset selection when filters change
  useEffect(() => {
    setSelectedOferta(null);
    setCurrentIndex(0);
    setOffset(0);
  }, [filters]);

  // Select oferta from list
  const handleSelect = (oferta: OfertaValidacion) => {
    const idx = ofertas.findIndex((o) => o.id_oferta === oferta.id_oferta);
    setSelectedOferta(oferta);
    setCurrentIndex(idx >= 0 ? idx : 0);
  };

  // Navigate
  const navigateTo = useCallback(
    (direction: "prev" | "next") => {
      if (ofertas.length === 0) return;
      const newIndex =
        direction === "next"
          ? Math.min(currentIndex + 1, ofertas.length - 1)
          : Math.max(currentIndex - 1, 0);
      setCurrentIndex(newIndex);
      setSelectedOferta(ofertas[newIndex]);
    },
    [ofertas, currentIndex]
  );

  // After evaluating: update local state + auto-next
  const handleEvaluated = useCallback(
    (resultado: ValidacionHumana) => {
      // Update local oferta state
      setOfertas((prev) =>
        prev.map((o) =>
          o.id_oferta === selectedOferta?.id_oferta
            ? { ...o, validacion_humana: resultado }
            : o
        )
      );
      if (selectedOferta) {
        setSelectedOferta((prev) =>
          prev ? { ...prev, validacion_humana: resultado } : prev
        );
      }
      // Update stats locally
      setStats((prev) => {
        if (!prev) return prev;
        const wasNull = selectedOferta?.validacion_humana == null;
        const wasPrev = selectedOferta?.validacion_humana;
        const next = { ...prev };
        // Decrement old
        if (wasNull) {
          next.pendientes = Math.max(0, next.pendientes - 1);
        } else if (wasPrev) {
          next[wasPrev] = Math.max(0, next[wasPrev] - 1);
        }
        // Increment new
        next[resultado]++;
        return next;
      });
      // Auto-navigate to next
      if (currentIndex < ofertas.length - 1) {
        navigateTo("next");
      }
    },
    [selectedOferta, currentIndex, ofertas.length, navigateTo]
  );

  // Keyboard: Arrow up/down for list navigation
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "ArrowUp") {
        e.preventDefault();
        navigateTo("prev");
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        navigateTo("next");
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [navigateTo]);

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Filters bar */}
      <div className="border-b bg-white px-4 py-2 shrink-0">
        <ValidationFilters filters={filters} onChange={setFilters} stats={stats} ofertas={ofertas} />
      </div>

      {/* Main content: 3-panel split */}
      {loading ? (
        <div className="flex items-center justify-center flex-1">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="ml-2 text-sm text-gray-500">Cargando ofertas...</span>
        </div>
      ) : ofertas.length === 0 ? (
        <div className="flex items-center justify-center flex-1 text-gray-500 text-sm">
          No se encontraron ofertas con los filtros seleccionados
        </div>
      ) : (
        <div className="flex-1 min-h-0">
          <ResizablePanelGroup direction="horizontal" className="h-full">
            {/* Panel 1: List */}
            <ResizablePanel defaultSize={20} minSize={15} maxSize={30}>
              <div className="h-full flex flex-col border-r">
                <div className="px-3 py-1.5 border-b bg-gray-50 text-xs text-gray-500 shrink-0">
                  {offset + currentIndex + 1} / {total} ofertas
                </div>
                <div className="flex-1 min-h-0">
                  <OfertaList
                    ofertas={ofertas}
                    selectedId={selectedOferta?.id_oferta ?? null}
                    onSelect={handleSelect}
                  />
                </div>
                <ListPagination
                  offset={offset}
                  pageSize={PAGE_SIZE}
                  total={total}
                  onPageChange={(newOffset) => {
                    setOffset(newOffset);
                    setSelectedOferta(null);
                    setCurrentIndex(0);
                  }}
                />
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Panel 2: Puesto */}
            <ResizablePanel defaultSize={40} minSize={25}>
              {selectedOferta ? (
                <PuestoPanel oferta={selectedOferta} />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                  Selecciona una oferta
                </div>
              )}
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Panel 3: Clasificacion */}
            <ResizablePanel defaultSize={40} minSize={25}>
              {selectedOferta ? (
                <ClasificacionPanel oferta={selectedOferta} />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                  Selecciona una oferta
                </div>
              )}
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      )}

      {/* Already reviewed banner */}
      {selectedOferta?.validacion_humana &&
        selectedOferta.validacion_humana_por && (
          <div className={`border-t px-4 py-1.5 flex items-center gap-2 text-xs shrink-0 ${
            selectedOferta.validacion_humana_por === currentUserEmail
              ? "bg-blue-50 border-blue-200 text-blue-700"
              : "bg-amber-50 border-amber-200 text-amber-800"
          }`}>
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span>
              Evaluada como <strong>{selectedOferta.validacion_humana.toUpperCase()}</strong> por{" "}
              <strong>{selectedOferta.validacion_humana_por.split("@")[0]}</strong>
              {selectedOferta.validacion_humana_at && (
                <> el {new Date(selectedOferta.validacion_humana_at).toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</>
              )}
            </span>
          </div>
        )}

      {/* Sticky bottom bar: actions */}
      {selectedOferta && (
        <ValidationActions
          idOferta={selectedOferta.id_oferta}
          tituloOferta={selectedOferta.titulo_limpio || selectedOferta.titulo}
          iscoCode={selectedOferta.isco_code}
          currentValidacion={selectedOferta.validacion_humana}
          oferta={selectedOferta}
          onEvaluated={handleEvaluated}
        />
      )}
    </div>
  );
}
