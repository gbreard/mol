import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  VelocidadCoberturaChart,
  VELOCIDAD_COLORS,
} from "../../components/laboratorio/VelocidadCoberturaChart";
import type { VelocidadCobertura } from "../../lib/supabase";

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

const mockData: VelocidadCobertura[] = [
  {
    isco_code: "2514",
    isco_label: "Programadores de aplicaciones",
    total_ofertas: 50,
    mediana_dias: 60,
    q1_dias: 30,
    q3_dias: 90,
    min_dias: 5,
    max_dias: 120,
    categoria: "lenta",
  },
  {
    isco_code: "4110",
    isco_label: "Oficinistas generales",
    total_ofertas: 30,
    mediana_dias: 25,
    q1_dias: 15,
    q3_dias: 35,
    min_dias: 7,
    max_dias: 50,
    categoria: "normal",
  },
  {
    isco_code: "9112",
    isco_label: "Limpiadores de oficinas",
    total_ofertas: 20,
    mediana_dias: 8,
    q1_dias: 3,
    q3_dias: 12,
    min_dias: 1,
    max_dias: 20,
    categoria: "rapida",
  },
];

describe("VelocidadCoberturaChart", () => {
  it("renders chart container", () => {
    render(<VelocidadCoberturaChart data={mockData} />);
    expect(screen.getByTestId("velocidad-chart-container")).toBeInTheDocument();
  });

  it("renders bar chart", () => {
    render(<VelocidadCoberturaChart data={mockData} />);
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("renders legend with counts per category", () => {
    render(<VelocidadCoberturaChart data={mockData} />);
    const legend = screen.getByTestId("velocidad-legend");
    expect(legend).toBeInTheDocument();
    expect(legend.textContent).toContain("rapida (1)");
    expect(legend.textContent).toContain("normal (1)");
    expect(legend.textContent).toContain("lenta (1)");
  });

  it("handles empty data", () => {
    render(<VelocidadCoberturaChart data={[]} />);
    const legend = screen.getByTestId("velocidad-legend");
    expect(legend.textContent).toContain("rapida (0)");
    expect(legend.textContent).toContain("normal (0)");
    expect(legend.textContent).toContain("lenta (0)");
  });

  it("VELOCIDAD_COLORS has exactly 3 entries", () => {
    expect(Object.keys(VELOCIDAD_COLORS)).toHaveLength(3);
    expect(VELOCIDAD_COLORS).toHaveProperty("rapida");
    expect(VELOCIDAD_COLORS).toHaveProperty("normal");
    expect(VELOCIDAD_COLORS).toHaveProperty("lenta");
  });
});
