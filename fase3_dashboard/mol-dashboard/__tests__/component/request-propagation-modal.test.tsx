/**
 * Tests para RequestPropagationModal — SPEC T Fase 4.
 *
 * Cubre: render, validación de justificación, submit OK, error de API,
 * cancelar y submit con tipo aproximado.
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";

import { RequestPropagationModal } from "@/components/issues/RequestPropagationModal";

const ISSUE_ID = "test-issue-uuid";

afterEach(() => server.resetHandlers());

function setup(overrides: Partial<React.ComponentProps<typeof RequestPropagationModal>> = {}) {
  const onClose = vi.fn();
  const onSubmitted = vi.fn();
  const props = {
    issueId: ISSUE_ID,
    open: true,
    onClose,
    onSubmitted,
    ...overrides,
  };
  return { ...render(<RequestPropagationModal {...props} />), onClose, onSubmitted };
}

describe("RequestPropagationModal", () => {
  it("no renderiza si open=false", () => {
    const { container } = render(
      <RequestPropagationModal
        issueId={ISSUE_ID}
        open={false}
        onClose={() => {}}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("muestra título y campos básicos", () => {
    setup();
    expect(screen.getByText(/Solicitar propagación/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/operarios de depósito/)).toBeInTheDocument();
    expect(screen.getByText(/El admin va a revisar/)).toBeInTheDocument();
  });

  it("botón Enviar deshabilitado sin justificación", () => {
    setup();
    const enviar = screen.getByText(/Enviar solicitud/) as HTMLButtonElement;
    expect(enviar.disabled).toBe(true);
  });

  it("submit OK llama onSubmitted y onClose", async () => {
    server.use(
      http.post(`/api/issues/${ISSUE_ID}/solicitar-propagacion`, async () =>
        HttpResponse.json({ ok: true, issue_id: ISSUE_ID })
      )
    );
    const { onClose, onSubmitted } = setup();

    const textarea = screen.getByPlaceholderText(/operarios de depósito/);
    fireEvent.change(textarea, {
      target: { value: "Esto aplica a todos los operarios similares" },
    });

    fireEvent.click(screen.getByText(/Enviar solicitud/));
    await waitFor(() => expect(onSubmitted).toHaveBeenCalled());
    expect(onClose).toHaveBeenCalled();
  });

  it("submit con error muestra el mensaje", async () => {
    server.use(
      http.post(`/api/issues/${ISSUE_ID}/solicitar-propagacion`, async () =>
        HttpResponse.json({ error: "Solicitud ya existe" }, { status: 409 })
      )
    );
    const { onSubmitted } = setup();

    fireEvent.change(screen.getByPlaceholderText(/operarios de depósito/), {
      target: { value: "test justificación" },
    });
    fireEvent.click(screen.getByText(/Enviar solicitud/));

    await waitFor(() =>
      expect(screen.getByText(/Solicitud ya existe/)).toBeInTheDocument()
    );
    expect(onSubmitted).not.toHaveBeenCalled();
  });

  it("Cancelar llama onClose", () => {
    const { onClose } = setup();
    fireEvent.click(screen.getByText(/Cancelar/));
    expect(onClose).toHaveBeenCalled();
  });

  it("contador de caracteres se actualiza", () => {
    setup();
    const textarea = screen.getByPlaceholderText(/operarios de depósito/);
    fireEvent.change(textarea, { target: { value: "Hola mundo" } });
    expect(screen.getByText(/10\/500/)).toBeInTheDocument();
  });

  it("envía tipo_aproximado seleccionado", async () => {
    let capturedBody: Record<string, unknown> | null = null;
    server.use(
      http.post(`/api/issues/${ISSUE_ID}/solicitar-propagacion`, async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ ok: true });
      })
    );

    const { onSubmitted } = setup();
    fireEvent.change(screen.getByPlaceholderText(/operarios de depósito/), {
      target: { value: "test" },
    });
    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "matching_esco" },
    });
    fireEvent.click(screen.getByText(/Enviar solicitud/));

    await waitFor(() => expect(onSubmitted).toHaveBeenCalled());
    expect(capturedBody).toMatchObject({
      justificacion: "test",
      tipo_aproximado: "matching_esco",
    });
  });
});
