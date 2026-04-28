/**
 * Test del fragment OfertasEjemploTable dentro de /admin/procesamiento/catalogo.
 * Verifica que las ofertas detectadas se renderizan con link a validación.
 *
 * Como el componente está privado dentro del page, testeamos indirectamente
 * renderizando el page completo con MSW intercepting.
 */
import { describe, it, expect, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";

import CatalogoPage from "@/app/admin/procesamiento/catalogo/page";

afterEach(() => server.resetHandlers());

const ocupacionConOfertas = {
  id: "mol-occ-test",
  label: "Test polivalente",
  label_normalized: "test polivalente",
  definicion: "Definición de prueba",
  isco_parent: "7233",
  isco_parent_label: "mecánicos",
  esco_parent_uri: null,
  esco_parent_label: null,
  source: "mol_catalogo",
  skills_esenciales: ["skill1", "skill2"],
  skills_opcionales: ["opt1"],
  sector: "Industrial",
  frecuencia_mercado: 50,
  primera_deteccion: "2026-04-28",
  estado: "detectada",
  aprobada_por: null,
  version_catalogo: null,
  notas: "test",
  ofertas_ejemplo: [
    {
      id_oferta: "8088943442",
      titulo: "Patient & Diagnostic Manager",
      esco_actual: "1221.4 director comercial",
      regla_aplicada: "sin_regla",
      fecha_deteccion: "2026-04-28",
    },
    {
      id_oferta: "1118102093",
      titulo: "Técnico de Mantenimiento Edilicio",
      esco_actual: "7131.1 pintor de obra",
      regla_aplicada: "R162_tecnico_mantenimiento_edilicio",
      fecha_deteccion: "2026-04-26",
    },
  ],
};

describe("Catálogo MOL — OfertasEjemploTable", () => {
  it("muestra la fila expandible con chevron cuando hay ofertas_ejemplo", async () => {
    server.use(
      http.get("/api/catalogo-mol/ocupaciones", () =>
        HttpResponse.json({ ocupaciones: [ocupacionConOfertas], total: 1 })
      ),
      http.get("/api/catalogo-mol/stats", () =>
        HttpResponse.json({
          skills: { total: 0, catalogadas: 0, en_revision: 0, detectadas: 0, descartadas: 0, por_tipo: {} },
          ocupaciones: { total: 1, catalogadas: 0, en_revision: 0, detectadas: 1, descartadas: 0 },
          versiones: [],
          ultima_version: null,
        })
      ),
      http.get("/api/catalogo-mol/skills", () => HttpResponse.json({ skills: [], total: 0 })),
      http.get("/api/catalogo-mol/versiones", () => HttpResponse.json({ versiones: [] })),
      http.get("/api/catalogo-mol/unclassified", () =>
        HttpResponse.json({ unclassified_skills: [], unclassified_titles: [], total_ofertas: 0 })
      )
    );

    render(<CatalogoPage />);

    // Click en tab Ocupaciones (el page abre Skills por default)
    await waitFor(() => screen.getByText(/Ocupaciones MOL/));
    fireEvent.click(screen.getByText(/Ocupaciones MOL/));

    // Esperar que la fila aparezca
    await waitFor(() =>
      expect(screen.getByText("Test polivalente")).toBeInTheDocument()
    );

    // Hay un botón con chevron (la fila es expandible)
    const expandBtn = screen.getByTitle(/Ver 2 ofertas/);
    expect(expandBtn).toBeInTheDocument();

    // Click expande la fila
    fireEvent.click(expandBtn);

    // Verifica que aparece tabla anidada con las 2 ofertas
    await waitFor(() => {
      expect(screen.getByText(/Ofertas que motivaron esta entrada/)).toBeInTheDocument();
    });
    expect(screen.getByText("8088943442")).toBeInTheDocument();
    expect(screen.getByText("Patient & Diagnostic Manager")).toBeInTheDocument();
    expect(screen.getByText("1118102093")).toBeInTheDocument();
    expect(screen.getByText(/1221\.4 director comercial/)).toBeInTheDocument();

    // Hay link a validación
    const links = screen.getAllByTitle(/Abrir oferta en validación/);
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/admin/validacion?id=8088943442");
  });

  it("ocupación sin ofertas_ejemplo NO muestra chevron expandible", async () => {
    const ocupacionSinOfertas = { ...ocupacionConOfertas, id: "mol-occ-vacia", ofertas_ejemplo: [] };
    server.use(
      http.get("/api/catalogo-mol/ocupaciones", () =>
        HttpResponse.json({ ocupaciones: [ocupacionSinOfertas], total: 1 })
      ),
      http.get("/api/catalogo-mol/stats", () =>
        HttpResponse.json({
          skills: { total: 0, catalogadas: 0, en_revision: 0, detectadas: 0, descartadas: 0, por_tipo: {} },
          ocupaciones: { total: 1, catalogadas: 0, en_revision: 0, detectadas: 1, descartadas: 0 },
          versiones: [],
          ultima_version: null,
        })
      ),
      http.get("/api/catalogo-mol/skills", () => HttpResponse.json({ skills: [], total: 0 })),
      http.get("/api/catalogo-mol/versiones", () => HttpResponse.json({ versiones: [] })),
      http.get("/api/catalogo-mol/unclassified", () =>
        HttpResponse.json({ unclassified_skills: [], unclassified_titles: [], total_ofertas: 0 })
      )
    );

    render(<CatalogoPage />);
    await waitFor(() => screen.getByText(/Ocupaciones MOL/));
    fireEvent.click(screen.getByText(/Ocupaciones MOL/));
    await waitFor(() => screen.getByText("Test polivalente"));

    // No hay botón expandible (queda solo "—")
    expect(screen.queryByTitle(/Ver \d+ ofertas/)).not.toBeInTheDocument();
  });
});
