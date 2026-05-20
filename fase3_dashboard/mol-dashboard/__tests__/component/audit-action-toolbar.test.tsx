import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createRef } from "react";
import { AuditActionToolbar, type AuditActionToolbarHandle } from "@/components/validacion/AuditActionToolbar";

/**
 * Tests del AuditActionToolbar (SPEC W Etapa 1 — sub-tarea D.1).
 *
 * Cubre:
 *   - Render según estado_revision (null / revisada / mal_extraida_total)
 *   - Toggle on/off de "Revisada"
 *   - Modal de confirmación de "Mal extraída total" con/sin nota
 *   - Manejo de errores con toast
 *   - GET history fallback cuando monta con estado != null y sin action_id local
 *   - Imperative handle (triggerRevisada / triggerMalExtraida) para atajos
 *
 * Refs:
 *   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md F4, F5, F6
 *   components/validacion/AuditActionToolbar.tsx
 */

const toastSuccess = vi.fn();
const toastError = vi.fn();
vi.mock("sonner", () => ({
  toast: {
    success: (...args: unknown[]) => toastSuccess(...args),
    error: (...args: unknown[]) => toastError(...args),
  },
}));

type FetchCall = { url: string; method: string; body?: unknown };
let fetchCalls: FetchCall[];
let fetchHandler: (url: string, init?: RequestInit) => Promise<Response>;

