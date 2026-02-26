import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  BrechaCalificacionChart,
  CATEGORIA_COLORS,
} from "../../components/laboratorio/BrechaCalificacionChart";
import type { BrechaCalificacion } from "../../lib/supabase";

vi.mock("recharts", () => {
  const MockResponsiveContainer = ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  );
  const MockBarChart = ({ children }: any) => (
    <div data-testid="bar-chart">{children}</div>
  );
  const MockBar = ({ children }: any) => (
    <div data-testid="bar">{children}</div>
  );
  return {
    ResponsiveContainer: MockResponsiveContainer,
    BarChart: MockBarChart,
    Bar: MockBar,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    ReferenceLine: () => null,
    Cell: () => null,
  };
});

const mockData: BrechaCalificacion[] = [
  {
    isco_code: "2514",
    isco_label: "Programadores de aplicaciones",
    total_ofertas: 50,
    skills_promedio: 8.5,
    brecha: 1.65,
    categoria: "sobreexigente",
  },
  {
    isco_code: "4110",
    isco_label: "Oficinistas generales",
    total_ofertas: 30,
    skills_promedio: 5.2,
    brecha: 1.01,
    categoria: "equilibrado",
  },
  {
    isco_code: "9112",
    isco_label: "Limpiadores de oficinas",
    total_ofertas: 20,
    skills_promedio: 2.1,
    brecha: 0.41,
    categoria: "subexigente",
  },
];

describe("BrechaCalificacionChart", () => {
  it("renders chart container", () => {
    render(<BrechaCalificacionChart data={mockData} />);
    expect(screen.getByTestId("brecha-chart-container")).toBeInTheDocument();
  });

  it("renders bar chart", () => {
    render(<BrechaCalificacionChart data={mockData} />);
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("renders legend with counts per category", () => {
    render(<BrechaCalificacionChart data={mockData} />);
    const legend = screen.getByTestId("brecha-legend");
    expect(legend).toBeInTheDocument();
    expect(legend.textContent).toContain("sobreexigente (1)");
    expect(legend.textContent).toContain("equilibrado (1)");
    expect(legend.textContent).toContain("subexigente (1)");
  });

  it("handles empty data", () => {
    render(<BrechaCalificacionChart data={[]} />);
    const legend = screen.getByTestId("brecha-legend");
    expect(legend.textContent).toContain("sobreexigente (0)");
    expect(legend.textContent).toContain("equilibrado (0)");
    expect(legend.textContent).toContain("subexigente (0)");
  });

  it("CATEGORIA_COLORS has exactly 3 entries", () => {
    expect(Object.keys(CATEGORIA_COLORS)).toHaveLength(3);
    expect(CATEGORIA_COLORS).toHaveProperty("sobreexigente");
    expect(CATEGORIA_COLORS).toHaveProperty("equilibrado");
    expect(CATEGORIA_COLORS).toHaveProperty("subexigente");
  });
});
