/**
 * Tests para ProcessPropagationPanel — SPEC T Fase 4 (admin).
 *
 * Cubre los 3 pasos: estructurar → dry-run → aplicar/rechazar.
 */
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";

import { ProcessPropagationPanel } from "@/components/issues/ProcessPropagationPanel";
import type { Issue } from "@/lib/types";

const ISSUE_ID = "test-issue-uuid";

const baseIssue: Issue = {
  id: ISSUE_ID,
  titulo: "Test issue",
  tipo: "error_isco",
  estado: "resuelto",
  prioridad: "alta",
  autor_id: "u1",
  autor_email: "user@test.com",
  created_at: "2026-04-27T10:00:00Z",
  updated_at: "2026-04-27T10:00:00Z",
  id_oferta: "8299423434",
  propagacion_solicitada: true,
  propagacion_solicitada_por: "cynthia@oede.gob.ar",
  propagacion_solicitada_at: "2026-04-28T14:00:00Z",
};

beforeEach(() => {
  // happy-dom no tiene confirm/prompt — los stubeo
  vi.stubGlobal("confirm", () => true);
  vi.stubGlobal("prompt", () => "motivo test");
});

afterEach(() => {
  server.resetHandlers();
  vi.unstubAllGlobals();
});

describe("ProcessPropagationPanel", () => {
  it("renderiza paso 1 inicial con info del solicitante", () => {
    render(<ProcessPropagationPanel issue={baseIssue} />);
    expect(screen.getByText(/Procesar propagación/)).toBeInTheDocument();
    expect(screen.getByText(/cynthia@oede.gob.ar/)).toBeInTheDocument();
    expect(screen.getByText(/Estimar/)).toBeInTheDocument();
  });

  it("dry-run exitoso pasa a paso 2 con conteo + sample", async () => {
    server.use(
      http.post(`/api/issues/${ISSUE_ID}/propagation/dry-run`, async () =>
        HttpResponse.json({
          issue_id: ISSUE_ID,
          result: {
            tipo: "matching_esco",
            ofertas_identificadas: 7,
            ofertas_actualizadas: 7,
            ids_tocados: [101, 102, 103, 104, 105, 106, 107],
            errores: [],
            dry_run: true,
          },
        })
      )
    );
    const { container } = render(<ProcessPropagationPanel issue={baseIssue} />);

    fireEvent.click(screen.getByText(/Estimar/));

    await waitFor(() =>
      expect(container.textContent).toMatch(/7\s*ofertas matchean/)
    );
    expect(container.textContent).toContain("Sample");
    expect(container.textContent).toContain("101");
    expect(screen.getByText(/Aplicar a las 7/)).toBeInTheDocument();
  });

  it("apply exitoso pasa a paso 3 con mensaje verde", async () => {
    server.use(
      http.post(`/api/issues/${ISSUE_ID}/propagation/dry-run`, async () =>
        HttpResponse.json({
          issue_id: ISSUE_ID,
          result: {
            tipo: "matching_esco",
            ofertas_identificadas: 3,
            ofertas_actualizadas: 3,
            ids_tocados: [1, 2, 3],
            errores: [],
            dry_run: true,
          },
        })
      ),
      http.post(`/api/issues/${ISSUE_ID}/propagation/apply`, async () =>
        HttpResponse.json({
          issue_id: ISSUE_ID,
          applied_by: "admin@test.com",
          result: { ofertas_actualizadas: 3 },
        })
      )
    );
    const onApplied = vi.fn();
    const { container } = render(
      <ProcessPropagationPanel issue={baseIssue} onApplied={onApplied} />
    );

    fireEvent.click(screen.getByText(/Estimar/));
    await waitFor(() => expect(container.textContent).toMatch(/3\s*ofertas matchean/));

    fireEvent.click(screen.getByText(/Aplicar a las 3/));
    await waitFor(() => expect(onApplied).toHaveBeenCalled());
    expect(screen.getByText(/Propagación aplicada/)).toBeInTheDocument();
  });

  it("rechazar llama API y onApplied", async () => {
    server.use(
      http.post(`/api/issues/${ISSUE_ID}/propagation/rechazar`, async () =>
        HttpResponse.json({ ok: true })
      )
    );
    const onApplied = vi.fn();
    render(<ProcessPropagationPanel issue={baseIssue} onApplied={onApplied} />);

    fireEvent.click(screen.getByText(/Rechazar/));
    await waitFor(() => expect(onApplied).toHaveBeenCalled());
  });

  it("dry-run con error muestra mensaje", async () => {
    server.use(
      http.post(`/api/issues/${ISSUE_ID}/propagation/dry-run`, async () =>
        HttpResponse.json({ error: "patrón inválido" }, { status: 400 })
      )
    );
    render(<ProcessPropagationPanel issue={baseIssue} />);
    fireEvent.click(screen.getByText(/Estimar/));
    await waitFor(() =>
      expect(screen.getByText(/patrón inválido/)).toBeInTheDocument()
    );
  });

  it("editor permite cambiar tipo de condición", () => {
    render(<ProcessPropagationPanel issue={baseIssue} />);
    // Hay 2 selects: el primero es Tipo (4 propagation tipos),
    // el segundo es Condición - tipo (titulo_contiene_alguno, regla_aplicada, ...)
    const selects = screen.getAllByRole("combobox") as HTMLSelectElement[];
    const condicionSelect = selects.find(
      (s) => s.value === "id_oferta_lista" || s.value === "titulo_contiene_alguno"
    );
    expect(condicionSelect).toBeDefined();
    if (!condicionSelect) return;
    fireEvent.change(condicionSelect, { target: { value: "regla_aplicada" } });
    expect(screen.getByPlaceholderText(/R236_analista_marketing/)).toBeInTheDocument();
  });

  it("botón Editar patrón vuelve al paso 1", async () => {
    server.use(
      http.post(`/api/issues/${ISSUE_ID}/propagation/dry-run`, async () =>
        HttpResponse.json({
          issue_id: ISSUE_ID,
          result: {
            tipo: "matching_esco",
            ofertas_identificadas: 1,
            ofertas_actualizadas: 1,
            ids_tocados: [99],
            errores: [],
            dry_run: true,
          },
        })
      )
    );
    render(<ProcessPropagationPanel issue={baseIssue} />);
    fireEvent.click(screen.getByText(/Estimar/));
    await waitFor(() => screen.getByText(/Editar patrón/));

    fireEvent.click(screen.getByText(/Editar patrón/));
    expect(screen.getByText(/Estimar/)).toBeInTheDocument();
  });
});