function defaultFetchHandler(url: string, init?: RequestInit) {
  // Mock por defecto: POST devuelve action_id, DELETE devuelve OK,
  // GET history devuelve array vacío
  if (init?.method === "POST" && url === "/api/audit-actions") {
    return Promise.resolve(
      new Response(JSON.stringify({ success: true, action_id: 42 }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  if (init?.method === "DELETE" && url.startsWith("/api/audit-actions/")) {
    return Promise.resolve(
      new Response(JSON.stringify({ reverted: true, action_id: 99 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  if ((init?.method === "GET" || !init?.method) && url.includes("/audit-history")) {
    return Promise.resolve(
      new Response(JSON.stringify({ actions: [], total: 0 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  return Promise.resolve(new Response("not found", { status: 404 }));
}

beforeEach(() => {
  fetchCalls = [];
  toastSuccess.mockClear();
  toastError.mockClear();
  fetchHandler = defaultFetchHandler;
  global.fetch = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = typeof input === "string" ? input : (input as Request).url;
    let parsedBody: unknown;
    if (init?.body && typeof init.body === "string") {
      try {
        parsedBody = JSON.parse(init.body);
      } catch {
        parsedBody = init.body;
      }
    }
    fetchCalls.push({
      url,
      method: (init?.method || "GET").toUpperCase(),
      body: parsedBody,
    });
    return fetchHandler(url, init);
  }) as unknown as typeof fetch;
});

afterEach(() => {
  vi.restoreAllMocks();
});

function findCall(method: string, urlSubstring: string): FetchCall | undefined {
  return fetchCalls.find(
    (c) => c.method === method && c.url.includes(urlSubstring),
  );
}

// =============================================================================
// Render según estado
// =============================================================================
describe("AuditActionToolbar — render según estado", () => {
  it("estado=null muestra ambos botones sin highlight", () => {
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={vi.fn()}
      />,
    );
    const revisada = screen.getByTestId("btn-marcar-revisada");
    const mal = screen.getByTestId("btn-mal-extraida");
    expect(revisada).not.toBeDisabled();
    expect(mal).not.toBeDisabled();
    expect(revisada).toHaveAttribute("aria-pressed", "false");
    expect(mal).toHaveAttribute("aria-pressed", "false");
  });

  it("estado='revisada' muestra 'Revisada ✓' + Mal extraída disabled", () => {
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual="revisada"
        onAuditComplete={vi.fn()}
      />,
    );
    expect(screen.getByText("Revisada ✓")).toBeInTheDocument();
    expect(screen.getByTestId("btn-mal-extraida")).toBeDisabled();
    expect(screen.getByTestId("btn-marcar-revisada")).toHaveAttribute("aria-pressed", "true");
  });

  it("estado='mal_extraida_total' muestra 'Mal extraída ⚠' + Revisada disabled", () => {
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual="mal_extraida_total"
        onAuditComplete={vi.fn()}
      />,
    );
    expect(screen.getByText("Mal extraída ⚠")).toBeInTheDocument();
    expect(screen.getByTestId("btn-marcar-revisada")).toBeDisabled();
    expect(screen.getByTestId("btn-mal-extraida")).toHaveAttribute("aria-pressed", "true");
  });
});

// =============================================================================
// Marcar revisada
// =============================================================================
describe("AuditActionToolbar — marcar revisada", () => {
  it("click 'Revisada' llama POST con payload correcto", async () => {
    const onAuditComplete = vi.fn();
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={onAuditComplete}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-marcar-revisada"));
    await waitFor(() => expect(toastSuccess).toHaveBeenCalled());

    const call = findCall("POST", "/api/audit-actions");
    expect(call).toBeDefined();
    expect(call!.body).toEqual({
      id_oferta: "ID_001",
      action_type: "mark_revised",
      target_type: "oferta_global",
    });
  });

  it("POST exitoso dispara toast + onAuditComplete('revisada')", async () => {
    const onAuditComplete = vi.fn();
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={onAuditComplete}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-marcar-revisada"));
    await waitFor(() => expect(onAuditComplete).toHaveBeenCalledWith("revisada"));
    expect(toastSuccess).toHaveBeenCalledWith("Oferta marcada como revisada");
  });

  it("POST fallido dispara toast.error con mensaje del backend", async () => {
    fetchHandler = (_url, _init) =>
      Promise.resolve(
        new Response(JSON.stringify({ error: "id_oferta no existe: ID_001" }), {
          status: 404,
          headers: { "Content-Type": "application/json" },
        }),
      );
    const onAuditComplete = vi.fn();
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={onAuditComplete}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-marcar-revisada"));
    await waitFor(() => expect(toastError).toHaveBeenCalled());
    expect(toastError).toHaveBeenCalledWith("id_oferta no existe: ID_001");
    expect(onAuditComplete).not.toHaveBeenCalled();
  });
});

// =============================================================================
// Marcar mal extraída — modal
// =============================================================================
describe("AuditActionToolbar — marcar mal extraída con modal", () => {
  it("click 'Mal extraída' abre AlertDialog con textarea", async () => {
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-mal-extraida"));
    await waitFor(() => {
      expect(screen.getByText(/Marcar oferta como mal extraída/i)).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText(/Ej: las tareas son títulos/i)).toBeInTheDocument();
  });

  it("Confirmar CON nota: POST incluye 'note'", async () => {
    const onAuditComplete = vi.fn();
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={onAuditComplete}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-mal-extraida"));
    await waitFor(() => screen.getByPlaceholderText(/Ej: las tareas son títulos/i));
    fireEvent.change(screen.getByPlaceholderText(/Ej: las tareas son títulos/i), {
      target: { value: "Tareas son encabezados, no descripciones" },
    });
    fireEvent.click(screen.getByText("Confirmar"));
    await waitFor(() =>
      expect(onAuditComplete).toHaveBeenCalledWith("mal_extraida_total"),
    );

    const call = findCall("POST", "/api/audit-actions");
    expect(call!.body).toEqual({
      id_oferta: "ID_001",
      action_type: "mark_total_failure",
      target_type: "oferta_global",
      note: "Tareas son encabezados, no descripciones",
    });
  });

  it("Confirmar SIN nota: POST NO incluye 'note'", async () => {
    const onAuditComplete = vi.fn();
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={onAuditComplete}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-mal-extraida"));
    await waitFor(() => screen.getByText("Confirmar"));
    fireEvent.click(screen.getByText("Confirmar"));
    await waitFor(() =>
      expect(onAuditComplete).toHaveBeenCalledWith("mal_extraida_total"),
    );

    const call = findCall("POST", "/api/audit-actions");
    expect(call!.body).not.toHaveProperty("note");
    expect(call!.body).toEqual({
      id_oferta: "ID_001",
      action_type: "mark_total_failure",
      target_type: "oferta_global",
    });
  });

  it("Cancelar el modal NO dispara POST", async () => {
    const onAuditComplete = vi.fn();
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={onAuditComplete}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-mal-extraida"));
    await waitFor(() => screen.getByText("Cancelar"));
    fireEvent.click(screen.getByText("Cancelar"));
    // No esperar onAuditComplete — sólo verificar que no se hizo POST
    expect(findCall("POST", "/api/audit-actions")).toBeUndefined();
    expect(onAuditComplete).not.toHaveBeenCalled();
  });
});

// =============================================================================
// Desmarcar (toggle off)
// =============================================================================
describe("AuditActionToolbar — desmarcar (toggle off)", () => {
  it("Click 'Revisada ✓' con history poblado llama DELETE del lastActionId obtenido vía GET history", async () => {
    fetchHandler = (url, init) => {
      if ((init?.method === "GET" || !init?.method) && url.includes("/audit-history")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              actions: [
                { id: 77, action_type: "mark_revised", id_oferta: "ID_001" },
              ],
              total: 1,
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      return defaultFetchHandler(url, init);
    };
    const onAuditComplete = vi.fn();
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual="revisada"
        onAuditComplete={onAuditComplete}
      />,
    );
    // El primer GET es el del useEffect (resolve fallback action_id). Esperamos.
    await waitFor(() => expect(findCall("GET", "/audit-history")).toBeDefined());
    fireEvent.click(screen.getByTestId("btn-marcar-revisada"));
    await waitFor(() =>
      expect(findCall("DELETE", "/api/audit-actions/77")).toBeDefined(),
    );
    expect(toastSuccess).toHaveBeenCalledWith("Revisión removida");
    expect(onAuditComplete).toHaveBeenCalledWith(null);
  });

  it("Click 'Mal extraída ⚠' (toggle off) llama DELETE", async () => {
    fetchHandler = (url, init) => {
      if ((init?.method === "GET" || !init?.method) && url.includes("/audit-history")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              actions: [
                { id: 88, action_type: "mark_total_failure", id_oferta: "ID_001" },
              ],
              total: 1,
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      return defaultFetchHandler(url, init);
    };
    const onAuditComplete = vi.fn();
    render(
      <AuditActionToolbar
        idOferta="ID_001"
        estadoRevisionActual="mal_extraida_total"
        onAuditComplete={onAuditComplete}
      />,
    );
    await waitFor(() => expect(findCall("GET", "/audit-history")).toBeDefined());
    fireEvent.click(screen.getByTestId("btn-mal-extraida"));
    await waitFor(() =>
      expect(findCall("DELETE", "/api/audit-actions/88")).toBeDefined(),
    );
    expect(toastSuccess).toHaveBeenCalledWith("Marca de mal extraída removida");
    expect(onAuditComplete).toHaveBeenCalledWith(null);
  });
});

// =============================================================================
// Mount con estado != null: GET history para resolver lastActionId
// =============================================================================
describe("AuditActionToolbar — GET history al montar", () => {
  it("mount con estado='revisada' hace GET /audit-history", async () => {
    render(
      <AuditActionToolbar
        idOferta="ID_HIST"
        estadoRevisionActual="revisada"
        onAuditComplete={vi.fn()}
      />,
    );
    await waitFor(() => {
      const call = findCall("GET", "/api/oferta/ID_HIST/audit-history");
      expect(call).toBeDefined();
    });
  });

  it("mount con estado=null NO hace GET history", async () => {
    render(
      <AuditActionToolbar
        idOferta="ID_NULL"
        estadoRevisionActual={null}
        onAuditComplete={vi.fn()}
      />,
    );
    // Esperar un microtick para asegurar que useEffect corrió
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(findCall("GET", "/audit-history")).toBeUndefined();
  });
});

// =============================================================================
// Imperative handle (para atajos de teclado en el padre)
// =============================================================================
describe("AuditActionToolbar — imperative handle", () => {
  it("triggerRevisada() ejecuta la misma lógica que el click", async () => {
    const onAuditComplete = vi.fn();
    const ref = createRef<AuditActionToolbarHandle>();
    render(
      <AuditActionToolbar
        ref={ref}
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={onAuditComplete}
      />,
    );
    expect(ref.current).not.toBeNull();
    act(() => {
      ref.current?.triggerRevisada();
    });
    await waitFor(() => expect(onAuditComplete).toHaveBeenCalledWith("revisada"));
  });

  it("triggerMalExtraida() abre el modal (no postea aún)", async () => {
    const ref = createRef<AuditActionToolbarHandle>();
    render(
      <AuditActionToolbar
        ref={ref}
        idOferta="ID_001"
        estadoRevisionActual={null}
        onAuditComplete={vi.fn()}
      />,
    );
    act(() => {
      ref.current?.triggerMalExtraida();
    });
    await waitFor(() => {
      expect(screen.getByText(/Marcar oferta como mal extraída/i)).toBeInTheDocument();
    });
    expect(findCall("POST", "/api/audit-actions")).toBeUndefined();
  });
});
