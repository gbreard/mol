"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getOfertasValidacion } from "@/lib/supabase";
import { OfertaValidacion, ValidationFiltersState } from "@/lib/types";
import { ValidationFilters } from "@/components/validacion/ValidationFilters";
import { OfertaList } from "@/components/validacion/OfertaList";
import { OfertaDetail } from "@/components/validacion/OfertaDetail";

const PAGE_SIZE = 50;

const EMPTY_FILTERS: ValidationFiltersState = {
  iscoGroup: "",
  portal: "",
  provincia: "",
  metodo: "",
  search: "",
};

export default function ValidacionPage() {
  const [filters, setFilters] = useState<ValidationFiltersState>(EMPTY_FILTERS);
  const [ofertas, setOfertas] = useState<OfertaValidacion[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedOferta, setSelectedOferta] = useState<OfertaValidacion | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [offset, setOffset] = useState(0);

  // Fetch ofertas
  const fetchOfertas = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getOfertasValidacion(filters, PAGE_SIZE, offset);
      setOfertas(result.ofertas);
      setTotal(result.total);
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

  // Navigate prev/next
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

  // After evaluating, auto-navigate to next
  const handleEvaluated = useCallback(() => {
    if (currentIndex < ofertas.length - 1) {
      navigateTo("next");
    }
  }, [currentIndex, ofertas.length, navigateTo]);

  // Keyboard navigation
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" && !e.ctrlKey) {
        e.preventDefault();
        navigateTo("prev");
      } else if (e.key === "ArrowRight" && !e.ctrlKey) {
        e.preventDefault();
        navigateTo("next");
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [navigateTo]);

  const globalIndex = offset + currentIndex + 1;
  const canPrev = currentIndex > 0 || offset > 0;
  const canNext = currentIndex < ofertas.length - 1 || offset + PAGE_SIZE < total;

  const handlePagePrev = () => {
    if (currentIndex > 0) {
      navigateTo("prev");
    } else if (offset > 0) {
      setOffset(Math.max(0, offset - PAGE_SIZE));
      setCurrentIndex(PAGE_SIZE - 1);
    }
  };

  const handlePageNext = () => {
    if (currentIndex < ofertas.length - 1) {
      navigateTo("next");
    } else if (offset + PAGE_SIZE < total) {
      setOffset(offset + PAGE_SIZE);
      setCurrentIndex(0);
      setSelectedOferta(null);
    }
  };

  return (
    <div className="p-6 space-y-4">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Panel de Validacion
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Revision oferta por oferta: original, NLP, matching, skills.
          Usa flechas para navegar, Ctrl+1/2/3 para evaluar.
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="py-3 px-4">
          <ValidationFilters filters={filters} onChange={setFilters} />
        </CardContent>
      </Card>

      {/* List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <span className="ml-2 text-sm text-gray-500">
                Cargando ofertas...
              </span>
            </div>
          ) : (
            <OfertaList
              ofertas={ofertas}
              selectedId={selectedOferta?.id_oferta ?? null}
              onSelect={handleSelect}
            />
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      {ofertas.length > 0 && (
        <div className="flex items-center justify-center gap-3">
          <Button
            size="sm"
            variant="outline"
            onClick={handlePagePrev}
            disabled={!canPrev}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Anterior
          </Button>
          <span className="text-sm text-gray-600 tabular-nums">
            Oferta {globalIndex} de {total}
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={handlePageNext}
            disabled={!canNext}
          >
            Siguiente
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
          <span className="text-xs text-gray-400 ml-2">
            Flechas: navegar
          </span>
        </div>
      )}

      {/* Detail panel */}
      {selectedOferta && (
        <Card>
          <CardContent className="p-4">
            <OfertaDetail
              oferta={selectedOferta}
              onEvaluated={handleEvaluated}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
