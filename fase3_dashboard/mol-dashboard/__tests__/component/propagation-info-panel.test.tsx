/**
 * Tests para PropagationInfoPanel — SPEC T Fase 4.
 *
 * Cubre los 4 estados visibles + botones según rol + banner explicativo.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { PropagationInfoPanel } from "@/components/issues/PropagationInfoPanel";
import type { Issue } from "@/lib/types";

const baseIssue: Issue = {
  id: "test-id-1",
  titulo: "Test issue",
  tipo: "error_isco",
  estado: "resuelto",
  prioridad: "media",
  autor_id: "u1",
  autor_email: "user@test.com",
  created_at: "2026-04-27T10:00:00Z",
  updated_at: "2026-04-27T10:00:00Z",
};

describe("PropagationInfoPanel", () => {
  it("estado aplicada muestra mensaje verde + detalle del patrón", () => {
    const { container } = render(
      <PropagationInfoPanel
        issue={{
          ...baseIssue,
          propagacion_n: 7,
          patron_corregido: {
            tipo: "matching_esco",
            campo: "esco_label",
            condicion: { tipo: "regla_aplicada", valor_unico: "R358" },
            valor_anterior: "9333.3",
            valor_nuevo: "8343.4",
          },
        }}
      />
    );
    expect(container.textContent).toContain("se propagó a");
    // El conteo aparece en el mensaje (puede aparecer tb en badge "+7")
    expect(container.textContent).toContain("7");
    // Detalle del patrón
    expect(container.textContent).toContain("regla_aplicada");
    expect(container.textContent).toContain("R358");
    expect(container.textContent).toContain("9333.3");
    expect(container.textContent).toContain("8343.4");
  });

  it("estado solicitada muestra solicitante + botón cancelar", () => {
    const onCancelar = vi.fn();
    render(
      <PropagationInfoPanel
        issue={{
          ...baseIssue,
          propagacion_solicitada: true,
          propagacion_solicitada_por: "cynthia@oede.gob.ar",
          propagacion_solicitada_at: "2026-04-28T14:00:00Z",
        }}
        onCancelarSolicitud={onCancelar}
      />
    );
    expect(screen.getByText(/Solicitada por/)).toBeInTheDocument();
    expect(screen.getByText("cynthia@oede.gob.ar")).toBeInTheDocument();
    const cancelar = screen.getByText(/Cancelar solicitud/);
    fireEvent.click(cancelar);
    expect(onCancelar).toHaveBeenCalled();
  });

  it("estado sin_auditar muestra botón solicitar", () => {
    const onSolicitar = vi.fn();
    render(
      <PropagationInfoPanel
        issue={{ ...baseIssue, estado: "resuelto" }}
        onSolicitar={onSolicitar}
      />
    );
    expect(screen.getByText(/se cerró antes/)).toBeInTheDocument();
    const btn = screen.getByText(/Sí, solicitar propagación/);
    fireEvent.click(btn);
    expect(onSolicitar).toHaveBeenCalled();
  });

  it("estado excepcion muestra mensaje neutro", () => {
    render(
      <PropagationInfoPanel
        issue={{
          ...baseIssue,
          propagacion_n: 0,
          patron_corregido: {
            tipo: "matching_esco",
            campo: "esco_label",
            condicion: { tipo: "id_oferta_lista", valores: ["123"] },
          },
        }}
      />
    );
    expect(screen.getByText(/Caso puntual/)).toBeInTheDocument();
  });

  it("banner '¿Qué es?' colapsable", () => {
    const { container } = render(<PropagationInfoPanel issue={baseIssue} />);
    expect(container.textContent).not.toContain("Cuando reportás un error");
    fireEvent.click(screen.getByText(/¿Qué es esto/));
    expect(container.textContent).toContain("Cuando reportás un error");
  });

  it("banner muestra texto distinto para analista (no admin)", () => {
    const { container } = render(
      <PropagationInfoPanel issue={baseIssue} isAdmin={false} />
    );
    fireEvent.click(screen.getByText(/¿Qué es esto/));
    // textContent agrega el texto de elementos anidados (incluye <b>)
    expect(container.textContent).toContain("NO aplicás la propagación");
    expect(container.textContent).toContain("Quien aplica");
  });

  it("banner muestra texto distinto para admin", () => {
    const { container } = render(<PropagationInfoPanel issue={baseIssue} isAdmin />);
    fireEvent.click(screen.getByText(/¿Qué es esto/));
    expect(container.textContent).toContain("Como admin");
    expect(container.textContent).not.toContain("NO aplicás");
  });
});
