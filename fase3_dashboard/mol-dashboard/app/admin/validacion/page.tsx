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
  runId: "",
};

interface GoldSetCandidate {
  id_oferta: string;
  titulo: string;
  isco_code: string;
  isco_label: string;
  prioridad: number;
  razon: string;
  regla_aplicada: string | null;
  tiene_correccion_cynthia: boolean;
}

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
  const [goldSetMode, setGoldSetMode] = useState(false);
  const [goldSetStats, setGoldSetStats] = useState<{ total: number; correctos: number; errores: number } | null>(null);
  const [goldSetCandidates, setGoldSetCandidates] = useState<GoldSetCandidate[]>([]);

  // Get current user email
  useEffect(() => {
    createBrowserClient()
      .auth.getUser()
      .then(({ data: { user } }) => {
        setCurrentUserEmail(user?.email ?? null);
      });
  }, []);

  // Fetch ofertas (normal mode or gold set mode)
  const fetchOfertas = useCallback(async () => {
    setLoading(true);
    try {
      if (goldSetMode) {
        // Gold Set candidates mode
        const res = await fetch("/api/gold-set/candidates?limit=100");
        if (!res.ok) throw new Error("Error cargando candidatas");
        const json = await res.json();
        const candidates: GoldSetCandidate[] = json.candidates || [];
        setGoldSetStats(json.gold_set_stats || null);
        setGoldSetCandidates(candidates);

        // Fetch full oferta data for the candidate IDs
        if (candidates.length > 0) {
          const candidateIds = candidates.map(c => c.id_oferta);
          const result = await getOfertasValidacion(
            { ...EMPTY_FILTERS, ids: candidateIds } as any,
            candidates.length,
            0
          );
          // Reorder by candidate priority
          const idOrder = new Map(candidateIds.map((id, i) => [id, i]));
          const sorted = result.ofertas.sort((a, b) =>
            (idOrder.get(a.id_oferta) ?? 999) - (idOrder.get(b.id_oferta) ?? 999)
          );
          setOfertas(sorted);
          setTotal(sorted.length);
        } else {
          setOfertas([]);
          setTotal(0);
        }
      } else {
        // Normal mode
        const [result, statsResult] = await Promise.all([
          getOfertasValidacion(filters, PAGE_SIZE, offset),
          getValidacionStats(),
        ]);
        setOfertas(result.ofertas);
        setTotal(result.total);
        setStats(statsResult);
        setGoldSetCandidates([]);
      }
      // Auto-select first if nothing selected
      if (!selectedOferta) {
        setSelectedOferta(ofertas[0] || null);
        setCurrentIndex(0);
      }
    } catch (err) {
      console.error("Error loading ofertas:", err);
    } finally {
      setLoading(false);
    }
  }, [goldSetMode, filters, offset]);

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
      {/* Filters bar + Gold Set toggle */}
      <div className="border-b bg-white px-4 py-2 shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex-1">
            {!goldSetMode && (
              <ValidationFilters filters={filters} onChange={setFilters} stats={stats} ofertas={ofertas} />
            )}
            {goldSetMode && (
              <span className="text-sm text-amber-700 font-medium">
                Modo Gold Set — {goldSetCandidates.length} candidatas
              </span>
            )}
          </div>
          <button
            onClick={() => { setGoldSetMode(!goldSetMode); setSelectedOferta(null); setOffset(0); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              goldSetMode
                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                : 'bg-gray-100 text-gray-600 hover:bg-amber-50 hover:text-amber-700'
            }`}
          >
            <span>&#9733;</span>
            {goldSetMode ? 'Salir Gold Set' : 'Candidatas Gold Set'}
          </button>
        </div>
        {/* Gold Set banner */}
        {goldSetMode && goldSetStats && (
          <div className="mt-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            <div className="flex items-center gap-3">
              <span className="text-amber-500 text-lg">&#9733;</span>
              <div className="flex-1">
                <div className="text-xs text-amber-800 font-medium">
                  Modo Gold Set — Validá estas ofertas y presioná Alt+6 para agregarlas.
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-amber-600">Progreso: {goldSetStats.total}/150</span>
                  <div className="flex-1 max-w-[200px] bg-amber-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${goldSetStats.total >= 150 ? 'bg-green-500' : 'bg-amber-500'}`}
                      style={{ width: `${Math.min(100, goldSetStats.total / 150 * 100)}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-amber-600">{Math.round(goldSetStats.total / 150 * 100)}%</span>
                </div>
              </div>
            </div>
          </div>
        )}
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
                    goldSetCandidates={goldSetMode ? goldSetCandidates : undefined}
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
