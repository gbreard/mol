/**
 * Tests para PropagationBadge — SPEC T Fase 4.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { PropagationBadge, getPropagationEstado } from "@/components/issues/PropagationBadge";
import type { Issue } from "@/lib/types";

const baseIssue: Pick<Issue, "estado" | "patron_corregido" | "propagacion_n" | "propagacion_solicitada"> = {
  estado: "resuelto",
};

describe("getPropagationEstado", () => {
  it("issue resuelto + propagacion_n>0 → aplicada", () => {
    expect(
      getPropagationEstado({ ...baseIssue, propagacion_n: 7, patron_corregido: { tipo: "matching_esco", campo: "esco_label", condicion: { tipo: "regla_aplicada" } } })
    ).toBe("aplicada");
  });

  it("issue resuelto + solicitada=true + n=0 → solicitada", () => {
    expect(
      getPropagationEstado({ ...baseIssue, propagacion_solicitada: true, propagacion_n: 0 })
    ).toBe("solicitada");
  });

  it("issue resuelto + patron sin n → excepcion", () => {
    expect(
      getPropagationEstado({
        ...baseIssue,
        patron_corregido: { tipo: "matching_esco", campo: "x", condicion: { tipo: "regla_aplicada" } },
        propagacion_n: 0,
      })
    ).toBe("excepcion");
  });

  it("issue resuelto sin patron → sin_auditar", () => {
    expect(getPropagationEstado(baseIssue)).toBe("sin_auditar");
  });

  it("issue resuelto con _audit_note → sin_auditar", () => {
    expect(
      getPropagationEstado({
        ...baseIssue,
        patron_corregido: { _audit_note: "audit-no-pattern" },
      })
    ).toBe("sin_auditar");
  });

  it("issue pendiente sin solicitud → null", () => {
    expect(getPropagationEstado({ ...baseIssue, estado: "pendiente" })).toBeNull();
  });

  it("issue pendiente con solicitud → solicitada", () => {
    expect(
      getPropagationEstado({ ...baseIssue, estado: "pendiente", propagacion_solicitada: true })
    ).toBe("solicitada");
  });
});

describe("PropagationBadge render", () => {
  it("aplicada muestra +N", () => {
    const { container } = render(
      <PropagationBadge
        issue={{
          estado: "resuelto",
          propagacion_n: 7,
          patron_corregido: { tipo: "matching_esco", campo: "x", condicion: { tipo: "regla_aplicada" } },
        }}
      />
    );
    expect(container.textContent).toContain("+7");
    expect(container.querySelector("span")?.title).toContain("propagó");
  });

  it("solicitada muestra '🟡 Solicitada'", () => {
    render(
      <PropagationBadge
        issue={{ estado: "resuelto", propagacion_solicitada: true, propagacion_n: 0 }}
      />
    );
    expect(screen.getByText(/Solicitada/)).toBeTruthy();
  });

  it("sin patron + resuelto muestra '⚠ Sin auditar'", () => {
    render(<PropagationBadge issue={{ estado: "resuelto" }} />);
    expect(screen.getByText(/Sin auditar/)).toBeTruthy();
  });

  it("issue pendiente sin solicitud no renderiza", () => {
    const { container } = render(<PropagationBadge issue={{ estado: "pendiente" }} />);
    expect(container.firstChild).toBeNull();
  });
});
