import { describe, it, expect } from "vitest";
import { shouldSkipKeyNavigation } from "@/lib/keyboard-utils";

/**
 * Tests para el fix de B1 — listener global de ArrowUp/Down debe ignorar
 * eventos cuyo target es un campo editable o vive dentro de un dialog.
 *
 * Sin esto, Cyn perdía la oferta seleccionada al escribir en el wizard
 * de Edición y usar flechas para navegar el texto.
 *
 * Ref: docs/issues/2026-05-19_B1_oferta_cambia_entre_secciones.md
 */
describe("shouldSkipKeyNavigation (fix B1)", () => {
  it("skip cuando el target es un INPUT", () => {
    const input = document.createElement("input");
    expect(shouldSkipKeyNavigation(input)).toBe(true);
  });

  it("skip cuando el target es un TEXTAREA", () => {
    const textarea = document.createElement("textarea");
    expect(shouldSkipKeyNavigation(textarea)).toBe(true);
  });

  it("skip cuando el target es un SELECT", () => {
    const select = document.createElement("select");
    expect(shouldSkipKeyNavigation(select)).toBe(true);
  });

  it("skip cuando el target es contentEditable", () => {
    const div = document.createElement("div");
    div.contentEditable = "true";
    expect(shouldSkipKeyNavigation(div)).toBe(true);
  });

  it("skip cuando el target está dentro de un role='dialog' (modal/wizard)", () => {
    const dialog = document.createElement("div");
    dialog.setAttribute("role", "dialog");
    const inner = document.createElement("button");
    dialog.appendChild(inner);
    document.body.appendChild(dialog);
    try {
      expect(shouldSkipKeyNavigation(inner)).toBe(true);
    } finally {
      document.body.removeChild(dialog);
    }
  });

  it("NO skip cuando el target es un div común fuera de dialog (navegación normal)", () => {
    const div = document.createElement("div");
    expect(shouldSkipKeyNavigation(div)).toBe(false);
  });

  it("NO skip cuando el target es un button común", () => {
    const btn = document.createElement("button");
    expect(shouldSkipKeyNavigation(btn)).toBe(false);
  });

  it("NO skip cuando el target es null (no hay foco)", () => {
    expect(shouldSkipKeyNavigation(null)).toBe(false);
  });
});
