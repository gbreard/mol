/**
 * Test de integración del checkbox "solicitar propagación" en WizardModal.
 * SPEC T Fase 4 cosmético #1.
 *
 * Verifica que:
 * - El checkbox solo aparece cuando trigger=error.
 * - Al activarlo, el flag solicitar_propagacion=true llega al onSave.
 * - Sin activarlo, el flag queda undefined/false.
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { WizardModal } from "@/components/validacion/wizard/WizardModal";
import type { OfertaValidacion } from "@/lib/types";

const minimalOferta: OfertaValidacion = {
  id_oferta: "test-oferta-1",
  titulo: "Test oferta",
  titulo_limpio: "Test oferta",
  descripcion: "descripcion test",
  empresa: "Empresa X",
  portal: "test-portal",
  isco_code: "1234",
  isco_label: "test label",
  esco_occupation_label: "test esco",
  fecha_publicacion: "2026-04-27",
  estado_validacion: "pendiente",
  validacion_humana: null,
  // campos opcionales
  ofertas_skills: [],
} as unknown as OfertaValidacion;

afterEach(() => vi.restoreAllMocks());

describe("WizardModal — checkbox solicitar propagación", () => {
  it("checkbox aparece cuando trigger=error", () => {
    render(
      <WizardModal
        open
        onOpenChange={() => {}}
        oferta={minimalOferta}
        trigger="error"
        onSave={vi.fn()}
      />
    );
    expect(
      screen.getByText(/Esta corrección probablemente aplica/)
    ).toBeInTheDocument();
  });

  it("checkbox NO aparece cuando trigger=revisar", () => {
    render(
      <WizardModal
        open
        onOpenChange={() => {}}
        oferta={minimalOferta}
        trigger="revisar"
        onSave={vi.fn()}
      />
    );
    expect(
      screen.queryByText(/Esta corrección probablemente aplica/)
    ).not.toBeInTheDocument();
  });

  it("checkbox NO aparece cuando trigger=editar", () => {
    render(
      <WizardModal
        open
        onOpenChange={() => {}}
        oferta={minimalOferta}
        trigger="editar"
        onSave={vi.fn()}
      />
    );
    expect(
      screen.queryByText(/Esta corrección probablemente aplica/)
    ).not.toBeInTheDocument();
  });

  it("activar checkbox + guardar pasa solicitar_propagacion=true en correcciones", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <WizardModal
        open
        onOpenChange={() => {}}
        oferta={minimalOferta}
        trigger="error"
        onSave={onSave}
      />
    );

    // Escribir nota para habilitar botón Guardar
    const textarea = screen.getByPlaceholderText(/Nota de correccion/);
    fireEvent.change(textarea, { target: { value: "Esta es la justificación" } });

    // Activar checkbox
    const checkbox = screen.getByRole("checkbox") as HTMLInputElement;
    fireEvent.click(checkbox);
    expect(checkbox.checked).toBe(true);

    // Guardar
    fireEvent.click(screen.getByText(/Guardar correccion/));

    await vi.waitFor(() => expect(onSave).toHaveBeenCalled());
    const [, correcciones] = onSave.mock.calls[0];
    expect(correcciones.solicitar_propagacion).toBe(true);
    expect(correcciones.nota).toBe("Esta es la justificación");
  });

  it("sin activar checkbox, solicitar_propagacion queda undefined", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <WizardModal
        open
        onOpenChange={() => {}}
        oferta={minimalOferta}
        trigger="error"
        onSave={onSave}
      />
    );

    fireEvent.change(screen.getByPlaceholderText(/Nota de correccion/), {
      target: { value: "test" },
    });
    fireEvent.click(screen.getByText(/Guardar correccion/));

    await vi.waitFor(() => expect(onSave).toHaveBeenCalled());
    const [, correcciones] = onSave.mock.calls[0];
    expect(correcciones.solicitar_propagacion).toBeUndefined();
  });
});
