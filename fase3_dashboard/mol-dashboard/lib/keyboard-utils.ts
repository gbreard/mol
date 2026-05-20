/**
 * Devuelve true si las teclas de navegación (flechas, etc.) deben
 * ignorarse porque el foco está en un elemento donde tienen su propio
 * comportamiento natural (escribir texto, abrir dropdown, navegar dialog).
 *
 * Usado por listeners globales (ej: ArrowUp/Down para navegar lista de
 * ofertas) para evitar interferir con inputs del wizard o dialogs.
 *
 * Reportado en B1: docs/issues/2026-05-19_B1_oferta_cambia_entre_secciones.md
 */
export function shouldSkipKeyNavigation(target: EventTarget | null): boolean {
  if (!target) return false;
  const el = target as HTMLElement;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (el.isContentEditable) return true;
  if (typeof el.closest === "function" && el.closest('[role="dialog"]')) return true;
  return false;
}
