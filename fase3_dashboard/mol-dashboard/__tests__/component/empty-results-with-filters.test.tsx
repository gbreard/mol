import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { EmptyResultsWithFilters } from "@/components/validacion/EmptyResultsWithFilters";
import { ValidationFiltersState } from "@/lib/types";

/**
 * Tests para el fix de B2 — empty state distingue casos para que Cyn
 * entienda por qué el buscador "no devolvió nada":
 *   - hay búsqueda + filtros: mensaje explicativo + botón limpiar
 *   - sólo búsqueda: mensaje simple
 *   - sólo filtros (sin búsqueda): mensaje genérico
 *
 * Ref: docs/issues/2026-05-19_B2_buscador_id_inconsistente.md
 */

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

describe("EmptyResultsWithFilters (fix B2)", () => {
  it("muestra mensaje + botón limpiar cuando hay search Y otros filtros activos", () => {
    const onClearFiltersKeepSearch = vi.fn();
    const onClearAll = vi.fn();
    render(
      <EmptyResultsWithFilters
        filters={{ ...EMPTY_FILTERS, search: "1234567890", iscoGroup: "5000", provincia: "CABA" }}
        onClearFiltersKeepSearch={onClearFiltersKeepSearch}
        onClearAll={onClearAll}
      />
    );
    expect(screen.getByText(/Sin resultados para .1234567890./)).toBeInTheDocument();
    expect(screen.getByText(/Probablemente el término o ID no cumple con los filtros activos/i)).toBeInTheDocument();
    expect(screen.getByText("ISCO")).toBeInTheDocument();
    expect(screen.getByText("5000")).toBeInTheDocument();
    expect(screen.getByText("Provincia")).toBeInTheDocument();
    expect(screen.getByText("CABA")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Limpiar filtros .mantener búsqueda./i })).toBeInTheDocument();
  });

  it("NO muestra mensaje de filtros cuando sólo hay búsqueda activa (sin otros filtros)", () => {
    render(
      <EmptyResultsWithFilters
        filters={{ ...EMPTY_FILTERS, search: "1234567890" }}
        onClearFiltersKeepSearch={vi.fn()}
        onClearAll={vi.fn()}
      />
    );
    expect(screen.getByText(/Sin resultados para .1234567890./)).toBeInTheDocument();
    expect(screen.queryByText(/Probablemente el término o ID no cumple con los filtros activos/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Limpiar filtros .mantener búsqueda./i })).not.toBeInTheDocument();
  });

  it("click en 'Limpiar filtros (mantener búsqueda)' dispara el callback correcto", () => {
    const onClearFiltersKeepSearch = vi.fn();
    const onClearAll = vi.fn();
    render(
      <EmptyResultsWithFilters
        filters={{ ...EMPTY_FILTERS, search: "abc", sector: "Comercio" }}
        onClearFiltersKeepSearch={onClearFiltersKeepSearch}
        onClearAll={onClearAll}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Limpiar filtros .mantener búsqueda./i }));
    expect(onClearFiltersKeepSearch).toHaveBeenCalledTimes(1);
    expect(onClearAll).not.toHaveBeenCalled();
  });

  it("click en 'Limpiar todo' dispara onClearAll y no onClearFiltersKeepSearch", () => {
    const onClearFiltersKeepSearch = vi.fn();
    const onClearAll = vi.fn();
    render(
      <EmptyResultsWithFilters
        filters={{ ...EMPTY_FILTERS, search: "abc", sector: "Comercio" }}
        onClearFiltersKeepSearch={onClearFiltersKeepSearch}
        onClearAll={onClearAll}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Limpiar todo/i }));
    expect(onClearAll).toHaveBeenCalledTimes(1);
    expect(onClearFiltersKeepSearch).not.toHaveBeenCalled();
  });

  it("muestra mensaje genérico cuando no hay búsqueda ni filtros (caso vacío total)", () => {
    render(
      <EmptyResultsWithFilters
        filters={EMPTY_FILTERS}
        onClearFiltersKeepSearch={vi.fn()}
        onClearAll={vi.fn()}
      />
    );
    expect(screen.getByText(/No se encontraron ofertas con los filtros seleccionados/i)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("muestra mensaje genérico cuando hay filtros pero no búsqueda", () => {
    render(
      <EmptyResultsWithFilters
        filters={{ ...EMPTY_FILTERS, iscoGroup: "5000", estadoValidacion: "pendiente" }}
        onClearFiltersKeepSearch={vi.fn()}
        onClearAll={vi.fn()}
      />
    );
    expect(screen.getByText(/No se encontraron ofertas con los filtros seleccionados/i)).toBeInTheDocument();
    // No hay botón porque no hay búsqueda que preservar
    expect(screen.queryByRole("button", { name: /Limpiar filtros .mantener búsqueda./i })).not.toBeInTheDocument();
  });

  it("lista todos los filtros activos enumerándolos (regresión: no se pierde ninguno)", () => {
    render(
      <EmptyResultsWithFilters
        filters={{
          ...EMPTY_FILTERS,
          search: "test",
          iscoGroup: "5000",
          seniority: "senior",
          sector: "Comercio",
          modalidad: "remoto",
          provincia: "CABA",
          portal: "bumeran",
          scoreRange: ">0.7",
          estadoValidacion: "pendiente",
          nivelEducativo: "universitario",
          metodo: "regla_negocio",
          runId: "run_x",
        }}
        onClearFiltersKeepSearch={vi.fn()}
        onClearAll={vi.fn()}
      />
    );
    // Verifico labels de los 11 filtros no-search
    expect(screen.getByText("ISCO")).toBeInTheDocument();
    expect(screen.getByText("Seniority")).toBeInTheDocument();
    expect(screen.getByText("Sector")).toBeInTheDocument();
    expect(screen.getByText("Modalidad")).toBeInTheDocument();
    expect(screen.getByText("Provincia")).toBeInTheDocument();
    expect(screen.getByText("Portal")).toBeInTheDocument();
    expect(screen.getByText("Score")).toBeInTheDocument();
    expect(screen.getByText("Estado")).toBeInTheDocument();
    expect(screen.getByText("Nivel educativo")).toBeInTheDocument();
    expect(screen.getByText("Método")).toBeInTheDocument();
    expect(screen.getByText("Corrida")).toBeInTheDocument();
  });
});
