import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ValidationFilters } from "@/components/validacion/ValidationFilters";
import { ValidationFiltersState } from "@/lib/types";

/**
 * Tests para el bloque "Revisión" agregado en sub-tarea D.2 (SPEC W F7/F8).
 *
 * Verifica:
 *   - Radio group: 4 opciones excluyentes (Todas/Pendientes/Revisadas/Mal extraídas)
 *   - Checkbox: Solo datos incompletos (on/off → "true"/"")
 *   - Checkbox: Solo corregidas manualmente (on/off → "true"/"")
 *   - Render del subtítulo "Revisión"
 *   - Regresión: filtros existentes siguen funcionando
 *
 * Ref: docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 3.3.4
 */

// Mock las funciones del módulo que ValidationFilters + RunFilter usan
vi.mock("@/lib/supabase", () => ({
  getValidacionFilterOptions: () =>
    Promise.resolve({
      portales: ["bumeran", "computrabajo"],
      provincias: ["Capital Federal"],
      metodos: ["semantico_unico"],
      iscoGroups: [{ code: "2", label: "Profesionales" }],
      seniorities: ["junior", "senior"],
      modalidades: ["remoto", "presencial"],
      sectores: ["Tecnología"],
      nivelesEducativos: ["universitario"],
    }),
  getRunsDisponibles: () => Promise.resolve([]),
}));

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
  soloDatosIncompletos: "",
  soloCorreccionManual: "",
  estadoRevision: "",
};

function renderFilters(overrides: Partial<ValidationFiltersState> = {}, onChange = vi.fn()) {
  const filters = { ...EMPTY_FILTERS, ...overrides };
  render(<ValidationFilters filters={filters} onChange={onChange} stats={null} />);
  return { onChange };
}

describe("ValidationFilters — bloque Revisión (D.2)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renderiza el subtítulo 'Revisión'", async () => {
    renderFilters();
    await waitFor(() => {
      expect(screen.getByText(/Revisión/i)).toBeInTheDocument();
    });
  });

  it("renderiza las 4 opciones del radio + 2 checkboxes", async () => {
    renderFilters();
    await waitFor(() => {
      expect(screen.getByLabelText(/^Todas$/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/^Pendientes$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Revisadas$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Mal extraídas$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Solo datos incompletos/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Solo corregidas manualmente/i)).toBeInTheDocument();
  });

  it("por default 'Todas' está seleccionado", async () => {
    renderFilters();
    await waitFor(() => {
      const todas = screen.getByLabelText(/^Todas$/i);
      expect(todas).toHaveAttribute("aria-checked", "true");
    });
  });

  it("click en 'Pendientes' llama onChange con estadoRevision='pendiente'", async () => {
    const onChange = vi.fn();
    renderFilters({}, onChange);
    await waitFor(() => screen.getByLabelText(/^Pendientes$/i));
    fireEvent.click(screen.getByLabelText(/^Pendientes$/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ estadoRevision: "pendiente" }),
    );
  });

  it("click en 'Revisadas' llama onChange con estadoRevision='revisada'", async () => {
    const onChange = vi.fn();
    renderFilters({}, onChange);
    await waitFor(() => screen.getByLabelText(/^Revisadas$/i));
    fireEvent.click(screen.getByLabelText(/^Revisadas$/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ estadoRevision: "revisada" }),
    );
  });

  it("click en 'Mal extraídas' llama onChange con estadoRevision='mal_extraida_total'", async () => {
    const onChange = vi.fn();
    renderFilters({}, onChange);
    await waitFor(() => screen.getByLabelText(/^Mal extraídas$/i));
    fireEvent.click(screen.getByLabelText(/^Mal extraídas$/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ estadoRevision: "mal_extraida_total" }),
    );
  });

  it("click en 'Todas' (cuando otra estaba activa) limpia estadoRevision", async () => {
    const onChange = vi.fn();
    renderFilters({ estadoRevision: "revisada" }, onChange);
    await waitFor(() => screen.getByLabelText(/^Todas$/i));
    fireEvent.click(screen.getByLabelText(/^Todas$/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ estadoRevision: "" }),
    );
  });

  it("toggle datos incompletos off → on: onChange con 'true'", async () => {
    const onChange = vi.fn();
    renderFilters({}, onChange);
    await waitFor(() => screen.getByLabelText(/Solo datos incompletos/i));
    fireEvent.click(screen.getByLabelText(/Solo datos incompletos/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ soloDatosIncompletos: "true" }),
    );
  });

  it("toggle datos incompletos on → off: onChange con ''", async () => {
    const onChange = vi.fn();
    renderFilters({ soloDatosIncompletos: "true" }, onChange);
    await waitFor(() => screen.getByLabelText(/Solo datos incompletos/i));
    fireEvent.click(screen.getByLabelText(/Solo datos incompletos/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ soloDatosIncompletos: "" }),
    );
  });

  it("toggle corregidas manualmente off → on: onChange con 'true'", async () => {
    const onChange = vi.fn();
    renderFilters({}, onChange);
    await waitFor(() => screen.getByLabelText(/Solo corregidas manualmente/i));
    fireEvent.click(screen.getByLabelText(/Solo corregidas manualmente/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ soloCorreccionManual: "true" }),
    );
  });

  it("toggle corregidas manualmente on → off: onChange con ''", async () => {
    const onChange = vi.fn();
    renderFilters({ soloCorreccionManual: "true" }, onChange);
    await waitFor(() => screen.getByLabelText(/Solo corregidas manualmente/i));
    fireEvent.click(screen.getByLabelText(/Solo corregidas manualmente/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ soloCorreccionManual: "" }),
    );
  });

  it("estado externo 'revisada' refleja el radio correcto seleccionado", async () => {
    renderFilters({ estadoRevision: "revisada" });
    await waitFor(() => {
      expect(screen.getByLabelText(/^Revisadas$/i)).toHaveAttribute("aria-checked", "true");
    });
    expect(screen.getByLabelText(/^Todas$/i)).toHaveAttribute("aria-checked", "false");
  });

  it("estado externo soloDatosIncompletos='true' refleja el checkbox tildado", async () => {
    renderFilters({ soloDatosIncompletos: "true" });
    await waitFor(() => {
      const cb = screen.getByLabelText(/Solo datos incompletos/i);
      expect(cb).toHaveAttribute("aria-checked", "true");
    });
  });
});

describe("ValidationFilters — regresión filtros existentes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Limpiar resetea TODO incluido bloque Revisión", async () => {
    const onChange = vi.fn();
    renderFilters(
      {
        portal: "bumeran",
        estadoRevision: "revisada",
        soloDatosIncompletos: "true",
        soloCorreccionManual: "true",
      },
      onChange,
    );
    await waitFor(() => screen.getByText(/Limpiar/i));
    fireEvent.click(screen.getByText(/Limpiar/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        portal: "",
        estadoRevision: "",
        soloDatosIncompletos: "",
        soloCorreccionManual: "",
      }),
    );
  });

  it("input de búsqueda sigue presente (los controles existentes no rompieron)", async () => {
    renderFilters();
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Titulo, ID o lista IDs/i)).toBeInTheDocument();
    });
  });
});
